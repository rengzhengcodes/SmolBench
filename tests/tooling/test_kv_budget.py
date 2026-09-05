"""Pin ``scripts/arch/kv_budget.py``'s corrected KV@131k figures for the roster.

Every expected value below was hand-derived from ``arch_configs_raw.json`` --
the arithmetic is written out per row as ``layers x kv_heads x head_dim x 2
(K,V) x 2 bytes (BF16) x context`` -- and only then compared against the tool.
"""

from __future__ import annotations

import json
import sys

import pytest

from tests._paths import SCRIPTS

sys.path.insert(0, str(SCRIPTS / "arch"))

from kv_budget import (  # noqa: E402
    kv_bytes, _is_shared_latent, _kv_layers, _layer_kv_shape, _layer_mix,
    _replication, _text_config,
)

RAW = json.loads((SCRIPTS / "arch" / "arch_configs_raw.json").read_text())
CTX = 131072
GB = 1e9


def _kv_gb(model: str, tp: int = 1, naive: bool = False) -> float:
    return kv_bytes(_text_config(RAW[model]), CTX, tp=tp, naive=naive) / GB


# The audit's headline corrections (naive GB, corrected GB) at 131,072 tokens, tp=1.
#
# Naive = every layer holds full-context KV at the model-level head geometry:
#   num_hidden_layers x 2(K,V) x num_key_value_heads x head_dim x 2B x 131072.
#
# gemma-4-31b   n_kv 16, head_dim 256, global_head_dim 512,
#               num_global_key_value_heads 4, 60 layers = 50 sliding@1024 + 10 full
#   naive   60 x 2x16x256 x2B x131072       = 60 x 2.147e9   = 128.85 GB
#   sliding 50 x 2x16x256 x2B x  1024       = 50 x 16.777e6  =   0.839 GB
#   global  10 x 2x 4x512 x2B x131072       = 10 x 1.0737e9  =  10.737 GB -> 11.58
# gemma-4-12b   n_kv 8, head_dim 256, global_head_dim 512,
#               num_global_key_value_heads 1, 48 layers = 40 sliding@1024 + 8 full
#   naive   48 x 2x8x256 x2B x131072        = 48 x 1.0737e9  =  51.54 GB
#   sliding 40 x 2x8x256 x2B x  1024        = 40 x 8.389e6   =   0.336 GB
#   global   8 x 2x1x512 x2B x131072        =  8 x 268.4e6   =   2.147 GB ->  2.48
# gemma-4-e2b   n_kv 1, head_dim 256, global_head_dim 512,
#               num_global_key_value_heads null -> falls back to n_kv 1,
#               35 layers = 28 sliding@512 + 7 full, num_kv_shared_layers 20 so
#               only layers 0-14 allocate: layer_types full at 4, 9, 14
#               -> 12 sliding + 3 global
#   naive   35 x 2x1x256 x2B x131072        = 35 x 134.2e6   =   4.70 GB
#   sliding 12 x 2x1x256 x2B x   512        = 12 x 524288    =   0.006 GB
#   global   3 x 2x1x512 x2B x131072        =  3 x 268.4e6   =   0.805 GB ->  0.81
# glm-4.7-flash MLA: no head_dim field, so naive falls back to
#               hidden 2048 // 20 heads = 102 (floor), n_kv 20, 47 layers
#   naive   47 x 2x20x102 x2B x131072       = 47 x 1.0695e9  =  50.27 GB
#   MLA     47 x (kv_lora 512 + qk_rope 64) x2B x131072 = 47 x 150.99e6 = 7.10
# qwen3.5-27b   n_kv 4, head_dim 256, 64 layers = 48 linear + 16 full
#   naive   64 x 2x4x256 x2B x131072        = 64 x 536.9e6   =  34.36 GB
#   full    16 x 536.9e6                                     =   8.59 GB
# exaone-4.0-32b / exaone-4.5-33b  n_kv 8, head_dim 128 (4.5 has no head_dim
#               field: hidden 5120 // 40 heads = 128), 64 layers,
#               sliding_window_pattern LLLG -> 48 sliding@4096 + 16 full
#   naive   64 x 2x8x128 x2B x131072        = 64 x 536.9e6   =  34.36 GB
#   sliding 48 x 2x8x128 x2B x  4096        = 48 x 16.777e6  =   0.805 GB
#   full    16 x 536.9e6                                     =   8.59 GB ->  9.40
# deepseek-v3.1 MLA: no head_dim field -> 7168 // 128 heads = 56, n_kv 128,
#               61 layers
#   naive   61 x 2x128x56 x2B x131072       = 61 x 3.758e9   = 229.24 GB
#   MLA     61 x (512 + 64) x2B x131072     = 61 x 150.99e6  =   9.21 GB
# nemotron-3-nano-4b  n_kv 8, head_dim 128, 42 layers; hybrid_override_pattern
#               'M-M-M-MM-M-M*-M-M*-M-M-M*-M-M-MM*-MMM-M-M-' = 21 M + 17 '-'
#               + 4 '*', and only the 4 attention layers hold KV
#   naive   42 x 2x8x128 x2B x131072        = 42 x 536.9e6   =  22.55 GB
#   attn     4 x 536.9e6                                     =   2.15 GB
# nemotron-3-nano-30b-a3b  n_kv 2, head_dim 128, 52 layers; pattern = 23 M +
#               23 E + 6 '*'
#   naive   52 x 2x2x128 x2B x131072        = 52 x 134.2e6   =   6.98 GB
#   attn     6 x 134.2e6                                     =   0.81 GB
# nemotron-3-super-120b-a12b  n_kv 2, head_dim 128, 88 layers; pattern = 40 M +
#               40 E + 8 '*'
#   naive   88 x 2x2x128 x2B x131072        = 88 x 134.2e6   =  11.81 GB
#   attn     8 x 134.2e6                                     =   1.07 GB
# deepseek-v4-pro / -flash  SHARED LATENT (no kv_lora_rank field): one
#               head_dim 512 + qk_rope 64 = 576-wide row per token per layer,
#               shared by K and V, so no x2 and no tp replication. n_kv 1,
#               head_dim 512; 61 layers (pro) / 43 layers (flash).
#   latent  per layer per token (512 + 64) x2B             = 1152 B
#           x131072                                        = 150.99e6
#   pro     61 x 150.99e6                                  =   9.21 GB
#   flash   43 x 150.99e6                                  =   6.49 GB
#   naive   per layer per token 2x1x512 x2B                = 2048 B
#           x131072                                        = 268.44e6
#   pro     61 x 268.44e6                                  =  16.37 GB
#   flash   43 x 268.44e6                                  =  11.54 GB
#   (pro's 9.21 GB coinciding with deepseek-v3.1's is arithmetic, not a
#    copy-paste: both are 61 layers x 576 dims x 2B x ctx -- V3.1 as
#    kv_lora_rank 512 + rope 64, V4 as head_dim 512 + rope 64.)
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
def test_kv_matches_the_audit(model, expected):
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
def test_hybrid_pattern_bills_only_attention_layers(model, attention_layers):
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


