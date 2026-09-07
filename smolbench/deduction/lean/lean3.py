"""Detect and inject Lean 3 syntax relics.

Lean 3 syntax survives SFT/LoRA training as a residue: `refl` for `rfl`,
`existsi` for `use`, `begin...end`, `λ x, e` binders, trailing commas.
`find_relics`/`has_relics` detect it (the analyzer's `l3` leak-rate column);
`corrupt_tail` injects it to build repair rows (see `build_repair_user`).
Detection is parse-level only -- no mathlib3->mathlib4 lemma-rename rule.

Shared-vocabulary invariant: anything `corrupt_tail` injects, `find_relics`
must catch. `corrupt_tail` enforces this mechanically (see its Returns), so no
repair row carries an error the model gets no signal for.

Stdlib only, deterministic via `corrupt_tail`'s `random.Random` argument.
Bracket depth (``⟨⟩ () [] {}``) accumulates across the whole text, never reset
per line, so an unclosed ``⟨`` can suppress a trailing-comma flag several
lines later; string-literal contents are not skipped.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Relic:
    """One Lean 3 relic found by `find_relics`, or claimed by `corrupt_tail`."""

    #: One of "refl", "existsi", "binder-comma", "trailing-comma", "begin-end".
    kind: str
    #: The offending token, the stripped line (begin-end/trailing-comma), or
    #: the binder-through-comma snippet.
    text: str
    #: Lean 4 replacement, or None where no single-token fix applies
    #: (begin-end; binder-comma, whose fix would mean guessing which arrow).
    fix: str | None
    #: 0-indexed line within the scanned text.
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


#: `refl`/`existsi` are plain-word tactics, matched with `\b` so `le_refl`
#: (`_` is a `\w` char, so no boundary before "refl") and `existsi_something`
#: aren't mistaken for the bare tactic.
_REFL_RE = re.compile(r"\brefl\b")
_EXISTSI_RE = re.compile(r"\bexistsi\b")

#: Lean4 `rfl`, distinct from `_REFL_RE` (the Lean3 tactic `refl`); used only
#: to corrupt `rfl` into `refl`.
_RFL_RE = re.compile(r"\brfl\b")

#: `fun`/`λ` binder keyword. `λ` is a Unicode letter, so `\b` already requires
#: a non-word char on either side; no special-casing needed.
_BINDER_RE = re.compile(r"\b(?:fun|λ)\b")

#: Markers after which `refl` counts as tactic-head position (line start is
#: checked separately as an empty prefix).
_REFL_HEAD_MARKERS = (";", "<;>", "·", "{")


def _is_head_position(line_prefix: str) -> bool:
    """True if text following `line_prefix` sits in tactic-head position.

    Shared by `find_relics`' rule 2 and `_head_rfl_matches`, so an injected
    `refl` is re-detectable by construction: a term-position `rfl`
    (`exact rfl`) is never targeted, since rule 2 doesn't flag `exact refl`.

    Parameters
    ----------
    line_prefix : str
        Text preceding the possible tactic.

    Returns
    -------
    bool
        Whether the following text is in tactic-head position.
    """
    p = line_prefix.rstrip()
    return p == "" or p.endswith(_REFL_HEAD_MARKERS)


def _binder_forward_scan(text: str, start: int) -> tuple[str, int, int] | None:
    """Scan `text[start:]` for the binder's own comma or arrow.

    Shared by the `binder-comma` rule and the `binder` transform. Depth is
    relative to `start` (just past `fun`/`λ`), so a nested comma doesn't count
    -- in `fun ⟨a, b⟩ ↦ e` the comma is inside the just-opened `⟨`.

    Parameters
    ----------
    text : str
        The whole text, since a binder's arrow or comma may fall on the next line.
    start : int
        Position just past `fun` or `λ`.

    Returns
    -------
    tuple[str, int, int] | None
        ``("comma"|"arrow", start, end)`` for whichever comes first, or `None`.
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

    Applies five rules (see inline comments), each guarded against Lean 4
    constructs that merely resemble a relic; pinned by `test_lean_lean3.py`.
    Bracket depth accumulates across the whole text, not per line.

    Rules 1/2/3/5 run line by line; `binder-comma` (rule 4) is a separate
    whole-text pass since its arrow or comma can follow a line break.

    Parameters
    ----------
    text : str
        Lean text to scan.

    Returns
    -------
    list[Relic]
        One `Relic` per distinct (kind, text, line) triple, in scan order -- two
        `refl` tactics on one line report as one relic.
    """
    relics: list[Relic] = []
    seen: set[tuple[str, str, int]] = set()

    def emit(kind: str, rtext: str, fix: str | None, line: int) -> None:
        key = (kind, rtext, line)
        if key not in seen:
            seen.add(key)
            relics.append(Relic(kind=kind, text=rtext, fix=fix, line=line))

    lines = text.split("\n")

    # Cumulative bracket depth after each line, accumulated from the start of
    # the whole text; rule 5 needs this to check depth at line end.
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

        # Rule 2: flag `refl` only in tactic-head position, excluding `le_refl x`
        # and `Equiv.refl` (`.` is a word boundary, so `\brefl\b` alone would not).
        for m in _REFL_RE.finditer(line):
            if _is_head_position(line[: m.start()]):
                emit("refl", "refl", "rfl", lineno)

        # Rule 3: `existsi`. Lean 4 removed it outright, so unlike `refl` any
        # occurrence, not just tactic-head, is a relic.
        if _EXISTSI_RE.search(line):
            emit("existsi", "existsi", "use", lineno)

        # Rule 5: a trailing comma inside a still-open bracket (multi-line
        # `refine ⟨foo,`) is legitimate Lean 4 term syntax, not a relic.
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

    Shares `_is_head_position` with rule 2: a term-position `rfl`
    (`exact rfl`, `⟨rfl, h⟩`) rewritten to `refl` would not be re-detected.

    Parameters
    ----------
    text : str
        Lean text to scan.

    Returns
    -------
    list[re.Match]
        Tactic-head `rfl` token matches.
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
    `_binder_forward_scan`'s relative depth, since `binder` only corrupts a
    top-level binder. A binder already followed by a comma before any arrow is
    already a `binder-comma` relic, so a "comma" scan result doesn't count.

    Parameters
    ----------
    text : str
        Lean text to scan.

    Returns
    -------
    tuple[re.Match, int, int] | None
        ``(binder_match, arrow_start, arrow_end)``, or `None`.
    """
    for m in _BINDER_RE.finditer(text):
        # Proof-tail-sized text, so re-walking the prefix per candidate binder
        # is cheap and avoids threading a running-depth accumulator through here.
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

    Removing the arrow makes it a `binder-comma` relic. `fun` becomes `λ`
    too, since Lean 3 has no `fun` keyword and `fun x, e` is a syntax the
    detector flags but Lean 3 never produced.

    Parameters
    ----------
    text : str
        Lean text to corrupt.
    rng : random.Random
        Seeded random generator.

    Returns
    -------
    tuple[str, list[Relic]] | None
        Corrupted text and its injected relic, or `None` when no binder applies.
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

    Parameters
    ----------
    text : str
        Lean text to inspect.

    Returns
    -------
    list[int]
        0-indexed lines eligible for the `trailing` transform.
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

    The only transform that can inject several relics at once. A random
    subset, not every eligible line, mimics a model dropping commas
    inconsistently.

    Parameters
    ----------
    text : str
        Lean text to corrupt.
    rng : random.Random
        Seeded random generator.

    Returns
    -------
    tuple[str, list[Relic]] | None
        Corrupted text and injected trailing-comma relics, or `None` when no line applies.
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


