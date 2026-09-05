"""Shared machinery for the ``statistical_analyses.ipynb`` cell tests.

``tests/tooling/test_analysis_stats.py`` exercises the analysis MODULES that
notebook imports. Its ``test_stats_notebook_*`` siblings exercise the code the
notebook implements INLINE: sections 0, 7 and 8 define an archive reader, a
posterior-power classifier and a set of flip-rate estimators that live nowhere
else in the tree, so nothing else in the suite can catch them drifting from the
live modules they are supposed to agree with.

Each test pulls one cell's source out of the ``.ipynb`` by a stable needle and
``exec``s it, the same way ``tests/deduction/test_postcutoff_docs.py`` already
does for ``is_mathlib_cell``. Nothing here executes the notebook: the cells
under test are pure, and the one that builds an S3 client is handed a stubbed
``_aws.fresh_client`` so no AWS call is possible.

Not named ``test_*`` on purpose -- it holds no tests and must not be collected.
"""

from __future__ import annotations

import json

from tests._paths import NOTEBOOKS

STATS_NB = NOTEBOOKS / "statistical_analyses.ipynb"


def load_notebook() -> dict:
    """Parse ``statistical_analyses.ipynb``."""
    return json.loads(STATS_NB.read_text())


def cell_source(nb: dict, needle: str) -> str:
    """Return the source of the ONE cell containing `needle`.

    Cells are addressed by content, never by index: the notebook gains and
    loses cells, and an index-keyed test would silently start asserting about
    a different cell instead of failing.
    """
    hits = [c for c in nb["cells"] if needle in "".join(c["source"])]
    assert len(hits) == 1, f"expected exactly one cell containing {needle!r}, got {len(hits)}"
    return "".join(hits[0]["source"])


def load_analysis_modules() -> dict:
    """Load the live analysis modules under the names the notebook binds them to.

    Mirrors the notebook's own loader: both legs ship a ``power_analysis.py``
    that siblings import by BARE name, so each is bound as ``power_analysis``
    only while its dependants exec, then unbound.

    ``notebooks/induction/run_study.py`` calls ``load_dotenv`` and parses
    ``INDUCTION_SHARD`` at MODULE SCOPE, so loading it mutates ``os.environ``
    for the rest of the pytest session. The whole environment is snapshotted
    and restored around the load: ``load_dotenv`` writes keys that cannot be
    named in advance, so a per-key monkeypatch would not cover it.
    """
    import importlib.util
    import os
    import sys

    def load(name, rel, bare=None):
        spec = importlib.util.spec_from_file_location(name, NOTEBOOKS / rel)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module          # dataclass annotations resolve early
        if bare:
            sys.modules[bare] = module
        spec.loader.exec_module(module)
        return module

    saved_modules = {k: sys.modules.get(k) for k in ("power_analysis", "error_bars")}
    saved_env = dict(os.environ)
    saved_path = list(sys.path)
    try:
        ded_pa = load("nbt_ded_power_analysis", "deduction/analysis/power_analysis.py",
                      bare="power_analysis")
        error_bars = load("nbt_ded_error_bars", "deduction/analysis/error_bars.py",
                          bare="error_bars")
        ind_pa = load("nbt_ind_power_analysis", "induction/analysis/power_analysis.py",
                      bare="power_analysis")
        paired = load("nbt_ind_paired", "induction/analysis/paired_analysis.py")
        run_study = load("nbt_ind_run_study", "induction/run_study.py")
    finally:
        for key, old in saved_modules.items():
            if old is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = old
        os.environ.clear()
        os.environ.update(saved_env)
        sys.path[:] = saved_path
    return dict(ded_pa=ded_pa, error_bars=error_bars, ind_pa=ind_pa, paired=paired,
                run_study=run_study, power_common=sys.modules["_power_common"])


def load_deduction_power_analysis():
    """Load just the deduction ``power_analysis`` the notebook binds as ``ded_pa``."""
    import importlib.util
    import sys

    path = NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py"
    spec = importlib.util.spec_from_file_location("nbt_ded_power_analysis_only", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["nbt_ded_power_analysis_only"] = module   # dataclass annotations
    spec.loader.exec_module(module)
    return module
