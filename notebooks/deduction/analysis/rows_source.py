"""Where this study's verified rows live on S3, and which of them are retired.

Centralizes the bucket/prefix lookup and the retired-artifact guard so all
three report scripts read one archive instead of each expecting a local
``--rows-dir`` tree that nothing writes. S3's
``<prefix>/scaling_<key>/verified_rows.jsonl`` lands locally as
``<key>/<candidate>`` (``scaling_`` stripped), matching what ``error_bars``
and ``hint_vs_noise`` already expect from ``--rows-dir``.

These scripts run under ``uv run --no-project`` (no smolbench or boto3
installed by default); ``boto3`` is imported lazily inside
`download_scaling_rows` so every non-S3 path stays usable there.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from smolbench.evals.retired_markers import is_retired  # noqa: E402
from smolbench.evals.study_config import load_study_config  # noqa: E402

# The archive's address.
# Read from the committed study_config.toml (same file the fleet driver and
# results store read), not restated as a literal, so no script can point at a
# bucket a run never wrote to. study_config reads no env vars, so resolving at
# import time (load_study_config is memoized) can't miss a late override. The
# spool PREFIX, by contrast, is env-overridable and resolved per call instead
# -- see `spool_prefix`.
S3_BUCKET = load_study_config().results.bucket
S3_REGION = load_study_config().results.region

#: Duplicated from `smolbench.deduction.lean.runner.DEDUCTION_SPOOL_PREFIX`
#: rather than imported: that module reaches the provider and corpus stacks.
_DEDUCTION_SPOOL_PREFIX = "deduction_postcutoff/runs"


def spool_prefix() -> str:
    """The ``LEAN_SPOOL_PREFIX`` override, or `_DEDUCTION_SPOOL_PREFIX`; never trailing "/".

    Resolved per call, never at import or as an argparse default, so a late
    override takes effect.
    """
    raw = os.environ.get("LEAN_SPOOL_PREFIX", "").strip()
    return raw.rstrip("/") if raw else _DEDUCTION_SPOOL_PREFIX


# The retired-artifact guard.
def _banner(title: str, lines: Iterable[str]) -> str:
    """The loud guards all print the same 78-column "!!" frame; build it once."""
    bar = "!" * 78
    return "\n".join([bar, f"!!  {title}", bar, *lines, bar])


def reject_superseded(paths: Iterable[str | Path]) -> None:
    """Refuse retired row artifacts, loudly and by name.

    Raises ``SystemExit`` naming every path `retired_markers.is_retired`
    rejects. A warning would not do: these files parse and their rows are
    well-formed, so ingesting one yields a complete, plausible, wrong report.

    Parameters
    ----------
    paths : Iterable[str | Path]
        accepts full ``s3://bucket/key`` URIs, not just local paths --
        matched on the basename, so the message still names the offending run.
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


# S3 -> local.
def download_scaling_rows(
    dest_dir: Path,
    *,
    prefix: str,
    candidates: tuple[str, ...] = ("verified_rows.jsonl",),
    client: Any = None,
) -> list[Path]:
    """Download this study's ``scaling_*`` run row files from S3 into `dest_dir`.

    Lists each run's objects before downloading, rather than probing candidate
    keys and swallowing 404s: this makes every object visible to the
    retired-artifact guard before anything downloads, and turns a missing
    candidate into a listing fact instead of a caught ``ClientError``.

    Returns the downloaded local paths, sorted. A run with none of
    `candidates` present is silently omitted rather than raising: a partially
    collected study is a legitimate input to `power_analysis` (its
    ``--models`` filter exists for that), while ``error_bars`` and
    ``hint_vs_noise`` each already fail on a missing lane in their own terms.

    Parameters
    ----------
    prefix : str
        S3 key prefix WITH a trailing "/"; callers resolve it
        (`spool_prefix`, or a CLI value) rather than a module constant, so a
        late ``LEAN_SPOOL_PREFIX`` override applies per call.
    candidates : tuple[str, ...]
        basenames tried in preference order; the chosen name is also
        the landed basename, so `power_analysis`'s unverified-input banner
        still fires on its ``all_rows.jsonl`` fallback.
    client : Any
        optional S3 client, for tests; only
        ``get_paginator("list_objects_v2")`` and ``download_file`` are called
        on it.
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
            continue  # partial collection is valid input; see docstring above

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
    client: Any = None,
) -> Path:
    """Return a local directory of ``<model>/verified_rows.jsonl``, fetching if asked.

    The single entry point the report scripts call once in `main`.

    Raises `ValueError` if both or neither of `rows_dir` / `s3_prefix` is
    given -- the CLIs also enforce this via a required mutually-exclusive
    group, but the function is directly importable. Raises `SystemExit` if
    the download found no run files, or via `download_scaling_rows`'
    retired-artifact guard.

    The fetch temp directory is left uncleaned: a reader commonly re-runs the
    same report against rows just fetched and should not pay the download
    again, and the path is printed to stderr for reuse or manual removal.
    That progress line goes to stderr rather than stdout so it never lands in
    a captured transcript of the report itself.

    Parameters
    ----------
    s3_prefix : str | None
        normalized to a single trailing "/"; an empty prefix is
        refused (`ValueError`) rather than guessed at, since it would
        silently list the whole bucket.
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


def add_source_args(parser: argparse.ArgumentParser) -> None:
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


def resolve_from_args(args: argparse.Namespace) -> Path:
    """`resolve_rows_dir` for a parser built by `add_source_args`.

    ``--s3`` with no value arrives as "" (its ``const``), so the default prefix
    is resolved here rather than as an argparse default. The single-element
    `candidates` default stands: neither caller has an ``all_rows.jsonl``
    fallback, and those rows carry the ungraded "unverified" sentinel.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed source arguments.

    Returns
    -------
    Path
        Resolved rows directory.
    """
    return resolve_rows_dir(
        rows_dir=args.rows_dir,
        s3_prefix=None if args.s3 is None else (args.s3 or spool_prefix()),
    )