#: Applicability check for a transform: can it do anything to `text`?
_IsApplicable = Callable[[str], bool]
#: Apply step: returns `(new_text, injected_relics)`, or `None` if it turns
#: out to be a no-op despite `_IsApplicable` returning True -- `corrupt_tail`
#: treats that as "contributed nothing" rather than asserting.
_Apply = Callable[[str, random.Random], tuple[str, list[Relic]] | None]

#: `(is_applicable, apply)` pairs, in the fixed order `corrupt_tail` scans them.
_TRANSFORMS: dict[str, tuple[_IsApplicable, _Apply]] = {
    "rfl_to_refl": (_rfl_applicable, _apply_rfl),
    "binder": (_binder_applicable, _apply_binder),
    "trailing": (_trailing_applicable, _apply_trailing),
    "use_to_existsi": (_use_applicable, _apply_use),
}


def corrupt_tail(tail: str, rng: random.Random) -> tuple[str, list[Relic]] | None:
    """Inject a seeded mix of Lean 3 relics into a clean Lean 4 tactic tail.

    Draws ``n = rng.randint(1, min(3, len(applicable)))`` of `_TRANSFORMS`
    applicable to `tail`, shuffles them (seeded), and applies them against the
    evolving text, re-checking applicability before each -- an earlier
    transform can consume what a later one needed. Deterministic given
    `(tail, rng-state)`.

    The post-condition re-runs `find_relics` and keeps only injected relics
    whose kind is re-detected, enforcing the shared-vocabulary invariant so no
    phantom claim leaks into `synth_error` / repair-row metadata.

    Parameters
    ----------
    tail : str
        Clean Lean 4 tactic tail to corrupt.
    rng : random.Random
        Seeded random generator.

    Returns
    -------
    tuple[str, list[Relic]] | None
        ``(corrupted, injected)``, or `None` if no transform applies, every attempt is a
        no-op, ``corrupted == tail``, or the post-condition above empties `injected`.
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

    Only the first relic decides the message: a real compiler stops at its
    first error. Message shapes mimic cases pinned in `test_lean_lean3.py`,
    not Lean's real diagnostics.

    Parameters
    ----------
    relics : list[Relic]
        Relics whose first item determines the message.

    Returns
    -------
    str
        Lean-compiler-shaped error message.

    Raises
    ------
    ValueError
        If `relics` is empty or its first element's `kind` isn't one of the five
        `find_relics` produces.
    """
    if not relics:
        raise ValueError("synth_error requires at least one relic")
    first = relics[0]
    if first.kind in ("refl", "existsi", "begin-end"):
        return "<stdin>:1:1: unknown tactic"
    if first.kind in ("binder-comma", "trailing-comma"):
        return "<stdin>:1:1: unexpected token ','; expected command"
    raise ValueError(f"unknown relic kind {first.kind!r}")


