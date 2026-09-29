"""Write ``smolbench/deduction/horn/iclr.json``, the record that ``horn.repro`` reads.

The record holds the protocol of the ICLR 2027 Horn runs, each model's chain length and
serving settings, a digest of every served theory, and the published pass rates. It was
built once from the served rungs and the results summaries:

    python scripts/deduction/horn/build_iclr_protocol.py \\
        --rungs /home/fisherxue/horn_results_2026-09-26/rungs_roster2 \\
        --results notebooks/deduction/results

``--rungs`` is the directory the runs were served from (``m<m>/s<seed>/...``);
``--results`` holds ``iclr/horn_summary.json`` and ``default/horn_summary.json`` from
``notebooks/deduction/analysis/horn_results.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from smolbench.deduction.horn.cli import (  # noqa: E402
    DEFAULT_ALT_PER_LEMMA,
    DEFAULT_HEIGHT,
    parse_seeds,
)
from smolbench.deduction.horn.render import ARMS  # noqa: E402
from smolbench.deduction.horn.repro import PROTOCOL_PATH, rung_digests  # noqa: E402

SEEDS = "100-199"
BEDROCK_REGION = "us-east-2"
THINKING_HIGH = {"reasoning_effort": "high"}

#: Models in table order (families small to large): backend and run notes.
MODELS: dict[str, dict] = {
    "gemma-4-e2b": {"backend": "vllm"},
    "gemma-4-12b": {"backend": "vllm"},
    "gemma-4-31b": {"backend": "vllm"},
    "nemotron-3-nano-4b": {"backend": "vllm"},
    "nemotron-3-nano-30b-a3b": {
        "backend": "bedrock",
        "bedrock_model_id": "nvidia.nemotron-nano-3-30b",
        "bedrock_extra_fields": THINKING_HIGH,
        "notes": "1 cell never scored (Bedrock error), counted as a failure",
    },
    "nemotron-3-super-120b-a12b": {
        "backend": "bedrock",
        "bedrock_model_id": "nvidia.nemotron-super-3-120b",
        "bedrock_extra_fields": THINKING_HIGH,
    },
    "qwen3.5-27b": {"backend": "vllm"},
    "qwen3.5-122b-a10b": {"backend": "vllm"},
    "qwen3.5-397b-a17b": {"backend": "vllm", "notes": "m set by hand (not calibrated); FP8 checkpoint"},
    "deepseek-v4-flash": {"backend": "vllm", "notes": "FP8 KV cache"},
    "deepseek-v3.1": {
        "backend": "bedrock",
        "bedrock_model_id": "deepseek.v3-v1:0",
        "bedrock_extra_fields": THINKING_HIGH,
        "notes": "120 rows contain a stray token inserted by the provider (lem 11, pad 42, disc 33, both 34)",
    },
    "glm-4.7-flash": {
        "backend": "bedrock",
        "bedrock_model_id": "zai.glm-4.7-flash",
        "bedrock_extra_fields": THINKING_HIGH,
    },
    "glm-4.7": {
        "backend": "bedrock",
        "bedrock_model_id": "zai.glm-4.7",
        "bedrock_extra_fields": THINKING_HIGH,
    },
    "ministral-3-3b": {
        "backend": "bedrock",
        "bedrock_model_id": "mistral.ministral-3-3b-instruct",
        "notes": "instruct checkpoint, no thinking; lem below 60% at m=1",
    },
    "ministral-3-8b": {
        "backend": "bedrock",
        "bedrock_model_id": "mistral.ministral-3-8b-instruct",
        "notes": "instruct checkpoint, no thinking; lem below 60% at m=1",
    },
    "ministral-3-14b": {
        "backend": "bedrock",
        "bedrock_model_id": "mistral.ministral-3-14b-instruct",
        "notes": "instruct checkpoint, no thinking",
    },
}


def _results(summary: dict) -> dict:
    out = {arm: round(100 * summary["arms"][arm]["mean"], 1) for arm in ARMS}
    for name, d in summary["deltas"].items():
        out[name] = round(d["mean"] if isinstance(d, dict) else d, 1)
    return out


def main(argv: list[str] | None = None) -> int:
    """Build and write the record."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--rungs", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=PROTOCOL_PATH)
    a = ap.parse_args(argv)
    from smolbench.evals.providers.ec2 import (  # pylint: disable=import-outside-toplevel
        EC2_VLLM_IMAGE,
        EC2_DEPLOY_SPECS,
    )

    summaries = {
        mode: json.loads((a.results / mode / "horn_summary.json").read_text(encoding="utf-8"))["models"]
        for mode in ("iclr", "default")
    }
    models: dict[str, dict] = {}
    for key, extra in MODELS.items():
        entry: dict = {"m": summaries["iclr"][key]["m"], **extra}
        if entry["backend"] == "bedrock":
            entry["bedrock_region"] = BEDROCK_REGION
        else:
            spec = EC2_DEPLOY_SPECS[key]
            args = spec.get("vllm_args", [])
            entry["hf_model_id"] = spec["hf_model_id"]
            entry["revision"] = args[args.index("--revision") + 1]
        entry["results"] = {mode: _results(summaries[mode][key]) for mode in summaries}
        models[key] = entry
    seeds = parse_seeds(SEEDS)
    levels = sorted({e["m"] for e in models.values()})
    record = {
        "description": (
            "Protocol of the Horn benchmark runs in the ICLR 2027 submission. Read by "
            "smolbench.deduction.horn.repro; built by scripts/deduction/horn/build_iclr_protocol.py."
        ),
        "seeds": SEEDS,
        "replicates": 3,
        "arms": list(ARMS),
        "height": DEFAULT_HEIGHT,
        "alt_per_lemma": DEFAULT_ALT_PER_LEMMA,
        "sampling": {"temperature": 0.7, "max_tokens": 131072, "context_length": 131072},
        "scoring": "iclr",
        "vllm_image": EC2_VLLM_IMAGE,
        "results_note": (
            "Pass rates in percent: mean over seeds of the per-seed pass rate over 3 replicates. "
            "Deltas are seed-paired, in points. 'iclr' uses the stored verdicts; 'default' rescores "
            "with the default extractor. The iclr Qwen3.5-122B row is the final value; the "
            "submitted table was built before that model's run finished (both 24.7 there)."
        ),
        "models": models,
        "rung_digests": {str(m): rung_digests(a.rungs / f"m{m}", seeds) for m in levels},
    }
    a.out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {a.out}: {len(models)} models, levels {levels}, {len(seeds)} seeds each")
    return 0


if __name__ == "__main__":
    sys.exit(main())
