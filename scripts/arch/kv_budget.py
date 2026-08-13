"""Correct KV-cache sizing for the family-ladder roster.

The original tier/tp assignments assumed every layer holds full-context KV.
The 2026-08-13 fleet audit showed that is false for a third of the roster --
four attention families shrink KV by 4-25x versus the naive figure:

* **sliding/local layers** cache only ``min(ctx, sliding_window)`` tokens
  (Gemma-4: 40 of 48 layers at window 1024; EXAONE's ``LLLG`` pattern at
  window 4096);
* **linear-attention layers** hold constant state, not ctx-proportional KV
  (Qwen3.5-27B: 48 of 64 layers);
* **MLA** caches one ``kv_lora_rank + qk_rope_head_dim`` latent per token,
  NOT ``n_kv_heads * head_dim`` (GLM-4.7-Flash, DeepSeek-V3.1);
* and vLLM **replicates KV heads when tp > num_key_value_heads**, so
  ``x max(1, tp / n_kv)`` for non-MLA models -- DeepSeek-V4's single KV head
  at tp=8 really is 8x its tp=1 figure.

Per layer, BF16 (2 bytes), per token of effective context::

    full attention:    2 * n_kv * head_dim * 2
    sliding/local:     2 * n_kv * head_dim * 2      (ctx capped at window)
    linear_attention:  ~0
    MLA:               (kv_lora_rank + qk_rope_head_dim) * 2

The layer mix comes from config ``layer_types`` (a list) when present, else
``sliding_window_pattern`` (a cycling string like ``"LLLG"``; ``L`` = local/
sliding, ``G`` = global/full), else every layer counts as full attention. A
bare ``sliding_window`` value WITHOUT either mix field is deliberately NOT
applied (DeepSeek-V4 carries ``sliding_window=128`` for its CSA/HCA sparse
scheme yet keeps full-length KV).

For replication-study box sizing, budget ``weights + 2.0 x KV@131k`` against
``0.90 x total VRAM`` (about 8 concurrent requests) -- sizing for a single
sequence produces boxes that go negative at real concurrency. Weight sizes
come from checkpoint shard totals, not this tool.

Usage
-----
``.venv/bin/python scripts/arch/kv_budget.py [--ctx 131072]``

Prints one row per roster model: the naive all-full figure, the corrected
tp=1 figure, and the corrected figure at the deploy spec's tp.
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
    """The attention-relevant config block (multimodal wrappers nest it)."""
    config = raw["config"]
    inner = config.get("text_config")
    if isinstance(inner, dict):
        # Fall back to the outer block for fields the wrapper hoists.
        merged = dict(config)
        merged.update(inner)
        return merged
    return config


def _layer_mix(cfg: Dict[str, Any]) -> list:
    """Per-layer attention kinds: 'full' | 'sliding' | 'linear'."""
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
    return ["full"] * n_layers


def kv_bytes(cfg: Dict[str, Any], ctx: int, tp: int = 1, naive: bool = False) -> int:
    """Total KV-cache bytes for one sequence of `ctx` tokens.

    Parameters
    ----------
    cfg : Dict[str, Any]
        The (text) config block for one checkpoint.
    ctx : int
        Sequence length in tokens.
    tp : int
        Tensor-parallel degree; KV heads replicate when ``tp > n_kv`` for
        non-MLA models, multiplying total KV by ``tp / n_kv``.
    naive : bool
        When True, reproduce the WRONG pre-audit assumption (every layer
        full-context GQA KV) for comparison columns.

    Returns
    -------
    int
        KV bytes across all layers (and all tp shards -- replication makes
        the total exceed the tp=1 figure, it never shrinks it).
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
    from smolbench.evals.ec2 import EC2_DEPLOY_SPECS

    raw = json.loads(_CONFIGS.read_text())
    gib = 1e9  # decimal GB, matching the 2026-08-13 audit tables
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
