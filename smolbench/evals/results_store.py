"""
Store replicate results in S3, with local files as the offline/test fallback.

``ReplicateHarness`` writes every replicate YAML through a
:class:`ResultsStore`, so results survive an ephemeral spot instance; a
:class:`ReplicateAddress` carries `tag` (local key) and `model` (S3 key).

Env contract: ``SMOLBENCH_RESULTS_S3=s3://<bucket>[/<base-prefix>]`` selects the
S3 store, unset/empty/whitespace-only the local store rooted at ``results_dir``;
region is ``SMOLBENCH_RESULTS_S3_REGION``, else ``AWS_REGION``, else ``None``.
:func:`resolve_store` reads both at CALL time, never as module constants (a
notebook runs ``load_dotenv(keys.env)`` AFTER ``import smolbench``), and falls
back to local whenever ``results_dir`` is not under ``repo_root()``, which keeps
the offline suite's ``tmp_path`` runs hermetic.

Earliest-wins: S3 is an append-only LOG keyed
``<base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml`` with a
FIXED-WIDTH UTC ``run_ts``. A dump always creates a NEW object; every read takes
the EARLIEST run per (model, seed, info) -- the lexicographic MINIMUM key -- so
scores stay pass@1 and voiding a run takes an explicit exclusion. The LOCAL
layout keeps one file per (tag, info, seed), overwritten in place with no
history (committed results trees must stay byte-identical), and is what
analysis code reads; :func:`sync_down` bridges log -> local, one-way and
overwriting, so regrade only AFTER syncing down and unsetting the env var.
"""

import abc
import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence

import smolbench
from smolbench.evals import Marks
from smolbench.evals import _aws


def repo_root() -> Path:
    """Return the git checkout root: absolute, symlink-free, never cwd-relative.

    The one blessed path anchor for this repo -- a notebook kernel and the
    power-analysis scripts read the same ``results/`` tree from different cwds.
    """
    # smolbench.__file__ is <repo_root>/smolbench/__init__.py.
    return Path(smolbench.__file__).resolve().parents[1]


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parse an ``s3://bucket[/base-prefix]`` URI into ``(bucket, base_prefix)``.

    Shared deliberately: anything else mapping this URI to a bucket/prefix
    (e.g. a bucket seeder) must use THIS parser, or writer and reader drift and
    orphan history under a prefix neither finds.

    Parameters
    ----------
    uri : str
        NOT stripped here; ``resolve_store`` strips its env value first, so
        whitespace AROUND the URI stays distinct from whitespace INSIDE it.

    Returns
    -------
    tuple[str, str]
        ``base_prefix`` is ``""`` for a bucket-only URI, and never carries a
        leading or trailing ``"/"``.

    Raises
    ------
    ValueError
        Missing ``"s3://"`` scheme, or an empty or whitespace-bearing
        ``"/"``-delimited segment -- a name S3 never accepts, which would give
        a store that can never find what it writes.
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


def utcnow() -> datetime:
    """Return the current instant as a timezone-aware UTC ``datetime``.

    The ONE seam for "now", so a single monkeypatch pins every ``run_ts`` a test
    observes; ``ReplicateHarness.run_replicates`` calls it once per seed, so a
    seed's pooled ``evaluate()`` shares one timestamp. tz-aware because
    :func:`format_run_ts` appends a literal ``"Z"``.
    """
    return datetime.now(timezone.utc)


def format_run_ts(when: datetime) -> str:
    """Format `when` as the fixed-width UTC timestamp used in S3 log keys.

    Parameters
    ----------
    when : datetime
        Must ALREADY be UTC (normally :func:`utcnow`): ``tzinfo`` is not
        converted or inspected and the ``"Z"`` is a literal, so a naive or
        non-UTC datetime is silently mislabeled.

    Returns
    -------
    str
        Exactly 16 characters (``"20260810T193000Z"``); the fixed width makes
        lexicographic order equal chronological order for earliest-wins reads
        (``%z`` would vary off UTC).
    """
    return when.strftime("%Y%m%dT%H%M%SZ")


