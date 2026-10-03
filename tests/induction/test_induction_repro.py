"""Reproduction of the induction table (``induction.repro``, ``induction_results.py``)."""

from __future__ import annotations

import importlib.util
import io
import json
import sys

import pytest
import yaml

from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS
from smolbench.induction import repro
from tests._paths import NOTEBOOKS

ANALYSIS = NOTEBOOKS / "induction" / "analysis"
ARMS = ("intens", "noise_intens", "extens")
STAMP = "20260811T065805Z"
LATER = "20260901T000000Z"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ANALYSIS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write(data, model, seed, arm, correct, stamp=STAMP, null=0):
    path = data / "induction" / model / f"seed={seed}" / f"{arm}--{stamp}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    scores = [1] * correct + [None] * null + [0] * (9 - correct - null)
    path.write_text(
        yaml.safe_dump(
            {
                "model": model,
                "date": "2026-08-11",
                "marks": [{"score": s} for s in scores],
            }
        )
    )
    return path


@pytest.fixture()
def data(tmp_path):
    """Two models x 3 seeds x 4 arms; gemma-4-e2b seed 0 intens re-collected twice."""
    correct = {"intens": 9, "noise_intens": 6, "extens": 3, "zero": 0}
    for model in ("gemma-4-e2b", "glm-4.7"):
        for seed in range(3):
            for arm, k in correct.items():
                _write(tmp_path, model, seed, arm, k - seed if arm != "zero" else 0)
    _write(tmp_path, "gemma-4-e2b", 0, "intens", 0, stamp="20260101T000000Z")
    stale = (
        tmp_path
        / "induction"
        / "gemma-4-e2b"
        / "seed=0"
        / "intens--20260101T000000Z.superseded"
    )
    stale.write_text("{}")
    _write(tmp_path, "gemma-4-e2b", 0, "intens", 1, stamp=LATER)
    return tmp_path


def test_protocol_record_is_complete():
    """The protocol pins every model's checkpoint, its published deltas and 30 digests."""
    proto = repro.load_protocol()
    assert proto["arms"] == list(ARMS) and repro.parse_seeds(proto["seeds"]) == list(
        range(30)
    )
    assert len(proto["models"]) == 16 and list(proto["seed_digests"]) == list(
        proto["models"]
    )
    for key, e in proto["models"].items():
        args = EC2_DEPLOY_SPECS[key]["vllm_args"]
        assert e["hf_model_id"] == EC2_DEPLOY_SPECS[key]["hf_model_id"], key
        assert e["revision"] == args[args.index("--revision") + 1], key
        r = e["results"]
        for a, b in repro.DELTAS:
            assert (
                f"{repro.delta(r[a]['mean'], r[b]['mean']):.1f}"
                == f"{r[f'{a}-{b}']:.1f}"
            ), key
        assert sorted(map(int, proto["seed_digests"][key])) == list(range(30))


def test_parse_seeds_mixes_ranges_and_numbers():
    """Seed lists mix ranges and single seeds."""
    assert repro.parse_seeds("0-2,7") == [0, 1, 2, 7]


def test_select_runs_keeps_the_earliest_surviving_run(data):
    """Superseded runs and the zero arm are skipped; the earliest run wins."""
    runs = repro.select_runs(data, ARMS)
    assert len(runs) == 2 * 3 * 3
    assert runs["gemma-4-e2b", 0, "intens"].name == f"intens--{STAMP}.yaml"
    assert not any(arm == "zero" for *_, arm in runs)


def test_accuracy_counts_null_as_wrong(tmp_path):
    """A null score is wrong, and a short replicate is refused."""
    assert (
        repro.replicate_accuracy(_write(tmp_path, "m", 0, "intens", 4, null=2)) == 4 / 9
    )
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump({"marks": [{"score": 1}]}))
    with pytest.raises(ValueError, match="1 marks, expected 9"):
        repro.replicate_accuracy(bad)


def test_cells_and_deltas(data):
    """Cells hold per-seed accuracy; deltas use the printed means."""
    cells = repro.load_cells(data)
    assert cells["glm-4.7", "extens"] == {0: 3 / 9, 1: 2 / 9, 2: 1 / 9}
    mean, sd = repro.cell_stats(cells["glm-4.7", "intens"])
    assert mean == pytest.approx(8 / 9) and sd == pytest.approx(1 / 9)
    assert repro.delta(0.9484, 0.1151) == pytest.approx(83.3)


