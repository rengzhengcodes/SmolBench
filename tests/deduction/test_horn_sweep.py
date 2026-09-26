"""The Horn sweep driver against a stub OpenAI-compatible server.

The stub answers each request from the ``## Goal`` line of the user prompt: the
designed proof for that goal (inside ``<think>`` and a draft, or in the reasoning
channel), a cap-hit response with null content, or an aborted response.
"""

import importlib.util
import json
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tests._paths import REPO_ROOT

SWEEP = REPO_ROOT / "scripts" / "deduction" / "horn" / "sweep.py"


def _load_sweep():
    spec = importlib.util.spec_from_file_location("horn_sweep", SWEEP)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["horn_sweep"] = (
        mod  # dataclasses resolve annotations through sys.modules
    )
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def sweep():
    return _load_sweep()


def _render(out: Path, seeds: str) -> Path:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "smolbench.deduction.horn.cli",
            "render",
            "--seeds",
            seeds,
            "--m",
            "3",
            "--arms",
            "lem",
            "both",
            "--out",
            str(out),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
    )
    return out


@pytest.fixture(scope="module")
def rung(tmp_path_factory) -> Path:
    """Two small theories rendered with the CLI (lem and both arms)."""
    return _render(tmp_path_factory.mktemp("rungs") / "rung_a", "0-1")


@pytest.fixture(scope="module")
def rung_b(tmp_path_factory) -> Path:
    """A second rung with the same seeds and arm names (a different level)."""
    return _render(tmp_path_factory.mktemp("rungs") / "rung_b", "0-1")


class _Stub(BaseHTTPRequestHandler):
    """Answer from a table keyed by the goal line; record every request body."""

    proofs: dict[str, str] = {}
    requests: list[dict] = []
    length_for: set[str] = set()
    abort_for: set[str] = set()
    reasoning_channel: bool = False
    streamed: bool = False

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).requests.append(body)
        user = body["messages"][-1]["content"]
        mt = re.search(r"## Goal\n(\S+)", user)
        assert mt is not None
        goal = mt.group(1)
        msg: dict = {"role": "assistant"}
        finish = "stop"
        if goal in self.length_for:
            msg["content"] = None  # cap hit inside reasoning: vLLM returns null content
            msg["reasoning_content"] = "still thinking about " + goal
            finish = "length"
        elif goal in self.abort_for:
            msg["content"] = ""
            finish = "abort"
        else:
            proof = self.proofs[goal]
            first = proof.splitlines()[0]
            if self.reasoning_channel:
                msg["reasoning_content"] = f"let me try {first} ... no wait"
                msg["content"] = (
                    f"Draft:\n{first}\n\nFinal proof:\n```\n{proof}```\nThat completes it.\n"
                )
            else:
                msg["content"] = (
                    f"<think>let me try {first} ... no wait</think>\nDraft:\n{first}\n\n"
                    f"Final proof:\n```\n{proof}```\n"
                )
        usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        if body.get("stream"):
            type(self).streamed = True
            delta = {k: v for k, v in msg.items() if k != "role"}
            chunks = [
                {
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant"},
                            "finish_reason": None,
                        }
                    ]
                },
                {"choices": [{"index": 0, "delta": delta, "finish_reason": finish}]},
                {"choices": [], "usage": usage},
            ]
            data = (
                "".join(f"data: {json.dumps(c)}\n\n" for c in chunks)
                + "data: [DONE]\n\n"
            )
            self._reply(data.encode(), "text/event-stream")
            return
        choice = {"message": msg, "finish_reason": finish}
        data = json.dumps({"model": body["model"], "choices": [choice], "usage": usage})
        self._reply(data.encode(), "application/json")

    def _reply(self, data: bytes, ctype: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(
        self, format, *args
    ):  # noqa: A002  # pylint: disable=redefined-builtin
        return


@pytest.fixture()
def server(rung, rung_b):
    _Stub.proofs = {}
    _Stub.requests = []
    _Stub.length_for = set()
    _Stub.abort_for = set()
    _Stub.reasoning_channel = False
    _Stub.streamed = False
    for meta in list(rung.glob("s*/*/meta.json")) + list(rung_b.glob("s*/*/meta.json")):
        m = json.loads(meta.read_text())
        _Stub.proofs[m["goal"] + "(" + m["constant"] + ")"] = (
            "\n".join(m["designed_proof"]) + "\n"
        )
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Stub)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/v1"
    srv.shutdown()


