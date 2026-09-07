"""Per-lane driver for the DEDUCTION side of the family-ladder scaling study.

One invocation serves exactly one checkpoint on one EC2 box and runs one
``smolbench.deduction.lean.runner.sweep`` against it; the fleet supervisor
(``scripts/fleet/run_fleet.py``) launches up to 21 of these, one per lane,
each reattaching to the box its induction phase already provisioned via that
phase's ``EC2_EXPERIMENT_TAG``/state file. ``MODELS``/``COT_ARGS`` are loaded
by file path from ``notebooks/induction/run_study.py`` (the roster's single
source of truth) rather than imported, since a bare ``import run_study``
would be ambiguous once both trees' same-named modules are on ``sys.path``.
Sweep knobs live in ``notebooks/deduction/sweep.yaml``; ``build_config``
stamps its SHA-256 (and ``decontam_config.toml``'s) into every run's
``manifest.json`` for provenance. What this file adds on top is lane
IDENTITY -- ``run_name``, seeds, the served model, optional shard/whitelist.

MODULE IMPORT ORDER IS LOAD-BEARING: this file's ``os.environ.setdefault``
calls must land before ``smolbench.evals.providers.ec2`` is first imported
(directly or transitively), because that module freezes ``EC2_*`` constants
from the environment at import time. Get it wrong and nothing raises -- two
lanes can silently swap served checkpoints on a live billing box. See the
comment above the setdefault block for the exact ordering rule, and the GUARD
right after it for the tag-collision check this import path also runs.

Run (repo root)::

    LEAN_MODEL=glm-4.7 .venv/bin/python notebooks/deduction/run_study.py
    LEAN_MODEL=glm-4.7 .venv/bin/python notebooks/deduction/run_study.py --teardown
"""

import argparse
import copy
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any

# These two `smolbench` imports must stay above the `os.environ.setdefault`
# block below (the constants and the GUARD that follows both need them), and
# are VERIFIED ec2-free -- checked one module per fresh interpreter, since a
# shared one proves nothing about which import pulled what::
#
#     import sys, smolbench.evals.study_config   # then again for .experiment
#     assert "smolbench.evals.providers.ec2" not in sys.modules
#
# `study_config` pulls in only `smolbench{,.evals,.evals.quiz}`; `experiment`
# additionally pulls `smolbench.evals.{_aws,provider,replicates,results_store}`
# -- neither reaches `providers.ec2`. Re-run this check before adding a third
# smolbench import here: one that reached `ec2` would freeze this lane's
# EC2_* constants from the still-unseeded environment, with nothing raised.
from smolbench.evals.experiment import validate_experiment_tag
from smolbench.evals.study_config import load_study_config
from smolbench.evals.retired_markers import is_retired

logging.basicConfig(level=logging.INFO)

# Anchoring + S3-spool constants. No environment reads and no AWS calls, but
# the SPOOL_* pair does parse the committed study config off disk at import.
#
# parents[2] of <repo>/notebooks/deduction/run_study.py is the repo root.
# Anchored via __file__, never the cwd: the fleet, a notebook kernel or a bare
# shell may launch this file from anywhere.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: Bucket/region this lane spools its run directory to -- one bucket shared
#: with the induction-phase results store, read from the committed
#: ``smolbench/evals/study_config.toml`` rather than duplicated here, so it
#: cannot go stale independently of the config ``results_store`` itself reads
#: (VERIFIED: both ``default_results_uri`` and ``resolve_store`` call
#: ``load_study_config().results``). Two separate calls rather than one bound
#: temporary: the loader is memoized on the resolved path, so the second call
#: parses nothing and leaves no import-time temporary needing a ``del``.
SPOOL_BUCKET: str = load_study_config().results.bucket
SPOOL_REGION: str = load_study_config().results.region
#: The destination key prefix comes from ``runner.spool_prefix()``, resolved
#: at call time inside ``spool_to_s3`` and the GUARD in ``main`` below -- not
#: a module constant here, so a late ``LEAN_SPOOL_PREFIX`` override takes
#: effect per-invocation rather than at import.

#: The latest date any served checkpoint's weights were published (last HF
#: commit touching a weight file at each roster lane's pinned `--revision`,
#: resolved 2026-08-30). Weights cannot encode data published after they were
#: written, so this bounds every knowledge cutoff from above and is the floor
#: a post-cutoff corpus's `target_date` must clear -- see `build_config`'s
#: corpus gate.
ROSTER_LATEST_RELEASE: str = "2026-06-03"


def lane_env_defaults(
    key: str, *, repo_root: Path, state_file: str | None = None
) -> dict[str, str]:
    """Derive this lane's four ``EC2_*``/``SMOLBENCH_LEAN_RESULTS`` defaults.

    Pure, so this module's top-level code stays the only thing touching
    ``os.environ`` (via ``setdefault``, before the first import of
    ``smolbench.evals.providers.ec2``). Does not validate `key` against
    ``MODELS``: that table is not loaded yet here.

    Parameters
    ----------
    state_file : str | None, optional
        ``None`` derives ``repo_root / f".ec2_state_scaling_{key}.json"``;
        a bare or relative name resolves against `repo_root`, not the process cwd
        -- anchoring both phases to the same root is how this lane reattaches to
        induction's box.
    """
    if state_file is None:
        resolved_state_file = repo_root / f".ec2_state_scaling_{key}.json"
    else:
        candidate = Path(state_file)
        resolved_state_file = candidate if candidate.is_absolute() else repo_root / candidate

    return {
        "EC2_EXPERIMENT_TAG": f"scaling-{key}",
        "EC2_STATE_FILE": str(resolved_state_file),
        "EC2_VLLM_IMAGE": "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7",
        "SMOLBENCH_LEAN_RESULTS": str(repo_root / "notebooks" / "deduction" / "results"),
    }


