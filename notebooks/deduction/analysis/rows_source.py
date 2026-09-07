"""Where this study's verified rows come from, and which of them are retired.

This module is the ONE place the deduction analysis scripts ask two questions:
"which S3 prefix holds this study's rows, and how are they laid out?" and "is
this artifact a live measurement or a retired one?". It exists because all
three scripts in this directory need both answers and only one of them used to
have either: ``power_analysis.py`` owned the bucket constants, the spool-prefix
resolver, the retired-artifact guard and the only S3 downloader, while
``error_bars.py`` and ``hint_vs_noise.py`` -- the two scripts the PUBLISHED
deduction numbers come from -- could read nothing but a local ``--rows-dir``
tree, in a ``<rows_dir>/<model>/verified_rows.jsonl`` layout that nothing in
this repository writes. The archive was therefore unreachable from the exact
scripts whose numbers were published. Concentrating the layout knowledge here
lets all three offer the same ``--s3`` / ``--rows-dir`` choice against one
implementation, so a change to the archive layout is a change to one file.

LAYOUTS -- the two this module bridges, spelled out because they differ:

* On S3 the writers spool one run per model to
  ``s3://<S3_BUCKET>/<prefix>/scaling_<spec-key>/verified_rows.jsonl``.
* On disk `download_scaling_rows` lands each run at
  ``<dest_dir>/<spec-key>/<candidate>`` -- the leading ``scaling_`` STRIPPED,
  which is precisely the tree ``error_bars.lane_outcomes`` and
  ``hint_vs_noise.main`` already read from ``--rows-dir``.

RUN ENVIRONMENT -- these scripts' documented run environment is ``uv run
--no-project --with numpy --with scipy``: an interpreter with neither smolbench
nor boto3 installed. That constrains this module in two separate places. Which
smolbench modules it may import is settled by the ``sys.path`` insert below and
the comment above it. And ``boto3`` is imported inside `download_scaling_rows`
alone, never at module scope, so every local ``--rows-dir`` run and every pure
function in these scripts stays usable in that environment; only an actual
``--s3`` fetch needs an interpreter that has boto3.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from smolbench.evals.retired_markers import is_retired  # noqa: E402
from smolbench.evals.study_config import load_study_config  # noqa: E402

# --------------------------------------------------------------------------- #
# The archive's address.
# --------------------------------------------------------------------------- #
# Both values are the committed config's -- ``smolbench/evals/study_config.toml``,
# the same file the fleet driver and the results store read -- so no analysis
# script can point at a bucket the run never wrote to. They are deliberately
# not restated in prose anywhere: prose could drift from the bucket a run
# actually reads.
#
# Import-time versus call-time resolution is immaterial here: `study_config`
# reads no environment variables at all (that is a documented invariant of its
# module, not an accident), so there is no late `load_dotenv` whose effect a
# frozen import-time read could miss. `load_study_config` is memoized, so
# resolving at import costs one TOML parse the rest of the process reuses.
#
# The spool PREFIX, by contrast, is env-overridable and so must NOT be a
# constant -- see `spool_prefix`.
S3_BUCKET = load_study_config().results.bucket
S3_REGION = load_study_config().results.region

#: This study's S3 key prefix; duplicated from
#: `smolbench.deduction.lean.runner.DEDUCTION_SPOOL_PREFIX` rather than imported,
#: because that module reaches the provider and corpus stacks.
_DEDUCTION_SPOOL_PREFIX = "deduction_postcutoff/runs"


def spool_prefix() -> str:
    """The ``LEAN_SPOOL_PREFIX`` override, or `_DEDUCTION_SPOOL_PREFIX`; never trailing "/".

    Resolved per call, never at import or as an argparse default, so a late
    override takes effect.
    """
    raw = os.environ.get("LEAN_SPOOL_PREFIX", "").strip()
    return raw.rstrip("/") if raw else _DEDUCTION_SPOOL_PREFIX


# --------------------------------------------------------------------------- #
# The retired-artifact guard.
# --------------------------------------------------------------------------- #
def _banner(title: str, lines) -> str:
    """The loud guards all print the same 78-column "!!" frame; build it once."""
    bar = "!" * 78
    return "\n".join([bar, f"!!  {title}", bar, *lines, bar])


def reject_superseded(paths) -> None:
    """Refuse retired row artifacts, loudly and by name.

    Raises ``SystemExit`` naming every path `retired_markers.is_retired` rejects.
    A warning would not do: these files parse and their rows are well-formed, so
    ingesting one yields a complete, plausible, WRONG report.

    Parameters
    ----------
    paths : iterable
        Anything ``Path`` accepts. `download_scaling_rows` feeds it full
        ``s3://bucket/key`` URIs rather than local paths -- ``Path("s3://b/x/"
        "a_SUPERSEDED-1.jsonl").name`` is still the basename, so the guard's
        semantics are unchanged while the message names the offending RUN.
    """
    bad = [str(p) for p in paths if is_retired(p)]
    if not bad:
        return
    raise SystemExit(_banner(
        "REFUSING SUPERSEDED ROW FILE(S)",
        [f"!!  {b}" for b in bad] + [
            "!!",
            "!!  A *_SUPERSEDED-* file is a RETIRED artifact kept as an audit",
            "!!  trail (see run_study.py --force-rerun). Its rows were collected",
            "!!  on hardware that has since been superseded; pooling them with",
            "!!  current rows re-creates the mixed-hardware confound the archive",
            "!!  was made to remove. Point the loader at verified_rows.jsonl.",
        ]))


# --------------------------------------------------------------------------- #
# S3 -> local.
# --------------------------------------------------------------------------- #
def download_scaling_rows(
    dest_dir: Path,
    *,
    prefix: str,
    candidates: tuple[str, ...] = ("verified_rows.jsonl",),
    client=None,
) -> list[Path]:
    """Download this study's ``scaling_*`` run row files from S3 into `dest_dir`.

    Lists ``s3://S3_BUCKET/<prefix>`` with ``Delimiter="/"`` and keeps the
    common prefixes whose last path segment starts with ``scaling_``. For each
    such run it then LISTS the run's objects and downloads the first entry of
    `candidates` that is actually present, to
    ``dest_dir/<model_key>/<candidate>``, where ``<model_key>`` is the run
    prefix's last segment with the leading ``scaling_`` stripped.

    WHY LIST INSTEAD OF BLIND-DOWNLOADING. The obvious implementation asks S3
    for each candidate key in turn and swallows the 404. Listing first buys two
    things a 404-probe loop cannot:

    1. It makes the retired-artifact guard reachable on the S3 path AT ALL.
       `reject_superseded` used to see only LOCAL paths, so an
       ``all_rows_SUPERSEDED-<stamp>.jsonl`` object sitting in the bucket was
       silently invisible to every ``--s3`` reader -- exactly the "complete,
       plausible, WRONG report" hazard that guard exists to prevent. Every
       listed key of a run goes through `reject_superseded` BEFORE anything is
       downloaded from that run.
    2. A missing object becomes a FACT (a membership test on the listing)
       instead of a swallowed ``ClientError`` -- no ``botocore`` exception
       handling, and no risk of a non-404 error being mistaken for absence.

    ONE DOWNLOADER FOR THREE SCRIPTS. The ``<model_key>/<candidate>`` layout is
    what ``error_bars.lane_outcomes`` and ``hint_vs_noise.main`` already expect
    from ``--rows-dir`` (``<rows_dir>/<model>/verified_rows.jsonl``), and
    ``power_analysis.load_joint_cells`` does not look at directory names at all
    -- it keys each model off the row's own ``model`` field. So this single
    layout serves all three, and `power_analysis` merely sees its local scratch
    tree lose a ``scaling_`` prefix it never read.

    Parameters
    ----------
    dest_dir : Path
        Directory to land runs under; per-run subdirectories are created.
    prefix : str
        S3 key prefix to list under, WITH a trailing "/". Callers resolve this
        (`spool_prefix`, or a CLI value) and pass it in -- it is never a module
        constant, so a late ``LEAN_SPOOL_PREFIX`` override takes effect per
        invocation.
    candidates : tuple of str, optional
        Basenames to look for inside a run, in PREFERENCE order; the first one
        present wins. The default is the single verified file. `power_analysis`
        passes ``("verified_rows.jsonl", "all_rows.jsonl")`` to keep its
        documented fallback; because the candidate name is also the landed
        basename, ``load_joint_cells``'s unverified-input banner still fires on
        the fallback under this layout.
    client : optional
        An S3 client. Defaults to ``None`` -> a lazily built
        ``boto3.client("s3", region_name=S3_REGION)``. It is a parameter so
        tests can inject a fake; only ``get_paginator("list_objects_v2")`` and
        ``download_file`` are ever called on it.

    Returns
    -------
    list of Path
        The downloaded local paths, sorted. A run with NONE of `candidates`
        present is silently omitted rather than raising: a partially collected
        study is a legitimate input to `power_analysis`, whose ``--models``
        filter exists for exactly that case. ``error_bars`` and
        ``hint_vs_noise`` do require all 21 lanes, but each already fails on a
        missing one in its own terms (``error_bars.main``'s ``missing row
        files`` pre-check; a ``FileNotFoundError`` naming the lane in
        ``hint_vs_noise``), so that check is not duplicated here.

    Raises
    ------
    SystemExit
        Via `reject_superseded`, if any object in a run carries a retirement
        marker in its basename -- before that run is downloaded.

    Notes
    -----
    ``boto3`` is imported INSIDE this function, and only when `client` is not
    supplied, so both the local ``--rows-dir`` path and an injected-client test
    run in an interpreter without boto3 installed.

    Both listings go through the paginator. Nothing bounds the object count
    under a run prefix -- ``ListObjectsV2`` returns at most 1000 keys per
    response and sets a continuation token past that -- so paginating the
    per-run listing is what makes the retired-artifact scan complete rather
    than a scan of the first page. The run-prefix discovery is paginated for
    the same reason and, secondarily, so this function needs only two methods
    from `client`; no overflow has been observed at either listing, this is
    the safe default rather than a fix for a measured failure.
    """
    if client is None:
        # Lazy, and skipped entirely for an injected client: keeps every
        # non-S3 code path in these scripts boto3-free.
        import boto3

        client = boto3.client("s3", region_name=S3_REGION)

    paginator = client.get_paginator("list_objects_v2")

    # Phase 1: discover the run prefixes. Delimiter="/" makes S3 roll each
    # <prefix>/scaling_<key>/... family up into one CommonPrefixes entry.
    run_prefixes = sorted(
        common["Prefix"]
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix, Delimiter="/")
        for common in page.get("CommonPrefixes", [])
        if Path(common["Prefix"].rstrip("/")).name.startswith("scaling_")
    )

    # Phase 2: per run, list -> guard -> download at most one file.
    downloaded: list[Path] = []
    for run_prefix in run_prefixes:
        keys = [
            obj["Key"]
            for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=run_prefix)
            for obj in page.get("Contents", [])
        ]
        # Full URIs, not bare basenames: `reject_superseded` matches on the
        # basename either way, and the refusal message then says which run.
        reject_superseded(f"s3://{S3_BUCKET}/{key}" for key in keys)

        present = {Path(key).name for key in keys}
        chosen = next((name for name in candidates if name in present), None)
        if chosen is None:
            continue  # partially collected study; documented in Returns

        model_key = Path(run_prefix.rstrip("/")).name[len("scaling_"):]
        local_dir = dest_dir / model_key
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / chosen
        client.download_file(S3_BUCKET, f"{run_prefix}{chosen}", str(local_path))
        downloaded.append(local_path)
    return sorted(downloaded)


def resolve_rows_dir(
    *,
    rows_dir: Path | None,
    s3_prefix: str | None,
    candidates: tuple[str, ...] = ("verified_rows.jsonl",),
    client=None,
) -> Path:
    """Return a local directory of ``<model>/verified_rows.jsonl``, fetching if asked.

    The single entry point the report scripts call once in `main`: hand it the
    two parsed CLI values and use the returned directory everywhere the local
    ``--rows-dir`` used to be used.

    Parameters
    ----------
    rows_dir : Path or None
        A local tree, returned UNCHANGED and with no I/O of any kind.
    s3_prefix : str or None
        An S3 key prefix, with or without a trailing "/" (normalized here;
        `download_scaling_rows` itself keeps the strict "with trailing /"
        contract). Callers resolve it -- from `spool_prefix` or an explicit
        command-line value -- AFTER ``parse_args``, never as an argparse
        default.
    candidates : tuple of str, optional
        Passed through to `download_scaling_rows`.
    client : optional
        Passed through to `download_scaling_rows`; for tests.

    Returns
    -------
    Path
        `rows_dir`, or the fresh temporary directory the runs were landed in.

    Raises
    ------
    ValueError
        If both or neither of `rows_dir` / `s3_prefix` is given (the CLIs also
        enforce this with a required mutually-exclusive group; this check is
        the belt to that suspenders, since the function is importable), or if
        `s3_prefix` normalizes to the empty string -- an empty prefix would
        silently list the whole bucket, so it is refused rather than guessed
        at.
    SystemExit
        If the download found no run files at all, with a message naming the
        full ``s3://.../`` URI that was searched; or via
        `download_scaling_rows`' retired-artifact guard.

    Notes
    -----
    The temporary directory is deliberately NOT registered for cleanup. Two
    reasons, stated rather than left to look like an oversight: a reader
    commonly re-runs the same report (a different ``-B``, ``--mode``, or
    ``--out-json``) against the rows just fetched and should not pay the
    download again, and the path is printed to stderr so it can be reused or
    removed by hand. These are 21 JSONL files, not a cache that grows without
    bound.

    The progress line goes to STDERR on purpose: these scripts' STDOUT is the
    report itself, and a stray line there would land in any captured transcript
    of the published numbers.
    """
    if (rows_dir is None) == (s3_prefix is None):
        raise ValueError(
            "exactly one of rows_dir= (--rows-dir) or s3_prefix= (--s3) must be "
            f"given; got rows_dir={rows_dir!r}, s3_prefix={s3_prefix!r}"
        )
    if rows_dir is not None:
        return rows_dir

    normalized = s3_prefix.rstrip("/")
    if not normalized:
        raise ValueError(
            "s3_prefix= (--s3) resolved to an empty key prefix, which would list "
            "the entire bucket; pass a real prefix or call spool_prefix() to get "
            "this study's default"
        )
    normalized += "/"

    dest_dir = Path(tempfile.mkdtemp(prefix="smolbench_deduction_rows_"))
    print(
        f"Downloading run rows from s3://{S3_BUCKET}/{normalized} into "
        f"{dest_dir} ...",
        file=sys.stderr,
    )
    landed = download_scaling_rows(
        dest_dir, prefix=normalized, candidates=candidates, client=client
    )
    if not landed:
        raise SystemExit(
            f"no scaling_*/{candidates[0]} objects found under "
            f"s3://{S3_BUCKET}/{normalized} -- nothing to analyze. Check the "
            f"prefix (--s3 <PREFIX>, or LEAN_SPOOL_PREFIX) and that the "
            f"verification pass has run."
        )
    return dest_dir


def add_source_args(parser) -> None:
    """Add the ``--rows-dir`` / ``--s3 [PREFIX]`` source group the report scripts share."""
    # Required on the GROUP, not on `--rows-dir`: argparse rejects a required
    # argument inside a mutually-exclusive group at parser-construction time.
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--rows-dir", type=Path, default=None,
                        help="local directory of <model>/verified_rows.jsonl "
                             "to analyse; the way to read a tree you already "
                             "have, including one a previous --s3 run left "
                             "behind")
    source.add_argument("--s3", nargs="?", const="", default=None,
                        metavar="PREFIX",
                        help="download this study's rows from "
                             "s3://<bucket>/<PREFIX>/scaling_<key>/"
                             "verified_rows.jsonl into a temp "
                             "<dir>/<model>/verified_rows.jsonl tree and "
                             "analyse those. PREFIX is optional and defaults "
                             "to this study's spool prefix (LEAN_SPOOL_PREFIX, "
                             "or the re-collection's), resolved AFTER parsing.")


def resolve_from_args(args) -> Path:
    """`resolve_rows_dir` for a parser built by `add_source_args`.

    ``--s3`` with no value arrives as "" (its ``const``), so the default prefix
    is resolved here rather than as an argparse default. The single-element
    `candidates` default stands: neither caller has an ``all_rows.jsonl``
    fallback, and those rows carry the ungraded "unverified" sentinel.
    """
    return resolve_rows_dir(
        rows_dir=args.rows_dir,
        s3_prefix=None if args.s3 is None else (args.s3 or spool_prefix()),
    )
