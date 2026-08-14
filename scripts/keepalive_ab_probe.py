"""A/B gate for the TCP-keepalive fix: does keepalive rescue a long idle completion?

WHY THIS EXISTS
---------------
The 2026-08-14 ministral-3-14b reshard lost all seven boxes to the same
failure: vLLM finished generating (``num_requests_running 0``,
``generation_tokens_total`` frozen at 360,874) while the driver sat on four
ESTABLISHED sockets blocked in ``poll()``, and the box -- genuinely idle from
its own point of view -- was then reaped by the idle watchdog. The diagnosis
is that a non-streaming completion is SILENT on the wire for the whole
generation, and a ~43-minute silence is long enough for the NAT gateway on
this host's Wi-Fi egress path to drop the flow, so the response lands in a
dead mapping.

``smolbench.evals.openai_compat`` now mounts a Session that stamps
SO_KEEPALIVE + TCP_KEEPIDLE on every completion socket. That fix is a
hypothesis until measured: keepalive cannot help if the response was actually
lost server-side. This script settles it for the price of one box.

THE DESIGN, AND WHY IT IS SHAPED THIS WAY
-----------------------------------------
Four requests fire at the same instant against one box: two through the
keepalive Session, two through bare ``requests.post`` (which creates its own
Session per call and never sets SO_KEEPALIVE -- the pre-fix behavior). They
carry a byte-identical prompt and completion budget, so the ONLY difference
between the arms is the socket option.

What sets the idle duration is the PROMPT, not the concurrency. Decoding
attends over the whole context, so the extens arm's 61k-character prompts run
~34 tok/s while intens' 748-character prompts run ~52 tok/s. At an 88k-token
budget that is a ~43-minute idle versus a ~29.5-minute one -- and the run that
used intens prompts returned cleanly on BOTH arms, never reaching the regime
and proving nothing. Hence the extens default. ``--pairs`` remains available
to lengthen the idle further by contending for decode.

Two replicates per arm because a single hang could be coincidence.

Reading the result:
  * keepalive returns, plain hangs      -> fix proven, relaunch the reshard
  * both return, longest run >= floor   -> the failure did not reproduce; the
                                           network path may have changed
                                           again. Do NOT claim the fix works.
  * both return, longest run <  floor   -> PROBE INVALID: nothing idled long
                                           enough to test. Says nothing either
                                           way; lengthen and re-run.
  * both hang                           -> fault is server-side, keepalive was
                                           never the answer. Stop and rethink.

The box is torn down in a ``finally`` so a hang cannot leave it billing, and
it is provisioned with a raised idle timeout: at the default 30 minutes the
watchdog would reap the box mid-probe and manufacture a false "both hang".
"""

import argparse
import concurrent.futures
import logging
import os
import pathlib
import re
import sys
import time
from typing import Any, Dict, Tuple

# Repo-anchored so the script runs from any cwd (generated-files-stay-in-repo).
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

#: The probe's own tag/state file. MUST NOT collide with a study lane's state
#: file -- a shared state file would let this script's provision() reattach to
#: a live study box and swap the served model out from under it.
os.environ.setdefault("EC2_EXPERIMENT_TAG", "keepalive-probe")
os.environ.setdefault(
    "EC2_STATE_FILE", str(REPO_ROOT / ".ec2_state_keepalive_probe.json")
)
#: The failing generation takes ~43 min; the default 30-minute watchdog would
#: reap the box mid-probe. Set BEFORE importing ec2 (module-level constant).
os.environ.setdefault("EC2_IDLE_TIMEOUT_MIN", "90")

import requests  # noqa: E402

from smolbench.evals import ec2  # noqa: E402
from smolbench.evals.openai_compat import SESSION  # noqa: E402

MODEL = "ministral-3-14b"
#: Matches the study's derived completion budget for this lane (the driver
#: logged "worst prompt 34,676 tok (+8,000 reserve) -> completion budget
#: 88,396"), so the probe generates for as long as the real run did.
COMPLETION_BUDGET = 88_396
#: 100 min. Must exceed the HONEST generation time or a slow-but-healthy
#: keepalive arm gets cut off and misreported as a hang -- with the extens
#: prompt (61k chars of context) decode runs ~34 tok/s, so an 88k-token
#: completion takes ~45 min and the margin needs to absorb the spread.
#: Symmetric across both arms; an asymmetric timeout would bias the comparison.
READ_TIMEOUT_S = 6_000
CONNECT_TIMEOUT_S = 10
#: A probe run is only informative if SOMETHING ran long enough to create the
#: idle stretch under test. The boxes that failed were reaped after 30 minutes
#: idle, so a run whose longest request settled in well under that never
#: reached the regime -- 35 min sits just above the ~43-minute honest
#: generation's lower spread while staying clear of the fast-answer case.
MIN_VALID_ELAPSED_S = 2_100


