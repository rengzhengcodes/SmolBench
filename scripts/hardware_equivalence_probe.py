"""Does the g6e.4xlarge -> g6e.2xlarge substitution change what a model generates?

WHY
---
Two 2026-08-14 repair lanes (nemotron-3-nano-4b, ministral-3-3b) regenerate
cells on g6e.2xlarge although their original cells came from g6e.4xlarge. Both
sizes carry exactly ONE L40S 48GB and run tp=1 with the same image and vLLM
args, so the substitution *should* be generation-neutral -- host vCPU/RAM
affect throughput, not sampling. "Should" is an argument, not evidence.

THE DESIGN, AND WHY THE BASELINE IS THE WHOLE POINT
--------------------------------------------------
Comparing one 4xlarge pass against one 2xlarge pass cannot answer the
question. vLLM is not guaranteed bitwise-reproducible even on ONE box: with
continuous batching, what else is in flight changes reduction order and hence
numerics, and this repo has already recorded a model that was
non-deterministic despite a fixed seed. A naive cross-size comparison would
therefore attribute vLLM's own jitter to the hardware.

So we measure both:

  BASELINE   pass A1 vs A2 -- same box, same seed, same prompts, back to back.
             This is the noise floor: how reproducible this model is at all.
  CROSS-SIZE pass A1 vs B  -- original size vs substituted size.

The verdict compares the two. If CROSS-SIZE agreement is no worse than
BASELINE, the substitution is indistinguishable from re-running on the very
same machine, which is exactly the claim being audited. If BASELINE is perfect
(A1 == A2 byte-for-byte) and CROSS-SIZE is not, the hardware IS the variable
and the affected lanes need re-running on g6e.4xlarge.

Prompts are the lane's REAL deduction prompts pulled from its S3 run dir, at
the study's own temperature/seed/max_tokens, so the test exercises the regime
the data was generated in rather than a synthetic proxy.

Each box is pinned with EC2_REQUIRE_GPU, which also exercises the guard this
probe exists to justify.

USAGE
    scripts/hardware_equivalence_probe.py --model nemotron-3-nano-4b
"""

import argparse
import hashlib
import json
import logging
import os
import pathlib
import re
import sys
from typing import Any, Dict, List, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

BUCKET = "smolbench-results-414266451290"
#: The study's own deduction generation settings (notebooks/deduction).
TEMPERATURE = 0.7
MAX_TOKENS = 32_768
SEED = 0


