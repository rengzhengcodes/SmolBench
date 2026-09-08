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
    """Round-trips byte-for-byte at indent=1, keeps list-of-lines `source`, no outputs.

    This is the recipe any edit script must use. A whole-file renormalization
    (or a `source` collapsed to one string) would bury the real change in noise.
    """
    if not path.exists():
        pytest.skip(f"{path.name} lives in a later stack slice")
    raw = path.read_text()
    nb = json.loads(raw)
    assert json.dumps(nb, indent=1, ensure_ascii=False) + "\n" == raw
    for i, cell in enumerate(nb["cells"]):
        assert isinstance(cell["source"], list), f"cell {i} source is not a list of lines"
        assert not cell.get("outputs"), f"cell {i} gained stored outputs"
        assert cell.get("execution_count") is None, f"cell {i} gained an execution_count"


def test_dependency_filter_covers_every_lake_package(stats_nb: dict[str, Any]) -> None:
    """Std was renamed Batteries; the filter must key on `.lake/packages/`, not one name.

    A marker naming only `std` silently reclassified every Batteries theorem as
    Mathlib once mathlib4 switched, inflating the "Mathlib-only" population.
    """
    src = _cell_source(stats_nb, "def is_mathlib_cell")
    ns: dict = {}
    exec(compile(src, str(STATS_NB), "exec"), ns)
    is_mathlib_cell = ns["is_mathlib_cell"]

    for dep in (".lake/packages/std/Std/Data/List.lean",
                ".lake/packages/batteries/Batteries/Data/List.lean",
                ".lake/packages/aesop/Aesop/Frontend.lean",
                ".lake/packages/plausible/Plausible.lean"):
        assert is_mathlib_cell({"file_path": dep}) is False, dep
    for mathlib in ("Mathlib/Algebra/Group/Basic.lean", "Mathlib/Data/Nat/Defs.lean"):
        assert is_mathlib_cell({"file_path": mathlib}) is True, mathlib
    # A missing path is not evidence of a dependency; keep treating it as Mathlib.
    assert is_mathlib_cell({}) is True
    assert is_mathlib_cell({"file_path": None}) is True
