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
from typing import Any, Dict, List, Optional, Tuple

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


def run_pass(model: str, prompts: List[Tuple[str, str]], label: str,
            meta: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, str]:
    """Sends every prompt at the study's settings; returns {prompt_id: output}.

    Parameters
    ----------
    model : str
        Deploy-spec model id being served.
    prompts : list of (str, str)
        ``(prompt_id, prompt_text)`` pairs, in the order to send them.
    label : str
        Log-line prefix identifying this pass (e.g. ``"det@tp4:P1"``).
    meta : dict of str to dict, optional
        When given, populated IN PLACE with one entry per prompt id:
        ``{"finish_reason": ..., "completion_tokens": ..., "prompt_tokens":
        ..., "chars": ...}`` (see Notes). Omit (the default, ``None``) to skip
        metadata collection entirely -- the historical call shape.

    Returns
    -------
    dict of str to str
        ``{prompt_id: reasoning + "\\x00" + content}`` for every prompt, in
        the SAME layout every committed ``sha_table_P1``/``sha_table_P2`` and
        every ``cross_tp``/``_vs_head``/``_vs_run1`` comparison is recorded
        against. This return shape is unchanged regardless of whether `meta`
        is supplied.

    Raises
    ------
    RuntimeError
        If the server reports a non-positive context length -- the token
        budget for the comparison would otherwise be unknown.

    Notes
    -----
    Design: uses ``ec2.complete()`` rather than ``ec2.query()``.
    ``query()`` narrows the response to the ``(content, reasoning)`` 2-tuple
    and DISCARDS the token counters and finish reason; ``complete()`` is the
    identical call (same retry loop, same request shape) returning the full
    ``ChatResult``, which is what makes per-row metadata possible at all.
    That metadata is what distinguishes "the model stopped" (``finish_reason
    == "stop"``) from "the model exhausted its completion-token budget inside
    the reasoning channel" (``finish_reason == "length"`` with a large
    ``completion_tokens``) -- exactly the population the D6.1 empty-row bug
    was silently collapsing into "excluded (empty)".

    ``meta``, when given, is MUTATED (a new key per prompt id is inserted);
    nothing is ever read from it.
    """
    from smolbench.evals import ec2

    # `query`'s FOURTH POSITIONAL parameter is context_length, and it defaults
    # to 0 -- omitting it makes complete() reject every response as
    # "total_tokens > 0". Resolve it from the running server the same way
    # run_quiz does, rather than hardcoding the spec's max_model_len, so the
    # probe measures the box that actually landed.
    ctx_len: int = ec2._CLIENT.context_length(model)
    logging.info("%s: server reports context_length=%d", label, ctx_len)
    if ctx_len <= 0:
        raise RuntimeError(
            f"{label}: server reported context_length={ctx_len}; refusing to run a "
            "comparison whose token budget is unknown."
        )

    results: Dict[str, str] = {}
    for i, (pid, text) in enumerate(prompts, 1):
        # `ChatClient.complete` takes `context_length` KEYWORD-ONLY (unlike
        # `query`'s positional-or-keyword parameter of the same name) -- pass
        # it by keyword rather than positionally.
        rsp = ec2.complete(
            text, model, SEED,
            context_length=ctx_len,
            extra_args={"temperature": TEMPERATURE, "max_tokens": MAX_TOKENS},
            request_timeout=1800,
        )
        results[pid] = (rsp.reasoning or "") + "\x00" + (rsp.content or "")
        if meta is not None:
            meta[pid] = {
                "finish_reason": rsp.finish_reason,
                "completion_tokens": rsp.completion_tokens,
                "prompt_tokens": rsp.prompt_tokens,
                "chars": len(results[pid]),
            }
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


