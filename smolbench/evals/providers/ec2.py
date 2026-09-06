"""
Serve models from a self-provisioned EC2 Spot instance.

One large Spot box per experiment runs vLLM's OpenAI-compatible server in
Docker; sections swap WHICH model it serves rather than provisioning new
hardware, because multi-GPU SageMaker endpoint quotas default to 0 while Spot
P5 capacity is available. One lifecycle step per notebook cell::

    state = provision_spot_instance()   # idempotent; once at notebook start
    with serve_model(DENSE_MODEL):      # per archetype section
        marks = evaluate(quiz, DENSE_MODEL, SEED)
    shutdown_instance()                 # once at notebook end

Provisioning records the box in ``EC2_STATE_FILE`` (repo root, mode 0600,
gitignored) and tags it ``smolbench:experiment``, so a re-run reattaches --
rebuilding lost state from the tagged instance's user-data -- instead of
launching a second box. ``serve_model`` tears NOTHING down on exit;
abandonment is covered by the on-instance idle watchdog
(``EC2_IDLE_TIMEOUT_MIN`` without requests, after an ``EC2_STARTUP_GRACE_MIN``
load grace), a boot-scheduled ``shutdown -h +EC2_MAX_LIFETIME_MIN``, and
one-time Spot with InstanceInitiatedShutdownBehavior=terminate, so any OS
shutdown terminates the box and deletes its EBS volume.

Why EC2 rather than SageMaker
    The SageMaker path still exists (``providers/aws.py``'s
    ``provision_endpoint``) but multi-GPU endpoint quotas default to 0 (one
    Service Quotas ticket per instance type), endpoints bill on-demand with
    no spot market, and its vLLM DLC is configured only through a few env
    vars -- no argv plumbing -- so it cannot serve this module's
    digest-pinned image, per-spec ``--revision`` pins, or
    ``DETERMINISM_ARGS``.

Env-read timing
    Provisioning ``EC2_*`` constants are captured at IMPORT time -- set them
    before the first import (e.g. keys.env). Read at CALL time:
    ``EC2_INFERENCE_BASE_URL``, ``EC2_VLLM_API_KEY``, ``EC2_STATE_FILE``,
    ``EC2_CAPACITY_RESERVATION`` (and ``EC2_CAPACITY_RESERVATION_REGION``),
    ``HF_TOKEN``, and the shared client's own ``EC2_MAX_PARALLEL_REQUESTS`` /
    ``EC2_STREAM_COMPLETIONS`` / ``EC2_INFO`` / ``EC2_INFO_RESPONSE``.
    Setup needs ``INFERENCE_PROVIDER=ec2``, ``AWS_REGION`` (first region
    tried, more via ``EC2_REGIONS``), boto3-resolvable credentials, and
    ``HF_TOKEN`` only for gated repos (baked into user-data at provision
    time). boto3/botocore import lazily, so the inference path needs neither.
    The ``model`` argument to query()/evaluate() is an ``EC2_DEPLOY_SPECS``
    key, which is also vLLM's ``--served-model-name``.

Security model
    Ports 8000 (vLLM) and 9000 (agent) are open ONLY to the caller's public IP
    /32, re-asserted by every provisioning call -- re-run it if your IP
    changes. Both are plain HTTP behind a per-experiment random token held in
    the state file and in user-data (readable in-account via
    DescribeInstanceAttribute); accepted for a short-lived single-user box.
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
from smolbench.evals.results_store import parse_s3_uri, repo_root
from smolbench.evals.study_config import load_study_config

AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
# Spot capacity hunt order, tried TYPE-MAJOR: each type across every region
# before falling back to the next type. p5e = 8xH200/1128 GB VRAM, p5 =
# 8xH100/640 GB. Both lists are runtime-filtered against
# describe_instance_type_offerings, so listing a region a type has not
# reached yet is harmless.
EC2_INSTANCE_TYPES: Tuple[str, ...] = tuple(
    dict.fromkeys(
        t.strip()
        for t in os.getenv("EC2_INSTANCE_TYPES", "p5e.48xlarge,p5.48xlarge").split(",")
        if t.strip()
    )
)
# Default region list comes from the committed study config's [fleet].regions
# (smolbench/evals/study_config.toml), not a second hand-copied literal here.
# AWS_REGION still leads (a caller's own region is tried first, exactly as
# before) and the EC2_REGIONS environment override below is unchanged;
# study_config imports only the stdlib, so importing it here adds no cycle.
_DEFAULT_REGIONS: str = ",".join(
    dict.fromkeys((AWS_REGION, *load_study_config().fleet.regions))
)
EC2_REGIONS: Tuple[str, ...] = tuple(
    dict.fromkeys(
        r.strip() for r in os.getenv("EC2_REGIONS", _DEFAULT_REGIONS).split(",") if r.strip()
    )
)
# Root gp3 volume: OS and docker image only. The model cache lives on
# instance-store NVMe (bootstrap formats and mounts the first device at
# /opt/hf-cache) to dodge gp3's 1000 MB/s ceiling; every targeted type has
# one (p5e/p5/p4de/g5/g6). On a type WITHOUT instance store the cache falls
# back to the root volume -- raise EC2_ROOT_VOLUME_GB to hold your
# checkpoints (the largest roster entry, deepseek-v4-pro, is ~865 GB).
EC2_ROOT_VOLUME_GB: int = int(os.getenv("EC2_ROOT_VOLUME_GB", "300"))
EC2_ROOT_VOLUME_THROUGHPUT: int = int(os.getenv("EC2_ROOT_VOLUME_THROUGHPUT", "500"))
EC2_ROOT_VOLUME_IOPS: int = int(os.getenv("EC2_ROOT_VOLUME_IOPS", "3000"))
# Digest-pinned on purpose: the :nightly tag is mutable. Bump this digest
# deliberately; never fall back to a moving tag.
EC2_VLLM_IMAGE: str = os.getenv("EC2_VLLM_IMAGE", "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7")
# Deep Learning Base GPU AMI (Ubuntu 22.04): it preinstalls the NVIDIA
# driver, Docker, and the NVIDIA container toolkit, so boot installs
# nothing. The SSM parameter resolves to the latest build per region.
EC2_AMI_SSM_PARAM: str = os.getenv(
    "EC2_AMI_SSM_PARAM",
    "/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-22.04/latest/ami-id",
)
EC2_SECURITY_GROUP_NAME: str = os.getenv("EC2_SECURITY_GROUP_NAME", "smolbench-inference")
# Fixed ports for the two on-instance HTTP planes -- see the module
# docstring's "Security model" section for what each guards. Deliberately NOT
# env-configurable: changing either needs coordinated changes beyond this
# client (the security-group ingress rule, the payload scripts' docker
# port-publish/probe URLs, vLLM's own listen port), so an override belongs in
# code, not in a stray env var.
EC2_VLLM_PORT: int = 8000
EC2_AGENT_PORT: int = 9000
# Value of the ``smolbench:experiment`` tag, used to find, reattach to and
# terminate this experiment's instance. Import-time capture: set
# EC2_EXPERIMENT_TAG before the first import of this module (see "Env-read
# timing" in the module docstring); setting it later has no effect.
EC2_EXPERIMENT_TAG: str = os.getenv("EC2_EXPERIMENT_TAG", "periodic-induction")
# Anchored to the repo root via `repo_root()`, not the cwd and not a
# hand-counted depth off this file. Gitignored: it holds the control token
# and the vLLM key. The EC2_STATE_FILE override is read at call time, in
# `_state_path`.
_DEFAULT_STATE_FILE: Path = repo_root() / ".ec2_state.json"
EC2_IDLE_TIMEOUT_MIN: int = int(os.getenv("EC2_IDLE_TIMEOUT_MIN", "30"))
# The serve timeout and the watchdog's loading-counts-as-active grace must
# cover a COLD checkpoint pull from HF: a ~410 GB download on a live 405B
# serve outran both 90 and 120 min. A warm S3 cache takes minutes, but the
# first-ever pull sets the bound.
# INVARIANT: the watchdog payload's own STARTUP_GRACE_MIN env fallback
# (payloads/watchdog.py.txt, used only if the env var fails to propagate to
# the instance) must match this default -- keep both at "180".
EC2_STARTUP_GRACE_MIN: int = int(os.getenv("EC2_STARTUP_GRACE_MIN", "180"))
EC2_MAX_LIFETIME_MIN: int = int(os.getenv("EC2_MAX_LIFETIME_MIN", "1440"))
EC2_PROVISION_TIMEOUT_MIN: int = int(os.getenv("EC2_PROVISION_TIMEOUT_MIN", "15"))
#: "spot" (default) or "on-demand". Set this only on purpose: on-demand pays
#: several times the spot rate and cannot be reclaimed, so a forgotten box
#: bills at full price until the idle watchdog or the lifetime backstop
#: fires. It exists for a lane whose exact instance type has NO spot capacity
#: anywhere and whose hardware must not change -- same silicon, bought
#: differently, is the only move that keeps the lane uncontaminated.
EC2_MARKET: str = os.getenv("EC2_MARKET", "spot")
#: Spot bid ceiling, as a multiple of the median observed AZ price. The 1.25
#: default clears a normal-priced AZ while outlier AZs (2.46x intra-type
#: spread) fail fast with SpotMaxPriceTooLow, so the hunt moves on. Set <= 0
#: to send NO MaxPrice: the ceiling then defaults to the on-demand price, the
#: highest bid EC2 accepts.
#:
#: Within spot, InsufficientInstanceCapacity is about physical hosts, not
#: money -- EC2 does not allocate by bid, so raising the multiplier only helps
#: when an AZ's price exceeds the cap. On-demand's priority protects against
#: interruption, not against an empty pool: when on-demand reports no
#: capacity, TRY SPOT before concluding the hardware is unavailable.
EC2_SPOT_BID_MULTIPLIER: float = float(os.getenv("EC2_SPOT_BID_MULTIPLIER", "1.25"))
EC2_SERVE_TIMEOUT_MIN: int = int(os.getenv("EC2_SERVE_TIMEOUT_MIN", "180"))
# Optional EC2 key pair for SSH debugging. Empty (the default) means no SSH:
# boot problems are then visible only via the serial console or the instance
# screenshot.
EC2_KEY_NAME: str = os.getenv("EC2_KEY_NAME", "")
# evaluate()'s default fan-out is the EC2_MAX_PARALLEL_REQUESTS env var
# (default 8), which the shared ChatClient reads at call time.
# Per-request inference READ timeout, kept generous (and overridable per
# eval) so long CoT generations finish on attempt 1. Retries never re-seed:
# every attempt re-POSTs the byte-identical seeded body (openai_compat
# merges ``seed`` after extra_args, so it can never be dropped or varied),
# so a generation longer than the read budget just times out again on each
# attempt -- a short budget censors the top of the CoT-length distribution
# rather than re-rolling it.
EC2_REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("EC2_REQUEST_TIMEOUT_SECONDS", "600"))
# Connect timeout, kept SHORT and SEPARATE from the long read timeout above,
# because requests treats a scalar ``timeout`` as both connect AND read: a
# dead or unreachable box (spot reclaim, IP drift) would then blackhole each
# connect for the full read budget, turning 10 attempts into hours of
# hanging. Failing connects fast trips the connection-failure cap within
# minutes and raises the actionable "endpoint unreachable" error, while a
# genuinely slow generation still gets the full read budget.
EC2_CONNECT_TIMEOUT_SECONDS: float = float(os.getenv("EC2_CONNECT_TIMEOUT_SECONDS", "10"))
EC2_RETRY_BACKOFF_SECONDS: int = int(os.getenv("EC2_RETRY_BACKOFF_SECONDS", "60"))
# Consecutive connection failures tolerated before concluding the endpoint is
# gone (spot interruption or IP drift) rather than transiently overloaded.
EC2_MAX_CONNECTION_FAILURES: int = int(os.getenv("EC2_MAX_CONNECTION_FAILURES", "10"))
# Soft, post-hoc token guard for models that have no deploy spec.
EC2_CONTEXT_LENGTH: int = int(os.getenv("EC2_CONTEXT_LENGTH", "16384"))
# Optional S3 model cache, e.g. s3://smolbench-model-cache-<acct>/hf. When
# set, provisioning creates the bucket and an instance profile (S3 RW on the
# bucket, plus SSM core); the agent pulls each checkpoint from S3 before
# launching vLLM (same-region S3-to-NVMe runs at multi-GB/s, versus 10-35 min
# from HF) and serve_model uploads fresh weights back in the background, so
# the mirror seeds itself and only the first instance pays the HF cost.
# Cross-region pulls still work, slower and at ~$0.02/GB, so put the bucket
# where spot capacity usually lands (EC2_S3_CACHE_REGION).
EC2_S3_MODEL_CACHE: str = os.getenv("EC2_S3_MODEL_CACHE", "").rstrip("/")
EC2_S3_CACHE_REGION: str = os.getenv("EC2_S3_CACHE_REGION", AWS_REGION)
EC2_INSTANCE_ROLE_NAME: str = os.getenv("EC2_INSTANCE_ROLE_NAME", "smolbench-ec2-role")
# EC2_INFERENCE_BASE_URL / EC2_VLLM_API_KEY bypass the state file and point
# the inference path at any OpenAI-compatible server (the stub server in
# tests/evals/test_openai_compat.py). They are read at call time, in
# _base_url/_api_key/_connection, not here; so are EC2_INFO and
# EC2_INFO_RESPONSE (verbose logging), by the shared ChatClient.

# Per-model deployment spec. The dict key is both (a) the ``model`` argument
# the notebook passes to query()/evaluate() and (b) vLLM's
# ``--served-model-name``, so the OpenAI request body carries it verbatim.
# ``_aws.EC2_SPEC_KEYS`` is the authoritative key list (and what
# tests/evals/test_aws_shared.py pins every spec against); ``_aws.DeploySpec``
# documents each field.
#
# --- Family-ladder scaling study roster --------------------------------
# 21 models = 7 families x 3 rungs, one EC2 instance per model. Every
# architecture is in-tree upstream, so no entry needs --trust-remote-code;
# every repo is ungated. Uniform max_model_len=131072: the smallest native
# window on the roster is exactly 131072 (gemma-4-E2B, GLM-4.5-Air,
# EXAONE-4.0-32B), so nothing is down-capped below native and a scaling study
# cannot let context vary with the vendor's YaRN generosity. Every spec also
# serves DETERMINISM_ARGS (appended after this dict) on top of the
# digest-pinned image and a per-spec --revision/--tokenizer-revision pin;
# both revision flags are pinned even though tokenizer_revision inherits
# --revision at the pinned build, so the pin does not depend on that
# inheritance. Prefix caching is OFF everywhere (a nondeterminism source),
# and results from this config must NEVER pool with stock-config data.
#
# Instance tiers (chosen from weights-size and 128k-KV arithmetic; the
# fleet supervisor maps these to EC2_INSTANCE_TYPES per lane):
#   tier A g6e.4xlarge  (1x L40S 48 GB):  nano-4b, gemma e2b, ministral-3b
#   tier B g6e.12xlarge (4x L40S 192 GB): qwen 27b, nano-30b, gemma 12b/31b,
#                                         glm-4.7-flash, ministral 8b/14b,
#                                         exaone 32b/33b
#   tier C p5.48xlarge  (8x H100 640 GB): qwen 122b/397b-fp8, super-120b,
#                                         glm-4.5-air, k-exaone-236b
#   tier D p6-b200.48xlarge (8x B200 1440 GB): glm-4.7, deepseek-v3.1,
#                                         deepseek-v4-pro, deepseek-v4-flash
#
# tp notes: GLM-4.7-Flash has 20 attention heads, so tp must divide 20; it
# runs tp=4 on tier B (a p5 would idle half its GPUs). Nemotron-Nano-30B has
# only 2 KV heads; vLLM replicates KV heads when tp exceeds n_kv. All other
# tp choices divide the head counts exactly (verified from each config.json).
#
# Reasoning wiring (CoT is ON for every model in this study; the per-request
# chat_template_kwargs toggles ride in extra_args from the study drivers --
# see notebooks/induction/run_study.py COT_ARGS):
#   * Qwen3.5 / Gemma-4: a server-side --reasoning-parser (qwen3 / gemma4)
#     splits the think block into reasoning_content. Gemma-4's template
#     defaults enable_thinking to FALSE, so the driver MUST pass it true, and
#     its think tags are Gemma-specific, so the client-side "</think>"
#     fallback would NOT catch them -- the parser is load-bearing there.
#   * Nemotron-3: enable_thinking defaults on in the shipped template, and
#     query() splits the plain-text <think> block CLIENT-side; do not switch
#     to the vLLM nemotron_v3 parser without re-verifying.
#   * GLM-4.x: thinking defaults ON; the glm47/glm45 parsers split it
#     server-side.
#   * Ministral-3 Reasoning: the [THINK] protocol lives ONLY in the shipped
#     template's default_system_message, which the template injects ONLY when
#     no system message is supplied -- so the Lean eval, which always supplies
#     one, would silently disable thinking. Fix: inject that exact default
#     text as the provider system_prompt below. ChatClient puts it FIRST and
#     the template renders each system message as its own [SYSTEM_PROMPT]
#     block, so induction stays byte-identical to out-of-box behavior while
#     Lean gets the think protocol plus its own instructions. Do NOT switch
#     these entries to --tokenizer-mode mistral: that bypasses the Jinja
#     template entirely.
#   * EXAONE: no vLLM reasoning parser exists for it, so query() splits the
#     plain-text <think> block client-side. EXAONE-4.0-32B defaults
#     enable_thinking OFF, so the driver must pass it true. Only 4.5-33B is a
#     multimodal wrapper (hence its --language-model-only).
#   * DeepSeek V4: the repos ship NO chat template (404, and no
#     tokenizer_config key); the toggle lives in the repo's Python
#     encoding_dsv4.py. vLLM accepts a LITERAL template string via
#     --chat-template, so DSV4_CHAT_TEMPLATE below reproduces the shipped
#     encoding for the [system?, user] + generation-prompt shapes this repo
#     sends (byte-equality pinned by tests/evals/test_dsv4_chat_template.py
#     against the vendored encoding module). chat_template_kwargs
#     {"thinking": true} drives both the template branch and vLLM's
#     deepseek_v4 parser, whose initial state accepts the prompt-final
#     <think>. DeepSeek-V3.1 DOES ship its own template (thinking kwarg), so
#     it needs no override.

# Inline stand-in for the chat template DeepSeek V4 does not ship (see the
# DeepSeek V4 note above): renders the [system?, user] + generation-prompt
# shapes this repo sends exactly as the repo's own encoding_dsv4.py does --
# system text bare, user text prefixed ``<｜User｜>``, then ``<｜Assistant｜>``
# followed by an open ``<think>`` when ``thinking`` is true/unset (CoT on,
# the study default) or a closed ``</think>`` when false. Byte-equality with
# the vendored encoder is pinned by tests/evals/test_dsv4_chat_template.py.
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

# The Ministral-3 Reasoning template's default_system_message, verbatim
# (the md5 of the shipped chat_template.jinja is
# f9ce03df8c692f42b2aeb78024e29f4f, identical across the 3B/8B/14B rungs).
# Needed because Ministral has NO native thinking toggle: the shipped
# template exposes no enable_thinking/thinking chat_template_kwargs -- the
# [THINK] protocol lives entirely in this default system message, which the
# template injects ONLY when the request supplies no system message of its
# own. Any eval that sets a system prompt (the Lean eval always does) would
# therefore silently disable thinking; injecting the exact default text as
# the spec-level system_prompt keeps thinking on in every case while leaving
# no-system-prompt requests byte-identical to out-of-box behavior. See the
# Ministral note above.
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
    # Smoke-test entry: exercises the full lifecycle on a cheap single-GPU
    # spot instance (g6.2xlarge / g5.2xlarge) for well under a dollar. 32768
    # is the checkpoint's native window.
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
    # tp=4: tier A's g6e.12xlarge capacity fallback lands this lane on 4x
    # L40S in practice, and a 12B model with ~95k-token thinking budgets on
    # ONE L40S hit the 3600s read timeout on long arms. 16 attention heads
    # and 8 KV heads shard cleanly across 4; tp=4 does require that 4-GPU
    # box, which the fallback list provides.
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
    # SM90 hazard: on p5/p5e/p5en this spec MUST carry the Marlin W4A16 MXFP4
    # pin, so do NOT serve this marlin-less arg set there -- it is SM100/B200
    # only (FLASHMLA_SPARSE_DSV4 accepts major in [9,10]; fp8_ds_mla KV).
    # Memory: Flash weights are 160 GB. --disable-custom-all-reduce stays.
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
    # Pro targets p6-b200 (SM100) only. Native MXFP4 expert path (no Marlin
    # pin); gmu 0.93 for the 865 GB checkpoint on 1128 GB of VRAM.
    # Do NOT serve this marlin-less spec on p5/p5e/p5en -- SM90 needs the pin.
    "deepseek-v4-pro":   {"hf_model_id": "deepseek-ai/DeepSeek-V4-Pro", "tp": 8, "max_model_len": 131072,
                          "vllm_args": ["--reasoning-parser", "deepseek_v4", "--chat-template", DSV4_CHAT_TEMPLATE,
                                        "--tokenizer-mode", "deepseek_v4",
                                        "--attention-backend", "FLASHMLA_SPARSE_DSV4", "--kv-cache-dtype", "fp8_ds_mla",
                                        "--block-size", "256", "--disable-custom-all-reduce",
                                        "--gpu-memory-utilization", "0.93",
                                        "--revision", "b5968e9190ef611bbf34a7229255be88a0e937c1",
                                        "--tokenizer-revision", "b5968e9190ef611bbf34a7229255be88a0e937c1"]},
}

#: vLLM args certified deterministic within one process. Results generated
#: under this bundle are NOT comparable with stock-config data. The four
#: flags were never attributed individually: relax any one of them only
#: after re-certifying with a byte-agreement probe.
DETERMINISM_ARGS: List[str] = [
    "--no-enable-prefix-caching", "--max-num-seqs", "1",
    "--enforce-eager", "--seed", "0",
]

for _spec_key, _spec in EC2_DEPLOY_SPECS.items():
    _args = list(_spec.get("vllm_args") or [])
    assert "--enable-prefix-caching" not in _args, _spec_key
    assert not ({a for a in DETERMINISM_ARGS if a.startswith("--")} & set(_args)), _spec_key
    # Make the KV budget a function of the spec, not of free VRAM at
    # profiling time (which varies with whatever else the box was doing).
    # 0.92 equals vLLM's default AT THE PINNED BUILD
    # (vllm/config/cache.py:69 at 8efa13b70), made explicit here, and is what
    # the hinge det arms actually resolved to (their cache_config_info
    # records gpu_memory_utilization=0.92), so nothing the experiment
    # certified changes. deepseek-v4-pro keeps 0.93 for its larger footprint.
    if "--gpu-memory-utilization" not in _args:
        _args += ["--gpu-memory-utilization", "0.92"]
    _spec["vllm_args"] = _args + DETERMINISM_ARGS

#: ``num_attention_heads`` per family-ladder checkpoint, copied from each
#: model's config.json (archived source scripts/arch/arch_configs_raw.json;
#: test_deploy_specs drift-pins this map against the vendored config.json rows
#: in tests/fixtures/roster_configs.json). Models absent here (the
#: qwen2.5-1.5b canary) fall back to their spec's static ``tp`` in derive_tp.
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

#: GPU count per instance type this provider hunts. For an unknown type,
#: `derive_tp` falls back to the spec's static ``tp`` instead of guessing.
_INSTANCE_GPU_COUNTS = {
    "g6e.xlarge": 1, "g6e.2xlarge": 1, "g6e.4xlarge": 1, "g6e.8xlarge": 1,
    "g6e.16xlarge": 1, "g6e.12xlarge": 4, "g6e.24xlarge": 4, "g6e.48xlarge": 8,
    # g7 = RTX PRO 4500 (32GB), g7e = RTX PRO 6000 (96GB); both SM120,
    # PCIe-only. Counts verified via describe-instance-types -- the 12xlarge
    # sizes carry TWO GPUs, unlike g6e's four. Map a family fully or not at
    # all (see derive_tp's fallback warning for what a half-mapped family
    # does to a lane).
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
    """Return the tensor-parallel degree (>= 1) for `model` on the box that landed.

    ``tp = gcd(num_attention_heads, gpu_count)``: the largest head-divisor that
    also divides the landed GPU count, so every GPU the hunt paid for is used
    where divisibility allows (a tp=1 spec idled 3 of 4 L40S on g6e.12xlarge).

    Parameters
    ----------
    spec : Dict[str, Any]
        Deploy spec; its ``"tp"`` is the fallback when `model` is absent from
        ``MODEL_ATTENTION_HEADS`` or `instance_type` from
        ``_INSTANCE_GPU_COUNTS``.
    """
    heads = MODEL_ATTENTION_HEADS.get(model)
    gpus = _INSTANCE_GPU_COUNTS.get(instance_type)
    if heads is None or gpus is None:
        if heads is not None and instance_type:
            # The dangerous fallback: if a lane's hunt spans mapped AND
            # unmapped types, the spec tp used here differs from the derived
            # tp on the mapped box -- a silent mid-lane tp change, so warn
            # loudly and get the gap mapped.
            logging.warning(
                f"derive_tp: instance type {instance_type!r} not in "
                f"_INSTANCE_GPU_COUNTS; falling back to spec tp="
                f"{spec.get('tp', 1)} for {model!r} -- add the type's GPU "
                "count to keep tp derivation consistent across a lane"
            )
        return spec.get("tp", 1)
    tp = max(1, math.gcd(heads, gpus))
    if tp < gpus:
        # Correct but wasteful: head divisibility strands GPUs (20 heads on an
        # 8-GPU box give tp=4, idling four). Warn loudly so a half-used
        # expensive box stays visible.
        logging.warning(
            f"derive_tp: {model!r} on {instance_type} uses tp={tp} of {gpus} "
            f"GPUs ({heads} attention heads don't divide further) -- "
            f"{gpus - tp} GPUs will sit idle"
        )
    return tp


#: GPU marketing name and memory per instance FAMILY (the type prefix before
#: the size dot; p6 families keep their full hyphenated prefix). Purely
#: descriptive: ``server_config`` uses it so a result file names its silicon
#: without the reader needing this module's type tables.
_INSTANCE_GPU_NAMES = {
    "g6e": "L40S 48GB", "g7": "RTX PRO 4500 32GB", "g7e": "RTX PRO 6000 96GB",
    "p4d": "A100 40GB", "p5": "H100 80GB", "p5e": "H200 141GB",
    "p5en": "H200 141GB", "p6-b200": "B200 180GB", "p6-b300": "B300 288GB",
}


#: Optional hardware pin, ``"<gpu-name-substring>:<count>"`` (e.g.
#: ``"L40S:1"``). When set, a lane REFUSES to serve on a box whose silicon
#: does not match.
#:
#: WHY: widening ``EC2_INSTANCE_TYPES`` to escape a capacity wall is a silent
#: confound -- a wider list can land a lane on a box with a different GPU
#: count, changing derived tp mid-lane. Pinning the silicon rather than the
#: instance size keeps a same-GPU substitution legal and refuses a
#: tp-changing one.
#:
#: Determinism scope: the pin is necessary but NOT sufficient. Measured
#: (commit ac11f8c2): nemotron-3-nano-4b was 8/8 bitwise-identical at a
#: fixed seed on one box, yet 0/8 across g6e.4xlarge vs g6e.2xlarge with
#: the SAME 1x L40S and tp=1 -- host vCPU/RAM change batching and thus
#: reduction order. The pin blocks silicon/tp swaps; it does not certify
#: cross-box reproducibility, so a lane that must be bit-reproducible also
#: needs the same instance SIZE.
EC2_REQUIRE_GPU: str = os.getenv("EC2_REQUIRE_GPU", "")


def _assert_required_gpu(state: Dict[str, Any], model: str) -> None:
    """Check that the landed box's GPU matches ``EC2_REQUIRE_GPU``.

    Runs BEFORE the container swap, so a mismatched box never generates a
    single row. No-ops when the pin is unset (the default).

    Raises
    ------
    RuntimeError
        The pin is set and the landed instance type is either absent from this
        module's GPU tables (unknown hardware is reported, never treated as a
        match) or names silicon that does not match the pin.
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


