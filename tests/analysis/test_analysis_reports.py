"""Behavioural pins for the ``notebooks/induction/analysis/`` report scripts.

These scripts had no tests: every one of them walks a real 21-model x 4-arm
replicate tree and prints a narrative report, so nothing in them could be
exercised without a fixture tree. ``tests/analysis/conftest.py`` builds one
with controlled per-cell accuracy, compliance and DEPTH, and the tests below
run each report end-to-end against it and assert on what it printed.

Three trees, each engineered for a specific claim (see each fixture's
docstring):

* ``shallow_tree`` -- 6 seeds everywhere. The sign-flip floor ``2/2**6 =
  3.1e-2`` sits far above Holm's loosest threshold ``0.05/210 = 2.381e-4``,
  so NO contrast is rejectable however large its effect. Every positive
  control "fails". This is an incomplete sync, not a null result, and the
  report has to say so.
* ``collapse_tree`` -- 16 seeds (floor ``3.1e-5``, rejectable), with four
  deliberate anomalies: a collapsed noise arm, a weak-but-COMPLIANT intens
  arm, a lane whose intens and noise arms cover DIFFERENT seed sets, and a
  legacy lane with no assessed marks.
* ``clean_tree`` -- 16 seeds, every informative arm at 0.99 and fully
  compliant: all 126 findings are ceiling ties and no cell is collapsed.

Every number quoted in a docstring below was OBSERVED by running the report
at commit f3a13c9a before the fixes; where a test asserts an absence, the
string it forbids was present in that run.
"""

import io
import contextlib
import re

import pytest

# The four module fixtures are imported for their SIDE EFFECT of entering this
# module's namespace: pytest collects fixtures from a test module's globals,
# and ``tests/analysis`` deliberately has no conftest.py (see _trees.py).
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

#: Lane whose `noise_intens` arm is 90% non-compliant AND scores at the floor:
#: a genuine padding collapse, so its failing positive control IS explained by
#: the pad.
COLLAPSE_MODEL = "ds_pro"
#: Lane whose `intens` arm scores at the floor while staying FULLY COMPLIANT:
#: its failing positive control is NOT explained by the pad, and must not be
#: swept into the padding exoneration.
WEAK_MODEL = "min3_3b"
#: Lane whose `intens` cell covers 16 seeds but whose `noise_intens` cell
#: covers only the first 10, with the intens non-compliance living entirely on
#: the 6 seeds noise does not have. Whole-cell and common-seed deltas disagree.
SKEW_MODEL = "exaone_32b"
#: Lane whose `noise_intens` marks all pre-date the compliance field, so the
#: census has no cell for it and the padding table must be one row short.
LEGACY_MODEL = "glm_air"
#: Lane whose `noise_intens` arm is a BYTE COPY of its `extens` arm: an exact
#: tie, which the direction label had no branch for.
TIED_MODEL = "nemo3_30b"

_SKEW_SPLIT = 10


def _run(fn) -> str:
    """Call `fn`, returning everything it wrote to stdout and stderr."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        fn()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Trees
# ---------------------------------------------------------------------------

def _shallow_profile(model, info):
    seeds = range(SHALLOW_DEPTH)
    return (0.10 if info == "zero" else 0.90), 0.0, "empty", seeds


def _collapse_profile(model, info):
    seeds = range(DEEP_DEPTH)
    if model == COLLAPSE_MODEL and info == "noise_intens":
        return 0.10, 0.90, "empty", seeds
    if model == WEAK_MODEL and info == "intens":
        return 0.10, 0.0, "empty", seeds
    if model == LEGACY_MODEL and info == "noise_intens":
        # mode=None -> every mark NOT_ASSESSED, so the census omits the cell.
        return 0.90, 0.0, None, seeds
    if model == SKEW_MODEL and info == "intens":
        # Non-compliant ONLY on the seeds the noise arm lacks.
        return 0.90, (lambda seed: 0.90 if seed >= _SKEW_SPLIT else 0.0), \
            "empty", seeds
    if model == SKEW_MODEL and info == "noise_intens":
        return 0.90, 0.50, "empty", range(_SKEW_SPLIT)
    return (0.10 if info == "zero" else 0.90), 0.0, "empty", seeds


def _clean_profile(model, info):
    seeds = range(DEEP_DEPTH)
    return (0.10 if info == "zero" else 0.99), 0.0, "empty", seeds


@pytest.fixture(scope="session")
def shallow_tree(tmp_path_factory, power_analysis):
    """6 seeds everywhere: below the sign-flip resolution floor."""
    root = tmp_path_factory.mktemp("shallow")
    build_tree(root, power_analysis.MODELS, power_analysis.INFOS, _shallow_profile)
    return root


@pytest.fixture(scope="session")
def collapse_tree(tmp_path_factory, power_analysis):
    """16 seeds, with the four engineered anomalies this module's constants name."""
    root = tmp_path_factory.mktemp("collapse")
    build_tree(root, power_analysis.MODELS, power_analysis.INFOS, _collapse_profile,
               copies={(TIED_MODEL, "noise_intens"): (TIED_MODEL, "extens")})
    return root


