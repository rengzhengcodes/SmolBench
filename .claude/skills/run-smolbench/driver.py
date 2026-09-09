"""Offline end-to-end smoke driver for the evaluation harness.

Use `timeout 120`: OpenRouter retries transient failures indefinitely with a
60-second backoff, so a bad stub otherwise hangs the driver.

Exit codes: 0 pass, 1 stage failure, 2 environment/import failure.
"""

import os
import string
import sys
import tempfile
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

_STAGE = {"n": 0, "total": 8}


def stage(name: str, detail: str) -> None:
    """Print a successful progress line for one smoke-test stage."""
    _STAGE["n"] += 1
    print(f"[{_STAGE['n']}/{_STAGE['total']}] {name}: ok — {detail}")


def check(cond: bool, msg: str) -> None:
    """Raise when a smoke-test condition is not met."""
    # Explicit raise, not assert: asserts vanish under `python -O`.
    if not cond:
        raise RuntimeError(msg)


def main() -> None:
    """Run the offline end-to-end eval-harness smoke test."""
    check(
        sys.version_info[:2] == (3, 12),
        f"Python {sys.version.split()[0]} is not the project interpreter; smolbench "
        f"pins 3.12. Run via {REPO_ROOT}/.venv/bin/python (after `uv sync --all-extras`).",
    )
    stage("env", f"python {sys.version.split()[0]} at {sys.executable}")

    try:
        # Reuse the test stub so the two dialects cannot drift.
        from tests.conftest import StubServer, StubTokenizer, chat_completion
    except ImportError as err:
        print(
            f"FAIL: cannot import tests.conftest ({err}).\n"
            f"Expected tests/conftest.py under {REPO_ROOT} and pytest installed "
            "-- run `uv sync --all-extras` from the repo root.",
            file=sys.stderr,
        )
        sys.exit(2)

    from smolbench.evals import Marks
    from smolbench.evals import provider
    from smolbench.induction.periodic import (
        PeriodicConfig,
        Prompter,
        get_periodic_numeric_quiz,
        get_periodic_quiz,
        numeric_count_query_gen,
        tof_membership_query_gen,
    )

    periodic_template = string.Template(
        "Context:\n---\n"
        "There is a counting game. Count positions starting from 1. "
        "At each position write down words according to the following rules:\n"
        "$positive_info\n"
        "Query:\nHow many of the positions 1 through $seq_len include '$label'? "
        "Answer with a single integer."
    )
    periodic_cfg = PeriodicConfig(n=3, labels=["fizz", "buzz", "gerbil"], seed=42)
    periodic_prompter = Prompter(periodic_template, {}, numeric_count_query_gen)
    intens, extens, noise_intens = get_periodic_numeric_quiz(periodic_cfg, periodic_prompter, tokenizer=StubTokenizer())
    check(len(intens) == len(extens) == len(noise_intens) == 3, "expected 3 questions per periodic quiz")
    # lcm(1..3) is 6, yielding 6//1, 6//2, and 6//3.
    check([q.answer for q in intens] == [6, 3, 2], f"periodic answers {[q.answer for q in intens]} != [6, 3, 2]")
    intens2, _, _ = get_periodic_numeric_quiz(periodic_cfg, periodic_prompter, tokenizer=StubTokenizer())
    check(tuple(intens) == tuple(intens2), "periodic generation is not seed-deterministic")
    stage("periodic", f"{len(intens)} Numeric questions, answers {[q.answer for q in intens]}, seed-stable")

    tof_template = string.Template(
        "Context:\n---\n"
        "There is a counting game. Count positions starting from 1. "
        "At each position write down words according to the following rules:\n"
        "$positive_info\n"
        "Query:\nDoes position $pos include '$label'? Answer with only one "
        "word: 'True' or 'False'."
    )
    tof_cfg = PeriodicConfig(n=4, labels=["fizz", "buzz", "gerbil", "dax"], seed=1776)
    tof_prompter = Prompter(tof_template, {}, tof_membership_query_gen)
    tof_intens, _, _ = get_periodic_quiz(tof_cfg, tof_prompter, tokenizer=StubTokenizer())
    n_true = sum(1 for q in tof_intens if q.answer is True)
    n_false = sum(1 for q in tof_intens if q.answer is False)
    check(n_true >= 1 and n_true == n_false, f"expected balanced ToF polarity, got {n_true}T/{n_false}F")
    tof_intens2, _, _ = get_periodic_quiz(tof_cfg, tof_prompter, tokenizer=StubTokenizer())
    check(tuple(tof_intens) == tuple(tof_intens2), "periodic ToF generation is not seed-deterministic")
    stage("periodic-tof", f"{len(tof_intens)} ToF questions ({n_true} True / {n_false} False), seed-stable")

    server = StubServer()
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        # Dispatch reads the environment at call time, so post-import settings apply.
        os.environ["INFERENCE_PROVIDER"] = "openrouter"
        os.environ["OPENROUTER_BASE_URL"] = server.base_url
        os.environ["OPENROUTER_API_KEY"] = "smoke-dummy"
        ctx = provider.get_model_context_length("smolbench-smoke")
        check(ctx == 100000, f"stub context length lookup returned {ctx}")
        stage("dispatch", f"INFERENCE_PROVIDER=openrouter -> stub at {server.base_url}, ctx={ctx}")

        server.queue_response(chat_completion("6", reasoning_content="thought"))
        content, reasoning = provider.query(
            intens[0].prompt, "smolbench-smoke", seed=42, context_length=ctx
        )
        check((content, reasoning) == ("6", "thought"), f"query returned {(content, reasoning)!r}")
        last_post = [r for r in server.requests if r["body"] is not None][-1]
        check(last_post["body"].get("seed") == 42, f"request body lost the seed: {last_post['body']}")
        stage("query", "content+reasoning channels parsed, seed=42 present in request body")

        # max_parallel=1 preserves FIFO response-to-question mapping.
        server.queue_response(chat_completion(str(intens[0].answer)))  # correct
        server.queue_response(chat_completion("99"))                   # incorrect
        server.queue_response(chat_completion("no digits here"))       # invalid
        marks_seq = provider.evaluate(
            intens, "smolbench-smoke", seed=42, max_parallel=1, show_progress=False
        )
        tally = (marks_seq.correct, marks_seq.incorrect, marks_seq.invalid)
        check(tally == (1, 1, 1), f"sequential grading tally {tally} != (1, 1, 1)")
        stage("evaluate-seq", "graded 3 Numeric questions -> 1 correct / 1 incorrect / 1 invalid")

        # Parallel responses must be uniform because completion order varies.
        server.default_response = chat_completion("True")
        marks_par = provider.evaluate(
            tof_intens, "smolbench-smoke", seed=42, max_parallel=4, show_progress=False
        )
        check(
            (marks_par.correct, marks_par.incorrect, marks_par.invalid)
            == (n_true, n_false, 0),
            f"parallel tally {(marks_par.correct, marks_par.incorrect, marks_par.invalid)} "
            f"!= {(n_true, n_false, 0)}",
        )
        stage("evaluate-par", f"{len(tof_intens)} ToF questions at max_parallel=4 -> {n_true} correct")
    finally:
        server.shutdown()
        server_thread.join(timeout=5)

    # A temporary directory keeps smoke artifacts out of the repository.
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "smoke_marks.yaml"
        marks_par.dump(out)
        text = out.read_text()
        check("!!python/object" not in text, "dump produced python-object-tagged YAML")
        check(Marks.load(out) == marks_par, "Marks YAML round trip lost data")
    stage("marks-io", "safe-YAML dump/load round trip equal")

    total_qs = len(intens) + len(tof_intens) + 1
    print(
        f"\nPASS — smolbench offline smoke: {total_qs} stub completions served "
        f"({len(server.requests)} HTTP requests recorded), "
        f"seq tally {tally}, par tally ({marks_par.correct}, {marks_par.incorrect}, "
        f"{marks_par.invalid})."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 -- smoke driver: any failure is a FAIL
        import traceback

        traceback.print_exc()
        print(f"\nFAIL at stage {_STAGE['n'] + 1}/{_STAGE['total']}", file=sys.stderr)
        sys.exit(1)
