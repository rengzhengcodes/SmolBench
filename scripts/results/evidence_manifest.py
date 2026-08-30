#!/usr/bin/env python
"""Build and verify ``EVIDENCE.json``, the manifest that pins what a writeup cites.

Each results directory can hold an ``EVIDENCE.json`` file. That file lists
every artifact a writeup relies on and pins each one by its sha256 hash.
This module builds the file, then verifies it later, so a missing or
changed artifact is easy to find.

``notebooks/*/results/`` is gitignored wholesale (see ``.gitignore:235``).
Every tracked file under it needs a manual ``git add -f``, so nothing
forces a writeup's cited artifacts into git, and scratch files a writeup
cites can end up preserved only as tracked tarballs under
``notebooks/deduction/results/uncommitted_evidence_preserved_2026-08-22/``.
This module turns that class of gap into a test. For each results
directory:

  * ``EVIDENCE.json`` pins every artifact by sha256, including artifacts
    that exist only INSIDE one of the preserved tarballs. The manifest
    addresses these as ``tarball:<tarball-relpath>!<member-path>`` and
    hashes each one by STREAMING the member out of the archive. The tool
    never extracts a file to disk: an extracted scratch tree inside a
    gitignored results directory is how untracked evidence gets born in
    the first place.
  * :func:`verify` re-hashes every pinned reference, then checks
    coverage: every backtick-quoted artifact name in each ``writeup``
    entry must be a whole-path-component suffix of some pinned
    reference, or else carry an explicit ``allowlist`` entry WITH A
    REASON.

Two properties matter and are easy to break by "improving" them:

  * A reference MAY traverse upward with ``..`` -- the real back-filled
    manifests reach up two levels to the preserved tarballs. This module
    has no guard that keeps a reference inside the manifest's own
    directory, by design.
  * :func:`build` is DETERMINISTIC: it never reads a timestamp, iterates
    a set, or depends on ``id()`` order. Rebuilding the same inputs
    produces byte-identical output, so a diff on the manifest always
    means the evidence itself changed.

This module does not judge whether an artifact is the *right* one. It
only checks that the thing a writeup names is pinned and unchanged. A
semantic claim -- for example, that a ``_final_`` name actually holds an
interim raw file -- belongs in an entry's ``note`` field, not here.

Usage
-----
::

    .venv/bin/python scripts/results/evidence_manifest.py verify [dir ...]
    .venv/bin/python scripts/results/evidence_manifest.py build <dir> --spec <spec.json>

With no directories given, ``verify`` walks every ``EVIDENCE.json`` under
``notebooks/*/results/`` and exits non-zero if any manifest fails.

Notes
-----
Load this module by file path. ``scripts/`` is not an importable
package, so callers reach this module through
``importlib.util.spec_from_file_location``/``module_from_spec``.
Register the module in ``sys.modules`` BEFORE calling ``exec_module``.
This is importlib's own documented recipe, and the pattern the tests use.

This step is required, not optional. Under
``from __future__ import annotations``, every annotation is a string.
``@dataclass`` -- :class:`VerifyResult` is one -- resolves each string
through ``sys.modules[cls.__module__]``. For an unregistered module,
that lookup returns ``None``, and ``dataclasses._is_type`` raises
``AttributeError: 'NoneType' object has no attribute '__dict__'``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

MANIFEST_NAME = "EVIDENCE.json"
SCHEMA = "smolbench-evidence-manifest/1"

#: The closed role vocabulary. A role states WHY an artifact is in the
#: package. That is what makes a missing ``estimator`` or
#: ``preregistration`` entry visible as an absence. The set stays closed
#: on purpose, so a typo fails loudly instead of silently inventing a
#: role nobody greps for.
ROLES = ("writeup", "analysis_input", "raw", "estimator", "preregistration",
         "config", "gate", "teardown", "log", "other")

#: Suffixes that make a backtick-quoted token look like an artifact worth
#: gating. The list stays narrow on purpose: the scanner runs over human
#: prose, and a false positive costs a human an allowlist entry. The bar
#: is "ends like a file we would ever commit".
CITED_SUFFIXES = (".json", ".jsonl", ".gz", ".yaml", ".yml", ".txt", ".md",
                  ".sh", ".py")

#: Suffixes the repo gate treats as writeups (tests import this).
WRITEUP_SUFFIXES = (".md", ".txt")

REPO = Path(__file__).resolve().parents[2]

#: Marker prefix for a reference into a preserved tarball.
TARBALL_PREFIX = "tarball:"

#: Hashing chunk size. 1 MiB keeps a large gzipped raw file off the heap,
#: while still reading one block at a time. These packages pin whole run
#: dumps, not just summaries.
CHUNK_BYTES = 1 << 20

_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")

#: A citation token: backtick-delimited, and it never spans a newline.
#: The character class excludes backticks, so a left-to-right scan pairs
#: the delimiters without any backtracking heuristics.
_BACKTICKED = re.compile(r"`([^`\n]+)`")


class ResolutionError(FileNotFoundError):
    """Raised when a manifest reference does not resolve to a readable file.

    This subclasses :class:`FileNotFoundError`. That lets :func:`build`
    meet its documented contract ("raises FileNotFoundError if an entry
    does not resolve") by simple propagation. :func:`verify` catches this
    error and folds the already-formatted message into its failure
    census.

    Notes
    -----
    Each message is built complete, in the form ``"<relpath>: missing
    tarball member: <member>"``. Both callers report the same wording.
    """


# --------------------------------------------------------------------------
# reference grammar
# --------------------------------------------------------------------------

def _split_reference(relpath: str) -> tuple[str, str | None]:
    """Split a manifest ``relpath`` into its on-disk path and tarball member.

    Parameters
    ----------
    relpath : str
        Either a plain POSIX-style path relative to the manifest's own
        directory (``..`` is allowed and used in practice), or a tarball
        reference ``tarball:<tarball-relpath>!<member-path>``.

    Returns
    -------
    tuple of (str, str or None)
        ``(path, None)`` for a plain reference; ``(tarball_relpath, member)``
        for a tarball reference. Both components come back verbatim, with
        no normalisation -- the manifest's own spelling is what gets
        re-verified.

    Raises
    ------
    ValueError
        A ``tarball:`` reference has no ``!`` separator, or either side of
        the separator is empty.

    Notes
    -----
    The split happens on the FIRST ``!``. A member path may contain
    ``!``; a tarball path effectively cannot. If a tarball path did
    contain one, this function could not address it. That limitation is
    accepted rather than worked around: an escape syntax nobody uses is a
    second grammar to get wrong.
    """
    if not relpath.startswith(TARBALL_PREFIX):
        return relpath, None
    body = relpath[len(TARBALL_PREFIX):]
    tar_relpath, sep, member = body.partition("!")
    if not sep or not tar_relpath or not member:
        raise ValueError(
            f"malformed tarball reference (want "
            f"'{TARBALL_PREFIX}<tarball>!<member>'): {relpath!r}")
    return tar_relpath, member


def _candidates(relpath: str) -> list[str]:
    """Return the path strings a citation may be matched against.

    A plain reference offers one candidate: itself. A tarball reference
    offers TWO: the tarball's own path, since a writeup may legitimately
    cite the preserved archive, and the member path inside it. The
    member path is how a citation of an artifact that exists only inside
    a preserved tarball gets covered.

    Parameters
    ----------
    relpath : str
        A schema-valid manifest reference.

    Returns
    -------
    list of str
        One or two candidate paths, in a fixed order (tarball, then member).
    """
    path, member = _split_reference(relpath)
    return [path] if member is None else [path, member]


@contextmanager
def _open_reference(manifest_dir: Path, relpath: str) -> Iterator[IO[bytes]]:
    """Open a manifest reference for binary reading, without extracting it.

    Parameters
    ----------
    manifest_dir : Path
        Directory the ``EVIDENCE.json`` belongs to; all references are
        resolved relative to it.
    relpath : str
        A schema-valid reference (see :func:`_split_reference`).

    Yields
    ------
    IO[bytes]
        A readable binary stream, closed on exit.

    Raises
    ------
    ResolutionError
        The plain file, the tarball, or the tarball member is absent, or
        is not a regular file.
    ValueError
        The reference is a malformed ``tarball:`` reference.
    tarfile.TarError
        The archive exists but this function cannot read it as a gzipped
        tar.

    Notes
    -----
    This function opens the archive once per reference. It does not
    cache the archive across a whole :func:`verify` pass. That costs a
    re-open when several entries name the same tarball, but it also
    guarantees that no archive handle outlives the entry that needed it
    -- the pass holds no state that could go stale. The member streams
    via ``extractfile``; this function never calls
    ``extract``/``extractall``, so the filesystem stays byte-for-byte as
    it was found.
    """
    tar_relpath, member = _split_reference(relpath)
    target = manifest_dir / tar_relpath

    # Plain reference: the common case, one stat and one open.
    if member is None:
        if not target.is_file():
            detail = ("missing file (not a regular file)" if target.exists()
                      else "missing file")
            raise ResolutionError(f"{relpath}: {detail}: {tar_relpath}")
        with target.open("rb") as handle:
            yield handle
        return

    # Tarball reference: the archive must exist before the member can.
    if not target.is_file():
        raise ResolutionError(f"{relpath}: missing tarball: {tar_relpath}")
    with tarfile.open(target, "r:gz") as archive:
        try:
            info = archive.getmember(member)
        except KeyError:
            raise ResolutionError(
                f"{relpath}: missing tarball member: {member}") from None
        # A directory, symlink, or hardlink member reports the same
        # "missing tarball member" phrase, plus a parenthetical. What is
        # missing is the regular file the manifest claims to have pinned.
        stream = archive.extractfile(info) if info.isfile() else None
        if stream is None:
            raise ResolutionError(
                f"{relpath}: missing tarball member (not a regular file): "
                f"{member}")
        with stream:
            yield stream


def _sha256_of_reference(manifest_dir: Path, relpath: str) -> str:
    """Stream a reference and return its sha256 as 64 lowercase hex chars.

    Parameters
    ----------
    manifest_dir : Path
        Directory the manifest belongs to.
    relpath : str
        A schema-valid reference.

    Returns
    -------
    str
        Lowercase hex digest.

    Raises
    ------
    ResolutionError
        The reference does not resolve (see :func:`_open_reference`).

    Notes
    -----
    This function streams the reference in :data:`CHUNK_BYTES` blocks.
    These packages pin whole run dumps. A manifest tool that needs each
    artifact to fit in RAM would simply never run on the ones that
    matter most.
    """
    digest = hashlib.sha256()
    with _open_reference(manifest_dir, relpath) as stream:
        for chunk in iter(lambda: stream.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------
# the scanner
# --------------------------------------------------------------------------

def cited_artifacts(text: str) -> list[str]:
    """Extract the artifact filenames a writeup cites in backticks.

    This function is conservative and fully deterministic. It recognises
    only backtick-quoted, whitespace-free tokens that end in a known
    artifact suffix. Anything cleverer -- stripping punctuation,
    splitting on ``/``, lowercasing -- would trade a hard, explainable
    rule for a heuristic a human then has to argue with. The cost of a
    miss here is small: a real citation goes ungated, and the writeup's
    author can fix it by writing the name the way every other citation
    in the corpus already appears.

    Parameters
    ----------
    text : str
        Raw writeup text (Markdown or plain text).

    Returns
    -------
    list of str
        Sorted, deduplicated citation tokens, verbatim as written.

    Notes
    -----
    A token never spans a newline, so an unmatched backtick cannot
    swallow the rest of the document. This function rejects any token
    that still contains whitespace after stripping. That rule keeps
    prose like ``sha256(pool_analyze.py) = 3824a4`` from being read as a
    citation.

    Examples
    --------
    >>> cited_artifacts("the raw is `all_rows.jsonl`, run `--flag` twice")
    ['all_rows.jsonl']
    >>> cited_artifacts("`b.json` and `a.json` and `a.json`")
    ['a.json', 'b.json']
    """
    found: set[str] = set()
    for raw in _BACKTICKED.findall(text):
        token = raw.strip()
        if not token or any(ch.isspace() for ch in token):
            continue
        if token.endswith(CITED_SUFFIXES):
            found.add(token)
    return sorted(found)


def covers(cited: str, entry_path: str) -> bool:
    """Is ``cited`` a whole-path-component suffix of ``entry_path``?

    This check is the load-bearing subtlety of the whole mechanism. A
    citation of ``all_rows.jsonl`` IS satisfied by an entry
    ``sub/all_rows.jsonl`` -- the same file, addressed from a different
    place. It is NOT satisfied by ``originals_all_rows.jsonl``, which
    merely ends with the same bytes and names a DIFFERENT artifact.

    Parameters
    ----------
    cited : str
        Citation token, as written in the writeup.
    entry_path : str
        A candidate path from the manifest (a plain relpath, or a tarball's
        path or member path).

    Returns
    -------
    bool
        True iff the trailing ``/``-separated components of ``entry_path``
        equal all components of ``cited``.

    Notes
    -----
    This check is asymmetric by design. A longer citation is never
    covered by a shorter entry path: ``r6/backup/all_rows.jsonl`` is not
    covered by ``backup/all_rows.jsonl``. The writeup made the more
    specific claim, so the manifest must meet it.

    Examples
    --------
    >>> covers("all_rows.jsonl", "sub/all_rows.jsonl")
    True
    >>> covers("all_rows.jsonl", "originals_all_rows.jsonl")
    False
    >>> covers("r6/backup/all_rows.jsonl", "backup/all_rows.jsonl")
    False
    """
    cited_parts = cited.split("/")
    entry_parts = entry_path.split("/")
    if len(cited_parts) > len(entry_parts):
        return False
    return entry_parts[len(entry_parts) - len(cited_parts):] == cited_parts


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def build(manifest_dir: str | Path,
          entries: Iterable[Mapping[str, Any]],
          allowlist: Iterable[Mapping[str, Any]] = (),
          *,
          note: str | None = None,
          write: bool = True) -> dict[str, Any]:
    """Hash every listed artifact and write the directory's ``EVIDENCE.json``.

    Parameters
    ----------
    manifest_dir : str or Path
        Directory the manifest belongs to. Every entry's ``relpath`` is
        resolved relative to it (upward ``..`` traversal is legitimate).
    entries : iterable of mapping
        Each mapping needs ``relpath`` (non-empty str) and ``role`` (one of
        :data:`ROLES`), and may carry ``note`` (str) and ``sha256`` (str). A
        supplied ``sha256`` is CHECKED, never trusted.
    allowlist : iterable of mapping, optional
        Each mapping needs non-empty str ``name`` and ``reason``: a citation
        that no entry covers, plus the reason that is acceptable.
    note : str, optional
        Free text describing the package; the key is omitted when None.
    write : bool, default True
        Write ``manifest_dir/EVIDENCE.json``. False computes and returns the
        manifest without touching the filesystem.

    Returns
    -------
    dict
        The manifest, with keys in the order ``schema, note?, entries,
        allowlist`` and each entry in the order ``relpath, sha256, role,
        note?``.

    Raises
    ------
    FileNotFoundError
        An entry does not resolve: a missing plain file, a missing
        tarball, or a missing tarball member. A manifest of ghosts is
        worse than no manifest, so this function writes nothing in that
        case.
    ValueError
        A missing or empty ``relpath``; a ``role`` outside :data:`ROLES`;
        a malformed ``tarball:`` reference; a non-str ``note``; a
        supplied ``sha256`` that disagrees with the computed one; or an
        allowlist entry missing ``name`` or ``reason``, or with an empty
        one.

    Notes
    -----
    This function keeps caller order for both lists. Grouping entries by
    role or by story is an editorial choice, and sorting would destroy
    it. Combined with the absence of any timestamp, that keeps rebuilds
    byte-identical, so a diff on ``EVIDENCE.json`` always means the
    evidence itself moved.

    This function does NOT check citation coverage. ``build()`` states
    what exists; only :func:`verify` judges whether the writeups' claims
    are met. That split lets a manifest get built first, with the gaps
    read off afterwards.
    """
    mdir = Path(manifest_dir)

    if note is not None and not isinstance(note, str):
        raise ValueError(f"note must be a string, got {type(note).__name__}")

    # Check the allowlist first: it costs no I/O, so a typo there fails
    # before this function streams hundreds of megabytes of raw files.
    checked_allowlist: list[dict[str, str]] = []
    for i, raw in enumerate(allowlist):
        name = raw.get("name")
        reason = raw.get("reason")
        if not isinstance(name, str) or not name:
            raise ValueError(f"allowlist {i}: name is missing or empty: {raw!r}")
        if not isinstance(reason, str) or not reason:
            raise ValueError(
                f"allowlist {i}: reason is missing or empty for {name!r} -- an "
                "allowlist entry with no reason is an undocumented hole")
        checked_allowlist.append({"name": name, "reason": reason})

    # For each entry, validate the cheap schema first, then resolve and
    # hash it. This order reports a bad role as a ValueError, instead of
    # whatever the filesystem happens to say about its path.
    checked_entries: list[dict[str, Any]] = []
    for i, raw in enumerate(entries):
        relpath = raw.get("relpath")
        if not isinstance(relpath, str) or not relpath:
            raise ValueError(f"entry {i}: relpath is missing or empty: {raw!r}")
        role = raw.get("role")
        if role not in ROLES:
            raise ValueError(
                f"entry {i} ({relpath}): bad role: {role!r} -- expected one of "
                f"{', '.join(ROLES)}")
        entry_note = raw.get("note")
        if entry_note is not None and not isinstance(entry_note, str):
            raise ValueError(f"entry {i} ({relpath}): note must be a string")
        _split_reference(relpath)  # ValueError on a malformed tarball ref

        digest = _sha256_of_reference(mdir, relpath)
        supplied = raw.get("sha256")
        if supplied is not None and supplied != digest:
            raise ValueError(
                f"entry {i} ({relpath}): supplied sha256 {supplied} disagrees "
                f"with computed {digest} -- refusing to bless a stale hash")

        entry: dict[str, Any] = {"relpath": relpath, "sha256": digest,
                                 "role": role}
        if entry_note is not None:
            entry["note"] = entry_note
        checked_entries.append(entry)

    manifest: dict[str, Any] = {"schema": SCHEMA}
    if note is not None:
        manifest["note"] = note
    manifest["entries"] = checked_entries
    manifest["allowlist"] = checked_allowlist

    if write:
        # newline="\n" pins the exact bytes written. The determinism
        # guarantee covers the FILE, not just the dict.
        (mdir / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8", newline="\n")
    return manifest


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------

@dataclass
class VerifyResult:
    """Outcome of verifying one ``EVIDENCE.json``.

    Attributes
    ----------
    ok : bool
        ``not failures``.
    manifest_dir : Path
        The directory that was verified, as the caller named it.
    n_entries : int
        Entries the manifest LISTS, including any the schema check
        rejected. The census reports the file; the failures report the
        defects.
    roles : dict of str to int
        Counts per role, over schema-valid entries only. A role with no
        entries is absent from this dict rather than set to zero.
    allowlist : list of dict
        The schema-valid allowlist entries, as stored.
    citations : dict of str to list of str
        Writeup relpath -> sorted citation tokens found in it. Present
        for every ``writeup`` entry that resolved, whether or not all of
        its citations were covered.
    failures : list of str
        Human-readable defects, in check order. An empty list means the
        manifest verified.
    """

    ok: bool
    manifest_dir: Path
    n_entries: int
    roles: dict[str, int]
    allowlist: list[dict]
    citations: dict[str, list[str]]
    failures: list[str]


def _check_entry_schema(index: int, entry: Any, failures: list[str]) -> bool:
    """Validate one raw manifest entry, appending any defects to ``failures``.

    Parameters
    ----------
    index : int
        Position in ``entries``, used to name the entry in messages (the
        ``relpath`` may itself be the missing field).
    entry : Any
        The decoded JSON value at that position.
    failures : list of str
        Accumulator, appended to in place.

    Returns
    -------
    bool
        True if the entry is well formed enough to resolve and to serve
        as a coverage candidate.

    Notes
    -----
    This function runs every check before it returns. A hand-edited
    entry therefore reports all of its defects in one pass, instead of
    one defect per re-run.
    """
    if not isinstance(entry, Mapping):
        failures.append(f"entry {index}: not an object: {entry!r}")
        return False

    ok = True
    relpath = entry.get("relpath")
    if not isinstance(relpath, str) or not relpath:
        failures.append(f"entry {index}: relpath is missing or empty: "
                        f"{relpath!r}")
        ok = False

    role = entry.get("role")
    if role not in ROLES:
        failures.append(f"entry {index}: bad role: {role!r} "
                        f"(relpath={relpath!r})")
        ok = False

    digest = entry.get("sha256")
    if not isinstance(digest, str) or not _HEX64.match(digest):
        failures.append(f"entry {index}: sha256 is not 64 lowercase hex: "
                        f"{digest!r} (relpath={relpath!r})")
        ok = False

    note = entry.get("note")
    if note is not None and not isinstance(note, str):
        failures.append(f"entry {index}: note is not a string: {note!r} "
                        f"(relpath={relpath!r})")
        ok = False

    if ok:
        try:
            _split_reference(relpath)  # a str by now: checked just above
        except ValueError as exc:
            failures.append(f"entry {index}: {exc}")
            ok = False
    return ok


def _check_allowlist_schema(raw_allowlist: Any,
                            failures: list[str]) -> list[dict]:
    """Validate the manifest's allowlist, returning its usable entries.

    Parameters
    ----------
    raw_allowlist : Any
        The decoded ``allowlist`` value (absent is treated as empty).
    failures : list of str
        Accumulator, appended to in place.

    Returns
    -------
    list of dict
        Well-formed ``{"name": ..., "reason": ...}`` entries, in file order.

    Notes
    -----
    This function reports AND drops any entry whose ``reason`` is
    missing. Such an entry must not keep working as an escape hatch --
    otherwise the cheapest way to silence a coverage failure would be to
    delete its justification.
    """
    if not isinstance(raw_allowlist, list):
        failures.append(f"allowlist: not a list: {raw_allowlist!r}")
        return []

    usable: list[dict] = []
    for i, item in enumerate(raw_allowlist):
        if not isinstance(item, Mapping):
            failures.append(f"allowlist {i}: not an object: {item!r}")
            continue
        name = item.get("name")
        reason = item.get("reason")
        ok = True
        if not isinstance(name, str) or not name:
            failures.append(f"allowlist {i}: name is missing or empty: {name!r}")
            ok = False
        if not isinstance(reason, str) or not reason:
            failures.append(f"allowlist {i}: reason is missing or empty "
                            f"(name={name!r})")
            ok = False
        if ok:
            usable.append({"name": name, "reason": reason})
    return usable


def verify(manifest_dir: str | Path) -> VerifyResult:
    """Re-hash a directory's pinned evidence and check its citation coverage.

    Checks, in order: manifest schema; reference resolution; sha256 (by
    streaming); and citation coverage for every ``writeup`` entry.

    Parameters
    ----------
    manifest_dir : str or Path
        Directory holding the ``EVIDENCE.json``.

    Returns
    -------
    VerifyResult
        Census plus failures. This function COLLECTS every defect except
        a missing or unparseable manifest, rather than raising on the
        first one. One run therefore reports the whole state of a
        package, not just its first defect.

    Raises
    ------
    FileNotFoundError
        ``manifest_dir/EVIDENCE.json`` does not exist.
    json.JSONDecodeError
        The manifest is not valid JSON. This error propagates
        deliberately: there is no partial census to report in that
        case.

    Notes
    -----
    This function is read-only. It streams tarball members and never
    extracts them, so the tree stays byte-for-byte as it was found.

    A sha256 mismatch does NOT stop the entry's citation scan. A writeup
    that drifted is exactly the one whose citations most need checking,
    so this function reports the two defects independently.
    """
    mdir = Path(manifest_dir)
    manifest_path = mdir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"no {MANIFEST_NAME} in {mdir}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    failures: list[str] = []

    # ---- check 1: schema -------------------------------------------------
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list):
        failures.append(f"entries: not a list: {raw_entries!r}")
        raw_entries = []
    valid = [e for i, e in enumerate(raw_entries)
             if _check_entry_schema(i, e, failures)]
    allowlist = _check_allowlist_schema(data.get("allowlist", []), failures)

    # Coverage candidates come from every schema-valid entry, whether or
    # not it resolves. A broken tarball is one failure. It must not also
    # cascade into a bogus "cited artifact not covered" for every name
    # it holds.
    candidates: list[str] = []
    for entry in valid:
        candidates.extend(_candidates(entry["relpath"]))
    allowed_names = {a["name"] for a in allowlist}

    roles: dict[str, int] = {}
    citations: dict[str, list[str]] = {}
    for entry in valid:
        relpath = entry["relpath"]
        roles[entry["role"]] = roles.get(entry["role"], 0) + 1

        # ---- check 2+3: resolution, then sha256 --------------------------
        try:
            actual = _sha256_of_reference(mdir, relpath)
        except ResolutionError as exc:
            failures.append(str(exc))
            continue  # nothing further is knowable about this entry
        except (OSError, tarfile.TarError) as exc:
            failures.append(f"{relpath}: unreadable: {exc}")
            continue
        if actual != entry["sha256"]:
            failures.append(f"{relpath}: sha256 mismatch: "
                            f"manifest={entry['sha256']} actual={actual}")

        # ---- check 4: citation coverage (writeups only) ------------------
        if entry["role"] != "writeup":
            continue
        try:
            with _open_reference(mdir, relpath) as stream:
                text = stream.read().decode("utf-8", errors="replace")
        except (ResolutionError, OSError, tarfile.TarError) as exc:
            # Unreachable in practice: this function hashed the file a
            # moment ago. Handled anyway, so a file that changes out
            # from under this run degrades to a failure line.
            failures.append(f"{relpath}: unreadable writeup: {exc}")
            continue
        cited = cited_artifacts(text)
        citations[relpath] = cited
        for name in cited:
            if name in allowed_names:
                continue
            if any(covers(name, candidate) for candidate in candidates):
                continue
            failures.append(f"{relpath}: cited artifact not covered: {name}")

    return VerifyResult(ok=not failures, manifest_dir=mdir,
                        n_entries=len(raw_entries), roles=roles,
                        allowlist=allowlist, citations=citations,
                        failures=failures)


def find_manifests(root: Path | None = None) -> list[Path]:
    """Locate every ``EVIDENCE.json`` under ``notebooks/*/results/``.

    Parameters
    ----------
    root : Path, optional
        Tree to search; defaults to :data:`REPO`.

    Returns
    -------
    list of Path
        Sorted manifest paths, at any depth below a results directory (a
        package under ``results/runs/<name>/`` counts too). An empty
        list is a valid state, not an error.
    """
    base = REPO if root is None else Path(root)
    return sorted(base.glob(f"notebooks/*/results/**/{MANIFEST_NAME}"))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _display_dir(path: Path) -> str:
    """Render a directory relative to :data:`REPO` when it lies inside it."""
    try:
        return path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def _census_lines(result: VerifyResult) -> list[str]:
    """Render the human-readable census for one verified manifest.

    Parameters
    ----------
    result : VerifyResult
        A completed verification.

    Returns
    -------
    list of str
        Report lines (without the FAIL lines, which the caller prints
        unindented so they grep cleanly out of a long run).
    """
    lines = [f"{_display_dir(result.manifest_dir)}: {result.n_entries} entries"]
    if result.roles:
        # Render in ROLES order, not manifest order, so the census of
        # two packages stays diffable against each other.
        lines.append("  roles: " + ", ".join(
            f"{role}={result.roles[role]}" for role in ROLES
            if role in result.roles))
    for item in result.allowlist:
        lines.append(f"  allowlist: {item['name']} -- {item['reason']}")
    for relpath in sorted(result.citations):
        lines.append(f"  writeup {relpath}: "
                     f"{len(result.citations[relpath])} cited artifacts checked")
    return lines


def _cmd_verify(dirs: Sequence[str]) -> int:
    """Verify the named directories, or every manifest in the repo.

    Parameters
    ----------
    dirs : sequence of str
        Directories holding an ``EVIDENCE.json``; empty means
        :func:`find_manifests`.

    Returns
    -------
    int
        0 if every manifest verified, 1 otherwise.
    """
    targets = ([Path(d) for d in dirs] if dirs
               else [p.parent for p in find_manifests()])
    if not targets:
        print(f"nothing to verify: no {MANIFEST_NAME} under "
              "notebooks/*/results/")
        print("OK (0 manifests)")
        return 0

    n_failed = 0
    for target in targets:
        try:
            result = verify(target)
        except FileNotFoundError as exc:
            # A directory named on the command line with no manifest is
            # a user error, not a crash. Report it in the same census
            # shape.
            print(f"FAIL {_display_dir(target)}: {exc}")
            n_failed += 1
            continue
        print("\n".join(_census_lines(result)))
        for failure in result.failures:
            print(f"FAIL {_display_dir(result.manifest_dir)}: {failure}")
        if not result.ok:
            n_failed += 1

    plural = "" if len(targets) == 1 else "s"
    if n_failed:
        print(f"FAILED ({n_failed} of {len(targets)} manifest{plural})")
        return 1
    print(f"OK ({len(targets)} manifest{plural})")
    return 0


def _cmd_build(manifest_dir: str, spec_path: str) -> int:
    """Build one ``EVIDENCE.json`` from a JSON spec file.

    Parameters
    ----------
    manifest_dir : str
        Directory to write the manifest into.
    spec_path : str
        JSON file of the form ``{"note": ..., "entries": [...],
        "allowlist": [...]}``. The spec carries no hashes: they are computed
        here, so a spec can be hand-written and re-run after the evidence
        legitimately changes.

    Returns
    -------
    int
        0. Any defect raises out of :func:`build` instead.
    """
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    manifest = build(manifest_dir,
                     spec.get("entries", []),
                     spec.get("allowlist", []),
                     note=spec.get("note"))
    out = Path(manifest_dir) / MANIFEST_NAME
    print(f"wrote {out}: {len(manifest['entries'])} entries, "
          f"{len(manifest['allowlist'])} allowlist")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point.

    Parameters
    ----------
    argv : list of str, optional
        Argument vector without the program name; defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Process exit status: 0 on success, 1 if any manifest failed to verify.
    """
    parser = argparse.ArgumentParser(
        description="Pin and verify the evidence behind a results writeup.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_verify = sub.add_parser(
        "verify",
        help="re-hash pinned evidence and check citation coverage")
    p_verify.add_argument(
        "dirs", nargs="*", metavar="dir",
        help=(f"directories holding an {MANIFEST_NAME}; default: every one "
              "under notebooks/*/results/"))

    p_build = sub.add_parser(
        "build", help=f"write the {MANIFEST_NAME} for a results directory")
    p_build.add_argument("manifest_dir",
                         help=f"directory to write {MANIFEST_NAME} into")
    p_build.add_argument("--spec", required=True, metavar="spec.json",
                         help="JSON spec: entries (relpath/role/note), "
                              "allowlist (name/reason), optional note")

    args = parser.parse_args(argv)
    if args.command == "verify":
        return _cmd_verify(args.dirs)
    return _cmd_build(args.manifest_dir, args.spec)


if __name__ == "__main__":
    raise SystemExit(main())
