"""
Interfacing with models served from a self-provisioned EC2 Spot instance.

One large Spot instance is provisioned once per experiment and runs vLLM's
OpenAI-compatible server in Docker; each archetype section swaps WHICH model
that instance serves instead of re-provisioning hardware (contrast with
aws.py's per-archetype SageMaker ``provision_endpoint``). The motivation is
quota: multi-GPU SageMaker endpoint quotas default to 0, while EC2 Spot
allocation for the P5 family is available.

Lifecycle contract (each step is a notebook cell)::

    state = provision_spot_instance()        # once, at notebook start
    with serve_model(DENSE_MODEL):            # per archetype section
        marks = evaluate(quiz, DENSE_MODEL, SEED)
    shutdown_instance()                       # once, at notebook end

``provision_spot_instance`` is idempotent: it records the instance in a local
state file (``EC2_STATE_FILE``) and tags it ``smolbench:experiment``, so
re-running the cell (or restarting the kernel) reattaches to a live instance
instead of launching a second one. ``serve_model`` exits WITHOUT tearing
anything down -- the next section swaps the container, and abandonment is
covered by the safety nets below.

Safety nets (autonomous, on-instance -- they need no client involvement):
  - An idle watchdog (looping systemd service, checks every 60s) shuts the
    box down after ``EC2_IDLE_TIMEOUT_MIN`` minutes without activity. Activity = control-agent
    requests, movement in vLLM's request-token counters, or a model still
    loading within ``EC2_STARTUP_GRACE_MIN`` of its ``/serve``.
  - An absolute backstop ``shutdown -h +EC2_MAX_LIFETIME_MIN`` is scheduled at
    boot, before anything fallible runs.
  - The instance is a one-time Spot instance launched with
    InstanceInitiatedShutdownBehavior=terminate, so an OS-level shutdown
    TERMINATES it (and deletes its EBS volume) rather than leaving it stopped.

Setup
-----
    INFERENCE_PROVIDER=ec2     # to route smolbench.evals.provider here
    AWS_REGION=us-east-1       # first region tried (more via EC2_REGIONS)
    AWS_PROFILE=...            # any boto3-resolvable credentials work
    HF_TOKEN=hf_...            # OPTIONAL: only for gated repos added to the
                               # specs (the defaults are all ungated); baked
                               # into the instance at provision time

Provisioning imports boto3/botocore lazily, so importing this module (and the
query path) requires neither -- same convention as aws.py. The ``model``
argument to query()/evaluate() is a key of ``EC2_DEPLOY_SPECS``; that key is
also what vLLM serves under (``--served-model-name``), so it goes in the
request body verbatim.

Security model (accepted trade-offs for a short-lived, single-user box):
  - The security group opens ports 8000 (vLLM) and 9000 (control agent) ONLY
    to the caller's public IP /32; provisioning re-asserts the rule for the
    current IP on every call, so re-run it if your IP changes mid-experiment.
  - vLLM requires a per-experiment random ``--api-key``; the control agent
    requires a per-experiment random bearer token. Both live in the state
    file (mode 0600, gitignored) and in the instance's user-data, which any
    principal in the AWS account can read via DescribeInstanceAttribute.
  - Both planes are plain HTTP, so the tokens are visible in transit between
    you and the instance.
"""

import contextlib
import json
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional, Tuple

import requests
from joblib import Parallel, delayed

from smolbench.evals import Answer, QnA, Quiz, Mark, Marks

AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
# Spot capacity hunt order. Types are tried type-major (each type across every
# region before falling back to the next type): p5e (8xH200, 1128 GB VRAM)
# first, then p5 (8xH100, 640 GB). Regions default to AWS_REGION plus the US
# regions that offer the P5 family; both lists are runtime-filtered against
# describe_instance_type_offerings, so harmless to list a region a type has
# not reached yet.
EC2_INSTANCE_TYPES: Tuple[str, ...] = tuple(
    dict.fromkeys(
        t.strip()
        for t in os.getenv("EC2_INSTANCE_TYPES", "p5e.48xlarge,p5.48xlarge").split(",")
        if t.strip()
    )
)
_DEFAULT_REGIONS: str = ",".join(dict.fromkeys((AWS_REGION, "us-east-1", "us-east-2", "us-west-2")))
EC2_REGIONS: Tuple[str, ...] = tuple(
    dict.fromkeys(
        r.strip() for r in os.getenv("EC2_REGIONS", _DEFAULT_REGIONS).split(",") if r.strip()
    )
)
# Root gp3 volume: OS + docker image only. The model cache lives on
# instance-store NVMe when the type has one (every targeted type does:
# p5e/p5/p4de/g5/g6) -- bootstrap formats and mounts the first one at
# /opt/hf-cache, dodging gp3's 1000 MB/s ceiling. If you launch a type
# WITHOUT instance store, the cache falls back to the root volume: raise
# EC2_ROOT_VOLUME_GB to hold your checkpoints (the FP8 trio is ~1.1 TB).
EC2_ROOT_VOLUME_GB: int = int(os.getenv("EC2_ROOT_VOLUME_GB", "300"))
EC2_ROOT_VOLUME_THROUGHPUT: int = int(os.getenv("EC2_ROOT_VOLUME_THROUGHPUT", "500"))
EC2_ROOT_VOLUME_IOPS: int = int(os.getenv("EC2_ROOT_VOLUME_IOPS", "3000"))
# Pinned to vLLM 0.11.1 to match the SageMaker DLC the specs were written
# against (vllm:0.11.1-gpu-py312-...), keeping serving behavior comparable.
EC2_VLLM_IMAGE: str = os.getenv("EC2_VLLM_IMAGE", "vllm/vllm-openai:v0.11.1")
# Deep Learning Base GPU AMI (Ubuntu 22.04): NVIDIA driver, Docker, and the
# NVIDIA container toolkit preinstalled -- nothing to install at boot. The SSM
# parameter resolves to the latest build per region.
EC2_AMI_SSM_PARAM: str = os.getenv(
    "EC2_AMI_SSM_PARAM",
    "/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-22.04/latest/ami-id",
)
EC2_SECURITY_GROUP_NAME: str = os.getenv("EC2_SECURITY_GROUP_NAME", "smolbench-inference")
# Value of the ``smolbench:experiment`` tag used to find/reattach/terminate
# this experiment's instance.
EC2_EXPERIMENT_TAG: str = os.getenv("EC2_EXPERIMENT_TAG", "periodic-induction")
# Resolved relative to the cwd, so the notebook keeps it next to itself in
# notebooks/periodic/. Contains the control token and vLLM key -> gitignored.
EC2_STATE_FILE: str = os.getenv("EC2_STATE_FILE", ".ec2_state.json")
EC2_IDLE_TIMEOUT_MIN: int = int(os.getenv("EC2_IDLE_TIMEOUT_MIN", "30"))
# Serve timeout and the watchdog's loading-counts-as-active grace must cover a
# COLD checkpoint pull from HF: a ~410 GB download proved that 90/120 min are
# too tight (a live 405B serve outran both). With the S3 cache warm these are
# minutes, but the first-ever pull sets the bound.
EC2_STARTUP_GRACE_MIN: int = int(os.getenv("EC2_STARTUP_GRACE_MIN", "180"))
EC2_MAX_LIFETIME_MIN: int = int(os.getenv("EC2_MAX_LIFETIME_MIN", "1440"))
EC2_PROVISION_TIMEOUT_MIN: int = int(os.getenv("EC2_PROVISION_TIMEOUT_MIN", "15"))
EC2_SERVE_TIMEOUT_MIN: int = int(os.getenv("EC2_SERVE_TIMEOUT_MIN", "180"))
# Optional EC2 key pair name for SSH debugging; empty = no SSH (the default --
# boot problems are then visible only via the serial console/screenshot).
EC2_KEY_NAME: str = os.getenv("EC2_KEY_NAME", "")
EC2_MAX_PARALLEL_REQUESTS: int = int(os.getenv("EC2_MAX_PARALLEL_REQUESTS", "8"))
EC2_RETRY_BACKOFF_SECONDS: int = int(os.getenv("EC2_RETRY_BACKOFF_SECONDS", "60"))
# Consecutive connection failures tolerated before concluding the endpoint is
# gone (spot interruption / IP drift) rather than transiently overloaded.
EC2_MAX_CONNECTION_FAILURES: int = int(os.getenv("EC2_MAX_CONNECTION_FAILURES", "10"))
# Soft post-hoc token guard for models without a deploy spec.
EC2_CONTEXT_LENGTH: int = int(os.getenv("EC2_CONTEXT_LENGTH", "16384"))
# Optional S3 model cache, e.g. s3://smolbench-model-cache-<acct>/hf. When
# set, provisioning creates the bucket and an instance profile (S3 RW on the
# bucket + SSM core), the agent pulls each checkpoint from S3 before launching
# vLLM (same-region S3 -> NVMe runs at multi-GB/s vs 10-35 min from HF), and
# serve_model uploads freshly downloaded weights back in the background -- so
# the mirror seeds itself: the first instance pays HF once, later ones don't.
# Cross-region pulls still work (slower, ~$0.02/GB), so put the bucket where
# spot capacity usually lands (EC2_S3_CACHE_REGION).
EC2_S3_MODEL_CACHE: str = os.getenv("EC2_S3_MODEL_CACHE", "").rstrip("/")
EC2_S3_CACHE_REGION: str = os.getenv("EC2_S3_CACHE_REGION", AWS_REGION)
EC2_INSTANCE_ROLE_NAME: str = os.getenv("EC2_INSTANCE_ROLE_NAME", "smolbench-ec2-role")
# Overrides that bypass the state file -- point the inference path at any
# OpenAI-compatible server (used by the offline stub tests).
EC2_INFERENCE_BASE_URL: Optional[str] = os.getenv("EC2_INFERENCE_BASE_URL")
EC2_VLLM_API_KEY: Optional[str] = os.getenv("EC2_VLLM_API_KEY")
EC2_INFO: bool = bool(int(os.getenv("EC2_INFO", "0")))
EC2_INFO_RESPONSE: bool = bool(int(os.getenv("EC2_INFO_RESPONSE", "0")))

