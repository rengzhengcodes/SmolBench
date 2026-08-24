"""A/B a live serving box: does a STREAMED long generation arrive when a
non-streamed one does not?

WHY THIS EXISTS
---------------
``scripts/delivery_probe.py`` measured the ministral-3-14b delivery fault
live on 2026-08-16, on ONE box with the original client stack:

    08:04:51Z  running=0 waiting=0 gen_tok=354,389 finished={'stop': 1,
               'length': 4} | client ESTAB=4 recvq=[0, 0, 0, 0]

Four cap-length responses finished on the server. 58 minutes later, the
client still held four ESTABLISHED sockets with EMPTY receive queues, and
all four eventually hit the 5400 s read timeout. The one short
(``stop``) response landed normally. So the tokens exist, and the body
never crosses the wire; the loss is selective by generation LENGTH.

That leaves two candidate mechanisms. They are confounded in the study
workload, because a cap-length completion is both SLOW and BIG:

  silence   a non-streaming completion sends nothing between the request
            and the finished body, so something on the path drops a
            ~32-minute-idle flow, and the response lands in a dead
            mapping;
  size      a ~350 KB body fails where a small one succeeds.

This probe does not try to separate these mechanisms; it tests the FIX
instead. It fires two requests, identical in every sampling parameter,
that differ only in ``stream``:

  A  stream=False   the study's current transport: one silent wait, one body
  B  stream=True    server-sent events: bytes flow continuously from token 1

``min_tokens`` forces both requests to run long, regardless of what the
model would naturally do, so this probe guarantees the silent window
instead of hoping for it. Both requests run CONCURRENTLY, so both see
the same box, the same load, and the same network conditions in the same
minutes.

If B arrives and A times out, streaming is the fix, and the mechanism is
the silence (or anything a continuous byte flow cures). If BOTH fail,
idleness is not the mechanism, and streaming is not the answer.

This script writes NO study data. It is a transport measurement against
a box that is already up.

USAGE
    scripts/streaming_ab_probe.py --state .ec2_state_induction-...json
    scripts/streaming_ab_probe.py --state <file> --min-tokens 40000
"""

import argparse
import json
import pathlib
import threading
import time
from typing import Any, Dict

import requests

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

#: The prompt text is irrelevant to a transport test; what matters is that
#: the generation runs long, which ``min_tokens`` guarantees. This prompt
#: is lifted from the study's own arm text, so the request shape (system
#: plus user, same template) matches what actually fails.
PROMPT = (
    "There is a counting game. Positions are counted starting from 1. "
    "At each position, words are written according to the following rules:\n"
    "Every 1 positions write gv.\nEvery 2 positions write ps.\n"
    "Every 3 positions write qo.\n\n"
    "Question: How many of the positions 1 through 2520 include 'ps'? "
    "Think through it carefully and at length before answering."
)


def _endpoint(state_path: pathlib.Path) -> Dict[str, str]:
    state = json.loads(state_path.read_text())
    return {
        "url": f"http://{state['public_ip']}:8000/v1/chat/completions",
        "key": state["vllm_api_key"],
        "model": state["serving"]["served_model_name"],
    }


