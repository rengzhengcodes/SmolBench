"""Offline tests for ``rebuttal/run_protocol.py`` against the shared OpenAI stub."""

# pylint: disable=redefined-outer-name,unused-argument  # fixtures are imported and requested by name

import argparse
import os
import sys
from datetime import datetime, timezone

import pytest

# The stub Bedrock server, the proof response and the test module's own copy of
# ``bedrock_trio`` are shared with test_bedrock_trio.py, which sits in this folder.
import test_bedrock_trio as tbt
from test_bedrock_trio import _final, _proof_response, fake_s3, mantle  # noqa: F401  # pylint: disable=unused-import
from tests._paths import REPO_ROOT, load_by_path
from conftest import StubTokenizer

bt = tbt.bt
NEMO = tbt.NEMO
PAST = "2020-01-01T00:00:00Z"
FUTURE = "2099-01-01T00:00:00Z"


@pytest.fixture
def rp(monkeypatch):
    """``run_protocol`` sharing this test suite's ``bedrock_trio``, so its monkeypatches apply."""
    monkeypatch.setitem(sys.modules, "bedrock_trio", bt)
    return load_by_path(REPO_ROOT / "rebuttal" / "run_protocol.py", "run_protocol_under_test")


@pytest.fixture
def cli(rp, mantle, tmp_path, monkeypatch):
    """The CLI pointed at the stub, with authentication and the probe replaced and results under ``tmp_path``."""
    calls = {"mint": 0, "bucket": [], "probe": 0}

    def mint_token(_region):
        # Like the real one: a token already in the environment is kept.
        calls["mint"] += 1
        if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
            monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "tok")
        return os.environ["AWS_BEARER_TOKEN_BEDROCK"]

    def pick_reasoning_args(model, _region):
        calls["probe"] += 1
        return {"reasoning_effort": "high"}, [{"args": {"reasoning_effort": "high"}, "model": model.key}]

    monkeypatch.setattr(bt, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(bt, "RUNGS_DIR", tmp_path / "rungs")
    monkeypatch.setattr(bt, "horn_m", lambda _key: 2)  # the rung the other tests render
    monkeypatch.setattr(bt, "mint_token", mint_token)
    monkeypatch.setattr(bt, "pick_reasoning_args", pick_reasoning_args)
    monkeypatch.setattr(bt, "check_bucket", calls["bucket"].append)
    # A token another session left behind must not survive: the CLI drops it and mints one.
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "stale")
    return rp, calls


def _posts(mantle):
    return [r for r in mantle.requests if r["path"].endswith("/chat/completions")]


@pytest.mark.parametrize(
    "text, seeds",
    [
        ("100-103", [100, 101, 102, 103]),
        ("100,105", [100, 105]),
        ("7", [7]),
        ("0-1, 5,1", [0, 1, 5]),
        ("3-3", [3]),
    ],
)
def test_parse_seeds(rp, text, seeds):
    assert rp.parse_seeds(text) == seeds


@pytest.mark.parametrize("text", ["", "a", "5-3", "-3", "3-", "1,,2", "1-2-3"])
def test_parse_seeds_rejects_malformed_lists(rp, text):
    with pytest.raises(argparse.ArgumentTypeError, match="seed"):
        rp.parse_seeds(text)


def test_parse_deadline_gives_an_aware_instant_and_rejects_a_naive_one(rp):
    assert rp.parse_deadline("2026-11-16T10:30:00Z") == datetime(2026, 11, 16, 10, 30, tzinfo=timezone.utc)
    assert rp.parse_deadline("2026-11-16T11:30:00+01:00") == datetime(2026, 11, 16, 10, 30, tzinfo=timezone.utc)
    with pytest.raises(argparse.ArgumentTypeError, match="no UTC offset"):
        rp.parse_deadline("2026-11-16T10:30:00")
    with pytest.raises(argparse.ArgumentTypeError, match="ISO 8601"):
        rp.parse_deadline("tomorrow")


def test_usage_errors_exit_with_1_not_the_stopped_code(rp, capsys):
    naive = ["horn", "--model", "x", "--deadline", "2026-11-16T10:30:00"]
    for argv in (naive, ["horn"], ["horn", "--model", "x", "--arms", "nope"]):
        with pytest.raises(SystemExit) as exit_:
            rp.main(argv)
        assert exit_.value.code == 1
    assert "no UTC offset" in capsys.readouterr().err