# Env setdefaults -- must run before smolbench.evals.providers.ec2 is
# imported by anything, directly or transitively (module docstring).
#
# Read raw, unvalidated: MODELS (loaded below) would validate LEAN_MODEL, but
# loading it here would import providers.ec2 too early. selected_model(),
# called later from main(), does the real validation.
_RAW_LEAN_MODEL: str = os.environ.get("LEAN_MODEL", "").strip()
_RAW_LEAN_STATE_FILE: str | None = os.environ.get("LEAN_STATE_FILE") or None

if _RAW_LEAN_MODEL:
    for _env_name, _env_value in lane_env_defaults(
        _RAW_LEAN_MODEL, repo_root=REPO_ROOT, state_file=_RAW_LEAN_STATE_FILE
    ).items():
        # setdefault, never assignment: a value the fleet supervisor (or an
        # interactive shell) already exported must win over this default.
        os.environ.setdefault(_env_name, _env_value)
    del _env_name, _env_value

    # GUARD -- cross-lane box adoption. Boxes are discovered by tag when a
    # state file is absent, so a second lane under the same tag adopts the
    # first lane's instance and serves its own model on top of it; every row
    # after the swap is attributed to the wrong model. keys.env's standalone
    # `EC2_EXPERIMENT_TAG=scaling-standalone`, exported with `set -a`, is how
    # lanes end up sharing one tag.
    #
    # Two checks, and the order is load-bearing: `validate_experiment_tag`
    # (shared with induction) refuses an empty/whitespace tag or the bare
    # shared fleet prefix, but it cannot do the exact per-lane compare
    # below since it does not know this lane's model
    # key. It must run first because the bare-prefix case would otherwise be
    # misdiagnosed by the exact compare as "wrong lane" when the real danger
    # is that the tag names the WHOLE fleet -- fleet teardown terminates by
    # tag.
    #
    # lane=None: shard support lives in `run_name`, never in
    # EC2_EXPERIMENT_TAG, so there is no suffix to strip.
    _TAG = os.environ.get("EC2_EXPERIMENT_TAG", "")
    try:
        validate_experiment_tag(_TAG, None)
    except ValueError as exc:
        # Translated, never propagated: every guard in this file signals a
        # configuration mistake as SystemExit before any AWS call, not a raw
        # traceback. Cannot mis-label a broken study config as a tag failure:
        # SPOOL_BUCKET above already forced the same memoized config load to
        # succeed, so validate_experiment_tag's internal load is a cache hit
        # that cannot raise -- every ValueError here is one of its own
        # refusals.
        raise SystemExit(
            f"{exc}\n"
            f"Fix: export EC2_EXPERIMENT_TAG=scaling-{_RAW_LEAN_MODEL} for this "
            "lane (or stop sourcing keys.env in the launcher)."
        ) from exc

    # Exact compare, never a substring test: spec keys nest ("glm-4.7" is a
    # prefix of "glm-4.7-flash"), so containment would accept a well-formed
    # neighbouring lane's tag -- the case the shared validator above cannot
    # catch, since that tag passes it cleanly.
    if _TAG != f"scaling-{_RAW_LEAN_MODEL}":
        raise SystemExit(
            f"EC2_EXPERIMENT_TAG={_TAG!r} is not this lane's tag "
            f"('scaling-{_RAW_LEAN_MODEL}').\n"
            "Two lanes sharing a tag will adopt each other's EC2 instance and "
            "generate rows under the wrong model.\n"
            "Most likely cause: a launcher sourced notebooks/deduction/keys.env "
            "with `set -a`, exporting its standalone default and overriding the "
            "per-lane value this driver would otherwise install.\n"
            f"Fix: export EC2_EXPERIMENT_TAG=scaling-{_RAW_LEAN_MODEL} for this "
            "lane (or stop sourcing keys.env in the launcher)."
        )
    del _TAG
# else: LEAN_MODEL is unset/empty -- skip the block rather than seed a
# misleading tag like "scaling-"; selected_model() raises for this case
# before any real work happens.

# Load notebooks/induction/run_study.py by file path -- a bare `import
# run_study` is ambiguous once both trees' same-named modules are on
# sys.path in one process, which is already run_fleet.py's situation.
_INDUCTION_RUN_STUDY_PATH: Path = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
_induction_spec = importlib.util.spec_from_file_location(
    "deduction_induction_run_study", _INDUCTION_RUN_STUDY_PATH
)
_induction = importlib.util.module_from_spec(_induction_spec)
# Must register in sys.modules before exec_module: a @dataclass applied
# inside a module not yet registered raises `AttributeError: 'NoneType'
# object has no attribute '__dict__'`, since dataclass introspection
# resolves the defining module by sys.modules name lookup.
sys.modules[_induction_spec.name] = _induction
_induction_spec.loader.exec_module(_induction)  # runs that file's own load_dotenv(...) etc.

#: Spec key -> short analysis tag. Imported, never re-declared.
MODELS: dict[str, str] = _induction.MODELS
#: Spec key -> per-request CoT-toggle kwargs, total over MODELS. Imported,
#: never re-declared.
COT_ARGS: dict[str, dict] = _induction.COT_ARGS