def load_prompts(model: str, n: int) -> List[Tuple[str, str]]:
    """Returns [(prompt_id, text)] of real prompts from the lane's S3 run dir.

    Sorted by key so the selection is deterministic across invocations -- a
    probe whose inputs drift between runs cannot support a claim about
    reproducibility.
    """
    import boto3

    s3 = boto3.client("s3")
    prefix = f"deduction/runs/scaling_{model}/theorems/"
    keys: List[str] = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix):
        for o in page.get("Contents", []):
            if o["Key"].endswith(".md") and "/prompts/" in o["Key"]:
                keys.append(o["Key"])
    keys.sort()
    picked = keys[:: max(1, len(keys) // n)][:n]
    out: List[Tuple[str, str]] = []
    for k in picked:
        body = s3.get_object(Bucket=BUCKET, Key=k)["Body"].read().decode("utf-8", "replace")
        out.append((k[len(prefix):], body))
    return out


def run_pass(model: str, prompts: List[Tuple[str, str]], label: str) -> Dict[str, str]:
    """Sends every prompt at the study's settings; returns {prompt_id: output}."""
    from smolbench.evals import ec2

    results: Dict[str, str] = {}
    for i, (pid, text) in enumerate(prompts, 1):
        content, reasoning = ec2.query(
            text, model, SEED,
            extra_args={"temperature": TEMPERATURE, "max_tokens": MAX_TOKENS},
            request_timeout=1800,
        )
        results[pid] = (reasoning or "") + "\x00" + (content or "")
        logging.info("%s: %d/%d %s -> %d chars", label, i, len(prompts), pid[:48],
                     len(results[pid]))
    return results


def compare(a: Dict[str, str], b: Dict[str, str]) -> Dict[str, Any]:
    """Exact-match rate plus a per-prompt digest diff."""
    shared = sorted(set(a) & set(b))
    same = [p for p in shared if a[p] == b[p]]
    diffs = []
    for p in shared:
        if a[p] != b[p]:
            diffs.append({
                "prompt": p,
                "len_a": len(a[p]), "len_b": len(b[p]),
                "sha_a": hashlib.sha256(a[p].encode()).hexdigest()[:12],
                "sha_b": hashlib.sha256(b[p].encode()).hexdigest()[:12],
                "common_prefix_chars": len(os.path.commonprefix([a[p], b[p]])),
            })
    return {"n": len(shared), "identical": len(same),
            "rate": (len(same) / len(shared)) if shared else 0.0, "diffs": diffs}


def serve_and_run(model: str, itype: str, regions: str, gpu_pin: str,
                  prompts: List[Tuple[str, str]], labels: List[str]) -> List[Dict[str, str]]:
    """Provisions ONE box of `itype`, runs one pass per label, tears it down."""
    from smolbench.evals import ec2

    os.environ["EC2_INSTANCE_TYPES"] = itype
    os.environ["EC2_REGIONS"] = regions
    passes: List[Dict[str, str]] = []
    try:
        state = ec2.provision_spot_instance(
            instance_types=tuple(itype.split(",")), regions=tuple(regions.split(",")),
            idle_timeout_min=90,
        )
        logging.info("%s: provisioned %s (%s)", itype, state["instance_id"],
                     state["instance_type"])
        with ec2.serve_model(model):
            cfg = ec2.server_config(model) or {}
            logging.info("%s: serving on %s / %s / tp=%s", itype,
                         cfg.get("instance_type"), cfg.get("gpu"), cfg.get("tp"))
            for label in labels:
                passes.append(run_pass(model, prompts, f"{itype}:{label}"))
    finally:
        try:
            ec2.shutdown_instance()
        except Exception:
            logging.exception("TEARDOWN FAILED for %s -- terminate by hand", itype)
    return passes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--type-a", default="g6e.4xlarge", help="Original instance size.")
    ap.add_argument("--type-b", default="g6e.2xlarge", help="Substituted instance size.")
    ap.add_argument("--gpu-pin", default="L40S:1")
    ap.add_argument("--regions", default="us-west-2,us-east-1,us-east-2")
    ap.add_argument("--n-prompts", type=int, default=8)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Own tag/state file: must never adopt a live study lane's box.
    os.environ["EC2_EXPERIMENT_TAG"] = f"hwprobe-{args.model}"
    os.environ["EC2_STATE_FILE"] = str(REPO_ROOT / f".ec2_state_hwprobe_{args.model}.json")
    os.environ["EC2_REQUIRE_GPU"] = args.gpu_pin

    prompts = load_prompts(args.model, args.n_prompts)
    logging.info("loaded %d real prompts for %s", len(prompts), args.model)

    a1, a2 = serve_and_run(args.model, args.type_a, args.regions, args.gpu_pin,
                           prompts, ["A1", "A2"])
    (b1,) = serve_and_run(args.model, args.type_b, args.regions, args.gpu_pin,
                          prompts, ["B1"])

    baseline = compare(a1, a2)     # same box, back to back
    cross = compare(a1, b1)        # original size vs substituted size

    report = {
        "model": args.model, "type_a": args.type_a, "type_b": args.type_b,
        "seed": SEED, "temperature": TEMPERATURE, "n_prompts": len(prompts),
        "baseline_same_box": baseline, "cross_size": cross,
    }
    out = REPO_ROOT / f"notebooks/deduction/results/hwprobe_{args.model}.json"
    out.write_text(json.dumps(report, indent=2))

    print(f"\n=== {args.model}: {args.type_a} vs {args.type_b} ===")
    print(f"  BASELINE   (same {args.type_a} box, A1 vs A2): "
          f"{baseline['identical']}/{baseline['n']} identical ({baseline['rate']:.0%})")
    print(f"  CROSS-SIZE ({args.type_a} vs {args.type_b}, A1 vs B1): "
          f"{cross['identical']}/{cross['n']} identical ({cross['rate']:.0%})")
    print("\n=== VERDICT ===")
    if baseline["rate"] == 1.0 and cross["rate"] == 1.0:
        print("  NEUTRAL: this model is bitwise-reproducible at a fixed seed, and the "
              "substituted size reproduces the original size exactly. The swap did not "
              "change what the model generates.")
    elif cross["rate"] >= baseline["rate"]:
        print(f"  NEUTRAL WITHIN NOISE: the model is NOT bitwise-reproducible even on one "
              f"box ({baseline['rate']:.0%} self-agreement), and cross-size agreement "
              f"({cross['rate']:.0%}) is no worse. The substitution is indistinguishable "
              "from re-running on the same machine; the variability is vLLM's, not the "
              "hardware's.")
    else:
        print(f"  HARDWARE IS A VARIABLE: cross-size agreement ({cross['rate']:.0%}) is "
              f"BELOW the same-box baseline ({baseline['rate']:.0%}). The affected cells "
              f"should be regenerated on {args.type_a}.")
    print(f"\nreport: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
