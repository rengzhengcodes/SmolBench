"""Command-line runner of the attention replay: one model per process.

    python rebuttal/run_attention.py --model gemma-4-31b --smoke            # plan only
    python rebuttal/run_attention.py --model gemma-4-31b --seeds 0-9 --approved
    python rebuttal/run_attention.py --model gemma-4-31b --audit-only       # audit stored captures
    python rebuttal/run_attention.py --model gemma-4-31b --study horn --arms lem pad --reps 0-1
    python rebuttal/run_attention.py --model gemma-4-31b --study horn --reps 0-1 --approved
    python rebuttal/run_attention.py --model gemma-4-31b --study horn --audit-only
    python rebuttal/run_attention.py --model <model> --job-ids ID ID --fill --exec-timeout-s 3600
    python rebuttal/run_attention.py --model <model> --job-ids @ids.txt --approved

Without ``--approved`` it prints the plan of ``attention_replay.plan_replay`` (sizes,
errors, storage estimate) and exits 0; it builds no AWS client. With ``--approved`` it
calls ``attention_replay.replay_model``, which provisions ONE billed spot GPU box,
captures the stored induction transcripts, shuts the box down and only then audits and
records what landed. A model runs per process so that a failure, or an expired AWS
session (they last 4 hours), stops one model and not the others; ``--seeds`` splits one
model across several runs.

With ``--audit-only`` it calls ``attention_replay.audit_existing`` instead: it audits the
captures of the model that are already in the bucket and no manifest records yet (for
example when an audit outlived the AWS session before it wrote any manifest), and writes
their manifests. It reads and writes S3 only, launches nothing and needs no ``--approved``;
given together with ``--approved`` it still launches nothing. A rerun resumes: the run
folders already recorded are skipped. ``--audit-workers`` sets how many jobs are audited at
once, in both modes (each worker holds one multi-GB array in memory).

``--study horn`` replays the deduction (Horn) study instead of the induction one. Its
transcripts come from the model's rows file (``--rows``, default
``<results folder>/horn/<model>.jsonl``) and the stored rung prompts (``--rungs-dir``,
default ``bedrock_trio.RUNGS_DIR``); ``--arms`` and ``--reps`` (same syntax as ``--seeds``)
narrow the jobs and ``--seeds`` selects the instance seeds. Those four flags are an error
with ``--study induction``. ``--mode {mass,summary}`` picks the capture mode (default: the
driver's choice, mass for induction and summary for horn) and ``--capture-max-model-len N``
overrides the capture context length, in both studies. All of them work with ``--audit-only``
(``--mode`` is not needed there: the stored objects say which mode they hold).
``--label-added-lines`` (horn only, exit 2 with ``--study induction``) labels the added lines
of every padded arm as class 1, so the pad ratio is defined for deduction; the plan says so
and counts the class-1 tokens per arm, and every manifest records it. Without it no deduction
token is class 1, as in the captures stored so far. Stored jobs are skipped whatever their
classes, so give a labelled run its own ``--s3-uri``.

Recapture. ``--job-ids ID [ID ...]`` narrows the plan, the run or the audit to the jobs with
those ids (the driver rejects an id that no planned job has). An argument that starts with
``@`` names a file with one id per line; blank lines are skipped, and an unreadable file or
a selection with no id at all is an error (exit 2). ``--fill`` completes the stems that
hold some but not all of their objects; it needs ``--job-ids``, so that it can never re-send
a whole seed range (exit 2 without it). ``--exec-timeout-s`` (vLLM's step timeout of the
capture serve), ``--gate-tol`` and ``--gpu-memory-utilization`` override the serve
settings; the driver validates them and a bad value exits 1 before anything launches. With
``--audit-only`` the audit launches nothing, so ``--fill``, ``--exec-timeout-s``,
``--gate-tol`` and ``--gpu-memory-utilization`` are errors there (a silently ignored serve
flag could hide a typo); ``--job-ids`` is allowed. The plan prints the selected jobs and a
``serve settings`` block with the values that ``--approved`` would launch with.

Defaults follow the notebook's attention cells: the results root is the induction mirror
(``bedrock_trio.RESULTS_DIR / "induction"``, or the same under the smoke folder with
``--smoke``) and the destination is ``<RESULTS_S3>[/<smoke prefix>]/attention-v2``.

Exit codes: 0 every job that was sent passed the capture and the audit; 1 an exception
(also a refusal such as an unverified serve); 2 a bad command line; 3 some job failed
the capture or the content audit, or some job was not sent (a dead engine stops the
sending of the rest; the report names them); 4 the box could not be shut down (it may still be
billing; the report is written first). With ``--audit-only``: 0 every audited job was
verified (also when there was nothing to audit), 3 some job failed the audit, 1 an
exception; the report file is ``attention_audit--<model>--<stamp>.json``. For ``--study horn`` the
report files are ``attention_report--horn--<model>--<stamp>.json`` and
``attention_audit--horn--<model>--<stamp>.json``.

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
#: Jobs audited at once, as ``attention_replay.replay_model`` and ``audit_existing`` default.
DEFAULT_AUDIT_WORKERS: int = 8
#: Sub-folder of the destination holding the captures (the notebook's ``attention-v2``).
ATTENTION_SUBPREFIX: str = "attention-v2"

EXIT_OK: int = 0
EXIT_EXCEPTION: int = 1
EXIT_JOBS_FAILED: int = 3
EXIT_SHUTDOWN_FAILED: int = 4

#: Values of ``--study``.
STUDIES: Tuple[str, ...] = ("induction", "horn")

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


def _positive_int(text: str) -> int:
    """Parse an integer of at least 1 (argparse ``type``; a bad value exits with code 2)."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer") from None
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {value}")
    return value


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
    parser.add_argument("--run-label", default=None,
                        help="label of this run in the instance tag; needed when two runs of one "
                             "model are live at once (for example s0-14)")
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
    parser.add_argument("--audit-workers", type=_positive_int, default=DEFAULT_AUDIT_WORKERS,
                        help="jobs audited at once; each holds one array in memory (default: %(default)s)")
    parser.add_argument("--audit-only", action="store_true",
                        help="audit and manifest the captures already in the bucket; launches nothing "
                             "and needs no --approved")
    parser.add_argument("--report-dir", type=Path, default=None,
                        help="where the JSON report goes (default: the results folder next to the mirror)")
    parser.add_argument("--study", choices=STUDIES, default="induction",
                        help="which study to replay (default: %(default)s)")
    parser.add_argument("--mode", choices=("mass", "summary"), default=None,
                        help="capture mode (default: the driver's choice, mass for induction and "
                             "summary for horn)")
    parser.add_argument("--capture-max-model-len", type=_positive_int, default=None, metavar="N",
                        help="capture context length in tokens, overriding the driver's default")
    parser.add_argument("--arms", nargs="+", default=None, metavar="ARM",
                        help="horn only: only these arms (default: every arm)")
    parser.add_argument("--reps", type=parse_seeds, default=None,
                        help="horn only: only these replicates, e.g. 0-1 or 0,2 (default: every replicate)")
    parser.add_argument("--rows", type=Path, default=None,
                        help="horn only: the model's rows file (default: <results folder>/horn/<model>.jsonl)")
    parser.add_argument("--rungs-dir", type=Path, default=None,
                        help="horn only: folder of the stored rung prompts (default: bedrock_trio.RUNGS_DIR)")
    parser.add_argument("--label-added-lines", action="store_true",
                        help="horn only: label the added lines of the padded arms as class 1, the pad class; "
                             "use a new --s3-uri, stored jobs are skipped")
    parser.add_argument("--job-ids", nargs="+", default=None, metavar="ID",
                        help="only these job ids; an argument starting with @ is a file with one id per "
                             "line (default: every planned job)")
    parser.add_argument("--fill", action="store_true",
                        help="complete the stems that hold some but not all objects; needs --job-ids")
    parser.add_argument("--gate-tol", type=float, default=None, metavar="X",
                        help="tolerance of the capture gate, overriding the driver's default")
    parser.add_argument("--exec-timeout-s", type=int, default=None, metavar="N",
                        help="vLLM's step timeout in seconds for the capture serve "
                             "(default: the driver's, 3600)")
    parser.add_argument("--gpu-memory-utilization", type=float, default=None, metavar="X",
                        help="share of GPU memory vLLM may use, overriding the driver's default")
    return parser


