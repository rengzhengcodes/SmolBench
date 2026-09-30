"""Behavioral pins for induction analysis reports.

Synthetic trees keep reported claims conditional on their supporting data.
"""

import math
import re
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from smolbench.evals.parsing import EMPTY
from tests.analysis._trees import (
    DEEP_DEPTH,
    FAMILIES,
    FIRST_CELL,
    INFOS,
    MODELS,
    N_HARMONICS,
    N_PRIMARY,
    N_REPLICATES,
    SHALLOW_DEPTH,
    Cell,
    _power_common,
    build_tree,
    copies_from,
    extens_vs_noise,
    paired_analysis,
    profile_for,
    run_captured,
    significance_report,
    study_design,
    tree_fixture,
)

#: Collapsed noise arm whose failed control is padding-driven.
COLLAPSE_MODEL = "ds_pro"
#: Compliant failed control that padding cannot exonerate.
WEAK_MODEL = "min3_3b"
#: Mismatched seed coverage makes whole-cell and common-seed deltas differ.
SKEW_MODEL = "exaone_32b"
#: Byte copy creates an exact tie.
TIED_MODEL = "nemo3_30b"
#: Lane the single-lane fixtures perturb: reversed control, non-pad collapse, copied padding control.
LANE_MODEL = "ds_flash"
if not {COLLAPSE_MODEL, WEAK_MODEL, SKEW_MODEL, TIED_MODEL, LANE_MODEL} <= set(MODELS):
    raise RuntimeError("a fixture tag is no longer on the pre-registered roster")

#: Seeds below this are SKEW_MODEL's noise coverage; its intens non-compliance starts here.
_SKEW_SPLIT = 10


def _skew_census(
    per_seed: Mapping[tuple[str, str], Mapping[int, int]],
) -> Callable[[dict], dict]:
    """Wrap the census so `per_seed` ``{cell: {seed: non_compliant}}`` (of `N_HARMONICS` marks) overwrite it and the cell rate is recomputed."""
    real = significance_report.compliance_census

    def skewed(marks: object) -> dict:
        census = real(marks)
        for key, replacements in per_seed.items():
            cell = census[key]
            cell["per_seed"].update(
                {seed: (nc, N_HARMONICS) for seed, nc in replacements.items()}
            )
            nc = sum(n for n, _t in cell["per_seed"].values())
            cell["rate"] = nc / sum(t for _n, t in cell["per_seed"].values())
        return census

    return skewed


def test_collapse_note_uses_the_supplied_rate() -> None:
    """Collapse annotations use the compared-seed rate, not the whole-cell rate."""
    key = ("model", "noise_intens")
    census = {key: {"modes": Counter({EMPTY: 3})}}
    assert significance_report.collapse_note(key, 0.1, census) == ""
    assert significance_report.collapse_note(key, 0.3, census).startswith(
        "model/noise_intens 30.0% non-compliant"
    )


def test_gate_note_handles_no_data_and_numeric_gates() -> None:
    """Ungated ladder findings render both available and unavailable gate p-values."""
    row = {"kind_is_ladder": True, "gated": False, "family": "family"}
    assert (
        significance_report.gate_note(row, {"family": {"p_gate": None}})
        == "  [UNGATED: family omnibus has no common-seed data]"
    )
    assert (
        significance_report.gate_note(row, {"family": {"p_gate": 0.001234}})
        == "  [UNGATED: family omnibus p=1.23e-03]"
    )
    assert (
        significance_report.gate_note(
            {**row, "gated": True}, {"family": {"p_gate": None}}
        )
        == ""
    )


def test_classify_rejects_a_zero_first_pair() -> None:
    """A zero arm in `key_a` would invert the arm-vs-floor reading; refuse it."""
    with pytest.raises(RuntimeError, match="zero arm must be key_b"):
        significance_report.classify(("m", "zero"), ("m", "intens"))


#: The family `_steep_profile` makes rise; every other family stays flat.
_STEEP_FAMILY, _STEEP_RUNGS = next(iter(FAMILIES.items()))


def _steep_profile(depth: int) -> Callable[[str, str], Cell]:
    """First family's rungs rise 0.2/0.5/0.9 over `depth` seeds; all else default."""
    return profile_for(
        {
            (rung, info): (rate, 0.0, range(depth))
            for rung, rate in zip(_STEEP_RUNGS, (0.20, 0.50, 0.90))
            for info in INFOS
            if info != "zero"
        },
        depth=depth,
    )


ladder_tree = tree_fixture(
    "ladder_tree",
    _steep_profile(DEEP_DEPTH),
    "16 seeds; the first family's rungs rise steeply (0.2/0.5/0.9).",
)


def test_omnibus_gates_reject_on_a_steep_ladder(ladder_tree: Path) -> None:
    """A clearly rising family trips its Tier-1 gate."""
    marks = significance_report.load_marks(ladder_tree)
    gate = significance_report.omnibus_gates(marks)[_STEEP_FAMILY]
    assert gate["n_seeds"] == DEEP_DEPTH
    assert gate["reject"] is True
    assert gate["p"] < study_design.ALPHA_OMNIBUS
    assert gate["p_perm"] < study_design.ALPHA_OMNIBUS


