"""Static lint of the family-ladder EC2_DEPLOY_SPECS roster.

Every check here guards a failure mode that would otherwise surface only on a
live multi-GPU box at $20-25/hour:

* ``tp`` must shard the checkpoint's real head counts (GLM-4.7-Flash has 20
  attention heads, so tp=8 crashes vLLM at startup -- the trap that motivated
  this file);
* ``max_model_len`` must not exceed the shipped config's context window (a
  card claim is not a config value);
* every ``--reasoning-parser`` must exist in vLLM's parser registry (a typo'd
  parser name is a startup crash);
* ``--language-model-only`` belongs on exactly the multimodal wrappers
  (``*ForConditionalGeneration``) -- on a ``*ForCausalLM`` it is an unknown-
  model-surgery no-op at best;
* spec keys become S3 result-key components and ``--served-model-name``s, so
  they must stay path/URL-safe.

Ground truth lives in ``tests/fixtures/roster_configs.json`` -- head counts,
context windows, and architecture strings vendored from each repo's shipped
``config.json`` on 2026-08-11. When a rung is swapped, re-vendor its row.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from smolbench.evals.ec2 import DSV4_CHAT_TEMPLATE, EC2_DEPLOY_SPECS

ROSTER = json.loads(
    (Path(__file__).parent / "fixtures" / "roster_configs.json").read_text()
)

# The smoke entry predates the study and serves at 16k on a single small GPU;
# every other spec is a counted study rung and must obey the study invariants.
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


def test_roster_fixture_covers_exactly_the_study_specs():
    assert sorted(ROSTER) == STUDY_KEYS


def test_study_is_seven_families_of_three():
    assert len(STUDY_KEYS) == 21


@pytest.mark.parametrize("key", STUDY_KEYS)
def test_tp_shards_the_real_head_counts(key):
    spec, facts = EC2_DEPLOY_SPECS[key], ROSTER[key]
    tp = spec.get("tp", 1)
    heads = facts["num_attention_heads"]
    assert heads % tp == 0, f"{key}: tp={tp} does not divide {heads} attention heads"
    kv = facts["num_key_value_heads"]
    if kv is not None:
        # vLLM replicates KV heads when tp > n_kv; either direction must divide.
        assert kv % tp == 0 or tp % kv == 0, f"{key}: tp={tp} vs kv={kv}"
    for lin in ("linear_num_key_heads", "linear_num_value_heads"):
        if facts.get(lin) is not None:
            assert facts[lin] % tp == 0, f"{key}: tp={tp} does not divide {lin}={facts[lin]}"


@pytest.mark.parametrize("key", STUDY_KEYS)
def test_max_model_len_within_shipped_context(key):
    spec, facts = EC2_DEPLOY_SPECS[key], ROSTER[key]
    assert spec["max_model_len"] == 131072, f"{key}: study context is uniform 131072"
    assert spec["max_model_len"] <= facts["native_max_len"], (
        f"{key}: max_model_len {spec['max_model_len']} exceeds shipped "
        f"context {facts['native_max_len']}"
    )


@pytest.mark.parametrize("key", STUDY_KEYS)
def test_reasoning_parser_names_exist(key):
    parser = _flag_value(_args(EC2_DEPLOY_SPECS[key]), "--reasoning-parser")
    if parser is not None:
        assert parser in KNOWN_PARSERS, f"{key}: unknown reasoning parser {parser!r}"


@pytest.mark.parametrize("key", STUDY_KEYS)
def test_language_model_only_iff_multimodal_wrapper(key):
    args = _args(EC2_DEPLOY_SPECS[key])
    is_mm = ROSTER[key]["architecture"].endswith("ForConditionalGeneration")
    assert ("--language-model-only" in args) == is_mm, (
        f"{key}: --language-model-only "
        f"{'missing on multimodal wrapper' if is_mm else 'set on a text-only arch'} "
        f"({ROSTER[key]['architecture']})"
    )


@pytest.mark.parametrize("key", STUDY_KEYS)
def test_prefix_caching_on_every_study_spec(key):
    assert "--enable-prefix-caching" in _args(EC2_DEPLOY_SPECS[key]), (
        f"{key}: both evals reuse long prompt prefixes; caching is part of the design"
    )


@pytest.mark.parametrize("key", STUDY_KEYS)
def test_no_trust_remote_code_anywhere(key):
    assert "--trust-remote-code" not in _args(EC2_DEPLOY_SPECS[key]), (
        f"{key}: every roster arch is in-tree upstream; remote code is not part of the study"
    )


@pytest.mark.parametrize("key", sorted(EC2_DEPLOY_SPECS))
def test_spec_keys_are_key_safe(key):
    # S3 key component + --served-model-name + state-file suffix.
    assert re.fullmatch(r"[a-z0-9][a-z0-9.\-]*", key), f"unsafe spec key {key!r}"


def test_deepseek_v4_rows_carry_the_inline_template_and_parser():
    for key in ("deepseek-v4-flash", "deepseek-v4-pro"):
        args = _args(EC2_DEPLOY_SPECS[key])
        assert _flag_value(args, "--chat-template") == DSV4_CHAT_TEMPLATE, key
        assert _flag_value(args, "--reasoning-parser") == "deepseek_v4", key
    # V3.1 ships its own template: overriding it would discard the vendor's
    # tool-call and multi-turn handling for no gain.
    assert "--chat-template" not in _args(EC2_DEPLOY_SPECS["deepseek-v3.1"])


def test_ministral_rows_carry_the_think_protocol_system_prompt():
    from smolbench.evals.ec2 import MINISTRAL_THINK_SYSTEM

    for key in ("ministral-3-3b", "ministral-3-8b", "ministral-3-14b"):
        assert EC2_DEPLOY_SPECS[key].get("system_prompt") == MINISTRAL_THINK_SYSTEM, key
        # The template injects the think protocol only when NO system message
        # arrives; --tokenizer-mode mistral would bypass the Jinja template and
        # defeat the workaround.
        assert "--tokenizer-mode" not in _args(EC2_DEPLOY_SPECS[key]), key
    # No other spec injects a provider system prompt in this study.
    for key in STUDY_KEYS:
        if not key.startswith("ministral"):
            assert "system_prompt" not in EC2_DEPLOY_SPECS[key], key


def test_hf_model_ids_match_the_vendored_roster():
    for key in STUDY_KEYS:
        assert EC2_DEPLOY_SPECS[key]["hf_model_id"] == ROSTER[key]["repo"], key


# ---------------------------------------------------------------------------
# derive_tp (2026-08-13 fleet audit): tp comes from the landed box, not a pin
# ---------------------------------------------------------------------------


def test_model_attention_heads_match_the_vendored_roster():
    from smolbench.evals.ec2 import MODEL_ATTENTION_HEADS

    assert set(MODEL_ATTENTION_HEADS) == set(STUDY_KEYS)
    for key in STUDY_KEYS:
        assert MODEL_ATTENTION_HEADS[key] == ROSTER[key]["num_attention_heads"], key


@pytest.mark.parametrize(
    "model,instance_type,expected",
    [
        # Uses every GPU the hunt paid for when head divisibility allows: a
        # tp=1 spec landing on a 4-GPU g6e.12xlarge idled 3 of 4 L40S.
        ("ministral-3-3b", "g6e.12xlarge", 4),
        ("nemotron-3-nano-4b", "g6e.12xlarge", 4),
        ("nemotron-3-nano-4b", "g6e.4xlarge", 1),
        # 20 heads cannot shard 8 ways -- the largest common divisor is 4.
        ("glm-4.7-flash", "p5.48xlarge", 4),
        ("glm-4.7-flash", "g6e.12xlarge", 4),
        # The in-flight lanes' derived tp equals their previous static pin
        # (verified before this landed mid-drain).
        ("gemma-4-12b", "g6e.12xlarge", 4),
        ("ministral-3-14b", "g6e.12xlarge", 4),
        ("deepseek-v4-pro", "p6-b200.48xlarge", 8),
        ("deepseek-v4-flash", "p6-b200.48xlarge", 8),
    ],
)
def test_derive_tp_uses_the_landed_gpu_count(model, instance_type, expected):
    from smolbench.evals.ec2 import derive_tp

    assert derive_tp(model, instance_type, EC2_DEPLOY_SPECS[model]) == expected


def test_derive_tp_falls_back_to_the_spec_pin():
    from smolbench.evals.ec2 import derive_tp

    # Unknown model (the canary is deliberately absent from the heads map).
    assert derive_tp("qwen2.5-1.5b", "g6e.12xlarge", {"tp": 1}) == 1
    # Unknown instance type: never guess a GPU count.
    assert derive_tp("gemma-4-12b", "g7e.2xlarge", {"tp": 4}) == 4
    # No pin at all defaults to 1.
    assert derive_tp("qwen2.5-1.5b", "mystery.large", {}) == 1
