"""Detect and (for training-data purposes) inject Lean 3 syntax and lemma-name relics.

Pilot evals of `smolbench.deduction.lean` showed two Lean-2-ism failure modes
that survive SFT/LoRA training in small residue: **Lean 3 tactic syntax**
(`refl` instead of `rfl`, `existsi` instead of `use`, comma-terminated
`begin...end` blocks, `λ x, e` binders instead of `fun x ↦ e` / `λ x ↦ e`,
trailing commas after tactics) and **mathlib3 lemma names** that were renamed
or restructured in the mathlib4 port (`supr_le` -> `iSup_le`,
`iso.inv_comp_eq` -> `Iso.inv_comp_eq`). This module is the shared detector
and corrupter both downstream consumers need:

- **Detection** (`find_relics` / `has_relics`) -- used by the run analyzer to
  compute an `l3` leak-rate column over a model's generated tactic blocks,
  and by dataset-QC tooling to sanity-check that a training corpus is clean.
- **Corruption** (`corrupt_tail`) -- used by the auxiliary SFT dataset
  builder to turn a clean, ground-truth Lean 4 tactic tail into a
  Lean-3-flavored "previous attempt", paired with the clean tail as the
  target. This teaches a model the *repair* move (see `build_repair_user`),
  rather than only ever seeing clean Lean 4 in training.

Shared-vocabulary invariant
----------------------------
Detection and corruption are two faces of the same rule set, and must never
drift apart: **anything the corrupter can inject, the detector must catch.**
This is not just documentation -- it is mechanically enforced by
`corrupt_tail`'s post-condition (`find_relics(corrupted, align)` must be
non-empty, or the corruption attempt is discarded and `None` is returned).
A corruption transform that silently produced undetectable relics would
poison the repair dataset with rows whose "error" the model can never
observe a signal for, so this check is not optional. The five corruption
transforms below are literally named after the Lean4->Lean3 syntactic
*inverse* of one detection rule each (`rfl->refl` undoes the fix for the
`refl` rule, `use->existsi` undoes the fix for the `existsi` rule, etc.),
which is what keeps the two sides in lockstep by construction rather than by
convention alone.

The `#align` asset and graceful degradation
--------------------------------------------
Lemma-name detection (`lean3-name`) and the `rename` corruption transform
both need a Lean3<->Lean4 name map, loaded from a small gzip-compressed JSON
asset (`ALIGN_ASSET_NAME`, resolved BESIDE the benchmark dataset directory --
``corpus.data_root().parent`` -- by default, the committed-sidecar layout
`corpus.replay_passing_path` documents: small committed artifacts live next
to, never inside, the wholesale-gitignored ``leandojo_benchmark_4/`` download).
That asset is built by `scripts/build_lean3_align_map.py`, which mines the
traced mathlib4 snapshot's `#align` directives (mathlib4's own compatibility
shims recording each declaration's mathlib3 name) -- this module does not
build or validate the asset itself, only consumes it via `AlignMap`.

Every public function in this module accepts `align: AlignMap | None = None`
and degrades gracefully when it is absent: `align=None` disables the
name-map-dependent rule (`lean3-name` in `find_relics`) and transform
(`rename` in `corrupt_tail`) without raising, leaving parse-level-only
detection/corruption (Lean 3 *syntax*, not lemma names) fully functional.
This lets callers that have not yet bootstrapped the align asset (or are
running in an environment without `notebooks/lean/data/`) still get useful
signal.

Design constraints
-------------------
- Dependency-free beyond the standard library plus `.corpus` (for
  `data_root()` only, imported lazily at call time inside `AlignMap.load` --
  see its docstring). No `lean_dojo`, no torch/datasets -- this module must
  import cleanly on the main py3.14 venv.
- Fully deterministic: `corrupt_tail` takes an explicit `random.Random`
  instance and never reads global random state or wall-clock time, so a
  training-data build is byte-for-byte reproducible from its seed.
- Bracket-depth tracking (across ``⟨⟩ () [] {}``) is required by several
  rules and is **cumulative across lines**, not reset per line -- an
  unclosed ``⟨`` several lines up correctly suppresses a trailing-comma
  flag several lines later (e.g. a multi-line ``refine ⟨foo,\\n  bar⟩``).
  The scanner does not attempt to skip over string-literal contents (Lean
  tactic strings essentially never contain the bracket/comma characters this
  module cares about in the pilot data this was built against); this is a
  known, deliberate limitation rather than an oversight.
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

#: Filename of the Lean3->Lean4 `#align` name-map asset, resolved by default
#: at ``corpus.data_root() / ALIGN_ASSET_NAME``. Built by
#: ``scripts/build_lean3_align_map.py`` (see the module docstring).
ALIGN_ASSET_NAME = "lean3_align.json.gz"


@dataclass(frozen=True)
class Relic:
    """One Lean 3 relic found by `find_relics` (or claimed by `corrupt_tail`).

    Parameters
    ----------
    kind : str
        One of ``"refl"``, ``"existsi"``, ``"binder-comma"``,
        ``"trailing-comma"``, ``"begin-end"``, ``"lean3-name"`` -- see the
        module-level detection rules in `find_relics`.
    text : str
        The offending token or line snippet that triggered the flag.
        Exact shape depends on `kind`: a bare tactic keyword for
        ``"refl"``/``"existsi"``, the stripped line for
        ``"begin-end"``/``"trailing-comma"``, the token itself for
        ``"lean3-name"``, and the binder-through-comma snippet for
        ``"binder-comma"``.
    fix : str or None
        The known Lean 4 replacement (``"rfl"``, ``"use"``, the aligned
        Lean 4 name, or the line with its trailing comma removed), or
        ``None`` when no single-token fix applies (``"begin-end"``,
        ``"binder-comma"`` -- removing a Lean3-style binder comma requires
        knowing what arrow to insert, which this module does not guess).
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
    mathlib3 name the Lean4 declaration replaces. Names are frequently
    referenced in the wild (and in pilot model outputs) via a shorter,
    unqualified or partially-qualified form -- e.g. ``iso.inv_comp_eq``
    instead of the full ``category_theory.iso.inv_comp_eq`` -- so exact
    string matching alone misses most real occurrences. This class adds
    conservative suffix matching: a query resolves via a dotted suffix only
    when that suffix is unique across the whole map, so an ambiguous partial
    name (one that could refer to two different declarations) never
    silently picks one.

    Parameters
    ----------
    lean3_to_lean4 : dict of str -> str
        Mapping from full mathlib3 declaration name to its mathlib4
        replacement name. Copied on construction (the instance owns its own
        dict; mutating the caller's dict afterward has no effect on this
        `AlignMap`).

    Notes
    -----
    All lookup indexes (suffix buckets, the Lean4 suffix set, and
    `reverse_unique`) are built once here, not recomputed per lookup --
    `find_relics` and `corrupt_tail` call `lookup_lean3` / `is_lean4_name` /
    `reverse_unique` once per candidate token in a scan, so this matters for
    dataset-build-scale usage.
    """

    def __init__(self, lean3_to_lean4: dict[str, str]) -> None:
        self.lean3_to_lean4: dict[str, str] = dict(lean3_to_lean4)

        # Suffix indexes over the LEAN3 keys, bucketed by their last one and
        # last two dotted components (value = every full lean3 name sharing
        # that suffix). `lookup_lean3` resolves a query token against these
        # buckets when it isn't an exact key, and only when the bucket has
        # exactly one member -- an ambiguous suffix (two different lean3
        # names sharing it) must never guess.
        self._suffix1: dict[str, set[str]] = {}
        self._suffix2: dict[str, set[str]] = {}
        for lean3_name in self.lean3_to_lean4:
            parts = lean3_name.split(".")
            self._suffix1.setdefault(parts[-1], set()).add(lean3_name)
            if len(parts) >= 2:
                self._suffix2.setdefault(".".join(parts[-2:]), set()).add(lean3_name)

        # Every component-boundary dotted suffix of every LEAN4 value
        # (including the full name itself, at the i=0 suffix), for
        # `is_lean4_name`'s "is this token already valid Lean 4" guard.
        self._lean4_suffixes: set[str] = set()
        for lean4_name in self.lean3_to_lean4.values():
            parts = lean4_name.split(".")
            for i in range(len(parts)):
                self._lean4_suffixes.add(".".join(parts[i:]))

        # lean4 -> lean3, restricted to lean4 names with a UNIQUE lean3
        # preimage. `rename` (the corruption transform) must never corrupt
        # a Lean4 name into an arbitrarily-chosen one of several equally
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

        Convenience constructor for tests and small fixtures -- identical to
        ``AlignMap(pairs)``, spelled out for readability at call sites.

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
            Explicit asset path. When omitted (the default), resolves to
            ``corpus.data_root().parent / ALIGN_ASSET_NAME`` -- BESIDE the
            gitignored benchmark dataset dir, not inside it, matching the
            committed-sidecar layout of `corpus.replay_passing_path` (the
            asset is a small committed artifact; ``data_root()`` itself is
            the wholesale-gitignored ~700 MB download). `corpus.data_root()`
            is called here, at call time -- not cached at import time --
            so a caller (including tests) that repoints the
            ``SMOLBENCH_LEAN_DATA`` environment variable before calling
            `load` gets the freshly-resolved path.

        Returns
        -------
        AlignMap or None
            The loaded map, or ``None`` if the asset file does not exist.
            Absence is not an error: every other function in this module
            accepts ``align=None`` and degrades to parse-level-only
            detection/corruption (see the module docstring), so a caller
            that has not bootstrapped the align asset yet still gets useful
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
            2. `token`'s last-two dotted components match a suffix bucket
               with exactly one candidate lean3 name (checked before the
               1-component bucket, since a 2-component match is more
               specific).
            3. `token`'s last-one dotted component matches a suffix bucket
               with exactly one candidate.

            ``None`` if none of the above resolve, including the case where
            a suffix bucket exists but is ambiguous (>= 2 candidates).
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

        Used as the CLEAN guard in `find_relics`'s ``lean3-name`` rule: a
        token that already resolves via `lookup_lean3` should still not be
        flagged if it is itself already valid Lean 4 (defense in depth --
        with a well-formed align map this should be unreachable, since a
        Lean4 name should not simultaneously collide with a Lean3 suffix
        bucket, but the guard costs nothing and the spec calls for it
        explicitly).

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
            Entries of `lean3_to_lean4` inverted, keeping only Lean4 names
            with exactly one Lean3 preimage (see `__init__` for why
            ambiguous inverses are dropped). Used by the `rename`
            corruption transform to pick a Lean3 spelling to inject that is
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
#: `rename` corruption transform. Broad on purpose (includes `!`/`?`/`'`,
#: valid trailing characters in Lean identifiers, plus `.` for dotted
#: qualification, plus the subscript digits ``₀``-``₉`` (U+2080-U+2089) that
#: Mathlib names routinely end with, e.g. ``div_mul_cancel₀`` -- omitting
#: them split such identifiers mid-name, so the `rename` transform could
#: rewrite the alphabetic stem while stranding the subscript, producing a
#: Frankenstein token (``div_mul_cancel'₀``) that matched neither the Lean3
#: nor the Lean4 spelling of anything) -- callers filter and trim the raw
#: match (see `_iter_candidate_tokens`).
_CANDIDATE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'.!?₀-₉]*")

#: `refl`/`existsi` are plain-word Lean tactics; matched with `\b` word
#: boundaries so e.g. `le_refl` (no boundary before "refl", `_` is a `\w`
#: char) and `existsi_something` are not mistaken for the bare tactic.
_REFL_RE = re.compile(r"\brefl\b")
_EXISTSI_RE = re.compile(r"\bexistsi\b")

#: The Lean4 `rfl` tactic token -- distinct from `_REFL_RE` above (which
#: matches the Lean3 tactic `refl` for detection). Used only by the
#: `rfl->refl` corruption transform, which looks for `rfl` to corrupt INTO
#: `refl`.
_RFL_RE = re.compile(r"\brfl\b")

#: `fun`/`λ` binder keyword. `λ` is a Unicode letter, so plain `\b` already
#: requires a non-word char (e.g. whitespace) on either side of it -- no
#: special-casing needed beyond the ordinary `\b`.
_BINDER_RE = re.compile(r"\b(?:fun|λ)\b")

#: Prefixes (after stripping trailing whitespace from the text preceding a
#: `refl` match) that put `refl` in "tactic-head position" per the spec:
#: line start (checked separately as an empty prefix), or right after one of
#: these tactic-combinator markers.
_REFL_HEAD_MARKERS = (";", "<;>", "·", "{")  # ';' '<;>' '·' '{'


def _is_head_position(line_prefix: str) -> bool:
    """True if text following `line_prefix` sits in tactic-head position.

    The single source of the "tactic-head position" predicate shared by
    `find_relics`'s rule 2 (detecting the Lean 3 `refl` tactic) and the
    `rfl->refl` corruption transform (`_head_rfl_matches`): a token is in
    head position when everything before it on its line is empty or ends
    with one of `_REFL_HEAD_MARKERS`. Keeping detector and corrupter on one
    predicate is what makes an injected `refl` relic re-detectable by
    construction (the shared-vocabulary invariant) -- a `rfl` rewritten in
    term position (`exact rfl`) would produce `exact refl`, which rule 2
    deliberately does NOT flag, so the transform must not target it either.
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
        One ``(match, token)`` pair per candidate, where `token` is the raw
        regex match with a trailing ``.``/``,`` stripped (sentence/list
        punctuation, not part of the identifier), filtered to tokens of
        length >= 3 that contain a ``_`` or ``.`` -- short, plain
        identifiers (`x`, `hx`, `n`) are never lemma names and would
        otherwise dominate false-positive matches. The `re.Match` gives the
        ORIGINAL (untrimmed) span; callers that need the token's own span
        use ``match.start()`` and ``match.start() + len(token)`` (the
        trimmed length), not ``match.end()``.
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

    Implements the shared "scanning forward from the binder AT THE BINDER'S
    OWN bracket depth" rule used by both `find_relics`'s ``binder-comma``
    detection and the `binder` corruption transform: depth is tracked
    *relative* to `start` (the position immediately after the `fun`/`λ`
    keyword), so a comma nested one level deeper than the binder (e.g. in
    `fun ⟨a, b⟩ ↦ e`, nested inside the just-opened `⟨`) does not count.

    Parameters
    ----------
    text : str
        Full text being scanned (not just one line -- a binder near a
        line's end could, in principle, have its arrow/comma on the next
        line, and bracket depth is cumulative across lines throughout this
        module).
    start : int
        Absolute index to start scanning from (typically
        ``binder_match.end()``).

    Returns
    -------
    (str, int, int) or None
        ``("comma", i, i + 1)`` for the first depth-0 ``,``, or
        ``("arrow", i, j)`` for the first ``↦`` (``j = i + 1``) or ``=>``
        (``j = i + 2``), whichever occurs first in scan order. ``None`` if
        neither is found before the end of `text`.
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
    """Scan `text` for Lean 3 syntax and (optionally) mathlib3 lemma names.

    Applies six detection rules (see the inline comments below for each);
    all are precision-guarded against real Lean 4 constructs that
    superficially resemble a Lean 3 relic, validated against pilot model
    outputs (see ``tests/test_lean_lean3.py`` for the exact CLEAN/FLAGGED
    cases this was built against).

    Parameters
    ----------
    text : str
        Tactic-block text to scan (typically one model generation's
        extracted tactic lines, or a training-data tail). May be
        multi-line; bracket depth is tracked cumulatively across the whole
        text, not reset per line.
    align : AlignMap, optional
        Lean3->Lean4 name map. When ``None``, the ``lean3-name`` rule is
        skipped entirely (graceful degradation -- see the module
        docstring); the other five rules are parse-level and always run.

    Returns
    -------
    list of Relic
        One `Relic` per distinct ``(kind, text, line)`` triple found, in
        scan order (the five parse-level rules are checked line-by-line
        top to bottom, in rule order, except ``binder-comma`` which is
        scanned as a separate pass over the whole text since a binder's
        arrow/comma can in principle follow a line break). Duplicate
        ``(kind, text, line)`` triples collapse to a single `Relic` --
        e.g. two `refl` tactics on one line report as one relic.

    Notes
    -----
    Pure function; does not mutate `text` or `align`. O(n) in the length of
    `text` for the parse-level rules; the ``lean3-name`` rule additionally
    does one `AlignMap.lookup_lean3` / `AlignMap.is_lean4_name` call per
    candidate token (each O(1) average, via the suffix-bucket indexes built
    once in `AlignMap.__init__`).
    """
    relics: list[Relic] = []
    seen: set[tuple[str, str, int]] = set()

    def emit(kind: str, rtext: str, fix: str | None, line: int) -> None:
        key = (kind, rtext, line)
        if key not in seen:
            seen.add(key)
            relics.append(Relic(kind=kind, text=rtext, fix=fix, line=line))

    lines = text.split("\n")

    # Cumulative bracket depth AFTER each line's own characters -- rule 5
    # (trailing-comma) needs depth accumulated from the START of the whole
    # text, not reset per line, so an unbalanced open bracket several lines
    # up correctly suppresses a flag several lines later.
    depth_after_line: list[int] = []
    running = 0
    for line in lines:
        for ch in line:
            running += _bracket_delta(ch)
        depth_after_line.append(running)

    for lineno, line in enumerate(lines):
        stripped = line.strip()

        # Rule 1: begin/end block markers (removed wholesale in Lean 4;
        # tactic blocks are just indentation, no wrapper keywords).
        if stripped in ("begin", "end") or stripped.startswith("begin "):
            emit("begin-end", stripped, None, lineno)

        # Rule 2: `refl` only in tactic-head position (line start, or right
        # after a tactic-combinator marker) -- excludes `le_refl x` and
        # `Equiv.refl` (a lemma name / namespaced identifier, not the bare
        # tactic), which `\brefl\b` alone would NOT exclude (the `.` before
        # `refl` in `Equiv.refl` is itself a word boundary).
        for m in _REFL_RE.finditer(line):
            if _is_head_position(line[: m.start()]):
                emit("refl", "refl", "rfl", lineno)

        # Rule 3: `existsi` -- removed in Lean 4 outright, so unlike `refl`
        # any occurrence (not just tactic-head) is a relic.
        if _EXISTSI_RE.search(line):
            emit("existsi", "existsi", "use", lineno)

        # Rule 5: trailing comma while cumulative depth is 0 -- a comma
        # inside an still-open `⟨`/`(`/`[`/`{` (e.g. multi-line
        # `refine ⟨foo,`) is legitimate Lean 4 term syntax, not a relic.
        if stripped.endswith(",") and depth_after_line[lineno] == 0:
            emit("trailing-comma", stripped, stripped[:-1].rstrip(), lineno)

        # Rule 6: mathlib3 lemma/def names, only when an align map is given.
        if align is not None:
            for _m, tok in _iter_candidate_tokens(line):
                mapped = align.lookup_lean3(tok)
                if mapped is not None and not align.is_lean4_name(tok):
                    emit("lean3-name", tok, mapped, lineno)

    # Rule 4: binder-comma. A separate whole-text pass (see
    # `_binder_forward_scan`'s docstring for why it isn't line-bounded).
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
        ``bool(find_relics(text, align))``. Provided as a readable,
        short-circuiting-in-spirit convenience for QC call sites that only
        need a yes/no answer (the analyzer's `l3` leak-rate column, dataset
        cleanliness assertions) without constructing the full relic list at
        the call site -- though note this is a thin wrapper, not a
        short-circuited scan: `find_relics` still runs to completion.
    """
    return bool(find_relics(text, align))


# ---------------------------------------------------------------------------
# Corruption
# ---------------------------------------------------------------------------


def _rename_lookup(tok: str, reverse_unique: dict[str, str]) -> str | None:
    """`tok`'s longest dotted suffix (itself included) keying `reverse_unique`.

    Checked longest-suffix-first (`tok` itself, then its last-``n-1``
    components, ...) so a token with extra outer namespace qualification
    beyond what the align map recorded still resolves via its more specific
    (longer) suffix in preference to a shorter, less specific one.
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
    replacement `_apply_rename` would actually write -- see that docstring
    for the truncation rule) is itself DETECTABLE by `find_relics`'s rule 6,
    checked with rule 6's exact predicate chain:

    - it must differ from the original token -- ~8k of mathlib4's `#align`
      pairs are identity spellings (``#align inv_inv inv_inv``), for which
      a "rename" would be a byte-level no-op that still claimed a
      lean3-name relic;
    - it must pass `_iter_candidate_tokens`'s token-shape filter (length
      >= 3, contains ``_`` or ``.``), or rule 6 never even tokenizes it;
    - `align.lookup_lean3` must resolve it and `align.is_lean4_name` must
      reject it -- rule 6's own flag condition. Bare snake_case names that
      are also valid Lean4 suffixes (``inv_comp_eq``) fail the second half
      and are correctly excluded here too.

    Without this filter the corrupter could inject relics the detector can
    never corroborate, poisoning `synth_error` with claims like
    ``unknown identifier 'inv_inv'`` about a perfectly valid Lean 4 name
    (found and adversarially confirmed in review, 2026-07-12).
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
            continue  # identity #align pair -- no-op "rename"
        if len(truncated) < 3 or ("_" not in truncated and "." not in truncated):
            continue  # would not even tokenize as a rule-6 candidate
        if align.lookup_lean3(truncated) is None or align.is_lean4_name(truncated):
            continue  # rule 6 would not flag the replacement
        out.append((m, tok, truncated))
    return out


