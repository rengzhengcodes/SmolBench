"""KV-cache sizing for the family-ladder roster.

A naive figure assuming every layer holds full-context KV is wrong for two
thirds of the roster: five attention mechanisms shrink KV by 4-25x, and tp
replication grows it. Per layer, per token of effective context, at BF16:

* **full attention**: ``2 * n_kv * head_dim * 2`` bytes.
* **sliding/local layers**: the same, over ``min(ctx, sliding_window)`` tokens
  (Gemma-4: 40 of 48 layers at window 1024; EXAONE's ``LLLG`` at 4096).
* **linear-attention layers**: ~0 -- constant state, not ctx-proportional KV
  (Qwen3.5-27B: 48 of 64 layers; NemotronH's Mamba-2 mixers).
* **hybrid layer stacks**: NemotronH's ``hybrid_override_pattern`` names one
  mixer per layer -- ``*`` attention, ``M`` Mamba-2, ``-``/``E`` an MLP/MoE-only
  layer with no attention block. Only ``*`` caches KV: 4 of 42, 6 of 52, 8 of 88.
* **Gemma-4's two attention blocks**: global (``full_attention``) layers use
  ``global_head_dim`` 512 and ``num_global_key_value_heads``, sliding layers
  ``head_dim`` 256 and ``num_key_value_heads`` -- so head geometry is per layer,
  not per model. The last ``num_kv_shared_layers`` layers reuse an earlier
  layer's KV and allocate none (E2B: 20 of 35). ``attention_k_eq_v`` does not
  halve anything: both K and V are written, so the ``x2`` stands.
* **MLA**: ``(kv_lora_rank + qk_rope_head_dim) * 2``, one latent per token
  instead of ``n_kv_heads * head_dim`` (GLM-4.7-Flash, DeepSeek-V3.1).
* **DeepSeek-V4's shared latent**: ``(head_dim + qk_rope_head_dim) * 2``, one
  row per token shared by K and V -- no ``kv_lora_rank`` field, but the same
  "one row, no per-head replication" shape as MLA (see `_is_shared_latent`).
* vLLM **replicates KV heads when tp exceeds a layer's KV-head count**,
  multiplying that layer's non-MLA, non-shared-latent KV by
  ``max(1, tp / n_kv)``: Gemma-4-12B's 1-head global layers replicate at tp=4
  while its 8-head sliding layers do not. DeepSeek-V4's single KV head does
  *not* replicate this way -- there is one shared row per token per layer, not
  one per KV head, so a tp shard cannot be "a per-head copy".

The layer mix comes from ``hybrid_override_pattern`` (a per-layer string), else
``layer_types`` (a list), else ``sliding_window_pattern`` (a cycling string,
``L`` local / ``G`` global), else every layer counts as full attention; a bare
``sliding_window`` with neither mix field is deliberately NOT applied (see
`_layer_mix`).

For box sizing, budget ``weights + 2.0 x KV@131k`` (about 8 concurrent
requests) against ``0.90 x total VRAM``; a box sized for one sequence goes
negative at real concurrency. Weight sizes come from checkpoint shard totals,
not this tool. ``kv_budget.py [--ctx 131072]`` prints, per roster model, the
naive figure against the corrected one at tp=1 and at the deploy spec's tp.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_HERE = Path(__file__).resolve().parent
_CONFIGS = _HERE / "arch_configs_raw.json"

BYTES_BF16 = 2
DEFAULT_CTX = 131072

# NemotronH ``hybrid_override_pattern`` alphabet, one character per layer.
# 'M' Mamba-2 is a linear mixer (constant state); '-' (dense MLP) and 'E' (MoE)
# layers carry no attention block at all, so neither kind holds KV.
_HYBRID_KINDS = {"*": "full", "M": "linear", "-": "none", "E": "none"}

# Kinds that allocate no ctx-proportional KV cache.
_NO_KV = ("linear", "none")


def _text_config(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Return the attention-relevant config block (multimodal wrappers nest it)."""
    config = raw["config"]
    inner = config.get("text_config")
    if isinstance(inner, dict):
        # The outer block still supplies fields the wrapper hoists.
        merged = dict(config)
        merged.update(inner)
        return merged
    return config