def mechanism_evidence(serve_log: Optional[Dict[str, Any]]) -> str:
    """Says whether a CONFIG claim (not a byte-comparison claim) has evidence.

    Design (D5.1): `capture_serve_log` is the sole producer of the evidence
    behind claims like "custom all-reduce was active/off", "enforce-eager was
    honored", or "prefix-caching was on". Before it was fixed, its `/status`
    call was unauthenticated and returned HTTP 401, so `engine_config_parsed`
    came back empty BY CONSTRUCTION -- not because the box was quiet -- and a
    tp=8 dense arm nonetheless banked a "custom all-reduce ACTIVE" claim in a
    commit title on exactly such an empty capture. This function is the single
    choke point every probe now routes a config claim through, so that defect
    cannot recur silently: a byte-comparison result (e.g. `within_process_
    baseline`) stays fully reportable regardless of this function's answer --
    only the MECHANISM claim is gated on it.

    Parameters
    ----------
    serve_log : dict or None
        The dict returned by `capture_serve_log` (or `None`/`{}` if the
        capture was never attempted). No other shape is inspected beyond
        ``serve_log["engine_config_parsed"]``.

    Returns
    -------
    str
        ``"engine_config"`` when `serve_log` is a mapping whose
        ``engine_config_parsed`` sub-dict is present AND non-empty (i.e. at
        least one config key -- `tensor_parallel_size`,
        `disable_custom_all_reduce`, `enforce_eager`, ... -- was actually
        parsed out of the vLLM startup banner). ``"UNMEASURED"`` in every
        other case: `serve_log` is `None`/`{}`, `engine_config_parsed` is
        absent, `engine_config_parsed` is present but empty (log text was
        captured but nothing matched the parser), or `serve_log` carries an
        `error` key from a failed capture.

    Notes
    -----
    Pure and side-effect-free; safe to call on an already-persisted report
    dict without re-fetching anything.
    """
    if not isinstance(serve_log, dict):
        return "UNMEASURED"
    parsed = serve_log.get("engine_config_parsed")
    if isinstance(parsed, dict) and parsed:
        return "engine_config"
    return "UNMEASURED"


#: Fixed control-stimulus prefix for the D8 per-arm sensitivity control (see
#: ``run_sensitivity_row``). A module-level constant -- no randomness, no
#: timestamp, no interpolation of any kind -- so the SAME perturbation is
#: applied on every arm, every run, every box. A control whose own stimulus
#: drifted between invocations could not support a claim about whether the
#: *server* changed behavior between two arms; it would only show that two
#: different random prefixes produced two different outputs, which is true of
#: any two distinct prompts and proves nothing about determinism.
SENSITIVITY_PREFIX = "[[SENSITIVITY-CONTROL-A7F3]]\n"


