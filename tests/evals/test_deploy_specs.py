"""Statically lint the family-ladder EC2_DEPLOY_SPECS roster against
``tests/fixtures/roster_configs.json`` (config.json rows vendored 2026-08-11;
re-vendor a row when its rung is swapped)."""

import inspect
import json
import re
from collections import Counter

import pytest

from smolbench.evals.providers import ec2
from smolbench.evals.providers.ec2 import (
    DETERMINISM_ARGS, DSV4_CHAT_TEMPLATE, EC2_DEPLOY_SPECS, MINISTRAL_THINK_SYSTEM,
    MODEL_ATTENTION_HEADS, derive_tp,
)

from tests._paths import FIXTURES

ROSTER = json.loads((FIXTURES / "roster_configs.json").read_text())
_SHA40 = re.compile(r"[0-9a-f]{40}")

#: The 21 study rungs plus the qwen2.5-1.5b canary, which is exempt from the
#: study invariants but not from the determinism bundle (ec2.py appends that
#: over EC2_DEPLOY_SPECS.items() unconditionally).
ALL_KEYS = sorted(EC2_DEPLOY_SPECS)
STUDY_KEYS = sorted(set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"})

#: vLLM reasoning-parser registry names, vendored from vllm/reasoning/__init__.py.
KNOWN_PARSERS = {"deepseek_r1", "deepseek_v3", "deepseek_v4", "gemma4", "glm45",
                 "glm47", "mistral", "nemotron_v3", "openai_gptoss", "qwen3"}


def _args(spec):
    return list(spec.get("vllm_args") or [])


def _flag_value(args, flag):
    return args[args.index(flag) + 1] if flag in args else None


def test_roster_and_study_shape():
    assert sorted(ROSTER) == STUDY_KEYS == sorted(MODEL_ATTENTION_HEADS) and len(STUDY_KEYS) == 21


@pytest.mark.parametrize("key", ALL_KEYS)
def test_spec_invariants(key):
    """Determinism bundle, revision pins, flag hygiene and a path-safe key (it is
    an S3 key component, a --served-model-name and a state-file suffix)."""
    args = _args(EC2_DEPLOY_SPECS[key])
    assert args[-len(DETERMINISM_ARGS):] == DETERMINISM_ARGS, key
    assert "--enable-prefix-caching" not in args, key
    assert args.count("--revision") == args.count("--tokenizer-revision") == 1, key
    rev, tok = _flag_value(args, "--revision"), _flag_value(args, "--tokenizer-revision")
    assert _SHA40.fullmatch(rev) and _SHA40.fullmatch(tok) and rev == tok, key
    assert args.count("--gpu-memory-utilization") == 1, key
    assert _flag_value(args, "--gpu-memory-utilization") in {"0.92", "0.93"}, key
    assert not {f: n for f, n in Counter(a for a in args if a.startswith("--")).items() if n > 1}
    assert re.fullmatch(r"[a-z0-9][a-z0-9.\-]*", key)


@pytest.mark.parametrize("key", STUDY_KEYS)
def test_study_spec_matches_roster(key):
    """Every study rung agrees with its vendored config.json row."""
    spec, facts = EC2_DEPLOY_SPECS[key], ROSTER[key]
    args, tp, kv = _args(spec), spec.get("tp", 1), facts["num_key_value_heads"]
    # vLLM replicates KV heads when tp > n_kv, so either direction may divide.
    assert facts["num_attention_heads"] % tp == 0, key
    assert kv is None or kv % tp == 0 or tp % kv == 0, key
    for lin in ("linear_num_key_heads", "linear_num_value_heads"):
        assert facts.get(lin) is None or facts[lin] % tp == 0, (key, lin)
    assert spec["max_model_len"] == 131072 <= facts["native_max_len"], key
    parser = _flag_value(args, "--reasoning-parser")
    assert parser is None or parser in KNOWN_PARSERS, key
    is_mm = facts["architecture"].endswith("ForConditionalGeneration")
    assert ("--language-model-only" in args) == is_mm, key
    assert "--trust-remote-code" not in args, key  # every roster arch is in-tree
    assert spec["hf_model_id"] == facts["repo"], key
    assert MODEL_ATTENTION_HEADS[key] == facts["num_attention_heads"], key


def test_ec2_vllm_image_default_is_digest_pinned():
    """Reads the source so an env override cannot mask a drift to a mutable tag."""
    match = re.search(r'os\.getenv\("EC2_VLLM_IMAGE",\s*"([^"]+)"', inspect.getsource(ec2))
    assert match and re.fullmatch(r"vllm/vllm-openai@sha256:[0-9a-f]{64}", match.group(1))


def test_per_family_row_overrides():
    """DSV4 inline template/parser; Ministral think-protocol system prompt."""
    for key in ("deepseek-v4-flash", "deepseek-v4-pro"):
        args = _args(EC2_DEPLOY_SPECS[key])
        assert _flag_value(args, "--chat-template") == DSV4_CHAT_TEMPLATE, key
        assert _flag_value(args, "--reasoning-parser") == "deepseek_v4", key
    # V3.1 ships its own template; overriding it would discard vendor handling.
    assert "--chat-template" not in _args(EC2_DEPLOY_SPECS["deepseek-v3.1"])
    for key in STUDY_KEYS:
        spec = EC2_DEPLOY_SPECS[key]
        if not key.startswith("ministral"):
            assert "system_prompt" not in spec, key
            continue
        assert spec.get("system_prompt") == MINISTRAL_THINK_SYSTEM, key
        # --tokenizer-mode mistral would bypass the think-protocol Jinja template.
        assert "--tokenizer-mode" not in _args(spec), key


@pytest.mark.parametrize(
    "model,instance_type,spec,expected",
    [
        # tp = gcd(heads, landed GPUs): use every GPU the hunt paid for. In-flight
        # lanes match their old static pin; glm-4.7-flash's 20 heads cap tp at 4.
        ("ministral-3-3b", "g6e.12xlarge", None, 4), ("glm-4.7-flash", "p5.48xlarge", None, 4),
        ("nemotron-3-nano-4b", "g6e.12xlarge", None, 4), ("glm-4.7-flash", "g6e.12xlarge", None, 4),
        ("nemotron-3-nano-4b", "g6e.4xlarge", None, 1), ("gemma-4-12b", "g6e.12xlarge", None, 4),
        ("ministral-3-14b", "g6e.12xlarge", None, 4), ("gemma-4-12b", "p5.4xlarge", None, 1),
        ("deepseek-v4-pro", "p6-b200.48xlarge", None, 8),
        ("deepseek-v4-flash", "p6-b200.48xlarge", None, 8),
        # Fall back to the spec pin: unknown model, unknown type, no pin.
        ("qwen2.5-1.5b", "g6e.12xlarge", {"tp": 1}, 1),
        ("qwen2.5-1.5b", "mystery.large", {}, 1), ("gemma-4-12b", "g9.99xlarge", {"tp": 4}, 4),
        # g7.12xlarge has two GPUs, not four like g6e.12xlarge; every g7 size must
        # be mapped or a lane spanning sizes changes tp mid-lane.
        ("gemma-4-12b", "g7.12xlarge", None, 2), ("ministral-3-14b", "g7.24xlarge", None, 4),
        ("exaone-4.5-33b", "g7e.2xlarge", None, 1), ("ministral-3-14b", "g7.48xlarge", None, 8),
        ("gemma-4-12b", "g7.24xlarge", None, 4), ("ministral-3-14b", "g7e.12xlarge", None, 2),
    ],
)
def test_derive_tp(model, instance_type, spec, expected):
    spec = EC2_DEPLOY_SPECS[model] if spec is None else spec
    assert derive_tp(model, instance_type, spec) == expected


def test_hardware_pin_blocks_a_gpu_swap_but_allows_a_size_swap(monkeypatch):
    """EC2_REQUIRE_GPU pins the silicon, not the size: a same-silicon size swap
    is accepted; four same-family GPUs (would change tp), other silicon and an
    unmapped type (reported, never a match) raise."""
    monkeypatch.setattr(ec2, "EC2_REQUIRE_GPU", "L40S:1")
    ec2._assert_required_gpu({"instance_type": "g6e.2xlarge"}, "ministral-3-3b")
    ec2._assert_required_gpu({"instance_type": "g6e.4xlarge"}, "ministral-3-3b")
    for itype in ("g6e.12xlarge", "g7.4xlarge", "zz9.42xlarge"):
        with pytest.raises(RuntimeError):
            ec2._assert_required_gpu({"instance_type": itype}, "ministral-3-3b")
    monkeypatch.setattr(ec2, "EC2_REQUIRE_GPU", "")  # unset pin is a no-op
    ec2._assert_required_gpu({"instance_type": "g6e.12xlarge"}, "ministral-3-3b")
