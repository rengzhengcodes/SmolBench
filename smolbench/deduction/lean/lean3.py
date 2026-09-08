"""Detect Lean 3 syntax relics in generated Lean 4 proofs.

Lean 3 syntax survives SFT/LoRA training as a residue: `refl` for `rfl`,
`existsi` for `use`, `begin...end`, `λ x, e` binders, and trailing commas.
Detection is parse-level only; no mathlib3-to-mathlib4 lemma rename rule is
attempted. Bracket depth accumulates across the whole text so commas inside a
multi-line bracketed term are not misclassified.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Relic:
    """One Lean 3 relic found by `find_relics`."""

    kind: str
    text: str
    fix: str | None
    line: int


_OPEN_BRACKETS = "⟨([{"
_CLOSE_BRACKETS = "⟩)]}"
_REFL_RE = re.compile(r"\brefl\b")
_EXISTSI_RE = re.compile(r"\bexistsi\b")
_BINDER_RE = re.compile(r"\b(?:fun|λ)\b")
_REFL_HEAD_MARKERS = (";", "<;>", "·", "{")


def _bracket_delta(ch: str) -> int:
    """Return the nesting delta contributed by one character.

    A shared helper keeps line-depth and binder-depth calculations consistent.

    Parameters
    ----------
    ch : str
        Character to classify.

    Returns
    -------
    int
        ``1`` for an opener, ``-1`` for a closer, otherwise ``0``.
    """
    if ch in _OPEN_BRACKETS:
        return 1
    if ch in _CLOSE_BRACKETS:
        return -1
    return 0


def _is_head_position(line_prefix: str) -> bool:
    """Return whether following text occupies tactic-head position.

    This excludes term-position occurrences such as ``exact refl``.

    Parameters
    ----------
    line_prefix : str
        Text preceding the possible tactic.

    Returns
    -------
    bool
        Whether a tactic may start after the prefix.
    """
    prefix = line_prefix.rstrip()
    return prefix == "" or prefix.endswith(_REFL_HEAD_MARKERS)


def _binder_forward_scan(text: str, start: int) -> tuple[str, int, int] | None:
    """Find the binder's own comma or arrow after `start`.

    Relative depth prevents commas inside destructured binder patterns from
    counting as the binder separator.

    Parameters
    ----------
    text : str
        Whole text being scanned.
    start : int
        Position immediately after ``fun`` or ``λ``.

    Returns
    -------
    tuple[str, int, int] | None
        Kind and bounds of the first separator, or ``None``.
    """
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "," and depth == 0:
            return "comma", i, i + 1
        if ch == "↦":
            return "arrow", i, i + 1
        if text[i:i + 2] == "=>":
            return "arrow", i, i + 2
        depth += _bracket_delta(ch)
        i += 1
    return None


def find_relics(text: str) -> list[Relic]:
    """Scan `text` for parse-level Lean 3 syntax relics.

    Rules run line by line except binder commas, whose separator may occur on
    a later line. Findings are deduplicated by kind, text, and line.

    Parameters
    ----------
    text : str
        Lean text to scan.

    Returns
    -------
    list[Relic]
        Relics in scan order.
    """
    relics: list[Relic] = []
    seen: set[tuple[str, str, int]] = set()

    def emit(kind: str, relic_text: str, fix: str | None, line: int) -> None:
        key = kind, relic_text, line
        if key not in seen:
            seen.add(key)
            relics.append(Relic(kind=kind, text=relic_text, fix=fix, line=line))

    lines = text.split("\n")
    depth_after_line: list[int] = []
    running = 0
    for line in lines:
        running += sum(_bracket_delta(ch) for ch in line)
        depth_after_line.append(running)

    for lineno, line in enumerate(lines):
        stripped = line.strip()
        if stripped in ("begin", "end") or stripped.startswith("begin "):
            emit("begin-end", stripped, None, lineno)
        for match in _REFL_RE.finditer(line):
            if _is_head_position(line[:match.start()]):
                emit("refl", "refl", "rfl", lineno)
        if _EXISTSI_RE.search(line):
            emit("existsi", "existsi", "use", lineno)
        if stripped.endswith(",") and depth_after_line[lineno] == 0:
            emit("trailing-comma", stripped, stripped[:-1].rstrip(), lineno)

    for match in _BINDER_RE.finditer(text):
        found = _binder_forward_scan(text, match.end())
        if found is not None and found[0] == "comma":
            _, _comma_start, comma_end = found
            lineno = text.count("\n", 0, match.start())
            emit("binder-comma", text[match.start():comma_end], None, lineno)

    return relics