def experiment_name(results_dir: Path, prefix: str = "") -> str:
    """Derive the ``<experiment>`` segment of an S3 log key from a results dir.

    Parameters
    ----------
    results_dir : Path
        Must resolve under ``repo_root()``; :func:`resolve_store`, the only
        production caller, has already confirmed that.

    Returns
    -------
    str
        POSIX-separated, no leading/trailing ``"/"``. Repo-relative
        ``notebooks/<nb>/results`` gives ``<nb>``; any other shape falls back
        to its full repo-relative POSIX path (stable and collision-free for an
        unconventional tree), except ``repo_root()`` itself, which gives ``""``,
        never ``"."``. A non-empty `prefix` (e.g. ``"one_hop_"``) folds in as a
        sub-level with exactly one trailing ``"_"`` stripped:
        ``"chromatic/one_hop"``.

    Raises
    ------
    ValueError
        From ``Path.relative_to``, when `results_dir` is outside ``repo_root()``.
    """
    rel = results_dir.resolve().relative_to(repo_root())
    parts = rel.parts
    if len(parts) == 3 and parts[0] == "notebooks" and parts[2] == "results":
        base = parts[1]
    else:
        # repo_root() itself is Path("."): "" rather than the literal ".".
        base = "" if rel == Path(".") else rel.as_posix()
    if not prefix:
        return base
    # Exactly one "_": the prefix convention is always "<name>_".
    sub = prefix[:-1] if prefix.endswith("_") else prefix
    return f"{base}/{sub}" if base else sub


@dataclass(frozen=True)
class ReplicateAddress:
    """Identify one (archetype, info type, seed) replicate result.

    Threaded through every :class:`ResultsStore` method in place of a raw key,
    so each backend renders its own layout from the SAME address:
    :class:`LocalResultsStore` keys on `tag`, :class:`S3ResultsStore` on `model`.
    """

    #: Archetype tag (e.g. ``"decode"``, ``"cot"``): the LOCAL directory key
    #: (``{prefix}{tag}_{info}``); ignored by ``S3ResultsStore`` (see `model`).
    tag: str
    #: Info type (e.g. ``"intens"``, ``"extens"``, ``"noise_intens"``); both backends.
    info: str
    #: Replicate seed; both backends.
    seed: int
    #: Model id: the S3 LOG key (``<model>/seed=<seed>/<info>--<run_ts>.yaml``);
    #: ignored by ``LocalResultsStore``. THE ONE ASYMMETRY in the address
    #: scheme: local keys on `tag`, the log on `model`. Callers normally go
    #: model -> tag via ``archetype_tags``; ``ReplicateHarness.cot_chain_lengths``
    #: is keyed on `tag` ALONE, reverse-looks-up the FIRST model carrying it
    #: (see that method's docstring) and passes ``None`` when none does.
    #:
    #: ``model=None`` is a READ-only shape: ``LocalResultsStore`` never inspects
    #: `model`; ``S3ResultsStore.exists``/``list_seeds`` return ``False``/``[]``;
    #: ``dump_marks`` REFUSES it rather than write a literal ``"None"`` segment
    #: into a log that cannot be corrected once written.
    model: Optional[str] = None


class ResultsStore(abc.ABC):
    """Backend-agnostic interface over one experiment's results.

    A store is rooted at a fixed location -- a local directory, or an S3
    bucket/prefix -- and addresses each result by :class:`ReplicateAddress`.
    """

    @abc.abstractmethod
    def exists(self, addr: ReplicateAddress) -> bool:
        """Return whether a replicate result is already stored at `addr`.

        The resume-skip check ``ReplicateHarness`` makes before re-evaluating a
        (tag, info, seed), so a resumed run never re-bills landed work; on S3
        ANY logged run counts. Backend errors other than "not found" propagate
        rather than read as ``False``: a credentials failure is not "not run yet".
        """

    @abc.abstractmethod
    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        """Persist `marks` for `addr`, stamped with `run_ts`.

        No existence check; a caller wanting resume-skip calls :meth:`exists`
        first (as ``ReplicateHarness`` does).

        Parameters
        ----------
        run_ts : datetime
            Collection instant; ``ReplicateHarness.run_replicates`` captures
            :func:`utcnow` ONCE per seed so a pooled ``evaluate()`` is one run.
        """

    @abc.abstractmethod
    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """Deserialize the replicate result stored/logged at `addr`.

        Returns
        -------
        Marks
            The single local file, or on S3 the EARLIEST logged run.

        Raises
        ------
        FileNotFoundError
            Nothing is stored/logged for `addr` (S3 names the missing prefix).
        """

    @abc.abstractmethod
    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """List every seed with at least one stored/logged replicate.

        Parameters
        ----------
        model : str or None
            The S3 key dimension; ``None`` yields ``[]`` (see
            ``ReplicateAddress.model``).
        tag : str
            The local key dimension.

        Returns
        -------
        list[int]
            SORTED and DISTINCT (a seed re-collected many times counts once);
            empty when nothing is stored yet, which is not an error.
        """

    @abc.abstractmethod
    def describe(self) -> str:
        """Return this store's location: a path, or an ``s3://bucket/prefix``.

        For logging/CLI output only; never parsed back into a store.
        """