def load_prompt(bucket: str, key: str, mark_index: int) -> str:
    """Pulls one real study prompt out of a completed result object in S3.

    Uses a genuine prompt rather than a synthetic one because the failure is
    length-dependent: this lane's marks generate to the cap and that is what
    creates the long silence. Streamed and discarded -- nothing persists
    locally (no run data accumulates on this host).
    """
    import boto3
    import yaml

    body = boto3.client("s3").get_object(Bucket=bucket, Key=key)["Body"].read()
    marks = yaml.safe_load(body)["marks"]
    return marks[mark_index]["query"]


def _body(prompt: str) -> Dict[str, Any]:
    """Builds the completion body the STUDY would send, not a minimal one.

    The provider system prompt is mandatory here, not cosmetic: Ministral's
    thinking mode is carried entirely by the deploy-spec ``system_prompt``
    (this family takes no ``chat_template_kwargs``), so omitting it serves the
    model non-reasoning. It then answers this "reply with a single integer"
    prompt in milliseconds -- no long generation, no long idle, and the probe
    measures nothing. The first run of this script did exactly that: four
    requests settled in 2 seconds. System message first, matching
    ChatClient's ordering.
    """
    messages = [{"role": "user", "content": prompt}]
    sys_prompt = ec2._system_prompt(MODEL)
    if sys_prompt:
        messages.insert(0, {"role": "system", "content": sys_prompt})
    return {
        "model": MODEL,
        "messages": messages,
        # Seeded like every other generation in this study; never dropped.
        "seed": 0,
        "max_completion_tokens": COMPLETION_BUDGET,
    }


def one_request(arm: str, index: int, url: str, token: str, prompt: str) -> Dict[str, Any]:
    """Issues one completion and reports how it ended, never raising.

    ``arm="keepalive"`` goes through the shared Session (SO_KEEPALIVE +
    TCP_KEEPIDLE); ``arm="plain"`` calls ``requests.post``, which builds a
    throwaway Session with default socket options -- i.e. exactly what the
    client did before the fix.
    """
    started = time.monotonic()
    poster = SESSION.post if arm == "keepalive" else requests.post
    try:
        response = poster(
            url=url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=_body(prompt),
            timeout=(CONNECT_TIMEOUT_S, READ_TIMEOUT_S),
        )
        elapsed = time.monotonic() - started
        content = ""
        if response.status_code == 200:
            choice = response.json()["choices"][0]["message"]
            content = (choice.get("content") or "") + (choice.get("reasoning_content") or "")
        outcome = "returned" if response.status_code == 200 else f"http_{response.status_code}"
        return {"arm": arm, "index": index, "outcome": outcome,
                "elapsed_s": round(elapsed, 1), "chars": len(content)}
    except Exception as exc:  # noqa: BLE001 -- every failure mode is a result
        elapsed = time.monotonic() - started
        return {"arm": arm, "index": index, "outcome": f"{type(exc).__name__}",
                "elapsed_s": round(elapsed, 1), "chars": 0, "error": str(exc)[:200]}