# Short, separate timeout for server_config()'s best-effort LIVE probes (vLLM
# /version, /metrics, the agent /status). Deliberately much shorter than the
# on-instance polling timeouts (_AGENT_POLL_S etc.): provenance fields are
# allowed to be missing, so a slow or dead endpoint must degrade a handful of
# them to None in seconds rather than stall an eval batch.
_SERVER_CONFIG_PROBE_TIMEOUT_S: int = 5


def _fetch_vllm_version(ip: str, vllm_api_key: str) -> Optional[str]:
    """Return the ``version`` string from vLLM's ``GET /version``, or None."""
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
    """Return the raw Prometheus line(s) mentioning ``cache_config_info``, or None.

    The labels carry ``num_gpu_blocks`` / ``gpu_memory_utilization`` /
    ``block_size``, and stay deliberately UNPARSED: the label set drifts across
    vLLM builds, so the raw line survives where a parsed dict would not. None
    on no match or any request failure.
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


def _fetch_agent_fingerprint(
    state: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[List[str]]]:
    """Return (``/status``'s ``"fingerprint"``, attention-backend log lines).

    Best-effort: either element degrades to None on failure, and ``_agent`` is
    called with ``connect_retries=0`` because this is a snapshot, not a wait
    loop. The backend lines are mined from ``/status``'s ``log_tail`` (the
    container's last ~300 lines; they appear in no metrics endpoint), a moving
    window -- call ``server_config`` right after serve or they may have gone.
    """
    try:
        status = _agent(
            state, "GET", "/status",
            timeout=_SERVER_CONFIG_PROBE_TIMEOUT_S, connect_retries=0,
        )
    except Exception:  # noqa: BLE001
        return None, None
    backend_lines: Optional[List[str]] = None
    try:
        tail = status.get("log_tail") or ""
        hits = [ln.strip() for ln in tail.splitlines()
                if "attention backend" in ln.lower() or "attn_backend" in ln.lower()]
        backend_lines = hits or None
    except Exception:  # noqa: BLE001
        backend_lines = None
    return status.get("fingerprint"), backend_lines


def server_config(model: str) -> Optional[Dict[str, Any]]:
    """Return a serving-stack snapshot for `model`, for result provenance.

    Stamped onto every stored replicate (``Marks.server_config`` via
    ``ReplicateHarness.run_replicates``) and written as a deduction run's
    ``server_config.yaml`` sidecar. Reads the state file at call time, so call
    it INSIDE the ``serve_model`` block.

    Returns
    -------
    Optional[Dict[str, Any]]
        None only when the state-file read itself raised; otherwise every key
        is present (None for unknown/unreachable pieces), so readers always
        see the full schema. Four groups:

        - From state/spec, no network: ``gpu`` comes from a static per-type
          table, NOT an nvidia-smi observation; ``vllm_image`` is the
          CONFIGURED ``EC2_VLLM_IMAGE``, possibly a mutable tag;
          ``hf_model_id`` is the spec's pin, not necessarily what is loaded.
        - From ``state["last_serve"]`` (the argv actually POSTed):
          ``vllm_args``, ``max_model_len``, ``served_at`` (UTC ISO-8601), all
          None unless ``last_serve["model"] == model``, so a previous swap on
          the same box is never misattributed.
        - Live probes (read-only GETs bounded by
          ``_SERVER_CONFIG_PROBE_TIMEOUT_S``), None on any failure including
          "no box": ``vllm_version``, ``vllm_cache_config`` (raw unparsed
          ``cache_config_info`` Prometheus lines), ``attention_backend_log``,
          ``vllm_image_digest``, ``agent_fingerprint``
          (``payloads/agent.py.txt``'s ``fingerprint()``: ``nvidia_smi`` is an
          OBSERVATION, unlike the static ``gpu``; ``hf_snapshots`` = resolved
          revision dirnames on disk; ``weights_digest`` = sha256 of the
          safetensors index plus per-file sizes, NOT a full weights read).
        - Client-side env reads, populated even with no box:
          ``max_parallel_requests`` (``EC2_MAX_PARALLEL_REQUESTS``, default 8)
          and ``stream`` (``EC2_STREAM_COMPLETIONS``), each individually
          guarded so one malformed value degrades only itself.

    Notes
    -----
    NEVER raises: provenance is a passenger and must not crash a lane.
    """
    try:
        state = _load_state() or {}
        spec = EC2_DEPLOY_SPECS.get(model, {})
        itype = state.get("instance_type") or ""
        gpus = _INSTANCE_GPU_COUNTS.get(itype)
        name = _INSTANCE_GPU_NAMES.get(itype.split(".", 1)[0])

        # The ACTUAL launched argv, not the (possibly since-edited) spec --
        # see serve_model's "last_serve" stash. Trusted only when it names
        # THIS model, so a previous swap on the same box is never
        # misattributed.
        last_serve = state.get("last_serve") or {}
        last_serve_matches = bool(state) and last_serve.get("model") == model
        vllm_args = last_serve.get("vllm_args") if last_serve_matches else None
        max_model_len = last_serve.get("max_model_len") if last_serve_matches else None
        served_at = last_serve.get("served_at") if last_serve_matches else None

        # Live probes are attempted only with enough state to reach the box
        # at all; otherwise short-circuit to None without a doomed call.
        ip = state.get("public_ip")
        vllm_key = state.get("vllm_api_key")
        vllm_version = _fetch_vllm_version(ip, vllm_key) if ip and vllm_key else None
        vllm_cache_config = _fetch_vllm_cache_config(ip, vllm_key) if ip and vllm_key else None
        agent_fp, attention_backend = (
            _fetch_agent_fingerprint(state) if ip else (None, None))
        vllm_image_digest = None
        if agent_fp:
            digests = agent_fp.get("image_repo_digests")
            if digests:
                vllm_image_digest = digests[0]

        # Guarded individually, not just by the function-wide except below:
        # both parse an env var, and a malformed override (e.g.
        # EC2_STREAM_COMPLETIONS=true instead of "1") must degrade only THIS
        # field to None, not blank the whole already-computed snapshot.
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
            # From last_serve like its siblings, never re-derived live: a
            # reattach onto a different instance type or a spec edit would
            # otherwise stamp a tp the completions never ran under.
            "tp": last_serve.get("tp") if last_serve_matches else None,
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
            "attention_backend_log": attention_backend,
            "agent_fingerprint": agent_fp,
            "vllm_image_digest": vllm_image_digest,
            "max_parallel_requests": max_parallel_requests,
            "stream": stream,
        }
    except Exception:  # noqa: BLE001 -- see Notes: provenance never crashes a lane
        logging.warning("server_config: could not snapshot the serving config", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Internal poll/timeout tuning: an implementation detail, NOT
# env-configurable like the EC2_* knobs above. These bound how chattily this
# module polls AWS and the instance; a notebook run should not tune them.
# ---------------------------------------------------------------------------
# _wait_public_ip: budget and cadence for DescribeInstances reporting a
# public IP after launch.
_WAIT_IP_TIMEOUT_S: int = 300
_WAIT_IP_POLL_S: int = 5
# Consecutive "absent" DescribeInstances polls tolerated before concluding
# the instance is really gone (~30s at _WAIT_IP_POLL_S=5; the
# eventual-consistency window is typically a few seconds).
_ABSENT_STREAK_LIMIT: int = 6
# _wait_agent: /status retry cadence, and how often it additionally confirms
# via DescribeInstances that the instance is still alive. 6 polls * 10s is one
# extra DescribeInstances per minute -- cheap insurance against silently
# polling a dead box for the whole timeout instead of failing fast.
_AGENT_POLL_S: int = 10
_AGENT_PROGRESS_EVERY_N_POLLS: int = 6
# _wait_model_ready: /status re-poll cadence while a model loads (the
# checkpoint download dominates; see the function's docstring).
_MODEL_READY_POLL_S: int = 15
# _ensure_instance_profile: IAM is eventually consistent, so a just-created
# role/instance-profile is not immediately usable by RunInstances; this is
# empirically enough slack for that propagation to catch up.
_IAM_PROPAGATION_SLEEP_S: int = 12
# list_models(): inherits openai_compat.METADATA_TIMEOUT_S through
# metadata_get's default parameter.


# ---------------------------------------------------------------------------
# Local state file (instance identity + secrets); shared by both paths
# ---------------------------------------------------------------------------


def _state_path() -> Path:
    """Return the state-file path; the env override is honored at call time."""
    return Path(os.getenv("EC2_STATE_FILE", str(_DEFAULT_STATE_FILE))).expanduser()


def _load_state() -> Optional[Dict[str, Any]]:
    """Return the saved instance state, or None when absent/corrupt."""
    try:
        return json.loads(_state_path().read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _save_state(state: Dict[str, Any]) -> None:
    """Write the state file, owner-only from the moment it is created.

    It holds the control token and the vLLM api key, so the mode rides on
    ``os.open`` rather than a write-then-``chmod``, which would leave the
    secrets readable at the process umask for the window in between. The
    ``fchmod`` re-asserts it on a file some earlier version left looser.
    """
    path = _state_path()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)  # re-assert before os.fdopen takes the descriptor
    with os.fdopen(fd, "w") as file:
        file.write(json.dumps(state, indent=2) + "\n")


def _clear_state(instance_id: Optional[str] = None) -> None:
    """Remove the local state file, unless another instance has claimed it.

    Parameters
    ----------
    instance_id : Optional[str]
        The instance being torn down; when the file names a DIFFERENT one (a
        second run for the same experiment tag provisioned a fresh box
        mid-teardown) it is left alone, since deleting it strands a live,
        billing GPU box with no driver and no local record. None deletes
        unconditionally, for callers with no instance in hand.
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
    """Return the OpenAI-compatible base URL, resolved at call time.

    It cannot be an import-time constant: the instance's IP does not exist
    until provisioning. ``EC2_INFERENCE_BASE_URL`` overrides the state file
    (for tests or externally managed servers).
    """
    override = os.getenv("EC2_INFERENCE_BASE_URL")
    if override:
        return override.rstrip("/")
    return f"http://{_require_state()['public_ip']}:{EC2_VLLM_PORT}/v1"


def _api_key() -> str:
    """Return the vLLM bearer token at call time: ``EC2_VLLM_API_KEY``, else the state file."""
    override = os.getenv("EC2_VLLM_API_KEY")
    if override:
        return override
    return _require_state()["vllm_api_key"]


# ---------------------------------------------------------------------------
# Inference path (requests only; no boto3)
# ---------------------------------------------------------------------------


def get_model_context_length(model: str) -> int:
    """Return the served context window: the spec's ``max_model_len``.

    That is exactly what vLLM was launched with, so it doubles as the soft
    post-hoc token guard. Specless models fall back to ``EC2_CONTEXT_LENGTH``.
    """
    spec = EC2_DEPLOY_SPECS.get(model)
    if spec and "max_model_len" in spec:
        return spec["max_model_len"]
    return EC2_CONTEXT_LENGTH


def list_models(model: str = "") -> List[str]:
    """Return the ``data[].id`` values from vLLM's ``GET /v1/models``.

    Normally a single-element list: this instance serves exactly one model at
    a time, whichever ``serve_model`` last swapped in.

    Parameters
    ----------
    model : str
        Accepted and IGNORED; it exists only for signature parity with
        ``smolbench.evals.providers.aws.list_models`` so
        ``smolbench.evals.provider`` can dispatch uniformly.
    """
    response = metadata_get(f"{_base_url()}/models", _api_key(), check_status=True)
    return [m["id"] for m in response.get("data", [])]


def _raise_endpoint_unreachable(err: Exception) -> NoReturn:
    """Raise an actionable error after repeated connection failures.

    Distinguishes, best-effort via lazy boto3, the two common causes: the spot
    instance was interrupted/terminated, or the caller's public IP changed so
    the security group blocks them. It must also work with no AWS credentials,
    so every boto3 problem degrades to the generic message.
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
            # Not _instance_state (see its Notes): a raw ClientError must reach
            # the `except Exception` below and keep the generic detail.
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
    """Return the chat URL and the vLLM token, from ONE state snapshot.

    ``ChatClient.connection`` calls this once per request attempt, so a spot
    instance re-provisioned mid-retry-loop is picked up on the next attempt,
    and the URL and token can never come from two different state versions.
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
    """Return the spec-level system prompt (e.g. ``MINISTRAL_THINK_SYSTEM``), or None.

    Injecting it at the provider layer keeps the notebook's user prompts
    byte-identical across archetypes.
    """
    return EC2_DEPLOY_SPECS.get(model, {}).get("system_prompt")


_CLIENT = ChatClient(
    name="EC2 endpoint",
    env_prefix="EC2",
    connection=_connection,
    context_length=get_model_context_length,
    system_prompt=_system_prompt,
    retry_backoff_s=EC2_RETRY_BACKOFF_SECONDS,
    # (connect, read): a short connect fails fast on a dead box, a long read
    # covers genuine long CoT generations (see the constants' comments).
    connect_timeout_s=EC2_CONNECT_TIMEOUT_SECONDS,
    read_timeout_s=EC2_REQUEST_TIMEOUT_SECONDS,
    # A self-managed spot endpoint can vanish (interruption, watchdog,
    # caller-IP drift), so unlike managed providers this caps connection-level
    # failures instead of retrying forever against a dead box, and diagnoses
    # the cause (spot reclaim vs. caller-IP drift) in the raised error.
    max_connection_failures=EC2_MAX_CONNECTION_FAILURES,
    on_unreachable=_raise_endpoint_unreachable,
)

# The provider-facing API; see ChatClient.query/complete/evaluate. The
# plain-text <think> splitting that Nemotron-3 and EXAONE need (this study
# serves neither with a server-side reasoning parser; see the "Reasoning
# wiring" note in EC2_DEPLOY_SPECS) lives in the shared client, so every
# provider handles it identically.
query = _CLIENT.query
complete = _CLIENT.complete
evaluate = _CLIENT.evaluate


# ---------------------------------------------------------------------------
# On-instance payloads (control agent, idle watchdog, cloud-init bootstrap)
# ---------------------------------------------------------------------------
# The payload programs and cloud-init templates are byte-exact assets in
# smolbench/evals/payloads/; that package renders them (render_user_data),
# gzip-packs them (pack_user_data) for RunInstances' UserData kwarg, and
# documents their contract.


# ---------------------------------------------------------------------------
# EC2 spot provisioning / lifecycle (lazy boto3; opt-in)
# ---------------------------------------------------------------------------
# These functions import boto3/botocore internally (via _aws.fresh_client),
# so the inference path stays dependency-free (see the module docstring).
# Each client is a FRESH boto3 Session per operation: boto3.client()'s default
# session caches credentials, so a refreshed ~/.aws/credentials (~12h IdP
# sessions) keeps raising RequestExpired until kernel restart. Rationale in
# _aws.fresh_client's docstring (shared with aws.py).

# ClientError codes that mean "this pool cannot fill the request right now"
# -- worth trying the next subnet or region -- as opposed to quota or genuine
# errors.
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
    """Return ``_aws.fresh_client("ec2", region)``.

    Every EC2 call site in this module goes through this local name, never
    ``_aws.fresh_client`` directly, so ``tests/evals/test_ec2_provision.py``'s
    ``monkeypatch.setattr(ec2, "_ec2_client", ...)`` intercepts all of them.
    """
    return _aws.fresh_client("ec2", region)


_error_code = _aws.error_code


def _my_public_ip() -> str:
    return requests.get("https://checkip.amazonaws.com", timeout=10).text.strip()


def _resolve_ami(region: str) -> Tuple[str, str]:
    """Return (ami_id, root_device_name) for the region's latest DL Base GPU AMI."""
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
    """Return (default vpc id, [(subnet_id, az), ...]) for the region."""
    ec2 = _ec2_client(region)
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
    if not vpcs:
        return None, []
    vpc_id = vpcs[0]["VpcId"]
    subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
    return vpc_id, sorted((s["SubnetId"], s["AvailabilityZone"]) for s in subnets)


def _authorize_ingress(region: str, group_id: str, ip: str) -> None:
    """Open EC2_VLLM_PORT and EC2_AGENT_PORT to ip/32; tolerate existing rules."""
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
    """Return the experiment security group's id, and create it if absent."""
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
    """Create the S3 cache bucket if it is absent (private, default settings)."""
    from botocore.exceptions import ClientError

    s3 = _aws.fresh_client("s3", region)
    try:
        s3.head_bucket(Bucket=bucket)
        return
    except ClientError as err:
        code = _error_code(err)
        if code not in ("404", "NoSuchBucket"):
            # 403/301 is ambiguous: either the name exists in another account
            # or region (surfaced here rather than failing confusingly at
            # create), or HEAD is simply denied to scoped credentials (the
            # EC2-only operator key has no s3:*; instances reach the cache via
            # their instance profile, not the caller's). An account-id suffix
            # proves the bucket is ours, and sts:GetCallerIdentity needs no
            # policy, so the check works for the most restricted principal.
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
    """Return the instance-profile name for the model cache, and create it if absent.

    Wraps ``_aws.ensure_instance_profile`` with this module's
    ``EC2_INSTANCE_ROLE_NAME`` / ``_IAM_PROPAGATION_SLEEP_S``. The role grants
    read/write scoped to the cache bucket plus SSM core, which doubles as the
    break-glass shell for a box with no SSH key.
    """
    return _aws.ensure_instance_profile(EC2_INSTANCE_ROLE_NAME, bucket, _IAM_PROPAGATION_SLEEP_S)


def _find_tagged_instance() -> Optional[Tuple[str, Dict[str, Any]]]:
    """Find a live instance tagged for this experiment across EC2_REGIONS."""
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
    """Decode already-base64-decoded user-data bytes into the rendered script.

    User-data ships gzip-compressed (``payloads.pack_user_data``), so gunzip
    first and fall back to plain UTF-8, since a live instance can outlive the
    code change that provisioned it. Both exceptions below land in
    ``_recover_state_from_instance``'s best-effort ``except Exception``.

    Raises
    ------
    UnicodeDecodeError
        `raw` is neither valid gzip nor valid UTF-8 text.
    EOFError
        `raw` is gzip-magic-prefixed but truncated (the magic matches, so
        BadGzipFile never fires).
    """
    try:
        return gzip.decompress(raw).decode()
    except gzip.BadGzipFile:
        return raw.decode()


def _recover_state_from_instance(
    region: str, instance: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Rebuild the state dict for a live instance whose state file was lost.

    The per-experiment secrets ride in the instance's user-data (the
    ``/etc/smolbench/env`` heredoc), so DescribeInstanceAttribute recovers them
    -- the in-account visibility the security model already accepts. Returns
    None when the user-data will not parse (a foreign or older-format
    instance), leaving the caller to refuse reuse.
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
    # The env heredoc writes one NAME=value per line at column 0. The
    # embedded python scripts only ever reference these names via
    # os.environ, so a plain line scan is unambiguous.
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
        # From DescribeInstances, not the user-data env: without it a
        # recovered in-block instance would be misread as outside the
        # capacity block and terminated on the next provision.
        "capacity_reservation_id": instance.get("CapacityReservationId"),
        "launched_at": launch_time.strftime("%Y-%m-%dT%H:%M:%SZ") if launch_time else "?",
    }


