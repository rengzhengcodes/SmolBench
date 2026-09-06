"""The roster, results bucket and region have ONE source; pin every consumer to it.

``smolbench/evals/study_config.toml`` (parsed by
``smolbench.evals.study_config``) is the committed source for this study's
21-checkpoint roster and its results bucket/region. Three deduction-side
consumers used to re-declare parts of it by hand:

* ``notebooks/deduction/analysis/power_analysis.py`` re-typed all 21 keys as
  ``FAMILIES``, guarded only by a length/uniqueness ``assert`` that ``python -O``
  strips, plus the bucket and region as string literals;
* ``scripts/results/audit_lean_pinning.py`` re-typed the same 21 keys as a flat
  ``LANES`` list, plus its own ``BUCKET``/``REGION`` literals;
* ``notebooks/deduction/run_study.py`` spelled the spool bucket and region out
  as ``SPOOL_BUCKET``/``SPOOL_REGION``.

All of them now read the config. These tests pin that: the consumers must agree
with ``study_config`` (not merely with each other), and the literals must be
GONE from the sources -- an equality check alone would still pass against a
hand-typed copy that happens to be correct today.

The induction driver's own ``MODELS`` is pinned here too. It reads the same
config, so this is a second, independent route to the same roster: if either
side stopped reading the config the two would diverge here.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

from smolbench.evals.study_config import families, load_study_config, roster_keys
from tests._paths import NOTEBOOKS, SCRIPTS

INDUCTION_DRIVER = NOTEBOOKS / "induction" / "run_study.py"
POWER_ANALYSIS = NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py"
AUDIT = SCRIPTS / "results" / "audit_lean_pinning.py"
DEDUCTION_DRIVER = NOTEBOOKS / "deduction" / "run_study.py"


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


# ---------------------------------------------------------------------------
# Pin each consumer to study_config itself, and pin the literals GONE.
# ---------------------------------------------------------------------------

#: Files that must no longer spell the results bucket or its region. The bucket
#: string is checked verbatim; the region is checked as a QUOTED literal, so a
#: prose mention inside a docstring is not what trips this (the point is that no
#: code path re-declares the value, not that the words are unmentionable).
_NO_LITERALS = (POWER_ANALYSIS, AUDIT, DEDUCTION_DRIVER)
_BUCKET_LITERAL = "smolbench-results-414266451290"


def test_power_analysis_roster_is_the_config_roster(power_analysis):
    """FAMILIES and MODELS come from study_config, family NAMES included.

    Name equality is the half a "same 21 keys" check misses: before this
    landed, `FAMILIES` grouped the identical keys under three different family
    labels (``nemotron3``/``ministral3``/``deepseek``), which show up in every
    within-family contrast label and in `error_bars.py --out-json`.
    """
    assert dict(power_analysis.FAMILIES) == {f: tuple(r) for f, r in families().items()}
    assert tuple(power_analysis.MODELS) == tuple(roster_keys())


def test_power_analysis_module_scope_guards_survive_dash_O(power_analysis):
    """The drift guards are `raise`, not `assert` -- `python -O` strips asserts.

    Checked on the SOURCE, because a passing import proves nothing either way:
    the guards only fire on a broken config, which the committed one is not.
    """
    source = POWER_ANALYSIS.read_text()
    head = source.split("# Design constants.", 1)[0]
    assert "\nassert " not in head, (
        "a module-scope `assert` guard survives above the design constants; "
        "`python -O` would delete it"
    )
    assert "raise ValueError(" in head


def test_audit_lanes_are_the_config_roster(roster):
    """LANES is study_config's roster, in order (and so still equals the driver's)."""
    if not AUDIT.exists():
        pytest.skip("audit_lean_pinning.py lives in a later stack slice")
    audit = _load(AUDIT, "audit_lean_pinning_for_config_pin")
    assert list(audit.LANES) == list(roster_keys()) == list(roster)


def test_bucket_and_region_come_from_the_config(power_analysis):
    """Every consumer's bucket/region constant equals the committed config's."""
    results = load_study_config().results
    assert (power_analysis.S3_BUCKET, power_analysis.S3_REGION) == (
        results.bucket, results.region)
    if AUDIT.exists():
        audit = _load(AUDIT, "audit_lean_pinning_for_bucket_pin")
        assert (audit.BUCKET, audit.REGION) == (results.bucket, results.region)


@pytest.mark.parametrize("path", _NO_LITERALS, ids=lambda p: p.name)
def test_bucket_and_region_literals_are_gone_from_consumers(path):
    """The value must be READ, not re-typed.

    An equality assertion alone cannot catch a hand-typed copy that is correct
    today and silently stale after the bucket moves, so this pins the absence of
    the literal rather than the presence of the right value.
    """
    source = path.read_text()
    assert _BUCKET_LITERAL not in source, (
        f"{path.name} still spells the results bucket literally; read it from "
        "smolbench.evals.study_config instead"
    )
    for quoted in (f'"{load_study_config().results.region}"',
                   f"'{load_study_config().results.region}'"):
        assert quoted not in source, (
            f"{path.name} still spells the results region as a quoted literal "
            f"({quoted}); read it from smolbench.evals.study_config instead"
        )
