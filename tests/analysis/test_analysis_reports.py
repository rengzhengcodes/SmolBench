"""Behavioral pins for induction analysis reports.

Synthetic trees keep reported claims conditional on their supporting data.
"""

import contextlib
import io
import re
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

# Pytest discovers imported fixtures from module globals.
# pylint: disable=unused-import  # fixture names register pytest fixtures
from tests.analysis._trees import (  # noqa: F401
    DEEP_DEPTH,
    SHALLOW_DEPTH,
    build_tree,
    extens_vs_noise,
    paired_analysis,
    power_analysis,
    repoint,
    significance_report,
)

#: Collapsed noise arm whose failed control is padding-driven.
COLLAPSE_MODEL = "ds_pro"
#: Compliant failed control that padding cannot exonerate.
WEAK_MODEL = "min3_3b"
#: Mismatched seed coverage makes whole-cell and common-seed deltas differ.
SKEW_MODEL = "exaone_32b"
#: Byte copy creates an exact tie.
TIED_MODEL = "nemo3_30b"
#: Model whose informative arm is deliberately below its empty-context floor.
REVERSED_MODEL = "ds_flash"
#: Model whose collapse annotation is not caused by padding.
CAVEAT_MODEL = "ds_flash"
#: Model whose copied noise control does not reject while compliance is skewed.
PAD_CONTROL_MODEL = "ds_flash"

_SKEW_SPLIT = 10


def _skew_census(
    module: ModuleType, key: tuple[str, str], per_seed: dict[range, tuple[int, int]]
) -> Callable[[dict], dict]:
    """Wrap `module.compliance_census` so `key`'s per-seed counts are overwritten."""
    real = module.compliance_census

    def skewed(compliance: dict) -> dict:
        census = real(compliance)
        cell = census[key]
        for seeds, counts in per_seed.items():
            for seed in seeds:
                cell["per_seed"][seed] = counts
        nc = sum(n for n, _t in cell["per_seed"].values())
        cell["rate"] = nc / sum(t for _n, t in cell["per_seed"].values())
        return census

    return skewed


