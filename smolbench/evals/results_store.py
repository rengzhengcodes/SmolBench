"""
S3-backed replicate results store, with local-filesystem storage as the
offline/test fallback.

Every replicate YAML written by :class:`~smolbench.evals.replicates.
ReplicateHarness` can be routed through a :class:`ResultsStore` instead of
going straight through ``open()``/``Marks.dump``/``Marks.load``, so a study's
results can live in S3 -- durable across an ephemeral EC2 spot instance's
lifetime, and shared between the box that generated them and whatever
machine later analyzes them -- without a second harness code path.
:func:`resolve_store` picks which backend a given results directory uses;
everything else in this module is plumbing around that one choice.

Every method on :class:`ResultsStore` addresses one replicate result via a
:class:`ReplicateAddress` (archetype tag, info type, seed, and -- for the S3
backend -- model id) rather than a raw string key. See that dataclass's
docstring for why an address has two different "identity" fields instead of
one: the local layout is keyed by `tag`, the S3 log is keyed by `model`, and
neither backend needs to know the other's key shape.

Env contract
------------
``SMOLBENCH_RESULTS_S3=s3://<bucket>[/<base-prefix>]`` selects the S3 store.
Unset, empty, or whitespace-only selects the local filesystem store rooted at
the caller's ``results_dir`` -- today's behavior, unchanged.

``SMOLBENCH_RESULTS_S3_REGION`` sets the S3 client's region; when unset,
``AWS_REGION`` is used instead; when that is unset too, ``None`` is passed
through to boto3, which resolves a region from its own chain (profile
config, instance metadata, etc. -- see
:func:`smolbench.evals._aws.fresh_client`).

Both variables are read INSIDE :func:`resolve_store`, at call time, never
captured as module-level constants. This mirrors ``smolbench.evals.ec2``'s
own documented hazard for its ``EC2_*`` constants (see that module's
docstring, "Env-read timing" section) for a structurally identical reason:
every notebook's first cell calls ``load_dotenv(keys.env)`` AFTER
``import smolbench...``-style statements have already executed. A constant
frozen at THIS module's import time would freeze to the un-overridden
default (unset -> local store) for the rest of the kernel's life, silently --
no exception, no log line, just every subsequent replicate quietly landing on
the ephemeral box's local disk instead of S3.

S3 key layout: an APPEND-ONLY EXPERIMENT LOG, not a mirror of the local tree
-------------------------------------------------------------------------------
An earlier version of this module mirrored ``results_dir``'s repo-relative
path directly onto the S3 key space, one object per replicate file, updated
in place on every rerun. That scheme is GONE. The bucket now holds a clean,
append-only log organised by model, seed, and collection time::

    <base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml

- ``base-prefix`` is the optional path segment carried by the
  ``SMOLBENCH_RESULTS_S3`` URI (see :func:`parse_s3_uri`); may be ``""``.
- ``experiment`` is derived from a results directory by
  :func:`experiment_name`: ``repo_root()/notebooks/<nb>/results`` -> ``<nb>``,
  with a harness ``prefix`` (e.g. ``"one_hop_"``) folded in as a SUB-LEVEL
  with its trailing ``"_"`` stripped -> ``<nb>/one_hop``. A results directory
  that does not match the ``notebooks/<nb>/results`` shape falls back to its
  full repo-relative POSIX path -- see that function's docstring.
- ``model`` is the model id exactly as passed to
  ``ReplicateHarness.run_replicates`` (a key of ``archetype_tags``).
- ``seed=<seed>`` is the literal ``seed=`` marker, for browsability in the S3
  console/CLI.
- ``run_ts`` is :func:`format_run_ts` applied to the instant this replicate
  was collected -- a FIXED-WIDTH UTC ``YYYYMMDDTHHMMSSZ`` stamp. The fixed
  width is load-bearing: it is what lets every "earliest run" lookup in this
  module be a plain lexicographic string MINIMUM over listed keys, with no
  timestamp parsing anywhere.

Worked example -- empty base prefix, notebook ``periodic_moe``, model
``gpt-oss-120b``, seed 1776, info ``extens``::

    periodic_moe/gpt-oss-120b/seed=1776/extens--20260810T193000Z.yaml

APPEND-ONLY, and every read resolves the EARLIEST run
-------------------------------------------------------
A dump ALWAYS creates a new, timestamped object; it never overwrites a prior
run's. Re-running an experiment (a re-collected replicate, a fixed bug, a
relaunch after a spot interruption) therefore ADDS to the log rather than
replacing anything in it -- no verdict is ever destroyed. Every read path in
this module (:meth:`S3ResultsStore.load_marks`, :func:`sync_down`) resolves
the EARLIEST ``run_ts`` per (model, seed, info) and treats only that one as
live; every later object under the same (model, seed, info) prefix is log
history, readable directly from S3 (e.g. for an audit of a re-collection)
but invisible to every method in this module.

EARLIEST-wins is a user ruling (2026-08-16), not a stylistic choice, and the
reads resolved LATEST until that date. The first logged run is the one
measurement whose selection cannot correlate with anything discovered after
it was taken -- retries, re-collections, and regrades all postdate it -- so
it is the estimator that keeps every reported score pass@1 under any later
operational history. (Either extreme is outcome-blind; "any run with a
desirable property" is the rule that would not be.)

The corollary is deliberate and must not be engineered around: **a
re-collection can never supersede logged data.** New objects for an already-
logged (model, seed, info) are invisible to every reader here. If logged
data must ever be voided (a corrupt collection, a voided arm), that now
requires an EXPLICIT exclusion visible to readers -- there is no
supersede-by-newer-object mechanism anymore, and quietly restoring one would
reverse the ruling.

The LOCAL layout is a different animal, and stays exactly as it always was:
one file per (tag, info, seed) -- ``{prefix}{tag}_{info}/rep_{seed}.yaml`` --
overwritten in place on every rerun. Append-only and earliest-wins are S3-LOG
properties; :class:`LocalResultsStore` has no history at all, by design,
because the local tree is what every existing analysis script, notebook, and
already-committed results directory depends on staying byte-identical.

Local fallback and the test suite's hermeticity
-------------------------------------------------
:func:`resolve_store` falls back to :class:`LocalResultsStore` whenever
``results_dir`` is not under ``repo_root()`` -- even with
``SMOLBENCH_RESULTS_S3`` set. ``pytest``'s ``tmp_path`` fixtures are always
outside the repo checkout, so the entire offline test suite keeps exercising
the local store unconditionally, even on a developer's shell that happens to
export ``SMOLBENCH_RESULTS_S3`` for their own interactive notebook work. No
test needs to unset the variable to stay hermetic.

No local write-through when S3 is active
-------------------------------------------
When :func:`resolve_store` returns an :class:`S3ResultsStore`, replicates are
appended ONLY to the S3 log -- there is no local write-through copy made
alongside it. This keeps a spot instance's local disk out of the durability
picture entirely (the whole point of moving to S3), at the cost that the
analysis layer (``notebooks/*/power_analysis.py``, the figure scripts), which
reads a LOCAL results tree and is deliberately NOT being ported to go through
``ResultsStore``, cannot see S3-resident results until they are pulled down.
:func:`sync_down` is that bridge.

``sync_down`` TRANSLATES the S3 log into the local layout -- and is
ONE-WAY and DESTRUCTIVE (S3 -> local only)
-----------------------------------------------------------------------------
Because the S3 layout is no longer a mirror of the local one, bringing an
S3-backed experiment's results onto local disk is a TRANSLATION, not a copy:
for each (model, seed, info) the EARLIEST logged run is written to the local
path a ``LocalResultsStore`` would use for that replicate, under the model's
configured archetype TAG -- which the log itself does not carry (a log key
names a model, never a tag). :func:`sync_down` therefore needs the
``{model: tag}`` mapping (an experiment's ``archetype_tags``) as an explicit
argument; :meth:`~smolbench.evals.replicates.ReplicateHarness.sync_down` is
the PRIMARY way to invoke this, since a harness already has that mapping in
hand and never has to re-type it.

This is still a ONE-WAY, DESTRUCTIVE mirror in the direction it operates:
:func:`sync_down` copies S3 -> local ONLY. It overwrites local files with
whatever the S3 log holds as the earliest run for the same
(model, seed, info), and it never uploads anything in the other direction.
Any local-only modification is silently DESTROYED by the next ``sync_down``
unless it was deliberately re-appended to the S3 log first -- and note that
under earliest-wins a re-append CANNOT restore a local edit either: the new
object postdates the original and is therefore invisible to readers.
Concretely, ``scripts/regrade.py --write`` rewrites replicate YAMLs IN PLACE
on the local tree, and a later ``sync_down`` of the same experiment
overwrites that regrade back to the log's earliest verdict with no warning.
The safe
operator sequence is: sync down, unset ``SMOLBENCH_RESULTS_S3`` (so
subsequent runs touch the local tree only, not S3), and regrade locally.
The pre-ruling sequence ended "...then re-seed the regraded tree back to
S3"; that step is now DEAD -- a re-seeded object postdates the original and
no reader here will ever resolve it (and seeding a regrade over history is
separately forbidden for this bucket regardless). A regrade that must
outlive the local tree is an explicit-exclusion problem, not a re-seed
problem.

URI parsing: one parser, shared
----------------------------------
:func:`parse_s3_uri` is the single source of truth for what counts as a
well-formed ``s3://bucket[/base-prefix]`` URI; :func:`resolve_store` calls it
rather than re-parsing inline, and it is a public, importable function
specifically so other packages that need to agree with this module on the
bucket/prefix mapping (e.g. a provisioning script seeding a bucket at a given
``--dest``) parse the SAME URI the SAME way. Two independent parsers for the
same URI format is how a seeder and a reader silently drift and orphan
history under a prefix neither of them can find again.

Command-line usage
-------------------
::

    python -m smolbench.evals.results_store <results_dir> \\
        --tag model=tag [--tag model=tag ...] [--prefix one_hop_]

syncs one (repo-anchored) results directory down from its S3-backed
experiment log, given the ``{model: tag}`` mapping on the command line. See
:func:`main`. ``ReplicateHarness.sync_down()`` is the PRIMARY way to do
this from inside a notebook, since a harness already has ``archetype_tags``
in hand and never has to re-type the mapping; this CLI exists for
out-of-notebook use (a standalone script, a shell one-liner, CI).
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
    """Returns the repository root, anchored via the installed package.

    Design: every notebook computes its results/state-file paths the same
    way (``Path(smolbench.__file__).resolve().parents[1]``) rather than
    anything cwd-relative, because notebook kernels can run with a temp-dir
    cwd and the power-analysis scripts read the same ``results/`` tree from
    a different working directory entirely. This function is that one
    blessed anchor, reused by every path derived below (and, via
    ``smolbench.induction.experiment``'s re-export, by every existing
    caller that predates this module).

    Returns
    -------
    Path
        The directory containing the top-level ``notebooks/`` folder (i.e.
        the git checkout root), resolved to an absolute, symlink-free path.
    """
    # smolbench.__file__ -> <repo_root>/smolbench/__init__.py; two parents
    # up strips both the file and the package directory.
    return Path(smolbench.__file__).resolve().parents[1]


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parses an ``s3://bucket[/base-prefix]`` URI into ``(bucket, base_prefix)``.

    The single source of truth for what counts as a well-formed URI in this
    module's sense -- see the module docstring's "URI parsing: one parser,
    shared" section for why this is a public function rather than a helper
    inlined into :func:`resolve_store`: another package (a bucket-seeding
    script) needs to agree with this module on the exact same mapping, and
    two independently-maintained parsers for the same format is exactly how
    that agreement quietly breaks.

    Parameters
    ----------
    uri : str
        A candidate URI, e.g. ``"s3://my-bucket/archive"`` or
        ``"s3://my-bucket"``. Not stripped of surrounding whitespace by this
        function -- callers that read this from an environment variable
        (``resolve_store``) do that themselves before calling in, since
        "the env var had stray whitespace around an otherwise-valid URI" and
        "the URI itself contains whitespace" are different failures worth
        distinguishing at the call site.

    Returns
    -------
    tuple of (str, str)
        ``(bucket, base_prefix)``. ``base_prefix`` is ``""`` when the URI
        carries no path beyond the bucket, and never has a leading or
        trailing ``"/"`` in any case.

    Raises
    ------
    ValueError
        The URI is malformed, naming both the offending URI and the specific
        rule it broke:

        - Does not start with the literal scheme ``"s3://"`` (e.g. a bare
          bucket name, a wrong scheme like ``"https://"``, or a single-slash
          typo like ``"s3:/bucket"``).
        - Contains an EMPTY path segment once the scheme is stripped and any
          trailing ``"/"`` removed -- this covers a missing bucket
          (``"s3://"``, ``"s3:///notebooks"``) and a doubled internal slash
          anywhere in the bucket or prefix (``"s3://buck//archive"``,
          ``"s3://buck/arch//ive"``) uniformly, since both are the same
          underlying defect (an empty ``"/"``-delimited component).
        - Any segment (bucket or a prefix component) contains whitespace, or
          differs from its own ``.strip()`` -- rejects a URI like
          ``"s3:// buck/archive"`` or ``"s3://bu ck"`` that would otherwise
          parse into a bucket name S3 itself would never accept, silently
          producing a store that can never find anything it writes.

    Notes
    -----
    Trailing ``"/"`` is stripped from the URI (after the scheme) before
    splitting, so ``"s3://bucket/archive/"`` and ``"s3://bucket/archive"``
    parse identically. The scheme is checked, and only then stripped, before
    trailing slashes are removed -- stripping trailing ``"/"`` from the RAW
    uri first would corrupt the ``"s3://"`` scheme separator itself for an
    all-slash remainder (e.g. bare ``"s3://"``).
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
    """Returns the current instant as a timezone-aware UTC ``datetime``.

    The ONE seam this module's callers use to get "now" -- every S3 log
    timestamp traces back to a call to this function, never to
    ``datetime.now(timezone.utc)`` written out inline elsewhere. That makes a
    single monkeypatch (``monkeypatch.setattr(results_store, "utcnow", lambda:
    FIXED)``) enough to pin every ``run_ts`` a test observes, and it is what
    ``ReplicateHarness.run_replicates`` calls once per seed to give every
    info type collected in that seed's pooled ``evaluate()`` call one shared
    timestamp (see that method's docstring).

    Returns
    -------
    datetime
        ``datetime.now(timezone.utc)`` -- always timezone-aware (``tzinfo``
        is never ``None``). This matters because :func:`format_run_ts`
        appends a literal ``"Z"`` without inspecting the offset: formatting a
        NAIVE datetime through it would silently mislabel local time as UTC.
    """
    return datetime.now(timezone.utc)


def format_run_ts(when: datetime) -> str:
    """Formats `when` as the fixed-width UTC timestamp used in S3 log keys.

    Parameters
    ----------
    when : datetime
        Normally the return value of :func:`utcnow`, i.e. timezone-aware and
        already in UTC. This function does NOT itself convert `when` to UTC
        or inspect its ``tzinfo`` -- it appends a literal ``"Z"``
        unconditionally, so a naive or non-UTC-aware datetime is silently
        mislabeled. Every call site in this module passes a value from
        :func:`utcnow`, which is always correct by construction.

    Returns
    -------
    str
        ``when.strftime("%Y%m%dT%H%M%SZ")``, e.g. ``"20260810T193000Z"`` --
        always exactly 16 characters (FIXED WIDTH, zero-padded fields). The
        fixed width is load-bearing: it is what makes a plain lexicographic
        string comparison of two ``run_ts`` values agree with chronological
        order, which is how every "earliest run wins" read in this module
        (:meth:`S3ResultsStore.load_marks`, :func:`sync_down`) finds the
        first logged run without ever parsing a timestamp back out of a key.

    Notes
    -----
    Design: a literal trailing ``"Z"`` baked into the ``strftime`` format
    string, rather than ``%z``/``isoformat()``, is deliberate. ``%z`` on a
    UTC-aware datetime renders ``"+0000"`` (5 characters, wrong shape for the
    "Z" convention this scheme documents), and would vary in width entirely
    for a non-UTC offset. The literal ``"Z"`` is unconditional and always
    exactly one character, which is what preserves the fixed-width guarantee
    regardless of what ``when`` actually is.
    """
    return when.strftime("%Y%m%dT%H%M%SZ")


def experiment_name(results_dir: Path, prefix: str = "") -> str:
    """Derives an experiment's S3 log path segment from its local results dir.

    See the module docstring's "S3 key layout" section for where this fits
    into a full key. This function computes only the ``<experiment>``
    segment.

    Parameters
    ----------
    results_dir : Path
        A repo-anchored results directory (e.g.
        ``InductionExperiment.results_dir``). Must resolve under
        ``repo_root()`` -- :func:`resolve_store`, this function's only
        production caller, only ever reaches it after already confirming
        that itself (its hermeticity fallback returns a
        ``LocalResultsStore`` for anything that fails the anchor check,
        before ``experiment_name`` is called at all).
    prefix : str, optional
        The harness's namespace prefix (e.g. ``"one_hop_"``), forwarded
        verbatim from ``ReplicateHarness.prefix`` / ``resolve_store``.
        Defaults to ``""`` (no sub-level folded in).

    Returns
    -------
    str
        POSIX-separated, with no leading or trailing ``"/"``.

        - When `results_dir`, taken relative to ``repo_root()``, is EXACTLY
          three path components shaped ``notebooks/<nb>/results`` (first
          component literally ``"notebooks"``, last literally
          ``"results"``): ``<nb>``, or ``<nb>/<sub>`` when `prefix` is
          non-empty.
        - Otherwise (`results_dir` does not match that three-component
          shape -- e.g. a differently-named results tree, or a notebook
          nested more than one level deep): `results_dir`'s own full
          repo-relative POSIX path, with the same `prefix` sub-level folded
          in on top. THIS IS A DOCUMENTED FALLBACK, not a degraded/error
          case -- every notebook in this repo today uses the
          ``notebooks/<nb>/results`` shape, but this function does not
          assume that holds forever, and a results tree that does not match
          it still gets a stable, collision-free experiment name rather
          than an exception.

        In both cases, `prefix` (when non-empty) is folded in as a
        SUB-LEVEL with exactly one trailing ``"_"`` stripped --
        ``"one_hop_"`` becomes the sub-level ``"one_hop"`` (a prefix with no
        trailing ``"_"`` is used as-is) -- e.g. notebook ``"chromatic"``
        with ``prefix="one_hop_"`` yields ``"chromatic/one_hop"``.

    Raises
    ------
    ValueError
        `results_dir` does not resolve under ``repo_root()`` (propagated
        from ``Path.relative_to``). Not expected to fire from
        :func:`resolve_store`'s call site (see Parameters above); a direct
        caller that skips the anchor check gets the same error
        :func:`resolve_store` would itself have raised there.

    Notes
    -----
    ``results_dir == repo_root()`` itself has repo-relative path
    ``Path(".")``, whose ``.as_posix()`` is the literal string ``"."`` --
    the one case where "the full repo-relative POSIX path" would otherwise
    be that awkward single character. This function special-cases it to
    ``""`` instead (folding a non-empty `prefix` in directly, with no
    leading ``"/"``), mirroring the equivalent special case the pre-log-scheme
    version of :func:`resolve_store` used to apply to its own repo-mirroring
    prefix.
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
    """Identifies one (archetype, info type, seed) replicate result.

    Threaded through every :class:`ResultsStore` method instead of a raw
    string key, so each backend can render its own layout from the SAME
    address without either backend needing to know the other's key shape --
    :class:`LocalResultsStore` addresses a replicate by `tag`, while
    :class:`S3ResultsStore` addresses one by `model`.
    """

    #: Archetype tag (e.g. ``"decode"``, ``"cot"``) -- drives the LOCAL
    #: layout's directory name (``{prefix}{tag}_{info}``). Ignored entirely
    #: by ``S3ResultsStore`` (see `model`).
    tag: str
    #: Info type (e.g. ``"intens"``, ``"extens"``, ``"noise_intens"``). Used
    #: by BOTH backends.
    info: str
    #: Replicate seed. Used by BOTH backends.
    seed: int
    #: Model id -- drives the S3 LOG layout's key
    #: (``<model>/seed=<seed>/<info>--<run_ts>.yaml``). Ignored entirely by
    #: ``LocalResultsStore`` (see `tag`).
    #:
    #: THIS IS THE ONE ASYMMETRY IN THE ADDRESS SCHEME: the local layout is
    #: keyed by `tag`, but the S3 log is keyed by `model`. Most callers
    #: (``run_replicates``, ``has_outstanding``, ``summarize``) know a real
    #: model id, because they reach a ``ReplicateAddress`` by working
    #: through ``archetype_tags`` forward (model -> tag).
    #: ``ReplicateHarness.cot_chain_lengths(tag="cot")``, though, is keyed
    #: on `tag` ALONE -- an existing test calls it with no model in scope at
    #: all -- so the harness reverse-looks-up `tag` -> `model` through
    #: ``archetype_tags`` (first match; see that method's docstring for why
    #: first-match is correct there) and passes ``None`` when NO configured
    #: model carries that tag.
    #:
    #: A ``None`` model is NOT an error ON READ. ``LocalResultsStore`` never
    #: inspects `model` at all, so it is unaffected; ``S3ResultsStore.
    #: exists``/``list_seeds`` both explicitly special-case ``None`` to mean
    #: "nothing logged" (``False``/``[]``) rather than raising or building a
    #: key with a literal ``"None"`` path segment. ON WRITE, though,
    #: ``None`` IS refused: ``S3ResultsStore.dump_marks`` raises
    #: ``ValueError`` rather than write into the append-only log under a
    #: literal ``"None"`` model directory, since that log has no
    #: overwrite/correction mechanism for a bad object once written -- see
    #: that method's docstring. ``model=None`` is therefore a READ-only
    #: shape in practice: legitimate for the tag-keyed lookups that produce
    #: it (``ReplicateHarness.cot_chain_lengths`` when no configured model
    #: carries the requested tag), never for a write.
    model: Optional[str] = None


class ResultsStore(abc.ABC):
    """Backend-agnostic interface over one experiment's replicate results.

    A store is rooted at some fixed location -- a local directory, or an S3
    bucket/prefix -- and every method below addresses one replicate result
    via a :class:`ReplicateAddress` rather than a raw string key. See that
    dataclass's docstring for why an address carries two different
    "identity" fields (`tag` and `model`) instead of one.
    """

    @abc.abstractmethod
    def exists(self, addr: ReplicateAddress) -> bool:
        """Whether a replicate result is already stored at `addr`.

        Parameters
        ----------
        addr : ReplicateAddress
            The replicate to check.

        Returns
        -------
        bool
            True iff a result is already stored/logged for `addr`. This is
            the resume-skip check: ``ReplicateHarness`` consults it before
            re-evaluating a given (tag, info, seed), so a resumed run never
            re-runs (and re-bills) work that already landed. For an
            S3-backed store, ANY logged run counts as done -- no ordering
            requirement at all, since any logged run proves the work was
            already performed once (and under earliest-wins reads, the
            first one is precisely the run that counts).

        Raises
        ------
        Exception
            Backend-specific errors OTHER THAN "not found"/"not logged"
            propagate rather than being reported as False -- see
            :meth:`S3ResultsStore.exists` for the concrete case (a
            credentials/permissions failure must never be silently read as
            "this replicate has not been run yet").
        """

    @abc.abstractmethod
    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        """Persists `marks` for `addr`, stamped with `run_ts`.

        Parameters
        ----------
        marks : Marks
            The graded result to persist.
        addr : ReplicateAddress
            Which replicate this is.
        run_ts : datetime
            The instant this collection event represents -- normally
            :func:`utcnow`, captured ONCE per seed by
            ``ReplicateHarness.run_replicates`` so every info type collected
            in that seed's single pooled ``evaluate()`` call shares one
            timestamp (a per-info timestamp would let one seed's arms
            scatter across several apparent "runs" in the log, which is
            wrong: they are one evaluation event that happened to cover
            several info types at once).

            Meaning differs by backend:

            - ``S3ResultsStore``: embedded in the newly-created object's key
              (:func:`format_run_ts` applied to `run_ts`) -- this IS the
              mechanism that makes the write append-only. Every call creates
              a NEW object; nothing is ever overwritten.
            - ``LocalResultsStore``: IGNORED entirely. The local layout has
              exactly one file per (tag, info, seed); a rerun overwrites it
              in place, exactly as it did before this parameter existed.
              Append-only is an S3-LOG property, not a local-tree property.

        Returns
        -------
        None

        Notes
        -----
        Performs no existence check of its own -- callers that want
        resume-skip semantics check :meth:`exists` first (as
        ``ReplicateHarness`` does).
        """

    @abc.abstractmethod
    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """Deserializes the replicate result stored/logged at `addr`.

        Parameters
        ----------
        addr : ReplicateAddress
            Which replicate to load.

        Returns
        -------
        Marks
            For ``LocalResultsStore``, the single file stored at `addr`'s
            path. For ``S3ResultsStore``, the EARLIEST logged run for `addr`
            (see :meth:`S3ResultsStore.load_marks`) -- later re-collections
            of the same replicate are never returned by this method.

        Raises
        ------
        FileNotFoundError
            Nothing is stored/logged for `addr`, on EITHER backend: locally
            because the underlying ``open()``/``Path`` access already
            raises this; on S3 because it is explicitly raised, naming the
            missing key prefix, since an empty listing has no exception of
            its own to surface. Callers that need to distinguish "not
            found" from a genuine backend failure should check
            :meth:`exists` first.
        """

    @abc.abstractmethod
    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """Lists every seed with at least one stored/logged replicate.

        Parameters
        ----------
        model : str or None
            Model id -- the S3 backend's key dimension. ``None`` means "no
            model is known for this query" (see ``ReplicateAddress.model``);
            ``S3ResultsStore`` returns ``[]`` in that case rather than
            raising.
        tag : str
            Archetype tag -- the local backend's key dimension.
        info : str
            Info type.

        Returns
        -------
        list of int
            SORTED, DISTINCT seeds. For ``S3ResultsStore`` this counts a
            seed once regardless of how many times it was re-collected
            (append-only reruns do not inflate this count) -- see
            :meth:`ResultsStore.dump_marks`'s docstring on append-only
            semantics. Empty when nothing has been stored/logged yet for
            this (backend-appropriate) key, matching the pre-existing
            behavior of globbing a directory that does not exist: no
            replicates found is not an error.
        """

    @abc.abstractmethod
    def describe(self) -> str:
        """A short, human-readable identifier for this store's location.

        Returns
        -------
        str
            E.g. a local filesystem path, or an ``s3://bucket/prefix`` URI.
            For logging/CLI output only -- never parsed back into a store.
        """


@dataclass(frozen=True)
class LocalResultsStore(ResultsStore):
    """Filesystem-backed store: today's on-disk replicate tree, unchanged.

    Every method here reproduces the pre-``ResultsStore`` behavior that used
    to live directly in ``ReplicateHarness``/``Marks`` byte-for-byte, so
    existing local results trees (including already-committed ones) remain
    readable with no migration step. This store IGNORES `addr.model` and the
    `run_ts` argument to :meth:`dump_marks` entirely -- there is exactly one
    local file per (tag, info, seed) replicate, and a new run overwrites it,
    exactly as it always has. Append-only, earliest-wins semantics are S3-LOG
    properties (see the module docstring); they do not apply here -- note the
    asymmetry this creates: a local rerun REPLACES its predecessor, an
    S3-logged rerun is INVISIBLE to readers behind its predecessor.
    """

    #: Directory holding the per-condition replicate dirs -- an experiment's
    #: ``results_dir``.
    root: Path
    #: Optional namespace prefix on directory names (e.g. ``"one_hop_"``),
    #: forwarded verbatim from ``ReplicateHarness.prefix``.
    prefix: str = ""

    def _dirname(self, tag: str, info: str) -> str:
        """The directory name for one (archetype, info type): ``f"{self.prefix}{tag}_{info}"``."""
        return f"{self.prefix}{tag}_{info}"

    def _path(self, addr: ReplicateAddress) -> Path:
        """The on-disk path for one replicate: ``root/{prefix}{tag}_{info}/rep_{seed}.yaml``.

        `addr.model` plays no part in this path -- see the class docstring.
        """
        return self.root / self._dirname(addr.tag, addr.info) / f"rep_{addr.seed}.yaml"

    def exists(self, addr: ReplicateAddress) -> bool:
        """See ``ResultsStore.exists``. Backed by ``Path.exists``."""
        return self._path(addr).exists()

    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        """See ``ResultsStore.dump_marks``. `run_ts` is ignored (see class docstring).

        Notes
        -----
        ``path.parent.mkdir(parents=True, exist_ok=True)`` is this method's
        responsibility (not the caller's), so a single ``dump_marks`` call is
        a complete unit of work for BOTH backends -- S3 needs no mkdir at
        all (there are no directories, only keys), so the harness can no
        longer be the one responsible for it.
        """
        path = self._path(addr)
        path.parent.mkdir(parents=True, exist_ok=True)
        marks.dump(path)

    def load_marks(self, addr: ReplicateAddress) -> Marks:
        """See ``ResultsStore.load_marks``. Backed by ``Marks.load``."""
        return Marks.load(self._path(addr))

    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        """See ``ResultsStore.list_seeds``. `model` is ignored (see class docstring).

        Notes
        -----
        Globs ``rep_*.yaml`` under ``root/{prefix}{tag}_{info}`` and parses
        the integer seed out of each matched name (the text between
        ``"rep_"`` and the ``.yaml`` suffix, via ``Path.stem``). A name whose
        seed portion does not parse as a plain ``int`` is SKIPPED, not
        counted -- today's original glob-based ``summarize`` would have
        counted any ``rep_*.yaml`` file regardless of what followed the
        underscore, but a malformed name (hand-edited, partially written, or
        from some other tool entirely) is not a genuine replicate and should
        not be reported as one. ``Path.glob`` on a directory that does not
        exist yields nothing rather than raising, which is exactly right for
        an archetype/info-type combination that has not been run yet.
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
    """Parses one S3 log key's remainder into ``(seed, info, run_ts)``.

    The reverse of the ``"seed=<seed>/<info>--<run_ts>.yaml"`` key shape
    (see the module docstring's "S3 key layout" section), applied to `rel`
    -- a key with the leading ``"<log_prefix>/<model>/"`` portion already
    stripped off. Shared by :meth:`S3ResultsStore.list_seeds` and
    :func:`sync_down`, which both need to recover a listed key's (seed,
    info, run_ts) rather than merely testing for existence.

    Parameters
    ----------
    rel : str
        A key remainder, e.g. ``"seed=1776/extens--20260810T193000Z.yaml"``.
        UNTRUSTED in general (it comes from an S3 listing, not from this
        module's own writers exclusively -- see :func:`sync_down`'s
        traversal-guard notes), but this function only ever extracts
        `seed`/`info`/`run_ts` from a shape that already constrains what
        those values can contain (an ``int``, and text with no ``"/"``); it
        performs no filesystem access itself.

    Returns
    -------
    tuple of (int, str, str) or None
        ``(seed, info, run_ts)`` on a match, or ``None`` when `rel` does not
        match the expected shape -- a caller under the same listing prefix
        that predates this key scheme, was hand-placed, or is otherwise not
        one of this module's own log entries. Every caller of this function
        skips a ``None`` result rather than raising, treating a stray key as
        "not one of ours" instead of a hard error.

    Notes
    -----
    Matching rules, applied in order:

    1. `rel` must split on ``"/"`` into EXACTLY two components (a
       ``"seed=..."`` segment and a filename) -- anything deeper or
       shallower does not match.
    2. The first component must start with the literal ``"seed="`` marker,
       and the remainder must parse as a plain ``int`` (``int(...)``, so a
       leading ``"-"`` is accepted -- this module never writes a negative
       seed, but nothing about the log format forbids one, and rejecting it
       here would be an assumption this function has no need to make).
    3. The second component must end with ``".yaml"``; the text before that
       suffix is split on the FIRST ``"--"`` it contains into
       ``(info, run_ts)``. No component of this scheme's `info` values
       (``"intens"``, ``"extens"``, ``"noise_intens"``, ``"cot"``, ...) ever
       contains ``"--"``, so splitting on the first occurrence is
       unambiguous for every key this module itself ever writes.
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
    """S3-backed store: an append-only replicate log under one key prefix.

    See the module docstring's "S3 key layout" section for the full key
    shape this store reads and writes:
    ``<base_prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml``.

    Every operation opens its own client via :meth:`_client` rather than
    caching one on the instance -- see that method's docstring for why a
    per-call, freshly-constructed client matters for a long-lived store
    object.
    """

    #: S3 bucket name.
    bucket: str
    #: Base prefix carried by the ``SMOLBENCH_RESULTS_S3`` URI; never has a
    #: leading or trailing ``"/"``. May be ``""`` (no base prefix).
    base_prefix: str
    #: This experiment's log path segment, e.g. ``"periodic_moe"`` or
    #: ``"chromatic/one_hop"`` -- see :func:`experiment_name`.
    experiment: str
    #: Region for the S3 client, or ``None`` to let boto3 resolve one from
    #: its own chain.
    region: Optional[str] = None

    @property
    def log_prefix(self) -> str:
        """This store's key prefix, ``base_prefix`` and ``experiment`` joined.

        Returns
        -------
        str
            ``"/".join(p for p in (self.base_prefix, self.experiment) if p)``
            -- i.e. whichever of the two are non-empty, joined with a single
            ``"/"``, with no leading or trailing ``"/"`` UNLESS both are
            empty (then this is ``""`` itself). Every model/seed/info key
            below is built on top of this prefix.
        """
        return "/".join(p for p in (self.base_prefix, self.experiment) if p)

    def _seed_prefix(self, model: str, seed: int) -> str:
        """The key prefix for one (model, seed): ``f"{log_prefix}/{model}/seed={seed}/"``."""
        return f"{self.log_prefix}/{model}/seed={seed}/"

    def _info_prefix(self, model: str, seed: int, info: str) -> str:
        """The key prefix for one (model, seed, info): `_seed_prefix` plus ``f"{info}--"``.

        Every logged run of this replicate shares this prefix, differing
        only in the ``run_ts`` (and trailing ``.yaml``) that follows it --
        this is exactly the prefix :meth:`exists`/:meth:`dump_marks`/
        :meth:`load_marks` list or write under.
        """
        return self._seed_prefix(model, seed) + f"{info}--"

    def _client(self):
        """Returns a fresh boto3 S3 client for this store's region.

        Design: ``_aws.fresh_client`` builds a brand-new
        ``boto3.session.Session`` per call SPECIFICALLY so a rotated
        credentials file is picked up on the very next call instead of
        raising ``ExpiredToken`` until the kernel restarts -- and a
        ``ResultsStore`` instance (unlike a short-lived script) is typically
        cached for a whole notebook session, which routinely runs many
        hours, longer than an IdP-issued session's credentials lifetime.
        Caching a client on ``self`` here would reintroduce exactly the
        staleness ``fresh_client`` exists to avoid.

        Cost: a resume check (``exists``) issues one ``list_objects_v2``
        (``MaxKeys=1``) per (info type, seed), so a 3-arm, 30-replicate
        model costs on the order of 90 listing requests plus 90 fresh
        ``Session`` constructions -- on the order of seconds, against a
        ``serve_model`` step that pulls hundreds of GB of model weights onto
        the instance. The per-call session cost is negligible next to that.

        Returns
        -------
        Any
            A boto3 S3 client bound to ``self.region`` (or boto3's own
            resolved default region when ``self.region`` is ``None``).

        Notes
        -----
        Imports boto3 lazily via ``_aws.fresh_client`` -- see that
        function's docstring and this module's "Env contract" section for
        why nothing in this module requires boto3 merely by being imported.
        """
        return _aws.fresh_client("s3", self.region)

    def exists(self, addr: ReplicateAddress) -> bool:
        """See ``ResultsStore.exists``. Backed by ``list_objects_v2(MaxKeys=1)``.

        Parameters
        ----------
        addr : ReplicateAddress
            Requires `addr.model` to mean anything -- an S3 key always
            names a model, never a bare tag (see ``ReplicateAddress.model``).

        Returns
        -------
        bool
            ``False`` immediately when `addr.model` is ``None`` -- this is
            the tag-only-read case documented on ``ReplicateAddress.model``,
            and it is NOT an error: it means "no model in
            ``archetype_tags`` carries this tag", which the local store
            answers just fine (it never looks at `model`) and this store
            correctly reports as "nothing logged". Otherwise, ``True`` iff
            the listing under `addr`'s (model, seed, info) prefix returns at
            least one key.

        Notes
        -----
        Unlike ``head_object`` (which 404s for a missing key), a
        ``list_objects_v2`` query that matches nothing returns a normal 200
        response with an empty (or absent) ``Contents`` -- it never raises
        for "not found". This method therefore needs NO exception handling
        of its own: any exception ``list_objects_v2`` DOES raise (a
        credentials/permissions failure, a malformed bucket name, ...)
        propagates completely unhandled, which is exactly the desired
        behavior -- such a failure must never be silently read as "this
        replicate has not been run yet" (that would re-run, and re-bill,
        work that may well already exist).
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

        Raises
        ------
        ValueError
            `addr.model` is ``None``. The S3 log is keyed by MODEL, not by
            tag (see ``ReplicateAddress.model``'s docstring), so a
            model-less address has no valid key to write to at all --
            without this guard, Python's f-string interpolation of
            ``None`` would silently degrade into the literal path segment
            ``"None"`` (e.g. ``"periodic_moe/None/seed=1776/intens--....
            yaml"``) rather than raising. That would be written to the
            APPEND-ONLY log, where nothing can later overwrite or correct
            it -- unlike every other mistake in this design, which is
            self-healing on the next correct run, a bad ``None/`` object
            persists until someone finds and deletes it by hand, sitting as
            a sibling to the real per-model directories in what is meant to
            be a clean, deliberately-provisioned experiment log. Raised
            BEFORE ``put_object`` is ever called, so a refused write leaves
            no object behind.

            ``model=None`` is legitimately reachable on this class (`addr`
            is not statically guaranteed to carry a model) -- it is just
            never legitimate to WRITE with. It is a READ-only shape, used by
            tag-keyed lookups (``ReplicateHarness.cot_chain_lengths``, when
            no configured model carries the requested tag), which
            ``LocalResultsStore`` can serve because its layout has no model
            dimension to be missing in the first place; :meth:`exists` and
            :meth:`list_seeds` on THIS store both still accept ``None`` and
            answer "nothing here" (``False``/``[]``) rather than raising --
            only a WRITE with no model is refused.

        Notes
        -----
        Always creates a NEW object -- the key embeds `run_ts`
        (:func:`format_run_ts`), so two calls for the same `addr` at
        different `run_ts` values write two DIFFERENT keys, never
        overwriting one another. This is the append-only mechanism the
        module docstring describes; there is no existence check or delete
        here, by design.
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

        Returns
        -------
        Marks
            The run at the LEXICOGRAPHICALLY MINIMUM key under `addr`'s
            (model, seed, info) prefix -- which, thanks to `run_ts`'s fixed
            width (see :func:`format_run_ts`), is exactly the
            chronologically first logged run. Every later run under the
            same prefix is ignored: user ruling 2026-08-16, "use the
            earliest results to keep pass@1" (this method resolved LATEST
            before that date; see the module docstring for the rationale
            and the supersede-requires-explicit-exclusion corollary).

        Raises
        ------
        FileNotFoundError
            Nothing is logged under `addr`'s prefix -- named explicitly in
            the message (the prefix itself, so an operator can go inspect
            it directly in S3) so a caller that skipped :meth:`exists`
            first gets a clear, addressable error instead of, say, an
            ``IndexError`` from an empty min() over nothing.

        Notes
        -----
        An S3 listing is lexicographically ordered within and across pages,
        so the FIRST matching key of the FIRST page is already the minimum.
        The loop below still scans the (tiny: one to a few keys) listing
        with an explicit running min rather than an early ``break``, so the
        selection rule is stated in code as an ordering rule -- symmetric
        with what a reader of the pre-ruling running-max version would have
        seen -- rather than as an artifact of S3's iteration order.
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

        Parameters
        ----------
        model : str or None
            ``[]`` is returned immediately when this is ``None`` -- see
            ``ReplicateAddress.model``'s tag-only-read note.
        tag : str
            UNUSED here -- `tag` is the LOCAL store's key dimension (see the
            class docstring's key shape, which has no `tag` in it at all).
            Accepted purely for interface symmetry with
            ``LocalResultsStore.list_seeds``/``ResultsStore.list_seeds``, so
            a caller can pass one (`tag`, `info`) pair to either backend
            through the same call shape without branching on which backend
            it got back from ``resolve_store``.
        info : str
            Only seeds with at least one logged run for this exact `info`
            are returned.

        Returns
        -------
        list of int
            Sorted, distinct seeds parsed out of every key under
            ``f"{log_prefix}/{model}/"`` whose (:func:`_parse_log_entry`)
            `info` component matches. A seed re-collected more than once
            (multiple logged runs) still contributes exactly ONE entry --
            this counts DISTINCT seeds, not log objects, matching
            ``ReplicateHarness.summarize``'s "number of distinct seeds with
            at least one logged run" replicate count.
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
    """Resolves which ``ResultsStore`` backend `results_dir` should use.

    Reads ``SMOLBENCH_RESULTS_S3``/``SMOLBENCH_RESULTS_S3_REGION`` at CALL
    time (see the module docstring's "Env contract" section) and performs
    the following steps IN THIS ORDER -- the order itself is load-bearing,
    not incidental:

    1. If ``SMOLBENCH_RESULTS_S3`` is unset, empty, or whitespace-only,
       return ``LocalResultsStore(results_dir, prefix)`` immediately.
    2. Otherwise PARSE the URI and raise ``ValueError`` on anything
       malformed -- BEFORE the repo-anchor check in step 3. Validating the
       URI first means a typo'd env var always fails loudly, at the first
       call that resolves a store. The alternative ordering (anchor check
       first) would let a malformed URI fall back SILENTLY to a local write
       for any ``results_dir`` that happens not to be repo-anchored, which
       is the dangerous direction: a run believing it wrote to S3 while its
       results only ever landed on an ephemeral box's local disk, discovered
       only after that box (and the results with it) is gone.
    3. Check whether ``results_dir`` resolves under ``repo_root()``
       (``Path.relative_to``, which raises ``ValueError`` when it does not).
       If it does not, log at INFO that ``SMOLBENCH_RESULTS_S3`` is set but
       this directory is not repo-anchored, and return
       ``LocalResultsStore(results_dir, prefix)``. This is the HERMETICITY
       PROPERTY documented in the module docstring: ``pytest``'s
       ``tmp_path`` fixtures are always outside the repo checkout, so the
       offline test suite keeps using the local store even when a
       developer's shell exports ``SMOLBENCH_RESULTS_S3`` for unrelated
       interactive work. No test needs to unset the variable to stay
       hermetic.
    4. Derive this experiment's log path segment via
       :func:`experiment_name` (which re-derives the same repo-relative
       path computed in step 3 -- a second, cheap ``Path.relative_to`` call
       rather than threading the already-computed value through, so each
       function stays self-contained; see :func:`main`'s docstring for the
       same accepted-duplication rationale elsewhere in this module).
    5. Resolve the region: ``SMOLBENCH_RESULTS_S3_REGION``, else
       ``AWS_REGION``, else ``None``.
    6. Return the resulting ``S3ResultsStore``.

    Parameters
    ----------
    results_dir : Path
        An experiment's results directory, e.g.
        ``InductionExperiment.results_dir``. Does not need to exist --
        resolved with plain ``Path.resolve()`` (NOT ``strict=True``), since
        an S3-first run's LOCAL results directory legitimately may never be
        created at all.
    prefix : str, optional
        The harness's namespace prefix (e.g. ``"one_hop_"``, forwarded
        verbatim from ``ReplicateHarness.prefix``). Threaded through to
        whichever store is returned: it becomes ``LocalResultsStore.prefix``
        on the local path (unchanged from before this parameter existed),
        or is folded into ``S3ResultsStore.experiment`` via
        :func:`experiment_name` on the S3 path. Defaults to ``""``.

    Returns
    -------
    ResultsStore
        A ``LocalResultsStore`` or ``S3ResultsStore`` per the steps above.

    Raises
    ------
    ValueError
        ``SMOLBENCH_RESULTS_S3`` is set to something that does not parse as
        ``s3://<bucket>[/<prefix>]`` -- see :func:`parse_s3_uri` for the
        exact rules (step 2).
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
    """Extracts a whole-object MD5 hex digest from an S3 ``ETag`` value.

    Parameters
    ----------
    etag : str or None
        The raw ``ETag`` field from a ``list_objects_v2`` listing entry
        (``obj.get("ETag")``), e.g. ``'"d41d8cd98f00b204e9800998ecf8427e"'``
        -- S3 wraps ETags in literal double quotes -- or ``None``/absent
        when the listing entry carries no ``ETag`` at all.

    Returns
    -------
    str or None
        The bare hex digest with the surrounding quotes stripped, IFF
        `etag` encodes a single-part upload's whole-object MD5. ``None``
        when `etag` is missing/falsy, or when it is a MULTIPART ETag -- S3
        forms those as ``<hex>-<partcount>``, never a valid MD5 of the
        object's actual bytes, identifiable by a literal ``"-"`` in the
        unquoted value. A ``None`` return means "cannot verify this
        object's identity from its ETag alone"; callers must treat that as
        "assume different" (download), never as "assume same" (skip).
    """
    if not etag:
        return None
    unquoted = etag.strip('"')
    if "-" in unquoted:
        return None  # multipart ETag: "<hex>-<partcount>", not a whole-object MD5
    return unquoted


def _resolve_download_path(resolved_dir: Path, rel: str, key: str) -> Path:
    """Joins `rel` under the already-resolved `resolved_dir`, refusing traversal.

    Parameters
    ----------
    resolved_dir : Path
        ``results_dir.resolve()`` -- the directory every downloaded file
        must land strictly inside.
    rel : str
        The LOCAL destination path, relative to `resolved_dir` -- for
        :func:`sync_down`, the ``{prefix}{tag}_{info}/rep_{seed}.yaml``
        path its (model, tag) mapping and the log entry's parsed (seed,
        info) together determine. Named `rel` (and still validated, rather
        than trusted outright) because its `info`/`seed` components trace
        back to an S3 KEY -- see :func:`_parse_log_entry` -- and this
        module's own writers are not the only thing that can ever place an
        object under a listed prefix.
    key : str
        The full S3 key `rel` was derived from. Named in the raised error
        (not just the resolved local path) because the KEY is what an
        operator has to go find and delete in S3 to stop this recurring;
        the refused local path was never created in the first place.

    Returns
    -------
    Path
        The fully resolved local destination for `rel`, guaranteed (by the
        check below) to lie strictly inside `resolved_dir`.

    Raises
    ------
    ValueError
        The resolved destination equals `resolved_dir` itself (not a valid
        destination -- this function is only ever asked to place a FILE),
        or lies outside `resolved_dir` entirely (a ``".."``-laden path
        walking out of the results tree). Raised BEFORE the caller creates
        any parent directory or writes any byte, so a refused key leaves no
        trace on disk.
    """
    candidate = (resolved_dir / rel).resolve()
    if candidate == resolved_dir or not candidate.is_relative_to(resolved_dir):
        raise ValueError(
            f"sync_down: refusing S3 key {key!r}: resolves to {candidate}, "
            f"outside results_dir {resolved_dir}"
        )
    return candidate


def sync_down(results_dir: Path, tags: Mapping[str, str], prefix: str = "") -> int:
    """Translates an S3-backed experiment's log into the local analysis layout.

    The analysis layer (``notebooks/*/power_analysis.py`` and the figure
    scripts) reads a LOCAL results tree off disk and is deliberately not
    being ported onto ``ResultsStore`` -- see the module docstring's "No
    local write-through when S3 is active" section. This function is the
    bridge: for every (model, seed, info) under `results_dir`'s resolved S3
    log, it downloads the EARLIEST logged run and writes it to the local path
    a ``LocalResultsStore`` would use for that replicate.

    This is a TRANSLATION, not a mirror -- see the module docstring's
    "``sync_down`` TRANSLATES the S3 log into the local layout" section for
    why: the S3 layout no longer has any per-key correspondence to the local
    one, so the LOCAL directory a downloaded run lands in comes from `tags`
    (the model's configured archetype tag), not from anything in the S3 key
    itself.

    THIS IS STILL A ONE-WAY, DESTRUCTIVE OPERATION in the direction it
    copies -- see the module docstring's section of that name. It writes S3
    -> local only, overwriting whatever is on disk with the log's earliest
    run; it never appends to (or otherwise touches) the S3 log. A
    local-only edit (e.g. a local ``scripts/regrade.py --write`` regrade) is
    silently destroyed by the next call, and under earliest-wins no
    re-append to S3 can protect it either (the module docstring's regrade
    sequence).

    Parameters
    ----------
    results_dir : Path
        The local results directory to populate. Must resolve (per
        :func:`resolve_store`) to an ``S3ResultsStore`` with a non-empty
        ``log_prefix`` -- i.e. ``SMOLBENCH_RESULTS_S3`` must be set,
        `results_dir` must be under ``repo_root()``, and the resulting
        ``log_prefix`` must not be empty (see Raises).
    tags : Mapping[str, str]
        ``{model: tag}`` -- an experiment's ``archetype_tags``. This is the
        one thing the S3 log cannot supply on its own (a log key names a
        model, never a tag), which is exactly why
        ``ReplicateHarness.sync_down()`` -- which already has this mapping
        in hand -- is the PRIMARY way to call this function; the
        module-level CLI (:func:`main`) exists for callers that have to
        re-type the mapping by hand.
    prefix : str, optional
        Namespace prefix on the local directory names being written
        (forwarded to :func:`experiment_name` for resolving the store, and
        to each downloaded replicate's local directory name,
        ``f"{prefix}{tag}_{info}"``). Defaults to ``""``.

    Returns
    -------
    int
        The number of objects actually DOWNLOADED, summed across every
        `tags` entry. Objects skipped because an identical local copy
        already exists (see Notes) are not counted.

    Raises
    ------
    RuntimeError
        ``resolve_store(results_dir, prefix)`` resolved to a
        ``LocalResultsStore`` instead of an ``S3ResultsStore``, for one of
        exactly two reasons (named explicitly in the message so the caller
        does not have to re-derive which applies): ``SMOLBENCH_RESULTS_S3``
        is unset/empty, or `results_dir` is not under ``repo_root()``.
    ValueError
        Either of two distinct integrity guards tripped:

        - The resolved store's ``log_prefix`` is ``""``: syncing would list
          and mirror the ENTIRE bucket into `results_dir` rather than one
          experiment's slice of it -- refused outright rather than silently
          pulling down everything anyone ever put in that bucket.
        - A downloaded entry's computed local destination, once stripped
          and resolved, lies OUTSIDE `results_dir` (see
          :func:`_resolve_download_path`). The message names the offending
          S3 key.

    Notes
    -----
    For each ``model, tag`` in `tags`, this function paginates
    ``f"{log_prefix}/{model}/"`` and parses every listed key with
    :func:`_parse_log_entry` into ``(seed, info, run_ts)``, keeping only the
    entry with the LEXICOGRAPHICALLY MINIMUM `run_ts` per ``(seed, info)``
    -- i.e. the earliest logged run, exactly as ``S3ResultsStore.load_marks``
    resolves it (user ruling 2026-08-16; both functions MUST agree, or a
    synced tree and a direct load would silently fork the analysis). A key
    that does not match the expected shape (stray, hand-placed, or predating
    this key scheme) is silently skipped, not downloaded.

    A local file is SKIPPED (not re-downloaded) only when ALL of: (a) it
    already exists; (b) the S3 object's ``ETag``, read directly off the
    listing entry (no extra ``head_object`` call per key -- ``list_objects_
    v2`` already returns it alongside ``Size``), decodes to a single-part
    whole-object MD5 (see :func:`_etag_md5` -- a MULTIPART upload's ETag has
    the form ``<hex>-<partcount>`` and can never equal a plain MD5); and (c)
    that MD5 equals ``hashlib.md5`` of the local file's actual bytes. A
    missing local file, an unverifiable/absent ``ETag``, or a digest
    mismatch all fall through to "download" -- this function never treats
    two objects as identical without positive evidence.

    A size-only comparison would be UNSOUND for this workload:
    ``scripts/regrade.py --write`` rewrites a replicate YAML's ``score``
    field in place, and a ``1 -> 0`` flip is byte-length-preserving (same
    total character count, different content), so a size-only check would
    skip the re-download and let a stale, since-corrected verdict silently
    survive a sync that was supposed to refresh it.

    ``hashlib.md5(..., usedforsecurity=False)`` is used throughout: this
    hash is an INTEGRITY check against S3's own content identifier, never a
    security primitive, and the explicit flag keeps the call from being
    rejected on a FIPS-configured Python build that disables MD5 for
    security use by default.

    ACCEPTED COST: any object uploaded as a multipart transfer carries a
    ``<hex>-<partcount>`` ETag that can never match a plain MD5, so such
    objects re-download on EVERY ``sync_down`` call, indefinitely -- there
    is no way to verify them cheaply from the listing alone. This is a
    deliberate correctness-over-bandwidth trade: the alternative is the
    silent stale-verdict bug described above.

    Every downloaded entry's local destination is validated (via
    :func:`_resolve_download_path`) to resolve strictly inside
    `results_dir` BEFORE any parent directory is created or any byte is
    written.
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
        # Per (seed, info): (run_ts, key, etag) of the EARLIEST run seen so
        # far -- the selection rule is user-ruled (2026-08-16, "use the
        # earliest results to keep pass@1") and must match load_marks
        # exactly; a sync_down that resolved a different run than a direct
        # load would silently fork the analysis. A dict keyed on
        # (seed, info) is the natural shape for "keep only the winner of a
        # running min over run_ts" -- no separate grouping/sorting pass is
        # needed, since the running-min update is O(1) per listed key.
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
            # F5 guard FIRST: validate before touching the filesystem at
            # all, so a refused entry leaves no trace (no mkdir, no partial
            # write, not even a stat/exists call against a bogus path).
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
    """CLI entry point: syncs one results directory down from its S3 log.

    ::

        python -m smolbench.evals.results_store <results_dir> \\
            --tag model=tag [--tag model=tag ...] [--prefix one_hop_]

    ``ReplicateHarness.sync_down()`` is the PRIMARY way to bring an
    S3-backed experiment's results onto local disk -- a harness already has
    the ``{model: tag}`` mapping (``archetype_tags``) in hand. This CLI
    exists for out-of-notebook use, where that mapping has to be re-typed by
    hand as repeated ``--tag`` flags.

    Parameters
    ----------
    argv : Sequence[str] or None
        Argument vector to parse, excluding the program name -- forwarded to
        ``argparse.ArgumentParser.parse_args``. ``None`` (the default) makes
        argparse read ``sys.argv[1:]``, i.e. normal CLI invocation; a caller
        may pass an explicit list instead (e.g. from a test).

    Returns
    -------
    int
        ``0`` on success. A malformed ``--tag`` value (no ``"="``), or any
        other argparse-level problem, calls ``parser.error(...)``, which
        prints a usage message and raises ``SystemExit(2)`` -- that
        propagates rather than being caught here.

    Notes
    -----
    Each ``--tag`` value is split on the FIRST ``"="`` into ``(model, tag)``
    via ``str.partition``, so a model id or tag containing further ``"="``
    characters is handled unambiguously (only the first one is the
    delimiter). Later ``--tag`` entries for the same model silently
    OVERWRITE earlier ones in the resulting mapping (an ordinary ``dict``
    build), matching how a repeated CLI flag is conventionally read.

    Prints one line naming `results_dir`, the number of objects downloaded,
    and the resolved store's :meth:`ResultsStore.describe`, e.g.::

        notebooks/periodic_moe/results: 42 downloaded from s3://my-bucket/archive/periodic_moe

    ``resolve_store`` is called once more here purely to obtain that
    description string; :func:`sync_down` performs its own independent
    resolution internally. The duplicate resolution is cheap (an env-var
    read and some string joins, no I/O of its own) and keeps each
    function's env-read self-contained per the module docstring's
    call-time contract, rather than threading a pre-resolved store through
    ``sync_down``'s public signature.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m smolbench.evals.results_store",
        description=(
            "Syncs one results directory down from its S3-backed experiment "
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
        help="model=tag mapping entry (an archetype_tags item); repeatable.",
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