def expand_job_ids(parser: argparse.ArgumentParser, raw: Optional[Sequence[str]]) -> Optional[List[str]]:
    """Expand ``@file`` arguments of ``--job-ids`` into the ids they list.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Used to report a bad selection as a command-line error (exit 2).
    raw : Sequence[str], optional
        The ``--job-ids`` values; ``None`` when the flag was not given.

    Returns
    -------
    Optional[List[str]]
        ``None`` for ``None``; otherwise the ids in order, duplicates kept (the driver
        collapses them). A ``@file`` holds one id per line; each line is stripped and
        blank lines are skipped.

    Raises
    ------
    SystemExit
        Through ``parser.error`` (code 2) when a ``@file`` cannot be read or the
        selection yields no id.
    """
    if raw is None:
        return None
    ids: List[str] = []
    for item in raw:
        if not item.startswith("@"):
            ids.append(item)
            continue
        try:
            text = Path(item[1:]).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            parser.error(f"--job-ids: cannot read {item[1:]!r}: {exc}")
        ids.extend(line.strip() for line in text.splitlines() if line.strip())
    if not ids:
        parser.error("--job-ids: the selection holds no job id")
    return ids


def _print_plan(model: str, results_root: Path, s3_uri: str, serve: Dict[str, object],
                **kwargs: object) -> int:
    """Print the offline plan, its errors and the serve settings; builds no AWS client.

    `serve` holds the ``fill``, ``gate_tol``, ``execute_model_timeout_s`` and
    ``gpu_memory_utilization`` keywords of ``attention_replay.serve_settings``; the block
    printed is what a ``--approved`` run would launch the capture serve with. A setting
    the driver rejects raises ``ValueError`` before the plan-only line, so nothing is
    presented as ready. `kwargs` are the planning keywords of
    ``attention_replay.plan_replay`` (seeds, mode, capture length, job ids and, for the
    horn study, the study keywords). Returns the exit code.
    """
    # Imported here: the module sets the provider's environment defaults at import time.
    from smolbench.evals.providers import ec2

    plan = ar.plan_replay(results_root, [model], s3_uri=s3_uri, **kwargs)[model]
    print(plan.summary())
    for err in plan.errors[:_LIST_LIMIT]:
        print("  error:", err)
    if len(plan.errors) > _LIST_LIMIT:
        print(f"  ... and {len(plan.errors) - _LIST_LIMIT} more errors")
    settings = ar.serve_settings(
        spec=ec2.EC2_DEPLOY_SPECS[model], capture_max_model_len=plan.capture_max_model_len, **serve,
    )
    print("serve settings (what --approved would launch with):")
    print(f"  capture context (max_model_len): {settings['max_model_len']} tokens")
    print(f"  execute timeout: {settings['execute_model_timeout_s']} s")
    print(f"  gate tolerance: {settings['gate_tol']}")
    print(f"  fill: {settings['fill']}")
    print(f"  GPU memory share: {settings['gpu_memory_utilization']}")
    print("plan only: nothing was launched (pass --approved to run it)")
    return EXIT_OK