def evaluate_sensitivity(perturbed: str, base: str) -> Dict[str, Any]:
    """Decides whether a perturbed generation genuinely diverged from its base.

    Design (D8) -- why this must be PREFIX-aware and not a plain ``!=``: a
    naive ``perturbed != base`` test calls a row "SENSITIVE" merely because it
    stopped at a different length, which makes the whole control vacuous
    whenever the sensitivity row is generated under a smaller token cap than
    the passes it is meant to control for (``--sensitivity-max-tokens`` exists
    precisely so a budget-constrained arm can do this). A control that says
    SENSITIVE unconditionally is not a control -- it can never report BLIND,
    so it can never catch a model that is actually ignoring the perturbation.
    Sensitivity means the BYTES diverged before either row stopped, not that
    one generation happened to be shorter than the other.

    Parameters
    ----------
    perturbed : str
        The row produced from the perturbed prompt (``SENSITIVITY_PREFIX +``
        the base prompt text), serialized the same way as every comparison
        row: ``reasoning + "\\x00" + content``.
    base : str
        The corresponding UNPERTURBED row this arm already produced for the
        same prompt (e.g. its own P1 output), same serialization.

    Returns
    -------
    dict
        ``chars`` : int
            ``len(perturbed)``.
        ``base_chars`` : int
            ``len(base)``.
        ``sha12`` : str
            First 12 hex characters of ``sha256(perturbed)``.
        ``base_sha12`` : str
            First 12 hex characters of ``sha256(base)``.
        ``common_prefix_chars`` : int
            Length of the longest common prefix of ``perturbed`` and ``base``,
            computed unconditionally -- including when one side is empty
            (``<= 1`` char), in which case it is ``1`` exactly when the OTHER
            side also starts with the ``"\\x00"`` separator (an empty
            ``reasoning`` channel), else ``0``. This field is diagnostic and
            is NOT what `differs` is decided from in the empty-row cases --
            see Notes.
        ``comparable_chars`` : int
            ``min(chars, base_chars)``, computed unconditionally -- the span
            over which divergence COULD be observed if both rows were
            non-empty. When either row is empty this is ``<= 1`` (bounded by
            whichever side is empty), not necessarily ``0``.
        ``differs`` : bool
            ``True`` iff the perturbed row diverged from ``base`` within the
            comparable span. See Notes for the exact three-way rule.
        ``reason`` : str
            Short human-readable explanation of the verdict above.

    Notes
    -----
    The rule, exactly, in priority order:

    1. ``len(perturbed) <= 1`` -> ``differs = False``. An empty perturbed row
       is a delivery fault (the same transport signature ``hinge_probe``
       retries on), not evidence the model is insensitive to the
       perturbation -- it did not respond to ANYTHING, perturbed or not.
    2. ``len(base) <= 1`` -> ``differs = False``. There is nothing to compare
       the perturbation's effect against, so no verdict can be reached.
    3. Otherwise: ``m = min(len(perturbed), len(base))``,
       ``cp = len(os.path.commonprefix([perturbed, base]))``, and
       ``differs = cp < m``. Three sub-cases fall out of this:

       * ``cp < m`` -- the two rows disagree at byte ``cp``, strictly inside
         the span both rows actually cover. SENSITIVE, regardless of which
         row is longer.
       * ``cp == m`` and equal lengths -- byte-identical to ``base``. BLIND.
       * ``cp == m`` and unequal lengths -- the shorter row is a strict
         PREFIX of the longer one. This is truncation (a token-budget or
         stop-condition difference), not divergence. BLIND.

    Pure and side-effect-free.
    """
    chars = len(perturbed)
    base_chars = len(base)
    # Computed unconditionally -- including in the empty-row branches below,
    # where `differs` is decided WITHOUT consulting these two fields (an
    # empty row's length says nothing about sensitivity by itself). They are
    # NOT necessarily 0 here: `comparable_chars` is bounded by whichever side
    # is empty (<= 1, not 0), and `common_prefix_chars` is 1 whenever both
    # rows happen to share the "\x00" separator byte at position 0 (e.g. an
    # empty perturbed row against a base row whose reasoning channel is also
    # empty) -- a real, unremarkable case given every row is
    # `reasoning + "\x00" + content`. Kept in the return value regardless, as
    # diagnostic context, never as the basis for `differs` in these branches.
    comparable_chars = min(chars, base_chars)
    common_prefix_chars = len(os.path.commonprefix([perturbed, base]))
    sha12 = hashlib.sha256(perturbed.encode()).hexdigest()[:12]
    base_sha12 = hashlib.sha256(base.encode()).hexdigest()[:12]

    if chars <= 1:
        differs = False
        reason = ("perturbed row is <= 1 char (the delivery-fault signature): "
                  "not evidence of sensitivity, just a fault")
    elif base_chars <= 1:
        differs = False
        reason = "base row is <= 1 char: nothing to compare the perturbation against"
    else:
        differs = common_prefix_chars < comparable_chars
        if differs:
            reason = f"diverged at byte {common_prefix_chars}"
        elif chars == base_chars:
            reason = "byte-identical to base"
        else:
            reason = "a strict PREFIX of base: truncation, not divergence"

    return {
        "chars": chars, "base_chars": base_chars,
        "sha12": sha12, "base_sha12": base_sha12,
        "common_prefix_chars": common_prefix_chars,
        "comparable_chars": comparable_chars,
        "differs": bool(differs), "reason": reason,
    }


def control_status(sensitivity_row: Optional[Dict[str, Any]]) -> str:
    """Reads a sensitivity row's verdict off as a two-state control status.

    Parameters
    ----------
    sensitivity_row : dict or None
        The dict returned by ``run_sensitivity_row``/``evaluate_sensitivity``,
        or anything else that might end up in ``entry["sensitivity_row"]``:
        ``None`` (never run), ``{}``, or an ``{"error": ...}`` dict from a
        failed control call.

    Returns
    -------
    str
        ``"SENSITIVE"`` when `sensitivity_row` is a mapping and
        ``sensitivity_row["differs"]`` is truthy. ``"BLIND"`` in every other
        case -- missing row, empty dict, error dict, or a row whose own
        ``differs`` came back ``False``.

    Notes
    -----
    Design: absence of evidence defaults to BLIND, never to SENSITIVE. A
    control that could not be evaluated (a failed generation, a row that was
    simply never run) has not demonstrated anything, and treating "no data"
    as "the probe is working" would silently re-introduce the exact defect
    this control exists to close -- a HOLD banked without ever confirming the
    control that was supposed to gate it actually fired.

    Pure and side-effect-free.
    """
    if not isinstance(sensitivity_row, dict):
        return "BLIND"
    return "SENSITIVE" if sensitivity_row.get("differs") else "BLIND"


