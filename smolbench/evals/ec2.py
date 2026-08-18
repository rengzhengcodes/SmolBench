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
import gzip
import json
import logging
import math
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional, Tuple

import requests

from smolbench.evals import _aws
from smolbench.evals._aws import DeploySpec
from smolbench.evals.openai_compat import ChatClient, metadata_get
from smolbench.evals.payloads import pack_user_data, render_user_data

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
# Digest-pinned to the build the 2026-08-16 determinism hinge experiment
# certified (vLLM 0.27.2rc1.dev122+g8efa13b70; Docker Hub tag
# nightly-8efa13b700f1836657699cae2503dc2feab27fa0). :nightly is mutable --
# >=4 distinct builds served the family-ladder study through it (see
# notebooks/DETERMINISM_PLAN_2026-08-16.md section 1.4). Bump this digest
# deliberately, never back to a moving tag.
EC2_VLLM_IMAGE: str = os.getenv("EC2_VLLM_IMAGE", "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7")
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
#: "spot" (default) or "on-demand". Only ever set this deliberately: on-demand
#: pays several times the spot rate and cannot be reclaimed, so a forgotten box
#: bills at full price until the idle watchdog or the lifetime backstop fires.
#: It exists for a lane whose exact instance type has NO spot capacity anywhere
#: and whose hardware must not be substituted -- buying the same silicon a
#: different way is the only move that keeps the lane uncontaminated.
EC2_MARKET: str = os.getenv("EC2_MARKET", "spot")
#: Spot bid ceiling as a multiple of the median observed AZ price. The 1.25
#: default gives a normal-priced AZ headroom while letting outlier AZs (a 2.46x
#: intra-type spread was observed 2026-08-13) fail fast with SpotMaxPriceTooLow
#: so the hunt moves on. Set <= 0 to send NO MaxPrice at all, which defaults the
#: ceiling to the on-demand price -- the highest bid EC2 accepts.
#:
#: What this knob does and does not do, corrected against evidence 2026-08-16:
#:
#: Within spot, InsufficientInstanceCapacity is a statement about physical hosts,
#: not about money -- EC2 stopped allocating by bid years ago, and the spot price
#: never exceeds on-demand. So raising the multiplier only helps when an AZ's
#: price genuinely exceeds the cap (a 2.46x intra-type spread was observed, so
#: that does happen); it cannot conjure hosts.
#:
#: BUT do not conclude that on-demand is strictly better at ACQUIRING capacity.
#: I asserted that and was wrong: on-demand's priority is about not being
#: interrupted, not about which pool has free hosts, and the two are accounted
#: separately. deepseek-v3.1 spent 2,079 ON-DEMAND attempts across 13 AZs and 4
#: regions failing with InsufficientInstanceCapacity, then landed a
#: p5en.48xlarge on SPOT within one attempt. (The landing AZ was priced $26.45/h,
#: comfortably under the $34.06 cap that had been in force, so the bid level
#: itself was probably not the operative change -- switching market was, or the
#: capacity happened to free up. Both readings survive the evidence.)
#:
#: Practical rule: when on-demand reports no capacity, TRY SPOT before concluding
#: the hardware is unavailable.
EC2_SPOT_BID_MULTIPLIER: float = float(os.getenv("EC2_SPOT_BID_MULTIPLIER", "1.25"))
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
# Post-study determinism default (2026-08-18, user directive: all model
# configurations must be deterministic): every spec below now serves the
# hinge-certified determinism bundle (DETERMINISM_ARGS, appended after this
# dict) on top of the digest-pinned EC2_VLLM_IMAGE default and a per-spec
# --revision/--tokenizer-revision pin. Prefix caching is OFF everywhere --
# it was load-bearing for THIS study's throughput (each induction quiz
# reuses one long prompt prefix across its 9 questions, each Lean theorem
# reuses its context block across 4 rungs), but the 2026-08-16 hinge
# experiment certified it as a nondeterminism source: the counter-check
# showed thousands of prefix-cache hits under the stock config and zero
# under the determinism config. The throughput cost of the swap is real and
# accepted -- --max-num-seqs 1 serializes decoding and --enforce-eager drops
# CUDA-graph capture -- and results generated under this config must NEVER
# be pooled with the family-ladder study's stock-config data (cross-config
# byte-agreement measured 0/8; see notebooks/DETERMINISM_PLAN_2026-08-16.md
# section 3). Every entry's --revision/--tokenizer-revision pins the
# checkpoint AND the tokenizer to that repo's main-branch commit SHA
# resolved 2026-08-18 (DETERMINISM_PLAN section 4 row 2). Belt-and-braces:
# at the pinned build tokenizer_revision INHERITS --revision when unset
# (vllm/config/model.py:542), so the second flag is redundant today --
# pinning both makes the pin independent of that inheritance behavior,
# on every entry, not just this one shared note.
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
    "qwen2.5-1.5b":        {"hf_model_id": "Qwen/Qwen2.5-1.5B-Instruct", "tp": 1, "max_model_len": 32768,
                            "vllm_args": ["--revision", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
                                          "--tokenizer-revision", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"]},
    # -- Qwen3.5 (Alibaba, CN): 27B dense / 122B-A10B / 397B-A17B (official FP8) --
    "qwen3.5-27b":       {"hf_model_id": "Qwen/Qwen3.5-27B", "tp": 4, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "qwen3", "--language-model-only",
                                        "--revision", "fc05daec18b0a78c049392ed2e771dde82bdf654",
                                        "--tokenizer-revision", "fc05daec18b0a78c049392ed2e771dde82bdf654"]},
    "qwen3.5-122b-a10b": {"hf_model_id": "Qwen/Qwen3.5-122B-A10B", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "qwen3", "--language-model-only",
                                        "--revision", "dc4d348443bc740c68e2d77492492c11606384d5",
                                        "--tokenizer-revision", "dc4d348443bc740c68e2d77492492c11606384d5"]},
    "qwen3.5-397b-a17b": {"hf_model_id": "Qwen/Qwen3.5-397B-A17B-FP8", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "qwen3", "--language-model-only",
                                        "--revision", "ea5b4f81096f3901c91dea97f81324302495781d",
                                        "--tokenizer-revision", "ea5b4f81096f3901c91dea97f81324302495781d"]},
    # -- Nemotron 3 (NVIDIA, US): Nano-4B / Nano-30B-A3B / Super-120B-A12B, all BF16 --
    "nemotron-3-nano-4b":         {"hf_model_id": "nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16", "tp": 1, "max_model_len": 131072,
                                   "vllm_args": ["--revision", "dfaf35de3e30f1867dd8dbc38a7fc9fb52d3914f",
                                                 "--tokenizer-revision", "dfaf35de3e30f1867dd8dbc38a7fc9fb52d3914f"]},
    "nemotron-3-nano-30b-a3b":    {"hf_model_id": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16", "tp": 4, "max_model_len": 131072,
                                   "vllm_args": ["--revision", "2d59de1cbd51c0adf384eb906b766d1aee0e0517",
                                                 "--tokenizer-revision", "2d59de1cbd51c0adf384eb906b766d1aee0e0517"]},
    "nemotron-3-super-120b-a12b": {"hf_model_id": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16", "tp": 8, "max_model_len": 131072,
                                   "vllm_args": ["--revision", "d51eab0d1f979ebc26b546e634a04f450d99158e",
                                                 "--tokenizer-revision", "d51eab0d1f979ebc26b546e634a04f450d99158e"]},
    # -- Gemma 4 (Google, US): E2B / 12B / 31B instruction-tuned --
    "gemma-4-e2b": {"hf_model_id": "google/gemma-4-E2B-it", "tp": 1, "max_model_len": 131072,
                    "vllm_args": ["--reasoning-parser", "gemma4", "--language-model-only",
                                  "--revision", "3e22461f65e89153144f8adb70e3b8c2cc9845a7",
                                  "--tokenizer-revision", "3e22461f65e89153144f8adb70e3b8c2cc9845a7"]},
    # tp=4 (2026-08-12): tier A's g6e.12xlarge capacity fallback means this
    # lane lands on 4x L40S in practice, and a 12B with ~95k-token thinking
    # budgets on ONE L40S hit the 3600s read timeout on long arms. 16 attn /
    # 8 KV heads shard cleanly; on a true single-GPU box vLLM ignores nothing
    # -- tp=4 simply requires the 4-GPU box, which the fallback list provides.
    "gemma-4-12b": {"hf_model_id": "google/gemma-4-12B-it", "tp": 4, "max_model_len": 131072,
                    "vllm_args": ["--reasoning-parser", "gemma4", "--language-model-only",
                                  "--revision", "707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7",
                                  "--tokenizer-revision", "707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7"]},
    "gemma-4-31b": {"hf_model_id": "google/gemma-4-31B-it", "tp": 4, "max_model_len": 131072,
                    "vllm_args": ["--reasoning-parser", "gemma4", "--language-model-only",
                                  "--revision", "842da3794eaa0b77d5f08bae87a17459d91ff475",
                                  "--tokenizer-revision", "842da3794eaa0b77d5f08bae87a17459d91ff475"]},
    # -- GLM-4.x (Zhipu/Z.ai, CN): 4.7-Flash / 4.5-Air / 4.7 (cross-generation, flagged) --
    "glm-4.7-flash": {"hf_model_id": "zai-org/GLM-4.7-Flash", "tp": 4, "max_model_len": 131072,
                      "vllm_args": ["--reasoning-parser", "glm47",
                                    "--revision", "7dd20894a642a0aa287e9827cb1a1f7f91386b67",
                                    "--tokenizer-revision", "7dd20894a642a0aa287e9827cb1a1f7f91386b67"]},
    "glm-4.5-air":   {"hf_model_id": "zai-org/GLM-4.5-Air", "tp": 8, "max_model_len": 131072,
                      "vllm_args": ["--reasoning-parser", "glm45",
                                    "--revision", "a24ceef6ce4f3536971efe9b778bdaa1bab18daa",
                                    "--tokenizer-revision", "a24ceef6ce4f3536971efe9b778bdaa1bab18daa"]},
    "glm-4.7":       {"hf_model_id": "zai-org/GLM-4.7", "tp": 8, "max_model_len": 131072,
                      "vllm_args": ["--reasoning-parser", "glm47",
                                    "--revision", "602d01efcdd332c5238ca4bcede555defbe83eb7",
                                    "--tokenizer-revision", "602d01efcdd332c5238ca4bcede555defbe83eb7"]},
    # -- Ministral-3 Reasoning 2512 (Mistral, FR): 3B / 8B / 14B --
    "ministral-3-3b":  {"hf_model_id": "mistralai/Ministral-3-3B-Reasoning-2512", "tp": 1, "max_model_len": 131072,
                        "vllm_args": ["--reasoning-parser", "mistral", "--language-model-only",
                                      "--revision", "4a36357c811bf511a7b625d132e12f22408aac91",
                                      "--tokenizer-revision", "4a36357c811bf511a7b625d132e12f22408aac91"],
                        "system_prompt": MINISTRAL_THINK_SYSTEM},
    "ministral-3-8b":  {"hf_model_id": "mistralai/Ministral-3-8B-Reasoning-2512", "tp": 4, "max_model_len": 131072,
                        "vllm_args": ["--reasoning-parser", "mistral", "--language-model-only",
                                      "--revision", "81eaece1948f3875421d9a45bc55487d10e2d894",
                                      "--tokenizer-revision", "81eaece1948f3875421d9a45bc55487d10e2d894"],
                        "system_prompt": MINISTRAL_THINK_SYSTEM},
    "ministral-3-14b": {"hf_model_id": "mistralai/Ministral-3-14B-Reasoning-2512", "tp": 4, "max_model_len": 131072,
                        "vllm_args": ["--reasoning-parser", "mistral", "--language-model-only",
                                      "--revision", "51f9210f3cd20f3452a80d5819d15dc61cc50630",
                                      "--tokenizer-revision", "51f9210f3cd20f3452a80d5819d15dc61cc50630"],
                        "system_prompt": MINISTRAL_THINK_SYSTEM},
    # -- EXAONE (LG AI Research, KR): 4.0-32B / 4.5-33B / K-EXAONE-236B-A23B (cross-gen, flagged) --
    "exaone-4.0-32b":    {"hf_model_id": "LGAI-EXAONE/EXAONE-4.0-32B", "tp": 4, "max_model_len": 131072,
                          "vllm_args": ["--revision", "a1d54d1c148c30881ed27e035b650da489b51b92",
                                        "--tokenizer-revision", "a1d54d1c148c30881ed27e035b650da489b51b92"]},
    "exaone-4.5-33b":    {"hf_model_id": "LGAI-EXAONE/EXAONE-4.5-33B", "tp": 4, "max_model_len": 131072,
                          "vllm_args": ["--language-model-only",
                                        "--revision", "570aa4b15a4f45ba1133072b45f50198f6e3b4fd",
                                        "--tokenizer-revision", "570aa4b15a4f45ba1133072b45f50198f6e3b4fd"]},
    "k-exaone-236b-a23b": {"hf_model_id": "LGAI-EXAONE/K-EXAONE-236B-A23B", "tp": 8, "max_model_len": 131072,
                           "vllm_args": ["--gpu-memory-utilization", "0.92",
                                         "--revision", "61e6d578eb102b578e5704e2916ac841df9eca0a",
                                         "--tokenizer-revision", "61e6d578eb102b578e5704e2916ac841df9eca0a"]},
    # -- DeepSeek (CN): V4-Flash / V3.1 / V4-Pro (cross-gen, flagged; V4 = inline template) --
    # !! V4 status (re-corrected 2026-08-12, adversarial re-read of the
    # v0.27.1 source + upstream issue traffic): the earlier "SM100-only"
    # closure was ALSO WRONG. The nvidia/model.py:316 raise sits behind
    # `use_mega_moe`, i.e. the OPT-IN `--moe-backend deep_gemm_mega_moe`
    # (never auto-selected at v0.27.1; nothing rewrites the "auto" default),
    # and we never passed that flag, so it cannot have been our crash.
    # SM90 has an in-tree serving path -- Marlin W4A16 MXFP4 experts +
    # FLASHMLA_SPARSE_DSV4 attention + fp8_ds_mla KV -- demonstrated live on
    # 4xH200 at v0.27.0 (vllm#51822; also #51743, #47769). The args below
    # pin that path instead of trusting the oracle's fallthrough. Memory:
    # Flash weights 160 GB (fits with huge headroom); Pro 865 GB (fits
    # 8xH200's 1128 GB with ~260 GB headroom -- tight, gmu 0.93). Our
    # actual construction-time crash cause remains UNDIAGNOSED (the log
    # window elided the root exception line; window since widened) -- if the
    # pinned relaunch still dies, read the full worker traceback. Known
    # hazards: vllm#47769 (Marlin repack IMA under TP+EP -- we don't enable
    # EP), vllm#49165 (FlashInfer cold-JIT race; workaround
    # VLLM_BLOCKSCALE_FP8_GEMM_FLASHINFER=0).
    # Flash moved to the SM100/B200 recipe 2026-08-13 (mirrors Pro, which
    # proved it live: healthy graphs serve + ~10 min/seed): the Marlin pin
    # and --enforce-eager are DROPPED so the native MXFP4 path serves with
    # CUDA graphs. Economics at then-current spot: 18 remaining eager seeds
    # on p5 ($20/h x ~2.4h/seed) ~= $1,040 vs ~$210-420 on p6-b200 ($41.5/h)
    # -- 2x the rate, ~15x the throughput. Do NOT serve this marlin-less
    # spec on p5/p5e/p5en (SM90 without the pin = the original undiagnosed
    # crash config). Seeds 0-11 were generated on the SM90 marlin/eager
    # stack; 12+ on SM100 native/graphs -- documented replicate-subset
    # numerics difference. --disable-custom-all-reduce kept (proven set).
    # NOTE (2026-08-18): DETERMINISM_ARGS re-adds --enforce-eager to this
    # spec; the CUDA-graph decision above is now historical.
    "deepseek-v4-flash": {"hf_model_id": "deepseek-ai/DeepSeek-V4-Flash", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "deepseek_v4", "--chat-template", DSV4_CHAT_TEMPLATE,
                                        "--tokenizer-mode", "deepseek_v4",
                                        "--attention-backend", "FLASHMLA_SPARSE_DSV4", "--kv-cache-dtype", "fp8_ds_mla",
                                        "--block-size", "256", "--disable-custom-all-reduce",
                                        "--revision", "60d8d70770c6776ff598c94bb586a859a38244f1",
                                        "--tokenizer-revision", "60d8d70770c6776ff598c94bb586a859a38244f1"]},
    "deepseek-v3.1":     {"hf_model_id": "deepseek-ai/DeepSeek-V3.1", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--revision", "c0781d039fb7a1ba2abc4add0bdc293e92d2b8db",
                                        "--tokenizer-revision", "c0781d039fb7a1ba2abc4add0bdc293e92d2b8db"]},
    # Pro now targets p6-b200 (SM100) ONLY -- the SM90 story is exhausted:
    # eager decode measured ~5-7h per induction seed (87k-token budget-burners,
    # infeasible x30), and CUDA-graph capture IMA'd on H200 twice (2026-08-12
    # inside custom_all_reduce.cuh; 2026-08-13 again with custom AR disabled,
    # teardown trace in CUDASymmetricMemory.cu). On SM100 the Marlin W4A16
    # fallback pin is DROPPED so the oracle takes the native MXFP4 expert path
    # (the deep_gemm_mega_moe raise is opt-in-only at v0.27.1 and cannot
    # auto-select); FLASHMLA_SPARSE_DSV4 accepts major in [9,10]. Graphs stay
    # ON -- that is the experiment. Do NOT serve this marlin-less spec on
    # p5/p5e/p5en: SM90 without the pin is the original undiagnosed crash
    # config. Flash still carries the proven SM90 eager set as the reference.
    # NOTE (2026-08-18): DETERMINISM_ARGS re-adds --enforce-eager to this
    # spec; the CUDA-graph decision above is now historical.
    "deepseek-v4-pro":   {"hf_model_id": "deepseek-ai/DeepSeek-V4-Pro", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "deepseek_v4", "--chat-template", DSV4_CHAT_TEMPLATE,
                                        "--tokenizer-mode", "deepseek_v4",
                                        "--attention-backend", "FLASHMLA_SPARSE_DSV4", "--kv-cache-dtype", "fp8_ds_mla",
                                        "--block-size", "256", "--disable-custom-all-reduce",
                                        "--gpu-memory-utilization", "0.93",
                                        "--revision", "b5968e9190ef611bbf34a7229255be88a0e937c1",
                                        "--tokenizer-revision", "b5968e9190ef611bbf34a7229255be88a0e937c1"]},
}