@dataclass(frozen=True)
class LocalResultsStore(ResultsStore):
    """Store to the on-disk replicate tree: ``{prefix}{tag}_{info}/rep_{seed}.yaml``.

    IGNORES `addr.model` and :meth:`dump_marks`'s `run_ts` entirely: one file
    per (tag, info, seed), overwritten in place. Append-only/earliest-wins are
    S3-LOG properties only -- a local rerun REPLACES its predecessor, an S3
    rerun stays INVISIBLE behind it.
    """

    #: Directory holding the per-condition replicate dirs -- an experiment's
    #: ``results_dir``.
    root: Path
    #: Optional namespace prefix on directory names (e.g. ``"one_hop_"``),
    #: forwarded verbatim from ``ReplicateHarness.prefix``.
    prefix: str = ""

    def _dirname(self, tag: str, info: str) -> str:
        """Return ``f"{self.prefix}{tag}_{info}"``, the per-condition dir name."""
        return f"{self.prefix}{tag}_{info}"

    def _path(self, addr: ReplicateAddress) -> Path:
        """Return ``root/{prefix}{tag}_{info}/rep_{seed}.yaml``; `addr.model` is unused."""
        return self.root / self._dirname(addr.tag, addr.info) / f"rep_{addr.seed}.yaml"

    def exists(self, addr: ReplicateAddress) -> bool:
        """See ``ResultsStore.exists``. Backed by ``Path.exists``."""
        return self._path(addr).exists()

    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        """See ``ResultsStore.dump_marks``. Ignores `run_ts`; mkdirs its own
        parents, so one call is a complete unit of work on both backends.
        """
        path = self._path(addr)
        path.parent.mkdir(parents=True, exist_ok=True)
        marks.dump(path)

    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """See ``ResultsStore.load_marks``. Backed by ``Marks.load``."""
        return Marks.load(self._path(addr))

    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """See ``ResultsStore.list_seeds``. Ignores `model`; globs ``rep_*.yaml``.

        A name whose seed portion does not parse as an ``int`` is SKIPPED (not a
        replicate); a missing directory globs to nothing rather than raising.
        """
        dirpath = self.root / self._dirname(tag, info)
        seeds: set[int] = set()
        for path in dirpath.glob("rep_*.yaml"):
            seed_str = path.stem[len("rep_"):]  # "rep_1776" -> "1776"
            try:
                seeds.add(int(seed_str))
            except ValueError:
                continue  # malformed name -- not a replicate; see docstring
        return sorted(seeds)

    def describe(self) -> str:
        """See ``ResultsStore.describe``. Returns ``str(self.root)``."""
        return str(self.root)


