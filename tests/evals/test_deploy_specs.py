"""Statically lint the family-ladder EC2_DEPLOY_SPECS roster.

Every check here guards a failure mode that would otherwise surface only on
a live multi-GPU box at $20-25/hour:

* ``tp`` must shard the checkpoint's real head counts. GLM-4.7-Flash has 20
  attention heads, so tp=8 crashes vLLM at startup -- the trap that
  motivated this file.
* ``max_model_len`` must not exceed the shipped config's context window. A
  card claim is not a config value.
* Every ``--reasoning-parser`` must exist in vLLM's parser registry. A
  typo'd parser name is a startup crash.
* ``--language-model-only`` belongs on exactly the multimodal wrappers
  (``*ForConditionalGeneration``). On a ``*ForCausalLM`` it is at best an
  unknown-model-surgery no-op.
* Spec keys become S3 result-key components and ``--served-model-name``s,
  so they must stay path/URL-safe.

Ground truth lives in ``tests/fixtures/roster_configs.json``: head counts,
context windows, and architecture strings vendored from each repo's shipped
``config.json`` on 2026-08-11. When a rung is swapped, re-vendor its row.
"""

from __future__ import annotations

import json
import re
from collections import Counter

import pytest

from smolbench.evals.ec2 import DETERMINISM_ARGS, DSV4_CHAT_TEMPLATE, EC2_DEPLOY_SPECS

from tests._paths import FIXTURES, REPO_ROOT

#: All 22 deploy-spec keys (21 study rungs plus the qwen2.5-1.5b canary). The
#: determinism-bundle tests below cover every entry, unlike STUDY_KEYS
#: (which excludes the canary). The 2026-08-18 user ruling ("all model
#: configurations deterministic") drew no such distinction, and the loop in
#: ec2.py that appends DETERMINISM_ARGS runs over EC2_DEPLOY_SPECS.items()
#: unconditionally.
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
        # vLLM replicates KV heads when tp > n_kv. Either direction must divide.
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


# ---------------------------------------------------------------------------
# Post-study determinism default (2026-08-18)
#
# User ruling 2026-08-18: all model configurations must be deterministic,
# using the certified bundle from the 2026-08-16 hinge experiment. Every
# test below covers all 22 EC2_DEPLOY_SPECS entries (ALL_KEYS), including
# qwen2.5-1.5b. The ruling drew no exception for the smoke-test canary, and
# neither does the ec2.py loop that appends DETERMINISM_ARGS.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", ALL_KEYS)
def test_determinism_args_are_a_contiguous_suffix(key):
    """User ruling 2026-08-18: all model configurations must be deterministic.

    This uses the certified bundle from the 2026-08-16 hinge experiment.
    DETERMINISM_ARGS must land as a contiguous suffix of vllm_args, not
    merely "present somewhere," because ec2.py builds it by appending
    (``_args + DETERMINISM_ARGS``). A spec whose bundle is scattered or
    truncated would mean the append logic broke for that entry specifically.
    """
    args = _args(EC2_DEPLOY_SPECS[key])
    n = len(DETERMINISM_ARGS)
    assert args[-n:] == DETERMINISM_ARGS, f"{key}: DETERMINISM_ARGS is not a trailing suffix of {args}"


@pytest.mark.parametrize("key", ALL_KEYS)
def test_prefix_caching_is_off_every_spec(key):
    """User ruling 2026-08-18: all model configurations must be deterministic.

    This uses the certified bundle from the 2026-08-16 hinge experiment.
    ``--enable-prefix-caching`` was load-bearing for study throughput, but
    the hinge experiment certified it as a nondeterminism source (thousands
    of cache hits under stock, zero under the determinism config). It must
    be absent everywhere, including the qwen2.5-1.5b canary.
    """
    assert "--enable-prefix-caching" not in _args(EC2_DEPLOY_SPECS[key]), (
        f"{key}: prefix caching is a certified nondeterminism source and must stay off"
    )


@pytest.mark.parametrize("key", ALL_KEYS)
def test_revision_and_tokenizer_revision_pinned(key):
    """User ruling 2026-08-18: all model configurations must be deterministic.

    This uses the certified bundle from the 2026-08-16 hinge experiment. As a
    belt-and-braces check: at the pinned build, ``--tokenizer-revision`` inherits
    ``--revision`` when unset (vllm/config/model.py:542), so the second flag is
    redundant today. Both are pinned, each exactly once, each with the same 40-char
    lowercase-hex commit SHA, so the checkpoint and tokenizer stay pinned together
    independently of that inheritance behavior.
    """
    args = _args(EC2_DEPLOY_SPECS[key])
    for flag in ("--revision", "--tokenizer-revision"):
        assert args.count(flag) == 1, f"{key}: {flag} must appear exactly once, found {args.count(flag)}"
    revision = _flag_value(args, "--revision")
    tokenizer_revision = _flag_value(args, "--tokenizer-revision")
    assert _SHA40.fullmatch(revision), f"{key}: --revision {revision!r} is not a 40-char lowercase hex SHA"
    assert _SHA40.fullmatch(tokenizer_revision), (
        f"{key}: --tokenizer-revision {tokenizer_revision!r} is not a 40-char lowercase hex SHA"
    )
    assert revision == tokenizer_revision, (
        f"{key}: --revision {revision!r} != --tokenizer-revision {tokenizer_revision!r}"
    )


