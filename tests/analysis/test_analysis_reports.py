"""Behavioral pins for induction analysis reports.

Synthetic trees keep reported claims conditional on their supporting data.
"""

import re
import shutil
from collections import Counter
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType

import pytest

from smolbench.evals import Marks

# Pytest discovers imported fixtures from module globals.
# pylint: disable=unused-import  # fixture names register pytest fixtures
from tests.analysis._trees import (  # noqa: F401
    DEEP_DEPTH,
    FAMILIES,
    INFOS,
    MODELS,
    N_HARMONICS,
    SHALLOW_DEPTH,
    build_tree,
    extens_vs_noise,
    paired_analysis,
    power_analysis,
    profile_for,
    run_captured,
    significance_report,
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
#: Model whose collapse annotation is not caused by padding.
PAD_MODEL = "ds_flash"

_SKEW_SPLIT = 10


def _skew_census(
    module: ModuleType,
    per_seed: Mapping[tuple[str, str], dict[int, tuple[int, int]]],
) -> Callable[[dict], dict]:
    """Wrap the census so selected per-seed counts are overwritten."""
    real = module.compliance_census

    def skewed(marks: object) -> dict:
        census = real(marks)
        for key, replacements in per_seed.items():
            cell = census[key]
            cell["per_seed"].update(replacements)
            nc = sum(n for n, _t in cell["per_seed"].values())
            cell["rate"] = nc / sum(t for _n, t in cell["per_seed"].values())
        return census

    return skewed


def test_collapse_note_uses_the_supplied_rate(significance_report: ModuleType) -> None:
    """Collapse annotations use the compared-seed rate, not the whole-cell rate."""
    key = ("model", "noise_intens")
    census = {key: {"modes": Counter({"empty": 3})}}
    assert significance_report.collapse_note(key, 0.1, census) == ""
    assert significance_report.collapse_note(key, 0.3, census).startswith(
        "model/noise_intens 30.0% non-compliant"
    )


def test_gate_note_handles_no_data_and_numeric_gates(
    significance_report: ModuleType,
) -> None:
    """Ungated ladder findings render both available and unavailable gate p-values."""
    row = {"kind_is_ladder": True, "gated": False, "family": "family"}
    assert (
        significance_report.gate_note(row, {"family": {"p": None}})
        == "  [EXPLORATORY: family omnibus has no common-seed data]"
    )
    assert (
        significance_report.gate_note(row, {"family": {"p": 0.001234}})
        == "  [EXPLORATORY: family omnibus p=1.23e-03]"
    )
    assert (
        significance_report.gate_note({**row, "gated": True}, {"family": {"p": None}})
        == ""
    )


@pytest.mark.parametrize(
    ("rate_i", "rate_n", "expected"),
    ((0.30, 0.60, False), (0.10, 0.25, True), (0.10, 0.20, False)),
)
def test_pad_crossing(
    significance_report: ModuleType, rate_i: float, rate_n: float, expected: bool
) -> None:
    """Only a threshold crossing is attributed to padding."""
    assert significance_report.pad_crossing(rate_i, rate_n) is expected


def test_classify_rejects_a_zero_first_pair(significance_report: ModuleType) -> None:
    """A zero arm in `key_a` would invert the arm-vs-floor reading; refuse it."""
    with pytest.raises(RuntimeError, match="zero arm must be key_b"):
        significance_report.classify(("m", "zero"), ("m", "intens"))


_STEEP_RUNGS = next(iter(FAMILIES.values()))
ladder_tree = tree_fixture(
    "ladder_tree",
    profile_for(
        {
            (rung, info): (rate, 0.0, "empty", range(DEEP_DEPTH))
            for rung, rate in zip(_STEEP_RUNGS, (0.20, 0.50, 0.90))
            for info in INFOS
            if info != "zero"
        }
    ),
    "16 seeds; the first family's rungs rise steeply (0.2/0.5/0.9).",
)


@pytest.fixture(scope="session")
def gated_steep_family(power_analysis: ModuleType) -> str:
    """The family `ladder_tree` makes steep."""
    return next(iter(power_analysis.FAMILIES))


def test_omnibus_gates_reject_on_a_steep_ladder(
    ladder_tree: Path,
    gated_steep_family: str,
    significance_report: ModuleType,
    power_analysis: ModuleType,
) -> None:
    """A clearly rising family trips its Tier-1 gate."""
    marks = significance_report.load_marks(ladder_tree)
    gates = significance_report.omnibus_gates(marks)
    gate = gates[gated_steep_family]
    assert gate["n_seeds"] == DEEP_DEPTH
    assert gate["reject"]
    assert gate["p"] < power_analysis.ALPHA_OMNIBUS


def test_omnibus_gates_do_not_reject_flat_family(
    clean_tree: Path, significance_report: ModuleType
) -> None:
    """Equal rung rates leave every gate unrejected."""
    marks = significance_report.load_marks(clean_tree)
    gates = significance_report.omnibus_gates(marks)
    assert gates
    for gate in gates.values():
        assert gate["p"] > 0.05
        assert not gate["reject"]


def test_omnibus_gate_uses_only_common_seeds(
    tmp_path: Path, power_analysis: ModuleType, significance_report: ModuleType
) -> None:
    """A cell missing seeds shrinks the gate's seed set to the intersection."""
    family, rungs = next(iter(power_analysis.FAMILIES.items()))
    narrow = (rungs[0], "intens")

    build_tree(tmp_path, profile_for({narrow: (0.90, 0.0, "empty", range(10))}))
    marks = significance_report.load_marks(tmp_path)
    gates = significance_report.omnibus_gates(marks)
    assert gates[family]["n_seeds"] == 10
    for other, gate in gates.items():
        if other != family:
            assert gate["n_seeds"] == DEEP_DEPTH


def test_ungated_ladder_findings_are_labelled_exploratory(
    ladder_tree: Path,
    gated_steep_family: str,
    significance_report: ModuleType,
    report: Callable[[Path], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A significant ladder contrast in a non-rejecting family is marked EXPLORATORY."""
    computed = significance_report.compute(ladder_tree)
    assert computed.gates[gated_steep_family]["reject"]
    gated_ladders = [r for r in computed.findings if r["kind_is_ladder"] and r["gated"]]
    assert gated_ladders, "ladder_tree should yield gated ladder findings"
    out = report(ladder_tree)
    assert "[EXPLORATORY:" not in out

    monkeypatch.setattr(
        significance_report,
        "omnibus_gates",
        lambda _marks: {
            family: {"n_seeds": DEEP_DEPTH, "stat": 0.0, "p": 0.5, "reject": False}
            for family in significance_report.FAMILIES
        },
    )
    ungated = significance_report.compute(ladder_tree)
    assert ungated.n_ladder_ungated == len(gated_ladders)
    out = report(ladder_tree)
    assert "[EXPLORATORY:" in out
    assert "EXPLORATORY, not confirmed scaling effects" in out


def test_missing_family_cell_yields_no_data_gate(
    clean_tree: Path,
    gated_steep_family: str,
    significance_report: ModuleType,
    report: Callable[[Path], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An absent cell reports the no-data gate entry, and render prints it."""
    marks = significance_report.load_marks(clean_tree)
    rungs = significance_report.FAMILIES[gated_steep_family]
    del marks.correct[(rungs[0], "intens")]
    gates = significance_report.omnibus_gates(marks)
    assert gates[gated_steep_family] == {
        "n_seeds": 0,
        "stat": None,
        "p": None,
        "reject": False,
    }

    # load_marks cannot produce a missing cell, so render is checked against a
    # patched gate entry on a complete (flat) tree -- flat families add no
    # findings, so no ungated row ever formats the missing p.
    real = significance_report.omnibus_gates

    def fake(marks: object) -> dict:
        gates = real(marks)
        gates[gated_steep_family] = {
            "n_seeds": 0,
            "stat": None,
            "p": None,
            "reject": False,
        }
        return gates

    monkeypatch.setattr(significance_report, "omnibus_gates", fake)
    out = report(clean_tree)
    assert f"{gated_steep_family:12s} n_seeds=  0 stat=     n/a" in out
    assert "no data" in out


@pytest.fixture
def no_data_gate_tree(tmp_path: Path, power_analysis: ModuleType) -> Path:
    """Pairwise ladder overlaps remain while the family-wide intersection is empty."""
    rungs = next(iter(FAMILIES.values()))
    n_rep = power_analysis.N_REPLICATES
    r2_seeds = {
        "intens": tuple(range(20)),
        "extens": tuple(range(10, 30)),
        "noise_intens": tuple(range(10)) + tuple(range(20, 30)),
        "zero": tuple(range(5)) + tuple(range(15, 30)),
    }
    overrides = {
        (rung, info): (rate, 0.0, "empty", seeds)
        for info in INFOS
        for rung, rate, seeds in (
            (rungs[0], 0.0, range(n_rep)),
            (rungs[1], 1.0, range(n_rep)),
            (rungs[2], 0.9, r2_seeds[info]),
        )
    }
    build_tree(tmp_path, profile_for(overrides, depth=n_rep))
    return tmp_path


def test_no_data_gate_renders_exploratory(
    no_data_gate_tree: Path,
    power_analysis: ModuleType,
    significance_report: ModuleType,
) -> None:
    """An ungated significant ladder finding renders a no-data explanation."""
    family = next(iter(power_analysis.FAMILIES))
    computed = significance_report.compute(no_data_gate_tree)
    ungated = [
        row
        for row in computed.findings
        if row["kind_is_ladder"] and row["family"] == family and not row["gated"]
    ]
    assert ungated
    assert computed.gates[family]["p"] is None
    out = run_captured(lambda: significance_report.render(computed))
    assert "omnibus has no common-seed data" in out


_DEEP = range(DEEP_DEPTH)
_LOW, _HIGH = (0.10, 0.0, "empty", _DEEP), (0.90, 0.0, "empty", _DEEP)

shallow_tree = tree_fixture(
    "shallow_tree",
    profile_for(depth=SHALLOW_DEPTH),
    "6 seeds everywhere: below the sign-flip resolution floor.",
)
collapse_tree = tree_fixture(
    "collapse_tree",
    profile_for(
        {
            (COLLAPSE_MODEL, "noise_intens"): (0.10, 0.90, "empty", _DEEP),
            (WEAK_MODEL, "intens"): _LOW,
            # Non-compliance is outside noise's seed coverage.
            (SKEW_MODEL, "intens"): (
                0.90,
                lambda seed: 0.90 if seed >= _SKEW_SPLIT else 0.0,
                "empty",
                _DEEP,
            ),
            (SKEW_MODEL, "noise_intens"): (0.90, 0.50, "empty", range(_SKEW_SPLIT)),
        }
    ),
    "16 seeds, with the four engineered anomalies this module's constants name.",
    copies={(TIED_MODEL, "noise_intens"): (TIED_MODEL, "extens")},
)
_CLEAN_SOURCE = (MODELS[0], "intens")
clean_tree = tree_fixture(
    "clean_tree",
    profile_for(rate=0.99),
    "16 seeds, every informative arm at 0.99 and compliant: all ties, no collapse.",
    copies={
        (model, info): _CLEAN_SOURCE
        for model in MODELS
        for info in INFOS
        if info != "zero" and (model, info) != _CLEAN_SOURCE
    },
)
reversed_tree = tree_fixture(
    "reversed_tree",
    profile_for({(PAD_MODEL, "intens"): _LOW, (PAD_MODEL, "zero"): _HIGH}),
    "Build a tree with one significant informative arm below its floor.",
)
ceiling_tree = tree_fixture(
    "ceiling_tree",
    profile_for(rate=0.97),
    "Build a tree with ceiling pairs that include discordances.",
)
caveat_tree = tree_fixture(
    "caveat_tree",
    profile_for({(PAD_MODEL, "intens"): (0.50, 0.50, "empty", _DEEP)}),
    "Build a tree with collapse findings but no padding crossing.",
)
padding_control_tree = tree_fixture(
    "padding_control_tree",
    profile_for(
        {(PAD_MODEL, info): _LOW for info in ("intens", "noise_intens", "zero")}
    ),
    "Build a copied noise control whose compliance can be skewed independently.",
    copies={
        (PAD_MODEL, info): (PAD_MODEL, "zero") for info in ("intens", "noise_intens")
    },
)
shared_seed_noise_tree = tree_fixture(
    "shared_seed_noise_tree",
    profile_for({(SKEW_MODEL, "intens"): (0.90, 0.0, "empty", range(_SKEW_SPLIT))}),
    "Build a lane with clean extra noise seeds absent from intens.",
)


@pytest.fixture
def report(
    significance_report: ModuleType,
) -> Callable[[Path], str]:
    """Return captured report output for an explicit result directory."""

    def _report(root: Path) -> str:
        return run_captured(lambda: significance_report.main(root))

    return _report


# The shallow fixture pins the incomplete-sync guard and control messaging.


def test_shallow_sync_prints_an_incomplete_banner_and_no_exoneration(
    report: Callable[[Path], str],
    shallow_tree: Path,
    significance_report: ModuleType,
) -> None:
    """At 6 seeds nothing is rejectable, so the report must say `INCOMPLETE SYNC` and suppress the padding exoneration."""
    out = report(shallow_tree)
    computed = significance_report.compute(shallow_tree)
    assert computed.floor_bound
    assert computed.depth_min == SHALLOW_DEPTH
    assert "INCOMPLETE SYNC" in out
    # The blanket exoneration must NOT print under a floor-bound family.
    assert "whitespace padding drove" not in out
    # Include threshold arithmetic so the banner is auditable.
    banner = out.split("INCOMPLETE SYNC", 1)[1][:800]
    assert f"2/2**{computed.depth_max}" in banner
    assert f"ALPHA/m = {significance_report.ALPHA} / {computed.m}" in banner


def test_failing_controls_are_exonerated_only_where_the_pad_explains_them(
    report: Callable[[Path], str],
    collapse_tree: Path,
    significance_report: ModuleType,
) -> None:
    """Collapsed noise controls are split from compliant failures."""
    out = report(collapse_tree)
    computed = significance_report.compute(collapse_tree)
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
    explained, _, unexplained = controls.partition("NOT explained by padding")
    # The partial-collapse caveat sits above the split ...
    assert "caveat, not a demonstrated cause of the failed control" in explained
    # ... and the compliant, non-noise failure is named below it.
    assert any(WEAK_MODEL in row["label"] for row in computed.fails_unexplained)


def _padding_control_report(
    report: Callable[[Path], str],
    significance_report: ModuleType,
    padding_control_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
    noise_counts: tuple[int, int],
) -> str:
    """Return a report with matched-seed intens/noise compliance rates overridden."""
    monkeypatch.setattr(
        significance_report,
        "compliance_census",
        _skew_census(
            significance_report,
            {
                (PAD_MODEL, "intens"): dict.fromkeys(
                    range(DEEP_DEPTH), (0, N_HARMONICS)
                ),
                (PAD_MODEL, "noise_intens"): dict.fromkeys(
                    range(DEEP_DEPTH), noise_counts
                ),
            },
        ),
    )
    return report(padding_control_tree)


def test_partial_pad_crossing_is_not_called_near_total(
    report: Callable[[Path], str],
    significance_report: ModuleType,
    padding_control_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A partial compliance collapse is reported as a caveat, not control causation."""
    out = _padding_control_report(
        report,
        significance_report,
        padding_control_tree,
        monkeypatch,
        (4, N_HARMONICS),
    )
    computed = significance_report.compute(padding_control_tree)
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    assert computed.fails_partial
    assert not computed.fails_total
    assert f"{computed.partial_compliance} compliant on the compared seeds" in controls
    assert "near-total non-compliance" not in controls
    assert "55.6% compliant on the compared seeds" in controls
    assert "caveat, not a demonstrated cause of the failed control" in controls


def test_total_pad_crossing_keeps_near_total_exoneration(
    report: Callable[[Path], str],
    significance_report: ModuleType,
    padding_control_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A total compliance collapse retains the padding exoneration."""
    out = _padding_control_report(
        report,
        significance_report,
        padding_control_tree,
        monkeypatch,
        (N_HARMONICS, N_HARMONICS),
    )
    computed = significance_report.compute(padding_control_tree)
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    assert computed.fails_total
    assert "near-total non-compliance" in controls


def test_reversed_controls_are_not_counted_as_passing(
    report: Callable[[Path], str],
    reversed_tree: Path,
    significance_report: ModuleType,
) -> None:
    """A significant control below its floor is reported as reversed, not ahead."""
    out = report(reversed_tree)
    computed = significance_report.compute(reversed_tree)
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    reversed_lines = [
        line for line in controls.splitlines() if line.startswith("  REVERSED")
    ]
    assert any(
        f"[{PAD_MODEL}] intens vs zero" in line for line in reversed_lines
    ), reversed_lines
    assert (
        f"{len(computed.passing)} significant with the informative arm AHEAD"
        in controls
    )
    assert f"{len(computed.reversed_)} significant" in controls
    assert f"{len(computed.fails)} not rejected" in controls
    assert computed.n_floor == len(computed.passing) + len(computed.reversed_) + len(
        computed.fails
    )
    assert "scores no better" not in controls


def test_replicate_depth_gate_uses_the_shallowest_lane(
    paired_analysis: ModuleType,
    tmp_path_factory: pytest.TempPathFactory,
    power_analysis: ModuleType,
) -> None:
    """The shallowest lane controls the depth warning."""
    deep_cell = (power_analysis.MODELS[0], "intens")
    root = tmp_path_factory.mktemp("mixed_depth")

    deep = (0.90, 0.0, "empty", range(power_analysis.N_REPLICATES))
    build_tree(root, profile_for({deep_cell: deep}, depth=SHALLOW_DEPTH))
    out = run_captured(lambda: paired_analysis.main(root))
    assert "WARNING" in out
    assert str(SHALLOW_DEPTH) in out


def test_extra_replicate_seed_is_rejected(
    shallow_tree: Path,
    power_analysis: ModuleType,
    paired_analysis: ModuleType,
    tmp_path: Path,
) -> None:
    """A lane outside the registered seed range is a collection failure."""
    root = tmp_path / "extra-seed"
    shutil.copytree(shallow_tree, root)
    cell = (power_analysis.MODELS[0], power_analysis.INFOS[0])
    source = root / f"{cell[0]}_{cell[1]}" / "rep_0.yaml"
    source.rename(source.with_name("rep_30.yaml"))
    with pytest.raises(SystemExit, match="30"):
        paired_analysis.load_marks(root)


def test_partial_replicate_is_rejected(
    shallow_tree: Path,
    power_analysis: ModuleType,
    paired_analysis: ModuleType,
    tmp_path: Path,
) -> None:
    """A replicate with too few marks is a collection failure."""
    root = tmp_path / "partial-replicate"
    shutil.copytree(shallow_tree, root)
    cell = (power_analysis.MODELS[0], power_analysis.INFOS[0])
    path = root / f"{cell[0]}_{cell[1]}" / "rep_0.yaml"
    marks = Marks.load(path)
    Marks(
        model=marks.model,
        marks=marks.marks[:-1],
        date=marks.date,
        server_config=marks.server_config,
        regraded_from=marks.regraded_from,
    ).dump(path)
    with pytest.raises(
        SystemExit,
        match=rf"{path}.*{power_analysis.N_HARMONICS}",
    ):
        paired_analysis.load_marks(root)


# ===========================================================================
# the padding table subtracted rates over different seed sets
# ===========================================================================


def _padding_table(out: str) -> "dict[str, str]":
    """Parse the PADDING EFFECT table into ``{lane: row text}``."""
    block = out.split("PADDING EFFECT", 1)[1].split("=> The pad", 1)[0]
    rows = {}
    for line in block.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[1].endswith("%"):
            rows[parts[0]] = line
    return rows


def test_padding_table_subtracts_over_the_common_seeds_only(
    report: Callable[[Path], str],
    collapse_tree: Path,
    significance_report: ModuleType,
) -> None:
    """The delta is a within-lane difference, so both rates must be computed over the same seeds."""
    out = report(collapse_tree)
    computed = significance_report.compute(collapse_tree)
    rows = _padding_table(out)
    assert SKEW_MODEL in rows, rows
    row = rows[SKEW_MODEL]
    assert "COLLAPSE" in row and "not padding-specific" not in row, row
    skew = next(r for r in computed.pad_rows if r["model"] == SKEW_MODEL)
    assert skew["rate_i"] == 0
    assert "0.0%" in row


def test_padding_table_reports_the_seed_count_it_used(
    report: Callable[[Path], str],
    collapse_tree: Path,
    significance_report: ModuleType,
) -> None:
    """Every row carries the n it was computed over, so a 10-seed comparison isn't mistaken for a 16-seed one."""
    out = report(collapse_tree)
    computed = significance_report.compute(collapse_tree)
    header = [ln for ln in out.splitlines() if "delta" in ln and "noise" in ln]
    assert header, out[:2000]
    assert re.search(r"\bn\b", header[0]), header[0]
    rows = _padding_table(out)
    n_common = {r["model"]: r["n_common"] for r in computed.pad_rows}
    assert n_common[SKEW_MODEL] == _SKEW_SPLIT
    assert n_common[COLLAPSE_MODEL] == DEEP_DEPTH


def test_padding_table_counts_come_from_the_rows_it_actually_built(
    report: Callable[[Path], str],
    collapse_tree: Path,
    power_analysis: ModuleType,
    significance_report: ModuleType,
) -> None:
    """Every count in the section comes from the table's own row count, not a hard-coded lane total."""
    out = report(collapse_tree)
    computed = significance_report.compute(collapse_tree)
    assert f"all {len(power_analysis.MODELS)} lanes" not in out
    assert len(computed.pad_rows) == len(power_analysis.MODELS)
    assert len(computed.pad_lanes) == sum(
        row["verdict"] == "COLLAPSE" for row in computed.pad_rows
    )
    assert (
        f"=> The pad itself pushes {len(computed.pad_lanes)} of "
        f"{len(computed.pad_rows)} lanes"
    ) in out


def test_padding_intro_numerator_comes_from_the_common_seed_table(
    report: Callable[[Path], str],
    collapse_tree: Path,
    significance_report: ModuleType,
) -> None:
    """`In X of Y lanes` counts table rows whose common-seed noise rate crosses the criterion."""
    out = report(collapse_tree)
    computed = significance_report.compute(collapse_tree)
    n_over = sum(
        row["rate_n"] >= significance_report.COLLAPSE_THRESHOLD
        for row in computed.pad_rows
    )
    assert (
        f"In {n_over} of {len(computed.pad_rows)} lanes with both arms measured" in out
    )


def test_all_cells_noise_count_uses_whole_cell_rates(
    report: Callable[[Path], str],
    significance_report: ModuleType,
    shared_seed_noise_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The all-cells census count must not reuse common-seed padding rates."""
    monkeypatch.setattr(
        significance_report,
        "compliance_census",
        _skew_census(
            significance_report,
            {
                (SKEW_MODEL, "intens"): dict.fromkeys(
                    range(_SKEW_SPLIT), (0, N_HARMONICS)
                ),
                (SKEW_MODEL, "noise_intens"): dict.fromkeys(
                    range(3), (N_HARMONICS, N_HARMONICS)
                ),
            },
        ),
    )
    out = report(shared_seed_noise_tree)
    computed = significance_report.compute(shared_seed_noise_tree)
    assert computed.n_noise_over_cells == 0
    assert computed.n_noise_over_lanes == 1
    assert "0 of" in out
    assert f"In 1 of {len(computed.pad_rows)} lanes with both arms measured" in out


def test_zero_vs_zero_controls_report_the_measured_count_only(
    report: Callable[[Path], str],
    collapse_tree: Path,
    shallow_tree: Path,
    significance_report: ModuleType,
) -> None:
    """The report neither asserts nor assumes a zero rejection count for cross-model floors."""
    for tree in (collapse_tree, shallow_tree):
        out = report(tree)
        computed = significance_report.compute(tree)
        assert "by construction" not in out, out
        assert computed.zero_vs_zero
        assert computed.n_zero_significant == sum(
            computed.hp[i] for i in computed.zero_vs_zero
        )
        assert f"{len(computed.zero_vs_zero)} zero-vs-zero ladder contrasts" in out
        assert f"{computed.n_zero_significant} significant" in out


# Each narrative conclusion is gated by its own computed count.


def test_the_ladder_claim_is_conditional_on_its_own_count(
    report: Callable[[Path], str],
    shallow_tree: Path,
    collapse_tree: Path,
    significance_report: ModuleType,
) -> None:
    """The family-scaling claim needs `n_lad > 0`; with none, only the info-arm story may print."""
    # The one-sided claim that must never print again, whatever n_lad is.
    one_sided = "bites the family-scaling story, not the info-arm story"

    # Floor-bound: Holm rejects nothing, so no story claim is earned.
    shallow = report(shallow_tree)
    assert one_sided not in shallow
    assert "bites the family-scaling story" not in shallow

    # Not floor-bound: the claim must track the count printed beside it.
    collapse = report(collapse_tree)
    computed = significance_report.compute(collapse_tree)
    assert computed.lost, "fixture no longer produces any Holm losses"
    assert (
        f"{computed.n_lost_ladder} of the {len(computed.lost)} losses are LADDER contrasts"
        in collapse
    )
    if computed.n_lost_ladder:
        assert "bites the family-scaling story" in collapse
    else:
        # The zero branch must name the side the data shows, not just avoid the phrase.
        assert one_sided not in collapse, collapse
        assert "info-arm story" in collapse


def test_the_two_mechanism_claim_is_conditional_on_a_flagged_finding(
    report: Callable[[Path], str],
    shallow_tree: Path,
    clean_tree: Path,
    collapse_tree: Path,
) -> None:
    """`TWO-MECHANISM` needs a significant finding that actually touches a collapse; zero findings or zero collapses must not earn it."""
    assert "TWO-MECHANISM" not in report(shallow_tree)
    assert "TWO-MECHANISM" not in report(clean_tree)
    assert "TWO-MECHANISM" in report(collapse_tree)


def test_two_mechanism_needs_a_pad_crossing_extens_vs_noise_finding(
    report: Callable[[Path], str],
    caveat_tree: Path,
    significance_report: ModuleType,
) -> None:
    """A collapse annotation without a pad crossing cannot support two mechanisms."""
    out = report(caveat_tree)
    computed = significance_report.compute(caveat_tree)
    assert computed.n_flag > 0
    assert (
        f"[COLLAPSE] {computed.n_flag} of {len(computed.findings)} findings touch"
        in out
    )
    assert "TWO-MECHANISM" not in out
    assert "no evidence for a second" in out


def test_the_ceiling_claim_is_conditional_and_counts_its_discordances(
    report: Callable[[Path], str],
    collapse_tree: Path,
    clean_tree: Path,
    power_analysis: ModuleType,
    significance_report: ModuleType,
) -> None:
    """`CEILING pairs` needs at least one ceiling pair, and its zero-discordant count must be measured, not asserted as "many"."""
    collapse = report(collapse_tree)
    assert "ties by\n  construction" not in collapse
    assert "ties by construction" not in collapse

    clean = report(clean_tree)
    computed = significance_report.compute(clean_tree)
    ceiling_line = [ln for ln in clean.splitlines() if "CEILING pairs" in ln]
    assert ceiling_line, clean[-2000:]
    assert len(computed.ceiling) == power_analysis.N_INFO_CONTRASTS
    assert f"CEILING pairs (both arms >= 0.95): {len(computed.ceiling)}" in clean
    assert f"{computed.n_zero_discordant} of them have ZERO discordant items" in clean


def test_ceiling_non_rejections_are_split_into_ties_and_unresolved(
    report: Callable[[Path], str],
    ceiling_tree: Path,
    clean_tree: Path,
    significance_report: ModuleType,
) -> None:
    """Ceiling non-rejections distinguish exact ties from unresolved pairs."""
    out = report(ceiling_tree)
    computed = significance_report.compute(ceiling_tree)
    assert computed.ceiling
    assert f"{computed.n_zero_discordant} of them have ZERO discordant items" in out
    assert "UNRESOLVED" in out
    assert "ties by construction" not in out
    assert computed.n_zero_discordant < len(computed.ceiling)

    clean = report(clean_tree)
    clean_computed = significance_report.compute(clean_tree)
    assert clean_computed.n_zero_discordant == len(clean_computed.ceiling)
    assert (
        f"{clean_computed.n_zero_discordant} of them have ZERO discordant items"
        in clean
    )


# Exact ties retain a distinct direction label.


def test_exact_ties_are_labelled_tied_not_extens_higher(
    extens_vs_noise: ModuleType, collapse_tree: Path
) -> None:
    """A byte-identical pair of arms must be labelled tied, not awarded to either side."""
    out = run_captured(lambda: extens_vs_noise.main(collapse_tree))
    tied_rows = [ln for ln in out.splitlines() if TIED_MODEL in ln]
    assert tied_rows, out[:2000]
    for line in tied_rows:
        assert "extens HIGHER" not in line, line
        assert "noise HIGHER" not in line, line
    assert any("tied" in ln.lower() or "TIED" in ln for ln in tied_rows), tied_rows
    # The bucket counter must agree with the RAW DIRECTION block's tally.
    raw = out.split("RAW DIRECTION", 1)[1]
    assert re.search(r"\b1 exactly tied", raw), raw[:400]


def test_collapsed_lane_buckets_as_collapse(
    extens_vs_noise: ModuleType, power_analysis: ModuleType, collapse_tree: Path
) -> None:
    """A lane whose noise arm is broken must carry a `COLLAPSED` annotation, so it is never read as information."""
    out = run_captured(lambda: extens_vs_noise.main(collapse_tree))
    # The per-model table only: detail rows take their mechanism from the bucket heading.
    table = out.split("mechanism / non-compliance", 1)[1].split(
        f"\nH{power_analysis.N_PRIMARY} =", 1
    )[0]
    rows = {
        ln.split()[0]: ln
        for ln in table.splitlines()
        if ln[:1].isalpha() and len(ln.split()) > 3
    }
    assert COLLAPSE_MODEL in rows, table[:2500]
    assert "noise COLLAPSED" in rows[COLLAPSE_MODEL], rows[COLLAPSE_MODEL]
    # Annotation only: nothing in the report claims the direction is forced.
    assert "forced" not in out.lower(), out


def test_mechanism_annotates_collapse_without_asserting_direction(
    extens_vs_noise: ModuleType,
) -> None:
    """Every collapse pattern gets its own label and none encodes a direction."""
    thr = extens_vs_noise.COLLAPSE_THRESHOLD
    assert extens_vs_noise.mechanism(0.0, 0.0) == "information"
    assert extens_vs_noise.mechanism(0.0, thr) == "noise COLLAPSED"
    assert extens_vs_noise.mechanism(thr, 0.0) == "extens COLLAPSED"
    assert extens_vs_noise.mechanism(thr, thr) == "both COLLAPSED"
    assert set(extens_vs_noise.MECHANISMS) == {
        extens_vs_noise.mechanism(e, n) for e in (0.0, thr) for n in (0.0, thr)
    }
    # Direction comes from accuracies alone.
    assert extens_vs_noise.direction(0.2, 0.8) == "noise HIGHER"


def test_extens_vs_noise_rates_use_the_aligned_seed_population(
    extens_vs_noise: ModuleType,
    collapse_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-compliance outside the seeds the noise arm covers must not colour the contrast."""
    # Whole-cell view: every seed the noise arm lacks is fully non-compliant.
    skewed = _skew_census(
        extens_vs_noise,
        {
            (SKEW_MODEL, "extens"): dict.fromkeys(
                range(_SKEW_SPLIT, DEEP_DEPTH), (N_HARMONICS, N_HARMONICS)
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
    report: Callable[[Path], str],
    collapse_tree: Path,
    significance_report: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Collapse tags use only seeds shared by the compared contrast arms."""
    skewed = _skew_census(
        significance_report,
        {
            (SKEW_MODEL, "noise_intens"): {
                **dict.fromkeys(range(_SKEW_SPLIT), (0, N_HARMONICS)),
                **dict.fromkeys(
                    range(_SKEW_SPLIT, DEEP_DEPTH),
                    (N_HARMONICS, N_HARMONICS),
                ),
            }
        },
    )
    monkeypatch.setattr(significance_report, "compliance_census", skewed)
    out = report(collapse_tree)
    label = f"[{SKEW_MODEL}] noise_intens vs zero"
    lines = [line for line in out.splitlines() if label in line]
    assert lines, out[:3000]
    assert all("[COLLAPSE:" not in line for line in lines), lines

    crossing = _skew_census(
        significance_report,
        {
            (SKEW_MODEL, "noise_intens"): dict.fromkeys(
                range(_SKEW_SPLIT), (N_HARMONICS, N_HARMONICS)
            )
        },
    )
    monkeypatch.setattr(significance_report, "compliance_census", crossing)
    out = report(collapse_tree)
    lines = [line for line in out.splitlines() if label in line]
    assert lines, out[:3000]
    assert any("[COLLAPSE:" in line for line in lines), lines
