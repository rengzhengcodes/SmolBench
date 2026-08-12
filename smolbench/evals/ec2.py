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
state file (``EC2_STATE_FILE``, by default at the repo root regardless of the
caller's cwd) and tags it ``smolbench:experiment``, so re-running the cell (or
restarting the kernel) reattaches to a live instance instead of launching a
second one. Even with the state file lost entirely, it rebuilds the state from
the tagged instance's user-data rather than stranding the box. ``serve_model`` exits WITHOUT tearing
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

Env-read timing: the PROVISIONING constants above this docstring (AWS_REGION,
EC2_INSTANCE_TYPES, EC2_VLLM_IMAGE, EC2_EXPERIMENT_TAG, EC2_S3_MODEL_CACHE /
EC2_S3_CACHE_REGION, and the other EC2_* module attributes near the top of
this file) are captured at IMPORT time -- set them before the first ``import
smolbench.evals.ec2`` (e.g. in keys.env, loaded before the notebook's imports
run), not right before calling provision_spot_instance(). This is deliberate:
notebooks bind them as ordinary module attributes (``ec2.EC2_EXPERIMENT_TAG``
etc.) that a call-time getter would break. The exception is the INFERENCE-path
knobs -- EC2_INFERENCE_BASE_URL, EC2_VLLM_API_KEY, EC2_STATE_FILE (plus
HF_TOKEN, which was never a module constant) -- which genuinely ARE read at
call time (inside _base_url/_api_key/_connection/_state_path/
provision_spot_instance respectively), so those may be set any time before
the relevant call.

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

from smolbench.evals import _aws
from smolbench.evals._aws import DeploySpec
from smolbench.evals.openai_compat import ChatClient, metadata_get
from smolbench.evals.payloads import render_user_data

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
# Fixed (NOT env-configurable, unlike the EC2_* knobs around them) ports for
# the two on-instance HTTP planes -- see the module docstring's "Security
# model" section for what each guards. Kept as plain constants rather than
# EC2_*-style os.getenv knobs because changing either requires coordinated
# changes beyond just this client (the security group ingress rule, the
# payload scripts' docker port-publish/probe URLs, and vLLM's own listen
# port), so a would-be override belongs in code, not a stray env var.
EC2_VLLM_PORT: int = 8000
EC2_AGENT_PORT: int = 9000
# Value of the ``smolbench:experiment`` tag used to find/reattach/terminate
# this experiment's instance. The "periodic-induction" default is specific to
# THIS experiment; other experiments sharing this module (e.g. chromatic) set
# EC2_EXPERIMENT_TAG in their own env BEFORE the first `import
# smolbench.evals.ec2` -- it is an import-time capture (see "Env-read timing"
# in the module docstring), so setting it later has no effect.
EC2_EXPERIMENT_TAG: str = os.getenv("EC2_EXPERIMENT_TAG", "periodic-induction")
# Anchored to the repo root via this module's own location, NOT the cwd:
# notebook kernels and scripts run with arbitrary cwds (temp dirs included),
# and a cwd-relative default once stranded a live instance's state where no
# later session could find it. Contains the control token and vLLM key ->
# gitignored. The EC2_STATE_FILE env override is read at CALL time (in
# _state_path), so notebooks may set it any time before the first
# provision/query -- there is no import-order trap.
_DEFAULT_STATE_FILE: Path = Path(__file__).resolve().parents[2] / ".ec2_state.json"
EC2_IDLE_TIMEOUT_MIN: int = int(os.getenv("EC2_IDLE_TIMEOUT_MIN", "30"))
# Serve timeout and the watchdog's loading-counts-as-active grace must cover a
# COLD checkpoint pull from HF: a ~410 GB download proved that 90/120 min are
# too tight (a live 405B serve outran both). With the S3 cache warm these are
# minutes, but the first-ever pull sets the bound.
# INVARIANT: the watchdog payload's own STARTUP_GRACE_MIN env fallback
# (payloads/watchdog.py.txt; used only if the env var somehow fails to
# propagate to the instance) must match this default -- keep both at "180"
# if either changes.
EC2_STARTUP_GRACE_MIN: int = int(os.getenv("EC2_STARTUP_GRACE_MIN", "180"))
EC2_MAX_LIFETIME_MIN: int = int(os.getenv("EC2_MAX_LIFETIME_MIN", "1440"))
EC2_PROVISION_TIMEOUT_MIN: int = int(os.getenv("EC2_PROVISION_TIMEOUT_MIN", "15"))
EC2_SERVE_TIMEOUT_MIN: int = int(os.getenv("EC2_SERVE_TIMEOUT_MIN", "180"))
# Optional EC2 key pair name for SSH debugging; empty = no SSH (the default --
# boot problems are then visible only via the serial console/screenshot).
EC2_KEY_NAME: str = os.getenv("EC2_KEY_NAME", "")
# evaluate()'s default fan-out is the EC2_MAX_PARALLEL_REQUESTS env var
# (default 8), read at call time by the shared ChatClient.
# Per-request inference read timeout. Long CoT generations (max_completion_tokens
# over big prompts) can exceed the old hardcoded 120 s; raise the default and let
# callers override per eval so long chains finish on attempt 1 (deterministic),
# instead of timing out and surviving only via the retry lottery -- which censors
# the CoT-length distribution from the top.
EC2_REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("EC2_REQUEST_TIMEOUT_SECONDS", "600"))
# Connect timeout, kept SHORT and SEPARATE from the (long) read timeout above.
# requests treats a scalar ``timeout`` as both connect AND read, so a generous
# read timeout for long CoT generations would also make a dead/unreachable box
# (spot reclaim, IP drift) blackhole each connect for the full read timeout
# before retrying -- 10 attempts then turns into hours of hanging. A short
# connect timeout fails fast so the connection-failure cap trips in minutes and
# raises the actionable "endpoint unreachable" error, while a genuinely slow
# generation still gets the full read budget.
EC2_CONNECT_TIMEOUT_SECONDS: float = float(os.getenv("EC2_CONNECT_TIMEOUT_SECONDS", "10"))
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
# EC2_INFERENCE_BASE_URL / EC2_VLLM_API_KEY env overrides bypass the state
# file and point the inference path at any OpenAI-compatible server (used by
# tests/test_openai_compat.py's local stub server). They are read at call
# time in _base_url/_api_key/_connection, not here. EC2_INFO /
# EC2_INFO_RESPONSE (verbose logging) are likewise read at call time by the
# shared ChatClient.

