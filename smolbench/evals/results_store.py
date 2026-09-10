"""Store replicate results in S3, with local files as an offline fallback.

S3 uses immutable, earliest-surviving runs to preserve pass@1; supersession writes sibling
markers so spent runs remain visible to resume checks. Local storage overwrites one file per
(tag, info, seed); ``sync_down`` copies S3's earliest survivors into that layout.
"""

import abc
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import smolbench
from smolbench.evals import Marks
from smolbench.evals import _aws
from smolbench.evals.study_config import load_study_config

# Retire immutable S3 runs with sibling markers.
S3_SUPERSEDED_SUFFIX = ".superseded"

# Keep local retirement names consistent with the deduction layout.
LOCAL_SUPERSEDED_INFIX = ".SUPERSEDED-"


def repo_root() -> Path:
    """Return the absolute repository root for cwd-independent result paths."""
    return Path(smolbench.__file__).resolve().parents[1]


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parse an ``s3://bucket[/base-prefix]`` URI into ``(bucket, base_prefix)``.

    Central parsing keeps readers and writers on the same prefix; surrounding env whitespace is
    stripped by ``resolve_store``, but URI segments may not contain whitespace.

    Parameters
    ----------
    uri : str
        URI to parse.

    Returns
    -------
    tuple[str, str]
        Bucket and prefix.

    Raises
    ------
    ValueError
        For malformed or whitespace-bearing URI segments.
    """
    if not uri.startswith("s3://"):
        raise ValueError(f"S3 URI {uri!r} is malformed: must start with 's3://'")
    rest = uri[len("s3://"):].rstrip("/")
    segments = rest.split("/")
    for i, seg in enumerate(segments):
        kind = "bucket name" if i == 0 else "prefix segment"
        if not seg:
            raise ValueError(
                f"S3 URI {uri!r} is malformed: empty {kind} (a double slash, "
                "or nothing between/after slashes)"
            )
        if seg != seg.strip() or any(ch.isspace() for ch in seg):
            raise ValueError(
                f"S3 URI {uri!r} is malformed: {kind} {seg!r} contains whitespace"
            )
    bucket, *prefix_segments = segments
    base_prefix = "/".join(prefix_segments)
    return bucket, base_prefix


#: The project's study bucket -- the DOCUMENTED FALLBACK used only when
#: ``SMOLBENCH_RESULTS_S3`` is unset (see `resolve_results_location`). Read
#: from the committed ``[results]`` section of ``study_config.toml`` (issue
#46), never re-typed: it was previously a literal duplicated across ten
#: files, so a redirected results store silently did not reach them. Tools
#: import this name; the TOML is the one place the value is written down.
DEFAULT_RESULTS_BUCKET: str = load_study_config().results.bucket


def resolve_results_location() -> tuple[str, str]:
    """Resolve the ``(bucket, base_prefix)`` a TOOL should target for S3 results.

    Reads ``SMOLBENCH_RESULTS_S3`` at CALL time (never a module constant --
    same rationale as :func:`resolve_store`: a notebook runs
    ``load_dotenv(keys.env)`` AFTER ``import smolbench``), stripped exactly as
    :func:`resolve_store` strips it.

    Returns
    -------
    tuple[str, str]
        ``(bucket, base_prefix)``. `base_prefix` is ``""`` for a bucket-only
        URI (or when the env var is unset) and never carries a leading or
        trailing ``"/"`` (see :func:`parse_s3_uri`). Unset, empty, or
        whitespace-only ``SMOLBENCH_RESULTS_S3`` yields
        the committed ``[results]`` ``(bucket, base_prefix)`` from
        ``study_config.toml``, logged at INFO so the fallback is never silent.

    Raises
    ------
    ValueError
        Propagated from :func:`parse_s3_uri` when ``SMOLBENCH_RESULTS_S3`` is
        set but malformed. NOT swallowed and NOT downgraded to the default:
        mirroring `resolve_store`'s step-2 rationale, a typo'd URI must fail
        loudly rather than silently provision or audit the WRONG bucket.

    Notes
    -----
    For TOOLS that need the bucket/prefix pair directly -- a bucket
    provisioner, a completeness auditor, a snapshot exporter -- none of which
    hold or need a ``results_dir``. Code that needs a working
    :class:`ResultsStore` must still go through :func:`resolve_store`, which
    additionally handles the local-store and offline-test hermeticity cases
    (neither of which applies to a tool addressing the bucket itself).
    """
    uri = os.environ.get("SMOLBENCH_RESULTS_S3", "").strip()
    if not uri:
        results = load_study_config().results
        logging.info(
            "resolve_results_location: SMOLBENCH_RESULTS_S3 is unset/empty; "
            f"falling back to the committed study bucket ({results.bucket!r})."
        )
        return results.bucket, results.base_prefix
    return parse_s3_uri(uri)

def default_results_uri() -> str:
    """Return the committed project's canonical results URI."""
    results = load_study_config().results
    if not results.base_prefix:
        return f"s3://{results.bucket}"
    return f"s3://{results.bucket}/{results.base_prefix}"