def _layer_mix(cfg: Dict[str, Any]) -> List[str]:
    """Return each layer's mixer kind: 'full' | 'sliding' | 'linear' | 'none'.

    Mechanism only. KV *sharing* is a separate question -- see `_kv_layers`.
    """
    n_layers = cfg["num_hidden_layers"]
    pattern = cfg.get("hybrid_override_pattern")
    if isinstance(pattern, str) and pattern:
        # Exact key: Nemotron-3-Super also ships ``mtp_hybrid_override_pattern``
        # ('*E'), which describes the unloaded MTP head, not the served stack.
        if len(pattern) != n_layers:
            raise ValueError(
                f"hybrid_override_pattern is {len(pattern)} chars, "
                f"num_hidden_layers is {n_layers}"
            )
        unknown = set(pattern) - set(_HYBRID_KINDS)
        if unknown:
            raise ValueError(f"unknown hybrid_override_pattern symbols: {sorted(unknown)}")
        return [_HYBRID_KINDS[ch] for ch in pattern]
    layer_types = cfg.get("layer_types")
    if isinstance(layer_types, list) and layer_types:
        kinds = []
        for t in layer_types:
            if t == "sliding_attention":
                kinds.append("sliding")
            elif t == "linear_attention":
                kinds.append("linear")
            else:
                kinds.append("full")
        return kinds
    pattern = cfg.get("sliding_window_pattern")
    if isinstance(pattern, str) and pattern:
        return [
            "sliding" if pattern[i % len(pattern)] == "L" else "full"
            for i in range(n_layers)
        ]
    # NOT a bug: a bare ``sliding_window`` with neither mix field is ignored.
    # DeepSeek-V4 carries ``sliding_window=128`` as CSA/HCA scaffolding while
    # keeping full-length KV; applying it would shrink KV ~1000x and size boxes
    # that OOM at serve.
    return ["full"] * n_layers


def _kv_layers(cfg: Dict[str, Any]) -> List[str]:
    """`_layer_mix` with cross-layer KV sharing applied: the KV-allocating mix.

    The last ``num_kv_shared_layers`` layers read an earlier layer's cache and
    allocate none of their own (Gemma-4-E2B: layers 15-34 of 35).
    """
    kinds = _layer_mix(cfg)
    shared = cfg.get("num_kv_shared_layers") or 0
    if shared:
        first_shared = len(kinds) - shared
        kinds = [k if i < first_shared else "none" for i, k in enumerate(kinds)]
    return kinds


def _layer_kv_shape(cfg: Dict[str, Any], kind: str) -> Tuple[int, int]:
    """Return ``(kv_heads, head_dim)`` for one layer of mixer `kind`.

    Gemma-4 is the only roster family whose two attention blocks differ: its
    global layers cache ``global_head_dim`` 512 rows over
    ``num_global_key_value_heads``. E2B leaves that head count null (and the
    override is gated on ``attention_k_eq_v``, false there), so it falls back to
    ``num_key_value_heads`` -- both readings give the same figure.
    """
    n_heads = cfg["num_attention_heads"]
    n_kv = cfg.get("num_key_value_heads") or n_heads
    head_dim = cfg.get("head_dim") or cfg["hidden_size"] // n_heads
    if kind == "full" and cfg.get("global_head_dim"):
        head_dim = cfg["global_head_dim"]
        n_kv = cfg.get("num_global_key_value_heads") or n_kv
    return n_kv, head_dim


def _is_shared_latent(cfg: Dict[str, Any]) -> bool:
    """Return whether `cfg` describes DeepSeek-V4's shared-latent KV cache.

    DeepSeek-V4 caches one ``head_dim + qk_rope_head_dim``-wide row per token
    per layer, shared by K and V, with no per-head replication -- structurally
    close to MLA, but keyed under different fields (no ``kv_lora_rank``).

    Two independent readings are OR-ed together so a later V4 point release
    that renames ``model_type`` still lands on the right arithmetic:

    * the label reading -- ``model_type == "deepseek_v4"``;
    * the structural reading -- a single KV head (``num_key_value_heads == 1``)
      with a rope split (``qk_rope_head_dim`` present) but *no* MLA latent rank.

    The ``kv_lora_rank is None`` clause in the structural reading is load-
    bearing: a config *with* ``kv_lora_rank`` set is ordinary MLA (DeepSeek-V3.1,
    GLM-4.7-Flash) and must fall to the existing MLA branch in `kv_bytes`, not
    be stolen here just because it also happens to have one KV head and a rope
    split.

    Parameters
    ----------
    cfg : dict
        The (text) config block for one checkpoint.

    Returns
    -------
    bool
        True if the shared-latent branch applies to this config.
    """
    if cfg.get("model_type") == "deepseek_v4":
        return True
    return (
        cfg.get("num_key_value_heads") == 1
        and cfg.get("qk_rope_head_dim") is not None
        and cfg.get("kv_lora_rank") is None
    )


