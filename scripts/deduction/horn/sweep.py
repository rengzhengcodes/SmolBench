"""Run Horn-bench rungs against an OpenAI-compatible endpoint, one chat completion per cell.

Each cell is (rung, arm, theory seed, replicate). The request is the arm's ``system.md``
as the system message (after any provider system prompt the model's deployment spec
needs, such as Ministral's ``[THINK]`` instructions) and ``prompt.md`` as the user
message, sent once with the model's thinking arguments, a sampling temperature and an
output cap. No tools, no file reading: the served model sees the whole prompt in one
context. Responses stream by default so a long generation does not hit an idle timeout.

The answer is the last contiguous block of ``derive`` lines after any reasoning block is
removed, scored with ``smolbench.deduction.horn.checker.verify``. A response cut at the
output cap (``finish_reason == "length"``) scores as ``length``. A cell whose request
failed, or whose finish reason is neither ``stop`` nor ``length``, is written with verdict
``exception`` and is retried on the next run.

Rows append to a JSONL file keyed by (model, rung, arm, seed, replicate); rerunning skips
cells already scored, so a stopped sweep resumes. The file is locked while a sweep runs.
The exit status is 1 when any cell is missing or failed.

usage::

    python scripts/deduction/horn/sweep.py --endpoint http://127.0.0.1:8000/v1 \\
        --model qwen3.5-27b --rung-dir <rung> --replicates 3 \\
        --out results/qwen3.5-27b.jsonl
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from smolbench.deduction.horn.checker import _STEP_RE, verify  # noqa: E402
from smolbench.deduction.horn.render import ARMS, Rendered  # noqa: E402
from smolbench.deduction.horn.theory import Theory  # noqa: E402
from smolbench.evals.openai_compat import ChatClient, ChatResult  # noqa: E402

_THINK_BLOCK_RE = re.compile(
    r"<think>.*?</think>|\[THINK\].*?\[/THINK\]", re.DOTALL | re.IGNORECASE
)
_FENCE_RE = re.compile(r"^\s*```")
_LINE_DECOR_RE = re.compile(r"^[\s>*`_-]+|[\s*`_]+$")
_FINAL_REASONS = ("stop", "length")


def thinking_args(spec_key: str, mode: str) -> dict[str, Any]:
    """Chat-template arguments that switch a roster model's thinking on.

    Mirrors ``COT_ARGS`` in ``notebooks/induction/run_study.py``: Ministral needs no
    toggle (its thinking comes from the provider system prompt, see
    ``provider_system_prompt``), DeepSeek spells it ``thinking``, the rest take
    ``enable_thinking`` (Gemma-4 and EXAONE default it off, so ``True`` is load-bearing).
    ``mode`` is ``auto`` (the roster rule; an unknown key is an error, so a model never
    runs with thinking silently off), ``on`` (force ``enable_thinking``) or ``off``.
    """
    if mode == "off":
        return {}
    if mode == "on":
        return {"chat_template_kwargs": {"enable_thinking": True}}
    from smolbench.evals.study_config import (  # pylint: disable=import-outside-toplevel
        roster_keys,
    )

    if spec_key not in roster_keys():
        raise SystemExit(
            f"--spec-key {spec_key!r} is not a roster key; pass --thinking on|off explicitly"
        )
    if spec_key.startswith("ministral"):
        return {}
    flag = "thinking" if spec_key.startswith("deepseek") else "enable_thinking"
    return {"chat_template_kwargs": {flag: True}}


def provider_system_prompt(spec_key: str) -> str | None:
    """The deployment spec's own system prompt for ``spec_key``.

    Ministral's ``[THINK]`` protocol lives there: the chat template drops its default
    system message once any system message is sent, so the EC2 provider injects it.
    """
    from smolbench.evals.providers import ec2  # pylint: disable=import-outside-toplevel

    return ec2.EC2_DEPLOY_SPECS.get(spec_key, {}).get("system_prompt")


def strip_reasoning(text: str) -> str:
    """Remove inline reasoning blocks (``<think>`` and Ministral's ``[THINK]``)."""
    return _THINK_BLOCK_RE.sub("", text)


def _step_text(line: str) -> str | None:
    """The step in ``line`` with list markers, quotes and backticks removed, or None."""
    s = _LINE_DECOR_RE.sub("", line.strip())
    return s if _STEP_RE.match(s) else None


def final_proof_block(text: str) -> str:
    """The last contiguous run of proof-step lines in ``text``.

    Trailing prose after the proof is skipped; the block then extends upward over step
    lines and blank lines and stops at any other line or at a pair of code fences (a
    closed block followed by an opened one), so a draft proof earlier in the answer is
    not scored. Returns ``""`` (verdict ``no_answer``) when there is no step line.
    """
    lines = text.rstrip().splitlines()
    block: list[str] = []
    fences = 0
    for line in reversed(lines):
        s = line.strip()
        if not s:
            continue
        if _FENCE_RE.match(s):
            fences += 1
            if block and fences >= 2:
                break
            continue
        step = _step_text(s)
        if step is None:
            if block:
                break
            continue  # trailing prose before the last step line
        fences = 0
        block.append(step)
    if not block:
        return ""
    return "\n".join(reversed(block)) + "\n"


@dataclass
class Cell:
    """One request: an arm of one theory, one replicate."""

    rung: str
    arm: str
    seed: int
    rep: int
    prompt_path: Path

    @property
    def key(self) -> tuple:
        """Resume key (without the model; the row adds it)."""
        return (self.rung, self.arm, self.seed, self.rep)


def cells_in(
    rung_dir: Path, arms: list[str], seeds: list[int] | None, reps: int
) -> list[Cell]:
    """Every (arm, seed, replicate) in ``rung_dir`` that has a rendered prompt."""
    rung = rung_dir.resolve().name
    out: list[Cell] = []
    for sd in sorted(rung_dir.glob("s[0-9][0-9][0-9][0-9]")):
        seed = int(sd.name[1:])
        if seeds is not None and seed not in seeds:
            continue
        for arm in arms:
            p = sd / arm / "prompt.md"
            if p.exists():
                out.extend(Cell(rung, arm, seed, r, p) for r in range(reps))
    return out


def _row_key(row: dict) -> tuple:
    return (row["model"], row["rung"], row["arm"], row["seed"], row["rep"])


def repair_tail(out: Path) -> None:
    """Drop a torn last line (a write cut by a kill) so the next row starts clean."""
    if not out.exists() or out.stat().st_size == 0:
        return
    data = out.read_bytes()
    if data.endswith(b"\n"):
        return
    cut = data.rfind(b"\n") + 1
    out.write_bytes(data[:cut])
    logging.warning("%s: dropped a torn last line (%d bytes)", out, len(data) - cut)


def done_keys(out: Path) -> set[tuple]:
    """Keys of rows already scored in ``out``; ``exception`` rows are not done."""
    keys: set[tuple] = set()
    if not out.exists():
        return keys
    for line in out.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            if row.get("verdict") != "exception":
                keys.add(_row_key(row))
        except (json.JSONDecodeError, KeyError):
            continue
    return keys


def load_rendered(cell: Cell) -> tuple[Theory, Rendered]:
    """Theory and the arm's Rendered (from meta.json, prompt.md and system.md)."""
    arm_dir = cell.prompt_path.parent
    theory = Theory.from_json(
        (arm_dir.parent / "theory.json").read_text(encoding="utf-8")
    )
    meta = json.loads((arm_dir / "meta.json").read_text(encoding="utf-8"))
    rendered = Rendered.from_meta(
        meta,
        prompt=cell.prompt_path.read_text(encoding="utf-8"),
        system=(arm_dir / "system.md").read_text(encoding="utf-8"),
    )
    return theory, rendered


def score(theory: Theory, rendered: Rendered, result: ChatResult) -> dict:
    """Verdict fields for one response.

    A finish reason other than stop/length is infrastructure, not the model, and scores
    ``exception`` so the cell is retried.
    """
    if result.finish_reason not in _FINAL_REASONS:
        return {
            "answer": "",
            "verdict": "exception",
            "steps": 0,
            "route": "",
            "reason": f"finish_reason={result.finish_reason!r}",
            "ignored_lines": 0,
        }
    answer = final_proof_block(strip_reasoning(result.content or ""))
    v = verify(theory, rendered, answer, result.finish_reason or "stop")
    return {
        "answer": answer,
        "verdict": v.verdict,
        "steps": v.steps,
        "route": v.route,
        "reason": v.reason,
        "ignored_lines": v.ignored_lines,
    }


@dataclass(frozen=True)
class Settings:
    """Request settings shared by every cell of a sweep."""

    model: str
    spec_key: str
    extra_args: dict
    context_length: int
    timeout: int
    max_retries: int
    system_prompt: str | None


def _base_row(cell: Cell, st: Settings, rendered: Rendered | None) -> dict:
    return {
        "model": st.model,
        "spec_key": st.spec_key,
        "rung": cell.rung,
        "arm": cell.arm,
        "seed": cell.seed,
        "rep": cell.rep,
        "prompt_sha256": hashlib.sha256(cell.prompt_path.read_bytes()).hexdigest()[:16],
        "sampling": st.extra_args,
        "provider_system_prompt": bool(st.system_prompt),
        "n_prompt_tokens_rendered": rendered.n_tokens if rendered else None,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def output_cap(st: Settings, prompt_tokens: int) -> int:
    """``max_tokens`` for a prompt of ``prompt_tokens`` (cl100k count): the requested cap,
    cut so that prompt and output fit the served context with a 50% tokenizer margin on
    the prompt (vLLM rejects a request whose prompt plus ``max_tokens`` exceeds it)."""
    room = st.context_length - int(1.5 * prompt_tokens) - 1024
    return max(1024, min(int(st.extra_args.get("max_tokens", room)), room))


def run_cell(client: ChatClient, cell: Cell, st: Settings) -> dict:
    """Send one request and return the scored row.

    A failed request returns an ``exception`` row instead of raising.
    """
    t0 = time.time()
    rendered: Rendered | None = None
    try:
        theory, rendered = load_rendered(cell)
        result = client.complete(
            rendered.prompt,
            st.model,
            cell.rep,
            system=rendered.system,
            context_length=st.context_length,
            extra_args=st.extra_args | {"max_tokens": output_cap(st, rendered.n_tokens)},
            request_timeout=st.timeout,
            max_retries=st.max_retries,
        )
    except Exception as err:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        return _base_row(cell, st, rendered) | {
            "verdict": "exception",
            "reason": f"{type(err).__name__}: {str(err)[:500]}",
            "elapsed_s": round(time.time() - t0, 1),
        }
    row = _base_row(cell, st, rendered) | {
        "max_tokens_sent": output_cap(st, rendered.n_tokens),
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "finish_reason": result.finish_reason,
        "reasoning_chars": len(result.reasoning or ""),
        "elapsed_s": round(time.time() - t0, 1),
        "content": result.content,
        "reasoning": result.reasoning,
    }
    row.update(score(theory, rendered, result))
    return row


def summarize(rows: list[dict]) -> str:
    """Per-arm pass rate, cap hits, exceptions and mean completion tokens."""
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["arm"], []).append(r)
    lines = [
        f"{'arm':8s} {'n':>4s} {'pass':>6s} {'length':>6s} {'exc':>4s} "
        f"{'mean out tok':>12s} verdicts"
    ]
    for arm, rs in sorted(by.items()):
        ok = sum(r["verdict"] == "success" for r in rs)
        length = sum(r.get("finish_reason") == "length" for r in rs)
        exc = sum(r["verdict"] == "exception" for r in rs)
        scored = [r for r in rs if r["verdict"] != "exception"]
        tok = sum(r["completion_tokens"] for r in scored) / max(1, len(scored))
        verdicts: dict[str, int] = {}
        for r in rs:
            verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
        lines.append(
            f"{arm:8s} {len(rs):4d} {100 * ok / len(rs):5.1f}% {length:6d} {exc:4d} "
            f"{tok:12.0f} {verdicts}"
        )
    return "\n".join(lines)


def _parse_seeds(spec: str | None) -> list[int] | None:
    if not spec:
        return None
    if "-" in spec and "," not in spec:
        lo, hi = spec.split("-")
        return list(range(int(lo), int(hi) + 1))
    return [int(x) for x in spec.split(",") if x.strip()]


def build_parser() -> argparse.ArgumentParser:
    """CLI options."""
    ap = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n\n", maxsplit=1)[0]
    )
    ap.add_argument(
        "--endpoint", required=True, help="base URL, e.g. http://127.0.0.1:8000/v1"
    )
    ap.add_argument("--api-key", default=os.getenv("HORN_API_KEY", "EMPTY"))
    ap.add_argument("--model", required=True, help="served model name")
    ap.add_argument(
        "--spec-key",
        default=None,
        help="roster key for thinking args and the provider system prompt (default: --model)",
    )
    ap.add_argument("--thinking", choices=["auto", "on", "off"], default="auto")
    ap.add_argument("--rung-dir", required=True)
    ap.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS))
    ap.add_argument(
        "--seeds",
        default=None,
        help="comma list or a-b range; default: every seed in the rung",
    )
    ap.add_argument("--replicates", type=int, default=3)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--context-length", type=int, default=131072)
    ap.add_argument("--stream", dest="stream", action="store_true", default=True)
    ap.add_argument("--no-stream", dest="stream", action="store_false")
    ap.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="read timeout, seconds (between chunks when streaming)",
    )
    ap.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="attempts per cell on retryable errors",
    )
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument(
        "--out", required=True, help="JSONL results file (appended; resumes)"
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="list cells and the request settings, send nothing",
    )
    return ap


