"""Probe whether the determinism bundle survives the 8-GPU NVLink topology.

This is the tp=8 extension of the hinge probe. It exercises the
topology every MoE deploy spec in this study actually serves on.

Why
---
`notebooks/DETERMINISM_PLAN_2026-08-16.md` section 3 certified the bundle
(`--no-enable-prefix-caching --max-num-seqs 1 --enforce-eager --seed 0`) at
**tp=1** (single L40S). `scripts/tp4_hinge_probe.py` then certified it at
**tp=4** (g6e.12xlarge, 4x L40S over PCIe) on 2026-08-21: both
ministral-3-3b and nemotron-3-nano-4b came back 8/8 byte-identical within
one process. A stock@tp4 positive control scored 1/4, which proves the
probe still detects nondeterminism on a multi-GPU box.

That leaves the **nine tp=8 specs** uncertified: qwen3.5-397b-a17b,
qwen3.5-122b-a10b, nemotron-3-super-120b-a12b, k-exaone-236b-a23b,
glm-4.5-air, glm-4.7, deepseek-v3.1, deepseek-v4-flash, deepseek-v4-pro.
Two mechanisms are new at tp=8, and nothing measured so far exercises
them:

  1. **The custom all-reduce path.** vLLM selects a hand-written NVLink
     all-reduce kernel when peer-to-peer access is available across all
     ranks (p5-class boxes have NVSwitch). The g6e boxes of the
     tp=1/tp=4 arms are PCIe-only and fall back to NCCL. Different
     kernel, different reduction order, different chance of run-to-run
     drift.
  2. **MoE routing at 8-way TP.** Every tp=8 spec in this study is a
     mixture-of-experts model whose experts are TP-sharded (no spec
     sets `--enable-expert-parallel` -- do NOT add it here, it would be
     off-protocol). Expert-parallel-free MoE at tp=8 still adds a
     second reduction per layer.

Design (one 8-GPU p5-class box per invocation)
  tier 1  DENSE-AT-TP8   ministral-3-3b (32 heads -> gcd(32,8)=8) under the
                         bundle. This is THE VERDICT ARM. It runs
                         alongside a stock@tp8 positive control, so an
                         8/8 det arm cannot mean "the probe went blind
                         on this silicon".
  tier 2  MOE-AT-TP8     nemotron-3-super-120b-a12b (32 heads, ~240GB BF16,
                         the smallest tp=8 MoE spec) under the bundle.

The protocol is the hinge's own protocol, unchanged and shared with
tp=4: the same deterministically-selected real deduction prompts from
the model's own S3 run dir, the same seed/temperature/max_tokens, two
back-to-back passes within ONE server process, byte-compared.

Pre-committed rules (fixed before any data was seen; inherited from tp=4)
  * tp GATE. `ec2.derive_tp` computes gcd(num_attention_heads,
    gpu_count). ministral-3-3b and nemotron-3-super-120b-a12b both have
    32 heads, so tp=8 on an 8-GPU box. This probe ASSERTS that value
    from the recorded launch payload after every serve; a mismatch
    aborts the arm before it sends a single prompt. This gate exists to
    stop a tp=8 certification from resting on a tp=4 measurement.
  * EMPTY ROWS ARE EXCLUDED ONLY WHEN BOTH PASSES ARE EMPTY (D8.3
    correction; see `guarded_compare` below). A row where exactly ONE
    pass came back empty and the other did not is DIVERGENT. It stays IN
    the identity denominator, and this probe names it under
    `one_sided_empty_rows`. Only a row where BOTH passes are still
    <= 1 chars after the retry counts as a true non-event; this probe
    excludes that row and names it under `excluded_empty_rows`. The
    retry trigger itself -- re-ask once on a length <= 1 delivery --
    stays unchanged.
  * ARM-LEVEL CHECKPOINTS. A spot reclaim between P1 and P2 kills the
    server process. A P2 resumed against a new process would silently
    turn a within-process test into a cross-process one (measured
    cross-process flip rate 9.5%, plan section 6.2). Completed arms
    persist; an interrupted arm re-runs from P1.

What this probe adds over tp4_hinge_probe.py
  * The serve log is captured UNCONDITIONALLY (tp=4 grabbed it only on
    failure). This probe greps the log for all-reduce / NVLink / P2P /
    MoE lines, so "the custom all-reduce path was exercised" is a
    recorded fact, not an inference from the instance type.
  * A SHA-level tp=4-vs-tp=8 cross comparison. The tp=4 JSONs store
    `sha_table_P1/P2` for all rows, so this comparison is now free and
    exact; the tp=4 report could only compare lengths against tp=1.
    SCOPE: GPU model confounds that comparison -- tp=4 ran on L40S,
    tp=8 runs on H100/H200. A disagreement means "different config,
    different bytes", consistent with the existing cross-config pooling
    guard. It is NOT evidence about tensor-parallel degree in
    isolation.

Usage
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
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path("/workspace/SmolBench")
#: Explicit, NOT __file__.parent. The tp=4/tp=1 hinge JSONs live here, and
#: the cross-tp comparison reads them from here.
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
    """Build a sha256 + length table for every row, including identical ones.

    Parameters
    ----------
    passes : dict of str to str
        Prompt id -> row text for one pass.

    Returns
    -------
    dict of str to dict
        Prompt id -> ``{"sha256_12": <12-char hex>, "len": <int>}``.
    """
    return {p: {"sha256_12": hashlib.sha256(t.encode()).hexdigest()[:12], "len": len(t)}
            for p, t in sorted(passes.items())}


def guarded_compare(hw, a: Dict[str, str], b: Dict[str, str]) -> Dict[str, Any]:
    """Run hw.compare() with the pre-committed empty-row exclusion applied.

    A row is "empty" (length <= 1) because the stored text is
    ``reasoning + "\\x00" + content``. A row with neither channel
    populated is exactly the one separator byte. This function excludes
    a row from the identity denominator ONLY when BOTH passes are
    empty -- that is the sole case where "nothing was measured" is a
    true description. A row where exactly ONE side is empty is not
    unmeasured. It is the single most DIVERGENT outcome the probe can
    observe: one pass produced real text, the other produced none. That
    row MUST stay in the denominator, entering ``n``/``diffs`` through
    ``hw.compare`` like any other disagreement. This function also
    surfaces it in ``one_sided_empty_rows``, so it can be inspected
    without re-deriving it from the diff list.

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
    Design: the rule used to be "exclude when EITHER side is empty"
    (``or`` instead of the both-sides ``and`` below). The incident that
    forced this fix: in the moe run-2 stock control, prompt
    ``CategoryTheory.Limits.Types.Pushout.condition/prompts/hint-2.md``
    had P1 = 83,661 characters (sha ``1e6e5acf9886``) and P2 = 1
    character. That P2 was NOT a non-event. It was a 106,545-character
    reasoning-only cap-hit that the client was, at the time, discarding
    on delivery -- a separate, since-fixed defect. One pass produced
    83k characters and the other produced nothing: the most divergent
    outcome available. The old rule scored it "excluded (empty)",
    turning a 0/4 control into a reported 0/3. The both-empty rule
    closes that hole. A one-sided empty row can never count as
    agreement (see
    ``test_guarded_compare_one_sided_row_can_never_be_identical``), so
    admitting it to the denominator can only ever lower the measured
    rate.

    ``moe_tp8_probe.py`` imports and reuses THIS copy
    (``tp8.guarded_compare``) rather than defining its own, so it
    inherits the fix automatically. This copy stays textually identical
    to ``tp4_hinge_probe.py``'s copy, so a fix to one can never silently
    diverge from the other.
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