def verdict(results) -> str:
    """Turns the four outcomes into the decision the probe exists to make."""
    keepalive = [r for r in results if r["arm"] == "keepalive"]
    plain = [r for r in results if r["arm"] == "plain"]
    ka_ok = sum(r["outcome"] == "returned" for r in keepalive)
    pl_ok = sum(r["outcome"] == "returned" for r in plain)

    # A run that never generated for long never created the idle stretch the
    # hypothesis is about, so its outcome carries no information either way --
    # report that instead of a verdict. Checked BEFORE the success branches so
    # a fast all-returned run can't be misread as "keepalive works".
    longest = max((r["elapsed_s"] for r in results), default=0)
    if longest < MIN_VALID_ELAPSED_S:
        thought = max((r["chars"] for r in results), default=0)
        why = ("the model answered instead of thinking -- check the system prompt"
               if thought < 10_000 else
               f"generation was long ({thought:,} chars) but FAST: raise --pairs so "
               "more concurrent streams slow per-stream decode and lengthen the idle")
        return (f"PROBE INVALID: longest request settled in {longest / 60:.1f} min, under "
                f"the {MIN_VALID_ELAPSED_S / 60:.0f} min floor, so the idle stretch that "
                f"strands responses was never created -- {why}. This says nothing about "
                "keepalive either way.")
    if ka_ok and not pl_ok:
        return ("FIX PROVEN: keepalive returned and plain did not. Relaunch the "
                "reshard with the fix in place.")
    if ka_ok and pl_ok:
        return ("NOT REPRODUCED: both arms returned. The failure did not occur "
                "this run -- do NOT claim the fix works on this evidence.")
    if not ka_ok and not pl_ok:
        return ("FIX REFUTED: both arms hung. The fault is server-side, not the "
                "idle connection. Stop and rethink before spending further.")
    return ("ANOMALOUS: plain returned but keepalive did not. Treat as "
            "unexplained; do not relaunch on this evidence.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="smolbench-results-414266451290")
    parser.add_argument(
        "--prompt-key",
        default="induction/ministral-3-14b/seed=0/extens--20260814T044724Z.yaml",
        help="Completed result object to lift a real study prompt from. Defaults to "
             "the EXTENS arm: its prompts are 61k chars vs intens' 748, and decoding "
             "over that much context is what slowed the failing boxes to ~34 tok/s "
             "and produced the ~43-minute idle. An intens prompt runs ~52 tok/s and "
             "finishes in 29.5 min -- short of the regime, proving nothing.",
    )
    parser.add_argument(
        "--mark-index", type=int, default=0,
        help="Which mark's query to use (default 0).",
    )
    parser.add_argument("--types", default="g7.24xlarge")
    parser.add_argument("--regions", default="us-east-2")
    # Concurrency is the control knob for idle DURATION at a fixed token budget:
    # more streams -> slower per-stream decode -> longer silence on each socket.
    # 2 pairs produced only a 29.5-minute idle (three streams ran at ~52 tok/s),
    # short of the ~43 minutes the failing boxes saw, and the run proved nothing.
    parser.add_argument(
        "--pairs", type=int, default=2,
        help="Keepalive/plain request pairs to fire concurrently (default 4 = 8 requests).",
    )
    parser.add_argument(
        "--keep-box", action="store_true",
        help="Skip teardown (debugging only -- the box then bills until its watchdog fires).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    prompt = load_prompt(args.bucket, args.prompt_key, args.mark_index)
    logging.info("prompt loaded: %d chars from %s[%d]", len(prompt), args.prompt_key, args.mark_index)

    os.environ["EC2_INSTANCE_TYPES"] = args.types
    os.environ["EC2_REGIONS"] = args.regions

    try:
        state = ec2.provision_spot_instance(
            instance_types=tuple(args.types.split(",")),
            regions=tuple(args.regions.split(",")),
            idle_timeout_min=int(os.environ["EC2_IDLE_TIMEOUT_MIN"]),
        )
        logging.info("provisioned %s in %s", state["instance_id"], state["region"])

        with ec2.serve_model(MODEL):
            url, token = ec2._connection(MODEL)
            logging.info("serving at %s", url)
            # Interleaved so both arms start together: an arm fired second
            # would see a different queue depth and a different decode rate.
            plan: Tuple[Tuple[str, int], ...] = tuple(
                (arm, i) for i in range(args.pairs) for arm in ("keepalive", "plain")
            )
            logging.info("firing %d requests (%d pair(s))", len(plan), args.pairs)
            started = time.monotonic()
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(plan)) as pool:
                futures = [
                    pool.submit(one_request, arm, i, url, token, prompt)
                    for arm, i in plan
                ]
                results = [f.result() for f in futures]
            logging.info("all four settled after %.1f min", (time.monotonic() - started) / 60)
            # Logged HERE, before teardown, not only in the final print: the
            # teardown waiter can run for minutes (or fail outright), and a
            # probe whose whole purpose is one measurement must not be able to
            # lose that measurement behind a slow terminate.
            for r in results:
                logging.info(
                    "RESULT %s #%d: %s after %.1fs (%d chars)%s",
                    r["arm"], r["index"], r["outcome"], r["elapsed_s"], r["chars"],
                    f" -- {r.get('error', '')}" if r.get("error") else "",
                )
            logging.info("VERDICT: %s", verdict(results))
    finally:
        if args.keep_box:
            logging.warning("--keep-box set: instance left RUNNING and billing")
        else:
            try:
                ec2.shutdown_instance()
                logging.info("probe box terminated")
            except Exception:
                logging.exception("TEARDOWN FAILED -- terminate by hand, the box is billing")

    print("\n=== A/B RESULTS ===")
    for r in sorted(results, key=lambda r: (r["arm"], r["index"])):
        print(f"  {r['arm']:9s} #{r['index']}  {r['outcome']:22s} "
              f"{r['elapsed_s']:8.1f}s  {r['chars']:,} chars"
              + (f"  {r.get('error', '')}" if r.get("error") else ""))
    print("\n=== VERDICT ===")
    print(verdict(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
