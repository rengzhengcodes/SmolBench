"""The deduction analysis scripts' reporting contracts (13-13, 13-16, 13-26).

These three scripts produce the study's published prose and numbers, and each
finding here is about a claim the code made that the data did not support:

* **13-13** -- the null-result narrative ("this null rules out LARGE effects",
  "consistent with no effect rather than a real effect") printed unconditionally,
  even on data where every contrast was Holm-significant, and quoted a different
  study's effect range as a literal in its own conclusion.
* **13-16** -- three loaders `continue` past ``replicate_idx != 0`` under a
  docstring calling it "a filter, not an assumption ... the code stays correct if
  a later run adds replicates". Dropped rows must be announced.
* **13-26** -- a hand-rolled log-space binomial CDF standing in for
  ``scipy.stats.binom`` in a file whose own run environment provides scipy.

Loaded by file path, as the scripts themselves are: they run under
``uv run --no-project --with numpy --with scipy`` with no smolbench installed.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from math import comb
from pathlib import Path

import pytest

from tests._paths import NOTEBOOKS

ANALYSIS = NOTEBOOKS / "deduction" / "analysis"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        f"deduction_analysis_{name}", ANALYSIS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def pa():
    return _load("power_analysis")


@pytest.fixture(scope="module")
def hvn():
    return _load("hint_vs_noise")


def _cell(theorem, rung, ok, *, model="m", k=1, replicate_idx=0):
    return {"kind": "cell", "model": model, "theorem_id": theorem, "k": k,
            "rung": rung, "replicate_idx": replicate_idx,
            "verdict": "success" if ok else "lean_error"}


def _write_rows_dir(root: Path, models, *, n_theorems, b, c):
    """One `verified_rows.jsonl` per model: `b` hint-only wins, `c` noise-only wins.

    The remaining ``n_theorems - b - c`` cells are concordant successes, so the
    discordant total (what exact McNemar conditions on) is exactly ``b + c``.
    """
    for model in models:
        d = root / model
        d.mkdir(parents=True)
        rows = []
        for i in range(n_theorems):
            if i < b:
                hint_ok, noise_ok = True, False
            elif i < b + c:
                hint_ok, noise_ok = False, True
            else:
                hint_ok, noise_ok = True, True
            rows.append(_cell(f"T{i}", "hint:3", hint_ok, model=model))
            rows.append(_cell(f"T{i}", "noise:3", noise_ok, model=model))
        (d / "verified_rows.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows))


# ---------------------------------------------------------------------------
# 13-13: the null narrative must follow the result
# ---------------------------------------------------------------------------


#: Fragments that may ONLY appear when nothing reached significance.
_NULL_NARRATIVE = ("rules out LARGE effects", "consistent with no effect")
#: A different study's numbers, quoted as literals in this one's conclusion.
_CROSS_STUDY_LITERALS = ("0.155", "0.866")


def test_null_narrative_is_suppressed_when_everything_is_significant(hvn, tmp_path, capsys):
    """13-13: an all-significant run must not print the null-result paragraph.

    Every model gets 60 cells, of which 20 are discordant and ALL favour
    hint:3 (b=20, c=0), so exact McNemar gives
    p = 2 * 0.5**20 and Holm rejects for all 21 models. Before the fix the
    script printed "Significant under Holm: 21 of 21" and then, verbatim, both
    null sentences -- the MDE interpretation sits inside `if boundaries:`,
    which is a statement about whether the MDE was computable, not about
    whether the result was null, and the direction sentence was ungated
    entirely.
    """
    _write_rows_dir(tmp_path, hvn.MODELS, n_theorems=60, b=20, c=0)
    assert hvn.main(["--rows-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Significant under Holm: 21 of 21" in out
    for fragment in _NULL_NARRATIVE:
        assert fragment not in out, (
            f"{fragment!r} printed on data where every contrast is significant"
        )


def test_null_narrative_still_prints_on_an_actual_null(hvn, tmp_path, capsys):
    """13-13: the interpretation is gated, not deleted -- a real null still gets it.

    b/c is 11/9 for half the models and 9/11 for the rest: 20 discordant pairs
    per model (enough that the MDE's boundary search can clear Holm's strictest
    step, so the paragraph is reachable at all), a two-sided p near 0.82, and a
    sign split near even, which is what "consistent with no effect" is supposed
    to describe.
    """
    half = len(hvn.MODELS) // 2
    _write_rows_dir(tmp_path, hvn.MODELS[:half], n_theorems=60, b=11, c=9)
    _write_rows_dir(tmp_path, hvn.MODELS[half:], n_theorems=60, b=9, c=11)
    assert hvn.main(["--rows-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Significant under Holm: 0 of 21" in out
    assert "MINIMUM DETECTABLE EFFECT" in out
    assert any(fragment in out for fragment in _NULL_NARRATIVE), (
        "a genuine null must still be interpreted; the fix gates the paragraph, "
        "it does not remove it"
    )
    # The direction line reports the counts it computed, not a fixed verdict.
    assert f"{half} favour hint:3" in out or f"{len(hvn.MODELS) - half} favour hint:3" in out


def test_no_cross_study_effect_literals_in_the_conclusion(hvn, tmp_path, capsys):
    """13-13: the induction leg's 0.155-0.866 range is not a literal in this leg.

    Checked in the SOURCE as well as the output: a conclusion that quotes
    another study's effect sizes from a string literal cannot go stale
    visibly. If the range is ever restored it must be read from that study's
    report at runtime.
    """
    source = (ANALYSIS / "hint_vs_noise.py").read_text()
    for literal in _CROSS_STUDY_LITERALS:
        assert literal not in source, (
            f"{literal!r} is still a literal in hint_vs_noise.py"
        )
    half = len(hvn.MODELS) // 2
    _write_rows_dir(tmp_path, hvn.MODELS[:half], n_theorems=60, b=11, c=9)
    _write_rows_dir(tmp_path, hvn.MODELS[half:], n_theorems=60, b=9, c=11)
    hvn.main(["--rows-dir", str(tmp_path)])
    out = capsys.readouterr().out
    for literal in _CROSS_STUDY_LITERALS:
        assert literal not in out


# ---------------------------------------------------------------------------
# 13-16: dropped replicates are announced
# ---------------------------------------------------------------------------


def test_extra_replicates_are_reported_as_dropped(pa, tmp_path, capsys, caplog):
    """13-16: an R>1 row is DISCARDED, and the loader says so with a count.

    The docstring used to call the ``replicate_idx == 0`` filter "a filter, not
    an assumption ... the code stays correct if a later run adds replicates".
    It is an assumption: replicate 1 is dropped, never aggregated, so a run
    that bought replicates would silently be analysed at R=1. Accepts the
    warning on either channel, since these scripts print banners to stderr in
    some places and use `logging` in others -- what is pinned is that the
    count is announced at all.
    """
    path = tmp_path / "verified_rows.jsonl"
    rows = [
        _cell("T1", "stepk:1", True, model="m1"),
        _cell("T1", "stepk:1", False, model="m1", replicate_idx=1),
        _cell("T1", "stepk:1", False, model="m1", replicate_idx=2),
        _cell("T1", "stepk:1", True, model="m2"),
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))

    with caplog.at_level(0):
        _, blocks, _ = pa.load_joint_cells([path], models=("m1", "m2"))
    captured = capsys.readouterr()
    announced = captured.out + captured.err + caplog.text

    assert blocks["T1"][(1, "stepk:1")] == {"m1": 1, "m2": 1}, (
        "replicate 0 is still what is graded"
    )
    assert "2" in announced and "replicate" in announced.lower(), (
        "the loader dropped 2 replicate rows without announcing it:\n" + announced
    )


def test_replicate_filter_docstrings_no_longer_claim_r_gt_1_correctness(pa):
    """13-16: no loader still advertises that it stays correct under R>1."""
    for path in (ANALYSIS / "power_analysis.py", ANALYSIS / "error_bars.py",
                 ANALYSIS / "hint_vs_noise.py"):
        text = path.read_text()
        assert "a filter, not an assumption" not in text, path.name
        assert "the code stays correct if a later run" not in text, path.name
        # Each of the three loaders must instead say the rows are DROPPED.
        if "replicate_idx" in text:
            assert "drop" in text.lower(), (
                f"{path.name} filters on replicate_idx without documenting that "
                "the rows are discarded"
            )


# ---------------------------------------------------------------------------
# 13-26: exact McNemar against the library
# ---------------------------------------------------------------------------


def _reference_mcnemar(b: int, c: int) -> float:
    """Exact two-sided McNemar p, computed independently of the module under test.

    Deliberately NOT scipy and NOT the module's own helper: a plain
    ``math.comb`` sum over the conditional Binomial(b + c, 1/2), so this pins
    the VALUE rather than agreement between two spellings of the same call.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