@pytest.mark.parametrize("key", ALL_KEYS)
def test_gpu_memory_utilization_pinned(key):
    """User ruling 2026-08-18: all model configurations must be deterministic.

    This uses the certified bundle from the 2026-08-16 hinge experiment.
    DETERMINISM_PLAN section 4 row 4: the KV budget must be an explicit
    function of the spec, not of free VRAM at profiling time. 0.92 is
    vLLM's default at the pinned build (vllm/config/cache.py:69 at
    8efa13b70) made explicit, and the value the hinge det arms actually
    resolved to. deepseek-v4-pro (0.93) keeps the larger value its memory
    footprint already required.
    """
    args = _args(EC2_DEPLOY_SPECS[key])
    assert args.count("--gpu-memory-utilization") == 1, (
        f"{key}: --gpu-memory-utilization must appear exactly once"
    )
    value = _flag_value(args, "--gpu-memory-utilization")
    assert value in {"0.92", "0.93"}, f"{key}: unexpected --gpu-memory-utilization {value!r}"


@pytest.mark.parametrize("key", ALL_KEYS)
def test_no_flag_repeats(key):
    """User ruling 2026-08-18: all model configurations must be deterministic.

    This uses the certified bundle from the 2026-08-16 hinge experiment.
    No ``--flag`` token may appear twice in a spec's vllm_args. This is a
    general well-formedness check, not determinism-specific, but it is
    exactly the failure mode a careless DETERMINISM_ARGS append could
    cause, for example double-adding ``--gpu-memory-utilization`` to a
    spec that already pinned one. So it rides with this test block instead
    of loosening to tolerate any repeat.
    """
    args = _args(EC2_DEPLOY_SPECS[key])
    flags = [a for a in args if a.startswith("--")]
    counts = Counter(flags)
    repeats = {flag: n for flag, n in counts.items() if n > 1}
    assert not repeats, f"{key}: flag(s) repeated in vllm_args: {repeats}"


