"""Fetch and normalise the architecture facts for the family-ladder roster.

Fetches each rung's ``config.json`` at the exact commit its deploy spec pinned
with ``--revision``, never the moving branch tip, since a vendor force-push to
the tip would silently re-base every KV figure derived from these configs (see
`spec_revision`). Where a model card disagrees with the config, the config
wins: it is the only artefact guaranteed to match the weights vLLM served.
Every record carries both the pinned and hub-resolved SHA so a later reader
can catch a moved or deleted pin.

Writes two outputs: ``arch_configs_raw.json`` (verbatim audit trail) and
``arch_facts.json`` (normalised, diagram-ready). ``--check`` cross-checks both
against ground truth and exits non-zero without writing either, so a failed
run never overwrites the previous known-good pair (see `cross_check`).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# huggingface_hub (already a dependency) buys auth/retry/caching for free and
# is the only client that resolves a revision pin to a commit SHA via a
# documented API (HfApi.repo_info) rather than an undocumented header.
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.errors import EntryNotFoundError

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

# Field groupings, intentionally generous: a key unique to one family still
# lands in the group a reader would look for it in. Anything unlisted goes to
# ``unclassified``, so a new architectural knob announces itself.

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

    The one seam the offline tests monkeypatch (by name and signature), so
    `collect` never calls `huggingface_hub` directly. Never raises --
    one rung's fetch failure must not abort the whole roster sweep.

    Parameters
    ----------
    repo : str
        Hugging Face repository identifier.
    filename : str
        JSON filename to retrieve.
    revision : str
        Pinned repository revision.

    Returns
    -------
    Tuple[Optional[Any], Optional[str], Optional[str]]
        ``(payload, resolved_revision, error)``; ``error`` is ``"absent"``
        when the repo ships no such file at this revision (not every repo
        ships a generation_config.json), otherwise the exception string.
    """
    try:
        path = hf_hub_download(repo_id=repo, filename=filename, revision=revision)
        payload = json.loads(Path(path).read_text())
    except EntryNotFoundError:
        # Common base of the hub's 404 and the local-cache-miss error, so
        # catching it covers both without guessing which one applies.
        return None, None, "absent"
    except Exception as exc:  # noqa: BLE001 -- report, never abort the sweep
        return None, None, f"{type(exc).__name__}: {exc}"

    try:
        # Instantiated per call, not module scope, so importing this module
        # makes no network call; called only after the payload fetch succeeds
        # so a metadata-lookup failure never masks a plain 404 on the file.
        resolved_revision = HfApi().repo_info(repo_id=repo, revision=revision).sha
    except Exception as exc:  # noqa: BLE001 -- report, never abort the sweep
        # Payload is kept even though the SHA lookup failed; cross_check's
        # missing-revision check catches the None downstream.
        return payload, None, f"{type(exc).__name__}: {exc}"

    if not resolved_revision:
        # An empty/falsy .sha (never observed, not guaranteed non-empty) must
        # not slip through as a silent resolved_revision=None, error=None.
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

    A block diagram draws the repeating unit and an ``x N`` multiplier, not 61
    individual layers.

    Parameters
    ----------
    items : List[Any]
        Layer sequence to inspect.

    Returns
    -------
    Optional[Dict[str, Any]]
        None when the sequence doesn't tile (DeepSeek's leading dense layers,
        Nemotron's irregular hybrid), which sends the caller to the run-length
        view instead.
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
    ``--language-model-only``, exactly that inner model. Top-level keys win on
    collision, since they describe the wrapper.

    Parameters
    ----------
    config : Dict[str, Any]
        Model configuration, possibly with a ``text_config`` wrapper.

    Returns
    -------
    Tuple[Dict[str, Any], List[str]]
        The hoisted configuration and names of sibling modality towers.
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

    Parameters
    ----------
    config : Dict[str, Any]
        Model configuration containing a layer encoding.

    Returns
    -------
    Dict[str, Any]
        Drawable layer sequence metadata.
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


def spec_revision(spec: Dict[str, Any]) -> str:
    """Return the commit SHA a deploy spec pins with its ``--revision`` flag.

    Deliberately does not fall back to ``"main"``: silently
    auditing an unpinned rung against a moving branch is exactly the defect
    this function exists to prevent.

    Parameters
    ----------
    spec : Dict[str, Any]
        Deploy specification containing ``vllm_args``.

    Returns
    -------
    str
        Commit SHA pinned by ``--revision``.

    Raises
    ------
    ValueError
        If ``vllm_args`` has no ``--revision`` flag or no SHA after it.
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
        injectable in place of `_fetch` so offline tests can pass a fake with
        no network access, without monkeypatching module globals.

    Returns
    -------
    Dict[str, Any]
        Fetch timestamp, raw fetch results and normalised architecture facts.
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
        # Not caught: an unpinned spec is a roster defect, not a per-rung
        # fetch failure to record and move on.
        pinned = spec_revision(spec)
        config, revision, error = fetch(repo, "config.json", pinned)
        generation, _, generation_error = fetch(repo, "generation_config.json", pinned)
        status = "ok " if config else "FAIL"
        detail = "" if error is None else f"  <- {error}"
        print(f"{status}  {spec_key:<28} {repo}{detail}", flush=True)

        raw[spec_key] = {
            "repo": repo,
            # Both SHAs are kept side by side because that pair is the check:
            # they agree unless the pin moved or was deleted upstream.
            "pinned_revision": pinned,
            "revision": revision,
            "fetched_at": fetched_at,
            "config": config,
            "config_error": error,
            "generation_config": generation,
            "generation_config_error": generation_error,
        }
        if config is None:
            # `revision` stays a key (as None) on failure too, since
            # cross_check's missing-revision check relies on it being present.
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

    Check 1 compares fetched configs against
    ``tests/fixtures/roster_configs.json`` on the four fields both hold; a
    mismatch means the upstream checkpoint moved under the study. Check 2
    compares each record's own pinned vs. resolved revision -- the
    vendor-force-push case this whole fix targets -- independently of the
    fixture, since that invariant holds regardless of what the fixture
    covers.

    Parameters
    ----------
    facts : Dict[str, Any]
        Fetched architecture facts keyed by roster specification.

    Returns
    -------
    List[str]
        One line per problem found; empty when everything agrees.
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

    # Own loop over `facts` (not folded into the fixture loop above) so it
    # still runs on roster keys the fixture doesn't cover.
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

    # --check runs before either output is written, so a failed cross-check
    # leaves the previous known-good files as the audit trail instead of
    # being overwritten by the fetch that failed to agree.
    if args.check:
        problems = cross_check(bundle["facts"])
        if problems:
            print("\nCROSS-CHECK MISMATCHES:")
            for line in problems:
                print(f"  {line}")
            return 1
        print(f"cross-check vs tests/fixtures/roster_configs.json: all {len(bundle['facts'])} agree")

    _RAW_PATH.write_text(json.dumps(bundle["raw"], indent=1, sort_keys=True) + "\n")
    _FACTS_PATH.write_text(json.dumps(
        {"fetched_at": bundle["fetched_at"], "models": bundle["facts"]},
        indent=1, sort_keys=True) + "\n")

    # Cosmetic path display; falls back to the raw path if a test
    # monkeypatches these to a tmp dir outside _REPO_ROOT, so display never
    # crashes a passing run.
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
