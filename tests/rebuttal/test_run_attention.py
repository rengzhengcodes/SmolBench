"""Offline tests of the attention-replay command line (``rebuttal/run_attention.py``).

No AWS, no GPU, no network. The command line calls ``attention_replay`` through its module
attribute, so a test injects the fake box and the stub tokenizer by wrapping the module's
``replay_model`` and ``plan_replay``; the public functions take no test-only parameters
that the command line does not need. The fakes (box, S3, tokenizers) are the ones of
``test_attention_replay.py``.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tests._paths import REPO_ROOT, load_by_path

# Fakes and fixtures of the driver's own tests (tests/ has no packages, so load by path).
helpers = load_by_path(
    REPO_ROOT / "tests" / "rebuttal" / "test_attention_replay.py", "attention_replay_tests_for_cli"
)
ar = helpers.ar
GEMMA, DSV31 = helpers.GEMMA, helpers.DSV31
CLI_PATH = REPO_ROOT / "rebuttal" / "run_attention.py"
ENV_NAMES = ("EC2_S3_MODEL_CACHE", "EC2_S3_CACHE_REGION", "EC2_MAX_LIFETIME_MIN")


@pytest.fixture
def cli(monkeypatch):
    """The command-line module, sharing ``ar`` with the helpers (one copy of the driver).

    ``snapshot_env`` keeps the module's ``EC2_*`` defaults from leaking into the pytest process.
    """
    monkeypatch.setitem(sys.modules, "attention_replay", ar)
    return load_by_path(CLI_PATH, "run_attention_under_test", snapshot_env=True)


def _root(tmp_path: Path, model: str = GEMMA) -> Path:
    """A results root laid out like the default one: ``<tmp>/results/induction``."""
    root = tmp_path / "results" / "induction"
    helpers._write_results(root, model)
    return root


def _inject(monkeypatch, cli, box, s3, model: str = GEMMA) -> dict:
    """Wrap the driver's entry points so the command line runs against the fakes.

    Returns the keyword arguments the command line passed to ``replay_model`` (empty until
    it is called).
    """
    seen: dict = {}
    real_replay, real_plan = ar.replay_model, ar.plan_replay
    if model == GEMMA:
        stubs = helpers._gemma_plan_kwargs()
    else:
        stubs = dict(tokenizer_for=lambda m: helpers.CharTokenizer(helpers.DS_SPECIALS),
                     template_for=lambda m: helpers.ds_template(),
                     config_for=lambda m: {"num_hidden_layers": 2, "num_attention_heads": 4})

    def replay(model_key, results_root, s3_uri, **kw):
        seen.update(kw, model_key=model_key, results_root=results_root, s3_uri=s3_uri)
        return real_replay(model_key, results_root, s3_uri, ec2=box, s3_client_factory=lambda: s3,
                           poll_s=0, **stubs, **kw)

    def plan(results_root, models, **kw):
        seen["plan_kwargs"] = dict(kw, results_root=results_root, models=models)
        return real_plan(results_root, models, **stubs, **kw)

    monkeypatch.setattr(cli.ar, "replay_model", replay)
    monkeypatch.setattr(cli.ar, "plan_replay", plan)
    return seen


def _reports(directory: Path) -> list:
    return sorted(directory.glob("attention_report--*.json")) if directory.is_dir() else []


# ------------------------------------------------------------------------ seed parsing

@pytest.mark.parametrize("text, expected", [
    ("0-9", list(range(10))), ("3", [3]), ("0,2,5-7", [0, 2, 5, 6, 7]),
    ("7,2,2,4-5", [2, 4, 5, 7]), ("4-4", [4]), (" 1-2", [1, 2]),
])
def test_parse_seeds(cli, text, expected) -> None:
    assert cli.parse_seeds(text) == expected


@pytest.mark.parametrize("text", ["", "a", "1-", "-3", "5-2", "1,,2", "1.5", "0-9-12"])
def test_parse_seeds_refuses_a_bad_selection(cli, text) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        cli.parse_seeds(text)


def test_a_bad_seed_range_exits_with_the_argparse_code(cli, capsys) -> None:
    with pytest.raises(SystemExit) as caught:
        cli.main(["--model", GEMMA, "--seeds", "5-2"])
    assert caught.value.code == 2 and "end is below start" in capsys.readouterr().err


# ---------------------------------------------------------------- environment defaults

def _env_probe(env: dict) -> dict:
    """Load the command line in a clean interpreter and report what the provider read.

    The provider reads its environment when it is imported, so only a fresh process can
    show the order. AWS and network calls are made to raise first, which also proves the
    module imports without touching either.
    """
    script = textwrap.dedent(f"""
        import importlib.util, json, socket, sys
        sys.path[:0] = [{str(REPO_ROOT)!r}]

        def refuse(*a, **k):
            raise AssertionError("network or AWS touched at import")

        socket.socket.connect = refuse
        socket.getaddrinfo = refuse
        import botocore.client
        botocore.client.ClientCreator.create_client = refuse
        assert "smolbench.evals.providers" not in sys.modules
        spec = importlib.util.spec_from_file_location("run_attention_probe", {str(CLI_PATH)!r})
        module = importlib.util.module_from_spec(spec)
        sys.modules["run_attention_probe"] = module
        spec.loader.exec_module(module)
        from smolbench.evals.providers import ec2
        print(json.dumps({{"cache": ec2.EC2_S3_MODEL_CACHE, "region": ec2.EC2_S3_CACHE_REGION,
                           "life": ec2.EC2_MAX_LIFETIME_MIN}}))
    """)
    clean = {k: v for k, v in os.environ.items() if k not in ENV_NAMES}
    done = subprocess.run([sys.executable, "-I", "-c", script], env={**clean, **env},
                          capture_output=True, text=True, cwd=REPO_ROOT.parent, timeout=300)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_the_provider_environment_defaults_are_set_before_the_provider_is_imported() -> None:
    assert _env_probe({}) == {
        "cache": "s3://smolbench-model-cache-414266451290/hf", "region": "us-west-2", "life": 240,
    }


def test_the_provider_environment_defaults_do_not_override_what_the_caller_set() -> None:
    mine = {"EC2_S3_MODEL_CACHE": "s3://mine/cache", "EC2_MAX_LIFETIME_MIN": "60"}
    # Only the variable the caller left unset takes the default.
    assert _env_probe(mine) == {"cache": "s3://mine/cache", "region": "us-west-2", "life": 60}


# ------------------------------------------------------------------ defaults and plan

def test_default_locations_follow_the_notebook(cli) -> None:
    bt = ar.bt
    assert cli.default_locations(False) == (
        bt.RESULTS_DIR / "induction", f"{bt.RESULTS_S3}/attention-v2")
    assert cli.default_locations(True) == (
        bt.RESULTS_DIR / bt.SMOKE_PREFIX / "induction",
        f"{bt.RESULTS_S3}/{bt.SMOKE_PREFIX}/attention-v2")


def test_without_approved_the_plan_is_printed_and_nothing_is_built(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    box, s3 = helpers.AuditedBox(helpers.FakeS3()), helpers.FakeS3()
    seen = _inject(monkeypatch, cli, box, s3)

    def never(*a, **k):
        raise AssertionError("an AWS client was built without --approved")

    monkeypatch.setattr(ar, "_default_s3_factory", never)
    monkeypatch.setattr("boto3.session.Session", never)
    monkeypatch.setattr(ar, "replay_model", never)  # the injected wrapper would reach it too
    code = cli.main(["--model", GEMMA, "--results-root", str(root), "--seeds", "0-1",
                     "--report-dir", str(tmp_path / "reports")])
    out = capsys.readouterr().out
    assert code == 0 and box.calls == []
    assert f"{GEMMA}: 2 runs, 3 marks -> 3 jobs" in out and "plan only" in out
    # The plan got the same arguments the run would: seeds, root and the default destination.
    assert seen["plan_kwargs"]["seeds"] == [0, 1] and seen["plan_kwargs"]["results_root"] == root
    assert seen["plan_kwargs"]["s3_uri"] == cli.default_locations(False)[1]
    assert not (tmp_path / "reports").exists()


def test_the_plan_lists_its_errors(cli, tmp_path, monkeypatch, capsys) -> None:
    root = tmp_path / "results" / "induction"
    # A related_intens run with no intens run of its seed cannot be planned: an error, not a job.
    helpers._write_related_results(root, DSV31, intens=False)
    _inject(monkeypatch, cli, helpers.AuditedBox(helpers.FakeS3()), helpers.FakeS3(), DSV31)
    assert cli.main(["--model", DSV31, "--results-root", str(root)]) == 0
    out = capsys.readouterr().out
    assert "  error: " in out and "no intens run for seed 0" in out


def test_an_unknown_model_exits_1_with_a_message(cli, tmp_path, capsys) -> None:
    assert cli.main(["--model", "no-such-model", "--results-root", str(tmp_path)]) == 1
    assert "no-such-model" in capsys.readouterr().err


# --------------------------------------------------------------------------- the run

def test_approved_runs_against_the_fake_box_and_writes_the_report(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    s3 = helpers.FakeS3()
    box = helpers.AuditedBox(s3)
    seen = _inject(monkeypatch, cli, box, s3)
    # No --report-dir: the report goes to the results folder next to the mirror.
    code = cli.main(["--model", GEMMA, "--results-root", str(root), "--seeds", "0", "--approved",
                     "--instance-types", "p5.48xlarge"])
    out = capsys.readouterr().out
    assert code == 0
    assert seen["approved"] is True and seen["allow_unverified_serve"] is False
    assert seen["seeds"] == [0] and seen["audit_arrays"] == "all"
    assert seen["instance_types"] == ["p5.48xlarge"]
    assert seen["batch_timeout_s"] == 2400 and seen["url_ttl_s"] == 3600
    assert seen["s3_uri"] == cli.default_locations(False)[1] and seen["results_root"] == root
    assert f"{GEMMA}: 3 verified, 0 failed, 0 failed the audit, 0 already stored, 0 partial, 2 manifests" in out
    assert "arm intens: 0 over the" in out and "arm noise_intens: 0 over the" in out
    (path,) = _reports(tmp_path / "results")
    assert path.name.startswith(f"attention_report--{GEMMA}--")
    saved = json.loads(path.read_text())
    assert len(saved["verified"]) == 3 and len(saved["manifests"]) == 2 and saved["plan"]["jobs"] == 3
    assert box.calls[-1] == "shutdown"


def test_the_report_dir_flag_and_smoke_defaults(cli, tmp_path, monkeypatch, capsys) -> None:
    s3 = helpers.FakeS3()
    seen = _inject(monkeypatch, cli, helpers.AuditedBox(s3), s3)
    root = _root(tmp_path)
    assert cli.main(["--model", GEMMA, "--results-root", str(root), "--approved", "--smoke",
                     "--report-dir", str(tmp_path / "out")]) == 0
    assert len(_reports(tmp_path / "out")) == 1 and not _reports(tmp_path / "results")
    assert seen["s3_uri"] == cli.default_locations(True)[1] and "smoke" in seen["s3_uri"]
    capsys.readouterr()


def test_failed_jobs_exit_3_and_the_report_is_written(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    s3 = helpers.FakeS3()

    class WrongClassesBox(helpers.AuditedBox):
        def attn_start(self, state, payload):
            for line in payload["jobs"]:
                line["classes"] = [0] * (len(line["classes"]) - 1) + [3]
            return super().attn_start(state, payload)

    _inject(monkeypatch, cli, WrongClassesBox(s3), s3)
    code = cli.main(["--model", GEMMA, "--results-root", str(root), "--approved"])
    out = capsys.readouterr().out
    assert code == 3 and "failed the audit" in out
    (path,) = _reports(tmp_path / "results")
    assert json.loads(path.read_text())["audit_failures"]


def test_an_exception_exits_1_without_a_report_and_the_box_is_down(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    s3 = helpers.FakeS3()
    box = helpers.AuditedBox(s3, fail_attn=True)
    _inject(monkeypatch, cli, box, s3)
    code = cli.main(["--model", GEMMA, "--results-root", str(root), "--approved"])
    assert code == 1 and "box unreachable" in capsys.readouterr().err
    assert box.calls[-1] == "shutdown" and not _reports(tmp_path / "results")


def test_a_shutdown_failure_exits_4_after_writing_the_report(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    s3 = helpers.FakeS3()
    box = helpers.ShutdownBox(s3, shutdown_script=[RuntimeError("TerminateInstances denied")])
    _inject(monkeypatch, cli, box, s3)
    code = cli.main(["--model", GEMMA, "--results-root", str(root), "--approved"])
    captured = capsys.readouterr()
    assert code == 4 and "TerminateInstances denied" in captured.err
    assert "3 verified" in captured.out
    (path,) = _reports(tmp_path / "results")
    assert len(json.loads(path.read_text())["verified"]) == 3


def test_a_shutdown_failure_still_exits_4_when_the_report_cannot_be_written(
        cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    s3 = helpers.FakeS3()
    box = helpers.ShutdownBox(s3, shutdown_script=[RuntimeError("TerminateInstances denied")])
    _inject(monkeypatch, cli, box, s3)
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("")  # a file where the report folder should be
    code = cli.main(["--model", GEMMA, "--results-root", str(root), "--approved",
                     "--report-dir", str(blocker)])
    assert code == 4 and "could not be written" in capsys.readouterr().err


def test_an_unverified_serve_is_refused_unless_the_flag_is_given(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path, DSV31)
    s3 = helpers.FakeS3()
    box = helpers.AuditedBox(s3)
    seen = _inject(monkeypatch, cli, box, s3, DSV31)
    assert cli.main(["--model", DSV31, "--results-root", str(root), "--approved"]) == 1
    assert "ServeUnverified" in capsys.readouterr().err
    assert box.calls == [] and seen["allow_unverified_serve"] is False
    assert cli.main(["--model", DSV31, "--results-root", str(root), "--approved",
                     "--allow-unverified-serve"]) == 0
    assert seen["allow_unverified_serve"] is True
    assert box.calls[-1] == "shutdown"
    capsys.readouterr()


# ------------------------------------------------------------------- --audit-only

no_ec2 = helpers.no_ec2  # the fixture of the driver's tests: any EC2 or real-AWS call fails


def _inject_audit(monkeypatch, cli, s3) -> dict:
    """Wrap ``audit_existing`` so the command line runs against the fake S3 and the stub tokenizer.

    Also makes ``replay_model`` and ``plan_replay`` fail the test: ``--audit-only`` must reach
    neither. Returns the keyword arguments the command line passed to ``audit_existing``.
    """
    seen: dict = {}
    real_audit = ar.audit_existing
    stubs = helpers._gemma_plan_kwargs()

    def audit(model_key, results_root, s3_uri, **kw):
        seen.update(kw, model_key=model_key, results_root=results_root, s3_uri=s3_uri)
        return real_audit(model_key, results_root, s3_uri, s3_client_factory=lambda: s3, **stubs, **kw)

    def never(*a, **k):
        raise AssertionError("--audit-only reached the capture path")

    monkeypatch.setattr(cli.ar, "audit_existing", audit)
    monkeypatch.setattr(cli.ar, "replay_model", never)
    monkeypatch.setattr(cli.ar, "plan_replay", never)
    return seen


def _audit_reports(directory: Path) -> list:
    return sorted(directory.glob("attention_audit--*.json")) if directory.is_dir() else []


def _jobs_at_default_destination(cli, root: Path):
    """The planned jobs, keyed under the command line's default destination."""
    _bucket, prefix = ar.parse_s3_uri(cli.default_locations(False)[1])
    planned, errors = ar.build_jobs(GEMMA, root, prefix, tokenizer=helpers.CharTokenizer(helpers.GEMMA_SPECIALS),
                                    template=helpers.gemma_template())
    assert not errors
    return [p.job for p in planned]


