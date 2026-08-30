#!/usr/bin/env python
"""Build and verify ``EVIDENCE.json``, the manifest that pins what a writeup cites.

A results directory's ``EVIDENCE.json`` pins by sha256 every artifact a writeup
relies on. ``notebooks/*/results/`` is gitignored wholesale, so some survive
only inside tracked tarballs under
``notebooks/deduction/results/uncommitted_evidence_preserved_2026-08-22/``;
those are addressed as ``tarball:<tarball-relpath>!<member-path>`` and hashed by
STREAMING the member -- never extracted, since a scratch tree in a gitignored
results directory is how untracked evidence gets born. :func:`verify` re-hashes
every reference, then requires each backtick-quoted artifact name in a
``writeup`` entry to be a whole-path-component suffix of a pinned reference, or
to carry an ``allowlist`` entry WITH A REASON; whether an artifact is the
*right* one is a claim for its ``note``, not for this tool.

Deliberate, and easy to "fix" by mistake: a reference MAY traverse upward with
``..`` (no containment guard), and :func:`build` is DETERMINISTIC, so a diff on
a rebuild means the evidence moved.

Entry points: ``verify [dir ...]`` (no directories = every manifest under
``notebooks/*/results/``; exits non-zero if any fails) and ``build <dir> --spec
<spec.json>``. ``scripts/`` is not an importable package: load this module by
file path and register it in ``sys.modules`` BEFORE ``exec_module``, or the
``@dataclass`` :class:`VerifyResult` raises ``AttributeError`` (under ``from
__future__ import annotations`` dataclasses resolve annotations via
``sys.modules[cls.__module__]``, ``None`` for an unregistered module).
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

#: The closed role vocabulary. A role states WHY an artifact is in the package,
#: which is what makes a missing ``estimator`` or ``preregistration`` entry
#: visible as an absence; closed so a typo fails loudly instead of inventing a
#: role nobody greps for.
ROLES = ("writeup", "analysis_input", "raw", "estimator", "preregistration",
         "config", "gate", "teardown", "log", "other")

#: Suffixes that make a backtick-quoted token look like an artifact worth
#: gating. Narrow on purpose: the scanner runs over human prose, and a false
#: positive costs a human an allowlist entry.
CITED_SUFFIXES = (".json", ".jsonl", ".gz", ".yaml", ".yml", ".txt", ".md",
                  ".sh", ".py")

#: Suffixes the repo gate treats as writeups (tests import this).
WRITEUP_SUFFIXES = (".md", ".txt")

REPO = Path(__file__).resolve().parents[2]

#: Marker prefix for a reference into a preserved tarball.
TARBALL_PREFIX = "tarball:"

#: Hashing chunk size. 1 MiB keeps a large gzipped raw file off the heap;
#: these packages pin whole run dumps, not just summaries.
CHUNK_BYTES = 1 << 20

_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")

#: A citation token: backtick-delimited, never spanning a newline. The character
#: class excludes backticks, so a left-to-right scan pairs the delimiters without
#: backtracking heuristics.
_BACKTICKED = re.compile(r"`([^`\n]+)`")


class ResolutionError(FileNotFoundError):
    """Raised when a manifest reference does not resolve to a readable file.

    Subclasses :class:`FileNotFoundError`, so :func:`build` meets its documented
    contract by propagation while :func:`verify` folds the message into its
    failure census. Messages are built complete, so both callers report
    identical wording.
    """


# --------------------------------------------------------------------------
# reference grammar
# --------------------------------------------------------------------------

def _split_reference(relpath: str) -> tuple[str, str | None]:
    """Split a manifest ``relpath`` into its on-disk path and tarball member.

    Parameters
    ----------
    relpath : str
        POSIX path relative to the manifest's own directory, or
        ``tarball:<tarball>!<member>``, split on the FIRST ``!``: a member may
        contain one, a tarball path effectively cannot, so no escape syntax has
        to be invented.

    Returns
    -------
    tuple of (str, str or None)
        Path and member, verbatim and unnormalised (the manifest's own spelling
        is what gets re-verified); member is ``None`` for a plain reference.

    Raises
    ------
    ValueError
        ``tarball:`` reference with no ``!`` separator, or an empty side.
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

    A plain reference offers itself; a tarball reference offers two, in fixed
    order -- the tarball's own path (a writeup may cite the archive itself) then
    the member path (how an artifact living only inside one gets covered).
    """
    path, member = _split_reference(relpath)
    return [path] if member is None else [path, member]


@contextmanager
def _open_reference(manifest_dir: Path, relpath: str) -> Iterator[IO[bytes]]:
    """Open a manifest reference for binary reading, without extracting it.

    Members stream via ``extractfile``; ``extract``/``extractall`` are never
    called, so the filesystem stays byte-for-byte as found. The archive is
    opened per reference and never cached, so no handle outlives its entry.

    Parameters
    ----------
    relpath : str
        Reference in :func:`_split_reference`'s grammar, resolved against
        ``manifest_dir``.

    Yields
    ------
    IO[bytes]
        Binary stream, closed on exit.

    Raises
    ------
    ResolutionError
        The file, the tarball, or the member is absent or not a regular file.
    ValueError
        Malformed ``tarball:`` reference.
    tarfile.TarError
        The archive is not readable as a gzipped tar.
    """
    tar_relpath, member = _split_reference(relpath)
    target = manifest_dir / tar_relpath

    # Plain reference: one stat and one open.
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
        # A directory, symlink, or hardlink member keeps the "missing tarball
        # member" phrase: what is missing is the regular file the manifest
        # claims to have pinned.
        stream = archive.extractfile(info) if info.isfile() else None
        if stream is None:
            raise ResolutionError(
                f"{relpath}: missing tarball member (not a regular file): "
                f"{member}")
        with stream:
            yield stream


def _sha256_of_reference(manifest_dir: Path, relpath: str) -> str:
    """Stream a reference and return its sha256 as 64 lowercase hex chars.

    Reads in :data:`CHUNK_BYTES` blocks; raises `ResolutionError` if the
    reference does not resolve.
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

    Returns sorted, deduplicated tokens verbatim: backtick-quoted,
    whitespace-free, ending in a :data:`CITED_SUFFIXES` suffix, never spanning a
    newline -- so an unmatched backtick cannot swallow the document, and prose
    like ``sha256(pool_analyze.py) = 3824a4`` is not read as a citation. A miss
    costs only one real citation going ungated, which is why the rule stays hard
    rather than heuristic.
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

    ``entry_path`` is a manifest candidate: a plain relpath, or a tarball's own
    path or member path. Asymmetric by design -- a longer citation is never
    covered by a shorter entry path, since the writeup made the more specific
    claim and the manifest must meet it.

    Examples
    --------
    >>> covers("all_rows.jsonl", "originals_all_rows.jsonl")
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

    Caller order is kept for both lists (grouping by role is an editorial choice
    sorting would destroy) and no timestamp is written, so rebuilds are
    byte-identical. Coverage is NOT checked here; only :func:`verify` judges a
    writeup's claims.

    Parameters
    ----------
    manifest_dir : str or Path
        Directory written into, and the base every ``relpath`` resolves against
        (upward ``..`` is legitimate).
    entries : iterable of mapping
        Each needs ``relpath`` (non-empty str) and ``role`` (one of
        :data:`ROLES`); may carry ``note`` (str) and ``sha256``, which is
        CHECKED against the computed digest, never trusted.
    allowlist : iterable of mapping
        Each needs non-empty ``name`` and ``reason``: a citation no entry
        covers, plus why that is acceptable.
    note : str, optional
        Free text; the key is omitted from the manifest when None.
    write : bool, default True
        False returns the manifest without touching the filesystem.

    Returns
    -------
    dict
        Ordered ``schema, note?, entries, allowlist``; each entry ``relpath,
        sha256, role, note?``.

    Raises
    ------
    FileNotFoundError
        An entry does not resolve; nothing is written in that case.
    ValueError
        Any constraint above violated, or a supplied ``sha256`` disagreeing with
        the computed one.
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

    # Validate the cheap schema before resolving and hashing, so a bad role
    # is a ValueError instead of whatever the filesystem says about its path.
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
        # newline="\n" pins the exact bytes: determinism covers the FILE, not
        # just the dict.
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
        The directory that was verified, as the caller named it (unresolved).
    n_entries : int
        Entries the manifest LISTS, including any the schema check rejected.
    roles : dict of str to int
        Counts per role over schema-valid entries only; a role with none is
        absent rather than zero.
    allowlist : list of dict
        The schema-valid allowlist entries only, as stored.
    citations : dict of str to list of str
        Writeup relpath -> sorted citation tokens, for every ``writeup`` entry
        that resolved, covered or not.
    failures : list of str
        Human-readable defects, in check order; empty means verified.
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

    ``index`` names the entry in messages, since ``relpath`` may itself be the
    missing field. Returns True if the entry is well formed enough to resolve
    and to serve as a coverage candidate. Every check runs before returning, so
    a hand-edited entry reports all its defects in one pass.
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

    ``raw_allowlist`` is the decoded ``allowlist`` value (absent = empty);
    well-formed entries come back in file order. An entry whose ``reason`` is
    missing is reported AND dropped, or deleting the justification would be the
    cheapest way to silence a coverage failure.
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

    Read-only. Checks in order: manifest schema; reference resolution; sha256
    (by streaming); citation coverage for every ``writeup`` entry. Every defect
    except a missing or unparseable manifest is COLLECTED rather than raised, so
    one run reports the whole state of a package; a sha256 mismatch does NOT
    stop that entry's citation scan, since a writeup that drifted is the one
    whose citations most need checking.

    Returns
    -------
    VerifyResult
        Census plus the ordered failure list.

    Raises
    ------
    FileNotFoundError
        ``manifest_dir/EVIDENCE.json`` does not exist.
    json.JSONDecodeError
        The manifest is not valid JSON; propagates deliberately, since there is
        no partial census to report.
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

    # Candidates come from every schema-valid entry, resolving or not: a broken
    # tarball is one failure, and must not also cascade into a bogus "cited
    # artifact not covered" for every name it holds.
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
            # Unreachable in practice (hashed a moment ago); handled so a file
            # changing under this run degrades to a failure line.
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

    Searches ``root`` (default :data:`REPO`) at any depth below a results
    directory, so a package under ``results/runs/<name>/`` counts too. Sorted;
    an empty list is a valid state, not an error.
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

    Excludes the FAIL lines, which the caller prints unindented so they grep
    cleanly out of a long run.
    """
    lines = [f"{_display_dir(result.manifest_dir)}: {result.n_entries} entries"]
    if result.roles:
        # ROLES order, not manifest order, so two packages' censuses stay
        # diffable against each other.
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
    """Verify ``dirs``, or every :func:`find_manifests` manifest when empty.

    Returns 0 if every manifest verified, 1 otherwise.
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
            # A named directory with no manifest is a user error, not a crash.
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

    ``spec_path`` holds ``{"note": ..., "entries": [...], "allowlist": [...]}``
    with no hashes -- they are computed here, so a spec can be hand-written and
    re-run after the evidence legitimately changes. Returns 0; any defect raises
    out of :func:`build` instead.
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
    """Command-line entry point; returns 0, or 1 if any manifest failed to verify."""
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