def _describe_instance(region: str, instance_id: str) -> Optional[Dict[str, Any]]:
    """Return the full DescribeInstances record for one instance, or None.

    None covers both "never existed" and "aged out of the API"
    (``InvalidInstanceID.NotFound``, raised once a terminated instance's record
    expires, typically ~an hour after termination). Callers needing only the
    state Name should use ``_instance_state``.
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
    """Return an instance's EC2 ``State.Name``, or "absent" when it is gone.

    One DescribeInstances call via ``_describe_instance``; "absent" also
    covers ``InvalidInstanceID.NotFound`` (aged out), which is swallowed.

    Notes
    -----
    Sites needing another field from the same describe result
    (``_wait_public_ip``, ``_reattach_existing_instance``) deliberately skip
    this helper to avoid a second DescribeInstances call;
    ``_raise_endpoint_unreachable`` skips it because it wants the raw
    ClientError, not "absent".
    """
    instance = _describe_instance(region, instance_id)
    return (instance or {}).get("State", {}).get("Name", "absent")


def _try_launch(region: str, kwargs: Dict[str, Any]) -> str:
    """Call run_instances, with a fallback for spot rejecting the shutdown behavior.

    One-time spot instances terminate on OS shutdown regardless, so asking for
    InstanceInitiatedShutdownBehavior=terminate is belt-and-braces; some API
    paths reject the combination, and this then retries without it.
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
    """Poll DescribeInstances (via ``_aws.poll_until``) for a public IPv4.

    Raises
    ------
    RuntimeError
        The instance went ``shutting-down``/``terminated`` before ever getting
        an IP (spot reclaimed right after launch), or stayed absent from
        DescribeInstances for ``_ABSENT_STREAK_LIMIT`` consecutive polls; a
        single absent poll is tolerated as eventual consistency.
    TimeoutError
        No public IP within ``timeout_s`` (default ``_WAIT_IP_TIMEOUT_S``).
    """

    absent_streak = 0

    def check() -> Optional[str]:
        nonlocal absent_streak
        instance = _describe_instance(region, instance_id)
        # Not _instance_state: PublicIpAddress is read from the SAME result
        # below (see _instance_state's Notes).
        inst_state = (instance or {}).get("State", {}).get("Name", "absent")
        if inst_state == "absent":
            # Eventual consistency: a just-launched instance can be invisible
            # for seconds; a reclaimed one stays "terminated" for ~an hour.
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
    """Make one authenticated control-agent call; raise with the body on failure.

    Parameters
    ----------
    connect_retries : int
        Extra attempts, 15s apart, on CONNECT-level failures only
        (``requests.ConnectionError``, which covers ConnectTimeout): the
        caller's egress NAT drops connections in bursts and killed one-shot
        ``/serve`` calls mid-sweep on a healthy box. Every agent endpoint is
        idempotent, so connect patience is always safe; the polling loops and
        the best-effort graceful shutdown pass 0 to keep their own cadence.
    """
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
        except requests.exceptions.ConnectionError:
            if attempt == connect_retries:
                raise
            time.sleep(15)
    if not response.ok:
        raise RuntimeError(f"agent {method} {path} -> {response.status_code}: {response.text[:2000]}")
    return response.json()


