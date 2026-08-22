"""moe-tp8: the last two determinism-certification gaps.

COPY, not a mutation, of scripts/tp8_hinge_probe.py (whose header explains why
reuse-in-place is destructive: it rewrites notebooks/deduction/results/
tp8hinge_<model>.json and texts_tp8_<model>_<arm>_P{1,2}.json.gz, which are
committed audit artifacts at HEAD). Everything here writes into the scratchpad
under fresh names; nothing in the repo is touched.

The measurement helpers (resilient_pass / sha_table / guarded_compare /
capture_serve_log) are IMPORTED from the HEAD probe so the protocol is byte-for-
byte the one that ran tonight -- only the arm plan and the deadline discipline
are new.

GAPS CLOSED
  A  MOE-DET-TP8            nemotron-3-super-120b-a12b (tier C's own hunt list,
                            p5.48xlarge/p5e.48xlarge) under the bundle at tp=8.
                            MoE experts are TP-sharded (no --enable-expert-
                            parallel in any spec; adding one would be off-
                            protocol) -> a second reduction per layer that
                            nothing measured so far exercises.
  B  DENSE-DET-TP8-NOCAR    ministral-3-3b under the bundle PLUS
                            --disable-custom-all-reduce: the NCCL-fallback
                            collective that both deepseek specs pin.
  C  STOCK-TP8 (control)    ministral-3-3b stock, only if time+budget remain.

WHAT IS NEW vs the HEAD probe
  * ARM-RELATIVE deadlines. The HEAD probe's pass deadline is absolute from
    process start, which is why tonight's stock arm recorded 0 rows. Each arm
    here gets its own t0 and its own minute budget.
  * A THROUGHPUT PROBE (max_tokens=256) issued right after each serve, so k is
    chosen from a measured tokens/s rather than a guess. A 120B MoE at tp=8 in
    eager mode could be anywhere from 6 to 30 tok/s and that changes k by 4x.
  * k IS THE ONLY KNOB. max_tokens stays at the study's 32768 and the seed /
    temperature / prompt set stay fixed, so every row measured here is
    comparable to the tp=1 / tp=4 / tp=8-dense arms. Cutting max_tokens would
    make the arm non-comparable; cutting k just measures fewer rows.
  * PREFIX-STABLE prompt selection. load_prompts(model, 8) then [:k] -- never
    load_prompts(model, k), whose stride keys[::len//n] picks a DIFFERENT set
    for a different n unless len(keys) divides cleanly. Both models resolve to
    the same 8 ids (verified pre-flight), so arm B/C rows are directly
    SHA-comparable to the committed tp8hinge_ministral-3-3b.json.
  * ARM A DOES NOT ABORT THE RUN. The HEAD probe re-raises on its det arm; here
    a nemotron OOM-at-load must still leave arm B measurable.
  * A serve-log ASSERTION right after serve. capture_serve_log's authenticated
    version has never run against a live box (tonight's report carries the OLD
    3-key shape), and it is the sole producer of arm B's headline evidence.
    If it comes back empty we learn it in minute 1, not after an hour of
    generation -- and arm B carries an independent fallback: the recorded
    launch payload proves the flag was passed, and a SHA diff against tonight's
    custom-all-reduce run proves the collective actually changed.

PRE-COMMITTED VERDICT RULE (fixed before any data was seen)
  k/k byte-identical, empty rows excluded (DETERMINISM_PLAN section 1.3) =>
  the bundle HOLDS for that arm at tp=8; any non-empty divergence => it does
  not, and the first differing byte offset is reported. k is stated in every
  verdict sentence -- "2/2 over N tokens" is not "certified", it is 2/2.
"""

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import logging
import os
import pathlib
import sys
import time
from typing import Any, Dict, List

REPO_ROOT = pathlib.Path("/workspace/SmolBench")
OUT_DIR = pathlib.Path(
    "/tmp/claude-1001/-workspace-SmolBench/e02d645d-a971-4770-ad99-4f84f96cc96e"
    "/scratchpad/r7-moe-tp8")
