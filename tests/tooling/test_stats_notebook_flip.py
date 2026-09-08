"""Section 8's measurability rule, pinned to the live grader."""

from __future__ import annotations

from types import ModuleType
from typing import Any

import pytest

from tests.tooling._notebook_cells import (
    STATS_NB,
    _load,
    cell_source,
    load_notebook,
)

from notebooks.deduction.analysis import notebook_stats


@pytest.fixture(scope="module")
def nb() -> dict:
    return load_notebook()


@pytest.fixture(scope="module")
def ded_pa() -> ModuleType:
    """The live deduction grader, loaded once for the module."""
    return _load("nbt_ded_power_analysis_only", "deduction/analysis/power_analysis.py")


def _rows(
    *verdicts: str, theorem: str = "t1", file_path: str = "Mathlib/Data/Nat/Defs.lean"
) -> list[dict[str, Any]]:
    """Build one cell's rows, in file order (== chronological), from its verdicts."""
    return [{"kind": "cell", "model": "m1", "theorem_id": theorem, "k": 1,
             "rung": "stepk:1", "replicate_idx": 0, "verdict": v,
             "file_path": file_path} for v in verdicts]


#: ``(verdicts, measurable)``, derived from ``grade_verdicts``' contract
#: (earliest surviving attempt wins; unmeasurable verdicts are skipped), not
#: from whatever the notebook currently does.
MEASURABILITY_CASES = [
    pytest.param(("success",), True, id="success"),
    # The rule must be the COMPLEMENT of the unmeasurable set, not an
    # enumeration, so a verdict added to the taxonomy tomorrow is measured by
    # default. `"failure"` stands in for such a verdict here.
    pytest.param(("failure",), True, id="unknown-graded-verdict"),
    pytest.param(("lean_error",), True, id="lean_error"),
    pytest.param(("incomplete",), True, id="incomplete"),
    pytest.param(("given_up",), True, id="given_up"),
    # Regression: dedupe-then-whitelist kept the exception row and dropped the
    # cell; grade_verdicts skips the exception and scores the retry.
    pytest.param(("exception", "success"), True, id="exception-then-success"),
    pytest.param(("replay_failed", "failure"), True, id="replay_failed-then-failure"),
    pytest.param(("exception", "replay_failed"), False, id="no-surviving-attempt"),
    pytest.param(("exception",), False, id="exception-only"),
    pytest.param((), False, id="no-rows"),
    # The generation-time sentinel is deliberately not in UNMEASURABLE_VERDICTS
    # (power_analysis treats it as a loud error, not a silent drop); `is_pass`
    # raises on it, so it must not be selected into a sample.
    pytest.param(("unverified",), False, id="ungraded-sentinel"),
    pytest.param(("exception", "unverified"), False, id="ungraded-after-exception"),
]


@pytest.mark.parametrize("verdicts, measurable", MEASURABILITY_CASES)
def test_measurability_follows_the_live_grader(
    ded_pa: ModuleType, verdicts: tuple[str, ...], measurable: bool
) -> None:
    """The cell's answer must equal the table, checked apart from the derivation below so cell drift and table drift report separately."""
    keys = notebook_stats.measurable_cell_keys(
        _rows(*verdicts), ded_pa.UNMEASURABLE_VERDICTS)
    assert bool(keys) is measurable, (verdicts, keys)


@pytest.mark.parametrize("verdicts, measurable", MEASURABILITY_CASES)
def test_measurability_agrees_with_grade_verdicts(
    ded_pa: ModuleType, verdicts: tuple[str, ...], measurable: bool
) -> None:
    """The table must be derived from the live grader rather than restated, so the two cannot drift apart."""
    graded = ded_pa.grade_verdicts(list(verdicts))
    survivor = next((v for v in verdicts if v not in ded_pa.UNMEASURABLE_VERDICTS), None)
    assert measurable is (graded is not None and survivor != "unverified")


def test_no_positive_whitelist_survives(
    nb: dict[str, Any]
) -> None:
    """The complement of ``UNMEASURABLE_VERDICTS`` must not be re-declared literally."""
    import re

    src = cell_source(nb, "ported estimators:")
    # Anchored: a bare ``"MEASURABLE_VERDICTS" in src`` also matches every
    # mention of ``UNMEASURABLE_VERDICTS``, i.e. the correct code.
    assert not re.search(r"(?<![A-Z_])MEASURABLE_VERDICTS", src), src
    assert "UNMEASURABLE_VERDICTS" in src, "measurability is no longer derived from the live set"
    assert "ded_pa.UNMEASURABLE_VERDICTS" in src, "the live set must be read, not copied"