def sensitivity_key(model: str, instance_id: Any, arm: str) -> str:
    """Builds the report-level index key for a per-arm sensitivity control row.

    Parameters
    ----------
    model : str
        The model identifier the arm was run against (e.g.
        ``"nemotron-3-super-120b-a12b"``).
    instance_id : Any
        The EC2 instance id the arm ran on (e.g. ``"i-047406b"``). Accepted
        as ``Any`` and stringified unconditionally rather than typed ``str``,
        because the drivers pass ``state.get("instance_id")``, which can be
        ``None`` before provisioning finishes recording it -- the key must
        degrade to the literal substring ``"None"`` rather than raising.
    arm : str
        The arm identifier distinguishing this control row from every other
        arm run against the same model on the same box (e.g. ``"det"``,
        ``"stock"``, or MoE's ``"A"``/``"A2"``/``"B"``/``"C"``).

    Returns
    -------
    str
        ``f"{model}@{instance_id}@{arm}"``.

    Notes
    -----
    Design (D8 follow-up): the report-level index ``report["sensitivity_rows"]``
    was keyed ``f"{model}@{instance_id}"``, taken literally from the original
    spec's "keyed by (model, instance_id)". But every driver runs SEVERAL arms
    against the same model on the same box -- tp4/tp8 each run ``det`` and
    ``stock``; ``moe`` runs arms B and C on the dense model and A/A2 on the
    MoE model -- so each arm's control row overwrote the previous one under
    that two-part key, and the top-level index retained only the LAST arm's
    row. Per-arm ``entry["sensitivity_row"]`` was always written in full and
    independently of this index, so no verdict was ever computed from the
    wrong control; only the report-level AUDIT TRAIL lost the earlier arms'
    rows. Centralising the key-building logic in one helper, called from all
    three drivers, also prevents the three hand-rolled f-strings from
    drifting apart again -- which is how this defect arose in the first
    place: one file's key expression changed, or none did, with nothing to
    keep the copies in sync.

    Pure and side-effect-free.

    Examples
    --------
    >>> sensitivity_key("ministral-3-3b", "i-abc", "det")
    'ministral-3-3b@i-abc@det'
    >>> sensitivity_key("ministral-3-3b", "i-abc", "stock")
    'ministral-3-3b@i-abc@stock'
    >>> sensitivity_key("m", None, "stock")
    'm@None@stock'
    """
    return f"{model}@{instance_id}@{arm}"


