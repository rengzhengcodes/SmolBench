"""The roster, results bucket and region have one source; pin every consumer to it.

``smolbench/evals/study_config.toml`` (parsed by
``smolbench.evals.study_config``) is the committed source for this study's
21-checkpoint roster and its results bucket/region. Three deduction-side
consumers (power_analysis's ``FAMILIES``, audit_lean_pinning's ``LANES``,
run_study's ``SPOOL_BUCKET``/``SPOOL_REGION``) now read it instead of
re-declaring it by hand. These tests pin that the consumers agree with
``study_config`` (not merely with each other) and that the old literals are
gone from the sources -- an equality check alone would still pass against a
hand-typed copy that happens to be correct today.

The induction driver's own ``MODELS`` is pinned here too, as a second,
independent route to the same roster: if either side stopped reading the
config the two would diverge here.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from smolbench.evals.study_config import families, load_study_config, roster_keys
from tests._paths import NOTEBOOKS, SCRIPTS, load_by_path

INDUCTION_DRIVER = NOTEBOOKS / "induction" / "run_study.py"
POWER_ANALYSIS = NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py"
ROWS_SOURCE = POWER_ANALYSIS.parent / "rows_source.py"
AUDIT = SCRIPTS / "results" / "audit_lean_pinning.py"
DEDUCTION_DRIVER = NOTEBOOKS / "deduction" / "run_study.py"


def _load(path: Path, name: str) -> ModuleType:
    """Exec `path` as module `name`, restoring os.environ afterwards.

    The induction driver reads ``LEAN_*``/``EC2_*`` at import time, so this
    would otherwise mutate the environment for every later test in the
    session. Registered in ``sys.modules`` before ``exec_module`` because a
    ``@dataclass`` in a module absent from ``sys.modules`` fails to resolve
    its own annotations.
    """
    saved = dict(os.environ)
    try:
        return load_by_path(path, name)
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
def power_analysis() -> ModuleType:
    return _load(POWER_ANALYSIS, "deduction_power_analysis_for_roster_pin")


# Pin each consumer to study_config itself, and pin the literals gone.

#: Files that must no longer spell the results bucket or its region. The bucket
#: string is checked verbatim; the region is checked as a quoted literal, so a
#: prose mention inside a docstring is not what trips this (the point is that no
#: code path re-declares the value, not that the words are unmentionable).
_NO_LITERALS = (POWER_ANALYSIS, AUDIT, DEDUCTION_DRIVER)
_BUCKET_LITERAL = "smolbench-results-414266451290"


def test_power_analysis_roster_is_the_config_roster(power_analysis: ModuleType) -> None:
    """FAMILIES and MODELS come from study_config, family names included.

    Name equality is the half a "same 21 keys" check misses: before this
    landed, `FAMILIES` grouped the identical keys under three different family
    labels (``nemotron3``/``ministral3``/``deepseek``), which show up in every
    within-family contrast label and in `error_bars.py --out-json`.
    """
    assert dict(power_analysis.FAMILIES) == {f: tuple(r) for f, r in families().items()}
    assert tuple(power_analysis.MODELS) == tuple(roster_keys())


def test_power_analysis_module_scope_guards_survive_dash_O() -> None:
    """Module-scope drift guards use explicit raises because ``-O`` strips asserts."""
    source = POWER_ANALYSIS.read_text()
    head = source.split("# Design constants.", 1)[0]
    assert "\nassert " not in head, (
        "a module-scope `assert` guard survives above the design constants; "
        "`python -O` would delete it"
    )
    assert "raise ValueError(" in head


def test_audit_lanes_are_the_config_roster(roster: tuple[str, ...]) -> None:
    """LANES is study_config's roster, in order (and so still equals the driver's)."""
    if not AUDIT.exists():
        pytest.skip("audit_lean_pinning.py lives in a later stack slice")
    audit = _load(AUDIT, "audit_lean_pinning_for_config_pin")
    assert list(audit.LANES) == list(roster_keys()) == list(roster)


def test_bucket_and_region_come_from_the_config() -> None:
    """Every consumer's bucket/region constant equals the committed config's."""
    results = load_study_config().results
    rows_source = _load(ROWS_SOURCE, "deduction_rows_source_for_bucket_pin")
    assert rows_source.S3_BUCKET == results.bucket
    if AUDIT.exists():
        audit = _load(AUDIT, "audit_lean_pinning_for_bucket_pin")
        assert (audit.BUCKET, audit.REGION) == (results.bucket, results.region)


@pytest.mark.parametrize("path", _NO_LITERALS, ids=lambda p: p.name)
def test_bucket_and_region_literals_are_gone_from_consumers(path: Path) -> None:
    """The value must be read, not re-typed.

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
