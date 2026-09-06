"""Detect and inject Lean 3 syntax relics.

Lean 3 *syntax* survives SFT/LoRA training as a small residue: `refl` for
`rfl`, `existsi` for `use`, `begin...end`, `λ x, e` binders, trailing commas.
`find_relics`/`has_relics` detect it (the analyzer's `l3` leak-rate column,
dataset QC); `corrupt_tail` injects it to build repair rows -- corrupted tail as
the "previous attempt", clean tail as the target (see `build_repair_user`).

**Shared-vocabulary invariant: anything the corrupter can inject, the detector
must catch.** `corrupt_tail` enforces it mechanically (see its Returns), so no
repair row carries an "error" the model gets no signal for.

Detection is PARSE-LEVEL only, and deliberately so. This module once carried a
second, name-level rule flagging mathlib3 lemma names the mathlib4 port renamed
(`supr_le` -> `iSup_le`), resolved through a Lean 3 <-> Lean 4
declaration-name map loaded from a gzipped JSON asset, plus a matching corrupter
transform that rewrote a Lean 4 name back into its Lean 3 spelling. That asset
was never built anywhere in this tree -- it lived only inside an S3 archive
nothing here produces -- so the rule was inert on every machine and `l3` was
silently parse-level everywhere. Rule and transform are removed rather than left
permanently disabled, so `l3` now means the same thing wherever it is computed.

Stdlib only. `corrupt_tail` is deterministic: its `random.Random` argument is
the only randomness source, so a build is byte-reproducible from its seed.
Bracket depth (``⟨⟩ () [] {}``) accumulates across lines, never reset per line,
so an unclosed ``⟨`` suppresses a trailing-comma flag several lines later;
string-literal contents are deliberately not skipped.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Relic:
    """One Lean 3 relic found by `find_relics`, or claimed by `corrupt_tail`.

    Attributes
    ----------
    kind : str
        One of ``refl``, ``existsi``, ``binder-comma``, ``trailing-comma``,
        ``begin-end``.
    text : str
        The offending token, or the stripped line (``begin-end``,
        ``trailing-comma``) or binder-through-comma snippet.
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


#: `refl`/`existsi` are plain-word Lean tactics, matched with `\b` boundaries so
#: `le_refl` (no boundary before "refl", since `_` is a `\w` char) and
#: `existsi_something` are not mistaken for the bare tactic.
_REFL_RE = re.compile(r"\brefl\b")
_EXISTSI_RE = re.compile(r"\bexistsi\b")

#: The Lean4 `rfl` token, distinct from `_REFL_RE` above (which detects the Lean3
#: tactic `refl`). Used only by the `rfl->refl` transform, to corrupt it INTO
#: `refl`.
_RFL_RE = re.compile(r"\brfl\b")

#: `fun`/`λ` binder keyword. `λ` is a Unicode letter, so a plain `\b` already
#: requires a non-word char on either side; no special-casing needed.
_BINDER_RE = re.compile(r"\b(?:fun|λ)\b")

#: Prefixes that put `refl` in "tactic-head position", after stripping trailing
#: whitespace from the text preceding a `refl` match: line start (checked
#: separately as an empty prefix), or one of these combinator markers.
_REFL_HEAD_MARKERS = (";", "<;>", "·", "{")


def _is_head_position(line_prefix: str) -> bool:
    """True if text following `line_prefix` sits in tactic-head position.

    Head position = everything before the token on its line is empty, or ends
    with a `_REFL_HEAD_MARKERS` combinator. Single source of the predicate for
    both `find_relics`' rule 2 and the `rfl->refl` transform
    (`_head_rfl_matches`), which makes an injected `refl` re-detectable by
    construction: a term-position `rfl` (`exact rfl`) must not be targeted, since
    rule 2 deliberately does not flag `exact refl`.
    """
    p = line_prefix.rstrip()
    return p == "" or p.endswith(_REFL_HEAD_MARKERS)


