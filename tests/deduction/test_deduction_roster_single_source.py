"""The 21-model roster is re-declared in three places; pin them against each other (13-25).

``notebooks/induction/run_study.py``'s ``MODELS`` is the roster's single source
of truth -- ``notebooks/deduction/run_study.py`` says so in its own module
docstring and loads it BY FILE PATH rather than re-typing it. Two deduction-side
consumers do re-type it:

* ``notebooks/deduction/analysis/power_analysis.py::FAMILIES`` re-declares all 21
  keys, grouped into 7 families of 3. Its module-scope ``assert`` catches only
  length and uniqueness drift, and is stripped under ``python -O``; nothing
  compared it against the roster.
* ``scripts/results/audit_lean_pinning.py::LANES`` re-types the same 21 keys as a
  flat list, with a comment explaining the duplication is deliberate ("so this
  audit does not depend on the driver it is auditing") -- a defensible choice
  that still needs a test, or the audit silently audits a stale roster.

These tests do not remove either duplicate (a single roster/bucket config is
tracked as a follow-up issue). They make a divergence fail here instead of
surfacing as a lane that was never analysed.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

from tests._paths import NOTEBOOKS, SCRIPTS

INDUCTION_DRIVER = NOTEBOOKS / "induction" / "run_study.py"
POWER_ANALYSIS = NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py"
AUDIT = SCRIPTS / "results" / "audit_lean_pinning.py"


def _load(path, name):
    """Exec `path` as module `name`, restoring os.environ afterwards.

    The induction driver calls ``load_dotenv()`` and reads ``LEAN_*``/``EC2_*``
    at import time, so importing it here would otherwise mutate the environment
    for every later test in the session. Registered in ``sys.modules`` before
    ``exec_module`` because a ``@dataclass`` defined in a module absent from
    ``sys.modules`` fails to resolve its own annotations.
    """
    saved = dict(os.environ)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(name, None)
        os.environ.clear()
        os.environ.update(saved)


@pytest.fixture(scope="module")
def roster() -> tuple[str, ...]:
    """The roster's spec keys, in the induction driver's declaration order."""
    induction = _load(INDUCTION_DRIVER, "induction_run_study_for_roster_pin")
    keys = tuple(induction.MODELS)
    assert len(keys) == 21, f"roster is {len(keys)} keys, expected 21"
    return keys


@pytest.fixture(scope="module")
def power_analysis():
    return _load(POWER_ANALYSIS, "deduction_power_analysis_for_roster_pin")


def test_power_analysis_families_cover_the_roster_exactly(roster, power_analysis):
    """FAMILIES' 21 keys are the roster's 21 keys -- as a SET and by count.

    Set equality, not just a count: 21-vs-21 with one key swapped for a typo is
    exactly the failure that would otherwise surface as a lane silently missing
    from every contrast the analysis reports.
    """
    flat = [m for rungs in power_analysis.FAMILIES.values() for m in rungs]
    assert len(power_analysis.FAMILIES) == 7, sorted(power_analysis.FAMILIES)
    assert all(len(rungs) == 3 for rungs in power_analysis.FAMILIES.values())
    assert len(flat) == len(set(flat)) == 21
    assert set(flat) == set(roster), {
        "missing_from_FAMILIES": sorted(set(roster) - set(flat)),
        "not_in_roster": sorted(set(flat) - set(roster)),
    }
    assert tuple(power_analysis.MODELS) == tuple(flat), (
        "MODELS must stay a plain flattening of FAMILIES"
    )


def test_audit_lanes_cover_the_roster_exactly(roster):
    """audit_lean_pinning.LANES is the same 21 keys, in the same ORDER.

    Order matters here in a way it does not for `FAMILIES`: LANES' own comment
    calls itself "the 21 lane spec keys, in roster order", and reports built
    from it are read side by side with the induction study's.
    """
    if not AUDIT.exists():
        pytest.skip("audit_lean_pinning.py lives in a later stack slice")
    audit = _load(AUDIT, "audit_lean_pinning_for_roster_pin")
    assert list(audit.LANES) == list(roster), {
        "missing_from_LANES": sorted(set(roster) - set(audit.LANES)),
        "not_in_roster": sorted(set(audit.LANES) - set(roster)),
        "order_only": sorted(audit.LANES) == sorted(roster),
    }


def test_flip_run_lanes_are_real_lanes(roster):
    """Every FLIP_RUNS lane names a roster key, so a re-run cannot audit a ghost."""
    if not AUDIT.exists():
        pytest.skip("audit_lean_pinning.py lives in a later stack slice")
    audit = _load(AUDIT, "audit_lean_pinning_for_flip_pin")
    unknown = sorted({lane for _, lane in audit.FLIP_RUNS} - set(roster))
    assert not unknown, unknown