def utcnow() -> datetime:
    """Return a timezone-aware UTC instant for patchable run timestamps."""
    return datetime.now(timezone.utc)


def format_run_ts(when: datetime) -> str:
    """Format a UTC timestamp for lexicographically ordered S3 keys.

    ``when`` must already be UTC because the literal ``"Z"`` is not converted.

    Parameters
    ----------
    when : datetime
        UTC instant.

    Returns
    -------
    str
        Fixed-width timestamp.
    """
    return when.strftime("%Y%m%dT%H%M%SZ")


def experiment_name(results_dir: Path, prefix: str = "") -> str:
    """Derive an S3 experiment segment from a repository results directory.

    Notebook result paths use the notebook name; the repository root maps to ``""`` rather
    than ``"."``.

    Parameters
    ----------
    results_dir : Path
        Directory under ``repo_root()``.
    prefix : str, optional
        Sub-level; one trailing ``"_"`` is stripped.

    Returns
    -------
    str
        S3 experiment segment.
    """
    rel = results_dir.resolve().relative_to(repo_root())
    parts = rel.parts
    if len(parts) == 3 and parts[0] == "notebooks" and parts[2] == "results":
        base = parts[1]
    else:
        base = "" if rel == Path(".") else rel.as_posix()
    if not prefix:
        return base
    sub = prefix[:-1] if prefix.endswith("_") else prefix
    return f"{base}/{sub}" if base else sub


@dataclass(frozen=True)
class ReplicateAddress:
    """Identify a replicate; local storage keys on ``tag``, S3 on ``model``."""

    #: Local directory key; ignored by S3.
    tag: str
    #: Condition information dimension.
    info: str
    #: Replicate seed.
    seed: int
    #: S3 key; ``None`` is read-only because an immutable log cannot correct a bad key.
    model: Optional[str] = None


class ResultsStore(abc.ABC):
    """Backend-agnostic interface for one experiment's results."""

    @abc.abstractmethod
    def exists(self, addr: ReplicateAddress) -> bool:
        """Return whether a replicate result is already stored at `addr`.

        S3 counts superseded runs so resume checks do not re-bill them; backend failures propagate.

        Parameters
        ----------
        addr : ReplicateAddress
            Replicate address.

        Returns
        -------
        bool
            Whether a result exists.
        """

    @abc.abstractmethod
    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        """Persist `marks` for `addr`, stamped with `run_ts`.

        No existence check; a caller wanting resume-skip calls ``exists`` first.

        Parameters
        ----------
        marks : Marks
            Result to persist.
        addr : ReplicateAddress
            Destination address.
        run_ts : datetime
            Collection instant.
        """

    @abc.abstractmethod
    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """Deserialize the replicate result stored/logged at `addr`.

        Parameters
        ----------
        addr : ReplicateAddress
            Replicate address.

        Returns
        -------
        Marks
            Stored result.

        Raises
        ------
        FileNotFoundError
            If no result is stored.
        """

    @abc.abstractmethod
    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """List every seed with at least one stored/logged replicate.

        Parameters
        ----------
        model : Optional[str]
            S3 key; ``None`` yields no seeds.
        tag : str
            Local key.
        info : str
            Condition information.

        Returns
        -------
        list[int]
            Sorted distinct seeds.
        """

    @abc.abstractmethod
    def supersede_all(self, addr: ReplicateAddress, reason: str) -> int:
        """Retire every currently-surviving run stored/logged at `addr`.

        S3 writes markers rather than changing immutable runs; local storage renames files.

        Parameters
        ----------
        addr : ReplicateAddress
            Address to retire.
        reason : str
            Operator-facing retirement reason.

        Returns
        -------
        int
            Retired run count.
        """

    def regrade(
        self, marks: Marks, addr: ReplicateAddress, run_ts: datetime, *, reason: str
    ) -> None:
        """Replace every surviving run at `addr` with a self-describing regrade.

        Supersede before writing: a crash must fail loudly rather than serve the old earliest run.

        Parameters
        ----------
        marks : Marks
            Must name its replaced run via ``regraded_from``.
        addr : ReplicateAddress
            Address to replace.
        run_ts : datetime
            New run timestamp.
        reason : str
            Retirement reason.
        """
        if marks.regraded_from is None:
            raise ValueError(
                f"ResultsStore.regrade: refusing {addr!r} -- marks.regraded_from "
                "is None; a regrade must name the run_ts of the run it replaces."
            )
        self.supersede_all(addr, reason)
        self.dump_marks(marks, addr, run_ts)

    @abc.abstractmethod
    def describe(self) -> str:
        """Return this store's display location."""


