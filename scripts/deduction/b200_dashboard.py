"""Read-only progress dashboard for the packed B200 run (packed_box.py).

Serves an auto-refreshing page at http://127.0.0.1:8765. A background thread
polls the box every ``--interval`` seconds with one SSH call (a Python script
on stdin that only reads files, ``/proc`` and ``nvidia-smi``) and lists and
copies ``verified_rows.jsonl`` from S3 into a local temp dir. It never writes
to the box or to S3.

The SSH script reads each lane's ``all_rows.jsonl`` from the byte offset of
the previous poll, so each poll transfers only new rows, in compact form.

Start::

    nohup python3 scripts/deduction/b200_dashboard.py > /tmp/b200_dashboard.log 2>&1 &

Stop::

    kill <pid>    # pid is in /tmp/b200_dashboard.pid

Pick the work dir with ``?mode=full`` / ``?mode=calib`` / ``?mode=auto`` on the
page URL, or ``--mode`` at start. ``auto`` uses ``full`` once it exists.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import tempfile
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = "ubuntu@34.217.49.59"
KEY = os.path.expanduser("~/.ssh/gpu-training.pem")
BASE = "/opt/dlami/nvme/sb"
BUCKET = "smolbench-results-414266451290"
S3_PREFIX = {
    "full": "deduction_postcutoff/b200_2026-09-24/setA_v2",
    "calib": "deduction_postcutoff/b200_2026-09-24/calib",
}
DEADLINE = datetime(2026, 9, 25, 11, 0, tzinfo=timezone.utc)
RUNGS = [
    "stepk:2", "sig:0", "sig:1", "sig:2", "sig:3", "proof:0", "proof:2",
    "sigpad:1", "sigpad:2", "sigpad:3", "proofpad:0", "proofpad:2",
    "hoponly:1", "hoponly:2", "hoponly:3",
]
N_MODELS, N_THEOREMS, N_REPS = 21, 100, 3
SCORED = {"success", "lean_error", "incomplete", "given_up", "no_answer", "timeout"}
RATE_WINDOW_S = 15 * 60

# Runs on the box. Reads only. ARGS is substituted before sending.
REMOTE = r'''
import glob, json, os, re, subprocess, sys, time
ARGS = json.loads(%(args)r)
base = ARGS["base"]
out = {"t": time.time(), "exists": {m: os.path.isdir(f"{base}/{m}/logs") for m in ("full", "calib")}}
mode = ARGS["mode"]
if mode == "auto":
    mode = "full" if out["exists"]["full"] else "calib"
out["mode"] = mode
work = f"{base}/{mode}"
logs = f"{work}/logs"

def tail(path, n, nbytes=65536):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - nbytes))
            return f.read().decode("utf-8", "replace").splitlines()[-n:]
    except OSError:
        return []

try:
    out["status"] = json.load(open(f"{logs}/status.json"))
except Exception as e:
    out["status"] = None; out["status_err"] = str(e)
out["status_mtime"] = os.path.getmtime(f"{logs}/status.json") if os.path.exists(f"{logs}/status.json") else None
out["log_tail"] = tail(f"{logs}/packed_box.log", 15)

try:
    r = subprocess.run(["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used,memory.total",
                        "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=20)
    out["gpus"] = [[x.strip() for x in l.split(",")] for l in r.stdout.strip().splitlines()]
except Exception as e:
    out["gpus"] = []; out["gpu_err"] = str(e)

me = os.getpid()
n_filter, drivers, lanes, verifiers = 0, [], 0, 0
verifying = set()
for p in os.listdir("/proc"):
    if not p.isdigit() or int(p) == me:
        continue
    try:
        cmd = open(f"/proc/{p}/cmdline", "rb").read().split(b"\0")
    except OSError:
        continue
    s = b" ".join(cmd).decode("utf-8", "replace")
    if "python" not in s:
        continue
    if "smolbench.deduction.lean.cli filter" in s:
        n_filter += 1
    elif "packed_box.py" in s:
        drivers.append(s[:600])
    elif "run_study.py" in s:
        lanes += 1
    elif "lean_verify_rows.py" in s:
        verifiers += 1
        mm = re.search(r"--runs scaling_(\S+)", s)
        if mm:
            verifying.add(mm.group(1))
out["n_filter"], out["drivers"], out["n_lane_procs"], out["n_verify_procs"] = n_filter, drivers, lanes, verifiers

lane_logs = []
for path in sorted(glob.glob(f"{logs}/lane_*_r*.log") + glob.glob(f"{logs}/verify_*.log")):
    try:
        data = open(path, "rb").read()
    except OSError:
        continue
    lane_logs.append({"name": os.path.basename(path), "size": len(data),
                      "mtime": os.path.getmtime(path),
                      "traceback": data.count(b"Traceback"),
                      "trivial": data.count(b"trivial-skip"),
                      "last": data.decode("utf-8", "replace").strip().splitlines()[-1:]})
out["lane_logs"] = lane_logs

# Lean-check status per model: the driver logs "verify <model>: rc=N" when a
# check ends; lean_verify_rows.py logs "N group(s) total" and checkpoint
# progress lines while it runs.
verify = {}
rc_re = re.compile(r"verify (\S+): rc=(-?\d+)")
for line in tail(f"{logs}/packed_box.log", 5000, nbytes=4 << 20):
    mm = rc_re.search(line)
    if mm:
        verify.setdefault(mm.group(1), {})["rc"] = int(mm.group(2))
for path in glob.glob(f"{logs}/verify_*.log"):
    model = os.path.basename(path)[len("verify_"):-len(".log")]
    v = verify.setdefault(model, {})
    total = done = None
    for line in tail(path, 400, nbytes=1 << 20):
        mm = re.search(r"(\d+) group\(s\) total", line)
        if mm:
            total = int(mm.group(1))
        mm = re.search(r"after (\d+)/(\d+) group", line)
        if mm:
            done, total = int(mm.group(1)), int(mm.group(2))
        mm = re.search(r"progress (\d+)/(\d+) group\(s\); (\d+)/(\d+) scored success", line)
        if mm:
            done, total = int(mm.group(1)), int(mm.group(2))
            v["ok"], v["scored"] = int(mm.group(3)), int(mm.group(4))
        if "group(s) processed" in line:
            done = total
    v.update({"log": True, "done_groups": done, "total_groups": total})
for model in verifying:
    verify.setdefault(model, {})["running"] = True
out["verify"] = verify

offsets = ARGS["offsets"]
runs = {}
for d in sorted(glob.glob(f"{work}/results/runs/scaling_*")):
    model = os.path.basename(d)[len("scaling_"):]
    info = {"rows": [], "reset": False}
    path = f"{d}/all_rows.jsonl"
    try:
        st = os.stat(path)
        prev = offsets.get(path)
        off = 0
        if prev and prev[1] == st.st_ino and prev[0] <= st.st_size:
            off = prev[0]
        else:
            info["reset"] = True
        with open(path, "rb") as f:
            f.seek(off)
            chunk = f.read()
        end = chunk.rfind(b"\n") + 1
        for line in chunk[:end].splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("kind", "cell") != "cell":
                continue
            info["rows"].append([r.get("theorem_id"), r.get("k"), r.get("rung"), r.get("replicate_idx"),
                                 r.get("verdict"), r.get("completion_tokens") or 0,
                                 r.get("finish_reason"), r.get("gen_ms") or 0,
                                 r.get("prompt_tokens") or 0])
        info["offset"] = [off + end, st.st_ino]
        info["path"] = path
        info["mtime"] = st.st_mtime
    except OSError:
        info["reset"] = True
    try:
        m = json.load(open(f"{d}/manifest.json"))
        info["manifest"] = {"started_at": m.get("started_at"), "finished_at": m.get("finished_at"),
                            "counts": m.get("counts")}
        c = m.get("config") or {}
        info["manifest"]["shape"] = [(c.get("theorems") or {}).get("limit"), len(c.get("rungs") or []),
                                     c.get("n_replicates")]
    except Exception:
        info["manifest"] = None
    runs[model] = info
out["runs"] = runs
print(json.dumps(out))
'''


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def fmt_dur(sec: float) -> str:
    if sec < 0:
        return "-" + fmt_dur(-sec)
    h, rem = divmod(int(sec), 3600)
    return f"{h}h {rem // 60:02d}m"


def pct(xs: list[int], q: float):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * (len(s) - 1) + 0.5))]


class State:
    """Everything the page shows; one instance per mode, updated by the poller."""

    def __init__(self) -> None:
        self.offsets: dict[str, list] = {}
        self.rows: dict[str, dict] = defaultdict(dict)  # model -> key -> row
        self.hist: dict[str, deque] = defaultdict(deque)  # model -> (t, n)
        self.total_hist: deque = deque()
        self.verified: dict[str, dict] = {}  # model -> {"etag":..., "rows": {key: verdict}}
        self.remote: dict | None = None
        self.remote_err = ""
        self.s3_err = ""
        self.last_ok: datetime | None = None
        self.last_try: datetime | None = None


class Poller:
    def __init__(self, mode: str, interval: int, tmp: Path, host: str = HOST, label: str = "box") -> None:
        self.host = host
        self.label = label
        self.mode = mode
        self.interval = interval
        self.tmp = tmp
        self.states: dict[str, State] = defaultdict(State)
        self.lock = threading.Lock()
        self.wake = threading.Event()

    def set_mode(self, mode: str) -> None:
        if mode in ("auto", "full", "calib") and mode != self.mode:
            self.mode = mode
            self.wake.set()

    def run(self) -> None:
        while True:
            try:
                self.poll()
            except Exception as e:  # noqa: BLE001 - keep the thread alive
                with self.lock:
                    self.states[self.mode].remote_err = f"poll error: {type(e).__name__}: {e}"
            self.wake.wait(self.interval)
            self.wake.clear()

    def poll(self) -> None:
        req_mode = self.mode
        # Offsets belong to the resolved mode; auto resolves remotely, so send both.
        offsets = {}
        for st in self.states.values():
            offsets.update(st.offsets)
        args = json.dumps({"base": BASE, "mode": req_mode, "offsets": offsets})
        script = REMOTE % {"args": args}
        t_try = now_utc()
        try:
            r = subprocess.run(
                ["ssh", "-i", KEY, "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                 "-o", "ServerAliveInterval=15", self.host, "python3", "-"],
                input=script, capture_output=True, text=True, timeout=120,
            )
            if r.returncode != 0:
                raise RuntimeError(f"ssh rc={r.returncode}: {r.stderr.strip()[-300:]}")
            data = json.loads(r.stdout)
        except Exception as e:  # noqa: BLE001
            with self.lock:
                st = self.states[req_mode]
                st.remote_err = f"box unreachable or script failed: {e}"
                st.last_try = t_try
            return
        mode = data["mode"]
        with self.lock:
            st = self.states[mode]
            if req_mode == "auto":
                self.states["auto"] = st
            st.last_try = t_try
            st.last_ok = t_try
            st.remote_err = ""
            st.remote = data
            t = data["t"]
            total = 0
            for model, info in data["runs"].items():
                if info.get("reset"):
                    st.rows[model] = {}
                rows = st.rows[model]
                for tid, k, rung, rep, verdict, ctok, fin, gms, ptok in info["rows"]:
                    rows.setdefault((tid, k, rung, rep), (verdict, ctok, fin, gms, ptok))
                if "offset" in info:
                    st.offsets[info["path"]] = info["offset"]
                h = st.hist[model]
                h.append((t, len(rows)))
                while h and t - h[0][0] > RATE_WINDOW_S + 120:
                    h.popleft()
                total += len(rows)
            st.total_hist.append((t, total))
            while st.total_hist and t - st.total_hist[0][0] > RATE_WINDOW_S + 120:
                st.total_hist.popleft()
        self.poll_s3(mode, st)

    def poll_s3(self, mode: str, st: State) -> None:
        prefix = S3_PREFIX[mode]
        try:
            r = subprocess.run(
                ["aws", "s3", "ls", f"s3://{BUCKET}/{prefix}/", "--recursive"],
                capture_output=True, text=True, timeout=120,
            )
            if r.returncode not in (0, 1):  # 1: nothing under the prefix
                raise RuntimeError(r.stderr.strip()[-300:])
        except Exception as e:  # noqa: BLE001
            st.s3_err = f"s3 ls failed: {e}"
            return
        st.s3_err = ""
        for line in r.stdout.splitlines():
            parts = line.split(None, 3)
            if len(parts) != 4 or not parts[3].endswith("/verified_rows.jsonl"):
                continue
            key = parts[3]
            # Canonical results sit directly under the prefix; _live/ and
            # _final/ are backup copies (and _live/ holds an early partial check).
            if "/_live/" in key or "/_final" in key:
                continue
            m = re.search(r"/scaling_([^/]+)/verified_rows\.jsonl$", key)
            if not m:
                continue
            model, tag = m.group(1), " ".join(parts[:3])
            if st.verified.get(model, {}).get("tag") == tag:
                continue
            dest = self.tmp / self.label / mode / f"{model}.jsonl"
            dest.parent.mkdir(parents=True, exist_ok=True)
            cp = subprocess.run(
                ["aws", "s3", "cp", "--only-show-errors", f"s3://{BUCKET}/{key}", str(dest)],
                capture_output=True, text=True, timeout=600,
            )
            if cp.returncode != 0:
                st.s3_err = f"s3 cp {model}: {cp.stderr.strip()[-200:]}"
                continue
            rows = {}
            with dest.open() as f:
                for ln in f:
                    try:
                        row = json.loads(ln)
                    except ValueError:
                        continue
                    if row.get("kind", "cell") != "cell":
                        continue
                    rows[(row.get("theorem_id"), row.get("k"), row.get("rung"),
                          row.get("replicate_idx"))] = row.get("verdict")
            dest.unlink(missing_ok=True)
            with self.lock:
                st.verified[model] = {"tag": tag, "rows": rows}


# ---------------------------------------------------------------- rendering

CSS = """
:root { --bg:#fff; --fg:#1d1d1f; --muted:#6b6b6b; --line:#ddd; --head:#f3f3f3;
        --bar:#3a7bd5; --bad:#c0392b; --ok:#1e8449; --warn:#b9770e; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#161618; --fg:#e6e6e6; --muted:#9a9a9a; --line:#333; --head:#222226;
          --bar:#5b9bf0; --bad:#ec7063; --ok:#58d68d; --warn:#f5b041; } }
body { background:var(--bg); color:var(--fg); font:14px/1.4 system-ui,sans-serif;
       margin:16px; }
h1 { font-size:20px; margin:0 0 8px; } h2 { font-size:16px; margin:20px 0 6px; }
table { border-collapse:collapse; } th,td { border-bottom:1px solid var(--line);
  padding:3px 8px; text-align:right; white-space:nowrap; }
th { background:var(--head); } td.l, th.l { text-align:left; }
.muted { color:var(--muted); } .bad { color:var(--bad); } .ok { color:var(--ok); }
.warn { color:var(--warn); }
.kv span { margin-right:22px; display:inline-block; }
.meter { display:inline-block; width:90px; height:9px; background:var(--line);
         vertical-align:middle; } .meter i { display:block; height:100%; background:var(--bar); }
pre { background:var(--head); padding:8px; overflow-x:auto; font-size:12px; }
a { color:var(--bar); } .wrap { overflow-x:auto; }
"""


def e(x) -> str:
    return html.escape("" if x is None else str(x))


def meter(frac: float) -> str:
    frac = max(0.0, min(1.0, frac))
    return f'<span class="meter"><i style="width:{frac * 100:.0f}%"></i></span>'


def rate_of(hist: deque, t_now: float) -> float | None:
    """Rows per minute over the last RATE_WINDOW_S, from our own poll history."""
    pts = [p for p in hist if t_now - p[0] <= RATE_WINDOW_S]
    if len(pts) < 2 or pts[-1][0] - pts[0][0] < 60:
        return None
    return (pts[-1][1] - pts[0][1]) / ((pts[-1][0] - pts[0][0]) / 60)


def render_box(poller: Poller, mode_req: str) -> tuple[str, dict]:
    """One box's sections; returns (html, verified rows by model) for the pooled table."""
    with poller.lock:
        st = poller.states.get(mode_req) or State()
        d = st.remote
        rows_by_model = {m: dict(r) for m, r in st.rows.items()}
        verified = {m: v["rows"] for m, v in st.verified.items()}
        hist = {m: deque(h) for m, h in st.hist.items()}
        total_hist = deque(st.total_hist)
    now = now_utc()
    mode = d["mode"] if d else mode_req
    out = [f"<h1>{e(poller.label)}: {e(poller.host)}</h1>"
           f"<div class=muted>packed run <b>{e(mode)}</b>, work dir {BASE}/{e(mode)}</div>"]
    kv = [f"<span>refreshed: {e(st.last_ok.strftime('%H:%M:%S') if st.last_ok else 'never')} UTC</span>"]
    if st.remote_err:
        kv.append(f"<span class=bad>{e(st.remote_err)}</span>")
    if st.s3_err:
        kv.append(f"<span class=bad>{e(st.s3_err)}</span>")
    if d is None:
        out.append("<p class=kv>" + "".join(kv) + "</p><p>Waiting for the first poll.</p>")
        return "".join(out), {}

    status = d.get("status") or []
    lane_logs = d.get("lane_logs", [])
    trivial = max((x["trivial"] for x in lane_logs if x["name"].startswith("lane_")), default=0)
    any_finished = any((i.get("manifest") or {}).get("finished_at") for i in d["runs"].values())
    def exp_for(m: str) -> int:
        shape = ((d["runs"].get(m) or {}).get("manifest") or {}).get("shape") or []
        lim, nr, reps = (list(shape) + [None] * 3)[:3]
        return (reps or N_REPS) * ((nr or len(RUNGS)) * (lim or N_THEOREMS) - trivial)

    names = [s["model"] for s in status] or list(d["runs"]) or ["?"] * N_MODELS
    expected = sum(exp_for(m) for m in names)
    done = sum(len(r) for r in rows_by_model.values())
    trate = rate_of(total_hist, d["t"])
    eta = ""
    if trate and trate > 0:
        fin = datetime.fromtimestamp(d["t"] + (expected - done) / trate * 60, timezone.utc)
        late = " (after deadline)" if fin > DEADLINE else ""
        eta = f"{fin.strftime('%m-%d %H:%M')} UTC{late}"
    exp_note = "" if any_finished else " (upper bound: trivial skips not all seen yet)"
    kv.append(f"<span>generations: <b>{done:,}</b> / {expected:,}{exp_note} "
              f"{meter(done / expected if expected else 0)}</span>")
    kv.append(f"<span>rate (last 15 min): {f'{trate:.1f}/min' if trate is not None else 'n/a'}</span>")
    kv.append(f"<span>est. finish: {e(eta or 'n/a')}</span>")
    drv = d.get("drivers") or []
    kv.append(f"<span>driver: {'<span class=ok>running</span>' if drv else '<span class=warn>not running</span>'}"
              f"; lane procs {d.get('n_lane_procs', 0)}; verify procs {d.get('n_verify_procs', 0)}</span>")
    if d.get("status_mtime"):
        age = (d["t"] - d["status_mtime"]) / 60
        kv.append(f"<span class={'bad' if age > 2 else 'muted'}>status.json age: {age:.0f} min</span>")
    if d.get("n_filter"):
        kv.append(f"<span class=warn>replay-filter jobs: {d['n_filter']}</span>")
    ex = d.get("exists", {})
    kv.append(f"<span class=muted>full exists: {ex.get('full')}; calib exists: {ex.get('calib')}</span>")
    out.append("<p class=kv>" + "".join(kv) + "</p>")
    if drv:
        out.append(f"<div class=muted style='font-size:12px'>driver cmd: {e(drv[0])}</div>")

    # GPU panel
    holder = {}
    for s in status:
        if s.get("state") in ("serving", "running") and isinstance(s.get("gpus"), list):
            for g in s["gpus"]:
                holder[int(g)] = f"{s['model']} ({s['state']})"
    out.append("<h2>GPUs</h2><div class=wrap><table><tr><th>GPU</th><th>util %</th><th></th>"
               "<th>mem GiB</th><th></th><th class=l>model</th></tr>")
    for g in d.get("gpus", []):
        try:
            idx, util, used, tot = int(g[0]), float(g[1]), float(g[2]), float(g[3])
        except (ValueError, IndexError):
            continue
        out.append(f"<tr><td>{idx}</td><td>{util:.0f}</td><td>{meter(util / 100)}</td>"
                   f"<td>{used / 1024:.0f} / {tot / 1024:.0f}</td><td>{meter(used / tot if tot else 0)}</td>"
                   f"<td class=l>{e(holder.get(idx, '-'))}</td></tr>")
    if not d.get("gpus"):
        out.append(f"<tr><td colspan=6 class=l>nvidia-smi gave no data {e(d.get('gpu_err', ''))}</td></tr>")
    out.append("</table></div>")

    # Model table
    out.append("<h2>Models</h2><div class=wrap><table><tr><th class=l>model</th><th class=l>GPUs</th>"
               "<th class=l>state</th><th>min</th><th>done / expected</th><th></th><th>gen/min</th>"
               "<th>median out tok</th><th>p90 out tok</th><th>len-cut</th><th>exception</th>"
               "<th class=l>Lean check</th><th>Lean pass</th><th class=l>note</th></tr>")
    models = [s["model"] for s in status] + sorted(
        set(rows_by_model) - {s["model"] for s in status})
    smap = {s["model"]: s for s in status}
    for m in models:
        s = smap.get(m, {})
        rows = rows_by_model.get(m, {})
        n = len(rows)
        per_model_exp = exp_for(m)
        ctoks = [r[1] for r in rows.values() if r[0] != "exception"]
        n_len = sum(1 for r in rows.values() if r[2] == "length")
        n_exc = sum(1 for r in rows.values() if r[0] == "exception")
        r_recent = rate_of(hist.get(m, deque()), d["t"])
        mins = s.get("minutes") or 0
        if r_recent is None and n and mins and s.get("state") == "running":
            rate_s = f"~{n / mins:.1f}"  # lifetime average until we have history
        else:
            rate_s = f"{r_recent:.1f}" if r_recent is not None else "-"
        v = verified.get(m)
        vs_live = (d.get("verify") or {}).get(m, {})
        if v:
            scored = [x for x in v.values() if x in SCORED]
            ok = sum(1 for x in scored if x == "success")
            lean = f"{ok / len(scored):.1%} ({ok}/{len(scored)})" if scored else "0 scored"
        elif vs_live.get("scored"):
            # Running pass rate from the verifier's per-group log line on the box.
            ok, sc = vs_live["ok"], vs_live["scored"]
            lean = f"{ok / sc:.1%} ({ok}/{sc}) so far"
        else:
            lean = "-"
        state = s.get("state", "?")
        vs = (d.get("verify") or {}).get(m, {})
        if vs.get("running"):
            prog = (f" {vs['done_groups'] or 0}/{vs['total_groups']} groups"
                    if vs.get("total_groups") else "")
            check, ccls = "running" + prog, "warn"
        elif "rc" in vs:
            check, ccls = ("done", "ok") if vs["rc"] == 0 else (f"failed rc={vs['rc']}", "bad")
        elif state == "done":
            check, ccls = "queued", "muted"
        elif state == "failed":
            check, ccls = "not run (lane failed)", "bad"
        else:
            check, ccls = "waiting for lane", "muted"
        scls = {"failed": "bad", "done": "ok", "running": "", "serving": "warn"}.get(state, "muted")
        gp = s.get("gpus")
        gps = ",".join(map(str, gp)) if isinstance(gp, list) else f"({gp})"
        out.append(
            f"<tr><td class=l>{e(m)}</td><td class=l>{e(gps)}</td><td class='l {scls}'>{e(state)}</td>"
            f"<td>{mins:.0f}</td><td>{n:,} / {per_model_exp:,}</td>"
            f"<td>{meter(n / per_model_exp if per_model_exp else 0)}</td><td>{rate_s}</td>"
            f"<td>{e(pct(ctoks, 0.5) if ctoks else '-')}</td><td>{e(pct(ctoks, 0.9) if ctoks else '-')}</td>"
            f"<td>{n_len or ''}</td><td class={'bad' if n_exc else ''}>{n_exc or ''}</td>"
            f"<td class='l {ccls}'>{e(check)}</td>"
            f"<td>{e(lean)}</td><td class='l muted'>{e(s.get('note', ''))[:120]}</td></tr>")
    out.append("</table></div>")
    if st.remote and d.get("status") is None:
        out.append(f"<p class=muted>status.json unreadable: {e(d.get('status_err'))}</p>")

    # Logs
    out.append(f"<h2>packed_box.log (last 15 lines)</h2><pre>{e(chr(10).join(d.get('log_tail', [])) or '(missing)')}</pre>")
    tb = [x for x in lane_logs if x["traceback"]]
    out.append("<h2>Logs containing Traceback</h2>")
    if tb:
        out.append("<table><tr><th class=l>log</th><th>count</th><th class=l>last line</th></tr>")
        for x in tb:
            out.append(f"<tr><td class='l bad'>{e(x['name'])}</td><td>{x['traceback']}</td>"
                       f"<td class='l muted'>{e((x['last'] or [''])[0][:160])}</td></tr>")
        out.append("</table>")
    else:
        out.append(f"<p class=muted>None ({len(lane_logs)} lane/verify logs checked).</p>")
    return "".join(out), verified


def render(pollers: list[Poller], mode_req: str) -> str:
    now = now_utc()
    out = [f"<!doctype html><html><head><meta charset=utf-8>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<meta http-equiv=refresh content=30><title>B200 run</title>"
           f"<style>{CSS}</style></head><body>"]
    links = " | ".join(
        f"<b>{m}</b>" if m == mode_req else f'<a href="/?mode={m}">{m}</a>'
        for m in ("auto", "full", "calib"))
    left = (DEADLINE - now).total_seconds()
    cls = "bad" if left < 2 * 3600 else ""
    out.append(f"<p class=kv><span>{len(pollers)} box(es)</span><span>mode: {links}</span>"
               f"<span>now: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC</span>"
               f"<span class={cls}>left until 11:00 UTC Sep 25: <b>{fmt_dur(left)}</b></span></p>")
    verified: dict[str, dict] = {}
    for poller in pollers:
        body, v = render_box(poller, mode_req)
        out.append(body)
        verified.update(v)  # models are disjoint across boxes
    mode = mode_req
    for poller in pollers:
        with poller.lock:
            st = poller.states.get(mode_req)
            if st and st.remote:
                mode = st.remote["mode"]
                break
    # Per-rung table
    out.append(f"<h2>Per rung, pooled over the {len(verified)} model(s) whose Lean check is in S3</h2>")
    if verified:
        groups: dict[tuple, list[int]] = defaultdict(list)
        for m, vr in verified.items():
            for (tid, k, rung, rep), verdict in vr.items():
                if verdict in SCORED:
                    groups[(m, tid, k, rung)].append(1 if verdict == "success" else 0)
        by_rung: dict[str, list[list[int]]] = defaultdict(list)
        for (m, tid, k, rung), xs in groups.items():
            by_rung[rung].append(xs)
        out.append("<div class=wrap><table><tr><th class=l>rung</th><th>pass@1</th><th>pass@3</th>"
                   "<th>n groups</th><th>groups with 3 reps</th></tr>")
        for rung in RUNGS + sorted(set(by_rung) - set(RUNGS)):
            gs = by_rung.get(rung, [])
            if not gs:
                out.append(f"<tr><td class=l>{e(rung)}</td><td>-</td><td>-</td><td>0</td><td>0</td></tr>")
                continue
            p1 = sum(sum(x) / len(x) for x in gs) / len(gs)
            full3 = [x for x in gs if len(x) >= 3]
            p3 = f"{sum(1 for x in full3 if any(x)) / len(full3):.1%}" if full3 else "-"
            out.append(f"<tr><td class=l>{e(rung)}</td><td>{p1:.1%}</td><td>{p3}</td>"
                       f"<td>{len(gs)}</td><td>{len(full3)}</td></tr>")
        out.append("</table></div><p class=muted>pass@3 uses only groups with all 3 replicates scored. "
                   "Scored verdicts: " + ", ".join(sorted(SCORED)) + ".</p>")
    else:
        out.append(f"<p class=muted>No verified_rows.jsonl under s3://{BUCKET}/{S3_PREFIX[mode]}/ yet.</p>")

    out.append("<p class=muted>Read-only. JSON at <a href='/json'>/json</a>.</p></body></html>")
    return "".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--interval", type=int, default=45, help="seconds between polls")
    ap.add_argument("--mode", default="auto", choices=["auto", "full", "calib"])
    ap.add_argument("--host", default=HOST,
                    help="comma list of boxes to poll, each user@ip or label=user@ip")
    ap.add_argument("--pid-file", default="/tmp/b200_dashboard.pid")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="b200_dashboard_"))
    pollers: list[Poller] = []
    for i, spec in enumerate(x.strip() for x in args.host.split(",") if x.strip()):
        label, _, host = spec.rpartition("=")
        pollers.append(Poller(args.mode, args.interval, tmp, host or spec, label or f"box{i + 1}"))
    for poller in pollers:
        threading.Thread(target=poller.run, daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if "mode" in q:
                for poller in pollers:
                    poller.set_mode(q["mode"][0])
            if u.path == "/json":
                body_d = {}
                for poller in pollers:
                    with poller.lock:
                        st = poller.states.get(poller.mode)
                        body_d[poller.label] = ({k: v for k, v in (st.remote or {}).items() if k != "runs"}
                                                if st else {})
                body = json.dumps(body_d, default=str).encode()
                ctype = "application/json"
            elif u.path == "/":
                body = render(pollers, pollers[0].mode).encode()
                ctype = "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a) -> None:
            pass

    Path(args.pid_file).write_text(str(os.getpid()))
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
