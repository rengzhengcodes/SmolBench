"""The Horn tables and figures from a released results folder (``make_figures.py``)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys

import pytest

from smolbench.deduction.horn.render import ARMS
from smolbench.deduction.horn.repro import check_data, seed_digest
from tests._paths import REPO_ROOT

ANALYSIS = REPO_ROOT / "notebooks" / "deduction" / "analysis"
MODEL = "gemma-4-e2b"
SEEDS = range(100, 112)


def _load(name: str):
    if str(ANALYSIS) not in sys.path:
        sys.path.insert(0, str(ANALYSIS))
    spec = importlib.util.spec_from_file_location(name, ANALYSIS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _row(arm: str, seed: int, rep: int, ok: bool) -> dict:
    verdict = "success" if ok else "invalid_step"
    fields = {
        "answer": "",
        "verdict": verdict,
        "steps": 6,
        "route": "short",
        "reason": "",
        "ignored_lines": 0,
    }
    return {
        "model": MODEL, "spec_key": MODEL, "rung": "m6", "arm": arm, "seed": seed, "rep": rep,
        "prompt_tokens": 900, "completion_tokens": 2000 + 100 * ARMS.index(arm),
        "finish_reason": "stop", "content": "derive a(c) from f(c)\n", "reasoning": "",
        **fields, "source": "spot",
    }  # fmt: skip


@pytest.fixture()
def data(tmp_path):
    """A results folder with one model: 4 arms x 12 seeds x 3 replicates."""
    rng = random.Random(0)
    rate = {"lem": 0.9, "pad": 0.7, "disc": 0.6, "both": 0.4}
    rows = []
    for rep in range(3):
        for seed in SEEDS:
            for arm in ARMS:
                ok = rng.random() < rate[arm]
                rows.append(_row(arm, seed, rep, ok))
    path = tmp_path / "data" / "horn" / "rows" / f"{MODEL}.jsonl"
    path.parent.mkdir(parents=True)
    body = "".join(json.dumps(r) + "\n" for r in rows).encode()
    path.write_bytes(body)
    prompts = tmp_path / "data" / "horn" / "prompts" / "m6"
    seed = prompts / "s0100"
    seed.mkdir(parents=True)
    (seed / "theory.json").write_bytes(b"synthetic-theory")
    for index, arm in enumerate(ARMS):
        arm_dir = seed / arm
        arm_dir.mkdir()
        for name in ("prompt.md", "system.md", "meta.json"):
            (arm_dir / name).write_bytes(f"{arm}-{name}-{index}".encode())
    manifest = {
        "files": {
            f"horn/rows/{MODEL}.jsonl": {
                "sha256": hashlib.sha256(body).hexdigest(),
                "rows": len(rows),
            }
        },
        "prompts": {
            "m6": {
                "arms": list(ARMS),
                "digests": {"100": seed_digest(prompts / "s0100")},
            }
        },
    }
    (tmp_path / "data" / "MANIFEST.json").write_text(json.dumps(manifest))
    return tmp_path / "data", rows


def test_check_data_catches_a_changed_file(data):
    """The manifest catches changed files and missing prompts."""
    folder, _ = data
    assert not check_data(folder)
    path = folder / "horn" / "rows" / f"{MODEL}.jsonl"
    path.write_bytes(path.read_bytes() + b"\n")
    assert check_data(folder) == [
        f"horn/rows/{MODEL}.jsonl: checksum differs from the MANIFEST"
    ]
    (folder / "horn" / "prompts" / "m6" / "s0100" / "pad" / "prompt.md").write_text(
        "changed"
    )
    assert check_data(folder)[1:] == [
        "horn/prompts/m6/s0100: digest differs from the MANIFEST"
    ]
    (folder / "horn" / "prompts" / "m6" / "s0100" / "disc" / "meta.json").unlink()
    assert check_data(folder)[1:] == ["horn/prompts/m6/s0100: meta.json missing"]


def test_make_figures_writes_the_tables_and_figures(data, tmp_path):
    """The figure script writes the paper tables and figures."""
    pytest.importorskip("matplotlib")
    folder, rows = data
    out = tmp_path / "out"
    assert _load("make_figures").main(["--data", str(folder), "--out", str(out)]) == 0
    summary = json.loads((out / "horn_summary.json").read_text())["models"][MODEL]
    for arm in ARMS:
        selected = [row for row in rows if row["arm"] == arm]
        per_seed = {}
        for row in selected:
            per_seed.setdefault(row["seed"], []).append(row["verdict"] == "success")
        expected = sum(sum(values) / len(values) for values in per_seed.values()) / len(
            per_seed
        )
        assert summary["arms"][arm]["mean"] == pytest.approx(expected)
    for name in (
        "horn_table.tex",
        "horn_table_full.tex",
        "horn_ladder_arms.png",
        "horn_routes.md",
        "reasoning_length_increase.png",
    ):
        assert (out / name).exists(), name