#: Fixed instruction suffix `build_repair_user` appends last: a coordination
#: contract between repair-dataset builders and repair-loop runners, so the
#: bytes must stay unreworded. Still mentions lemma names even though the
#: parse-level corrupter can no longer inject one -- rewording would fork the
#: contract, and nothing here records every consumer.
_REPAIR_INSTRUCTIONS = (
    "The attempt above may use Lean 3 syntax or lemma names that Lean 4 / Mathlib 4\n"
    "rejects. If it is already valid Lean 4, output it unchanged; otherwise output the\n"
    "corrected Lean 4 tactics. Output only the tactic lines, nothing else."
)


def build_repair_user(user: str, attempt: str, error: str | None = None) -> str:
    """Append a previous-attempt repair block to a user turn.

    The layout's exact bytes are a coordination
    contract, so no parameters vary it.

    Parameters
    ----------
    user : str
        User turn to extend.
    attempt : str
        Previous Lean tactic attempt.
    error : str | None, optional
        `synth_error`'s output or a real replay error; its block is omitted when `None`.

    Returns
    -------
    str
        User turn with the previous-attempt repair block appended.
    """
    error_block = f"Lean reported:\n```\n{error}\n```\n\n" if error is not None else ""
    return (
        f"{user}\n\n"
        "## Previous attempt\n"
        f"```lean\n{attempt}\n```\n"
        f"{error_block}"
        f"{_REPAIR_INSTRUCTIONS}"
    )
