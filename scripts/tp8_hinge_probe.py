"""tp=8 extension of the hinge: does the determinism bundle survive the
8-GPU NVLink topology that every MoE deploy spec actually serves on?

WHY
---
`notebooks/DETERMINISM_PLAN_2026-08-16.md` section 3 certified the bundle
(`--no-enable-prefix-caching --max-num-seqs 1 --enforce-eager --seed 0`) at
**tp=1** (single L40S), and `scripts/tp4_hinge_probe.py` certified it at
**tp=4** (g6e.12xlarge, 4x L40S over PCIe) on 2026-08-21: 8/8 byte-identical
within one process for both ministral-3-3b and nemotron-3-nano-4b, with a
stock@tp4 positive control at 1/4 proving the probe still detects
nondeterminism on a multi-GPU box.

That leaves the **nine tp=8 specs** uncertified -- qwen3.5-397b-a17b,
qwen3.5-122b-a10b, nemotron-3-super-120b-a12b, k-exaone-236b-a23b, glm-4.5-air,
glm-4.7, deepseek-v3.1, deepseek-v4-flash, deepseek-v4-pro. Two mechanisms are
new at tp=8 and are unexercised by anything measured so far:

  1. **The custom all-reduce path.** vLLM selects a hand-written NVLink
     all-reduce kernel when peer-to-peer access is available across all ranks
     (p5-class boxes have NVSwitch); the g6e boxes of the tp=1/tp=4 arms are
     PCIe-only and fall back to NCCL. Different kernel, different reduction
     order, different opportunity for run-to-run drift.
  2. **MoE routing at 8-way TP.** Every tp=8 spec in this study is a
     mixture-of-experts model whose experts are TP-sharded (no
     `--enable-expert-parallel` in any spec -- do NOT add it here, it would be
     off-protocol). Expert-parallel-free MoE at tp=8 still adds a second
     reduction per layer.

DESIGN (ONE 8-GPU p5-class box per invocation)
  tier 1  DENSE-AT-TP8   ministral-3-3b (32 heads -> gcd(32,8)=8) under the
                         bundle -> THE VERDICT ARM, plus a stock@tp8 positive
                         control so an 8/8 det arm cannot be "the probe went
                         blind on this silicon".
  tier 2  MOE-AT-TP8     nemotron-3-super-120b-a12b (32 heads, ~240GB BF16,
                         the smallest tp=8 MoE spec) under the bundle.

Protocol is the hinge's, unchanged and shared with tp=4: the same
deterministically-selected real deduction prompts from the model's own S3 run
dir, same seed/temperature/max_tokens, two back-to-back passes within ONE
server process, byte-compared.

PRE-COMMITTED RULES (fixed before any data was seen; inherited from tp=4)
  * tp GATE. `ec2.derive_tp` computes gcd(num_attention_heads, gpu_count).
    ministral-3-3b and nemotron-3-super-120b-a12b both have 32 heads, so on an
    8-GPU box tp=8. This is ASSERTED from the recorded launch payload after
    every serve; a mismatch aborts the arm before a single prompt is sent.
    Certifying tp=8 from a tp=4 measurement is the failure mode this exists for.
  * EMPTY ROWS ARE UNMEASURED, NOT DIVERGENT (plan section 1.3 / mechanism 11).
  * ARM-LEVEL CHECKPOINTS. A spot reclaim between P1 and P2 kills the server
    process; resuming P2 against a new process would silently convert a
    within-process test into a cross-process one (measured cross-process flip
    rate 9.5%, plan section 6.2). Completed arms persist; an interrupted arm is
    re-run from P1.

WHAT THIS PROBE ADDS OVER tp4_hinge_probe.py
  * The serve log is captured UNCONDITIONALLY (tp=4 grabbed it only on
    failure), and grepped for all-reduce / NVLink / P2P / MoE lines, so
    "the custom all-reduce path was exercised" is a recorded fact rather than
    an inference from the instance type.
  * A SHA-level tp=4-vs-tp=8 cross comparison (the tp=4 JSONs store
    `sha_table_P1/P2` for all rows, so this is now free and exact; the tp=4
    report could only compare lengths against tp=1).
    SCOPE: that comparison is confounded by GPU model -- tp=4 ran on L40S,
    tp=8 runs on H100/H200. A disagreement means "different config, different
    bytes", consistent with the existing cross-config pooling guard; it is NOT
    evidence about tensor-parallel degree in isolation.

USAGE
    set -a; . notebooks/ec2-operator.env; . notebooks/deduction/keys.env; set +a
    unset EC2_EXPERIMENT_TAG
    EC2_ROOT_VOLUME_GB=500 EC2_MAX_LIFETIME_MIN=120 \
      .venv/bin/python scripts/tp8_hinge_probe.py --arms det,stock --control-n 4
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
import re
import sys
import time
from typing import Any, Dict, List

REPO_ROOT = pathlib.Path("/workspace/SmolBench")
#: Explicit, NOT __file__.parent -- the tp=4/tp=1 hinge JSONs live here and the
#: cross-tp comparison reads them from here.
OUT_DIR = REPO_ROOT / "notebooks" / "deduction" / "results"
sys.path.insert(0, str(REPO_ROOT))

DET_ARGS = ["--no-enable-prefix-caching", "--max-num-seqs", "1",
            "--enforce-eager", "--seed", "0"]

#: Serve-log lines worth keeping: the all-reduce / topology / MoE evidence.
_LOG_PATTERNS = re.compile(
    r"custom.?all.?reduce|CustomAllreduce|all.?reduce|NVLink|nvlink|P2P|p2p|"
    r"NCCL|nccl|expert|Expert|tensor.?parallel|TP=|world_size|pynccl|symm",
)


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
    """SHA + length for EVERY row, identical ones included."""
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


def resilient_pass(hw, ec2, model: str, prompts, label: str, entry: Dict[str, Any],
                   key: str, gz_path: pathlib.Path, stop_at_min: float,
                   t_start: float, save) -> Dict[str, str]:
    """One probe pass, persisted ROW BY ROW and stoppable at a wall deadline.

    Identical request shape to ``hardware_equivalence_probe.run_pass`` and the
    same length<=1 delivery-fault retry as ``hinge_probe.guarded_pass`` -- the
    measurement is unchanged. What is added is failure containment, which the
    tp=4 probe lacked and which matters far more at $20/h on an 8-GPU box:

      * every completed row is written to the report and the gz archive
        immediately, so a spot reclaim or a lifetime fuse firing mid-pass
        costs the remaining rows, not the whole arm;
      * no NEW prompt is issued after ``stop_at_min`` minutes from process
        start, so the pass lands rather than being severed;
      * a per-row exception is recorded and the pass continues.

    P2 is then run over exactly the prompt ids P1 completed, so the byte
    comparison always has a matched denominator -- a truncated arm reports
    k/k over a smaller k, never a spurious divergence.
    """
    ctx_len = ec2._CLIENT.context_length(model)
    logging.info("%s: server reports context_length=%d", label, ctx_len)
    if ctx_len <= 0:
        raise RuntimeError(f"{label}: context_length={ctx_len}; token budget unknown.")

    results: Dict[str, str] = {}

    def _ask(text: str) -> str:
        content, reasoning = ec2.query(
            text, model, hw.SEED, ctx_len,
            extra_args={"temperature": hw.TEMPERATURE, "max_tokens": hw.MAX_TOKENS},
            request_timeout=1800)
        return (reasoning or "") + "\x00" + (content or "")

    for i, (pid, text) in enumerate(prompts, 1):
        mins = (time.time() - t_start) / 60.0
        if mins > stop_at_min:
            entry[f"{key}_truncated_at_min"] = round(mins, 1)
            entry[f"{key}_rows_done"] = len(results)
            logging.warning("%s: %.1f min elapsed -- stopping pass after %d rows",
                            label, mins, len(results))
            save()
            break
        try:
            txt = _ask(text)
            if len(txt) <= 1:
                logging.warning("%s: row %s length %d -- delivery-fault signature; "
                                "re-asking once", label, pid, len(txt))
                redo = _ask(text)
                entry.setdefault(f"retried_rows_{key}", {})[pid] = {
                    "original_len": len(txt), "retry_len": len(redo)}
                if len(redo) > 1:
                    txt = redo
            results[pid] = txt
        except Exception as exc:  # noqa: BLE001 -- one bad row must not kill the arm
            entry.setdefault(f"{key}_errors", {})[pid] = f"{type(exc).__name__}: {exc}"
            logging.exception("%s: row %s FAILED", label, pid)
            save()
            continue
        logging.info("%s: %d/%d %s -> %d chars", label, i, len(prompts), pid[:48],
                     len(results[pid]))
        entry[f"sha_table_{key}"] = sha_table(results)
        with gzip.open(gz_path, "wt") as fh:
            json.dump(results, fh)
        save()
    return results


def capture_serve_log(state: Dict[str, Any]) -> Dict[str, Any]:
    """Unconditional, AUTHENTICATED capture of the vLLM container log + grep.

    Three faults in the tp=4 probe's version are fixed here, all found live on
    2026-08-21 against the running tp=8 box:

    1. It sent no ``Authorization`` header, and the control agent's ``/status``
       is token-gated -- every such call returned HTTP 401 ``{"error": "bad
       token"}``. The tp=4 report's serve-log fields were therefore empty by
       construction, not because the box was quiet. (``hinge_probe.fingerprint``
       has the same unauthenticated ``/status`` call, which is why its
       ``image_digest_lines`` are empty in the archived reports.)
    2. It read ``serve_log_tail``, which is the *launcher script's* stdout
       (aws s3 sync + ``docker run -d``) -- vLLM's own startup banner lives in
       ``log_tail`` (``docker logs --tail 300 vllm``). The all-reduce and
       tensor-parallel facts are only in the latter.
    3. It was called only from the ``except`` branch, so a SUCCESSFUL arm
       recorded nothing about which collective implementation vLLM chose.
    """
    out: Dict[str, Any] = {}
    try:
        import requests
        r = requests.get(
            f"http://{state['public_ip']}:9000/status",
            headers={"Authorization": "Bearer " + str(state.get("control_token", ""))},
            timeout=30)
        out["http_status"] = r.status_code
        st = r.json()
        vllm_log = str(st.get("log_tail") or "")
        out["container"] = st.get("container")
        out["healthy"] = st.get("healthy")
        out["vllm_log_chars"] = len(vllm_log)
        out["vllm_log_tail"] = vllm_log[-14000:]
        out["launcher_log_tail"] = str(st.get("serve_log_tail") or "")[-3000:]
        lines = vllm_log.splitlines()
        out["topology_lines"] = sorted({l.strip()[:400] for l in lines
                                        if _LOG_PATTERNS.search(l)})[:60]
        # The single line that settles tp / custom all-reduce / eager / seed.
        cfg = [l for l in lines if "Initializing a V1 LLM engine" in l
               or "non-default args" in l]
        out["engine_config_lines"] = [l[:4000] for l in cfg][:4]
        joined = " ".join(cfg)
        for k in ("tensor_parallel_size", "disable_custom_all_reduce", "enforce_eager",
                  "enable_prefix_caching", "seed", "pipeline_parallel_size"):
            m = re.search(k + r"=([^,\s}]+)", joined)
            if m:
                out.setdefault("engine_config_parsed", {})[k] = m.group(1)
        out["worker_ranks"] = sorted({m.group(0) for m in
                                      re.finditer(r"Worker_TP\d+", vllm_log)})
    except Exception as exc:  # noqa: BLE001 -- provenance, never fatal
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def cross_tp(model: str, this_sha: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Exact SHA comparison of this tp=8 P1 against the archived tp=4 det P1."""
    src = OUT_DIR / f"tp4hinge_{model}.json"
    if not src.exists():
        return {"available": False, "reason": f"{src.name} absent"}
    try:
        det = json.loads(src.read_text())["arms"]["det"]
        prev = det["sha_table_P1"]
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
    shared = sorted(set(prev) & set(this_sha))
    rows = [{"prompt": p,
             "tp4_sha": prev[p]["sha256_12"], "tp8_sha": this_sha[p]["sha256_12"],
             "tp4_len": prev[p]["len"], "tp8_len": this_sha[p]["len"],
             "same": prev[p]["sha256_12"] == this_sha[p]["sha256_12"]}
            for p in shared]
    return {"available": True, "n": len(shared),
            "identical": sum(r["same"] for r in rows),
            "tp4_gpu": "L40S (g6e.12xlarge, PCIe)",
            "confound_note": "tp=4 ran on L40S, tp=8 on H100/H200: GPU model and "
                             "tp change together, so a mismatch is a cross-CONFIG "
                             "fact, not a tp-in-isolation fact.",
            "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="ministral-3-3b")
    ap.add_argument("--type", default="p5.48xlarge,p5e.48xlarge,p5en.48xlarge")
    ap.add_argument("--gpu-pin", default=":8",
                    help="Empty name substring + count 8: any 8-GPU p5-class box.")
    ap.add_argument("--expect-tp", type=int, default=8)
    ap.add_argument("--regions", default="us-east-2,us-west-2,us-east-1")
    ap.add_argument("--n-prompts", type=int, default=8)
    ap.add_argument("--arms", default="det,stock")
    ap.add_argument("--control-n", type=int, default=4,
                    help="If >0, run the stock control on this many prompts only.")
    ap.add_argument("--deadline-min", type=float, default=150.0,
                    help="Wall-clock budget from process start; no NEW arm starts after it.")
    ap.add_argument("--arm-start-latest-min", type=float, default=95.0,
                    help="No arm after the first may START later than this many minutes in.")
    ap.add_argument("--pass-deadline-min", type=float, default=1e9,
                    help="No NEW prompt is issued after this many minutes from process "
                         "start; the pass lands on the rows already done.")
    ap.add_argument("--p2-grace-min", type=float, default=25.0,
                    help="Extra minutes P2 gets over --pass-deadline-min, so a P1 that "
                         "ran to the deadline still gets its matching second pass.")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    t_start = time.time()

    os.environ["EC2_STREAM_COMPLETIONS"] = "1"
    os.environ["EC2_MAX_PARALLEL_REQUESTS"] = "1"
    os.environ["EC2_EXPERIMENT_TAG"] = f"tp8hinge-{args.model}"
    os.environ["EC2_STATE_FILE"] = str(REPO_ROOT / f".ec2_state_tp8hinge_{args.model}.json")
    os.environ["EC2_REQUIRE_GPU"] = args.gpu_pin
    os.environ["EC2_INSTANCE_TYPES"] = args.type
    os.environ["EC2_REGIONS"] = args.regions
    # Fuse: the shell is expected to export a tighter one per box.
    os.environ.setdefault("EC2_MAX_LIFETIME_MIN", "150")

    hw = _load_hwprobe()
    hinge = _load_hinge()
    from smolbench.evals import ec2

    prompts = hw.load_prompts(args.model, args.n_prompts)
    logging.info("tp8hinge[%s]: %d prompts", args.model, len(prompts))

    # Apples-to-apples check against the tp=4 arm's prompt set.
    tp4_path = OUT_DIR / f"tp4hinge_{args.model}.json"
    tp4_ids: List[str] = []
    if tp4_path.exists():
        try:
            tp4_ids = sorted(json.loads(tp4_path.read_text())["arms"]["det"]["sha_table_P1"])
        except Exception:  # noqa: BLE001
            tp4_ids = []
    ids = sorted(p for p, _ in prompts)
    same_prompts = bool(tp4_ids) and set(tp4_ids) <= set(ids)
    logging.info("tp8hinge: prompt set matches the tp=4 hinge arm: %s", same_prompts)

    spec_args = list(ec2.EC2_DEPLOY_SPECS[args.model].get("vllm_args", []))
    _det = getattr(ec2, "DETERMINISM_ARGS", DET_ARGS)
    if list(_det) != DET_ARGS:
        raise RuntimeError(
            f"ec2.DETERMINISM_ARGS {_det!r} != this probe's DET_ARGS {DET_ARGS!r}; "
            "the stock arm would silently keep determinism flags. Refusing.")
    if spec_args[-len(_det):] == list(_det):
        base_args = spec_args[:-len(_det)]
    else:
        base_args = [a for a in spec_args if a != "--enable-prefix-caching"]
    if any(a in base_args for a in DET_ARGS):
        raise RuntimeError(f"determinism flags survived the strip: {base_args!r}")
    arm_args = {"det": base_args + DET_ARGS,
                "stock": base_args + ["--enable-prefix-caching"]}

    report_path = OUT_DIR / f"tp8hinge_{args.model}.json"
    report: Dict[str, Any] = {}
    if report_path.exists():
        report = json.loads(report_path.read_text())
    report.update({
        "probe": "tp8_hinge", "model": args.model, "type": args.type,
        "expect_tp": args.expect_tp, "n_prompts": args.n_prompts,
        "seed": hw.SEED, "temperature": hw.TEMPERATURE, "max_tokens": hw.MAX_TOKENS,
        "stream": True, "prompt_ids": ids,
        "prompt_set_matches_tp4_hinge": same_prompts,
        "started_utc": report.get("started_utc") or _dt.datetime.now(
            _dt.timezone.utc).isoformat(),
    })
    report.setdefault("arms", {})

    def save() -> None:
        report_path.write_text(json.dumps(report, indent=1))

    try:
        state = ec2.provision_spot_instance(
            instance_types=tuple(args.type.split(",")),
            regions=tuple(args.regions.split(",")),
            idle_timeout_min=60,
        )
        logging.info("tp8hinge: provisioned %s (%s @ %s)", state["instance_id"],
                     state["instance_type"], state.get("availability_zone"))
        report["instance"] = {k: state.get(k) for k in
                              ("instance_id", "instance_type", "region",
                               "availability_zone", "public_ip")}
        report["provisioned_utc"] = report.get("provisioned_utc") or _dt.datetime.now(
            _dt.timezone.utc).isoformat()
        save()

        for idx, arm in enumerate([a.strip() for a in args.arms.split(",") if a.strip()]):
            if report["arms"].get(arm, {}).get("complete"):
                logging.info("tp8hinge: arm %s already complete; skipping", arm)
                continue
            mins = (time.time() - t_start) / 60.0
            if mins > args.deadline_min or (idx > 0 and mins > args.arm_start_latest_min):
                logging.warning("tp8hinge: %.1f min elapsed -- SKIPPING arm %s "
                                "(budget guard)", mins, arm)
                report["arms"].setdefault(arm, {})["skipped_for_budget_at_min"] = round(mins, 1)
                save()
                continue

            arm_prompts = prompts
            if arm != "det" and args.control_n:
                arm_prompts = prompts[:args.control_n]
            ec2.EC2_DEPLOY_SPECS[args.model]["vllm_args"] = arm_args[arm]
            logging.info("tp8hinge: serving arm=%s args=%s", arm, arm_args[arm])
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
                    entry["server_config"] = ec2.server_config(args.model) or {}
                    entry["fingerprint"] = hinge.fingerprint(state, args.model)
                    entry["serve_log"] = capture_serve_log(state)
                    save()
                    if served_tp != args.expect_tp:
                        raise RuntimeError(
                            f"tp GATE FAILED: launched tp={served_tp!r}, expected "
                            f"{args.expect_tp}. Refusing to measure -- a tp<8 "
                            "measurement must never be reported as tp=8.")
                    cfg = entry["server_config"]
                    logging.info("tp8hinge[%s]: tp GATE PASSED (tp=%s, gpu=%s, vllm=%s)",
                                 arm, served_tp, cfg.get("gpu"), cfg.get("vllm_version"))
                    logging.info("tp8hinge[%s]: topology lines: %s", arm,
                                 str(entry["serve_log"].get("topology_lines"))[:600])
                    passes: Dict[str, Dict[str, str]] = {}
                    p1 = resilient_pass(
                        hw, ec2, args.model, arm_prompts,
                        f"{arm}@tp{args.expect_tp}:P1", entry, "P1",
                        OUT_DIR / f"texts_tp8_{args.model}_{arm}_P1.json.gz",
                        args.pass_deadline_min, t_start, save)
                    passes["P1"] = p1
                    entry["pass_done_P1_min"] = round((time.time() - t_start) / 60.0, 1)
                    save()
                    # P2 covers exactly what P1 completed: matched denominator.
                    p2_prompts = [(pid, txt) for pid, txt in arm_prompts if pid in p1]
                    entry["n_prompts_compared"] = len(p2_prompts)
                    p2 = resilient_pass(
                        hw, ec2, args.model, p2_prompts,
                        f"{arm}@tp{args.expect_tp}:P2", entry, "P2",
                        OUT_DIR / f"texts_tp8_{args.model}_{arm}_P2.json.gz",
                        args.pass_deadline_min + args.p2_grace_min, t_start, save)
                    passes["P2"] = p2
                    entry["pass_done_P2_min"] = round((time.time() - t_start) / 60.0, 1)
                    entry["fingerprint_after"] = hinge.fingerprint(state, args.model)
                    entry["serve_log_after"] = capture_serve_log(state)
                    entry["within_process_baseline"] = guarded_compare(
                        hw, passes["P1"], passes["P2"])
                    if arm == "det":
                        entry["cross_tp_vs_tp4_det_P1"] = cross_tp(
                            args.model, entry["sha_table_P1"])
                    entry["serve_plus_passes_s"] = round(time.time() - t0, 1)
                    entry["complete"] = True
                    save()
                    c = entry["within_process_baseline"]
                    logging.info("tp8hinge[%s]: %d/%d identical (%d excluded empty)",
                                 arm, c["identical"], c["n"], len(c["excluded_empty_rows"]))
            except Exception as exc:  # noqa: BLE001
                entry["FAILED"] = f"{type(exc).__name__}: {exc}"
                entry["serve_log_on_failure"] = capture_serve_log(state)
                save()
                logging.exception("tp8hinge: arm %s FAILED", arm)
                if arm == "det":
                    raise

        report["finished_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
        report["elapsed_min"] = round((time.time() - t_start) / 60.0, 1)
        save()
        print("\n=== tp8 hinge:", args.model, "===")
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
