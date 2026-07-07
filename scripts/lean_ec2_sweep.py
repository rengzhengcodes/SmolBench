"""Drive the Lean 4 deduction sweep over the >200B trio on one EC2 spot box.

The trio's base + LoRA variants cannot share a single sweep config: the lean
runner interleaves ``models`` at the innermost loop, but the EC2 box serves
ONE model at a time (``ec2.serve_model`` swaps the vLLM container). So this
driver provisions once, then for each model-variant does
``serve_model(key)`` -> ``runner.sweep(single-model config)`` into a shared
per-phase ``run_dir`` (rows are keyed by ``(model, theorem, k, rung,
rollout)``, so variants never collide), and tears the box down at the end --
the same serve-swap pattern ``InductionExperiment`` uses for the induction
archetypes.

Runs on ``.venv-lean`` (the sweep verifies proofs via ``lean_dojo``). Needs
AWS creds for provisioning and, for the private LoRA repos, ``HF_TOKEN``
exported BEFORE this script provisions (the token is baked into the instance
at provision time -- see smolbench/evals/ec2.py).

Examples
--------
    # Base-only pilot (no LoRA repos yet):
    .venv-lean/bin/python scripts/lean_ec2_sweep.py --phase pilot

    # Full base+LoRA headline once the adapters are trained & pushed:
    HF_TOKEN=hf_... .venv-lean/bin/python scripts/lean_ec2_sweep.py --phase headline \
        --lora-llama    <org>/llama-31-405b-lean-lora \
        --lora-nemotron <org>/nemotron-ultra-253b-lean-lora \
        --lora-qwen     <org>/qwen3-235b-a22b-lean-lora
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# EC2_EXPERIMENT_TAG is captured at import time (see ec2.py's env-timing note),
# so set the experiment's identity BEFORE importing ec2. Isolate this
# experiment's instance + state from notebooks/periodic and notebooks/chromatic.
os.environ.setdefault("EC2_EXPERIMENT_TAG", "lean-deduction")
os.environ.setdefault("EC2_STATE_FILE", str(_REPO_ROOT / ".ec2_state_lean.json"))

# The base-model trio: (EC2_DEPLOY_SPECS key, LoRA-arg name). The three base
# keys already exist in EC2_DEPLOY_SPECS (qwen3-235b-a22b added in Phase 0).
TRIO = [
    ("llama-31-405b", "lora_llama"),
    ("nemotron-ultra-253b", "lora_nemotron"),
    ("qwen3-235b-a22b", "lora_qwen"),
]

# Shared sweep knobs. max_tokens/request_timeout are sized for the reasoning
# arm (nemotron-ultra); non-reasoning models stop early regardless.
_COMMON = dict(
    seed=1776,
    temperature=0.7,
    max_tokens=32768,
    request_timeout=1200,
    max_retries=2,
    dojo_timeout=300,
    concurrent_gen=True,
    skip_trivial=True,
    theorem_workers=8,
    k={"strategy": "last"},
)

PHASES = {
    # Cheap validation of serving + wiring + base-vs-LoRA signal.
    "pilot": {
        **_COMMON,
        "run_name": "lean_trio_pilot",
        "n_rollouts": 1,
        "theorems": {"source": "replay_passing", "kind": "novel_premises", "split": "val"},
        "rungs": ["stepk:1", "hint:2", "noise:3", "hint:3"],
    },
    # The headline generalization sweep: all 10 rungs on novel_premises/test.
    "headline": {
        **_COMMON,
        "run_name": "lean_trio_headline",
        "n_rollouts": 3,
        "theorems": {"source": "replay_passing", "kind": "novel_premises", "split": "test"},
        "rungs": [
            "stepk:0", "stepk:1", "stepk:2",
            "hint:0", "hint:1", "hint:2", "hint:3", "hint:4",
            "noise:3", "noise:4",
        ],
    },
}


def _variants(args, ec2) -> list[dict]:
    """Resolve the model-variant list, registering LoRA deploy specs as needed.

    Base variants reuse the existing EC2_DEPLOY_SPECS entries. For each LoRA
    repo supplied on the CLI, register a runtime deploy spec that serves the
    adapter on top of the base via vLLM's ``--enable-lora`` (the spec key --
    which the client sends as ``model=`` -- is the lora-module name vLLM routes
    on). Pass ``--merged-lora`` if the repo is a *merged* full checkpoint
    rather than an adapter (then it is just another ``hf_model_id``).
    """
    variants: list[dict] = []
    for base_key, lora_attr in TRIO:
        variants.append({"key": base_key, "display": f"{base_key}-base"})
        lora_repo = getattr(args, lora_attr)
        if not lora_repo:
            continue
        lora_key = f"{base_key}-lean-lora"
        if args.merged_lora:
            spec = {"hf_model_id": lora_repo, "tp": 8, "max_model_len": 131072}
        else:
            base_spec = ec2.EC2_DEPLOY_SPECS[base_key]
            spec = {
                "hf_model_id": base_spec["hf_model_id"],
                "tp": 8,
                "max_model_len": 131072,
                "vllm_args": [
                    "--enable-lora",
                    "--max-lora-rank", str(args.lora_rank),
                    "--lora-modules", f"{lora_key}={lora_repo}",
                ],
            }
        ec2.EC2_DEPLOY_SPECS[lora_key] = spec  # runtime registration
        variants.append({"key": lora_key, "display": lora_key})
    return variants


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--phase", choices=list(PHASES), default="pilot")
    p.add_argument("--lora-llama", dest="lora_llama", default=None, help="HF repo of the Llama-3.1-405B Lean LoRA")
    p.add_argument("--lora-nemotron", dest="lora_nemotron", default=None, help="HF repo of the Nemotron-Ultra Lean LoRA")
    p.add_argument("--lora-qwen", dest="lora_qwen", default=None, help="HF repo of the Qwen3-235B Lean LoRA")
    p.add_argument("--merged-lora", action="store_true", help="LoRA repos are merged full checkpoints, not adapters")
    p.add_argument("--lora-rank", type=int, default=16, help="must be >= the adapters' rank for --enable-lora")
    p.add_argument("--no-teardown", action="store_true", help="leave the instance up after the sweep")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    from smolbench.evals import ec2
    from smolbench.deduction.lean import runner

    config = dict(PHASES[args.phase])
    variants = _variants(args, ec2)
    run_dir = runner.results_root() / "runs" / config["run_name"]

    lora_missing = [k for k, a in TRIO if not getattr(args, a)]
    if lora_missing:
        print(f"note: no LoRA repo for {lora_missing} -> running BASE only for those", flush=True)

    ec2.provision_spot_instance()
    try:
        for v in variants:
            cfg = {**config, "models": [{"provider": "ec2", "model": v["key"], "display_name": v["display"]}]}
            print(f"=== {args.phase}: serving {v['key']} -> sweep display={v['display']} ===", flush=True)
            with ec2.serve_model(v["key"]):
                runner.sweep(cfg, run_dir)
        runner.write_run_analysis(run_dir)
        print(f"done: {args.phase} sweep -> {run_dir}", flush=True)
    finally:
        if not args.no_teardown:
            ec2.shutdown_instance()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