def _stored(cli, root: Path):
    """Three captures stored in a fake bucket with no manifest (the audit never ran)."""
    jobs = _jobs_at_default_destination(cli, root)
    s3 = helpers.FakeS3()
    for job in jobs:
        helpers._store_capture(s3, job)
    return s3, jobs


@pytest.mark.usefixtures("no_ec2")
@pytest.mark.parametrize("extra", [[], ["--approved"]])
def test_audit_only_audits_the_stored_captures_and_launches_nothing(
        cli, tmp_path, monkeypatch, capsys, extra) -> None:
    root = _root(tmp_path)
    s3, jobs = _stored(cli, root)
    seen = _inject_audit(monkeypatch, cli, s3)
    code = cli.main(["--model", GEMMA, "--results-root", str(root), "--audit-only", *extra])
    out = capsys.readouterr().out
    assert code == 0
    assert f"{GEMMA}: 3 verified, 0 failed, 0 failed the audit, 0 already stored, 0 partial, 2 manifests" in out
    # Defaults: every array, 8 workers, every seed, the notebook's destination.
    assert seen["arrays"] == "all" and seen["workers"] == 8 and seen["seeds"] is None
    assert seen["s3_uri"] == cli.default_locations(False)[1] and seen["results_root"] == root
    # The report goes to the results folder, under a name that says "audit".
    (path,) = _audit_reports(tmp_path / "results")
    assert path.name.startswith(f"attention_audit--{GEMMA}--") and not _reports(tmp_path / "results")
    saved = json.loads(path.read_text())
    assert len(saved["verified"]) == 3 and len(saved["manifests"]) == 2 and saved["instance_type"] is None
    assert sum("manifest--" in k for k in s3.objects) == 2