#: vLLM args certified deterministic by the 2026-08-16 hinge experiment
#: (8/8 byte-identical within one process, both probe models; cross-config
#: agreement with the study's stock config is 0/8, so results generated
#: under this bundle are NOT comparable with the family-ladder study data).
#: Byte-identical to scripts/hinge_probe.py DET_ARGS -- the certified argv.
#: Attribution across the four flags was deliberately not separated: relax
#: any one of them only after re-certifying with a hinge-style probe.
DETERMINISM_ARGS: List[str] = [
    "--no-enable-prefix-caching", "--max-num-seqs", "1",
    "--enforce-eager", "--seed", "0",
]

for _spec_key, _spec in EC2_DEPLOY_SPECS.items():
    _args = list(_spec.get("vllm_args") or [])
    assert "--enable-prefix-caching" not in _args, _spec_key
    assert not ({a for a in DETERMINISM_ARGS if a.startswith("--")} & set(_args)), _spec_key
    # Plan §4 row 4: make the KV budget a function of the spec, not of free
    # VRAM at profiling time. 0.92 == vLLM's default AT THE PINNED BUILD
    # (vllm/config/cache.py:69 at 8efa13b70), made explicit -- and the value
    # the hinge det arms actually resolved to (their cache_config_info
    # records gpu_memory_utilization=0.92), so this changes nothing that
    # experiment certified. deepseek-v4-pro (0.93) keeps its larger
    # footprint; k-exaone's explicit 0.92 now coincides with the default.
    if "--gpu-memory-utilization" not in _args:
        _args += ["--gpu-memory-utilization", "0.92"]
    _spec["vllm_args"] = _args + DETERMINISM_ARGS