# Per-model deployment spec. The dict key is simultaneously (a) the ``model``
# argument the notebook passes to query()/evaluate() and (b) vLLM's
# ``--served-model-name``, so the OpenAI request body carries it verbatim.
# Keys: hf_model_id, tp (tensor parallelism), max_model_len (also the soft
# context guard), optional vllm_args (extra CLI flags), optional system_prompt
# (prepended to every request for that model).
#
# VRAM math behind the FP8 choice (uniform precision across archetypes): BF16
# Llama-3.1-405B (~810 GB) and BF16 Llama-4-Maverick (~800 GB) do not fit the
# 640 GB of a p5.48xlarge, so those two must be FP8 there; Nemotron-Ultra-253B
# is FP8 as well to keep precision comparable. All three FP8 checkpoints
# (~410/253/417 GB) fit p5.48xlarge with KV headroom at 32k context, and fit
# p5e.48xlarge (1128 GB) trivially.
#
# All three repos are UNGATED (anonymous download; no HF account or token):
# Meta's own meta-llama/*-FP8 repos require a logged-in account with the Llama
# license accepted, so the Llama-architecture models use the official
# redistributions from Red Hat AI (Neural Magic -- vLLM's quantization team;
# compressed-tensors FP8, vLLM-native) and NVIDIA's own Nemotron release.
# Gating verified 2026-06-10 via anonymous /resolve/main/config.json fetches.
#
# Nemotron-Ultra reasoning: the model's documented CoT toggle is the system
# prompt "detailed thinking on" (its chat template keys off it; the OpenAI
# ``reasoning_effort`` param is not wired up for it on vLLM). Injecting it
# here, at the provider layer, keeps the notebook's user prompts byte-identical
# across archetypes while ``--reasoning-parser deepseek_r1`` splits the
# <think>...</think> output into the response's ``reasoning_content`` channel.
EC2_DEPLOY_SPECS: Dict[str, Dict[str, Any]] = {
    # Small smoke-test entry: exercises the full lifecycle on a cheap single-GPU
    # spot instance (g6.2xlarge / g5.2xlarge) for well under a dollar.
    "qwen2.5-1.5b":        {"hf_model_id": "Qwen/Qwen2.5-1.5B-Instruct", "tp": 1, "max_model_len": 16384},
    "llama-31-405b":       {"hf_model_id": "RedHatAI/Meta-Llama-3.1-405B-Instruct-FP8-dynamic", "tp": 8, "max_model_len": 32768},
    "nemotron-ultra-253b": {"hf_model_id": "nvidia/Llama-3_1-Nemotron-Ultra-253B-v1-FP8", "tp": 8, "max_model_len": 32768,
                            "vllm_args": ["--trust-remote-code", "--reasoning-parser", "deepseek_r1"],
                            "system_prompt": "detailed thinking on"},
    "llama4-maverick":     {"hf_model_id": "RedHatAI/Llama-4-Maverick-17B-128E-Instruct-FP8", "tp": 8, "max_model_len": 32768},
}


# ---------------------------------------------------------------------------
# Local state file (instance identity + secrets); shared by both paths
# ---------------------------------------------------------------------------


def _state_path() -> Path:
    return Path(EC2_STATE_FILE)


