"""Detect and inject Lean 3 syntax and lemma-name relics.

Two Lean-3-isms survive SFT/LoRA training as a small residue: Lean 3
*syntax* (`refl` for `rfl`, `existsi` for `use`, `begin...end`, `λ x, e`
binders, trailing commas) and *mathlib3 lemma names* the mathlib4 port
renamed (`supr_le` -> `iSup_le`). `find_relics`/`has_relics` detect them
(the analyzer's `l3` leak-rate column, dataset QC); `corrupt_tail` injects
them to build repair-SFT rows -- corrupted tail as the "previous attempt",
clean tail as the target (see `build_repair_user`).

**Shared-vocabulary invariant: anything the corrupter can inject, the
detector must catch.** `corrupt_tail` enforces it mechanically, returning
`None` when `find_relics` does not corroborate the relics it injected, so
no repair row carries an "error" the model gets no signal for.

`lean3-name` detection and the `rename` transform need the Lean3<->Lean4
`#align` map, which `AlignMap.load` reads from a gzipped-JSON asset at
``corpus.data_root().parent / ALIGN_ASSET_NAME`` -- BESIDE the gitignored
benchmark download, per `corpus.replay_passing_path`'s committed-sidecar
layout. Every public function takes ``align=None``, which disables exactly
that rule and that transform, and never raises.

Stdlib plus `.corpus` only (no `lean_dojo`, no torch). `corrupt_tail` is
deterministic: its `random.Random` argument is the only randomness source,
so a build is byte-reproducible from its seed. Bracket depth (``⟨⟩ () []
{}``) accumulates cumulatively across lines, never reset per line, so an
unclosed ``⟨`` suppresses a trailing-comma flag several lines later;
string-literal contents are deliberately not skipped.
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

    Attributes
    ----------
    kind : str
        One of ``refl``, ``existsi``, ``binder-comma``, ``trailing-comma``,
        ``begin-end``, ``lean3-name``.
    text : str
        The offending token (``refl``/``existsi``/``lean3-name``) or stripped
        line (``begin-end``/``trailing-comma``, or the binder-through-comma
        snippet).
    fix : str or None
        The Lean 4 replacement; ``None`` where no single-token fix applies --
        ``begin-end``, and ``binder-comma`` (whose fix would mean guessing which
        arrow to insert).
    line : int
        0-indexed within the scanned text.
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

    mathlib4's `#align` directives record the mathlib3 name each Lean4
    declaration replaces. Real references are usually partially qualified
    (``iso.inv_comp_eq`` for ``category_theory.iso.inv_comp_eq``), so lookup
    also resolves a dotted suffix -- but only one that is unique across the
    whole map; an ambiguous partial name never silently picks a candidate.

    The constructor copies `lean3_to_lean4` and builds every lookup index
    (suffix buckets, the Lean4 suffix set, `reverse_unique`) once, since scans
    query them once per candidate token at dataset-build scale.
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
        """Alias of the constructor, spelled out for test/fixture call sites."""
        return cls(pairs)

    @classmethod
    def load(cls, path: Path | None = None) -> AlignMap | None:
        """Load the align map from its gzip-compressed JSON asset.

        Asset format: gzip-compressed UTF-8 JSON,
        ``{"lean3_to_lean4": {<lean3 name>: <lean4 name>, ...}}``.

        Parameters
        ----------
        path : Path, optional
            Defaults to ``corpus.data_root().parent / ALIGN_ASSET_NAME`` --
            beside the gitignored ~700 MB benchmark download, not inside it.
            `corpus.data_root()` is resolved at call time, not cached at import,
            so a caller (or test) that repoints ``SMOLBENCH_LEAN_DATA`` first
            gets the fresh path.

        Returns
        -------
        AlignMap or None
            ``None`` when the file does not exist. Absence is not an error:
            every other function here accepts ``align=None`` and degrades to
            parse-level-only detection/corruption.
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

        Order: exact Lean3 key; then `token`'s last two dotted components
        against a suffix bucket holding exactly one lean3 name (more specific,
        so checked first); then its last component likewise. ``None`` if nothing
        resolves, including when a matching bucket is ambiguous (>= 2
        candidates). `token` is expected already trimmed of trailing ``.``/``,``
        (see `_iter_candidate_tokens`).
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
        """True if `token` is a known Lean4 name, or a dotted suffix of one.

        The CLEAN guard in `find_relics`' ``lean3-name`` rule: a token that
        resolves via `lookup_lean3` is still not flagged when it is itself
        already valid Lean 4. Defense in depth -- unreachable with a
        well-formed align map.
        """
        return token in self._lean4_suffixes

    @property
    def reverse_unique(self) -> dict[str, str]:
        """Lean4 -> Lean3 name, restricted to Lean4 names with one preimage.

        Ambiguous inverses are dropped (see `__init__`), so the `rename`
        transform always injects an unambiguously corresponding Lean3 spelling.
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

    Head position = everything before the token on its line is empty, or ends
    with a `_REFL_HEAD_MARKERS` combinator. Single source of the predicate for
    both `find_relics`' rule 2 and the `rfl->refl` transform
    (`_head_rfl_matches`), which makes an injected `refl` re-detectable by
    construction: a term-position `rfl` (`exact rfl`) must not be targeted,
    since rule 2 deliberately does not flag `exact refl`.
    """
    p = line_prefix.rstrip()
    return p == "" or p.endswith(_REFL_HEAD_MARKERS)


