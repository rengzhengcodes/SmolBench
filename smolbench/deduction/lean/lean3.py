"""Detect and inject Lean 3 syntax and lemma-name relics.

Two Lean-3-ism failure modes show up in generated tactic blocks, and
survive SFT/LoRA training as a small residue. The first is
**Lean 3 tactic syntax**: `refl` instead of `rfl`, `existsi` instead of
`use`, comma-terminated `begin...end` blocks, `λ x, e` binders instead of
`fun x ↦ e` / `λ x ↦ e`, and trailing commas after tactics. The second is
**mathlib3 lemma names** that the mathlib4 port renamed or restructured
(`supr_le` -> `iSup_le`, `iso.inv_comp_eq` -> `Iso.inv_comp_eq`).

This module is the shared detector and corrupter for both jobs:

- **Detection** (`find_relics` / `has_relics`). The run analyzer calls this
  to compute an `l3` leak-rate column over a model's generated tactic
  blocks. Dataset-QC tooling calls it to check that a training corpus is
  clean.
- **Corruption** (`corrupt_tail`). The auxiliary SFT dataset builder calls
  this to turn a clean, ground-truth Lean 4 tactic tail into a
  Lean-3-flavored "previous attempt", paired with the clean tail as the
  target. This teaches a model the *repair* move (see `build_repair_user`),
  instead of showing it only clean Lean 4 during training.

Shared-vocabulary invariant
----------------------------
Detection and corruption are two faces of one rule set. They must never
drift apart: **anything the corrupter can inject, the detector must
catch.** This is not just a documentation promise. `corrupt_tail`
mechanically enforces it as a post-condition: `find_relics(corrupted,
align)` must return at least one relic, or the corruption attempt is
discarded and the function returns `None`. A corruption transform that
silently produced an undetectable relic would poison the repair dataset
with a row whose "error" the model never gets a signal for, so this check
is not optional. Each of the five corruption transforms below is named
after the Lean4->Lean3 syntactic *inverse* of one detection rule
(`rfl->refl` undoes the `refl` rule's fix, `use->existsi` undoes the
`existsi` rule's fix, and so on). This naming keeps the two sides in
lockstep by construction, not merely by convention.

The `#align` asset and graceful degradation
--------------------------------------------
Lemma-name detection (`lean3-name`) and the `rename` corruption transform
both need a Lean3<->Lean4 name map. The map loads from a small
gzip-compressed JSON asset (`ALIGN_ASSET_NAME`), resolved by default BESIDE
the benchmark dataset directory (``corpus.data_root().parent``). This
matches the committed-sidecar layout `corpus.replay_passing_path`
documents: small committed artifacts live next to the wholesale-gitignored
``leandojo_benchmark_4/`` download, never inside it. The asset is mined from the traced mathlib4 snapshot's `#align` directives
(mathlib4's compatibility shims recording each declaration's mathlib3
name). This module consumes it through `AlignMap`; it does not build or
validate it.

Every public function in this module accepts `align: AlignMap | None =
None` and degrades gracefully when `align` is absent. `align=None`
disables the name-map-dependent rule (`lean3-name` in `find_relics`) and
transform (`rename` in `corrupt_tail`) without raising an error. The
parse-level-only detection and corruption (Lean 3 *syntax*, not lemma
names) still work in full. This lets a caller that has not yet
bootstrapped the align asset, or that runs in an environment without
`notebooks/deduction/data/`, still get useful signal.

Design constraints
-------------------
- Stays dependency-free beyond the standard library plus `.corpus` (for
  `data_root()` only, imported lazily at call time inside `AlignMap.load` --
  see its docstring). This module imports no `lean_dojo` and no
  torch/datasets, so it must import cleanly on the main py3.14 venv.
- Stays fully deterministic. `corrupt_tail` takes an explicit
  `random.Random` instance and never reads global random state or the
  wall clock, so a training-data build is byte-for-byte reproducible from
  its seed.
- Tracks bracket depth (across ``⟨⟩ () [] {}``) **cumulatively across
  lines**, not reset per line, as several rules require. An unclosed
  ``⟨`` several lines up correctly suppresses a trailing-comma flag
  several lines later (e.g. a multi-line ``refine ⟨foo,\\n  bar⟩``). The
  scanner does not skip string-literal contents: Lean tactic strings
  essentially never contain the bracket/comma characters this module
  cares about. This is a deliberate limitation, not an oversight.
"""

from __future__ import annotations

import gzip
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import corpus

#: Filename of the Lean3->Lean4 `#align` name-map asset. It resolves by
#: default at ``corpus.data_root().parent / ALIGN_ASSET_NAME``. See the
#: module docstring.
ALIGN_ASSET_NAME = "lean3_align.json.gz"


@dataclass(frozen=True)
class Relic:
    """One Lean 3 relic found by `find_relics`, or claimed by `corrupt_tail`.

    Parameters
    ----------
    kind : str
        One of ``"refl"``, ``"existsi"``, ``"binder-comma"``,
        ``"trailing-comma"``, ``"begin-end"``, ``"lean3-name"`` -- see the
        module-level detection rules in `find_relics`.
    text : str
        The offending token or line snippet that triggered the flag. The
        exact shape depends on `kind`: a bare tactic keyword for
        ``"refl"``/``"existsi"``, the stripped line for
        ``"begin-end"``/``"trailing-comma"``, the token itself for
        ``"lean3-name"``, and the binder-through-comma snippet for
        ``"binder-comma"``.
    fix : str or None
        The known Lean 4 replacement: ``"rfl"``, ``"use"``, the aligned
        Lean 4 name, or the line with its trailing comma removed. This is
        ``None`` when no single-token fix applies (``"begin-end"``,
        ``"binder-comma"``). A Lean3-style binder comma's fix needs to
        know which arrow to insert, so this module does not guess it.
    line : int
        0-indexed line number within the scanned text.
    """

    kind: str
    text: str
    fix: str | None
    line: int


