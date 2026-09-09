"""Run one DEDUCTION study lane on one EC2 box.

Fleet launches up to 21 lanes, each reattaching to induction's EC2 tag/state box.
Load the induction roster by path because both study trees have ``run_study``.
Set ``EC2_*`` before importing ``providers.ec2``: it freezes them at import,
otherwise lanes can silently serve each other's checkpoint on a billing box.
"""

import argparse
import copy
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any

# These imports must remain before ``setdefault`` and ec2-free; a new import
# reaching ``providers.ec2`` freezes unseeded EC2_* values without an error.
from smolbench.evals.experiment import validate_experiment_tag
from smolbench.evals.spool import spool_prefix
from smolbench.evals.study_config import load_study_config
from smolbench.evals.retired_markers import is_retired

logging.basicConfig(level=logging.INFO)

# Anchor paths to ``__file__``, never cwd: fleet and notebook launches vary it.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: Shared spool location from the study config, so it cannot drift from results_store; the
#: loader is memoized by resolved path, so the second call parses nothing and needs no temporary.
SPOOL_BUCKET: str = load_study_config().results.bucket
SPOOL_REGION: str = load_study_config().results.region
#: Resolve ``spool_prefix()`` at call time so late ``LEAN_SPOOL_PREFIX`` applies.

#: Latest served-weight release: the last Hugging Face commit touching a weight file at each lane's
#: pinned ``--revision`` (resolved 2026-08-30); corpus dates must clear it.
ROSTER_LATEST_RELEASE: str = "2026-06-03"


def lane_env_defaults(
    key: str, *, repo_root: Path, state_file: str | None = None
) -> dict[str, str]:
    """Derive this lane's EC2 and results defaults.

    Stay pure because ``setdefault`` must precede ``providers.ec2``; MODELS is unavailable then.

    Parameters
    ----------
    key : str
        Model lane key.
    repo_root : Path
        Repository root anchoring relative state-file paths.
    state_file : str | None, optional
        State-file path; relative paths use ``repo_root`` so both phases attach to one box.

    Returns
    -------
    dict[str, str]
        Lane environment defaults.
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


# Set defaults before any ``providers.ec2`` import; loading MODELS here is too
# early, so ``selected_model`` validates the raw value later.
_RAW_LEAN_MODEL: str = os.environ.get("LEAN_MODEL", "").strip()
_RAW_LEAN_STATE_FILE: str | None = os.environ.get("LEAN_STATE_FILE") or None

if _RAW_LEAN_MODEL:
    for _env_name, _env_value in lane_env_defaults(
        _RAW_LEAN_MODEL, repo_root=REPO_ROOT, state_file=_RAW_LEAN_STATE_FILE
    ).items():
        # Never overwrite a fleet or shell value.
        os.environ.setdefault(_env_name, _env_value)
    del _env_name, _env_value

    # Tags discover boxes without state files; shared tags silently attribute
    # rows to the wrong model. Validate the bare fleet tag first, because fleet
    # teardown terminates by tag; shards belong only in ``run_name``.
    _TAG = os.environ.get("EC2_EXPERIMENT_TAG", "")
    try:
        validate_experiment_tag(_TAG, None)
    except ValueError as exc:
        # Guards raise SystemExit before AWS; the earlier memoized config load
        # means this ValueError is a tag refusal, not a broken config.
        raise SystemExit(
            f"{exc}\n"
            f"Fix: export EC2_EXPERIMENT_TAG=scaling-{_RAW_LEAN_MODEL} for this "
            "lane (or stop sourcing keys.env in the launcher)."
        ) from exc

    # Never use containment: ``glm-4.7`` prefixes ``glm-4.7-flash``.
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
# Unset LEAN_MODEL must not seed ``scaling-``; selected_model raises before work.

# Load by path: both trees expose ``run_study`` on sys.path.
_INDUCTION_RUN_STUDY_PATH: Path = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
_induction_spec = importlib.util.spec_from_file_location(
    "deduction_induction_run_study", _INDUCTION_RUN_STUDY_PATH
)
_induction = importlib.util.module_from_spec(_induction_spec)
# Register before exec_module: dataclass resolves its module through sys.modules.
sys.modules[_induction_spec.name] = _induction
_induction_spec.loader.exec_module(_induction)  # runs that file's own load_dotenv(...) etc.

#: Spec key to short analysis tag; imported roster, never redeclare its source of truth.
MODELS: dict[str, str] = _induction.MODELS
#: Spec key to per-request CoT-toggle kwargs, total over MODELS; imported settings, never redeclare.
COT_ARGS: dict[str, dict] = _induction.COT_ARGS

# Late imports require EC2_* defaults and MODELS/COT_ARGS.
from smolbench.evals.providers import ec2  # noqa: E402
from smolbench.evals import _aws, results_store  # noqa: E402
from smolbench.deduction.lean import corpus, runner  # noqa: E402
from smolbench.deduction.lean.nullverify import NullVerifier  # noqa: E402


def selected_model() -> str:
    """Resolve and validate this lane's model key from ``LEAN_MODEL``.

    Deferred until ``MODELS`` is loaded.
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

    Read at call time so calls can change it; it couples theorem selection and
    decoding (replicate ``i`` uses ``seed + i``).
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
            "it to use 0, or set it to an integer."
        ) from None