def _run(fn: Callable[[], None]) -> str:
    """Call `fn`, returning everything it wrote to stdout and stderr."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        fn()
    return buf.getvalue()


def test_collapse_note_uses_the_supplied_rate(significance_report: ModuleType) -> None:
    """Collapse annotations use the compared-seed rate, not the whole-cell rate."""
    key = ("model", "noise_intens")
    census = {key: {"modes": Counter({"empty": 3})}}
    assert significance_report.collapse_note(key, 0.1, census) == ""
    assert significance_report.collapse_note(key, 0.3, census).startswith(
        "model/noise_intens 30.0% non-compliant"
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


def _shallow_profile(model: str, info: str) -> tuple[float, float, str, range]:
    seeds = range(SHALLOW_DEPTH)
    return (0.10 if info == "zero" else 0.90), 0.0, "empty", seeds


def _collapse_profile(
    model: str, info: str
) -> tuple[float, float | Callable[[int], float], str, range]:
    seeds = range(DEEP_DEPTH)
    if model == COLLAPSE_MODEL and info == "noise_intens":
        return 0.10, 0.90, "empty", seeds
    if model == WEAK_MODEL and info == "intens":
        return 0.10, 0.0, "empty", seeds
    if model == SKEW_MODEL and info == "intens":
        # Non-compliance is outside noise's seed coverage.
        return 0.90, (lambda seed: 0.90 if seed >= _SKEW_SPLIT else 0.0), "empty", seeds
    if model == SKEW_MODEL and info == "noise_intens":
        return 0.90, 0.50, "empty", range(_SKEW_SPLIT)
    return (0.10 if info == "zero" else 0.90), 0.0, "empty", seeds


def _clean_profile(model: str, info: str) -> tuple[float, float, str, range]:
    seeds = range(DEEP_DEPTH)
    return (0.10 if info == "zero" else 0.99), 0.0, "empty", seeds


def _reversed_profile(model: str, info: str) -> tuple[float, float, str, range]:
    seeds = range(DEEP_DEPTH)
    if model == REVERSED_MODEL and info == "intens":
        return 0.10, 0.0, "empty", seeds
    if model == REVERSED_MODEL and info == "zero":
        return 0.90, 0.0, "empty", seeds
    return (0.10 if info == "zero" else 0.90), 0.0, "empty", seeds


def _ceiling_profile(model: str, info: str) -> tuple[float, float, str, range]:
    seeds = range(DEEP_DEPTH)
    return (0.10 if info == "zero" else 0.97), 0.0, "empty", seeds


def _caveat_profile(model: str, info: str) -> tuple[float, float, str, range]:
    seeds = range(DEEP_DEPTH)
    if model == CAVEAT_MODEL and info == "intens":
        return 0.50, 0.50, "empty", seeds
    return (0.10 if info == "zero" else 0.90), 0.0, "empty", seeds


def _padding_control_profile(model: str, info: str) -> tuple[float, float, str, range]:
    seeds = range(DEEP_DEPTH)
    if model == PAD_CONTROL_MODEL and info in {"intens", "noise_intens", "zero"}:
        return 0.10, 0.0, "empty", seeds
    return (0.10 if info == "zero" else 0.90), 0.0, "empty", seeds


def _shared_seed_noise_profile(
    model: str, info: str
) -> tuple[float, float, str, range]:
    if model == SKEW_MODEL and info == "intens":
        return 0.90, 0.0, "empty", range(_SKEW_SPLIT)
    if model == SKEW_MODEL and info == "noise_intens":
        return 0.90, 0.0, "empty", range(DEEP_DEPTH)
    return (0.10 if info == "zero" else 0.90), 0.0, "empty", range(DEEP_DEPTH)


@pytest.fixture(scope="session")
def shallow_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> Path:
    """6 seeds everywhere: below the sign-flip resolution floor."""
    root = tmp_path_factory.mktemp("shallow")
    build_tree(root, power_analysis.MODELS, power_analysis.INFOS, _shallow_profile)
    return root


@pytest.fixture(scope="session")
def collapse_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> Path:
    """16 seeds, with the four engineered anomalies this module's constants name."""
    root = tmp_path_factory.mktemp("collapse")
    build_tree(
        root,
        power_analysis.MODELS,
        power_analysis.INFOS,
        _collapse_profile,
        copies={(TIED_MODEL, "noise_intens"): (TIED_MODEL, "extens")},
    )
    return root


@pytest.fixture(scope="session")
def clean_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> Path:
    """16 seeds, every informative arm at 0.99 and compliant: all ties, no collapse."""
    root = tmp_path_factory.mktemp("clean")
    source = (power_analysis.MODELS[0], "intens")
    copies = {
        (model, info): source
        for model in power_analysis.MODELS
        for info in power_analysis.INFOS
        if info != "zero" and (model, info) != source
    }
    build_tree(
        root,
        power_analysis.MODELS,
        power_analysis.INFOS,
        _clean_profile,
        copies=copies,
    )
    return root


@pytest.fixture(scope="session")
def reversed_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> Path:
    """Build a tree with one significant informative arm below its floor."""
    root = tmp_path_factory.mktemp("reversed")
    build_tree(root, power_analysis.MODELS, power_analysis.INFOS, _reversed_profile)
    return root


@pytest.fixture(scope="session")
def ceiling_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> Path:
    """Build a tree with ceiling pairs that include discordances."""
    root = tmp_path_factory.mktemp("ceiling")
    build_tree(root, power_analysis.MODELS, power_analysis.INFOS, _ceiling_profile)
    return root


@pytest.fixture(scope="session")
def caveat_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> Path:
    """Build a tree with collapse findings but no padding crossing."""
    root = tmp_path_factory.mktemp("caveat")
    build_tree(root, power_analysis.MODELS, power_analysis.INFOS, _caveat_profile)
    return root


@pytest.fixture(scope="session")
def padding_control_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> Path:
    """Build a copied noise control whose compliance can be skewed independently."""
    root = tmp_path_factory.mktemp("padding-control")
    source = (PAD_CONTROL_MODEL, "zero")
    build_tree(
        root,
        power_analysis.MODELS,
        power_analysis.INFOS,
        _padding_control_profile,
        copies={
            (PAD_CONTROL_MODEL, info): source for info in ("intens", "noise_intens")
        },
    )
    return root


