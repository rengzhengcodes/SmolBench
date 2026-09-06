"""`.claude/skills/run-smolbench/stub_llm.py` reuses the offline suite's stub server.

`lean_smoke.sh --e2e` drives a REAL Lean sweep against two fake LLMs. Those two
servers used to be a second, hand-rolled OpenAI-compatible stub sitting beside
`driver.py` in the same directory -- and `driver.py` already imports
`tests/conftest.py`'s `StubServer` "so the stub dialect has one source of
truth". Two stubs meant the dialect the smoke path exercised could drift from
the one the offline suite exercises, silently.

`--e2e` itself needs `elan`, a built mathlib4 checkout and a real corpus, so it
cannot run here. What CAN be checked offline is the contract that script depends
on, which is exactly what would break if the reuse were done wrong: the ports
line, the two fixed answers, the context-length GET routes, and the on-disk
request log. This drives the real script in a subprocess and asserts each.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request

import pytest

from tests._paths import REPO_ROOT

SKILL = REPO_ROOT / ".claude" / "skills" / "run-smolbench"
STUB = SKILL / "stub_llm.py"

#: The two answers `lean_smoke.sh --e2e` depends on. GOOD is the real
#: ground-truth tail of ``Lagrange.eval_nodal_at_node`` at k=1, so the sweep row
#: must come back ``verdict: success``; BAD names a lemma that does not exist,
#: which is what makes real Lean return ``lean_error`` rather than a failed
#: goal. Spelled out here rather than imported from the script: the point is
#: that they survived the rewrite byte for byte.
GOOD = "Here is the proof:\n```lean\nexact s.prod_eq_zero hi (sub_self (v i))\n```"
BAD = "```lean\nexact nonexistent_lemma_xyz42\n```"


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read())


def _post_completion(port: int, model: str, seed: int) -> dict:
    payload = json.dumps({"model": model, "seed": seed, "temperature": 0.7,
                          "messages": [{"role": "user", "content": "hi"}]}).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions", data=payload,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())


@pytest.fixture
def stub_process(tmp_path):
    """Start `stub_llm.py`, yield ``(ports, reqlog_path)``, then kill it."""
    reqlog = tmp_path / "reqlog.jsonl"
    proc = subprocess.Popen(
        [sys.executable, str(STUB), str(reqlog)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(REPO_ROOT))
    try:
        # The script prints its ports line BEFORE either server starts serving,
        # so a reader can never poll a port that is not yet bound -- the same
        # ordering `lean_smoke.sh` relies on when it polls ports.json.
        line = proc.stdout.readline()
        if not line:
            proc.wait(timeout=30)
            pytest.fail(f"stub_llm.py printed no ports line; stderr={proc.stderr.read()!r}")
        yield json.loads(line), reqlog
    finally:
        proc.kill()
        proc.wait(timeout=30)


def test_the_stub_serves_both_answers_and_both_context_length_shapes(stub_process):
    ports, _ = stub_process
    assert set(ports) == {"pi", "or"}
    assert ports["pi"] != ports["or"]

    good = _post_completion(ports["pi"], "stub-good-model", 4242)
    bad = _post_completion(ports["or"], "stub-bad-model", 4242)
    assert good["choices"][0]["message"]["content"] == GOOD
    assert bad["choices"][0]["message"]["content"] == BAD

    # Both providers probe context length before generating, by different
    # routes: OpenRouter's `/endpoints` and Prime Intellect's `/models/<id>`.
    # A stub that answered only one would fail the sweep before it reached a
    # single completion.
    assert _get_json(
        f"http://127.0.0.1:{ports['or']}/v1/models/stub-bad-model/endpoints"
    )["data"]["endpoints"][0]["context_length"] > 0
    assert _get_json(
        f"http://127.0.0.1:{ports['pi']}/v1/models/stub-good-model"
    )["context_length"] > 0


def test_every_completion_is_logged_in_the_shape_the_smoke_script_parses(stub_process):
    """The log line keys `lean_smoke.sh --e2e` actually reads.

    That script does ``[r for r in reqs if r["path"].endswith("/chat/completions")]``
    and then reads ``r["body"]["model"]`` and ``r["body"].get("seed")``, so
    `path` and `body` are the load-bearing keys. The `path` filter is also what
    makes logging GETs harmless: conftest's handler records them too, with
    ``"body": null``, and they never reach a subscript of ``None``.
    """
    ports, reqlog = stub_process
    _post_completion(ports["pi"], "stub-good-model", 4242)
    _post_completion(ports["or"], "stub-bad-model", 4242)
    _get_json(f"http://127.0.0.1:{ports['pi']}/v1/models/stub-good-model")

    # The servers write from handler threads; give the last one a moment to land.
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and len(reqlog.read_text().splitlines()) < 3:
        time.sleep(0.05)

    records = [json.loads(line) for line in reqlog.read_text().splitlines() if line]
    completions = [r for r in records if r["path"].endswith("/chat/completions")]
    assert len(completions) == 2, records
    assert {r["body"]["model"] for r in completions} == {"stub-good-model", "stub-bad-model"}
    assert all(r["body"]["seed"] == 4242 for r in completions)
    assert {r["stub"] for r in completions} == {"PI", "OR"}
    # A GET was recorded too, and carries a null body -- the condition the
    # script's `path` filter has to survive.
    assert any(r["body"] is None for r in records), records


def test_the_skill_does_not_hand_roll_a_second_stub_dialect():
    """The response shapes and GET routes come from `tests/conftest.py`, not a copy.

    Checked on the module's AST, not by substring: the file legitimately
    mentions `ThreadingHTTPServer` in a comment explaining why its log writes
    need a lock, and a bare ``in`` test flags that prose as if it were a
    reimplementation. What must be absent is an `http.server` IMPORT or a
    handler method DEFINITION -- the things that would constitute a second
    dialect.
    """
    import ast

    source = STUB.read_text()
    assert "from tests.conftest import" in source

    tree = ast.parse(source)
    imported = {
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name for node in ast.walk(tree)
        if isinstance(node, ast.Import) for alias in node.names
    }
    assert not {m for m in imported if m.split(".")[0] == "http"}, sorted(imported)
    assert "tests.conftest" in imported

    defined = {node.name for node in ast.walk(tree)
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    handler_methods = defined & {"do_POST", "do_GET", "_reply", "_reply_sse", "log_message"}
    assert not handler_methods, (
        f"{sorted(handler_methods)} defined in stub_llm.py -- the stub dialect "
        "has one source of truth in tests/conftest.py"
    )
