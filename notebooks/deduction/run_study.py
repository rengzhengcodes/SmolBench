"""Per-lane driver for the DEDUCTION side of the family-ladder scaling study.

WHAT THIS IS: one invocation serves exactly ONE checkpoint on one EC2 box and
runs one ``smolbench.deduction.lean.runner.sweep`` against it. The fleet
supervisor (``scripts/fleet/run_fleet.py``) launches up to 21 of these, one per
lane; each reattaches to the box its induction phase already provisioned, by
reusing that phase's ``EC2_EXPERIMENT_TAG`` and state file.
``MODELS``/``COT_ARGS`` are loaded BY FILE PATH from
``notebooks/induction/run_study.py`` (the roster's single source of truth),
never ``import run_study``: both trees ship a module of that name.

MODULE IMPORT ORDER is load-bearing. ``smolbench.evals.providers.ec2`` freezes
``EC2_EXPERIMENT_TAG``, ``EC2_VLLM_IMAGE``, ``EC2_INSTANCE_TYPES`` and
``EC2_REGIONS`` into module constants at import time, so this file's
``os.environ.setdefault`` calls (values from ``lane_env_defaults``) must land
before that module is first imported -- including transitively, via the
induction module's own ``load_dotenv`` (no ``override=True``, so it can never
beat an already-set value). Get the order wrong and nothing raises:
this lane's tag, state file and vLLM image silently drift, and two lanes swap
served checkpoints on a live billing box. ``setdefault``, never assignment, is
what lets a fleet-exported value win. Import also raises ``SystemExit`` when
``EC2_EXPERIMENT_TAG`` does not name this lane's model, because lanes sharing a
tag adopt each other's instance and generate rows under the wrong model.

LIFECYCLE, in ``main`` order: (1) parse arguments; (2) resolve ``LEAN_MODEL``
and build the sweep config; (3) resolve ``LEAN_VERIFY`` -- steps 1-3 all run
BEFORE any AWS call, so a configuration mistake never lands on a billing box;
(4) provision (idempotent: reattaches); (5) serve the checkpoint; (6) sweep,
then spool to S3 once at the end; (7) tear down, from a ``finally`` and only
under ``--teardown``, which is for STANDALONE runs (under the fleet the
supervisor owns instance lifecycle). COST: steps 4-6 make live AWS calls,
billed for as long as the box stays up.

Environment: ``LEAN_MODEL`` (required; one key of ``MODELS``);
``LEAN_STATE_FILE`` (optional EC2 state file, default
``.ec2_state_scaling_<LEAN_MODEL>.json`` -- a bare or relative name resolves
against ``REPO_ROOT``, which is how both phases find the same box);
``LEAN_RUN_NAME``, ``LEAN_SHARD``, ``LEAN_CELL_WHITELIST`` (optional, read at
``build_config`` call time rather than at import); ``LEAN_VERIFY`` --
``"defer"`` (the default) passes a ``NullVerifier`` that never imports
``lean_dojo`` and records every verdict ``"unverified"``, leaving real checking
to the later pass ``scripts/deduction/lean_verify_rows.py``, while ``"real"``
verifies inline.

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

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Anchoring + S3-spool constants (pure; no environment or filesystem effects)
# ---------------------------------------------------------------------------
# This file is <repo>/notebooks/deduction/run_study.py, so parents[0] is
# .../notebooks/deduction, parents[1] is .../notebooks, and parents[2] is
# the repo root. This anchors via __file__, never the cwd, because the
# fleet, a notebook kernel, or a bare shell may launch this file from any
# working directory.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: Same bucket and region ``scripts/fleet/run_fleet.py``'s own
#: ``sync_deduction_spool`` uses for the induction-phase results store.
#: This study's whole S3 footprint lives in one bucket. This value is a
#: plain literal (not imported from ``run_fleet``), so this file has no
#: dependency on that off-limits module.
SPOOL_BUCKET: str = "smolbench-results-414266451290"
SPOOL_REGION: str = "us-west-2"
#: Differs from ``run_fleet.sync_deduction_spool``'s own
#: ``"deduction/runs"`` destination prefix in spelling only -- same value,
#: chosen independently here. This file owns its own spool contract end to
#: end (upload-verify-prune), instead of delegating to that off-limits
#: script.
SPOOL_PREFIX: str = "deduction/runs"


def lane_env_defaults(
    key: str, *, repo_root: Path, state_file: str | None = None
) -> dict[str, str]:
    """Derive this lane's four ``EC2_*``/``SMOLBENCH_LEAN_RESULTS`` defaults.

    Pure: reads only its arguments and returns a fresh dict, so this module's
    top-level code stays the only thing that touches ``os.environ`` (via
    ``setdefault``, before the first import of
    ``smolbench.evals.providers.ec2``). It does NOT validate `key` against
    ``MODELS``: that table is not loaded yet when this is called (see the
    module docstring's import-order note).

    Parameters
    ----------
    state_file : str or None
        ``None`` derives ``repo_root / f".ec2_state_scaling_{key}.json"``; a
        bare or relative name resolves against `repo_root`, NOT the process cwd
        -- both phases anchoring the same bare name to the same root is how
        this lane reattaches to induction's box. Absolute names are used as-is.

    Returns
    -------
    dict[str, str]
        ``EC2_EXPERIMENT_TAG`` (``f"scaling-{key}"``), ``EC2_STATE_FILE``
        (absolute), ``EC2_VLLM_IMAGE`` (digest-pinned; must match the image the
        induction phase already serves under, or reattaching swaps images
        mid-study) and ``SMOLBENCH_LEAN_RESULTS``
        (``repo_root/notebooks/deduction/results``, set explicitly so output
        location does not depend on how ``smolbench`` is installed).
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


# ---------------------------------------------------------------------------
# Env setdefaults -- MUST run before smolbench.evals.providers.ec2 is imported by
# anything (directly or transitively). See the module docstring's "MODULE
# IMPORT ORDER" section for the full mechanical justification.
# ---------------------------------------------------------------------------
# Read RAW, unvalidated. The table that would let us validate LEAN_MODEL
# (MODELS, loaded below) is not available yet. Validating it here would
# require loading that table first, which would import smolbench.evals.providers.ec2
# too early. Validation waits for selected_model(), called later from
# main().
_RAW_LEAN_MODEL: str = os.environ.get("LEAN_MODEL", "").strip()
_RAW_LEAN_STATE_FILE: str | None = os.environ.get("LEAN_STATE_FILE") or None

if _RAW_LEAN_MODEL:
    for _env_name, _env_value in lane_env_defaults(
        _RAW_LEAN_MODEL, repo_root=REPO_ROOT, state_file=_RAW_LEAN_STATE_FILE
    ).items():
        # Use setdefault, NEVER a bare assignment: a value the fleet
        # supervisor (or an interactive shell) already exported into this
        # process's environment must always win over this file's own
        # default.
        os.environ.setdefault(_env_name, _env_value)
    del _env_name, _env_value

    # GUARD -- cross-lane box adoption. setdefault above means an
    # EC2_EXPERIMENT_TAG already in the environment WINS. This is correct
    # when a fleet supervisor overrides it per lane, but catastrophic when
    # the value is shared: boxes are discovered by tag whenever a state
    # file is absent (``_recover_tagged_instance``), so a second lane
    # started under the same tag ADOPTS the first lane's instance and
    # serves its own model on top of it. Rows generated after such a swap
    # get attributed to the wrong model.
    #
    # keys.env ships ``EC2_EXPERIMENT_TAG=scaling-standalone`` as a
    # standalone-run safety default, and a launcher that sources keys.env
    # with ``set -a`` exports it into every lane -- which is how two lanes
    # end up sharing a tag.
    #
    # A lane's tag must name its lane. Fail loudly, rather than let a run
    # produce mislabelled data.
    _TAG = os.environ.get("EC2_EXPERIMENT_TAG", "")
    if _RAW_LEAN_MODEL not in _TAG:
        raise SystemExit(
            f"EC2_EXPERIMENT_TAG={_TAG!r} does not name this lane's model "
            f"({_RAW_LEAN_MODEL!r}).\n"
            "Two lanes sharing a tag will adopt each other's EC2 instance and "
            "generate rows under the wrong model.\n"
            "Most likely cause: a launcher sourced notebooks/deduction/keys.env "
            "with `set -a`, exporting its standalone default and overriding the "
            "per-lane value this driver would otherwise install.\n"
            f"Fix: export EC2_EXPERIMENT_TAG=scaling-{_RAW_LEAN_MODEL} for this "
            "lane (or stop sourcing keys.env in the launcher)."
        )
    del _TAG
# else: LEAN_MODEL is unset/empty. Deriving a tag/state-file from an
# empty key (e.g. "scaling-") would be actively misleading, with no
# benefit: selected_model() (called later, from main()) raises an
# actionable SystemExit for exactly this case, before anything else in
# this module's runtime path does real work. So this file simply skips
# the whole setdefault block, instead of seeding it with a placeholder
# key.

# ---------------------------------------------------------------------------
# Load notebooks/induction/run_study.py BY FILE PATH -- the single source
# of truth for MODELS / COT_ARGS. Never use a bare `import run_study`:
# this repo's own deduction and induction trees each ship a same-named
# run_study.py, so a bare module-name import would be ambiguous the
# moment both are ever on sys.path in the same process. That is exactly
# the situation scripts/fleet/run_fleet.py is already in, and it uses this same
# by-path pattern for the same reason.
# ---------------------------------------------------------------------------
_INDUCTION_RUN_STUDY_PATH: Path = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
_induction_spec = importlib.util.spec_from_file_location(
    "deduction_induction_run_study", _INDUCTION_RUN_STUDY_PATH
)
_induction = importlib.util.module_from_spec(_induction_spec)
# MUST register in sys.modules BEFORE exec_module. A @dataclass decorator
# applied inside a module object not yet present in sys.modules raises
# `AttributeError: 'NoneType' object has no attribute '__dict__'` (some
# dataclass-machinery introspection resolves the defining module by
# looking it up in sys.modules by name). Without this line, the loaded
# module hits that same error at its first @dataclass.
sys.modules[_induction_spec.name] = _induction
_induction_spec.loader.exec_module(_induction)  # runs that file's own load_dotenv(...) etc.

#: Spec key -> short analysis tag. Imported, never re-declared -- see the
#: module docstring's "WHAT THIS IS" section.
MODELS: dict[str, str] = _induction.MODELS
#: Spec key -> per-request CoT-toggle kwargs, TOTAL over MODELS. Imported,
#: never re-declared.
COT_ARGS: dict[str, dict] = _induction.COT_ARGS

# ---------------------------------------------------------------------------
# Late imports: safe only now that (a) our own EC2_* setdefaults have
# landed, and (b) MODELS/COT_ARGS are bound. noqa: E402 matches
# notebooks/induction/run_study.py's own late-import convention, for the
# same reason: these imports are intentionally not at the top of the
# file.
# ---------------------------------------------------------------------------
from smolbench.evals.providers import ec2  # noqa: E402
from smolbench.deduction.lean import runner  # noqa: E402
from smolbench.deduction.lean.nullverify import NullVerifier  # noqa: E402


def selected_model() -> str:
    """Resolve and validate this lane's model key from ``LEAN_MODEL``.

    Deferred counterpart to the raw, unvalidated import-time read: ``MODELS``
    is guaranteed loaded by the time this runs. Raises ``SystemExit``, listing
    every valid key, if ``LEAN_MODEL`` is unset, empty or unknown.
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


def build_config(key: str) -> dict:
    """Build this lane's ``runner.sweep`` configuration.

    USER-LOCKED: every key is identical across all 21 checkpoints except
    ``run_name`` and the single ``models[0]`` entry, which is what lets a
    next-tactic success-rate difference point to the model rather than to a
    changed sweep. ``runner.sweep`` accepts every key verbatim. Callers must
    validate `key` first (e.g. ``selected_model()``): ``COT_ARGS`` is total over
    ``MODELS``, so any other key raises a bare ``KeyError``.

    Returns
    -------
    dict
        16 keys, including a ``theorems`` block selecting 300 of the
        ``replay_passing``/``novel_premises``/``val`` pool's theorems at seed 0,
        and a ``models[0]["extra_params"]`` that is a DEEP copy of
        ``COT_ARGS[key]``, so in-place mutation by a caller cannot corrupt that
        shared nested table for other lanes. Two further keys are conditional:
        ``theorems["shard"]`` under ``LEAN_SHARD``, and top-level
        ``cell_whitelist`` (path plus a ``runner.hash_cell_keys`` fingerprint of
        its sorted content, so ``manifest.json`` records which whitelist was in
        effect even if the file is later edited) under ``LEAN_CELL_WHITELIST``.

    Notes
    -----
    ``LEAN_SHARD``, ``LEAN_RUN_NAME`` and ``LEAN_CELL_WHITELIST`` are read at
    CALL time, never at import and never cached. ``run_name`` defaults to
    ``f"scaling_{key}"`` plus a ``_shard<i>of<n>`` suffix when sharding
    (matching ``scripts/fleet/run_fleet.py``'s ``Lane`` naming); an explicit
    ``LEAN_RUN_NAME`` wins verbatim. With ``LEAN_CELL_WHITELIST`` set this also
    does file I/O and can raise ``ValueError`` from
    ``runner.load_cell_whitelist`` -- before any AWS call.
    """
    # Optional theorem-stride shard ("i/n", passed through to
    # runner._select_theorems). The shard key is CONDITIONALLY present.
    # When LEAN_SHARD is unset, the theorems block stays byte-identical to
    # the unsharded study config. When sharding, the DEFAULT run_name
    # gains a _shard<i>of<n> suffix. This stops two concurrently running
    # shards from sharing a run directory: concurrent appends to one
    # all_rows.jsonl from separate processes interleave large rows and
    # corrupt the file. An explicit LEAN_RUN_NAME still wins verbatim, so
    # a caller overriding it for a sharded launch owns that uniqueness
    # themselves.
    shard = os.environ.get("LEAN_SHARD", "").strip()
    shard_suffix = ""
    if shard:
        shard_suffix = "_shard" + shard.replace("/", "of")
    run_name = os.environ.get("LEAN_RUN_NAME", "").strip() or f"scaling_{key}{shard_suffix}"
    theorems: dict[str, Any] = {
        "source": "replay_passing",
        "kind": "novel_premises",
        "split": "val",
        "limit": 300,
        "seed": 0,
    }
    if shard:
        theorems["shard"] = shard

    cfg: dict[str, Any] = {
        "run_name": run_name,
        "seed": 0,
        "temperature": 0.7,
        "max_tokens": 32768,
        "request_timeout": 1800,
        "max_retries": 2,
        "dojo_timeout": 300,
        "concurrent_gen": True,
        "skip_trivial": True,
        "k": {"strategy": "last"},
        "n_replicates": 1,
        "theorems": theorems,
        "rungs": ["stepk:1", "hint:2", "noise:3", "hint:3"],
        "theorem_workers": 4,
        "max_concurrency": 8,
        "models": [
            {
                "provider": "ec2",
                "model": key,
                "display_name": key,
                "extra_params": copy.deepcopy(COT_ARGS[key]),
            }
        ],
    }

    # Optional LEAN_CELL_WHITELIST sidecar stamp -- CONDITIONALLY present,
    # mirroring the shard key above. Unlike `shard`, this value does NOT
    # drive `runner.sweep`'s own behavior: `runner.sweep` reads
    # `LEAN_CELL_WHITELIST` directly from the environment itself (see that
    # function's docstring). This function writes this key purely so the
    # run's `manifest.json` sidecar (`sweep` stamps `{"config": config,
    # ...}` verbatim -- see runner.py's module docstring, "Output layout")
    # records WHICH whitelist file was in effect for this run,
    # without embedding the (possibly large) key list a second time.
    # Recording the path alone would not be enough, because a whitelist
    # file can be edited or replaced after a run starts. So
    # `runner.hash_cell_keys` fingerprints its SORTED content instead. A
    # reader can diff `sha256` against a fresh
    # `hash_cell_keys(runner.load_cell_whitelist(path))` call to confirm
    # the file on disk is the exact one this run used.
    # `runner.load_cell_whitelist` itself raises loudly on a missing or
    # malformed file, so an operator gets that failure HERE, before any
    # AWS call -- see this function's own Notes section.
    whitelist_path = os.environ.get("LEAN_CELL_WHITELIST", "").strip()
    if whitelist_path:
        cfg["cell_whitelist"] = {
            "path": whitelist_path,
            "sha256": runner.hash_cell_keys(runner.load_cell_whitelist(whitelist_path)),
        }

    return cfg


def select_verifier() -> Any:
    """Resolve the verifier object to hand to ``runner.sweep``, from ``LEAN_VERIFY``.

    ``NullVerifier()`` when ``LEAN_VERIFY`` is unset, empty or ``"defer"`` (the
    default; every verdict is then recorded ``"unverified"`` rather than
    replayed against a real Dojo); the ``smolbench.deduction.lean.verify``
    MODULE object -- not an instance, since ``runner.sweep`` calls its functions
    directly -- when it is exactly ``"real"``. That import lives inside the
    ``"real"`` branch so importing this file never requires ``lean_dojo``;
    ``"real"`` without it raises ``ImportError`` naming the fix
    (``uv sync --all-extras``). Any other value raises ``SystemExit``.
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

    END-OF-RUN ONLY: called once, after ``runner.sweep`` returns (`run_dir` is
    that sweep's output, ``runner.results_root() / "runs" / run_name``).
    ``sweep`` exposes no progress hook, so a crash mid-sweep leaves the rows
    unspooled on local disk until a relaunch reaches this call again.

    Two-phase, and the ordering is load-bearing: upload and verify EVERY file
    (in sorted, deterministic order) before pruning ANY, so a part-way failure
    cannot already have deleted files whose uploads are unconfirmed. Pruning
    keeps ``run_dir / "manifest.json"`` (so a later resume recognises the run
    without re-downloading the spool), then removes now-empty subdirectories
    deepest-first, swallowing ``OSError``; ``run_dir`` is never removed.

    Parameters
    ----------
    key : str
        Model spec key. The destination prefix
        ``f"{SPOOL_PREFIX}/scaling_{key}/"`` is built from this, NOT from
        ``run_dir.name``, so the S3 layout stays keyed on the MODEL even when
        ``LEAN_RUN_NAME`` renamed the run directory.
    client : Any, optional
        boto3 S3 client exposing ``upload_file`` and ``head_object``; ``None``
        lazily imports boto3 and builds one against `SPOOL_REGION` (boto3, not
        the ``aws`` CLI, which this repo does not depend on), so importing this
        file needs no AWS SDK and tests can inject a fake.

    Returns
    -------
    int
        Files uploaded and verified; ``0``, nothing uploaded or pruned, when
        `run_dir` is not a directory -- not an error, since a lane that produced
        nothing yet (or was already spooled) has nothing to sync.

    Raises
    ------
    RuntimeError
        If any upload fails verification (``head_object`` raised, or its
        ``"ContentLength"`` differs from the local size) -- raised BEFORE any
        pruning, naming the S3 key and both sizes.
    """
    if not run_dir.is_dir():
        logging.info(f"spool_to_s3[{key}]: no run directory at {run_dir}; nothing to sync.")
        return 0

    if client is None:
        import boto3  # lazy -- see docstring

        client = boto3.client("s3", region_name=SPOOL_REGION)

    dest_prefix = f"{SPOOL_PREFIX}/scaling_{key}/"
    files = sorted(p for p in run_dir.rglob("*") if p.is_file())

    # Phase 1: upload + verify EVERY file before deleting anything (see
    # docstring's "Two-phase" note for why this ordering is load-bearing).
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

    # Phase 2: every upload is verified, so pruning is now safe. This
    # keeps manifest.json so a later resume of this run recognises it
    # already exists, without re-downloading the whole spool from S3
    # first just to check.
    manifest_path = run_dir / "manifest.json"
    for path in files:
        if path != manifest_path:
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


def main(argv: list[str] | None = None) -> None:
    """Entry point: resolve the lane, provision/serve/sweep, spool, maybe teardown.

    ``SystemExit`` comes from argument parsing, ``selected_model()`` (unset or
    unknown ``LEAN_MODEL``) or ``select_verifier()`` (invalid ``LEAN_VERIFY``)
    -- all three BEFORE any AWS call. Past those checks every path makes live,
    billable AWS calls (``ec2.provision_spot_instance()``,
    ``ec2.serve_model()``, and ``ec2.shutdown_instance()`` under
    ``--teardown``). The sweep runs with ``resume=not --force-rerun``, so a
    relaunched lane picks up from the on-disk ``all_rows.jsonl`` whether or not
    the crashed attempt ever reached the S3 spool. `argv` is a parameter so
    tests and notebook cells can call this without a subprocess.
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
    config = build_config(key)
    run_dir = runner.results_root() / "runs" / config["run_name"]

    # Resolved -- and any SystemExit raised -- BEFORE provisioning: see the
    # module docstring's "LIFECYCLE" step 3.
    verifier = select_verifier()

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
            # Provenance sidecar: snapshot the serving stack INSIDE the
            # serve block (the landed box is the one that generates), and
            # write it into run_dir so spool_to_s3 carries it with the
            # rows. One file per run, not per row: a deduction run serves
            # on one box unless it crashes. A relaunch APPENDS a fresh
            # timestamped snapshot instead of overwriting, so a resumed
            # run that landed on different hardware stays visible in the
            # log.
            cfg = ec2.server_config(key)
            if cfg is not None:
                import datetime

                import yaml

                # mkdir first: runner.sweep creates run_dir itself, but
                # this sidecar writes BEFORE the sweep runs.
                run_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                with (run_dir / "server_config.yaml").open("a") as sink:
                    yaml.safe_dump([{"captured_utc": stamp, **cfg}],
                                   sink, default_flow_style=False, indent=4)
            if args.force_rerun:
                # Move the old rows aside instead of appending on top of
                # them. With resume=False the sweep regenerates every
                # cell, but it still APPENDS to all_rows.jsonl. That would
                # leave both the superseded and the fresh row for each key
                # in one file, on different hardware, with nothing but
                # line order to tell them apart. Archiving removes that
                # confound, so it is part of the operation, not a
                # courtesy. The archive stays inside run_dir, so
                # spool_to_s3 carries it to S3 under its own key: this
                # preserves the superseded data and labels it plainly,
                # and never silently drops it.
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
        # tears its box down even if the sweep itself raised -- see the
        # module docstring's "LIFECYCLE" step 7.
        if args.teardown:
            logging.info(f"main[{key}]: --teardown set; shutting down this lane's instance.")
            ec2.shutdown_instance()

    print(f"DEDUCTION LANE COMPLETE: {key} ({n} cell row(s)) run_dir={run_dir}", flush=True)


if __name__ == "__main__":
    main()