@pytest.fixture(scope="session")
def shared_seed_noise_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> Path:
    """Build a lane with clean extra noise seeds absent from intens."""
    root = tmp_path_factory.mktemp("shared-seed-noise")
    build_tree(
        root,
        power_analysis.MODELS,
        power_analysis.INFOS,
        _shared_seed_noise_profile,
    )
    return root


@pytest.fixture
def report(
    repoint: Callable[[Path], None], significance_report: ModuleType
) -> Callable[[Path], str]:
    """Return ``root -> significance_report.main()``'s captured output."""

    def _report(root: Path) -> str:
        repoint(root)
        return _run(significance_report.main)

    return _report


# ===========================================================================
# the control-failure message is hard-coded and there is no depth guard
# ===========================================================================


def test_shallow_sync_prints_an_incomplete_banner_and_no_exoneration(
    report: Callable[[Path], str], shallow_tree: Path
) -> None:
    """At 6 seeds nothing is rejectable, so the report must say `INCOMPLETE SYNC` and suppress the padding exoneration."""
    out = report(shallow_tree)
    assert "INCOMPLETE SYNC" in out
    # The blanket exoneration must NOT print under a floor-bound family.
    assert "whitespace padding drove" not in out
    # Include threshold arithmetic so the banner is auditable.
    banner = out.split("INCOMPLETE SYNC", 1)[1][:800]
    assert re.search(r"2\s*/\s*2\W*\W?6|3\.12\d*e-0?2", banner), banner
    assert re.search(r"2\.38\d*e-0?4|0\.05\s*/\s*210", banner), banner