def _args(server, rung, out, **kw):
    base = {
        "--endpoint": server,
        "--model": "stub-model",
        "--spec-key": "gemma-4-e2b",
        "--rung-dir": str(rung),
        "--out": str(out),
        "--concurrency": "2",
        "--max-retries": "1",
        "--replicates": "2",
    }
    base.update(kw)
    args = []
    for k, v in base.items():
        args.extend([k, v])
    return args + ["--arms", "lem", "both"]


def _rows(out: Path) -> list[dict]:
    return [json.loads(line) for line in out.read_text().splitlines()]


def test_final_proof_block(sweep):
    fp = sweep.final_proof_block
    text = "Draft:\nderive a(c) from f(c)\nbad\nFinal:\n```\nderive a(c) from f(c)\nderive g(c) from a(c)\n```\n"
    assert fp(text) == "derive a(c) from f(c)\nderive g(c) from a(c)\n"
    # trailing prose after the proof is skipped, not a fallback to the whole text
    assert (
        fp("bad draft line\nderive a(c) from f(c)\n\nThis completes the proof.")
        == "derive a(c) from f(c)\n"
    )
    # inline backticks and list markers are stripped
    assert (
        fp("- `derive a(c) from f(c)`\n- `derive g(c) from a(c)`")
        == "derive a(c) from f(c)\nderive g(c) from a(c)\n"
    )
    # two fenced blocks: only the last one
    assert (
        fp("```\nderive z(c) from f(c)\n```\n```\nderive a(c) from f(c)\n```")
        == "derive a(c) from f(c)\n"
    )
    assert fp("no steps here") == ""
    assert fp("derive a(c) from f(c)\ngive up") == "derive a(c) from f(c)\n"


def test_strip_reasoning_both_forms(sweep):
    assert sweep.strip_reasoning("<think>x</think>a[THINK]y[/THINK]b") == "ab"


def test_thinking_args(sweep):
    assert sweep.thinking_args("deepseek-v4-flash", "auto") == {
        "chat_template_kwargs": {"thinking": True}
    }
    assert sweep.thinking_args("gemma-4-e2b", "auto") == {
        "chat_template_kwargs": {"enable_thinking": True}
    }
    assert sweep.thinking_args("ministral-3-8b", "auto") == {}
    assert sweep.thinking_args("anything", "off") == {}
    with pytest.raises(SystemExit):
        sweep.thinking_args("not-a-roster-model", "auto")  # fails closed


def test_provider_system_prompt_ministral(sweep):
    assert "[THINK]" in sweep.provider_system_prompt("ministral-3-8b")
    assert sweep.provider_system_prompt("gemma-4-e2b") is None