def kv_bytes(cfg: Dict[str, Any], ctx: int, tp: int = 1, naive: bool = False) -> int:
    """Total KV-cache bytes for one sequence of `ctx` tokens, over all layers and tp shards.

    Parameters
    ----------
    cfg : dict
        The (text) config block for one checkpoint.
    tp : int
        Tensor-parallel degree. For models that are neither MLA nor
        shared-latent (see `_is_shared_latent`) KV heads replicate when
        ``tp > n_kv``, multiplying a layer's total by ``tp / n_kv``. Applied per
        layer, because Gemma-4's two blocks hold different KV-head counts.
    naive : bool
        Assume every layer holds full-context GQA KV at the model-level head
        geometry -- the uncorrected comparison column.

    Returns
    -------
    int
        Replication only ever raises the total above the tp=1 figure.
    """
    n_layers = cfg["num_hidden_layers"]
    n_heads = cfg["num_attention_heads"]
    n_kv = cfg.get("num_key_value_heads") or n_heads
    head_dim = cfg.get("head_dim") or cfg["hidden_size"] // n_heads
    mla = cfg.get("kv_lora_rank") is not None and not naive

    if mla:
        # One shared latent per token; no per-head KV, no replication.
        per_token = (cfg["kv_lora_rank"] + cfg.get("qk_rope_head_dim", 0)) * BYTES_BF16
        return per_token * ctx * n_layers

    if _is_shared_latent(cfg) and not naive:
        # DeepSeek-V4: one (head_dim + qk_rope_head_dim)-wide row per token per
        # layer, shared by K and V -- no ``2 *`` (there is no separate K and V
        # to double) and no tp replication (one row per token, not one per KV
        # head, so a tp shard is not "a per-head copy"; see `_replication`).
        # Hand check for deepseek-v4-pro: 61 layers x (512 + 64) x 2 B x
        # 131072 tokens = 9.21 GB, against 16.37 GB naive at tp=1 and 131.0 GB
        # on the old (wrong) replicated-at-tp=8 GQA reading this fix removes.
        per_token = (head_dim + cfg.get("qk_rope_head_dim", 0)) * BYTES_BF16
        return per_token * ctx * n_layers

    if naive:
        per_token_full = 2 * n_kv * head_dim * BYTES_BF16
        return int(per_token_full * ctx * n_layers * max(1, tp / n_kv))

    window = cfg.get("sliding_window")
    total = 0.0
    for kind in _kv_layers(cfg):
        if kind in _NO_KV:
            continue
        kv_heads, dim = _layer_kv_shape(cfg, kind)
        eff_ctx = min(ctx, window) if (kind == "sliding" and window) else ctx
        per_token = 2 * kv_heads * dim * BYTES_BF16
        total += per_token * eff_ctx * max(1, tp / kv_heads)
    return int(total)


def _replication(cfg: Dict[str, Any], tp: int) -> float:
    """Largest per-layer KV-head replication factor at `tp` (1.0 if none, MLA and shared-latent included)."""
    if cfg.get("kv_lora_rank") is not None or _is_shared_latent(cfg):
        return 1.0
    factors = [
        max(1, tp / _layer_kv_shape(cfg, kind)[0])
        for kind in _kv_layers(cfg)
        if kind not in _NO_KV
    ]
    return max(factors, default=1.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ctx", type=int, default=DEFAULT_CTX)
    args = parser.parse_args()

    sys.path.insert(0, str(_HERE.parent.parent))
    from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS

    raw = json.loads(_CONFIGS.read_text())
    gib = 1e9  # decimal GB
    print(f"{'model':<28}{'naive GB':>10}{'actual GB':>11}{'@spec tp':>10}   notes")
    for model in sorted(raw):
        cfg = _text_config(raw[model])
        tp = EC2_DEPLOY_SPECS.get(model, {}).get("tp", 1)
        naive = kv_bytes(cfg, args.ctx, tp=1, naive=True) / gib
        actual = kv_bytes(cfg, args.ctx, tp=1) / gib
        at_tp = kv_bytes(cfg, args.ctx, tp=tp) / gib
        notes = []
        if cfg.get("kv_lora_rank") is not None:
            notes.append("MLA")
        elif _is_shared_latent(cfg):
            notes.append("shared latent (K=V)")
        mix = _layer_mix(cfg)
        if "sliding" in mix:
            notes.append(f"{mix.count('sliding')}/{len(mix)} sliding@{cfg.get('sliding_window')}")
        if "linear" in mix:
            notes.append(f"{mix.count('linear')}/{len(mix)} linear")
        if "none" in mix:
            notes.append(f"{mix.count('none')}/{len(mix)} MLP-only")
        shared = cfg.get("num_kv_shared_layers") or 0
        if shared:
            notes.append(f"{shared}/{len(mix)} KV-shared")
        replication = _replication(cfg, tp)
        if replication > 1:
            notes.append(f"KV heads replicate x{replication:g} at tp={tp}")
        print(f"{model:<28}{naive:>10.1f}{actual:>11.1f}{at_tp:>10.1f}   {', '.join(notes)}")


if __name__ == "__main__":
    main()