@pytest.mark.usefixtures("no_ec2")
def test_audit_only_passes_its_options_through(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    s3, _jobs = _stored(cli, root)
    seen = _inject_audit(monkeypatch, cli, s3)
    assert cli.main(["--model", GEMMA, "--results-root", str(root), "--audit-only", "--seeds", "0",
                     "--audit-arrays", "sample", "--audit-workers", "3", "--smoke",
                     "--report-dir", str(tmp_path / "out")]) == 0
    assert seen["seeds"] == [0] and seen["arrays"] == "sample" and seen["workers"] == 3
    assert "smoke" in seen["s3_uri"] and len(_audit_reports(tmp_path / "out")) == 1
    capsys.readouterr()


@pytest.mark.usefixtures("no_ec2")
def test_audit_only_exits_3_when_a_capture_fails_the_audit(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    jobs = _jobs_at_default_destination(cli, root)
    s3 = helpers.FakeS3()
    helpers._store_capture(s3, jobs[0])
    helpers._store_capture(s3, jobs[1], meta_over={0: {"n_tokens": 999}})
    helpers._store_capture(s3, jobs[2])
    _inject_audit(monkeypatch, cli, s3)
    code = cli.main(["--model", GEMMA, "--results-root", str(root), "--audit-only"])
    out = capsys.readouterr().out
    assert code == 3 and "1 failed the audit" in out and jobs[1].job_id in out
    (path,) = _audit_reports(tmp_path / "results")
    assert list(json.loads(path.read_text())["audit_failures"]) == [jobs[1].job_id]


@pytest.mark.usefixtures("no_ec2")
def test_audit_only_exits_0_when_there_is_nothing_to_audit(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    s3 = helpers.FakeS3()  # nothing captured at all
    _inject_audit(monkeypatch, cli, s3)
    assert cli.main(["--model", GEMMA, "--results-root", str(root), "--audit-only"]) == 0
    assert "3 planned job(s) have no capture" in capsys.readouterr().out
    (path,) = _audit_reports(tmp_path / "results")
    assert json.loads(path.read_text())["not_captured"] == 3 and not s3.puts


@pytest.mark.usefixtures("no_ec2")
def test_audit_only_exits_1_on_an_exception_without_a_report(cli, tmp_path, monkeypatch, capsys) -> None:
    root = _root(tmp_path)
    _inject_audit(monkeypatch, cli, helpers.FakeS3())
    monkeypatch.setattr(cli.ar, "audit_existing", lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("S3 unreachable")))
    assert cli.main(["--model", GEMMA, "--results-root", str(root), "--audit-only"]) == 1
    assert "S3 unreachable" in capsys.readouterr().err and not _audit_reports(tmp_path / "results")


@pytest.mark.parametrize("value", ["0", "-1", "x", "1.5"])
def test_a_bad_audit_worker_count_exits_with_the_argparse_code(cli, capsys, value) -> None:
    with pytest.raises(SystemExit) as caught:
        cli.main(["--model", GEMMA, "--audit-workers", value])
    assert caught.value.code == 2 and "--audit-workers" in capsys.readouterr().err


@pytest.mark.parametrize("extra, expected", [([], 8), (["--audit-workers", "2"], 2)])
def test_the_capture_path_passes_the_audit_worker_count(
        cli, tmp_path, monkeypatch, capsys, extra, expected) -> None:
    root = _root(tmp_path)
    s3 = helpers.FakeS3()
    seen = _inject(monkeypatch, cli, helpers.AuditedBox(s3), s3)
    assert cli.main(["--model", GEMMA, "--results-root", str(root), "--approved", *extra]) == 0
    assert seen["audit_workers"] == expected
    capsys.readouterr()