@pytest.fixture(scope="session")
def clean_tree(tmp_path_factory, power_analysis):
    """16 seeds, every informative arm at 0.99 and compliant: all ties, no collapse."""
    root = tmp_path_factory.mktemp("clean")
    build_tree(root, power_analysis.MODELS, power_analysis.INFOS, _clean_profile)
    return root


@pytest.fixture
def report(repoint, significance_report):
    """Return ``root -> significance_report.main()``'s captured output."""

    def _report(root):
        repoint(root)
        return _run(significance_report.main)

    return _report


# ===========================================================================
# 12-03 -- the control-failure message is hard-coded and there is no depth guard
# ===========================================================================

def test_shallow_sync_prints_an_incomplete_banner_and_no_exoneration(report,
                                                                     shallow_tree):
    """At 6 seeds nothing is rejectable, so the report must say INCOMPLETE SYNC.

    Holm's LOOSEST threshold over the 210-contrast family is 0.05/210 =
    2.381e-4, while ``signflip_exact_p``'s hard floor is 2/2**S = 3.125e-2 at
    S=6. No contrast can be rejected at ANY effect size, so all 63 positive
    controls "fail" -- observed verbatim at f3a13c9a, together with the fixed
    padding exoneration printed underneath rows like
    ``[qwen35_122b] intens vs zero 0.852 vs 0.093``, which is not a noise arm
    and not non-compliant at all. The banner must fire and the exoneration
    must be suppressed: a floor-bound family is an incomplete sync, not a
    result about padding.
    """
    out = report(shallow_tree)
    assert "INCOMPLETE SYNC" in out
    # The blanket exoneration must NOT print under a floor-bound family.
    assert "whitespace padding drove" not in out
    # The banner itself has to carry the arithmetic that justifies it, so a
    # reader can check the comparison rather than take the label on trust.
    banner = out.split("INCOMPLETE SYNC", 1)[1][:800]
    assert re.search(r"2\s*/\s*2\W*\W?6|3\.12\d*e-0?2", banner), banner
    assert re.search(r"2\.38\d*e-0?4|0\.05\s*/\s*210", banner), banner


def test_failing_controls_are_exonerated_only_where_the_pad_explains_them(
        report, collapse_tree):
    """Exactly one of the two failing controls is a collapsed noise arm.

    ``ds_pro``'s noise arm is 90% non-compliant AND scores at the floor -- the
    pad really does explain its failure. ``min3_3b``'s intens arm scores at
    the floor while staying 100% compliant -- the pad explains nothing there.
    At f3a13c9a both were covered by one hard-coded paragraph: "These 2
    failures ... each is a noise arm the whitespace padding drove to
    near-total non-compliance". The count must now be 1 of 2, and the
    unexplained failure must be named as such.
    """
    out = report(collapse_tree)
    controls = out.split("ZERO-ARM CONTROLS", 1)[1]
    fails = [ln for ln in controls.splitlines() if ln.strip().startswith("FAILS")]
    # Derived from the printed rows, not hard-coded: a row qualifies for the
    # padding exoneration only if its arm is `noise_intens` AND the census
    # flagged that cell at or above COLLAPSE_THRESHOLD.
    qualifying = [ln for ln in fails if "noise_intens" in ln and "[COLLAPSE:" in ln]
    assert fails and qualifying and len(qualifying) < len(fails), fails

    match = re.search(r"These (\d+) of (\d+) failures", controls)
    assert match, controls
    assert (int(match.group(1)), int(match.group(2))) == (len(qualifying), len(fails))

    assert "NOT explained by padding" in controls
    explained, _, unexplained = controls.partition("NOT explained by padding")
    # The exoneration paragraph sits above the split ...
    assert "whitespace padding drove" in explained
    # ... and the compliant, non-noise failure is named below it.
    assert WEAK_MODEL in unexplained
    assert WEAK_MODEL not in explained.rsplit("These ", 1)[-1]


