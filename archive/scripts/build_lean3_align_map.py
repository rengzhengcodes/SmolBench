"""Build the Lean3->Lean4 `#align` name-map asset (`lean3_align.json.gz`).

`smolbench.deduction.lean.lean3`'s ``lean3-name`` detection rule and
``rename`` corruption transform both need a Lean3<->Lean4 declaration-name
map (`smolbench.deduction.lean.lean3.AlignMap`). mathlib4's own porting
tool (`mathport`) recorded that map itself, as one ``#align <lean3-name>
<lean4-name>`` compatibility-shim directive per ported declaration, sitting
directly above (or near) the declaration it renames. This script mines
those directives out of the traced mathlib4 checkout LeanDojo already
pulled to build the benchmark, and writes them out as a small, versioned,
gzip-compressed JSON asset that `AlignMap.load` consumes at dataset-build
and analysis time -- no LeanDojo/Lean toolchain needed to *read* the asset
afterward, only to *build* it once.

Source of truth and scope
--------------------------
The commit to mine is read from the already-bootstrapped benchmark's own
``metadata.json`` (``from_repo.commit``) rather than passed on the command
line -- the align map MUST describe the exact same mathlib4 snapshot the
rest of the pipeline (`smolbench.deduction.lean.corpus`, `.premises`)
already assumes, so pinning it to that file's own recorded commit removes
an entire class of "which mathlib4 was this built against" drift.

Only lines beginning ``#align `` (a literal trailing space; note this also
naturally excludes ``#align_import ...`` lines, mathport's *file*-level
directive, which does not start with ``#align`` followed by a space) at
column 0 are treated as directives -- a handful of ``#align``-*looking*
occurrences appear indented inside doc comments elsewhere in the corpus
(mathport's own usage instructions, quoted verbatim in a docstring); those
are prose, not directives, and are deliberately excluded by anchoring the
match at the start of the raw (non-``lstrip``ped) line.

Reproducibility
----------------
The written asset is CONTENT-reproducible (byte-for-byte identical across
repeated runs against the same checkout): the gzip stream is built via
``gzip.GzipFile(mtime=0, ...)`` into an in-memory buffer with no ``filename``
attribute available to embed (avoids both of gzip's two non-determinism
sources -- the embedded mtime and the embedded original filename), and the
JSON payload is serialized with ``sort_keys=True`` so key order never
depends on dict-insertion order (in turn: file-walk order).

Expected scale (informational only, NOT asserted anywhere in this module or
its tests -- see the module docstring of ``tests/test_lean3_repair_build.py``
for why a hard count assertion against a live, occasionally-updated external
checkout would be brittle): a planning-phase grep of the benchmark's pinned
commit (``fe4454af...``) found 130,965 raw ``#align `` lines resolving to
130,752 unique Lean3 keys -- i.e. roughly 130.7k pairs, with a couple hundred
duplicate-key lines and a much smaller number of malformed (``-- comment``
before any lean4 name, or truncated) lines.

Runs on the main 3.14 venv (no ``lean_dojo`` import -- this only walks
plain-text ``.lean`` files LeanDojo already cached on disk):

    .venv/bin/python scripts/build_lean3_align_map.py
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import sys
from pathlib import Path

# Anchor imports on the repo root (scripts/..), so an ad-hoc `python
# scripts/build_lean3_align_map.py` works even if the package is not
# `pip install`ed into the active interpreter (mirrors scripts/build_lean_sft.py).
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from smolbench.deduction.lean import corpus  # noqa: E402
from smolbench.deduction.lean.lean3 import ALIGN_ASSET_NAME  # noqa: E402

#: Manifest filename, derived from `ALIGN_ASSET_NAME` by stripping its
#: double suffix (`.json.gz`) rather than `Path.stem` (which only strips
#: ONE suffix, giving the wrong `lean3_align.json.manifest.json`) -- see
#: `main`'s use.
_MANIFEST_NAME = ALIGN_ASSET_NAME.removesuffix(".json.gz") + ".manifest.json"


def _cache_root() -> Path:
    """Root of LeanDojo's traced-repo cache.

    Resolution order: the ``LEAN_DOJO_CACHE_DIR`` environment variable if
    set, else ``~/.cache/lean_dojo`` (LeanDojo's own hardcoded default --
    see ``smolbench.deduction.lean.premises._traced_root``, which locates
    the same cache without the env-var override this script adds; tests
    need the override to point at a fixture tree without touching the real
    home directory).

    Returns
    -------
    Path
        Not guaranteed to exist -- see `_checkout_path`'s caller in `main`.
    """
    override = os.getenv("LEAN_DOJO_CACHE_DIR")
    if override:
        return Path(override)
    return Path.home() / ".cache" / "lean_dojo"


def _checkout_path(commit: str) -> Path:
    """The traced mathlib4 checkout directory for `commit`, under `_cache_root()`.

    Parameters
    ----------
    commit : str
        Full mathlib4 commit hash (from the benchmark's ``metadata.json``).

    Returns
    -------
    Path
        ``<cache root>/leanprover-community-mathlib4-<commit>/mathlib4`` --
        LeanDojo's own on-disk naming convention for a traced GitHub repo
        (organization-repo-commit, then the repo name again as the actual
        checkout root).
    """
    return _cache_root() / f"leanprover-community-mathlib4-{commit}" / "mathlib4"


def _scan_align_lines(files: list[Path]) -> tuple[dict[str, str], dict]:
    """Extract Lean3->Lean4 pairs from ``#align`` directives in `files`.

    Parameters
    ----------
    files : list of Path
        ``.lean`` files to scan, in a FIXED (caller-sorted) order -- see
        `main`, which sorts the file walk before calling this so that
        first-occurrence dedup below is deterministic across machines/runs
        regardless of the underlying filesystem's directory-listing order.

    Returns
    -------
    (pairs, stats) : (dict[str, str], dict)
        `pairs` -- ``{lean3_name: lean4_name}``, one entry per FIRST
        occurrence of a given `lean3_name` across the scan (see below).
        `stats` -- ``{"align_lines", "pairs", "duplicate_lean3_keys",
        "malformed_lines"}``; by construction
        ``align_lines == pairs + duplicate_lean3_keys + malformed_lines``
        (an accounting identity every candidate line falls into exactly one
        bucket of -- verified by ``tests/test_lean3_repair_build.py``).

    Notes
    -----
    A candidate line is any line whose text (unstripped of leading
    whitespace -- see the module docstring's "Source of truth and scope")
    starts with the literal ``"#align "`` (this also excludes
    ``#align_import ...``, which has no space right after ``#align``). The
    line is then split on whitespace; ``parts[1]`` is the Lean3 name and
    ``parts[2]`` the Lean4 name -- anything after that (mathport commonly
    appends a ``-- reorder implicits``-style trailing comment) is ignored.
    Fewer than 3 whitespace-separated parts (a directive missing even a
    Lean4 name) is malformed and counted, not raised -- a handful of
    genuinely malformed lines should not abort a 4000-file scan.

    A Lean3 key seen more than once keeps its FIRST-encountered mapping
    (mathport's later re-declarations of the same shim are much rarer than,
    and strictly less authoritative than, the original); subsequent
    occurrences are counted under `duplicate_lean3_keys`, not overwritten.
    """
    pairs: dict[str, str] = {}
    align_lines = 0
    duplicate_lean3_keys = 0
    malformed_lines = 0

    for path in files:
        text = path.read_text(encoding="utf-8")
        for line in text.split("\n"):
            if not line.startswith("#align "):
                continue
            align_lines += 1
            parts = line.split()
            if len(parts) < 3:
                malformed_lines += 1
                continue
            lean3_name, lean4_name = parts[1], parts[2]
            if lean3_name in pairs:
                duplicate_lean3_keys += 1
                continue
            pairs[lean3_name] = lean4_name

    stats = {
        "align_lines": align_lines,
        "pairs": len(pairs),
        "duplicate_lean3_keys": duplicate_lean3_keys,
        "malformed_lines": malformed_lines,
    }
    return pairs, stats


def _encode_asset(pairs: dict[str, str]) -> bytes:
    """Gzip-compress the align-map JSON payload, byte-reproducibly.

    Parameters
    ----------
    pairs : dict of str -> str
        The Lean3->Lean4 map to encode.

    Returns
    -------
    bytes
        A gzip stream of ``{"lean3_to_lean4": pairs}`` (compact separators,
        ``sort_keys=True``), built with ``mtime=0`` into an in-memory
        buffer with no filename to embed -- see the module docstring's
        "Reproducibility" section for why both matter.
    """
    payload = json.dumps({"lean3_to_lean4": pairs}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    buf = io.BytesIO()
    # `fileobj=buf` (not `filename=`) so GzipFile has no `.name` to embed;
    # `mtime=0` pins the header's otherwise-wall-clock timestamp field.
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(payload)
    return buf.getvalue()


def build_parser() -> argparse.ArgumentParser:
    """Build the (argument-free) CLI parser.

    Returns
    -------
    argparse.ArgumentParser
        No flags are exposed -- every input this script needs (the source
        commit, the cache location, the output location) is resolved from
        `smolbench.deduction.lean.corpus.data_root()` (the output goes to
        its ``.parent``, the committed-sidecar layout -- see `main`) and the
        ``LEAN_DOJO_CACHE_DIR`` environment variable (see `_cache_root`),
        both of which tests repoint via `monkeypatch.setenv` rather than
        CLI flags -- consistent with how every other loader in this package
        resolves its data root (see `corpus.data_root`'s docstring).
    """
    return argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)


def main(argv: list[str] | None = None) -> int:
    """Run the align-map build end to end; return a process exit code.

    Parameters
    ----------
    argv : list of str, optional
        Forwarded to `argparse.ArgumentParser.parse_args` (``None`` reads
        `sys.argv`); this script currently defines no flags, so `argv` is
        parsed only to support ``--help`` and reject unexpected arguments.

    Returns
    -------
    int
        ``0`` on success. ``1`` if the benchmark metadata is missing or the
        traced mathlib4 checkout is not cached locally -- both are
        environment-setup problems the caller must fix (bootstrap the
        benchmark / let LeanDojo pull the trace once), not something this
        script can recover from, so they are reported with an actionable
        message and a non-zero exit rather than raising.
    """
    build_parser().parse_args(argv)

    try:
        commit = corpus.metadata()["from_repo"]["commit"]
    except FileNotFoundError as exc:
        print(
            f"error: {exc}\nthe LeanDojo Benchmark 4 metadata is not bootstrapped -- see "
            "notebooks/lean/README.md's 'Data bootstrap' section",
            file=sys.stderr,
        )
        return 1

    checkout = _checkout_path(commit)
    if not checkout.is_dir():
        print(
            f"error: no traced mathlib4 checkout at {checkout}\n"
            "the ~2.4 GB traced corpus is pulled lazily by LeanDojo's own `Dojo` on its first "
            "call (cold start: a few minutes) -- see notebooks/lean/README.md's 'Data bootstrap' "
            "section -- or set $LEAN_DOJO_CACHE_DIR to an existing cache root",
            file=sys.stderr,
        )
        return 1

    # Sorted walk: deterministic first-occurrence dedup order (see
    # `_scan_align_lines`'s docstring), independent of the filesystem's
    # own (unspecified) directory-listing order.
    files = sorted((checkout / "Mathlib").rglob("*.lean"))
    pairs, stats = _scan_align_lines(files)
    stats = {"files_scanned": len(files), **stats}

    # Committed-sidecar layout: the asset lives BESIDE the wholesale-
    # gitignored leandojo_benchmark_4/ dataset dir, not inside it -- same
    # rationale (and same `.parent` anchor) as `corpus.replay_passing_path`:
    # small committed artifacts must not be swallowed by the dataset dir's
    # gitignore rule.
    out_dir = corpus.data_root().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    asset_path = out_dir / ALIGN_ASSET_NAME
    asset_bytes = _encode_asset(pairs)
    asset_path.write_bytes(asset_bytes)

    manifest = {
        "config": {"source_commit": commit, "cache_path": str(checkout)},
        "stats": stats,
        "asset": {
            "name": ALIGN_ASSET_NAME,
            "sha256": hashlib.sha256(asset_bytes).hexdigest(),
            "bytes": len(asset_bytes),
        },
    }
    manifest_path = out_dir / _MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(
        f"scanned {stats['files_scanned']} files, {stats['align_lines']} #align lines -> "
        f"{stats['pairs']} pairs ({stats['duplicate_lean3_keys']} duplicate keys, "
        f"{stats['malformed_lines']} malformed) -> {asset_path}\nmanifest -> {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
