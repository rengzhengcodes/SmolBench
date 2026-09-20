"""Filename markers for retired row artifacts, shared by writers and readers.

Stdlib-only on purpose: ``notebooks/deduction/analysis/rows_source.py`` runs under
``uv run --no-project`` and must be able to import this without the rest of the package.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

#: ``run_study.py --force-rerun`` renames a superseded ``all_rows.jsonl`` to
#: ``all_rows_SUPERSEDED-<stamp>.jsonl`` instead of deleting it (audit trail).
SUPERSEDED_MARKER = "SUPERSEDED"
#: STALE and BROKEN are anchored ``_MARKER-`` so ordinary words in basenames cannot match.
RETIRED_MARKERS = (SUPERSEDED_MARKER, "_STALE-", "_BROKEN-")


def is_retired(path: str | Path) -> bool:
    """True if the BASENAME carries a retirement marker (directories named after an audit are not targets)."""
    name = Path(path).name
    return any(m in name for m in RETIRED_MARKERS)


def retired_paths(paths: Iterable[str | Path]) -> list[str]:
    """Stringified `paths` whose basenames carry a retirement marker."""
    return [str(p) for p in paths if is_retired(p)]
