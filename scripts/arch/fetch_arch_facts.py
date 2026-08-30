"""Fetch and normalise the architecture facts for the family-ladder roster.

The 21-checkpoint study (``scripts/fleet/run_fleet.py``) records how each
checkpoint was SERVED, nothing about what it IS. This pulls every rung's own
``config.json`` (and ``generation_config.json``) from the Hugging Face repo it
was served from: ``config.json`` is the only artefact guaranteed to agree with
the weights vLLM loaded, so where a model card disagrees the config wins and the
disagreement is itself a finding. Every record carries the resolved commit SHA
(the ``x-repo-commit`` response header) and a UTC fetch timestamp, so a later
reader can tell a stale note from a moved checkpoint.

The roster is :data:`smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS` minus the
``qwen2.5-1.5b`` smoke entry -- the same subset ``run_fleet`` pins its tiers
against. No literal model list lives here: a fourth copy is a fourth thing that
can drift.

Two ``__file__``-anchored outputs: ``arch_configs_raw.json``, the verbatim audit
trail, and ``arch_facts.json``, a normalised diagram-ready view (``text_config``
wrappers hoisted, per-layer arrays run-length encoded into their repeating
motif, fields grouped by attention / positional encoding / MoE / state space).
Unrecognised keys are kept under ``derived.unclassified`` rather than dropped:
an unfamiliar field on a 2026 architecture is a finding.

``--check`` also cross-checks the fetched configs against
``tests/fixtures/roster_configs.json`` (the deploy-spec test's ground truth) on
the four fields both hold, and exits non-zero on any mismatch or fetch failure.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS  # noqa: E402

#: The smoke-test entry is not part of the study roster; ``run_fleet`` excludes
#: it from its own tier check the same way.
_SMOKE_KEY = "qwen2.5-1.5b"

_RAW_PATH = _HERE / "arch_configs_raw.json"
_FACTS_PATH = _HERE / "arch_facts.json"
_FIXTURE_PATH = _REPO_ROOT / "tests" / "fixtures" / "roster_configs.json"

_TIMEOUT_SECONDS = 60

# --------------------------------------------------------------------------
# Field groupings
#
# These lists drive the normalised view and are intentionally *generous*: a key
# appearing in only one family (``attn_output_gate``, ``ssm_state_size``,
# ``num_kv_shared_layers``) still lands in the group a reader would look for it
# in. Anything unlisted goes to ``unclassified``, so a new architectural knob
# announces itself instead of vanishing.
# --------------------------------------------------------------------------

_SHAPE_KEYS = (
    "model_type", "num_hidden_layers", "hidden_size", "intermediate_size",
    "vocab_size", "tie_word_embeddings", "torch_dtype", "dtype",
    "hidden_act", "hidden_activation", "mlp_hidden_act", "hidden_size_per_layer_input",
    "use_double_wide_mlp", "num_experts_per_layer_input", "rms_norm_eps",
    "layer_norm_epsilon", "final_logit_softcapping", "attn_logit_softcapping",
)

_ATTENTION_KEYS = (
    "num_attention_heads", "num_key_value_heads", "head_dim", "global_head_dim",
    "num_global_key_value_heads", "attention_bias", "attention_dropout",
    "attn_output_gate", "attention_k_eq_v", "sliding_window", "layer_types",
    "full_attention_interval", "num_kv_shared_layers", "use_qk_norm", "qk_layernorm",
    "sliding_window_pattern", "attention_chunk_size", "use_bidirectional_attention",
    "linear_num_key_heads", "linear_num_value_heads", "linear_key_head_dim",
    "linear_value_head_dim", "linear_conv_kernel_dim", "decoder_sparse_step",
)

_MLA_KEYS = (
    "q_lora_rank", "kv_lora_rank", "qk_nope_head_dim", "qk_rope_head_dim",
    "v_head_dim", "qk_head_dim", "index_head_dim", "index_n_heads", "index_topk",
)

_ROPE_KEYS = (
    "rope_theta", "rope_scaling", "rope_parameters", "rope_local_base_freq",
    "partial_rotary_factor", "max_position_embeddings", "rope_traditional",
    "no_rope_layers", "nope_layer_interval",
)

_MOE_KEYS = (
    "num_experts", "n_routed_experts", "num_local_experts", "num_experts_per_tok",
    "top_k_experts", "n_shared_experts", "shared_expert_intermediate_size",
    "moe_intermediate_size", "expert_intermediate_size", "moe_layer_freq",
    "first_k_dense_replace", "norm_topk_prob", "scoring_func", "topk_method",
    "n_group", "topk_group", "routed_scaling_factor", "router_aux_loss_coef",
    "enable_moe_block", "num_nextn_predict_layers", "mtp_num_layers",
    "use_grouped_topk", "n_group_experts",
)

_SSM_KEYS = (
    "hybrid_override_pattern", "mamba_num_heads", "mamba_head_dim", "ssm_state_size",
    "conv_kernel", "n_groups", "expand", "chunk_size", "time_step_rank",
    "time_step_min", "time_step_max", "time_step_floor", "use_mamba_kernels",
    "mamba_hidden_act", "mamba_proj_bias", "use_conv_bias",
)

#: Keys that carry no architectural signal: token ids, plumbing, HF bookkeeping.
_IGNORED_KEYS = frozenset({
    "architectures", "auto_map", "bos_token_id", "eos_token_id", "pad_token_id",
    "unk_token_id", "transformers_version", "use_cache", "initializer_range",
    "_name_or_path", "output_attentions", "output_hidden_states", "return_dict",
    "chunk_size_feed_forward", "is_encoder_decoder", "id2label", "label2id",
    "problem_type", "torchscript", "num_logits_to_keep", "ep_size",
    "hidden_dropout", "mlp_bias", "use_bias", "residual_in_fp32",
    "rescale_prenorm_residual", "tokenizer_class", "pretraining_tp",
})


def _fetch(repo: str, filename: str) -> Tuple[Optional[Any], Optional[str], Optional[str]]:
    """Fetch one JSON file from a Hugging Face repo's main revision.

    Returns
    -------
    tuple
        ``(payload, revision, error)``: the parsed JSON or ``None``, the commit
        SHA from the ``x-repo-commit`` response header, and a failure reason
        (``None`` on success). A 404 reports ``"absent"``, so callers can tell
        "this repo ships no generation_config" from "the network broke".
    """
    url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
    request = urllib.request.Request(url, headers={"User-Agent": "smolbench-arch-facts"})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            revision = response.headers.get("x-repo-commit")
            return json.loads(response.read().decode("utf-8")), revision, None
    except urllib.error.HTTPError as exc:
        return None, None, "absent" if exc.code == 404 else f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 -- report, never abort the sweep
        return None, None, f"{type(exc).__name__}: {exc}"


def _rle(items: List[Any]) -> List[Dict[str, Any]]:
    """Run-length encode a per-layer list into ``[{value, count}, ...]``."""
    runs: List[Dict[str, Any]] = []
    for item in items:
        if runs and runs[-1]["value"] == item:
            runs[-1]["count"] += 1
        else:
            runs.append({"value": item, "count": 1})
    return runs


def _motif(items: List[Any]) -> Optional[Dict[str, Any]]:
    """Find the shortest repeating motif that tiles ``items`` exactly.

    A block diagram draws the repeating unit and an ``x N`` multiplier, not 61
    individual layers.

    Returns
    -------
    dict or None
        ``{"pattern": [...], "repeats": N}``, or ``None`` when the sequence does
        not tile (DeepSeek's leading dense layers, Nemotron's irregular hybrid),
        which sends the caller to the run-length view.
    """
    n = len(items)
    if n == 0:
        return None
    for period in range(1, n // 2 + 1):
        if n % period:
            continue
        pattern = items[:period]
        if all(items[i] == pattern[i % period] for i in range(n)):
            return {"pattern": pattern, "repeats": n // period}
    return None


def _hoist(config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Hoist a multimodal wrapper's ``text_config`` up, returning it and any sibling towers.

    Ten of the 21 rungs ship as ``*ForConditionalGeneration`` wrappers whose
    language-model fields live in ``text_config``; the study serves them with
    ``--language-model-only``, which is exactly that inner model. Top-level keys
    win on collision, since they describe the wrapper. The returned sibling
    names (vision, audio) let a write-up note that the served model is the text
    tower of a larger checkpoint.
    """
    text_config = config.get("text_config")
    if not isinstance(text_config, dict):
        return dict(config), []
    hoisted = {k: v for k, v in text_config.items() if not k.startswith("_")}
    siblings = [
        key for key in ("vision_config", "audio_config", "video_config")
        if isinstance(config.get(key), dict)
    ]
    for key, value in config.items():
        if key in ("text_config",) or key in siblings:
            continue
        hoisted[key] = value
    return hoisted, siblings


