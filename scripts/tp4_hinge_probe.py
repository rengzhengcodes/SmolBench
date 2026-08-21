"""tp=4 extension of the 2026-08-16 hinge: does the determinism bundle survive
multi-GPU tensor parallelism?

WHY
---
`notebooks/DETERMINISM_PLAN_2026-08-16.md` section 3 certified the bundle
(`--no-enable-prefix-caching --max-num-seqs 1 --enforce-eager --seed 0`) at
**tp=1** on a single L40S: 8/8 byte-identical within one process for both
nemotron-3-nano-4b and ministral-3-3b. 18 of 22 deploy specs serve at tp=4 or
tp=8, where multi-GPU all-reduce ordering is an untested nondeterminism source
(the docs carry exactly that scope caveat). This probe measures it.

DESIGN (one g6e.12xlarge = 4x L40S, PCIe, no NVLink)
  arm 1  det@tp4    ministral-3-3b under the bundle  -> THE VERDICT ARM
  arm 2  stock@tp4  ministral-3-3b under the study-era stock config
                    -> POSITIVE CONTROL: tp=1 stock was 0/8 (all eight
                       prompts diverged). If stock@tp4 is also ~0/8 the probe
                       demonstrably still DETECTS nondeterminism on this box,
                       so an 8/8 det arm cannot be "the probe went blind".
  arm 3  nemotron det@tp4 (optional, time/budget permitting)

Protocol is the hinge's, unchanged: the same 8 deterministically-selected real
deduction prompts, same seed/temperature/max_tokens, two back-to-back passes
within ONE server process, byte-compared.

PRE-COMMITTED RULES (fixed before any data was seen)
  * tp GATE. ministral-3-3b has 32 attention heads; g6e.12xlarge has 4 GPUs, so
    ec2.derive_tp -> gcd(32,4)=4 and serve_model POSTs tp=4 to the agent, which
    passes `--tensor-parallel-size 4`. This is ASSERTED from the recorded launch
    payload after every serve; a mismatch aborts the arm before a single prompt
    is sent. Certifying tp=4 from a tp=1 measurement is the failure mode this
    guard exists for.
  * EMPTY ROWS ARE UNMEASURED, NOT DIVERGENT (plan section 1.3 / mechanism 11).
    Streaming transport is on and the hinge's retry guard is reused; a row that
    is still length <= 1 after the retry is EXCLUDED from the denominator and
    named in the report, rather than counted as a tp=4 refutation.
  * ARM-LEVEL CHECKPOINTS. A spot reclaim between P1 and P2 kills the server
    process; resuming P2 against a new process would silently convert a
    within-process test into a cross-process one (measured cross-process flip
    rate 9.5%, plan section 6.2) and could manufacture a refutation. Completed
    arms persist; an interrupted arm is re-run from P1.

USAGE
    set -a; . notebooks/ec2-operator.env; . notebooks/deduction/keys.env; set +a
    unset EC2_EXPERIMENT_TAG
    .venv/bin/python <this>/tp4_hinge_probe.py --arms det,stock
"""

import argparse
import datetime as _dt
import gzip
import hashlib
import importlib.util
import json
import logging
import os
import pathlib
import sys
import time
from typing import Any, Dict, List, Tuple

REPO_ROOT = pathlib.Path("/workspace/SmolBench")
OUT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

DET_ARGS = ["--no-enable-prefix-caching", "--max-num-seqs", "1",
            "--enforce-eager", "--seed", "0"]