def _load_state() -> Optional[Dict[str, Any]]:
    """Returns the saved instance state, or None when absent/corrupt."""
    try:
        return json.loads(_state_path().read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _save_state(state: Dict[str, Any]) -> None:
    path = _state_path()
    path.write_text(json.dumps(state, indent=2) + "\n")
    path.chmod(0o600)  # holds the control token and the vLLM api key


def _clear_state() -> None:
    try:
        _state_path().unlink()
    except OSError:
        pass


def _require_state() -> Dict[str, Any]:
    state = _load_state()
    if state is None:
        raise RuntimeError(
            f"No EC2 instance state found at {_state_path().resolve()}; "
            "run provision_spot_instance() first."
        )
    return state


def _base_url() -> str:
    """The OpenAI-compatible base URL, resolved at call time.

    Unlike aws.py this cannot be an import-time constant: the instance's IP
    does not exist until provisioning. ``EC2_INFERENCE_BASE_URL`` overrides
    (tests / externally managed servers); otherwise the state file supplies it.
    """
    if EC2_INFERENCE_BASE_URL:
        return EC2_INFERENCE_BASE_URL.rstrip("/")
    return f"http://{_require_state()['public_ip']}:8000/v1"


def _api_key() -> str:
    if EC2_VLLM_API_KEY:
        return EC2_VLLM_API_KEY
    return _require_state()["vllm_api_key"]


# ---------------------------------------------------------------------------
# Inference path (requests only; no boto3)
# ---------------------------------------------------------------------------


def get_model_context_length(model: str) -> int:
    """Returns the served context window for a model.

    The deploy spec's ``max_model_len`` is exactly what vLLM was launched
    with, so it doubles as the soft post-hoc token guard; models without a
    spec fall back to ``EC2_CONTEXT_LENGTH``.
    """
    spec = EC2_DEPLOY_SPECS.get(model)
    if spec and "max_model_len" in spec:
        return spec["max_model_len"]
    return EC2_CONTEXT_LENGTH


def list_models() -> list[str]:
    """Lists model ids the instance's vLLM currently serves (normally one)."""
    response = requests.get(
        url=f"{_base_url()}/models",
        headers={"Authorization": f"Bearer {_api_key()}"},
        timeout=120,
    )
    response.raise_for_status()
    return [m["id"] for m in response.json().get("data", [])]


def _is_retryable_request_error(err: requests.exceptions.RequestException) -> bool:
    """
    Returns whether an inference request error should be retried.
    """
    if isinstance(err, requests.exceptions.HTTPError):
        response = err.response
        if response is None:
            return True

        return response.status_code == 429 or 500 <= response.status_code < 600

    return True


def _raise_endpoint_unreachable(err: Exception) -> NoReturn:
    """Raises an actionable error after repeated connection failures.

    Distinguishes (best-effort, via lazy boto3) the two common causes: the
    spot instance was interrupted/terminated, or the caller's public IP
    changed so the security group now blocks them. Must also work with no AWS
    credentials, so every boto3 problem degrades to the generic message.
    """
    state = _load_state()
    detail = "no state file; EC2_INFERENCE_BASE_URL override in use?"
    if state is not None:
        detail = f"instance {state.get('instance_id', '?')} state could not be checked"
        try:
            ec2 = _ec2_client(state.get("region", AWS_REGION))  # lazy boto3 inside
            reservations = ec2.describe_instances(InstanceIds=[state["instance_id"]])[
                "Reservations"
            ]
            instances = reservations[0]["Instances"] if reservations else []
            inst_state = instances[0]["State"]["Name"] if instances else "absent"
            if inst_state not in ("pending", "running"):
                raise RuntimeError(
                    f"EC2 spot instance {state['instance_id']} is {inst_state} -- likely a "
                    "spot interruption (or the idle watchdog fired). Re-run "
                    "provision_spot_instance() and re-run this section; results of "
                    "completed sections are already serialized."
                ) from err
            detail = f"instance {state['instance_id']} is {inst_state}"
        except RuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001 -- diagnosis only, never mask
            detail = f"instance-state check failed: {type(exc).__name__}: {exc}"
    raise RuntimeError(
        f"Inference endpoint unreachable after {EC2_MAX_CONNECTION_FAILURES} consecutive "
        f"connection failures ({detail}). If the instance is running, your public IP "
        "probably changed and the security group is blocking you: re-run "
        "provision_spot_instance() to re-authorize your current IP."
    ) from err


def query(
    prompt: str,
    model: str,
    seed: int,
    context_length: int = 0,
    extra_args: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[str]]:
    """
    Queries the model currently served by the experiment's EC2 instance.

    Parameters
    ----------
    prompt:
        The content posed to the LLM we expect an answer from.
    model:
        The model to evaluate (an ``EC2_DEPLOY_SPECS`` key; sent verbatim as
        the OpenAI ``model`` field since vLLM serves under that name).
    seed:
        Seed for LLM output.
    context_length:
        Context length of LLM model.
    extra_args:
        Extra args for `json=<slug>` of requests to get certain LLM behavior.

    Returns
    -------
    The model's output.
    """
    spec = EC2_DEPLOY_SPECS.get(model, {})
    # Spec-level system prompt (e.g. Nemotron's "detailed thinking on" CoT
    # toggle) is injected here so the notebook's user prompts stay identical
    # across archetypes.
    messages: List[Dict[str, str]] = []
    if spec.get("system_prompt"):
        messages.append({"role": "system", "content": spec["system_prompt"]})
    messages.append({"role": "user", "content": prompt})

    attempt: int = 0
    connection_failures: int = 0
    # Keep attempting to get a result until one is provisioned.
    while True:
        attempt += 1
        # Tries to get a non-error code response from the endpoint.
        try:
            response = requests.post(
                url=f"{_base_url()}/chat/completions",
                headers={
                    "Authorization": f"Bearer {_api_key()}",
                    "Content-Type": "application/json",
                },
                json=(
                    {
                        "model": model,
                        "messages": messages,
                        "seed": seed,
                    }
                    | (extra_args if extra_args else {})
                ),
                timeout=120,
            )
            # The server answered, so the instance is alive: only sustained
            # connection failures should count toward the unreachable verdict.
            connection_failures = 0

            if not response.ok:
                logging.info(response.text)

            response.raise_for_status()
            body = response.json()
            if EC2_INFO and EC2_INFO_RESPONSE:
                logging.info(body)

            msg = body["choices"][0]["message"]
            if msg["content"] is None:
                logging.warning("Body returned none value: \n" f"{body}")
                return "", None
            # vLLM's reasoning parsers surface chain-of-thought as
            # reasoning_content (reasoning kept as a fallback for other
            # OpenAI-compatible servers behind EC2_INFERENCE_BASE_URL).
            reasoning = msg.get("reasoning_content") or msg.get("reasoning")
            # Usage may be omitted by some servers; only guard when a token
            # count is reported.
            usage = body.get("usage") or {}
            tokens = usage.get("total_tokens")
            if tokens is not None and tokens > context_length:
                raise ValueError(f"Response:\n{body}\n was {tokens} > {context_length}")
            if EC2_INFO:
                logging.info(f"Response:\n{body}\n was {tokens} <= {context_length}")
            return msg["content"], reasoning

        # Attempts to retry exceptions if possible.
        except requests.exceptions.RequestException as err:
            if not _is_retryable_request_error(err):
                raise
            # A self-managed spot endpoint can vanish (interruption, watchdog,
            # caller-IP drift); unlike aws.py, cap connection-level failures
            # instead of retrying forever against a dead box.
            if not isinstance(err, requests.exceptions.HTTPError):
                connection_failures += 1
                if connection_failures >= EC2_MAX_CONNECTION_FAILURES:
                    _raise_endpoint_unreachable(err)
            logging.info(
                f"EC2 endpoint request failed on attempt {attempt}: {err}. "
                f"Retrying in {EC2_RETRY_BACKOFF_SECONDS} seconds."
            )
            time.sleep(EC2_RETRY_BACKOFF_SECONDS)


def evaluate(
    quiz: Quiz, model: str, seed: int, extra_args: Optional[Dict[str, Any]] = None
) -> Marks:
    """Evaluates a model given a sequence of quizzes."""
    ctx_len: int = get_model_context_length(model)
    max_workers: int = max(1, min(len(quiz), EC2_MAX_PARALLEL_REQUESTS))
    responses: list[Tuple[str, Optional[str]]] = Parallel(n_jobs=max_workers, prefer="threads")(
        delayed(query)(q.prompt, model, seed, ctx_len, extra_args=extra_args)
        for q in quiz
    )

    mark_list: list[Mark] = []
    q: QnA
    raw: str
    reasoning: Optional[str]
    for q, (raw, reasoning) in zip(quiz, responses):
        try:
            conditioned: Answer = q.condition(raw)
        except ValueError as e:
            if EC2_INFO:
                logging.info(e)
            mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw, reasoning=reasoning, score=None))
            continue

        part_correct, _ = q.score(conditioned)
        mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw, reasoning=reasoning, score=part_correct))

    return Marks(model=model, marks=tuple(mark_list))


# ---------------------------------------------------------------------------
# On-instance payloads (control agent, idle watchdog, cloud-init bootstrap)
# ---------------------------------------------------------------------------
# These run under Ubuntu 22.04's system python3 (3.10): keep them stdlib-only
# and 3.10-compatible. They are module constants (not rendered strings) so the
# offline tests can ast.parse() them directly.