def _print_report(model: str, report: "ar.ReplayReport") -> None:
    """Print the report counts, the per-arm over-context counts and the first failures."""
    print(
        f"{model}: {len(report.verified)} verified, {len(report.failed)} failed, "
        f"{len(report.audit_failures)} failed the audit, {len(report.skipped_existing)} already stored, "
        f"{len(report.partial)} partial, {len(report.manifests)} manifests, "
        f"{len(report.not_sent)} not sent"
    )
    if report.engine_died:
        print(f"  engine died: {report.engine_died}")
        if report.engine_log:
            print(f"  engine log: {report.engine_log}")
    if report.refilled:
        print(f"  {len(report.refilled)} job(s) completed by --fill")
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


def _write_report(report: "ar.ReplayReport", report_dir: Path, kind: str = "report",
                  study: str = "induction") -> Path:
    """Write `report` as JSON to ``<report_dir>/attention_<kind>[--horn]--<model>--<stamp>.json``.

    `kind` is ``"report"`` for a capture run and ``"audit"`` for ``--audit-only``. The
    horn study adds ``--horn`` after the kind; the induction names are unchanged.

    The file is created exclusively (mode ``"x"``): a report is a record of a billed
    run and is never overwritten. The stamp has microsecond precision.

    Raises
    ------
    FileExistsError
        When the file already exists.
    """
    report_dir.mkdir(parents=True, exist_ok=True)
    infix = "--horn" if study == "horn" else ""
    path = report_dir / f"attention_{kind}{infix}--{report.model}--{format_run_ts(utcnow())}.json"
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
    ``True`` and still refuses anything else. ``--audit-only`` is checked first and never
    reaches ``replay_model``. An interrupt is not caught: the driver has already shut the
    box down by then (and ``--audit-only`` has no box).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    study = args.study
    if study == "induction":
        # These flags only mean something for the horn study; a silent ignore would let a
        # typo launch the wrong (billed) replay, so name the flag and exit 2.
        for flag, value in (("--arms", args.arms), ("--reps", args.reps),
                            ("--rows", args.rows), ("--rungs-dir", args.rungs_dir),
                            ("--label-added-lines", args.label_added_lines or None)):
            if value is not None:
                parser.error(f"{flag} is only valid with --study horn")
    job_ids = expand_job_ids(parser, args.job_ids)
    if args.fill and job_ids is None:
        parser.error("--fill requires --job-ids (fill must never re-send a whole seed range)")
    if args.audit_only:
        # The audit launches nothing, so a serve flag would be ignored; name it instead.
        for flag, value in (("--fill", args.fill or None), ("--gate-tol", args.gate_tol),
                            ("--exec-timeout-s", args.exec_timeout_s),
                            ("--gpu-memory-utilization", args.gpu_memory_utilization)):
            if value is not None:
                parser.error(f"{flag} has no effect with --audit-only (the audit launches nothing)")
    default_root, default_s3 = default_locations(args.smoke)
    results_root = args.results_root if args.results_root is not None else default_root
    s3_uri = args.s3_uri if args.s3_uri is not None else default_s3
    # The mirror's parent is the results folder (it also holds horn/ and attention-v2/).
    report_dir = args.report_dir if args.report_dir is not None else results_root.parent
    # Keywords shared by plan, replay and audit; the horn keywords are added only for horn so
    # that the induction calls keep their earlier shape.
    study_kwargs: Dict[str, object] = {}
    if study == "horn":
        study_kwargs = {
            "study": "horn",
            "horn_rows": args.rows if args.rows is not None
            else results_root.parent / "horn" / f"{args.model}.jsonl",
            "rungs_dir": args.rungs_dir if args.rungs_dir is not None else ar.bt.RUNGS_DIR,
            "arms": args.arms,
            "reps": args.reps,
        }
        if args.label_added_lines:
            # Only when given, so that a default horn call keeps its earlier keywords.
            study_kwargs["label_added_lines"] = True
    try:
        if args.audit_only:
            # Design: checked before --approved so that the two flags together can never
            # launch a box; the audit path has no way to reach the EC2 provider.
            report = ar.audit_existing(
                args.model, results_root, s3_uri,
                seeds=args.seeds, arrays=args.audit_arrays, workers=args.audit_workers,
                capture_max_model_len=args.capture_max_model_len, job_ids=job_ids, **study_kwargs,
            )
            _print_report(args.model, report)
            print(f"  {report.not_captured} planned job(s) have no capture in the bucket")
            print(f"report: {_write_report(report, report_dir, 'audit', study)}")
            # NOTE: as for a capture run, a manifest error or a partial job still exits 0 (both
            # are printed above and held in the report file); only a failed audit exits 3. After
            # a manifest error the audited jobs are not recorded: run --audit-only again.
            return EXIT_JOBS_FAILED if report.audit_failures else EXIT_OK
        if not args.approved:
            return _print_plan(
                args.model, results_root, s3_uri,
                {"fill": args.fill, "gate_tol": args.gate_tol,
                 "execute_model_timeout_s": args.exec_timeout_s,
                 "gpu_memory_utilization": args.gpu_memory_utilization},
                seeds=args.seeds, mode=args.mode,
                capture_max_model_len=args.capture_max_model_len, job_ids=job_ids, **study_kwargs,
            )
        try:
            report = ar.replay_model(
                args.model, results_root, s3_uri,
                approved=True,
                allow_unverified_serve=args.allow_unverified_serve is True,
                instance_types=args.instance_types,
                batch_timeout_s=args.batch_timeout_s,
                url_ttl_s=args.url_ttl_s,
                audit_arrays=args.audit_arrays,
                audit_workers=args.audit_workers,
                seeds=args.seeds,
                run_label=args.run_label,
                mode=args.mode,
                capture_max_model_len=args.capture_max_model_len,
                job_ids=job_ids,
                fill=args.fill,
                gate_tol=args.gate_tol,
                execute_model_timeout_s=args.exec_timeout_s,
                gpu_memory_utilization=args.gpu_memory_utilization,
                # The server log tail of a dead engine is saved next to the report.
                engine_log_dir=report_dir,
                **study_kwargs,
            )
        except ar.ShutdownFailed as exc:
            # The capture and audit are done and the results ride on the exception:
            # keep them, then report the incident. A failed write must not turn this
            # exit code into 1.
            print(f"error: {exc}", file=sys.stderr)
            _print_report(args.model, exc.report)
            try:
                print(f"report: {_write_report(exc.report, report_dir, study=study)}")
            except OSError as write_exc:
                print(f"error: the report could not be written: {write_exc!r}", file=sys.stderr)
            return EXIT_SHUTDOWN_FAILED
        _print_report(args.model, report)
        print(f"report: {_write_report(report, report_dir, study=study)}")
        # NOTE: the exit rule counts failed, audit-failed and not-sent jobs (a dead engine
        # leaves the rest unsent, so they were not captured). A manifest error or a partial
        # job (a stored job missing a rank object) still exits 0; both are printed above and
        # held in the report file.
        return EXIT_JOBS_FAILED if report.failed or report.audit_failures or report.not_sent else EXIT_OK
    except Exception as exc:  # noqa: BLE001 -- any failure is an exit code, with its message
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_EXCEPTION


if __name__ == "__main__":
    sys.exit(main())
