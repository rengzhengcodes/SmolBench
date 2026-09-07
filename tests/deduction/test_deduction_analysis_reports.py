"""Reporting contracts for the deduction analysis scripts -- each check below guards
a claim the code made that the data did not support: an unconditional null-narrative
sentence, a cross-study literal in the conclusion, a silently dropped extra
replicate, and a hand-rolled binomial CDF standing in for scipy.

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


#: Bare module names the deduction and induction analysis scripts share. The
#: scripts import their siblings by bare name off their own sys.path insert,
#: so a cached induction ``power_analysis`` (left by tests/analysis) would be
#: handed to deduction's ``error_bars`` and fail with an ImportError on a
#: symbol only the induction module lacks. Evict foreign siblings first.
_BARE_SIBLINGS = ("_power_common", "power_analysis", "paired_analysis", "error_bars",
                  "hint_vs_noise", "rows_source", "significance_report",
                  "extens_vs_noise", "multiplicity_sim")


def _owned_by(module, directory: Path) -> bool:
    file = getattr(module, "__file__", None)
    return bool(file) and Path(file).resolve().parent == directory.resolve()


def _load(name: str):
    for sibling in _BARE_SIBLINGS:
        mod = sys.modules.get(sibling)
        if mod is not None and not _owned_by(mod, ANALYSIS):
            del sys.modules[sibling]
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


# The null narrative must follow the result.


#: Fragments that may ONLY appear when nothing reached significance.
_NULL_NARRATIVE = ("rules out LARGE effects", "consistent with no effect")
#: A different study's numbers, quoted as literals in this one's conclusion.
_CROSS_STUDY_LITERALS = ("0.155", "0.866")


def test_null_narrative_is_suppressed_when_everything_is_significant(hvn, tmp_path, capsys):
    """An all-significant run (b=20, c=0 for every model, p=2*0.5**20, Holm rejects all 21) must not print the null-result paragraph."""
    _write_rows_dir(tmp_path, hvn.MODELS, n_theorems=60, b=20, c=0)
    assert hvn.main(["--rows-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Significant under Holm: 21 of 21" in out
    for fragment in _NULL_NARRATIVE:
        assert fragment not in out, (
            f"{fragment!r} printed on data where every contrast is significant"
        )


def test_null_narrative_still_prints_on_an_actual_null(hvn, tmp_path, capsys):
    """The interpretation is gated, not deleted: b/c=11/9 (and reversed) gives 20 discordant pairs, p near 0.82, and a near-even sign split -- a genuine null must still get the paragraph."""
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
    """The induction leg's 0.155-0.866 range must not be a literal here, checked in source and output: if it's ever restored it must be read from that study's report at runtime, not hardcoded."""
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


# Dropped replicates are announced.


def test_extra_replicates_are_reported_as_dropped(pa, tmp_path, capsys, caplog):
    """replicate_idx != 0 rows are dropped, never aggregated; the loader must announce the count (stderr banner or logging), or a run with bought replicates would silently be analysed at R=1."""
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


# Exact McNemar against the library.


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
    """The scipy-backed implementation matches an independent reference, including b+c==0 (p=1, not division by zero) and the two-sided doubling clamped at 1.0."""
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


# Holm delegated to statsmodels.


@pytest.fixture(scope="module")
def eb():
    return _load("error_bars")


def _reference_holm(pvals, alpha):
    """Holm step-down, computed independently of the module under test.

    Sorts ascending and rejects ranks 1..i for the largest i whose p_(i) <= alpha /
    (m - i + 1), stopping at the first failing rank. Uses a stable sort, which the
    old hand-rolled implementation used and which `multipletests` does not guarantee.
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
    """multipletests(method="holm") must reproduce the retired hand-rolled rule exactly, including tie-handling: several contrasts sit exactly on the decision boundary, and multipletests's argsort is not guaranteed stable."""
    import numpy as np

    got = eb.holm(np.array(pvals, dtype=float), 0.05)
    assert list(map(bool, got)) == _reference_holm(pvals, 0.05), (pvals, list(got))
    assert len(got) == len(pvals), "the mask must stay in the input's order and length"