def run_sensitivity_row(ec2, model: str, base_prompt_id: str, base_prompt_text: str,
                        base_output: str, *, seed: int = SEED,
                        temperature: float = TEMPERATURE, max_tokens: int = MAX_TOKENS,
                        request_timeout: int = 1800,
                        prefix: str = SENSITIVITY_PREFIX) -> Dict[str, Any]:
    """Generates and scores the D8 in-process sensitivity-control row.

    Design (D8) -- why every arm needs its OWN control: the verdict rule is
    "k/k byte-identical => the bundle HOLDS", and nothing tied a HOLD to a
    control that had actually fired -- the tp=8 dense HOLD was banked
    alongside a `stock` positive control that recorded ``n = 0``
    (``notebooks/deduction/results/tp8hinge_ministral-3-3b.json``, deadline-cut
    before its first prompt returned). A same-model stock control cannot fix
    this in general either: nemotron-3-nano-4b's own tp=1 `stock` arm was
    itself 8/8 byte-identical (prefix-cache replay -- 15,258 prefix-cache
    queries, 3,904 hits), so "stock must diverge" can never be satisfiable for
    that model. This function generates ONE extra row -- from a
    deterministically perturbed copy of the arm's own first prompt -- inside
    the SAME server process the arm's two comparison passes ran in, giving
    every arm an independent, self-contained proof that the probe is capable
    of detecting a difference at all.

    Parameters
    ----------
    ec2 : module
        The loaded ``smolbench.evals.ec2`` module, supplying ``complete()``
        and ``_CLIENT.context_length()``.
    model : str
        Deploy-spec model id currently being served.
    base_prompt_id : str
        The prompt id this control row is controlling for (normally the
        arm's first prompt, ``arm_prompts[0][0]``). Carried through into the
        returned dict as ``prompt_id`` purely for provenance -- not used in
        the comparison itself.
    base_prompt_text : str
        The UNPERTURBED prompt text for `base_prompt_id`. `prefix` is
        prepended to this text to form the actual request.
    base_output : str
        The arm's own unperturbed output for `base_prompt_id` (its P1 row,
        same ``reasoning + "\\x00" + content`` serialization), used as the
        comparison base for ``evaluate_sensitivity``.
    seed : int, optional
        Sampling seed. Defaults to the study's own `SEED` so the control runs
        under the arm's own sampling regime.
    temperature : float, optional
        Sampling temperature. Defaults to `TEMPERATURE`.
    max_tokens : int, optional
        Completion-token budget for the control row. Defaults to `MAX_TOKENS`
        (the study's own cap), but callers may lower it -- see the
        ``--sensitivity-max-tokens`` CLI flag on each driver -- to bound the
        control's added cost on slow arms; this is sound because
        `evaluate_sensitivity` is prefix-aware (a shorter row that still
        diverges before it hits the smaller cap is still SENSITIVE).
    request_timeout : int, optional
        Seconds to wait for the completion. Default ``1800``, matching every
        other pass in this module.
    prefix : str, optional
        The perturbation prepended to `base_prompt_text`. Defaults to
        `SENSITIVITY_PREFIX`. Exposed as a parameter (rather than hardcoded)
        purely for testability; production callers should not override it.

    Returns
    -------
    dict
        Everything `evaluate_sensitivity` returns (``chars``, ``base_chars``,
        ``sha12``, ``base_sha12``, ``common_prefix_chars``,
        ``comparable_chars``, ``differs``, ``reason``), merged with:

        ``prompt_id``
            `base_prompt_id`, unchanged.
        ``perturbation``
            The `prefix` actually used.
        ``max_tokens``
            The `max_tokens` actually used.
        ``finish_reason``
            The control generation's ``ChatResult.finish_reason``.
        ``completion_tokens``
            The control generation's ``ChatResult.completion_tokens``.

    Raises
    ------
    RuntimeError
        Propagated from ``ec2._CLIENT.context_length`` or ``ec2.complete`` on
        a request failure. Callers (the three drivers) catch this and record
        ``{"error": ...}`` instead -- a failed control is BLIND, not fatal to
        the arm.

    Notes
    -----
    Fully deterministic given identical inputs: no timestamp or elapsed-time
    field is recorded anywhere in the return value, so two calls with the
    same arguments against a model that itself samples deterministically
    return equal dicts. Design: uses ``ec2.complete()`` (never ``ec2.query()``)
    for the same reason ``run_pass`` does -- ``query()`` discards
    ``finish_reason``/``completion_tokens``, which this function needs to
    report alongside the byte verdict. ``context_length`` is KEYWORD-ONLY on
    ``ChatClient.complete`` (unlike ``query``'s positional-or-keyword
    parameter of the same name); it is passed by keyword here for that
    reason.
    """
    ctx_len: int = ec2._CLIENT.context_length(model)
    rsp = ec2.complete(
        prefix + base_prompt_text, model, seed,
        context_length=ctx_len,
        extra_args={"temperature": temperature, "max_tokens": max_tokens},
        request_timeout=request_timeout,
    )
    text = (rsp.reasoning or "") + "\x00" + (rsp.content or "")
    row = evaluate_sensitivity(text, base_output)
    row.update({
        "prompt_id": base_prompt_id,
        "perturbation": prefix,
        "max_tokens": max_tokens,
        "finish_reason": rsp.finish_reason,
        "completion_tokens": rsp.completion_tokens,
    })
    return row