def test_every_selected_cell_is_safe_for_is_pass(ded_pa: ModuleType) -> None:
    """`is_pass` raises on `unverified`, so this filter must be the thing that removes it before callers reach is_pass."""
    with pytest.raises(ValueError, match="unverified"):
        notebook_stats.is_pass("unverified")

    rows = (_rows("exception", "success", theorem="a")
            + _rows("unverified", theorem="b")
            + _rows("failure", theorem="c"))
    selected = notebook_stats.measurable_cell_keys(rows, ded_pa.UNMEASURABLE_VERDICTS)
    assert len(selected) == 2, selected
    assert not any("b" in str(key) for key in selected), selected
    # Every selected cell's surviving verdict must go through is_pass unraised.
    surviving = {"a": "success", "c": "failure"}
    for theorem, verdict in surviving.items():
        assert any(theorem in str(key) for key in selected), theorem
        notebook_stats.is_pass(verdict)


def test_dependency_cells_are_still_excluded(ded_pa: ModuleType) -> None:
    """The Mathlib-only restriction is unchanged by the measurability fix."""
    rows = (_rows("exception", "success", theorem="dep",
                  file_path=".lake/packages/batteries/Batteries/Data/List.lean")
            + _rows("exception", "success", theorem="mathlib"))
    keys = notebook_stats.measurable_cell_keys(rows, ded_pa.UNMEASURABLE_VERDICTS)
    assert len(keys) == 1 and "mathlib" in str(keys[0]), keys


def test_selection_is_sorted_and_order_independent(ded_pa: ModuleType) -> None:
    """`select_sample_keys` is only reproducible over an ALREADY-SORTED population."""
    rows = _rows("success", theorem="t3") + _rows("success", theorem="t1") \
        + _rows("success", theorem="t2")
    keys = notebook_stats.measurable_cell_keys(rows, ded_pa.UNMEASURABLE_VERDICTS)
    assert keys == sorted(keys)
    assert keys == notebook_stats.measurable_cell_keys(
        list(reversed(rows)), ded_pa.UNMEASURABLE_VERDICTS)


def test_ported_estimator_names_all_exist(
    nb: dict[str, Any]
) -> None:
    """Every name the section advertises (markdown "What was ported" sentence and the cell's print) must be defined; none may dangle."""
    import re

    src = cell_source(nb, "ported estimators:")
    advertised = (
        "clopper_pearson_interval", "flip_stats", "verifier_drift_stats", "is_pass",
        "group_rows_by_cell", "surviving_verdict", "measurable_cell_keys",
        "select_sample_keys",
    )
    assert 'print("ported estimators:", ", ".join(sorted(' in src
    for name in advertised:
        assert f'"{name}"' in src
        assert callable(getattr(notebook_stats, name))

    markdown = cell_source(nb, "**What was ported.**")
    sentence = markdown.split("**What was ported.**", 1)[1].split(".\n", 1)[0]
    named = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", sentence))
    missing = sorted(n for n in named if not hasattr(notebook_stats, n))
    assert not missing, f"section-8 markdown names undefined helpers: {missing}"


def test_the_in_cell_grader_pin_is_live_not_a_no_op(
    nb: dict[str, Any], ded_pa: ModuleType
) -> None:
    """The cell's own assertion loop must actually fire (not just be present) when a grader disagreeing with the earliest-surviving rule is bound."""
    class _WrongGrader:
        UNMEASURABLE_VERDICTS = ded_pa.UNMEASURABLE_VERDICTS

        @staticmethod
        def grade_verdicts(verdicts: list[str]) -> int | None:
            # Latest surviving attempt wins: pass@N dressed up as pass@1,
            # exactly what grade_verdicts exists to prevent.
            survivors = [v for v in verdicts if v not in ded_pa.UNMEASURABLE_VERDICTS]
            return None if not survivors else int(survivors[-1] == "success")

    src = cell_source(nb, "ported estimators:")
    with pytest.raises(AssertionError):
        exec(compile(src, str(STATS_NB), "exec"), {"ded_pa": _WrongGrader})


def test_a_row_with_no_verdict_is_not_a_measurement(ded_pa: ModuleType) -> None:
    """A missing verdict must be dropped, not scored 0 like `grade_verdicts` would: this chooses what to SAMPLE, and scoring it would book "never recorded" as "measured and lost"."""
    rows = _rows("success", theorem="ok")
    orphan = _rows("success", theorem="orphan")
    for row in orphan:
        del row["verdict"]
    keys = notebook_stats.measurable_cell_keys(
        rows + orphan, ded_pa.UNMEASURABLE_VERDICTS)
    assert len(keys) == 1 and "ok" in str(keys[0]), keys
