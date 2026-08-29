"""Statically lint the family-ladder EC2_DEPLOY_SPECS roster.

Ground truth is ``tests/fixtures/roster_configs.json`` (head counts, context
windows, architectures vendored from each repo's config.json on 2026-08-11);
re-vendor a row when its rung is swapped.
"""

from __future__ import annotations

import inspect
import json
import logging
import re
from collections import Counter

import pytest

from smolbench.evals.providers import ec2
from smolbench.evals.providers.ec2 import (
    DETERMINISM_ARGS,
    DSV4_CHAT_TEMPLATE,
    EC2_DEPLOY_SPECS,
    MINISTRAL_THINK_SYSTEM,
    MODEL_ATTENTION_HEADS,
    derive_tp,
)

from tests._paths import FIXTURES

#: All 22 deploy-spec keys (21 study rungs plus the qwen2.5-1.5b canary). The
#: determinism-bundle tests below cover every entry, unlike STUDY_KEYS
#: (which excludes the canary): the loop in ec2.py that appends
#: DETERMINISM_ARGS runs over EC2_DEPLOY_SPECS.items() unconditionally.
ALL_KEYS = sorted(EC2_DEPLOY_SPECS)

#: A flag that appears exactly once, followed by a 40-char lowercase hex
#: SHA. This matches both git commit hashes and, by construction, nothing
#: else in any spec's vllm_args. So this also checks the hinge/plan table's
#: transcription into EC2_DEPLOY_SPECS.
_SHA40 = re.compile(r"[0-9a-f]{40}")

ROSTER = json.loads((FIXTURES / "roster_configs.json").read_text())