def _parse_log_entry(rel: str) -> Optional[tuple[int, str, str]]:
    """Parse an S3 log key remainder into ``(seed, info, run_ts)``, or ``None``.

    Reverses the ``"seed=<seed>/<info>--<run_ts>.yaml"`` key shape; shared by
    :meth:`S3ResultsStore.list_seeds` and :func:`sync_down`.

    Parameters
    ----------
    rel : str
        Key with the leading ``"<log_prefix>/<model>/"`` stripped; UNTRUSTED
        (an S3 listing, not only this module's writers), so it touches no
        filesystem.

    Returns
    -------
    tuple[int, str, str] or None
        ``None`` unless `rel` is ``"seed=<int>/<info>--<run_ts>.yaml"`` (a
        negative seed parses); callers SKIP such keys as "not one of ours". The
        stem splits on the FIRST ``"--"``, unambiguous since no `info` has one.
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
    """Store to S3: an append-only replicate log under one key prefix.

    Keys are
    ``<base_prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml``.
    Every operation opens its own client via :meth:`_client`, never a cached one.
    """

    #: S3 bucket name.
    bucket: str
    #: Base prefix carried by the ``SMOLBENCH_RESULTS_S3`` URI; never has a
    #: leading or trailing ``"/"``. May be ``""`` (no base prefix).
    base_prefix: str
    #: This experiment's log path segment, e.g. ``"induction"`` or
    #: ``"induction/one_hop"`` -- see :func:`experiment_name`.
    experiment: str
    #: Region for the S3 client, or ``None`` to let boto3 resolve one from
    #: its own chain.
    region: Optional[str] = None

    @property
    def log_prefix(self) -> str:
        """Return this store's key root: ``base_prefix`` and ``experiment`` joined.

        Whichever are non-empty, single ``"/"``, no leading/trailing ``"/"``;
        ``""`` when both are empty.
        """
        return "/".join(p for p in (self.base_prefix, self.experiment) if p)

    def _seed_prefix(self, model: str, seed: int) -> str:
        """Return ``f"{log_prefix}/{model}/seed={seed}/"``."""
        return f"{self.log_prefix}/{model}/seed={seed}/"

    def _info_prefix(self, model: str, seed: int, info: str) -> str:
        """Return the prefix every logged run of this replicate shares."""
        return self._seed_prefix(model, seed) + f"{info}--"

    def _client(self):
        """Return a fresh boto3 S3 client for ``self.region`` (boto3 resolves ``None``).

        Never cached: ``_aws.fresh_client`` builds a new ``Session`` per call so
        rotated credentials apply immediately (a notebook kernel outlives an IdP
        session). Cost -- ~90 sessions for a 3-arm 30-replicate resume check --
        is seconds. boto3 is imported lazily there, so this module imports
        without it.
        """
        return _aws.fresh_client("s3", self.region)

    def exists(self, addr: ReplicateAddress) -> bool:
        """See ``ResultsStore.exists``. Backed by ``list_objects_v2(MaxKeys=1)``.

        ``list_objects_v2`` rather than ``head_object`` because it never raises
        for "not found" (200 with empty ``Contents``), so a credentials failure
        still propagates. ``addr.model is None`` -> ``False``.
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
        """See ``ResultsStore.dump_marks``. Backed by ``put_object`` into a key
        embedding `run_ts`; raises ``ValueError`` for ``model=None`` BEFORE the
        call, so a refused write leaves no object.
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

    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """See ``ResultsStore.load_marks``. Reads the EARLIEST logged run.

        An explicit running min over the listed keys, rather than breaking on
        S3's already-ordered listing, keeps the selection rule in the code;
        ``FileNotFoundError`` names the prefix when nothing is logged there.
        """
        prefix = self._info_prefix(addr.model, addr.seed, addr.info)
        client = self._client()
        paginator = client.get_paginator("list_objects_v2")
        earliest_key: Optional[str] = None
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if earliest_key is None or key < earliest_key:
                    earliest_key = key
        if earliest_key is None:
            raise FileNotFoundError(
                f"no logged run under s3://{self.bucket}/{prefix}"
            )
        obj = client.get_object(Bucket=self.bucket, Key=earliest_key)
        return Marks.loads(obj["Body"].read().decode())

    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """See ``ResultsStore.list_seeds``. Backed by a paginated ``list_objects_v2``.

        `tag` is UNUSED (an S3 key has no tag dimension) and accepted only so
        one call shape serves either backend; ``model=None`` returns ``[]``.
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
        """See ``ResultsStore.describe``. Returns ``f"s3://{bucket}/{log_prefix}"``."""
        return f"s3://{self.bucket}/{self.log_prefix}"


def resolve_store(results_dir: Path, prefix: str = "") -> ResultsStore:
    """Resolve which ``ResultsStore`` backend `results_dir` should use.

    Reads ``SMOLBENCH_RESULTS_S3``/``SMOLBENCH_RESULTS_S3_REGION`` at CALL
    time. The step ORDER is load-bearing:

    1. ``SMOLBENCH_RESULTS_S3`` unset/empty/whitespace-only -> local store.
    2. Otherwise parse the URI (:func:`parse_s3_uri`), raising ``ValueError``
       on anything malformed, BEFORE the anchor check -- anchor-first would let
       a typo'd URI degrade SILENTLY to a local write on an ephemeral box, a
       loss discovered only once that box is gone.
    3. `results_dir` not under ``repo_root()`` -> log at INFO, local store.
       This is the hermeticity property: ``tmp_path`` fixtures are outside the
       checkout, so the offline suite stays local even when a developer's shell
       exports the variable.
    4-6. Derive :func:`experiment_name`, resolve the region, and return the
       ``S3ResultsStore``.

    Parameters
    ----------
    results_dir : Path
        Need not exist -- resolved non-strictly, since an S3-first run may never
        create its local results directory.
    prefix : str, optional
        Becomes ``LocalResultsStore.prefix``, or folds into
        ``S3ResultsStore.experiment``.
    """
    uri = os.environ.get("SMOLBENCH_RESULTS_S3", "").strip()
    # Step 1.
    if not uri:
        return LocalResultsStore(results_dir, prefix)

    # Step 2: validate BEFORE the anchor check (docstring step 2 says why).
    bucket, base_prefix = parse_s3_uri(uri)

    # Step 3: hermeticity fallback.
    try:
        results_dir.resolve().relative_to(repo_root())
    except ValueError:
        logging.info(
            f"resolve_store: SMOLBENCH_RESULTS_S3 is set, but {results_dir} is "
            f"not under repo_root() ({repo_root()}); using the local store "
            "(this is the offline-test-suite hermeticity fallback)."
        )
        return LocalResultsStore(results_dir, prefix)

    # Step 4.
    experiment = experiment_name(results_dir, prefix)

    # Step 5: None lets boto3's own chain decide.
    region = (
        os.environ.get("SMOLBENCH_RESULTS_S3_REGION")
        or os.environ.get("AWS_REGION")
        or None
    )

    # Step 6.
    return S3ResultsStore(
        bucket=bucket, base_prefix=base_prefix, experiment=experiment, region=region
    )


