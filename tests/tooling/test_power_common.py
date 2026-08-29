"""Test ``notebooks/_power_common.py``: shared power-analysis scaffolding.

This covers what both live power-analysis scripts import: the
replicate-count formatter and the ``__file__``-anchored results-dir helper.
The scripts' own statistics are intentionally NOT shared code, and so are
out of scope here.

This file imports ``_power_common`` the same way those scripts do: by
inserting ``notebooks/``, where the module lives, onto ``sys.path``,
anchored off this test file's own resolved path rather than the process
cwd, so ``pytest`` works no matter the invocation directory.
"""

import sys
from pathlib import Path

from tests._paths import NOTEBOOKS

sys.path.insert(0, str(NOTEBOOKS))

import _power_common as pc



def test_fmt_r_none_prints_censored_form():
    """`None` means "not reached within the scanned cap".

    It prints as ``>{max_replicates}``, independent of what a numeric
    result would look like at that same cap.
    """
    assert pc.fmt_r(None, 80) == ">80"
    assert pc.fmt_r(None, 200) == ">200"


def test_fmt_r_int_prints_as_plain_number():
    """Any non-`None` result prints as the bare number.

    This includes the boundary case where the value equals `max_replicates` itself. The
    `>max` form is reserved for `None`, and is never triggered by a numeric comparison
    to the cap. See `fmt_r`'s source: the branch is `r is None`, not `r >=
    max_replicates`.
    """
    assert pc.fmt_r(1, 80) == "1"
    assert pc.fmt_r(80, 80) == "80"  # equals the cap, still not censored
    assert pc.fmt_r(200, 80) == "200"  # exceeds the cap; still a real value


def test_results_dir_anchored_on_file_not_cwd():
    """`results_dir` must resolve relative to the given file's directory.

    It must never resolve relative to the process cwd. Otherwise `uv run --no-project
    ... notebooks/x/power_analysis.py` would break when invoked from outside the repo
    root. Repo convention: __file__-anchored paths only.
    """
    fake_script = NOTEBOOKS / "periodic" / "power_analysis.py"
    assert pc.results_dir(str(fake_script)) == (
        NOTEBOOKS / "periodic" / "results"
    )
    # A relative path string must resolve the same way as its absolute form
    # (exercises the `.resolve()` call), confirming cwd is not silently used
    # as long as the resolved parent matches. Written move-invariantly (this
    # test file's own directory, not a hand-counted REPO_ROOT-relative path)
    # so it keeps passing regardless of which tests/ subdirectory this file
    # lives in.
    assert pc.results_dir(__file__) == Path(__file__).resolve().parent / "results"


def test_results_dir_up_anchors_above_the_callers_own_directory():
    """`up=N` must climb N levels before appending ``results``.

    Both live power-analysis scripts sit one level below their study root
    (``notebooks/<study>/analysis/power_analysis.py``) but must resolve the
    study's own ``notebooks/<study>/results``, not a sibling ``analysis/results``
    that no experiment ever writes. That distinction is load-bearing: only the
    exactly-three-component ``notebooks/<study>/results`` shape maps onto the
    short S3 experiment name (`results_store.experiment_name`); a deeper path
    silently takes the full-path fallback and mints a different prefix.
    """
    script = NOTEBOOKS / "periodic" / "analysis" / "power_analysis.py"
    assert pc.results_dir(str(script), up=1) == NOTEBOOKS / "periodic" / "results"
    # up=0 is the default and must stay a pure no-op change of behaviour.
    assert pc.results_dir(str(script), up=0) == pc.results_dir(str(script))


def test_the_up_callers_are_where_this_helper_expects_them():
    """Tripwire: both `up=1` callers must still be one level below their study.

    This pins only the LAYOUT the `up=1` call sites assume. Whether each
    script actually passes `up=1` is pinned by reading its resolved
    ``RESULTS_DIR`` in ``tests/tooling/test_analysis_stats.py``, which
    already has both modules loaded under unique names.
    """
    for study in ("induction", "deduction"):
        script = NOTEBOOKS / study / "analysis" / "power_analysis.py"
        assert script.is_file(), f"{script} moved; update `up=` at its call site"


def test_module_is_stdlib_only():
    """Must import in the slim `uv run --no-project` envs, and in a bare interpreter.

    Those envs have no numpy or scipy installed beyond the scripts' own
    `--with` flags. So the module must not itself require numpy or
    scipy at import time. This is checked two ways: the module already
    imported successfully above without numpy/scipy necessarily being
    on the path, and its source contains no such import statement.
    Belt-and-suspenders: this second check also catches a
    lazily-imported-but-still-forbidden dependency.
    """
    source = Path(pc.__file__).read_text()
    for banned in ("numpy", "scipy", "statsmodels", "yaml"):
        assert f"import {banned}" not in source
        assert f"from {banned}" not in source