def test_failing_controls_are_exonerated_only_where_the_pad_explains_them(
    report: Callable[[Path], str], collapse_tree: Path
) -> None:
    """Collapsed noise controls are split from compliant failures."""
    out = report(collapse_tree)
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    fails = [ln for ln in controls.splitlines() if ln.strip().startswith("FAILS")]
    # Exoneration requires a collapsed noise arm.
    qualifying = [ln for ln in fails if "noise_intens" in ln and "[COLLAPSE:" in ln]
    assert fails and qualifying and len(qualifying) < len(fails), fails

    match = re.search(r"These (\d+) of (\d+) failures", controls)
    assert match, controls
    total_count, total_denominator = map(int, match.groups())
    partial = re.search(
        r"(\d+) of (\d+) failures are noise arms on a lane the pad carried over",
        controls,
    )
    assert partial, controls
    assert total_denominator == len(fails)
    assert total_count + int(partial.group(1)) == len(qualifying)

    assert "NOT explained by padding" in controls
    explained, _, unexplained = controls.partition("NOT explained by padding")
    # The partial-collapse caveat sits above the split ...
    assert "caveat, not a demonstrated cause of the failed control" in explained
    # ... and the compliant, non-noise failure is named below it.
    assert WEAK_MODEL in unexplained
    assert WEAK_MODEL not in explained.rsplit("These ", 1)[-1]


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
            (PAD_CONTROL_MODEL, "intens"),
            {range(DEEP_DEPTH): (0, 9)},
        ),
    )
    monkeypatch.setattr(
        significance_report,
        "compliance_census",
        _skew_census(
            significance_report,
            (PAD_CONTROL_MODEL, "noise_intens"),
            {range(DEEP_DEPTH): noise_counts},
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
    controls = _padding_control_report(
        report,
        significance_report,
        padding_control_tree,
        monkeypatch,
        (4, 9),
    ).split("ZERO-ARM CONTROLS", 1)[1]
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
    controls = _padding_control_report(
        report,
        significance_report,
        padding_control_tree,
        monkeypatch,
        (9, 9),
    ).split("ZERO-ARM CONTROLS", 1)[1]
    assert "near-total non-compliance" in controls


def test_reversed_controls_are_not_counted_as_passing(
    report: Callable[[Path], str], reversed_tree: Path
) -> None:
    """A significant control below its floor is reported as reversed, not ahead."""
    out = report(reversed_tree)
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    reversed_lines = [
        line for line in controls.splitlines() if line.startswith("  REVERSED")
    ]
    assert any(
        f"[{REVERSED_MODEL}] intens vs zero" in line for line in reversed_lines
    ), reversed_lines
    match = re.search(
        r"(\d+) arm-vs-floor positive controls.*?: (\d+) significant with the "
        r"informative arm AHEAD, (\d+) significant\nbut REVERSED .*?, "
        r"(\d+) not rejected\.",
        controls,
        re.DOTALL,
    )
    assert match, controls
    total, passing, reversed_count, fails = map(int, match.groups())
    assert passing == total - reversed_count - fails
    assert "scores no better" not in controls


def test_replicate_depth_gate_uses_the_shallowest_lane(
    repoint: Callable[[Path], None],
    paired_analysis: ModuleType,
    tmp_path_factory: pytest.TempPathFactory,
    power_analysis: ModuleType,
) -> None:
    """One deep lane must not silence the short-depth warning (``paired_analysis.py:306``)."""
    deep_cell = (power_analysis.MODELS[0], "intens")
    root = tmp_path_factory.mktemp("mixed_depth")

    def profile(model: str, info: str) -> tuple[float, float, str, range]:
        seeds = (
            range(paired_analysis.EXPECTED_R)
            if (model, info) == deep_cell
            else range(SHALLOW_DEPTH)
        )
        return (0.10 if info == "zero" else 0.90), 0.0, "empty", seeds

    build_tree(root, power_analysis.MODELS, power_analysis.INFOS, profile)
    repoint(root)
    out = _run(paired_analysis.main)
    assert "WARNING" in out
    assert str(SHALLOW_DEPTH) in out


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
    report: Callable[[Path], str], collapse_tree: Path
) -> None:
    """The delta is a within-lane difference, so both rates must be computed over the same seeds."""
    out = report(collapse_tree)
    rows = _padding_table(out)
    assert SKEW_MODEL in rows, rows
    row = rows[SKEW_MODEL]
    assert "COLLAPSE" in row and "not padding-specific" not in row, row
    # Common-seed intens non-compliance is 0%, not the ~34% whole-cell rate.
    assert re.search(r"\s0\.0%\s", row), row


def test_padding_table_reports_the_seed_count_it_used(
    report: Callable[[Path], str], collapse_tree: Path
) -> None:
    """Every row carries the n it was computed over, so a 10-seed comparison isn't mistaken for a 16-seed one."""
    out = report(collapse_tree)
    header = [ln for ln in out.splitlines() if "delta" in ln and "noise" in ln]
    assert header, out[:2000]
    assert re.search(r"\bn\b", header[0]), header[0]
    rows = _padding_table(out)
    assert re.search(rf"\b{_SKEW_SPLIT}\b", rows[SKEW_MODEL]), rows[SKEW_MODEL]
    assert re.search(rf"\b{DEEP_DEPTH}\b", rows[COLLAPSE_MODEL]), rows[COLLAPSE_MODEL]


def test_padding_table_counts_come_from_the_rows_it_actually_built(
    report: Callable[[Path], str], collapse_tree: Path
) -> None:
    """Every count in the section comes from the table's own row count, not a hard-coded lane total."""
    out = report(collapse_tree)
    assert "all 21 lanes" not in out
    n_rows = len(_padding_table(out))
    # Every lane has a census cell for both arms, so the table is the roster.
    assert n_rows == 21, out
    section = out.split("COLLAPSE CENSUS", 1)[1].split("ALL cells", 1)[0]
    counts = {int(n) for n in re.findall(r"of (\d+) lanes", section)}
    assert counts == {n_rows}, section

    def crosses(line: str) -> bool:
        parts = line.split()
        intens, noise = float(parts[1].rstrip("%")), float(parts[2].rstrip("%"))
        return noise >= 25 > intens

    expected_pad = sum(1 for line in _padding_table(out).values() if crosses(line))
    match = re.search(r"=> The pad itself pushes (\d+) of (\d+) lanes", out)
    assert match, out
    assert int(match.group(1)) == expected_pad
    assert int(match.group(2)) == n_rows


def test_padding_intro_numerator_comes_from_the_common_seed_table(
    report: Callable[[Path], str],
    collapse_tree: Path,
    significance_report: ModuleType,
) -> None:
    """`In X of Y lanes` counts table rows whose common-seed noise rate crosses the criterion."""
    out = report(collapse_tree)
    rows = _padding_table(out)
    over = [
        lane
        for lane, line in rows.items()
        if float(line.split()[2].rstrip("%")) / 100
        >= significance_report.COLLAPSE_THRESHOLD
    ]
    section = out.split("COLLAPSE CENSUS", 1)[1]
    match = re.search(r"In (\d+) of (\d+) lanes with both arms measured", section)
    assert match, section[:1200]
    assert int(match.group(1)) == len(over), (over, section[:1200])
    assert int(match.group(2)) == len(rows)


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
            (SKEW_MODEL, "intens"),
            {range(_SKEW_SPLIT): (0, 9)},
        ),
    )
    monkeypatch.setattr(
        significance_report,
        "compliance_census",
        _skew_census(
            significance_report,
            (SKEW_MODEL, "noise_intens"),
            {range(3): (9, 9)},
        ),
    )
    out = report(shared_seed_noise_tree)
    cells = re.search(
        r"(\d+) of (\d+) cells are at or above .*?; (\d+) of them are noise arms",
        out,
    )
    assert cells, out
    assert int(cells.group(3)) == 0
    padding = re.search(r"In (\d+) of (\d+) lanes with both arms measured", out)
    assert padding, out
    assert int(padding.group(1)) == 1


