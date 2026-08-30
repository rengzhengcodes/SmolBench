"""KV-cache sizing for the family-ladder roster.

A naive figure assuming every layer holds full-context KV is wrong for a third
of the roster: three attention mechanisms shrink KV by 4-25x, and tp
replication grows it. Per layer, per token of effective context, at BF16:

* **full attention**: ``2 * n_kv * head_dim * 2`` bytes.
* **sliding/local layers**: the same, over ``min(ctx, sliding_window)`` tokens
  (Gemma-4: 40 of 48 layers at window 1024; EXAONE's ``LLLG`` at 4096).
* **linear-attention layers**: ~0 -- constant state, not ctx-proportional KV
  (Qwen3.5-27B: 48 of 64 layers).
* **MLA**: ``(kv_lora_rank + qk_rope_head_dim) * 2``, one latent per token
  instead of ``n_kv_heads * head_dim`` (GLM-4.7-Flash, DeepSeek-V3.1).
* vLLM **replicates KV heads when tp > num_key_value_heads**, multiplying
  non-MLA KV by ``max(1, tp / n_kv)``: DeepSeek-V4's single KV head at tp=8 is
  8x its tp=1 figure.

The layer mix comes from ``layer_types`` (a list), else
``sliding_window_pattern`` (a cycling string, ``L`` local / ``G`` global), else
every layer counts as full attention; a bare ``sliding_window`` with neither mix
field is deliberately NOT applied (see `_layer_mix`).

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
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent
_CONFIGS = _HERE / "arch_configs_raw.json"

BYTES_BF16 = 2
DEFAULT_CTX = 131072


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


def _layer_mix(cfg: Dict[str, Any]) -> list:
    """Return per-layer attention kinds: 'full' | 'sliding' | 'linear'."""
    n_layers = cfg["num_hidden_layers"]
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


def kv_bytes(cfg: Dict[str, Any], ctx: int, tp: int = 1, naive: bool = False) -> int:
    """Total KV-cache bytes for one sequence of `ctx` tokens, over all layers and tp shards.

    Parameters
    ----------
    cfg : dict
        The (text) config block for one checkpoint.
    tp : int
        Tensor-parallel degree. For non-MLA models KV heads replicate when
        ``tp > n_kv``, multiplying the total by ``tp / n_kv``.
    naive : bool
        Assume every layer holds full-context GQA KV -- the uncorrected
        comparison column.

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

    replication = max(1, tp / n_kv)
    per_token_full = 2 * n_kv * head_dim * BYTES_BF16
    if naive:
        return int(per_token_full * ctx * n_layers * replication)

    window = cfg.get("sliding_window")
    total = 0
    for kind in _layer_mix(cfg):
        if kind == "linear":
            continue
        eff_ctx = min(ctx, window) if (kind == "sliding" and window) else ctx
        total += per_token_full * eff_ctx
    return int(total * replication)


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
        mix = _layer_mix(cfg)
        if "sliding" in mix:
            notes.append(f"{mix.count('sliding')}/{len(mix)} sliding@{cfg.get('sliding_window')}")
        if "linear" in mix:
            notes.append(f"{mix.count('linear')}/{len(mix)} linear")
        n_kv = cfg.get("num_key_value_heads") or cfg["num_attention_heads"]
        if tp > n_kv and cfg.get("kv_lora_rank") is None:
            notes.append(f"KV heads replicate x{tp // n_kv} at tp={tp}")
        print(f"{model:<28}{naive:>10.1f}{actual:>11.1f}{at_tp:>10.1f}   {', '.join(notes)}")


if __name__ == "__main__":
    main()
