"""Run one study of the Bedrock protocol for one model from the command line.

``bedrock_trio.ipynb`` runs the models one after another at a low concurrency, which is
too slow for the full protocol (2,400 Horn cells per model, some of them 15 minutes
long). This script runs one study for one model per process, so that one process per model
can run side by side, each with its own concurrency, deadline and failure limit::

    python rebuttal/run_protocol.py induction --model <key> [--seeds 0-29]
        [--concurrency 12] [--smoke] [--region us-east-1] [--no-s3] [--skip-prompt-check]
    python rebuttal/run_protocol.py horn --model <key> [--seeds 100-199] [--reps 3]
        [--arms lem pad ...] [--concurrency 24] [--deadline 2026-11-16T10:30:00Z]
        [--max-consecutive-failures 8] [--push-every 200] [--smoke] [--region us-east-1]
        [--no-s3] [--rep-indices 0,2] [--rows-label LABEL] [--ramp-start K [--ramp-minutes 30]]

The steps are those of the notebook: check the results bucket, mint a Bedrock token that
belongs to this process, resolve the model's Bedrock id, find the reasoning arguments with
one small billed request (and refuse to go on if the model does not reason), then run the
study. Both studies resume from the bucket, so a run that stopped (at its deadline, or
after repeated failures) is continued by running the same command again.

Two processes can collect one model's cells at once, for example from two Bedrock regions
without confounding arm with region: give each its own cells (``--rep-indices 0,2`` in one,
``--rep-indices 1`` in the other, so that every arm has the same mix of regions) and its own
local rows file (``--rows-label``, which names ``horn/<model>--<label>.jsonl``; the rows lock
is per file). Each process pulls the bucket's rows before it chooses cells and pushes only
rows the bucket lacks. A labelled file is a working copy: the reports read
``horn/<model>.jsonl``, which ``bedrock_trio.pull_horn_rows`` refreshes from the bucket. The
caller keeps the cells disjoint; ``run_horn`` prints how many of its cells were already
done at the start and how many rows it wrote for cells the bucket covers twice at the end.
``--ramp-start K`` starts with at most K cells in flight and doubles that every
``--ramp-minutes`` (default 30) up to ``--concurrency``, because Bedrock answers 503 when
the load more than doubles within 30 minutes.

Exit code: 0 when the run finished or stopped at its deadline, 2 when ``run_horn`` stopped
after consecutive failures (``bedrock_trio.HornRunStopped``, usually expired credentials),
1 on any other error, including a command line that does not parse.

Importing this module touches neither AWS nor the network.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import NoReturn, Optional, Sequence

# ``bedrock_trio.py`` is not a package: its folder goes on ``sys.path``, as in the notebook
# (running this file does that already; an import of this module from elsewhere does not).
# An already-registered ``bedrock_trio`` is reused, so a caller keeps one shared copy.
_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import bedrock_trio as bt  # noqa: E402  # pylint: disable=wrong-import-position

LOG = logging.getLogger("run_protocol")

#: The protocol: induction replicate seeds 0-29; Horn theory seeds 100-199, 3 replicates.
PROTOCOL_INDUCTION_SEEDS = tuple(range(30))
PROTOCOL_HORN_SEEDS = tuple(range(100, 200))
PROTOCOL_HORN_REPS = 3
#: The notebook's smoke values (``SMOKE`` in its config cell).
SMOKE_INDUCTION_SEEDS = (0, 1)
SMOKE_HORN_SEEDS = (100, 101)
SMOKE_HORN_REPS = 1
#: Parallel requests per process; Horn cells are long and few per second, induction short.
DEFAULT_INDUCTION_CONCURRENCY = 12
DEFAULT_HORN_CONCURRENCY = 24
#: Exit codes (see the module docstring).
EXIT_OK, EXIT_ERROR, EXIT_STOPPED = 0, 1, 2


def parse_seeds(text: str) -> list[int]:
    """Parse a seed list such as ``"100-103"``, ``"100,105"`` or ``"0-3,10"``.

    A range ``a-b`` includes both ends. Items are separated by commas; a seed named twice
    is kept once, in the position of its first mention.

    Parameters
    ----------
    text : str
        The list. Seeds are non-negative integers, and a range needs ``a <= b``.

    Returns
    -------
    list[int]
        The seeds, in the order given.

    Raises
    ------
    argparse.ArgumentTypeError
        If an item is not an integer or a range, a range runs backwards, or the list is
        empty.

    Examples
    --------
    >>> parse_seeds("100-103")
    [100, 101, 102, 103]
    >>> parse_seeds("100,105")
    [100, 105]
    >>> parse_seeds("0-1,5,1")
    [0, 1, 5]
    """
    seeds: list[int] = []
    for item in text.split(","):
        item = item.strip()
        lo, sep, hi = item.partition("-")
        try:
            first, last = int(lo), int(hi) if sep else int(lo)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"bad seed list {text!r}: {item!r} is neither an integer nor a range such as 100-199"
            ) from None
        if first < 0 or last < first:
            raise argparse.ArgumentTypeError(f"bad seed list {text!r}: {item!r} is not a range of non-negative seeds")
        seeds += range(first, last + 1)
    # dict.fromkeys: each seed once, in first-mention order.
    return list(dict.fromkeys(seeds))


def parse_deadline(text: str) -> datetime:
    """Parse an ISO 8601 timestamp that carries a UTC offset (``Z`` is accepted).

    Parameters
    ----------
    text : str
        For example ``2026-11-16T10:30:00Z`` or ``2026-11-16T11:30:00+01:00``.

    Returns
    -------
    datetime
        A timezone-aware instant.

    Raises
    ------
    argparse.ArgumentTypeError
        If the text is not an ISO 8601 timestamp, or has no UTC offset. A naive time is
        refused because the host's zone is not the operator's: the same text would mean
        different instants on different machines.

    Examples
    --------
    >>> parse_deadline("2026-11-16T10:30:00Z").isoformat()
    '2026-11-16T10:30:00+00:00'
    """
    try:
        when = datetime.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"bad deadline {text!r}: use ISO 8601 with a UTC offset, such as 2026-11-16T10:30:00Z"
        ) from None
    if when.utcoffset() is None:
        raise argparse.ArgumentTypeError(
            f"deadline {text!r} has no UTC offset: add Z or an offset such as +00:00"
        )
    return when


def _positive_int(text: str) -> int:
    """An integer of at least 1; a bad value is a usage error, raised before any billed call."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer") from None
    if value < 1:
        raise argparse.ArgumentTypeError(f"{text!r} must be at least 1")
    return value