# ---------------------------------------------------------------------------
# AlignMap: the Lean3 <-> Lean4 name map
# ---------------------------------------------------------------------------


class AlignMap:
    """A Lean3<->Lean4 declaration-name map, with suffix-based fuzzy lookup.

    mathlib4's `#align` directives record, for many declarations, the exact
    mathlib3 name the Lean4 declaration replaces. In the wild, names are
    frequently referenced via a shorter, unqualified or partially-qualified
    form -- e.g. ``iso.inv_comp_eq``
    instead of the full ``category_theory.iso.inv_comp_eq``. Exact string
    matching alone misses most real occurrences, so this class adds
    conservative suffix matching: a query resolves via a dotted suffix only
    when that suffix is unique across the whole map. An ambiguous partial
    name, one that could refer to two different declarations, never
    silently picks one.

    Parameters
    ----------
    lean3_to_lean4 : dict of str -> str
        Mapping from full mathlib3 declaration name to its mathlib4
        replacement name. The constructor copies this dict, so the
        instance owns its own copy; mutating the caller's dict afterward
        has no effect on this `AlignMap`.

    Notes
    -----
    All lookup indexes (suffix buckets, the Lean4 suffix set, and
    `reverse_unique`) are built once here, not recomputed per lookup.
    `find_relics` and `corrupt_tail` call `lookup_lean3`, `is_lean4_name`,
    and `reverse_unique` once per candidate token in a scan, so this
    matters at dataset-build scale.
    """

    def __init__(self, lean3_to_lean4: dict[str, str]) -> None:
        self.lean3_to_lean4: dict[str, str] = dict(lean3_to_lean4)

        # Suffix indexes over the LEAN3 keys, bucketed by their last one and
        # last two dotted components. Each bucket value holds every full
        # lean3 name that shares that suffix. `lookup_lean3` resolves a
        # query token against these buckets when the token isn't an exact
        # key, and only when the bucket has exactly one member -- an
        # ambiguous suffix (two different lean3 names sharing it) must
        # never guess.
        self._suffix1: dict[str, set[str]] = {}
        self._suffix2: dict[str, set[str]] = {}
        for lean3_name in self.lean3_to_lean4:
            parts = lean3_name.split(".")
            self._suffix1.setdefault(parts[-1], set()).add(lean3_name)
            if len(parts) >= 2:
                self._suffix2.setdefault(".".join(parts[-2:]), set()).add(lean3_name)

        # Every component-boundary dotted suffix of every LEAN4 value,
        # including the full name itself at the i=0 suffix. This set backs
        # `is_lean4_name`'s "is this token already valid Lean 4" guard.
        self._lean4_suffixes: set[str] = set()
        for lean4_name in self.lean3_to_lean4.values():
            parts = lean4_name.split(".")
            for i in range(len(parts)):
                self._lean4_suffixes.add(".".join(parts[i:]))

        # lean4 -> lean3, restricted to lean4 names with a UNIQUE lean3
        # preimage. The `rename` corruption transform must never corrupt a
        # Lean4 name into an arbitrarily chosen one of several equally
        # valid Lean3 spellings -- that would make the "expected" repair
        # target ambiguous.
        preimages: dict[str, list[str]] = {}
        for lean3_name, lean4_name in self.lean3_to_lean4.items():
            preimages.setdefault(lean4_name, []).append(lean3_name)
        self._reverse_unique: dict[str, str] = {
            lean4_name: lean3_names[0]
            for lean4_name, lean3_names in preimages.items()
            if len(lean3_names) == 1
        }

    @classmethod
    def from_pairs(cls, pairs: dict[str, str]) -> AlignMap:
        """Build an `AlignMap` directly from a ``{lean3: lean4}`` dict.

        This is a convenience constructor for tests and small fixtures. It
        behaves identically to ``AlignMap(pairs)``, spelled out for
        readability at call sites.

        Parameters
        ----------
        pairs : dict of str -> str
            Lean3 name -> Lean4 name pairs.

        Returns
        -------
        AlignMap
        """
        return cls(pairs)

    @classmethod
    def load(cls, path: Path | None = None) -> AlignMap | None:
        """Load the align map from its gzip-compressed JSON asset.

        Parameters
        ----------
        path : Path, optional
            Explicit asset path. When omitted (the default), this resolves
            to ``corpus.data_root().parent / ALIGN_ASSET_NAME`` -- BESIDE
            the gitignored benchmark dataset dir, not inside it. This
            matches the committed-sidecar layout of
            `corpus.replay_passing_path`: the asset is a small committed
            artifact, while ``data_root()`` itself is the wholesale
            gitignored ~700 MB download. `load` calls `corpus.data_root()`
            here, at call time, not cached at import time. A caller
            (including a test) that repoints the ``SMOLBENCH_LEAN_DATA``
            environment variable before calling `load` gets the
            freshly-resolved path.

        Returns
        -------
        AlignMap or None
            The loaded map, or ``None`` if the asset file does not exist.
            Absence is not an error: every other function in this module
            accepts ``align=None`` and degrades to parse-level-only
            detection/corruption (see the module docstring). A caller that
            has not bootstrapped the align asset yet still gets useful
            behavior instead of an exception.

        Notes
        -----
        Asset format: gzip-compressed UTF-8 JSON,
        ``{"lean3_to_lean4": {<lean3 name>: <lean4 name>, ...}}``.
        """
        if path is None:
            path = corpus.data_root().parent / ALIGN_ASSET_NAME
        if not path.exists():
            return None
        with gzip.open(path, "rt", encoding="utf-8") as f:
            payload = json.load(f)
        return cls(payload["lean3_to_lean4"])

    def lookup_lean3(self, token: str) -> str | None:
        """Resolve a candidate identifier token to its Lean4 name, if known.

        Parameters
        ----------
        token : str
            A candidate identifier (see `find_relics`'s ``lean3-name`` rule
            for the token-extraction contract this is meant to be called
            with -- typically already stripped of trailing ``.``/``,``).

        Returns
        -------
        str or None
            `token`'s Lean4 replacement, resolved in this order:

            1. Exact match against a Lean3 key.
            2. `token`'s last two dotted components match a suffix bucket
               with exactly one candidate lean3 name. This check runs
               before the 1-component bucket, since a 2-component match is
               more specific.
            3. `token`'s last dotted component matches a suffix bucket
               with exactly one candidate.

            Returns ``None`` if none of the above resolve, including the
            case where a suffix bucket exists but is ambiguous (2 or more
            candidates).
        """
        exact = self.lean3_to_lean4.get(token)
        if exact is not None:
            return exact
        bucket = self._suffix2.get(token)
        if bucket is not None and len(bucket) == 1:
            return self.lean3_to_lean4[next(iter(bucket))]
        bucket = self._suffix1.get(token)
        if bucket is not None and len(bucket) == 1:
            return self.lean3_to_lean4[next(iter(bucket))]
        return None

    def is_lean4_name(self, token: str) -> bool:
        """True if `token` is exactly a known Lean4 name, or a suffix of one.

        This method is the CLEAN guard in `find_relics`'s ``lean3-name``
        rule: a token that already resolves via `lookup_lean3` should
        still not get flagged if it is itself already valid Lean 4. This
        is defense in depth. With a well-formed align map, this branch
        should be unreachable, since a Lean4 name should not
        simultaneously collide with a Lean3 suffix bucket. The guard costs
        nothing to run, and the spec calls for it explicitly.

        Parameters
        ----------
        token : str
            Candidate identifier token.

        Returns
        -------
        bool
            ``True`` iff `token` equals some Lean4 name in the map exactly,
            or equals a component-boundary dotted suffix of one.
        """
        return token in self._lean4_suffixes

    @property
    def reverse_unique(self) -> dict[str, str]:
        """Lean4 name -> Lean3 name, restricted to unique inverses.

        Returns
        -------
        dict of str -> str
            The entries of `lean3_to_lean4` inverted, keeping only Lean4
            names with exactly one Lean3 preimage (see `__init__` for why
            an ambiguous inverse is dropped). The `rename` corruption
            transform uses this to pick a Lean3 spelling to inject that is
            unambiguously "the" corresponding Lean3 name.
        """
        return self._reverse_unique