@dataclass(frozen=True)
class LocalResultsStore(ResultsStore):
    """Store ``{prefix}{tag}_{info}/rep_{seed}.yaml`` files, overwriting each address."""

    #: Experiment results directory.
    root: Path
    #: Namespace prefix for directory names.
    prefix: str = ""

    def _dirname(self, tag: str, info: str) -> str:
        return f"{self.prefix}{tag}_{info}"

    def _path(self, addr: ReplicateAddress) -> Path:
        return self.root / self._dirname(addr.tag, addr.info) / f"rep_{addr.seed}.yaml"

    def exists(self, addr: ReplicateAddress) -> bool:
        """Return whether the local result file exists.

        Parameters
        ----------
        addr : ReplicateAddress
            Replicate address.

        Returns
        -------
        bool
            Whether the file exists.
        """
        return self._path(addr).exists()

    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        """Persist marks in the local layout; ``run_ts`` is unused.

        Parameters
        ----------
        marks : Marks
            Result to persist.
        addr : ReplicateAddress
            Destination address.
        run_ts : datetime
            Ignored collection timestamp.
        """
        path = self._path(addr)
        path.parent.mkdir(parents=True, exist_ok=True)
        marks.dump(path)

    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """Load local marks.

        Parameters
        ----------
        addr : ReplicateAddress
            Replicate address.

        Returns
        -------
        Marks
            Local result.
        """
        return Marks.load(self._path(addr))

    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """List seeds from local ``rep_*.yaml`` files.

        Malformed and superseded filenames fail integer parsing and are skipped.

        Parameters
        ----------
        model : Optional[str]
            Ignored local-store model key.
        tag : str
            Local key.
        info : str
            Condition information.

        Returns
        -------
        list[int]
            Sorted seed values.
        """
        dirpath = self.root / self._dirname(tag, info)
        seeds: set[int] = set()
        for path in dirpath.glob("rep_*.yaml"):
            seed_str = path.stem[len("rep_"):]
            try:
                seeds.add(int(seed_str))
            except ValueError:
                continue
        return sorted(seeds)

    def supersede(self, addr: ReplicateAddress, reason: str) -> Optional[Path]:
        """Retire a local run by renaming it to an ignored filename.

        Same-second supersedes share a destination, preserving the one-file-per-address layout;
        the bytes survive on disk, so an operator can restore them by renaming back.

        Parameters
        ----------
        addr : ReplicateAddress
            Stored-run address.
        reason : str
            Logged retirement reason.

        Returns
        -------
        Optional[Path]
            Renamed path, or ``None``.
        """
        path = self._path(addr)
        if not path.exists():
            return None
        retired = path.with_name(
            f"{path.stem}{LOCAL_SUPERSEDED_INFIX}{format_run_ts(utcnow())}.yaml"
        )
        os.replace(path, retired)
        logging.info(f"LocalResultsStore.supersede: {path} -> {retired} ({reason})")
        return retired

    def supersede_all(self, addr: ReplicateAddress, reason: str) -> int:
        """Retire the local run and return zero or one.

        Parameters
        ----------
        addr : ReplicateAddress
            Address to retire.
        reason : str
            Retirement reason.

        Returns
        -------
        int
            Retired run count.
        """
        return 1 if self.supersede(addr, reason) is not None else 0

    def describe(self) -> str:
        """See ``ResultsStore.describe``."""
        return str(self.root)