# Control agent: the notebook's only way to drive the instance (no SSH, no SSM
# role). Bearer-authenticated HTTP on :9000; every authenticated request also
# feeds the idle watchdog by touching last_active. /serve launches docker
# asynchronously because a cold `docker run` may first pull the multi-GB vLLM
# image; progress is observable via /status instead of a long-blocking POST.
AGENT_PY: str = '''\
"""smolbench control agent: swaps the vLLM container on request."""
import hmac
import json
import os
import shlex
import subprocess
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Overridable so the repo's offline tests can run the agent unprivileged.
RUN_DIR = os.environ.get("SMOLBENCH_RUN_DIR", "/var/run/smolbench")
AGENT_PORT = int(os.environ.get("SMOLBENCH_AGENT_PORT", "9000"))
SERVE_LOG = os.path.join(RUN_DIR, "serve.log")
SYNC_LOG = os.path.join(RUN_DIR, "sync.log")
CONTROL_TOKEN = os.environ["CONTROL_TOKEN"]
VLLM_API_KEY = os.environ["VLLM_API_KEY"]
HF_TOKEN = os.environ.get("HF_TOKEN", "")
VLLM_IMAGE = os.environ["VLLM_IMAGE"]
# Optional S3 mirror of the HF hub cache (creds come from the instance
# profile; empty = HF-only, the pre-S3 behavior).
S3_CACHE = os.environ.get("S3_CACHE_URI", "").rstrip("/")
CACHE_HUB = os.environ.get("SMOLBENCH_CACHE_HUB", "/opt/hf-cache/hub")
SERVE_PROC = None  # the in-flight `docker run -d` launcher, if any
SYNC_PROC = None  # the in-flight cache upload, if any


def touch(name):
    path = os.path.join(RUN_DIR, name)
    with open(path, "a"):
        os.utime(path, None)


def docker(*args, timeout=120):
    return subprocess.run(["docker"] + list(args), capture_output=True, text=True, timeout=timeout)


def container_state():
    probe = docker("inspect", "-f", "{{.State.Status}}", "vllm")
    return probe.stdout.strip() if probe.returncode == 0 else "absent"


def vllm_healthy():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def tail(path, limit=8000):
    try:
        with open(path, "rb") as fh:
            return fh.read()[-limit:].decode("utf-8", "replace")
    except OSError:
        return ""


class Handler(BaseHTTPRequestHandler):
    def _reply(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authed(self):
        got = self.headers.get("Authorization", "")
        if not hmac.compare_digest(got, "Bearer " + CONTROL_TOKEN):
            self._reply(401, {"error": "bad token"})
            return False
        touch("last_active")
        return True

    def do_GET(self):
        if not self._authed():
            return
        if self.path != "/status":
            self._reply(404, {"error": "unknown path"})
            return
        logs = docker("logs", "--tail", "40", "vllm")
        self._reply(200, {
            "container": container_state(),
            "healthy": vllm_healthy(),
            "serve_rc": SERVE_PROC.poll() if SERVE_PROC is not None else None,
            "sync_rc": SYNC_PROC.poll() if SYNC_PROC is not None else None,
            "sync_started": SYNC_PROC is not None,
            "log_tail": (logs.stdout + logs.stderr)[-8000:],
            "serve_log_tail": tail(SERVE_LOG),
            "sync_log_tail": tail(SYNC_LOG, 2000),
        })

    def do_POST(self):
        if not self._authed():
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._reply(400, {"error": "bad json"})
            return
        if self.path == "/serve":
            self._serve(payload)
        elif self.path == "/sync-up":
            self._sync_up(payload)
        elif self.path == "/stop":
            docker("rm", "-f", "vllm")
            self._reply(200, {"ok": True})
        elif self.path == "/shutdown":
            # Reply first; the OS halt (=> spot termination) races the socket.
            self._reply(200, {"ok": True, "shutting_down": True})
            subprocess.Popen(["shutdown", "-h", "now"])
        else:
            self._reply(404, {"error": "unknown path"})

    def _serve(self, payload):
        global SERVE_PROC
        try:
            name = str(payload["served_model_name"])
            hf_id = str(payload["hf_model_id"])
            tp = int(payload.get("tp", 1))
            max_len = int(payload.get("max_model_len", 16384))
            vllm_args = [str(a) for a in payload.get("vllm_args", [])]
        except (KeyError, TypeError, ValueError) as exc:
            self._reply(400, {"error": "bad payload: %s" % (exc,)})
            return
        docker("rm", "-f", "vllm")
        touch("serve_started")  # opens the watchdog's startup-grace window
        cmd = [
            "docker", "run", "-d", "--name", "vllm",
            # --ipc=host is mandatory at tp>1: NCCL needs more shared memory
            # than docker's default 64 MB /dev/shm.
            "--gpus", "all", "--ipc=host",
            "-p", "8000:8000",
            # The HF cache outlives container swaps, so each checkpoint
            # downloads once per instance. vLLM's compile/CUDA-graph cache is
            # persisted alongside it, so RE-serving a model skips the
            # several-minute torch.compile step.
            "-v", "/opt/hf-cache:/root/.cache/huggingface",
            "-v", "/opt/hf-cache/vllm-cache:/root/.cache/vllm",
            "-e", "HF_TOKEN=" + HF_TOKEN,
            "-e", "HUGGING_FACE_HUB_TOKEN=" + HF_TOKEN,
            VLLM_IMAGE,
            "--model", hf_id,
            "--served-model-name", name,
            "--tensor-parallel-size", str(tp),
            "--max-model-len", str(max_len),
            "--api-key", VLLM_API_KEY,
        ] + vllm_args
        # Async: a cold `docker run -d` blocks minutes on the image pull;
        # /status reports serve_rc + serve_log_tail meanwhile. S3 mirror:
        # blobs/ holds weights once, snapshots/refs symlinks travel as a tiny
        # meta.tar (s3 sync follows symlinks -- mirroring snapshots/ directly
        # doubles every transfer). No meta.tar -> legacy whole-prefix sync,
        # and HF fills any remaining gap.
        script = ""
        if S3_CACHE:
            sub = "models--" + hf_id.replace("/", "--")
            s3p = shlex.quote(S3_CACHE + "/" + sub)
            loc = shlex.quote(CACHE_HUB + "/" + sub)
            script += (
                "mkdir -p %s\\n"
                "aws s3 sync --only-show-errors --exclude '*.incomplete' %s/blobs %s/blobs || true\\n"
                "T=$(mktemp)\\n"
                "if aws s3 cp --only-show-errors %s/meta.tar $T; then tar -xf $T -C %s; "
                "else aws s3 sync --only-show-errors --exclude '*.incomplete' %s %s || true; fi\\n"
                "rm -f $T\\n"
            ) % (loc, s3p, loc, s3p, loc, s3p, loc)
        script += shlex.join(cmd)
        log = open(SERVE_LOG, "wb")
        SERVE_PROC = subprocess.Popen(["bash", "-c", script], stdout=log, stderr=subprocess.STDOUT)
        self._reply(202, {"ok": True, "launching": name})

    def _sync_up(self, payload):
        """Uploads (part of) the hub cache to S3: blobs once + meta.tar.

        snapshots holding real >1M files (restored from the legacy doubled
        mirror) cannot be tarred sanely -> legacy whole-prefix sync instead.
        *.incomplete never travels (would confuse a later resume).
        """
        global SYNC_PROC
        if not S3_CACHE:
            self._reply(200, {"ok": True, "skipped": "S3_CACHE_URI not set"})
            return
        sub = str(payload.get("subdir", "")).strip("/")
        dirs = "%s/%s" % (CACHE_HUB, sub) if sub else "%s/models--*" % CACHE_HUB
        body = (
            "for d in %s; do [ -d $d ] || continue; n=$(basename $d); "
            "aws s3 sync --only-show-errors --exclude '*.incomplete' $d/blobs %s/$n/blobs; "
            "if find $d/snapshots -type f -size +1M 2>/dev/null | grep -q .; then "
            "aws s3 sync --only-show-errors --exclude '*.incomplete' --exclude 'blobs/*' $d %s/$n; "
            "else T=$(mktemp); tar -cf $T -C $d snapshots refs 2>/dev/null && "
            "aws s3 cp --only-show-errors $T %s/$n/meta.tar; rm -f $T; fi; done"
        ) % (dirs, S3_CACHE, S3_CACHE, S3_CACHE)
        log = open(SYNC_LOG, "ab")
        SYNC_PROC = subprocess.Popen(["bash", "-c", body], stdout=log, stderr=subprocess.STDOUT)
        self._reply(202, {"ok": True, "syncing": sub or "all"})

    def log_message(self, *args):
        pass  # systemd journals stdout; per-request noise is not useful


def main():
    os.makedirs(RUN_DIR, exist_ok=True)
    touch("last_active")
    ThreadingHTTPServer(("0.0.0.0", AGENT_PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
'''

# Idle watchdog: a long-running service that checks once a minute. It is a
# plain loop under Restart=always rather than a systemd timer ON PURPOSE --
# the obvious OnUnitActiveSec=60 + Type=oneshot pairing fires exactly once,
# because a oneshot unit never enters the "active" state the timer measures
# from (found live: the smoke instance's watchdog never re-armed). Activity =
#   (a) any authenticated control-agent request (the agent touches last_active),
#   (b) movement in vLLM's request-token counters, or requests in flight
#       (clients hit vLLM directly during evals, invisible to the agent), or
#   (c) a container that is up but not yet answering /metrics (weights still
#       downloading/loading), honored only within the startup grace window.
# vLLM's --api-key only guards /v1/*; /metrics and /health are keyless on
# localhost, and the security group closes the port to everyone else.
WATCHDOG_PY: str = '''\
"""smolbench idle watchdog: halts the instance after sustained inactivity."""
import os
import subprocess
import time
import urllib.request

# Overridable so the repo's offline tests can run the watchdog unprivileged.
RUN_DIR = os.environ.get("SMOLBENCH_RUN_DIR", "/var/run/smolbench")
IDLE_TIMEOUT_S = int(os.environ.get("IDLE_TIMEOUT_MIN", "30")) * 60
STARTUP_GRACE_S = int(os.environ.get("STARTUP_GRACE_MIN", "120")) * 60
CHECK_INTERVAL_S = 60


def path(name):
    return os.path.join(RUN_DIR, name)


def touch(name):
    target = path(name)
    with open(target, "a"):
        os.utime(target, None)


def mtime(name):
    try:
        return os.path.getmtime(path(name))
    except OSError:
        return None


def metrics_activity():
    """True/False = counters moved / are still; None = vLLM not answering."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/metrics", timeout=5) as resp:
            text = resp.read().decode("utf-8", "replace")
    except Exception:
        return None
    total = 0.0
    running = 0.0
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        if line.startswith("vllm:prompt_tokens_total") or line.startswith("vllm:generation_tokens_total"):
            try:
                total += float(line.rsplit(" ", 1)[1])
            except (ValueError, IndexError):
                pass
        elif line.startswith("vllm:num_requests_running"):
            try:
                running += float(line.rsplit(" ", 1)[1])
            except (ValueError, IndexError):
                pass
    snapshot = path("tokens_snapshot")
    previous = None
    try:
        with open(snapshot) as fh:
            previous = fh.read().strip()
    except OSError:
        pass
    current = repr(total)
    if previous != current:
        with open(snapshot, "w") as fh:
            fh.write(current)
        return True
    return running > 0


def container_running():
    probe = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", "vllm"],
        capture_output=True, text=True,
    )
    return probe.returncode == 0 and probe.stdout.strip() == "true"


def check_once():
    last = mtime("last_active")
    if last is None:
        touch("last_active")  # boot counts as the start of the idle clock
        return
    active = metrics_activity()
    if active:
        touch("last_active")
        return
    if active is None and container_running():
        # vLLM is up but not serving metrics yet: weights are downloading or
        # loading. Counts as activity only within the grace window so a wedged
        # download cannot keep the instance alive forever.
        started = mtime("serve_started")
        if started is not None and time.time() - started < STARTUP_GRACE_S:
            touch("last_active")
            return
    idle = time.time() - last
    if idle > IDLE_TIMEOUT_S:
        print("idle %ds > %ds; shutting down" % (idle, IDLE_TIMEOUT_S), flush=True)
        subprocess.Popen(["shutdown", "-h", "now"])


def main():
    os.makedirs(RUN_DIR, exist_ok=True)
    once = os.environ.get("SMOLBENCH_WATCHDOG_ONCE") == "1"  # test hook
    while True:
        try:
            check_once()
        except Exception as exc:
            # A transient failure (docker hiccup, fs error) must not kill the
            # safety net; log and keep watching.
            print("watchdog check failed: %r" % (exc,), flush=True)
        if once:
            return
        time.sleep(CHECK_INTERVAL_S)


if __name__ == "__main__":
    main()
'''