# ---------------------------------------------------------------------------
# Bracket-depth scanning (shared by detection and corruption)
# ---------------------------------------------------------------------------

_OPEN_BRACKETS = "⟨([{"
_CLOSE_BRACKETS = "⟩)]}"


def _bracket_delta(ch: str) -> int:
    """+1 for an opening bracket, -1 for a closing bracket, else 0."""
    if ch in _OPEN_BRACKETS:
        return 1
    if ch in _CLOSE_BRACKETS:
        return -1
    return 0


#: Candidate identifier-token regex shared by lean3-name detection and the
#: `rename` corruption transform. This regex is broad on purpose. It
#: includes `!`/`?`/`'`, valid trailing characters in Lean identifiers,
#: plus `.` for dotted qualification, plus the subscript digits
#: ``₀``-``₉`` (U+2080-U+2089) that Mathlib names routinely end with, e.g.
#: ``div_mul_cancel₀``. Without the subscripts, such an identifier would
#: split mid-name: the `rename` transform could then rewrite the
#: alphabetic stem while stranding the subscript, producing a Frankenstein
#: token (``div_mul_cancel'₀``) that matches neither the Lean3 nor the
#: Lean4 spelling of anything. Callers filter and trim the raw match (see
#: `_iter_candidate_tokens`).
_CANDIDATE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'.!?₀-₉]*")

#: `refl`/`existsi` are plain-word Lean tactics. This regex matches them
#: with `\b` word boundaries, so `le_refl` (no boundary before "refl",
#: since `_` is a `\w` char) and `existsi_something` are not mistaken for
#: the bare tactic.
_REFL_RE = re.compile(r"\brefl\b")
_EXISTSI_RE = re.compile(r"\bexistsi\b")

#: The Lean4 `rfl` tactic token, distinct from `_REFL_RE` above (which
#: matches the Lean3 tactic `refl` for detection). Only the `rfl->refl`
#: corruption transform uses this, to find `rfl` and corrupt it INTO
#: `refl`.
_RFL_RE = re.compile(r"\brfl\b")

#: `fun`/`λ` binder keyword. `λ` is a Unicode letter, so a plain `\b`
#: already requires a non-word char (e.g. whitespace) on either side of
#: it. No special-casing is needed beyond the ordinary `\b`.
_BINDER_RE = re.compile(r"\b(?:fun|λ)\b")

#: Prefixes that put `refl` in "tactic-head position" per the spec, after
#: stripping trailing whitespace from the text preceding a `refl` match:
#: line start (checked separately as an empty prefix), or right after one
#: of these tactic-combinator markers.
_REFL_HEAD_MARKERS = (";", "<;>", "·", "{")  # ';' '<;>' '·' '{'


def _is_head_position(line_prefix: str) -> bool:
    """True if text following `line_prefix` sits in tactic-head position.

    This is the single source of the "tactic-head position" predicate.
    `find_relics`'s rule 2 (detecting the Lean 3 `refl` tactic) and the
    `rfl->refl` corruption transform (`_head_rfl_matches`) both use it. A
    token sits in head position when everything before it on its line is
    empty, or ends with one of `_REFL_HEAD_MARKERS`. One shared predicate
    for both detector and corrupter makes an injected `refl` relic
    re-detectable by construction (the shared-vocabulary invariant). A
    `rfl` rewritten in term position (`exact rfl`) would produce `exact
    refl`, which rule 2 deliberately does NOT flag, so the transform must
    not target it either.
    """
    p = line_prefix.rstrip()
    return p == "" or p.endswith(_REFL_HEAD_MARKERS)