def test_omnibus_gates_do_not_reject_flat_family(clean_tree: Path) -> None:
    """Equal rung rates on the copied info arms (zero arms are independent draws) leave every gate unrejected."""
    marks = significance_report.load_marks(clean_tree)
    gates = significance_report.omnibus_gates(marks)
    assert gates
    for gate in gates.values():
        assert gate["p_gate"] > study_design.ALPHA_OMNIBUS
        assert gate["reject"] is False


def test_omnibus_gate_permutation_isolated_by_family(ladder_tree: Path) -> None:
    """A family gate's permutation p-value ignores unrelated family cells."""
    marks = significance_report.load_marks(ladder_tree)
    full = significance_report.omnibus_gates(marks)
    family, rungs = list(FAMILIES.items())[-1]
    filtered = paired_analysis.CellMarks(
        {k: v for k, v in marks.correct.items() if k[0] in rungs},
        marks.valid,
        marks.compliance,
    )
    partial = significance_report.omnibus_gates(filtered)

    assert partial[family]["p_perm"] == full[family]["p_perm"]
    for other, gate in partial.items():
        if other != family:
            assert gate == significance_report.GATE_NO_DATA


def test_omnibus_gate_uses_only_common_seeds(tmp_path: Path) -> None:
    """A cell missing seeds shrinks the gate's seed set to the intersection."""
    narrow = (_STEEP_RUNGS[0], "intens")
    build_tree(tmp_path, profile_for({narrow: (0.90, 0.0, range(10))}))
    marks = significance_report.load_marks(tmp_path)
    gates = significance_report.omnibus_gates(marks)
    assert gates[_STEEP_FAMILY]["n_seeds"] == 10
    for other, gate in gates.items():
        if other != _STEEP_FAMILY:
            assert gate["n_seeds"] == DEEP_DEPTH


