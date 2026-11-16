"""Command-line runner of the attention replay: one model per process.

    python rebuttal/run_attention.py --model gemma-4-31b --smoke            # plan only
    python rebuttal/run_attention.py --model gemma-4-31b --seeds 0-9 --approved

Without ``--approved`` it prints the plan of ``attention_replay.plan_replay`` (sizes,
errors, storage estimate) and exits 0; it builds no AWS client. With ``--approved`` it
calls ``attention_replay.replay_model``, which provisions ONE billed spot GPU box,
captures the stored induction transcripts, shuts the box down and only then audits and
records what landed. A model runs per process so that a failure, or an expired AWS
session (they last 4 hours), stops one model and not the others; ``--seeds`` splits one
model across several runs.

Defaults follow the notebook's attention cells: the results root is the induction mirror
(``bedrock_trio.RESULTS_DIR / "induction"``, or the same under the smoke folder with
``--smoke``) and the destination is ``<RESULTS_S3>[/<smoke prefix>]/attention-v2``.

Exit codes: 0 every job that was sent passed the capture and the audit; 1 an exception
(also a refusal such as an unverified serve); 2 a bad command line; 3 some job failed
the capture or the content audit; 4 the box could not be shut down (it may still be
billing; the report is written first).

The module imports without touching AWS or the network.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent

#: Environment the EC2 provider reads WHEN IT IS IMPORTED (module-level constants), so
#: it must be set before anything imports ``smolbench.evals.providers``. ``setdefault``
#: keeps a value the caller already exported. The mirror is the fleet's weight cache (an
#: instance without it fetches the checkpoint anonymously from the hub and its workers
#: failed that way); 240 minutes is the provider's lifetime backstop, matching an AWS
#: session, instead of its 24-hour default.
PROVIDER_ENV_DEFAULTS: Dict[str, str] = {
    "EC2_S3_MODEL_CACHE": "s3://smolbench-model-cache-414266451290/hf",
    "EC2_S3_CACHE_REGION": "us-west-2",
    "EC2_MAX_LIFETIME_MIN": "240",
}
for _name, _value in PROVIDER_ENV_DEFAULTS.items():
    os.environ.setdefault(_name, _value)

# rebuttal/ is not a package. Run as a script this directory is already first on
# sys.path; the guard covers a caller that loaded the file by path.
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import attention_replay as ar  # noqa: E402 -- must follow the environment defaults above
from smolbench.evals.results_store import format_run_ts, utcnow  # noqa: E402

#: Per-batch ceiling (seconds) of one ``/attn`` call; 40 minutes.
DEFAULT_BATCH_TIMEOUT_S: int = 2400
#: Presigned-URL lifetime (seconds); must exceed the batch timeout.
DEFAULT_URL_TTL_S: int = 3600
#: Sub-folder of the destination holding the captures (the notebook's ``attention-v2``).
ATTENTION_SUBPREFIX: str = "attention-v2"

EXIT_OK: int = 0
EXIT_EXCEPTION: int = 1
EXIT_JOBS_FAILED: int = 3
EXIT_SHUTDOWN_FAILED: int = 4

#: How many plan errors / failed jobs the console lists; the full set is in the report file.
_LIST_LIMIT: int = 10

_SEED_PART = re.compile(r"^(\d+)(?:-(\d+))?$")


def parse_seeds(text: str) -> List[int]:
    """Parse a seed selection such as ``"0-9"``, ``"3"`` or ``"0,2,5-7"``.

    Parameters
    ----------
    text : str
        Comma-separated parts; each part is a non-negative integer or an inclusive
        range ``a-b`` with ``a <= b``.

    Returns
    -------
    List[int]
        The selected seeds, sorted, without duplicates.

    Raises
    ------
    argparse.ArgumentTypeError
        On an empty selection, a part that is not an integer or a range, or a range
        whose end lies below its start (argparse turns this into exit code 2).

    Examples
    --------
    >>> parse_seeds("0-3")
    [0, 1, 2, 3]
    >>> parse_seeds("7,2,2,4-5")
    [2, 4, 5, 7]
    """
    seeds = set()
    for part in text.split(","):
        match = _SEED_PART.match(part.strip())
        if match is None:
            raise argparse.ArgumentTypeError(
                f"bad seed selection {text!r}: {part.strip()!r} is not an integer or a range a-b"
            )
        first = int(match.group(1))
        last = int(match.group(2)) if match.group(2) is not None else first
        if last < first:
            raise argparse.ArgumentTypeError(f"bad seed range {part.strip()!r}: end is below start")
        seeds.update(range(first, last + 1))
    return sorted(seeds)


def default_locations(smoke: bool) -> Tuple[Path, str]:
    """Return the default ``(results root, S3 destination)``, as the notebook's cells build them.

    Parameters
    ----------
    smoke : bool
        Use the smoke folder and prefix: the bucket is append-only, so a smoke run gets
        its own sub-prefix and the protocol prefix stays clean.

    Returns
    -------
    Tuple[Path, str]
        ``bt.RESULTS_DIR[/<smoke prefix>] / "induction"`` and
        ``<bt.RESULTS_S3>[/<smoke prefix>]/attention-v2``.
    """
    bt = ar.bt
    results_dir = bt.RESULTS_DIR / bt.SMOKE_PREFIX if smoke else bt.RESULTS_DIR
    s3_root = bt.RESULTS_S3 + (f"/{bt.SMOKE_PREFIX}" if smoke else "")
    return results_dir / "induction", f"{s3_root}/{ATTENTION_SUBPREFIX}"


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser (see the module docstring for the flags' meaning)."""
    parser = argparse.ArgumentParser(
        prog="run_attention.py",
        description="Plan or run the attention replay of ONE model (a run is billed).",
    )
    parser.add_argument("--model", required=True, help="roster key, e.g. gemma-4-31b")
    parser.add_argument("--results-root", type=Path, default=None,
                        help="folder holding induction/<model>/seed=<s>/ (default: the induction mirror)")
    parser.add_argument("--s3-uri", default=None,
                        help="s3://bucket/prefix destination (default: <RESULTS_S3>/attention-v2)")
    parser.add_argument("--smoke", action="store_true",
                        help="use the smoke mirror folder and the smoke S3 prefix for the defaults")
    parser.add_argument("--seeds", type=parse_seeds, default=None,
                        help="only these seeds, e.g. 0-9 or 0,2,5-7 (default: every seed)")
    parser.add_argument("--approved", action="store_true",
                        help="launch the billed spot box; without it only the plan is printed")
    parser.add_argument("--allow-unverified-serve", action="store_true",
                        help="also run a model whose serving on the pinned image is unverified")
    parser.add_argument("--instance-types", nargs="+", default=None, metavar="TYPE",
                        help="instance types to hunt, overriding the model's list")
    parser.add_argument("--batch-timeout-s", type=int, default=DEFAULT_BATCH_TIMEOUT_S,
                        help="ceiling of one capture batch (default: %(default)s)")
    parser.add_argument("--url-ttl-s", type=int, default=DEFAULT_URL_TTL_S,
                        help="presigned-URL lifetime; must exceed --batch-timeout-s (default: %(default)s)")
    parser.add_argument("--audit-arrays", choices=("all", "sample"), default="all",
                        help="download every array for the audit, or one job per run (default: all)")
    parser.add_argument("--report-dir", type=Path, default=None,
                        help="where the JSON report goes (default: the results folder next to the mirror)")
    return parser


