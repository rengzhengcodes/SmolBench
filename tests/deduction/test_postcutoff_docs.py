"""Notebook serialization and executable-cell contracts."""

import json
from pathlib import Path
from typing import Any

import pytest

from tests._paths import NOTEBOOKS

STATS_NB = NOTEBOOKS / "statistical_analyses.ipynb"
LEAN_NB = NOTEBOOKS / "deduction" / "lean_eval.ipynb"


@pytest.fixture(scope="module")
def stats_nb() -> dict[str, Any]:
    if not STATS_NB.exists():
        pytest.skip("statistical_analyses.ipynb lives in the top stack slice")
    return json.loads(STATS_NB.read_text())


def _cell_source(nb: dict[str, Any], needle: str) -> str:
    hits = [c for c in nb["cells"] if needle in "".join(c["source"])]
    assert len(hits) == 1, f"expected exactly one cell containing {needle!r}, got {len(hits)}"
    return "".join(hits[0]["source"])


@pytest.mark.parametrize("path", [STATS_NB, LEAN_NB], ids=lambda p: p.name)
def test_notebook_json_shape_survives_editing(path: Path) -> None:
    """Round-trip notebooks byte-for-byte at indent=1 with line-list sources."""
    if not path.exists():
        pytest.skip(f"{path.name} lives in a later stack slice")
    raw = path.read_text()
    nb = json.loads(raw)
    assert json.dumps(nb, indent=1, ensure_ascii=False) + "\n" == raw
    for i, cell in enumerate(nb["cells"]):
        assert isinstance(cell["source"], list), f"cell {i} source is not a list of lines"
        assert not cell.get("outputs"), f"cell {i} gained stored outputs"
        assert cell.get("execution_count") is None, f"cell {i} gained an execution_count"


def test_dependency_filter_covers_every_lake_package() -> None:
    """Filter `.lake/packages/`, not one dependency name, to avoid misclassification.

    Std was renamed Batteries; an ``std``-only marker silently made every Batteries theorem Mathlib and inflated the "Mathlib-only" population.
    """
    from notebooks.deduction.analysis.notebook_stats import is_mathlib_cell

    for dep in (".lake/packages/std/Std/Data/List.lean",
                ".lake/packages/batteries/Batteries/Data/List.lean",
                ".lake/packages/aesop/Aesop/Frontend.lean",
                ".lake/packages/plausible/Plausible.lean"):
        assert is_mathlib_cell({"file_path": dep}) is False, dep
    for mathlib in ("Mathlib/Algebra/Group/Basic.lean", "Mathlib/Data/Nat/Defs.lean"):
        assert is_mathlib_cell({"file_path": mathlib}) is True, mathlib
    # Missing paths are not dependency evidence, so treat them as Mathlib.
    assert is_mathlib_cell({}) is True
    assert is_mathlib_cell({"file_path": None}) is True
