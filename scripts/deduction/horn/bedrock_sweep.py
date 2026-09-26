"""Run Horn-bench rungs against AWS Bedrock (Converse API), one request per cell.

Same cells, rows, resume keys and scoring as ``sweep.py``; only the transport differs:
``bedrock-runtime`` ``converse_stream`` with a long-term Bedrock API key
(``AWS_BEARER_TOKEN_BEDROCK`` in the repo's ``.env``) or the caller's AWS session, the system
message from ``system.md``, the prompt as the user message, a sampling temperature, an
output cap cut per cell so that prompt and output fit ``--context-length`` (Bedrock
rejects a request whose prompt plus ``maxTokens`` exceeds the model's context), and
optional model-specific request fields (``--extra-fields`` JSON, for example a thinking
switch). Reasoning content blocks are kept apart from the answer text;
the answer is the last block of ``derive`` lines in the text after inline reasoning is
stripped. ``stopReason == max_tokens`` scores as ``length``.

usage::

    python scripts/deduction/horn/bedrock_sweep.py --model zai.glm-4.7-flash \\
        --spec-key glm-4.7-flash --region us-east-2 --rung-dir <rung> --arms lem \\
        --replicates 1 --out results/glm-4.7-flash.jsonl
"""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for _p in (str(REPO_ROOT), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# pylint: disable=wrong-import-position
import sweep  # noqa: E402  (scripts/deduction/horn/sweep.py, same directory)
from smolbench.deduction.horn.render import ARMS  # noqa: E402
from smolbench.evals.openai_compat import ChatResult  # noqa: E402

_STOP_TO_FINISH = {"end_turn": "stop", "stop_sequence": "stop", "max_tokens": "length"}


@dataclass(frozen=True)
class BedrockSettings:
    """Request settings shared by every cell."""

    model: str
    spec_key: str
    region: str
    max_tokens: int
    temperature: float
    extra_fields: dict | None
    timeout: int
    max_retries: int
    context_length: int = 131072

    @property
    def sampling(self) -> dict:
        """What the row records as the sampling parameters."""
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "extra_fields": self.extra_fields,
        }


def _client(st: BedrockSettings):
    """A bedrock-runtime client. ``AWS_BEARER_TOKEN_BEDROCK`` (a long-term Bedrock API
    key, loaded from the repo's ``.env``) is used when set; otherwise the usual
    credential chain (an ``aws login`` session)."""
    import boto3  # pylint: disable=import-outside-toplevel
    from botocore.config import Config  # pylint: disable=import-outside-toplevel
    from dotenv import load_dotenv  # pylint: disable=import-outside-toplevel

    load_dotenv(REPO_ROOT / ".env")
    return boto3.client(
        "bedrock-runtime",
        region_name=st.region,
        config=Config(
            read_timeout=st.timeout,
            connect_timeout=30,
            retries={"max_attempts": st.max_retries, "mode": "adaptive"},
        ),
    )


def output_cap(st: BedrockSettings, prompt_tokens: int) -> int:
    """``max_tokens`` for a prompt of ``prompt_tokens`` (cl100k count): the cap, cut so that
    prompt and output fit the context with a 50% tokenizer margin on the prompt."""
    room = st.context_length - int(1.5 * prompt_tokens) - 1024
    return max(1024, min(st.max_tokens, room))


def converse(
    client, st: BedrockSettings, system: str, prompt: str, prompt_tokens: int = 0
) -> ChatResult:
    """One streamed Converse call, collected into a ``ChatResult``."""
    kw = {
        "modelId": st.model,
        "system": [{"text": system}],
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {
            "maxTokens": output_cap(st, prompt_tokens),
            "temperature": st.temperature,
        },
    }
    if st.extra_fields:
        kw["additionalModelRequestFields"] = st.extra_fields
    text: list[str] = []
    reasoning: list[str] = []
    stop = None
    usage: dict = {}
    for ev in client.converse_stream(**kw)["stream"]:
        if "contentBlockDelta" in ev:
            d = ev["contentBlockDelta"]["delta"]
            if "text" in d:
                text.append(d["text"])
            elif "reasoningContent" in d:
                reasoning.append(d["reasoningContent"].get("text", ""))
        elif "messageStop" in ev:
            stop = ev["messageStop"].get("stopReason")
        elif "metadata" in ev:
            usage = ev["metadata"].get("usage", {})
    return ChatResult(
        content="".join(text),
        reasoning="".join(reasoning) or None,
        prompt_tokens=usage.get("inputTokens", 0),
        completion_tokens=usage.get("outputTokens", 0),
        cached_prompt_tokens=usage.get("cacheReadInputTokens", 0),
        total_tokens=usage.get("totalTokens"),
        model=st.model,
        finish_reason=_STOP_TO_FINISH.get(stop or "", stop or "unknown"),
    )