def _print_plan(model: str, results_root: Path, s3_uri: str, seeds: Optional[Sequence[int]]) -> int:
    """Print the offline plan and its errors; builds no AWS client. Returns the exit code."""
    plan = ar.plan_replay(results_root, [model], s3_uri=s3_uri, seeds=seeds)[model]
    print(plan.summary())
    for err in plan.errors[:_LIST_LIMIT]:
        print("  error:", err)
    if len(plan.errors) > _LIST_LIMIT:
        print(f"  ... and {len(plan.errors) - _LIST_LIMIT} more errors")
    print("plan only: nothing was launched (pass --approved to run it)")
    return EXIT_OK


def _print_report(model: str, report: "ar.ReplayReport") -> None:
    """Print the report counts, the per-arm over-context counts and the first failures."""
    print(
        f"{model}: {len(report.verified)} verified, {len(report.failed)} failed, "
        f"{len(report.audit_failures)} failed the audit, {len(report.skipped_existing)} already stored, "
        f"{len(report.partial)} partial, {len(report.manifests)} manifests"
    )
    if report.plan is not None:
        for arm, stats in report.plan.per_arm.items():
            print(f"  arm {arm}: {stats['over_context']} over the "
                  f"{report.plan.capture_max_model_len}-token capture context (excluded)")
    failures = {**report.failed, **report.audit_failures}
    for job, why in list(failures.items())[:_LIST_LIMIT]:
        print(f"  {job}: {why}")
    if len(failures) > _LIST_LIMIT:
        print(f"  ... and {len(failures) - _LIST_LIMIT} more (see the report file)")
    if report.manifest_error:
        print("  manifest error:", report.manifest_error)