def _load_hwprobe():
    spec = importlib.util.spec_from_file_location(
        "hardware_equivalence_probe", REPO_ROOT / "scripts" / "hardware_equivalence_probe.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_hinge():
    spec = importlib.util.spec_from_file_location(
        "hinge_probe", REPO_ROOT / "scripts" / "hinge_probe.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def sha_table(passes: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """SHA + length for EVERY row, identical ones included.

    The tp=1 hinge JSON stores digests only for DIFFERING rows, which is why no
    tp=1-vs-tp=4 byte comparison is possible from the archive. Recording all of
    them here makes the next such comparison free.
    """
    return {p: {"sha256_12": hashlib.sha256(t.encode()).hexdigest()[:12], "len": len(t)}
            for p, t in sorted(passes.items())}


def guarded_compare(hw, a: Dict[str, str], b: Dict[str, str]) -> Dict[str, Any]:
    """hw.compare() with the pre-committed empty-row exclusion applied."""
    excluded = sorted(p for p in set(a) & set(b)
                      if len(a.get(p, "")) <= 1 or len(b.get(p, "")) <= 1)
    a2 = {p: t for p, t in a.items() if p not in excluded}
    b2 = {p: t for p, t in b.items() if p not in excluded}
    out = hw.compare(a2, b2)
    out["excluded_empty_rows"] = excluded
    out["n_before_exclusion"] = len(set(a) & set(b))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="ministral-3-3b")
    ap.add_argument("--type", default="g6e.12xlarge")
    ap.add_argument("--gpu-pin", default="L40S:4")
    ap.add_argument("--expect-tp", type=int, default=4)
    ap.add_argument("--regions", default="us-east-2,us-west-2")
    ap.add_argument("--n-prompts", type=int, default=8)
    ap.add_argument("--arms", default="det,stock")
    ap.add_argument("--control-n", type=int, default=0,
                    help="If >0, run the stock control on this many prompts only.")
    ap.add_argument("--deadline-min", type=float, default=210.0,
                    help="Wall-clock budget from process start; no NEW arm starts after it.")
    ap.add_argument("--arm-start-latest-min", type=float, default=150.0,
                    help="No arm after the first may START later than this many minutes in.")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    t_start = time.time()

    os.environ["EC2_STREAM_COMPLETIONS"] = "1"
    os.environ["EC2_MAX_PARALLEL_REQUESTS"] = "1"
    os.environ["EC2_EXPERIMENT_TAG"] = f"tp4hinge-{args.model}"
    os.environ["EC2_STATE_FILE"] = str(REPO_ROOT / f".ec2_state_tp4hinge_{args.model}.json")
    os.environ["EC2_REQUIRE_GPU"] = args.gpu_pin
    os.environ["EC2_INSTANCE_TYPES"] = args.type
    os.environ["EC2_REGIONS"] = args.regions
    os.environ.setdefault("EC2_MAX_LIFETIME_MIN", "270")

    hw = _load_hwprobe()
    hinge = _load_hinge()
    from smolbench.evals import ec2

    prompts = hw.load_prompts(args.model, args.n_prompts)
    logging.info("tp4hinge[%s]: %d prompts", args.model, len(prompts))

    # Apples-to-apples check against the tp=1 arm's prompt set.
    tp1_path = REPO_ROOT / f"notebooks/deduction/results/hinge_{args.model}.json"
    tp1_ids: List[str] = []
    if tp1_path.exists():
        tp1 = json.loads(tp1_path.read_text())
        tp1_ids = sorted({d["prompt"] for d in
                          tp1["comparisons"]["stock_baseline (arm B/D)"]["diffs"]})
    ids = sorted(p for p, _ in prompts)
    same_prompts = bool(tp1_ids) and set(tp1_ids) <= set(ids)
    logging.info("tp4hinge: prompt set matches the tp=1 hinge arm: %s", same_prompts)

    spec_args = list(ec2.EC2_DEPLOY_SPECS[args.model].get("vllm_args", []))
    _det = getattr(ec2, "DETERMINISM_ARGS", DET_ARGS)
    if spec_args[-len(_det):] == _det:
        base_args = spec_args[:-len(_det)]
    else:
        base_args = [a for a in spec_args if a != "--enable-prefix-caching"]
    arm_args = {"det": base_args + DET_ARGS,
                "stock": base_args + ["--enable-prefix-caching"]}

    report_path = OUT_DIR / f"tp4hinge_{args.model}.json"
    report: Dict[str, Any] = {}
    if report_path.exists():
        report = json.loads(report_path.read_text())
    report.update({
        "probe": "tp4_hinge", "model": args.model, "type": args.type,
        "expect_tp": args.expect_tp, "n_prompts": args.n_prompts,
        "seed": hw.SEED, "temperature": hw.TEMPERATURE, "max_tokens": hw.MAX_TOKENS,
        "stream": True, "prompt_ids": ids,
        "prompt_set_matches_tp1_hinge": same_prompts,
        "started_utc": report.get("started_utc") or _dt.datetime.now(
            _dt.timezone.utc).isoformat(),
    })
    report.setdefault("arms", {})

    def save() -> None:
        report_path.write_text(json.dumps(report, indent=1))

    try:
        state = ec2.provision_spot_instance(
            instance_types=(args.type,), regions=tuple(args.regions.split(",")),
            idle_timeout_min=60,
        )
        logging.info("tp4hinge: provisioned %s (%s @ %s)", state["instance_id"],
                     state["instance_type"], state.get("availability_zone"))
        report["instance"] = {k: state.get(k) for k in
                              ("instance_id", "instance_type", "region",
                               "availability_zone", "public_ip")}
        report["provisioned_utc"] = report.get("provisioned_utc") or _dt.datetime.now(
            _dt.timezone.utc).isoformat()
        save()

        for idx, arm in enumerate([a.strip() for a in args.arms.split(",") if a.strip()]):
            done = report["arms"].get(arm, {}).get("complete")
            if done:
                logging.info("tp4hinge: arm %s already complete; skipping", arm)
                continue
            mins = (time.time() - t_start) / 60.0
            if mins > args.deadline_min or (idx > 0 and mins > args.arm_start_latest_min):
                logging.warning("tp4hinge: %.1f min elapsed -- SKIPPING arm %s "
                                "(budget guard)", mins, arm)
                report["arms"].setdefault(arm, {})["skipped_for_budget_at_min"] = round(mins, 1)
                save()
                continue

            arm_prompts = prompts
            if arm != "det" and args.control_n:
                arm_prompts = prompts[:args.control_n]
            ec2.EC2_DEPLOY_SPECS[args.model]["vllm_args"] = arm_args[arm]
            logging.info("tp4hinge: serving arm=%s args=%s", arm, arm_args[arm])
            t0 = time.time()
            entry: Dict[str, Any] = {"vllm_args": arm_args[arm],
                                     "n_prompts_this_arm": len(arm_prompts)}
            report["arms"][arm] = entry
            save()
            try:
                with ec2.serve_model(args.model, force=True):
                    st = ec2._load_state() or {}
                    served_tp = (st.get("last_serve") or {}).get("tp")
                    entry["served_tp"] = served_tp
                    cfg = ec2.server_config(args.model) or {}
                    entry["server_config"] = cfg
                    entry["fingerprint"] = hinge.fingerprint(state, args.model)
                    save()
                    if served_tp != args.expect_tp:
                        raise RuntimeError(
                            f"tp GATE FAILED: launched tp={served_tp!r}, expected "
                            f"{args.expect_tp}. Refusing to measure -- a tp=1 "
                            "measurement must never be reported as tp=4.")
                    logging.info("tp4hinge[%s]: tp GATE PASSED (tp=%s, gpu=%s, "
                                 "vllm=%s, nvidia_smi=%s)", arm, served_tp,
                                 cfg.get("gpu"), cfg.get("vllm_version"),
                                 str((cfg.get("agent_fingerprint") or {}).get("nvidia_smi"))[:200])
                    passes: Dict[str, Dict[str, str]] = {}
                    for i in (1, 2):
                        label = f"{arm}@tp{args.expect_tp}:P{i}"
                        res = hinge.guarded_pass(hw, args.model, arm_prompts, label)
                        retr = res.pop("_retried_rows", None)
                        if retr:
                            entry[f"retried_rows_P{i}"] = json.loads(retr)
                        passes[f"P{i}"] = res
                        entry[f"sha_table_P{i}"] = sha_table(res)
                        save()
                        with gzip.open(OUT_DIR / f"texts_{args.model}_{arm}_P{i}.json.gz",
                                       "wt") as fh:
                            json.dump(res, fh)
                    entry["fingerprint_after"] = hinge.fingerprint(state, args.model)
                    entry["within_process_baseline"] = guarded_compare(
                        hw, passes["P1"], passes["P2"])
                    entry["serve_plus_passes_s"] = round(time.time() - t0, 1)
                    entry["complete"] = True
                    save()
                    c = entry["within_process_baseline"]
                    logging.info("tp4hinge[%s]: %d/%d identical (%d excluded empty)",
                                 arm, c["identical"], c["n"], len(c["excluded_empty_rows"]))
            except Exception as exc:  # noqa: BLE001
                entry["FAILED"] = f"{type(exc).__name__}: {exc}"
                try:
                    import requests
                    stt = requests.get(f"http://{state['public_ip']}:9000/status",
                                       timeout=10).json()
                    entry["serve_log_tail"] = str(stt.get("serve_log_tail"))[-4000:]
                except Exception:  # noqa: BLE001
                    pass
                save()
                logging.exception("tp4hinge: arm %s FAILED", arm)
                if arm == "det":
                    raise

        report["finished_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
        report["elapsed_min"] = round((time.time() - t_start) / 60.0, 1)
        save()
        print("\n=== tp4 hinge:", args.model, "===")
        for arm, e in report["arms"].items():
            c = e.get("within_process_baseline")
            if c:
                print(f"  {arm}@tp{args.expect_tp}: {c['identical']}/{c['n']} identical"
                      f"  (excluded empty: {c['excluded_empty_rows']})")
        print("report:", report_path)
    finally:
        try:
            ec2.shutdown_instance()
        except Exception:
            logging.exception("TEARDOWN FAILED -- terminate by hand")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
