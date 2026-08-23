"""The hinge experiment: is the 8/8 determinism "noise floor" prefix-cache replay?

WHY THIS EXISTS
---------------
`notebooks/DETERMINISM_PLAN_2026-08-16.md` section 3 specifies this run; read it
first -- the predictions and refutation criteria are pre-registered there and this
script only executes them. In brief: the study's same-box reproducibility baseline
(`nemotron-3-nano-4b` 8/8 byte-identical across two back-to-back passes) was
measured with `--enable-prefix-caching` ON, and the second pass re-sends the first
pass's exact prompts -- so its prefill is a cache hit replaying the first pass's
KV. The celebrated noise floor may be measuring the cache, not the kernels. And
`ministral-3-3b`'s 0/8 on its OWN same-box baseline -- the result that got it
written off as "nothing can be measured for it" -- was measured only under that
same configuration.

Four arms, two boxes, ONE box per model serving BOTH configs (the control agent's
``/serve`` swaps containers, and each swap is a fresh process -- exactly what a
within-process baseline requires):

  stock  the archived configuration, unchanged  -> replicates the archived number
  det    prefix caching OFF, --max-num-seqs 1, --enforce-eager, --seed 0

Per config: two back-to-back passes over the SAME 8 archived prompts, byte-compared.

  arm A = nemotron det   : drops below 8/8  => the floor was cache replay
  arm B = nemotron stock : expected 8/8     (comparability control)
  arm C = ministral det  : goes to 8/8      => the "unmeasurable" verdict is wrong
  arm D = ministral stock: expected 0/8     (replication)

REFUTED if arm C stays at 0/8. Exonerated if arm A stays 8/8.

Lessons from the archive this script bakes in rather than repeats:
  - STREAMING TRANSPORT ON (``EC2_STREAM_COMPLETIONS=1``), else a cap-length
    response can vanish on the wire and the probe re-measures the transport
    fault instead of the sampler. Any row of length <= 1 is the fault's
    signature: re-asked once and BOTH results recorded.
  - FINGERPRINT RECORDED PER CONFIG (vLLM /version, image digest from the agent
    log, prefix-cache metric lines) -- the archived probes' "same image"
    assumption was unverifiable because nobody wrote the build down, and the
    study ended with five recorded builds plus at least one unrecorded one.
  - The determinism args REPLACE ``--enable-prefix-caching`` rather than append
    after it: prefix caching is default-ON in vLLM V1, so the explicit negation
    is required and the positive flag must not be left to argue with it.
  - The study spec is overridden IN PROCESS only; ``EC2_DEPLOY_SPECS`` on disk
    is never edited, and the probe runs under its own tag/state file so it can
    never adopt a study lane's box.

USAGE
    set -a && source notebooks/deduction/keys.env && source notebooks/ec2-operator.env && set +a
    unset EC2_EXPERIMENT_TAG
    .venv/bin/python scripts/hinge_probe.py --model nemotron-3-nano-4b
    .venv/bin/python scripts/hinge_probe.py --model ministral-3-3b

Writes ``notebooks/deduction/results/hinge_<model>.json`` and tears its box down
in a ``finally``. Roughly 45-70 min and ~$2-3.5 per model at g6e.4xlarge spot.
"""

import argparse
import importlib.util
import json
import logging
import os
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "notebooks" / "deduction" / "results"

#: The determinism configuration under test. Replaces the spec's
#: ``--enable-prefix-caching`` (see module docstring); model-specific args like
#: ministral's reasoning parser are PRESERVED from the original spec.
DET_ARGS = ["--no-enable-prefix-caching", "--max-num-seqs", "1",
            "--enforce-eager", "--seed", "0"]


