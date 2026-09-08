"""KV-cache sizing for the family-ladder roster.

Account for layer mix, sharing, latent KV, and tp replication. Boxes budget
``weights + 2.0 x KV@131k`` (about 8 requests) against ``0.90 x total VRAM``
because one-sequence sizing goes negative at concurrency.
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

# NemotronH's per-layer alphabet: 'M' Mamba-2 has constant state, '-'/'E'
# (MLP/MoE) carry no attention block -- neither holds KV.
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

    Parameters
    ----------
    cfg : Dict[str, Any]
        Layer-mix fields.

    Returns
    -------
    List[str]
        Per-layer mixer kinds.
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
    # A bare ``sliding_window`` with neither mix field is deliberately ignored:
    # DeepSeek-V4 carries ``sliding_window=128`` as CSA/HCA scaffolding while
    # keeping full-length KV; applying it would undersize the box and OOM it.
    return ["full"] * n_layers


def _kv_layers(cfg: Dict[str, Any]) -> List[str]:
    """`_layer_mix` with cross-layer KV sharing applied: the KV-allocating mix.

    Shared layers allocate no cache because they read an earlier layer's cache.

    Parameters
    ----------
    cfg : Dict[str, Any]
        KV-sharing fields.

    Returns
    -------
    List[str]
        Per-layer cache-allocating mixer kinds.
    """
    kinds = _layer_mix(cfg)
    shared = cfg.get("num_kv_shared_layers") or 0
    if shared:
        first_shared = len(kinds) - shared
        kinds = [k if i < first_shared else "none" for i, k in enumerate(kinds)]
    return kinds


def _layer_kv_shape(cfg: Dict[str, Any], kind: str) -> Tuple[int, int]:
    """Return ``(kv_heads, head_dim)`` for one layer of mixer `kind`.

    Global layers use their own head geometry; null global heads fall back.

    Parameters
    ----------
    cfg : Dict[str, Any]
        KV-head dimensions.
    kind : str
        Layer mixer kind.

    Returns
    -------
    Tuple[int, int]
        KV heads and head dimension.
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

    Match label or structure so renamed point releases retain the arithmetic.
    Exclude ``kv_lora_rank`` because it denotes ordinary MLA.

    Parameters
    ----------
    cfg : Dict[str, Any]
        Configuration to classify.

    Returns
    -------
    bool
        Whether the cache is shared-latent.
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
    cfg : Dict[str, Any]
        Cache geometry.
    ctx : int
        Sequence length.
    tp : int, optional
        Tensor-parallel shards; ordinary KV heads replicate when ``tp > n_kv``.
    naive : bool, optional
        Use full-context GQA at model-level geometry.

    Returns
    -------
    int
        Cache bytes.
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
        # One row per token per layer, shared by K and V: no ``2 *``, and no tp
        # replication since a shard isn't "a per-head copy" here.
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
    """Print the roster's naive and corrected KV-cache budgets."""
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
