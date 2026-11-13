"""The control agent's ``/attn`` capture endpoint and ``/serve``'s env/files, offline.

The agent asset is executed by path
inside a subprocess (it reads required env vars at import, and the capture loop
patches ``urllib.request.urlopen``, which must never touch the pytest process),
and each scenario prints its observations as JSON.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from smolbench.evals.payloads import AGENT_PY

DRIVER = r'''
import importlib.util, json, os, sys, threading, time

spec = importlib.util.spec_from_file_location("agent", os.environ["AGENT_PATH"])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

TMP = os.environ["TMP_DIR"]
mod.HF_CACHE = os.path.join(TMP, "hf-cache")
mod.ATTN_DIR = os.path.join(mod.HF_CACHE, "attn")
mod.SERVE_LOG = os.path.join(TMP, "serve.log")
mod.touch = lambda name: None

DONE = os.path.join(mod.ATTN_DIR, "done")
CURRENT = os.path.join(mod.ATTN_DIR, "current.json")

docker_calls = []
class R:
    def __init__(self, out="", rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc
def fake_docker(*args, timeout=120):
    docker_calls.append(list(args))
    if args[0] == "inspect":
        return R("absent\n", rc=1)
    return R()
mod.docker = fake_docker

launched = []
class FakePopen:
    def __init__(self, cmd, stdout=None, stderr=None):
        # Recorded at construction: /serve must stage `files` BEFORE docker runs.
        launched.append({"cmd": cmd, "files_present": sorted(
            os.path.join(dirpath, f)[len(mod.HF_CACHE) + 1:]
            for dirpath, _dirs, files in os.walk(mod.HF_CACHE) for f in files)})
    def poll(self):
        return 0
mod.subprocess.Popen = FakePopen

def handler():
    h = mod.Handler.__new__(mod.Handler)
    h.replies = []
    h.states = []
    def reply(code, body):
        h.replies.append([code, body])
        h.states.append(json.loads(json.dumps(mod.ATTN)))
    h._reply = reply
    h._authed = lambda: True
    return h

def write_done(job_id, rank, body):
    os.makedirs(DONE, exist_ok=True)
    with open(os.path.join(DONE, "%s.r%d.json" % (job_id, rank)), "w") as fh:
        json.dump(body, fh)

def read_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None

requests_seen = []

def urlopen_ok(req, timeout=None):
    """Stand in for the local vLLM: record the request, then let every rank finish."""
    requests_seen.append({
        "url": req.full_url, "headers": dict(req.headers),
        "body": json.loads(req.data.decode()), "timeout": timeout,
        "current": read_json(CURRENT),
    })
    body = json.loads(req.data.decode())
    job_id = read_json(CURRENT)["job_id"]
    for rank in range(int(os.environ.get("TP", "2"))):
        write_done(job_id, rank, {"ok": True, "error": None, "gate_max_rel": 0.001 * (rank + 1),
                                  "bytes": 1234, "uploaded": True, "http_status": [200, 200],
                                  "seq": read_json(CURRENT)["seq"], "rank": rank})
    class Resp:
        def __enter__(self_inner):
            return self_inner
        def __exit__(self_inner, *a):
            return False
        def read(self_inner):
            return b"{}"
    return Resp()

JOBS = [
    {"job_id": "q0", "prompt_token_ids": [1, 2, 3], "completion_token_ids": [4, 5],
     "positions": [3, 4], "put_urls": ["u0r0", "u0r1"], "meta_put_urls": ["m0r0", "m0r1"]},
    {"job_id": "q1", "prompt_token_ids": [9], "completion_token_ids": [8],
     "positions": [1], "put_urls": ["u1r0", "u1r1"], "meta_put_urls": ["m1r0", "m1r1"]},
]


MASS_JOB = {
    "job_id": "q7", "prompt_token_ids": [1, 2, 3, 4], "completion_token_ids": [5, 6],
    "positions": [5], "put_urls": ["u7r0", "u7r1"], "meta_put_urls": ["m7r0", "m7r1"],
    "mode": "mass", "query_start": 4, "classes": [0, 1, 1, 2, 3, 3],
}


def join():
    if mod.ATTN_THREAD is not None:
        mod.ATTN_THREAD.join(timeout=30)


def scenario_happy():
    mod.urllib.request.urlopen = urlopen_ok
    h = handler()
    h._attn({"served_model_name": "demo", "tp": 2, "jobs": JOBS})
    at_reply = h.states[0]
    join()
    return {"replies": h.replies, "at_reply": at_reply, "final": mod.ATTN,
            "requests": requests_seen, "current_left": os.path.exists(CURRENT)}


def scenario_stale_done_is_cleared():
    """A previous serve's done files must not be read as this job's result."""
    for rank in (0, 1):
        write_done("q0", rank, {"ok": True, "error": None, "gate_max_rel": 9.9, "stale": True})
    mod.ATTN_WAIT_S = 0.2
    mod.time.sleep = lambda s: None

    def urlopen_silent(req, timeout=None):
        class Resp:
            def __enter__(self_inner):
                return self_inner
            def __exit__(self_inner, *a):
                return False
            def read(self_inner):
                return b"{}"
        return Resp()

    mod.urllib.request.urlopen = urlopen_silent
    h = handler()
    h._attn({"served_model_name": "demo", "tp": 2, "jobs": JOBS[:1]})
    join()
    return {"final": mod.ATTN}


def scenario_job_failure_continues():
    calls = {"n": 0}

    def urlopen_flaky(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("vLLM said no")
        return urlopen_ok(req, timeout=timeout)

    mod.urllib.request.urlopen = urlopen_flaky
    h = handler()
    h._attn({"served_model_name": "demo", "tp": 2, "jobs": JOBS})
    join()
    return {"final": mod.ATTN}


def scenario_conflict():
    gate = threading.Event()

    def urlopen_block(req, timeout=None):
        gate.wait(20)
        return urlopen_ok(req, timeout=timeout)

    mod.urllib.request.urlopen = urlopen_block
    first = handler()
    first._attn({"served_model_name": "demo", "tp": 2, "jobs": JOBS[:1]})
    second = handler()
    second._attn({"served_model_name": "demo", "tp": 2, "jobs": JOBS[:1]})
    out = {"second": second.replies}
    gate.set()
    join()
    out["after"] = {"running": mod.ATTN["running"], "done": mod.ATTN["done"]}
    # A third call, once the loop is finished, is accepted and keeps seq rising.
    seq_before = mod.ATTN_SEQ
    mod.urllib.request.urlopen = urlopen_ok
    third = handler()
    third._attn({"served_model_name": "demo", "tp": 2, "jobs": JOBS[1:]})
    join()
    out["third"] = third.replies
    out["seq_rose"] = mod.ATTN_SEQ > seq_before
    return out


def scenario_mass_mode():
    """A mass job's mode/query_start/classes must reach current.json verbatim."""
    mod.urllib.request.urlopen = urlopen_ok
    h = handler()
    h._attn({"served_model_name": "demo", "tp": 2, "jobs": [MASS_JOB, JOBS[1]]})
    join()
    return {"replies": h.replies, "requests": requests_seen, "final": mod.ATTN}