@pytest.mark.parametrize("b,c", [(0, 0), (0, 1), (1, 0), (3, 2), (10, 0), (20, 0),
                                 (60, 60), (120, 0), (61, 59), (120, 120)])
def test_mcnemar_exact_p_matches_an_independent_reference(pa, b, c):
    """13-26: the scipy-backed implementation returns the same numbers.

    Includes the edge cases the hand-rolled version handled explicitly and
    which a naive rewrite loses: ``b + c == 0`` (no discordant pairs -> p = 1,
    not a division by zero) and the two-sided doubling clamped at 1.0.
    """
    got = pa.mcnemar_exact_p(b, c)
    want = _reference_mcnemar(b, c)
    assert got == pytest.approx(want, abs=1e-9), (b, c, got, want)
    assert 0.0 <= got <= 1.0


def test_mcnemar_exact_p_agrees_across_the_whole_grid(pa):
    """Sweep b, c in 0..120 -- the range the study's discordant totals live in."""
    worst = max(
        abs(pa.mcnemar_exact_p(b, c) - _reference_mcnemar(b, c))
        for b in range(0, 121, 7) for c in range(0, 121, 7)
    )
    assert worst <= 1e-9, f"max |mcnemar_exact_p - reference| = {worst:g}"


# ---------------------------------------------------------------------------
# 13-26 (second half): Holm delegated to statsmodels
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def eb():
    return _load("error_bars")