def test_zero_vs_zero_controls_report_the_measured_count_only(
    report: Callable[[Path], str], collapse_tree: Path, shallow_tree: Path
) -> None:
    """The report neither asserts nor assumes a zero rejection count for cross-model floors."""
    for tree in (collapse_tree, shallow_tree):
        out = report(tree)
        assert "by construction" not in out, out
        match = re.search(
            r"(\d+) zero-vs-zero ladder contrasts.*?: (\d+) significant", out, re.S
        )
        assert match, out
        n_zz, n_sig = int(match.group(1)), int(match.group(2))
        assert n_zz > 0
        tail = out[match.end() :].split("=" * 78, 1)[0]
        assert len(re.findall(r"^  SIG    ", tail, re.M)) == n_sig, tail


# ===========================================================================
# three narrative conclusions printed regardless of their own counts
# ===========================================================================


def test_the_ladder_claim_is_conditional_on_its_own_count(
    report: Callable[[Path], str], shallow_tree: Path, collapse_tree: Path
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
    match = re.search(r"(\d+) of the (\d+) losses are LADDER contrasts", collapse)
    assert match, collapse
    n_lad, n_lost = int(match.group(1)), int(match.group(2))
    assert n_lost > 0, "fixture no longer produces any Holm losses"
    tail = collapse[match.start() : match.start() + 600]
    if n_lad:
        assert "bites the family-scaling story" in tail, tail
    else:
        # The zero branch must name the side the data shows, not just avoid the phrase.
        assert one_sided not in tail, tail
        assert "info-arm story" in tail, tail


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
    report: Callable[[Path], str], caveat_tree: Path
) -> None:
    """A collapse annotation without a pad crossing cannot support two mechanisms."""
    out = report(caveat_tree)
    match = re.search(
        r"\[COLLAPSE\] (\d+) of (\d+) findings touch a cell at or above",
        out,
    )
    assert match and int(match.group(1)) > 0, out
    assert "TWO-MECHANISM" not in out
    assert "no evidence for a second" in out