# Per-model deployment spec. The dict key is simultaneously (a) the ``model``
# argument the notebook passes to query()/evaluate() and (b) vLLM's
# ``--served-model-name``, so the OpenAI request body carries it verbatim.
# Keys: hf_model_id, tp (tensor parallelism), max_model_len (also the soft
# context guard), optional vllm_args (extra CLI flags), optional system_prompt
# (prepended to every request for that model).
#
# --- Family-ladder scaling study roster (2026-08-11) ------------------------
# 21 models = 7 families x 3 rungs (smallest / geometric-middle / largest
# counted rung of each family's ladder), one EC2 instance per model. Serving
# facts verified against each repo's shipped config.json + the upstream vLLM
# main registry on 2026-08-11; every architecture below is in-tree upstream, so
# NO --trust-remote-code anywhere. All repos UNGATED (anonymous HF API checks,
# 2026-08-10/11). Every entry serves at a uniform max_model_len=131072 -- the
# smallest native window on the roster is exactly 131072 (gemma-4-E2B,
# GLM-4.5-Air, EXAONE-4.0-32B), so nothing is down-capped below native, and a
# scaling study cannot let context vary with the vendor's YaRN generosity.
# --enable-prefix-caching everywhere: each induction quiz reuses one long
# prompt prefix across its 9 questions, each Lean theorem reuses its context
# block across 4 rungs.
#
# The whole roster needs EC2_VLLM_IMAGE=vllm/vllm-openai:nightly (the 2026
# architectures postdate every cut release; only Qwen3.5 support is confirmed
# in a tagged release, v0.26.0).
#
# Instance tiers (chosen per weights + 128k-KV arithmetic; the fleet
# supervisor maps these to EC2_INSTANCE_TYPES per lane):
#   tier A g6e.4xlarge  (1x L40S 48 GB):  nano-4b, gemma e2b/12b, ministral-3b
#   tier B g6e.12xlarge (4x L40S 192 GB): qwen 27b, nano-30b, gemma-31b,
#                                         glm-4.7-flash, ministral 8b/14b,
#                                         exaone 32b/33b
#   tier C p5.48xlarge  (8x H100 640 GB): qwen 122b/397b-fp8, super-120b,
#                                         glm-4.5-air, k-exaone-236b,
#                                         deepseek-v4-flash
#   tier D p5e.48xlarge (8x H200 1128 GB): glm-4.7, deepseek-v3.1, deepseek-v4-pro
#
# tp notes: GLM-4.7-Flash has 20 attention heads -> tp must divide 20, so it
# runs tp=4 on tier B (a p5 would idle half its GPUs). Nemotron-Nano-30B has
# only 2 KV heads; vLLM replicates KV heads when tp > n_kv. All other tp
# choices divide the head counts exactly (verified from each config.json).
#
# Reasoning wiring (CoT is ON for every model in this study; the per-request
# chat_template_kwargs toggles ride in extra_args from the study drivers --
# see notebooks/induction/run_study.py COT_ARGS):
#   * Qwen3.5 / Gemma-4: server-side --reasoning-parser (qwen3 / gemma4) splits
#     the think block into reasoning_content. Gemma-4's template defaults
#     enable_thinking to FALSE, so the driver MUST pass it true; its think tags
#     are Gemma-specific, so the client-side "</think>" fallback would NOT
#     catch them -- the parser is load-bearing there.
#   * Nemotron-3: enable_thinking defaults on in the shipped template; the
#     plain-text <think> block is split CLIENT-side in query() (same proven
#     path the periodic_moe study served Super-120B with; a nemotron_v3 parser
#     exists on vLLM main but has never been launched from this repo, so the
#     proven config wins).
#   * GLM-4.x: thinking defaults ON; glm47/glm45 parsers split it server-side.
#   * Ministral-3 Reasoning: the [THINK] protocol lives ONLY in the shipped
#     template's default_system_message, which the template injects ONLY when
#     no system message is supplied. The Lean eval always supplies one, which
#     would silently disable thinking. Fix: inject that exact default text as
#     the provider system_prompt below -- ChatClient puts it FIRST, the
#     template renders each system message as its own [SYSTEM_PROMPT] block,
#     so induction stays byte-identical to out-of-box behavior and Lean gets
#     think-protocol + its own instructions. Do NOT switch these entries to
#     --tokenizer-mode mistral: that bypasses the Jinja template entirely.
#   * EXAONE: no vLLM reasoning parser exists for it; plain-text <think> split
#     client-side. EXAONE-4.0-32B defaults enable_thinking OFF -> driver must
#     pass it true. Only 4.5-33B is a multimodal wrapper (hence its
#     --language-model-only).
#   * DeepSeek V4: the repos ship NO chat template (404 + no tokenizer_config
#     key, verified 2026-08-11) -- the toggle lives in the repo's Python
#     encoding_dsv4.py. vLLM accepts a LITERAL template string via
#     --chat-template, so DSV4_CHAT_TEMPLATE below reproduces the shipped
#     encoding for the [system?, user] + generation-prompt shapes this repo
#     sends (byte-equality pinned by tests/test_dsv4_chat_template.py against
#     the vendored encoding module). chat_template_kwargs {"thinking": true}
#     drives both the template branch and vLLM's deepseek_v4 parser, whose
#     initial state accepts the prompt-final <think>. DeepSeek-V3.1 DOES ship
#     its template (thinking kwarg) -- no override there.
DSV4_CHAT_TEMPLATE: str = (
    "<｜begin▁of▁sentence｜>"
    "{%- for m in messages -%}"
    "{%- if m['role'] == 'system' -%}{{ m['content'] }}"
    "{%- elif m['role'] == 'user' -%}{{ '<｜User｜>' + m['content'] }}"
    "{%- endif -%}"
    "{%- endfor -%}"
    "{%- if add_generation_prompt -%}<｜Assistant｜>"
    "{%- if thinking is not defined or thinking -%}<think>{%- else -%}</think>{%- endif -%}"
    "{%- endif -%}"
)

# The Ministral-3 Reasoning template's default_system_message, verbatim (md5 of
# the shipped chat_template.jinja: f9ce03df8c692f42b2aeb78024e29f4f, identical
# across the 3B/8B/14B rungs; fetched 2026-08-11). See the Ministral note above.
MINISTRAL_THINK_SYSTEM: str = (
    "# HOW YOU SHOULD THINK AND ANSWER\n\n"
    "First draft your thinking process (inner monologue) until you arrive at a "
    "response. Format your response using Markdown, and use LaTeX for any "
    "mathematical equations. Write both your thoughts and the response in the "
    "same language as the input.\n\n"
    "Your thinking process must follow the template below:[THINK]Your thoughts "
    "or/and draft, like working through an exercise on scratch paper. Be as "
    "casual and as long as you want until you are confident to generate the "
    "response to the user.[/THINK]Here, provide a self-contained response."
)

EC2_DEPLOY_SPECS: Dict[str, DeploySpec] = {
    # Small smoke-test entry: exercises the full lifecycle on a cheap single-GPU
    # spot instance (g6.2xlarge / g5.2xlarge) for well under a dollar. 32768 =
    # the checkpoint's native window; the family-ladder canary pushes the real
    # ~14k-token extens quiz through it, which the old 16384 cap missed by one
    # token (live 400, 2026-08-11).
    "qwen2.5-1.5b":        {"hf_model_id": "Qwen/Qwen2.5-1.5B-Instruct", "tp": 1, "max_model_len": 32768},
    # -- Qwen3.5 (Alibaba, CN): 27B dense / 122B-A10B / 397B-A17B (official FP8) --
    "qwen3.5-27b":       {"hf_model_id": "Qwen/Qwen3.5-27B", "tp": 4, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "qwen3", "--language-model-only", "--enable-prefix-caching"]},
    "qwen3.5-122b-a10b": {"hf_model_id": "Qwen/Qwen3.5-122B-A10B", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "qwen3", "--language-model-only", "--enable-prefix-caching"]},
    "qwen3.5-397b-a17b": {"hf_model_id": "Qwen/Qwen3.5-397B-A17B-FP8", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "qwen3", "--language-model-only", "--enable-prefix-caching"]},
    # -- Nemotron 3 (NVIDIA, US): Nano-4B / Nano-30B-A3B / Super-120B-A12B, all BF16 --
    "nemotron-3-nano-4b":         {"hf_model_id": "nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16", "tp": 1, "max_model_len": 131072,
                                   "vllm_args": ["--enable-prefix-caching"]},
    "nemotron-3-nano-30b-a3b":    {"hf_model_id": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16", "tp": 4, "max_model_len": 131072,
                                   "vllm_args": ["--enable-prefix-caching"]},
    "nemotron-3-super-120b-a12b": {"hf_model_id": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16", "tp": 8, "max_model_len": 131072,
                                   "vllm_args": ["--enable-prefix-caching"]},
    # -- Gemma 4 (Google, US): E2B / 12B / 31B instruction-tuned --
    "gemma-4-e2b": {"hf_model_id": "google/gemma-4-E2B-it", "tp": 1, "max_model_len": 131072,
                    "vllm_args": ["--reasoning-parser", "gemma4", "--language-model-only", "--enable-prefix-caching"]},
    "gemma-4-12b": {"hf_model_id": "google/gemma-4-12B-it", "tp": 1, "max_model_len": 131072,
                    "vllm_args": ["--reasoning-parser", "gemma4", "--language-model-only", "--enable-prefix-caching"]},
    "gemma-4-31b": {"hf_model_id": "google/gemma-4-31B-it", "tp": 4, "max_model_len": 131072,
                    "vllm_args": ["--reasoning-parser", "gemma4", "--language-model-only", "--enable-prefix-caching"]},
    # -- GLM-4.x (Zhipu/Z.ai, CN): 4.7-Flash / 4.5-Air / 4.7 (cross-generation, flagged) --
    "glm-4.7-flash": {"hf_model_id": "zai-org/GLM-4.7-Flash", "tp": 4, "max_model_len": 131072,
                      "vllm_args": ["--reasoning-parser", "glm47", "--enable-prefix-caching"]},
    "glm-4.5-air":   {"hf_model_id": "zai-org/GLM-4.5-Air", "tp": 8, "max_model_len": 131072,
                      "vllm_args": ["--reasoning-parser", "glm45", "--enable-prefix-caching"]},
    "glm-4.7":       {"hf_model_id": "zai-org/GLM-4.7", "tp": 8, "max_model_len": 131072,
                      "vllm_args": ["--reasoning-parser", "glm47", "--enable-prefix-caching"]},
    # -- Ministral-3 Reasoning 2512 (Mistral, FR): 3B / 8B / 14B --
    "ministral-3-3b":  {"hf_model_id": "mistralai/Ministral-3-3B-Reasoning-2512", "tp": 1, "max_model_len": 131072,
                        "vllm_args": ["--reasoning-parser", "mistral", "--language-model-only", "--enable-prefix-caching"],
                        "system_prompt": MINISTRAL_THINK_SYSTEM},
    "ministral-3-8b":  {"hf_model_id": "mistralai/Ministral-3-8B-Reasoning-2512", "tp": 4, "max_model_len": 131072,
                        "vllm_args": ["--reasoning-parser", "mistral", "--language-model-only", "--enable-prefix-caching"],
                        "system_prompt": MINISTRAL_THINK_SYSTEM},
    "ministral-3-14b": {"hf_model_id": "mistralai/Ministral-3-14B-Reasoning-2512", "tp": 4, "max_model_len": 131072,
                        "vllm_args": ["--reasoning-parser", "mistral", "--language-model-only", "--enable-prefix-caching"],
                        "system_prompt": MINISTRAL_THINK_SYSTEM},
    # -- EXAONE (LG AI Research, KR): 4.0-32B / 4.5-33B / K-EXAONE-236B-A23B (cross-gen, flagged) --
    "exaone-4.0-32b":    {"hf_model_id": "LGAI-EXAONE/EXAONE-4.0-32B", "tp": 4, "max_model_len": 131072,
                          "vllm_args": ["--enable-prefix-caching"]},
    "exaone-4.5-33b":    {"hf_model_id": "LGAI-EXAONE/EXAONE-4.5-33B", "tp": 4, "max_model_len": 131072,
                          "vllm_args": ["--language-model-only", "--enable-prefix-caching"]},
    "k-exaone-236b-a23b": {"hf_model_id": "LGAI-EXAONE/K-EXAONE-236B-A23B", "tp": 8, "max_model_len": 131072,
                           "vllm_args": ["--gpu-memory-utilization", "0.92", "--enable-prefix-caching"]},
    # -- DeepSeek (CN): V4-Flash / V3.1 / V4-Pro (cross-gen, flagged; V4 = inline template) --
    # !! V4 status (corrected 2026-08-12): the 2026-08-11 "missing module"
    # diagnosis was WRONG -- new archs moved to a top-level vllm/models/
    # package (registry maps the fully-qualified "vllm.models.deepseek_v4"),
    # and the probe had imported the LEGACY flat path, whose
    # ModuleNotFoundError is by design. The module ships in the nightly that
    # crashed AND in v0.27.0/v0.27.1 (wheel + image layer listings). The
    # silent engine-core death on the 2026-08-11 nightly is therefore real
    # but UNDIAGNOSED. Known adjacent hazard: vllm#51326 reports corrupted
    # generations for V4-Flash on 8xH100 TP8 on 0.26/0.27.1 (maintainer:
    # deepgemm-related; 0.25.0 reported good) -- any V4 lane must pass a
    # coherence smoke before its data counts.
    "deepseek-v4-flash": {"hf_model_id": "deepseek-ai/DeepSeek-V4-Flash", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "deepseek_v4", "--chat-template", DSV4_CHAT_TEMPLATE, "--enable-prefix-caching"]},
    "deepseek-v3.1":     {"hf_model_id": "deepseek-ai/DeepSeek-V3.1", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--enable-prefix-caching"]},
    "deepseek-v4-pro":   {"hf_model_id": "deepseek-ai/DeepSeek-V4-Pro", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "deepseek_v4", "--chat-template", DSV4_CHAT_TEMPLATE, "--gpu-memory-utilization", "0.93", "--enable-prefix-caching"]},
}


