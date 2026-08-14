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

Four concurrent -- not two -- because concurrency sets the per-stream
generation rate, and the rate sets the idle duration that the whole
hypothesis turns on. At 4-way the measured rate was ~34 tok/s, so an ~88k
budget idles the connection ~43 minutes: the exact condition that failed. Two
concurrent would run ~50 tok/s and finish near 29 minutes, possibly UNDER the
gateway's idle threshold, and a negative result would then prove nothing.

Two replicates per arm because a single hang could be coincidence.

Reading the result:
  * keepalive returns, plain hangs      -> fix proven, relaunch the reshard
  * both return                         -> the failure did not reproduce; the
                                           network path may have changed
                                           again. Do NOT claim the fix works.
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
#: 70 min: comfortably past the ~43-minute honest generation, so a request
#: that has not returned by then is hung rather than slow. Symmetric across
#: both arms -- an asymmetric timeout would bias the comparison.
READ_TIMEOUT_S = 4_200
CONNECT_TIMEOUT_S = 10


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
    return {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
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
        default="induction/ministral-3-14b/seed=0/intens--20260814T044724Z.yaml",
        help="Completed result object to lift a real study prompt from.",
    )
    parser.add_argument(
        "--mark-index", type=int, default=1,
        help="Which mark's query to use (default 1: produced 302,677 chars).",
    )
    parser.add_argument("--types", default="g7.24xlarge")
    parser.add_argument("--regions", default="us-east-2")
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
            logging.info("serving; firing 2 keepalive + 2 plain at %s", url)
            plan: Tuple[Tuple[str, int], ...] = (
                ("keepalive", 0), ("plain", 0), ("keepalive", 1), ("plain", 1),
            )
            started = time.monotonic()
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [
                    pool.submit(one_request, arm, i, url, token, prompt)
                    for arm, i in plan
                ]
                results = [f.result() for f in futures]
            logging.info("all four settled after %.1f min", (time.monotonic() - started) / 60)
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