#: Tonight's committed tp=8 dense arm, for the arm-B cross comparison.
HEAD_TP8 = REPO_ROOT / "notebooks" / "deduction" / "results" / "tp8hinge_ministral-3-3b.json"
sys.path.insert(0, str(REPO_ROOT))

DET_ARGS = ["--no-enable-prefix-caching", "--max-num-seqs", "1",
            "--enforce-eager", "--seed", "0"]


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def throughput_probe(ec2, hw, model: str, text: str, entry: Dict[str, Any]) -> float:
    """One short generation, timed. Returns rough output tokens/s.

    Deliberately NOT part of the comparison: it is issued at max_tokens=256 and
    its output is discarded. It exists so k is picked from this box's measured
    rate. It runs on the same server process as the passes that follow, which
    is exactly the process whose speed we need.
    """
    ctx = ec2._CLIENT.context_length(model)
    t0 = time.time()
    content, reasoning = ec2.query(text, model, hw.SEED, ctx,
                                   extra_args={"temperature": hw.TEMPERATURE,
                                               "max_tokens": 2048},
                                   request_timeout=900)
    dt = time.time() - t0
    chars = len((reasoning or "") + (content or ""))
    # ~4 chars/token is the study's own ratio (tonight: 348581 chars over
    # ~87k tokens at 32768-cap rows). Only used to pick k.
    toks = chars / 4.0
    rate = toks / dt if dt > 0 else 0.0
    if rate <= 0.0:
        # Measured tonight on this exact silicon/bundle: 9.1 tok/s for the
        # 120B MoE (33897 chars / 15.6 min) and 33 tok/s for the dense 3B
        # (348581 chars / 43.7 min, committed tp8 arm). Never fall back to 0.
        rate = 9.1 if "120b" in model else 33.0
        entry.setdefault("throughput_probe", {})["fallback_rate_used"] = rate
        logging.warning("throughput probe returned nothing; falling back to %.1f tok/s", rate)
    entry["throughput_probe"] = {"seconds": round(dt, 1), "chars": chars,
                                 "approx_tokens": round(toks), "approx_tok_s": round(rate, 2)}
    logging.info("throughput probe: %d chars in %.1fs -> ~%.1f tok/s", chars, dt, rate)
    return rate


def pick_k(rate: float, prompts, minutes: float, max_k: int) -> int:
    """Largest k whose TWO passes fit in `minutes` at the measured rate.

    Row cost is estimated from the tp=8 dense arm's observed output lengths
    where available, else from the 32768 cap -- deliberately pessimistic, since
    over-running the window costs money and under-running only costs rows.
    """
    est = _row_token_estimates(prompts)
    budget_tokens = rate * minutes * 60.0 / 2.0  # two passes
    total = 0.0
    for k in range(1, max_k + 1):
        total += est[k - 1]
        if total > budget_tokens:
            return max(1, k - 1)
    return max_k