def test_defaults_are_the_protocol_and_smoke_switches_them(rp):
    def parse(*argv):
        return rp.resolve_defaults(rp.build_parser().parse_args(argv))

    ind, horn = parse("induction", "--model", "m"), parse("horn", "--model", "m")
    assert ind.seeds == list(range(30)) and ind.concurrency == 12 and not ind.smoke
    assert horn.seeds == list(range(100, 200)) and horn.reps == 3 and horn.arms == list(bt.HORN_ARMS)
    assert (horn.concurrency, horn.max_consecutive_failures, horn.push_every, horn.deadline) == (24, 8, 200, None)
    smoke_ind, smoke_horn = parse("induction", "--smoke", "--model", "m"), parse("horn", "--smoke", "--model", "m")
    assert smoke_ind.seeds == [0, 1]
    assert smoke_horn.seeds == [100, 101] and smoke_horn.reps == 1
    assert parse("horn", "--smoke", "--model", "m", "--seeds", "100", "--reps", "2").reps == 2


def test_horn_smoke_writes_one_row_per_replicate_under_the_smoke_folder(cli, mantle, tmp_path, capsys):
    rp, calls = cli
    _proof_response(mantle, tmp_path, reasoning="plan")
    code = rp.main(["horn", "--smoke", "--no-s3", "--model", NEMO.key, "--arms", "lem", "--seeds", "100",
                    "--reps", "2"])
    assert code == 0
    out = tmp_path / "results" / bt.SMOKE_PREFIX / "horn" / f"{NEMO.key}.jsonl"
    assert len(out.read_text().splitlines()) == 2 == len(_posts(mantle))
    assert not (tmp_path / "results" / "horn").exists(), "a smoke run stays out of the protocol folder"
    assert calls["mint"] == 1 and calls["probe"] == 1 and calls["bucket"] == [], "--no-s3 skips the bucket check"
    posted = _posts(mantle)[0]
    assert posted["headers"]["Authorization"] == "Bearer tok", "the stale token was replaced"
    assert posted["body"]["reasoning_effort"] == "high" and posted["body"]["model"] == NEMO.bedrock_id
    printed = capsys.readouterr().out
    assert "2 rows written by this call" in printed and "lem" in printed and "verdict:success" in printed
    assert f"{NEMO.key} horn: seeds 100 x 2 reps, arms lem" in printed and "deadline none" in printed


def test_induction_smoke_writes_the_released_layout_for_one_seed(cli, mantle, tmp_path, monkeypatch, capsys):
    rp, calls = cli
    monkeypatch.setattr(bt.load_run_study(), "for_model", lambda _model: StubTokenizer())
    mantle.default_response = _final("280", reasoning="2520 / 9")
    code = rp.main(["induction", "--smoke", "--no-s3", "--skip-prompt-check", "--model", NEMO.key, "--seeds", "0"])
    assert code == 0
    assert len(_posts(mantle)) == 36, "four arms x 9 questions"
    seed_dir = tmp_path / "results" / bt.SMOKE_PREFIX / "induction" / "induction" / NEMO.key / "seed=0"
    assert sorted(p.name.split("--")[0] for p in seed_dir.glob("*.yaml")) == sorted(bt.INDUCTION_ARMS)
    assert calls["mint"] == 1 and calls["bucket"] == []
    printed = capsys.readouterr().out
    assert "'unreasoned': 0" in printed and "extens" in printed


def test_s3_runs_check_the_bucket_with_the_prefix_of_the_run(cli, mantle, tmp_path, monkeypatch):
    rp, calls = cli
    seen = {}

    def fake_run_horn(model, region, reasoning, rung, seeds, reps, **kw):
        seen.update(model=model.key, region=region, reasoning=reasoning, seeds=seeds, reps=reps, **kw)
        return []

    monkeypatch.setattr(bt, "run_horn", fake_run_horn)
    monkeypatch.setattr(bt, "render_horn_rung", lambda m, seeds, rungs_dir, arms: tmp_path)
    argv = ["horn", "--model", NEMO.key, "--arms", "lem", "pad", "--seeds", "100-101", "--reps", "2",
            "--concurrency", "5", "--deadline", FUTURE, "--max-consecutive-failures", "3", "--push-every", "7",
            "--region", "us-west-2"]
    assert rp.main(argv + ["--smoke"]) == 0
    assert calls["bucket"] == [f"{bt.RESULTS_S3}/{bt.SMOKE_PREFIX}"]
    assert seen["s3_uri"] == calls["bucket"][0] and seen["region"] == "us-west-2"
    assert seen["out"] == tmp_path / "results" / bt.SMOKE_PREFIX / "horn" / f"{NEMO.key}.jsonl"
    assert (seen["seeds"], seen["reps"], list(seen["arms"])) == ([100, 101], 2, ["lem", "pad"])
    assert (seen["concurrency"], seen["max_consecutive_failures"], seen["push_every"]) == (5, 3, 7)
    assert seen["deadline"] == datetime(2099, 1, 1, tzinfo=timezone.utc)
    assert seen["reasoning"] == {"reasoning_effort": "high"}

    assert rp.main(argv) == 0, "without --smoke the protocol prefix and folder are used"
    assert calls["bucket"][-1] == bt.RESULTS_S3
    assert seen["out"] == tmp_path / "results" / "horn" / f"{NEMO.key}.jsonl"