def tp_gate(serve_log: Optional[Dict[str, Any]], expect_tp: int,
            payload_tp: Any) -> Dict[str, Any]:
    """Certify the SERVED tensor-parallel degree from the CONTAINER's own log.

    Design (D5.3): `tp4_hinge_probe.py`'s original gate asserted
    ``state["last_serve"]["tp"]`` -- the value the driver ITSELF computed
    (via ``ec2.derive_tp``) and POSTed to the control agent when it
    asked for the serve. That readback can only ever confirm the driver
    agrees with itself. It cannot detect a container that actually came
    up serving a different tp than the one requested: a bad
    `--tensor-parallel-size` flag, a vLLM fallback, or a stale image.
    A tp=4 certification from a container that is in fact running at
    tp=1 is the exact failure this function exists to prevent. The gate
    now reads vLLM's own startup banner instead: the
    ``tensor_parallel_size`` value vLLM itself printed, which
    `capture_serve_log` parses into ``engine_config_parsed``. It treats
    the launch payload as a secondary, corroborating record rather than
    the source of truth.

    Parameters
    ----------
    serve_log : dict or None
        The dict returned by ``capture_serve_log``. Must be a mapping whose
        ``engine_config_parsed`` sub-dict is present, non-empty, and carries
        a parseable ``tensor_parallel_size`` entry -- anything less and the
        gate refuses to certify rather than falling back to `payload_tp`.
    expect_tp : int
        The tensor-parallel degree this arm is claiming to measure (e.g. 4
        or 8).
    payload_tp : Any
        The tp value the driver itself recorded from the launch payload
        (e.g. ``state["last_serve"]["tp"]``). Pass ``None`` to skip the
        cross-check entirely; any other value is compared against the
        container's tp and must agree.

    Returns
    -------
    dict
        ``{"gate_basis": "engine_config", "engine_tp": int, "payload_tp":
        payload_tp, "payload_agrees": True}`` on success only -- there is
        no partial-success return. ``gate_basis`` is
        ``"engine_config"`` on every arm that reaches this return. The
        value ``"payload_readback"`` is deliberately UNREACHABLE from
        this function; it exists only to label pre-2026-08-23 reports,
        whose gate read the driver's own ``derive_tp`` output rather
        than the container.

    Raises
    ------
    RuntimeError
        `serve_log` is not a non-empty mapping, ``engine_config_parsed``
        is missing or empty, or ``tensor_parallel_size`` is absent or
        not parseable as `int`. This function NEVER falls back to
        `payload_tp` in any of these cases -- doing so would restore
        exactly the blindness this function removes, while leaving a
        `gate_basis` field that falsely claims the container was
        checked.
    RuntimeError
        The container's parsed ``tensor_parallel_size`` does not equal
        `expect_tp` (the message names both numbers). The arm must
        abort before it sends a single prompt.
    RuntimeError
        `payload_tp` is not `None` and disagrees with the container's tp
        (the message names both numbers). Two records of the same fact
        that disagree must never be banked as if they agreed -- this
        function banks neither.
    """
    if not isinstance(serve_log, dict):
        raise RuntimeError(
            "tp GATE FAILED: no serve log captured (got "
            f"{serve_log!r}); refusing to certify tp={expect_tp} without "
            "reading the container's own engine-config line.")
    parsed = serve_log.get("engine_config_parsed")
    if not isinstance(parsed, dict) or not parsed:
        raise RuntimeError(
            "tp GATE FAILED: serve log has no parsed engine_config "
            f"(engine_config_parsed={parsed!r}); refusing to certify "
            f"tp={expect_tp} from an unparseable or absent capture -- this "
            "must never silently fall back to the launch payload.")
    raw = parsed.get("tensor_parallel_size")
    if raw is None:
        raise RuntimeError(
            "tp GATE FAILED: engine_config_parsed has no "
            f"tensor_parallel_size key ({parsed!r}); refusing to certify "
            f"tp={expect_tp} -- this must never silently fall back to the "
            "launch payload.")
    try:
        engine_tp = int(raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"tp GATE FAILED: tensor_parallel_size={raw!r} is not an "
            f"integer ({type(exc).__name__}: {exc}); refusing to certify "
            f"tp={expect_tp} -- this must never silently fall back to the "
            "launch payload.") from exc
    if engine_tp != expect_tp:
        raise RuntimeError(
            f"tp GATE FAILED: container engine-config reports "
            f"tensor_parallel_size={engine_tp}, expected {expect_tp}. "
            "Refusing to measure -- a mismatched tp must never be reported "
            "as the expected one.")
    if payload_tp is not None and payload_tp != engine_tp:
        raise RuntimeError(
            f"tp GATE FAILED: container engine-config reports "
            f"tensor_parallel_size={engine_tp} but the launch payload "
            f"recorded tp={payload_tp!r}; two records of the same fact "
            "disagree -- refusing to bank either.")
    return {"gate_basis": "engine_config", "engine_tp": engine_tp,
            "payload_tp": payload_tp, "payload_agrees": True}