def _reference_holm(pvals, alpha):
    """Holm step-down, computed independently of the module under test.

    The rule the deleted hand-rolled body implemented: sort ascending, reject
    ranks ``1..i`` for the largest ``i`` whose ``p_(i) <= alpha / (m - i + 1)``,
    stopping at the first rank that fails. Uses a STABLE sort, which is what
    the old implementation used and what `multipletests` does not guarantee --
    so an equal result here is evidence the tie-handling really is
    order-independent, not just that two spellings agree.
    """
    import numpy as np

    m = len(pvals)
    order = np.argsort(np.asarray(pvals), kind="stable")
    reject = [False] * m
    for i, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - i):
            reject[idx] = True
        else:
            break
    return reject


@pytest.mark.parametrize("pvals", [
    [0.001, 0.002, 0.03, 0.9],
    [0.9, 0.03, 0.002, 0.001],                  # reversed: mask must follow input order
    [0.05 / 4] * 4,                             # every value exactly on rank 1's threshold
    [0.001, 0.001, 0.001, 0.5, 0.5],            # ties away from the boundary
    [1.0, 1.0, 1.0],                            # nothing rejected
    [0.0, 0.0],                                 # everything rejected
    [0.05 / 3, 0.05 / 2, 0.05, 0.4],            # each value on its OWN rank's threshold
])
def test_holm_delegation_matches_the_step_down_rule(eb, pvals):
    """13-26: `multipletests(method="holm")` reproduces the rule it replaced.

    `error_bars.holm`'s body was byte-identical to the induction leg's
    `paired_analysis.holm`; it now delegates to statsmodels. The risk in that
    swap is TIE HANDLING: several contrasts in this family sit exactly on the
    permutation test's 1/(B+1) resolution floor, so exact ties at the decision
    boundary are routine, and `multipletests` sorts with a plain (not
    guaranteed stable) `np.argsort`. These cases put ties on every rank's
    threshold and in reversed input order.
    """
    import numpy as np

    got = eb.holm(np.array(pvals, dtype=float), 0.05)
    assert list(map(bool, got)) == _reference_holm(pvals, 0.05), (pvals, list(got))
    assert len(got) == len(pvals), "the mask must stay in the input's order and length"
