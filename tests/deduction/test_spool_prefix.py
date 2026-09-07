"""The deduction S3 spool prefix: one constant, resolved from the env at call time."""

import importlib.util
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from smolbench.deduction.lean import runner
from tests._paths import NOTEBOOKS, REPO_ROOT, SCRIPTS

NEW = "deduction_postcutoff/runs"

#: Consumers that expose the prefix as a CLI override.
READERS = [
    SCRIPTS / "results" / "audit_lean_pinning.py",
    SCRIPTS / "results" / "audit_run_completeness.py",
    SCRIPTS / "results" / "snapshot_analysis_data.py",
    NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py",
]


def _help(path: Path, **env: str) -> subprocess.CompletedProcess[str]:
    """Run ``<path> --help`` in a clean interpreter.

    ``python <script>`` puts the SCRIPT's directory on ``sys.path[0]``, not the
    cwd, so `smolbench` would otherwise resolve through the venv's editable
    install -- which may point at a different checkout than the tree under test.
    """
    child = {k: v for k, v in os.environ.items() if k != "LEAN_SPOOL_PREFIX"}
    child["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT)] + ([child["PYTHONPATH"]] if child.get("PYTHONPATH") else []))
    child.update(env)
    return subprocess.run([sys.executable, str(path), "--help"], capture_output=True,
                          text=True, cwd=str(REPO_ROOT), timeout=300, env=child)


def test_the_new_prefix_is_declared_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEAN_SPOOL_PREFIX", raising=False)
    assert runner.DEDUCTION_SPOOL_PREFIX == NEW
    assert runner.spool_prefix() == NEW


def test_spool_prefix_reads_the_env_at_call_time(monkeypatch: pytest.MonkeyPatch) -> None:
    """No caching: a late-set override takes effect, and trailing slashes normalize."""
    monkeypatch.setenv("LEAN_SPOOL_PREFIX", "scratch/runs")
    assert runner.spool_prefix() == "scratch/runs"
    monkeypatch.setenv("LEAN_SPOOL_PREFIX", "other/runs/")
    assert runner.spool_prefix() == "other/runs"
    monkeypatch.setenv("LEAN_SPOOL_PREFIX", "")
    assert runner.spool_prefix() == NEW


@pytest.mark.parametrize("path", READERS, ids=lambda p: p.name)
def test_readers_expose_a_spool_prefix_flag(path: Path) -> None:
    """The prefix stays overridable per invocation, not only through the env."""
    if not path.exists():
        pytest.skip(f"{path.name} lives in a later stack slice")
    proc = _help(path)
    assert proc.returncode == 0, f"stderr={proc.stderr}"
    assert "--spool-prefix" in proc.stdout, proc.stdout


def _fake_s3(keys: list[str]) -> Any:
    """A boto3 stand-in whose paginator serves `keys` filtered by Prefix."""
    class _Pager:
        def paginate(
            self, Bucket: str, Prefix: str
        ) -> Iterator[dict[str, list[dict[str, int | str]]]]:  # noqa: N803 -- boto3's parameter names
            yield {"Contents": [{"Key": k, "Size": 10} for k in keys if k.startswith(Prefix)]}

    return type("_S3", (), {"get_paginator": lambda self, name: _Pager()})()


def test_snapshot_prefix_arithmetic_survives_the_slashless_resolver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`spool_prefix()` returns no trailing "/", but this module slices by `len(prefix)`.

    Forget the appended "/" and every deduction model name comes back empty
    (``"/scaling_x/f".split("/", 1)[0] == ""``) and every destination key is off
    by one character -- silently, on a 55k-object copy.
    """
    if not (SCRIPTS / "results" / "snapshot_analysis_data.py").exists():
        pytest.skip("snapshot_analysis_data.py lives in a later stack slice")
    spec = importlib.util.spec_from_file_location(
        "_snapshot_prefix_check", SCRIPTS / "results" / "snapshot_analysis_data.py")
    snap = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = snap
    try:
        spec.loader.exec_module(snap)
        keys = [f"{NEW}/scaling_glm-4.7/verified_rows.jsonl",
                f"{NEW}/scaling_gemma-4-12b/all_rows.jsonl",
                "induction/glm-4.7/seed=0/intens--2026-08-01.yaml"]
        monkeypatch.delenv("LEAN_SPOOL_PREFIX", raising=False)

        rows = snap.iter_source_keys(_fake_s3(keys))
        assert sorted((leg, model) for leg, model, _k, _s in rows) == [
            ("deduction", "gemma-4-12b"), ("deduction", "glm-4.7"),
            ("induction", "glm-4.7")]
        assert all(m for _l, m, _k, _s in rows), "a model name lost its prefix slice"
    finally:
        sys.modules.pop(spec.name, None)
