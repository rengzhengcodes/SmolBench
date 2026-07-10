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

**LoRA delivery.** The adapters were trained on the BF16 bases but are served
on the FP8 bases (both arms share the same FP8 base, so the base-vs-LoRA delta
isolates the adapter). Each adapter's target modules were statically verified
present in its FP8 base index. The read-only HF token cannot push adapters to
the Hub, so instead of ``--lora-modules name=<hf_repo>`` the LoRA specs carry an
``adapters`` block: the box stages the adapter from S3 (its instance profile
grants read) into the mounted hub cache before launch, and vLLM loads it from
the local path (see ``ec2.py`` ``_serve``). This needs ``EC2_S3_MODEL_CACHE``
set at provision time (attaches the instance profile) -- source
``notebooks/periodic/keys.env`` first.

Runs on ``.venv-lean`` (the sweep verifies proofs via ``lean_dojo``). Needs
AWS creds for provisioning + ``HF_TOKEN`` (the FP8 bases are ungated, but the
token is baked in for parity and future gated adds).

Examples
--------
    set -a; source notebooks/periodic/keys.env; set +a

    # Cheap capped pilot, base + LoRA for all three (serve-swapped):
    .venv-lean/bin/python scripts/lean_ec2_sweep.py --phase pilot

    # Base-only (skip the LoRA arms):
    .venv-lean/bin/python scripts/lean_ec2_sweep.py --phase pilot --no-lora

    # Full base+LoRA headline once the pilot gate is green:
    .venv-lean/bin/python scripts/lean_ec2_sweep.py --phase headline
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
# The LoRA arms need vLLM >= v0.23.0: v0.11.1 (the ec2.py default, since periodic's
# keys.env doesn't override it) crashes at the LoRA logits processor for adapters
# that add no vocab ("expanded size (0) must match (256)"). v0.23.0 (chromatic's pin)
# serves them fine -- confirmed live 2026-07-08. Self-contained so periodic is untouched.
os.environ.setdefault("EC2_VLLM_IMAGE", "vllm/vllm-openai:v0.23.0")

# The base-model trio (EC2_DEPLOY_SPECS keys). Each has a LoRA adapter in S3
# under <lora-s3-prefix>/<base_key>/ (adapter_config.json + adapter_model.safetensors).
TRIO = ["llama-31-405b", "nemotron-ultra-253b", "qwen3-235b-a22b"]