def _row_token_estimates(prompts) -> List[float]:
    """Per-row expected OUTPUT tokens, from tonight's dense tp=8 lengths."""
    try:
        tbl = json.loads(HEAD_TP8.read_text())["arms"]["det"]["sha_table_P1"]
    except Exception:  # noqa: BLE001
        tbl = {}
    out = []
    for pid, _ in prompts:
        row = tbl.get(pid)
        out.append((row["len"] / 4.0) if row else 32768.0)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--moe-model", default="nemotron-3-super-120b-a12b")
    ap.add_argument("--dense-model", default="ministral-3-3b")
    ap.add_argument("--type", default="p5.48xlarge,p5e.48xlarge")
    ap.add_argument("--regions", default="us-west-2,us-east-2,us-east-1")
    ap.add_argument("--expect-tp", type=int, default=8)
    ap.add_argument("--arms", default="A,B,C")
    ap.add_argument("--armA-min", type=float, default=125.0)
    ap.add_argument("--armB-min", type=float, default=52.0)
    ap.add_argument("--armC-min", type=float, default=28.0)
    ap.add_argument("--armA2-min", type=float, default=100.0)
    ap.add_argument("--report", default="moe_tp8_report_run2.json")
    ap.add_argument("--force-k", default="",
                    help="Per-arm k override, e.g. 'A2=4,C=4,B=3'. See below.")
    ap.add_argument("--force-k-why", default="",
                    help="Override pick_k. Used for A2 ONLY, and only because "
                         "pick_k's per-row estimates come from the DENSE model's "
                         "observed lengths (the only ones on disk) and overshot "
                         "nemotron by ~2.8x: its row 1 was 33897 chars where "
                         "ministral's was 93555. Feeding the measured MoE length "
                         "back in is a correction to a known-biased estimator, not "
                         "a relaxation of the protocol -- max_tokens, seed, "
                         "temperature and the prompt prefix are untouched.")
    ap.add_argument("--hard-stop-min", type=float, default=205.0,
                    help="No new pass starts after this many minutes from process start.")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    t_start = time.time()

    os.environ["EC2_STREAM_COMPLETIONS"] = "1"
    os.environ["EC2_MAX_PARALLEL_REQUESTS"] = "1"
    # ONE tag / ONE state file for the whole driver: two models share one box,
    # so a per-model tag would break _require_state() on the second serve and
    # make the teardown sweep ambiguous.
    os.environ["EC2_EXPERIMENT_TAG"] = "moetp8"
    os.environ["EC2_STATE_FILE"] = str(REPO_ROOT / ".ec2_state_moetp8.json")
    os.environ["EC2_REQUIRE_GPU"] = ":8"
    os.environ["EC2_INSTANCE_TYPES"] = args.type
    os.environ["EC2_REGIONS"] = args.regions
    os.environ.setdefault("EC2_MAX_LIFETIME_MIN", "215")

    hw = _load("hardware_equivalence_probe", "scripts/hardware_equivalence_probe.py")
    hinge = _load("hinge_probe", "scripts/hinge_probe.py")
    tp8 = _load("tp8_hinge_probe", "scripts/tp8_hinge_probe.py")
    from smolbench.evals import ec2

    if list(getattr(ec2, "DETERMINISM_ARGS", [])) != DET_ARGS:
        raise RuntimeError(f"ec2.DETERMINISM_ARGS drifted: {ec2.DETERMINISM_ARGS!r}")

    def spec_split(model: str):
        """(base_args_without_bundle, bundle_args) for a spec."""
        spec_args = list(ec2.EC2_DEPLOY_SPECS[model]["vllm_args"])
        if spec_args[-len(DET_ARGS):] != DET_ARGS:
            raise RuntimeError(f"{model}: bundle not at the tail of {spec_args!r}")
        base = spec_args[:-len(DET_ARGS)]
        if any(a in base for a in DET_ARGS):
            raise RuntimeError(f"{model}: determinism flags survived the strip: {base!r}")
        return base, spec_args

    moe_base, moe_det = spec_split(args.moe_model)
    dense_base, dense_det = spec_split(args.dense_model)

    ARMS = {
        "A": {"name": "MOE-DET-TP8", "model": args.moe_model,
              "args": moe_det, "minutes": args.armA_min, "max_k": 4},
        "A2": {"name": "MOE-DET-TP8-EXTENDED", "model": args.moe_model,
               "args": moe_det, "minutes": args.armA2_min, "max_k": 4},
        "B": {"name": "DENSE-DET-TP8-NOCAR", "model": args.dense_model,
              "args": dense_det + ["--disable-custom-all-reduce"],
              "minutes": args.armB_min, "max_k": 8},
        "C": {"name": "STOCK-TP8-CONTROL", "model": args.dense_model,
              "args": dense_base + ["--enable-prefix-caching"],
              "minutes": args.armC_min, "max_k": 4},
    }

    report_path = OUT_DIR / args.report
    _tag = pathlib.Path(args.report).stem
    report: Dict[str, Any] = {}
    if report_path.exists():
        report = json.loads(report_path.read_text())
    report.update({
        "probe": "moe_tp8", "expect_tp": args.expect_tp, "type": args.type,
        "regions": args.regions, "seed": hw.SEED, "temperature": hw.TEMPERATURE,
        "max_tokens": hw.MAX_TOKENS, "stream": True,
        "started_utc": report.get("started_utc") or _dt.datetime.now(
            _dt.timezone.utc).isoformat(),
        "arm_plan": {k: {"name": v["name"], "model": v["model"], "vllm_args": v["args"],
                         "minutes": v["minutes"]} for k, v in ARMS.items()},
    })
    report.setdefault("arms", {})

    def save() -> None:
        report_path.write_text(json.dumps(report, indent=1))

    save()
    state = None
    measured_rate: Dict[str, float] = {}
    try:
        state = ec2.provision_spot_instance(
            instance_types=tuple(args.type.split(",")),
            regions=tuple(args.regions.split(",")),
            idle_timeout_min=45,
        )
        logging.info("moetp8: provisioned %s (%s @ %s)", state["instance_id"],
                     state["instance_type"], state.get("availability_zone"))
        report["instance"] = {k: state.get(k) for k in
                              ("instance_id", "instance_type", "region",
                               "availability_zone", "public_ip", "launched_at")}
        report["provisioned_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
        report["provision_min"] = round((time.time() - t_start) / 60.0, 1)
        save()

        for code in [a.strip() for a in args.arms.split(",") if a.strip()]:
            arm = ARMS[code]
            if report["arms"].get(code, {}).get("complete"):
                logging.info("moetp8: arm %s already complete; skipping", code)
                continue
            mins = (time.time() - t_start) / 60.0
            if mins > args.hard_stop_min - 12:
                logging.warning("moetp8: %.1f min elapsed -- SKIPPING arm %s", mins, code)
                report["arms"].setdefault(code, {})["skipped_at_min"] = round(mins, 1)
                save()
                continue

            model = arm["model"]
            prompts8 = hw.load_prompts(model, 8)          # prefix-stable selection
            entry: Dict[str, Any] = {
                "arm_name": arm["name"], "model": model, "vllm_args": arm["args"],
                "arm_started_min": round(mins, 1),
                "prompt_ids_available": sorted(p for p, _ in prompts8),
            }
            report["arms"][code] = entry
            save()
            arm_t0 = time.time()
            ec2.EC2_DEPLOY_SPECS[model]["vllm_args"] = arm["args"]
            logging.info("moetp8: arm %s (%s) model=%s args=%s",
                         code, arm["name"], model, arm["args"])
            try:
                with ec2.serve_model(model, force=True):
                    st = ec2._load_state() or {}
                    served_tp = (st.get("last_serve") or {}).get("tp")
                    entry["served_tp"] = served_tp
                    entry["launch_payload_vllm_args"] = list(
                        (st.get("serving") or {}).get("vllm_args") or [])
                    entry["server_config"] = ec2.server_config(model) or {}
                    entry["fingerprint"] = hinge.fingerprint(state, model)
                    entry["serve_log"] = tp8.capture_serve_log(state)
                    entry["serve_min"] = round((time.time() - arm_t0) / 60.0, 1)
                    save()
                    if served_tp != args.expect_tp:
                        raise RuntimeError(
                            f"tp GATE FAILED: launched tp={served_tp!r}, expected "
                            f"{args.expect_tp}. Refusing to measure.")
                    sl = entry["serve_log"]
                    logging.info("moetp8[%s]: tp GATE PASSED tp=%s gpu=%s vllm=%s",
                                 code, served_tp, entry["server_config"].get("gpu"),
                                 entry["server_config"].get("vllm_version"))
                    logging.info("moetp8[%s]: serve_log http=%s chars=%s parsed=%s",
                                 code, sl.get("http_status"), sl.get("vllm_log_chars"),
                                 sl.get("engine_config_parsed"))
                    entry["serve_log_usable"] = bool(sl.get("vllm_log_chars"))
                    save()

                    # Probe once per MODEL. Arm C serves with prefix caching
                    # ON, so a warmup on a prompt that is IN the comparison set
                    # would seed the cache for row 1 and blunt the positive
                    # control; reusing arm B's dense rate avoids that entirely,
                    # and the fallback probe uses prompts8[-1], which is outside
                    # arm C's max_k=4 prefix.
                    if model in measured_rate:
                        rate = measured_rate[model]
                        entry["throughput_probe"] = {"reused_from_earlier_arm": rate}
                        logging.info("moetp8[%s]: reusing measured %.1f tok/s", code, rate)
                    else:
                        warm = prompts8[0][1] if code != "C" else prompts8[-1][1]
                        rate = throughput_probe(ec2, hw, model, warm, entry)
                        measured_rate[model] = rate
                    save()
                    remaining = arm["minutes"] - (time.time() - arm_t0) / 60.0
                    k = pick_k(rate, prompts8, max(remaining, 1.0), arm["max_k"])
                    forced = dict(
                        (kv.split("=")[0].strip(), int(kv.split("=")[1]))
                        for kv in args.force_k.split(",") if "=" in kv)
                    if code in forced:
                        entry["k_from_estimator"] = k
                        k = min(forced[code], arm["max_k"], len(prompts8))
                        entry["k_forced"] = k
                    entry["k_chosen"] = k
                    entry["k_budget_min_remaining"] = round(remaining, 1)
                    logging.info("moetp8[%s]: %.1f min left at ~%.1f tok/s -> k=%d",
                                 code, remaining, rate, k)
                    arm_prompts = prompts8[:k]
                    entry["n_prompts_this_arm"] = k
                    save()

                    # Arm-relative deadlines: no NEW prompt after the arm's own
                    # window. resilient_pass takes an absolute t0 + a minute
                    # cap, so passing arm_t0 makes the cap arm-relative.
                    p1_cap = arm["minutes"] * 0.60
                    p2_cap = arm["minutes"] * 1.02
                    p1 = tp8.resilient_pass(
                        hw, ec2, model, arm_prompts, f"{code}:P1", entry, "P1",
                        OUT_DIR / f"texts_{_tag}_{code}_{model}_P1.json.gz",
                        p1_cap, arm_t0, save)
                    entry["pass_done_P1_min"] = round((time.time() - arm_t0) / 60.0, 1)
                    save()
                    p2_prompts = [(pid, txt) for pid, txt in arm_prompts if pid in p1]
                    entry["n_prompts_compared"] = len(p2_prompts)
                    p2 = tp8.resilient_pass(
                        hw, ec2, model, p2_prompts, f"{code}:P2", entry, "P2",
                        OUT_DIR / f"texts_{_tag}_{code}_{model}_P2.json.gz",
                        p2_cap, arm_t0, save)
                    entry["pass_done_P2_min"] = round((time.time() - arm_t0) / 60.0, 1)
                    entry["fingerprint_after"] = hinge.fingerprint(state, model)
                    entry["serve_log_after"] = tp8.capture_serve_log(state)
                    entry["within_process_baseline"] = tp8.guarded_compare(hw, p1, p2)
                    # First differing byte offset for any divergent row.
                    diffs = []
                    for pid in sorted(set(p1) & set(p2)):
                        if p1[pid] != p2[pid] and len(p1[pid]) > 1 and len(p2[pid]) > 1:
                            off = next((i for i, (x, y) in enumerate(zip(p1[pid], p2[pid]))
                                        if x != y), min(len(p1[pid]), len(p2[pid])))
                            diffs.append({"prompt": pid, "first_diff_byte": off,
                                          "len_P1": len(p1[pid]), "len_P2": len(p2[pid])})
                    entry["divergent_rows"] = diffs
                    # Free cross-comparison against tonight's committed tp=8
                    # custom-all-reduce dense arm (same prompts/seed/image).
                    if model == args.dense_model:
                        entry["vs_head_tp8_customAR"] = _vs_head(entry.get("sha_table_P1") or {})
                    if code == "A2":
                        entry["vs_run1_armA_cross_process"] = _vs_run1(
                            entry.get("sha_table_P1") or {})
                    entry["arm_total_min"] = round((time.time() - arm_t0) / 60.0, 1)
                    entry["complete"] = True
                    save()
                    c = entry["within_process_baseline"]
                    logging.info("moetp8[%s]: %d/%d identical (excluded empty: %s)",
                                 code, c["identical"], c["n"], c["excluded_empty_rows"])
            except Exception as exc:  # noqa: BLE001 -- an arm must not kill the run
                entry["FAILED"] = f"{type(exc).__name__}: {exc}"
                try:
                    entry["serve_log_on_failure"] = tp8.capture_serve_log(state)
                except Exception:  # noqa: BLE001
                    pass
                save()
                logging.exception("moetp8: arm %s FAILED (continuing)", code)

        report["finished_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
        report["elapsed_min"] = round((time.time() - t_start) / 60.0, 1)
        save()
        print("\n=== moe-tp8 ===")
        for code, e in report["arms"].items():
            c = e.get("within_process_baseline")
            if c:
                print(f"  {code} {e.get('arm_name')}: {c['identical']}/{c['n']} identical")
            else:
                print(f"  {code} {e.get('arm_name')}: {e.get('FAILED') or e.get('skipped_at_min')}")
        print("report:", report_path)
    finally:
        report["teardown_attempted_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
        save()
        try:
            ec2.shutdown_instance()
            report["teardown"] = "shutdown_instance() returned"
        except Exception as exc:  # noqa: BLE001
            report["teardown"] = f"FAILED: {type(exc).__name__}: {exc}"
            logging.exception("TEARDOWN FAILED -- terminate by hand")
        report["finished_utc"] = report.get("finished_utc") or _dt.datetime.now(
            _dt.timezone.utc).isoformat()
        report["elapsed_min"] = round((time.time() - t_start) / 60.0, 1)
        save()
    return 0


def _vs_head(this_sha: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """SHA comparison against tonight's committed tp=8 dense det arm.

    Same model, prompts, seed, temperature, max_tokens, vLLM image digest and
    instance family -- differing ONLY in the collective/config flag under test.
    A mismatch here is mechanistic evidence that the collective kernel actually
    changed; combined with an internally k/k arm it says "different kernel,
    still deterministic" without depending on any log parsing.
    """
    try:
        prev = json.loads(HEAD_TP8.read_text())["arms"]["det"]["sha_table_P1"]
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
    shared = sorted(set(prev) & set(this_sha))
    rows = [{"prompt": p, "head_sha": prev[p]["sha256_12"],
             "this_sha": this_sha[p]["sha256_12"],
             "head_len": prev[p]["len"], "this_len": this_sha[p]["len"],
             "same": prev[p]["sha256_12"] == this_sha[p]["sha256_12"]} for p in shared]
    return {"available": True, "n": len(shared),
            "identical": sum(r["same"] for r in rows),
            "note": "HEAD arm = tp=8 p5.48xlarge H100 WITH custom all-reduce, "
                    "same image digest / prompts / seed.",
            "rows": rows}


def _vs_run1(this_sha: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """A2's P1 vs run 1's arm-A P1: same model, prompts, seed, bundle, config --
    but a DIFFERENT server process on a DIFFERENT box. This is a cross-process
    reading for a tp=8 MoE, the regime where the study has only ever measured a
    dense cross-process flip rate (9.5%, plan section 6.2). Agreement is a
    bonus; disagreement is expected-and-documented, NOT a within-process
    failure, and must never be reported as one."""
    try:
        prev = json.loads((OUT_DIR / "moe_tp8_report.json").read_text())[
            "arms"]["A"]["sha_table_P1"]
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
    shared = sorted(set(prev) & set(this_sha))
    rows = [{"prompt": p, "run1_sha": prev[p]["sha256_12"],
             "run2_sha": this_sha[p]["sha256_12"],
             "run1_len": prev[p]["len"], "run2_len": this_sha[p]["len"],
             "same": prev[p]["sha256_12"] == this_sha[p]["sha256_12"]} for p in shared]
    return {"available": True, "n": len(shared),
            "identical": sum(r["same"] for r in rows),
            "note": "CROSS-PROCESS and cross-instance; not a within-process test.",
            "rows": rows}


if __name__ == "__main__":
    raise SystemExit(main())