def _non_negative_int(text: str) -> int:
    """An integer of at least 0 (see ``_positive_int``)."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} must not be negative")
    return value


def _index_list(text: str) -> list[int]:
    """Parse a comma list of non-negative integers such as ``"0,2"``; each is kept once, in order.

    Raises
    ------
    argparse.ArgumentTypeError
        If an item is not a non-negative integer, or the list is empty.

    Examples
    --------
    >>> _index_list("0,2")
    [0, 2]
    >>> _index_list("1,1")
    [1]
    """
    items = [item.strip() for item in text.split(",")]
    if not all(item.isascii() and item.isdigit() for item in items):
        raise argparse.ArgumentTypeError(f"bad index list {text!r}: use non-negative integers such as 0,2")
    return list(dict.fromkeys(int(item) for item in items))


def _rows_label(text: str) -> str:
    """A rows-file label: only ``A-Za-z0-9._-`` (it becomes part of a file name)."""
    if not bt.HORN_LABEL.fullmatch(text):
        raise argparse.ArgumentTypeError(f"bad label {text!r}: use only A-Za-z0-9._- (at least one character)")
    return text


def _positive_float(text: str) -> float:
    """A finite number above 0 (see ``_positive_int``)."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from None
    if not 0 < value < float("inf"):
        raise argparse.ArgumentTypeError(f"{text!r} must be positive and finite")
    return value