def _rename_applicable(text: str, align: AlignMap | None) -> bool:
    return bool(_rename_candidates(text, align))


def _apply_rename(
    text: str, rng: random.Random, align: AlignMap | None
) -> tuple[str, list[Relic]] | None:
    """`rename`: replace one seeded-chosen Lean4 name with its Lean3 spelling.

    The replacement is the matched `reverse_unique` Lean3 name TRUNCATED to
    the same number of dotted components as the original token (e.g. a
    2-component token resolving to the 3-component lean3 name
    ``category_theory.iso.inv_comp_eq`` is replaced with the last 2
    components, ``iso.inv_comp_eq`` -- never the full name). This mimics
    how a partially-qualified Lean4 reference would look if mathlib3 had
    been referenced the same way, rather than inventing an implausible
    fully-qualified Lean3 name out of a short Lean4 token.
    """
    candidates = _rename_candidates(text, align)
    if not candidates:
        return None
    # Truncation (and the detectability filter on the truncated spelling)
    # happens inside `_rename_candidates`, so applicability and application
    # cannot disagree about which tokens are renamable.
    m, tok, truncated = rng.choice(candidates)
    start = m.start()
    end = start + len(tok)  # `tok` may be shorter than `m.group(0)` -- see
    # `_iter_candidate_tokens` (trailing `.`/`,` stripped).
    new_text = text[:start] + truncated + text[end:]
    lineno = text.count("\n", 0, start)
    # Recompute `.fix` via `align.lookup_lean3` (rather than reusing
    # `lean3_full`) so the claimed relic's `.fix` is exactly what an
    # independent `find_relics` call on `new_text` would derive -- the
    # shared-vocabulary invariant this module is built around.
    fix = align.lookup_lean3(truncated) if align is not None else None
    return new_text, [Relic(kind="lean3-name", text=truncated, fix=fix, line=lineno)]