# ---------------------------------------------------------------------------
# Internal poll/timeout tuning: implementation detail, NOT env-configurable
# like the EC2_* knobs above -- these bound how chattily this module polls
# AWS/the instance, not anything a notebook run should need to tune.
# ---------------------------------------------------------------------------
# _wait_public_ip: how long to wait for DescribeInstances to report a public
# IP after launch, and how often to re-poll while waiting.
_WAIT_IP_TIMEOUT_S: int = 300
_WAIT_IP_POLL_S: int = 5
# _wait_agent: how often to retry the control-agent's /status probe, and
# every how many polls to additionally confirm (via DescribeInstances) that
# the instance itself is still alive -- 6 polls * 10s = one extra
# DescribeInstances call per minute, cheap insurance against silently polling
# a dead box for the whole timeout instead of failing fast.
_AGENT_POLL_S: int = 10
_AGENT_PROGRESS_EVERY_N_POLLS: int = 6
# _wait_model_ready: how often to re-poll the agent's /status while a model
# loads (dominated by the checkpoint download; see the function's docstring).
_MODEL_READY_POLL_S: int = 15
# _ensure_instance_profile: IAM is eventually consistent, so a just-created
# role/instance-profile is not always immediately usable by RunInstances;
# this is empirically enough slack for that propagation to catch up.
_IAM_PROPAGATION_SLEEP_S: int = 12
# list_models(): read timeout for the small, fast GET /v1/models metadata
# call. Shared with every other provider via openai_compat.METADATA_TIMEOUT_S
# (see that constant's docstring) rather than a duplicate local literal --
# this used to be a deliberately-local constant, but the /_aws.py extraction
# was a natural point to fold it into the one already-shared value. Since the
# metadata_get() extraction, list_models() no longer names the constant
# directly -- it inherits this timeout from metadata_get's own default
# parameter (see smolbench.evals.openai_compat.metadata_get).


# ---------------------------------------------------------------------------
# Local state file (instance identity + secrets); shared by both paths
# ---------------------------------------------------------------------------


def _state_path() -> Path:
    """State-file path; the env override is honored at call time."""
    return Path(os.getenv("EC2_STATE_FILE", str(_DEFAULT_STATE_FILE))).expanduser()


def _load_state() -> Optional[Dict[str, Any]]:
    """Returns the saved instance state, or None when absent/corrupt.

    Falls back to the legacy cwd-relative ``.ec2_state.json`` (the pre-anchor
    default) when the primary path has nothing and no override is set, so
    state written by an older version is still honored.
    """
    candidates = [_state_path()]
    if not os.getenv("EC2_STATE_FILE"):
        candidates.append(Path(".ec2_state.json"))
    for path in candidates:
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _save_state(state: Dict[str, Any]) -> None:
    path = _state_path()
    path.write_text(json.dumps(state, indent=2) + "\n")
    path.chmod(0o600)  # holds the control token and the vLLM api key


def _clear_state(instance_id: Optional[str] = None) -> None:
    """Removes the local state file, unless another instance has claimed it.

    ``instance_id`` is the instance whose teardown is doing the clearing. When
    supplied, the file is LEFT ALONE if it now names a different instance --
    which happens when a second run for the same experiment tag provisions a
    fresh box and writes its state in the window between this teardown
    starting and finishing.

    Deleting it in that window strands the new box: its driver's next call
    raises "No EC2 instance state found" and exits, leaving a live GPU
    instance billing with nothing driving it and no local record that it
    exists. Seen live 2026-08-09 -- a p5.48xlarge orphaned for 8 minutes at
    ~$21/h, recovered only because ``provision_spot_instance`` can rebuild
    state from the instance's user-data via the experiment tag.

    Passing None keeps the unconditional behaviour, for callers with no
    instance in hand (nothing was resolved, so nothing can be mismatched).
    """
    try:
        if instance_id is not None:
            current = _load_state()
            if current is not None and current.get("instance_id") != instance_id:
                logging.info(
                    f"_clear_state: keeping state for {current.get('instance_id')}; "
                    f"it is not {instance_id}, the instance being torn down."
                )
                return
        _state_path().unlink()
    except OSError:
        pass


def _require_state() -> Dict[str, Any]:
    state = _load_state()
    if state is None:
        raise RuntimeError(
            f"No EC2 instance state found at {_state_path().resolve()} "
            "(override via EC2_STATE_FILE). Run provision_spot_instance() -- it is "
            "idempotent: it reattaches to a live instance via the state file or the "
            "smolbench:experiment tag (recovering lost state from the instance's "
            "user-data) before it would ever launch a new box."
        )
    return state


def _base_url() -> str:
    """The OpenAI-compatible base URL, resolved at call time.

    This cannot be an import-time constant: the instance's IP does not exist
    until provisioning. ``EC2_INFERENCE_BASE_URL`` overrides (tests /
    externally managed servers); otherwise the state file supplies it.
    """
    override = os.getenv("EC2_INFERENCE_BASE_URL")
    if override:
        return override.rstrip("/")
    return f"http://{_require_state()['public_ip']}:{EC2_VLLM_PORT}/v1"