def test_ungated_ladder_findings_are_labelled_exploratory(
    ladder_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A significant ladder contrast in a non-rejecting family is marked UNGATED."""
    out, computed = rendered(ladder_tree)
    assert computed.gates[_STEEP_FAMILY]["reject"]
    gated_ladders = [r for r in computed.findings if r["kind_is_ladder"] and r["gated"]]
    assert gated_ladders, "ladder_tree should yield gated ladder findings"
    assert "[UNGATED:" not in out

    monkeypatch.setattr(
        significance_report,
        "omnibus_gates",
        lambda _marks: {
            family: significance_report._gate_row(DEEP_DEPTH, 0.0, 0.5, 0.5)
            for family in FAMILIES
        },
    )
    ungated = significance_report.compute(ladder_tree)
    assert sum(r["kind_is_ladder"] and not r["gated"] for r in ungated.findings) == len(
        gated_ladders
    )
    out = run_captured(lambda: significance_report.render(ungated))
    assert "[UNGATED:" in out
    assert "does not confer confirmatory status" in out


def test_missing_family_cell_yields_no_data_gate(
    clean_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An absent cell reports the no-data gate entry, and render prints it."""
    marks = significance_report.load_marks(clean_tree)
    del marks.correct[(_STEEP_RUNGS[0], "intens")]
    gates = significance_report.omnibus_gates(marks)
    assert gates[_STEEP_FAMILY] == significance_report.GATE_NO_DATA

    # load_marks cannot produce a missing cell, so the gate is patched; any session tree serves.
    real = significance_report.omnibus_gates

    def fake(marks: object) -> dict:
        gates = real(marks)
        gates[_STEEP_FAMILY] = dict(significance_report.GATE_NO_DATA)
        return gates

    monkeypatch.setattr(significance_report, "omnibus_gates", fake)
    out = run_captured(lambda: significance_report.main(clean_tree))
    assert (
        f"{_STEEP_FAMILY:12s} n_seeds=  0 stat=     n/a p_chi2=      n/a "
        "p_perm=      n/a  no data" in out
    )


#: The steep family's third rung, per arm: windows that overlap pairwise but share no seed.
_SPLIT_SEEDS = {
    "intens": tuple(range(20)),
    "extens": tuple(range(10, N_REPLICATES)),
    "noise_intens": tuple(range(10)) + tuple(range(20, N_REPLICATES)),
    "zero": tuple(range(5)) + tuple(range(15, N_REPLICATES)),
}
no_data_gate_tree = tree_fixture(
    "no_data_gate_tree",
    profile_for(
        {
            (rung, info): (rate, 0.0, seeds)
            for info in INFOS
            for rung, rate, seeds in (
                (_STEEP_RUNGS[0], 0.0, range(N_REPLICATES)),
                (_STEEP_RUNGS[1], 1.0, range(N_REPLICATES)),
                (_STEEP_RUNGS[2], 0.9, _SPLIT_SEEDS[info]),
            )
        },
        depth=N_REPLICATES,
    ),
    "30 seeds; the steep family's ladders overlap pairwise but share no family-wide seed.",
)


def test_no_data_gate_renders_ungated(no_data_gate_tree: Path) -> None:
    """An ungated significant ladder finding renders a no-data explanation."""
    out, computed = rendered(no_data_gate_tree)
    ungated = [
        row
        for row in computed.findings
        if row["kind_is_ladder"] and row["family"] == _STEEP_FAMILY and not row["gated"]
    ]
    assert ungated
    assert computed.gates[_STEEP_FAMILY]["p"] is None
    assert "omnibus has no common-seed data" in out


def test_permutation_p_is_deterministic_and_bounded() -> None:
    """Same tensor and seed give the same p; the plus-one keeps it in (0, 1]."""
    rng = np.random.default_rng(0)
    tensor = (
        rng.random((8, study_design.N_RUNGS, N_HARMONICS * len(INFOS))) < 0.9
    ).astype(np.int64)
    stat = float(study_design.gcmh_stat(tensor.sum(axis=0)[None], 8)[0])
    p1, p2 = (
        significance_report.permutation_omnibus_p(
            tensor, stat, np.random.default_rng([significance_report.SEED, 0])
        )
        for _ in range(2)
    )
    assert p1 == p2
    assert 0 < p1 <= 1


def test_gate_requires_both_p_values(tmp_path: Path) -> None:
    """With 2 seeds the permutation p floors above ALPHA_OMNIBUS, so the asymptotic reject does not gate."""
    build_tree(tmp_path, _steep_profile(2))
    marks = significance_report.load_marks(tmp_path)
    gate = significance_report.omnibus_gates(marks)[_STEEP_FAMILY]
    assert gate["n_seeds"] == 2
    # The asymptotic p alone would gate; only the within-seed permutation blocks it.
    assert gate["p"] <= study_design.ALPHA_OMNIBUS
    # (N_RUNGS!)**n_seeds per-seed labellings, but gcmh_stat is invariant under a joint
    # relabelling, so N_RUNGS! of them tie the observed statistic: the exact p-value is
    # at least 1 / N_RUNGS!**(n_seeds - 1) (exactly that on this tree), far above the
    # +1 floor; the slack is three Monte-Carlo standard errors over N_GATE_PERMS draws.
    floor = 1 / math.factorial(study_design.N_RUNGS) ** (gate["n_seeds"] - 1)
    assert gate["p_perm"] >= floor - 3 * math.sqrt(
        floor * (1 - floor) / significance_report.N_GATE_PERMS
    )
    assert gate["p_perm"] > study_design.ALPHA_OMNIBUS
    assert gate["p_gate"] == max(gate["p"], gate["p_perm"])
    assert gate["reject"] is False


_DEEP = range(DEEP_DEPTH)
_LOW, _HIGH = (0.10, 0.0, _DEEP), (0.90, 0.0, _DEEP)

shallow_tree = tree_fixture(
    "shallow_tree",
    profile_for(depth=SHALLOW_DEPTH),
    "6 seeds everywhere: below the sign-flip resolution floor.",
)
collapse_tree = tree_fixture(
    "collapse_tree",
    profile_for(
        {
            # 1.0, not TOTAL_COLLAPSE: a rate generated at the threshold is a coin flip on 144 marks.
            (COLLAPSE_MODEL, "noise_intens"): (0.10, 1.0, _DEEP),
            (WEAK_MODEL, "intens"): _LOW,
            # Non-compliance is outside noise's seed coverage.
            (SKEW_MODEL, "intens"): (
                0.90,
                lambda seed: 0.90 if seed >= _SKEW_SPLIT else 0.0,
                _DEEP,
            ),
            (SKEW_MODEL, "noise_intens"): (0.90, 0.50, range(_SKEW_SPLIT)),
        }
    ),
    "16 seeds, with the four engineered anomalies this module's constants name.",
    copies={(TIED_MODEL, "noise_intens"): (TIED_MODEL, "extens")},
)
clean_tree = tree_fixture(
    "clean_tree",
    profile_for(rate=0.99),
    "16 seeds, every informative arm at 0.99 and compliant: all ties, no collapse.",
    copies=copies_from(FIRST_CELL, [info for info in INFOS if info != "zero"]),
)
reversed_tree = tree_fixture(
    "reversed_tree",
    profile_for({(LANE_MODEL, "intens"): _LOW, (LANE_MODEL, "zero"): _HIGH}),
    "Build a tree with one significant informative arm below its floor.",
)
ceiling_tree = tree_fixture(
    "ceiling_tree",
    profile_for(rate=0.97),
    "Build a tree with ceiling pairs that include discordances.",
)
caveat_tree = tree_fixture(
    "caveat_tree",
    profile_for({(LANE_MODEL, "intens"): (0.50, 0.50, _DEEP)}),
    "Build a tree with collapse findings but no padding crossing.",
)
padding_control_tree = tree_fixture(
    "padding_control_tree",
    profile_for(),
    "Build a copied noise control whose compliance can be skewed independently.",
    copies={
        (LANE_MODEL, info): (LANE_MODEL, "zero") for info in ("intens", "noise_intens")
    },
)
shared_seed_noise_tree = tree_fixture(
    "shared_seed_noise_tree",
    profile_for({(SKEW_MODEL, "intens"): (0.90, 0.0, range(_SKEW_SPLIT))}),
    "Build a lane with clean extra noise seeds absent from intens.",
)


#: Captured report text and the `Report` it was rendered from.
Rendered = tuple[str, significance_report.Report]
_RENDERED: dict[Path, Rendered] = {}
#: The two functions tests monkeypatch; `rendered` refuses to run while either is replaced.
_UNPATCHED = (significance_report.compliance_census, significance_report.omnibus_gates)


def rendered(tree: Path) -> Rendered:
    """Compute and render the significance report once per session tree.

    A test that monkeypatches the census or the gates calls `significance_report.main`,
    or `compute` then `render`, itself: a patched result must never enter the cache.
    """
    assert (
        significance_report.compliance_census,
        significance_report.omnibus_gates,
    ) == _UNPATCHED
    if tree not in _RENDERED:
        computed = significance_report.compute(tree)
        out = run_captured(lambda: significance_report.render(computed))
        _RENDERED[tree] = (out, computed)
    return _RENDERED[tree]


#: ``skewed_report(tree, per_seed)``: the report on `tree` under a `_skew_census` of `per_seed`; never cached.
SkewedReport = Callable[[Path, Mapping[tuple[str, str], Mapping[int, int]]], Rendered]


@pytest.fixture
def skewed_report(monkeypatch: pytest.MonkeyPatch) -> SkewedReport:
    """Compute and render the report with `significance_report.compliance_census` replaced by `_skew_census(per_seed)`."""

    def report(
        tree: Path, per_seed: Mapping[tuple[str, str], Mapping[int, int]]
    ) -> Rendered:
        monkeypatch.setattr(
            significance_report, "compliance_census", _skew_census(per_seed)
        )
        computed = significance_report.compute(tree)
        return run_captured(lambda: significance_report.render(computed)), computed

    return report


# The shallow fixture pins the incomplete-sync guard and control messaging.


def test_shallow_sync_prints_an_incomplete_banner_and_no_exoneration(
    shallow_tree: Path,
) -> None:
    """At 6 seeds nothing is rejectable, so the report must say `INCOMPLETE SYNC` and suppress the padding exoneration."""
    out, computed = rendered(shallow_tree)
    assert computed.floor_bound
    assert min(r["n_seeds"] for r in computed.rows) == SHALLOW_DEPTH
    assert "INCOMPLETE SYNC" in out
    # The blanket exoneration must NOT print under a floor-bound family.
    assert "whitespace padding drove" not in out
    # Include threshold arithmetic so the banner is auditable.
    banner = out.split("INCOMPLETE SYNC", 1)[1][:800]
    assert f"2/2**{max(r['n_seeds'] for r in computed.rows)}" in banner
    assert f"ALPHA/m = {significance_report.ALPHA} / {len(computed.rows)}" in banner


def test_failing_controls_are_exonerated_only_where_the_pad_explains_them(
    collapse_tree: Path,
) -> None:
    """Collapsed noise controls are split from compliant failures."""
    out, computed = rendered(collapse_tree)
    assert computed.fails
    assert len(computed.fails) == (
        len(computed.fails_total)
        + len(computed.fails_partial)
        + len(computed.fails_unexplained)
    )
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    assert (
        f"These {len(computed.fails_total)} of {len(computed.fails)} failures"
        in controls
    )
    assert (
        f"{len(computed.fails_partial)} of {len(computed.fails)} failures are noise arms"
        in controls
    )

    assert "NOT explained by padding" in controls
    explained = controls.split("NOT explained by padding", 1)[0]
    # The partial-collapse caveat sits above the split ...
    assert "caveat, not a demonstrated cause of the failed control" in explained
    # ... and the compliant, non-noise failure is named below it.
    assert any(WEAK_MODEL in row["label"] for row in computed.fails_unexplained)


@pytest.fixture
def padding_control_report(
    padding_control_tree: Path, skewed_report: SkewedReport
) -> Callable[[int], Rendered]:
    """Render `padding_control_tree` with `noise_nc` of every noise-arm seed's marks non-compliant and the intens arm compliant."""
    return lambda noise_nc: skewed_report(
        padding_control_tree,
        {
            (LANE_MODEL, "intens"): dict.fromkeys(range(DEEP_DEPTH), 0),
            (LANE_MODEL, "noise_intens"): dict.fromkeys(range(DEEP_DEPTH), noise_nc),
        },
    )


def test_partial_pad_crossing_is_not_called_near_total(
    padding_control_report: Callable[[int], Rendered],
) -> None:
    """A partial compliance collapse is reported as a caveat, not control causation."""
    out, computed = padding_control_report(4)
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    assert computed.fails_partial
    assert not computed.fails_total
    assert f"{computed.partial_compliance} compliant on the compared seeds" in controls
    assert "near-total non-compliance" not in controls
    assert "55.6% compliant on the compared seeds" in controls
    assert "caveat, not a demonstrated cause of the failed control" in controls


def test_total_pad_crossing_keeps_near_total_exoneration(
    padding_control_report: Callable[[int], Rendered],
) -> None:
    """A total compliance collapse retains the padding exoneration."""
    out, computed = padding_control_report(N_HARMONICS)
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    assert computed.fails_total
    assert "near-total non-compliance" in controls


def test_reversed_controls_are_not_counted_as_passing(reversed_tree: Path) -> None:
    """A significant control below its floor is reported as reversed, not ahead."""
    out, computed = rendered(reversed_tree)
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    reversed_lines = [
        line for line in controls.splitlines() if line.startswith("  REVERSED")
    ]
    assert any(
        f"[{LANE_MODEL}] intens vs zero" in line for line in reversed_lines
    ), reversed_lines
    assert (
        f"{len(computed.passing)} significant with the informative arm AHEAD"
        in controls
    )
    assert f"{len(computed.reversed_)} significant\nbut REVERSED" in controls
    assert f"{len(computed.fails)} not rejected" in controls
    n_controls = len(computed.passing) + len(computed.reversed_) + len(computed.fails)
    assert f"{n_controls} arm-vs-floor positive controls" in controls


def test_replicate_depth_gate_uses_the_shallowest_lane(tmp_path: Path) -> None:
    """The shallowest lane controls the depth warning."""
    deep = (0.90, 0.0, range(N_REPLICATES))
    overrides = {(MODELS[0], "intens"): deep}
    build_tree(tmp_path, profile_for(overrides, depth=SHALLOW_DEPTH))
    out = run_captured(lambda: paired_analysis.main(tmp_path))
    assert (
        f"WARNING: shallowest lane has {SHALLOW_DEPTH} replicates and the "
        f"deepest has {N_REPLICATES}" in out
    )


def test_reports_handle_invalid_marks(tmp_path: Path) -> None:
    """Invalid marks are excluded from paired comparisons without breaking reports."""
    build_tree(tmp_path, profile_for(invalid=0.25))
    assert run_captured(lambda: significance_report.main(tmp_path))
    out = run_captured(lambda: paired_analysis.main(tmp_path))
    marks = paired_analysis.load_marks(tmp_path)
    contrasts = study_design.build_primary_contrasts()

    assert sum(
        r["n"] for r in paired_analysis.labeled_rows(marks, contrasts, True)
    ) < sum(r["n"] for r in paired_analysis.labeled_rows(marks, contrasts, False))
    assert "DROP-INVALID pairs" in out


# The PADDING EFFECT table subtracts both arms' rates over their common seeds only.


def test_padding_table_subtracts_over_the_common_seeds_only(
    collapse_tree: Path,
) -> None:
    """The delta is a within-lane difference, so both rates must be computed over the same seeds."""
    out, computed = rendered(collapse_tree)
    table = out.split("PADDING EFFECT", 1)[1].split("=> The pad", 1)[0]
    rows = {
        parts[0]: line
        for line in table.splitlines()
        if len(parts := line.split()) >= 4 and parts[1].endswith("%")
    }
    assert SKEW_MODEL in rows, rows
    row = rows[SKEW_MODEL]
    assert "COLLAPSE" in row and "not padding-specific" not in row, row
    skew = next(r for r in computed.pad_rows if r["model"] == SKEW_MODEL)
    assert skew["rate_i"] == 0
    assert "0.0%" in row


def test_padding_table_reports_the_seed_count_it_used(collapse_tree: Path) -> None:
    """Every row carries the n it was computed over, so a 10-seed comparison isn't mistaken for a 16-seed one."""
    out, computed = rendered(collapse_tree)
    header = [ln for ln in out.splitlines() if "delta" in ln and "noise" in ln]
    assert header, out[:2000]
    assert re.search(r"\bn\b", header[0]), header[0]
    n_common = {r["model"]: r["n_common"] for r in computed.pad_rows}
    assert n_common[SKEW_MODEL] == _SKEW_SPLIT
    assert n_common[COLLAPSE_MODEL] == DEEP_DEPTH


def test_padding_verdict_names_the_arm_that_crossed(
    collapse_tree: Path, skewed_report: SkewedReport
) -> None:
    """COLLAPSE needs a clean intens arm and a noise arm at or above the criterion; a lane already collapsed unpadded is not padding-specific."""
    verdicts = {r["model"]: r["verdict"] for r in rendered(collapse_tree)[1].pad_rows}
    assert verdicts[COLLAPSE_MODEL] == "COLLAPSE"
    # LANE_MODEL has no override on this tree: both arms are compliant, so the pad crossed nothing.
    assert verdicts[LANE_MODEL] == "contract holds"
    # Both arms fully non-compliant: the lane collapsed, but not because of the pad.
    _, computed = skewed_report(
        collapse_tree,
        {
            (LANE_MODEL, info): dict.fromkeys(range(DEEP_DEPTH), N_HARMONICS)
            for info in ("intens", "noise_intens")
        },
    )
    verdict = next(r["verdict"] for r in computed.pad_rows if r["model"] == LANE_MODEL)
    assert verdict == "collapsed, but not padding-specific"
    assert LANE_MODEL not in computed.pad_lanes


def test_padding_table_counts_come_from_the_rows_it_actually_built(
    collapse_tree: Path,
) -> None:
    """Every count in the section comes from the table's own row count, not a hard-coded lane total."""
    computed = rendered(collapse_tree)[1]
    # load_marks refuses a lane with a missing arm, so pad_rows only differs from
    # len(MODELS) on a hand-shortened Report.
    short = replace(computed, pad_rows=computed.pad_rows[1:])
    out = run_captured(lambda: significance_report.render(short))
    n_rows = len(MODELS) - 1
    n_over = sum(
        r["rate_n"] >= paired_analysis.COLLAPSE_THRESHOLD for r in short.pad_rows
    )
    assert f"In {n_over} of {n_rows} lanes with both arms measured" in out
    assert (
        f"=> The pad itself pushes {len(computed.pad_lanes)} of {n_rows} lanes" in out
    )


def test_all_cells_noise_count_uses_whole_cell_rates(
    shared_seed_noise_tree: Path, skewed_report: SkewedReport
) -> None:
    """The all-cells census count must not reuse common-seed padding rates."""
    out, computed = skewed_report(
        shared_seed_noise_tree,
        {
            (SKEW_MODEL, "intens"): dict.fromkeys(range(_SKEW_SPLIT), 0),
            (SKEW_MODEL, "noise_intens"): dict.fromkeys(range(3), N_HARMONICS),
        },
    )
    assert sum(k[1] == "noise_intens" for k in computed.over) == 0
    assert (
        sum(
            r["rate_n"] >= paired_analysis.COLLAPSE_THRESHOLD for r in computed.pad_rows
        )
        == 1
    )
    crit = paired_analysis.COLLAPSE_CRITERION
    assert (
        f"{len(computed.over)} of {len(computed.census)} cells are at or above the "
        f"{crit} criterion; 0 of them are noise arms." in out
    )
    assert f"In 1 of {len(computed.pad_rows)} lanes with both arms measured" in out


def test_zero_vs_zero_controls_report_the_measured_count_only(
    collapse_tree: Path, shallow_tree: Path
) -> None:
    """The report neither asserts nor assumes a zero rejection count for cross-model floors."""
    for tree in (collapse_tree, shallow_tree):
        out, computed = rendered(tree)
        assert computed.zero_vs_zero
        n_sig = sum(computed.hp[i] for i in computed.zero_vs_zero)
        assert f"{len(computed.zero_vs_zero)} zero-vs-zero ladder contrasts" in out
        assert f"another's): {n_sig} significant." in out


# Each narrative conclusion is gated by its own computed count.


def test_the_ladder_claim_is_conditional_on_its_own_count(
    shallow_tree: Path, collapse_tree: Path
) -> None:
    """The one-sided family-scaling claim needs `n_lad == len(lost)`; a mixed loss set names both stories and none prints only the info-arm story."""
    one_sided = "bites the family-scaling story, not the info-arm story"

    # Floor-bound: Holm rejects nothing, so no story claim is earned.
    assert "bites the family-scaling story" not in rendered(shallow_tree)[0]

    # Not floor-bound: the claim must track the count printed beside it.
    collapse, computed = rendered(collapse_tree)
    assert computed.lost, "fixture no longer produces any Holm losses"
    n_lad = sum(r["kind_is_ladder"] for r in computed.lost)
    assert (
        f"{n_lad} of the {len(computed.lost)} losses are LADDER contrasts" in collapse
    )
    assert n_lad == 0, "fixture now loses a ladder contrast; pin that branch directly"
    assert one_sided not in collapse, collapse
    assert "info-arm story" in collapse
    # No fixture loses a ladder contrast to the clustering correction, so the
    # n_lad > 0 branch is rendered from a Report with one forced ladder loss.
    forced = replace(
        computed, lost=[next(r for r in computed.rows if r["kind_is_ladder"])]
    )
    out = run_captured(lambda: significance_report.render(forced))
    assert (
        "1 of the 1 losses are LADDER contrasts -- the clustering correction\n"
        "   bites the family-scaling story, not the info-arm story." in out
    )
    # One loss of each kind: neither one-sided story is earned.
    mixed = replace(
        computed,
        lost=[
            next(r for r in computed.rows if r["kind_is_ladder"]),
            next(r for r in computed.rows if not r["kind_is_ladder"]),
        ],
    )
    out = run_captured(lambda: significance_report.render(mixed))
    assert "1 of the 2 losses are LADDER contrasts and 1 are INFO-ARM" in out
    assert one_sided not in out


@pytest.mark.parametrize(
    "claim",
    (
        # A non-noise cell at or over the criterion.
        "non-noise arms appear here",
        # A significant finding that touches a collapse: neither count may be zero.
        "TWO-MECHANISM",
        # At least one lane crossed the criterion because of the pad.
        "is not inert",
    ),
)
def test_collapse_claims_print_only_on_the_tree_that_earns_them(
    claim: str, shallow_tree: Path, clean_tree: Path, collapse_tree: Path
) -> None:
    """Each collapse claim prints on the collapse tree and on neither the floor-bound nor the all-tied tree."""
    assert claim not in rendered(shallow_tree)[0]
    assert claim not in rendered(clean_tree)[0]
    assert claim in rendered(collapse_tree)[0]


def test_two_mechanism_needs_a_pad_crossing_extens_vs_noise_finding(
    caveat_tree: Path,
) -> None:
    """A collapse annotation without a pad crossing cannot support two mechanisms."""
    out, computed = rendered(caveat_tree)
    n_flag = sum(bool(r["collapse_tag"]) for r in computed.findings)
    assert n_flag > 0
    assert f"[COLLAPSE] {n_flag} of {len(computed.findings)} findings touch" in out
    assert "TWO-MECHANISM" not in out
    assert "None is an extens-vs-noise finding" in out


def test_the_ceiling_claim_is_conditional_and_counts_its_discordances(
    clean_tree: Path,
) -> None:
    """`CEILING pairs` needs at least one ceiling pair, and its zero-discordant count must be measured, not asserted as "many"."""
    clean, computed = rendered(clean_tree)
    ceiling_line = [ln for ln in clean.splitlines() if "CEILING pairs" in ln]
    assert ceiling_line, clean[-2000:]
    # Every finding on the clean tree is a tie: 63 ladder + 63 info-arm contrasts.
    assert not computed.findings
    assert len(computed.ceiling) == sum(r["kind"] == "finding" for r in computed.rows)
    assert (
        f"CEILING pairs (both arms >= {significance_report.CEILING}): "
        f"{len(computed.ceiling)}" in clean
    )
    n_zero_disc = sum(r["b"] + r["c"] == 0 for r in computed.ceiling)
    assert n_zero_disc == len(computed.ceiling)
    assert f"{n_zero_disc} of them have ZERO discordant items" in clean


def test_ceiling_non_rejections_are_split_into_ties_and_unresolved(
    ceiling_tree: Path,
) -> None:
    """Ceiling non-rejections distinguish exact ties from unresolved pairs."""
    out, computed = rendered(ceiling_tree)
    assert computed.ceiling
    n_zero_disc = sum(r["b"] + r["c"] == 0 for r in computed.ceiling)
    assert f"{n_zero_disc} of them have ZERO discordant items" in out
    assert "UNRESOLVED" in out
    assert n_zero_disc < len(computed.ceiling)


def test_holm_boundary_block_prints_the_ranks_around_the_stop(
    collapse_tree: Path,
) -> None:
    """The boundary block lists the last two Holm rejections and the first two stops, each at its own step threshold."""
    out, computed = rendered(collapse_tree)
    block = out.split("Holm step-down at the boundary", 1)[1].split("\n\n", 1)[0]
    parsed = re.findall(
        r"(REJ |stop) rank\s+(\d+)\s+p=([0-9.e+-]+)\s+thr=([0-9.e+-]+)", block
    )
    n_rej, m = int(computed.hp.sum()), len(computed.rows)
    assert 2 <= n_rej <= m - 2, n_rej
    assert [(mark, int(rank)) for mark, rank, _p, _thr in parsed] == [
        ("REJ ", n_rej - 1),
        ("REJ ", n_rej),
        ("stop", n_rej + 1),
        ("stop", n_rej + 2),
    ]
    ranked = sorted(r["p_cluster"] for r in computed.rows)
    for mark, rank, p, thr in parsed:
        i = int(rank)
        step = significance_report.ALPHA / (m - i + 1)
        assert (p, thr) == (f"{ranked[i - 1]:.4e}", f"{step:.4e}"), (mark, rank)
    # Holm rejects through rank n_rej and stops at the first rank whose p exceeds its step.
    assert ranked[n_rej - 1] <= significance_report.ALPHA / (m - n_rej + 1)
    assert ranked[n_rej] > significance_report.ALPHA / (m - n_rej)


def test_standing_question_flag_follows_holm_not_bonferroni(
    reversed_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A Holm-rejected intens-vs-noise row prints SEPARATES even where Bonferroni would not reject it."""
    marks = paired_analysis.load_marks(reversed_tree)
    key_a, key_b = (MODELS[0], "intens"), (MODELS[0], "noise_intens")
    a, b, sidx, _hidx = paired_analysis.aligned(marks, key_a, key_b, False)
    target = paired_analysis.seed_diffs(a, b, sidx)
    # Above Bonferroni's ALPHA/m but within Holm's second step ALPHA/(m - 1); the floor
    # contrasts at 2/2**DEEP_DEPTH rank ahead of it and carry it past that step.
    p_between = (study_design.ALPHA_PRIMARY + _power_common.ALPHA / (N_PRIMARY - 1)) / 2
    real = paired_analysis.signflip_exact_p
    monkeypatch.setattr(
        paired_analysis,
        "signflip_exact_p",
        lambda diffs: p_between if list(diffs) == target else real(diffs),
    )
    out = run_captured(lambda: paired_analysis.main(reversed_tree))
    standing = out.split("Standing question", 1)[1]
    line = next(ln for ln in standing.splitlines() if ln.split()[:1] == [MODELS[0]])
    assert f"{p_between:.2e}" in line, line
    assert "SEPARATES (Holm, PRIMARY)" in line, line
    assert "uncorrected" not in line, line


# Exact ties retain a distinct direction label.


def test_exact_ties_are_labelled_tied_not_extens_higher(collapse_tree: Path) -> None:
    """A byte-identical pair of arms must be labelled tied, not awarded to either side."""
    out = run_captured(lambda: extens_vs_noise.main(collapse_tree))
    tied_rows = [ln for ln in out.splitlines() if TIED_MODEL in ln]
    assert tied_rows, out[:2000]
    assert not any("HIGHER" in ln for ln in tied_rows), tied_rows
    assert any("tied" in ln.lower() for ln in tied_rows), tied_rows
    # The bucket counter must agree with the RAW DIRECTION block's tally.
    raw = out.split("RAW DIRECTION", 1)[1]
    assert re.search(r"\b1 exactly tied", raw), raw[:400]


def test_collapsed_lane_buckets_as_collapse(collapse_tree: Path) -> None:
    """A lane whose noise arm is broken must carry a `COLLAPSED` annotation, so it is never read as information."""
    out = run_captured(lambda: extens_vs_noise.main(collapse_tree))
    # The per-model table only: detail rows take their mechanism from the bucket heading.
    table = out.split("mechanism / non-compliance", 1)[1].split(f"\nH{N_PRIMARY} =", 1)[
        0
    ]
    rows = {
        ln.split()[0]: ln
        for ln in table.splitlines()
        if ln[:1].isalpha() and len(ln.split()) > 3
    }
    assert COLLAPSE_MODEL in rows, table[:2500]
    assert "noise COLLAPSED" in rows[COLLAPSE_MODEL], rows[COLLAPSE_MODEL]
    # SKEW_MODEL's noise lane stops at _SKEW_SPLIT seeds; the header must show the range, not the minimum.
    assert f"over {_SKEW_SPLIT}-{DEEP_DEPTH} replicates per lane" in out


def test_mechanism_annotates_collapse_without_asserting_direction() -> None:
    """Every collapse pattern gets its own label and none encodes a direction."""
    thr = paired_analysis.COLLAPSE_THRESHOLD
    assert extens_vs_noise.mechanism(0.0, 0.0) == "information"
    assert extens_vs_noise.mechanism(0.0, thr) == "noise COLLAPSED"
    assert extens_vs_noise.mechanism(thr, 0.0) == "extens COLLAPSED"
    assert extens_vs_noise.mechanism(thr, thr) == "both COLLAPSED"
    assert set(extens_vs_noise.Mechanism) == {
        extens_vs_noise.mechanism(e, n) for e in (0.0, thr) for n in (0.0, thr)
    }
    # Direction comes from accuracies alone.
    assert extens_vs_noise.direction(0.2, 0.8) == "noise HIGHER"


def test_extens_vs_noise_rates_use_the_aligned_seed_population(
    collapse_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-compliance outside the seeds the noise arm covers must not colour the contrast."""
    # Whole-cell view: every seed the noise arm lacks is fully non-compliant.
    skewed = _skew_census(
        {
            (SKEW_MODEL, "extens"): dict.fromkeys(
                range(_SKEW_SPLIT, DEEP_DEPTH), N_HARMONICS
            )
        },
    )
    monkeypatch.setattr(extens_vs_noise, "compliance_census", skewed)
    out = run_captured(lambda: extens_vs_noise.main(collapse_tree))
    skew_lines = [ln for ln in out.splitlines() if SKEW_MODEL in ln]
    assert skew_lines, out[:2000]
    rates = [
        int(match.group(1))
        for ln in skew_lines
        if (match := re.search(r"nc 0%/(\d+)%", ln))
    ]
    assert rates and 30 <= rates[0] <= 70, skew_lines
    assert all("extens COLLAPSED" not in ln for ln in skew_lines), skew_lines
    assert any("noise COLLAPSED" in ln for ln in skew_lines), skew_lines


def test_collapse_tags_use_the_compared_seeds(
    collapse_tree: Path, skewed_report: SkewedReport
) -> None:
    """Collapse tags use only seeds shared by the compared contrast arms."""
    label = f"[{SKEW_MODEL}] noise_intens vs zero"
    compared, uncompared = range(_SKEW_SPLIT), range(_SKEW_SPLIT, DEEP_DEPTH)
    for noise_census, tagged in (
        # Fully non-compliant only outside the compared seeds: no tag.
        (
            {**dict.fromkeys(compared, 0), **dict.fromkeys(uncompared, N_HARMONICS)},
            False,
        ),
        # Fully non-compliant on the compared seeds: tagged.
        (dict.fromkeys(compared, N_HARMONICS), True),
    ):
        out, _ = skewed_report(
            collapse_tree, {(SKEW_MODEL, "noise_intens"): noise_census}
        )
        lines = [line for line in out.splitlines() if label in line]
        assert lines, out[:3000]
        assert any("[COLLAPSE:" in line for line in lines) is tagged, lines