def scenario_bad_payloads():
    bad = [
        {"tp": 2, "jobs": []},                                      # no model name
        {"served_model_name": "d", "jobs": []},                     # no tp
        {"served_model_name": "d", "tp": 2, "jobs": {"q0": {}}},    # jobs not a list
        {"served_model_name": "d", "tp": 2,
         "jobs": [{k: v for k, v in JOBS[0].items() if k != "put_urls"}]},
        {"served_model_name": "d", "tp": "two", "jobs": []},
    ]
    out = []
    for payload in bad:
        h = handler()
        h._attn(payload)
        out.append(h.replies[0][0])
    return {"codes": out, "running": mod.ATTN["running"]}


def scenario_status_block():
    mod.urllib.request.urlopen = urlopen_ok
    h = handler()
    h.path = "/status"
    h.do_GET()
    return {"status": h.replies[0][1]}


def scenario_serve_env_and_files():
    payload = {
        "served_model_name": "demo", "hf_model_id": "acme/demo", "tp": 2,
        "max_model_len": 4096, "vllm_args": ["--enforce-eager"],
        "env": {"VLLM_PLUGINS": "smolbench_attn", "SMOLBENCH_ATTN_DIR": "/root/.cache/huggingface/attn"},
        "files": {"attn_plugin/smolbench_attn/__init__.py": "def register():\n    pass\n",
                  "attn_plugin/smolbench_attn-0.1.dist-info/entry_points.txt": "[vllm.general_plugins]\n"},
    }
    # Stale capture state from a previous serve must be swept.
    os.makedirs(DONE, exist_ok=True)
    with open(CURRENT, "w") as fh:
        json.dump({"job_id": "q7", "seq": 3}, fh)
    write_done("q7", 0, {"ok": True})
    h = handler()
    h._serve(payload)
    return {
        "replies": h.replies, "launched": launched,
        "plugin": open(os.path.join(mod.HF_CACHE, "attn_plugin", "smolbench_attn",
                                    "__init__.py")).read(),
        "current_left": os.path.exists(CURRENT),
        "done_left": sorted(os.listdir(DONE)) if os.path.isdir(DONE) else [],
    }


