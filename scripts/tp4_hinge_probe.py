"""Probe whether the determinism bundle survives multi-GPU tensor parallelism.

This is the tp=4 extension of the 2026-08-16 hinge probe.

Why
---
`notebooks/DETERMINISM_PLAN_2026-08-16.md` section 3 certified the bundle
(`--no-enable-prefix-caching --max-num-seqs 1 --enforce-eager --seed 0`) at
**tp=1** on a single L40S: 8/8 byte-identical within one process, for both
nemotron-3-nano-4b and ministral-3-3b. 18 of 22 deploy specs serve at tp=4
or tp=8, where multi-GPU all-reduce ordering is an untested nondeterminism
source (the docs carry exactly that scope caveat). This probe measures it.

Design (one g6e.12xlarge = 4x L40S, PCIe, no NVLink)
----------------------------------------------------
  arm 1  det@tp4    ministral-3-3b under the bundle. THE VERDICT ARM.
  arm 2  stock@tp4  ministral-3-3b under the study-era stock config.
                     POSITIVE CONTROL: tp=1 stock was 0/8 (all eight
                     prompts diverged). If stock@tp4 is also ~0/8, the
                     probe demonstrably still DETECTS nondeterminism on
                     this box, so an 8/8 det arm cannot be "the probe
                     went blind".

A separate run against nemotron-3-nano-4b (pass ``--model
nemotron-3-nano-4b``) repeats the det arm on that model, time and budget
permitting.

The protocol is the hinge's, unchanged: the same 8 deterministically-selected
real deduction prompts, the same seed/temperature/max_tokens, two
back-to-back passes within ONE server process, byte-compared.

Pre-committed rules (fixed before any data was seen)
----------------------------------------------------
  * tp GATE. ministral-3-3b has 32 attention heads; g6e.12xlarge has 4
    GPUs. So ec2.derive_tp -> gcd(32,4)=4, and serve_model POSTs tp=4 to
    the agent, which passes `--tensor-parallel-size 4`. As of 2026-08-23
    this is ASSERTED from the CONTAINER's own engine-config log line
    (`tp8_hinge_probe.tp_gate`, fed the output of `capture_serve_log`),
    NOT from the recorded launch payload. The payload can only confirm
    the driver agrees with itself. It cannot detect a container that
    actually came up serving a different tp: certifying tp=4 from a
    tp=1 container is exactly the failure mode this guard exists for
    (D5.3). The payload's own `tp` readback is still recorded and
    cross-checked against the container's. The two disagreeing aborts
    the arm, rather than banking either. An unparseable or absent
    engine-config capture also aborts the arm; it never silently falls
    back to the payload. A mismatch (or an unparseable log) aborts the
    arm before a single prompt is sent.
  * EMPTY ROWS ARE EXCLUDED ONLY WHEN BOTH PASSES ARE EMPTY (D8.3
    correction; see `guarded_compare` below). Streaming transport is on,
    and this probe reuses the hinge's retry guard. The retry trigger
    itself, re-ask once on a length <= 1 delivery, is unchanged. But a
    row that is STILL length <= 1 after the retry is no longer
    automatically "unmeasured". A row where exactly ONE pass came back
    empty and the other did not is the single most DIVERGENT outcome the
    probe can observe. It stays IN the identity denominator, named under
    `one_sided_empty_rows`. Only a row where BOTH passes are still <= 1
    chars after the retry is excluded as a true non-event, named under
    `excluded_empty_rows`.
  * ARM-LEVEL CHECKPOINTS. A spot reclaim between P1 and P2 kills the
    server process. If P2 resumed against a new process, that would
    silently convert a within-process test into a cross-process one
    (measured cross-process flip rate 9.5%, plan section 6.2), and could
    manufacture a refutation. Completed arms persist. This script
    re-runs an interrupted arm from P1.

Usage
-----
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
from typing import Any, Dict, List, Optional

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


def _load_tp8():
    """Load `tp8_hinge_probe.py` by path, mirroring `_load_hwprobe`/`_load_hinge`.

    Design (D5.3): the CONTAINER-reading tp gate (`tp_gate`) and the
    authenticated serve-log capture (`capture_serve_log`) both already
    exist in `tp8_hinge_probe.py`. The directive that introduced this
    function requires reuse over duplication: a second,
    independently-drifting copy of a safety gate is exactly the kind of
    half-applied fix `test_guarded_compare_excludes_only_both_empty_rows`
    exists to catch for `guarded_compare`.
    """
    spec = importlib.util.spec_from_file_location(
        "tp8_hinge_probe", REPO_ROOT / "scripts" / "tp8_hinge_probe.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def sha_table(passes: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """Return SHA + length for EVERY row, identical ones included.

    The tp=1 hinge JSON stores digests only for DIFFERING rows, which is
    why no tp=1-vs-tp=4 byte comparison is possible from the archive. This
    function records all of them here, so the next such comparison is
    free.
    """
    return {p: {"sha256_12": hashlib.sha256(t.encode()).hexdigest()[:12], "len": len(t)}
            for p, t in sorted(passes.items())}


def guarded_compare(hw, a: Dict[str, str], b: Dict[str, str]) -> Dict[str, Any]:
    """Apply the pre-committed empty-row exclusion to hw.compare().

    A row is "empty" (length <= 1) because the stored text is
    ``reasoning + "\\x00" + content``. A row with neither channel
    populated is exactly the one separator byte. A row is excluded from
    the identity denominator ONLY when BOTH passes are empty: that is the
    sole case where "nothing was measured" is a true description. A row
    where exactly ONE side is empty is not unmeasured. It is the single
    most DIVERGENT outcome the probe can observe (one pass produced real
    text, the other produced none), and MUST stay in the denominator,
    entering ``n``/``diffs`` through ``hw.compare`` like any other
    disagreement. This function also surfaces it in
    ``one_sided_empty_rows``, so it can be inspected without re-deriving
    it from the diff list.

    Parameters
    ----------
    hw : module
        The loaded ``hardware_equivalence_probe`` module, supplying
        ``compare()``.
    a, b : dict of str to str
        Pass-1 and pass-2 rows, keyed by prompt id. Values are the
        ``reasoning + "\\x00" + content`` serialization produced by
        ``hardware_equivalence_probe.run_pass``.

    Returns
    -------
    dict
        ``hw.compare(a2, b2)`` (``n``, ``identical``, ``rate``, ``diffs``)
        over the rows surviving exclusion, plus:

        ``excluded_empty_rows``
            Sorted prompt ids where BOTH sides are ``<= 1`` char. Removed
            from ``a2``/``b2`` and therefore absent from ``n``.
        ``one_sided_empty_rows``
            Sorted prompt ids where EXACTLY ONE side is ``<= 1`` char.
            Always present (``[]`` when none). These rows are NOT removed
            from ``a2``/``b2``.
        ``n_before_exclusion``
            ``len(set(a) & set(b))`` -- the shared-key count before any
            exclusion, unchanged by this fix.

    Notes
    -----
    Design: the rule used to be "exclude when EITHER side is empty" (``or``
    instead of the both-sides ``and`` below). The incident that forced this
    fix: in the moe run-2 stock control, prompt
    ``CategoryTheory.Limits.Types.Pushout.condition/prompts/hint-2.md`` had
    P1 = 83,661 characters (sha ``1e6e5acf9886``) and P2 = 1 character.
    That P2 was NOT a non-event. It was a 106,545-character reasoning-only
    cap-hit that the client was, at the time, discarding on delivery (a
    separate, since-fixed defect). One pass produced 83k characters, and
    the other produced nothing: the most divergent outcome available. The
    old rule scored it "excluded (empty)", turning a 0/4 control into a
    reported 0/3. The both-empty rule closes that hole. A one-sided empty
    row can never be counted as agreement (see
    ``test_guarded_compare_one_sided_row_can_never_be_identical``), so
    admitting it to the denominator can only ever lower the measured rate.
    """
    shared = set(a) & set(b)
    both_empty = sorted(p for p in shared
                        if len(a.get(p, "")) <= 1 and len(b.get(p, "")) <= 1)
    one_sided = sorted(p for p in shared
                       if (len(a.get(p, "")) <= 1) != (len(b.get(p, "")) <= 1))
    a2 = {p: t for p, t in a.items() if p not in both_empty}
    b2 = {p: t for p, t in b.items() if p not in both_empty}
    out = hw.compare(a2, b2)
    out["excluded_empty_rows"] = both_empty
    out["one_sided_empty_rows"] = one_sided
    out["n_before_exclusion"] = len(shared)
    return out


def _stock_control_str(report: Dict[str, Any]) -> Optional[str]:
    """Return ``"identical/n"`` for the sibling `stock` positive control, or `None`.

    Design (D8): `hardware_equivalence_probe.verdict_line`'s
    `stock_control` parameter wants a short summary of the STOCK arm's own
    within-process byte comparison, so a HOLD verdict names the positive
    control it was banked alongside. This is the exact provenance that
    was missing when the tp=8 dense HOLD was reported next to a `stock`
    control that had collected zero rows. This function is factored out
    here, rather than inlined at the `det` and `stock` arm call sites, so
    the two cannot independently drift.

    Parameters
    ----------
    report : dict
        The in-progress report dict; read from ``report["arms"]["stock"]``.

    Returns
    -------
    str or None
        ``f"{identical}/{n}"`` when the `stock` arm's own
        ``within_process_baseline`` has already been recorded in
        `report`, else `None`. `None` covers: the stock arm has not run
        yet, is still in progress, or failed before producing a
        comparison. `None` is the literal signal `verdict_line` renders
        as ``"absent"``.

    Notes
    -----
    Pure and side-effect-free. Reads `report`, mutates nothing.
    """
    c = (report.get("arms", {}).get("stock", {}) or {}).get("within_process_baseline")
    if not c:
        return None
    return f"{c['identical']}/{c['n']}"


def main() -> int:
    # Design (D8.2): this loads before the argparse parser is built, so
    # --sensitivity-max-tokens can default to hw.MAX_TOKENS directly,
    # rather than duplicating its literal value here (which would
    # silently drift if the study's own token budget ever changed). It is
    # safe to load this early: neither this module nor
    # `smolbench.evals.ec2` reads any environment variable at import
    # time. They read env vars only inside functions, after the env vars
    # this driver sets below are already in place.
    hw = _load_hwprobe()

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
    ap.add_argument("--sensitivity-max-tokens", type=int, default=hw.MAX_TOKENS,
                    help="max_tokens for the D8 in-process sensitivity-control row "
                         "(one extra generation per arm from a deterministically "
                         "perturbed copy of the arm's first prompt). Defaults to "
                         "the study's own max_tokens so the default changes no "
                         "protocol. Lowering it is sound: evaluate_sensitivity() "
                         "is prefix-aware, so a control row that diverges before "
                         "it hits a smaller cap is still scored SENSITIVE, not "
                         "merely truncated -- and a smaller cap bounds the "
                         "control's added cost on slow arms.")
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

    hinge = _load_hinge()
    tp8 = _load_tp8()
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
                    # Design (D5.3): this captures the serve log
                    # UNCONDITIONALLY, not only from the `except` branch
                    # below. A SUCCESSFUL arm previously recorded nothing
                    # about which tp the container actually came up
                    # serving. That left `served_tp` (the driver's own
                    # readback) as the only evidence on file, even though
                    # the run went fine.
                    entry["serve_log"] = tp8.capture_serve_log(state)
                    entry["mechanism_evidence"] = hw.mechanism_evidence(entry["serve_log"])
                    if entry["mechanism_evidence"] == "UNMEASURED":
                        logging.warning(
                            "tp4hinge[%s]: mechanism_evidence=UNMEASURED -- no "
                            "config claim (custom all-reduce state, "
                            "enforce-eager, prefix-caching) may be made for "
                            "this arm; the byte-comparison result below "
                            "remains fully reportable regardless.", arm)
                    save()
                    # Design (D5.3): the gate now reads the CONTAINER's own
                    # engine-config line via tp8.tp_gate, not `served_tp`.
                    # `served_tp` is only the value the driver itself
                    # computed and POSTed. It can only confirm the driver
                    # agrees with itself, and cannot detect a container
                    # that actually came up at a different tp. tp_gate
                    # raises RuntimeError on any mismatch or unparseable
                    # capture. The surrounding `except` below records
                    # FAILED and aborts this arm: the documented "a
                    # mismatch aborts that arm" contract.
                    gate = tp8.tp_gate(entry["serve_log"], args.expect_tp, served_tp)
                    entry["gate_basis"] = gate["gate_basis"]
                    entry["engine_tp"] = gate["engine_tp"]
                    entry["payload_agrees"] = gate["payload_agrees"]
                    save()
                    logging.info("tp4hinge[%s]: tp GATE PASSED via %s (engine_tp=%s, "
                                 "payload_tp=%s, gpu=%s, vllm=%s, nvidia_smi=%s)",
                                 arm, gate["gate_basis"], gate["engine_tp"],
                                 gate["payload_tp"], cfg.get("gpu"), cfg.get("vllm_version"),
                                 str((cfg.get("agent_fingerprint") or {}).get("nvidia_smi"))[:200])
                    passes: Dict[str, Dict[str, str]] = {}
                    for i in (1, 2):
                        label = f"{arm}@tp{args.expect_tp}:P{i}"
                        # D6.4: a fresh dict per pass. guarded_pass mutates
                        # it in place with per-row finish_reason/token
                        # counts.
                        row_meta: Dict[str, Dict[str, Any]] = {}
                        res = hinge.guarded_pass(hw, args.model, arm_prompts, label,
                                                 meta=row_meta)
                        retr = res.pop("_retried_rows", None)
                        if retr:
                            entry[f"retried_rows_P{i}"] = json.loads(retr)
                        passes[f"P{i}"] = res
                        entry[f"sha_table_P{i}"] = sha_table(res)
                        entry[f"row_meta_P{i}"] = row_meta
                        save()
                        with gzip.open(OUT_DIR / f"texts_{args.model}_{arm}_P{i}.json.gz",
                                       "wt") as fh:
                            json.dump(res, fh)
                    entry["fingerprint_after"] = hinge.fingerprint(state, args.model)

                    # D8: the arm's own in-process control, which runs
                    # AFTER P2 so it can never perturb prefix-cache state
                    # between the two passes being compared. See
                    # scripts/moe_tp8_probe.py's D8 design note for why a
                    # HOLD must be tied to a control that actually fired,
                    # and why a same-model `stock` control cannot serve
                    # as a universal substitute.
                    try:
                        _spid, _sptext = arm_prompts[0]
                        entry["sensitivity_row"] = hw.run_sensitivity_row(
                            ec2, args.model, _spid, _sptext,
                            passes["P1"].get(_spid, ""),
                            max_tokens=args.sensitivity_max_tokens)
                    except Exception as exc:  # noqa: BLE001 -- a failed control is BLIND, not fatal
                        entry["sensitivity_row"] = {"error": f"{type(exc).__name__}: {exc}"}
                        logging.exception("tp4hinge[%s]: sensitivity control FAILED", arm)
                    entry["control_status"] = hw.control_status(entry["sensitivity_row"])
                    # Design (D8 follow-up): index by (model, instance_id,
                    # arm) via the shared helper, not a hand-rolled
                    # (model, instance_id) key -- this driver runs both
                    # `det` and `stock` arms against the same model on
                    # the same box, so a two-part key is needed. See
                    # scripts/moe_tp8_probe.py's D8 design note and
                    # hw.sensitivity_key's docstring for the incident.
                    report.setdefault("sensitivity_rows", {})[
                        hw.sensitivity_key(args.model, state.get("instance_id"), arm)
                    ] = entry["sensitivity_row"]
                    save()

                    entry["within_process_baseline"] = guarded_compare(
                        hw, passes["P1"], passes["P2"])
                    c = entry["within_process_baseline"]
                    entry["verdict_line"] = hw.verdict_line(
                        arm=arm, identical=c["identical"], n=c["n"],
                        control_status=entry["control_status"], model=args.model,
                        instance_id=state.get("instance_id"),
                        stock_control=_stock_control_str(report),
                        mechanism_evidence=entry.get("mechanism_evidence"))
                    logging.info("tp4hinge[%s]: %s (excluded empty: %s)",
                                 arm, entry["verdict_line"], c["excluded_empty_rows"])
                    entry["serve_plus_passes_s"] = round(time.time() - t0, 1)
                    entry["complete"] = True
                    save()
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
                # Design (D8.2): print the scoped verdict line (see
                # scripts/moe_tp8_probe.py's D8 design note); the `or`
                # fallback covers a report from a pre-D8 run of this
                # driver, whose entries lack `verdict_line`.
                line = e.get("verdict_line") or f"{c['identical']}/{c['n']} identical"
                print(f"  {arm}@tp{args.expect_tp}: {line}"
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