def run_cell(client, cell: sweep.Cell, st: BedrockSettings) -> dict:
    """Send one request and return the scored row (an ``exception`` row on failure)."""
    t0 = time.time()
    base = {
        "model": st.model,
        "spec_key": st.spec_key,
        "rung": cell.rung,
        "arm": cell.arm,
        "seed": cell.seed,
        "rep": cell.rep,
        "provider": f"bedrock:{st.region}",
        "sampling": st.sampling | {"context_length": st.context_length},
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        theory, rendered = sweep.load_rendered(cell)
        base["n_prompt_tokens_rendered"] = rendered.n_tokens
        result = converse(client, st, rendered.system, rendered.prompt, rendered.n_tokens)
    except Exception as err:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        return base | {
            "verdict": "exception",
            "reason": f"{type(err).__name__}: {str(err)[:500]}",
            "elapsed_s": round(time.time() - t0, 1),
        }
    row = base | {
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "finish_reason": result.finish_reason,
        "reasoning_chars": len(result.reasoning or ""),
        "elapsed_s": round(time.time() - t0, 1),
        "content": result.content,
        "reasoning": result.reasoning,
    }
    row.update(sweep.score(theory, rendered, result))
    return row


def build_parser() -> argparse.ArgumentParser:
    """CLI options."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--model", required=True, help="Bedrock model id")
    ap.add_argument("--spec-key", default=None, help="roster key recorded in the rows")
    ap.add_argument("--region", default="us-east-2")
    ap.add_argument("--rung-dir", required=True)
    ap.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS))
    ap.add_argument("--seeds", default=None, help="comma list or a-b range")
    ap.add_argument("--replicates", type=int, default=3)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument(
        "--context-length",
        type=int,
        default=131072,
        help="prompt + output must fit this; the cap is cut per cell to make room",
    )
    ap.add_argument(
        "--extra-fields",
        default=None,
        help="JSON for additionalModelRequestFields (e.g. a thinking switch)",
    )
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--max-retries", type=int, default=6)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:  # pylint: disable=too-many-locals
    """CLI entry point; returns 1 when any cell is missing or failed."""
    a = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    st = BedrockSettings(
        model=a.model,
        spec_key=a.spec_key or a.model,
        region=a.region,
        max_tokens=a.max_tokens,
        temperature=a.temperature,
        extra_fields=json.loads(a.extra_fields) if a.extra_fields else None,
        timeout=a.timeout,
        max_retries=a.max_retries,
        context_length=a.context_length,
    )
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sweep.repair_tail(out)
    all_cells = sweep.cells_in(Path(a.rung_dir), a.arms, sweep._parse_seeds(a.seeds), a.replicates)  # pylint: disable=protected-access
    done = sweep.done_keys(out)
    todo = [c for c in all_cells if (a.model,) + c.key not in done]
    logging.info("%s: %d cells, %d done, %d to run (%s)", a.model, len(all_cells), len(all_cells) - len(todo), len(todo), st.sampling)
    if a.dry_run:
        for c in todo[:5]:
            print(asdict(c) | {"prompt_path": str(c.prompt_path)})
        return 0
    client = _client(st)
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
                logging.info("%s %s s%d r%d %s (%s, %s out tok, %ss)", c.rung, c.arm, c.seed, c.rep, row["verdict"], row.get("finish_reason"), row.get("completion_tokens", "-"), row.get("elapsed_s"))
    if rows:
        print(sweep.summarize(rows))
    failed = sum(r["verdict"] == "exception" for r in rows)
    missing = len(todo) - len(rows)
    print(f"cells {len(all_cells)}: done before {len(all_cells) - len(todo)}, scored now {len(rows) - failed}, failed {failed}, missing {missing}")
    return 1 if failed or missing else 0


if __name__ == "__main__":
    sys.exit(main())