def _api_key() -> str:
    """The vLLM bearer token, resolved at call time (override or state file)."""
    override = os.getenv("EC2_VLLM_API_KEY")
    if override:
        return override
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


def list_models(model: str = "") -> List[str]:
    """Lists model ids the instance's vLLM currently serves (normally one).

    Parameters
    ----------
    model : str, optional
        Accepted and IGNORED. This module's vLLM instance serves exactly one
        model at a time (whichever ``serve_model`` last swapped in), so there
        is nothing to select by name -- the parameter exists purely for
        signature parity with ``smolbench.evals.aws.list_models(model="")``,
        whose SageMaker path DOES use it (to fill a templated per-endpoint
        base URL). Sharing one signature across providers lets
        ``smolbench.evals.provider``'s dispatch surface call
        ``list_models(model)`` uniformly without special-casing EC2. Internal
        callers within this module (``serve_model``) intentionally keep
        calling ``list_models()`` with no argument, since they have nothing
        meaningful to pass either.

    Returns
    -------
    List[str]
        Model ids from the vLLM ``GET /v1/models`` response's ``data[].id``
        (normally a single-element list).
    """
    response = metadata_get(f"{_base_url()}/models", _api_key(), check_status=True)
    return [m["id"] for m in response.get("data", [])]


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
            # NOTE: intentionally NOT using the _instance_state(region, id)
            # helper here (see its docstring) -- that helper routes through
            # _describe_instance, which SWALLOWS InvalidInstanceID.NotFound
            # into "absent". Here, a raw ClientError (including NotFound) is
            # meant to fall into the `except Exception` below and produce the
            # generic "instance-state check failed" detail, not the specific
            # "is absent" RuntimeError -- switching this site to the helper
            # would silently change that error message for an aged-out
            # instance id, which is out of scope for this refactor.
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


def _connection(model: str) -> Tuple[str, str]:
    """Chat URL + vLLM token, resolved together from ONE state snapshot.

    Called once per request attempt (see ChatClient.connection): a spot
    instance re-provisioned mid-retry-loop is picked up on the next attempt,
    and reading the state file a single time per attempt closes the window
    where the URL and token could come from two different state versions.
    """
    base = os.getenv("EC2_INFERENCE_BASE_URL")
    key = os.getenv("EC2_VLLM_API_KEY")
    # Empty-string env values (blanked keys.env lines) count as unset, like
    # the truthiness checks in _base_url/_api_key.
    if not base or not key:
        state = _require_state()
        base = base or f"http://{state['public_ip']}:{EC2_VLLM_PORT}/v1"
        key = key or state["vllm_api_key"]
    return f"{base.rstrip('/')}/chat/completions", key


def _system_prompt(model: str) -> Optional[str]:
    """Spec-level system prompt (e.g. Nemotron's "detailed thinking on" CoT
    toggle), injected at the provider layer so the notebook's user prompts
    stay byte-identical across archetypes."""
    return EC2_DEPLOY_SPECS.get(model, {}).get("system_prompt")


_CLIENT = ChatClient(
    name="EC2 endpoint",
    env_prefix="EC2",
    connection=_connection,
    context_length=get_model_context_length,
    system_prompt=_system_prompt,
    retry_backoff_s=EC2_RETRY_BACKOFF_SECONDS,
    # (connect, read): short connect fails fast on a dead box; long read
    # covers genuine long CoT generations (see the constants' comments).
    connect_timeout_s=EC2_CONNECT_TIMEOUT_SECONDS,
    read_timeout_s=EC2_REQUEST_TIMEOUT_SECONDS,
    # A self-managed spot endpoint can vanish (interruption, watchdog,
    # caller-IP drift); unlike managed providers, cap connection-level
    # failures instead of retrying forever against a dead box, and diagnose
    # the cause (spot reclaim vs caller-IP drift) in the raised error.
    max_connection_failures=EC2_MAX_CONNECTION_FAILURES,
    on_unreachable=_raise_endpoint_unreachable,
)

# The provider-facing API (dispatched via smolbench.evals.provider); full
# parameter docs live on ChatClient.query / ChatClient.complete / ChatClient.evaluate. The
# plain-text <think> splitting Nemotron-Ultra and Olmo-Think need (no think
# token ids -> no server-side reasoning parser; see EC2_DEPLOY_SPECS) lives in
# the shared client, so every provider handles it identically.
query = _CLIENT.query
complete = _CLIENT.complete  # ChatResult-returning superset of query (usage, model, finish_reason)
evaluate = _CLIENT.evaluate


# ---------------------------------------------------------------------------
# On-instance payloads (control agent, idle watchdog, cloud-init bootstrap)
# ---------------------------------------------------------------------------
# The payload programs and cloud-init templates live as byte-exact assets in
# smolbench/evals/payloads/ (agent.py.txt, watchdog.py.txt, user_data.sh),
# exposed there as string constants and rendered by payloads.render_user_data
# (imported at the top of this module). See that package's docstring for the
# payload contract (py3.10/stdlib-only, 16 KB user-data budget) and
# tests/test_ec2_payloads.py for their pre-launch validation.


# ---------------------------------------------------------------------------
# EC2 spot provisioning / lifecycle (lazy boto3; opt-in)
# ---------------------------------------------------------------------------
# boto3/botocore are imported inside these functions (transitively, via
# _aws.fresh_client) so the inference path stays dependency-free (see module
# docstring). Clients are created from a FRESH boto3 Session per operation --
# not boto3.client(), whose process-wide default session caches credentials
# at first resolve, so a refreshed ~/.aws/credentials (IdP sessions here last
# ~12h) would otherwise keep raising RequestExpired until the kernel
# restarts. See smolbench.evals._aws.fresh_client's docstring for the full
# rationale -- this module and aws.py both hit the same failure mode
# independently, which is why the fix now lives in one shared place.

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
    """Thin wrapper over ``_aws.fresh_client("ec2", region)``.

    Kept as a locally-named one-liner (rather than calling ``_aws.
    fresh_client`` directly at every call site) so ``tests/test_ec2_
    provision.py`` and friends can keep doing
    ``monkeypatch.setattr(ec2, "_ec2_client", ...)`` exactly as before the
    ``_aws.py`` extraction -- every call site in this module goes through
    this name, never ``_aws.fresh_client`` directly, so patching this one
    name still intercepts every EC2 API call this module makes.
    """
    return _aws.fresh_client("ec2", region)


# Design: `_error_code = _aws.error_code` (rather than re-defining the body)
# keeps this a plain re-export -- same monkeypatchability as `_ec2_client`
# above (tests patch `ec2._error_code`), zero behavioral difference from the
# pre-extraction inline function.
_error_code = _aws.error_code


def _my_public_ip() -> str:
    return requests.get("https://checkip.amazonaws.com", timeout=10).text.strip()


