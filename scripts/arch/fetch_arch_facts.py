"""Fetch normalized architecture facts for the family-ladder roster.

Use deploy-spec revision pins so moving branch tips cannot alter audited KV
figures; config wins over model cards because it matches served weights.
Keep pinned and resolved SHAs to detect moved or deleted pins. ``--check``
writes nothing so disagreement preserves prior audit files.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Use the documented API to resolve revision pins to commit SHAs.
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.errors import EntryNotFoundError

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS  # noqa: E402

#: Exclude the smoke-test entry from the study roster.
_SMOKE_KEY = "qwen2.5-1.5b"

_RAW_PATH = _HERE / "arch_configs_raw.json"
_FACTS_PATH = _HERE / "arch_facts.json"
_FIXTURE_PATH = _REPO_ROOT / "tests" / "fixtures" / "roster_configs.json"

# Group known keys; retain unknown keys under ``unclassified``.

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


def _fetch(repo: str, filename: str, revision: str) -> Tuple[Optional[Any], Optional[str], Optional[str]]:
    """Fetch one JSON file from a Hugging Face repo at a pinned revision.

    This is the named seam offline tests patch, so `collect` never calls
    `huggingface_hub` directly. Never raise: one failure must not abort the roster sweep.

    Parameters
    ----------
    repo : str
        Hugging Face repository.
    filename : str
        JSON filename.
    revision : str
        Pinned revision.

    Returns
    -------
    Tuple[Optional[Any], Optional[str], Optional[str]]
        Payload, resolved revision, and error; absent files return ``"absent"``.
    """
    try:
        path = hf_hub_download(repo_id=repo, filename=filename, revision=revision)
        payload = json.loads(Path(path).read_text())
    except EntryNotFoundError:
        # Covers both hub 404s and local-cache misses.
        return None, None, "absent"
    except Exception as exc:  # noqa: BLE001 -- report, never abort the sweep
        return None, None, f"{type(exc).__name__}: {exc}"

    try:
        # Delay metadata lookup so import stays offline and 404s stay clear.
        resolved_revision = HfApi().repo_info(repo_id=repo, revision=revision).sha
    except Exception as exc:  # noqa: BLE001 -- report, never abort the sweep
        # Keep payload so cross_check can report the missing revision.
        return payload, None, f"{type(exc).__name__}: {exc}"

    if not resolved_revision:
        # Do not silently accept an empty SHA.
        return payload, None, "repo_info returned no commit sha for this revision"

    return payload, resolved_revision, None


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

    Diagrams use the motif and multiplier rather than 61 individual layers.

    Parameters
    ----------
    items : List[Any]
        Layer sequence.

    Returns
    -------
    Optional[Dict[str, Any]]
        Motif metadata, or None for an irregular sequence.
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

    Serve ``text_config`` for wrappers because the study uses
    ``--language-model-only``; top-level keys override collisions as wrapper metadata.

    Parameters
    ----------
    config : Dict[str, Any]
        Model configuration.

    Returns
    -------
    Tuple[Dict[str, Any], List[str]]
        Hoisted configuration and sibling tower names.
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

    Normalize ``layer_types`` and ``hybrid_override_pattern`` to one sequence.

    Parameters
    ----------
    config : Dict[str, Any]
        Model configuration.

    Returns
    -------
    Dict[str, Any]
        Drawable layer metadata.
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
            # Nemotron-H alphabet: M = Mamba-2, * = self-attention, - = MLP.
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


def spec_revision(spec: Dict[str, Any]) -> str:
    """Return the commit SHA a deploy spec pins with its ``--revision`` flag.

    Reject missing pins rather than auditing the moving ``main`` branch.

    Parameters
    ----------
    spec : Dict[str, Any]
        Deploy specification.

    Returns
    -------
    str
        ``--revision`` commit SHA.

    Raises
    ------
    ValueError
        Missing ``--revision`` or its SHA.
    """
    vllm_args = spec.get("vllm_args", [])
    repo = spec.get("hf_model_id", "<unknown repo>")
    try:
        flag_index = vllm_args.index("--revision")
    except ValueError as exc:
        raise ValueError(
            f"{repo}: deploy spec has no --revision pin in vllm_args; "
            "cannot audit an unpinned rung against a moving branch"
        ) from exc
    if flag_index + 1 >= len(vllm_args):
        raise ValueError(
            f"{repo}: --revision is the last vllm_args element with no SHA "
            "after it; cannot audit an unpinned rung against a moving branch"
        )
    return vllm_args[flag_index + 1]


_FetchFn = Callable[[str, str, str], Tuple[Optional[Any], Optional[str], Optional[str]]]


def collect(*, fetch: Optional[_FetchFn] = None) -> Dict[str, Any]:
    """Fetch every roster rung and build both the raw and normalised records.

    Parameters
    ----------
    fetch : Optional[_FetchFn], optional
        Optional fetch implementation.

    Returns
    -------
    Dict[str, Any]
        Timestamp, raw results, and normalized facts.
    """
    fetch = fetch or _fetch
    roster = {
        key: spec for key, spec in EC2_DEPLOY_SPECS.items() if key != _SMOKE_KEY
    }
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    raw: Dict[str, Any] = {}
    facts: Dict[str, Any] = {}

    for spec_key in sorted(roster):
        spec = roster[spec_key]
        repo = spec["hf_model_id"]
        # An unpinned spec is a roster defect, not a recoverable fetch failure.
        pinned = spec_revision(spec)
        config, revision, error = fetch(repo, "config.json", pinned)
        generation, _, generation_error = fetch(repo, "generation_config.json", pinned)
        status = "ok " if config else "FAIL"
        detail = "" if error is None else f"  <- {error}"
        print(f"{status}  {spec_key:<28} {repo}{detail}", flush=True)

        raw[spec_key] = {
            "repo": repo,
            # Keep both SHAs to detect moved or deleted pins.
            "pinned_revision": pinned,
            "revision": revision,
            "fetched_at": fetched_at,
            "config": config,
            "config_error": error,
            "generation_config": generation,
            "generation_config_error": generation_error,
        }
        if config is None:
            # Keep ``revision`` so cross_check reports missing pins.
            facts[spec_key] = {
                "repo": repo, "pinned_revision": pinned, "revision": revision, "error": error,
            }
            continue

        hoisted, siblings = _hoist(config)
        facts[spec_key] = {
            "repo": repo,
            "pinned_revision": pinned,
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
    """Run both cross-checks: fixture agreement and pin-vs-resolved revision.

    Compare the four fields shared with the fixture; a mismatch means the upstream
    checkpoint moved under the study. Independently compare pinned and resolved revisions.

    Parameters
    ----------
    facts : Dict[str, Any]
        Facts keyed by roster specification.

    Returns
    -------
    List[str]
        Problems, if any.
    """
    problems: List[str] = []

    if not _FIXTURE_PATH.exists():
        problems.append(f"fixture missing: {_FIXTURE_PATH}")
    else:
        fixture = json.loads(_FIXTURE_PATH.read_text())
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

    # Check every fact, including keys absent from the fixture.
    for spec_key, record in sorted(facts.items()):
        pinned = record.get("pinned_revision")
        resolved = record.get("revision")
        if pinned is None or resolved is None:
            problems.append(
                f"{spec_key}: missing revision (pinned={pinned!r}, resolved={resolved!r})"
            )
        elif pinned != resolved:
            problems.append(
                f"{spec_key}: pinned revision {pinned!r} != resolved {resolved!r} "
                "-- the pin moved or was deleted upstream since the study ran"
            )
    return problems


def main() -> int:
    """Fetch architecture facts and optionally cross-check their pinned revisions."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="cross-check against tests/fixtures/roster_configs.json "
                             "and each record's pinned vs. resolved revision")
    args = parser.parse_args()

    bundle = collect()
    failures = [k for k, v in bundle["facts"].items() if "error" in v]

    # Check first so mismatches preserve prior audit files.
    if args.check:
        problems = cross_check(bundle["facts"])
        if problems:
            print("\nCROSS-CHECK MISMATCHES:")
            for line in problems:
                print(f"  {line}")
            return 1
        print(f"cross-check vs tests/fixtures/roster_configs.json: all {len(bundle['facts'])} agree")

    _RAW_PATH.write_text(
        json.dumps(bundle["raw"], sort_keys=True, separators=(",", ":")) + "\n"
    )
    _FACTS_PATH.write_text(json.dumps(
        {"fetched_at": bundle["fetched_at"], "models": bundle["facts"]},
        indent=1, sort_keys=True) + "\n")

    # Accept temporary paths outside the repository in tests.
    try:
        facts_display = _FACTS_PATH.relative_to(_REPO_ROOT)
        raw_display = _RAW_PATH.relative_to(_REPO_ROOT)
    except ValueError:
        facts_display, raw_display = _FACTS_PATH, _RAW_PATH
    print(f"\nwrote {facts_display} and {raw_display} "
          f"({len(bundle['facts']) - len(failures)}/{len(bundle['facts'])} ok)")
    if failures:
        print(f"FAILED to fetch: {failures}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
