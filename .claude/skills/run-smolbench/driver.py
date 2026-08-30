"""Offline end-to-end smoke driver for the smolbench eval harness.

Drives the REAL production path -- quiz generation -> provider dispatch ->
ChatClient.query/evaluate -> grading -> Marks YAML IO -- against the local
OpenAI-compatible stub server from tests/conftest.py. Zero credentials, zero
network, zero AWS spend. Run from the repo root:

    timeout 120 .venv/bin/python .claude/skills/run-smolbench/driver.py

``timeout`` matters: the openrouter ChatClient retries transient failures
FOREVER with a 60s backoff, so a misbehaving stub would hang the driver.

Exit codes: 0 = PASS, 1 = a stage failed, 2 = environment/import problem.
"""

import os
import string
import sys
import tempfile
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# Stage counter state for uniform progress lines.
_STAGE = {"n": 0, "total": 8}


def stage(name: str, detail: str) -> None:
    _STAGE["n"] += 1
    print(f"[{_STAGE['n']}/{_STAGE['total']}] {name}: ok — {detail}")


def check(cond: bool, msg: str) -> None:
    # Explicit raise, not assert: asserts vanish under `python -O`.
    if not cond:
        raise RuntimeError(msg)


def main() -> None:
    # -- 1. Environment guard ------------------------------------------------
    check(
        sys.version_info[:2] == (3, 12),
        f"Python {sys.version.split()[0]} is not the project interpreter; smolbench "
        f"pins 3.12. Run via {REPO_ROOT}/.venv/bin/python (after `uv sync --all-extras`).",
    )
    stage("env", f"python {sys.version.split()[0]} at {sys.executable}")

    try:
        # Reused from the offline test suite so the stub dialect has one source
        # of truth (needs pytest importable -- it's in the dev extra).
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
    from smolbench.induction.chromatic import (
        ChromaticIntervalsConfig,
        get_random_exclusive_quiz,
        succession_query_gen,
    )
    from smolbench.induction.periodic import (
        PeriodicConfig,
        Prompter,
        get_periodic_numeric_quiz,
        numeric_count_query_gen,
    )

    # -- 2. Periodic quiz generation (offline, deterministic) ----------------
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
    # seq_len = lcm(1..3) = 6, so counts are 6//1, 6//2, 6//3.
    check([q.answer for q in intens] == [6, 3, 2], f"periodic answers {[q.answer for q in intens]} != [6, 3, 2]")
    intens2, _, _ = get_periodic_numeric_quiz(periodic_cfg, periodic_prompter, tokenizer=StubTokenizer())
    check(tuple(intens) == tuple(intens2), "periodic generation is not seed-deterministic")
    stage("periodic", f"{len(intens)} Numeric questions, answers {[q.answer for q in intens]}, seed-stable")

    # -- 3. Chromatic quiz generation (offline, deterministic) ---------------
    chromatic_template = string.Template(
        "Context:\n---\n"
        "There is a ceremonial role called the $role, whose job it is to head "
        "the $parade parade. The following lists the people who were $role and "
        "the years they were $role:\n$positive_info\n\n"
        "Query:\nHas $color1 handed the sceptre to $color2? Answer with only "
        "one word: 'True' or 'False'."
    )
    chromatic_cfg = ChromaticIntervalsConfig(n=40, intervals=10, colors=5, seed=1776)
    chromatic_prompter = Prompter(
        chromatic_template, {"role": "Twislax", "parade": "Gildane"}, succession_query_gen
    )
    chrom_intens, _, _ = get_random_exclusive_quiz(chromatic_cfg, chromatic_prompter, tokenizer=StubTokenizer())
    n_true = sum(1 for q in chrom_intens if q.answer is True)
    n_false = sum(1 for q in chrom_intens if q.answer is False)
    check(n_true >= 1 and n_true == n_false, f"expected balanced ToF polarity, got {n_true}T/{n_false}F")
    chrom_intens2, _, _ = get_random_exclusive_quiz(chromatic_cfg, chromatic_prompter, tokenizer=StubTokenizer())
    check(tuple(chrom_intens) == tuple(chrom_intens2), "chromatic generation is not seed-deterministic")
    stage("chromatic", f"{len(chrom_intens)} ToF questions ({n_true} True / {n_false} False), seed-stable")

    # -- 4. Stub server + call-time provider dispatch ------------------------
    server = StubServer()
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        # Dispatch is read at CALL time (smolbench/evals/provider.py), so env
        # set after import still applies -- exactly how notebooks do it.
        os.environ["INFERENCE_PROVIDER"] = "openrouter"
        os.environ["OPENROUTER_BASE_URL"] = server.base_url
        os.environ["OPENROUTER_API_KEY"] = "smoke-dummy"
        ctx = provider.get_model_context_length("smolbench-smoke")
        check(ctx == 100000, f"stub context length lookup returned {ctx}")
        stage("dispatch", f"INFERENCE_PROVIDER=openrouter -> stub at {server.base_url}, ctx={ctx}")

        # -- 5. Single seeded query round trip -------------------------------
        server.queue_response(chat_completion("6", reasoning_content="thought"))
        content, reasoning = provider.query(
            intens[0].prompt, "smolbench-smoke", seed=42, context_length=ctx
        )
        check((content, reasoning) == ("6", "thought"), f"query returned {(content, reasoning)!r}")
        last_post = [r for r in server.requests if r["body"] is not None][-1]
        check(last_post["body"].get("seed") == 42, f"request body lost the seed: {last_post['body']}")
        stage("query", "content+reasoning channels parsed, seed=42 present in request body")

        # -- 6. Sequential graded evaluate (queued right/wrong/invalid) ------
        # max_parallel=1 is REQUIRED: StubServer.next_response pops the queue
        # FIFO, so the response<->question mapping is deterministic only when
        # questions are asked one at a time.
        server.queue_response(chat_completion(str(intens[0].answer)))  # correct
        server.queue_response(chat_completion("99"))                   # incorrect
        server.queue_response(chat_completion("no digits here"))       # invalid
        marks_seq = provider.evaluate(
            intens, "smolbench-smoke", seed=42, max_parallel=1, show_progress=False
        )
        tally = (marks_seq.correct, marks_seq.incorrect, marks_seq.invalid)
        check(tally == (1, 1, 1), f"sequential grading tally {tally} != (1, 1, 1)")
        stage("evaluate-seq", "graded 3 Numeric questions -> 1 correct / 1 incorrect / 1 invalid")

        # -- 7. Parallel evaluate (uniform default response) -----------------
        # Parallel fan-out is only safe with a uniform default_response
        # (thread completion order is nondeterministic).
        server.default_response = chat_completion("True")
        marks_par = provider.evaluate(
            chrom_intens, "smolbench-smoke", seed=42, max_parallel=4, show_progress=False
        )
        check(
            (marks_par.correct, marks_par.incorrect, marks_par.invalid)
            == (n_true, n_false, 0),
            f"parallel tally {(marks_par.correct, marks_par.incorrect, marks_par.invalid)} "
            f"!= {(n_true, n_false, 0)}",
        )
        stage("evaluate-par", f"{len(chrom_intens)} ToF questions at max_parallel=4 -> {n_true} correct")
    finally:
        server.shutdown()
        server_thread.join(timeout=5)

    # -- 8. Marks YAML round trip (temp dir; smoke artifacts stay out of repo)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "smoke_marks.yaml"
        marks_par.dump(out)
        text = out.read_text()
        check("!!python/object" not in text, "dump produced python-object-tagged YAML")
        check(Marks.load(out) == marks_par, "Marks YAML round trip lost data")
    stage("marks-io", "safe-YAML dump/load round trip equal")

    total_qs = len(intens) + len(chrom_intens) + 1
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