def _load_hwprobe():
    """Imports the archived probe's helpers (load_prompts / run_pass / compare).

    Reused rather than copied so the hinge arms measure with byte-identical
    machinery to the archived baselines they replicate -- same prompt selection
    (deterministic S3 sort+stride), same request shape, same comparison.
    """
    spec = importlib.util.spec_from_file_location(
        "hardware_equivalence_probe",
        REPO_ROOT / "scripts" / "hardware_equivalence_probe.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def fingerprint(state: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Records what the archived probes failed to: WHICH server this is.

    Best-effort by design -- a missing endpoint is recorded as missing, never
    fatal, because the run's scientific payload is the byte comparison and a
    partial fingerprint is still more than the archive had.
    """
    import requests

    ip = state["public_ip"]
    out: Dict[str, Any] = {}
    try:
        r = requests.get(f"http://{ip}:8000/version",
                         headers={"Authorization": f"Bearer {state['vllm_api_key']}"},
                         timeout=10)
        out["vllm_version"] = r.json() if r.ok else f"HTTP {r.status_code}"
    except Exception as exc:  # noqa: BLE001 -- absence is a recordable fact
        out["vllm_version"] = f"unavailable: {type(exc).__name__}"
    try:
        r = requests.get(f"http://{ip}:8000/metrics",
                         headers={"Authorization": f"Bearer {state['vllm_api_key']}"},
                         timeout=10)
        lines = r.text.splitlines() if r.ok else []
        out["cache_metric_lines"] = [
            l for l in lines
            if ("prefix" in l or "cache_config" in l) and not l.startswith("#")
        ][:12]
    except Exception as exc:  # noqa: BLE001
        out["cache_metric_lines"] = [f"unavailable: {type(exc).__name__}"]
    try:
        r = requests.get(f"http://{ip}:9000/status", timeout=10)
        tail = json.dumps(r.json()) if r.ok else ""
        out["image_digest_lines"] = sorted(
            {seg[:80] for seg in tail.replace("\\n", "\n").splitlines()
             if "Digest: sha256" in seg or "vllm-0." in seg}
        )[:6]
    except Exception as exc:  # noqa: BLE001
        out["image_digest_lines"] = [f"unavailable: {type(exc).__name__}"]
    return out


def guarded_pass(hw, model: str, prompts: List[Tuple[str, str]],
                 label: str,
                 meta: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, str]:
    """One probe pass with the delivery-fault guard from plan section 3.3.

    A stored row of length <= 1 is the transport fault's signature (an empty
    body, not a divergence). Such a row is re-asked ONCE and both results kept:
    the retry under ``retried_rows`` for the record, the retry's text in the
    comparison IF it is non-empty (a real generation), the original otherwise
    (twice-empty means empty IS the response and belongs in the comparison).

    Parameters
    ----------
    hw : module
        The loaded ``hardware_equivalence_probe`` module, supplying
        ``SEED``/``TEMPERATURE``/``MAX_TOKENS`` and ``run_pass``.
    model : str
        Deploy-spec model id being served.
    prompts : list of (str, str)
        ``(prompt_id, prompt_text)`` pairs.
    label : str
        Log-line prefix for this pass.
    meta : dict of str to dict, optional
        Forwarded to ``hw.run_pass`` and then, on the retry path, updated IN
        PLACE (see Notes). Omit to skip metadata collection.

    Returns
    -------
    dict of str to str
        ``{prompt_id: reasoning + "\\x00" + content}``, plus (only when at
        least one row was retried) a ``"_retried_rows"`` marker key holding a
        JSON-encoded ``{prompt_id: {"original_len", "retry_len"}}`` map --
        popped by the caller before the dict is used as a comparison pass.

    Notes
    -----
    Design: the retry call uses ``ec2.complete()`` rather than ``ec2.query()``
    for the same reason ``hardware_equivalence_probe.run_pass`` does -- the
    delivery-fault retry is exactly where a real cap-hit (``finish_reason ==
    "length"``, a large ``completion_tokens``) is most likely to be sitting
    behind an apparently-empty row, and that fact would otherwise be lost the
    moment the retry runs.

    When ``meta`` is given, ``hw.run_pass`` has already populated
    ``meta[pid]`` for every prompt (including the ones retried here, from
    their FIRST attempt). On this retry path:

    * an ACCEPTED retry (``len(redo) > 1``) OVERWRITES ``meta[pid]`` with the
      retry's own metadata plus ``"from_retry": True`` -- the retry's numbers,
      not the discarded first attempt's, describe the row that is actually
      compared;
    * a REJECTED retry (``len(redo) <= 1``, i.e. still empty) leaves the
      original ``meta[pid]`` untouched and adds ``"retry_rejected": True`` to
      it, so a twice-empty row's metadata is not silently discarded either.
    """
    from smolbench.evals import ec2

    results = hw.run_pass(model, prompts, label, meta=meta)
    retried: Dict[str, str] = {}
    for pid, text in list(results.items()):
        if len(text) <= 1:
            logging.warning("%s: row %s has length %d -- delivery-fault "
                            "signature; re-asking once", label, pid, len(text))
            prompt_text = dict(prompts)[pid]
            ctx = ec2._CLIENT.context_length(model)
            # `ChatClient.complete` takes `context_length` KEYWORD-ONLY
            # (unlike `query`'s positional-or-keyword parameter of the same
            # name) -- pass it by keyword rather than positionally.
            rsp = ec2.complete(
                prompt_text, model, hw.SEED,
                context_length=ctx,
                extra_args={"temperature": hw.TEMPERATURE,
                            "max_tokens": hw.MAX_TOKENS},
                request_timeout=1800,
            )
            redo = (rsp.reasoning or "") + "\x00" + (rsp.content or "")
            retried[pid] = {"original_len": len(text), "retry_len": len(redo)}
            if len(redo) > 1:
                results[pid] = redo
                if meta is not None:
                    meta[pid] = {
                        "finish_reason": rsp.finish_reason,
                        "completion_tokens": rsp.completion_tokens,
                        "prompt_tokens": rsp.prompt_tokens,
                        "chars": len(redo),
                        "from_retry": True,
                    }
            elif meta is not None:
                meta[pid]["retry_rejected"] = True
    if retried:
        results["_retried_rows"] = json.dumps(retried)  # marker, popped by caller
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True,
                    choices=["nemotron-3-nano-4b", "ministral-3-3b"])
    ap.add_argument("--type", default="g6e.4xlarge")
    ap.add_argument("--gpu-pin", default="L40S:1")
    ap.add_argument("--regions", default="us-east-2,us-west-2,us-east-1")
    ap.add_argument("--n-prompts", type=int, default=8)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    # Transport: streaming ON before any client machinery is touched -- see
    # module docstring. Own tag/state so a live study lane's box can never be
    # adopted; GPU pinned so a mismatched box never serves a single prompt.
    os.environ["EC2_STREAM_COMPLETIONS"] = "1"
    os.environ["EC2_EXPERIMENT_TAG"] = f"hinge-{args.model}"
    os.environ["EC2_STATE_FILE"] = str(REPO_ROOT / f".ec2_state_hinge_{args.model}.json")
    os.environ["EC2_REQUIRE_GPU"] = args.gpu_pin
    os.environ["EC2_INSTANCE_TYPES"] = args.type
    os.environ["EC2_REGIONS"] = args.regions

    hw = _load_hwprobe()
    from smolbench.evals import ec2

    prompts = hw.load_prompts(args.model, args.n_prompts)
    logging.info("hinge[%s]: %d prompts (same deterministic selection as the "
                 "archived baselines)", args.model, len(prompts))

    # 2026-08-18: EC2_DEPLOY_SPECS now ships DETERMINISM_ARGS (== DET_ARGS)
    # as a suffix on every spec and no longer carries --enable-prefix-caching
    # (post-study determinism default). Reconstruct both arms from the base
    # args so the stock/det CONTRAST this probe exists to measure survives:
    # stock re-adds the study-era --enable-prefix-caching; det appends
    # DET_ARGS exactly once. (The spec's --revision/--gpu-memory-utilization
    # pins ride both arms equally and do not affect the contrast.)
    spec_args = list(ec2.EC2_DEPLOY_SPECS[args.model].get("vllm_args", []))
    _det = getattr(ec2, "DETERMINISM_ARGS", DET_ARGS)
    if spec_args[-len(_det):] == _det:
        base_args = spec_args[:-len(_det)]
    else:  # pre-2026-08-18 spec shape: strip the study-era caching flag
        base_args = [a for a in spec_args if a != "--enable-prefix-caching"]
    orig_args = base_args + ["--enable-prefix-caching"]
    det_args = base_args + DET_ARGS
    configs = [("stock", orig_args), ("det", det_args)]

    report: Dict[str, Any] = {
        "model": args.model, "type": args.type, "n_prompts": args.n_prompts,
        "seed": hw.SEED, "temperature": hw.TEMPERATURE,
        "max_tokens": hw.MAX_TOKENS, "stream": True,
        "det_args": det_args, "configs": {},
    }
    passes: Dict[str, Dict[str, str]] = {}
    out_path = RESULTS_DIR / f"hinge_{args.model}.json"

    try:
        state = ec2.provision_spot_instance(
            instance_types=(args.type,), regions=tuple(args.regions.split(",")),
            idle_timeout_min=90,
        )
        logging.info("hinge[%s]: provisioned %s (%s @ %s)", args.model,
                     state["instance_id"], state["instance_type"],
                     state.get("availability_zone"))
        report["instance"] = {k: state.get(k) for k in
                              ("instance_id", "instance_type",
                               "availability_zone", "public_ip")}

        for cfg_name, vllm_args in configs:
            # In-process override ONLY -- the spec on disk is never edited.
            ec2.EC2_DEPLOY_SPECS[args.model]["vllm_args"] = vllm_args
            logging.info("hinge[%s]: serving config=%s vllm_args=%s",
                         args.model, cfg_name, vllm_args)
            t0 = time.time()
            try:
                with ec2.serve_model(args.model, force=True):
                    fp = fingerprint(state, args.model)
                    logging.info("hinge[%s:%s]: fingerprint %s", args.model,
                                 cfg_name, json.dumps(fp)[:400])
                    for i in (1, 2):
                        label = f"{cfg_name}:P{i}"
                        # D6.4: a fresh dict per pass -- guarded_pass mutates
                        # it in place with per-row finish_reason/token counts.
                        row_meta: Dict[str, Dict[str, Any]] = {}
                        res = guarded_pass(hw, args.model, prompts, label, meta=row_meta)
                        retr = res.pop("_retried_rows", None)
                        passes[label] = res
                        if retr:
                            report["configs"].setdefault(cfg_name, {})[
                                f"retried_rows_P{i}"] = json.loads(retr)
                        report["configs"].setdefault(cfg_name, {})[
                            f"row_meta_P{i}"] = row_meta
                    fp_after = fingerprint(state, args.model)
                    report["configs"].setdefault(cfg_name, {}).update(
                        vllm_args=vllm_args, fingerprint=fp,
                        cache_metrics_after=fp_after.get("cache_metric_lines"),
                        serve_plus_passes_s=round(time.time() - t0, 1),
                    )
            except Exception:
                # A rejected flag kills the container and serve_model raises on
                # its health wait; capture the serve log so the spelling can be
                # fixed without guessing, then let the failure surface.
                try:
                    import requests
                    st = requests.get(f"http://{state['public_ip']}:9000/status",
                                      timeout=10).json()
                    report["configs"].setdefault(cfg_name, {})["serve_log_tail"] = \
                        str(st.get("serve_log_tail"))[-3000:]
                except Exception:  # noqa: BLE001
                    pass
                report["configs"].setdefault(cfg_name, {})["FAILED"] = True
                out_path.write_text(json.dumps(report, indent=1))
                raise

        report["comparisons"] = {
            "stock_baseline (arm B/D)": hw.compare(passes["stock:P1"], passes["stock:P2"]),
            "det_baseline (arm A/C)": hw.compare(passes["det:P1"], passes["det:P2"]),
            "cross_config (stock:P1 vs det:P1)": hw.compare(passes["stock:P1"], passes["det:P1"]),
        }
        stock = report["comparisons"]["stock_baseline (arm B/D)"]["identical"]
        det = report["comparisons"]["det_baseline (arm A/C)"]["identical"]
        n = args.n_prompts
        print(f"\n=== hinge[{args.model}] ===")
        print(f"  stock baseline: {stock}/{n}   det baseline: {det}/{n}")
        if args.model == "nemotron-3-nano-4b":
            if stock == n and det == n:
                print("  ARM A: floor EXONERATED -- 8/8 without the cache; the "
                      "noise floor is a genuine kernel-determinism result.")
            elif stock == n and det < n:
                print("  ARM A: floor WAS CACHE REPLAY -- agreement drops "
                      "without prefix caching. Section 1.1's limit confirmed.")
            else:
                print("  ARM B FAILED TO REPLICATE the archived 8/8 -- "
                      "interpret nothing else until that is explained.")
        else:
            if det == n:
                print("  ARM C: ministral IS measurable -- the 'nothing can be "
                      "measured' verdict is config, not the model. Correct the "
                      "inventory.")
            elif det == 0:
                print("  ARM C: hypothesis REFUTED -- nondeterministic even at "
                      "concurrency 1, eager, no cache. The inventory line "
                      "stands (re-worded to 'under any configuration tested').")
            else:
                print(f"  ARM C: intermediate ({det}/{n}) -- per the plan, "
                      "extend to n=32 rather than interpret.")
        out_path.write_text(json.dumps(report, indent=1))
        print(f"report: {out_path}")
    finally:
        try:
            ec2.shutdown_instance()
        except Exception:
            logging.exception("TEARDOWN FAILED for hinge[%s] -- terminate by hand",
                              args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