def test_replicate_depth_gate_uses_the_shallowest_lane(repoint, paired_analysis,
                                                       tmp_path_factory,
                                                       power_analysis):
    """One deep lane must not silence the short-depth warning (paired_analysis:306).

    The gate compared ``max(depths.values())`` against EXPECTED_R, so a single
    lane at full depth suppressed the warning for 83 short ones -- while the
    sign-flip floor is set by the SHALLOWEST lane in each contrast. Here one
    cell carries 30 replicates and every other carries 6.
    """
    deep_cell = (power_analysis.MODELS[0], "intens")
    root = tmp_path_factory.mktemp("mixed_depth")

    def profile(model, info):
        seeds = range(paired_analysis.EXPECTED_R) if (model, info) == deep_cell \
            else range(SHALLOW_DEPTH)
        return (0.10 if info == "zero" else 0.90), 0.0, "empty", seeds

    build_tree(root, power_analysis.MODELS, power_analysis.INFOS, profile)
    repoint(root)
    out = _run(paired_analysis.main)
    assert "WARNING" in out
    assert str(SHALLOW_DEPTH) in out


# ===========================================================================
# 12-04 -- the padding table subtracted rates over DIFFERENT seed sets
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


def test_padding_table_subtracts_over_the_common_seeds_only(report, collapse_tree):
    """The delta is a within-lane difference, so both rates need the same seeds.

    ``exaone_32b``'s intens cell has 16 replicates and its noise cell only the
    first 10, with ALL of the intens non-compliance living on the 6 seeds noise
    does not have. Over the whole cells that reads as intens ~34% vs noise
    ~50%, a +16pp delta -> "collapsed, but not padding-specific". Over the 10
    seeds both actually cover it is 0% vs ~50%, a ~+50pp delta -> "COLLAPSE".
    The table's own header calls the delta "attributable to the whitespace and
    nothing else", which is only true on matched seeds.
    """
    out = report(collapse_tree)
    rows = _padding_table(out)
    assert SKEW_MODEL in rows, rows
    row = rows[SKEW_MODEL]
    assert "COLLAPSE" in row and "not padding-specific" not in row, row
    # Common-seed intens non-compliance is 0%, not the ~34% whole-cell rate.
    assert re.search(r"\s0\.0%\s", row), row


def test_padding_table_reports_the_seed_count_it_used(report, collapse_tree):
    """Every row carries the n it was computed over; a 10-seed row is not a 16.

    Without an n column a reader cannot tell a lane compared on 10 matched
    seeds from one compared on 16, which is exactly the difference that moves
    a verdict.
    """
    out = report(collapse_tree)
    header = [ln for ln in out.splitlines() if "delta" in ln and "noise" in ln]
    assert header, out[:2000]
    assert re.search(r"\bn\b", header[0]), header[0]
    rows = _padding_table(out)
    assert re.search(rf"\b{_SKEW_SPLIT}\b", rows[SKEW_MODEL]), rows[SKEW_MODEL]
    assert re.search(rf"\b{DEEP_DEPTH}\b", rows[COLLAPSE_MODEL]), rows[COLLAPSE_MODEL]


def test_padding_table_counts_come_from_the_rows_it_actually_built(report,
                                                                  collapse_tree):
    """A lane with no census cell drops out of the table, so "all 21" is wrong.

    ``glm_air``'s noise marks all pre-date the compliance field, so the census
    omits that cell and the padding table can only build 20 rows. At f3a13c9a
    the caption said "all 21 lanes" and the header said "of ``len(MODELS)``"
    while the footer said "of ``len(pad_rows)``" -- three counts, two of them
    wrong, in one section.
    """
    out = report(collapse_tree)
    assert "all 21 lanes" not in out
    assert len(_padding_table(out)) == 20
    section = out.split("COLLAPSE CENSUS", 1)[1].split("ALL cells", 1)[0]
    # Every "of N lanes" count in this section is the table's own row count.
    counts = {int(n) for n in re.findall(r"of (\d+) lanes", section)}
    assert counts == {20}, section


# ===========================================================================
# 12-05 -- three narrative conclusions printed regardless of their own counts
# ===========================================================================