def verdict_line(*, arm: str, identical: int, n: int, control_status: str,
                 model: str, instance_id: Any, stock_control: Optional[str] = None,
                 mechanism_evidence: Optional[str] = None) -> str:
    """The single constructor for every HOLD/UNMEASURED string a probe emits.

    Design (D8) -- this is the sole choke point a byte-comparison result must
    route through to become a verdict sentence, so that "k/k identical" can
    never again turn into a printed HOLD without the reader being told, in the
    same sentence, whether the control that was supposed to license that HOLD
    actually fired. Every driver's per-arm log line and end-of-run summary
    print this string rather than constructing their own.

    Parameters
    ----------
    arm : str
        Short arm label (e.g. ``"det"``, ``"stock"``, or a moe arm code like
        ``"A"``/``"A2"``/``"B"``/``"C"``).
    identical : int
        Rows byte-identical between the arm's two within-process passes
        (``within_process_baseline["identical"]``).
    n : int
        Rows compared, empty-both-sides rows already excluded
        (``within_process_baseline["n"]``).
    control_status : str
        ``control_status(entry["sensitivity_row"])``'s return value for this
        arm -- ``"SENSITIVE"`` or ``"BLIND"``.
    model : str
        Deploy-spec model id, named in the verdict so the control's scope
        (which model, which box) is legible from the string alone.
    instance_id : Any
        The EC2 instance id this arm ran on, named for the same reason.
    stock_control : str or None, optional
        ``f"{identical}/{n}"`` for the sibling stock positive control, if it
        has completed; ``None`` if the stock arm has not run (or this arm IS
        the only arm run standalone). An unrun stock control is named as
        ``"absent"`` in the string rather than silently omitted -- the tp=8
        stock control that recorded n=0 was the exact incident that motivated
        this function.
    mechanism_evidence : str or None, optional
        ``entry.get("mechanism_evidence")`` for this arm, i.e.
        ``hardware_equivalence_probe.mechanism_evidence(entry["serve_log"])``
        if it was computed. When this is the literal string ``"UNMEASURED"``,
        an additional clause is appended stating that no CONFIG claim (custom
        all-reduce state, enforce-eager, prefix-caching) may be made for this
        arm while the byte result stands -- the byte-comparison verdict
        itself is unaffected. Any other value (including ``None``, meaning
        the driver never computed it) appends nothing.

    Returns
    -------
    str
        Always contains ``f"{identical}/{n}"`` and always names the control's
        scope (``control_status``, `model`, `instance_id`, and the stock
        control string or ``"absent"``). The verdict word is chosen as
        follows, in priority order:

        1. ``control_status != "SENSITIVE"`` or ``n <= 0`` -> ``"UNMEASURED"``.
           A BLIND control means the probe has not demonstrated it can detect
           anything on this box; ``n <= 0`` means the arm compared no rows at
           all (the tp=8 stock-control incident: a k/k-shaped claim can never
           be reported from an empty denominator, never a vacuous "0/0
           HOLDS").
        2. ``identical == n`` -> ``"HOLDS"``.
        3. otherwise -> ``"DOES NOT HOLD"``.

        On the BLIND/UNMEASURED path the string never contains the substring
        ``"HOLD"`` at all (so a caller cannot mistake it for a hedged HOLD by
        substring-matching); on a clean SENSITIVE HOLD it never contains
        ``"UNMEASURED"``.

    Notes
    -----
    Pure and side-effect-free.
    """
    if control_status != "SENSITIVE" or n <= 0:
        verdict = "UNMEASURED"
    elif identical == n:
        verdict = "HOLDS"
    else:
        verdict = "DOES NOT HOLD"

    line = (
        f"{arm}: {identical}/{n} identical -- bundle {verdict} "
        f"(control: sensitivity {control_status} on {model}@{instance_id}; "
        f"stock control {stock_control or 'absent'})"
    )
    if mechanism_evidence == "UNMEASURED":
        line += (
            " [mechanism UNMEASURED: no config claim (custom all-reduce state, "
            "enforce-eager, prefix-caching) may be made for this arm while the "
            "byte result stands]"
        )
    return line


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