# The smoke entry predates the study and serves at 16k on a single small
# GPU. Every other spec is a counted study rung and must obey the study
# invariants.
STUDY_KEYS = sorted(set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"})

# vLLM reasoning-parser registry names, vendored from
# vllm/reasoning/__init__.py @ main, 2026-08-11.
KNOWN_PARSERS = {
    "deepseek_r1", "deepseek_v3", "deepseek_v4",
    "gemma4", "glm45", "glm47",
    "mistral", "nemotron_v3", "openai_gptoss", "qwen3",
}


def _args(spec):
    return list(spec.get("vllm_args") or [])


def _flag_value(args, flag):
    return args[args.index(flag) + 1] if flag in args else None


def test_roster_and_study_shape():
    assert sorted(ROSTER) == STUDY_KEYS
    assert len(STUDY_KEYS) == 21
    assert set(MODEL_ATTENTION_HEADS) == set(STUDY_KEYS)


@pytest.mark.parametrize("key", ALL_KEYS)
def test_spec_invariants(key):
    """Determinism bundle, revision pins and general well-formedness, canary included."""
    args = _args(EC2_DEPLOY_SPECS[key])

    n = len(DETERMINISM_ARGS)
    assert args[-n:] == DETERMINISM_ARGS, f"{key}: DETERMINISM_ARGS is not a trailing suffix of {args}"

    assert "--enable-prefix-caching" not in args, f"{key}: prefix caching must stay off"

    for flag in ("--revision", "--tokenizer-revision"):
        assert args.count(flag) == 1, f"{key}: {flag} must appear exactly once, found {args.count(flag)}"
    revision = _flag_value(args, "--revision")
    tokenizer_revision = _flag_value(args, "--tokenizer-revision")
    assert _SHA40.fullmatch(revision), f"{key}: --revision {revision!r} is not a 40-char lowercase hex SHA"
    assert _SHA40.fullmatch(tokenizer_revision), f"{key}: bad --tokenizer-revision {tokenizer_revision!r}"
    assert revision == tokenizer_revision, f"{key}: {revision!r} != {tokenizer_revision!r}"

    assert args.count("--gpu-memory-utilization") == 1, f"{key}: --gpu-memory-utilization once"
    value = _flag_value(args, "--gpu-memory-utilization")
    assert value in {"0.92", "0.93"}, f"{key}: unexpected --gpu-memory-utilization {value!r}"

    repeats = {f: n for f, n in Counter(a for a in args if a.startswith("--")).items() if n > 1}
    assert not repeats, f"{key}: flag(s) repeated in vllm_args: {repeats}"

    # S3 key component + --served-model-name + state-file suffix.
    assert re.fullmatch(r"[a-z0-9][a-z0-9.\-]*", key), f"unsafe spec key {key!r}"


@pytest.mark.parametrize("key", STUDY_KEYS)
def test_study_spec_matches_roster(key):
    """Every study rung agrees with its vendored config.json row."""
    spec, facts = EC2_DEPLOY_SPECS[key], ROSTER[key]
    args = _args(spec)

    tp = spec.get("tp", 1)
    heads = facts["num_attention_heads"]
    assert heads % tp == 0, f"{key}: tp={tp} does not divide {heads} attention heads"
    kv = facts["num_key_value_heads"]
    if kv is not None:
        # vLLM replicates KV heads when tp > n_kv. Either direction must divide.
        assert kv % tp == 0 or tp % kv == 0, f"{key}: tp={tp} vs kv={kv}"
    for lin in ("linear_num_key_heads", "linear_num_value_heads"):
        if facts.get(lin) is not None:
            assert facts[lin] % tp == 0, f"{key}: tp={tp} does not divide {lin}={facts[lin]}"

    assert spec["max_model_len"] == 131072, f"{key}: study context is uniform 131072"
    assert spec["max_model_len"] <= facts["native_max_len"], (
        f"{key}: max_model_len exceeds shipped context {facts['native_max_len']}"
    )

    parser = _flag_value(args, "--reasoning-parser")
    if parser is not None:
        assert parser in KNOWN_PARSERS, f"{key}: unknown reasoning parser {parser!r}"

    is_mm = facts["architecture"].endswith("ForConditionalGeneration")
    assert ("--language-model-only" in args) == is_mm, (
        f"{key}: --language-model-only must be set iff multimodal ({facts['architecture']})"
    )

    assert "--trust-remote-code" not in args, f"{key}: every roster arch is in-tree upstream"
    assert spec["hf_model_id"] == facts["repo"], key
    assert MODEL_ATTENTION_HEADS[key] == facts["num_attention_heads"], key


def test_ec2_vllm_image_default_is_digest_pinned():
    """Reads the source so an env override cannot mask a drift back to a mutable tag."""
    source = inspect.getsource(ec2)
    match = re.search(r'os\.getenv\("EC2_VLLM_IMAGE",\s*"([^"]+)"', source)
    assert match, 'no os.getenv("EC2_VLLM_IMAGE", "...") default found in ec2.py'
    assert re.fullmatch(r"vllm/vllm-openai@sha256:[0-9a-f]{64}", match.group(1)), (
        f"EC2_VLLM_IMAGE default {match.group(1)!r} is not a digest pin "
        "(vllm/vllm-openai@sha256:<64 hex>) -- do not repoint it at a mutable tag"
    )


def test_deepseek_v4_rows_carry_the_inline_template_and_parser():
    for key in ("deepseek-v4-flash", "deepseek-v4-pro"):
        args = _args(EC2_DEPLOY_SPECS[key])
        assert _flag_value(args, "--chat-template") == DSV4_CHAT_TEMPLATE, key
        assert _flag_value(args, "--reasoning-parser") == "deepseek_v4", key
    # V3.1 ships its own template; overriding it would discard the vendor's
    # tool-call and multi-turn handling for no gain.
    assert "--chat-template" not in _args(EC2_DEPLOY_SPECS["deepseek-v3.1"])


def test_ministral_rows_carry_the_think_protocol_system_prompt():
    for key in ("ministral-3-3b", "ministral-3-8b", "ministral-3-14b"):
        assert EC2_DEPLOY_SPECS[key].get("system_prompt") == MINISTRAL_THINK_SYSTEM, key
        # --tokenizer-mode mistral would bypass the Jinja template that
        # injects the think protocol when no system message arrives.
        assert "--tokenizer-mode" not in _args(EC2_DEPLOY_SPECS[key]), key
    for key in STUDY_KEYS:
        if not key.startswith("ministral"):
            assert "system_prompt" not in EC2_DEPLOY_SPECS[key], key


@pytest.mark.parametrize(
    "model,instance_type,spec,expected",
    [
        # Use every GPU the hunt paid for when head divisibility allows.
        ("ministral-3-3b", "g6e.12xlarge", None, 4),
        ("nemotron-3-nano-4b", "g6e.12xlarge", None, 4),
        ("nemotron-3-nano-4b", "g6e.4xlarge", None, 1),
        # 20 heads cannot shard 8 ways; the largest common divisor is 4.
        ("glm-4.7-flash", "p5.48xlarge", None, 4),
        ("glm-4.7-flash", "g6e.12xlarge", None, 4),
        # The in-flight lanes' derived tp equals their previous static pin.
        ("gemma-4-12b", "g6e.12xlarge", None, 4),
        ("ministral-3-14b", "g6e.12xlarge", None, 4),
        ("deepseek-v4-pro", "p6-b200.48xlarge", None, 8),
        ("deepseek-v4-flash", "p6-b200.48xlarge", None, 8),
        # Fall back to the spec pin: unknown model, unknown type, no pin.
        ("qwen2.5-1.5b", "g6e.12xlarge", {"tp": 1}, 1),
        ("gemma-4-12b", "g9.99xlarge", {"tp": 4}, 4),
        ("qwen2.5-1.5b", "mystery.large", {}, 1),
        # g7.12xlarge carries two GPUs, not four like g6e.12xlarge. Every g7
        # size must be mapped, or a lane spanning sizes changes tp mid-lane.
        ("gemma-4-12b", "g7.12xlarge", None, 2),
        ("exaone-4.5-33b", "g7e.2xlarge", None, 1),
        ("ministral-3-14b", "g7.24xlarge", None, 4),
        ("ministral-3-14b", "g7.48xlarge", None, 8),
        ("gemma-4-12b", "g7.24xlarge", None, 4),
        ("gemma-4-12b", "p5.4xlarge", None, 1),
        ("ministral-3-14b", "g7e.12xlarge", None, 2),
    ],
)
def test_derive_tp(model, instance_type, spec, expected):
    if spec is None:
        spec = EC2_DEPLOY_SPECS[model]
    assert derive_tp(model, instance_type, spec) == expected


def test_derive_tp_unknown_type_fallback_warns_for_known_model(caplog):
    with caplog.at_level(logging.WARNING):
        assert derive_tp("gemma-4-12b", "g9.99xlarge", {"tp": 4}) == 4
    assert any("not in _INSTANCE_GPU_COUNTS" in r.message for r in caplog.records)
    # Unknown MODEL on a known type stays a silent, by-design fallback.
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        assert derive_tp("qwen2.5-1.5b", "g6e.12xlarge", {"tp": 1}) == 1
    assert not caplog.records


def test_hardware_pin_blocks_a_gpu_swap_but_allows_a_size_swap(monkeypatch):
    """EC2_REQUIRE_GPU pins the silicon, not the instance size."""
    monkeypatch.setattr(ec2, "EC2_REQUIRE_GPU", "L40S:1")

    # Same silicon, different size: the accepted substitution.
    ec2._assert_required_gpu({"instance_type": "g6e.2xlarge"}, "ministral-3-3b")
    ec2._assert_required_gpu({"instance_type": "g6e.4xlarge"}, "ministral-3-3b")

    # Same family, four GPUs: this would silently change tp.
    with pytest.raises(RuntimeError, match="hardware pin violated"):
        ec2._assert_required_gpu({"instance_type": "g6e.12xlarge"}, "ministral-3-3b")

    # Different silicon entirely.
    with pytest.raises(RuntimeError, match="hardware pin violated"):
        ec2._assert_required_gpu({"instance_type": "g7.4xlarge"}, "ministral-3-3b")

    # Unknown type is reported, never treated as a match.
    with pytest.raises(RuntimeError, match="not in this module's GPU tables"):
        ec2._assert_required_gpu({"instance_type": "zz9.42xlarge"}, "ministral-3-3b")

    # Unset pin is a no-op: every existing lane keeps working unchanged.
    monkeypatch.setattr(ec2, "EC2_REQUIRE_GPU", "")
    ec2._assert_required_gpu({"instance_type": "g6e.12xlarge"}, "ministral-3-3b")