def test_gemma_global_layers_use_their_own_head_geometry():
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


def test_replication_is_per_layer():
    """tp=4 replicates Gemma-4-12B's 1-head global layers, not its 8-head sliding ones."""
    sliding = 40 * 2 * 8 * 256 * 2 * 1024 / GB  # 0.336 GB, n_kv 8 >= tp
    global_ = 8 * 2 * 1 * 512 * 2 * CTX / GB  # 2.147 GB, n_kv 1 -> x4
    assert _kv_gb("gemma-4-12b", tp=4) == pytest.approx(sliding + 4 * global_, rel=1e-6)


def test_tp_and_attention_kind():
    """Neither one-row-per-token mechanism replicates across tp; a bare window is not applied.

    Rewritten for the DeepSeek-V4 fix: this test used to assert that
    ``kv(tp=8) == 8 * kv(tp=1)`` for deepseek-v4-pro and that its corrected
    figure equalled its naive one. Both held only because V4 fell through to
    the GQA path -- the very defect. They are replaced here by assertions on
    the MECHANISM that decides the arithmetic, so a future regression that
    re-routes V4 to GQA fails on the reason, not on a re-tuned number.
    """
    pro = _text_config(RAW["deepseek-v4-pro"])
    # V4 is detected as a shared latent by BOTH readings the tool accepts.
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

    # MLA is the same one-row shape keyed on a different field, and must NOT be
    # claimed by the shared-latent predicate.
    v31 = _text_config(RAW["deepseek-v3.1"])
    assert v31["kv_lora_rank"] == 512 and not _is_shared_latent(v31)
    assert _kv_gb("deepseek-v3.1", tp=8) == _kv_gb("deepseek-v3.1", tp=1)

    # sliding_window=128 without layer_types is the CSA/HCA scheme, not a
    # window: every layer still bills full context.
    assert pro.get("sliding_window") == 128 and not pro.get("layer_types")
    assert set(_layer_mix(pro)) == {"full"}
    assert len(_kv_layers(pro)) == pro["num_hidden_layers"] == 61


def test_shared_latent_predicate_does_not_steal_mla_or_gqa():
    """The predicate must claim exactly the two V4 rungs across the whole roster."""
    claimed = {m for m in RAW if _is_shared_latent(_text_config(RAW[m]))}
    assert claimed == {"deepseek-v4-pro", "deepseek-v4-flash"}
