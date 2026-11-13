"""Probe whether a Bedrock endpoint honours an output cap above the model-card cap.

The published Horn cells of DeepSeek V3.1 and Nemotron Super ran through the Converse API
in us-east-2 with a 131,072-token cap, and most of them used more output than the caps on
the model cards (8K and 32K). This script
runs a few Horn cells with a larger cap through one transport and reports, per cell, the
completion tokens and the finish reason. A completion longer than the model-card cap
shows that the endpoint honours the larger one.

Rows go to ``results/cap_probe/<label>.jsonl`` (a rerun skips the cells already there).
With ``--push`` the file is also uploaded once, as
``probes/cap-probe--<label>--<stamp>.jsonl`` under ``bedrock_trio.RESULTS_S3``.

usage::

    python rebuttal/cap_probe.py --transport mantle --region us-east-1 \\
        --model deepseek-v3.1 --arm lem --max-tokens 65536 --seeds 100,101 --push
    python rebuttal/cap_probe.py --transport converse --region us-east-2 \\
        --model nemotron-3-super-120b-a12b --arm pad --max-tokens 131072 --seeds 100-103
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bedrock_trio as bt  # noqa: E402  pylint: disable=wrong-import-position

from smolbench.evals.results_store import format_run_ts, utcnow  # noqa: E402  pylint: disable=wrong-import-position

PROBE_DIR = bt.RESULTS_DIR / "cap_probe"
# Rungs of the probe are kept apart from the rungs of the study runs.
PROBE_RUNGS = bt.RUNGS_DIR / "cap_probe"
REASONING = {"reasoning_effort": "high"}
# Output caps listed on the Bedrock model cards.
CARD_CAPS = {"deepseek-v3.1": 8192, "nemotron-3-super-120b-a12b": 32768}
# Ids on the Converse API (bedrock-runtime), from the published cells.
CONVERSE_IDS = {
    "deepseek-v3.1": "deepseek.v3-v1:0",
    "nemotron-3-super-120b-a12b": "nvidia.nemotron-super-3-120b",
}
# Ids on bedrock-mantle, from the notebook's probes.
MANTLE_IDS = {
    "deepseek-v3.1": "deepseek.v3.1",
    "nemotron-3-super-120b-a12b": "nvidia.nemotron-super-3-120b",
}


def run_probe(a: argparse.Namespace) -> list[dict]:
    """Run the outstanding cells and return every row of the label's file."""
    sweep = bt.load_sweep()
    seeds = sweep.seed_list(a.seeds)
    # The digest check needs the four paper arms, so they are rendered with the probe's arm.
    arms = tuple(dict.fromkeys(bt.HORN_PAPER_ARMS + (a.arm,)))
    rung = bt.render_horn_rung(bt.horn_m(a.model), seeds, rungs_dir=PROBE_RUNGS, arms=arms)
    if a.render_only:
        return []
    label = f"{a.transport}--{a.region}--{a.model}--{a.arm}--cap{a.max_tokens}"
    out = PROBE_DIR / f"{label}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    # A token is minted for the probe's own region; one left in the environment may be
    # for another region or expired.
    os.environ.pop("AWS_BEARER_TOKEN_BEDROCK", None)
    bt.mint_token(a.region)
    if a.transport == "mantle":
        model = replace(bt.TRIO[a.model], bedrock_id=MANTLE_IDS[a.model])
        bt.run_horn(
            model, a.region, REASONING, rung, seeds, 1, concurrency=4, out=out, arms=(a.arm,),
            max_tokens=a.max_tokens,
        )  # fmt: skip
    else:
        path = bt.REPO_ROOT / "scripts" / "deduction" / "horn" / "bedrock_sweep.py"
        spec = importlib.util.spec_from_file_location("smolbench_horn_bedrock_sweep", path)
        assert spec is not None and spec.loader is not None
        bedrock_sweep = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = bedrock_sweep
        spec.loader.exec_module(bedrock_sweep)
        bedrock_sweep.main([
            "--model", CONVERSE_IDS[a.model], "--spec-key", a.model, "--region", a.region,
            "--rung-dir", str(rung), "--arms", a.arm, "--seeds", a.seeds, "--replicates", "1",
            "--max-tokens", str(a.max_tokens),
            "--context-length", str(bt.HORN_CONTEXT_LENGTH),
            "--extra-fields", json.dumps(REASONING), "--out", str(out),
        ])  # fmt: skip
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
    if a.push and rows:
        key = bt.push_file(out, bt.RESULTS_S3, f"probes/cap-probe--{label}--{format_run_ts(utcnow())}.jsonl")
        print(f"pushed {key}")
    return rows


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; prints one line per cell."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--transport", choices=("mantle", "converse"), required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--model", choices=sorted(CONVERSE_IDS), required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--max-tokens", type=int, required=True)
    ap.add_argument("--seeds", default="100,101", help="comma list or a-b range")
    ap.add_argument("--push", action="store_true", help="upload the rows file to the bucket")
    ap.add_argument("--render-only", action="store_true", help="render the rung and stop")
    a = ap.parse_args(argv)
    card_cap = CARD_CAPS[a.model]
    for r in run_probe(a):
        toks = r.get("completion_tokens")
        over = "-" if toks is None else str(toks > card_cap)
        print(
            f"{a.transport} {a.region} {a.model} {a.arm} s{r['seed']} cap={a.max_tokens} "
            f"verdict={r['verdict']} finish={r.get('finish_reason')} completion_tokens={toks} "
            f"over_card_cap({card_cap})={over} error={str(r.get('error') or r.get('reason') or '')[:300]}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
