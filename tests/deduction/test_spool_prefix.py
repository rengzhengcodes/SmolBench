"""The deduction S3 spool prefix (A3): one constant, env override, legacy refusal.

The published pre-cutoff study lives under ``deduction/runs/scaling_<key>/`` and
must never be written again, so the re-collection writes elsewhere. These tests
pin the resolver and, for every module that used to hard-code the old literal,
prove the resolver is never called at import or parser-construction time --
which would make ``LEAN_SPOOL_PREFIX=deduction/runs`` explode before a reader
could legitimately pass the legacy prefix on the command line.
"""

import os
import subprocess
import sys

import pytest

from smolbench.deduction.lean import runner
from tests._paths import NOTEBOOKS, REPO_ROOT, SCRIPTS

LEGACY = "deduction/runs"
NEW = "deduction_postcutoff/runs"

#: Every module that used to hard-code the legacy prefix. ``--help`` exercises
#: import AND argparse default construction in one clean interpreter.
CONSUMERS = [
    SCRIPTS / "fleet" / "run_fleet.py",
    SCRIPTS / "deduction" / "lean_verify_rows.py",
    SCRIPTS / "results" / "audit_lean_pinning.py",
    SCRIPTS / "results" / "audit_run_completeness.py",
    SCRIPTS / "results" / "snapshot_analysis_data.py",
    NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py",
]

#: Analysis/audit consumers that READ the published study and therefore need to
#: accept the legacy prefix explicitly, without the env opt-in.
READERS = [
    SCRIPTS / "results" / "audit_lean_pinning.py",
    SCRIPTS / "results" / "audit_run_completeness.py",
    SCRIPTS / "results" / "snapshot_analysis_data.py",
    NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py",
]


