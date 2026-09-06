"""Fetch and normalise the architecture facts for the family-ladder roster.

The 21-checkpoint study (``scripts/fleet/run_fleet.py``) records how each
checkpoint was SERVED, nothing about what it IS. This pulls every rung's own
``config.json`` (and ``generation_config.json``) from the Hugging Face repo it
was served from, at the exact commit its deploy spec pinned with
``--revision`` -- never the moving branch tip, since a vendor force-push to
the tip would silently re-base every KV figure derived from these configs
while nothing here would notice. ``config.json`` is the only artefact
guaranteed to agree with the weights vLLM loaded, so where a model card
disagrees the config wins and the disagreement is itself a finding. Every
record carries both the pinned SHA (what the study served) and the SHA the
hub actually resolved that pin to, plus a UTC fetch timestamp, so a later
reader can tell a stale note from a moved checkpoint -- or catch the pin
itself having been moved or deleted upstream.

The roster is :data:`smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS` minus the
``qwen2.5-1.5b`` smoke entry -- the same subset ``run_fleet`` pins its tiers
against. No literal model list lives here: a fourth copy is a fourth thing that
can drift.

Two ``__file__``-anchored outputs: ``arch_configs_raw.json``, the verbatim audit
trail, and ``arch_facts.json``, a normalised diagram-ready view (``text_config``
wrappers hoisted, per-layer arrays run-length encoded into their repeating
motif, fields grouped by attention / positional encoding / MoE / state space).
Unrecognised keys go to ``derived.unclassified`` rather than being dropped: an
unfamiliar field on a 2026 architecture is a finding.

``--check`` cross-checks two independent things and exits non-zero, WITHOUT
writing either output, if either fails: (1) the fetched configs against
``tests/fixtures/roster_configs.json`` (the deploy-spec test's ground truth)
on the four fields both hold, and (2) each record's own pinned SHA against
the SHA the hub resolved -- a mismatch there means the pin moved or vanished
upstream since the study ran. Deferring both writes until after ``--check``
passes means a failed cross-check leaves the previous, known-good
``arch_configs_raw.json`` / ``arch_facts.json`` as the audit trail, rather
than being overwritten by the very fetch that failed to agree.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Design: huggingface_hub is a core dependency (see pyproject `dependencies`)
# already relied on by smolbench/evals/tokenization.py -- using it here in
# place of hand-rolled urllib buys auth, retry, and local caching for free,
# and it is the only client that can resolve a revision pin to a commit SHA
# via a documented API (HfApi.repo_info) rather than an undocumented header.
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

# --------------------------------------------------------------------------
# Field groupings
#
# Intentionally *generous*: a key appearing in only one family
# (``attn_output_gate``, ``ssm_state_size``, ``num_kv_shared_layers``) still
# lands in the group a reader would look for it in. Anything unlisted goes to
# ``unclassified``, so a new architectural knob announces itself.
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


def _fetch(repo: str, filename: str, revision: str) -> Tuple[Optional[Any], Optional[str], Optional[str]]:
    """Fetch one JSON file from a Hugging Face repo at a pinned revision.

    This is the one seam the offline tests monkeypatch (by name and by this
    exact signature), so ``collect`` never calls ``huggingface_hub`` directly.

    Parameters
    ----------
    repo : str
        The Hugging Face repo id the checkpoint was served from.
    filename : str
        The file to fetch, e.g. ``"config.json"`` or ``"generation_config.json"``.
    revision : str
        The commit SHA to fetch -- taken from the deploy spec's own
        ``--revision`` flag by :func:`spec_revision`, never the moving branch
        tip, since a vendor force-push to the tip would silently re-base
        every KV figure derived from these configs.

    Returns
    -------
    tuple
        ``(payload, resolved_revision, error)``:

        - ``payload``: the parsed JSON, or ``None`` if the file could not be
          fetched at all.
        - ``resolved_revision``: the commit SHA the hub actually resolved
          ``revision`` to, from a separate :meth:`HfApi.repo_info` call made
          *after* the payload fetch (so a 404 on the file itself is still
          reported as ``"absent"`` rather than being pre-empted by a metadata
          lookup). ``None`` when that lookup fails -- always paired with a
          non-``None`` ``error`` in that case; never silently ``None`` with
          ``error is None``.
        - ``error``: ``None`` on full success; the literal string
          ``"absent"`` when the repo ships no such file at this revision (an
          expected, informative absence -- not every repo ships a
          ``generation_config.json``), so callers can tell that apart from
          "the network broke"; otherwise ``f"{type(exc).__name__}: {exc}"``.

    Notes
    -----
    Never raises. Every exception this function can encounter -- missing
    file, auth failure, network error, a moved/deleted revision -- is caught
    and reported via the ``error`` slot instead, because one rung's fetch
    failure must not abort the whole roster sweep; the caller still wants the
    other 20/21 records.
    """
    try:
        path = hf_hub_download(repo_id=repo, filename=filename, revision=revision)
        payload = json.loads(Path(path).read_text())
    except EntryNotFoundError:
        # Design: huggingface_hub.errors.EntryNotFoundError is the common base
        # of both RemoteEntryNotFoundError (404 from the hub) and
        # LocalEntryNotFoundError (missing from an offline cache) in the
        # installed huggingface-hub version -- catching the base class covers
        # both without guessing which one a given call path raises.
        return None, None, "absent"
    except Exception as exc:  # noqa: BLE001 -- report, never abort the sweep
        return None, None, f"{type(exc).__name__}: {exc}"

    try:
        # Design: instantiated per call, not at module scope, so importing
        # this module (and `--help`) makes no network call. A separate call
        # from the payload fetch above, and made only after it succeeds, so a
        # metadata-lookup failure never masks a plain 404 on the file.
        resolved_revision = HfApi().repo_info(repo_id=repo, revision=revision).sha
    except Exception as exc:  # noqa: BLE001 -- report, never abort the sweep
        # NOTE: the payload is kept (it is real data the file fetch already
        # produced) even though the SHA lookup failed; the missing revision
        # is surfaced here as an error rather than returned as a silent
        # `None` with no explanation, and is caught again downstream by
        # cross_check's missing-revision problem.
        return payload, None, f"{type(exc).__name__}: {exc}"

    if not resolved_revision:
        # Guard: an empty/falsy `.sha` (never observed, but the API makes no
        # non-emptiness guarantee) must not slip through as a *silent*
        # `resolved_revision=None, error=None` -- that is precisely the
        # "returning None silently" the no-silent-fallback rule forbids, and
        # it would otherwise contradict this function's own Returns section.
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
    win on collision, since they describe the wrapper. The returned sibling names
    (vision, audio) let a write-up note that the served model is the text tower of
    a larger checkpoint.
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


def spec_revision(spec: Dict[str, Any]) -> str:
    """Return the commit SHA a deploy spec pins with its ``--revision`` flag.

    Parameters
    ----------
    spec : dict
        One entry of :data:`smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS`;
        the SHA is read from ``spec["vllm_args"]``, the list of CLI flags the
        study served this rung with.

    Returns
    -------
    str
        The SHA immediately following ``"--revision"`` in ``vllm_args``.

    Raises
    ------
    ValueError
        ``vllm_args`` has no ``"--revision"`` flag, or ``"--revision"`` is
        the last element with no value after it. Design: this deliberately
        does NOT fall back to ``"main"`` -- silently auditing an unpinned
        rung against a moving branch is exactly the defect this function
        exists to prevent. As of this writing all 22 entries of
        ``EC2_DEPLOY_SPECS`` carry ``--revision``, so this raise is a guard
        against a future unpinned entry, not a path any current rung takes.
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
    fetch : callable, optional
        A ``(repo, filename, revision) -> (payload, resolved_revision, error)``
        callable to use in place of :func:`_fetch`. Defaults to :func:`_fetch`
        itself. Design: accepting this as a parameter (rather than requiring
        callers to monkeypatch module state) lets the offline tests inject a
        fake with no network access and no reach into this module's globals.

    Returns
    -------
    dict
        ``{"fetched_at": ..., "raw": ..., "facts": ...}``.
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
        # Fail loudly here (not caught) -- an unpinned spec is a defect in the
        # roster itself, not a per-rung fetch failure to record and move on.
        pinned = spec_revision(spec)
        config, revision, error = fetch(repo, "config.json", pinned)
        generation, _, generation_error = fetch(repo, "generation_config.json", pinned)
        status = "ok " if config else "FAIL"
        detail = "" if error is None else f"  <- {error}"
        print(f"{status}  {spec_key:<28} {repo}{detail}", flush=True)

        raw[spec_key] = {
            "repo": repo,
            # Design: both SHAs are kept side by side because that pair *is*
            # the check -- they agree unless the pin was moved or deleted
            # upstream since the study served this rung.
            "pinned_revision": pinned,
            "revision": revision,
            "fetched_at": fetched_at,
            "config": config,
            "config_error": error,
            "generation_config": generation,
            "generation_config_error": generation_error,
        }
        if config is None:
            # `revision` is included (as None) even on failure so every
            # record -- not just the successful ones -- carries both keys;
            # cross_check's missing-revision check relies on the key being
            # present rather than absent.
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

    Two independent checks, both against ``facts``:

    1. Fetched configs vs. ``tests/fixtures/roster_configs.json`` (the
       deploy-spec test's ground truth) on the four fields both hold. A
       mismatch means the upstream checkpoint moved under the study.
    2. Each record's own ``pinned_revision`` (what the deploy spec asked for)
       vs. its ``revision`` (what the hub actually resolved that pin to). A
       mismatch here is the vendor-force-push case this whole fix targets:
       the pin itself moved or was deleted upstream since the study ran.
       Design: this is a self-consistency check on ``facts`` alone, not a
       fixture comparison -- the fixture has no revision field to compare
       against, and the invariant ("a record's own two SHAs agree") is
       actually stronger than a fixture comparison would be, since it holds
       for every record regardless of what is or isn't in the fixture.

    Returns
    -------
    list[str]
        One line per problem, from either check; empty when everything
        agrees.
    """
    problems: List[str] = []

    # Check 1: fixture agreement on shape/attention/positional fields.
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

    # Check 2: pinned vs. resolved revision, over every fetched record --
    # deliberately its own loop over `facts` rather than folded into the
    # fixture loop above, so it still runs (and can fail) on roster keys the
    # fixture doesn't happen to cover.
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
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="cross-check against tests/fixtures/roster_configs.json "
                             "and each record's pinned vs. resolved revision")
    args = parser.parse_args()

    bundle = collect()
    failures = [k for k, v in bundle["facts"].items() if "error" in v]

    # Design: --check runs BEFORE either output is written. A failed
    # cross-check must leave the previous, known-good arch_configs_raw.json
    # and arch_facts.json exactly as they were, so the audit trail is not
    # overwritten by the very fetch that failed to agree -- writing first and
    # checking after (the prior behaviour) destroyed that trail on every
    # failed run.
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

    # Design: relative_to(_REPO_ROOT) is purely cosmetic for the summary
    # print; fall back to the raw path if the two don't share a root (e.g. a
    # test monkeypatches _RAW_PATH/_FACTS_PATH to a tmp dir), so a passing run
    # never crashes on a path computation that has nothing to do with
    # correctness.
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
