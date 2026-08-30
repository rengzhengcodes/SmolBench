"""
Store replicate results in S3, with local files as the offline/test fallback.

``ReplicateHarness`` writes every replicate YAML through a
:class:`ResultsStore`, so results survive an ephemeral spot instance with no
second harness code path; a :class:`ReplicateAddress` names a replicate by both
`tag` (the local layout's key) and `model` (the S3 log's key).

Env contract: ``SMOLBENCH_RESULTS_S3=s3://<bucket>[/<base-prefix>]`` selects the
S3 store, unset/empty/whitespace-only the local store rooted at ``results_dir``;
region is ``SMOLBENCH_RESULTS_S3_REGION``, else ``AWS_REGION``, else ``None``
(boto3 resolves its own). Both are read inside :func:`resolve_store` at CALL
time, never as module constants: a notebook runs ``load_dotenv(keys.env)`` after
``import smolbench``, so a frozen constant would pin every later replicate to
the ephemeral box's local disk. :func:`resolve_store` also falls back to local
whenever ``results_dir`` is not under ``repo_root()``, keeping the offline
suite's ``tmp_path`` runs hermetic without unsetting anything.

S3 holds an append-only experiment LOG, keyed
``<base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml`` with a
FIXED-WIDTH UTC ``run_ts``, so every "earliest run" lookup here is a plain
lexicographic MINIMUM over listed keys. A dump always creates a NEW object and
every read resolves the EARLIEST run per (model, seed, info), keeping reported
scores pass@1: a re-collection can NEVER supersede logged data, and voiding it
requires an explicit exclusion visible to readers. The LOCAL layout instead
keeps one file per (tag, info, seed), overwritten in place with no history
(committed results trees must stay byte-identical), and analysis code reads
that tree; since an S3-active run writes no local copy,
:func:`sync_down` bridges the two, one-way and overwriting. It silently
destroys a local-only regrade, so the safe operator sequence is sync down,
unset ``SMOLBENCH_RESULTS_S3``, regrade locally.
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
    power-analysis scripts read the same ``results/`` tree from different
    working directories.
    """
    # smolbench.__file__ -> <repo_root>/smolbench/__init__.py; two parents
    # up strips both the file and the package directory.
    return Path(smolbench.__file__).resolve().parents[1]


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parse an ``s3://bucket[/base-prefix]`` URI into ``(bucket, base_prefix)``.

    Public and shared deliberately: any other package mapping the same URI to a
    bucket/prefix (e.g. a bucket-seeding script) must use THIS parser, or a
    seeder and a reader drift and orphan history under a prefix neither can find
    again. `uri` is not stripped here -- ``resolve_store`` strips its env-var
    value first, keeping "stray whitespace around the URI" distinguishable from
    "whitespace inside it". ``base_prefix`` is ``""`` when the URI names only a
    bucket and never carries a leading or trailing ``"/"``, so
    ``"s3://b/archive/"`` and ``"s3://b/archive"`` agree. Raises ``ValueError``
    -- naming the URI and the rule broken -- on a missing ``"s3://"`` scheme, an
    empty ``"/"``-delimited segment (missing bucket, or a doubled slash), or
    whitespace in a segment, which would yield a bucket name S3 never accepts
    and silently produce a store that can never find what it writes.
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
    observes; ``ReplicateHarness.run_replicates`` calls it once per seed so
    every info type in that seed's pooled ``evaluate()`` shares a timestamp.
    Always tz-aware, because :func:`format_run_ts` appends a literal ``"Z"``.
    """
    return datetime.now(timezone.utc)


def format_run_ts(when: datetime) -> str:
    """Format `when` as the fixed-width UTC timestamp used in S3 log keys.

    `when` must already be UTC (normally from :func:`utcnow`): ``tzinfo`` is
    neither converted nor inspected and the trailing ``"Z"`` is a literal, so a
    naive or non-UTC datetime is silently mislabeled. The result is always
    exactly 16 characters (``"20260810T193000Z"``), and that fixed width is
    load-bearing -- it makes lexicographic order agree with chronological order,
    which is how every earliest-run read here (:meth:`S3ResultsStore.load_marks`,
    :func:`sync_down`) works without parsing a timestamp out of a key (``%z``
    would render 5 characters and vary off UTC).
    """
    return when.strftime("%Y%m%dT%H%M%SZ")


def experiment_name(results_dir: Path, prefix: str = "") -> str:
    """Derive the ``<experiment>`` segment of an S3 log key from a results dir.

    `results_dir` must resolve under ``repo_root()``; :func:`resolve_store`, the
    only production caller, has already confirmed that. `prefix` is the harness
    namespace prefix, e.g. ``"one_hop_"``. Raises ``ValueError`` (from
    ``Path.relative_to``) if `results_dir` is not under ``repo_root()``.

    Returns
    -------
    str
        POSIX-separated, no leading/trailing ``"/"``. A repo-relative
        `results_dir` of exactly three components ``notebooks/<nb>/results``
        gives ``<nb>``; anything else falls back to its full repo-relative POSIX
        path -- a DOCUMENTED fallback, not an error, so an unconventional tree
        still gets a stable, collision-free name. A non-empty `prefix` folds in
        as a sub-level with exactly one trailing ``"_"`` stripped, so notebook
        ``"chromatic"`` with ``prefix="one_hop_"`` yields ``"chromatic/one_hop"``.

    Notes
    -----
    ``results_dir == repo_root()`` is repo-relative ``Path(".")``, whose
    ``as_posix()`` is the literal ``"."``; that one case is special-cased to
    ``""`` instead, with a non-empty `prefix` folded in without a leading
    ``"/"``.
    """
    rel = results_dir.resolve().relative_to(repo_root())
    parts = rel.parts
    if len(parts) == 3 and parts[0] == "notebooks" and parts[2] == "results":
        base = parts[1]
    else:
        # Documented fallback -- see the "Returns" section above. Path(".")
        # (results_dir == repo_root() itself) is special-cased to "" rather
        # than the literal string "." (see Notes).
        base = "" if rel == Path(".") else rel.as_posix()
    if not prefix:
        return base
    # Strip exactly one trailing "_" -- this repo's prefix convention is
    # always "<name>_" (a single trailing underscore, e.g. "one_hop_"), so
    # stripping more would over-reach for no prefix this codebase actually
    # uses.
    sub = prefix[:-1] if prefix.endswith("_") else prefix
    return f"{base}/{sub}" if base else sub


@dataclass(frozen=True)
class ReplicateAddress:
    """Identify one (archetype, info type, seed) replicate result.

    Threaded through every :class:`ResultsStore` method in place of a raw key,
    so each backend renders its own layout from the SAME address:
    :class:`LocalResultsStore` keys on `tag`, :class:`S3ResultsStore` on `model`.
    """

    #: Archetype tag (e.g. ``"decode"``, ``"cot"``) -- drives the LOCAL
    #: layout's directory name (``{prefix}{tag}_{info}``). Ignored
    #: entirely by ``S3ResultsStore`` (see `model`).
    tag: str
    #: Info type (e.g. ``"intens"``, ``"extens"``, ``"noise_intens"``).
    #: Used by BOTH backends.
    info: str
    #: Replicate seed. Used by BOTH backends.
    seed: int
    #: Model id -- drives the S3 LOG layout's key
    #: (``<model>/seed=<seed>/<info>--<run_ts>.yaml``). Ignored entirely
    #: by ``LocalResultsStore`` (see `tag`).
    #:
    #: THIS IS THE ONE ASYMMETRY IN THE ADDRESS SCHEME: the local layout
    #: is keyed by `tag`, but the S3 log is keyed by `model`. Most
    #: callers (``run_replicates``, ``has_outstanding``, ``summarize``)
    #: know a real model id, because they reach a ``ReplicateAddress`` by
    #: working through ``archetype_tags`` forward (model -> tag).
    #: ``ReplicateHarness.cot_chain_lengths(tag="cot")``, though, is
    #: keyed on `tag` ALONE -- an existing test calls it with no model in
    #: scope at all. So the harness reverse-looks-up `tag` -> `model`
    #: through ``archetype_tags`` (first match; see that method's
    #: docstring for why first-match is correct there), and passes
    #: ``None`` when NO configured model carries that tag.
    #:
    #: A ``None`` model is NOT an error ON READ. ``LocalResultsStore``
    #: never inspects `model` at all, so it is unaffected.
    #: ``S3ResultsStore.exists``/``list_seeds`` both explicitly
    #: special-case ``None`` to mean "nothing logged" (``False``/``[]``),
    #: rather than raising or building a key with a literal ``"None"``
    #: path segment. ON WRITE, though, ``None`` IS refused:
    #: ``S3ResultsStore.dump_marks`` raises ``ValueError`` rather than
    #: write into the append-only log under a literal ``"None"`` model
    #: directory, since that log has no overwrite/correction mechanism
    #: for a bad object once written -- see that method's docstring.
    #: ``model=None`` is therefore a READ-only shape in practice:
    #: legitimate for the tag-keyed lookups that produce it
    #: (``ReplicateHarness.cot_chain_lengths`` when no configured model
    #: carries the requested tag), never for a write.
    model: Optional[str] = None


class ResultsStore(abc.ABC):
    """Backend-agnostic interface over one experiment's results.

    A store is rooted at a fixed location -- a local directory, or an S3
    bucket/prefix -- and addresses each result by :class:`ReplicateAddress`.
    """

    @abc.abstractmethod
    def exists(self, addr: ReplicateAddress) -> bool:
        """Return whether a replicate result is already stored at `addr`.

        The resume-skip check ``ReplicateHarness`` consults before re-evaluating
        a (tag, info, seed), so a resumed run never re-runs (and re-bills) work
        that already landed; on S3, ANY logged run counts as done. Any backend
        error other than "not found" propagates rather than being reported as
        ``False``: a credentials/permissions failure must never be read as "this
        replicate has not been run yet".
        """

    @abc.abstractmethod
    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        """Persist `marks` for `addr`, stamped with `run_ts`.

        Performs no existence check; a caller wanting resume-skip calls
        :meth:`exists` first (as ``ReplicateHarness`` does). `run_ts` is the
        collection instant, normally :func:`utcnow` captured ONCE per seed by
        ``ReplicateHarness.run_replicates`` so every info type from that seed's
        single pooled ``evaluate()`` shares one timestamp (per-info stamps would
        scatter one evaluation event across several apparent runs).
        ``S3ResultsStore`` embeds it in the new object's key -- that IS the
        append-only mechanism; ``LocalResultsStore`` ignores it and overwrites
        one file per (tag, info, seed) in place.
        """

    @abc.abstractmethod
    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """Deserialize the replicate result stored/logged at `addr`.

        Returns the single local file, or on S3 the EARLIEST logged run -- never
        a later re-collection of the same replicate. Raises
        ``FileNotFoundError`` when nothing is stored/logged for `addr` on either
        backend (S3 raises it explicitly, naming the missing key prefix).
        """

    @abc.abstractmethod
    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """List every seed with at least one stored/logged replicate.

        `model` is the S3 backend's key dimension, `tag` the local backend's;
        ``model=None`` ("no model known for this query", see
        ``ReplicateAddress.model``) yields ``[]``, not an error. Seeds come back
        SORTED and DISTINCT -- a seed re-collected many times still counts once
        -- and empty when nothing is stored yet, which is not an error.
        """

    @abc.abstractmethod
    def describe(self) -> str:
        """Return this store's location (a path, or an ``s3://bucket/prefix``);
        for logging/CLI output only, never parsed back into a store.
        """


@dataclass(frozen=True)
class LocalResultsStore(ResultsStore):
    """Store to the on-disk replicate tree: ``{prefix}{tag}_{info}/rep_{seed}.yaml``.

    IGNORES `addr.model` and :meth:`dump_marks`'s `run_ts` entirely: one file
    per (tag, info, seed), overwritten in place. Append-only/earliest-wins are
    S3-LOG properties only, hence the asymmetry -- a local rerun REPLACES its
    predecessor, while an S3 rerun stays INVISIBLE behind it.
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
        """See ``ResultsStore.dump_marks``. Ignores `run_ts`; creates parent
        dirs itself, so one call is a complete unit of work on both backends.
        """
        path = self._path(addr)
        path.parent.mkdir(parents=True, exist_ok=True)
        marks.dump(path)

    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """See ``ResultsStore.load_marks``. Backed by ``Marks.load``."""
        return Marks.load(self._path(addr))

    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """See ``ResultsStore.list_seeds``. Ignores `model`; globs ``rep_*.yaml``.

        A name whose seed portion does not parse as an ``int`` is SKIPPED (a
        hand-edited or partially written name is not a replicate), and a missing
        directory globs to nothing rather than raising.
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
    :meth:`S3ResultsStore.list_seeds` and :func:`sync_down`. `rel` is a key with
    the leading ``"<log_prefix>/<model>/"`` already stripped, and is UNTRUSTED
    -- it comes from an S3 listing, not only from this module's writers -- so
    this touches no filesystem. Returns ``None`` when `rel` is not exactly two
    ``"/"`` components, the first does not start with ``"seed="`` followed by an
    ``int`` (a negative seed parses; the log format does not forbid one), or the
    second does not end in ``".yaml"`` with a ``"--"`` in its stem. The stem
    splits on the FIRST ``"--"``, unambiguous since no `info` value contains one.
    Callers SKIP a ``None``: a stray or pre-scheme key is "not one of ours".
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
        """Return ``base_prefix`` and ``experiment`` joined -- this store's key root.

        Whichever of the two are non-empty, joined by a single ``"/"``, no
        leading/trailing ``"/"``, ``""`` when both are empty.
        """
        return "/".join(p for p in (self.base_prefix, self.experiment) if p)

    def _seed_prefix(self, model: str, seed: int) -> str:
        """Return ``f"{log_prefix}/{model}/seed={seed}/"``."""
        return f"{self.log_prefix}/{model}/seed={seed}/"

    def _info_prefix(self, model: str, seed: int, info: str) -> str:
        """Return `_seed_prefix` plus ``f"{info}--"``: the prefix every logged run
        of this replicate shares, differing only in the ``run_ts``/``.yaml``.
        """
        return self._seed_prefix(model, seed) + f"{info}--"

    def _client(self):
        """Return a fresh boto3 S3 client for ``self.region`` (boto3 resolves ``None``).

        Never cached on ``self``: ``_aws.fresh_client`` builds a new ``Session``
        per call so rotated credentials are picked up immediately, and a store
        instance typically outlives an IdP session's credentials (a notebook
        kernel runs many hours). The cost -- one ``Session`` per listing, ~90
        for a 3-arm 30-replicate resume check -- is seconds against a
        ``serve_model`` step pulling hundreds of GB. boto3 is imported lazily
        there, so importing this module does not require it.
        """
        return _aws.fresh_client("s3", self.region)

    def exists(self, addr: ReplicateAddress) -> bool:
        """See ``ResultsStore.exists``. Backed by ``list_objects_v2(MaxKeys=1)``.

        ``False`` immediately when `addr.model` is ``None`` -- the tag-only-read
        case (see ``ReplicateAddress.model``), not an error; otherwise ``True``
        iff the listing under `addr`'s (model, seed, info) prefix returns a key.
        Unlike ``head_object``, ``list_objects_v2`` never raises for "not found"
        (200 with empty ``Contents``), so this needs no exception handling and a
        credentials or permissions failure propagates instead of being read as
        "not run yet", which would re-run and re-bill existing work.
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
        """See ``ResultsStore.dump_marks``. Backed by ``put_object``.

        Always creates a NEW object: the key embeds `run_ts`
        (:func:`format_run_ts`), so two calls for the same `addr` at different
        timestamps write two different keys. No existence check or delete, by
        design -- this is the append-only mechanism. Raises ``ValueError`` when
        `addr.model` is ``None``, BEFORE ``put_object`` so a refused write
        leaves no object: ``model=None`` is a READ-only shape
        (:meth:`exists`/:meth:`list_seeds` answer ``False``/``[]``), and without
        this guard f-string interpolation would write a literal ``"None"`` path
        segment into the append-only log, where only a manual delete removes it.
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

        Returns the run at the LEXICOGRAPHICALLY MINIMUM key under `addr`'s
        (model, seed, info) prefix, which `run_ts`'s fixed width makes the
        chronologically first; every later run is ignored (see the module
        docstring's supersede-requires-explicit-exclusion corollary). The loop
        keeps an explicit running min rather than breaking on S3's already-
        ordered listing, so the selection rule lives in the code. Raises
        ``FileNotFoundError`` naming the prefix when nothing is logged there.
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

        ``model=None`` returns ``[]`` immediately (the tag-only-read case);
        `tag` is UNUSED, since an S3 key has no tag dimension, and is accepted
        only so a caller can use one call shape for either backend. Returns
        sorted, DISTINCT seeds parsed (:func:`_parse_log_entry`) from keys under
        ``f"{log_prefix}/{model}/"`` whose `info` matches -- distinct seeds, not
        log objects, matching ``ReplicateHarness.summarize``'s replicate count.
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

    Reads ``SMOLBENCH_RESULTS_S3``/``SMOLBENCH_RESULTS_S3_REGION`` at CALL time
    and applies these steps, whose ORDER is load-bearing:

    1. ``SMOLBENCH_RESULTS_S3`` unset/empty/whitespace-only -> local store.
    2. Otherwise parse the URI, raising ``ValueError`` on anything malformed
       (:func:`parse_s3_uri`), BEFORE the anchor check -- checking the anchor
       first would let a typo'd URI fall back SILENTLY to a local write for any
       non-repo-anchored dir, a run that believes it wrote to S3 but landed on
       an ephemeral box's disk, found out only once that box is gone.
    3. `results_dir` not resolving under ``repo_root()`` -> log at INFO, return
       a local store. This is the hermeticity property: ``tmp_path`` fixtures
       are outside the checkout, so the offline suite stays local even when a
       developer's shell exports the variable.
    4-6. Derive :func:`experiment_name`, resolve the region
       (``SMOLBENCH_RESULTS_S3_REGION``, else ``AWS_REGION``, else ``None``),
       and return the ``S3ResultsStore``.

    `results_dir` need not exist -- it is resolved non-strictly, since an
    S3-first run's local results directory may never be created. `prefix`
    becomes ``LocalResultsStore.prefix``, or folds into
    ``S3ResultsStore.experiment`` via :func:`experiment_name`.
    """
    uri = os.environ.get("SMOLBENCH_RESULTS_S3", "").strip()
    # Step 1: unset/empty/whitespace-only -> local, unconditionally.
    if not uri:
        return LocalResultsStore(results_dir, prefix)

    # Step 2: parse + validate BEFORE the repo-anchor check (see the
    # docstring above for why this ordering is the safe direction).
    # parse_s3_uri is the single shared parser -- see the module docstring's
    # "URI parsing: one parser, shared" section.
    bucket, base_prefix = parse_s3_uri(uri)

    # Step 3: repo-anchor check / hermeticity fallback.
    try:
        results_dir.resolve().relative_to(repo_root())
    except ValueError:
        logging.info(
            f"resolve_store: SMOLBENCH_RESULTS_S3 is set, but {results_dir} is "
            f"not under repo_root() ({repo_root()}); using the local store "
            "(this is the offline-test-suite hermeticity fallback)."
        )
        return LocalResultsStore(results_dir, prefix)

    # Step 4: this experiment's log path segment (see module docstring's
    # "S3 key layout" section for a worked example).
    experiment = experiment_name(results_dir, prefix)

    # Step 5: region -- SMOLBENCH_RESULTS_S3_REGION, else AWS_REGION, else
    # None (let boto3's own resolution chain decide).
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

    `etag` is the raw, quote-wrapped ``obj.get("ETag")`` from a
    ``list_objects_v2`` entry. Returns the unquoted hex digest IFF it is a
    single-part upload's whole-object MD5, else ``None`` -- `etag` missing/falsy
    or MULTIPART (``<hex>-<partcount>``, never a valid MD5 of the bytes).
    ``None`` means "cannot verify identity from the ETag alone", which a caller
    must treat as "assume different" (download), never "assume same" (skip).
    """
    if not etag:
        return None
    unquoted = etag.strip('"')
    if "-" in unquoted:
        return None  # multipart ETag: "<hex>-<partcount>", not a whole-object MD5
    return unquoted


def _resolve_download_path(resolved_dir: Path, rel: str, key: str) -> Path:
    """Join `rel` under the already-resolved `resolved_dir`, refusing traversal.

    `resolved_dir` is ``results_dir.resolve()``, and every download must land
    strictly inside it. `rel` is validated rather than trusted because its
    components trace back to an S3 KEY -- this module's writers are not the only
    thing that can place an object under a prefix. Raises ``ValueError``, naming
    `key` (what an operator must find and delete to stop the refusal recurring),
    when the destination equals `resolved_dir` (only files are placed here) or
    lies outside it (a ``".."`` path); raised BEFORE the caller mkdirs or
    writes, so a refused key leaves no trace on disk.
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

    Analysis code (``notebooks/*/analysis/power_analysis.py``, the figure
    scripts) reads a LOCAL tree and is deliberately not ported onto
    ``ResultsStore``; this is the bridge. For each (model, seed, info) it
    downloads the EARLIEST logged run to the path ``LocalResultsStore`` would
    use -- a TRANSLATION, not a mirror, since the local directory comes from
    `tags` (``{model: tag}``, an experiment's ``archetype_tags``, the one thing
    the log cannot supply itself) and not from the S3 key, which names only a
    model. ``ReplicateHarness.sync_down()`` already holds that mapping and is
    the PRIMARY caller; :func:`main` exists for callers that must re-type it.
    `prefix` is forwarded to :func:`experiment_name` and used in each local
    directory name ``f"{prefix}{tag}_{info}"``. Returns the number of objects
    actually DOWNLOADED, excluding those skipped as already-identical.

    ONE-WAY and DESTRUCTIVE -- S3 -> local only, overwriting local files, never
    touching the log. It silently destroys a local-only edit (e.g. a
    ``scripts/results/regrade.py --write`` regrade), and under earliest-wins a
    re-append to S3 cannot protect one either; see the module docstring for the
    safe regrade sequence.

    Raises ``RuntimeError`` when `results_dir` resolved to a
    ``LocalResultsStore`` (``SMOLBENCH_RESULTS_S3`` unset/empty, or
    `results_dir` not under ``repo_root()``; the message says which), and
    ``ValueError`` when the resolved ``log_prefix`` is ``""`` -- syncing would
    mirror the ENTIRE bucket into `results_dir` -- or an entry's destination
    resolves outside `results_dir` (:func:`_resolve_download_path`).

    Notes
    -----
    Per model, keys under ``f"{log_prefix}/{model}/"`` are parsed by
    :func:`_parse_log_entry` and reduced to the LEXICOGRAPHICALLY MINIMUM
    `run_ts` per (seed, info) -- exactly ``S3ResultsStore.load_marks``'s rule,
    which the two MUST agree on or a synced tree and a direct load silently fork
    the analysis; keys not matching the shape are skipped. A local file is
    skipped only if it exists AND the listing entry's ``ETag`` (no extra
    ``head_object``) decodes to a single-part MD5 (:func:`_etag_md5`) AND that
    digest equals ``hashlib.md5`` of the local bytes; anything else
    re-downloads. Size-only would be UNSOUND, because a regrade's ``1 -> 0``
    score flip is byte-length-preserving and a stale verdict would survive the
    sync. ``usedforsecurity=False`` marks the hash as an integrity check, so it
    still runs on a FIPS-configured Python. ACCEPTED COST: a multipart-uploaded
    object's ``<hex>-<partcount>`` ETag can never match a plain MD5, so it
    re-downloads on every call, indefinitely.
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

    # Integrity guard: an empty resolved log prefix means "list the whole
    # bucket" to list_objects_v2. Refuse outright rather than silently
    # mirroring every object anything ever put in this bucket into one
    # results_dir.
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
        # Per (seed, info): (run_ts, key, etag) of the EARLIEST run seen
        # so far. This selection rule must match load_marks exactly --
        # a sync_down that resolved a different run than a direct load
        # would silently fork the analysis. A
        # dict keyed on (seed, info) is the natural shape for "keep
        # only the winner of a running min over run_ts": no separate
        # grouping/sorting pass is needed, since the running-min update
        # is O(1) per listed key.
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
            # Validate BEFORE touching the filesystem, so a refused entry
            # leaves no trace (no mkdir, no partial write, not even a stat
            # against a bogus path).
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

    ::

        python -m smolbench.evals.results_store <results_dir> \\
            --tag model=tag [--tag model=tag ...] [--prefix one_hop_]

    ``ReplicateHarness.sync_down()`` is the PRIMARY way to bring an S3-backed
    experiment's results onto local disk -- a harness already has the
    ``{model: tag}`` mapping (``archetype_tags``) in hand. This CLI exists for
    out-of-notebook use, where that mapping is re-typed by hand as repeated
    ``--tag`` flags; each splits on the FIRST ``"="``, so further ``"="`` in a
    model id or tag is unambiguous, and a later entry for the same model
    silently OVERWRITES an earlier one. `argv` defaults to ``None``, i.e.
    argparse reads ``sys.argv[1:]``. Returns ``0`` after printing one line
    naming `results_dir`, the number of objects downloaded and the store's
    :meth:`ResultsStore.describe`; a malformed ``--tag`` (no ``"="``) or any
    other argparse-level problem calls ``parser.error(...)``, raising
    ``SystemExit(2)``, which propagates rather than being caught here.
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
