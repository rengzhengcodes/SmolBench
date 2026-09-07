#!/usr/bin/env python
"""Build and verify ``EVIDENCE.json``, the manifest that pins what a writeup cites.

Pins each artifact by sha256, streaming even a tarball member rather than
extracting it -- extracting into the gitignored results dir is how untracked
evidence gets born. References may cross via ``..``, and :func:`build` is
deterministic, so a rebuild diff means the evidence moved.

Load by file path and register in ``sys.modules`` before ``exec_module``, or
the dataclass below can't resolve its annotations.
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

#: Closed role vocabulary: a typo fails loudly instead of inventing a role.
ROLES = ("writeup", "analysis_input", "raw", "estimator", "preregistration",
         "config", "gate", "teardown", "log", "other")

#: Citation-worthy suffixes, kept narrow: a false positive costs an allowlist entry.
CITED_SUFFIXES = (".json", ".jsonl", ".gz", ".yaml", ".yml", ".txt", ".md",
                  ".sh", ".py")

#: Suffixes the repo gate treats as writeups (tests import this).
WRITEUP_SUFFIXES = (".md", ".txt")

REPO = Path(__file__).resolve().parents[2]

TARBALL_PREFIX = "tarball:"

#: 1 MiB chunks keep a large gzipped raw file off the heap while hashing.
CHUNK_BYTES = 1 << 20

_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")

#: A citation token: backtick-delimited, never spanning a newline.
_BACKTICKED = re.compile(r"`([^`\n]+)`")


class ResolutionError(FileNotFoundError):
    """Raised when a manifest reference does not resolve to a readable file.

    Subclasses :class:`FileNotFoundError` so :func:`build` can propagate it
    while :func:`verify` collects it into a failure census.
    """


# -- reference grammar --

def _split_reference(relpath: str) -> tuple[str, str | None]:
    """Split a manifest ``relpath`` into its on-disk path and optional tarball member.

    Splits ``tarball:<tarball>!<member>`` on the FIRST ``!``, since a member
    may contain one but a tarball path effectively cannot.
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

    A tarball reference offers both the archive's own path and the member
    path, so a writeup can cite either.
    """
    path, member = _split_reference(relpath)
    return [path] if member is None else [path, member]


@contextmanager
def _open_reference(manifest_dir: Path, relpath: str) -> Iterator[IO[bytes]]:
    """Open a manifest reference for binary reading, without extracting it.

    Streams a tarball member via ``extractfile`` rather than
    ``extract``/``extractall``, so the filesystem stays byte-for-byte as
    found.
    """
    tar_relpath, member = _split_reference(relpath)
    target = manifest_dir / tar_relpath

    # Plain reference.
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
        # A directory/symlink/hardlink member reports "not a regular file".
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


# -- the scanner --

def cited_artifacts(text: str) -> list[str]:
    """Extract the artifact filenames a writeup cites in backticks.

    Returns sorted, deduplicated tokens verbatim: backtick-quoted,
    whitespace-free, ending in a :data:`CITED_SUFFIXES` suffix. Kept as a
    hard rule rather than a heuristic -- a miss only costs one citation
    going ungated.
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

    Asymmetric: a longer citation is never covered by a shorter entry path.
    """
    cited_parts = cited.split("/")
    entry_parts = entry_path.split("/")
    if len(cited_parts) > len(entry_parts):
        return False
    return entry_parts[len(entry_parts) - len(cited_parts):] == cited_parts


# -- build --

def build(manifest_dir: str | Path,
          entries: Iterable[Mapping[str, Any]],
          allowlist: Iterable[Mapping[str, Any]] = (),
          *,
          note: str | None = None,
          write: bool = True) -> dict[str, Any]:
    """Hash every listed artifact and write the directory's ``EVIDENCE.json``.

    Caller order is kept for both lists, and no timestamp is written, so
    rebuilds are byte-identical. Coverage is NOT checked here; only
    :func:`verify` judges a writeup's claims. A supplied ``sha256`` is
    checked against the computed digest, never trusted.
    """
    mdir = Path(manifest_dir)

    if note is not None and not isinstance(note, str):
        raise ValueError(f"note must be a string, got {type(note).__name__}")

    # Allowlist first: it costs no I/O, unlike the hashing pass below.
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

    # Validate cheap fields before hashing, so a bad role is a ValueError.
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
        # newline="\n" pins exact bytes: determinism covers the file too.
        (mdir / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8", newline="\n")
    return manifest


# -- verify --

@dataclass
class VerifyResult:
    """Outcome of verifying one ``EVIDENCE.json``.

    ``n_entries`` counts everything the manifest lists, including entries
    the schema check rejected; ``roles`` counts only the schema-valid ones.
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

    Every check runs before returning, so a hand-edited entry reports all
    its defects in one pass, not just the first.
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

    An entry missing ``reason`` is reported AND dropped -- keeping it would
    let deleting the justification silently pass a coverage failure.
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

    Checks schema, resolution, sha256, then coverage, in order, and COLLECTS
    every defect rather than raising -- a drifted writeup's sha256 mismatch
    still gets its citations scanned -- except a missing manifest or bad
    JSON, which propagate since there's no partial census to report.
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

    # Includes unresolved entries, else a broken tarball also misreports coverage.
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
            # Unreachable in practice (hashed a moment ago); kept as a graceful fallback.
            failures.append(f"{relpath}: unreadable writeup: {exc}")
            continue
        cited = cited_artifacts(text)
        citations[relpath] = cited
        # Name match only; whether it's the *right* artifact is for the entry's note.
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

    Searches at any depth below a results directory, so a package under
    ``results/runs/<name>/`` counts too.
    """
    base = REPO if root is None else Path(root)
    return sorted(base.glob(f"notebooks/*/results/**/{MANIFEST_NAME}"))


# -- CLI --

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
        # ROLES order keeps two packages' censuses diffable against each other.
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

    The spec carries no hashes -- they're computed here, so it can be
    hand-written and re-run after the evidence legitimately changes.
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