def _iter_candidate_tokens(text: str) -> list[tuple[re.Match, str]]:
    """Extract lean3-name candidate ``(match, token)`` pairs from `text`.

    `token` is the raw match with a trailing ``.``/``,`` stripped (sentence or
    list punctuation, not part of the identifier). Only tokens of length >= 3
    containing a ``_`` or ``.`` are kept: a short plain identifier (`x`, `hx`,
    `n`) is never a lemma name and would dominate false positives. The
    `re.Match` spans the ORIGINAL, untrimmed token, so a caller needing the
    token's own span must use ``match.start()`` and ``match.start() +
    len(token)``, not ``match.end()``.
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

    Shared by `find_relics`' ``binder-comma`` rule and the `binder`
    transform. Depth is tracked *relative* to `start` (immediately past the
    `fun`/`λ` keyword), so a comma nested one level deeper does not count --
    in `fun ⟨a, b⟩ ↦ e` the comma is inside the just-opened `⟨`. `text` is
    the whole text, not one line, since a binder's arrow or comma may fall
    on the next line.

    Returns
    -------
    (str, int, int) or None
        ``("comma", i, i + 1)`` for the first depth-0 ``,``, or
        ``("arrow", i, j)`` for the first ``↦`` (``j = i + 1``) or ``=>``
        (``j = i + 2``), whichever comes first; ``None`` if neither appears.
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

    Applies six rules (see the inline comments), each precision-guarded against
    Lean 4 constructs that merely resemble a relic, and pinned by
    ``tests/deduction/test_lean_lean3.py``. Pure function: O(n) for the
    parse-level rules, plus one `AlignMap.lookup_lean3` and one
    `AlignMap.is_lean4_name` call per candidate token for the name rule. `text`
    may be multi-line; bracket depth accumulates across the whole text, never
    reset per line. With ``align=None`` the ``lean3-name`` rule is skipped and
    the other five still run.

    Returns
    -------
    list of Relic
        One per distinct ``(kind, text, line)`` triple, in scan order -- so two
        `refl` tactics on one line report as one relic. The five parse-level
        rules run line by line, top to bottom, in rule order; ``binder-comma``
        is a separate whole-text pass, since a binder's arrow or comma can
        follow a line break.
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
    """``bool(find_relics(text, align))`` -- a full scan, not short-circuited."""
    return bool(find_relics(text, align))


# ---------------------------------------------------------------------------
# Corruption
# ---------------------------------------------------------------------------


def _rename_lookup(tok: str, reverse_unique: dict[str, str]) -> str | None:
    """`tok`'s longest dotted suffix (itself included) keying `reverse_unique`.

    Longest-first, so a token carrying extra outer namespace qualification
    still resolves via its more specific suffix.
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
    """Renamable ``(match, token, truncated_lean3_spelling)`` triples in `text`.

    A candidate survives only if the spelling `_apply_rename` would write is
    itself flaggable by `find_relics`' rule 6, checked against rule 6's own
    predicate chain: it must differ from the original token (~8k ``#align``
    pairs are identity spellings like ``#align inv_inv inv_inv``, where a
    "rename" is a byte-level no-op); it must pass `_iter_candidate_tokens`'
    shape filter (len >= 3, contains ``_`` or ``.``); and `align.lookup_lean3`
    must resolve it while `align.is_lean4_name` rejects it, which excludes a
    bare name that is also a valid Lean4 suffix (``inv_comp_eq``). Otherwise
    the corrupter could inject a relic the detector never corroborates, making
    `synth_error` claim ``unknown identifier 'inv_inv'`` about valid Lean 4.
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

    The replacement is the `reverse_unique` Lean3 name TRUNCATED to the token's
    own number of dotted components -- a 2-component token resolving to
    ``category_theory.iso.inv_comp_eq`` becomes ``iso.inv_comp_eq`` -- mimicking
    a partially-qualified mathlib3 reference rather than inventing an
    implausible fully-qualified name.
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

    Shares `_is_head_position` with rule 2: a term-position `rfl` (`exact
    rfl`, `⟨rfl, h⟩`) rewritten to `refl` would not be re-detected.
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

    "Depth-0" is the binder keyword's own cumulative bracket depth, not
    `_binder_forward_scan`'s relative depth: the `binder` transform corrupts
    only a top-level binder. A binder already followed by a comma before any
    arrow is already a `binder-comma` relic with nothing left to corrupt, so a
    ``"comma"`` scan result counts as no match.

    Returns
    -------
    (re.Match, int, int) or None
        ``(binder_match, arrow_start, arrow_end)``, or ``None`` if no binder
        qualifies.
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

    Removing the arrow is the mandatory part -- that is what makes it a
    `binder-comma` relic. `fun` also becomes `λ` because Lean 3 has no `fun`
    keyword, so `fun x, e` would be a syntax the detector flags but Lean 3 never
    produced.
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
    already comma-terminated.
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

    The only transform that can inject several relics at once. A random
    subset, rather than every eligible line, mimics a model dropping commas
    inconsistently rather than uniformly.
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

    Draws ``n = rng.randint(1, min(3, len(applicable)))`` of the five transforms
    (`rename`, `rfl->refl`, `binder`, `trailing`, `use->existsi`) applicable to
    `tail`, shuffles them (seeded), and applies them against the *evolving*
    text, re-checking applicability immediately before each and skipping
    no-ops -- an earlier transform can consume what a later one needed.

    Deterministic given ``(tail, rng-state, align)``: `rng` is the only
    randomness source. `tail` is assumed Lean-3-relic-free. With ``align=None``
    the `rename` transform is never applicable (it needs
    `AlignMap.reverse_unique`); the other four are unaffected.

    Returns
    -------
    (str, list of Relic) or None
        ``(corrupted, injected)``. The post-condition re-runs
        `find_relics(corrupted, align)` and keeps only injected relics whose
        kind the detector re-reports, so ``{r.kind for r in injected}`` is a
        subset of the detected kinds BY CONSTRUCTION (the shared-vocabulary
        invariant) and no phantom claim leaks into `synth_error` / repair-row
        metadata. ``None`` when no transform is applicable, when every attempt
        is a no-op, when ``corrupted == tail``, or when the post-condition
        leaves `injected` empty.
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

    Only the FIRST relic decides the message: a real compiler stops at and
    reports its first error, so a multi-relic tail would only ever surface one
    message to a repair loop. Shapes mimic the cases pinned in
    ``tests/deduction/test_lean_lean3.py``, not Lean's real diagnostics.

    - ``"unknown identifier '{text}'"`` for a `lean3-name` first relic.
    - ``"<stdin>:1:1: unknown tactic"`` for `refl` / `existsi` / `begin-end`.
    - ``"<stdin>:1:1: unexpected token ','; expected command"`` for
      `binder-comma` / `trailing-comma`.

    Raises
    ------
    ValueError
        If `relics` is empty, or its first element's `kind` is not one of the
        six kinds `find_relics` produces.
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

    Layout: `user`, a blank line, ``"## Previous attempt"``, the fenced
    ```lean`` block holding `attempt`, then -- only when `error` is given
    (typically `synth_error`'s output, or a real replay error) -- a fenced error
    block, then `_REPAIR_INSTRUCTIONS`. Those exact bytes are a coordination
    contract the repair-dataset builder and repair-loop runner format against,
    so this deliberately exposes no parameters to vary them.
    """
    error_block = f"Lean reported:\n```\n{error}\n```\n\n" if error is not None else ""
    return (
        f"{user}\n\n"
        "## Previous attempt\n"
        f"```lean\n{attempt}\n```\n"
        f"{error_block}"
        f"{_REPAIR_INSTRUCTIONS}"
    )