# Late imports: safe only now that our own EC2_* setdefaults have landed and
# MODELS/COT_ARGS are bound. Hence noqa: E402.
from smolbench.evals.providers import ec2  # noqa: E402
from smolbench.deduction.lean import corpus, decontam_config, runner  # noqa: E402
from smolbench.deduction.lean.nullverify import NullVerifier  # noqa: E402


def selected_model() -> str:
    """Resolve and validate this lane's model key from ``LEAN_MODEL``.

    Deferred counterpart to the raw, unvalidated import-time read: ``MODELS``
    is guaranteed loaded by the time this runs.
    """
    key = os.environ.get("LEAN_MODEL", "").strip()
    valid = ", ".join(sorted(MODELS))
    if not key:
        raise SystemExit(
            "LEAN_MODEL is unset (or empty). This driver serves exactly ONE "
            f"checkpoint per invocation. Set it to one of: {valid}"
        )
    if key not in MODELS:
        raise SystemExit(f"LEAN_MODEL={key!r} is not a known spec key. Valid keys: {valid}")
    return key


def resolve_lean_seed() -> int:
    """Resolve the one seed shared by theorem selection and decoding, from ``LEAN_SEED``.

    Read at call time, never cached, so a caller can flip ``LEAN_SEED``
    between ``build_config`` calls in one process. Drives two different
    things off one value: ``theorems["seed"]`` picks WHICH theorems this lane
    measures (``runner._select_theorems``); ``cfg["seed"]`` is the decode
    seed ``runner.sweep`` puts on the wire (replicate `i` decodes at
    `seed + i`).

    WARNING: a non-zero ``LEAN_SEED`` re-draws the theorem sample, desyncing
    from the pinned 300 in ``notebooks/deduction/pinned_theorems.json`` (its
    digest is asserted in ``tests/deduction/test_lean_pinning_audit.py``) and
    making the run incomparable with the published lanes. Only for a
    deliberate, clearly-labelled re-sampling experiment.
    """
    raw = os.environ.get("LEAN_SEED", "").strip()
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        raise SystemExit(
            f"LEAN_SEED={raw!r} is not a valid integer. This seed drives BOTH "
            "theorem selection (theorems.seed) and decoding (cfg.seed); unset "
            "it to use the pinned default (0), or set it to an integer."
        ) from None


# Sweep-config schema. This study's sweep knobs live in
# `notebooks/deduction/sweep.yaml`; what lives here is only the set of key
# names `build_config` expects that file to define, and the set it refuses.
#: This study's committed sweep-knob file. Anchored to `REPO_ROOT`, never the
#: cwd: the fleet, a notebook kernel or a bare shell may launch from anywhere.
SWEEP_CONFIG_PATH: Path = REPO_ROOT / "notebooks" / "deduction" / "sweep.yaml"

#: Schema guard, not a config table: only key names live here, every value
#: lives in `SWEEP_CONFIG_PATH`. `build_config` refuses a sweep file missing
#: any of these, because an absent key would fall through to
#: ``runner.sweep``'s own library default -- the silent drift these explicit
#: values exist to prevent.
REQUIRED_SWEEP_KEYS: frozenset[str] = frozenset(
    {
        "temperature",
        "max_tokens",
        "request_timeout",
        "max_retries",
        "dojo_timeout",
        "concurrent_gen",
        "skip_trivial",
        "k",
        "n_replicates",
        "rungs",
        "theorem_workers",
        "max_concurrency",
        "theorems",
    }
)

#: The same schema guard one level down, inside the sweep file's ``theorems``
#: block. ``seed`` and ``shard`` are deliberately not here: they are lane
#: identity, in `RESERVED_SWEEP_THEOREM_KEYS` instead.
REQUIRED_SWEEP_THEOREM_KEYS: frozenset[str] = frozenset(
    {"source", "kind", "split", "limit", "require_postcutoff"}
)

#: Keys the sweep file must not define, at top level. Each is per-lane
#: identity that `build_config` resolves from the environment and overlays on
#: the loaded document, so a value written in the file would be silently
#: overwritten -- e.g. a maintainer setting ``seed: 7`` there would still get
#: seed 0, with nothing raised or logged.
RESERVED_SWEEP_KEYS: frozenset[str] = frozenset(
    {"run_name", "seed", "models", "cell_whitelist"}
)

#: The same refusal inside the sweep file's ``theorems`` block: ``seed`` comes
#: from `resolve_lean_seed` and ``shard`` from ``LEAN_SHARD``.
RESERVED_SWEEP_THEOREM_KEYS: frozenset[str] = frozenset({"seed", "shard"})