def test_the_ceiling_claim_is_conditional_and_counts_its_discordances(
    report: Callable[[Path], str], collapse_tree: Path, clean_tree: Path
) -> None:
    """`CEILING pairs` needs at least one ceiling pair, and its zero-discordant count must be measured, not asserted as "many"."""
    collapse = report(collapse_tree)
    assert "ties by\n  construction" not in collapse
    assert "ties by construction" not in collapse

    clean = report(clean_tree)
    ceiling_line = [ln for ln in clean.splitlines() if "CEILING pairs" in ln]
    assert ceiling_line, clean[-2000:]
    assert " 126" in ceiling_line[0], ceiling_line[0]
    tail = clean.split("CEILING pairs", 1)[1]
    # A measured count of zero-discordant ceiling pairs, not the word "many".
    assert re.search(r"\d+ .{0,40}zero discordant", tail, re.IGNORECASE), tail[:600]


def test_ceiling_non_rejections_are_split_into_ties_and_unresolved(
    report: Callable[[Path], str], ceiling_tree: Path, clean_tree: Path
) -> None:
    """Ceiling non-rejections distinguish exact ties from unresolved pairs."""
    out = report(ceiling_tree)
    line = next(ln for ln in out.splitlines() if "CEILING pairs" in ln)
    match = re.search(
        r"CEILING pairs .*: (\d+)\. (\d+) of them have ZERO discordant items",
        line,
    )
    assert match, line
    ceiling_count, zero_count = map(int, match.groups())
    assert ceiling_count > 0
    assert "UNRESOLVED" in out
    assert "ties by construction" not in out
    assert zero_count < ceiling_count

    clean = report(clean_tree)
    clean_line = next(ln for ln in clean.splitlines() if "CEILING pairs" in ln)
    clean_match = re.search(
        r"CEILING pairs .*: (\d+)\. (\d+) of them have ZERO discordant items",
        clean_line,
    )
    assert clean_match, clean_line
    assert clean_match.group(1) == clean_match.group(2)


# ===========================================================================
# the direction label had no tie branch
# ===========================================================================


def test_exact_ties_are_labelled_tied_not_extens_higher(
    repoint: Callable[[Path], None], extens_vs_noise: ModuleType, collapse_tree: Path
) -> None:
    """A byte-identical pair of arms must be labelled tied, not awarded to either side."""
    repoint(collapse_tree)
    out = _run(extens_vs_noise.main)
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
    repoint: Callable[[Path], None], extens_vs_noise: ModuleType, collapse_tree: Path
) -> None:
    """A lane whose noise arm is broken must carry a `COLLAPSED` annotation, so it is never read as information."""
    repoint(collapse_tree)
    out = _run(extens_vs_noise.main)
    # The per-model table only: detail rows take their mechanism from the bucket heading.
    table = out.split("mechanism / non-compliance", 1)[1].split("\nH210 =", 1)[0]
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
    repoint: Callable[[Path], None],
    extens_vs_noise: ModuleType,
    collapse_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-compliance outside the seeds the noise arm covers must not colour the contrast."""
    repoint(collapse_tree)
    # Whole-cell view: every seed the noise arm lacks is fully non-compliant.
    skewed = _skew_census(
        extens_vs_noise,
        (SKEW_MODEL, "extens"),
        {range(_SKEW_SPLIT, DEEP_DEPTH): (9, 9)},
    )
    monkeypatch.setattr(extens_vs_noise, "compliance_census", skewed)
    out = _run(extens_vs_noise.main)
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
        (SKEW_MODEL, "noise_intens"),
        {range(_SKEW_SPLIT): (0, 9), range(_SKEW_SPLIT, DEEP_DEPTH): (9, 9)},
    )
    monkeypatch.setattr(significance_report, "compliance_census", skewed)
    out = report(collapse_tree)
    label = "[exaone_32b] noise_intens vs zero"
    lines = [line for line in out.splitlines() if label in line]
    assert lines, out[:3000]
    assert all("[COLLAPSE:" not in line for line in lines), lines

    crossing = _skew_census(
        significance_report, (SKEW_MODEL, "noise_intens"), {range(_SKEW_SPLIT): (9, 9)}
    )
    monkeypatch.setattr(significance_report, "compliance_census", crossing)
    out = report(collapse_tree)
    lines = [line for line in out.splitlines() if label in line]
    assert lines, out[:3000]
    assert any("[COLLAPSE:" in line for line in lines), lines
