"""Offline contracts for `run-smolbench/stub_llm.py`.

`--e2e` needs `elan`, so this subprocess checks its stub-server contract.
"""

# pylint: disable=missing-function-docstring

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests._paths import REPO_ROOT

SKILL = REPO_ROOT / ".claude" / "skills" / "run-smolbench"
STUB = SKILL / "stub_llm.py"

# GOOD proves the fixture theorem; BAD names no lemma, producing `lean_error`.
GOOD = "Here is the proof:\n```lean\nexact Mini.premiseA h (Mini.premiseB n)\n```"
BAD = "```lean\nexact nonexistent_lemma_xyz42\n```"


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read())


def _post_completion(port: int, model: str, seed: int) -> dict:
    payload = json.dumps(
        {
            "model": model,
            "seed": seed,
            "temperature": 0.7,
            "messages": [{"role": "user", "content": "hi"}],
        }
    ).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())


@pytest.fixture
def stub_process(tmp_path: Path) -> Iterator[tuple[dict[str, int], Path]]:
    """Start `stub_llm.py`, yield ``(ports, reqlog_path)``, then kill it."""
    reqlog = tmp_path / "reqlog.jsonl"
    with subprocess.Popen(
        [sys.executable, str(STUB), str(reqlog)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(REPO_ROOT),
    ) as proc:
        try:
            # The port line precedes serving, so readers never poll an unbound port.
            line = proc.stdout.readline()
            if not line:
                proc.wait(timeout=30)
                pytest.fail(
                    f"stub_llm.py printed no ports line; stderr={proc.stderr.read()!r}"
                )
            yield json.loads(line), reqlog
        finally:
            proc.kill()
            proc.wait(timeout=30)


def test_the_stub_serves_both_answers_and_both_context_length_shapes(
    stub_process: tuple[dict[str, int], Path],
) -> None:
    ports, _ = stub_process
    assert set(ports) == {"pi", "or"}
    assert ports["pi"] != ports["or"]

    good = _post_completion(ports["pi"], "stub-good-model", 4242)
    bad = _post_completion(ports["or"], "stub-bad-model", 4242)
    assert good["choices"][0]["message"]["content"] == GOOD
    assert bad["choices"][0]["message"]["content"] == BAD

    # Both context routes must work before either provider generates.
    assert (
        _get_json(f"http://127.0.0.1:{ports['or']}/v1/models/stub-bad-model/endpoints")[
            "data"
        ]["endpoints"][0]["context_length"]
        > 0
    )
    assert (
        _get_json(f"http://127.0.0.1:{ports['pi']}/v1/models/stub-good-model")[
            "context_length"
        ]
        > 0
    )


def test_every_completion_is_logged_in_the_shape_the_smoke_script_parses(
    stub_process: tuple[dict[str, int], Path],
) -> None:
    """Completion logs need `path` and `body`; GET bodies may be null."""
    ports, reqlog = stub_process
    _post_completion(ports["pi"], "stub-good-model", 4242)
    _post_completion(ports["or"], "stub-bad-model", 4242)
    _get_json(f"http://127.0.0.1:{ports['pi']}/v1/models/stub-good-model")

    # Handler threads may not have written the final record yet.
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and len(reqlog.read_text().splitlines()) < 3:
        time.sleep(0.05)

    records = [json.loads(line) for line in reqlog.read_text().splitlines() if line]
    completions = [r for r in records if r["path"].endswith("/chat/completions")]
    assert len(completions) == 2, records
    assert {r["body"]["model"] for r in completions} == {
        "stub-good-model",
        "stub-bad-model",
    }
    assert all(r["body"]["seed"] == 4242 for r in completions)
    assert {r["stub"] for r in completions} == {"PI", "OR"}
    # GETs carry null bodies, so the path filter must exclude them.
    assert any(r["body"] is None for r in records), records


def test_the_skill_does_not_hand_roll_a_second_stub_dialect() -> None:
    """The stub reuses `tests/conftest.py` rather than a second dialect."""
    import ast

    source = STUB.read_text()
    assert "from tests.conftest import" in source

    tree = ast.parse(source)
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not {m for m in imported if m.split(".")[0] == "http"}, sorted(imported)
    assert "tests.conftest" in imported

    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    handler_methods = defined & {
        "do_POST",
        "do_GET",
        "_reply",
        "_reply_sse",
        "log_message",
    }
    assert not handler_methods, (
        f"{sorted(handler_methods)} defined in stub_llm.py -- the stub dialect "
        "has one source of truth in tests/conftest.py"
    )