def main(argv: list[str] | None = None) -> int:  # pylint: disable=too-many-locals
    """CLI entry point; returns 1 when any cell is missing or failed."""
    a = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    os.environ["HORN_STREAM_COMPLETIONS"] = "1" if a.stream else "0"

    spec_key = a.spec_key or a.model
    extra_args = {"max_tokens": a.max_tokens, "temperature": a.temperature}
    extra_args.update(thinking_args(spec_key, a.thinking))
    st = Settings(
        model=a.model,
        spec_key=spec_key,
        extra_args=extra_args,
        context_length=a.context_length,
        timeout=a.timeout,
        max_retries=a.max_retries,
        system_prompt=provider_system_prompt(spec_key) if a.thinking != "off" else None,
    )

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    repair_tail(out)
    all_cells = cells_in(Path(a.rung_dir), a.arms, _parse_seeds(a.seeds), a.replicates)
    done = done_keys(out)
    todo = [c for c in all_cells if (a.model,) + c.key not in done]
    logging.info(
        "%s: %d cells, %d done, %d to run (settings %s, provider system prompt: %s)",
        a.model,
        len(all_cells),
        len(all_cells) - len(todo),
        len(todo),
        extra_args,
        bool(st.system_prompt),
    )
    if a.dry_run:
        for c in todo[:5]:
            print(asdict(c) | {"prompt_path": str(c.prompt_path)})
        return 0

    endpoint = a.endpoint.rstrip("/")
    client = ChatClient(
        name="horn",
        env_prefix="HORN",
        connection=lambda _: (f"{endpoint}/chat/completions", a.api_key),
        context_length=lambda _: a.context_length,
        system_prompt=lambda _: st.system_prompt,
        retry_backoff_s=15,
        read_timeout_s=a.timeout,
    )
    rows: list[dict] = []
    with out.open("a", encoding="utf-8") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            logging.error("%s is locked by another sweep; refusing to run twice", out)
            return 1
        with ThreadPoolExecutor(a.concurrency) as pool:
            futs = {pool.submit(run_cell, client, c, st): c for c in todo}
            for fut in as_completed(futs):
                c = futs[fut]
                row = fut.result()
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                fh.flush()
                rows.append(row)
                logging.info(
                    "%s %s s%d r%d %s (%s, %s out tok)",
                    c.rung,
                    c.arm,
                    c.seed,
                    c.rep,
                    row["verdict"],
                    row.get("finish_reason"),
                    row.get("completion_tokens", "-"),
                )
    if rows:
        print(summarize(rows))
    failed = sum(r["verdict"] == "exception" for r in rows)
    n_done_before = len(all_cells) - len(todo)
    missing = len(todo) - len(rows)
    print(
        f"cells {len(all_cells)}: done before {n_done_before}, scored now {len(rows) - failed}, "
        f"failed {failed}, missing {missing}"
    )
    return 1 if failed or missing else 0


if __name__ == "__main__":
    sys.exit(main())