def test_sweep_scores_streams_resumes_and_flags_length(sweep, rung, server, tmp_path):
    out = tmp_path / "rows.jsonl"
    goals = sorted(_Stub.proofs)
    _Stub.length_for = {goals[0]}
    args = _args(server, rung, out)
    assert sweep.main(args) == 0
    rows = _rows(out)
    assert len(rows) == 2 * 2 * 2  # seeds x arms x replicates
    body = _Stub.requests[0]
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert body["max_tokens"] == 32768 and body["temperature"] == 0.7
    assert body["chat_template_kwargs"] == {"enable_thinking": True}
    assert body["stream"] is True and _Stub.streamed
    assert {r["rung"] for r in rows} == {rung.name}
    assert all(r["sampling"]["max_tokens"] == 32768 for r in rows)
    length_rows = [r for r in rows if r["finish_reason"] == "length"]
    ok_rows = [r for r in rows if r["finish_reason"] == "stop"]
    assert length_rows and all(r["verdict"] == "length" for r in length_rows)
    assert all(r["content"] == "" and r["reasoning_chars"] > 0 for r in length_rows)
    assert ok_rows and all(r["verdict"] == "success" for r in ok_rows), [
        r["reason"] for r in ok_rows
    ]
    assert all(
        r["reasoning_chars"] > 0 for r in ok_rows
    )  # <think> split into the reasoning channel
    # resume: nothing left to do
    n_before = len(_Stub.requests)
    assert sweep.main(args) == 0
    assert len(_Stub.requests) == n_before
    assert len(_rows(out)) == len(rows)


def test_reasoning_channel_and_trailing_prose(sweep, rung, server, tmp_path):
    _Stub.reasoning_channel = True
    out = tmp_path / "rows.jsonl"
    assert sweep.main(_args(server, rung, out, **{"--replicates": "1"})) == 0
    rows = _rows(out)
    assert all(r["verdict"] == "success" for r in rows), [r["reason"] for r in rows]
    assert all(r["reasoning_chars"] > 0 for r in rows)


def test_ministral_gets_provider_system_prompt(sweep, rung, server, tmp_path):
    out = tmp_path / "rows.jsonl"
    args = _args(
        server, rung, out, **{"--spec-key": "ministral-3-8b", "--replicates": "1"}
    )
    assert sweep.main(args) == 0
    body = _Stub.requests[0]
    assert [m["role"] for m in body["messages"]] == ["system", "system", "user"]
    assert "[THINK]" in body["messages"][0]["content"]
    assert "chat_template_kwargs" not in body
    assert all(r["provider_system_prompt"] for r in _rows(out))


def test_second_rung_same_seeds_is_not_skipped(sweep, rung, rung_b, server, tmp_path):
    out = tmp_path / "rows.jsonl"
    assert sweep.main(_args(server, rung, out, **{"--replicates": "1"})) == 0
    n1 = len(_Stub.requests)
    assert sweep.main(_args(server, rung_b, out, **{"--replicates": "1"})) == 0
    assert len(_Stub.requests) == 2 * n1
    assert {r["rung"] for r in _rows(out)} == {rung.name, rung_b.name}


def test_abort_is_exception_retried_and_nonzero_exit(sweep, rung, server, tmp_path):
    out = tmp_path / "rows.jsonl"
    goals = sorted(_Stub.proofs)
    _Stub.abort_for = {goals[0]}
    args = _args(server, rung, out, **{"--replicates": "1"})
    assert sweep.main(args) == 1
    rows = _rows(out)
    exc = [r for r in rows if r["verdict"] == "exception"]
    assert exc and all("abort" in r["reason"] for r in exc)
    # the aborted cells are not done: a rerun sends them again and, once they stop, exits 0
    _Stub.abort_for = set()
    n_before = len(_Stub.requests)
    assert sweep.main(args) == 0
    assert len(_Stub.requests) == n_before + len(exc)


def test_torn_tail_is_repaired(sweep, rung, server, tmp_path):
    out = tmp_path / "rows.jsonl"
    args = _args(server, rung, out, **{"--replicates": "1"})
    assert sweep.main(args) == 0
    rows = _rows(out)
    out.write_text(
        out.read_text()
        + '{"model": "stub-model", "rung": "x", "arm": "lem", "seed": 0, "re'
    )
    assert sweep.main(args) == 0  # nothing to do, tail dropped
    assert _rows(out) == rows


# -- Bedrock driver (transport only; scoring is shared with sweep.py) -------------


class _FakeBedrock:
    """``converse_stream`` that replays a fixed event list and records the request."""

    def __init__(self, events):
        self.events = events
        self.requests = []

    def converse_stream(self, **kw):
        self.requests.append(kw)
        return {"stream": iter(self.events)}