def _classify(config: Dict[str, Any]) -> Dict[str, Any]:
    """Group a hoisted config's keys into the diagram's structural sections."""
    groups = {
        "shape": _SHAPE_KEYS,
        "attention": _ATTENTION_KEYS,
        "mla": _MLA_KEYS,
        "positional": _ROPE_KEYS,
        "moe": _MOE_KEYS,
        "ssm": _SSM_KEYS,
    }
    classified: Dict[str, Any] = {name: {} for name in groups}
    claimed = set(_IGNORED_KEYS)
    for name, keys in groups.items():
        for key in keys:
            if key in config:
                classified[name][key] = config[key]
                claimed.add(key)
    classified["quantization"] = config.get("quantization_config")
    claimed.add("quantization_config")
    classified["unclassified"] = {
        key: value for key, value in config.items()
        if key not in claimed and not key.startswith("_")
    }
    return classified


def _layer_view(config: Dict[str, Any]) -> Dict[str, Any]:
    """Derive the drawable layer sequence: run-length runs plus a motif.

    Normalises the two encodings to one list of strings: ``layer_types`` (a
    list; Qwen3.5 / Gemma-4 / GLM / EXAONE-4.x) and ``hybrid_override_pattern``
    (a character string; Nemotron-3).
    """
    view: Dict[str, Any] = {}
    layer_types = config.get("layer_types")
    if isinstance(layer_types, list) and layer_types:
        view["source"] = "layer_types"
        view["sequence"] = layer_types
    else:
        pattern = config.get("hybrid_override_pattern")
        if isinstance(pattern, str) and pattern:
            view["source"] = "hybrid_override_pattern"
            # Nemotron-H's alphabet: M = Mamba-2, * = self-attention, - = MLP.
            view["sequence"] = list(pattern)
    sequence = view.get("sequence")
    if not sequence:
        return {"source": None}
    view["length"] = len(sequence)
    view["runs"] = _rle(sequence)
    view["motif"] = _motif(sequence)
    view["counts"] = {
        value: sequence.count(value) for value in sorted(set(sequence), key=str)
    }
    return view