#: ``num_attention_heads`` per family-ladder checkpoint, copied from each
#: model's config.json (scripts/arch/arch_configs_raw.json is the archived
#: source; test_deploy_specs drift-pins this map against it). Used by
#: `derive_tp` -- models absent here (e.g. the qwen2.5-1.5b canary) fall back
#: to their spec's static ``tp``.
MODEL_ATTENTION_HEADS = {
    "deepseek-v3.1": 128,
    "deepseek-v4-flash": 64,
    "deepseek-v4-pro": 128,
    "exaone-4.0-32b": 40,
    "exaone-4.5-33b": 40,
    "gemma-4-12b": 16,
    "gemma-4-31b": 32,
    "gemma-4-e2b": 8,
    "glm-4.5-air": 96,
    "glm-4.7": 96,
    "glm-4.7-flash": 20,
    "k-exaone-236b-a23b": 64,
    "ministral-3-14b": 32,
    "ministral-3-3b": 32,
    "ministral-3-8b": 32,
    "nemotron-3-nano-30b-a3b": 32,
    "nemotron-3-nano-4b": 40,
    "nemotron-3-super-120b-a12b": 32,
    "qwen3.5-122b-a10b": 32,
    "qwen3.5-27b": 24,
    "qwen3.5-397b-a17b": 32,
}