def resilient_pass(hw, ec2, model: str, prompts, label: str, entry: Dict[str, Any],
                   key: str, gz_path: pathlib.Path, stop_at_min: float,
                   t_start: float, save) -> Dict[str, str]:
    """Run one probe pass, persisted ROW BY ROW and stoppable at a wall deadline.

    The request shape matches ``hardware_equivalence_probe.run_pass``, and
    this function uses the same length<=1 delivery-fault retry as
    ``hinge_probe.guarded_pass`` -- the measurement itself is unchanged.
    What this function adds is failure containment, which the tp=4 probe
    lacked and which matters far more at $20/h on an 8-GPU box:

      * Every completed row writes to the report and the gz archive
        immediately, so a spot reclaim or a lifetime fuse firing mid-pass
        costs only the remaining rows, not the whole arm.
      * No NEW prompt is issued after ``stop_at_min`` minutes from
        process start, so the pass lands instead of being severed.
      * A per-row exception is recorded, and the pass continues.

    P2 then runs over exactly the prompt ids P1 completed, so the byte
    comparison always has a matched denominator. A truncated arm reports
    k/k over a smaller k, never a spurious divergence.

    Design (D6.3b): every ask uses ``ec2.complete()`` rather than
    ``ec2.query()``, for the same reason as
    ``hardware_equivalence_probe.run_pass`` and
    ``hinge_probe.guarded_pass``: ``query()`` discards the finish reason
    and token counters that distinguish a finished generation from a
    reasoning-channel cap-hit. This function accumulates the per-row
    metadata into ``entry[f"row_meta_{key}"]``, next to
    ``entry[f"sha_table_{key}"]``, so the SAME ``save()`` calls persist
    it and it survives a truncated pass exactly as the sha table does.
    Retry semantics mirror ``hinge_probe.guarded_pass``: an accepted
    retry overwrites the row's metadata and marks
    ``"from_retry": True``; a rejected one marks
    ``"retry_rejected": True`` on the original (first-attempt) metadata.
    """
    ctx_len = ec2._CLIENT.context_length(model)
    logging.info("%s: server reports context_length=%d", label, ctx_len)
    if ctx_len <= 0:
        raise RuntimeError(f"{label}: context_length={ctx_len}; token budget unknown.")

    results: Dict[str, str] = {}
    row_meta: Dict[str, Dict[str, Any]] = {}

    def _ask(text: str) -> Tuple[str, Dict[str, Any]]:
        """Send one request; return (row text, this attempt's metadata)."""
        # `ChatClient.complete` takes `context_length` KEYWORD-ONLY,
        # unlike `query`'s positional-or-keyword parameter of the same
        # name -- pass it by keyword, not positionally.
        rsp = ec2.complete(
            text, model, hw.SEED,
            context_length=ctx_len,
            extra_args={"temperature": hw.TEMPERATURE, "max_tokens": hw.MAX_TOKENS},
            request_timeout=1800)
        row = (rsp.reasoning or "") + "\x00" + (rsp.content or "")
        return row, {
            "finish_reason": rsp.finish_reason,
            "completion_tokens": rsp.completion_tokens,
            "prompt_tokens": rsp.prompt_tokens,
            "chars": len(row),
        }

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
            txt, txt_meta = _ask(text)
            if len(txt) <= 1:
                logging.warning("%s: row %s length %d -- delivery-fault signature; "
                                "re-asking once", label, pid, len(txt))
                redo, redo_meta = _ask(text)
                entry.setdefault(f"retried_rows_{key}", {})[pid] = {
                    "original_len": len(txt), "retry_len": len(redo)}
                if len(redo) > 1:
                    txt = redo
                    redo_meta["from_retry"] = True
                    txt_meta = redo_meta
                else:
                    txt_meta["retry_rejected"] = True
            results[pid] = txt
            row_meta[pid] = txt_meta
        except Exception as exc:  # noqa: BLE001 -- one bad row must not kill the arm
            entry.setdefault(f"{key}_errors", {})[pid] = f"{type(exc).__name__}: {exc}"
            logging.exception("%s: row %s FAILED", label, pid)
            save()
            continue
        logging.info("%s: %d/%d %s -> %d chars", label, i, len(prompts), pid[:48],
                     len(results[pid]))
        entry[f"sha_table_{key}"] = sha_table(results)
        entry[f"row_meta_{key}"] = row_meta
        with gzip.open(gz_path, "wt") as fh:
            json.dump(results, fh)
        save()
    return results