def _load_bedrock():
    import importlib.util  # pylint: disable=import-outside-toplevel

    path = REPO_ROOT / "scripts" / "deduction" / "horn" / "bedrock_sweep.py"
    spec = importlib.util.spec_from_file_location("bedrock_sweep", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bedrock_sweep"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_bedrock_converse_separates_reasoning_and_maps_stop_reasons():
    """Reasoning deltas stay out of the answer; max_tokens becomes ``length``; fields pass through."""
    bs = _load_bedrock()
    st = bs.BedrockSettings("m", "k", "us-east-2", 2048, 0.7, {"reasoning_effort": "high"}, 10, 1)
    events = [
        {"contentBlockDelta": {"delta": {"reasoningContent": {"text": "thinking "}}}},
        {"contentBlockDelta": {"delta": {"reasoningContent": {"text": "more"}}}},
        {"contentBlockDelta": {"delta": {"text": "derive a(c) from b(c)\n"}}},
        {"contentBlockDelta": {"delta": {"text": "derive g(c) from a(c)"}}},
        {"messageStop": {"stopReason": "max_tokens"}},
        {"metadata": {"usage": {"inputTokens": 5, "outputTokens": 100, "totalTokens": 105}}},
    ]
    fake = _FakeBedrock(events)
    r = bs.converse(fake, st, "sys", "prompt")
    assert r.reasoning == "thinking more"
    assert r.content == "derive a(c) from b(c)\nderive g(c) from a(c)"
    assert r.finish_reason == "length" and r.completion_tokens == 100 and r.prompt_tokens == 5
    req = fake.requests[0]
    assert req["additionalModelRequestFields"] == {"reasoning_effort": "high"}
    assert req["inferenceConfig"] == {"maxTokens": 2048, "temperature": 0.7}
    assert req["system"] == [{"text": "sys"}] and req["messages"][0]["content"] == [{"text": "prompt"}]
    fake2 = _FakeBedrock([{"contentBlockDelta": {"delta": {"text": "x"}}}, {"messageStop": {"stopReason": "end_turn"}}])
    r2 = bs.converse(fake2, bs.BedrockSettings("m", "k", "r", 1, 0.0, None, 1, 1), "s", "p")
    assert r2.finish_reason == "stop" and r2.reasoning is None
    assert "additionalModelRequestFields" not in fake2.requests[0]


def test_bedrock_output_cap_fits_the_context():
    """The cap is the requested one when it fits, else what the context leaves."""
    bs = _load_bedrock()
    st = bs.BedrockSettings("m", "k", "r", 131072, 0.7, None, 1, 1, context_length=131072)
    assert bs.output_cap(st, 0) == 131072 - 1024
    assert bs.output_cap(st, 1100) == 131072 - 1650 - 1024
    small = bs.BedrockSettings("m", "k", "r", 32768, 0.7, None, 1, 1, context_length=131072)
    assert bs.output_cap(small, 15000) == 32768
    assert bs.output_cap(small, 130000) == 1024
    fake = _FakeBedrock([{"messageStop": {"stopReason": "end_turn"}}])
    bs.converse(fake, st, "s", "p", 1100)
    assert fake.requests[0]["inferenceConfig"]["maxTokens"] == 131072 - 1650 - 1024


def test_sweep_output_cap_fits_the_served_context(sweep):
    """The served-model driver cuts max_tokens per cell like the Bedrock one."""
    st = sweep.Settings("m", "k", {"max_tokens": 131072, "temperature": 0.7}, 131072, 1, 1, None)
    assert sweep.output_cap(st, 0) == 131072 - 1024
    assert sweep.output_cap(st, 4000) == 131072 - 6000 - 1024
    small = sweep.Settings("m", "k", {"max_tokens": 32768, "temperature": 0.7}, 131072, 1, 1, None)
    assert sweep.output_cap(small, 15000) == 32768