#: GPU count per instance type this provider hunts. Unknown types make
#: `derive_tp` fall back to the spec's static ``tp`` rather than guess.
_INSTANCE_GPU_COUNTS = {
    "g6e.xlarge": 1, "g6e.2xlarge": 1, "g6e.4xlarge": 1, "g6e.8xlarge": 1,
    "g6e.16xlarge": 1, "g6e.12xlarge": 4, "g6e.24xlarge": 4, "g6e.48xlarge": 8,
    # g7 = RTX PRO 4500 (32GB), g7e = RTX PRO 6000 (96GB); both SM120,
    # PCIe-only. Counts verified via describe-instance-types 2026-08-14,
    # ALL sizes this time (note the 12xlarge sizes carry TWO GPUs, unlike
    # g6e's four): a partially-mapped family is worse than an unmapped one,
    # because a lane whose --types spans a mapped and an unmapped size gets
    # derived tp on one box and spec-fallback tp on the other -- a silent
    # mid-lane tp change (2026-08-14 peer audit: the ministral g7.24xlarge
    # fleet ran the fallback path and was correct only by coincidence).
    "g7.2xlarge": 1, "g7.4xlarge": 1, "g7.8xlarge": 1,
    "g7.12xlarge": 2, "g7.24xlarge": 4, "g7.48xlarge": 8,
    "g7e.2xlarge": 1, "g7e.4xlarge": 1, "g7e.8xlarge": 1,
    "g7e.12xlarge": 2, "g7e.24xlarge": 4, "g7e.48xlarge": 8,
    "p4d.24xlarge": 8,
    "p5.4xlarge": 1,
    "p5.48xlarge": 8, "p5e.48xlarge": 8, "p5en.48xlarge": 8,
    "p6-b200.48xlarge": 8, "p6-b300.48xlarge": 8,
}


def derive_tp(model: str, instance_type: str, spec: Dict[str, Any]) -> int:
    """Tensor-parallel degree for `model` on the box that actually landed.

    ``tp = gcd(num_attention_heads, gpu_count)`` -- the largest head-divisor
    that also divides the landed GPU count, so every GPU the hunt paid for is
    used whenever head divisibility allows (2026-08-13 fleet audit: a tp=1
    spec landing on a 4-GPU g6e.12xlarge idled 3 of 4 L40S). The static
    ``spec["tp"]`` remains the fallback for models or instance types this
    module doesn't know.

    Parameters
    ----------
    model : str
        Deploy-spec key (e.g. ``"gemma-4-12b"``).
    instance_type : str
        The landed instance type from the provision state.
    spec : Dict[str, Any]
        The model's ``EC2_DEPLOY_SPECS`` entry (fallback ``tp`` source).

    Returns
    -------
    int
        Tensor-parallel degree, always >= 1.
    """
    heads = MODEL_ATTENTION_HEADS.get(model)
    gpus = _INSTANCE_GPU_COUNTS.get(instance_type)
    if heads is None or gpus is None:
        if heads is not None and instance_type:
            # A known model on an unmapped instance type is the dangerous
            # fallback: if a lane's hunt spans mapped AND unmapped types, the
            # spec tp used here can differ from the derived tp on the mapped
            # box -- a silent mid-lane tp change. Loud so the gap gets mapped.
            logging.warning(
                f"derive_tp: instance type {instance_type!r} not in "
                f"_INSTANCE_GPU_COUNTS; falling back to spec tp="
                f"{spec.get('tp', 1)} for {model!r} -- add the type's GPU "
                "count to keep tp derivation consistent across a lane"
            )
        return spec.get("tp", 1)
    tp = max(1, math.gcd(heads, gpus))
    if tp < gpus:
        # Correct but wasteful: head divisibility strands GPUs (e.g. 20
        # heads on an 8-GPU box -> tp=4, four GPUs idle). Loud, so a
        # half-used expensive box is visible rather than silent.
        logging.warning(
            f"derive_tp: {model!r} on {instance_type} uses tp={tp} of {gpus} "
            f"GPUs ({heads} attention heads don't divide further) -- "
            f"{gpus - tp} GPUs will sit idle"
        )
    return tp