def _iter_candidate_tokens(text: str) -> list[tuple[re.Match, str]]:
    """Extract lean3-name candidate tokens from `text`.

    Parameters
    ----------
    text : str
        Line (or larger span) of Lean tactic text.

    Returns
    -------
    list of (re.Match, str)
        One ``(match, token)`` pair per candidate. `token` is the raw
        regex match with a trailing ``.``/``,`` stripped, since that is
        sentence or list punctuation, not part of the identifier. The list
        keeps only tokens of length >= 3 that contain a ``_`` or ``.`` --
        a short, plain identifier (`x`, `hx`, `n`) is never a lemma name,
        and would otherwise dominate false-positive matches. The
        `re.Match` gives the ORIGINAL (untrimmed) span. A caller that
        needs the token's own span should use ``match.start()`` and
        ``match.start() + len(token)`` (the trimmed length), not
        ``match.end()``.
    """
    out: list[tuple[re.Match, str]] = []
    for m in _CANDIDATE_RE.finditer(text):
        tok = m.group(0).rstrip(".,")
        if len(tok) < 3 or ("_" not in tok and "." not in tok):
            continue
        out.append((m, tok))
    return out


def _binder_forward_scan(text: str, start: int) -> tuple[str, int, int] | None:
    """Scan `text[start:]` for the binder's own comma or arrow.

    This function implements the shared "scan forward from the binder AT
    THE BINDER'S OWN bracket depth" rule. Both `find_relics`'s
    ``binder-comma`` detection and the `binder` corruption transform use
    it. Depth is tracked *relative* to `start` (the position immediately
    after the `fun`/`λ` keyword). A comma nested one level deeper than
    the binder does not count -- e.g. in `fun ⟨a, b⟩ ↦ e`, the comma
    nests inside the just-opened `⟨`.

    Parameters
    ----------
    text : str
        Full text being scanned, not just one line. A binder near a
        line's end could, in principle, have its arrow or comma on the
        next line, and bracket depth is cumulative across lines
        throughout this module.
    start : int
        Absolute index to start scanning from (typically
        ``binder_match.end()``).

    Returns
    -------
    (str, int, int) or None
        ``("comma", i, i + 1)`` for the first depth-0 ``,``, or
        ``("arrow", i, j)`` for the first ``↦`` (``j = i + 1``) or ``=>``
        (``j = i + 2``), whichever comes first in scan order. Returns
        ``None`` if neither appears before the end of `text`.
    """
    depth = 0
    i = start
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "," and depth == 0:
            return ("comma", i, i + 1)
        if ch == "↦":
            return ("arrow", i, i + 1)
        if text[i : i + 2] == "=>":
            return ("arrow", i, i + 2)
        depth += _bracket_delta(ch)
        i += 1
    return None


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def find_relics(text: str, align: AlignMap | None = None) -> list[Relic]:
    """Scan `text` for Lean 3 syntax and, optionally, mathlib3 lemma names.

    This function applies six detection rules (see the inline comments
    below for each). Every rule is precision-guarded against real Lean 4
    constructs that superficially resemble a Lean 3 relic, and validated
    against the cases pinned in ``tests/deduction/test_lean_lean3.py`` (the
    exact CLEAN/FLAGGED cases this was built against).

    Parameters
    ----------
    text : str
        Tactic-block text to scan (typically one model generation's
        extracted tactic lines, or a training-data tail). This may be
        multi-line text; bracket depth is tracked cumulatively across the
        whole text, not reset per line.
    align : AlignMap, optional
        Lean3->Lean4 name map. When ``None``, `find_relics` skips the
        ``lean3-name`` rule entirely (graceful degradation -- see the
        module docstring). The other five rules are parse-level and
        always run.

    Returns
    -------
    list of Relic
        One `Relic` per distinct ``(kind, text, line)`` triple found, in
        scan order. The five parse-level rules run line by line, top to
        bottom, in rule order. ``binder-comma`` is the exception: it runs
        as a separate pass over the whole text, since a binder's arrow or
        comma can in principle follow a line break. Duplicate ``(kind,
        text, line)`` triples collapse to a single `Relic` -- e.g. two
        `refl` tactics on one line report as one relic.

    Notes
    -----
    This is a pure function; it does not mutate `text` or `align`. The
    parse-level rules run in O(n) time in the length of `text`. The
    ``lean3-name`` rule additionally makes one `AlignMap.lookup_lean3` and
    one `AlignMap.is_lean4_name` call per candidate token (each O(1) on
    average, via the suffix-bucket indexes `AlignMap.__init__` builds
    once).
    """
    relics: list[Relic] = []
    seen: set[tuple[str, str, int]] = set()

    def emit(kind: str, rtext: str, fix: str | None, line: int) -> None:
        key = (kind, rtext, line)
        if key not in seen:
            seen.add(key)
            relics.append(Relic(kind=kind, text=rtext, fix=fix, line=line))

    lines = text.split("\n")

    # Cumulative bracket depth AFTER each line's own characters. Rule 5
    # (trailing-comma) needs depth accumulated from the START of the whole
    # text, not reset per line, so an unbalanced open bracket several
    # lines up correctly suppresses a flag several lines later.
    depth_after_line: list[int] = []
    running = 0
    for line in lines:
        for ch in line:
            running += _bracket_delta(ch)
        depth_after_line.append(running)

    for lineno, line in enumerate(lines):
        stripped = line.strip()

        # Rule 1: begin/end block markers. Lean 4 removed these wholesale;
        # a tactic block is just indentation, with no wrapper keyword.
        if stripped in ("begin", "end") or stripped.startswith("begin "):
            emit("begin-end", stripped, None, lineno)

        # Rule 2: flag `refl` only in tactic-head position (line start, or
        # right after a tactic-combinator marker). This excludes `le_refl
        # x` and `Equiv.refl` (a lemma name or namespaced identifier, not
        # the bare tactic). `\brefl\b` alone would NOT exclude these: the
        # `.` before `refl` in `Equiv.refl` is itself a word boundary.
        for m in _REFL_RE.finditer(line):
            if _is_head_position(line[: m.start()]):
                emit("refl", "refl", "rfl", lineno)

        # Rule 3: `existsi`. Lean 4 removed this outright, so unlike
        # `refl`, any occurrence (not just tactic-head) is a relic.
        if _EXISTSI_RE.search(line):
            emit("existsi", "existsi", "use", lineno)

        # Rule 5: flag a trailing comma while cumulative depth is 0. A
        # comma inside a still-open `⟨`/`(`/`[`/`{` (e.g. multi-line
        # `refine ⟨foo,`) is legitimate Lean 4 term syntax, not a relic.
        if stripped.endswith(",") and depth_after_line[lineno] == 0:
            emit("trailing-comma", stripped, stripped[:-1].rstrip(), lineno)

        # Rule 6: mathlib3 lemma/def names, only when an align map is given.
        if align is not None:
            for _m, tok in _iter_candidate_tokens(line):
                mapped = align.lookup_lean3(tok)
                if mapped is not None and not align.is_lean4_name(tok):
                    emit("lean3-name", tok, mapped, lineno)

    # Rule 4: binder-comma. This runs as a separate whole-text pass; see
    # `_binder_forward_scan`'s docstring for why it isn't line-bounded.
    for m in _BINDER_RE.finditer(text):
        found = _binder_forward_scan(text, m.end())
        if found is not None and found[0] == "comma":
            _, comma_start, comma_end = found
            lineno = text.count("\n", 0, m.start())
            emit("binder-comma", text[m.start() : comma_end], None, lineno)

    return relics