# Cloud-init bootstrap. @@PLACEHOLDER@@ markers are filled by
# _render_user_data via str.replace -- NOT str.format/f-strings, since the
# embedded bash and python are full of braces and dollar signs. The max-
# lifetime backstop is scheduled FIRST so the box self-halts even if a later
# bootstrap step fails. Heredocs are single-quoted (<<'EOF') so the embedded
# scripts land byte-exact.
USER_DATA_TEMPLATE: str = '''\
#!/bin/bash
set -euo pipefail
exec > /var/log/smolbench-bootstrap.log 2>&1
echo "smolbench bootstrap starting: $(date -u)"

# Absolute backstop before anything fallible: an OS halt terminates a
# one-time spot instance.
shutdown -h +@@MAX_LIFETIME_MIN@@ "smolbench max-lifetime backstop" || true

mkdir -p /opt/smolbench /opt/hf-cache /var/run/smolbench /etc/smolbench

# Model cache on instance-store NVMe (multi-GB/s; no instance store -> root
# volume, so size EC2_ROOT_VOLUME_GB for the checkpoints then). The DL AMI
# pre-assembles ALL NVMe into one LVM at /opt/dlami/nvme -- mkfs on a raw
# device then fails "in use" (bit a live p5): bind-mount it instead. The
# raw-device path is for AMIs that leave devices alone; by-id detection
# because lsblk MODEL renders underscores on some kernels (also bit a p5).
if mountpoint -q /opt/dlami/nvme; then
  mkdir -p /opt/dlami/nvme/smolbench-hf-cache
  mount --bind /opt/dlami/nvme/smolbench-hf-cache /opt/hf-cache
  echo "model cache bind-mounted on the AMI-managed instance store (/opt/dlami/nvme)"
else
  CACHE_DEV=$(ls /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage* 2>/dev/null | grep -v -- -part | head -1 || true)
  if [ -z "$CACHE_DEV" ]; then
    CACHE_DEV=$(lsblk -dno NAME,MODEL | tr '_' ' ' | grep -i "instance storage" | head -1 | awk '{print "/dev/"$1}' || true)
  fi
  if [ -n "$CACHE_DEV" ]; then
    echo "model cache on instance-store $CACHE_DEV"
    mkfs.ext4 -q -F "$CACHE_DEV" && mount -o noatime "$CACHE_DEV" /opt/hf-cache || echo "NVMe mount failed; cache stays on the root volume"
  else
    echo "no instance-store NVMe; model cache on the root volume"
  fi
fi
mkdir -p /opt/hf-cache/hub

# Parallelism for the S3 cache pulls/pushes (aws s3 sync).
aws configure set default.s3.max_concurrent_requests 64 || true

cat > /etc/smolbench/env <<'ENV_EOF'
CONTROL_TOKEN=@@CONTROL_TOKEN@@
VLLM_API_KEY=@@VLLM_API_KEY@@
HF_TOKEN=@@HF_TOKEN@@
VLLM_IMAGE=@@VLLM_IMAGE@@
S3_CACHE_URI=@@S3_CACHE_URI@@
IDLE_TIMEOUT_MIN=@@IDLE_TIMEOUT_MIN@@
STARTUP_GRACE_MIN=@@STARTUP_GRACE_MIN@@
ENV_EOF
chmod 600 /etc/smolbench/env

cat > /opt/smolbench/agent.py <<'AGENT_EOF'
@@AGENT_PY@@
AGENT_EOF

cat > /opt/smolbench/watchdog.py <<'WATCHDOG_EOF'
@@WATCHDOG_PY@@
WATCHDOG_EOF

# The watchdog is a looping service, NOT a timer: OnUnitActiveSec never
# re-arms against a Type=oneshot unit (it never enters the "active" state),
# so a timer-driven watchdog runs exactly once and the box never reaps itself.
cat > /etc/systemd/system/smolbench-watchdog.service <<'UNIT_EOF'
[Unit]
Description=smolbench idle watchdog
After=docker.service

[Service]
EnvironmentFile=/etc/smolbench/env
ExecStart=/usr/bin/python3 /opt/smolbench/watchdog.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT_EOF

cat > /etc/systemd/system/smolbench-agent.service <<'UNIT_EOF'
[Unit]
Description=smolbench model-switcher agent
After=network-online.target docker.service
Wants=network-online.target

[Service]
EnvironmentFile=/etc/smolbench/env
ExecStart=/usr/bin/python3 /opt/smolbench/agent.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT_EOF

systemctl daemon-reload
# Watchdog first: even if the agent fails, idle termination still works.
systemctl enable --now smolbench-watchdog.service
systemctl enable --now smolbench-agent.service

# Pre-pull the (multi-GB) vLLM image so the first /serve does not block on it.
. /etc/smolbench/env
docker pull "$VLLM_IMAGE" > /var/log/smolbench-pull.log 2>&1 &

echo "smolbench bootstrap done: $(date -u)"
'''


def _render_user_data(
    control_token: str,
    vllm_api_key: str,
    hf_token: str,
    idle_timeout_min: int,
    startup_grace_min: int,
    max_lifetime_min: int,
    image: str,
    s3_cache_uri: str = "",
) -> str:
    """Fills the user-data template; asserts it is valid and within limits."""
    for payload, delimiter in ((AGENT_PY, "AGENT_EOF"), (WATCHDOG_PY, "WATCHDOG_EOF")):
        # A heredoc terminates at its delimiter; the scripts must never
        # contain one as a line of their own.
        assert delimiter not in payload, f"{delimiter} must not appear in the embedded script"
    rendered = USER_DATA_TEMPLATE
    for marker, value in (
        ("@@MAX_LIFETIME_MIN@@", str(max_lifetime_min)),
        ("@@CONTROL_TOKEN@@", control_token),
        ("@@VLLM_API_KEY@@", vllm_api_key),
        ("@@HF_TOKEN@@", hf_token),
        ("@@VLLM_IMAGE@@", image),
        ("@@S3_CACHE_URI@@", s3_cache_uri),
        ("@@IDLE_TIMEOUT_MIN@@", str(idle_timeout_min)),
        ("@@STARTUP_GRACE_MIN@@", str(startup_grace_min)),
        ("@@AGENT_PY@@", AGENT_PY.rstrip("\n")),
        ("@@WATCHDOG_PY@@", WATCHDOG_PY.rstrip("\n")),
    ):
        rendered = rendered.replace(marker, value)
    assert "@@" not in rendered, "unsubstituted placeholder left in user-data"
    # EC2 caps user-data at 16 KB before base64 (boto3 encodes it for us).
    assert len(rendered.encode()) < 16384, f"user-data too large: {len(rendered.encode())} bytes"
    return rendered


# ---------------------------------------------------------------------------
# EC2 spot provisioning / lifecycle (lazy boto3; opt-in)
# ---------------------------------------------------------------------------
# boto3/botocore are imported inside these functions so the inference path
# stays dependency-free (see module docstring). Clients are created from a
# FRESH boto3 Session per operation -- not boto3.client(), whose process-wide
# default session caches credentials at first resolve, so a refreshed
# ~/.aws/credentials (IdP sessions here last ~12h) would otherwise keep
# raising RequestExpired until the kernel restarts.

# ClientError codes that mean "this pool cannot fill the request right now" --
# worth trying the next subnet/region -- as opposed to quota or genuine errors.
_CAPACITY_ERROR_CODES = frozenset(
    {
        "InsufficientInstanceCapacity",
        "SpotMaxPriceTooLow",
        "Unsupported",
        "UnfulfillableCapacity",
        "InsufficientFreeAddressesInSubnet",
    }
)


def _ec2_client(region: str):
    import boto3  # lazy: keep the inference path boto3-free

    return boto3.session.Session().client("ec2", region_name=region)


def _error_code(err: Exception) -> str:
    return getattr(err, "response", {}).get("Error", {}).get("Code", "")


def _my_public_ip() -> str:
    return requests.get("https://checkip.amazonaws.com", timeout=10).text.strip()