def test_the_ladder_claim_is_conditional_on_its_own_count(report, shallow_tree,
                                                          collapse_tree):
    """"the clustering correction bites the family-scaling story" needs n_lad > 0.

    Observed at f3a13c9a on the shallow tree, verbatim: "0 of the 63 losses
    are LADDER contrasts -- the clustering correction bites the family-scaling
    story, not the info-arm story." Every one of those 63 losses was an
    info-arm contrast, i.e. the exact opposite of the claim. On the collapse
    tree n_lad is 2 of 4, so the claim is earned and must still print.
    """
    shallow = report(shallow_tree)
    assert "0 of the 63 losses" not in shallow or \
        "bites the family-scaling story" not in shallow
    assert "bites the family-scaling story" not in shallow

    collapse = report(collapse_tree)
    assert "bites the family-scaling story" in collapse


def test_the_two_mechanism_claim_is_conditional_on_a_flagged_finding(
        report, shallow_tree, clean_tree, collapse_tree):
    """"TWO-MECHANISM" needs a significant finding that actually touches a collapse.

    At f3a13c9a it printed under "[COLLAPSE] 0 of 0 findings touch a cell at or
    above 25% non-compliance" -- a two-mechanism conclusion drawn from zero
    findings and zero collapses. The shallow tree has 0 significant findings
    and the clean tree has 0 collapsed cells; the collapse tree has both, so
    the claim is earned there.
    """
    assert "TWO-MECHANISM" not in report(shallow_tree)
    assert "TWO-MECHANISM" not in report(clean_tree)
    assert "TWO-MECHANISM" in report(collapse_tree)


def test_the_ceiling_claim_is_conditional_and_counts_its_discordances(
        report, collapse_tree, clean_tree):
    """"CEILING pairs ... many have ZERO discordant items" needs ceiling pairs.

    At f3a13c9a it printed as "CEILING pairs (both arms >= 0.95): 0 -- these
    are ties by construction, not underpowered; many have ZERO discordant
    items". Nothing was 0.95, and the discordant counts nb/nc computed a few
    lines earlier were never stored, so "many have ZERO" was never measured
    at all. On the clean tree all 126 findings ARE ceiling pairs, so the
    claim is earned -- and the "ZERO discordant" part must be a computed
    count, not an adjective.
    """
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


# ===========================================================================
# 12-15 -- the direction label had no tie branch
# ===========================================================================

def test_exact_ties_are_labelled_tied_not_extens_higher(repoint, extens_vs_noise,
                                                        collapse_tree):
    """A byte-identical pair of arms is a tie, and the report already knows it.

    ``nemo3_30b``'s noise arm is a byte copy of its extens arm, so
    ``acc_n == acc_e`` exactly. ``"noise HIGHER" if acc_n > acc_e else "extens
    HIGHER"`` awarded that row to extens in two places, while the RAW
    DIRECTION block two screens later counted the same lane as a third
    category, "exactly tied" -- the one report contradicting itself.
    """
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


def test_collapsed_lane_still_buckets_as_collapse_not_unmeasured(repoint,
                                                                 extens_vs_noise,
                                                                 collapse_tree):
    """`mechanism()` must still see a rate for every measured cell.

    Regression guard for the census refactor (12-26): ``extens_vs_noise.main``
    reads non-compliance through a ``nc()`` closure over
    ``census.get(key)["rate"]``. If the census dict ever gained its per-seed
    decomposition WITHOUT keeping ``rate``, ``nc()`` would return NaN and every
    lane would silently fall into the "unmeasured" bucket -- which reads as a
    sync problem rather than the wrong-shaped dict it would be. The two loud
    buckets are pinned here from opposite directions: the collapsed lane must
    be COLLAPSE, and the lane whose census cell genuinely does not exist must
    be the ONLY unmeasured one.
    """
    repoint(collapse_tree)
    out = _run(extens_vs_noise.main)
    # The per-model table only: its rows carry the `mechanism` column, unlike
    # the per-bucket detail rows further down, which take their mechanism from
    # the bucket heading above them.
    table = out.split("mechanism / non-compliance", 1)[1].split("\nH210 =", 1)[0]
    rows = {ln.split()[0]: ln for ln in table.splitlines()
            if ln[:1].isalpha() and len(ln.split()) > 3}
    assert COLLAPSE_MODEL in rows, table[:2500]
    assert "COLLAPSE" in rows[COLLAPSE_MODEL], rows[COLLAPSE_MODEL]
    # LEGACY_MODEL's noise marks are all NOT_ASSESSED, so it has no census cell
    # and IS legitimately unmeasured -- it is the control that keeps the
    # assertion above from passing just because nothing is ever "unmeasured".
    unmeasured = [model for model, line in rows.items() if "unmeasured" in line]
    assert unmeasured == [LEGACY_MODEL], unmeasured