# Schema names for ``notebooks/deduction/sweep.yaml``.
#: Anchor the committed sweep config to REPO_ROOT, never cwd.
SWEEP_CONFIG_PATH: Path = REPO_ROOT / "notebooks" / "deduction" / "sweep.yaml"

#: Required names prevent silent fallback to runner.sweep library defaults.
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

#: Required ``theorems`` names; seed and shard are lane identity.
REQUIRED_SWEEP_THEOREM_KEYS: frozenset[str] = frozenset(
    {"source", "kind", "split", "limit"}
)

#: Per-lane names must not appear in YAML: overlays would silently replace them.
RESERVED_SWEEP_KEYS: frozenset[str] = frozenset(
    {"run_name", "seed", "models", "cell_whitelist"}
)

#: Theorem seed and shard come from the lane environment.
RESERVED_SWEEP_THEOREM_KEYS: frozenset[str] = frozenset({"seed", "shard"})


def _stamp_path(path: Path) -> str:
    """Format a path for manifest provenance.

    Use repo-relative paths so checkout locations do not change manifests;
    outside paths have no relative spelling and occur only through the test seam.

    Parameters
    ----------
    path : Path
        Path to record.

    Returns
    -------
    str
        Repo-relative path, otherwise absolute.
    """
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def build_config(key: str, *, sweep_config_path: Path | None = None) -> dict:
    """Load sweep knobs and overlay lane identity.

    Use ``runner.load_sweep_config``, shared with ``cli.cmd_run_sweep``, so
    the schema has one reader. Deep-copy the shared config so calls cannot
    mutate each other. Keep all knobs equal across 21 checkpoints except
    ``run_name`` and ``models[0]`` so
    differences measure models, and stamp the YAML SHA-256 in ``manifest.json``.
    Reject reserved names before missing names: overlays silently replace the
    former, while missing names silently use runner defaults. Reject corpora
    before the latest roster release because a checkpoint may have trained on
    their theorems. ``LEAN_SHARD``, ``LEAN_RUN_NAME``, ``LEAN_CELL_WHITELIST``,
    ``LEAN_CORPUS_SPLIT``, and ``LEAN_SEED`` are read at call time; the default
    run name is ``scaling_<key>`` with ``_shard<i>of<n>`` when sharded.

    Parameters
    ----------
    key : str
        Lane model key.
    sweep_config_path : Path | None, optional
        Alternate sweep config.

    Returns
    -------
    dict
        runner.sweep configuration.

    Raises
    ------
    SystemExit
        Corpus or schema refusal.
    FileNotFoundError, ValueError, yaml.YAMLError
        Broken or missing sweep config, not a lane misconfiguration.
    """
    # Gate before config construction and AWS calls.
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
    # ISO YYYY-MM-DD strings sort chronologically.
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

    # Check reserved keys first; malformed ``theorems`` contributes no keys.
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

    # A non-mapping ``theorems`` reports missing keys rather than AttributeError.
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

    # Shards need distinct directories: concurrent all_rows.jsonl appends corrupt rows.
    shard = os.environ.get("LEAN_SHARD", "").strip()
    shard_suffix = ""
    if shard:
        shard_suffix = "_shard" + shard.replace("/", "of")
    run_name = os.environ.get("LEAN_RUN_NAME", "").strip() or f"scaling_{key}{shard_suffix}"
    seed = resolve_lean_seed()

    # Deep-copy nested structures so calls remain private.
    cfg: dict[str, Any] = copy.deepcopy(loaded)

    cfg["run_name"] = run_name
    cfg["seed"] = seed

    theorems: dict[str, Any] = cfg["theorems"]
    theorems["seed"] = seed
    # Fix the corpus family while allowing the per-run split.
    yaml_split = theorems["split"]
    theorems["split"] = os.environ.get("LEAN_CORPUS_SPLIT", yaml_split).strip() or yaml_split
    if shard:
        theorems["shard"] = shard

    # Copy COT_ARGS so a caller cannot corrupt other lanes.
    cfg["models"] = [
        {
            "provider": "ec2",
            "model": key,
            "display_name": key,
            "extra_params": copy.deepcopy(COT_ARGS[key]),
        }
    ]

    # runner.sweep writes config verbatim; relative paths avoid checkout drift.
    cfg["sweep_config"] = {
        "path": _stamp_path(config_path),
        "sha256": sweep_config_sha256,
    }

    # Fingerprint sorted whitelist content because its file can change mid-run.
    whitelist_path = os.environ.get("LEAN_CELL_WHITELIST", "").strip()
    if whitelist_path:
        cfg["cell_whitelist"] = {
            "path": whitelist_path,
            "sha256": runner.hash_cell_keys(runner.load_cell_whitelist(whitelist_path)),
        }

    return cfg


