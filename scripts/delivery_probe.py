"""Watch a serving box for the DELIVERY fault: server finishes, client never hears.

WHY THIS EXISTS
---------------
On 2026-08-14 the ``ministral-3-14b`` induction lane stopped landing results
while its boxes were demonstrably still working. The signature, captured by
hand on a live box:

    vLLM      num_requests_running 0, generation_tokens_total FROZEN at
              360,874 (four requests had generated all the way to the cap),
              /v1/models answering in 49 ms
    client    four sockets still ESTABLISHED, threads parked in poll(), no
              response bodies, eventually a 5400 s read timeout

So the model produced the tokens and the response never crossed the wire.
The loss was perfectly length-correlated -- ``finished_reason=stop`` landed
13 of 13, ``finished_reason=length`` landed 0 of 28 -- which is what a
transport that drops a flow after N minutes of silence looks like: a
non-streaming completion sends NOTHING between the request and the finished
body, so only generations longer than that idle threshold are lost.

Diagnosing it after the fact is hopeless (the logs show only "Read timed
out"), so this samples both sides at once, continuously, while a run is in
flight:

  SERVER  vLLM's own counters -- requests running/waiting, generation tokens,
          and finished requests split by finish reason.
  CLIENT  this host's socket table, filtered to the box: how many connections
          to :8000 are ESTABLISHED, and how many bytes are sitting unread in
          their receive queues.

The DISCRIMINATOR is the pair (server finished, client sockets). If the
server's finished count climbs while the client keeps the same sockets open
with empty receive queues, the bodies are being lost in transit -- that is
the fault, live, with a timestamp. If the server's counters are frozen with
requests still running, the box itself is wedged, which is a different
problem with a different fix. Distinguishing those two by argument is what
failed last time; this measures them.

Reads only. It never touches the run, the box's serving process, or S3.

USAGE
    scripts/delivery_probe.py --state .ec2_state_induction-ministral-3-14b-s24of30.json
    scripts/delivery_probe.py --state <file> --interval 60 --once
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request
from typing import Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

#: vLLM metric names sampled every tick. Counters are cumulative since the
#: server started, so the interesting quantity is always the DELTA between
#: ticks -- a frozen counter is the whole point of the probe.
COUNTERS = (
    "vllm:num_requests_running",
    "vllm:num_requests_waiting",
    "vllm:generation_tokens_total",
    "vllm:prompt_tokens_total",
)
#: Finished-request counter, split by ``finished_reason`` (stop / length /
#: abort). The split matters: the 2026-08-14 loss hit ``length`` only.
FINISH_METRIC = "vllm:request_success_total"


def load_endpoint(state_path: pathlib.Path) -> Tuple[str, Optional[str]]:
    """Returns ``(ip, api_key)`` from an EC2 provider state file."""
    state = json.loads(state_path.read_text())
    ip = state.get("public_ip") or state.get("ip") or state.get("public_dns")
    if not ip:
        raise SystemExit(f"{state_path}: no public_ip/ip field; box not provisioned yet?")
    return ip, state.get("vllm_api_key")


def scrape_metrics(ip: str, api_key: Optional[str], timeout: float = 10.0) -> Dict[str, float]:
    """Scrapes vLLM's Prometheus endpoint into a flat {name: value} dict.

    Finish-reason labels are folded into the key (``...request_success_total
    [length]``) so a caller can print them without parsing labels again. A
    scrape failure returns an empty dict rather than raising: the probe must
    keep sampling across a transient blip, since a blip is itself a
    measurement.
    """
    req = urllib.request.Request(f"http://{ip}:8000/metrics")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001 -- an unreachable box IS the signal
        return {"_scrape_error": 1.0, "_scrape_error_msg": str(exc)}  # type: ignore[dict-item]

    out: Dict[str, float] = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        name, _, value = line.rpartition(" ")
        base = name.split("{", 1)[0]
        if base in COUNTERS:
            out[base] = out.get(base, 0.0) + float(value)
        elif base == FINISH_METRIC:
            reason = re.search(r'finished_reason="([^"]+)"', name)
            key = f"{FINISH_METRIC}[{reason.group(1) if reason else '?'}]"
            out[key] = out.get(key, 0.0) + float(value)
    return out


def client_sockets(ip: str) -> List[Tuple[str, int]]:
    """Returns ``[(state, recv_queue_bytes)]`` for this host's sockets to the box.

    A response body that never arrives leaves the socket ESTABLISHED with an
    EMPTY receive queue -- the client is not slow to read, there is simply
    nothing to read. That is the distinction this function exists to make
    visible, and it is why the receive queue is reported rather than just a
    connection count.
    """
    try:
        proc = subprocess.run(
            ["ss", "-tn", "state", "all", f"dst {ip}:8000"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:  # noqa: BLE001 -- ss absent is not fatal to the probe
        return []
    rows: List[Tuple[str, int]] = []
    for line in proc.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        # `ss -tn state all` prints: State Recv-Q Send-Q Local Peer
        # but for a filtered 'state all' query the State column is present
        # only sometimes; detect it by whether the first field is numeric.
        if parts[0].isdigit():
            rows.append(("ESTAB", int(parts[0])))
        else:
            rows.append((parts[0], int(parts[1]) if parts[1].isdigit() else 0))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", required=True,
                    help="EC2 provider state file (repo-root-relative or absolute)")
    ap.add_argument("--interval", type=float, default=60.0, help="seconds between samples")
    ap.add_argument("--once", action="store_true", help="sample once and exit")
    args = ap.parse_args()

    path = pathlib.Path(args.state)
    if not path.is_absolute():
        path = REPO_ROOT / path

    prev: Dict[str, float] = {}
    while True:
        if not path.exists():
            print(f"{time.strftime('%H:%M:%SZ', time.gmtime())} state file absent "
                  f"({path.name}) -- box not provisioned yet", flush=True)
            if args.once:
                return 1
            time.sleep(args.interval)
            continue

        ip, key = load_endpoint(path)
        m = scrape_metrics(ip, key)
        socks = client_sockets(ip)
        stamp = time.strftime("%H:%M:%SZ", time.gmtime())

        if "_scrape_error" in m:
            print(f"{stamp} {ip} SCRAPE FAILED: {m.get('_scrape_error_msg')} "
                  f"| client sockets={len(socks)}", flush=True)
        else:
            gen = m.get("vllm:generation_tokens_total", 0.0)
            d_gen = gen - prev.get("vllm:generation_tokens_total", gen)
            finished = {k: v for k, v in m.items() if k.startswith(FINISH_METRIC)}
            d_fin = {
                k: v - prev.get(k, v) for k, v in finished.items() if v - prev.get(k, v)
            }
            estab = [q for s, q in socks if s == "ESTAB"]
            print(
                f"{stamp} {ip} running={m.get('vllm:num_requests_running', 0):.0f} "
                f"waiting={m.get('vllm:num_requests_waiting', 0):.0f} "
                f"gen_tok={gen:,.0f} (+{d_gen:,.0f}) "
                f"finished={ {k.split('[')[1].rstrip(']'): int(v) for k, v in finished.items()} } "
                f"(+{ {k.split('[')[1].rstrip(']'): int(v) for k, v in d_fin.items()} }) "
                f"| client ESTAB={len(estab)} recvq={estab}",
                flush=True,
            )
            prev = m

        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