def _binder_forward_scan(text: str, start: int) -> tuple[str, int, int] | None:
    """Scan `text[start:]` for the binder's own comma or arrow.

    Shared by `find_relics`' ``binder-comma`` rule and the `binder` transform.
    Depth is tracked *relative* to `start` (just past the `fun`/`λ` keyword), so
    a comma nested one level deeper does not count -- in `fun ⟨a, b⟩ ↦ e` the
    comma is inside the just-opened `⟨`. `text` is the whole text, not one line,
    since a binder's arrow or comma may fall on the next line.

    Returns
    -------
    (str, int, int) or None
        ``("comma", i, i + 1)`` for the first depth-0 ``,``, or ``("arrow", i,
        j)`` for the first ``↦`` (``j = i + 1``) or ``=>`` (``j = i + 2``),
        whichever comes first; ``None`` if neither appears.
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


def find_relics(text: str) -> list[Relic]:
    """Scan `text` for Lean 3 syntax relics.

    Applies five rules (see the inline comments), each precision-guarded against
    Lean 4 constructs that merely resemble a relic, and pinned by
    ``tests/deduction/test_lean_lean3.py``. Pure and O(n). `text` may be
    multi-line; bracket depth accumulates across the whole text, never reset per
    line. Detection is parse-level only -- see the module docstring for the
    name-level rule this once also had and why it is gone.

    Returns
    -------
    list of Relic
        One per distinct ``(kind, text, line)`` triple, in scan order -- so two
        `refl` tactics on one line report as one relic. Four of the five rules
        run line by line, top to bottom, in rule order; ``binder-comma`` (rule
        4) is a separate whole-text pass, since a binder's arrow or comma can
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

    # Cumulative bracket depth AFTER each line's own characters, accumulated from
    # the START of the whole text -- what rule 5 needs (see the module docstring).
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

        # Rule 2: flag `refl` only in tactic-head position, which excludes
        # `le_refl x` and `Equiv.refl` (lemma names, not the bare tactic).
        # `\brefl\b` alone would not: the `.` in `Equiv.refl` is a word boundary.
        for m in _REFL_RE.finditer(line):
            if _is_head_position(line[: m.start()]):
                emit("refl", "refl", "rfl", lineno)

        # Rule 3: `existsi`. Lean 4 removed it outright, so unlike `refl` any
        # occurrence, not just tactic-head, is a relic.
        if _EXISTSI_RE.search(line):
            emit("existsi", "existsi", "use", lineno)

        # Rule 5: flag a trailing comma only at cumulative depth 0. Inside a
        # still-open `⟨`/`(`/`[`/`{` (e.g. multi-line `refine ⟨foo,`) it is
        # legitimate Lean 4 term syntax.
        if stripped.endswith(",") and depth_after_line[lineno] == 0:
            emit("trailing-comma", stripped, stripped[:-1].rstrip(), lineno)

    # Rule 4: binder-comma. This runs as a separate whole-text pass; see
    # `_binder_forward_scan`'s docstring for why it isn't line-bounded.
    for m in _BINDER_RE.finditer(text):
        found = _binder_forward_scan(text, m.end())
        if found is not None and found[0] == "comma":
            _, comma_start, comma_end = found
            lineno = text.count("\n", 0, m.start())
            emit("binder-comma", text[m.start() : comma_end], None, lineno)

    return relics


def has_relics(text: str) -> bool:
    """``bool(find_relics(text))`` -- a full scan, not short-circuited."""
    return bool(find_relics(text))


# ---------------------------------------------------------------------------
# Corruption
# ---------------------------------------------------------------------------


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


def _rfl_applicable(text: str) -> bool:
    return bool(_head_rfl_matches(text))


def _apply_rfl(text: str, rng: random.Random) -> tuple[str, list[Relic]] | None:
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
    `_binder_forward_scan`'s relative depth: the `binder` transform corrupts only
    a top-level binder. A binder already followed by a comma before any arrow is
    already a `binder-comma` relic with nothing left to corrupt, so a ``"comma"``
    scan result counts as no match.

    Returns
    -------
    (re.Match, int, int) or None
        ``(binder_match, arrow_start, arrow_end)``, or ``None`` if no binder
        qualifies.
    """
    for m in _BINDER_RE.finditer(text):
        # Proof-tail-sized text, so re-walking the prefix per candidate binder is
        # cheap and avoids threading a running-depth accumulator through here.
        binder_depth = sum(_bracket_delta(ch) for ch in text[: m.start()])
        if binder_depth != 0:
            continue
        found = _binder_forward_scan(text, m.end())
        if found is not None and found[0] == "arrow":
            return m, found[1], found[2]
    return None


def _binder_applicable(text: str) -> bool:
    return _first_binder_arrow(text) is not None


def _apply_binder(text: str, rng: random.Random) -> tuple[str, list[Relic]] | None:
    """`binder`: rewrite `fun`->`λ` and the binder's own arrow -> `,`.

    Removing the arrow is what makes it a `binder-comma` relic. `fun` also
    becomes `λ` because Lean 3 has no `fun` keyword, so `fun x, e` would be a
    syntax the detector flags but Lean 3 never produced.
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


def _trailing_applicable(text: str) -> bool:
    return bool(_trailing_eligible_lines(text))