def test_ec2_vllm_image_default_is_digest_pinned():
    """User ruling 2026-08-18: all model configurations must be deterministic.

    This uses the certified bundle from the 2026-08-16 hinge experiment.
    This test reads ec2.py's source text off disk, not the live
    ``ec2.EC2_VLLM_IMAGE`` module attribute, so a developer's
    ``EC2_VLLM_IMAGE`` environment override in the test process cannot mask
    a regression back to a mutable tag. The whole point of digest-pinning
    is defeated if the default itself drifts. The path is anchored through
    ``__file__`` (this repo's convention, see for example
    ``smolbench/evals/payloads/__init__.py``'s ``_HERE``) instead of a
    cwd-relative path, so it passes regardless of the directory pytest runs
    from.
    """
    ec2_py = REPO_ROOT / "smolbench" / "evals" / "ec2.py"
    source = ec2_py.read_text()
    match = re.search(r'os\.getenv\("EC2_VLLM_IMAGE",\s*"([^"]+)"', source)
    assert match, 'no os.getenv("EC2_VLLM_IMAGE", "...") default found in ec2.py'
    assert re.fullmatch(r"vllm/vllm-openai@sha256:[0-9a-f]{64}", match.group(1)), (
        f"EC2_VLLM_IMAGE default {match.group(1)!r} is not a digest pin "
        "(vllm/vllm-openai@sha256:<64 hex>) -- do not repoint it at a mutable tag"
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
    # V3.1 ships its own template. If it were overridden, that would discard the
    # vendor's tool-call and multi-turn handling for no gain.
    assert "--chat-template" not in _args(EC2_DEPLOY_SPECS["deepseek-v3.1"])


def test_ministral_rows_carry_the_think_protocol_system_prompt():
    from smolbench.evals.ec2 import MINISTRAL_THINK_SYSTEM

    for key in ("ministral-3-3b", "ministral-3-8b", "ministral-3-14b"):
        assert EC2_DEPLOY_SPECS[key].get("system_prompt") == MINISTRAL_THINK_SYSTEM, key
        # The template injects the think protocol only when no system
        # message arrives. --tokenizer-mode mistral would bypass the Jinja
        # template and defeat the workaround.
        assert "--tokenizer-mode" not in _args(EC2_DEPLOY_SPECS[key]), key
    # No other spec injects a provider system prompt in this study.
    for key in STUDY_KEYS:
        if not key.startswith("ministral"):
            assert "system_prompt" not in EC2_DEPLOY_SPECS[key], key


def test_hf_model_ids_match_the_vendored_roster():
    for key in STUDY_KEYS:
        assert EC2_DEPLOY_SPECS[key]["hf_model_id"] == ROSTER[key]["repo"], key


# ---------------------------------------------------------------------------
# derive_tp (2026-08-13 fleet audit): tp comes from the landed box, not from
# a pin.
# ---------------------------------------------------------------------------


def test_model_attention_heads_match_the_vendored_roster():
    from smolbench.evals.ec2 import MODEL_ATTENTION_HEADS

    assert set(MODEL_ATTENTION_HEADS) == set(STUDY_KEYS)
    for key in STUDY_KEYS:
        assert MODEL_ATTENTION_HEADS[key] == ROSTER[key]["num_attention_heads"], key


@pytest.mark.parametrize(
    "model,instance_type,expected",
    [
        # Uses every GPU the hunt paid for when head divisibility allows. A
        # tp=1 spec landing on a 4-GPU g6e.12xlarge idled 3 of 4 L40S.
        ("ministral-3-3b", "g6e.12xlarge", 4),
        ("nemotron-3-nano-4b", "g6e.12xlarge", 4),
        ("nemotron-3-nano-4b", "g6e.4xlarge", 1),
        # 20 heads cannot shard 8 ways. The largest common divisor is 4.
        ("glm-4.7-flash", "p5.48xlarge", 4),
        ("glm-4.7-flash", "g6e.12xlarge", 4),
        # The in-flight lanes' derived tp equals their previous static pin.
        # This was verified before this change landed mid-drain.
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
    assert derive_tp("gemma-4-12b", "g9.99xlarge", {"tp": 4}) == 4
    # No pin at all defaults to 1.
    assert derive_tp("qwen2.5-1.5b", "mystery.large", {}) == 1


def test_derive_tp_on_sm120_g7_boxes():
    from smolbench.evals.ec2 import derive_tp

    # g7.12xlarge carries two GPUs, not four like g6e.12xlarge.
    assert derive_tp("gemma-4-12b", "g7.12xlarge", EC2_DEPLOY_SPECS["gemma-4-12b"]) == 2
    assert derive_tp("exaone-4.5-33b", "g7e.2xlarge", EC2_DEPLOY_SPECS["exaone-4.5-33b"]) == 1
    # The larger g7 sizes must be mapped too. A lane whose hunt spans a
    # mapped and an unmapped size would silently change tp mid-lane
    # (2026-08-14 peer audit: the ministral g7.24xlarge fleet was on the
    # spec-fallback path, correct only by coincidence).
    assert derive_tp("ministral-3-14b", "g7.24xlarge", EC2_DEPLOY_SPECS["ministral-3-14b"]) == 4
    assert derive_tp("ministral-3-14b", "g7.48xlarge", EC2_DEPLOY_SPECS["ministral-3-14b"]) == 8
    assert derive_tp("gemma-4-12b", "g7.24xlarge", EC2_DEPLOY_SPECS["gemma-4-12b"]) == 4
    assert derive_tp("gemma-4-12b", "p5.4xlarge", EC2_DEPLOY_SPECS["gemma-4-12b"]) == 1
    assert derive_tp("ministral-3-14b", "g7e.12xlarge", EC2_DEPLOY_SPECS["ministral-3-14b"]) == 2


def test_derive_tp_unknown_type_fallback_warns_for_known_model(caplog):
    import logging

    from smolbench.evals.ec2 import derive_tp

    with caplog.at_level(logging.WARNING):
        assert derive_tp("gemma-4-12b", "g9.99xlarge", {"tp": 4}) == 4
    assert any("not in _INSTANCE_GPU_COUNTS" in r.message for r in caplog.records)
    # Unknown MODEL on a known type stays a silent, by-design fallback.
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        assert derive_tp("qwen2.5-1.5b", "g6e.12xlarge", {"tp": 1}) == 1
    assert not caplog.records


def test_hardware_pin_blocks_a_gpu_swap_but_allows_a_size_swap(monkeypatch):
    """EC2_REQUIRE_GPU pins the silicon, not the instance size.

    If you widen EC2_INSTANCE_TYPES to escape a capacity wall, that is the obvious move,
    and a silent confound. On 2026-08-14, two repair lanes completing cells generated on
    g6e.4xlarge landed on g6e.2xlarge. That was benign (both carry one L40S, so GPU and
    tp were unchanged) and was accepted. But the same widened list would equally have
    taken a 4-GPU g6e.12xlarge and changed derived tp mid-lane. The pin must permit the
    first case and refuse the second.
    """
    from smolbench.evals import ec2

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