def _resolve_ami(region: str) -> Tuple[str, str]:
    """Returns (ami_id, root_device_name) for the region's latest DL Base GPU AMI."""
    ssm = _aws.fresh_client("ssm", region)
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
    """Opens EC2_VLLM_PORT + EC2_AGENT_PORT to ip/32; tolerates existing rules."""
    from botocore.exceptions import ClientError

    ec2 = _ec2_client(region)
    for port in (EC2_VLLM_PORT, EC2_AGENT_PORT):
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
    from botocore.exceptions import ClientError

    s3 = _aws.fresh_client("s3", region)
    try:
        s3.head_bucket(Bucket=bucket)
        return
    except ClientError as err:
        code = _error_code(err)
        if code not in ("404", "NoSuchBucket"):
            # 403/301 is ambiguous: either the name exists in another
            # account/region (creating would fail confusingly, so surface
            # it), or HEAD is simply denied to scoped credentials (the
            # EC2-only operator key has no s3:*; instances reach the cache
            # via their instance profile, not the caller's credentials).
            # An account-id suffix in the bucket name proves it is ours --
            # sts:GetCallerIdentity needs no policy, so it works even for
            # the most restricted principal.
            if code == "403":
                account = _aws.fresh_client("sts", region).get_caller_identity()["Account"]
                if bucket.endswith(account):
                    logging.info(
                        f"_ensure_bucket: HEAD s3://{bucket} -> 403 under scoped "
                        f"credentials; bucket name is suffixed with this account "
                        f"({account}), proceeding"
                    )
                    return
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

    Thin wrapper over ``_aws.ensure_instance_profile``, threading in this
    module's own ``EC2_INSTANCE_ROLE_NAME`` / ``_IAM_PROPAGATION_SLEEP_S``
    module constants as that shared function's ``role_name`` /
    ``propagation_sleep_s`` parameters. Kept as a locally-named one-liner
    (rather than calling ``_aws.ensure_instance_profile`` directly from
    ``_launch_fresh``) for the same monkeypatchability reason as
    ``_ec2_client`` above -- tests patch ``ec2._ensure_instance_profile``.

    The role grants (a) read/write scoped to the cache bucket and (b) SSM core,
    which doubles as the break-glass shell for a box that has no SSH key.
    """
    return _aws.ensure_instance_profile(EC2_INSTANCE_ROLE_NAME, bucket, _IAM_PROPAGATION_SLEEP_S)


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


def _recover_state_from_instance(
    region: str, instance: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Rebuilds the state dict for a live instance whose state file was lost.

    The per-experiment secrets ride in the instance's user-data (the
    ``/etc/smolbench/env`` heredoc), so DescribeInstanceAttribute recovers
    them -- the same in-account visibility the security model already
    accepts. Returns None when the user-data cannot be parsed (a foreign or
    older-format instance), leaving the caller to refuse reuse.
    """
    import base64

    try:
        attr = _ec2_client(region).describe_instance_attribute(
            InstanceId=instance["InstanceId"], Attribute="userData"
        )
        user_data = base64.b64decode(attr["UserData"]["Value"]).decode()
    except Exception as exc:  # noqa: BLE001 -- recovery is best-effort
        logging.warning(f"state recovery: could not read instance user-data: {exc}")
        return None
    # The env heredoc writes one NAME=value per line at column 0; the embedded
    # python scripts only ever reference these names via os.environ, so a
    # plain line scan is unambiguous.
    env: Dict[str, str] = {}
    for line in user_data.splitlines():
        key, sep, value = line.partition("=")
        if sep and key in ("CONTROL_TOKEN", "VLLM_API_KEY", "IDLE_TIMEOUT_MIN", "S3_CACHE_URI"):
            env.setdefault(key, value)
    security_groups = instance.get("SecurityGroups") or []
    if not env.get("CONTROL_TOKEN") or not env.get("VLLM_API_KEY") or not security_groups:
        return None
    launch_time = instance.get("LaunchTime")
    return {
        "instance_id": instance["InstanceId"],
        "region": region,
        "availability_zone": instance.get("Placement", {}).get("AvailabilityZone", "?"),
        "instance_type": instance.get("InstanceType", "?"),
        "public_ip": instance.get("PublicIpAddress"),
        "security_group_id": security_groups[0]["GroupId"],
        "control_token": env["CONTROL_TOKEN"],
        "vllm_api_key": env["VLLM_API_KEY"],
        "idle_timeout_min": int(env.get("IDLE_TIMEOUT_MIN") or EC2_IDLE_TIMEOUT_MIN),
        "s3_cache": env.get("S3_CACHE_URI", EC2_S3_MODEL_CACHE),
        "launched_at": launch_time.strftime("%Y-%m-%dT%H:%M:%SZ") if launch_time else "?",
    }


def _describe_instance(region: str, instance_id: str) -> Optional[Dict[str, Any]]:
    """Returns the full DescribeInstances record for one instance, or None.

    None covers both "never existed" and "existed but aged out of the API"
    (``InvalidInstanceID.NotFound``, which AWS raises once a terminated
    instance's record expires, typically about an hour after termination) --
    callers that only need the state Name should use ``_instance_state``
    instead, which also normalizes both cases to ``"absent"``.
    """
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


def _instance_state(region: str, instance_id: str) -> str:
    """Returns an instance's EC2 state Name, or "absent" when it is gone.

    Thin convenience wrapper around ``_describe_instance`` for call sites that
    need ONLY the state name. Sites that also need another field from the
    same describe result (e.g. ``PublicIpAddress``) intentionally do NOT use
    this helper -- routing them through it would cost a second
    DescribeInstances call for data the caller already has in hand from its
    own ``_describe_instance`` call. See the inline notes at those call sites
    (``_wait_public_ip``, and ``provision_spot_instance``'s reattach branch)
    for why they keep the raw ``(instance or {}).get(...)`` idiom instead.

    Parameters
    ----------
    region : str
        AWS region to query.
    instance_id : str
        EC2 instance id.

    Returns
    -------
    str
        The instance's ``State.Name`` (e.g. ``"pending"``, ``"running"``,
        ``"shutting-down"``, ``"terminated"``), or ``"absent"`` when
        ``_describe_instance`` returns ``None`` (never existed, or aged out
        of the API after termination).

    Notes
    -----
    Makes one DescribeInstances API call per invocation (via
    ``_describe_instance``); callers polling in a loop should be mindful of
    that cost (see the poll-interval constants near the EC2_* config block).
    """
    instance = _describe_instance(region, instance_id)
    return (instance or {}).get("State", {}).get("Name", "absent")


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


def _wait_public_ip(region: str, instance_id: str, timeout_s: int = _WAIT_IP_TIMEOUT_S) -> str:
    """Polls DescribeInstances until ``instance_id`` reports a public IP.

    Parameters
    ----------
    region : str
        AWS region the instance was launched in.
    instance_id : str
        EC2 instance id to poll.
    timeout_s : int, optional
        Give up after this many seconds. Default ``_WAIT_IP_TIMEOUT_S``.

    Returns
    -------
    str
        The instance's public IPv4 address, as soon as EC2 reports one.

    Raises
    ------
    RuntimeError
        If the instance transitions to ``shutting-down``/``terminated``/
        absent before ever getting an IP (spot reclaimed right after launch).
    TimeoutError
        If no public IP appears within ``timeout_s``.

    Notes
    -----
    Built on ``_aws.poll_until``: the RuntimeError abort (spot reclaimed
    right after launch) is raised straight out of ``check()`` per that
    function's contract, propagating unchanged through ``poll_until``.
    ``check()`` returns ``ip or None`` rather than ``ip`` -- ``poll_until``
    treats any non-None return as success, so this preserves the original
    loop's truthiness check (``if ip:``) rather than an ``is not None``
    check, in case EC2 ever reports an empty-string address (never observed,
    but the original guarded it, so this does too).
    """

    def check() -> Optional[str]:
        instance = _describe_instance(region, instance_id)
        # NOTE: NOT using _instance_state(region, instance_id) here -- this
        # site also needs PublicIpAddress from the SAME describe result right
        # below, and the helper would cost a second DescribeInstances call
        # for state alone. See _instance_state's docstring.
        inst_state = (instance or {}).get("State", {}).get("Name", "absent")
        if inst_state in ("shutting-down", "terminated", "absent"):
            raise RuntimeError(
                f"instance {instance_id} went {inst_state} right after launch "
                "(spot reclaimed?); re-run provision_spot_instance()."
            )
        ip = (instance or {}).get("PublicIpAddress")
        return ip or None

    def on_timeout() -> TimeoutError:
        return TimeoutError(f"instance {instance_id} got no public IP in {timeout_s}s")

    return _aws.poll_until(check, timeout_s=timeout_s, interval_s=_WAIT_IP_POLL_S, on_timeout=on_timeout)


