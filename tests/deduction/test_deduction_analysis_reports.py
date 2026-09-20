"""Reporting contracts for deduction analysis scripts loaded by file path.

They run under ``uv run --no-project --with numpy --with scipy`` with no smolbench installed.
"""

# pylint: disable=missing-function-docstring

from __future__ import annotations

from math import comb
from pathlib import Path
from types import ModuleType

import pytest
from conftest import cell_row, write_jsonl

from tests._paths import NOTEBOOKS
from tests.analysis._trees import load_analysis

ANALYSIS = NOTEBOOKS / "deduction" / "analysis"


@pytest.fixture(scope="module")
def pa() -> ModuleType:
    return load_analysis("power_analysis", ANALYSIS)


@pytest.fixture(scope="module")
def hvn() -> ModuleType:
    return load_analysis("hint_vs_noise", ANALYSIS)


def _write_rows_dir(
    root: Path, models: list[str] | tuple[str, ...], *, n_theorems: int, b: int, c: int
) -> None:
    """Write rows with `b + c` discordant cells, which exact McNemar conditions on."""
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
            rows.append(
                cell_row(
                    theorem_id=f"T{i}",
                    rung="hint:3",
                    model=model,
                    verdict="success" if hint_ok else "lean_error",
                )
            )
            rows.append(
                cell_row(
                    theorem_id=f"T{i}",
                    rung="noise:3",
                    model=model,
                    verdict="success" if noise_ok else "lean_error",
                )
            )
        write_jsonl(d / "verified_rows.jsonl", rows)


# Null narrative follows the result.


#: Fragments allowed only for no significance.
_NULL_NARRATIVE = ("rules out LARGE effects", "consistent with no effect")
#: A different study's numbers, quoted as literals in this one's conclusion.
_CROSS_STUDY_LITERALS = ("0.155", "0.866")


def test_null_narrative_is_suppressed_when_everything_is_significant(
    hvn: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """With b=20, c=0, p=2*0.5**20, all 21 significant results omit null narrative."""
    _write_rows_dir(tmp_path, hvn.MODELS, n_theorems=60, b=20, c=0)
    assert hvn.main(["--rows-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Significant under Holm: 21 of 21" in out
    for fragment in _NULL_NARRATIVE:
        assert (
            fragment not in out
        ), f"{fragment!r} printed on data where every contrast is significant"


def test_null_narrative_still_prints_on_an_actual_null(
    hvn: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Gate rather than delete null interpretation; b/c=11/9 gives 20 pairs and p≈0.82."""
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
    # Report computed direction counts, not a fixed verdict.
    assert (
        f"{half} favour hint:3" in out
        or f"{len(hvn.MODELS) - half} favour hint:3" in out
    )


def test_no_cross_study_effect_literals_in_the_conclusion(
    hvn: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Cross-study 0.155–0.866 effects must be runtime data, never conclusion literals."""
    source = (ANALYSIS / "hint_vs_noise.py").read_text()
    for literal in _CROSS_STUDY_LITERALS:
        assert (
            literal not in source
        ), f"{literal!r} is still a literal in hint_vs_noise.py"
    half = len(hvn.MODELS) // 2
    _write_rows_dir(tmp_path, hvn.MODELS[:half], n_theorems=60, b=11, c=9)
    _write_rows_dir(tmp_path, hvn.MODELS[half:], n_theorems=60, b=9, c=11)
    hvn.main(["--rows-dir", str(tmp_path)])
    out = capsys.readouterr().out
    for literal in _CROSS_STUDY_LITERALS:
        assert literal not in out


# Dropped replicates are announced.


def test_extra_replicates_are_reported_as_dropped(
    pa: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Drop `replicate_idx != 0` with an announcement or paid data is silently analyzed at R=1."""
    path = tmp_path / "verified_rows.jsonl"
    rows = [
        cell_row(theorem_id="T1", rung="stepk:1", model="m1"),
        cell_row(
            theorem_id="T1",
            rung="stepk:1",
            model="m1",
            replicate_idx=1,
            verdict="lean_error",
        ),
        cell_row(
            theorem_id="T1",
            rung="stepk:1",
            model="m1",
            replicate_idx=2,
            verdict="lean_error",
        ),
        cell_row(theorem_id="T1", rung="stepk:1", model="m2"),
    ]
    write_jsonl(path, rows)

    with caplog.at_level(0):
        _, blocks, _ = pa.load_joint_cells([path], models=("m1", "m2"))
    captured = capsys.readouterr()
    announced = captured.out + captured.err + caplog.text

    assert blocks["T1"][(1, "stepk:1")] == {
        "m1": 1,
        "m2": 1,
    }, "replicate 0 is still what is graded"
    assert "2" in announced and "replicate" in announced.lower(), (
        "the loader dropped 2 replicate rows without announcing it:\n" + announced
    )


# Exact McNemar against the library.


def _reference_mcnemar(b: int, c: int) -> float:
    """Independent Binomial(b+c, 1/2) McNemar reference so this tests values, not the same call twice."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


@pytest.mark.parametrize(
    "b,c",
    [
        (0, 0),
        (0, 1),
        (1, 0),
        (3, 2),
        (10, 0),
        (20, 0),
        (60, 60),
        (120, 0),
        (61, 59),
        (120, 120),
    ],
)
def test_mcnemar_exact_p_matches_an_independent_reference(
    pa: ModuleType, b: int, c: int
) -> None:
    """Match the reference, including `b+c==0` → p=1 and a 1.0 cap."""
    got = pa.mcnemar_exact_p(b, c)
    want = _reference_mcnemar(b, c)
    assert got == pytest.approx(want, abs=1e-9), (b, c, got, want)
    assert 0.0 <= got <= 1.0


def test_mcnemar_exact_p_agrees_across_the_whole_grid(pa: ModuleType) -> None:
    """Sweep b, c in 0..120 -- the range the study's discordant totals live in."""
    worst = max(
        abs(pa.mcnemar_exact_p(b, c) - _reference_mcnemar(b, c))
        for b in range(0, 121, 7)
        for c in range(0, 121, 7)
    )
    assert worst <= 1e-9, f"max |mcnemar_exact_p - reference| = {worst:g}"


# Holm delegated to statsmodels.


@pytest.fixture(scope="module")
def eb() -> ModuleType:
    return load_analysis("error_bars", ANALYSIS)


def _reference_holm(pvals: list[float], alpha: float) -> list[bool]:
    """Independent stable-sort Holm reference because `multipletests` order is not guaranteed."""
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


@pytest.mark.parametrize(
    "pvals",
    [
        [0.001, 0.002, 0.03, 0.9],
        [0.9, 0.03, 0.002, 0.001],  # reversed: mask must follow input order
        [0.05 / 4] * 4,  # every value exactly on rank 1's threshold
        [0.001, 0.001, 0.001, 0.5, 0.5],  # ties away from the boundary
        [1.0, 1.0, 1.0],  # nothing rejected
        [0.0, 0.0],  # everything rejected
        [0.05 / 3, 0.05 / 2, 0.05, 0.4],  # each value on its OWN rank's threshold
    ],
)
def test_holm_delegation_matches_the_step_down_rule(
    eb: ModuleType, pvals: list[float]
) -> None:
    """Match the prior Holm rule at tie-sensitive decision boundaries."""
    import numpy as np

    got = eb.holm(np.array(pvals, dtype=float), 0.05)
    assert list(map(bool, got)) == _reference_holm(pvals, 0.05), (pvals, list(got))
    assert len(got) == len(pvals), "the mask must stay in the input's order and length"