def capture_serve_log(state: Dict[str, Any]) -> Dict[str, Any]:
    """Capture the vLLM container log unconditionally, with auth, and grep it.

    This function fixes three faults in the tp=4 probe's version, all
    found live on 2026-08-21 against the running tp=8 box:

    1. The tp=4 version sent no ``Authorization`` header, and the
       control agent's ``/status`` is token-gated. Every such call
       returned HTTP 401 ``{"error": "bad token"}``. The tp=4 report's
       serve-log fields were therefore empty by construction, not
       because the box was quiet. (``hinge_probe.fingerprint`` makes
       the same unauthenticated ``/status`` call, which is why its
       ``image_digest_lines`` are empty in the archived reports.)
    2. The tp=4 version read ``serve_log_tail``, which is the
       *launcher script's* stdout (``aws s3 sync`` + ``docker run
       -d``). vLLM's own startup banner lives in ``log_tail``
       (``docker logs --tail 300 vllm``) instead. The all-reduce and
       tensor-parallel facts appear only in the latter.
    3. The tp=4 version called this capture only from the ``except``
       branch, so a SUCCESSFUL arm recorded nothing about which
       collective implementation vLLM chose.
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
    """Compare this tp=8 P1's exact SHA against the archived tp=4 det P1.

    Caveat -- serialization boundary (D5.5b): as of 2026-08-23, the
    client RETAINS reasoning text on a null-content cap-hit, where it
    previously DISCARDED that text on delivery. For the cap-hit
    population, a row recorded after this fix is therefore not
    SHA-comparable to the archived tp=4 row recorded before it. A
    mismatch may reflect that serialization change rather than a
    tensor-parallel-degree fact. This caveat is independent of, and in
    addition to, the GPU-model confound this function's own
    ``confound_note`` already documents. Check the row's
    ``finish_reason``/``completion_tokens`` on both sides before you
    read a mismatch as evidence about tp in isolation.
    """
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


def _stock_control_str(report: Dict[str, Any]) -> Optional[str]:
    """Build ``"identical/n"`` for the sibling `stock` positive control, or `None`.

    Design (D8): `hardware_equivalence_probe.verdict_line`'s
    `stock_control` parameter wants a short summary of the STOCK arm's
    own within-process byte comparison, so a HOLD verdict names the
    positive control it was banked alongside. That is the exact
    provenance that was missing when the tp=8 dense HOLD was reported
    next to a `stock` control that had collected zero rows. This
    function is factored out here, rather than inlined at the `det` and
    `stock` arm call sites, so the two cannot independently drift. It
    stays textually identical to `tp4_hinge_probe.py`'s copy, for the
    same reason `guarded_compare` does: to keep the two in sync.

    Parameters
    ----------
    report : dict
        The in-progress report dict; read from ``report["arms"]["stock"]``.

    Returns
    -------
    str or None
        ``f"{identical}/{n}"`` when the `stock` arm's own
        ``within_process_baseline`` has already been recorded in
        `report`; else `None`, meaning the stock arm has not run yet,
        is still in progress, or failed before producing a comparison.
        `None` is the literal signal `verdict_line` renders as
        ``"absent"``.

    Notes
    -----
    This function is pure and has no side effect: it reads `report` and
    mutates nothing.
    """
    c = (report.get("arms", {}).get("stock", {}) or {}).get("within_process_baseline")
    if not c:
        return None
    return f"{c['identical']}/{c['n']}"


def main() -> int:
    # Design (D8.2): load this before the argparse parser is built, so
    # --sensitivity-max-tokens can default to hw.MAX_TOKENS directly
    # instead of duplicating its literal value here. A duplicated value
    # would silently drift if the study's own token budget ever changed.
    # This early load is safe: neither this module nor
    # `smolbench.evals.ec2` reads any environment variable at import
    # time -- only inside functions, after the driver sets the env vars
    # below.
    hw = _load_hwprobe()

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
                    help="Wall-clock budget from process start. No NEW arm starts "
                         "after it.")
    ap.add_argument("--arm-start-latest-min", type=float, default=95.0,
                    help="No arm after the first may START later than this many "
                         "minutes in.")
    ap.add_argument("--pass-deadline-min", type=float, default=1e9,
                    help="No NEW prompt is issued after this many minutes from "
                         "process start. The pass lands on the rows already done.")
    ap.add_argument("--p2-grace-min", type=float, default=25.0,
                    help="Extra minutes P2 gets over --pass-deadline-min, so a P1 "
                         "that ran to the deadline still gets its matching second "
                         "pass.")
    ap.add_argument("--sensitivity-max-tokens", type=int, default=hw.MAX_TOKENS,
                    help="max_tokens for the D8 in-process sensitivity-control row: "
                         "one extra generation per arm from a deterministically "
                         "perturbed copy of the arm's first prompt. Defaults to the "
                         "study's own max_tokens, so the default changes no "
                         "protocol. Lowering it is sound: evaluate_sensitivity() is "
                         "prefix-aware, so a control row that diverges before it "
                         "hits a smaller cap still scores SENSITIVE, not merely "
                         "truncated. A smaller cap also bounds the control's added "
                         "cost on slow arms.")
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
    # Fuse: the calling shell is expected to export a tighter value per box.
    os.environ.setdefault("EC2_MAX_LIFETIME_MIN", "150")

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
                    # Design (D5.1 follow-up): the config-claim gate is
                    # ARM-AGNOSTIC by nature. It exists to stop ANY claim
                    # about engine configuration -- custom all-reduce
                    # state, enforce-eager, prefix-caching -- from
                    # resting on an empty serve-log capture, regardless
                    # of which driver produced the capture. Even so, it
                    # was wired into tp4_hinge_probe.py and
                    # moe_tp8_probe.py only, because the directive that
                    # introduced it named those two files by name. That
                    # left tp8 -- THE arm of the motivating incident --
                    # ungated: a tp=8 dense arm banked a "custom
                    # all-reduce ACTIVE" claim in a commit title, on a
                    # capture that was empty by construction. (The
                    # pre-fix `/status` call was unauthenticated and
                    # returned HTTP 401, so the field was empty because
                    # auth failed, not because the box was quiet.)
                    # `entry.get("mechanism_evidence")` was already
                    # threaded into the verdict_line call below, so it
                    # silently evaluated to None -- which verdict_line
                    # correctly reads as "append no caveat". The gate
                    # was inert here specifically, not broken in
                    # general.
                    entry["mechanism_evidence"] = hw.mechanism_evidence(entry["serve_log"])
                    if entry["mechanism_evidence"] == "UNMEASURED":
                        logging.warning(
                            "tp8hinge[%s]: mechanism_evidence=UNMEASURED -- no "
                            "config claim (custom all-reduce state, "
                            "enforce-eager, prefix-caching) may be made for "
                            "this arm; the byte-comparison result below "
                            "remains fully reportable regardless.", arm)
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
                    # P2 covers exactly what P1 completed: a matched denominator.
                    p2_prompts = [(pid, txt) for pid, txt in arm_prompts if pid in p1]
                    # Design (D5.4): this code assigns the reported
                    # comparison count AFTER p2 returns, not from
                    # len(p2_prompts) here. resilient_pass can stop
                    # early on its own wall-clock deadline
                    # (--pass-deadline-min / --p2-grace-min), so "what
                    # P2 was ASKED to cover" can overstate "what it
                    # actually delivered". Every "k/k identical" verdict
                    # is quoted against this number, so it must reflect
                    # rows both passes actually completed, not a
                    # pre-pass guess.
                    p2 = resilient_pass(
                        hw, ec2, args.model, p2_prompts,
                        f"{arm}@tp{args.expect_tp}:P2", entry, "P2",
                        OUT_DIR / f"texts_tp8_{args.model}_{arm}_P2.json.gz",
                        args.pass_deadline_min + args.p2_grace_min, t_start, save)
                    passes["P2"] = p2
                    entry["n_prompts_compared"] = len(set(p1) & set(p2))
                    entry["pass_done_P2_min"] = round((time.time() - t_start) / 60.0, 1)
                    entry["fingerprint_after"] = hinge.fingerprint(state, args.model)
                    entry["serve_log_after"] = capture_serve_log(state)

                    # D8: the arm's own in-process control, which runs
                    # AFTER P2 so it can never perturb prefix-cache
                    # state between the two passes being compared. See
                    # scripts/moe_tp8_probe.py's D8 design note for why
                    # a HOLD must be tied to a control that actually
                    # fired, and why a same-model `stock` control cannot
                    # serve as a universal substitute. The incident that
                    # note documents is about this very file: this
                    # driver is the one that writes
                    # notebooks/deduction/results/tp8hinge_ministral-3-3b.json.
                    try:
                        _spid, _sptext = arm_prompts[0]
                        entry["sensitivity_row"] = hw.run_sensitivity_row(
                            ec2, args.model, _spid, _sptext, p1.get(_spid, ""),
                            max_tokens=args.sensitivity_max_tokens)
                    except Exception as exc:  # noqa: BLE001 -- a failed control is BLIND, not fatal
                        entry["sensitivity_row"] = {"error": f"{type(exc).__name__}: {exc}"}
                        logging.exception("tp8hinge[%s]: sensitivity control FAILED", arm)
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
                    logging.info("tp8hinge[%s]: %s (excluded empty: %s)",
                                 arm, entry["verdict_line"], c["excluded_empty_rows"])
                    if arm == "det":
                        entry["cross_tp_vs_tp4_det_P1"] = cross_tp(
                            args.model, entry["sha_table_P1"])
                    entry["serve_plus_passes_s"] = round(time.time() - t0, 1)
                    entry["complete"] = True
                    save()
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