#: GPU marketing name + memory per instance FAMILY (the type prefix before
#: the size dot). Purely descriptive -- consumed by ``server_config`` so a
#: result file names its silicon without the reader needing this module's
#: type tables. p6 families keep their full hyphenated prefix.
_INSTANCE_GPU_NAMES = {
    "g6e": "L40S 48GB", "g7": "RTX PRO 4500 32GB", "g7e": "RTX PRO 6000 96GB",
    "p4d": "A100 40GB", "p5": "H100 80GB", "p5e": "H200 141GB",
    "p5en": "H200 141GB", "p6-b200": "B200 180GB", "p6-b300": "B300 288GB",
}


#: Optional hardware pin, ``"<gpu-name-substring>:<count>"`` (e.g. ``"L40S:1"``).
#: When set, a lane REFUSES to serve on a box whose silicon does not match.
#:
#: WHY: widening ``EC2_INSTANCE_TYPES`` to escape a capacity wall is the
#: obvious move and a silent confound -- on 2026-08-14 two repair lanes that
#: were completing cells generated on g6e.4xlarge landed on g6e.2xlarge
#: instead. That case was benign (both carry exactly one L40S, so GPU and tp
#: were unchanged) and the user accepted it, but nothing in the system had
#: CHECKED that; the widened list would equally have accepted a 4-GPU
#: g6e.12xlarge, changing derived tp mid-lane. Pin the silicon, not the
#: instance size: it permits the harmless substitution and blocks the
#: contaminating one.
EC2_REQUIRE_GPU: str = os.getenv("EC2_REQUIRE_GPU", "")


def _assert_required_gpu(state: Dict[str, Any], model: str) -> None:
    """Raises when the landed box's GPU does not match ``EC2_REQUIRE_GPU``.

    Fails BEFORE the container swap, so a mismatched box never generates a
    single row. No-ops when the pin is unset (the default) or when the landed
    instance type is absent from this module's tables -- an unknown type is
    reported rather than silently treated as a match.
    """
    if not EC2_REQUIRE_GPU:
        return
    want_name, _, want_count = EC2_REQUIRE_GPU.partition(":")
    itype = str(state.get("instance_type") or "")
    got_count = _INSTANCE_GPU_COUNTS.get(itype)
    got_name = _INSTANCE_GPU_NAMES.get(itype.split(".", 1)[0])
    if got_name is None or got_count is None:
        raise RuntimeError(
            f"EC2_REQUIRE_GPU={EC2_REQUIRE_GPU!r} is set but instance type "
            f"{itype!r} is not in this module's GPU tables, so its silicon "
            "cannot be checked. Add it to _INSTANCE_GPU_COUNTS/_NAMES or drop "
            "the pin -- refusing to serve unverified hardware."
        )
    if want_name.strip() not in got_name or (want_count and got_count != int(want_count)):
        raise RuntimeError(
            f"hardware pin violated for lane {model!r}: EC2_REQUIRE_GPU="
            f"{EC2_REQUIRE_GPU!r} but {itype} carries {got_count}x {got_name}.\n"
            "Serving here would generate rows on different silicon from the "
            "rest of the lane. Wait for the pinned hardware, or clear the pin "
            "deliberately and record the change."
        )


# Short, separate timeout for server_config()'s best-effort LIVE probes
# (vLLM /version, /metrics, the agent /status). Deliberately much shorter than
# the on-instance polling timeouts above (_AGENT_POLL_S etc.): server_config
# is provenance, typically called once per replicate batch, and a slow/dead
# endpoint must degrade a handful of fields to None in seconds, not make an
# eval batch wait on a field that is allowed to be missing.
_SERVER_CONFIG_PROBE_TIMEOUT_S: int = 5


def _fetch_vllm_version(ip: str, vllm_api_key: str) -> Optional[str]:
    """The ``version`` string from vLLM's ``GET /version``, or None.

    Mirrors ``scripts/hinge_probe.py``'s ``fingerprint()`` request shape
    (Bearer the vLLM api key, short timeout) rather than inventing a new
    pattern -- that function is the one place this study already proved a
    ``/version`` probe works against a live box (DETERMINISM_PLAN section 3).
    """
    try:
        r = requests.get(
            f"http://{ip}:{EC2_VLLM_PORT}/version",
            headers={"Authorization": f"Bearer {vllm_api_key}"},
            timeout=_SERVER_CONFIG_PROBE_TIMEOUT_S,
        )
        return r.json().get("version") if r.ok else None
    except Exception:  # noqa: BLE001 -- best-effort provenance, never raises
        return None


def _fetch_vllm_cache_config(ip: str, vllm_api_key: str) -> Optional[List[str]]:
    """Raw Prometheus line(s) mentioning ``cache_config_info``, or None.

    Deliberately UNPARSED: the line's labels carry ``num_gpu_blocks`` /
    ``gpu_memory_utilization`` / ``block_size``, and vLLM's exact label set
    has moved across the builds this study observed (DETERMINISM_PLAN section
    1.4) -- storing the raw line survives that drift; a parsed dict would not.
    """
    try:
        r = requests.get(
            f"http://{ip}:{EC2_VLLM_PORT}/metrics",
            headers={"Authorization": f"Bearer {vllm_api_key}"},
            timeout=_SERVER_CONFIG_PROBE_TIMEOUT_S,
        )
        if not r.ok:
            return None
        lines = [
            line for line in r.text.splitlines()
            if "cache_config_info" in line and not line.startswith("#")
        ]
        return lines or None
    except Exception:  # noqa: BLE001
        return None


