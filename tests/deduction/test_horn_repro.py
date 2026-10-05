"""Reproduction of the ICLR Horn runs (``horn.repro``, ``horn.stats``, ``demo.py``)."""

from __future__ import annotations

import importlib.util
import json
import random
import sys

from smolbench.deduction.horn import repro
from smolbench.deduction.horn.cli import parse_seeds
from smolbench.deduction.horn.render import ARMS
from smolbench.deduction.horn.stats import contrast, format_p, load_rows, pass_rate
from tests._paths import REPO_ROOT

HORN_SCRIPTS = REPO_ROOT / "scripts" / "deduction" / "horn"


def _load(name: str):
    if str(HORN_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(HORN_SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, HORN_SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_parse_seeds_mixes_ranges_and_numbers():
    assert parse_seeds("100-102,200") == [100, 101, 102, 200]


def test_protocol_record_is_complete():
    proto = repro.load_protocol()
    assert proto["seeds"] == "100-199" and proto["replicates"] == 3
    assert proto["arms"] == list(ARMS)
    assert len(proto["models"]) == 16
    for key, e in proto["models"].items():
        assert str(e["m"]) in proto["rung_digests"], key
        assert {"lem", "pad", "disc", "both", "lem-both", "pad-both", "disc-both"} <= set(e["results"])
        if e["backend"] == "vllm":
            assert len(e["revision"]) == 40
        else:
            assert e["bedrock_model_id"] and e["bedrock_region"]
    for digests in proto["rung_digests"].values():
        assert sorted(map(int, digests)) == parse_seeds("100-199")


def test_render_matches_the_served_rung(tmp_path):
    seeds = [100, 157]
    repro.render_rung(tmp_path, 2, seeds)
    assert repro.verify_rung(tmp_path, 2, seeds) == []
    (tmp_path / "s0157" / "pad" / "prompt.md").write_text("changed", encoding="utf-8")
    assert repro.verify_rung(tmp_path, 2, seeds) == ["s0157: digest differs from the served rung"]
    assert repro.verify_rung(tmp_path, 2, [101]) == ["s0101: missing"]
    assert repro.verify_rung(tmp_path, 5, seeds)[0].startswith("no recorded digests for m=5")


def test_commands_carry_the_protocol_settings(tmp_path):
    cmd = repro.sweep_command("glm-4.7", tmp_path / "m48", tmp_path / "rows.jsonl", None, None)
    assert cmd[1].endswith("bedrock_sweep.py")
    assert cmd[cmd.index("--model") + 1] == "zai.glm-4.7"
    assert json.loads(cmd[cmd.index("--extra-fields") + 1]) == {"reasoning_effort": "high"}
    for flag, value in (("--seeds", "100-199"), ("--replicates", "3"), ("--max-tokens", "131072"),
                        ("--temperature", "0.7")):
        assert cmd[cmd.index(flag) + 1] == value
    cmd = repro.sweep_command("qwen3.5-27b", tmp_path, tmp_path / "rows.jsonl", "http://h:1/v1", None)
    assert cmd[1].endswith("sweep.py") and cmd[cmd.index("--endpoint") + 1] == "http://h:1/v1"
    serve = repro.serve_command("qwen3.5-27b")
    assert serve[:3] == ["vllm", "serve", "Qwen/Qwen3.5-27B"]
    assert serve[serve.index("--revision") + 1] == repro.load_protocol()["models"]["qwen3.5-27b"]["revision"]
    assert "--enforce-eager" not in serve and serve[serve.index("--max-num-seqs") + 1] == "256"


def _row(seed, rep, arm, verdict, rung="m2", model="glm-4.7"):
    return {"model": "zai.glm-4.7", "spec_key": model, "rung": rung, "arm": arm, "seed": seed,
            "rep": rep, "verdict": verdict}


def test_load_rows_dedupes_cells_and_keeps_rungs_apart(tmp_path):
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    a.write_text("\n".join(json.dumps(r) for r in [
        _row(1, 0, "lem", "success"), _row(1, 0, "both", "exception"), _row(1, 0, "both", "invalid_step"),
    ]) + "\n{torn")
    b.write_text("\n".join(json.dumps(r) for r in [
        _row(1, 0, "lem", "invalid_step"),  # duplicate of a's cell: the first read wins
        _row(1, 0, "lem", "success", rung="m6"),
    ]) + "\n")
    cells, dropped = load_rows([a, b])
    assert cells[("glm-4.7", "m2")]["lem"][1] == [True]
    assert cells[("glm-4.7", "m2")]["both"][1] == [False]
    assert cells[("glm-4.7", "m6")]["lem"][1] == [True]
    assert dropped == {"exception": 1, "unparsable": 1, "duplicate": 1}


def test_pass_rate_and_contrast_are_seed_paired():
    lem = {1: [True, True], 2: [True, False]}
    both = {1: [False, False], 2: [True, False], 3: [True, True]}
    assert pass_rate(lem) == 75.0
    mean, lo, hi, p, n = contrast(lem, both, random.Random(0))
    # differences 100 and 0: every sign flip has the same |mean|, so the exact p is 1
    assert (mean, n) == (50.0, 2) and lo <= mean <= hi and p == 1.0
    assert format_p(0.0, 100) == "p<5e-05" and format_p(0.5, 2) == "p=0.5000"


def test_report_compares_with_the_published_values(tmp_path):
    rows = tmp_path / "rows.jsonl"
    rows.write_text("\n".join(
        json.dumps(_row(s, 0, arm, "success" if arm == "lem" or s == 0 else "invalid_step", rung="m48"))
        for s in range(4) for arm in ARMS
    ) + "\n")
    text = repro.report([rows])
    assert "== glm-4.7 m48: 16 cells, 4 seeds" in text
    assert "published" in text and "74.0" in text  # the published lem rate


def test_lock_rows_refuses_a_second_writer_and_drops_a_torn_line(tmp_path):
    sweep = _load("sweep")
    out = tmp_path / "rows.jsonl"
    out.write_text('{"a": 1}\n{"b": ')
    fh = sweep.lock_rows(out)
    assert fh is not None
    assert out.read_text() == '{"a": 1}\n'
    assert sweep.lock_rows(out) is None  # the file stays intact while it is locked
    assert out.read_text() == '{"a": 1}\n'
    fh.close()


def test_demo_runs_end_to_end(tmp_path, capsys):
    demo = _load("demo")
    assert demo.main(["--out", str(tmp_path), "--m", "2", "--seeds", "0-1"]) == 0
    rows = [json.loads(x) for x in (tmp_path / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 2 * len(ARMS)
    assert {r["verdict"] for r in rows} == {"success"}
    assert "== oracle m2" in capsys.readouterr().out