def select_verifier() -> Any:
    """Select the ``LEAN_VERIFY`` verifier for ``runner.sweep``.

    Default ``defer`` records ``unverified`` for later checking; ``real`` returns its module because
    runner calls module functions. Keep the real import local so this module
    does not require the ``lean`` extra.
    """
    choice = os.environ.get("LEAN_VERIFY", "defer").strip() or "defer"
    if choice == "defer":
        return NullVerifier()
    if choice == "real":
        # verify.py imports lean_dojo, which is only needed for real verification.
        from smolbench.deduction.lean import verify

        return verify
    raise SystemExit(f"LEAN_VERIFY={choice!r} is not valid; expected 'defer' or 'real'.")


def spool_to_s3(run_dir: Path, key: str, *, client: Any = None) -> int:
    """Upload, verify, then prune a lane directory.

    Call only after sweep because it has no progress hook; crashes leave rows
    local until relaunch. Verify every sorted file before pruning so partial
    failures retain local data. Keep ``manifest.json``, ``all_rows.jsonl``,
    and retired siblings (including ``all_rows_SUPERSEDED-<stamp>.jsonl``):
    resume reads per-cell and sanity state only from all_rows.jsonl; deleting
    it would re-provision and regenerate already durable rows at extra cost.

    Parameters
    ----------
    run_dir : Path
        Local directory.
    key : str
        Model key for the destination prefix, even with LEAN_RUN_NAME.
    client : Any, optional
        Lazy boto3 client or injected fake.

    Returns
    -------
    int
        Verified file count; ``0`` for a missing directory.

    Raises
    ------
    RuntimeError
        Upload verification failure before pruning.
    """
    if not run_dir.is_dir():
        logging.info(f"spool_to_s3[{key}]: no run directory at {run_dir}; nothing to sync.")
        return 0

    if client is None:
        client = _aws.fresh_client("s3", SPOOL_REGION)

    dest_prefix = f"{spool_prefix()}/scaling_{key}/"
    files = sorted(p for p in run_dir.rglob("*") if p.is_file())

    # Verify every upload before deleting anything.
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

    # Verified uploads make pruning safe; retain resume state.
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
    """Return resume-mode cell keys not recorded on disk.

    Enumerate runner's own selectors before AWS provisioning; retaining
    ``all_rows.jsonl`` prevents every lane appearing outstanding. Drop a
    theorem only for a recorded sanity failure, and build runner row keys.
    This duplicates the sweep predicate, so update it with sweep changes:
    under-counting would skip a lane with real cells left. No test catches this
    drift except an end-to-end comparison against a live sweep.

    Parameters
    ----------
    config : dict
        Sweep configuration.
    run_dir : Path
        Run directory; absent rows mean nothing done.

    Raises
    ------
    ValueError
        Invalid theorem selection or whitelist.

    Returns
    -------
    set[tuple]
        Unrecorded cell keys.
    """
    all_rows_path = run_dir / "all_rows.jsonl"

    # Match runner's whitelist read for theorem and cell filtering.
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
        # Only recorded sanity failures suppress theorem cells.
        if sanity_done.get(theorem.full_name) in runner.SANITY_FAILURE_VERDICTS:
            continue
        for k in runner._k_indices(theorem, k_strategy):
            for rung in rungs:
                chain, level_str = rung.split(":", 1)
                level = int(level_str)
                # Match runner's trivial-rung skip.
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
    """Resolve, run, spool, and optionally tear down a lane.

    Reject arguments, lane config, shard spooling, and verifier selection
    before AWS. Skip provisioning when no cells remain; resume relies on the
    retained ``all_rows.jsonl`` even if a prior run crashed before spooling.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command-line arguments for direct tests.
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
            "repairing a lane whose cells were generated on more "
            "than one hardware config -- resume alone cannot do this, "
            "because it (correctly) skips cells that already have content."
        ),
    )
    args = parser.parse_args(argv)

    key = selected_model()
    # Corpus gate for every path, before any AWS call.
    config = build_config(key)
    run_dir = runner.results_root() / "runs" / config["run_name"]

    # Shards must not spool: a model-keyed destination lets the last partial
    # all_rows.jsonl overwrite canonical results. Merge them first with
    # scripts/deduction/merge_lean_shards.py.
    if config["theorems"].get("shard") and not args.no_s3:
        raise SystemExit(
            f"LEAN_SHARD={config['theorems']['shard']!r} requires --no-s3: a shard "
            f"would overwrite the canonical "
            f"s3://{SPOOL_BUCKET}/{spool_prefix()}/scaling_{key}/ objects "
            "with its partial rows.\n"
            "Fix: re-run this shard with --no-s3, then merge and spool with "
            "`scripts/deduction/merge_lean_shards.py <key> --n <n> "
            "--expect-cells <N> --expect-sanity <N> --spool`."
        )

    # Resolve before provisioning.
    verifier = select_verifier()

    # Avoid billable work when no cells remain; force-rerun and absent rows
    # are already known to require provisioning.
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
            # Snapshot the generating server; append so resumed hardware remains visible.
            cfg = ec2.server_config(key)
            if cfg is not None:
                import yaml

                # This sidecar precedes runner.sweep's directory creation.
                run_dir.mkdir(parents=True, exist_ok=True)
                stamp = results_store.format_run_ts(results_store.utcnow())
                with (run_dir / "server_config.yaml").open("a") as sink:
                    yaml.safe_dump([{"captured_utc": stamp, **cfg}],
                                   sink, default_flow_style=False, indent=4)
            if args.force_rerun:
                # resume=False still appends; archive old rows so superseded
                # and fresh rows cannot share a file. Keep it for S3 upload.
                old = run_dir / "all_rows.jsonl"
                if old.exists():
                    stamp = results_store.format_run_ts(results_store.utcnow())
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
        # Teardown must run even when the sweep raises.
        if args.teardown:
            logging.info(f"main[{key}]: --teardown set; shutting down this lane's instance.")
            ec2.shutdown_instance()

    print(f"DEDUCTION LANE COMPLETE: {key} ({n} cell row(s)) run_dir={run_dir}", flush=True)


if __name__ == "__main__":
    main()