def _parse_log_entry(rel: str) -> Optional[tuple[int, str, str]]:
    """Parse an S3 key remainder into ``(seed, info, run_ts)``, or ``None``.

    S3 listings are untrusted, so non-matching keys are skipped.

    Parameters
    ----------
    rel : str
        Key remainder.

    Returns
    -------
    Optional[tuple[int, str, str]]
        Parsed values, or ``None``.
    """
    parts = rel.split("/")
    if len(parts) != 2:
        return None
    seed_part, filename = parts
    if not seed_part.startswith("seed=") or not filename.endswith(".yaml"):
        return None
    try:
        seed = int(seed_part[len("seed="):])
    except ValueError:
        return None
    stem = filename[: -len(".yaml")]
    info, sep, run_ts = stem.partition("--")
    if not sep:
        return None
    return seed, info, run_ts


@dataclass(frozen=True)
class S3ResultsStore(ResultsStore):
    """Store immutable replicate runs in an S3 log.

    Supersession uses sibling markers; presence checks remain marker-blind to avoid re-billing.
    """

    #: S3 bucket name.
    bucket: str
    #: URI base prefix without edge slashes.
    base_prefix: str
    #: Experiment log path segment.
    experiment: str
    #: Client region, or boto3's resolution chain.
    region: Optional[str] = None

    def __post_init__(self) -> None:
        """Refuse a store whose :attr:`log_prefix` would be ``""``.

        An empty prefix would address the whole bucket.
        """
        if not self.log_prefix:
            raise ValueError(
                f"S3ResultsStore: refusing an empty log prefix on bucket "
                f"s3://{self.bucket} -- base_prefix and experiment are both "
                "empty, which would address the ENTIRE bucket."
            )

    @property
    def log_prefix(self) -> str:
        """Return this store's key root: `base_prefix` and `experiment` joined.

        Uses one slash and has no edge slashes.
        """
        return "/".join(p for p in (self.base_prefix, self.experiment) if p)

    def _seed_prefix(self, model: str, seed: int) -> str:
        return f"{self.log_prefix}/{model}/seed={seed}/"

    def _info_prefix(self, model: str, seed: int, info: str) -> str:
        """Return the prefix every logged run of this replicate shares."""
        return self._seed_prefix(model, seed) + f"{info}--"

    def _client(self) -> Any:
        """Return an uncached S3 client so rotated credentials apply immediately."""
        return _aws.fresh_client("s3", self.region)

    def exists(self, addr: ReplicateAddress) -> bool:
        """Return whether an S3 run exists; ``None`` model returns ``False``.

        Listing avoids treating credential failures as absence.

        Parameters
        ----------
        addr : ReplicateAddress
            Replicate address.

        Returns
        -------
        bool
            Whether a run exists.
        """
        if addr.model is None:
            return False
        resp = self._client().list_objects_v2(
            Bucket=self.bucket,
            Prefix=self._info_prefix(addr.model, addr.seed, addr.info),
            MaxKeys=1,
        )
        return bool(resp.get("Contents"))

    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        """Write marks under a timestamped S3 key.

        A ``None`` model is refused because immutable logs cannot correct a bad key.

        Parameters
        ----------
        marks : Marks
            Result to persist.
        addr : ReplicateAddress
            Destination address.
        run_ts : datetime
            Key timestamp.
        """
        if addr.model is None:
            raise ValueError(
                f"S3ResultsStore.dump_marks: refusing to write {addr!r} -- "
                "the S3 log is keyed by model, and this address carries no "
                "model. model=None is a READ-only shape (used by tag-keyed "
                "lookups such as ReplicateHarness.cot_chain_lengths when no "
                "configured model carries the requested tag, served by "
                "LocalResultsStore instead, whose layout has no model "
                "dimension); it must never be written to the append-only "
                "log, where a bad object cannot later be corrected, only "
                "deleted by hand."
            )
        key = self._info_prefix(addr.model, addr.seed, addr.info) + format_run_ts(run_ts) + ".yaml"
        self._client().put_object(Bucket=self.bucket, Key=key, Body=marks.dumps().encode())

    def _list_run_partition(self, addr: ReplicateAddress) -> "tuple[list[str], int]":
        """List run stamps and supersession markers in one traversal.

        Parameters
        ----------
        addr : ReplicateAddress
            Replicate address.

        Returns
        -------
        tuple[list[str], int]
            Sorted survivors and marker count.
        """
        prefix = self._info_prefix(addr.model, addr.seed, addr.info)
        client = self._client()
        paginator = client.get_paginator("list_objects_v2")
        marker_stamps: set[str] = set()
        run_stamps: list[str] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                rest = obj["Key"][len(prefix):]
                if rest.endswith(S3_SUPERSEDED_SUFFIX):
                    marker_stamps.add(rest[: -len(S3_SUPERSEDED_SUFFIX)])
                elif rest.endswith(".yaml"):
                    run_stamps.append(rest[: -len(".yaml")])
        survivors = sorted(ts for ts in run_stamps if ts not in marker_stamps)
        return survivors, len(marker_stamps)

    def list_runs(self, addr: ReplicateAddress) -> "list[str]":
        """Return ascending run stamps without sibling supersession markers.

        Parameters
        ----------
        addr : ReplicateAddress
            Replicate address.

        Returns
        -------
        list[str]
            Sorted surviving timestamps.
        """
        survivors, _marker_count = self._list_run_partition(addr)
        return survivors

    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """Load the earliest surviving S3 run.

        Missing survivors report whether markers retired prior runs.

        Parameters
        ----------
        addr : ReplicateAddress
            Replicate address.

        Returns
        -------
        Marks
            Earliest surviving result.
        """
        prefix = self._info_prefix(addr.model, addr.seed, addr.info)
        survivors, marker_count = self._list_run_partition(addr)
        if not survivors:
            if marker_count:
                raise FileNotFoundError(
                    f"no surviving logged run under s3://{self.bucket}/{prefix} "
                    f"-- {marker_count} logged run(s) there were superseded "
                    "and never replaced"
                )
            raise FileNotFoundError(
                f"no logged run under s3://{self.bucket}/{prefix}"
            )
        earliest_key = prefix + survivors[0] + ".yaml"
        obj = self._client().get_object(Bucket=self.bucket, Key=earliest_key)
        return Marks.loads(obj["Body"].read().decode())

    def supersede(self, addr: ReplicateAddress, run_ts: str, reason: str) -> str:
        """Write a sibling marker to retire one immutable S3 run.

        The run stamp need not exist; a stray marker is harmless.

        Parameters
        ----------
        addr : ReplicateAddress
            Logged-run address.
        run_ts : str
            Run-key timestamp.
        reason : str
            Marker-body reason.

        Returns
        -------
        str
            Written marker key.
        """
        if addr.model is None:
            raise ValueError(
                f"S3ResultsStore.supersede: refusing {addr!r} -- model=None "
                "is a READ-only address shape (see ReplicateAddress.model); "
                "nothing is ever logged there to supersede."
            )
        key = self._info_prefix(addr.model, addr.seed, addr.info) + run_ts + S3_SUPERSEDED_SUFFIX
        body = json.dumps({"superseded_at": utcnow().isoformat(), "reason": reason}).encode()
        self._client().put_object(Bucket=self.bucket, Key=key, Body=body)
        return key

    def supersede_all(self, addr: ReplicateAddress, reason: str) -> int:
        """Retire every surviving S3 run; repeated calls return zero.

        Parameters
        ----------
        addr : ReplicateAddress
            Address to retire.
        reason : str
            Retirement reason.

        Returns
        -------
        int
            Retired run count.
        """
        survivors = self.list_runs(addr)
        for run_ts in survivors:
            self.supersede(addr, run_ts, reason)
        return len(survivors)

    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """List S3 seeds for an info value; ``None`` model yields ``[]``.

        Marker-blind listings retain retired runs for resume checks.

        Parameters
        ----------
        model : Optional[str]
            S3 model key.
        tag : str
            Unused S3 tag.
        info : str
            Condition information.

        Returns
        -------
        list[int]
            Sorted seeds.
        """
        if model is None:
            return []
        client = self._client()
        paginator = client.get_paginator("list_objects_v2")
        list_prefix = f"{self.log_prefix}/{model}/"
        seeds: set[int] = set()
        for page in paginator.paginate(Bucket=self.bucket, Prefix=list_prefix):
            for obj in page.get("Contents", []):
                parsed = _parse_log_entry(obj["Key"][len(list_prefix):])
                if parsed is None:
                    continue
                seed, entry_info, _run_ts = parsed
                if entry_info == info:
                    seeds.add(seed)
        return sorted(seeds)

    def describe(self) -> str:
        """See ``ResultsStore.describe``."""
        return f"s3://{self.bucket}/{self.log_prefix}"