def has_relics(text: str, align: AlignMap | None = None) -> bool:
    """True if `find_relics` would report at least one relic.

    Parameters
    ----------
    text : str
        Text to scan; see `find_relics`.
    align : AlignMap, optional
        See `find_relics`.

    Returns
    -------
    bool
        ``bool(find_relics(text, align))``. This is a readable convenience
        for a QC call site that only needs a yes/no answer (the analyzer's
        `l3` leak-rate column, or a dataset cleanliness assertion) without
        building the full relic list itself. It is a thin wrapper, not a
        short-circuited scan: `find_relics` still runs to completion.
    """
    return bool(find_relics(text, align))


# ---------------------------------------------------------------------------
# Corruption
# ---------------------------------------------------------------------------


def _rename_lookup(tok: str, reverse_unique: dict[str, str]) -> str | None:
    """`tok`'s longest dotted suffix (itself included) keying `reverse_unique`.

    This function checks suffixes longest-first: `tok` itself, then its
    last ``n-1`` components, and so on. A token with extra outer namespace
    qualification beyond what the align map recorded still resolves via
    its more specific (longer) suffix, in preference to a shorter, less
    specific one.
    """
    parts = tok.split(".")
    for i in range(len(parts)):
        suffix = ".".join(parts[i:])
        candidate = reverse_unique.get(suffix)
        if candidate is not None:
            return candidate
    return None


def _rename_candidates(
    text: str, align: AlignMap | None
) -> list[tuple[re.Match, str, str]]:
    """Renamable ``(match, token, truncated_lean3_spelling)`` candidates in `text`.

    A candidate survives only if its truncated Lean3 spelling (the
    replacement `_apply_rename` would actually write -- see that
    docstring for the truncation rule) is itself DETECTABLE by
    `find_relics`'s rule 6. This function checks rule 6's exact predicate
    chain:

    - The spelling must differ from the original token. About 8k of
      mathlib4's `#align` pairs are identity spellings (``#align inv_inv
      inv_inv``), for which a "rename" would be a byte-level no-op that
      still claimed a lean3-name relic.
    - The spelling must pass `_iter_candidate_tokens`'s token-shape filter
      (length >= 3, contains ``_`` or ``.``), or rule 6 never even
      tokenizes it.
    - `align.lookup_lean3` must resolve it, and `align.is_lean4_name`
      must reject it -- rule 6's own flag condition. A bare snake_case
      name that is also a valid Lean4 suffix (``inv_comp_eq``) fails the
      second check, and this function correctly excludes it too.

    Without this filter, the corrupter could inject a relic the detector
    can never corroborate, poisoning `synth_error` with a claim like
    ``unknown identifier 'inv_inv'`` about a perfectly valid Lean 4 name.
    """
    if align is None:
        return []
    reverse = align.reverse_unique
    if not reverse:
        return []
    out = []
    for m, tok in _iter_candidate_tokens(text):
        lean3_full = _rename_lookup(tok, reverse)
        if lean3_full is None:
            continue
        n_components = len(tok.split("."))
        # Python slicing clamps gracefully: if `lean3_full` has fewer parts
        # than `n_components`, `[-n_components:]` returns the whole list.
        truncated = ".".join(lean3_full.split(".")[-n_components:])
        if truncated == tok:
            continue  # identity #align pair; a "rename" here is a no-op
        if len(truncated) < 3 or ("_" not in truncated and "." not in truncated):
            continue  # would not even tokenize as a rule-6 candidate
        if align.lookup_lean3(truncated) is None or align.is_lean4_name(truncated):
            continue  # rule 6 would not flag this replacement
        out.append((m, tok, truncated))
    return out


def _rename_applicable(text: str, align: AlignMap | None) -> bool:
    return bool(_rename_candidates(text, align))


