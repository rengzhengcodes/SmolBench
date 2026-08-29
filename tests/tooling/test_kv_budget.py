"""Pin ``scripts/arch/kv_budget.py``'s corrected KV@131k figures for the roster.

Each expected value below was derived independently of the tool.
"""

from __future__ import annotations

import json
import sys

import pytest

from tests._paths import SCRIPTS

sys.path.insert(0, str(SCRIPTS / "arch"))

from kv_budget import kv_bytes, _text_config  # noqa: E402

RAW = json.loads((SCRIPTS / "arch" / "arch_configs_raw.json").read_text())
CTX = 131072
GB = 1e9


def _kv_gb(model: str, tp: int = 1, naive: bool = False) -> float:
    return kv_bytes(_text_config(RAW[model]), CTX, tp=tp, naive=naive) / GB


# The audit's headline corrections (naive GB, corrected GB) at 131,072 tokens, tp=1.
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
def test_kv_matches_the_audit(model, expected):
    """Corrected and naive figures both, so the layer mix stays pinned."""
    naive_gb, actual_gb = expected
    assert _kv_gb(model) == pytest.approx(actual_gb, abs=0.1)
    assert _kv_gb(model, naive=True) == pytest.approx(naive_gb, rel=0.02)


def test_tp_and_attention_kind():
    """MQA replicates KV across tp; MLA does not; a bare window is not applied."""
    # DeepSeek-V4-Pro has one KV head: tp=8 replicates its KV 8x.
    assert _kv_gb("deepseek-v4-pro", tp=8) == pytest.approx(
        8 * _kv_gb("deepseek-v4-pro", tp=1), rel=1e-6)
    # MLA caches one shared latent: there are no KV heads to replicate.
    assert _kv_gb("deepseek-v3.1", tp=8) == _kv_gb("deepseek-v3.1", tp=1)
    # sliding_window=128 without layer_types is the CSA/HCA scheme, not a window.
    cfg = _text_config(RAW["deepseek-v4-pro"])
    assert cfg.get("sliding_window") and not cfg.get("layer_types")
    assert _kv_gb("deepseek-v4-pro") == pytest.approx(
        _kv_gb("deepseek-v4-pro", naive=True), rel=1e-6)