def _apply_trailing(text: str, rng: random.Random) -> tuple[str, list[Relic]] | None:
    """`trailing`: append `,` to a seeded non-empty subset of eligible lines.

    The only transform that can inject several relics at once. A random subset,
    rather than every eligible line, mimics a model dropping commas
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


def _use_applicable(text: str) -> bool:
    return any(line.lstrip().startswith("use ") for line in text.split("\n"))


def _apply_use(text: str, rng: random.Random) -> tuple[str, list[Relic]] | None:
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


#: Every transform's applicability check: can it do anything to `text`?
_IsApplicable = Callable[[str], bool]
#: Every transform's apply step, returning `(new_text, [Relic injected, ...])`, or
#: `None` when it turns out to be a no-op despite `_IsApplicable` returning True.
#: That should not normally happen; `corrupt_tail` treats it as "contributed
#: nothing" rather than asserting.
_Apply = Callable[[str, random.Random], tuple[str, list[Relic]] | None]

#: `(is_applicable, apply)` pairs, keyed by transform name, in the fixed
#: order `corrupt_tail` checks them for its "which are applicable" scan.
_TRANSFORMS: dict[str, tuple[_IsApplicable, _Apply]] = {
    "rfl_to_refl": (_rfl_applicable, _apply_rfl),
    "binder": (_binder_applicable, _apply_binder),
    "trailing": (_trailing_applicable, _apply_trailing),
    "use_to_existsi": (_use_applicable, _apply_use),
}


def corrupt_tail(tail: str, rng: random.Random) -> tuple[str, list[Relic]] | None:
    """Inject a seeded mix of Lean 3 relics into a clean Lean 4 tactic tail.

    Draws ``n = rng.randint(1, min(3, len(applicable)))`` of the `_TRANSFORMS`
    applicable to `tail`, shuffles them (seeded), and applies them against the
    *evolving* text, re-checking applicability immediately before each and
    skipping no-ops -- an earlier transform can consume what a later one needed.

    Deterministic given ``(tail, rng-state)``: `rng` is the only randomness
    source, so a build is byte-reproducible from its seed. `tail` is assumed
    Lean-3-relic-free.

    Returns
    -------
    (str, list of Relic) or None
        ``(corrupted, injected)``. The post-condition re-runs
        `find_relics(corrupted)` and keeps only injected relics whose kind the
        detector re-reports, so ``{r.kind for r in injected}`` is a subset of
        the detected kinds BY CONSTRUCTION (the shared-vocabulary invariant), and
        no phantom claim leaks into `synth_error` / repair-row metadata. ``None``
        when no transform is applicable, when every attempt is a no-op, when
        ``corrupted == tail``, or when the post-condition empties `injected`.
    """
    applicable_names = [
        name for name, (is_applicable, _apply) in _TRANSFORMS.items() if is_applicable(tail)
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
        if not is_applicable(text):
            # An earlier transform in this pass consumed the only occurrence this
            # one needed -- e.g. `trailing` claimed the line `binder` would target.
            continue
        result = apply(text, rng)
        if result is None:
            continue
        text, relics = result
        injected.extend(relics)
        applied += 1

    if not injected or text == tail:
        return None
    detected_kinds = {r.kind for r in find_relics(text)}
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

    Only the FIRST relic decides the message: a real compiler stops at its first
    error, so a multi-relic tail would only ever surface one message to a repair
    loop. The message shapes below mimic the cases pinned in
    ``tests/deduction/test_lean_lean3.py``, not Lean's real diagnostics.

    Raises
    ------
    ValueError
        If `relics` is empty, or its first element's `kind` is not one of the
        five kinds `find_relics` produces.
    """
    if not relics:
        raise ValueError("synth_error requires at least one relic")
    first = relics[0]
    if first.kind in ("refl", "existsi", "begin-end"):
        return "<stdin>:1:1: unknown tactic"
    if first.kind in ("binder-comma", "trailing-comma"):
        return "<stdin>:1:1: unexpected token ','; expected command"
    raise ValueError(f"unknown relic kind {first.kind!r}")


#: Fixed instruction suffix `build_repair_user` appends last. A named constant
#: rather than inline text because it is a coordination contract: any
#: repair-dataset builder and any repair-loop runner format their prompts against
#: it byte-for-byte, so it must stay greppable and un-reworded. The wording names
#: lemma names as well as syntax even though the parse-level corrupter can no
#: longer inject a lemma-name error; the bytes are frozen because rewording them
#: would fork the contract, and nothing in this tree records which consumers were
#: written against them.
_REPAIR_INSTRUCTIONS = (
    "The attempt above may use Lean 3 syntax or lemma names that Lean 4 / Mathlib 4\n"
    "rejects. If it is already valid Lean 4, output it unchanged; otherwise output the\n"
    "corrected Lean 4 tactics. Output only the tactic lines, nothing else."
)


def build_repair_user(user: str, attempt: str, error: str | None = None) -> str:
    """Append a previous-attempt repair block to a user turn.

    `error` is typically `synth_error`'s output or a real replay error; its block
    is omitted entirely when ``None``. The exact bytes of the layout below are a
    coordination contract, so this exposes no parameters to vary them.
    """
    error_block = f"Lean reported:\n```\n{error}\n```\n\n" if error is not None else ""
    return (
        f"{user}\n\n"
        "## Previous attempt\n"
        f"```lean\n{attempt}\n```\n"
        f"{error_block}"
        f"{_REPAIR_INSTRUCTIONS}"
    )
