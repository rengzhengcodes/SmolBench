"""Detect parse-level Lean 3 syntax relics in generated Lean 4 proofs.

Bracket depth spans lines so nested-term commas are not flagged; strings are scanned too.
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
# Word boundaries avoid mistaking names such as ``le_refl`` or
# ``existsi_something`` for bare tactics.
_REFL_RE = re.compile(r"\brefl\b")
_EXISTSI_RE = re.compile(r"\bexistsi\b")
# ``λ`` is a Unicode word character, so the same boundary rule works for it.
_BINDER_RE = re.compile(r"\b(?:fun|λ)\b")
# Markers after which ``refl`` occupies tactic-head position; line start is
# checked separately as an empty prefix.
_REFL_HEAD_MARKERS = (";", "<;>", "·", "{")


def _bracket_delta(ch: str) -> int:
    """Classify a bracket character for shared line and binder depth.

    Parameters
    ----------
    ch : str
        Character.

    Returns
    -------
    int
        `1` for opener, `-1` for closer, else `0`.
    """
    if ch in _OPEN_BRACKETS:
        return 1
    if ch in _CLOSE_BRACKETS:
        return -1
    return 0


def _is_head_position(line_prefix: str) -> bool:
    """Return whether a following token can be a tactic head.

    Parameters
    ----------
    line_prefix : str
        Preceding text.

    Returns
    -------
    bool
        Whether a tactic may start there.
    """
    prefix = line_prefix.rstrip()
    return prefix == "" or prefix.endswith(_REFL_HEAD_MARKERS)


def _binder_forward_scan(text: str, start: int) -> tuple[str, int, int] | None:
    """Find a binder separator after `start`, ignoring nested-pattern commas.

    Parameters
    ----------
    text : str
        Text.
    start : int
        Position after ``fun`` or ``λ``.

    Returns
    -------
    tuple[str, int, int] | None
        Separator kind and bounds, if present.
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
    """Find parse-level Lean 3 relics, deduplicated by kind, text, and line.

    Parameters
    ----------
    text : str
        Lean text.

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