def resolve_store(results_dir: Path, prefix: str = "") -> ResultsStore:
    """Resolve the local or S3 store for ``results_dir``.

    Validate an S3 URI before the hermetic local fallback so typos do not silently lose results.
    Configured regions apply only to the project's bucket.
    Read at call time, not import: a notebook runs ``load_dotenv`` after importing smolbench.

    Parameters
    ----------
    results_dir : Path
        Results directory.
    prefix : str, optional
        Local namespace or S3 experiment subpath.

    Returns
    -------
    ResultsStore
        Results store.
    """
    uri = os.environ.get("SMOLBENCH_RESULTS_S3", "").strip()
    if not uri:
        return LocalResultsStore(results_dir, prefix)

    bucket, base_prefix = parse_s3_uri(uri)

    try:
        results_dir.resolve().relative_to(repo_root())
    except ValueError:
        logging.info(
            f"resolve_store: SMOLBENCH_RESULTS_S3 is set, but {results_dir} is "
            f"not under repo_root() ({repo_root()}); using the local store "
            "(this is the offline-test-suite hermeticity fallback)."
        )
        return LocalResultsStore(results_dir, prefix)

    experiment = experiment_name(results_dir, prefix)

    # Use configured region only for the configured bucket.
    results_config = load_study_config().results
    config_region = results_config.region if bucket == results_config.bucket else None
    region = (
        os.environ.get("SMOLBENCH_RESULTS_S3_REGION")
        or os.environ.get("AWS_REGION")
        or config_region
    )

    return S3ResultsStore(
        bucket=bucket, base_prefix=base_prefix, experiment=experiment, region=region
    )