def test_unknown_model_exits_nonzero_with_the_roster_and_sends_nothing(cli, mantle, capsys):
    rp, calls = cli
    assert rp.main(["horn", "--smoke", "--no-s3", "--model", "gpt-nope"]) != 0
    err = capsys.readouterr().err
    assert "unknown model 'gpt-nope'" in err and all(k in err for k in bt.TRIO)
    assert mantle.requests == [] and calls["mint"] == 0


def test_a_past_deadline_exits_zero_without_authenticating_or_sending(cli, mantle, tmp_path, capsys):
    rp, calls = cli
    _proof_response(mantle, tmp_path, reasoning="plan")
    code = rp.main(["horn", "--smoke", "--no-s3", "--model", NEMO.key, "--arms", "lem", "--seeds", "100",
                    "--deadline", PAST])
    assert code == 0 and mantle.requests == []
    assert calls["mint"] == calls["probe"] == 0
    assert "deadline has passed" in capsys.readouterr().out
    assert not (tmp_path / "results").exists()


def test_horn_run_stopped_exits_with_2_and_other_errors_with_1(cli, mantle, tmp_path, monkeypatch, caplog):
    rp, _ = cli
    monkeypatch.setattr(bt, "render_horn_rung", lambda m, seeds, rungs_dir, arms: tmp_path)
    argv = ["horn", "--smoke", "--no-s3", "--model", NEMO.key]

    def stopped(*_args, **_kw):
        raise bt.HornRunStopped("8 consecutive cells failed; last error: HTTPError: 401")

    monkeypatch.setattr(bt, "run_horn", stopped)
    assert rp.main(argv) == 2
    assert "8 consecutive cells failed" in caplog.text

    def broken(*_args, **_kw):
        raise RuntimeError("another sweep holds the lock")

    monkeypatch.setattr(bt, "run_horn", broken)
    assert rp.main(argv) == 1


def test_a_model_that_does_not_reason_ends_the_run_with_1_before_any_study(cli, mantle, monkeypatch, caplog):
    rp, _ = cli

    def no_reasoning(model, _region):
        raise RuntimeError(f"{model.key}: no reasoning candidate worked: []")

    monkeypatch.setattr(bt, "pick_reasoning_args", no_reasoning)
    monkeypatch.setattr(bt, "run_horn", lambda *a, **k: pytest.fail("the study must not run unreasoned"))
    assert rp.main(["horn", "--smoke", "--no-s3", "--model", NEMO.key]) == 1
    assert "no reasoning candidate worked" in caplog.text


def test_the_cli_drops_a_stale_token_and_uses_its_own(cli, mantle, tmp_path):
    rp, calls = cli
    _proof_response(mantle, tmp_path)
    assert rp.main(["horn", "--smoke", "--no-s3", "--model", NEMO.key, "--arms", "lem", "--seeds", "100"]) == 0
    assert calls["mint"] == 1
    assert {r["headers"]["Authorization"] for r in _posts(mantle)} == {"Bearer tok"}


def test_induction_checks_the_prompts_unless_told_to_skip(cli, mantle, monkeypatch):
    rp, _calls = cli
    rs = bt.load_run_study()
    monkeypatch.setattr(rs, "for_model", lambda _model: StubTokenizer())
    mantle.default_response = _final("280", reasoning="2520 / 9")
    checked = []
    monkeypatch.setattr(bt, "released_queries", lambda key, seed: {"released": (key, seed)})
    monkeypatch.setattr(bt, "check_induction_prompts",
                        lambda mine, released, tok: checked.append(released) or [{"added_lines": 1, "pad_tokens": 0}])
    args = ["induction", "--smoke", "--no-s3", "--model", NEMO.key, "--seeds", "0"]
    assert rp.main(args + ["--skip-prompt-check"]) == 0 and checked == []
    assert rp.main(args) == 0 and checked == [{"released": (NEMO.key, 0)}]


@pytest.mark.parametrize("bad", [["--concurrency", "0"], ["--push-every", "0"], ["--max-consecutive-failures", "-1"],
                                 ["--reps", "0"]])
def test_bad_numbers_are_usage_errors_before_any_billed_call(cli, mantle, bad):
    rp, calls = cli
    with pytest.raises(SystemExit) as err:
        rp.main(["horn", "--smoke", "--no-s3", "--model", NEMO.key] + bad)
    assert err.value.code == 1 and calls["mint"] == 0 and calls["probe"] == 0 and not _posts(mantle)