def run_one(ep: Dict[str, str], stream: bool, max_tokens: int, min_tokens: int,
            timeout: int, out: Dict[str, Any]) -> None:
    """Issue one completion, and record WHEN bytes arrived, not just whether.

    ``first_byte_s`` is the discriminator between the two arms. For the
    streamed request, it should be a few seconds (the first SSE chunk).
    For the non-streamed request, it is the whole generation time, which
    is precisely the silent window under suspicion.

    Parameters
    ----------
    ep : dict
        Endpoint info from `_endpoint`: ``url``, ``key``, ``model``.
    stream : bool
        Whether to request server-sent-event streaming.
    max_tokens : int
        ``max_tokens`` to send in the completion body.
    min_tokens : int
        ``min_tokens`` to send in the completion body.
    timeout : int
        Read timeout in seconds.
    out : dict
        Result dict this function updates in place, so a caller running
        this function in a background thread can read the result after
        the thread joins. On success, this function sets ``ok=True`` and
        records ``first_byte_s``, ``bytes``, ``chunks``, and (for a
        non-streamed request) ``finish_reason`` and
        ``completion_tokens``. On failure, it sets ``ok=False`` and
        records ``error``. It always records ``elapsed_s``.
    """
    body = {
        "model": ep["model"],
        "messages": [{"role": "user", "content": PROMPT}],
        "seed": 0,
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "min_tokens": min_tokens,
        "stream": stream,
    }
    started = time.time()
    out.update({"stream": stream, "started": time.strftime("%H:%M:%SZ", time.gmtime())})
    try:
        resp = requests.post(
            ep["url"],
            headers={"Authorization": f"Bearer {ep['key']}", "Content-Type": "application/json"},
            json=body, timeout=(10, timeout), stream=stream,
        )
        resp.raise_for_status()
        if stream:
            n_bytes = 0
            n_chunks = 0
            first = None
            for chunk in resp.iter_content(chunk_size=None):
                if not chunk:
                    continue
                if first is None:
                    first = time.time() - started
                n_bytes += len(chunk)
                n_chunks += 1
            out.update(first_byte_s=first, bytes=n_bytes, chunks=n_chunks)
        else:
            raw = resp.content
            out.update(first_byte_s=time.time() - started, bytes=len(raw), chunks=1)
            payload = json.loads(raw)
            out["finish_reason"] = payload["choices"][0].get("finish_reason")
            out["completion_tokens"] = (payload.get("usage") or {}).get("completion_tokens")
        out["ok"] = True
    except Exception as exc:  # noqa: BLE001 -- a failure IS the result
        out.update(ok=False, error=f"{type(exc).__name__}: {exc}")
    out["elapsed_s"] = time.time() - started


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", required=True)
    ap.add_argument("--max-tokens", type=int, default=88396,
                    help="the study's own completion budget for this lane")
    ap.add_argument("--min-tokens", type=int, default=60000,
                    help="forces a long generation so the silent window is guaranteed")
    ap.add_argument("--timeout", type=int, default=5400,
                    help="read timeout, matching the study's --request-timeout")
    args = ap.parse_args()

    path = pathlib.Path(args.state)
    if not path.is_absolute():
        path = REPO_ROOT / path
    ep = _endpoint(path)

    results: Dict[str, Dict[str, Any]] = {"non_streamed": {}, "streamed": {}}
    threads = [
        threading.Thread(target=run_one, args=(ep, False, args.max_tokens,
                                               args.min_tokens, args.timeout,
                                               results["non_streamed"])),
        threading.Thread(target=run_one, args=(ep, True, args.max_tokens,
                                               args.min_tokens, args.timeout,
                                               results["streamed"])),
    ]
    print(f"{time.strftime('%H:%M:%SZ', time.gmtime())} A/B against {ep['url']} "
          f"(min_tokens={args.min_tokens}, max_tokens={args.max_tokens})", flush=True)
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for name, r in results.items():
        print(f"{name:14} {json.dumps(r, default=str)}", flush=True)

    a, b = results["non_streamed"], results["streamed"]
    if b.get("ok") and not a.get("ok"):
        print("VERDICT: streaming DELIVERS where non-streaming does not -- "
              "the fault is the silent socket, and streaming is the fix.", flush=True)
    elif a.get("ok") and b.get("ok"):
        print("VERDICT: BOTH delivered -- the fault did not reproduce in this "
              "window; do not conclude anything from it.", flush=True)
    elif not a.get("ok") and not b.get("ok"):
        print("VERDICT: BOTH failed -- idleness is not the mechanism and "
              "streaming is NOT the fix.", flush=True)
    else:
        print("VERDICT: non-streamed delivered but streamed did not -- "
              "unexpected; investigate before acting.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