def _stamp_path(path: Path) -> str:
    """Spell `path` the way a manifest provenance stamp records it.

    Repo-relative whenever possible, never absolute: an absolute path would
    embed this box's checkout location in every archived manifest and make
    two boxes' manifests differ over nothing.

    A path outside the repo has no repo-relative spelling, so it is returned
    absolute instead -- reachable only through `build_config`'s
    ``sweep_config_path`` test seam, never in production. Shared by both of
    `build_config`'s provenance stamps (``sweep_config`` and
    ``decontam_config``) so the two cannot drift apart in how they spell a
    path.
    """
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def build_config(key: str, *, sweep_config_path: Path | None = None) -> dict:
    """Build this lane's ``runner.sweep`` configuration: load the knobs, overlay the lane.

    Two layers. Sweep KNOBS load from the committed
    ``notebooks/deduction/sweep.yaml`` through ``runner.load_sweep_config`` --
    the same loader ``cli.cmd_run_sweep``'s ``--config`` uses, so the schema
    has one reader. This lane's IDENTITY (``run_name``, ``seed``, ``models``,
    ``theorems.seed``/``kind``/``split``, optional ``shard``/``cell_whitelist``,
    and the two provenance stamps below) is then overlaid on a deep copy of
    what was loaded, so mutating one call's config cannot reach another's.

    USER-LOCKED: every key is identical across all 21 checkpoints except
    ``run_name`` and ``models[0]``, so a next-tactic success-rate difference
    points at the model, not a changed sweep. The sweep file's SHA-256, and
    ``decontam_config.toml``'s (its premise stoplist decides what
    ``hint:3``/``hint:4`` contain), are stamped into every run's
    ``manifest.json`` as ``sweep_config``/``decontam_config`` provenance.

    Two refusals guard the loaded file, RESERVED checked before MISSING so a
    file breaking both is diagnosed by the more dangerous one: a RESERVED key
    (`RESERVED_SWEEP_KEYS`, `RESERVED_SWEEP_THEOREM_KEYS`) would be silently
    overwritten by the lane-identity overlay; a MISSING key
    (`REQUIRED_SWEEP_KEYS`, `REQUIRED_SWEEP_THEOREM_KEYS`) would fall through
    to ``runner.sweep``'s own library default instead of this study's pinned
    value. Both raise ``SystemExit`` naming the offending keys.

    Post-cutoff corpus gate, run at call time before the config is built:
    ``SystemExit`` if ``corpus.postcutoff_metadata()`` is None (the corpus
    predates every roster checkpoint's training cutoff) or if its
    ``target_date`` is earlier than `ROSTER_LATEST_RELEASE` (some checkpoint
    may already have seen the theorems during training).

    `sweep_config_path` is a test seam (default ``None`` reads the committed
    file); a path outside the repo is stamped absolute, since it has no
    repo-relative spelling. ``LEAN_SHARD``, ``LEAN_RUN_NAME``,
    ``LEAN_CELL_WHITELIST``, ``LEAN_CORPUS_KIND``, ``LEAN_CORPUS_SPLIT`` and
    ``LEAN_SEED`` are all read at call time, never at import and never
    cached; ``run_name`` defaults to ``f"scaling_{key}"`` plus a
    ``_shard<i>of<n>`` suffix when sharding, matching
    ``scripts/fleet/run_fleet.py``'s ``Lane`` naming.

    Raises
    ------
    SystemExit
        Corpus gate or reserved/missing key refusal above.
    FileNotFoundError, ValueError, yaml.YAMLError
        Propagated from ``runner.load_sweep_config`` un-translated: these
        mean the committed config is broken or gone, not that this lane was
        misconfigured.
    """
    # Post-cutoff corpus gate -- see the docstring above. Runs before the
    # config dict below is built, and before any AWS call.
    block = corpus.postcutoff_metadata()
    if block is None:
        raise SystemExit(
            f"{corpus.data_root()} (traced at commit "
            f"{corpus.metadata()['from_repo']['commit']}) is not a post-cutoff "
            "corpus. This study will not run on a pre-cutoff corpus -- every "
            "roster checkpoint's knowledge cutoff postdates the original "
            "LeanDojo Benchmark 4 snapshot, so its theorems are not a valid "
            "held-out set. Build a post-cutoff corpus with "
            "scripts/deduction/build_postcutoff_corpus.py (Package B) and "
            "point SMOLBENCH_LEAN_DATA at it."
        )
    # Plain string comparison is correct here: ISO YYYY-MM-DD dates sort
    # lexicographically in chronological order, so this needs no date parsing.
    if not (block["target_date"] >= ROSTER_LATEST_RELEASE):
        raise SystemExit(
            f"corpus target_date={block['target_date']!r} is earlier than "
            f"ROSTER_LATEST_RELEASE={ROSTER_LATEST_RELEASE!r}: a target date "
            "before the roster's latest release means some checkpoint may "
            "have already seen the corpus's \"post-cutoff\" theorems during "
            "training."
        )

    config_path = SWEEP_CONFIG_PATH if sweep_config_path is None else Path(sweep_config_path)
    loaded, sweep_config_sha256 = runner.load_sweep_config(config_path)

    # REFUSAL 1 -- reserved keys, checked first (see docstring). `theorems`
    # may be absent or not a mapping here (the next refusal's business), so
    # its sub-keys are read defensively rather than indexed.
    loaded_theorems = loaded.get("theorems")
    loaded_theorem_keys = set(loaded_theorems) if isinstance(loaded_theorems, dict) else set()
    reserved = sorted(
        {name for name in RESERVED_SWEEP_KEYS if name in loaded}
        | {f"theorems.{name}" for name in RESERVED_SWEEP_THEOREM_KEYS & loaded_theorem_keys}
    )
    if reserved:
        raise SystemExit(
            f"{config_path}: reserved key(s) {', '.join(reserved)}.\n"
            "Each is per-lane IDENTITY, resolved at build_config call time from "
            "LEAN_RUN_NAME / LEAN_SEED / LEAN_MODEL / LEAN_SHARD / "
            "LEAN_CELL_WHITELIST and overlaid on top of this file, so a value "
            "set here would be SILENTLY OVERWRITTEN and have no effect at all.\n"
            "Fix: delete the key(s) from the file and set the matching "
            "environment variable instead."
        )

    # REFUSAL 2 -- missing knobs. Top level first: by the time the sub-key
    # check runs, `theorems` (itself required) is known present, but a
    # `theorems` block that is present yet not a mapping contributes no keys,
    # so it reports all five sub-keys missing rather than raising
    # AttributeError.
    missing = sorted(REQUIRED_SWEEP_KEYS - set(loaded))
    if not missing:
        missing = sorted(
            f"theorems.{name}" for name in REQUIRED_SWEEP_THEOREM_KEYS - loaded_theorem_keys
        )
    if missing:
        raise SystemExit(
            f"{config_path}: missing required key(s) {', '.join(missing)}.\n"
            "Every knob this study pins must be stated explicitly: an absent key "
            "falls through to runner.sweep's own library default instead of this "
            "study's value, silently and with nothing recorded."
        )

    # Sharding suffixes the default run_name so two concurrent shards don't
    # write one run directory: concurrent appends to one all_rows.jsonl from
    # separate processes interleave large rows and corrupt the file. An
    # explicit LEAN_RUN_NAME wins verbatim and owns that uniqueness itself.
    shard = os.environ.get("LEAN_SHARD", "").strip()
    shard_suffix = ""
    if shard:
        shard_suffix = "_shard" + shard.replace("/", "of")
    run_name = os.environ.get("LEAN_RUN_NAME", "").strip() or f"scaling_{key}{shard_suffix}"
    seed = resolve_lean_seed()

    # Deep copy, never the loader's return value or a shallow copy: nested
    # structures (`theorems`, `k`, `rungs`) must be private to this call.
    cfg: dict[str, Any] = copy.deepcopy(loaded)

    cfg["run_name"] = run_name
    cfg["seed"] = seed

    theorems: dict[str, Any] = cfg["theorems"]
    theorems["seed"] = seed
    # kind/split: the sweep file's values are the defaults
    # LEAN_CORPUS_KIND/LEAN_CORPUS_SPLIT override (and a blank override falls
    # back to). Each is bound to a local first, since the assignment
    # overwrites the very value it falls back to.
    yaml_kind = theorems["kind"]
    theorems["kind"] = os.environ.get("LEAN_CORPUS_KIND", yaml_kind).strip() or yaml_kind
    yaml_split = theorems["split"]
    theorems["split"] = os.environ.get("LEAN_CORPUS_SPLIT", yaml_split).strip() or yaml_split
    if shard:
        theorems["shard"] = shard

    # extra_params deep-copies the shared COT_ARGS table, so no caller can
    # corrupt it for other lanes.
    cfg["models"] = [
        {
            "provider": "ec2",
            "model": key,
            "display_name": key,
            "extra_params": copy.deepcopy(COT_ARGS[key]),
        }
    ]

    # `runner.sweep` writes `config` verbatim into manifest.json, so stamping
    # the digest here is the entire mechanism -- nothing inside sweep does a
    # matching thing. Repo-relative, never absolute, so two boxes' manifests
    # don't differ over checkout location alone.
    cfg["sweep_config"] = {
        "path": _stamp_path(config_path),
        "sha256": sweep_config_sha256,
    }

    # decontam_config.toml's premise stoplist decides what the hint:3/hint:4
    # rungs contain, so the manifest records which stoplist produced them,
    # same as the sweep-file stamp above. Computed here from a file the
    # package ships (path and digest off the same loaded object, so they
    # can't drift apart), not read from the sweep file -- hence absent from
    # both the reserved and required key sets.
    decontam = decontam_config.load_decontam_config()
    cfg["decontam_config"] = {
        "path": _stamp_path(decontam.path),
        "sha256": decontam.sha256,
    }

    # Optional, like the shard key above, but purely informational: `runner.sweep`
    # reads LEAN_CELL_WHITELIST itself. Fingerprints the SORTED content, not
    # just the path, since the file can be edited after a run starts; a
    # reader diffs `sha256` against a fresh hash to confirm which file a run
    # actually used.
    whitelist_path = os.environ.get("LEAN_CELL_WHITELIST", "").strip()
    if whitelist_path:
        cfg["cell_whitelist"] = {
            "path": whitelist_path,
            "sha256": runner.hash_cell_keys(runner.load_cell_whitelist(whitelist_path)),
        }

    return cfg


