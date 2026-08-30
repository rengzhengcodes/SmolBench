"""Docs and notebooks that state the post-cutoff contract (A5, A7).

Prose goes stale silently, so the load-bearing claims are pinned here: the
Mathlib-vs-dependency filter's actual predicate, the notebooks' JSON shape (an
edit script that stringifies `source` or drops outputs makes every later diff
unreviewable), and the attribution of the OLD study's 300/805/944 counts.
"""

import json
import re

import pytest

from tests._paths import NOTEBOOKS

STATS_NB = NOTEBOOKS / "statistical_analyses.ipynb"
LEAN_NB = NOTEBOOKS / "deduction" / "lean_eval.ipynb"
README = NOTEBOOKS / "deduction" / "README.md"

#: The counts that describe the OLD, pre-cutoff study only.
OLD_STUDY_NUMBERS = re.compile(r"\b(300|805|944)\b")


@pytest.fixture(scope="module")
def stats_nb() -> dict:
    return json.loads(STATS_NB.read_text())


@pytest.fixture(scope="module")
def lean_nb() -> dict:
    return json.loads(LEAN_NB.read_text())


def _cell_source(nb: dict, needle: str) -> str:
    hits = [c for c in nb["cells"] if needle in "".join(c["source"])]
    assert len(hits) == 1, f"expected exactly one cell containing {needle!r}, got {len(hits)}"
    return "".join(hits[0]["source"])


@pytest.mark.parametrize("path", [STATS_NB, LEAN_NB], ids=lambda p: p.name)
def test_notebook_json_shape_survives_editing(path):
    """Round-trips byte-for-byte at indent=1, keeps list-of-lines `source`, no outputs.

    This is the recipe any edit script must use. A whole-file renormalization
    (or a `source` collapsed to one string) would bury the real change in noise.
    """
    raw = path.read_text()
    nb = json.loads(raw)
    assert json.dumps(nb, indent=1, ensure_ascii=False) + "\n" == raw
    for i, cell in enumerate(nb["cells"]):
        assert isinstance(cell["source"], list), f"cell {i} source is not a list of lines"
        assert not cell.get("outputs"), f"cell {i} gained stored outputs"
        assert cell.get("execution_count") is None, f"cell {i} gained an execution_count"


def test_dependency_filter_covers_every_lake_package(stats_nb):
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


def test_lean_eval_attributes_the_old_counts(lean_nb):
    """300 / 805 / 944 are the pre-cutoff study's numbers, not standing facts."""
    offenders = [
        i for i, c in enumerate(lean_nb["cells"])
        if c["cell_type"] == "markdown"
        and OLD_STUDY_NUMBERS.search("".join(c["source"]))
        and "pre-cutoff" not in "".join(c["source"])
    ]
    assert not offenders, (
        f"markdown cells {offenders} state 300/805/944 without marking them as the "
        "pre-cutoff study's numbers")


def test_readme_states_what_the_code_now_enforces():
    """The cutoff section must describe the enforced contract and point at Package B."""
    text = README.read_text()
    start = text.index("### Corpus date vs. model cutoffs")
    section = text[start:text.index("\n## ", start)]
    for token in ("require_postcutoff", "is_postcutoff_corpus", "ROSTER_LATEST_RELEASE",
                  "build_postcutoff_corpus.py"):
        assert token in section, f"{token!r} missing from the cutoff section"
    # The S3 layout section must not still promise the published study's prefix
    # for NEW runs.
    assert "deduction_postcutoff/runs" in text