def _etag_md5(etag) -> Optional[str]:
    """Extract a whole-object MD5 hex digest from an S3 ``ETag`` value.

    Returns the unquoted hex digest IFF `etag` (the raw, quote-wrapped
    ``list_objects_v2`` value) is a single-part upload's whole-object MD5;
    ``None`` for missing/falsy or MULTIPART (``<hex>-<partcount>``, never an MD5
    of the bytes), which a caller must treat as "assume different" (download).
    """
    if not etag:
        return None
    unquoted = etag.strip('"')
    if "-" in unquoted:
        return None
    return unquoted


def _resolve_download_path(resolved_dir: Path, rel: str, key: str) -> Path:
    """Join `rel` under the already-resolved `resolved_dir`, refusing traversal.

    `rel` is validated rather than trusted because its components trace back to
    an S3 KEY, and this module's writers are not the only thing that can put an
    object under a prefix. Raises ``ValueError`` naming `key` (what an operator
    must delete to stop the refusal recurring) when the destination equals
    `resolved_dir` or lies outside it -- before the caller mkdirs or writes, so
    a refused key leaves no trace.
    """
    candidate = (resolved_dir / rel).resolve()
    if candidate == resolved_dir or not candidate.is_relative_to(resolved_dir):
        raise ValueError(
            f"sync_down: refusing S3 key {key!r}: resolves to {candidate}, "
            f"outside results_dir {resolved_dir}"
        )
    return candidate