def _etag_md5(etag: Optional[str]) -> Optional[str]:
    """Extract a single-part object MD5 from an S3 ``ETag`` value.

    Parameters
    ----------
    etag : Optional[str]
        S3 ETag.

    Returns
    -------
    Optional[str]
        Unquoted MD5, or ``None`` for missing or multipart ETags.
    """
    if not etag:
        return None
    unquoted = etag.strip('"')
    if "-" in unquoted:
        return None
    return unquoted


def _resolve_download_path(resolved_dir: Path, rel: str, key: str) -> Path:
    """Join an untrusted S3-derived path under ``resolved_dir``.

    Parameters
    ----------
    resolved_dir : Path
        Resolved local directory.
    rel : str
        Relative destination.
    key : str
        Source S3 key.

    Returns
    -------
    Path
        Validated destination.

    Raises
    ------
    ValueError
        If the destination is outside ``resolved_dir``.
    """
    candidate = (resolved_dir / rel).resolve()
    if candidate == resolved_dir or not candidate.is_relative_to(resolved_dir):
        raise ValueError(
            f"sync_down: refusing S3 key {key!r}: resolves to {candidate}, "
            f"outside results_dir {resolved_dir}"
        )
    return candidate


def sync_down(results_dir: Path, tags: Mapping[str, str], prefix: str = "") -> int:
    """Copy earliest surviving S3 runs into the local analysis layout.

    Selection must match ``load_marks``; collect markers and candidates in one listing to use a
    consistent snapshot. Skip only matching single-part ETag MD5s, since size can match regrades.
    One-way and destructive: overwrites local files and never touches the log, so a local-only
    regrade is silently destroyed.

    Parameters
    ----------
    results_dir : Path
        Local destination.
    tags : Mapping[str, str]
        Model-to-local-tag mapping.
    prefix : str, optional
        Experiment and local-directory prefix.

    Returns
    -------
    int
        Downloaded object count.
    """
    store = resolve_store(results_dir, prefix)
    if not isinstance(store, S3ResultsStore):
        uri = os.environ.get("SMOLBENCH_RESULTS_S3", "").strip()
        if not uri:
            raise RuntimeError(
                "sync_down: SMOLBENCH_RESULTS_S3 is unset or empty -- there is "
                f"no S3 log to sync down from. Export it, e.g. "
                f"SMOLBENCH_RESULTS_S3={default_results_uri()!r}."
            )
        raise RuntimeError(
            f"sync_down: {results_dir} is not under repo_root() "
            f"({repo_root()}), so resolve_store falls back to the local "
            "store for it (see resolve_store's hermeticity fallback) -- "
            f"there is no S3 log to sync down from. (SMOLBENCH_RESULTS_S3 is "
            f"set to {uri!r}; the project's default is "
            f"{default_results_uri()!r}.)"
        )

    resolved_dir = results_dir.resolve()
    client = store._client()
    paginator = client.get_paginator("list_objects_v2")
    downloaded = 0
    skipped = 0
    for model, tag in tags.items():
        list_prefix = f"{store.log_prefix}/{model}/"
        # Select after traversal so every marker shares the listing snapshot.
        superseded: dict[tuple[int, str], set[str]] = {}
        # Retain candidates until every marker is known.
        candidates: dict[tuple[int, str], list[tuple[str, str, object]]] = {}
        for page in paginator.paginate(Bucket=store.bucket, Prefix=list_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(S3_SUPERSEDED_SUFFIX):
                    rel = key[len(list_prefix): -len(S3_SUPERSEDED_SUFFIX)] + ".yaml"
                    parsed = _parse_log_entry(rel)
                    if parsed is None:
                        continue
                    seed, info, run_ts = parsed
                    superseded.setdefault((seed, info), set()).add(run_ts)
                    continue
                if key.endswith("/"):
                    continue
                parsed = _parse_log_entry(key[len(list_prefix):])
                if parsed is None:
                    continue
                seed, info, run_ts = parsed
                candidates.setdefault((seed, info), []).append(
                    (run_ts, key, obj.get("ETag"))
                )

        # Must match ``load_marks`` selection.
        earliest: dict[tuple[int, str], tuple[str, str, object]] = {}
        for seed_info, rows in candidates.items():
            marker_stamps = superseded.get(seed_info, ())
            surviving = [row for row in rows if row[0] not in marker_stamps]
            if surviving:
                earliest[seed_info] = min(surviving, key=lambda row: row[0])

        for (seed, info), (_run_ts, key, etag) in earliest.items():
            local_rel = f"{prefix}{tag}_{info}/rep_{seed}.yaml"
            # Validate before filesystem changes.
            local_path = _resolve_download_path(resolved_dir, local_rel, key)
            etag_md5 = _etag_md5(etag)
            if (
                local_path.exists()
                and etag_md5 is not None
                # Cache check, not security; FIPS permits this flag.
                and etag_md5
                == hashlib.md5(local_path.read_bytes(), usedforsecurity=False).hexdigest()
            ):
                skipped += 1
                continue
            local_path.parent.mkdir(parents=True, exist_ok=True)
            body = client.get_object(Bucket=store.bucket, Key=key)["Body"].read()
            # Resume checks require existing files never be torn writes.
            tmp = local_path.with_name(local_path.name + ".tmp")
            tmp.write_bytes(body)
            os.replace(tmp, local_path)
            downloaded += 1

    logging.info(
        f"sync_down: {store.describe()} -> {results_dir}: "
        f"{downloaded} downloaded, {skipped} skipped (already present)."
    )
    return downloaded


def main(argv: "Sequence[str] | None" = None) -> int:
    """Run the S3-to-local sync CLI.

    Repeated ``--tag MODEL=TAG`` values split at the first ``"="``; later model entries replace
    earlier ones.

    Parameters
    ----------
    argv : Sequence[str] | None, optional
        Command-line arguments.

    Returns
    -------
    int
        Exit status.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m smolbench.evals.results_store",
        description=(
            "Sync one results directory down from its S3-backed experiment "
            "log (see resolve_store/sync_down). ReplicateHarness.sync_down() "
            "is the primary path for this; this CLI is for out-of-notebook "
            "use. Reads SMOLBENCH_RESULTS_S3 from the environment; the "
            f"project's own bucket is {default_results_uri()!r}."
        ),
    )
    parser.add_argument(
        "results_dir",
        type=Path,
        help="Repo-anchored results directory to sync down.",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        metavar="MODEL=TAG",
        help="A model=tag mapping entry (an archetype_tags item). Repeatable.",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Optional namespace prefix on result directory names, e.g. 'one_hop_'.",
    )
    args = parser.parse_args(argv)

    tags: dict[str, str] = {}
    for entry in args.tag:
        if "=" not in entry:
            parser.error(f"--tag must be MODEL=TAG, got {entry!r} (no '=')")
        model, _, tag = entry.partition("=")
        tags[model] = tag

    store = resolve_store(args.results_dir, args.prefix)
    n = sync_down(args.results_dir, tags, args.prefix)
    print(f"{args.results_dir}: {n} downloaded from {store.describe()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
