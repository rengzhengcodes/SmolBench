"""Resolve verified study rows and reject retired artifacts.

S3 rows land in the local layout report scripts expect:
``<prefix>/scaling_<key>/verified_rows.jsonl`` becomes ``<key>/<candidate>`` with
``scaling_`` stripped. Import boto3 only for S3 downloads so ``uv run --no-project``
local paths remain usable. ``download_scaling_rows(run_marker="")`` accepts every run
directory, which is how the marker-less DojoInit recovery spool is fetched.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from smolbench.evals.retired_markers import is_retired  # noqa: E402
from smolbench.evals.spool import spool_prefix  # noqa: E402
from smolbench.evals.study_config import load_study_config  # noqa: E402
from smolbench.evals import _aws  # noqa: E402

# Use committed study config so readers cannot target an unwritten bucket.
# Resolve the env-overridable spool prefix per call.
S3_BUCKET = load_study_config().results.bucket
S3_REGION = load_study_config().results.region

def _banner(title: str, lines: Iterable[str]) -> str:
    """Build the shared 78-column refusal frame."""
    bar = "!" * 78
    return "\n".join([bar, f"!!  {title}", bar, *lines, bar])


def reject_superseded(paths: Iterable[str | Path]) -> None:
    """Refuse retired row artifacts, loudly and by name.

    Raise ``SystemExit`` for every path `retired_markers.is_retired` rejects:
    well-formed retired rows would yield a plausible wrong report.

    Parameters
    ----------
    paths : Iterable[str | Path]
        Paths or S3 URIs, matched on basename.
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


def download_scaling_rows(
    dest_dir: Path,
    *,
    prefix: str,
    candidates: tuple[str, ...] = ("verified_rows.jsonl",),
    run_marker: str = "scaling_",
    client: Any = None,
) -> list[Path]:
    """Download this study's ``<run_marker>*`` run row files from S3 into `dest_dir`.

    List before downloading so the retired guard sees every object. Omit runs
    without candidates because partial studies are valid `power_analysis` input.

    Parameters
    ----------
    dest_dir : Path
        Download destination.
    prefix : str
        Trailing-slash S3 prefix, resolved per call for late ``LEAN_SPOOL_PREFIX`` overrides.
    candidates : tuple[str, ...]
        Candidate basenames; retain the chosen name so `power_analysis` flags ``all_rows.jsonl`` as unverified.
    run_marker : str, optional
        Run-directory name prefix under `prefix`; ``""`` accepts every run directory.
    client : Any
        Optional S3 client.

    Returns
    -------
    list[Path]
        Sorted downloaded paths.
    """
    if client is None:
        # Keep non-S3 paths boto3-free.
        client = _aws.fresh_client("s3", S3_REGION)

    paginator = client.get_paginator("list_objects_v2")

    # Delimiter groups each run into one prefix; ``run_marker=""`` matches every
    # directory, which the recovery tree with no shared marker relies on.
    run_prefixes = sorted(
        common["Prefix"]
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix, Delimiter="/")
        for common in page.get("CommonPrefixes", [])
        if Path(common["Prefix"].rstrip("/")).name.startswith(run_marker)
    )

    downloaded: list[Path] = []
    for run_prefix in run_prefixes:
        keys = [
            obj["Key"]
            for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=run_prefix)
            for obj in page.get("Contents", [])
        ]
        # Full URIs identify the offending run in refusals.
        reject_superseded(f"s3://{S3_BUCKET}/{key}" for key in keys)

        present = {Path(key).name for key in keys}
        chosen = next((name for name in candidates if name in present), None)
        if chosen is None:
            continue  # Partial collection is valid input.

        # With run_marker="" this slices at 0 and leaves the segment whole --
        # the "strip nothing" half of the unmarked layout's contract.
        model_key = Path(run_prefix.rstrip("/")).name[len(run_marker):]
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
    run_marker: str = "scaling_",
    client: Any = None,
) -> Path:
    """Return local rows, downloading S3 rows when requested.

    Exactly one source is required. Keep fetched rows for reuse; progress goes
    to stderr so it cannot enter report output.

    Parameters
    ----------
    rows_dir : Path | None
        Local rows directory.
    s3_prefix : str | None
        S3 prefix; empty prefixes are refused to avoid listing the whole bucket.
    candidates : tuple[str, ...], optional
        Candidate row basenames.
    run_marker : str, optional
        Run-directory name prefix under `prefix`; ``""`` accepts every run directory.
    client : Any, optional
        S3 client.

    Returns
    -------
    Path
        Resolved row directory.
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
        dest_dir, prefix=normalized, candidates=candidates, run_marker=run_marker,
        client=client,
    )
    if not landed:
        # `run_marker` is echoed literally (including the empty string) so the
        # message stays true of whichever convention was actually searched,
        # rather than hard-coding the default's "scaling_*" past the point
        # this function started accepting other conventions too.
        raise SystemExit(
            f"no {run_marker}*/{candidates[0]} objects found under "
            f"s3://{S3_BUCKET}/{normalized} -- nothing to analyze. Check the "
            f"prefix (--s3 <PREFIX>, or LEAN_SPOOL_PREFIX) and that the "
            f"verification pass has run."
        )
    return dest_dir


def add_source_args(parser: argparse.ArgumentParser) -> None:
    """Add shared ``--rows-dir`` / ``--s3 [PREFIX]`` arguments."""
    # argparse rejects required arguments inside mutually exclusive groups.
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
    """Resolve rows for a parser built by `add_source_args`.

    Resolve valueless ``--s3`` here. Keep the verified-only candidate because
    ``all_rows.jsonl`` carries the ungraded ``unverified`` sentinel.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    Path
        Row directory.
    """
    return resolve_rows_dir(
        rows_dir=args.rows_dir,
        s3_prefix=None if args.s3 is None else (args.s3 or spool_prefix()),
    )