def collect() -> Dict[str, Any]:
    """Fetch every roster rung and build both the raw and normalised records."""
    roster = {
        key: spec for key, spec in EC2_DEPLOY_SPECS.items() if key != _SMOKE_KEY
    }
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    raw: Dict[str, Any] = {}
    facts: Dict[str, Any] = {}

    for spec_key in sorted(roster):
        spec = roster[spec_key]
        repo = spec["hf_model_id"]
        config, revision, error = _fetch(repo, "config.json")
        generation, _, generation_error = _fetch(repo, "generation_config.json")
        print(f"{'ok ' if config else 'FAIL'}  {spec_key:<28} {repo}"
              f"{'' if config else '  <- ' + str(error)}", flush=True)

        raw[spec_key] = {
            "repo": repo,
            "revision": revision,
            "fetched_at": fetched_at,
            "config": config,
            "config_error": error,
            "generation_config": generation,
            "generation_config_error": generation_error,
        }
        if config is None:
            facts[spec_key] = {"repo": repo, "error": error}
            continue

        hoisted, siblings = _hoist(config)
        facts[spec_key] = {
            "repo": repo,
            "revision": revision,
            "fetched_at": fetched_at,
            "architecture": (config.get("architectures") or [None])[0],
            "wrapper_towers": siblings,
            "served": {
                "tp": spec.get("tp"),
                "max_model_len": spec.get("max_model_len"),
                "vllm_args": spec.get("vllm_args", []),
            },
            "derived": _classify(hoisted),
            "layers": _layer_view(hoisted),
            "generation_config": generation,
        }
    return {"fetched_at": fetched_at, "raw": raw, "facts": facts}


def cross_check(facts: Dict[str, Any]) -> List[str]:
    """Compare fetched configs against ``tests/fixtures/roster_configs.json``.

    A mismatch means the upstream checkpoint moved under the study.

    Returns
    -------
    list[str]
        One line per mismatch; empty when everything agrees.
    """
    if not _FIXTURE_PATH.exists():
        return [f"fixture missing: {_FIXTURE_PATH}"]
    fixture = json.loads(_FIXTURE_PATH.read_text())
    problems: List[str] = []

    missing = set(fixture) ^ set(facts)
    if missing:
        problems.append(f"roster key mismatch vs fixture: {sorted(missing)}")

    for spec_key, expected in sorted(fixture.items()):
        actual = facts.get(spec_key)
        if not actual or "derived" not in actual:
            problems.append(f"{spec_key}: no config fetched")
            continue
        merged = {
            "architecture": actual["architecture"],
            **actual["derived"]["shape"],
            **actual["derived"]["attention"],
            **actual["derived"]["positional"],
        }
        for field in ("architecture", "num_attention_heads", "num_key_value_heads",
                      "max_position_embeddings"):
            if merged.get(field) != expected.get(field):
                problems.append(
                    f"{spec_key}.{field}: fixture={expected.get(field)!r} "
                    f"fetched={merged.get(field)!r}"
                )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="cross-check against tests/fixtures/roster_configs.json")
    args = parser.parse_args()

    bundle = collect()
    _RAW_PATH.write_text(json.dumps(bundle["raw"], indent=1, sort_keys=True) + "\n")
    _FACTS_PATH.write_text(json.dumps(
        {"fetched_at": bundle["fetched_at"], "models": bundle["facts"]},
        indent=1, sort_keys=True) + "\n")

    failures = [k for k, v in bundle["facts"].items() if "error" in v]
    print(f"\nwrote {_FACTS_PATH.relative_to(_REPO_ROOT)} and "
          f"{_RAW_PATH.relative_to(_REPO_ROOT)} "
          f"({len(bundle['facts']) - len(failures)}/{len(bundle['facts'])} ok)")
    if failures:
        print(f"FAILED to fetch: {failures}")

    if args.check:
        problems = cross_check(bundle["facts"])
        if problems:
            print("\nCROSS-CHECK MISMATCHES:")
            for line in problems:
                print(f"  {line}")
            return 1
        print("cross-check vs tests/fixtures/roster_configs.json: all 21 agree")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