def _head_rfl_matches(text: str) -> list[re.Match]:
    """`rfl` tokens in tactic-head position -- the only corruptible ones.

    Shares `_is_head_position` with `find_relics`'s rule 2: a `rfl` in term
    position (`exact rfl`, `⟨rfl, h⟩`) rewritten to `refl` would NOT be
    re-detected (rule 2 only flags tactic-head `refl`), so the transform
    must not target it -- an adversarially-confirmed review finding
    (2026-07-12) showed the unrestricted rewrite injecting phantom `refl`
    relics that broke the shared-vocabulary invariant and mis-classed
    `synth_error` output.
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

    "Depth-0" here is the binder keyword's own cumulative bracket depth
    (not the forward-scan-relative depth `_binder_forward_scan` uses) --
    the `binder` transform only corrupts a *top-level* binder, matching the
    spec's "first depth-0 fun/λ". A binder already followed by a comma
    before any arrow is already a `binder-comma` relic, not a target for
    this transform (it has nothing left to corrupt), so those are skipped
    (`_binder_forward_scan` returning `"comma"` is treated as no match).

    Returns
    -------
    (re.Match, int, int) or None
        ``(binder_match, arrow_start, arrow_end)`` for the first qualifying
        binder, or ``None`` if none exists.
    """
    for m in _BINDER_RE.finditer(text):
        # Texts here are proof-tail-sized (a handful of lines) so re-walking
        # the prefix per candidate binder is cheap; avoids threading a
        # separate running-depth accumulator through this small helper.
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

    Only the arrow is mandatory to remove (that is what makes the binder a
    `binder-comma` relic); `fun` is additionally rewritten to `λ` because
    Lean 3 has no `fun` keyword at all, so a corrupted `fun x, e` would be
    a syntax the detector correctly flags but that Lean 3 itself never
    produced -- `λ x, e` is more faithful to the real pilot failure mode.
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

    Eligible = non-blank, cumulative bracket depth 0 at line end, and not
    already ending in a comma (nothing new to corrupt there).
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

    Unlike the other four transforms (each touching exactly one location),
    this one can inject multiple relics in a single application -- picking
    a random non-empty subset (rather than always all eligible lines)
    mimics a model dropping commas inconsistently rather than uniformly
    across an entire proof.
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
#: `(text, rng, align) -> (new_text, [Relic injected, ...])`, or `None` if
#: -- despite `_IsApplicable` having returned True -- applying it turned out
#: to be a no-op (should not normally happen, but `corrupt_tail` treats it
#: as "this transform contributed nothing" rather than asserting).
_Apply = Callable[[str, random.Random, AlignMap | None], tuple[str, list[Relic]] | None]