class _Parser(argparse.ArgumentParser):
    """An ``ArgumentParser`` whose usage errors exit with 1, not argparse's 2.

    Exit code 2 means "``run_horn`` stopped after consecutive failures" here, and a
    wrapper that reacts to it (refresh the credentials, start again) must not mistake a
    mistyped option for it.
    """

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(EXIT_ERROR, f"{self.prog}: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    """The command-line parser: subcommands ``induction`` and ``horn``.

    A seed list or the arms left unset stay ``None``; ``resolve_defaults`` fills them
    from the protocol, or from the smoke values with ``--smoke``.
    """
    parser = _Parser(description=__doc__.split("\n\n", maxsplit=1)[0])
    sub = parser.add_subparsers(dest="study", required=True, parser_class=_Parser)

    def common(p: argparse.ArgumentParser, concurrency: int, seeds_help: str) -> None:
        # The model key is checked in ``run`` (against ``bt.TRIO``), not with ``choices``,
        # so that an unknown key exits 1 with the roster in the message.
        p.add_argument("--model", required=True, help=f"roster key: one of {', '.join(bt.TRIO)}")
        p.add_argument("--seeds", type=parse_seeds, default=None, help=seeds_help)
        p.add_argument("--concurrency", type=_positive_int, default=concurrency, help="parallel requests (default %(default)s)")
        p.add_argument("--smoke", action="store_true", help="smoke seeds, bucket prefix and mirror folder")
        p.add_argument("--region", default=bt.DEFAULT_REGION, help="Bedrock region (default %(default)s)")
        p.add_argument("--no-s3", action="store_true", help="keep results local; no bucket")

    ind = sub.add_parser("induction", help="periodic induction study")
    common(ind, DEFAULT_INDUCTION_CONCURRENCY, "replicate seeds, e.g. 0-29 (default; smoke: 0-1)")
    ind.add_argument("--skip-prompt-check", action="store_true", help="skip the check against the released prompts")

    horn = sub.add_parser("horn", help="Horn-rule deduction study")
    common(horn, DEFAULT_HORN_CONCURRENCY, "theory seeds, e.g. 100-199 (default; smoke: 100-101)")
    horn.add_argument("--reps", type=_positive_int, default=None, help="replicates per arm and seed (default 3; smoke: 1)")
    horn.add_argument("--arms", nargs="+", choices=bt.HORN_ARMS, default=None, metavar="ARM",
                      help=f"arms to run (default: all of {', '.join(bt.HORN_ARMS)})")
    horn.add_argument("--deadline", type=parse_deadline, default=None,
                      help="ISO 8601 time with an offset; no cell starts after it. Running cells "
                           "still finish (a long one takes 15 minutes or more), so set it well "
                           "before the credentials expire")
    horn.add_argument("--max-consecutive-failures", type=_non_negative_int, default=8,
                      help="stop after this many failed cells in a row; 0 disables (default %(default)s)")
    horn.add_argument("--push-every", type=_positive_int, default=200, help="new rows per upload (default %(default)s)")
    horn.add_argument("--rep-indices", type=_index_list, default=None, metavar="I,J",
                      help="run only these replicate indices, e.g. 0,2 (default: all of range(reps)); "
                           "a second process takes the others")
    horn.add_argument("--rows-label", type=_rows_label, default=None, metavar="LABEL",
                      help="use the local rows file horn/<model>--LABEL.jsonl so that a second process of "
                           "this model can run at once (only A-Za-z0-9._-)")
    horn.add_argument("--ramp-start", type=_positive_int, default=None, metavar="K",
                      help="start with at most K cells in flight and double that every --ramp-minutes "
                           "up to --concurrency (default: no ramp)")
    horn.add_argument("--ramp-minutes", type=_positive_float, default=30, metavar="M",
                      help="minutes between doublings with --ramp-start (default %(default)s)")
    return parser


def resolve_defaults(args: argparse.Namespace) -> argparse.Namespace:
    """Fill the seeds, replicates and arms that were left unset; return ``args``.

    Mutates ``args``. ``--smoke`` selects the notebook's smoke values, otherwise the
    protocol's.
    """
    if args.seeds is None:
        if args.study == "induction":
            args.seeds = list(SMOKE_INDUCTION_SEEDS if args.smoke else PROTOCOL_INDUCTION_SEEDS)
        else:
            args.seeds = list(SMOKE_HORN_SEEDS if args.smoke else PROTOCOL_HORN_SEEDS)
    if args.study == "horn":
        if args.reps is None:
            args.reps = SMOKE_HORN_REPS if args.smoke else PROTOCOL_HORN_REPS
        if args.arms is None:
            args.arms = list(bt.HORN_ARMS)
    return args


def check_horn_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Refuse the Horn options that need another option to judge, as a usage error.

    ``--rep-indices`` is judged against ``--reps`` and ``--ramp-start`` against
    ``--concurrency``, which are known only after ``resolve_defaults``. The same checks sit
    in ``bt.run_horn``, but by then the (billed) reasoning probe has run.
    """
    if args.study != "horn":
        return
    if args.rep_indices is not None and max(args.rep_indices) >= args.reps:
        parser.error(f"--rep-indices {args.rep_indices} must lie in range(--reps), that is 0-{args.reps - 1}")
    if args.ramp_start is not None and args.ramp_start > args.concurrency:
        parser.error(f"--ramp-start {args.ramp_start} must not exceed --concurrency {args.concurrency}")


def _seed_text(seeds: Sequence[int]) -> str:
    """``100-199`` for a consecutive run, else the comma list."""
    if len(seeds) > 1 and list(seeds) == list(range(seeds[0], seeds[0] + len(seeds))):
        return f"{seeds[0]}-{seeds[-1]}"
    return ",".join(map(str, seeds))


def _horn_scope_text(args: argparse.Namespace) -> str:
    """The Horn options that narrow or pace the run, for the start line (empty when none is set)."""
    text = ""
    if args.rep_indices is not None:
        text += f", rep indices {','.join(map(str, args.rep_indices))}"
    if args.rows_label is not None:
        text += f", rows label {args.rows_label}"
    if args.ramp_start is not None and args.ramp_start < args.concurrency:
        text += f", ramp {args.ramp_start} doubling every {args.ramp_minutes:g} min to {args.concurrency}"
    else:
        text += ", ramp none"
    return text


def _results_location(args: argparse.Namespace) -> tuple[Optional[str], Path]:
    """The bucket URI (``None`` with ``--no-s3``) and the local mirror folder.

    A smoke run gets its own prefix and folder, as in the notebook's config cell: the
    bucket is append-only, so the protocol prefix must stay clean. ``bt.RESULTS_DIR`` is
    read here, at call time.
    """
    s3_uri = None if args.no_s3 else bt.RESULTS_S3 + (f"/{bt.SMOKE_PREFIX}" if args.smoke else "")
    results = bt.RESULTS_DIR / bt.SMOKE_PREFIX if args.smoke else bt.RESULTS_DIR
    return s3_uri, results


def _prepare(args: argparse.Namespace, s3_uri: Optional[str]) -> tuple[bt.BedrockModel, dict]:
    """Authenticate, resolve the Bedrock id and find the reasoning arguments.

    The notebook's cells 3 and 5 for one model. The reasoning probe is one small billed
    request.

    Returns
    -------
    tuple[bt.BedrockModel, dict]
        The model with its Bedrock id, and the reasoning request fields.

    Raises
    ------
    RuntimeError
        If the bucket is unreachable or the model does not reason.
    LookupError
        If the model's Bedrock id cannot be resolved.
    """
    if s3_uri is not None:
        bt.check_bucket(s3_uri)
        LOG.info("results bucket %s is reachable", s3_uri)
    # A token left in the environment may belong to another session (and expire with it);
    # drop it so that the one used here is minted for this process.
    os.environ.pop("AWS_BEARER_TOKEN_BEDROCK", None)
    bt.mint_token(args.region)
    listing: set[str] = set()
    for path in ("/v1", "/openai/v1"):
        try:
            listing |= set(bt.list_mantle_models(args.region, path))
        except Exception as err:  # pylint: disable=broad-exception-caught
            # One path failing is not fatal (as in the notebook): the id may sit on the other.
            LOG.warning("GET %s/models failed: %s", path, err)
    model = bt.resolve_ids(sorted(listing), {args.model: bt.TRIO[args.model]})[args.model]
    LOG.info("%s resolves to %s at %s", model.key, model.bedrock_id, bt.base_url(model, args.region))
    reasoning, probes = bt.pick_reasoning_args(model, args.region)
    LOG.info("reasoning arguments %s (probe: %s)", reasoning, probes[-1])
    return model, reasoning


def _run_induction(args: argparse.Namespace, s3_uri: Optional[str], results: Path) -> int:
    """Run the induction study for ``args.model`` (the notebook's cells 7 and 9)."""
    model, reasoning = _prepare(args, s3_uri)
    if not args.skip_prompt_check:
        run_study = bt.load_run_study()
        related = bt.check_induction_prompts(
            bt.induction_quizzes(0, model.key), bt.released_queries(model.key, 0), run_study.for_model(model.key)
        )
        added = sorted({(r["added_lines"], r["pad_tokens"]) for r in related})
        LOG.info("prompts consistent with the released ICLR prompts; related_intens (added lines, pad tokens): %s",
                 added)
    harness = bt.induction_harness([model], args.seeds, results_dir=results, s3_uri=s3_uri)
    bt.run_induction(harness, model, args.region, reasoning, max_parallel=args.concurrency)
    if s3_uri is not None:
        LOG.info("mirrored %d files to %s", bt.pull_induction(s3_uri, results), results / "induction")
    print(f"== {model.key} induction summary (marks, unreasoned, null scores, empty responses per arm)")
    for (key, arm), counts in sorted(bt.induction_reasoning_report(results).items()):
        if key == model.key:
            print(f"  {arm}: {counts}")
    return EXIT_OK


def _print_horn_summary(
    key: str, results: Path, written: Optional[int], label: Optional[str] = None, s3_uri: Optional[str] = None
) -> None:
    """Rows written by this call (when known) and the verdict and finish-reason counts of its rows file.

    With a ``label`` the file is a working copy: the summary says so, and how to refresh the
    main file that the reports read.
    """
    if written is not None:
        print(f"== {key} horn: {written} rows written by this call")
    path = bt.horn_rows_path(key, results, label)
    if label is not None:
        main = bt.horn_rows_path(key, results)
        if s3_uri is None:
            print(f"  {path} is a working copy of this process; with --no-s3 nothing links it to {main}")
        else:
            print(
                f"  {path} is a working copy: it holds this process's rows and the bucket's rows as of its start, "
                f"not the other process's later rows, and the reports read {main}.\n"
                f"  Refresh {main} with every row of the bucket (no process may be writing it) by running from "
                f"the repository root:\n"
                f"    python -c \"import sys; sys.path.insert(0, 'rebuttal'); import bedrock_trio as bt; "
                f"print(bt.pull_horn_rows({key!r}, {s3_uri!r}, results_dir=bt.Path({str(results)!r})))\""
            )
    if not path.exists():
        return
    print(f"  counts by (model, arm) over {path}")
    for (model, arm), counts in sorted(bt.horn_breakdown([path]).items()):
        if model == key:
            print(f"  {arm}: {counts}")


def _run_horn(args: argparse.Namespace, s3_uri: Optional[str], results: Path) -> int:
    """Run the Horn study for ``args.model`` (the notebook's cell 11)."""
    model, reasoning = _prepare(args, s3_uri)
    m = bt.horn_m(model.key)
    rung = bt.render_horn_rung(m, args.seeds, rungs_dir=bt.RUNGS_DIR, arms=args.arms)
    try:
        rows = bt.run_horn(
            model, args.region, reasoning, rung, args.seeds, args.reps,
            concurrency=args.concurrency, out=bt.horn_rows_path(model.key, results, args.rows_label),
            arms=args.arms, s3_uri=s3_uri, push_every=args.push_every,
            deadline=args.deadline, max_consecutive_failures=args.max_consecutive_failures,
            rep_indices=args.rep_indices, ramp_start=args.ramp_start, ramp_minutes=args.ramp_minutes,
        )
    except bt.HornRunStopped as err:
        # The rows are on disk and pushed; the run is continued by running the command again.
        LOG.error("stopped: %s", err)
        _print_horn_summary(model.key, results, None, args.rows_label, s3_uri)
        return EXIT_STOPPED
    _print_horn_summary(model.key, results, len(rows), args.rows_label, s3_uri)
    return EXIT_OK


def run(args: argparse.Namespace) -> int:
    """Run the study that ``args`` selects and return the exit code.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed and defaulted arguments (``build_parser``, ``resolve_defaults``).

    Returns
    -------
    int
        0 on completion or at the deadline, 2 on ``HornRunStopped``, 1 on any other error
        (an unknown model key, an unreachable bucket, a model that does not reason, ...).
    """
    if args.model not in bt.TRIO:
        print(f"unknown model {args.model!r}: choose one of {', '.join(bt.TRIO)}", file=sys.stderr)
        return EXIT_ERROR
    s3_uri, results = _results_location(args)
    deadline = getattr(args, "deadline", None)
    arms = args.arms if args.study == "horn" else bt.INDUCTION_ARMS
    print(
        f"{args.model} {args.study}: seeds {_seed_text(args.seeds)}"
        + (f" x {args.reps} reps" if args.study == "horn" else "")
        + f", arms {' '.join(arms)}, concurrency {args.concurrency}, results {s3_uri or results}"
        + (f" (mirror {results})" if s3_uri else "")
        + f", deadline {deadline.isoformat() if deadline else 'none'}"
        + (_horn_scope_text(args) if args.study == "horn" else "")
    )
    # Design: a deadline already past is answered before authenticating, so that a late
    # start costs neither a token nor the (billed) reasoning probe.
    if deadline is not None and bt.utcnow() >= deadline:
        print(f"{args.model}: the deadline has passed; nothing started")
        return EXIT_OK
    try:
        if args.study == "induction":
            return _run_induction(args, s3_uri, results)
        return _run_horn(args, s3_uri, results)
    except Exception as err:  # pylint: disable=broad-exception-caught
        LOG.error("%s %s failed: %s: %s", args.model, args.study, type(err).__name__, err, exc_info=True)
        return EXIT_ERROR


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command-line entry point.

    Parameters
    ----------
    argv : Optional[Sequence[str]]
        Arguments after the program name; default ``sys.argv[1:]``.

    Returns
    -------
    int
        The exit code (see the module docstring). A usage error exits through
        ``SystemExit(1)``.
    """
    parser = build_parser()
    args = resolve_defaults(parser.parse_args(argv))
    check_horn_args(parser, args)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