@pytest.mark.parametrize("text, indices", [("0,2", [0, 2]), ("1", [1]), (" 2, 0 ", [2, 0]), ("1,1", [1])])
def test_parse_rep_indices(rp, text, indices):
    assert rp.build_parser().parse_args(["horn", "--model", "m", "--rep-indices", text]).rep_indices == indices


@pytest.mark.parametrize("bad", [["--rep-indices", "a"], ["--rep-indices", "-1"], ["--rep-indices", ""],
                                 ["--rep-indices", "0,,2"], ["--rep-indices", "1.5"], ["--rep-indices", "3"],
                                 ["--rows-label", ""], ["--rows-label", "a/b"], ["--rows-label", "a b"],
                                 ["--ramp-start", "0"], ["--ramp-start", "x"], ["--ramp-minutes", "0"],
                                 ["--ramp-minutes", "-2"], ["--ramp-minutes", "nan"], ["--ramp-minutes", "inf"],
                                 ["--ramp-start", "9", "--concurrency", "8"]])
def test_bad_replicate_label_and_ramp_options_are_usage_errors_before_any_billed_call(cli, mantle, bad):
    rp, calls = cli
    with pytest.raises(SystemExit) as err:
        rp.main(["horn", "--smoke", "--no-s3", "--model", NEMO.key, "--reps", "3"] + bad)
    assert err.value.code == 1 and calls["mint"] == 0 and calls["probe"] == 0 and not _posts(mantle)


def test_replicate_label_and_ramp_options_reach_run_horn_and_the_start_line(cli, mantle, tmp_path, monkeypatch, capsys):
    rp, calls = cli
    seen = {}

    def fake_run_horn(model, region, reasoning, rung, seeds, reps, **kw):
        seen.update(region=region, reps=reps, **kw)
        return []

    monkeypatch.setattr(bt, "run_horn", fake_run_horn)
    monkeypatch.setattr(bt, "render_horn_rung", lambda m, seeds, rungs_dir, arms: tmp_path)
    base = ["horn", "--smoke", "--no-s3", "--model", NEMO.key, "--reps", "3", "--concurrency", "8"]
    assert rp.main(base) == 0
    assert (seen["rep_indices"], seen["ramp_start"], seen["ramp_minutes"]) == (None, None, 30)
    assert seen["out"] == tmp_path / "results" / bt.SMOKE_PREFIX / "horn" / f"{NEMO.key}.jsonl"
    assert "ramp none" in capsys.readouterr().out

    argv = base + ["--rep-indices", "0,2", "--rows-label", "east-1", "--ramp-start", "2", "--ramp-minutes", "0.5",
                   "--region", "us-east-1"]
    assert rp.main(argv) == 0
    assert (seen["rep_indices"], seen["ramp_start"], seen["ramp_minutes"]) == ([0, 2], 2, 0.5)
    assert seen["out"] == tmp_path / "results" / bt.SMOKE_PREFIX / "horn" / f"{NEMO.key}--east-1.jsonl"
    printed = capsys.readouterr().out
    assert ", rep indices 0,2, rows label east-1, ramp 2 doubling every 0.5 min to 8" in printed
    assert "ramp none" not in printed


def test_a_labelled_run_writes_its_own_file_and_the_summary_says_how_to_refresh_the_main_one(
    cli, mantle, fake_s3, tmp_path, capsys
):
    rp, calls = cli
    _proof_response(mantle, tmp_path, reasoning="plan")
    argv = ["horn", "--smoke", "--model", NEMO.key, "--arms", "lem", "--seeds", "100", "--reps", "3",
            "--rep-indices", "1", "--rows-label", "east-2"]
    assert rp.main(argv) == 0
    folder = tmp_path / "results" / bt.SMOKE_PREFIX / "horn"
    assert sorted(f.name for f in folder.iterdir()) == [f"{NEMO.key}--east-2.jsonl"], "the main file is not written"
    assert len(_posts(mantle)) == 1
    printed = capsys.readouterr().out
    assert "1 rows written by this call" in printed and "is a working copy" in printed
    assert f"{NEMO.key}.jsonl" in printed and "pull_horn_rows" in printed and bt.RESULTS_S3 in printed
    assert "lem: " in printed, "the counts come from the labelled file"

    # The printed command does what it says: it fills the main file with every row of the bucket.
    smoke_uri, smoke_dir = f"{bt.RESULTS_S3}/{bt.SMOKE_PREFIX}", tmp_path / "results" / bt.SMOKE_PREFIX
    assert bt.pull_horn_rows(NEMO.key, smoke_uri, results_dir=smoke_dir) == 1
    assert len((folder / f"{NEMO.key}.jsonl").read_text().splitlines()) == 1

    # Without a bucket nothing links the working copy to the main file, and the summary says that.
    assert rp.main(argv + ["--no-s3", "--rows-label", "local-only"]) == 0
    assert "nothing links it to" in capsys.readouterr().out
