"""Pin ``scripts/arch/kv_budget.py`` to the 2026-08-13 fleet audit's table.

Each expected value below was independently derived in the audit (and the
sliding/MLA rows hand-checked again when this tool was written). They are
the corrected KV@131k figures whose divergence from the naive all-full
assumption motivated re-deriving tier assignments for the replication
study. A formula regression here silently re-poisons that sizing.
"""

from __future__ import annotations

import json
import sys

import pytest

from tests._paths import SCRIPTS

sys.path.insert(0, str(SCRIPTS / "arch"))

from kv_budget import kv_bytes, _layer_mix, _text_config  # noqa: E402

RAW = json.loads((SCRIPTS / "arch" / "arch_configs_raw.json").read_text())
CTX = 131072
GB = 1e9


def _kv_gb(model: str, tp: int = 1, naive: bool = False) -> float:
    return kv_bytes(_text_config(RAW[model]), CTX, tp=tp, naive=naive) / GB


# The audit's headline corrections (decimal GB at 131,072 tokens, tp=1).
AUDIT_TABLE = {
    "gemma-4-31b": (128.8, 22.3),
    "gemma-4-12b": (51.5, 8.9),
    "glm-4.7-flash": (50.3, 7.1),
    "qwen3.5-27b": (34.4, 8.6),
    "exaone-4.0-32b": (34.4, 9.4),
    "exaone-4.5-33b": (34.4, 9.4),
    "deepseek-v3.1": (229.2, 9.2),
}


@pytest.mark.parametrize("model,expected", AUDIT_TABLE.items())
def test_corrected_kv_matches_the_audit(model, expected):
    _naive_gb, actual_gb = expected
    assert _kv_gb(model) == pytest.approx(actual_gb, abs=0.1)


@pytest.mark.parametrize("model,expected", AUDIT_TABLE.items())
def test_naive_kv_reproduces_the_wrong_assumption(model, expected):
    naive_gb, _actual_gb = expected
    assert _kv_gb(model, naive=True) == pytest.approx(naive_gb, rel=0.02)


def test_kv_head_replication_scales_with_tp():
    # DeepSeek-V4-Pro has one KV head: tp=8 replicates its KV 8x. This is
    # why the model is genuinely KV-huge despite MQA.
    assert _kv_gb("deepseek-v4-pro", tp=8) == pytest.approx(
        8 * _kv_gb("deepseek-v4-pro", tp=1), rel=1e-6
    )


def test_mla_ignores_tp_replication():
    # MLA caches one shared latent: there are no KV heads to replicate.
    assert _kv_gb("deepseek-v3.1", tp=8) == _kv_gb("deepseek-v3.1", tp=1)


def test_linear_attention_layers_hold_no_ctx_kv():
    cfg = _text_config(RAW["qwen3.5-27b"])
    mix = _layer_mix(cfg)
    assert mix.count("linear") == 48 and len(mix) == 64
    # 16 full layers of 64 -> exactly 16/64 of the naive figure.
    assert _kv_gb("qwen3.5-27b") == pytest.approx(_kv_gb("qwen3.5-27b", naive=True) * 16 / 64)


def test_exaone_lllg_pattern_expands_correctly():
    mix = _layer_mix(_text_config(RAW["exaone-4.0-32b"]))
    # LLLG cycling over 64 layers: 48 local, 16 global, starting L,L,L,G.
    assert mix[:4] == ["sliding", "sliding", "sliding", "full"]
    assert mix.count("sliding") == 48 and mix.count("full") == 16


def test_bare_sliding_window_without_mix_fields_is_not_applied():
    # DeepSeek-V4 carries sliding_window=128 for its CSA/HCA sparse scheme,
    # but has neither layer_types nor sliding_window_pattern. Its KV stays
    # full-length. (If it were treated as windowed, KV would shrink about
    # 1000x and produce boxes that OOM at serve.)
    cfg = _text_config(RAW["deepseek-v4-pro"])
    assert cfg.get("sliding_window") and not cfg.get("layer_types")
    assert _kv_gb("deepseek-v4-pro") == pytest.approx(
        _kv_gb("deepseek-v4-pro", naive=True), rel=1e-6
    )
