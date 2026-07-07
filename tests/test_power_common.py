"""``notebooks/_power_common.py``: shared power-analysis scaffolding.

Covers the pieces the periodic and chromatic power-analysis scripts both
import: the experiment-design constants, the 18-contrast family builder, the
replicate-count formatter, and the ``__file__``-anchored results-dir helper.
The scripts' own statistics (CMH / Welch) are intentionally NOT shared code
and so are out of scope here -- see ``_power_common``'s module docstring for
why.

Imports ``_power_common`` the same way the two scripts do: by inserting
``notebooks/`` (where the module lives, one level above either script's own
directory) onto ``sys.path``. Anchored off this test file's own resolved
path rather than the process cwd, so ``pytest`` works regardless of the
invocation directory.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "notebooks"))

import _power_common as pc

# The 18 contrasts, transcribed verbatim from the current
# ``_power_common.build_contrasts()`` output (originally chromatic's
# pre-move implementation, verified structurally identical to periodic's
# former inline loop -- see the commit that introduced this module). Order
# matters: this pins both the *set* of contrasts and their print order,
# since both scripts render tables in this exact sequence.
EXPECTED_CONTRASTS = [
    ("[intens] decode vs cot", ("decode", "intens"), ("cot", "intens")),
    ("[intens] decode vs moe", ("decode", "intens"), ("moe", "intens")),
    ("[intens] cot vs moe", ("cot", "intens"), ("moe", "intens")),
    ("[extens] decode vs cot", ("decode", "extens"), ("cot", "extens")),
    ("[extens] decode vs moe", ("decode", "extens"), ("moe", "extens")),
    ("[extens] cot vs moe", ("cot", "extens"), ("moe", "extens")),
    (
        "[noise_intens] decode vs cot",
        ("decode", "noise_intens"),
        ("cot", "noise_intens"),
    ),
    (
        "[noise_intens] decode vs moe",
        ("decode", "noise_intens"),
        ("moe", "noise_intens"),
    ),
    (
        "[noise_intens] cot vs moe",
        ("cot", "noise_intens"),
        ("moe", "noise_intens"),
    ),
    ("[decode] intens vs extens", ("decode", "intens"), ("decode", "extens")),
    (
        "[decode] intens vs noise_intens",
        ("decode", "intens"),
        ("decode", "noise_intens"),
    ),
    (
        "[decode] extens vs noise_intens",
        ("decode", "extens"),
        ("decode", "noise_intens"),
    ),
    ("[cot] intens vs extens", ("cot", "intens"), ("cot", "extens")),
    (
        "[cot] intens vs noise_intens",
        ("cot", "intens"),
        ("cot", "noise_intens"),
    ),
    (
        "[cot] extens vs noise_intens",
        ("cot", "extens"),
        ("cot", "noise_intens"),
    ),
    ("[moe] intens vs extens", ("moe", "intens"), ("moe", "extens")),
    (
        "[moe] intens vs noise_intens",
        ("moe", "intens"),
        ("moe", "noise_intens"),
    ),
    (
        "[moe] extens vs noise_intens",
        ("moe", "extens"),
        ("moe", "noise_intens"),
    ),
]


def test_build_contrasts_returns_exactly_18():
    contrasts = pc.build_contrasts()
    assert len(contrasts) == 18
    # 9 archetype-within-info + 9 info-within-model, per the docstring.
    assert len(contrasts) == pc.N_TESTS


def test_build_contrasts_matches_pinned_literal():
    """Pins the full (name, key_a, key_b) sequence, not just the count.

    A change to MODELS/INFOS order, the label format, or the two nested-loop
    order (archetype contrasts first, then info-type contrasts) would slip
    past a bare length check but changes every downstream script's printed
    table -- this test catches that.
    """
    assert pc.build_contrasts() == EXPECTED_CONTRASTS


def test_build_contrasts_is_a_fresh_list_each_call():
    """Callers (both scripts) mutate/iterate the result; a shared mutable
    default would leak state between periodic's and chromatic's imports of
    the same process (not applicable across separate `uv run` invocations,
    but is applicable within a single pytest session importing the module
    once)."""
    a = pc.build_contrasts()
    b = pc.build_contrasts()
    assert a == b
    assert a is not b


def test_fmt_r_none_prints_censored_form():
    """`None` means "not reached within the scanned cap": prints as
    ``>{max_replicates}``, independent of what a numeric result would look
    like at that same cap."""
    assert pc.fmt_r(None, 80) == ">80"
    assert pc.fmt_r(None, 200) == ">200"


def test_fmt_r_int_prints_as_plain_number():
    """Any non-`None` result prints as the bare number -- including the
    boundary case where the value equals `max_replicates` itself. The
    `>max` form is reserved for `None`, not triggered by a numeric
    comparison to the cap (see `fmt_r`'s source: the branch is `r is None`,
    not `r >= max_replicates`)."""
    assert pc.fmt_r(1, 80) == "1"
    assert pc.fmt_r(80, 80) == "80"  # equals the cap, still not censored
    assert pc.fmt_r(200, 80) == "200"  # exceeds the cap; still a real value


def test_results_dir_anchored_on_file_not_cwd():
    """`results_dir` must resolve relative to the given file's directory,
    never the process cwd -- otherwise `uv run --no-project ...
    notebooks/x/power_analysis.py` would break when invoked from outside
    the repo root (repo convention: __file__-anchored paths only)."""
    fake_script = REPO_ROOT / "notebooks" / "periodic" / "power_analysis.py"
    assert pc.results_dir(str(fake_script)) == (
        REPO_ROOT / "notebooks" / "periodic" / "results"
    )
    # A relative path string must resolve the same way as its absolute form
    # (exercises the `.resolve()` call), confirming cwd is not silently used
    # as long as the resolved parent matches.
    assert pc.results_dir(__file__) == REPO_ROOT / "tests" / "results"


def test_alpha_corrected_is_bonferroni_over_18_tests():
    assert pc.N_TESTS == 18
    assert pc.ALPHA == 0.05
    assert pc.ALPHA_CORRECTED == 0.05 / 18


def test_module_is_stdlib_only():
    """Must import in the slim `uv run --no-project` envs (no numpy/scipy
    installed there beyond the scripts' own `--with` flags) and in a bare
    interpreter -- i.e. it must not itself require numpy/scipy at import
    time. Checked two ways: the module already imported successfully above
    without numpy/scipy necessarily being on the path, and its source
    contains no such import statement (belt-and-suspenders: catches a
    lazily-imported-but-still-forbidden dependency too)."""
    source = Path(pc.__file__).read_text()
    for banned in ("numpy", "scipy", "statsmodels", "yaml"):
        assert f"import {banned}" not in source
        assert f"from {banned}" not in source