def _resolve_ami(region: str) -> Tuple[str, str]:
    """Returns (ami_id, root_device_name) for the region's latest DL Base GPU AMI."""
    import boto3

    ssm = boto3.session.Session().client("ssm", region_name=region)
    ami = ssm.get_parameter(Name=EC2_AMI_SSM_PARAM)["Parameter"]["Value"]
    image = _ec2_client(region).describe_images(ImageIds=[ami])["Images"][0]
    return ami, image["RootDeviceName"]


def _offers_instance_type(region: str, instance_type: str) -> bool:
    offers = _ec2_client(region).describe_instance_type_offerings(
        LocationType="region",
        Filters=[{"Name": "instance-type", "Values": [instance_type]}],
    )["InstanceTypeOfferings"]
    return bool(offers)


def _default_vpc_subnets(region: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """Returns (default vpc id, [(subnet_id, az), ...]) for the region."""
    ec2 = _ec2_client(region)
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
    if not vpcs:
        return None, []
    vpc_id = vpcs[0]["VpcId"]
    subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
    return vpc_id, sorted((s["SubnetId"], s["AvailabilityZone"]) for s in subnets)


def _authorize_ingress(region: str, group_id: str, ip: str) -> None:
    """Opens 8000 (vLLM) + 9000 (agent) to ip/32; tolerates existing rules."""
    from botocore.exceptions import ClientError

    ec2 = _ec2_client(region)
    for port in (8000, 9000):
        try:
            ec2.authorize_security_group_ingress(
                GroupId=group_id,
                IpPermissions=[
                    {
                        "IpProtocol": "tcp",
                        "FromPort": port,
                        "ToPort": port,
                        "IpRanges": [{"CidrIp": f"{ip}/32", "Description": "smolbench caller"}],
                    }
                ],
            )
        except ClientError as err:
            if _error_code(err) != "InvalidPermission.Duplicate":
                raise


def _ensure_security_group(region: str, vpc_id: str, ip: str) -> str:
    """Returns the experiment security group's id, creating it if absent."""
    from botocore.exceptions import ClientError

    ec2 = _ec2_client(region)
    groups = ec2.describe_security_groups(
        Filters=[
            {"Name": "group-name", "Values": [EC2_SECURITY_GROUP_NAME]},
            {"Name": "vpc-id", "Values": [vpc_id]},
        ]
    )["SecurityGroups"]
    if groups:
        group_id = groups[0]["GroupId"]
    else:
        try:
            group_id = ec2.create_security_group(
                GroupName=EC2_SECURITY_GROUP_NAME,
                Description="smolbench inference (vLLM + control agent), caller-IP scoped",
                VpcId=vpc_id,
            )["GroupId"]
        except ClientError as err:
            if _error_code(err) != "InvalidGroup.Duplicate":  # racing another run
                raise
            group_id = ec2.describe_security_groups(
                Filters=[
                    {"Name": "group-name", "Values": [EC2_SECURITY_GROUP_NAME]},
                    {"Name": "vpc-id", "Values": [vpc_id]},
                ]
            )["SecurityGroups"][0]["GroupId"]
    _authorize_ingress(region, group_id, ip)
    return group_id


def _ensure_bucket(bucket: str, region: str) -> None:
    """Creates the S3 cache bucket if absent (private, default settings)."""
    import boto3
    from botocore.exceptions import ClientError

    s3 = boto3.session.Session().client("s3", region_name=region)
    try:
        s3.head_bucket(Bucket=bucket)
        return
    except ClientError as err:
        code = _error_code(err)
        if code not in ("404", "NoSuchBucket"):
            # 403/301: the name exists in another account/region -- creating
            # would fail confusingly, so surface it.
            raise RuntimeError(
                f"S3 bucket {bucket!r} exists but is not accessible from this "
                f"account/region (HEAD -> {code}); pick another EC2_S3_MODEL_CACHE."
            ) from err
    kwargs: Dict[str, Any] = {"Bucket": bucket}
    if region != "us-east-1":  # us-east-1 rejects an explicit LocationConstraint
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**kwargs)
    logging.info(f"_ensure_bucket: created s3://{bucket} in {region}")


def _ensure_instance_profile(bucket: str) -> str:
    """Returns the instance-profile name for the model cache, creating it if absent.

    The role grants (a) read/write scoped to the cache bucket and (b) SSM core,
    which doubles as the break-glass shell for a box that has no SSH key.
    """
    import json as _json

    import boto3
    from botocore.exceptions import ClientError

    iam = boto3.session.Session().client("iam")
    name = EC2_INSTANCE_ROLE_NAME
    trust = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    created = False
    try:
        iam.create_role(RoleName=name, AssumeRolePolicyDocument=_json.dumps(trust))
        created = True
    except ClientError as err:
        if _error_code(err) != "EntityAlreadyExists":
            raise
    # put_role_policy overwrites idempotently, so the grant tracks the bucket.
    iam.put_role_policy(
        RoleName=name,
        PolicyName="smolbench-s3-model-cache",
        PolicyDocument=_json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:ListBucket"],
                        "Resource": f"arn:aws:s3:::{bucket}",
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["s3:GetObject", "s3:PutObject"],
                        "Resource": f"arn:aws:s3:::{bucket}/*",
                    },
                ],
            }
        ),
    )
    iam.attach_role_policy(
        RoleName=name,
        PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    )
    try:
        iam.create_instance_profile(InstanceProfileName=name)
        created = True
    except ClientError as err:
        if _error_code(err) != "EntityAlreadyExists":
            raise
    try:
        iam.add_role_to_instance_profile(InstanceProfileName=name, RoleName=name)
    except ClientError as err:
        if _error_code(err) != "LimitExceeded":  # role already attached
            raise
    if created:
        time.sleep(12)  # let IAM propagate before RunInstances references it
    return name


def _find_tagged_instance() -> Optional[Tuple[str, Dict[str, Any]]]:
    """Finds a live instance tagged for this experiment across EC2_REGIONS."""
    for region in EC2_REGIONS:
        reservations = _ec2_client(region).describe_instances(
            Filters=[
                {"Name": "tag:smolbench:experiment", "Values": [EC2_EXPERIMENT_TAG]},
                {"Name": "instance-state-name", "Values": ["pending", "running"]},
            ]
        )["Reservations"]
        for reservation in reservations:
            for instance in reservation["Instances"]:
                return region, instance
    return None


def _describe_instance(region: str, instance_id: str) -> Optional[Dict[str, Any]]:
    from botocore.exceptions import ClientError

    try:
        reservations = _ec2_client(region).describe_instances(InstanceIds=[instance_id])[
            "Reservations"
        ]
    except ClientError as err:
        if _error_code(err) == "InvalidInstanceID.NotFound":
            return None
        raise
    for reservation in reservations:
        for instance in reservation["Instances"]:
            return instance
    return None


def _try_launch(region: str, kwargs: Dict[str, Any]) -> str:
    """run_instances with a fallback for spot rejecting the shutdown behavior.

    One-time spot instances terminate on OS shutdown regardless, so asking for
    InstanceInitiatedShutdownBehavior=terminate is belt-and-braces; some API
    paths reject the combination, in which case we simply retry without it.
    """
    from botocore.exceptions import ClientError

    ec2 = _ec2_client(region)
    try:
        response = ec2.run_instances(**kwargs)
    except ClientError as err:
        if (
            _error_code(err) in ("InvalidParameterCombination", "UnsupportedOperation")
            and "InstanceInitiatedShutdownBehavior" in kwargs
        ):
            retry_kwargs = {
                k: v for k, v in kwargs.items() if k != "InstanceInitiatedShutdownBehavior"
            }
            response = ec2.run_instances(**retry_kwargs)
        else:
            raise
    return response["Instances"][0]["InstanceId"]


def _wait_public_ip(region: str, instance_id: str, timeout_s: int = 300) -> str:
    deadline = time.time() + timeout_s
    while True:
        instance = _describe_instance(region, instance_id)
        state = (instance or {}).get("State", {}).get("Name", "absent")
        if state in ("shutting-down", "terminated", "absent"):
            raise RuntimeError(
                f"instance {instance_id} went {state} right after launch "
                "(spot reclaimed?); re-run provision_spot_instance()."
            )
        ip = (instance or {}).get("PublicIpAddress")
        if ip:
            return ip
        if time.time() > deadline:
            raise TimeoutError(f"instance {instance_id} got no public IP in {timeout_s}s")
        time.sleep(5)