def select_verifier() -> Any:
    """Resolve the verifier object to hand to ``runner.sweep``, from ``LEAN_VERIFY``.

    ``NullVerifier()`` when unset/empty/``"defer"`` (the default; every
    verdict is recorded ``"unverified"``, real checking deferred to a later
    pass); the ``verify`` MODULE object -- not an instance, since
    ``runner.sweep`` calls its functions directly -- when exactly ``"real"``.
    That import is local to the ``"real"`` branch, so importing this file
    never requires ``lean_dojo``.
    """
    choice = os.environ.get("LEAN_VERIFY", "defer").strip() or "defer"
    if choice == "defer":
        return NullVerifier()
    if choice == "real":
        # Local import: verify.py needs lean_dojo (the `lean` extra) at its own
        # module top level, and its ImportError names the fix if it is missing.
        from smolbench.deduction.lean import verify

        return verify
    raise SystemExit(f"LEAN_VERIFY={choice!r} is not valid; expected 'defer' or 'real'.")


def spool_to_s3(run_dir: Path, key: str, *, client: Any = None) -> int:
    """Upload one lane's run directory to S3, verify it, then prune local disk.

    End-of-run only, called once after ``runner.sweep`` returns. ``sweep``
    exposes no progress hook, so a crash mid-sweep leaves rows unspooled
    until a relaunch reaches this call again.

    Two-phase, ordering load-bearing: upload and verify every file (sorted,
    deterministic order) before pruning any, so a part-way failure cannot
    have already deleted an unconfirmed upload.

    Pruning keeps ``manifest.json``, ``all_rows.jsonl`` and any
    ``retired_markers.RETIRED_MARKERS``-named sibling (the
    ``all_rows_SUPERSEDED-<stamp>.jsonl`` files ``--force-rerun`` creates).
    ``all_rows.jsonl`` must survive: a relaunch's resume path
    (``runner._existing_keys``/``runner._sanity_done``) reads only that file
    to decide what is already recorded, including the ``kind: "sanity"``
    rows (there is no separate sanity file). Deleting it would force the
    next relaunch to re-provision, re-serve and regenerate every cell at
    real additional spend, even though the rows are already durably in S3;
    ``manifest.json`` alone does not substitute -- it carries
    ``config``/``run_name``/counts, never per-cell state.

    Parameters
    ----------
    key : str
        The destination prefix ``f"{runner.spool_prefix()}/scaling_{key}/"``
        is built from this, not ``run_dir.name``, so the S3 layout stays
        keyed on the model even when ``LEAN_RUN_NAME`` renamed the run
        directory.
    client : Any, optional
        ``None`` lazily builds a boto3 client, so importing this file needs
        no AWS SDK and tests can inject a fake.

    Returns
    -------
    int
        Files uploaded and verified; ``0`` (not an error) when `run_dir` is
        not a directory.

    Raises
    ------
    RuntimeError
        An upload fails verification (``head_object`` raised, or a size
        mismatch) -- raised before any pruning.
    """
    if not run_dir.is_dir():
        logging.info(f"spool_to_s3[{key}]: no run directory at {run_dir}; nothing to sync.")
        return 0

    if client is None:
        import boto3  # lazy -- see docstring

        client = boto3.client("s3", region_name=SPOOL_REGION)

    dest_prefix = f"{runner.spool_prefix()}/scaling_{key}/"
    files = sorted(p for p in run_dir.rglob("*") if p.is_file())

    # Phase 1: upload + verify every file before deleting anything.
    for path in files:
        rel = path.relative_to(run_dir).as_posix()
        dest_key = dest_prefix + rel
        client.upload_file(str(path), SPOOL_BUCKET, dest_key)

        local_size = path.stat().st_size
        try:
            head = client.head_object(Bucket=SPOOL_BUCKET, Key=dest_key)
            remote_size = head["ContentLength"]
        except Exception as exc:  # noqa: BLE001 -- re-raised below with actionable context
            raise RuntimeError(
                f"spool_to_s3[{key}]: could not verify upload of {dest_key!r} "
                f"(local size {local_size} bytes; head_object failed: {exc}); "
                "local data left intact, nothing pruned."
            ) from exc
        if remote_size != local_size:
            raise RuntimeError(
                f"spool_to_s3[{key}]: size mismatch verifying {dest_key!r}: "
                f"local={local_size} bytes, remote={remote_size} bytes; "
                "local data left intact, nothing pruned."
            )

    # Phase 2: every upload is verified, so pruning is safe (see docstring
    # for why manifest.json and all_rows.jsonl are kept).
    manifest_path = run_dir / "manifest.json"
    all_rows_path = run_dir / "all_rows.jsonl"
    for path in files:
        if path == manifest_path or path == all_rows_path:
            continue
        if is_retired(path):
            continue
        path.unlink()

    subdirs = sorted(
        (p for p in run_dir.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True
    )
    for subdir in subdirs:
        try:
            subdir.rmdir()
        except OSError:
            pass  # not empty -- fine, leave it

    logging.info(
        f"spool_to_s3[{key}]: uploaded and verified {len(files)} file(s) to "
        f"s3://{SPOOL_BUCKET}/{dest_prefix}"
    )
    return len(files)


def outstanding_cell_keys(config: dict, run_dir: Path) -> set[tuple]:
    """Return the cell keys `runner.sweep(config, run_dir, resume=True, ...)` would still write.

    Lets `main` check, without any AWS call, whether a lane has anything left
    to do before it provisions a box: enumerates the same "would this cell be
    skipped on resume?" predicate ``runner.sweep`` applies internally, and
    diffs it against what ``runner._existing_keys`` already finds on disk.
    Depends on ``spool_to_s3`` keeping ``all_rows.jsonl`` across its prune --
    without that file, every lane would always look fully outstanding.

    Mirrors ``runner.sweep``'s own nesting by calling the SAME functions
    sweep calls, not a re-implementation: theorem pool via
    ``runner._select_theorems`` (same ``LEAN_CELL_WHITELIST`` sweep reads);
    drop a theorem only on a RECORDED sanity failure
    (``runner._sanity_done`` in ``SANITY_FAILURE_VERDICTS`` -- no recorded
    verdict is not a failure); then ``k`` via ``runner._k_indices``, rungs
    skipped by ``runner.is_trivial_rung`` under ``skip_trivial``, and models
    x replicates, filtered by the cell whitelist -- exactly
    ``_run_cells_at_step_concurrent``'s own loop. Row keys built with
    ``runner._row_key`` so they compare equal to ``_existing_keys``'.

    DRIFT RISK: this re-enumerates sweep's cell predicate at a second site
    rather than importing one shared predicate (none exists). A future
    change to sweep's skip logic that isn't mirrored here would UNDER-count
    `expected` -- the unsafe direction, since this check would then skip
    provisioning a lane that still has real cells to write. No test catches
    this class of drift other than an end-to-end comparison against a live
    sweep; review this function alongside any change to sweep's
    cell-selection logic.

    Parameters
    ----------
    run_dir : Path
        Need not exist; an absent ``all_rows.jsonl`` reads as "nothing done".

    Raises
    ------
    ValueError
        Propagated from ``runner._select_theorems`` or
        ``runner.load_cell_whitelist`` -- the same conditions that would
        make ``runner.sweep`` itself raise before doing any work.
    """
    all_rows_path = run_dir / "all_rows.jsonl"

    # Same LEAN_CELL_WHITELIST env read runner.sweep itself performs: a
    # whitelist narrows both which theorems survive selection and which
    # individual cells survive below.
    cell_whitelist_path = os.environ.get("LEAN_CELL_WHITELIST", "").strip()
    cell_whitelist: frozenset[tuple] | None = (
        runner.load_cell_whitelist(cell_whitelist_path) if cell_whitelist_path else None
    )

    theorems = runner._select_theorems(config["theorems"], cell_whitelist=cell_whitelist)
    sanity_done = runner._sanity_done(all_rows_path)
    k_strategy = config.get("k", {}).get("strategy", "last")
    rungs: list[str] = list(config.get("rungs", []))
    models_cfg: list[dict] = list(config["models"])
    n_replicates = int(config.get("n_replicates", 1))
    skip_trivial = bool(config.get("skip_trivial", True))

    expected: set[tuple] = set()
    for theorem in theorems:
        # A recorded sanity failure means sweep's per-theorem worker returns
        # before generating any cell for this theorem on resume; no recorded
        # verdict is not a failure and falls through to enumeration below.
        if sanity_done.get(theorem.full_name) in runner.SANITY_FAILURE_VERDICTS:
            continue
        for k in runner._k_indices(theorem, k_strategy):
            for rung in rungs:
                chain, level_str = rung.split(":", 1)
                level = int(level_str)
                # Identical to runner.sweep's own trivial-rung skip.
                if skip_trivial and runner.is_trivial_rung(
                    theorem, k, chain, level  # type: ignore[arg-type]
                ):
                    continue
                for mc in models_cfg:
                    display_name = mc.get("display_name", mc["model"])
                    for replicate_idx in range(n_replicates):
                        key = runner._row_key(
                            display_name, theorem.full_name, k, rung, replicate_idx
                        )
                        if cell_whitelist is not None and key not in cell_whitelist:
                            continue
                        expected.add(key)

    done = runner._existing_keys(all_rows_path)
    outstanding = expected - done
    logging.info(
        f"outstanding_cell_keys[{config.get('run_name', run_dir.name)}]: "
        f"{len(expected)} expected, {len(expected & done)} done, "
        f"{len(outstanding)} outstanding"
    )
    return outstanding


def main(argv: list[str] | None = None) -> None:
    """Entry point: resolve the lane, provision/serve/sweep, spool, maybe teardown.

    ``SystemExit`` from argument parsing, ``selected_model()``, ``LEAN_SHARD``
    without ``--no-s3`` (the GUARD below), or ``select_verifier()`` -- all
    before any AWS call. Also before any AWS call: unless ``--force-rerun``
    or ``all_rows.jsonl`` doesn't exist yet, calls
    :func:`outstanding_cell_keys` and returns normally -- no provisioning,
    serving, sweep or spool -- when nothing is outstanding.

    Past those checks every path makes live, billable AWS calls. The sweep
    runs with ``resume=not --force-rerun``, so a relaunched lane picks up
    from on-disk ``all_rows.jsonl`` regardless of whether the crashed
    attempt reached the S3 spool -- true because ``spool_to_s3`` keeps that
    file across its prune (see its docstring).

    `argv` is a parameter so tests can call this without a subprocess.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Deduction-phase driver: serves ONE Lean theorem-proving "
            "checkpoint on one EC2 box and runs one runner.sweep of "
            "replicates against it."
        )
    )
    parser.add_argument(
        "--teardown",
        action="store_true",
        default=False,
        help=(
            "Terminate this lane's EC2 instance after the sweep (or after "
            "a failure) and exit. STANDALONE USE ONLY: under the fleet, "
            "the supervisor owns instance lifecycle and tears the box "
            "down itself once every phase scheduled for this lane has "
            "finished -- do not pass this flag from fleet-driven "
            "automation."
        ),
    )
    parser.add_argument(
        "--no-s3",
        action="store_true",
        default=False,
        help=(
            "Skip the end-of-run S3 spool sync (spool_to_s3) and leave "
            "this lane's replicate rows on local disk only."
        ),
    )
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        default=False,
        help=(
            "Regenerate EVERY cell, including ones that already have a "
            "proof, and move the existing all_rows.jsonl aside first. For "
            "decontaminating a lane whose cells were generated on more "
            "than one hardware config -- resume alone cannot do this, "
            "because it (correctly) skips cells that already have content."
        ),
    )
    args = parser.parse_args(argv)

    key = selected_model()
    # This line is the corpus gate (build_config's "Post-cutoff corpus gate")
    # for EVERY path through main, including --no-s3 and --force-rerun: it
    # runs before provisioning, serving or any other AWS call below.
    config = build_config(key)
    run_dir = runner.results_root() / "runs" / config["run_name"]

    # GUARD -- sharded lanes must not spool. `spool_to_s3`'s destination
    # prefix is keyed on the model, so every shard would upload its partial
    # all_rows.jsonl over the canonical object the analysis reads: last
    # writer wins and the lane silently reports one shard as the whole run.
    # Shards stay local until scripts/deduction/merge_lean_shards.py folds
    # them into the canonical run and spools that. Read off the config
    # (which owns the LEAN_SHARD read) rather than the environment again.
    if config["theorems"].get("shard") and not args.no_s3:
        raise SystemExit(
            f"LEAN_SHARD={config['theorems']['shard']!r} requires --no-s3: a shard "
            f"would overwrite the canonical "
            f"s3://{SPOOL_BUCKET}/{runner.spool_prefix()}/scaling_{key}/ objects "
            "with its partial rows.\n"
            "Fix: re-run this shard with --no-s3, then merge and spool with "
            "`scripts/deduction/merge_lean_shards.py <key> --n <n> "
            "--expect-cells <N> --expect-sanity <N> --spool`."
        )

    # Resolved -- and any SystemExit raised -- before provisioning.
    verifier = select_verifier()

    # Before spending real money (a fresh box, a served checkpoint, a whole
    # sweep), check whether this lane has anything left to do. Two cases
    # bypass the check rather than computing it: --force-rerun always means
    # "provision anyway", so computing it first would be wasted corpus I/O;
    # and no all_rows.jsonl yet means everything is trivially outstanding,
    # so calling outstanding_cell_keys would just re-derive that the hard
    # way. Depends on spool_to_s3 keeping all_rows.jsonl across its prune --
    # see that function's docstring.
    all_rows_path = run_dir / "all_rows.jsonl"
    if args.force_rerun:
        logging.info(
            f"main[{key}]: --force-rerun set; skipping the outstanding-cell "
            "check and provisioning unconditionally to regenerate every cell."
        )
    elif not all_rows_path.exists():
        logging.info(
            f"main[{key}]: no {all_rows_path} yet; nothing recorded for this "
            "run, so the whole lane is outstanding -- provisioning."
        )
    else:
        outstanding = outstanding_cell_keys(config, run_dir)
        if not outstanding:
            logging.info(
                f"main[{key}]: 0 cells outstanding in {run_dir} -- every "
                "expected cell is already recorded. Nothing to do; exiting "
                "WITHOUT provisioning, serving, sweeping or spooling."
            )
            return
        logging.info(
            f"main[{key}]: {len(outstanding)} cell(s) outstanding in "
            f"{run_dir}; provisioning to generate them."
        )

    logging.info(
        f"main[{key}]: provisioning (idempotent -- reattaches to this "
        f"lane's live 'scaling-{key}'-tagged instance if one already "
        "exists, e.g. the one the induction phase provisioned; otherwise "
        "launches a fresh one) ..."
    )
    ec2.provision_spot_instance()

    n = 0
    try:
        with ec2.serve_model(key):
            # Provenance sidecar: snapshot the serving stack inside the serve
            # block (the landed box is the one that generates), so
            # spool_to_s3 carries it with the rows. A relaunch appends a
            # fresh timestamped snapshot rather than overwriting, so a
            # resume on different hardware stays visible in the log.
            cfg = ec2.server_config(key)
            if cfg is not None:
                import datetime

                import yaml

                # mkdir first: runner.sweep creates run_dir itself, but this
                # sidecar writes before the sweep runs.
                run_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                with (run_dir / "server_config.yaml").open("a") as sink:
                    yaml.safe_dump([{"captured_utc": stamp, **cfg}],
                                   sink, default_flow_style=False, indent=4)
            if args.force_rerun:
                # Move old rows aside rather than appending on top: with
                # resume=False the sweep still appends to all_rows.jsonl, so
                # superseded and fresh rows for one key would otherwise share
                # a file with only line order to tell them apart. The
                # archive stays in run_dir so spool_to_s3 carries it to S3
                # under its own key.
                old = run_dir / "all_rows.jsonl"
                if old.exists():
                    import datetime

                    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
                        "%Y%m%dT%H%M%SZ"
                    )
                    archived = run_dir / f"all_rows_SUPERSEDED-{stamp}.jsonl"
                    old.rename(archived)
                    logging.warning(
                        f"main[{key}]: --force-rerun: archived {old.name} -> "
                        f"{archived.name} ({archived.stat().st_size} bytes); "
                        "regenerating ALL cells on the current box."
                    )
            n = runner.sweep(
                config, run_dir, resume=not args.force_rerun, verifier=verifier
            )
        logging.info(f"main[{key}]: sweep wrote {n} cell row(s) to {run_dir}")
        if args.no_s3:
            logging.info(f"main[{key}]: --no-s3 set; leaving replicate rows on local disk.")
        else:
            spool_to_s3(run_dir, key)
    finally:
        # In the finally block so a lane launched with --teardown still
        # tears its box down even if the sweep raised.
        if args.teardown:
            logging.info(f"main[{key}]: --teardown set; shutting down this lane's instance.")
            ec2.shutdown_instance()

    print(f"DEDUCTION LANE COMPLETE: {key} ({n} cell row(s)) run_dir={run_dir}", flush=True)


if __name__ == "__main__":
    main()