def _fetch_agent_fingerprint(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The control agent's ``/status`` ``"fingerprint"`` object, or None.

    Reuses ``_agent`` -- the same authenticated control-agent call
    ``_wait_model_ready`` already polls with -- instead of hand-rolling a
    second HTTP client against the same endpoint. ``connect_retries=0``:
    this is a best-effort snapshot, not a wait loop, so a single failed
    attempt degrades to None rather than retrying for minutes.
    """
    try:
        status = _agent(
            state, "GET", "/status",
            timeout=_SERVER_CONFIG_PROBE_TIMEOUT_S, connect_retries=0,
        )
        return status.get("fingerprint")
    except Exception:  # noqa: BLE001
        return None


def server_config(model: str) -> Optional[Dict[str, Any]]:
    """Serving-stack snapshot for `model` on the currently provisioned box.

    Built for result provenance: stamped onto every stored replicate
    (``Marks.server_config`` via ``ReplicateHarness.run_replicates``) and
    written as a deduction run's ``server_config.yaml`` sidecar, so results
    self-describe their hardware instead of needing a timestamp->config side
    table (the 2026-08-13 confound audit had to reconstruct exactly that
    because none of this was logged).

    Extended per ``notebooks/DETERMINISM_PLAN_2026-08-16.md`` section 5: the
    original 8 fields describe the BOX; the fields added here describe the
    ACTUAL serving process on it (the launched argv, the running vLLM build,
    the loaded checkpoint's on-disk identity, the GPU as observed rather than
    looked up in a static table) -- exactly the data that section's two-regime
    mystery needed and did not have.

    Parameters
    ----------
    model : str
        Deploy-spec key (e.g. ``"gemma-4-12b"``).

    Returns
    -------
    Optional[Dict[str, Any]]
        A dict with these keys; unknown/unreachable pieces are None rather
        than omitted, so readers see the schema even from a half-built
        snapshot. Returns None outright when no snapshot could be built at
        all (state-file read itself raised).

        State/spec-derived (original 8, box-only -- no network calls)::

            instance_type, gpu (e.g. "2x RTX PRO 4500 32GB", from a static
              table keyed by instance type -- NOT an nvidia-smi observation;
              see ``nvidia_smi`` below for that), tp, region,
              availability_zone, instance_id, vllm_image (the configured
              tag/digest reference, ``EC2_VLLM_IMAGE`` -- a MUTABLE tag is not
              a digest; see ``vllm_image_digest`` below for the resolved
              one), hf_model_id (the deploy spec's pin, not necessarily what
              is actually loaded -- see ``agent_fingerprint.hf_snapshots``).

        ``state["last_serve"]``-derived (the ARGV ``serve_model`` actually
        POSTed to the agent, stashed by that function -- see its docstring;
        None for every field below when no ``last_serve`` is recorded, or
        when its ``"model"`` does not match ``model`` -- i.e. the box is
        currently serving something else and these fields must not be
        misattributed to it)::

            vllm_args (List[str], the extra CLI flags actually sent),
            max_model_len (int, actually sent), served_at (str, UTC
            ISO-8601 timestamp of that ``/serve`` call).

        Live network probes (best-effort; short timeout; None on any
        failure, including "no box provisioned")::

            vllm_version (str, the ``"version"`` field of vLLM's own
              ``GET /version`` -- the build string, e.g.
              ``"0.27.2rc1.dev122+g8efa13b70"``), vllm_cache_config
              (List[str], the raw, UNPARSED Prometheus line(s) containing
              ``cache_config_info`` from ``GET /metrics`` -- carries
              num_gpu_blocks/gpu_memory_utilization/block_size as labels),
              agent_fingerprint (Dict[str, Any], the control agent's own
              best-effort snapshot -- see ``payloads/agent.py.txt``'s
              ``fingerprint()``: ``image_repo_digests`` (List[str] or None),
              ``nvidia_smi`` (str, one CSV row from ``nvidia-smi
              --query-gpu=...`` -- an OBSERVATION, unlike the static ``gpu``
              field above), ``hf_snapshots`` (List[str] of snapshot dirnames
              actually on disk for the served repo -- the resolved
              revision(s), settling "different weights vs different kernels"
              per DETERMINISM_PLAN section 1), ``weights_digest`` (str
              sha256 hex of the safetensors index + per-file sizes for the
              latest snapshot -- NOT a full weights read); vllm_image_digest
              (str, the first element of
              ``agent_fingerprint["image_repo_digests"]`` if present, else
              None -- the resolved digest, in contrast to the mutable
              ``vllm_image`` tag above).

        Client-side config (populated regardless of box state -- these are
        env-var reads, not observations of the box, so "no box" does not
        degrade them; mirrors the existing ``vllm_image``/``hf_model_id``
        precedent of recording config that does not require a live box)::

            max_parallel_requests (int, ``EC2_MAX_PARALLEL_REQUESTS`` read at
              call time via ``ChatClient._default_max_parallel`` -- default
              8; this module never calls ``os.getenv("EC2_MAX_PARALLEL_REQUESTS")``
              directly, the env var is composed dynamically as
              ``f"{env_prefix}_MAX_PARALLEL_REQUESTS"`` in
              ``openai_compat.ChatClient``, reused here rather than
              re-deriving the literal name), stream (bool,
              ``EC2_STREAM_COMPLETIONS`` read at call time via
              ``ChatClient._flag``). Both parse an env var and are
              individually guarded (None on a malformed override, e.g.
              ``EC2_STREAM_COMPLETIONS=true`` instead of ``"1"``) so one bad
              env value degrades only itself, not the whole snapshot.

    Notes
    -----
    NEVER raises: provenance is a passenger, and a lane must not crash (and
    crash-loop under its babysitter) because a snapshot field was missing.
    Reads the state file at call time -- call it INSIDE the ``serve_model``
    block so the landed instance it describes is the one that serves. The
    live network probes add at most a few seconds (bounded by
    ``_SERVER_CONFIG_PROBE_TIMEOUT_S``) and never touch anything that could
    slow or break serving itself -- they are read-only GETs against
    endpoints vLLM/the agent already expose.
    """
    try:
        state = _load_state() or {}
        spec = EC2_DEPLOY_SPECS.get(model, {})
        itype = state.get("instance_type") or ""
        gpus = _INSTANCE_GPU_COUNTS.get(itype)
        name = _INSTANCE_GPU_NAMES.get(itype.split(".", 1)[0])

        # The ACTUAL launched argv, not the (possibly since-edited) spec --
        # see serve_model's "last_serve" stash. Only trusted when it names
        # THIS model: a stale last_serve from a previous swap on the same box
        # must not be misattributed to whatever is being asked about now.
        last_serve = state.get("last_serve") or {}
        last_serve_matches = bool(state) and last_serve.get("model") == model
        vllm_args = last_serve.get("vllm_args") if last_serve_matches else None
        max_model_len = last_serve.get("max_model_len") if last_serve_matches else None
        served_at = last_serve.get("served_at") if last_serve_matches else None

        # Live probes: only attempted with enough of the state to reach the
        # box at all; otherwise short-circuit to None without a doomed call.
        ip = state.get("public_ip")
        vllm_key = state.get("vllm_api_key")
        vllm_version = _fetch_vllm_version(ip, vllm_key) if ip and vllm_key else None
        vllm_cache_config = _fetch_vllm_cache_config(ip, vllm_key) if ip and vllm_key else None
        agent_fp = _fetch_agent_fingerprint(state) if ip else None
        vllm_image_digest = None
        if agent_fp:
            digests = agent_fp.get("image_repo_digests")
            if digests:
                vllm_image_digest = digests[0]

        # Individually guarded (not just the function-wide except below):
        # both parse an env var, and a malformed override (e.g.
        # EC2_STREAM_COMPLETIONS=true instead of "1") must degrade only
        # THIS field to None -- letting it escape to the outer except would
        # blank the entire snapshot over one bad env value, breaking the
        # "each field None when unavailable" contract for every other field
        # that had already been computed successfully.
        try:
            max_parallel_requests = _CLIENT._default_max_parallel()
        except Exception:  # noqa: BLE001
            max_parallel_requests = None
        try:
            stream = _CLIENT._flag("STREAM_COMPLETIONS")
        except Exception:  # noqa: BLE001
            stream = None

        return {
            "instance_type": itype or None,
            "gpu": f"{gpus}x {name}" if gpus and name else None,
            "tp": derive_tp(model, itype, spec),
            "region": state.get("region"),
            "availability_zone": state.get("availability_zone"),
            "instance_id": state.get("instance_id"),
            "vllm_image": EC2_VLLM_IMAGE,
            "hf_model_id": spec.get("hf_model_id"),
            "vllm_args": vllm_args,
            "max_model_len": max_model_len,
            "served_at": served_at,
            "vllm_version": vllm_version,
            "vllm_cache_config": vllm_cache_config,
            "agent_fingerprint": agent_fp,
            "vllm_image_digest": vllm_image_digest,
            "max_parallel_requests": max_parallel_requests,
            "stream": stream,
        }
    except Exception:  # noqa: BLE001 -- see Notes: provenance never crashes a lane
        logging.warning("server_config: could not snapshot the serving config", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Internal poll/timeout tuning: implementation detail, NOT env-configurable
# like the EC2_* knobs above -- these bound how chattily this module polls
# AWS/the instance, not anything a notebook run should need to tune.
# ---------------------------------------------------------------------------
# _wait_public_ip: how long to wait for DescribeInstances to report a public
# IP after launch, and how often to re-poll while waiting.
_WAIT_IP_TIMEOUT_S: int = 300
_WAIT_IP_POLL_S: int = 5
# Consecutive "absent" DescribeInstances polls tolerated after RunInstances
# before concluding the instance is really gone (~30s at _WAIT_IP_POLL_S=5;
# the eventual-consistency window is typically a few seconds).
_ABSENT_STREAK_LIMIT: int = 6
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
# exposed there as string constants and rendered by payloads.render_user_data,
# then gzip-compressed by payloads.pack_user_data (both imported at the top of
# this module) before riding into RunInstances' UserData kwarg. See that
# package's docstring for the payload contract (py3.10/stdlib-only, 16 KB
# user-data budget -- now measured post-compression) and
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


def _decode_user_data(raw: bytes) -> str:
    """Decodes base64-decoded user-data bytes back into the rendered script.

    User-data has shipped gzip-compressed (via ``payloads.pack_user_data``)
    since the 2026-08-18 determinism change, so this gunzips first. A
    ``gzip.BadGzipFile`` falls back to treating ``raw`` as plain UTF-8 text --
    the pre-compression format every instance shipped before that change, and
    a live instance can outlive the code change that provisioned it (this is
    exactly the codepath ``_recover_state_from_instance`` uses to rebuild
    state for an instance the local state file has lost track of).

    Parameters
    ----------
    raw : bytes
        Already base64-DEcoded user-data, straight from
        ``DescribeInstanceAttribute``'s ``UserData.Value`` (which itself is
        base64 text over the wire; the caller decodes that layer first).

    Returns
    -------
    str
        The rendered cloud-init script, UTF-8 decoded.

    Raises
    ------
    UnicodeDecodeError, EOFError
        UnicodeDecodeError if `raw` is neither valid gzip nor valid UTF-8
        text; EOFError if it is gzip-magic-prefixed but truncated (the magic
        matches, so BadGzipFile never fires). Both are left to propagate to
        the caller's own
        best-effort ``except Exception``, matching the pre-existing recovery
        contract (return ``None`` rather than crash).
    """
    try:
        return gzip.decompress(raw).decode()
    except gzip.BadGzipFile:
        return raw.decode()


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
        user_data = _decode_user_data(base64.b64decode(attr["UserData"]["Value"]))
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
        If the instance transitions to ``shutting-down``/``terminated``
        before ever getting an IP (spot reclaimed right after launch), or
        stays absent from DescribeInstances for ``_ABSENT_STREAK_LIMIT``
        consecutive polls (a single absent poll is tolerated as eventual
        consistency, observed live 2026-08-14 during a quota-race relaunch).
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

    absent_streak = 0

    def check() -> Optional[str]:
        nonlocal absent_streak
        instance = _describe_instance(region, instance_id)
        # NOTE: NOT using _instance_state(region, instance_id) here -- this
        # site also needs PublicIpAddress from the SAME describe result right
        # below, and the helper would cost a second DescribeInstances call
        # for state alone. See _instance_state's docstring.
        inst_state = (instance or {}).get("State", {}).get("Name", "absent")
        if inst_state == "absent":
            # DescribeInstances is eventually consistent: a just-launched
            # instance can be invisible for several seconds even though it is
            # coming up fine (a truly reclaimed instance stays describable as
            # "terminated" for ~an hour -- it does not vanish). Only a
            # sustained streak means the instance is really gone.
            absent_streak += 1
            if absent_streak < _ABSENT_STREAK_LIMIT:
                return None
        else:
            absent_streak = 0
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


def _spot_price_map(region: str, instance_types: List[str]) -> Dict[Tuple[str, str], float]:
    """Current spot price per ``(instance_type, availability_zone)`` in `region`.

    Newest observation wins (``describe_spot_price_history`` returns rows
    newest-first). STRICTLY best-effort: any API failure returns ``{}`` so the
    capacity hunt degrades to its pre-2026-08-13 price-blind behaviour instead
    of dying -- pricing must never cost a lane its box.

    Parameters
    ----------
    region : str
        Region to query.
    instance_types : List[str]
        Instance types to price.

    Returns
    -------
    Dict[Tuple[str, str], float]
        ``{(instance_type, az): usd_per_hour}``; empty on any failure.
    """
    try:
        resp = _ec2_client(region).describe_spot_price_history(
            InstanceTypes=instance_types,
            ProductDescriptions=["Linux/UNIX"],
        )
        prices: Dict[Tuple[str, str], float] = {}
        for row in resp.get("SpotPriceHistory", []):
            prices.setdefault(
                (row["InstanceType"], row["AvailabilityZone"]), float(row["SpotPrice"])
            )
        return prices
    except Exception as exc:  # noqa: BLE001 -- pricing is advisory only
        logging.info(f"_spot_price_map: {region} lookup failed ({exc}); hunting price-blind")
        return {}


def _run_instances_kwargs(
    ami: str,
    instance_type: str,
    subnet_id: str,
    group_id: str,
    root_device: str,
    volume_gb: int,
    user_data: bytes,
    key_name: str,
    iam_profile: Optional[str],
    capacity_reservation_id: Optional[str] = None,
    max_price: Optional[str] = None,
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
    user_data : bytes
        Gzip-compressed cloud-init script (see ``payloads.pack_user_data``);
        passed through unencoded -- boto3 base64-encodes bytes ``UserData``
        directly (see ``base64_encode_user_data`` in botocore's handlers).
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
    max_price : Optional[str]
        Spot bid ceiling in USD/hour (stringified, as the API wants). When
        ``None`` the ceiling stays at EC2's default (the on-demand price) --
        the 2026-08-13 fleet audit found the price-blind default paying
        1.29-1.48x each type's cheapest AZ against a 2.46x intra-type
        spread, so `provision_spot_instance` now derives a cap from live
        ``describe_spot_price_history`` medians. A bid under an AZ's current
        price fails fast with ``SpotMaxPriceTooLow`` (a tolerated
        capacity-hunt code), moving the hunt to the next AZ.

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
                # MaxPrice added below only when the caller derived a cap --
                # omitting it keeps EC2's default ceiling (the on-demand
                # price), the pre-2026-08-13 behaviour.
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
    elif EC2_MARKET == "on-demand":
        # On-demand is expressed by the ABSENCE of InstanceMarketOptions --
        # there is no MarketType="on-demand". MaxPrice goes with it: an
        # on-demand launch has no bid.
        #
        # Used 2026-08-15 for deduction lane deepseek-v3.1, whose 415 dead
        # cells could not be regenerated because p5e.48xlarge spot had zero
        # capacity in every AZ for an entire night. The instance type, GPU
        # count and tp are IDENTICAL to the lane's original box -- only how
        # the capacity was purchased differs, so nothing about what ran
        # changes. InstanceInitiatedShutdownBehavior stays "terminate" and the
        # idle watchdog still fires, which matters far more here: an
        # abandoned on-demand p5e bills at full rate indefinitely, where an
        # abandoned spot box is at least reclaimable.
        kwargs.pop("InstanceMarketOptions", None)
    elif max_price:
        kwargs["InstanceMarketOptions"]["SpotOptions"]["MaxPrice"] = max_price
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
    # gzip-compressed (pack_user_data) rather than passed raw: raw headroom
    # under EC2's 16 KB cap was 7 bytes BEFORE the digest-pinned
    # EC2_VLLM_IMAGE reference, which put the raw render 57 bytes OVER the
    # cap. Compressed bytes flow
    # straight into run_instances(UserData=...) -- boto3 base64-encodes
    # bytes UserData directly, so no manual encoding step is needed.
    user_data = pack_user_data(
        render_user_data(
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

    # Price the whole hunt space up front (one best-effort call per region;
    # {} on failure = price-blind fallback). Each type's bid cap is 1.25x the
    # median of its observed AZ prices across ALL hunted regions: enough
    # headroom that a normal-priced AZ always clears it, while the outlier
    # AZs (2.46x intra-type spread observed 2026-08-13) fail fast with
    # SpotMaxPriceTooLow and the hunt moves on.
    spot_prices: Dict[str, Dict[Tuple[str, str], float]] = {
        r: _spot_price_map(r, list(instance_types)) for r in regions
    }
    type_caps: Dict[str, Optional[str]] = {}
    for _type in instance_types:
        observed = sorted(
            price
            for region_map in spot_prices.values()
            for (obs_type, _az), price in region_map.items()
            if obs_type == _type
        )
        if observed and EC2_SPOT_BID_MULTIPLIER > 0:
            median = observed[len(observed) // 2]
            type_caps[_type] = f"{EC2_SPOT_BID_MULTIPLIER * median:.4f}"
            logging.info(
                f"provision_spot_instance: {_type} bid cap ${type_caps[_type]}/h "
                f"({EC2_SPOT_BID_MULTIPLIER}x median of {len(observed)} AZ prices, "
                f"range ${observed[0]:.2f}-${observed[-1]:.2f})"
            )
        else:
            # No MaxPrice: the ceiling defaults to the ON-DEMAND price, which is
            # the highest bid EC2 accepts and the highest you can ever pay for
            # spot. Reached either because pricing lookup failed (price-blind
            # fallback) or because EC2_SPOT_BID_MULTIPLIER <= 0 asked for it.
            type_caps[_type] = None
            if EC2_SPOT_BID_MULTIPLIER <= 0:
                logging.info(
                    f"provision_spot_instance: {_type} bidding UNCAPPED "
                    "(EC2_SPOT_BID_MULTIPLIER<=0) -- ceiling is the on-demand "
                    "price, the maximum EC2 allows."
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
            # Cheapest AZ first; unpriced AZs keep their original order after
            # the priced ones (inf sorts last, sort is stable).
            region_prices = spot_prices.get(region, {})
            subnets_by_price = sorted(
                info["subnets"],
                key=lambda pair: region_prices.get((instance_type, pair[1]), float("inf")),
            )
            for subnet_id, az in subnets_by_price:
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
                    max_price=type_caps.get(instance_type),
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
    # Check the silicon BEFORE swapping the container: a mismatched box must
    # not generate even one row (see EC2_REQUIRE_GPU).
    _assert_required_gpu(state, model)
    serve_payload = {
        "served_model_name": model,
        "hf_model_id": spec["hf_model_id"],
        # Derived from the box that actually landed, not pinned per spec:
        # the hunt list can hand one lane boxes with different GPU counts.
        "tp": derive_tp(model, state.get("instance_type", ""), spec),
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
    # §5 provenance (DETERMINISM_PLAN_2026-08-16.md): a SEPARATE record from
    # ``state["serving"]`` above. That dict exists only to short-circuit the
    # already-serving fast path and mirrors the wire payload's own key names
    # (``served_model_name`` etc.); ``last_serve`` is what server_config()
    # reads back under stable, self-describing keys, so a spec edited mid-
    # study (or read long after the box that served it is gone) is still
    # visible as the argv that actually launched, not just the spec that was
    # asked for.
    state["last_serve"] = {
        "model": model,
        "hf_model_id": spec["hf_model_id"],
        "tp": serve_payload["tp"],
        "max_model_len": serve_payload["max_model_len"],
        "vllm_args": list(serve_payload["vllm_args"]),
        "image": EC2_VLLM_IMAGE,
        "served_at": datetime.now(timezone.utc).isoformat(),
    }
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
