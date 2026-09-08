"""Pin roster KV@131k figures from ``arch_configs_raw.json``."""

from __future__ import annotations

import json

import pytest

from tests._paths import SCRIPTS, load_by_path

load_by_path("kv_budget", SCRIPTS / "arch" / "kv_budget.py")

from kv_budget import (  # noqa: E402
    kv_bytes, _is_shared_latent, _kv_layers, _layer_kv_shape, _layer_mix,
    _replication, _text_config,
)

RAW = json.loads((SCRIPTS / "arch" / "arch_configs_raw.json").read_text())
CTX = 131072
GB = 1e9


def _kv_gb(model: str, tp: int = 1, naive: bool = False) -> float:
    return kv_bytes(_text_config(RAW[model]), CTX, tp=tp, naive=naive) / GB


# Naive figures bill full-context GQA; corrected figures apply cache geometry.
AUDIT_TABLE = {
    "gemma-4-31b": (128.85, 11.58),
    "gemma-4-12b": (51.54, 2.48),
    "gemma-4-e2b": (4.70, 0.81),
    "glm-4.7-flash": (50.27, 7.10),
    "qwen3.5-27b": (34.36, 8.59),
    "exaone-4.0-32b": (34.36, 9.40),
    "exaone-4.5-33b": (34.36, 9.40),
    "deepseek-v3.1": (229.24, 9.21),
    "nemotron-3-nano-4b": (22.55, 2.15),
    "nemotron-3-nano-30b-a3b": (6.98, 0.81),
    "nemotron-3-super-120b-a12b": (11.81, 1.07),
    "deepseek-v4-pro": (16.37, 9.21),
    "deepseek-v4-flash": (11.54, 6.49),
}


@pytest.mark.parametrize("model,expected", AUDIT_TABLE.items())
def test_kv_matches_the_audit(model: str, expected: tuple[float, float]) -> None:
    """Corrected and naive figures both, so the layer mix stays pinned."""
    naive_gb, actual_gb = expected
    assert _kv_gb(model) == pytest.approx(actual_gb, abs=0.02)
    assert _kv_gb(model, naive=True) == pytest.approx(naive_gb, rel=0.005)


@pytest.mark.parametrize(
    "model,attention_layers",
    [
        ("nemotron-3-nano-4b", 4),
        ("nemotron-3-nano-30b-a3b", 6),
        ("nemotron-3-super-120b-a12b", 8),
    ],
)
def test_hybrid_pattern_bills_only_attention_layers(
    model: str, attention_layers: int
) -> None:
    """Mamba-2 and MLP/MoE layers of the NemotronH stack hold no KV."""
    cfg = _text_config(RAW[model])
    pattern = cfg["hybrid_override_pattern"]
    assert len(pattern) == cfg["num_hidden_layers"]
    assert pattern.count("*") == attention_layers
    assert _kv_layers(cfg).count("full") == attention_layers
    # Uniform geometry, so the correction is exactly the attention-layer share.
    assert _kv_gb(model) == pytest.approx(
        _kv_gb(model, naive=True) * attention_layers / cfg["num_hidden_layers"],
        rel=1e-6,
    )


def test_gemma_global_layers_use_their_own_head_geometry() -> None:
    """Global layers cache global_head_dim rows over num_global_key_value_heads."""
    cfg = _text_config(RAW["gemma-4-12b"])
    assert _layer_kv_shape(cfg, "sliding") == (8, 256)
    assert _layer_kv_shape(cfg, "full") == (1, 512)
    # E2B leaves num_global_key_value_heads null: fall back to num_key_value_heads.
    e2b = _text_config(RAW["gemma-4-e2b"])
    assert e2b["num_global_key_value_heads"] is None
    assert _layer_kv_shape(e2b, "full") == (1, 512)
    # ...and its last 20 of 35 layers share KV, so 15 layers allocate.
    assert _kv_layers(e2b).count("none") == 20
    assert _kv_layers(e2b).count("sliding") == 12
    assert _kv_layers(e2b).count("full") == 3


def test_replication_is_per_layer() -> None:
    """tp=4 replicates Gemma-4-12B's 1-head global layers, not its 8-head sliding ones."""
    sliding = 40 * 2 * 8 * 256 * 2 * 1024 / GB  # 0.336 GB, n_kv 8 >= tp
    global_ = 8 * 2 * 1 * 512 * 2 * CTX / GB  # 2.147 GB, n_kv 1 -> x4
    assert _kv_gb("gemma-4-12b", tp=4) == pytest.approx(sliding + 4 * global_, rel=1e-6)


def test_tp_and_attention_kind() -> None:
    """Neither one-row-per-token mechanism replicates across tp; asserted on the mechanism, not a re-tuned number."""
    pro = _text_config(RAW["deepseek-v4-pro"])
    # V4 is detected as a shared latent by both readings the tool accepts.
    assert pro["model_type"] == "deepseek_v4"
    assert pro["num_key_value_heads"] == 1 and pro["qk_rope_head_dim"] == 64
    assert "kv_lora_rank" not in pro
    assert _is_shared_latent(pro)
    # ...so one row per token per layer is billed, and nothing per-head is left
    # for tp=8 to replicate.
    assert _kv_gb("deepseek-v4-pro") == pytest.approx(
        61 * (512 + 64) * 2 * CTX / GB, rel=1e-9)
    assert _kv_gb("deepseek-v4-pro", tp=8) == _kv_gb("deepseek-v4-pro", tp=1)
    assert _replication(pro, 8) == 1.0

    # MLA is the same one-row shape keyed on a different field, and must not
    # be claimed by the shared-latent predicate.
    v31 = _text_config(RAW["deepseek-v3.1"])
    assert v31["kv_lora_rank"] == 512 and not _is_shared_latent(v31)
    assert _kv_gb("deepseek-v3.1", tp=8) == _kv_gb("deepseek-v3.1", tp=1)

    # sliding_window=128 without layer_types is the CSA/HCA scheme, not a
    # window: every layer still bills full context.
    assert pro.get("sliding_window") == 128 and not pro.get("layer_types")
    assert set(_layer_mix(pro)) == {"full"}
    assert len(_kv_layers(pro)) == pro["num_hidden_layers"] == 61


def test_shared_latent_predicate_does_not_steal_mla_or_gqa() -> None:
    """The predicate must claim exactly the two V4 rungs across the whole roster."""
    claimed = {m for m in RAW if _is_shared_latent(_text_config(RAW[m]))}
    assert claimed == {"deepseek-v4-pro", "deepseek-v4-flash"}