def _apply_rename(
    text: str, rng: random.Random, align: AlignMap | None
) -> tuple[str, list[Relic]] | None:
    """`rename`: replace one seeded-chosen Lean4 name with its Lean3 spelling.

    The replacement is the matched `reverse_unique` Lean3 name, TRUNCATED
    to the same number of dotted components as the original token. For
    example, a 2-component token that resolves to the 3-component lean3
    name ``category_theory.iso.inv_comp_eq`` gets replaced with the last 2
    components, ``iso.inv_comp_eq`` -- never the full name. This mimics
    how a partially-qualified Lean4 reference would look if mathlib3 used
    the same qualification, instead of inventing an implausible
    fully-qualified Lean3 name out of a short Lean4 token.
    """
    candidates = _rename_candidates(text, align)
    if not candidates:
        return None
    # Truncation, and the detectability filter on the truncated spelling,
    # both happen inside `_rename_candidates`, so applicability and
    # application cannot disagree about which tokens are renamable.
    m, tok, truncated = rng.choice(candidates)
    start = m.start()
    end = start + len(tok)  # `tok` may be shorter than `m.group(0)` -- see
    # `_iter_candidate_tokens` (trailing `.`/`,` stripped).
    new_text = text[:start] + truncated + text[end:]
    lineno = text.count("\n", 0, start)
    # Recompute `.fix` via `align.lookup_lean3`, rather than reusing
    # `lean3_full`, so the claimed relic's `.fix` matches exactly what an
    # independent `find_relics` call on `new_text` would derive -- the
    # shared-vocabulary invariant this module is built around.
    fix = align.lookup_lean3(truncated) if align is not None else None
    return new_text, [Relic(kind="lean3-name", text=truncated, fix=fix, line=lineno)]


def _head_rfl_matches(text: str) -> list[re.Match]:
    """`rfl` tokens in tactic-head position -- the only corruptible ones.

    This function shares `_is_head_position` with `find_relics`'s rule 2.
    A `rfl` in term position (`exact rfl`, `⟨rfl, h⟩`) rewritten to `refl`
    would NOT be re-detected, since rule 2 only flags tactic-head `refl`,
    so the transform must not target it.
    """
    out = []
    for m in _RFL_RE.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        if _is_head_position(text[line_start : m.start()]):
            out.append(m)
    return out


def _rfl_applicable(text: str, align: AlignMap | None) -> bool:
    return bool(_head_rfl_matches(text))


def _apply_rfl(
    text: str, rng: random.Random, align: AlignMap | None
) -> tuple[str, list[Relic]] | None:
    """`rfl->refl`: rewrite the first TACTIC-HEAD `rfl` token to `refl`."""
    matches = _head_rfl_matches(text)
    if not matches:
        return None
    m = matches[0]
    new_text = text[: m.start()] + "refl" + text[m.end() :]
    lineno = text.count("\n", 0, m.start())
    return new_text, [Relic(kind="refl", text="refl", fix="rfl", line=lineno)]


def _first_binder_arrow(text: str) -> tuple[re.Match, int, int] | None:
    """First depth-0 `fun`/`λ` binder whose forward scan hits an arrow first.

    "Depth-0" here means the binder keyword's own cumulative bracket
    depth, not the forward-scan-relative depth `_binder_forward_scan`
    uses. The `binder` transform only corrupts a *top-level* binder,
    matching the spec's "first depth-0 fun/λ". A binder already followed
    by a comma before any arrow is already a `binder-comma` relic, so it
    is not a target for this transform: it has nothing left to corrupt.
    This function skips such a binder by treating `_binder_forward_scan`
    returning `"comma"` as no match.

    Returns
    -------
    (re.Match, int, int) or None
        ``(binder_match, arrow_start, arrow_end)`` for the first
        qualifying binder, or ``None`` if none exists.
    """
    for m in _BINDER_RE.finditer(text):
        # The text here is proof-tail-sized (a handful of lines), so
        # re-walking the prefix per candidate binder is cheap. This avoids
        # threading a separate running-depth accumulator through this
        # small helper.
        binder_depth = sum(_bracket_delta(ch) for ch in text[: m.start()])
        if binder_depth != 0:
            continue
        found = _binder_forward_scan(text, m.end())
        if found is not None and found[0] == "arrow":
            return m, found[1], found[2]
    return None


def _binder_applicable(text: str, align: AlignMap | None) -> bool:
    return _first_binder_arrow(text) is not None


def _apply_binder(
    text: str, rng: random.Random, align: AlignMap | None
) -> tuple[str, list[Relic]] | None:
    """`binder`: rewrite `fun`->`λ` and the binder's own arrow -> `,`.

    The only mandatory change is removing the arrow: that is what makes
    the binder a `binder-comma` relic. This function also rewrites `fun`
    to `λ`, because Lean 3 has no `fun` keyword at all. A corrupted `fun
    x, e` would be a syntax the detector correctly flags, but one Lean 3
    itself never produced. `λ x, e` is more faithful to real Lean 3.
    """
    found = _first_binder_arrow(text)
    if found is None:
        return None
    m, arrow_start, arrow_end = found
    replacement_binder = "λ" if m.group(0) == "fun" else m.group(0)
    prefix = text[: m.start()]
    middle = text[m.end() : arrow_start]
    suffix = text[arrow_end:]
    new_text = prefix + replacement_binder + middle + "," + suffix
    lineno = text.count("\n", 0, m.start())
    relic_text = replacement_binder + middle + ","
    return new_text, [Relic(kind="binder-comma", text=relic_text, fix=None, line=lineno)]


def _trailing_eligible_lines(text: str) -> list[int]:
    """0-indexed lines of `text` eligible for the `trailing` transform.

    A line is eligible when it is non-blank, its cumulative bracket depth
    is 0 at line end, and it does not already end in a comma (there is
    nothing new to corrupt there).
    """
    lines = text.split("\n")
    depth = 0
    eligible = []
    for i, line in enumerate(lines):
        for ch in line:
            depth += _bracket_delta(ch)
        stripped = line.rstrip()
        if stripped and depth == 0 and not stripped.endswith(","):
            eligible.append(i)
    return eligible


