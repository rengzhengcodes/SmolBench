"""Store replicate results in S3, with local files as the offline/test fallback.

``ReplicateHarness`` writes every replicate YAML through a :class:`ResultsStore`, so results
survive an ephemeral spot instance; a :class:`ReplicateAddress` carries `tag` (local key) and
`model` (S3 key).

Env contract: ``SMOLBENCH_RESULTS_S3=s3://<bucket>[/<base-prefix>]`` selects the S3 store,
unset/empty the local store rooted at ``results_dir``. :func:`resolve_store` reads the env at
call time, not at import, since a notebook runs ``load_dotenv`` after ``import smolbench``, and
falls back to local whenever `results_dir` is outside ``repo_root()`` so the offline suite's
``tmp_path`` runs stay hermetic.

Earliest-wins: S3 is an append-only log keyed
``<base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml`` with a fixed-width UTC
`run_ts`; every read takes the lexicographically (= chronologically) earliest surviving run per
(model, seed, info), so scores stay pass@1. A run is retired ("superseded") by writing a sibling
``.superseded`` marker beside it rather than editing or deleting it, keeping the log append-only
and every stored object immutable; :meth:`S3ResultsStore.exists` stays marker-blind on purpose so
the resume-skip check still counts a retired-but-unreplaced run as already spent, instead of
re-billing it. The local layout keeps one file per (tag, info, seed), overwritten in place with
no history; :func:`sync_down` bridges log -> local, one-way and overwriting.
:meth:`ResultsStore.regrade` replaces a run with a self-describing successor, superseding the old
run itself.
"""

import abc
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence

import smolbench
from smolbench.evals import Marks
from smolbench.evals import _aws
from smolbench.evals.study_config import load_study_config

# S3 marker suffix: a run at key ``K.yaml`` is retired by writing a SIBLING
# key ``K.superseded`` (never by touching ``K.yaml`` itself -- the log is
# append-only). Named once here so no use site repeats the literal and drifts
# from the writer (S3ResultsStore.supersede) or a reader
# (list_runs/load_marks/sync_down).
S3_SUPERSEDED_SUFFIX = ".superseded"

# Local retired-file infix: ``rep_<seed>.yaml`` -> a supersede renames it to
# ``rep_<seed>.SUPERSEDED-<run_ts>.yaml``. Matches the naming convention the
# sibling deduction leg already uses, so a human skimming a results directory
# recognizes a retired file the same way on either leg.
LOCAL_SUPERSEDED_INFIX = ".SUPERSEDED-"


def repo_root() -> Path:
    """Return the git checkout root: absolute, symlink-free, never cwd-relative.

    The one blessed path anchor for this repo -- a notebook kernel and the
    power-analysis scripts read the same ``results/`` tree from different cwds.
    """
    # smolbench.__file__ is <repo_root>/smolbench/__init__.py.
    return Path(smolbench.__file__).resolve().parents[1]


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parse an ``s3://bucket[/base-prefix]`` URI into ``(bucket, base_prefix)``.

    Shared deliberately: anything else mapping this URI to a bucket/prefix must use this parser,
    or writer and reader drift and orphan history under a prefix neither finds. `uri` is not
    stripped here; `resolve_store` strips its env value first, so whitespace around the URI
    stays distinct from whitespace inside it. `base_prefix` is ``""`` for a bucket-only URI,
    never carrying a leading or trailing ``"/"``. Raises ValueError on a missing ``"s3://"``
    scheme or an empty/whitespace-bearing segment -- a name S3 never accepts, which would give a
    store that can never find what it writes.
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
    """Return the project results bucket's canonical ``s3://...`` spelling.

    Reads ``smolbench.evals.study_config``'s committed ``[results]`` section, so this is the one
    place that URI is written down, used in error messages, CLI help and docs instead of each
    re-spelling the bucket name. Not what a caller should set ``SMOLBENCH_RESULTS_S3`` to for a
    different bucket -- it names the project's own provisioned bucket only.
    """
    results = load_study_config().results
    if not results.base_prefix:
        return f"s3://{results.bucket}"
    return f"s3://{results.bucket}/{results.base_prefix}"


