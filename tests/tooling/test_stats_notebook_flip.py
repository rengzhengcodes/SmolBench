"""Section 8's measurability rule, pinned to the live grader.

``measurable_cell_keys`` selects the population section 8 samples from; these
tests derive every expectation from ``grade_verdicts``' documented rule so it
cannot silently drift from ``power_analysis``'s ``UNMEASURABLE_VERDICTS``.
"""

from __future__ import annotations

import pytest

from tests.tooling._notebook_cells import (
    STATS_NB,
    cell_source,
    load_deduction_power_analysis,
    load_notebook,
)


@pytest.fixture(scope="module")
def nb() -> dict:
    return load_notebook()


@pytest.fixture(scope="module")
def ded_pa():
    """The live deduction grader, loaded once for the module."""
    return load_deduction_power_analysis()


@pytest.fixture(scope="module")
def flip_ns(nb, ded_pa) -> dict:
    """The executed namespace of section 8's estimator cell."""
    src = cell_source(nb, "def measurable_cell_keys")
    namespace = {"ded_pa": ded_pa}
    exec(compile(src, str(STATS_NB), "exec"), namespace)
    return namespace


def _rows(*verdicts, theorem="t1", file_path="Mathlib/Data/Nat/Defs.lean"):
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
def test_measurability_follows_the_live_grader(flip_ns, ded_pa, verdicts, measurable):
    """The cell's answer must equal the grader's rule, derived here rather than restated so the two cannot drift apart."""
    keys = flip_ns["measurable_cell_keys"](_rows(*verdicts))
    assert bool(keys) is measurable, (verdicts, keys)

    graded = ded_pa.grade_verdicts(list(verdicts))
    survivor = next((v for v in verdicts if v not in ded_pa.UNMEASURABLE_VERDICTS), None)
    assert measurable is (graded is not None and survivor != "unverified")


def test_no_positive_whitelist_survives(nb, flip_ns):
    """The complement of ``UNMEASURABLE_VERDICTS`` must not be re-declared literally."""
    import re

    src = cell_source(nb, "def measurable_cell_keys")
    # Anchored: a bare ``"MEASURABLE_VERDICTS" in src`` also matches every
    # mention of ``UNMEASURABLE_VERDICTS``, i.e. the correct code.
    assert not re.search(r"(?<![A-Z_])MEASURABLE_VERDICTS", src), src
    assert "UNMEASURABLE_VERDICTS" in src, "measurability is no longer derived from the live set"
    assert "ded_pa.UNMEASURABLE_VERDICTS" in src, "the live set must be read, not copied"


def test_every_selected_cell_is_safe_for_is_pass(flip_ns):
    """`is_pass` raises on `unverified`, so this filter must be the thing that removes it before callers reach is_pass."""
    is_pass, measurable_cell_keys = flip_ns["is_pass"], flip_ns["measurable_cell_keys"]
    with pytest.raises(ValueError, match="unverified"):
        is_pass("unverified")

    rows = (_rows("exception", "success", theorem="a")
            + _rows("unverified", theorem="b")
            + _rows("failure", theorem="c"))
    selected = measurable_cell_keys(rows)
    assert len(selected) == 2, selected
    assert not any("b" in str(key) for key in selected), selected
    # Every selected cell's surviving verdict must go through is_pass unraised.
    surviving = {"a": "success", "c": "failure"}
    for theorem, verdict in surviving.items():
        assert any(theorem in str(key) for key in selected), theorem
        is_pass(verdict)


def test_dependency_cells_are_still_excluded(flip_ns):
    """The Mathlib-only restriction is unchanged by the measurability fix."""
    rows = (_rows("exception", "success", theorem="dep",
                  file_path=".lake/packages/batteries/Batteries/Data/List.lean")
            + _rows("exception", "success", theorem="mathlib"))
    keys = flip_ns["measurable_cell_keys"](rows)
    assert len(keys) == 1 and "mathlib" in str(keys[0]), keys


def test_selection_is_sorted_and_order_independent(flip_ns):
    """`select_sample_keys` is only reproducible over an ALREADY-SORTED population."""
    rows = _rows("success", theorem="t3") + _rows("success", theorem="t1") \
        + _rows("success", theorem="t2")
    keys = flip_ns["measurable_cell_keys"](rows)
    assert keys == sorted(keys)
    assert keys == flip_ns["measurable_cell_keys"](list(reversed(rows)))


def test_ported_estimator_names_all_exist(nb, flip_ns, capsys):
    """Every name the section advertises (markdown "What was ported" sentence and the cell's print) must be defined; none may dangle."""
    import re

    src = cell_source(nb, "def measurable_cell_keys")
    exec(compile(src, str(STATS_NB), "exec"), dict(flip_ns))
    printed = capsys.readouterr().out
    advertised = printed.split("ported estimators:", 1)[1].strip().split(", ")
    assert advertised, printed
    for name in advertised:
        assert callable(flip_ns.get(name)), f"cell advertises {name!r}, which is not defined"

    markdown = cell_source(nb, "**What was ported.**")
    sentence = markdown.split("**What was ported.**", 1)[1].split(".\n", 1)[0]
    named = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", sentence))
    missing = sorted(n for n in named if n not in flip_ns)
    assert not missing, f"section-8 markdown names undefined helpers: {missing}"


def test_the_in_cell_grader_pin_is_live_not_a_no_op(nb, ded_pa):
    """The cell's own assertion loop must actually fire (not just be present) when a grader disagreeing with the earliest-surviving rule is bound."""
    class _WrongGrader:
        UNMEASURABLE_VERDICTS = ded_pa.UNMEASURABLE_VERDICTS

        @staticmethod
        def grade_verdicts(verdicts):
            # Latest surviving attempt wins: pass@N dressed up as pass@1,
            # exactly what grade_verdicts exists to prevent.
            survivors = [v for v in verdicts if v not in ded_pa.UNMEASURABLE_VERDICTS]
            return None if not survivors else int(survivors[-1] == "success")

    src = cell_source(nb, "def measurable_cell_keys")
    with pytest.raises(AssertionError):
        exec(compile(src, str(STATS_NB), "exec"), {"ded_pa": _WrongGrader})


def test_a_row_with_no_verdict_is_not_a_measurement(flip_ns):
    """A missing verdict must be dropped, not scored 0 like `grade_verdicts` would: this chooses what to SAMPLE, and scoring it would book "never recorded" as "measured and lost"."""
    rows = _rows("success", theorem="ok")
    orphan = _rows("success", theorem="orphan")
    for row in orphan:
        del row["verdict"]
    keys = flip_ns["measurable_cell_keys"](rows + orphan)
    assert len(keys) == 1 and "ok" in str(keys[0]), keys