def scenario_serve_rejects():
    base = {"served_model_name": "demo", "hf_model_id": "acme/demo", "tp": 1,
            "max_model_len": 4096, "vllm_args": []}
    out = []
    for extra in ({"env": {"A": 1}},
                  {"env": {"A": None}},
                  {"files": {"../escape.py": "x"}},
                  {"files": {"/etc/passwd": "x"}},
                  {"files": {"ok/../../escape.py": "x"}}):
        h = handler()
        before = len(launched)
        h._serve(dict(base, **extra))
        out.append({"code": h.replies[0][0], "launched": len(launched) - before})
    out.append({"escape_written": os.path.exists(os.path.join(TMP, "escape.py"))
                or os.path.exists(os.path.join(os.path.dirname(mod.HF_CACHE), "escape.py"))})
    return {"results": out}


print(json.dumps(globals()["scenario_" + os.environ["SCENARIO"]]()))
'''


def run(tmp_path: Path, scenario: str, **env: str) -> dict:
    """Execute one scenario against a by-path copy of the agent asset."""
    agent_path = tmp_path / "agent.py"
    agent_path.write_text(AGENT_PY)
    proc = subprocess.run(
        [sys.executable, "-c", DRIVER],
        env=os.environ | {
            "CONTROL_TOKEN": "tok", "VLLM_API_KEY": "key", "HF_TOKEN": "hf",
            "VLLM_IMAGE": "vllm/vllm-openai@sha256:deadbeef",
            "SMOLBENCH_CACHE_HUB": str(tmp_path / "hub"),
            "SMOLBENCH_VLLM_PORT": "8000",
            "AGENT_PATH": str(agent_path), "TMP_DIR": str(tmp_path),
            "SCENARIO": scenario, **env,
        },
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_attn_runs_every_job_in_order_and_reports_each_rank(tmp_path: Path) -> None:
    """One armed job at a time, one prefill each, every rank's done file collected."""
    out = run(tmp_path, "happy")
    assert out["replies"] == [[202, {"ok": True, "jobs": 2}]]
    # running is visible to the client's very first poll, not only once the thread starts.
    assert out["at_reply"]["running"] is True
    assert (out["at_reply"]["total"], out["at_reply"]["done"]) == (2, 0)

    # One completions request per job, in payload order, with the bearer key.
    assert [r["body"]["prompt"] for r in out["requests"]] == [[1, 2, 3, 4, 5], [9, 8]]
    for req in out["requests"]:
        assert req["url"] == "http://127.0.0.1:8000/v1/completions"
        assert req["headers"]["Authorization"] == "Bearer key"
        assert req["body"]["model"] == "demo"
        assert req["body"]["max_tokens"] == 1 and req["body"]["temperature"] == 0
        assert req["body"]["seed"] == 0  # every request keeps the reproducibility seed
        assert req["timeout"] == 1200
    # current.json is armed BEFORE the request and describes that job.
    first, second = (r["current"] for r in out["requests"])
    assert first["job_id"] == "q0" and first["n_tokens"] == 5 and first["positions"] == [3, 4]
    assert first["put_urls"] == ["u0r0", "u0r1"] and first["meta_put_urls"] == ["m0r0", "m0r1"]
    assert second["job_id"] == "q1" and second["n_tokens"] == 2
    # seq strictly increases: the plugin drops any job whose seq it has already finished.
    assert second["seq"] > first["seq"]

    final = out["final"]
    assert (final["running"], final["done"], final["total"]) == (False, 2, 2)
    assert final["current"] is None and final["error"] is None
    assert sorted(final["results"]) == ["q0", "q1"]
    assert sorted(final["results"]["q0"]) == ["0", "1"]
    assert final["results"]["q0"]["0"]["gate_max_rel"] == 0.001
    assert final["results"]["q0"]["1"]["gate_max_rel"] == 0.002
    assert final["results"]["q0"]["1"]["ok"] is True
    # The armed job is withdrawn when the loop ends: nothing stale for the next serve.
    assert out["current_left"] is False


def test_stale_done_files_are_never_read_as_this_jobs_result(tmp_path: Path) -> None:
    """A previous serve's ``q0.r*.json`` must be cleared, so a silent run times out."""
    out = run(tmp_path, "stale_done_is_cleared")
    result = out["final"]["results"]["q0"]
    assert "error" in result, result
    assert "0" not in result and "1" not in result
    assert out["final"]["done"] == 1 and out["final"]["running"] is False


def test_a_failing_job_is_recorded_and_the_loop_continues(tmp_path: Path) -> None:
    """One job's exception must not abandon the rest of the batch."""
    final = run(tmp_path, "job_failure_continues")["final"]
    assert "vLLM said no" in final["results"]["q0"]["error"]
    assert sorted(final["results"]["q1"]) == ["0", "1"]
    assert (final["done"], final["running"], final["error"]) == (2, False, None)


def test_a_second_attn_while_one_runs_is_refused(tmp_path: Path) -> None:
    """409 while the loop is alive; accepted again afterwards, with seq still rising."""
    out = run(tmp_path, "conflict")
    assert out["second"][0][0] == 409
    assert "already running" in out["second"][0][1]["error"]
    assert out["after"] == {"running": False, "done": 1}
    assert out["third"][0][0] == 202
    assert out["seq_rose"] is True


def test_bad_attn_payloads_are_refused_without_starting_a_thread(tmp_path: Path) -> None:
    out = run(tmp_path, "bad_payloads")
    assert out["codes"] == [400, 400, 400, 400, 400]
    assert out["running"] is False


def test_status_carries_the_attn_block_the_contract_lists(tmp_path: Path) -> None:
    status = run(tmp_path, "status_block")["status"]
    assert sorted(status["attn"]) == ["current", "done", "error", "results", "running", "total"]
    assert status["attn"]["running"] is False and status["attn"]["results"] == {}
    assert "healthy" in status  # the pre-existing blocks survive
    assert "replay" not in status  # the HF replay path is not shipped on this branch


def test_serve_stages_files_and_env_before_docker_and_sweeps_stale_capture_state(
    tmp_path: Path,
) -> None:
    """``files`` land under the cache mount first; ``env`` becomes ``-e NAME=value``."""
    out = run(tmp_path, "serve_env_and_files")
    assert out["replies"] == [[202, {"ok": True, "launching": "demo"}]]
    (launch,) = out["launched"]
    script = launch["cmd"][2]
    assert "-e VLLM_PLUGINS=smolbench_attn" in script
    assert "-e SMOLBENCH_ATTN_DIR=/root/.cache/huggingface/attn" in script
    # Written before `docker run` was ever spawned, not after.
    assert "attn_plugin/smolbench_attn/__init__.py" in launch["files_present"]
    assert "attn_plugin/smolbench_attn-0.1.dist-info/entry_points.txt" in launch["files_present"]
    assert out["plugin"] == "def register():\n    pass\n"
    # A previous serve's armed job and done files must not survive into this one.
    assert out["current_left"] is False and out["done_left"] == []


def test_serve_refuses_non_string_env_values_and_escaping_file_paths(tmp_path: Path) -> None:
    """Path traversal and non-string env values are 400s, and nothing is launched."""
    out = run(tmp_path, "serve_rejects")
    results = out["results"]
    assert [r["code"] for r in results[:5]] == [400, 400, 400, 400, 400]
    assert [r["launched"] for r in results[:5]] == [0, 0, 0, 0, 0]
    assert results[5]["escape_written"] is False


def test_the_agent_asset_stays_stdlib_only_and_heredoc_safe() -> None:
    """The capture endpoint must not drag a dependency in, nor break the user-data heredoc."""
    assert "import threading" in AGENT_PY and "import requests" not in AGENT_PY
    assert "AGENT_EOF" not in AGENT_PY


def test_a_mass_job_carries_its_class_labels_into_current_json(tmp_path: Path) -> None:
    """mode/query_start/classes are copied verbatim; a rows job gains none of them."""
    out = run(tmp_path, "mass_mode")
    assert out["replies"] == [[202, {"ok": True, "jobs": 2}]]
    mass, rows = (r["current"] for r in out["requests"])
    assert mass["mode"] == "mass" and mass["query_start"] == 4
    # A plain JSON list of small ints, in order, one per token of prompt + completion.
    assert mass["classes"] == [0, 1, 1, 2, 3, 3]
    assert len(mass["classes"]) == mass["n_tokens"] == 6
    # positions stays the gate list, and the required keys are unchanged.
    assert mass["positions"] == [5] and mass["put_urls"] == ["u7r0", "u7r1"]
    # The rows job must NOT acquire the mass keys (the plugin defaults mode
    # itself, and a literal "mode": null would be a different job shape).
    assert "mode" not in rows and "query_start" not in rows and "classes" not in rows
    assert rows["job_id"] == "q1" and rows["positions"] == [1]
    # Both jobs still ran, in order, one prefill each.
    assert [r["body"]["prompt"] for r in out["requests"]] == [[1, 2, 3, 4, 5, 6], [9, 8]]
    assert out["final"]["done"] == 2 and sorted(out["final"]["results"]) == ["q1", "q7"]