def _write_report(report: "ar.ReplayReport", report_dir: Path) -> Path:
    """Write `report` as JSON to ``<report_dir>/attention_report--<model>--<stamp>.json``.

    The file is created exclusively (mode ``"x"``): a report is a record of a billed
    run and is never overwritten. The stamp has microsecond precision.

    Raises
    ------
    FileExistsError
        When the file already exists.
    """
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"attention_report--{report.model}--{format_run_ts(utcnow())}.json"
    with open(path, "x", encoding="utf-8") as handle:
        json.dump(dataclasses.asdict(report), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the command line and return the process exit code (see the module docstring).

    Parameters
    ----------
    argv : Sequence[str], optional
        Arguments without the program name; defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        0, 1, 3 or 4 as documented; a bad command line exits 2 through argparse.

    Notes
    -----
    ``--approved`` is the only way to spend money: ``replay_model`` receives the literal
    ``True`` and still refuses anything else. An interrupt is not caught: the driver has
    already shut the box down by then.
    """
    args = build_parser().parse_args(argv)
    default_root, default_s3 = default_locations(args.smoke)
    results_root = args.results_root if args.results_root is not None else default_root
    s3_uri = args.s3_uri if args.s3_uri is not None else default_s3
    # The mirror's parent is the results folder (it also holds horn/ and attention-v2/).
    report_dir = args.report_dir if args.report_dir is not None else results_root.parent
    try:
        if not args.approved:
            return _print_plan(args.model, results_root, s3_uri, args.seeds)
        try:
            report = ar.replay_model(
                args.model, results_root, s3_uri,
                approved=True,
                allow_unverified_serve=args.allow_unverified_serve is True,
                instance_types=args.instance_types,
                batch_timeout_s=args.batch_timeout_s,
                url_ttl_s=args.url_ttl_s,
                audit_arrays=args.audit_arrays,
                seeds=args.seeds,
            )
        except ar.ShutdownFailed as exc:
            # The capture and audit are done and the results ride on the exception:
            # keep them, then report the incident. A failed write must not turn this
            # exit code into 1.
            print(f"error: {exc}", file=sys.stderr)
            _print_report(args.model, exc.report)
            try:
                print(f"report: {_write_report(exc.report, report_dir)}")
            except OSError as write_exc:
                print(f"error: the report could not be written: {write_exc!r}", file=sys.stderr)
            return EXIT_SHUTDOWN_FAILED
        _print_report(args.model, report)
        print(f"report: {_write_report(report, report_dir)}")
        # NOTE: the exit rule counts failed and audit-failed jobs only. A manifest error or
        # a partial job (a stored job missing a rank object) still exits 0; both are printed
        # above and held in the report file.
        return EXIT_JOBS_FAILED if report.failed or report.audit_failures else EXIT_OK
    except Exception as exc:  # noqa: BLE001 -- any failure is an exit code, with its message
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_EXCEPTION


if __name__ == "__main__":
    sys.exit(main())
