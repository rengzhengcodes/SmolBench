"""Run the deduction roster on one multi-GPU box, several models at a time.

The fleet serves one model per box through the control agent, with
``--max-num-seqs 1``. This driver instead runs on the box itself and packs it:

* one vLLM container per GPU subset (``docker run --gpus device=...``), each
  on its own host port, with batching on (``--max-num-seqs``) and CUDA graphs;
* a queue of models, started in plan order; a job waits for its GPUs, and a
  job that needs the whole box blocks smaller ones behind it so it is not
  starved;
* weights staged to the local HF cache ahead of the queue, so a GPU never
  waits on a download;
* one ``run_study.py`` lane per model against its server
  (``LEAN_EXTERNAL_ENDPOINT=1``), which spools its rows to S3 when it ends;
* ``lean_verify_rows.py`` on each finished lane, one lane at a time, using the
  box's spare CPUs;
* ``aws s3 sync`` of every lane's results directory and every log every few
  minutes, so nothing is lost if the box stops.

Batched decoding is not bit-for-bit reproducible, so these rows must not pool
with fleet (``--max-num-seqs 1``) rows; keep them under their own
``--spool-prefix``.

Run on the box (see ``--help`` for every option)::

    python scripts/deduction/packed_box.py --spool-prefix deduction_postcutoff/b200_2026-09-24 \\
        --lean-data /opt/sb/corpus_T2026-06-03/leandojo_benchmark_4 \\
        --mathlib-root /opt/sb/mathlib4-2ca39e62 --work /opt/dlami/nvme/sb
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import secrets
import subprocess
import sys
import threading
import time
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from smolbench.evals.providers import ec2  # noqa: E402

#: Plan for one p6-b200.48xlarge (8x B200, 179 GB each). GPU counts are the
#: smallest that leave ample KV cache and divide the model's attention heads;
#: the four DeepSeek/GLM-4.7 models keep the tp=8 recipes validated on B200.
#: Order is the queue, small models first (Fisher, 2026-09-24) so the cheap end
#: of the roster is done before the block ends: 1-GPU models packed eight at a
#: time (slow dense ones first, the non-thinking Ministrals last to fill gaps),
#: then 2- and 4-GPU models, then the whole-box models, which wait for all
#: eight GPUs to drain.
B200_PLAN: tuple[tuple[str, int], ...] = (
    ("qwen3.5-27b", 1),
    ("gemma-4-31b", 1),
    ("exaone-4.0-32b", 1),
    ("exaone-4.5-33b", 1),
    ("nemotron-3-nano-30b-a3b", 1),
    ("glm-4.7-flash", 1),
    ("gemma-4-12b", 1),
    ("nemotron-3-nano-4b", 1),
    ("gemma-4-e2b", 1),
    ("ministral-3-14b", 1),
    ("ministral-3-8b", 1),
    ("ministral-3-3b", 1),
    ("qwen3.5-122b-a10b", 2),
    ("nemotron-3-super-120b-a12b", 2),
    ("glm-4.5-air", 2),
    ("k-exaone-236b-a23b", 4),
    ("qwen3.5-397b-a17b", 4),
    ("deepseek-v4-flash", 8),
    ("deepseek-v3.1", 8),
    ("glm-4.7", 8),
    ("deepseek-v4-pro", 8),
)

#: Each checkpoint's native context window (max_position_embeddings in its
#: pinned Hugging Face config, read 2026-09-24).
NATIVE_CONTEXT: dict[str, int] = {
    "qwen3.5-27b": 262144, "qwen3.5-122b-a10b": 262144, "qwen3.5-397b-a17b": 262144,
    "nemotron-3-nano-4b": 262144, "nemotron-3-nano-30b-a3b": 262144,
    "nemotron-3-super-120b-a12b": 262144,
    "gemma-4-e2b": 131072, "gemma-4-12b": 262144, "gemma-4-31b": 262144,
    "glm-4.7-flash": 202752, "glm-4.5-air": 131072, "glm-4.7": 202752,
    "ministral-3-3b": 262144, "ministral-3-8b": 262144, "ministral-3-14b": 262144,
    "exaone-4.0-32b": 131072, "exaone-4.5-33b": 262144, "k-exaone-236b-a23b": 262144,
    "deepseek-v4-flash": 1048576, "deepseek-v3.1": 163840, "deepseek-v4-pro": 1048576,
}

#: Every model is served at the roster's smallest native window, with no
#: max_tokens, so each answer gets the same budget (131,072 tokens minus its
#: prompt) and one that does not stop within it scores as a failure
#: (finish_reason=length). Native windows up to 1M let a looping answer hold the
#: whole box for hours (deepseek-v4-flash, 2026-09-24: 20 answers past 150k tokens
#: while the longest finished one was 60.6k).
SHARED_CONTEXT: int = min(NATIVE_CONTEXT.values())


def served_context(key: str) -> int:
    return min(NATIVE_CONTEXT[key], SHARED_CONTEXT)


#: Fleet determinism flags this driver replaces: batching needs more than one
#: sequence, and CUDA graphs are the main decode-speed win.
_DROP_FLAGS = {"--max-num-seqs": 1, "--enforce-eager": 0}


@dataclass
class Job:
    key: str
    gpus: int
    replicates: int = 0  # 0: the sweep file's n_replicates
    devices: list[int] = field(default_factory=list)
    port: int = 0
    container: str = ""
    lane: subprocess.Popen | None = None
    started: float = 0.0
    state: str = "queued"  # queued | serving | running | done | failed
    note: str = ""


def vllm_args(key: str, max_num_seqs: int) -> list[str]:
    """The spec's vLLM arguments with the fleet's determinism flags replaced."""
    args = list(ec2.EC2_DEPLOY_SPECS[key].get("vllm_args", []))
    out: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in _DROP_FLAGS:
            i += 1 + _DROP_FLAGS[a]
            continue
        out.append(a)
        i += 1
    return out + ["--max-num-seqs", str(max_num_seqs)]


def revision(key: str) -> str:
    args = ec2.EC2_DEPLOY_SPECS[key].get("vllm_args", [])
    return args[args.index("--revision") + 1] if "--revision" in args else "main"


def docker_cmd(job: Job, api_key: str, hf_home: Path, max_num_seqs: int) -> list[str]:
    spec = ec2.EC2_DEPLOY_SPECS[job.key]
    heads = ec2.MODEL_ATTENTION_HEADS.get(job.key)
    if heads is not None and heads % job.gpus:
        raise SystemExit(f"{job.key}: {job.gpus} GPUs does not divide {heads} attention heads")
    return [
        "docker", "run", "-d", "--name", job.container,
        "--gpus", '"device=%s"' % ",".join(map(str, job.devices)),
        "--ipc=host",
        "-p", f"127.0.0.1:{job.port}:8000",
        "-v", f"{hf_home}:/root/.cache/huggingface",
        "-v", f"{hf_home}/vllm-cache:/root/.cache/vllm",
        "-e", "HF_HUB_OFFLINE=1",
        ec2.EC2_VLLM_IMAGE,
        "--model", spec["hf_model_id"],
        "--served-model-name", job.key,
        "--tensor-parallel-size", str(job.gpus),
        "--max-model-len", str(served_context(job.key)),
        "--api-key=" + api_key,
    ] + vllm_args(job.key, max_num_seqs)


def healthy(port: int, api_key: str, key: str) -> bool:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/models", headers={"Authorization": f"Bearer {api_key}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return key in [m["id"] for m in json.load(r)["data"]]
    except Exception:  # noqa: BLE001 -- not up yet
        return False


def container_running(name: str) -> bool:
    out = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", name], capture_output=True, text=True
    )
    return out.stdout.strip() == "true"


class Prefetcher:
    """Download each model's pinned revision into the HF cache, in queue order."""

    def __init__(self, keys: list[str], hf_home: Path, logs: Path, parallel: int):
        self.done: dict[str, bool] = {}
        self._q = deque(keys)
        self._lock = threading.Lock()
        self._hf_home, self._logs = hf_home, logs
        self._threads = [threading.Thread(target=self._work, daemon=True) for _ in range(parallel)]
        for t in self._threads:
            t.start()

    def _work(self) -> None:
        while True:
            with self._lock:
                if not self._q:
                    return
                key = self._q.popleft()
            spec = ec2.EC2_DEPLOY_SPECS[key]
            log = (self._logs / f"download_{key}.log").open("w")
            env = dict(os.environ, HF_HOME=str(self._hf_home), HF_HUB_ENABLE_HF_TRANSFER="0")
            ok = False
            for attempt in range(3):
                rc = subprocess.run(
                    ["hf", "download", spec["hf_model_id"], "--revision", revision(key)],
                    stdout=log, stderr=subprocess.STDOUT, env=env,
                ).returncode
                if rc == 0:
                    ok = True
                    break
                time.sleep(30 * (attempt + 1))
            logging.info(f"download {key}: {'ok' if ok else 'FAILED'}")
            self.done[key] = ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spool-prefix", required=True, help="S3 key prefix for this study's rows")
    ap.add_argument("--lean-data", required=True, help="SMOLBENCH_LEAN_DATA for every lane")
    ap.add_argument("--mathlib-root", default="", help="SMOLBENCH_MATHLIB_ROOT; empty skips verification")
    ap.add_argument("--work", type=Path, required=True, help="results, logs and HF cache live here")
    ap.add_argument("--sweep", type=Path, default=REPO_ROOT / "notebooks/deduction/sweep_b200.yaml")
    ap.add_argument("--models", default="", help="comma list: run only these plan entries")
    ap.add_argument("--plan", default="",
                    help="comma list key=gpus overriding B200_PLAN's GPU count for those "
                         "models (an H200 box with 141 GB per GPU needs more GPUs per model)")
    ap.add_argument("--gpus", type=int, default=8)
    ap.add_argument("--max-num-seqs", type=int, default=256)
    ap.add_argument("--download-parallel", type=int, default=4)
    ap.add_argument("--verify-workers", type=int, default=48)
    ap.add_argument("--serve-timeout-min", type=int, default=90)
    ap.add_argument("--sync-every-s", type=int, default=300)
    ap.add_argument("--bucket", default="smolbench-results-414266451290")
    ap.add_argument("--live-logs", default="logs",
                    help="key under <spool-prefix>/_live/ for this box's logs; a second box "
                         "sharing the prefix needs its own (results are disjoint by model)")
    ap.add_argument("--passes", default="",
                    help="comma list of replicate counts, e.g. 1,3: run every model at "
                         "each count in turn (resume skips replicates already written)")
    ap.add_argument("--prefetch-only", action="store_true",
                    help="download every planned model's weights, then exit")
    args = ap.parse_args()

    work = args.work.resolve()
    logs, hf_home, results = work / "logs", work / "hf-cache", work / "results"
    for d in (logs, hf_home / "vllm-cache", results):
        d.mkdir(parents=True, exist_ok=True)
    hf_home = hf_home.resolve()  # a symlinked cache must reach docker -v as a real path
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[logging.FileHandler(logs / "packed_box.log"), logging.StreamHandler()],
    )
    only = [m.strip() for m in args.models.split(",") if m.strip()]
    override = {k: int(g) for k, g in (kv.split("=") for kv in args.plan.split(",") if kv.strip())}
    plan = [(k, override.get(k, g)) for k, g in B200_PLAN if not only or k in only]
    if only and len(plan) != len(only):
        raise SystemExit(f"unknown --models: {sorted(set(only) - {k for k, _ in plan})}")
    if set(override) - {k for k, _ in plan}:
        raise SystemExit(f"--plan names models outside the plan: {sorted(set(override) - {k for k, _ in plan})}")
    passes = [int(p) for p in args.passes.split(",") if p.strip()] or [0]
    jobs = deque(Job(k, g, reps) for reps in passes for k, g in plan)
    if args.prefetch_only:
        logs.mkdir(parents=True, exist_ok=True)
        pre = Prefetcher([k for k, _ in plan], hf_home, logs, args.download_parallel)
        while len(pre.done) < len(plan):
            time.sleep(10)
        failed = [k for k, ok in pre.done.items() if not ok]
        logging.info(f"prefetch finished; failed: {failed or 'none'}")
        return 1 if failed else 0
    api_key = secrets.token_hex(16)
    s3_live = f"s3://{args.bucket}/{args.spool_prefix}/_live"

    # Sync results and logs to S3 on a timer so a stopped box loses little.
    stop = threading.Event()

    def sync_loop() -> None:
        while not stop.wait(args.sync_every_s):
            for src, dst in ((results, "results"), (logs, args.live_logs)):
                subprocess.run(
                    ["aws", "s3", "sync", "--only-show-errors", str(src), f"{s3_live}/{dst}"],
                    capture_output=True,
                )

    threading.Thread(target=sync_loop, daemon=True).start()

    prefetch = Prefetcher([k for k, _ in plan], hf_home, logs, args.download_parallel)

    # Verification runs one lane at a time on the CPUs, after that lane spools.
    verify_q: deque[tuple[str, bool]] = deque()
    verify_done = threading.Event()

    def verify_loop() -> None:
        while True:
            if not verify_q:
                if verify_done.is_set():
                    return
                time.sleep(15)
                continue
            key, reverify = verify_q.popleft()
            env = dict(
                os.environ,
                SMOLBENCH_LEAN_DATA=args.lean_data,
                SMOLBENCH_MATHLIB_ROOT=args.mathlib_root,
                LEAN_SPOOL_PREFIX=args.spool_prefix,
                PATH=f"{Path.home()}/.elan/bin:" + os.environ["PATH"],
            )
            with (logs / f"verify_{key}.log").open("a") as log:
                rc = subprocess.run(
                    [sys.executable, str(REPO_ROOT / "scripts/deduction/lean_verify_rows.py"),
                     "--runs", f"scaling_{key}", "--workers", str(args.verify_workers)]
                    # A later pass adds replicates to groups already verified;
                    # group-keyed resume would skip them, so re-score all.
                    + (["--reverify-all"] if reverify else []),
                    stdout=log, stderr=subprocess.STDOUT, env=env,
                ).returncode
            logging.info(f"verify {key}: rc={rc}")

    verifier = None
    if args.mathlib_root:
        verifier = threading.Thread(target=verify_loop, daemon=True)
        verifier.start()

    free = set(range(args.gpus))
    running: list[Job] = []
    finished: list[Job] = []
    next_port = 8100

    def status() -> None:
        rows = [
            {"model": j.key, "gpus": j.devices or j.gpus, "state": j.state, "note": j.note,
             "minutes": round((time.time() - j.started) / 60, 1) if j.started else 0}
            for j in list(running) + list(jobs) + finished
        ]
        (logs / "status.json").write_text(json.dumps(rows, indent=1))

    while jobs or running:
        # Start what fits, in order; a whole-box job blocks the queue behind it.
        for job in list(jobs):
            if prefetch.done.get(job.key) is False:
                jobs.remove(job)
                job.state, job.note = "failed", "weight download failed; see download_<key>.log"
                finished.append(job)
                logging.info(f"failed {job.key}: {job.note}")
                continue
            if not prefetch.done.get(job.key):
                if job.gpus == args.gpus:
                    break
                continue
            if job.gpus > len(free):
                if job.gpus == args.gpus:
                    break
                continue
            jobs.remove(job)
            job.devices = sorted(free)[: job.gpus]
            free.difference_update(job.devices)
            job.port, next_port = next_port, next_port + 1
            job.container = f"vllm-{job.key}"
            subprocess.run(["docker", "rm", "-f", job.container], capture_output=True)
            cmd = docker_cmd(job, api_key, hf_home, args.max_num_seqs)
            (logs / f"server_{job.key}.json").write_text(json.dumps(
                {"model": job.key, "devices": job.devices, "image": ec2.EC2_VLLM_IMAGE,
                 "argv": [a if not a.startswith("--api-key=") else "--api-key=<redacted>" for a in cmd]},
                indent=1))
            rc = subprocess.run(cmd, capture_output=True, text=True)
            job.started = time.time()
            if rc.returncode != 0:
                job.state, job.note = "failed", f"docker run: {rc.stderr[-300:]}"
                free.update(job.devices)
                finished.append(job)
                continue
            job.state = "serving"
            running.append(job)
            logging.info(f"start {job.key} on GPUs {job.devices} port {job.port}")

        for job in list(running):
            if job.state == "serving":
                if healthy(job.port, api_key, job.key):
                    env = dict(
                        os.environ,
                        LEAN_MODEL=job.key,
                        EC2_EXPERIMENT_TAG=f"scaling-{job.key}",
                        LEAN_EXTERNAL_ENDPOINT="1",
                        EC2_SERVED_CONTEXT_LENGTH=str(served_context(job.key)),
                        EC2_STREAM_COMPLETIONS="1",
                        EC2_INFERENCE_BASE_URL=f"http://127.0.0.1:{job.port}/v1",
                        EC2_VLLM_API_KEY=api_key,
                        LEAN_SERVER_CONFIG=str(logs / f"server_{job.key}.json"),
                        LEAN_SWEEP_CONFIG=str(args.sweep),
                        LEAN_SPOOL_PREFIX=args.spool_prefix,
                        SMOLBENCH_LEAN_DATA=args.lean_data,
                        SMOLBENCH_LEAN_RESULTS=str(results),
                        **({"LEAN_N_REPLICATES": str(job.replicates)} if job.replicates else {}),
                    )
                    job.lane = subprocess.Popen(
                        [sys.executable, str(REPO_ROOT / "notebooks/deduction/run_study.py")],
                        stdout=(logs / f"lane_{job.key}_r{job.replicates}.log").open("w"),
                        stderr=subprocess.STDOUT, env=env, cwd=REPO_ROOT,
                    )
                    job.state = "running"
                    logging.info(f"lane {job.key}: server up after "
                                 f"{(time.time() - job.started) / 60:.1f} min")
                elif not container_running(job.container) or (
                    time.time() - job.started > args.serve_timeout_min * 60
                ):
                    tail = subprocess.run(["docker", "logs", "--tail", "40", job.container],
                                          capture_output=True, text=True)
                    (logs / f"server_{job.key}.log").write_text(tail.stdout + tail.stderr)
                    job.state, job.note = "failed", "server did not come up; see server_<key>.log"
            elif job.state == "running" and job.lane is not None and job.lane.poll() is not None:
                rc = job.lane.returncode
                job.state = "done" if rc == 0 else "failed"
                job.note = f"lane rc={rc}"
                if rc == 0:
                    verify_q.append((job.key, job.replicates != passes[0]))
            if job.state in ("done", "failed"):
                logs_out = subprocess.run(["docker", "logs", job.container],
                                          capture_output=True, text=True)
                (logs / f"server_{job.key}.log").write_text(logs_out.stdout + logs_out.stderr)
                subprocess.run(["docker", "rm", "-f", job.container], capture_output=True)
                free.update(job.devices)
                running.remove(job)
                finished.append(job)
                logging.info(f"{job.state} {job.key}: {job.note} "
                             f"({(time.time() - job.started) / 60:.1f} min)")
        status()
        time.sleep(10)

    verify_done.set()
    if verifier is not None:
        verifier.join()
    stop.set()
    for src, dst in ((results, "results"), (logs, args.live_logs)):
        subprocess.run(["aws", "s3", "sync", "--only-show-errors", str(src), f"{s3_live}/{dst}"])
    status()
    failed = [j.key for j in finished if j.state == "failed"]
    logging.info(f"all lanes finished; failed: {failed or 'none'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