def utcnow() -> datetime:
    """Return the current instant as a timezone-aware UTC ``datetime``.

    The one seam for "now", so a single monkeypatch pins every `run_ts` a test observes;
    `ReplicateHarness.run_replicates` calls it once per seed, so a seed's pooled `evaluate()`
    shares one timestamp. tz-aware because :func:`format_run_ts` appends a literal ``"Z"``.
    """
    return datetime.now(timezone.utc)


def format_run_ts(when: datetime) -> str:
    """Format `when` as the fixed-width UTC timestamp used in S3 log keys.

    `when` must already be UTC (normally :func:`utcnow`): `tzinfo` is not converted or
    inspected and the ``"Z"`` is a literal, so a naive or non-UTC datetime is silently
    mislabeled. Returns exactly 16 characters (``"20260810T193000Z"``); the fixed width makes
    lexicographic order equal chronological order for earliest-wins reads.
    """
    return when.strftime("%Y%m%dT%H%M%SZ")


def experiment_name(results_dir: Path, prefix: str = "") -> str:
    """Derive the ``<experiment>`` segment of an S3 log key from a results dir.

    `results_dir` must resolve under ``repo_root()`` (`resolve_store`, the only production
    caller, has already confirmed that); raises ValueError via `Path.relative_to` otherwise.
    Repo-relative ``notebooks/<nb>/results`` gives ``<nb>``; any other shape falls back to its
    full repo-relative POSIX path, except ``repo_root()`` itself, which gives ``""``, never
    ``"."``. A non-empty `prefix` folds in as a sub-level with exactly one trailing ``"_"``
    stripped: ``"induction/one_hop"``.
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
    #: Model id: the S3 LOG key; ignored by ``LocalResultsStore``. The one asymmetry in the
    #: address scheme -- local keys on `tag`, the log on `model`.
    #:
    #: ``model=None`` is a read-only shape: ``S3ResultsStore.exists``/``list_seeds`` return
    #: ``False``/``[]``; its ``load_marks`` doesn't special-case it and just raises
    #: ``FileNotFoundError`` on the literal ``"None"`` key segment; ``dump_marks`` refuses it
    #: rather than write that into a log that can't be corrected once written.
    model: Optional[str] = None


class ResultsStore(abc.ABC):
    """Backend-agnostic interface over one experiment's results.

    A store is rooted at a fixed location -- a local directory, or an S3
    bucket/prefix -- and addresses each result by :class:`ReplicateAddress`.
    """

    @abc.abstractmethod
    def exists(self, addr: ReplicateAddress) -> bool:
        """Return whether a replicate result is already stored at `addr`.

        The resume-skip check `ReplicateHarness` makes before re-evaluating a (tag, info, seed);
        on S3, any logged run counts, including a superseded one, since marker-blindness is what
        keeps a resumed run from re-billing work that was already collected and only later
        retired. Backend errors other than "not found" propagate rather than read as False: a
        credentials failure isn't "not run yet".
        """

    @abc.abstractmethod
    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        """Persist `marks` for `addr`, stamped with `run_ts`.

        No existence check; a caller wanting resume-skip calls :meth:`exists` first.
        run_ts: collection instant; `ReplicateHarness.run_replicates` captures :func:`utcnow`
            once per seed so a pooled `evaluate()` is one run.
        """

    @abc.abstractmethod
    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """Deserialize the replicate result stored/logged at `addr`.

        Returns the single local file, or on S3 the earliest logged run. Raises
        FileNotFoundError when nothing is stored/logged for `addr` (S3 names the missing prefix).
        """

    @abc.abstractmethod
    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """List every seed with at least one stored/logged replicate.

        model: the S3 key dimension; None yields [].
        tag: the local key dimension.

        Returns a sorted, distinct list (a seed re-collected many times counts once); empty
        when nothing is stored yet, which is not an error.
        """

    @abc.abstractmethod
    def supersede_all(self, addr: ReplicateAddress, reason: str) -> int:
        """Retire every currently-surviving run stored/logged at `addr`.

        The one call `ReplicateHarness` needs to void whatever is already there before
        collecting a replacement, or before `regrade` dumps a self-describing successor.
        "Retire" is backend-specific (an S3 `.superseded` marker per run, or a local rename)
        precisely so an append-only log never has an object edited or deleted to void it; the
        call shape is identical on both backends so a caller never branches.

        reason: freeform operator-facing text naming why the retirement happened; recorded in
            each S3 marker's body, only logged on the local store (nowhere durable to put it).

        Returns how many runs were retired; 0 (nothing was stored/logged at `addr`) is normal,
        not an error.
        """

    def regrade(
        self, marks: Marks, addr: ReplicateAddress, run_ts: datetime, *, reason: str
    ) -> None:
        """Replace every surviving run at `addr` with a self-describing regrade.

        Concrete on the ABC, built from :meth:`supersede_all` and :meth:`dump_marks` so there is
        exactly one regrade policy shared by both stores.

        marks: must carry `marks.regraded_from` (the `run_ts` of the run this replaces) -- a
            replacement that doesn't name what it replaced would defeat the point of a regrade
            in a log where nothing can be rewritten. Raises ValueError before touching the store
            if it's None.
        run_ts: stamp for the new run; forwarded to :meth:`dump_marks`.
        reason: forwarded to :meth:`supersede_all`, naming why the prior run(s) were retired.

        Supersedes before dumping, not after: a crash between the two steps leaves `addr` with
        no surviving run (`exists()` still reports it present, marker-blind, but `load_marks`
        refuses loudly, naming how many runs were superseded). The reverse order fails silently
        instead -- a crash after dumping but before superseding would leave two survivors, and
        earliest-wins would keep serving the old, un-regraded run with no sign anything was
        wrong.
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
        return f"{self.prefix}{tag}_{info}"

    def _path(self, addr: ReplicateAddress) -> Path:
        # addr.model is unused: the local layout has no model dimension.
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

        A name whose seed portion doesn't parse as an int is skipped (not a replicate; a missing
        directory globs to nothing rather than raising) -- which is also how a superseded
        ``rep_<seed>.SUPERSEDED-<run_ts>.yaml`` drops out with no special-casing, since its
        ``"rep_"``-stripped stem fails the same `int()` parse.
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

    def supersede(self, addr: ReplicateAddress, reason: str) -> Optional[Path]:
        """Retire the locally stored run at `addr`, if any, by renaming it.

        The local layout keeps no history, so "retire" means a plain rename to a name every
        reader already ignores: ``rep_<seed>.yaml`` -> ``rep_<seed>.SUPERSEDED-<ts>.yaml``. The
        bytes survive on disk (an operator can restore them by renaming back); nothing reads
        them again on its own.

        reason: logged only, at INFO level -- unlike the S3 marker, the local layout has no
            per-file side channel to persist it in.

        Returns the renamed file's new path, or None when nothing was stored at `addr` (a no-op,
        not an error). Backed by ``os.replace``; two supersedes of the same address within the
        same second produce the identical name, and the second silently overwrites the first
        retired file -- the same one-file-per-address property the live path already has.
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
        """See ``ResultsStore.supersede_all``.

        The local layout stores at most ONE run per address, so this is
        :meth:`supersede` recast as a count: ``1`` when something was there
        to retire, ``0`` when nothing was.
        """
        return 1 if self.supersede(addr, reason) is not None else 0

    def describe(self) -> str:
        """See ``ResultsStore.describe``."""
        return str(self.root)


def _parse_log_entry(rel: str) -> Optional[tuple[int, str, str]]:
    """Parse an S3 log key remainder into ``(seed, info, run_ts)``, or ``None``.

    Reverses the ``"seed=<seed>/<info>--<run_ts>.yaml"`` key shape; shared by
    :meth:`S3ResultsStore.list_seeds` and :func:`sync_down`. `rel` (the key with the leading
    ``"<log_prefix>/<model>/"`` stripped) is untrusted -- an S3 listing, not only this module's
    writers -- so it touches no filesystem. Returns None unless `rel` matches that shape
    (callers skip such keys as "not one of ours"); the stem splits on the first ``"--"``,
    unambiguous since no `info` has one.
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

    Keys are ``<base_prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml``. Every
    operation opens its own client via :meth:`_client`, never a cached one.

    A run is retired by a sibling ``<key>.superseded`` marker, never by touching or deleting the
    run object itself. :meth:`exists` and :meth:`list_seeds` stay marker-blind on purpose: they
    are the cheap presence probes `ReplicateHarness`'s resume-skip makes before spending GPU
    money, and superseding is only ever done paired with writing a replacement run (see
    `ReplicateHarness.run_replicates`'s `force_seeds` handling and :meth:`ResultsStore.regrade`).
    An unpaired supersede therefore leaves an address that :meth:`exists` still reports present
    but :meth:`load_marks` refuses to read -- a loud failure naming the prefix and marker count,
    not a silent empty read mistakable for "never collected".
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

    def __post_init__(self) -> None:
        """Refuse a store whose :attr:`log_prefix` would be ``""``.

        An empty prefix means "the whole bucket" to `list_objects_v2` -- `sync_down` would
        mirror every object into one results directory, and writes would land under a leading
        ``"/"``. Refused at construction, so `resolve_store` fails loudly instead of handing
        back a store that reads and writes the wrong thing.
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

        Whichever are non-empty, single ``"/"``, no leading/trailing ``"/"``; never ``""`` on a
        constructed store (see :meth:`__post_init__`).
        """
        return "/".join(p for p in (self.base_prefix, self.experiment) if p)

    def _seed_prefix(self, model: str, seed: int) -> str:
        return f"{self.log_prefix}/{model}/seed={seed}/"

    def _info_prefix(self, model: str, seed: int, info: str) -> str:
        """Return the prefix every logged run of this replicate shares."""
        return self._seed_prefix(model, seed) + f"{info}--"

    def _client(self):
        """Return a fresh boto3 S3 client for `self.region` (boto3 resolves `None`).

        Never cached: `_aws.fresh_client` builds a new Session per call so rotated credentials
        apply immediately (a notebook kernel outlives an IdP session), at a cost of seconds even
        across a full resume check. boto3 is imported lazily there, so this module imports
        without it.
        """
        return _aws.fresh_client("s3", self.region)

    def exists(self, addr: ReplicateAddress) -> bool:
        """See ``ResultsStore.exists``. Backed by ``list_objects_v2(MaxKeys=1)``, not
        ``head_object``, since it never raises for "not found" (200 with empty Contents), so a
        credentials failure still propagates. `addr.model is None` -> False.
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
        """See ``ResultsStore.dump_marks``. Backed by ``put_object`` into a key embedding
        `run_ts`; raises ValueError for `model=None` before the call, so a refused write leaves
        no object -- the S3 log is keyed by model, and a model-less address must never be
        written into a log where a bad object can't later be corrected, only deleted by hand.
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
        """One paginated listing over `addr`'s ``<info>--`` prefix, partitioned.

        Returns ``(survivor_run_ts, marker_count)``: survivors sorted ascending (lexicographic
        order equals chronological order), marker_count the number of ``.superseded`` keys seen
        regardless of whether their run is still present. Shared by :meth:`list_runs` and
        :meth:`load_marks` (which also needs the marker count for its FileNotFoundError message)
        so the survival rule lives in one traversal instead of two.
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
                # else: neither a run nor a marker under this prefix; ignore.
        survivors = sorted(ts for ts in run_stamps if ts not in marker_stamps)
        return survivors, len(marker_stamps)

    def list_runs(self, addr: ReplicateAddress) -> "list[str]":
        """Return the surviving run_ts stamps logged for `addr`, ascending.

        A run_ts survives iff it has no ``.superseded`` marker beside it -- the one place that
        definition is written down, shared by :meth:`load_marks` (takes the earliest) and
        :meth:`supersede_all` (retires every one). Empty covers both "nothing was ever logged"
        and "everything logged was superseded"; :meth:`load_marks` is what tells those apart.
        """
        survivors, _marker_count = self._list_run_partition(addr)
        return survivors

    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """See ``ResultsStore.load_marks``. Reads the earliest of :meth:`list_runs`'s survivors.

        FileNotFoundError names the prefix when nothing survives, and also the marker count when
        the reason is that every logged run was superseded rather than never logged, so an
        operator can tell "never collected" from "retired and not yet replaced" from the message
        alone.
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
        """Write a ``.superseded`` marker beside one already-logged run.

        The log is append-only, so a run can never be edited or deleted to void it -- a sibling
        key is written instead, the run object itself untouched, byte for byte.

        run_ts: the fixed-width stamp exactly as it appears in the run's key, not a `datetime`;
            this method never lists to find the run, it trusts the caller's stamp and writes the
            marker key directly.
        reason: freeform operator-facing text stored in the marker body; not interpreted by this
            module.

        Raises ValueError if `addr.model` is None: a model-less address is a read-only shape and
        nothing is ever logged there to supersede. Does not check whether `run_ts` actually names
        a logged run: a marker for a stamp nothing was ever logged under is harmless (nothing
        will ever match its prefix) and cheaper than an existence probe first.
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
        """See ``ResultsStore.supersede_all``. Supersedes every ``list_runs`` entry.

        Idempotent: a second call finds no survivors left and writes nothing new, returning 0.
        """
        survivors = self.list_runs(addr)
        for run_ts in survivors:
            self.supersede(addr, run_ts, reason)
        return len(survivors)

    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """See ``ResultsStore.list_seeds``. Backed by a paginated ``list_objects_v2``.

        `tag` is unused (an S3 key has no tag dimension), accepted only so one call shape serves
        either backend; `model=None` returns []. Marker-blind like :meth:`exists`:
        `_parse_log_entry` requires a `.yaml` filename, so a `.superseded` key already fails its
        parse and is skipped the same way as any other key that isn't one of ours -- a seed
        whose only logged run was superseded still counts, since the run object itself was never
        deleted.
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
    """Resolve which ``ResultsStore`` backend `results_dir` should use.

    Reads ``SMOLBENCH_RESULTS_S3``/``SMOLBENCH_RESULTS_S3_REGION`` at call time. Order is
    load-bearing: the URI is parsed and validated (raising ValueError on anything malformed)
    before the hermeticity check, since anchor-first would let a typo'd URI degrade silently to
    a local write on an ephemeral box, a loss discovered only once that box is gone.
    `results_dir` outside ``repo_root()`` then falls back to local (logged at INFO): `tmp_path`
    fixtures live outside the checkout, so the offline suite stays local even when a shell
    exports the variable.

    Region resolution: ``SMOLBENCH_RESULTS_S3_REGION``, else ``AWS_REGION``, else -- only when
    the URI's bucket equals the project's own provisioned bucket -- that config's region, else
    None (boto3's own chain decides). The config's region describes the config's bucket only; a
    URI naming a different bucket must keep resolving through boto3, since that bucket may live
    in any region.

    results_dir: need not exist -- resolved non-strictly, since an S3-first run may never create
        its local results directory.
    prefix: becomes `LocalResultsStore.prefix`, or folds into `S3ResultsStore.experiment`.
    """
    uri = os.environ.get("SMOLBENCH_RESULTS_S3", "").strip()
    if not uri:
        return LocalResultsStore(results_dir, prefix)

    # Validated before the hermeticity check (docstring says why).
    bucket, base_prefix = parse_s3_uri(uri)

    # Hermeticity fallback (docstring says why).
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

    # None lets boto3's own chain decide; the config fallback applies only when `bucket` is the
    # project's own, not as a general-purpose region default for an arbitrary bucket.
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


def _etag_md5(etag) -> Optional[str]:
    """Extract a whole-object MD5 hex digest from an S3 ``ETag`` value.

    Returns the unquoted hex digest iff `etag` is a single-part upload's whole-object MD5; None
    for missing/falsy or multipart (``<hex>-<partcount>``, never an MD5 of the bytes), which a
    caller must treat as "assume different" (download).
    """
    if not etag:
        return None
    unquoted = etag.strip('"')
    if "-" in unquoted:
        return None
    return unquoted


def _resolve_download_path(resolved_dir: Path, rel: str, key: str) -> Path:
    """Join `rel` under the already-resolved `resolved_dir`, refusing traversal.

    `rel` is validated rather than trusted since its components trace back to an S3 key, and
    this module's writers aren't the only thing that can put an object under a prefix. Raises
    ValueError naming `key` when the destination equals or lies outside `resolved_dir`, before
    the caller mkdirs or writes, so a refused key leaves no trace.
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

    Analysis code reads the local tree, not `ResultsStore`; this is the bridge. Each (model,
    seed, info)'s earliest surviving logged run lands where `LocalResultsStore` would put it.
    One-way and destructive: overwrites local files and never touches the log, so a local-only
    regrade is silently destroyed.

    tags: ``{model: tag}`` (an experiment's `archetype_tags`), the one thing the log can't
        supply; `ReplicateHarness.sync_down()` holds it and is the primary caller.
    prefix: forwarded to :func:`experiment_name`, and used in each local directory name.

    Returns the count of objects actually downloaded, excluding those skipped as identical.
    Raises RuntimeError if `results_dir` resolves to a `LocalResultsStore` (no log to sync), or
    ValueError if a destination resolves outside `results_dir`.

    The per-(seed, info) selection rule -- earliest surviving run_ts, a plain comparison of
    fixed-width stamps after excluding any stamp with a ``.superseded`` marker -- must stay
    identical to `S3ResultsStore.load_marks`'s, or a synced tree and a direct load fork the
    analysis. Markers are collected in the same single traversal as the run candidates, so every
    marker for a model is known before any (seed, info)'s survivor is chosen; a two-pass version
    (list once for markers, again for runs) was rejected since it doubles the LIST cost and could
    let two separate traversals observe two different snapshots of a live-changing prefix. A
    local file is skipped only when it exists and the listing ETag decodes to a single-part MD5
    equal to the local bytes' hash; size-only would be unsound (a regrade's 1 -> 0 flip preserves
    length). A multipart ETag never matches, so such an object re-downloads every call.
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

    # An empty log prefix (mirroring the whole bucket) never gets this far: S3ResultsStore
    # refuses to be constructed with one.
    resolved_dir = results_dir.resolve()
    client = store._client()
    paginator = client.get_paginator("list_objects_v2")
    downloaded = 0
    skipped = 0
    for model, tag in tags.items():
        list_prefix = f"{store.log_prefix}/{model}/"
        # One traversal, sorting each key into a superseded-marker record or a run candidate;
        # the earliest-wins reduction happens only after the loop, once every marker for this
        # model is known (see this function's docstring). A single pass also means the listing
        # can't observe a run and its later-published marker as two different snapshots.
        superseded: dict[tuple[int, str], set[str]] = {}
        # (seed, info) -> every candidate (run_ts, key, etag) seen so far. Held in full rather
        # than reduced with a streaming min, since a candidate can't be judged a survivor until
        # the whole listing (hence every marker) has been seen.
        candidates: dict[tuple[int, str], list[tuple[str, str, object]]] = {}
        for page in paginator.paginate(Bucket=store.bucket, Prefix=list_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(S3_SUPERSEDED_SUFFIX):
                    # Reuses _parse_log_entry by stripping the marker suffix and re-appending
                    # ".yaml", so the key shape is parsed in one place rather than twice.
                    rel = key[len(list_prefix): -len(S3_SUPERSEDED_SUFFIX)] + ".yaml"
                    parsed = _parse_log_entry(rel)
                    if parsed is None:
                        continue  # stray marker-shaped key; not one of ours
                    seed, info, run_ts = parsed
                    superseded.setdefault((seed, info), set()).add(run_ts)
                    continue
                if key.endswith("/"):
                    continue  # zero-byte directory placeholder, never written by this module
                parsed = _parse_log_entry(key[len(list_prefix):])
                if parsed is None:
                    continue  # stray key under this prefix; not one of ours
                seed, info, run_ts = parsed
                candidates.setdefault((seed, info), []).append(
                    (run_ts, key, obj.get("ETag"))
                )

        # Must match load_marks's earliest-surviving rule exactly (see docstring).
        earliest: dict[tuple[int, str], tuple[str, str, object]] = {}
        for seed_info, rows in candidates.items():
            marker_stamps = superseded.get(seed_info, ())
            surviving = [row for row in rows if row[0] not in marker_stamps]
            if surviving:
                earliest[seed_info] = min(surviving, key=lambda row: row[0])

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
                skipped += 1  # verified identical via ETag/MD5
                continue
            local_path.parent.mkdir(parents=True, exist_ok=True)
            body = client.get_object(Bucket=store.bucket, Key=key)["Body"].read()
            # tmp + os.replace, matching Marks.dump: a file that exists must
            # never be a torn write, because resume-skips gate on presence.
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
    """Run the CLI entry point: sync one results directory down from its S3 log.

    `ReplicateHarness.sync_down()` is the primary path (it already holds `archetype_tags`);
    this CLI re-types the mapping as repeated ``--tag MODEL=TAG`` flags, each split on the first
    ``"="`` (later ``"="`` are literal; a repeated model silently overwrites). Prints one summary
    line and returns 0.
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