#: Where the trained adapters live (same bucket as the model cache; the serving
#: box's instance profile grants read). Overridable via --lora-s3-prefix.
_ADAPTER_S3_PREFIX = "s3://smolbench-model-cache-414266451290/lean-train-checkpoints"

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
    # Cheap validation of serving + wiring + base-vs-LoRA signal: a seeded
    # 30-theorem sample of novel_premises/val, 4 rungs, 1 rollout, 6 variants.
    "pilot": {
        **_COMMON,
        "run_name": "lean_trio_pilot",
        "n_rollouts": 1,
        "theorems": {"source": "replay_passing", "kind": "novel_premises",
                     "split": "val", "limit": 30, "seed": 1776},
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

    Base variants reuse the existing EC2_DEPLOY_SPECS entries. Each LoRA variant
    serves the S3-hosted adapter on top of the SAME FP8 base via vLLM's
    ``--enable-lora``: the ``adapters`` block tells the box to stage the adapter
    from S3 into ``/opt/hf-cache/lora/<lora_key>`` (mounted into the container at
    ``/root/.cache/huggingface/lora/<lora_key>``) before launch, and
    ``--lora-modules`` points vLLM at that local path. The spec key (which the
    client sends as ``model=``) is the lora-module name vLLM routes on.
    """
    variants: list[dict] = []
    prefix = args.lora_s3_prefix.rstrip("/")
    # Qwen3-235B-A22B-FP8 can't serve on vLLM v0.23.0: block-FP8 requires each
    # TP shard's gate/up output divisible by 128, but 1536/8=192 isn't (and TP=4
    # hangs at NVLink multicast init). Its config also caps context at 40960.
    # Serve BF16 instead -- no block-quant constraint at TP=8, it's the adapter's
    # native precision, and 235B BF16 (~470 GB) fits 8x80 GB. (405B/Nemotron stay
    # FP8: 405B BF16 would not fit.) Carry the precision difference as a caveat.
    _qwen = ec2.EC2_DEPLOY_SPECS.get("qwen3-235b-a22b")
    if _qwen is not None:
        _qwen["hf_model_id"] = "Qwen/Qwen3-235B-A22B"
        _qwen["max_model_len"] = 40960
    for base_key in TRIO:
        variants.append({"key": base_key, "display": f"{base_key}-base"})
        if args.no_lora:
            continue
        lora_key = f"{base_key}-lean-lora"
        base_spec = ec2.EC2_DEPLOY_SPECS[base_key]
        container_path = f"/root/.cache/huggingface/lora/{lora_key}"
        ec2.EC2_DEPLOY_SPECS[lora_key] = {
            "hf_model_id": base_spec["hf_model_id"],
            "tp": base_spec.get("tp", 8),
            "max_model_len": base_spec.get("max_model_len", 131072),
            "vllm_args": [
                *base_spec.get("vllm_args", []),
                "--enable-lora",
                "--max-lora-rank", str(args.lora_rank),
                "--lora-modules", f"{lora_key}={container_path}",
            ],
            # region: the box may land in a different region than the bucket
            # (spot capacity), so the S3 sync must target the bucket's region.
            "adapters": [{"name": lora_key, "s3": f"{prefix}/{base_key}", "region": args.lora_region}],
        }
        variants.append({"key": lora_key, "display": lora_key})
    return variants


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--phase", choices=list(PHASES), default="pilot")
    p.add_argument("--lora-s3-prefix", default=_ADAPTER_S3_PREFIX,
                   help="S3 prefix with <base_key>/adapter_model.safetensors for each model")
    p.add_argument("--no-lora", action="store_true", help="run base variants only (skip the LoRA arms)")
    p.add_argument("--lora-rank", type=int, default=16, help="--max-lora-rank; must be >= the adapters' rank (16)")
    p.add_argument("--lora-region", default=os.environ.get("EC2_S3_CACHE_REGION", "us-west-2"),
                   help="AWS region of the adapter S3 bucket (the box may run in another region)")
    p.add_argument("--only", default=None,
                   help="comma-separated variant keys to restrict to (e.g. the Nemotron-first smoke)")
    p.add_argument("--limit", type=int, default=None,
                   help="override the phase's theorem count (e.g. --limit 1 for a warm-theorem smoke)")
    p.add_argument("--theorem-workers", type=int, default=None,
                   help="override parallel Dojo verifiers (local RAM-bound; lower if verification OOMs)")
    p.add_argument("--no-teardown", action="store_true", help="leave the instance up after the sweep")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # The sweep verifies proofs via lean_dojo, which shells out to `lake`/`elan`.
    # Ensure the elan toolchain is on PATH (installed at ~/.elan/bin but often not
    # exported) or every theorem SANITY-FAILs with "lake: command not found".
    elan_bin = Path.home() / ".elan" / "bin"
    if elan_bin.is_dir() and str(elan_bin) not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = f"{elan_bin}{os.pathsep}{os.environ.get('PATH', '')}"

    from smolbench.evals import ec2
    from smolbench.deduction.lean import runner

    config = dict(PHASES[args.phase])
    if args.limit is not None:
        # Override the phase's theorem count (seeded sample); e.g. --limit 1 smoke.
        config["theorems"] = {**config["theorems"], "limit": args.limit, "seed": config["theorems"].get("seed", 1776)}
    if args.theorem_workers is not None:
        config["theorem_workers"] = args.theorem_workers
    variants = _variants(args, ec2)
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        variants = [v for v in variants if v["key"] in wanted]
        if not variants:
            raise SystemExit(f"--only {sorted(wanted)} matched no variant of {[v for v in TRIO]}")
    run_dir = runner.results_root() / "runs" / config["run_name"]

    if args.no_lora:
        print("note: --no-lora -> BASE variants only", flush=True)

    ec2.provision_spot_instance()
    failures: list[tuple[str, str]] = []
    try:
        for v in variants:
            cfg = {**config, "models": [{"provider": "ec2", "model": v["key"], "display_name": v["display"]}]}
            print(f"=== {args.phase}: serving {v['key']} -> sweep display={v['display']} ===", flush=True)
            # Isolate each variant: a serve/sweep failure (e.g. one arm that vLLM
            # can't load) is logged and skipped so the rest of the pass still runs
            # and produces data, instead of aborting the whole (expensive) sweep.
            try:
                with ec2.serve_model(v["key"]):
                    runner.sweep(cfg, run_dir)
            except Exception as exc:  # noqa: BLE001
                msg = (str(exc).splitlines() or [type(exc).__name__])[0][:200]
                failures.append((v["key"], msg))
                print(f"!! {v['key']} FAILED — skipping: {type(exc).__name__}: {msg}", flush=True)
        runner.write_run_analysis(run_dir)
        if failures:
            print(f"note: {len(failures)}/{len(variants)} variant(s) failed: {failures}", flush=True)
        print(f"done: {args.phase} sweep -> {run_dir}", flush=True)
    finally:
        if not args.no_teardown:
            ec2.shutdown_instance()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