def sync_down(results_dir: Path, tags: Mapping[str, str], prefix: str = "") -> int:
    """Translate an S3-backed experiment's log into the local analysis layout.

    Analysis code (``notebooks/*/analysis/power_analysis.py``, figure scripts)
    reads the LOCAL tree and is deliberately not ported onto ``ResultsStore``;
    this is the bridge. Each (model, seed, info)'s EARLIEST logged run lands
    where ``LocalResultsStore`` would put it -- a TRANSLATION, since the local
    directory comes from `tags`, not the S3 key.

    ONE-WAY and DESTRUCTIVE: overwrites local files and never touches the log,
    so a local-only regrade is silently destroyed (earliest-wins means a
    re-append to S3 cannot protect one either).

    Parameters
    ----------
    tags : Mapping[str, str]
        ``{model: tag}`` (an experiment's ``archetype_tags``), the one thing
        the log cannot supply; ``ReplicateHarness.sync_down()`` holds it and is
        the PRIMARY caller.
    prefix : str, optional
        Forwarded to :func:`experiment_name`, and used in each local directory
        name ``f"{prefix}{tag}_{info}"``.

    Returns
    -------
    int
        Objects actually DOWNLOADED, excluding those skipped as identical.

    Raises
    ------
    RuntimeError
        `results_dir` resolved to a ``LocalResultsStore``: no log to sync.
    ValueError
        ``log_prefix`` is ``""`` (would mirror the ENTIRE bucket), or a
        destination resolves outside `results_dir`.

    Notes
    -----
    The per-(seed, info) minimum-`run_ts` selection MUST stay identical to
    ``S3ResultsStore.load_marks``'s, or a synced tree and a direct load fork the
    analysis. A local file is skipped only when it exists AND the listing
    ``ETag`` (no extra ``head_object``) decodes to a single-part MD5
    (:func:`_etag_md5`) equal to ``hashlib.md5`` of the local bytes; size-only
    would be UNSOUND (a regrade's ``1 -> 0`` flip preserves length).
    ``usedforsecurity=False`` keeps the hash legal under FIPS. ACCEPTED COST: a
    multipart ETag never matches, so such an object re-downloads every call.
    """
    store = resolve_store(results_dir, prefix)
    if not isinstance(store, S3ResultsStore):
        uri = os.environ.get("SMOLBENCH_RESULTS_S3", "").strip()
        if not uri:
            raise RuntimeError(
                "sync_down: SMOLBENCH_RESULTS_S3 is unset or empty -- there is "
                "no S3 log to sync down from."
            )
        raise RuntimeError(
            f"sync_down: {results_dir} is not under repo_root() "
            f"({repo_root()}), so resolve_store falls back to the local "
            "store for it (see resolve_store's hermeticity fallback) -- "
            "there is no S3 log to sync down from."
        )

    # An empty resolved log prefix means "list the whole bucket" to
    # list_objects_v2 -- refuse rather than mirror it into one results_dir.
    if store.log_prefix == "":
        raise ValueError(
            "sync_down: refusing to sync -- the resolved S3 log prefix is "
            f"empty, which would mirror the ENTIRE bucket s3://{store.bucket} "
            f"into {results_dir}. A results directory is expected to map to "
            "a non-empty experiment name (see experiment_name); this usually "
            "means results_dir == repo_root() with no base prefix in "
            "SMOLBENCH_RESULTS_S3 and no notebook-shaped results_dir."
        )

    resolved_dir = results_dir.resolve()
    client = store._client()
    paginator = client.get_paginator("list_objects_v2")
    downloaded = 0
    skipped = 0
    for model, tag in tags.items():
        list_prefix = f"{store.log_prefix}/{model}/"
        # Running min of (run_ts, key, etag) per (seed, info): no grouping
        # pass, and it must match load_marks's rule exactly (see Notes).
        earliest: dict[tuple[int, str], tuple[str, str, object]] = {}
        for page in paginator.paginate(Bucket=store.bucket, Prefix=list_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):
                    continue  # zero-byte directory placeholder, never written by this module
                parsed = _parse_log_entry(key[len(list_prefix):])
                if parsed is None:
                    continue  # stray key under this prefix; not one of ours
                seed, info, run_ts = parsed
                cur = earliest.get((seed, info))
                if cur is None or run_ts < cur[0]:
                    earliest[(seed, info)] = (run_ts, key, obj.get("ETag"))

        for (seed, info), (_run_ts, key, etag) in earliest.items():
            local_rel = f"{prefix}{tag}_{info}/rep_{seed}.yaml"
            # Validate BEFORE touching the filesystem: a refused key leaves no trace.
            local_path = _resolve_download_path(resolved_dir, local_rel, key)
            etag_md5 = _etag_md5(etag)
            if (
                local_path.exists()
                and etag_md5 is not None
                and etag_md5
                == hashlib.md5(local_path.read_bytes(), usedforsecurity=False).hexdigest()
            ):
                skipped += 1  # verified identical via ETag/MD5; see Notes
                continue
            local_path.parent.mkdir(parents=True, exist_ok=True)
            body = client.get_object(Bucket=store.bucket, Key=key)["Body"].read()
            local_path.write_bytes(body)
            downloaded += 1

    logging.info(
        f"sync_down: {store.describe()} -> {results_dir}: "
        f"{downloaded} downloaded, {skipped} skipped (already present)."
    )
    return downloaded


def main(argv: "Sequence[str] | None" = None) -> int:
    """Run the CLI entry point: sync one results directory down from its S3 log.

    ``ReplicateHarness.sync_down()`` is the PRIMARY path (it already holds
    ``archetype_tags``); this CLI re-types the mapping as repeated ``--tag
    MODEL=TAG`` flags, each split on the FIRST ``"="`` (later ``"="`` are
    literal; a repeated model silently OVERWRITES). Prints one summary line
    and returns ``0``.

    Raises
    ------
    SystemExit
        Code 2, via ``parser.error(...)``, on a malformed ``--tag`` (no ``"="``)
        or any other argparse-level problem.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m smolbench.evals.results_store",
        description=(
            "Sync one results directory down from its S3-backed experiment "
            "log (see resolve_store/sync_down). ReplicateHarness.sync_down() "
            "is the primary path for this; this CLI is for out-of-notebook "
            "use."
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