def _agent(
    state: Dict[str, Any], method: str, path: str, payload: Optional[Dict[str, Any]] = None,
    timeout: int = 120, connect_retries: int = 40,
) -> Dict[str, Any]:
    """One authenticated control-agent call; raises with the body on failure.

    ``connect_retries``: extra attempts on CONNECT-level failures only
    (``requests.ConnectionError``, which covers ConnectTimeout), 15s apart.
    The caller's egress NAT drops/rotates connections in bursts (live
    2026-07-19 and 2026-08-01: one-shot ``/serve`` calls died mid-sweep on
    transient ConnectTimeouts while the box was healthy), and every agent
    endpoint is idempotent, so a couple of minutes of connect patience is
    always safe. The polling loops (``_wait_agent``/``_wait_model_ready``)
    and the best-effort graceful shutdown pass 0 to keep their own cadence/
    fail-fast semantics.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(connect_retries + 1):
        try:
            response = requests.request(
                method,
                f"http://{state['public_ip']}:{EC2_AGENT_PORT}{path}",
                headers={"Authorization": f"Bearer {state['control_token']}"},
                json=payload,
                timeout=timeout,
            )
            break
        except requests.exceptions.ConnectionError as exc:
            last_exc = exc
            if attempt == connect_retries:
                raise
            time.sleep(15)
    if not response.ok:
        raise RuntimeError(f"agent {method} {path} -> {response.status_code}: {response.text[:2000]}")
    return response.json()


def _wait_agent(state: Dict[str, Any], timeout_min: int = EC2_PROVISION_TIMEOUT_MIN) -> None:
    """Waits for the control agent to answer after boot/reattach.

    Polls ``GET /status`` every ``_AGENT_POLL_S`` seconds; every
    ``_AGENT_PROGRESS_EVERY_N_POLLS`` polls it additionally confirms (via
    DescribeInstances) that the instance itself is still alive, so a spot
    reclaim during boot fails fast with an actionable error instead of
    silently exhausting the whole ``timeout_min`` budget.

    Parameters
    ----------
    state : Dict[str, Any]
        Instance state dict (needs ``public_ip``, ``control_token``,
        ``region``, ``instance_id``).
    timeout_min : int, optional
        Give up after this many minutes. Default ``EC2_PROVISION_TIMEOUT_MIN``.

    Raises
    ------
    RuntimeError
        If the periodic liveness check finds the instance no longer
        ``pending``/``running`` (spot reclaimed while waiting for its agent).
    TimeoutError
        If the agent never answers within ``timeout_min``.

    Notes
    -----
    Built on ``_aws.poll_until``. The every-``_AGENT_PROGRESS_EVERY_N_POLLS``
    liveness sub-check needs a poll COUNTER that survives across iterations,
    which ``poll_until``'s stateless ``check()`` contract does not provide by
    itself -- so ``check()`` closes over a ``polls`` counter via ``nonlocal``,
    exactly reproducing the original loop's own local ``polls`` variable.
    """
    from botocore.exceptions import ClientError

    polls = 0

    def check() -> Optional[bool]:
        nonlocal polls
        try:
            _agent(state, "GET", "/status", timeout=5, connect_retries=0)
            logging.info(f"control agent up at {state['public_ip']}:{EC2_AGENT_PORT}")
            return True
        except (requests.exceptions.RequestException, RuntimeError):
            pass
        polls += 1
        if polls % _AGENT_PROGRESS_EVERY_N_POLLS == 0:  # every minute, make sure the box still exists
            try:
                inst_state = _instance_state(state["region"], state["instance_id"])
                if inst_state not in ("pending", "running"):
                    raise RuntimeError(
                        f"instance {state['instance_id']} went {inst_state} while waiting "
                        "for its agent (spot reclaimed?); re-run provision_spot_instance()."
                    )
            except ClientError:
                # A transient describe failure (throttling, a brief AWS-side
                # blip) should not abort the wait -- swallow it and re-check
                # on the next progress poll. The RuntimeError raised just
                # above (instance genuinely gone) is not a ClientError and
                # still propagates out of check(), per poll_until's contract.
                pass
        return None

    def on_timeout() -> TimeoutError:
        return TimeoutError(
            f"control agent at {state['public_ip']}:{EC2_AGENT_PORT} not answering after "
            f"{timeout_min} min. Debug via the EC2 serial console / instance "
            "screenshot, or relaunch with EC2_KEY_NAME set for SSH; bootstrap "
            "logs to /var/log/smolbench-bootstrap.log on the instance."
        )

    _aws.poll_until(
        check, timeout_s=timeout_min * 60, interval_s=_AGENT_POLL_S, on_timeout=on_timeout
    )


def _reattach_existing_instance(my_ip: str) -> Optional[Dict[str, Any]]:
    """``provision_spot_instance`` branch 1: reuse the state-file instance.

    Preconditions: none -- safe to call unconditionally. A missing/corrupt
    state file (``_load_state()`` returns ``None``) is a normal "nothing to
    reattach to" outcome, not an error.

    Side effects (only when an instance IS reattached): re-authorizes the
    security group for ``my_ip``, refreshes and persists ``public_ip`` in the
    state file, and blocks until the control agent answers. When the
    recorded instance is no longer alive, the stale state file is cleared as
    a side effect so the caller's next strategy (tag recovery, then a fresh
    launch) starts from a clean slate.

    Parameters
    ----------
    my_ip : str
        Caller's current public IP, to (re-)authorize in the security group.

    Returns
    -------
    Optional[Dict[str, Any]]
        The refreshed, already-saved state dict when the state-file instance
        is still ``pending``/``running``; ``None`` when there is no state
        file, or the recorded instance is no longer alive.
    """
    state = _load_state()
    if state is None:
        return None
    instance = _describe_instance(state["region"], state["instance_id"])
    # NOTE: NOT using _instance_state(region, instance_id) here -- `instance`
    # is reused for PublicIpAddress just below, and the helper would cost a
    # second DescribeInstances call for state alone. See _instance_state's
    # docstring.
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
    return None


def _recover_tagged_instance(my_ip: str) -> Optional[Dict[str, Any]]:
    """``provision_spot_instance`` branch 2: recover a live tagged instance.

    Runs only after branch 1 finds nothing to reattach to. Covers a lost/
    never-written local state file: a live instance tagged
    ``smolbench:experiment=EC2_EXPERIMENT_TAG`` carries its own secrets in its
    user-data (see ``_recover_state_from_instance``), so this rebuilds the
    state dict from the instance itself rather than stranding a $30-45/h box.

    Side effects (only when state IS recovered): same as
    ``_reattach_existing_instance`` -- re-authorizes ingress, refreshes and
    persists ``public_ip``, waits for the agent.

    Parameters
    ----------
    my_ip : str
        Caller's current public IP, to (re-)authorize in the security group.

    Returns
    -------
    Optional[Dict[str, Any]]
        The recovered, already-saved state dict when a tagged live instance
        is found AND its user-data parses; ``None`` when no tagged instance
        exists at all (the caller should proceed to a fresh launch).

    Raises
    ------
    RuntimeError
        A tagged live instance exists but its user-data could not be parsed
        for the control token (a foreign or older-format instance) --
        refusing to silently reuse a box this process cannot authenticate to.
    """
    found = _find_tagged_instance()
    if found is None:
        return None
    region, instance = found
    state = _recover_state_from_instance(region, instance)
    if state is not None:
        _authorize_ingress(region, state["security_group_id"], my_ip)
        state["public_ip"] = instance.get("PublicIpAddress") or _wait_public_ip(
            region, state["instance_id"]
        )
        _save_state(state)
        _wait_agent(state)
        logging.info(
            f"provision_spot_instance: recovered state for {state['instance_id']} "
            f"({state['instance_type']} @ {region}, {state['public_ip']}) "
            "from its user-data"
        )
        return state
    name = next(
        (t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), "?"
    )
    raise RuntimeError(
        f"Found live instance {instance['InstanceId']} (Name={name}, "
        f"{instance.get('InstanceType', '?')} @ {region}, launched "
        f"{instance.get('LaunchTime', '?')}) tagged "
        f"smolbench:experiment={EC2_EXPERIMENT_TAG}, but no local state file, and its "
        "user-data could not be parsed for the control token, so it cannot be "
        "reused. If it is someone else's run (or a test) wait for it to "
        "finish/self-terminate; otherwise run shutdown_instance() to terminate it, "
        "then provision again."
    )


def _run_instances_kwargs(
    ami: str,
    instance_type: str,
    subnet_id: str,
    group_id: str,
    root_device: str,
    volume_gb: int,
    user_data: str,
    key_name: str,
    iam_profile: Optional[str],
    capacity_reservation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds the ``run_instances`` kwargs for one launch attempt.

    Pure and side-effect-free (no AWS calls): every value that varies per
    attempt (AZ/subnet, AMI, instance type, security group, root device) is a
    parameter; values fixed for the whole experiment (root-volume throughput/
    IOPS, the experiment tag) are read from the module-level ``EC2_*``
    constants, exactly as the inline dict this was extracted from did.

    Parameters
    ----------
    ami : str
        AMI id resolved for the target region (see ``_resolve_ami``).
    instance_type : str
        e.g. ``"p5e.48xlarge"``.
    subnet_id : str
        Default-VPC subnet to launch into (pins the availability zone).
    group_id : str
        Security group id from ``_ensure_security_group``.
    root_device : str
        Root device name for ``ami`` (e.g. ``"/dev/sda1"``), from
        ``_resolve_ami``.
    volume_gb : int
        Root gp3 volume size in GiB.
    user_data : str
        Rendered cloud-init script (see ``payloads.render_user_data``); passed
        through unencoded -- boto3 base64-encodes it internally.
    key_name : str
        EC2 key pair name for SSH debugging, or ``""`` to omit the
        ``KeyName`` kwarg entirely (no key pair attached).
    iam_profile : Optional[str]
        Instance-profile name for the S3 model cache, or ``None``/``""`` to
        omit the ``IamInstanceProfile`` kwarg (no S3 cache configured).
    capacity_reservation_id : Optional[str]
        A purchased EC2 Capacity Block reservation id. When set, the launch
        targets the reservation instead of the Spot market: MarketType
        becomes ``"capacity-block"`` (the API requires it for block-backed
        launches) and a ``CapacityReservationSpecification`` pins the
        instance to the block. The caller must pass the block's own AZ
        subnet and instance type -- a mismatch is rejected by RunInstances.

    Returns
    -------
    Dict[str, Any]
        Keyword arguments for ``ec2_client.run_instances(**kwargs)``: a
        one-time Spot instance with InstanceInitiatedShutdownBehavior=
        terminate (see ``_try_launch`` for the fallback when an API rejects
        that combination), a single ENI with a public IP in the experiment's
        security group, and a gp3 root volume sized/tuned from
        ``EC2_ROOT_VOLUME_*``.
    """
    kwargs: Dict[str, Any] = {
        "ImageId": ami,
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
                "Groups": [group_id],
                "AssociatePublicIpAddress": True,
                "DeleteOnTermination": True,
            }
        ],
        "BlockDeviceMappings": [
            {
                "DeviceName": root_device,
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
    if capacity_reservation_id:
        kwargs["InstanceMarketOptions"] = {"MarketType": "capacity-block"}
        kwargs["CapacityReservationSpecification"] = {
            "CapacityReservationTarget": {
                "CapacityReservationId": capacity_reservation_id
            }
        }
    if key_name:
        kwargs["KeyName"] = key_name
    if iam_profile:
        kwargs["IamInstanceProfile"] = {"Name": iam_profile}
    return kwargs


def _launch_fresh(
    instance_types: Tuple[str, ...],
    regions: Tuple[str, ...],
    volume_gb: int,
    idle_timeout_min: int,
    max_lifetime_min: int,
    my_ip: str,
) -> Dict[str, Any]:
    """``provision_spot_instance`` branch 3: hunt capacity and launch fresh.

    Runs only after branches 1 and 2 find nothing to reattach to or recover.
    Generates fresh per-experiment secrets (control token, vLLM API key),
    optionally provisions the S3 model-cache bucket/instance-profile, renders
    the cloud-init user-data once, then hunts Spot capacity TYPE-MAJOR: every
    region (and every default-VPC subnet/AZ within it) is tried for the first
    instance type before falling back to the next type. Per-region resources
    (AMI, security group, subnets) are resolved once and cached across the
    instance-type loop via ``region_info``.

    Parameters
    ----------
    instance_types : Tuple[str, ...]
        Instance types to try, in priority order (already defaulted by the
        caller to ``EC2_INSTANCE_TYPES`` when the notebook passes ``None``).
    regions : Tuple[str, ...]
        Regions to try per instance type (already defaulted to
        ``EC2_REGIONS``).
    volume_gb : int
        Root gp3 volume size in GiB (already defaulted to
        ``EC2_ROOT_VOLUME_GB``).
    idle_timeout_min : int
        Minutes of inactivity before the watchdog self-halts (already
        defaulted to ``EC2_IDLE_TIMEOUT_MIN``).
    max_lifetime_min : int
        Absolute lifetime backstop in minutes (already defaulted to
        ``EC2_MAX_LIFETIME_MIN``).
    my_ip : str
        Caller's public IP (resolved ONCE by ``provision_spot_instance`` and
        threaded through here) to authorize in each region's security group.
        Deliberately NOT re-resolved per region: reusing one snapshot for the
        whole hunt matches the pre-extraction behavior exactly and avoids one
        extra ``checkip.amazonaws.com`` round trip per region encountered.

    Returns
    -------
    Dict[str, Any]
        The newly launched instance's state dict (already saved to
        ``EC2_STATE_FILE``), once its control agent answers.

    Raises
    ------
    RuntimeError
        No ``(instance_type, region)`` combination yielded capacity; the
        message lists every attempt and its failure reason/code.
    """
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
    user_data = render_user_data(
        control_token=control_token,
        vllm_api_key=vllm_api_key,
        hf_token=hf_token,
        idle_timeout_min=idle_timeout_min,
        startup_grace_min=EC2_STARTUP_GRACE_MIN,
        max_lifetime_min=max_lifetime_min,
        image=EC2_VLLM_IMAGE,
        s3_cache_uri=EC2_S3_MODEL_CACHE,
        vllm_port=EC2_VLLM_PORT,
    )

    from botocore.exceptions import ClientError  # lazy: keep the inference path boto3-free

    # A purchased Capacity Block short-circuits the Spot hunt entirely: the
    # block fixes region, AZ, and instance type, so there is nothing to hunt.
    # Read at call time (not import) so the supervisor can set it per launch.
    cb_id = os.getenv("EC2_CAPACITY_RESERVATION", "")
    if cb_id:
        cb_region = os.getenv("EC2_CAPACITY_RESERVATION_REGION", "")
        if not cb_region:
            raise RuntimeError(
                "EC2_CAPACITY_RESERVATION is set but EC2_CAPACITY_RESERVATION_REGION "
                "is not; the reservation's region cannot be inferred."
            )
        cr = _ec2_client(cb_region).describe_capacity_reservations(
            CapacityReservationIds=[cb_id]
        )["CapacityReservations"][0]
        if cr["State"] != "active":
            # Matches the supervisor's drought grep so a block that has not
            # reached its start time is retried on the slow no-cap cadence.
            raise RuntimeError(
                f"InsufficientInstanceCapacity (capacity block {cb_id} is "
                f"{cr['State']!r}, not active yet; starts {cr.get('StartDate')})"
            )
        cb_type, cb_az = cr["InstanceType"], cr["AvailabilityZone"]
        vpc_id, subnets = _default_vpc_subnets(cb_region)
        subnet_id = next((s for s, az in subnets or [] if az == cb_az), None)
        if vpc_id is None or subnet_id is None:
            raise RuntimeError(f"no default-VPC subnet in {cb_az} for capacity block {cb_id}")
        ami, root_device = _resolve_ami(cb_region)
        group_id = _ensure_security_group(cb_region, vpc_id, my_ip)
        kwargs = _run_instances_kwargs(
            ami=ami,
            instance_type=cb_type,
            subnet_id=subnet_id,
            group_id=group_id,
            root_device=root_device,
            volume_gb=volume_gb,
            user_data=user_data,
            key_name=EC2_KEY_NAME,
            iam_profile=iam_profile,
            capacity_reservation_id=cb_id,
        )
        logging.info(
            f"provision_spot_instance: launching {cb_type} into capacity block "
            f"{cb_id} @ {cb_az} (no Spot hunt)"
        )
        instance_id = _try_launch(cb_region, kwargs)
        public_ip = _wait_public_ip(cb_region, instance_id)
        state = {
            "instance_id": instance_id,
            "region": cb_region,
            "availability_zone": cb_az,
            "instance_type": cb_type,
            "public_ip": public_ip,
            "security_group_id": group_id,
            "control_token": control_token,
            "vllm_api_key": vllm_api_key,
            "idle_timeout_min": idle_timeout_min,
            "s3_cache": EC2_S3_MODEL_CACHE,
            "capacity_reservation_id": cb_id,
            "launched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        _save_state(state)
        logging.info(
            f"provision_spot_instance: launched {instance_id} "
            f"({cb_type} @ {cb_az}, {public_ip}); waiting for its agent ..."
        )
        _wait_agent(state)
        return state

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
                kwargs = _run_instances_kwargs(
                    ami=info["ami"],
                    instance_type=instance_type,
                    subnet_id=subnet_id,
                    group_id=info["group_id"],
                    root_device=info["root_device"],
                    volume_gb=volume_gb,
                    user_data=user_data,
                    key_name=EC2_KEY_NAME,
                    iam_profile=iam_profile,
                )
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

    Delegates to three helpers, tried in order, each covering one branch of
    the idempotency contract: ``_reattach_existing_instance`` (state-file
    reuse), ``_recover_tagged_instance`` (state-file lost but a live tagged
    instance exists), ``_launch_fresh`` (neither -- hunt capacity and launch).

    When ``EC2_CAPACITY_RESERVATION`` is set, the reservation is authoritative:
    a live instance OUTSIDE that block is terminated rather than reused (it
    would bill Spot rates on top of the already-paid block), and the launch
    goes straight into the reservation via ``_launch_fresh``.

    Returns the state dict (also persisted to ``EC2_STATE_FILE``): instance_id,
    region, public_ip, instance_type, control_token, vllm_api_key, ...
    """
    instance_types = tuple(instance_types or EC2_INSTANCE_TYPES)
    regions = tuple(regions or EC2_REGIONS)
    volume_gb = volume_gb or EC2_ROOT_VOLUME_GB
    idle_timeout_min = idle_timeout_min or EC2_IDLE_TIMEOUT_MIN
    max_lifetime_min = max_lifetime_min or EC2_MAX_LIFETIME_MIN

    my_ip = _my_public_ip()
    cb_id = os.getenv("EC2_CAPACITY_RESERVATION", "")

    # 1) Reattach to the instance in the state file when it is still alive.
    state = _reattach_existing_instance(my_ip)
    if state is None:
        # 2) A live tagged instance without a state file: rebuild the state
        #    from the instance itself -- its secrets ride in its user-data
        #    (readable via DescribeInstanceAttribute; see the security model
        #    note up top), so losing the local file must not strand a
        #    $30-45/h box.
        state = _recover_tagged_instance(my_ip)
    if state is not None:
        if not cb_id or state.get("capacity_reservation_id") == cb_id:
            return state
        logging.info(
            f"provision_spot_instance: {state['instance_id']} is outside "
            f"capacity block {cb_id}; terminating it and launching in the "
            "block instead."
        )
        # wait=False: the block's capacity is independent of the dying box,
        # and p5-class teardown can outlast botocore's 10-min waiter (seen
        # live 2026-07-18: WaiterError killed the whole provision).
        shutdown_instance(wait=False)

    # 3) Fresh launch.
    return _launch_fresh(
        instance_types, regions, volume_gb, idle_timeout_min, max_lifetime_min, my_ip
    )


def _wait_model_ready(
    state: Dict[str, Any], model: str, timeout_min: int = EC2_SERVE_TIMEOUT_MIN
) -> None:
    """Polls the agent until vLLM answers /health for ``model``.

    First-time serves are dominated by the checkpoint download (hundreds of
    GB for the big FP8 models); the HF cache makes later swaps minutes.

    Notes
    -----
    Built on ``_aws.poll_until``. The TimeoutError message reports the LAST
    polled ``container`` state and ``log_tail`` -- data ``poll_until``'s
    zero-argument ``on_timeout()`` cannot see unless ``check()`` stashes it
    somewhere ``on_timeout()`` can read, hence the ``last_status`` closure
    variable populated on every poll (success or not) and read back only if
    the loop times out.
    """
    last_status: Dict[str, Any] = {}
    consec_failures = 0

    def check() -> Optional[bool]:
        nonlocal last_status, consec_failures
        # A single dropped /status must NOT abort the (up to hours-long) wait:
        # the caller's egress NAT rotates source IPs mid-run, so one connect
        # timeout is routine (live 2026-07-11: one flap killed an arm and its
        # stale serve script then raced the next arm's container). Only a
        # SOLID stretch of unreachability (~8 min at the 15s poll) is treated
        # as the box being gone.
        try:
            status = _agent(state, "GET", "/status", timeout=30, connect_retries=0)
        except requests.exceptions.RequestException as exc:
            consec_failures += 1
            if consec_failures >= 20:
                raise RuntimeError(
                    f"agent unreachable {consec_failures}x in a row while waiting "
                    f"for {model!r} (box gone or caller blocked): {exc}"
                ) from exc
            return None
        consec_failures = 0
        last_status = status
        if status.get("healthy"):
            return True
        container = status.get("container")
        serve_rc = status.get("serve_rc")
        if container in ("exited", "dead"):
            # Include the launcher's own output too: a container that dies
            # pre-entrypoint (bad mount, missing adapter file, OOM-kill)
            # leaves docker logs EMPTY, and the docker-run error then lives
            # only in the serve script's output (seen live 2026-07-19: an
            # adapter arm failed with a blank log_tail and no diagnosis).
            raise RuntimeError(
                f"vLLM container for {model!r} exited during startup; docker logs tail:\n"
                f"{status.get('log_tail', '')}\n"
                f"launcher output tail:\n{status.get('serve_log_tail', '')}"
            )
        # "created" alongside a failed launcher rc is equally terminal: the
        # container exists but nothing will ever start it (seen live
        # 2026-07-14: an orphaned launcher's docker run raced a swap's rm -f,
        # leaving a name-conflicted "created" container and rc=125).
        if container in ("absent", "created") and serve_rc not in (None, 0):
            raise RuntimeError(
                f"docker run for {model!r} failed (rc={serve_rc}, container={container}); "
                f"launcher output:\n{status.get('serve_log_tail', '')}"
            )
        return None

    def on_timeout() -> TimeoutError:
        return TimeoutError(
            f"{model!r} not healthy after {timeout_min} min "
            f"(container={last_status.get('container')}); "
            f"docker logs tail:\n{last_status.get('log_tail', '')}"
        )

    _aws.poll_until(
        check, timeout_s=timeout_min * 60, interval_s=_MODEL_READY_POLL_S, on_timeout=on_timeout
    )


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
    serve_payload = {
        "served_model_name": model,
        "hf_model_id": spec["hf_model_id"],
        "tp": spec.get("tp", 1),
        "max_model_len": spec.get("max_model_len", EC2_CONTEXT_LENGTH),
        # HF_TOKEN is deliberately NOT in this payload: it was baked into
        # the instance at provision time, so it never crosses plain HTTP.
        "vllm_args": list(spec.get("vllm_args", [])),
    }
    if spec.get("adapters"):
        # LoRA adapters staged from S3 on the box before launch (see _serve).
        serve_payload["adapters"] = [dict(a) for a in spec["adapters"]]
    if not force:
        # Decide BEFORE yielding: the yield must sit outside this try, or an
        # exception raised by the with-body would be swallowed here and the
        # generator would fall through to a second serve/yield.
        #
        # "Already serving" requires the recorded launch payload to match too:
        # the served name alone can't tell a 32k container from a 128k one, so
        # after a spec edit a re-run must swap, not skip. No record (state file
        # predates this field, or another client served) => swap to be safe.
        try:
            already_serving = (
                bool(_agent(state, "GET", "/status", timeout=15).get("healthy"))
                and list_models() == [model]
                and state.get("serving") == serve_payload
            )
        except (requests.exceptions.RequestException, RuntimeError):
            already_serving = False
        if already_serving:
            logging.info(f"serve_model: {model!r} already serving; skipping the swap.")
            yield model
            return
    logging.info(f"serve_model: requesting {model!r} ({spec['hf_model_id']}) ...")
    _agent(state, "POST", "/serve", serve_payload)
    _wait_model_ready(state, model, timeout_min or EC2_SERVE_TIMEOUT_MIN)
    served = list_models()
    if model not in served:
        raise RuntimeError(
            f"instance is healthy but serves {served}, not {model!r}; "
            "did another process swap the model?"
        )
    # Remember exactly what this container was launched with, so the
    # already-serving fast path above can tell config drift from a true match.
    state["serving"] = serve_payload
    _save_state(state)
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
    state = _require_state()
    _agent(state, "POST", "/stop")
    if state.pop("serving", None) is not None:
        _save_state(state)


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
                status = _agent(state, "GET", "/status", timeout=10, connect_retries=0)
                if status.get("sync_started") and status.get("sync_rc") is None:
                    logging.warning(
                        "shutdown_instance: an S3 cache upload is still in flight and "
                        "will be cut short; the next instance re-downloads whatever "
                        "is missing (wait and re-run this cell to let it finish)."
                    )
            except Exception:  # noqa: BLE001
                pass
        try:  # best-effort graceful halt; termination below is authoritative
            _agent(state, "POST", "/shutdown", timeout=10, connect_retries=0)
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
        _clear_state(instance_id)
        return
    logging.info(f"shutdown_instance: terminating {instance_id} ({region}) ...")
    if wait:
        from botocore.exceptions import WaiterError

        try:
            _ec2_client(region).get_waiter("instance_terminated").wait(InstanceIds=[instance_id])
            logging.info(f"shutdown_instance: {instance_id} terminated.")
        except WaiterError:
            # TerminateInstances already succeeded above, so the instance IS
            # dying; p5-class teardown just outlasts botocore's 10-min waiter
            # (seen live 2026-07-18, twice). Crashing here would strand the
            # caller AFTER the only action that matters has been taken.
            logging.warning(
                f"shutdown_instance: {instance_id} still shutting down after the "
                "waiter's max attempts; termination is already issued, proceeding."
            )
    _clear_state(instance_id)