def _help(path, **env):
    """Run ``<path> --help`` in a clean interpreter.

    ``python <script>`` puts the SCRIPT's directory on ``sys.path[0]``, not the
    cwd, so `smolbench` would otherwise resolve through the venv's editable
    install -- which may point at a different checkout than the tree under test.
    ``PYTHONPATH`` pins it to this tree.
    """
    child = {k: v for k, v in os.environ.items()
             if k not in ("LEAN_SPOOL_PREFIX", "LEAN_ALLOW_LEGACY_PREFIX")}
    child["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT)] + ([child["PYTHONPATH"]] if child.get("PYTHONPATH") else []))
    child.update(env)
    return subprocess.run([sys.executable, str(path), "--help"], capture_output=True,
                          text=True, cwd=str(REPO_ROOT), timeout=300, env=child)


def test_the_new_prefix_is_declared_once(monkeypatch):
    """One constant, and it is not the published study's."""
    monkeypatch.delenv("LEAN_SPOOL_PREFIX", raising=False)
    monkeypatch.delenv("LEAN_ALLOW_LEGACY_PREFIX", raising=False)
    assert runner.DEDUCTION_SPOOL_PREFIX == NEW
    assert runner.spool_prefix() == NEW


def test_spool_prefix_reads_the_env_at_call_time(monkeypatch):
    """No caching: a late-set override takes effect, and trailing slashes normalize."""
    monkeypatch.delenv("LEAN_ALLOW_LEGACY_PREFIX", raising=False)
    monkeypatch.setenv("LEAN_SPOOL_PREFIX", "scratch/runs")
    assert runner.spool_prefix() == "scratch/runs"
    monkeypatch.setenv("LEAN_SPOOL_PREFIX", "other/runs/")
    assert runner.spool_prefix() == "other/runs"
    monkeypatch.setenv("LEAN_SPOOL_PREFIX", "")
    assert runner.spool_prefix() == NEW


@pytest.mark.parametrize("value", [LEGACY, LEGACY + "/"])
def test_spool_prefix_refuses_the_published_study_prefix(monkeypatch, value):
    """Writing under `deduction/runs` again would overwrite the published record."""
    monkeypatch.delenv("LEAN_ALLOW_LEGACY_PREFIX", raising=False)
    monkeypatch.setenv("LEAN_SPOOL_PREFIX", value)
    with pytest.raises(ValueError, match="LEAN_ALLOW_LEGACY_PREFIX"):
        runner.spool_prefix()
    monkeypatch.setenv("LEAN_ALLOW_LEGACY_PREFIX", "1")
    assert runner.spool_prefix() == LEGACY


@pytest.mark.parametrize("path", CONSUMERS, ids=lambda p: p.name)
def test_consumers_do_not_resolve_the_prefix_at_import_time(path):
    """`LEAN_SPOOL_PREFIX=deduction/runs` must not blow up import or `--help`.

    A module-level `spool_prefix()` call, or one used as an eagerly-evaluated
    argparse default, would raise here -- and would make the legacy prefix
    unusable even for a reader passing it explicitly.
    """
    proc = _help(path, LEAN_SPOOL_PREFIX=LEGACY)
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"


@pytest.mark.parametrize("path", READERS, ids=lambda p: p.name)
def test_readers_expose_a_spool_prefix_flag(path):
    """Analysis of the published (pre-cutoff) study must stay possible."""
    proc = _help(path)
    assert proc.returncode == 0, f"stderr={proc.stderr}"
    assert "--spool-prefix" in proc.stdout, proc.stdout


def test_power_analysis_duplicate_stays_in_step_with_runner():
    """`power_analysis.py` runs without smolbench installed, so it carries its own
    copy of both prefixes (the same constraint `SUPERSEDED_MARKER` is duplicated
    for). A copy is only safe if something fails when it drifts."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_pa_prefix_check", NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py")
    pa = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = pa
    try:
        spec.loader.exec_module(pa)
        assert pa._DEDUCTION_SPOOL_PREFIX == runner.DEDUCTION_SPOOL_PREFIX
        assert pa._LEGACY_SPOOL_PREFIX == runner.LEGACY_SPOOL_PREFIX
        assert pa.SUPERSEDED_MARKER == runner.SUPERSEDED_MARKER
    finally:
        sys.modules.pop(spec.name, None)


def _fake_s3(keys):
    """A boto3 stand-in whose paginator serves `keys` filtered by Prefix."""
    class _Pager:
        def paginate(self, Bucket, Prefix):  # noqa: N803 -- boto3's parameter names
            yield {"Contents": [{"Key": k, "Size": 10} for k in keys if k.startswith(Prefix)]}

    return type("_S3", (), {"get_paginator": lambda self, name: _Pager()})()


def test_snapshot_prefix_arithmetic_survives_the_slashless_resolver(monkeypatch):
    """`spool_prefix()` returns NO trailing "/", but this module slices by `len(prefix)`.

    Forget the appended "/" and every deduction model name comes back empty
    (``"/scaling_x/f".split("/", 1)[0] == ""``) and every destination key is off
    by one character -- silently, on a 55k-object copy.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_snapshot_prefix_check", SCRIPTS / "results" / "snapshot_analysis_data.py")
    snap = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = snap
    try:
        spec.loader.exec_module(snap)
        keys = [f"{NEW}/scaling_glm-4.7/verified_rows.jsonl",
                f"{NEW}/scaling_gemma-4-12b/all_rows.jsonl",
                "induction/glm-4.7/seed=0/intens--2026-08-01.yaml",
                LEGACY + "/scaling_glm-4.7/verified_rows.jsonl"]
        monkeypatch.delenv("LEAN_SPOOL_PREFIX", raising=False)
        monkeypatch.delenv("LEAN_ALLOW_LEGACY_PREFIX", raising=False)

        rows = snap.iter_source_keys(_fake_s3(keys))
        assert sorted((leg, model) for leg, model, _k, _s in rows) == [
            ("deduction", "gemma-4-12b"), ("deduction", "glm-4.7"),
            ("induction", "glm-4.7")]

        # The published study is still reachable by passing the prefix explicitly.
        legacy_rows = snap.iter_source_keys(_fake_s3(keys), deduction_prefix=LEGACY + "/")
        assert ("deduction", "glm-4.7") in [(leg, m) for leg, m, _k, _s in legacy_rows]
        assert all(m for _l, m, _k, _s in legacy_rows), "a model name lost its prefix slice"
    finally:
        sys.modules.pop(spec.name, None)