def test_check_data_finds_changed_and_missing_runs(data, monkeypatch):
    """check-data reports changed and missing replicates."""
    runs = repro.select_runs(data, ARMS)
    digests = {
        "glm-4.7": {
            str(s): repro.seed_digest({a: runs["glm-4.7", s, a] for a in ARMS})
            for s in range(3)
        }
    }
    proto = dict(repro.load_protocol(), seed_digests=digests)
    monkeypatch.setattr(repro, "load_protocol", lambda: proto)
    assert not repro.check_data(data)
    _write(data, "glm-4.7", 1, "extens", 9)
    (data / "induction" / "glm-4.7" / "seed=2" / f"noise_intens--{STAMP}.yaml").unlink()
    assert repro.check_data(data) == [
        "glm-4.7/seed=1: digest differs from the published runs",
        "glm-4.7/seed=2: missing noise_intens",
    ]


def test_report_prints_published_values(data):
    """The report lists models in ladder order beside the published values."""
    text = repro.report(data)
    assert text.index("== gemma-4-e2b") < text.index("== glm-4.7")
    assert "0.948  0.100" in text and "+83.3" in text


class _FakeS3:
    """An S3 client over an in-memory ``{key: bytes}`` bucket."""

    def __init__(self, objects):
        self.objects = objects
        self.gets = []

    def get_paginator(self, _name):
        """Return a paginator yielding every object under the prefix in one page."""
        objects = self.objects

        class _Pages:
            @staticmethod
            def paginate(Bucket, Prefix):  # pylint: disable=invalid-name
                """Yield one page of the objects under ``Prefix``."""
                del Bucket
                yield {
                    "Contents": [
                        {"Key": k, "Size": len(v)}
                        for k, v in objects.items()
                        if k.startswith(Prefix)
                    ]
                }

        return _Pages()

    def get_object(self, Bucket, Key):  # pylint: disable=invalid-name
        """Return the object's body and record the request."""
        del Bucket
        self.gets.append(Key)
        return {"Body": io.BytesIO(self.objects[Key])}


def test_fetch_keeps_the_layout_and_resumes(tmp_path):
    """fetch keeps the key layout below the prefix and skips files it has."""
    client = _FakeS3(
        {"runs/induction/m/seed=0/intens--x.yaml": b"abc", "runs/other/k": b"no"}
    )
    assert repro.fetch(tmp_path, "b", "runs", client) == (1, 0)
    assert (
        tmp_path / "induction" / "m" / "seed=0" / "intens--x.yaml"
    ).read_bytes() == b"abc"
    assert repro.fetch(tmp_path, "b", "runs", client) == (0, 1)
    assert client.gets == ["runs/induction/m/seed=0/intens--x.yaml"]


def test_results_script_writes_the_tables(data, tmp_path, capsys):
    """The table script checks the data, then writes the tables and summary."""
    mod = _load("induction_results")
    out = tmp_path / "out"
    assert mod.main(["--data", str(data), "--out", str(out)]) == 1
    assert "pass --skip-check" in capsys.readouterr().out
    assert mod.main(["--data", str(data), "--out", str(out), "--skip-check"]) == 0
    tex = (out / "induction_table.tex").read_text(encoding="utf-8")
    assert r"\label{tab:induction-results}" in tex and "over 3 seeds" in tex
    assert tex.count(r"\addlinespace") == 1
    assert r"Gemma4 E2B-it & $\mathbf{0.889 \pm 0.111}$ &" in tex
    summary = json.loads((out / "induction_summary.json").read_text(encoding="utf-8"))
    assert list(summary["models"]) == ["gemma-4-e2b", "glm-4.7"]
    assert summary["models"]["glm-4.7"]["deltas"]["intens-extens"] == pytest.approx(
        66.7
    )
    assert "0 of 16 cells match" in capsys.readouterr().out


def test_results_script_formats_spreads_and_negative_deltas():
    """Spreads and negative deltas are formatted as published."""
    mod = _load("induction_results")
    assert mod.spread_of(0.1, 30, "ci") == pytest.approx(2.045 * 0.1 / 30**0.5)
    assert mod.spread_of(0.1, 30, "2sd") == pytest.approx(0.2)
    with pytest.raises(ValueError, match="no 95% t quantile"):
        mod.spread_of(0.1, 4, "ci")
    assert mod.fmt_delta(-0.4) == "$-0.4$" and mod.fmt_delta(3.0) == "3.0"