def _wait_agent(state: Dict[str, Any], timeout_min: int = EC2_PROVISION_TIMEOUT_MIN) -> None:
    """Wait for the control agent to answer after boot or reattach.

    Polls ``GET /status`` every ``_AGENT_POLL_S`` seconds; every
    ``_AGENT_PROGRESS_EVERY_N_POLLS`` polls it also confirms via
    DescribeInstances that the instance is alive, so a spot reclaim during
    boot fails fast instead of burning the whole budget.

    Parameters
    ----------
    state : Dict[str, Any]
        Needs ``public_ip``, ``control_token``, ``region``, ``instance_id``.

    Raises
    ------
    RuntimeError
        The liveness check found the instance no longer ``pending``/``running``
        (spot reclaimed while waiting for its agent).
    TimeoutError
        The agent never answered within ``timeout_min``.
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
                # blip) must not abort the wait: swallow it and re-check on
                # the next progress poll. The RuntimeError just above
                # (instance genuinely gone) is not a ClientError, so it still
                # propagates out of check(), per poll_until's contract.
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


def _attach(
    state: Dict[str, Any], instance: Dict[str, Any], my_ip: str, how: str
) -> Dict[str, Any]:
    """Shared attach tail for both reattach/recovery branches.

    Authorize ingress for `my_ip`, refresh and persist ``public_ip``, block
    until the agent answers, log. One implementation so the attach protocol
    cannot drift between the state-file and tag-recovery paths (which path
    runs depends only on whether the local state file survived).
    """
    region = state["region"]
    _authorize_ingress(region, state["security_group_id"], my_ip)
    state["public_ip"] = instance.get("PublicIpAddress") or _wait_public_ip(
        region, state["instance_id"]
    )
    _save_state(state)
    _wait_agent(state)
    logging.info(
        f"provision_spot_instance: {how} {state['instance_id']} "
        f"({state['instance_type']} @ {region}, {state['public_ip']})"
    )
    return state


def _reattach_existing_instance(my_ip: str) -> Optional[Dict[str, Any]]:
    """Run ``provision_spot_instance`` branch 1: reuse the state-file instance.

    Safe to call unconditionally: a missing or corrupt state file is a normal
    "nothing to reattach to" outcome, not an error. On reattach it
    re-authorizes the security group for `my_ip`, refreshes and persists
    ``public_ip``, and blocks until the agent answers; a dead recorded
    instance clears the stale state file so the next strategy starts clean.

    Returns
    -------
    Optional[Dict[str, Any]]
        The refreshed, already-saved state dict when the recorded instance is
        still ``pending``/``running``, else None.
    """
    state = _load_state()
    if state is None:
        return None
    instance = _describe_instance(state["region"], state["instance_id"])
    # Not _instance_state: `instance` is reused for PublicIpAddress below
    # (see _instance_state's Notes).
    inst_state = (instance or {}).get("State", {}).get("Name", "absent")
    if inst_state in ("pending", "running"):
        return _attach(state, instance, my_ip, "reattached to")
    logging.info(
        f"provision_spot_instance: stale state ({state['instance_id']} is {inst_state}); relaunching."
    )
    _clear_state()
    return None


def _recover_tagged_instance(my_ip: str) -> Optional[Dict[str, Any]]:
    """Run ``provision_spot_instance`` branch 2: recover a live tagged instance.

    Runs only after branch 1 finds nothing, covering a lost state file: an
    instance tagged ``smolbench:experiment=EC2_EXPERIMENT_TAG`` carries its own
    secrets in its user-data (see ``_recover_state_from_instance``), so state
    is rebuilt from the instance rather than stranding a $30-45/h box. Same
    side effects as ``_reattach_existing_instance``.

    Returns
    -------
    Optional[Dict[str, Any]]
        The recovered, already-saved state dict, or None when no tagged
        instance exists (the caller proceeds to a fresh launch).

    Raises
    ------
    RuntimeError
        A tagged live instance exists but its user-data would not parse for
        the control token (foreign or older-format box) -- refuse to reuse a
        box this process cannot authenticate to.
    """
    found = _find_tagged_instance()
    if found is None:
        return None
    region, instance = found
    state = _recover_state_from_instance(region, instance)
    if state is not None:
        return _attach(state, instance, my_ip, "recovered (from its user-data)")
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
    """Return ``{(instance_type, az): usd_per_hour}`` for `region`, ``{}`` on failure.

    The newest observation wins (``describe_spot_price_history`` returns rows
    newest-first). STRICTLY best-effort: any API failure returns ``{}`` and the
    capacity hunt degrades to price-blind, because pricing must never cost a
    lane its box.
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
    """Build the ``run_instances`` kwargs for one launch attempt.

    Pure and side-effect-free (no AWS calls). Describes a one-time Spot
    instance with InstanceInitiatedShutdownBehavior=terminate (``_try_launch``
    retries without it when an API path rejects the combination), a single ENI
    with a public IP in the experiment's security group, and a gp3 root volume
    tuned from ``EC2_ROOT_VOLUME_*``. Per-attempt values are parameters;
    experiment-wide ones (root-volume throughput/IOPS, the experiment tag)
    come from the module-level ``EC2_*`` constants.

    Parameters
    ----------
    subnet_id : str
        Pins the AZ for this attempt.
    volume_gb : int
        Root volume size, in GiB.
    user_data : bytes
        Gzip-compressed cloud-init script (``payloads.pack_user_data``),
        passed through UNENCODED: boto3's ``base64_encode_user_data`` handler
        base64-encodes bytes ``UserData`` itself.
    key_name : str
        EC2 key pair for SSH debugging; ``""`` omits ``KeyName`` entirely.
    iam_profile : Optional[str]
        Instance profile for the S3 model cache; ``None``/``""`` omits
        ``IamInstanceProfile`` (no S3 cache).
    capacity_reservation_id : Optional[str]
        Purchased EC2 Capacity Block id. When set, MarketType becomes
        ``"capacity-block"`` (required by the API) and the instance is pinned
        to the block instead of the Spot market; the caller must pass the
        block's own AZ subnet and instance type or RunInstances rejects it.
    max_price : Optional[str]
        Spot bid ceiling in USD/hour as the API's string; ``None`` leaves
        EC2's default ceiling (the on-demand price). Derived from live
        ``describe_spot_price_history`` medians because price-blind defaults
        paid 1.29-1.48x each type's cheapest AZ (see
        ``EC2_SPOT_BID_MULTIPLIER``).
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
                # MaxPrice is added below only when the caller derived a cap;
                # without it EC2 keeps its default on-demand-price ceiling.
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
        # On-demand = ABSENCE of InstanceMarketOptions (there is no
        # MarketType="on-demand"); MaxPrice goes with it. Instance type, GPU
        # count and tp stay IDENTICAL to the spot box; shutdown-terminate and
        # the idle watchdog still apply (see EC2_MARKET for why that
        # matters more here).
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
    """Run ``provision_spot_instance`` branch 3: hunt capacity and launch fresh.

    Runs only after branches 1 and 2 find nothing. Generates fresh
    per-experiment secrets (control token, vLLM API key), optionally
    provisions the S3 model-cache bucket/instance-profile, renders the
    cloud-init user-data once, then hunts Spot capacity TYPE-MAJOR: every
    region (and every default-VPC subnet/AZ within it) for the first instance
    type before falling back to the next. Per-region resources (AMI, security
    group, subnets) are resolved once and cached via ``region_info``. Every
    argument arrives already defaulted from the matching ``EC2_*`` constant.

    Parameters
    ----------
    volume_gb : int
        Root volume size, in GiB.
    idle_timeout_min, max_lifetime_min : int
        Watchdog and boot-scheduled-halt budgets, in minutes.
    my_ip : str
        Caller's public IP, resolved ONCE by the caller (one
        ``checkip.amazonaws.com`` round trip, not one per region).

    Returns
    -------
    Dict[str, Any]
        The new instance's state dict, already saved to ``EC2_STATE_FILE``,
        once its agent answers.

    Raises
    ------
    RuntimeError
        No ``(instance_type, region)`` combination yielded capacity; the
        message lists every attempt and its failure reason/code.
    """
    control_token = secrets.token_urlsafe(32)
    vllm_api_key = secrets.token_urlsafe(32)
    hf_token = os.getenv("HF_TOKEN", "")
    # Baked into user-data, so it CANNOT be injected after provisioning. All
    # default EC2_DEPLOY_SPECS repos are ungated, so empty is fine; a
    # set-but-INVALID token breaks even ungated downloads.
    if not hf_token:
        logging.warning(
            "HF_TOKEN is not set. The default deploy specs are all ungated, so "
            "this is fine -- but gated checkpoints added to EC2_DEPLOY_SPECS "
            "would fail to download, and the token cannot be injected after "
            "provisioning."
        )
    iam_profile: Optional[str] = None
    if EC2_S3_MODEL_CACHE:
        try:
            bucket = parse_s3_uri(EC2_S3_MODEL_CACHE)[0]
        except ValueError as err:
            raise ValueError(f"EC2_S3_MODEL_CACHE: {err}") from None
        _ensure_bucket(bucket, EC2_S3_CACHE_REGION)
        iam_profile = _ensure_instance_profile(bucket)
        logging.info(
            f"provision_spot_instance: S3 model cache at {EC2_S3_MODEL_CACHE} "
            f"(instance profile {iam_profile})"
        )
    # Gzip-compressed: the raw render exceeds EC2's 16 KB user-data cap
    # (see _run_instances_kwargs' user_data entry for the encoding contract).
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

    # A purchased Capacity Block short-circuits the Spot hunt entirely: it
    # fixes region, AZ and instance type. Read at call time, not at import,
    # so the supervisor can set it per launch.
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
            # Worded to match the supervisor's drought grep, so a block short
            # of its start time is retried on the slow no-cap cadence.
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

    # Price the whole hunt space up front (one best-effort call per region; {}
    # on failure = price-blind). Each type's cap = EC2_SPOT_BID_MULTIPLIER x
    # the median of its observed AZ prices across ALL hunted regions.
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
            # No MaxPrice (on-demand ceiling): pricing lookup failed, or
            # EC2_SPOT_BID_MULTIPLIER <= 0 asked for it.
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
            # the priced ones (inf sorts last and the sort is stable).
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
    """Provision (or reattach to) the experiment's EC2 spot instance.

    Idempotent, so re-running the cell after a kernel restart is safe. Tries,
    in order, ``_reattach_existing_instance`` (state-file box; re-authorizes
    the security group for the caller's CURRENT IP), ``_recover_tagged_instance``
    (state file lost, live tagged instance) and ``_launch_fresh`` (type-major
    capacity hunt). Each argument defaults to the matching ``EC2_*`` constant.

    When ``EC2_CAPACITY_RESERVATION`` is set the reservation is authoritative:
    a live instance OUTSIDE that block is TERMINATED rather than reused, since
    reuse would bill Spot on top of the already-paid block.

    Returns
    -------
    Dict[str, Any]
        State dict, also persisted to ``EC2_STATE_FILE``: instance_id, region,
        public_ip, instance_type, control_token, vllm_api_key, ...
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
        # 2) State file lost, live tagged instance: rebuild state from its
        #    user-data (see _recover_tagged_instance).
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
        # and a waiter timeout must not kill the whole provision.
        shutdown_instance(wait=False)

    # 3) Fresh launch.
    return _launch_fresh(
        instance_types, regions, volume_gb, idle_timeout_min, max_lifetime_min, my_ip
    )


def _wait_model_ready(
    state: Dict[str, Any], model: str, timeout_min: int = EC2_SERVE_TIMEOUT_MIN
) -> None:
    """Poll the agent until vLLM answers /health for ``model``.

    First-time serves are dominated by the checkpoint download (hundreds of
    GB); cached swaps take minutes. On timeout the error reports the LAST
    polled ``container`` state and ``log_tail``.
    """
    last_status: Dict[str, Any] = {}
    consec_failures = 0

    def check() -> Optional[bool]:
        nonlocal last_status, consec_failures
        # A single dropped /status must NOT abort the (up to hours-long)
        # wait: the caller's egress NAT rotates source IPs mid-run, and one
        # flap killed an arm whose stale serve script then raced the next
        # arm's container. Only a SOLID stretch of unreachability counts as
        # the box being gone: 20 consecutive misses, i.e. at least 5 min at
        # the 15s poll (longer, since each miss also burns its own timeout).
        try:
            status = _agent(state, "GET", "/status", timeout=30, connect_retries=0)
        except (requests.exceptions.RequestException, RuntimeError) as exc:
            # RuntimeError too: _agent raises it for any non-2xx reply, and a
            # transient 500/503 must count as a miss like a dropped
            # connection, not abort the wait (same pair _wait_agent catches).
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
            # Include the launcher's own output: a container that dies
            # pre-entrypoint (bad mount, missing adapter file, OOM-kill)
            # leaves docker logs EMPTY, so the docker-run error lives only in
            # the serve script's output.
            raise RuntimeError(
                f"vLLM container for {model!r} exited during startup; docker logs tail:\n"
                f"{status.get('log_tail', '')}\n"
                f"launcher output tail:\n{status.get('serve_log_tail', '')}"
            )
        # "created" alongside a failed launcher rc is equally terminal:
        # the container exists but nothing will ever start it (an
        # orphaned launcher's docker run racing a swap's rm -f leaves a
        # name-conflicted "created" container and rc=125).
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
    """Point the provisioned instance's vLLM at ``model`` for a ``with`` body.

    Swaps the serving container (removing the previous model's), waits until
    the OpenAI endpoint is healthy on ``model``, then yields it. Exit tears
    NOTHING down (see the module docstring).

    Parameters
    ----------
    timeout_min : Optional[int]
        Health-wait budget; None means ``EC2_SERVE_TIMEOUT_MIN``.
    force : bool
        Swap even when the box is already healthy on ``model`` with the same
        launch payload. The default fast path skips the swap, so re-running a
        section cell after an interruption costs seconds, not a reload.

    Raises
    ------
    KeyError
        ``model`` has no ``EC2_DEPLOY_SPECS`` entry.
    RuntimeError
        The instance became healthy serving something else (another process
        swapped the model).
    """
    spec = EC2_DEPLOY_SPECS.get(model)
    if spec is None:
        raise KeyError(
            f"No EC2_DEPLOY_SPECS entry for model {model!r}; "
            "add one with hf_model_id / tp / max_model_len."
        )
    state = _require_state()
    # BEFORE the swap: a mismatched box must not generate one row.
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
        # LoRA adapters staged from S3 on the box before launch (see
        # _serve).
        serve_payload["adapters"] = [dict(a) for a in spec["adapters"]]
    if not force:
        # Decide BEFORE yielding: the yield must sit outside this try, or an
        # exception raised by the with-body would be swallowed here and the
        # generator would fall through to a second serve/yield.
        #
        # "Already serving" also requires the recorded launch payload to
        # match: the served name alone cannot tell a 32k container from a
        # 128k one, so after a spec edit a re-run must swap, not skip. No
        # record (older state file, or another client served) means swap.
        try:
            # connect_retries=0 like every other probe: a throw-away check
            # must not block ~10 min (40 retries x 15s) on an unreachable box.
            already_serving = (
                bool(
                    _agent(
                        state, "GET", "/status", timeout=15, connect_retries=0
                    ).get("healthy")
                )
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
    # ``serving`` (wire-payload key names) exists only for the fast path's
    # drift check above; ``last_serve`` is the stable-keyed record
    # server_config() reads back, so the argv that ACTUALLY launched stays
    # visible after a spec edit or after the box is gone.
    #
    # Re-read the state file before writing: the wait above can span hours
    # (cold checkpoint pulls), and a concurrent provision may have recorded a
    # replacement box in the meantime. Writing the entry snapshot back would
    # clobber that newer instance's identity -- requests would go to the dead
    # box and shutdown would terminate the wrong id.
    current = _load_state()
    if current is None or current.get("instance_id") != state.get("instance_id"):
        logging.warning(
            "serve_model: state file no longer records this instance "
            f"({state.get('instance_id')}); not writing last_serve."
        )
    else:
        current["serving"] = serve_payload
        current["last_serve"] = {
            "model": model,
            "hf_model_id": spec["hf_model_id"],
            "tp": serve_payload["tp"],
            "max_model_len": serve_payload["max_model_len"],
            "vllm_args": list(serve_payload["vllm_args"]),
            "image": EC2_VLLM_IMAGE,
            "served_at": datetime.now(timezone.utc).isoformat(),
        }
        _save_state(current)
        state = current
    logging.info(f"serve_model: {model!r} is up at {_base_url()}")
    if state.get("s3_cache"):
        # Weights are complete on disk, so refresh the S3 mirror in the
        # background (a fast no-op when S3 already has them) and the next
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
        # Intentionally no teardown: the next archetype swaps the
        # container, and the on-instance watchdog handles abandonment.
        logging.info(f"serve_model: leaving {model!r} serving (no teardown).")


def agent_status() -> Dict[str, Any]:
    """Return the control agent's view: container state, health, recent docker logs."""
    return _agent(_require_state(), "GET", "/status")


def shutdown_instance(wait: bool = True) -> None:
    """Gracefully terminate the experiment's instance, and clear local state.

    Resolves the target from the state file, falling back to the
    ``smolbench:experiment`` tag (so a lost state file still terminates the
    box). Asks the agent for an OS-level shutdown first (graceful for docker),
    then authoritatively calls TerminateInstances -- instance, EBS volume
    (DeleteOnTermination) and any served model die with it. The security group
    is deliberately left behind: it is free, and EC2 will not delete it while
    the instance's network interface lingers anyway.

    Parameters
    ----------
    wait : bool
        Block on the ``instance_terminated`` waiter. A waiter timeout is logged
        and swallowed: TerminateInstances already succeeded, and p5-class
        teardown can outlast botocore's 10-minute budget.
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
        # Terminated instances age out of the EC2 API entirely, so "not
        # found" means the job is already done (the watchdog beat us to it).
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
            # Termination is already issued (see the `wait` parameter doc);
            # crashing here would strand the caller after the action that
            # matters.
            logging.warning(
                f"shutdown_instance: {instance_id} still shutting down after the "
                "waiter's max attempts; termination is already issued, proceeding."
            )
    _clear_state(instance_id)