def _trailing_applicable(text: str, align: AlignMap | None) -> bool:
    return bool(_trailing_eligible_lines(text))


def _apply_trailing(
    text: str, rng: random.Random, align: AlignMap | None
) -> tuple[str, list[Relic]] | None:
    """`trailing`: append `,` to a seeded non-empty subset of eligible lines.

    The other four transforms each touch exactly one location. This one
    can inject multiple relics in a single application. A random
    non-empty subset, rather than always every eligible line, mimics a
    model that drops commas inconsistently rather than uniformly across
    an entire proof.
    """
    eligible = _trailing_eligible_lines(text)
    if not eligible:
        return None
    k = rng.randint(1, len(eligible))
    chosen = sorted(rng.sample(eligible, k))
    lines = text.split("\n")
    relics: list[Relic] = []
    for i in chosen:
        raw = lines[i]
        stripped = raw.strip()
        lines[i] = raw.rstrip() + ","
        relics.append(Relic(kind="trailing-comma", text=stripped + ",", fix=stripped, line=i))
    return "\n".join(lines), relics


def _use_applicable(text: str, align: AlignMap | None) -> bool:
    return any(line.lstrip().startswith("use ") for line in text.split("\n"))


def _apply_use(
    text: str, rng: random.Random, align: AlignMap | None
) -> tuple[str, list[Relic]] | None:
    """`use->existsi`: rewrite the first `use `-prefixed line's tactic name."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("use "):
            indent = line[: len(line) - len(stripped)]
            lines[i] = indent + "existsi " + stripped[len("use ") :]
            relic = Relic(kind="existsi", text="existsi", fix="use", line=i)
            return "\n".join(lines), [relic]
    return None


#: Signature shared by every transform's applicability check:
#: `(text, align) -> "can this transform do anything to `text`?"`.
_IsApplicable = Callable[[str, AlignMap | None], bool]
#: Signature shared by every transform's apply step:
#: `(text, rng, align) -> (new_text, [Relic injected, ...])`, or `None`.
#: A transform returns `None` when applying it turns out to be a no-op,
#: even though `_IsApplicable` returned True. This should not normally
#: happen, but `corrupt_tail` treats it as "this transform contributed
#: nothing" rather than asserting.
_Apply = Callable[[str, random.Random, AlignMap | None], tuple[str, list[Relic]] | None]

#: `(is_applicable, apply)` pairs, keyed by transform name, in the fixed
#: order `corrupt_tail` checks them for its "which are applicable" scan.
_TRANSFORMS: dict[str, tuple[_IsApplicable, _Apply]] = {
    "rename": (_rename_applicable, _apply_rename),
    "rfl_to_refl": (_rfl_applicable, _apply_rfl),
    "binder": (_binder_applicable, _apply_binder),
    "trailing": (_trailing_applicable, _apply_trailing),
    "use_to_existsi": (_use_applicable, _apply_use),
}


def corrupt_tail(
    tail: str, rng: random.Random, align: AlignMap | None = None
) -> tuple[str, list[Relic]] | None:
    """Inject a seeded mix of Lean 3 relics into a clean Lean 4 tactic tail.

    This function picks a seeded random subset of the five corruption
    transforms (`rename`, `rfl->refl`, `binder`, `trailing`,
    `use->existsi` -- see their individual docstrings), applies them in
    sequence, then checks the shared-vocabulary post-condition before it
    returns.

    Parameters
    ----------
    tail : str
        Clean, ground-truth Lean 4 tactic text to corrupt, assumed
        Lean-3-relic-free -- typically an SFT dataset's target tail.
    rng : random.Random
        Source of randomness. `corrupt_tail` reads no other random or
        global state, so an identical `(tail, rng-state, align)` always
        produces identical output. A caller gets reproducibility by
        constructing a fresh `random.Random(seed)` per call, or per row.
    align : AlignMap, optional
        Lean3<->Lean4 name map. When ``None``, the `rename` transform is
        never applicable, since it needs `AlignMap.reverse_unique`. The
        other four transforms are unaffected.

    Returns
    -------
    (str, list of Relic) or None
        ``(corrupted, injected)``, where `corrupted` is `tail` with 1 to 3
        transforms applied, and `injected` lists the `Relic` objects the
        applied transforms claim to have introduced. A fresh
        `find_relics(corrupted, align)` call CORROBORATES this list: it
        drops any claimed relic whose `kind` the detector does not
        re-report on the final text. This makes ``{r.kind for r in
        injected}`` a subset of the detector's kinds BY CONSTRUCTION (the
        shared-vocabulary invariant, enforced structurally rather than
        assumed). This function returns ``None`` in any of these cases:

        - No transform is applicable to `tail` at all.
        - Every applicable transform, once actually attempted, turns out
          to make no change (an earlier transform in the same pass can
          consume the only occurrence a later one needed).
        - The post-condition fails: `find_relics(corrupted, align)` comes
          back empty, or corroboration drops EVERY claimed relic. Either
          case would leave downstream `synth_error` with nothing truthful
          to say.
        - `corrupted == tail` (a degenerate no-op).

    Notes
    -----
    Algorithm: first, compute which of the five transforms are applicable
    to `tail` as given. If none are, return `None` immediately.
    Otherwise, draw ``n = rng.randint(1, min(3, len(applicable)))``,
    shuffle the applicable names (seeded), and apply the first `n` of
    them, in that order, against the *evolving* text. This function
    re-checks each transform for applicability against the current text
    immediately before it runs, since an already-applied transform may
    have consumed what a later one needed, and skips the transform if it
    is no longer applicable or its own application is a no-op.
    `injected` accumulates the `Relic` object(s) each transform that
    *did* apply reports for itself. Each transform's relic construction
    mirrors `find_relics`'s own field semantics exactly (see, e.g.,
    `_apply_rename`'s `.fix` recomputation).

    The final post-condition then CORROBORATES the claims: it re-runs
    `find_relics` on the corrupted text and keeps only the injected
    relics whose kind the detector actually re-reports. A transform whose
    claimed relic ends up undetectable, e.g. degraded by a later
    transform in the same pass, or by a bookkeeping bug in a future
    transform, gets silently dropped from `injected` instead of leaking a
    phantom claim into `synth_error`/repair-row metadata. With the
    per-transform detectability gates (`_head_rfl_matches`,
    `_rename_candidates`'s filter) in place, this drop should never fire
    in practice; it is the structural backstop.

    `corrupt_tail` is fully deterministic given `(tail, rng, align)`.
    """
    applicable_names = [
        name for name, (is_applicable, _apply) in _TRANSFORMS.items() if is_applicable(tail, align)
    ]
    if not applicable_names:
        return None

    n = rng.randint(1, min(3, len(applicable_names)))
    order = list(applicable_names)
    rng.shuffle(order)

    text = tail
    injected: list[Relic] = []
    applied = 0
    for name in order:
        if applied >= n:
            break
        is_applicable, apply = _TRANSFORMS[name]
        if not is_applicable(text, align):
            # An earlier transform in this same pass consumed the only
            # occurrence this one needed. For example, `trailing` may
            # have already claimed the only eligible line `binder` would
            # also have targeted.
            continue
        result = apply(text, rng, align)
        if result is None:
            continue
        text, relics = result
        injected.extend(relics)
        applied += 1

    if not injected or text == tail:
        return None
    detected_kinds = {r.kind for r in find_relics(text, align)}
    if not detected_kinds:
        return None
    injected = [r for r in injected if r.kind in detected_kinds]
    if not injected:
        return None
    return text, injected


# ---------------------------------------------------------------------------
# Error synthesis and the repair-dataset coordination template
# ---------------------------------------------------------------------------


def synth_error(relics: list[Relic]) -> str:
    """Synthesize a Lean-compiler-shaped error message for a relic list.

    Only the FIRST relic decides the message. A real Lean compiler stops
    at, and reports, the first error it hits, so a multi-relic corrupted
    tail would, in reality, only ever surface one message to a repair
    loop at a time. The message shapes mimic the cases pinned in
    `tests/deduction/test_lean_lean3.py`, not the full fidelity of Lean's
    real diagnostics.

    Parameters
    ----------
    relics : list of Relic
        Relics to synthesize a message for, in scan/injection order
        (typically the return of `find_relics` or `corrupt_tail`'s
        `injected` list). Must be non-empty.

    Returns
    -------
    str
        - ``"unknown identifier '{text}'"`` for a `lean3-name` first relic.
        - ``"<stdin>:1:1: unknown tactic"`` for `refl` / `existsi` /
          `begin-end`.
        - ``"<stdin>:1:1: unexpected token ','; expected command"`` for
          `binder-comma` / `trailing-comma`.

    Raises
    ------
    ValueError
        If `relics` is empty, or its first element's `kind` is not one of
        the six kinds `find_relics` produces.
    """
    if not relics:
        raise ValueError("synth_error requires at least one relic")
    first = relics[0]
    if first.kind == "lean3-name":
        return f"unknown identifier '{first.text}'"
    if first.kind in ("refl", "existsi", "begin-end"):
        return "<stdin>:1:1: unknown tactic"
    if first.kind in ("binder-comma", "trailing-comma"):
        return "<stdin>:1:1: unexpected token ','; expected command"
    raise ValueError(f"unknown relic kind {first.kind!r}")


#: Fixed instruction suffix `build_repair_user` appends after the
#: previous-attempt code block (and error block, when present). This is a
#: module constant, not an f-string built inline in `build_repair_user`,
#: because it is a coordination contract: other work packages (the SFT
#: dataset builder, any repair-loop runner) format their prompts against
#: it byte-for-byte. One named constant keeps that contract greppable,
#: and stops one call site from accidentally rewording it.
_REPAIR_INSTRUCTIONS = (
    "The attempt above may use Lean 3 syntax or lemma names that Lean 4 / Mathlib 4\n"
    "rejects. If it is already valid Lean 4, output it unchanged; otherwise output the\n"
    "corrected Lean 4 tactics. Output only the tactic lines, nothing else."
)


def build_repair_user(user: str, attempt: str, error: str | None = None) -> str:
    """Append a previous-attempt repair block to a user turn.

    This function builds the exact coordination template the
    repair-dataset builder and repair-loop runner consume: the original
    user turn, followed by the previous (Lean-3-tainted) attempt in a
    fenced code block, an optional Lean-error block, and a fixed
    instruction to output corrected Lean 4 tactics (or the attempt
    unchanged, if it was already valid).

    Parameters
    ----------
    user : str
        The original user turn (e.g. `prompt.build_user_prompt`'s output).
    attempt : str
        The previous, possibly Lean-3-tainted, tactic-block attempt.
    error : str, optional
        A Lean compiler error message for `attempt` (typically
        `synth_error`'s output, or a real Lean error from a replay). When
        ``None``, the output includes no error block.

    Returns
    -------
    str
        ``user``, a blank line, ``"## Previous attempt"``, the fenced
        ```lean`` block containing `attempt`, then, only when `error` is
        given, a fenced error block, then `_REPAIR_INSTRUCTIONS`. This is
        a coordination constant: its exact byte layout matters to every
        downstream consumer, so this function deliberately does not
        expose extra parameters to modify it (whitespace, heading text,
        and so on are all fixed).
    """
    error_block = f"Lean reported:\n```\n{error}\n```\n\n" if error is not None else ""
    return (
        f"{user}\n\n"
        "## Previous attempt\n"
        f"```lean\n{attempt}\n```\n"
        f"{error_block}"
        f"{_REPAIR_INSTRUCTIONS}"
    )