def _agent(
    state: Dict[str, Any], method: str, path: str, payload: Optional[Dict[str, Any]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """One authenticated control-agent call; raises with the body on failure."""
    response = requests.request(
        method,
        f"http://{state['public_ip']}:9000{path}",
        headers={"Authorization": f"Bearer {state['control_token']}"},
        json=payload,
        timeout=timeout,
    )
    if not response.ok:
        raise RuntimeError(f"agent {method} {path} -> {response.status_code}: {response.text[:2000]}")
    return response.json()


def _wait_agent(state: Dict[str, Any], timeout_min: int = EC2_PROVISION_TIMEOUT_MIN) -> None:
    """Waits for the control agent to answer after boot/reattach."""
    deadline = time.time() + timeout_min * 60
    polls = 0
    while True:
        try:
            _agent(state, "GET", "/status", timeout=5)
            logging.info(f"control agent up at {state['public_ip']}:9000")
            return
        except (requests.exceptions.RequestException, RuntimeError):
            pass
        polls += 1
        if polls % 6 == 0:  # every minute, make sure the box still exists
            try:
                instance = _describe_instance(state["region"], state["instance_id"])
                inst_state = (instance or {}).get("State", {}).get("Name", "absent")
                if inst_state not in ("pending", "running"):
                    raise RuntimeError(
                        f"instance {state['instance_id']} went {inst_state} while waiting "
                        "for its agent (spot reclaimed?); re-run provision_spot_instance()."
                    )
            except ImportError:
                pass
        if time.time() > deadline:
            raise TimeoutError(
                f"control agent at {state['public_ip']}:9000 not answering after "
                f"{timeout_min} min. Debug via the EC2 serial console / instance "
                "screenshot, or relaunch with EC2_KEY_NAME set for SSH; bootstrap "
                "logs to /var/log/smolbench-bootstrap.log on the instance."
            )
        time.sleep(10)


def provision_spot_instance(
    instance_types: Optional[Tuple[str, ...]] = None,
    regions: Optional[Tuple[str, ...]] = None,
    volume_gb: Optional[int] = None,
    idle_timeout_min: Optional[int] = None,
    max_lifetime_min: Optional[int] = None,
) -> Dict[str, Any]:
    """Provisions (or reattaches to) the experiment's EC2 spot instance.

    Idempotent: a live instance recorded in the state file is reused -- the
    security group is re-authorized for the caller's CURRENT public IP and the
    saved endpoint refreshed -- so re-running the notebook cell after a kernel
    restart is safe. Otherwise launches a fresh one-time spot instance,
    hunting capacity type-major across ``instance_types`` x ``regions`` x each
    region's default-VPC subnets (AZs).

    Returns the state dict (also persisted to ``EC2_STATE_FILE``): instance_id,
    region, public_ip, instance_type, control_token, vllm_api_key, ...
    """
    instance_types = tuple(instance_types or EC2_INSTANCE_TYPES)
    regions = tuple(regions or EC2_REGIONS)
    volume_gb = volume_gb or EC2_ROOT_VOLUME_GB
    idle_timeout_min = idle_timeout_min or EC2_IDLE_TIMEOUT_MIN
    max_lifetime_min = max_lifetime_min or EC2_MAX_LIFETIME_MIN

    from botocore.exceptions import ClientError

    my_ip = _my_public_ip()

    # 1) Reattach to the instance in the state file when it is still alive.
    state = _load_state()
    if state is not None:
        instance = _describe_instance(state["region"], state["instance_id"])
        inst_state = (instance or {}).get("State", {}).get("Name", "absent")
        if inst_state in ("pending", "running"):
            _authorize_ingress(state["region"], state["security_group_id"], my_ip)
            state["public_ip"] = instance.get("PublicIpAddress") or _wait_public_ip(
                state["region"], state["instance_id"]
            )
            _save_state(state)
            _wait_agent(state)
            logging.info(
                f"provision_spot_instance: reattached to {state['instance_id']} "
                f"({state['instance_type']} @ {state['region']}, {state['public_ip']})"
            )
            return state
        logging.info(
            f"provision_spot_instance: stale state ({state['instance_id']} is {inst_state}); relaunching."
        )
        _clear_state()

    # 2) A live tagged instance without a state file is unusable: its control
    #    token only existed in the lost file. Refuse to leak a second box.
    found = _find_tagged_instance()
    if found is not None:
        region, instance = found
        name = next(
            (t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), "?"
        )
        raise RuntimeError(
            f"Found live instance {instance['InstanceId']} (Name={name}, "
            f"{instance.get('InstanceType', '?')} @ {region}, launched "
            f"{instance.get('LaunchTime', '?')}) tagged "
            f"smolbench:experiment={EC2_EXPERIMENT_TAG}, but no local state file -- its "
            "control token is unrecoverable, so it cannot be reused. If it is someone "
            "else's run (or a test) wait for it to finish/self-terminate; otherwise run "
            "shutdown_instance() to terminate it, then provision again."
        )

    # 3) Fresh launch.
    control_token = secrets.token_urlsafe(32)
    vllm_api_key = secrets.token_urlsafe(32)
    hf_token = os.getenv("HF_TOKEN", "")
    # The token is baked into user-data at boot and CANNOT be injected later
    # (an empty one once rode into a live p5e whose gated meta-llama serves
    # then 401'd). The default EC2_DEPLOY_SPECS now use only UNGATED repos
    # (RedHatAI / NVIDIA / Qwen), so an empty token is fine -- but anyone
    # swapping a gated checkpoint into the specs must set HF_TOKEN BEFORE
    # provisioning. Conversely, a set-but-invalid token breaks even ungated
    # downloads (the hub rejects bad credentials outright), so leave it empty
    # unless it is real.
    if not hf_token:
        logging.warning(
            "HF_TOKEN is not set. The default deploy specs are all ungated, so "
            "this is fine -- but gated checkpoints added to EC2_DEPLOY_SPECS "
            "would fail to download, and the token cannot be injected after "
            "provisioning."
        )
    iam_profile: Optional[str] = None
    if EC2_S3_MODEL_CACHE:
        bucket = EC2_S3_MODEL_CACHE.split("://", 1)[1].split("/", 1)[0]
        _ensure_bucket(bucket, EC2_S3_CACHE_REGION)
        iam_profile = _ensure_instance_profile(bucket)
        logging.info(
            f"provision_spot_instance: S3 model cache at {EC2_S3_MODEL_CACHE} "
            f"(instance profile {iam_profile})"
        )
    user_data = _render_user_data(
        control_token=control_token,
        vllm_api_key=vllm_api_key,
        hf_token=hf_token,
        idle_timeout_min=idle_timeout_min,
        startup_grace_min=EC2_STARTUP_GRACE_MIN,
        max_lifetime_min=max_lifetime_min,
        image=EC2_VLLM_IMAGE,
        s3_cache_uri=EC2_S3_MODEL_CACHE,
    )

    region_info: Dict[str, Optional[Dict[str, Any]]] = {}  # cached per-region lookups
    attempts: List[str] = []
    for instance_type in instance_types:
        for region in regions:
            if region not in region_info:
                vpc_id, subnets = _default_vpc_subnets(region)
                if vpc_id is None or not subnets:
                    region_info[region] = None
                    attempts.append(f"{region}: no default VPC/subnets")
                    continue
                ami, root_device = _resolve_ami(region)
                group_id = _ensure_security_group(region, vpc_id, my_ip)
                region_info[region] = {
                    "subnets": subnets,
                    "ami": ami,
                    "root_device": root_device,
                    "group_id": group_id,
                }
            info = region_info[region]
            if info is None:
                continue
            if not _offers_instance_type(region, instance_type):
                attempts.append(f"{instance_type} @ {region}: not offered")
                continue
            for subnet_id, az in info["subnets"]:
                kwargs: Dict[str, Any] = {
                    "ImageId": info["ami"],
                    "InstanceType": instance_type,
                    "MinCount": 1,
                    "MaxCount": 1,
                    "InstanceMarketOptions": {
                        "MarketType": "spot",
                        "SpotOptions": {
                            "SpotInstanceType": "one-time",
                            "InstanceInterruptionBehavior": "terminate",
                        },
                    },
                    "InstanceInitiatedShutdownBehavior": "terminate",
                    "NetworkInterfaces": [
                        {
                            "DeviceIndex": 0,
                            "SubnetId": subnet_id,
                            "Groups": [info["group_id"]],
                            "AssociatePublicIpAddress": True,
                            "DeleteOnTermination": True,
                        }
                    ],
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": info["root_device"],
                            "Ebs": {
                                "VolumeSize": volume_gb,
                                "VolumeType": "gp3",
                                "Throughput": EC2_ROOT_VOLUME_THROUGHPUT,
                                "Iops": EC2_ROOT_VOLUME_IOPS,
                                "DeleteOnTermination": True,
                            },
                        }
                    ],
                    "TagSpecifications": [
                        {
                            "ResourceType": "instance",
                            "Tags": [
                                {"Key": "smolbench:experiment", "Value": EC2_EXPERIMENT_TAG},
                                {"Key": "Name", "Value": f"smolbench-{EC2_EXPERIMENT_TAG}"},
                            ],
                        }
                    ],
                    "UserData": user_data,
                }
                if EC2_KEY_NAME:
                    kwargs["KeyName"] = EC2_KEY_NAME
                if iam_profile:
                    kwargs["IamInstanceProfile"] = {"Name": iam_profile}
                try:
                    logging.info(f"provision_spot_instance: trying {instance_type} in {az} ...")
                    instance_id = _try_launch(region, kwargs)
                except ClientError as err:
                    code = _error_code(err)
                    attempts.append(f"{instance_type} @ {az}: {code}")
                    if code == "MaxSpotInstanceCountExceeded":
                        # Per-region spot quota: no AZ in this region can help.
                        logging.info(f"{region}: spot quota exhausted for {instance_type}; skipping region")
                        break
                    if code in _CAPACITY_ERROR_CODES:
                        continue
                    raise

                public_ip = _wait_public_ip(region, instance_id)
                state = {
                    "instance_id": instance_id,
                    "region": region,
                    "availability_zone": az,
                    "instance_type": instance_type,
                    "public_ip": public_ip,
                    "security_group_id": info["group_id"],
                    "control_token": control_token,
                    "vllm_api_key": vllm_api_key,
                    "idle_timeout_min": idle_timeout_min,
                    "s3_cache": EC2_S3_MODEL_CACHE,
                    "launched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                _save_state(state)
                logging.info(
                    f"provision_spot_instance: launched {instance_id} "
                    f"({instance_type} @ {az}, {public_ip}); waiting for its agent ..."
                )
                _wait_agent(state)
                return state

    raise RuntimeError(
        "No spot capacity for any (instance type, region) combination:\n  "
        + "\n  ".join(attempts)
        + "\nWiden EC2_INSTANCE_TYPES/EC2_REGIONS or retry later."
    )


def _wait_model_ready(
    state: Dict[str, Any], model: str, timeout_min: int = EC2_SERVE_TIMEOUT_MIN
) -> None:
    """Polls the agent until vLLM answers /health for ``model``.

    First-time serves are dominated by the checkpoint download (hundreds of
    GB for the big FP8 models); the HF cache makes later swaps minutes.
    """
    deadline = time.time() + timeout_min * 60
    while True:
        status = _agent(state, "GET", "/status", timeout=30)
        if status.get("healthy"):
            return
        container = status.get("container")
        serve_rc = status.get("serve_rc")
        if container in ("exited", "dead"):
            raise RuntimeError(
                f"vLLM container for {model!r} exited during startup; docker logs tail:\n"
                f"{status.get('log_tail', '')}"
            )
        if container == "absent" and serve_rc not in (None, 0):
            raise RuntimeError(
                f"docker run for {model!r} failed (rc={serve_rc}); launcher output:\n"
                f"{status.get('serve_log_tail', '')}"
            )
        if time.time() > deadline:
            raise TimeoutError(
                f"{model!r} not healthy after {timeout_min} min "
                f"(container={container}); docker logs tail:\n{status.get('log_tail', '')}"
            )
        time.sleep(15)


@contextlib.contextmanager
def serve_model(model: str, timeout_min: Optional[int] = None, force: bool = False):
    """Points the provisioned instance's vLLM at ``model`` for a ``with`` body.

    Swaps the serving container (the previous model's container is removed),
    waits until the OpenAI endpoint is healthy and serving ``model``, and
    yields. Idempotent: when the instance is ALREADY healthy and serving
    ``model`` the swap is skipped entirely (pass ``force=True`` for a fresh
    container), so re-running a section cell after an interruption costs
    seconds, not a reload. Exit tears NOTHING down -- the instance stays up
    for the next section, and the idle watchdog covers the case where there
    is none::

        with serve_model(DENSE_MODEL):
            decode_intens_eval = evaluate(intens_quiz, DENSE_MODEL, SEED)
    """
    spec = EC2_DEPLOY_SPECS.get(model)
    if spec is None:
        raise KeyError(
            f"No EC2_DEPLOY_SPECS entry for model {model!r}; "
            "add one with hf_model_id / tp / max_model_len."
        )
    state = _require_state()
    if not force:
        # Decide BEFORE yielding: the yield must sit outside this try, or an
        # exception raised by the with-body would be swallowed here and the
        # generator would fall through to a second serve/yield.
        try:
            already_serving = bool(
                _agent(state, "GET", "/status", timeout=15).get("healthy")
            ) and list_models() == [model]
        except (requests.exceptions.RequestException, RuntimeError):
            already_serving = False
        if already_serving:
            logging.info(f"serve_model: {model!r} already serving; skipping the swap.")
            yield model
            return
    logging.info(f"serve_model: requesting {model!r} ({spec['hf_model_id']}) ...")
    _agent(
        state,
        "POST",
        "/serve",
        {
            "served_model_name": model,
            "hf_model_id": spec["hf_model_id"],
            "tp": spec.get("tp", 1),
            "max_model_len": spec.get("max_model_len", EC2_CONTEXT_LENGTH),
            # HF_TOKEN is deliberately NOT in this payload: it was baked into
            # the instance at provision time, so it never crosses plain HTTP.
            "vllm_args": list(spec.get("vllm_args", [])),
        },
    )
    _wait_model_ready(state, model, timeout_min or EC2_SERVE_TIMEOUT_MIN)
    served = list_models()
    if model not in served:
        raise RuntimeError(
            f"instance is healthy but serves {served}, not {model!r}; "
            "did another process swap the model?"
        )
    logging.info(f"serve_model: {model!r} is up at {_base_url()}")
    if state.get("s3_cache"):
        # The weights are complete on disk: refresh the S3 mirror in the
        # background (a fast no-op when S3 already has them) so the next
        # instance pulls from S3 instead of HF. Best-effort by design.
        try:
            _agent(
                state,
                "POST",
                "/sync-up",
                {"subdir": "models--" + spec["hf_model_id"].replace("/", "--")},
            )
            logging.info(f"serve_model: background S3 cache upload kicked off for {model!r}")
        except Exception as exc:  # noqa: BLE001
            logging.info(f"serve_model: S3 cache upload skipped: {exc}")
    try:
        yield model
    finally:
        # Intentionally no teardown: the next archetype swaps the container,
        # and the on-instance watchdog handles abandonment.
        logging.info(f"serve_model: leaving {model!r} serving (no teardown).")


def agent_status() -> Dict[str, Any]:
    """The control agent's view: container state, health, recent docker logs."""
    return _agent(_require_state(), "GET", "/status")


def stop_model() -> None:
    """Removes the serving container (without touching the instance)."""
    _agent(_require_state(), "POST", "/stop")


def shutdown_instance(wait: bool = True) -> None:
    """Gracefully terminates the experiment's instance and clears local state.

    Resolves the target from the state file, falling back to the
    ``smolbench:experiment`` tag (which also recovers from a lost state file).
    Asks the agent for an OS-level shutdown first (graceful for docker), then
    authoritatively calls TerminateInstances -- the instance, its EBS volume
    (DeleteOnTermination), and any served model die with it. The security
    group is intentionally left behind for reuse: it is free, and EC2 will not
    delete it while the instance's network interface lingers anyway.
    """
    state = _load_state()
    region: Optional[str] = None
    instance_id: Optional[str] = None
    if state is not None:
        region, instance_id = state["region"], state["instance_id"]
        if state.get("s3_cache"):
            try:  # warn when a cache upload would be cut short by the halt
                status = _agent(state, "GET", "/status", timeout=10)
                if status.get("sync_started") and status.get("sync_rc") is None:
                    logging.warning(
                        "shutdown_instance: an S3 cache upload is still in flight and "
                        "will be cut short; the next instance re-downloads whatever "
                        "is missing (wait and re-run this cell to let it finish)."
                    )
            except Exception:  # noqa: BLE001
                pass
        try:  # best-effort graceful halt; termination below is authoritative
            _agent(state, "POST", "/shutdown", timeout=10)
        except Exception as exc:  # noqa: BLE001
            logging.info(f"shutdown_instance: graceful shutdown skipped: {exc}")
    else:
        found = _find_tagged_instance()
        if found is not None:
            region, instance = found
            instance_id = instance["InstanceId"]

    if instance_id is None:
        logging.info("shutdown_instance: nothing to shut down.")
        _clear_state()
        return

    from botocore.exceptions import ClientError

    ec2 = _ec2_client(region)
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
    except ClientError as err:
        # Terminated instances age out of the EC2 API entirely; "not found"
        # means the job is already done (e.g. the watchdog beat us to it).
        if _error_code(err) != "InvalidInstanceID.NotFound":
            raise
        logging.info(f"shutdown_instance: {instance_id} already gone.")
        _clear_state()
        return
    logging.info(f"shutdown_instance: terminating {instance_id} ({region}) ...")
    if wait:
        _ec2_client(region).get_waiter("instance_terminated").wait(InstanceIds=[instance_id])
        logging.info(f"shutdown_instance: {instance_id} terminated.")
    _clear_state()