#: `(is_applicable, apply)` pairs, keyed by transform name, in the fixed
#: order `corrupt_tail` considers them for its "which are applicable" scan.
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

    Picks a seeded random subset of the five corruption transforms
    (`rename`, `rfl->refl`, `binder`, `trailing`, `use->existsi` -- see
    their individual docstrings) and applies them in sequence, then
    validates the shared-vocabulary post-condition before returning.

    Parameters
    ----------
    tail : str
        Clean (assumed Lean-3-relic-free) ground-truth Lean 4 tactic text
        to corrupt -- typically an SFT dataset's target tail.
    rng : random.Random
        Source of randomness. `corrupt_tail` reads no other random or
        global state, so identical `(tail, rng-state, align)` always
        produces identical output -- callers get reproducibility by
        constructing a fresh `random.Random(seed)` per call (or per row).
    align : AlignMap, optional
        Lean3<->Lean4 name map. When ``None``, the `rename` transform is
        never applicable (it needs `AlignMap.reverse_unique`); the other
        four transforms are unaffected.

    Returns
    -------
    (str, list of Relic) or None
        ``(corrupted, injected)`` where `corrupted` is `tail` with 1 to 3
        transforms applied and `injected` lists the `Relic`s the applied
        transforms claim to have introduced, CORROBORATED against a fresh
        `find_relics(corrupted, align)` call: any claimed relic whose
        `kind` the detector does not re-report on the final text is
        dropped, so ``{r.kind for r in injected}`` is a subset of the
        detector's kinds BY CONSTRUCTION (the shared-vocabulary
        invariant, enforced structurally rather than assumed). Returns
        ``None`` if:

        - no transform is applicable to `tail` at all, or
        - every applicable transform, once actually attempted (an earlier
          transform in the same pass can consume the only occurrence a
          later one needed), turned out to make no change, or
        - the post-condition fails: `find_relics(corrupted, align)` comes
          back empty, or corroboration drops EVERY claimed relic (either
          would leave downstream `synth_error` with nothing truthful to
          say), or
        - `corrupted == tail` (degenerate no-op).

    Notes
    -----
    Algorithm: compute which of the five transforms are applicable to
    `tail` as given; if none, return `None` immediately. Otherwise draw
    ``n = rng.randint(1, min(3, len(applicable)))``, shuffle the applicable
    names (seeded), and apply the first `n` of them in that order against
    the *evolving* text -- each transform is re-checked for applicability
    against the current text immediately before it runs (an already-applied
    transform may have consumed what a later one needed) and skipped if it
    is no longer applicable or its own application is a no-op. `injected`
    accumulates the `Relic`(s) each transform that *did* apply reports for
    itself; each transform's relic-construction mirrors `find_relics`'s own
    field semantics exactly (see e.g. `_apply_rename`'s `.fix`
    recomputation). The final post-condition then CORROBORATES the claims:
    it re-runs `find_relics` on the corrupted text and keeps only the
    injected relics whose kind the detector actually re-reports -- a
    transform whose claimed relic ended up undetectable (e.g. degraded by
    a later transform in the same pass, or a bookkeeping bug in a future
    transform) is silently dropped from `injected` rather than leaking a
    phantom claim into `synth_error`/repair-row metadata. With the
    per-transform detectability gates (`_head_rfl_matches`,
    `_rename_candidates`' filter) this drop should never fire in practice;
    it is the structural backstop.

    Fully deterministic given `(tail, rng, align)`.
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
            # occurrence this one needed (e.g. `trailing` claimed the only
            # eligible line `binder` would also have targeted).
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

    Only the FIRST relic decides the message -- a real Lean compiler stops
    at (and reports) the first error it hits, so a multi-relic corrupted
    tail would, in reality, only ever surface one message to a repair loop
    at a time. The message shapes mimic what was actually observed in
    pilot runs (see `tests/test_lean_lean3.py`), not the full fidelity of
    Lean's actual diagnostics.

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


#: Fixed instruction suffix appended by `build_repair_user` after the
#: previous-attempt code block (and error block, when present). A module
#: constant -- and NOT an f-string built inline in `build_repair_user` --
#: because it is a coordination contract other work packages (the SFT
#: dataset builder, any repair-loop runner) format their prompts against
#: byte-for-byte; keeping it as one named constant makes that contract
#: greppable and impossible to accidentally reword at one call site only.
_REPAIR_INSTRUCTIONS = (
    "The attempt above may use Lean 3 syntax or lemma names that Lean 4 / Mathlib 4\n"
    "rejects. If it is already valid Lean 4, output it unchanged; otherwise output the\n"
    "corrected Lean 4 tactics. Output only the tactic lines, nothing else."
)


def build_repair_user(user: str, attempt: str, error: str | None = None) -> str:
    """Append a previous-attempt repair block to a user turn.

    Builds the exact coordination template consumed by the repair-dataset
    builder / repair-loop runner: the original user turn, followed by the
    previous (Lean-3-tainted) attempt in a fenced code block, an optional
    Lean-error block, and a fixed instruction to output corrected Lean 4
    tactics (or the attempt unchanged, if it was already valid).

    Parameters
    ----------
    user : str
        The original user turn (e.g. `prompt.build_user_prompt`'s output).
    attempt : str
        The previous (possibly Lean-3-tainted) tactic-block attempt.
    error : str, optional
        A Lean compiler error message for `attempt` (typically
        `synth_error`'s output, or a real Lean error from a replay). When
        ``None``, no error block is included.

    Returns
    -------
    str
        ``user``, blank line, ``"## Previous attempt"``, the fenced
        ```lean`` block containing `attempt`, then (only when `error` is
        given) a fenced error block, then `_REPAIR_INSTRUCTIONS`. This is a
        coordination constant -- its exact byte layout matters to every
        downstream consumer, so it is deliberately not modifiable via extra
        parameters (whitespace, heading text, etc. are all fixed).
    """
    error_block = f"Lean reported:\n```\n{error}\n```\n\n" if error is not None else ""
    return (
        f"{user}\n\n"
        "## Previous attempt\n"
        f"```lean\n{attempt}\n```\n"
        f"{error_block}"
        f"{_REPAIR_INSTRUCTIONS}"
    )
