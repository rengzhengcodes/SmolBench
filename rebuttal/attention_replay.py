"""Replay the rebuttal's stored transcripts through an open-weights attention capture.

The rebuttal collected the induction arms (``intens``, ``noise_intens``,
``extens``, ``related_intens``) and the deduction (Horn) arms from three hosted
models and stored, per mark or per cell, only text: the query, the reasoning, the
response. Those hosted models expose no attention. This module asks what the
same text looks like to the matching open-weights checkpoint: it rebuilds each
transcript's token sequence, sends it to a spot GPU box running the vLLM
attention-capture plugin (``smolbench.evals.attention`` is the store-agnostic
client half), and keeps the attention arrays in a private S3 bucket. The offline
reader (``read_captures``) then computes the pad-mass ratio the noise arm is about
and the attention entropies; ``read_entropy_table`` returns both studies' entropies
in one table.

Two studies share this driver, chosen with the ``study`` keyword of the entry
points: ``"induction"`` (default; the stored YAML runs) and ``"horn"`` (the
deduction rows files; see "The deduction (Horn) replay" below). Everything that
spends money or touches the bucket is one implementation for both.

What it does, in order
----------------------
1. ``plan_replay`` / ``build_jobs``: read the stored runs, rebuild every mark's
   prompt and completion token ids, label every token with its key class
   (``attention.token_classes``), and size the job. No AWS access, no network
   beyond cached tokenizer/template files.
2. ``replay_model``: print the launch summary, refuse unless the caller passed
   ``approved=True``, skip every job that already has an object in the bucket,
   provision ONE spot box, serve the checkpoint in capture mode, run the jobs in
   batches, ALWAYS terminate the box as soon as the batches return, and only then
   audit what landed and write a manifest per run (the audit downloads every array
   to this machine, and the box must not bill while that runs).
3. ``audit_existing``: audit and manifest the captures that are already in the bucket
   (those whose audit never ran, for example because it outlived the AWS session);
   S3 only, no box.
4. ``read_captures``: offline, over a local mirror of the S3 tree (``pull_captures`` makes
   one); ``read_entropy_table`` returns the entropies of both studies in one table.

Capture modes and versions
--------------------------
The plugin stores a job in one of two kinds, chosen per run with the ``mode``
keyword of ``plan_replay``, ``replay_model`` and ``build_jobs`` (default
``"mass"`` for induction and ``"summary"`` for deduction; ``MODES`` lists both):

* ``"mass"``: per-row arrays ``[L, P, H_local, ...]`` (``mass``, ``entropy``,
  ``sink``, and from version 2 ``prompt_entropy``). Size grows with the number
  of response rows ``P``.
* ``"summary"``: the sums of those per-row statistics over the rows, per layer
  and local head (``attention.SUMMARY_ARRAYS``). Size does not depend on ``P``,
  which is what makes long responses storable.

The ``capture_version`` field of a rank's meta json tells the kinds of object
apart: 1 is mass without ``prompt_entropy`` (the meta has no field), 2 is mass
with it (``CAPTURE_VERSION``, what a mass run requires), 3 is summary, 4 is
summary that also splits the prompt entropy by prompt key class
(``sum_prompt_entropy_by_class``; ``SUMMARY_CAPTURE_VERSION``, what a summary run
requires; the stored version-3 captures stay valid). The audit refuses a meta whose
mode and version disagree, so a summary capture never passes as a mass capture or
the reverse.
The reader accepts both kinds, also mixed within one arm, and computes the same
statistics from either.

Where the rebuilt sequence is an approximation
----------------------------------------------
The stored marks hold text, not token ids, and the capture runs a different
copy of the model than the one that wrote the text. The sequence the box sees
is therefore a reconstruction. Every item below is a place where it can differ
from what the hosted model actually saw or produced; ``APPROXIMATIONS`` holds
the same list, one line each, and every plan and manifest carries it.

1. Token ids are encoded again from the stored text. The hosted service never
   returned ids. The sampler may have produced a token split that the
   tokenizer would not choose when it encodes the same text, so the completion
   ids can differ from the generated ones while the text is identical.
2. The prompt comes from the chat template pinned in the open-weights
   repository at the deploy spec's revision, rendered by this module's own
   re-implementation of the Hugging Face rendering environment (a sandboxed
   Jinja environment with ``raise_exception``, ``strftime_now`` and a
   ``tojson`` filter). The hosted service may serve another template version,
   add a system prompt or a date we cannot see, and a template that needs
   anything beyond this environment fails loudly instead of being guessed.
   ``strftime_now`` returns the date of the replay, not of the collection.
3. The thinking delimiters (``REASONING_FORMATS``) are the only hand-written
   part. Everything else comes from the real template. They are checked for
   existence in the vocabulary and in the rendered prompt, not for being what
   the hosted service emitted. No whitespace is inserted around them, so any
   newline the service emitted between reasoning and answer, or trimmed from
   them, is not restored.
4. The stored reasoning and response were split by the hosted service. A mark
   with no stored reasoning is rebuilt with an empty reasoning block. A
   generation that was cut at the output cap is rebuilt with a closing
   end-of-turn token it never emitted. With ``label_answer_tokens=True`` the answer
   tokens (class 4) are the completion tokens of the stored response and that
   end-of-turn token, so the answer/reasoning boundary is the hosted service's split;
   a token straddling it is class 3, and a mark without stored reasoning is all answer.
5. The conversation matches what the collection harness sent. Induction: one
   user turn, no system message. Deduction: one system turn holding the cell's
   ``system.md`` and one user turn holding its ``prompt.md``. Server-side
   defaults the harness did not send (a system prompt, guardrails, sampling
   settings) are not represented.
6. The capture runs the pinned open-weights checkpoint on EC2 (its own numerics
   and kernels), teacher-forced on the stored completion. It measures that
   checkpoint's attention on the hosted model's text, not the hosted service's
   internal computation.
7. The pad class is found by rule for ``noise_intens`` and by construction for
   ``related_intens``. By rule: the longest whitespace run of at least
   ``attention.MIN_PAD_RUN_CHARS`` characters inside the query; a mark whose query
   holds another long whitespace run is mislabelled. By construction: the added
   rule lines and the whitespace after them, located from the ``intens`` query of
   the same seed and question (``_related_pad_span``); a mark whose ``intens``
   query is missing or does not match is not planned. A mark without a pad has an
   undefined ratio (reported as nan). With ``label_added_lines=True`` the ``extens``
   listing (what that arm adds after the ``intens`` rules: every position line with
   its own newline, up to the newline that opens the question) is class 1, located
   the same way (``_extens_listing_span``, which also requires the question text to
   equal the ``intens`` query's); a mark where it cannot be located, or whose rebuild
   has no class-1 token, is not planned. ``intens``, ``noise_intens`` and
   ``related_intens`` keep their classes with or without the flag, and without it
   ``extens`` is labelled by rule, as before.
8. Tokens that straddle the edge of the query (template text merged into the
   query's first or last token) take the full token text as their piece. The
   template tokens next to the query are class 2, never class 0.
9. Induction: when a seed and arm has more than one stored run, only the
   earliest run (lexicographic minimum of the stamp) is replayed, as in the
   released-results reader. Marks of later runs are never captured. Deduction:
   when a cell (rung, arm, seed, replicate) has several non-exception rows, only
   the earliest by ``(ts, line index)`` is replayed.
10. Induction: ``bedrock_token_counts`` is always ``None``: the stored marks carry
    no usage field, so the rebuilt length cannot be compared with the length the
    hosted service counted. Deduction: each row stores ``prompt_tokens`` and
    ``completion_tokens`` as the service counted them, and a job carries them as
    ``bedrock_token_counts`` for that comparison.
11. What the system message adds (deduction only). The cell's ``system.md`` is
    rendered as a system turn before the user turn, as the collection sent it. Its
    tokens are class 2 (they are not query text, like the template's own tokens).
    The template may trim or move that text (the Gemma-4 template puts it after the
    thinking marker inside its own system turn); the rebuild only checks that the
    text, or its stripped form, occurs in the rendered prompt. The class-1 tokens depend
    on ``label_added_lines``. By default (``False``, how the stored captures were made) no
    token is class 1: the deduction study has no whitespace pad, so the pad-ratio fields
    of a deduction arm are undefined. With ``label_added_lines=True`` the ADDED lines of a
    padded arm are class 1: the lines that fill a derivation-tree slot of the library
    (lorem-ipsum filler in ``pad``, renamed tree rules in ``tjunk``, ``disc`` and ``fwd``,
    lemma copies in ``rep``, the real tree rules in ``both`` and ``marked-lemma``). They are
    located by rule key from the rung's ``theory.json`` (``_horn_added_line_spans``) and
    checked against the ``lem`` arm of the same seed; ``lem`` has none. Each added line
    counts with its own terminating newline, and a token is class 1 only when it lies
    entirely inside the added lines, so a token that straddles into a lemma line, a heading
    or the blank line after the library keeps its class (0 or 2).

S3 layout, append-only rule and approval gate
---------------------------------------------
Objects live under ``s3://smolbench-rebuttals-<account>/bedrock-trio/attention``::

    <prefix>/induction/<model>/seed=<s>/<arm>--<stamp>/q<idx>.r<rank>.npz
    <prefix>/induction/<model>/seed=<s>/<arm>--<stamp>/q<idx>.r<rank>.json
    <prefix>/induction/<model>/seed=<s>/<arm>--<stamp>/manifest--<utc>.json

The directory name repeats the stored result file's ``<arm>--<stamp>`` so a
capture can always be traced to the one file it was built from. ``rank`` runs
over the tensor-parallel ranks of the box.

The bucket is APPEND-ONLY. The presigned PUT URLs sign ``If-None-Match: *``,
so S3 refuses a PUT onto an existing key with 412. Before provisioning this
module still lists every job's keys, because a re-sent job would only fail
with 412 on a billed box and a partial rank set cannot be completed by
re-sending: a job with ANY key present is never sent and is reported
(``skipped_existing``). Each tensor-parallel rank uploads its own npz and json,
so a stored job is complete only when both objects of every rank ``0..tp-1``
exist; a job with some but not all of them is also reported as ``partial``
(every missing key is logged): inspect those by hand. When the tp of the plan
is unknown only the two rank-0 objects can be checked, and the log line says
so. Manifests are written once under a microsecond stamp after the key is
shown to be absent. Nothing here deletes or overwrites.

Recapture: ``job_ids`` and fill mode. The ``job_ids`` keyword of ``plan_replay``,
``replay_model`` and ``audit_existing`` is an allow-list: only those jobs are planned, sent,
audited and manifested, and a name that is not among the built jobs is an error. A recapture
goes under the SAME keys, because the replay is a deterministic teacher-forced prefill: the
stored objects stay as they are and only the missing ones are added. ``replay_model(fill=True,
job_ids=[...])`` does that for a job that holds some but not all expected objects (a job that
lost a rank): after ``attention.fill_refusal`` has shown the stored objects to be of the same
kind (mode, capture version, tp), the job is sent and the plugin puts only the absent
objects. A rank whose npz already existed writes its meta with ``"npz_put": "existing"``, and
the audit then skips only the npz size comparison. The audit also refuses a rank whose meta
declares a ``gate_tol`` above ``MAX_GATE_TOL``, so no capture certifies itself with a loose
tolerance. The effective serve settings (``serve_settings``) are recorded in every manifest
as ``"serve"``. A new manifest that lists a job ``verified`` completes an older manifest that
listed it as failed: the reader takes the union of the verified entries of a folder.

Engine death. When the serving engine dies mid-run, ``replay_model`` stops sending, saves the
box's log tail to a new file while the box is still up, shuts the box down, audits and
manifests the jobs that did verify, and reports the rest as ``not_sent``. It does not raise.

Spending money needs an explicit decision. ``replay_model`` raises
``ApprovalRequired`` unless ``approved is True`` (the singleton; ``1`` and
``"yes"`` are refused) and does so before any EC2 or S3 client exists. The
provider's own spend guards stay in force: the idle watchdog from the default
provisioning arguments, the lifetime backstop, and termination in a
``finally`` block.

The deduction (Horn) replay
---------------------------
``study="horn"`` replays the cells of the deduction experiment. Inputs: the model's
rows file (JSON lines, ``bt.horn_rows_path(model)`` by default, or ``horn_rows=``: a
rows file, a folder holding ``<model>.jsonl``, or a mapping per model) and the rendered
rungs (``<rungs_dir>/<rung>/s<seed:04d>/<arm>/prompt.md`` and ``system.md``, default
``bt.RUNGS_DIR``). ``results_root`` is ignored. Each row is one cell and holds the
generation: ``content`` (the answer), ``reasoning``, the token counts and ``ts``.
The collection sent ``system.md`` as a system message and ``prompt.md`` as the user
message, so the rebuild renders both (approximation 11).

Selection rule. The rows file can be appended to while it is read, and several
machines can write parts of it, so rows can be out of time order. Each line is
parsed; an unterminated last line that does not parse is reported as torn and any
other bad line is reported with its line number (neither stops the plan). The filters
``arms``, ``seeds`` and ``reps`` apply first. Rows are then grouped by cell ``(rung,
arm, seed, rep)``. A row with ``verdict == "exception"`` holds no generation and never
counts (it is only counted per arm, ``exception_rows``). Of the other rows of a cell
the EARLIEST by ``(ts, line index)`` is replayed. A selected row that cannot be
rebuilt faithfully is a plan error and its cell is not planned: its ``spec_key`` is
another model's, the collection added a provider system prompt (whose text is not
stored), ``prompt.md`` or ``system.md`` is missing, the digest of ``prompt.md`` is not
the row's ``prompt_sha256`` (the rung changed since the collection), the stored text
is mis-decoded, or the rebuild fails.

Layout and keys. Objects live next to the induction ones, never under them::

    <prefix>/deduction/horn/<model>/<rung>/<arm>/s<seed>.rep<rep>.r<rank>.npz
    <prefix>/deduction/horn/<model>/<rung>/<arm>/s<seed>.rep<rep>.r<rank>.json
    <prefix>/deduction/horn/<model>/<rung>/<arm>/manifest--<utc>.json

The job id is ``horn.<rung>.<arm>.s<seed>.rep<rep>``. One manifest per ``<rung>/<arm>``
folder per run records the cell's seed, replicate, ``prompt_sha256`` and the row's
line index (``row_index``). The listing prefix ``s<seed>.rep<rep>.`` cannot match
another cell's objects, and no key matches an induction key.

Mode. Deduction responses are long (up to 131072 tokens), so jobs default to
``"summary"``, whose size does not grow with the response. ``plan_replay`` plans either
mode, so the size of the mass capture can be compared. ``replay_model(study="horn",
mode="mass")`` raises ``ValueError`` unless ``allow_horn_mass=True``, and the message
states the mass estimate. The instance tag is ``EC2_TAG-horn-<model>[-label]``
(``run_tag``), so a deduction run and an induction run of one model use separate boxes
and state files.

The deepseek-v3.1 serving refusal
---------------------------------
The shipped plugin wraps vLLM's ``Attention.forward`` and also its multi-head
latent attention path, so ``deepseek-v3.1`` is capture-supported and
``CAPTURE_UNSUPPORTED`` is empty. The MLA path has never run live. Serving that
model on the pinned vLLM image is unverified: it failed at engine start there on
2026-09-19. ``replay_model`` therefore raises ``ServeUnverified`` for it unless
``allow_unverified_serve=True`` (see ``SERVE_UNVERIFIED``). The plan for that
model still works, so its token sizes are known. Capture serves it with a
49152-token context (``CAPTURE_MAX_MODEL_LEN``); jobs longer than that are
excluded as over-context, in the plan and in the run. The ``capture_max_model_len``
keyword of ``plan_replay``, ``replay_model`` and ``audit_existing`` replaces that context
(of any model) for one run; it must be an integer up to the spec's ``max_model_len``.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import logging
import math
import numbers
import os
import re
import signal
import shutil
import sys
import tempfile
import threading
from collections.abc import Hashable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, FrozenSet, Iterator, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

from smolbench.evals import attention, attention_analysis, tokenization
from smolbench.evals.quiz import Marks
from smolbench.evals.results_store import format_run_ts, parse_s3_uri

__all__ = [
    "APPROXIMATIONS",
    "ARMS",
    "ApprovalRequired",
    "BUCKET",
    "CAPTURE_MAX_MODEL_LEN",
    "CAPTURE_UNSUPPORTED",
    "CAPTURE_VERSION",
    "CaptureUnsupported",
    "MODES",
    "SUMMARY_CAPTURE_VERSION",
    "SUMMARY_CAPTURE_VERSIONS",
    "ChatTemplate",
    "DEFAULT_RESULTS_ROOT",
    "DEFAULT_S3_URI",
    "EC2_TAG",
    "run_tag",
    "HornRun",
    "INSTANCE_TYPES",
    "MAX_GATE_TOL",
    "PLUGIN_DEFAULT_GATE_TOL",
    "PlannedJob",
    "REASONING_FORMATS",
    "REGION",
    "ReasoningFormat",
    "ReasoningFormatError",
    "Rebuilt",
    "ReplayPlan",
    "ReplayReport",
    "Run",
    "SERVE_UNVERIFIED",
    "STATE_DIR",
    "STUDIES",
    "ServeUnverified",
    "ShutdownFailed",
    "TemplateMismatch",
    "TemplateUnavailable",
    "attention_shape",
    "audit_captures",
    "audit_existing",
    "build_jobs",
    "capture_max_model_len",
    "check_reasoning_format",
    "find_runs",
    "job_id_for",
    "load_chat_template",
    "load_model_config",
    "looks_misdecoded",
    "plan_replay",
    "pull_captures",
    "read_captures",
    "read_entropy_table",
    "entropy_ci",
    "job_seed",
    "rebuild_sequence",
    "replay_model",
    "run_prefix",
    "serve_settings",
    "write_manifest",
]

_HERE = Path(__file__).resolve().parent


def _load_bedrock_trio() -> ModuleType:
    """Return the sibling ``bedrock_trio`` module, importing it by file path.

    ``rebuttal/`` is not a package, so the module is loaded from the path
    anchored on this file. It is registered in ``sys.modules`` BEFORE
    ``exec_module``: it uses ``from __future__ import annotations`` together
    with dataclasses, and dataclass processing looks the module up by name, which
    fails for an unregistered module. An already-registered module of the same
    name is reused, so a caller (or a test) that loaded it first keeps one
    shared copy.

    Returns
    -------
    ModuleType
        The ``bedrock_trio`` module.

    Raises
    ------
    ImportError
        When the file cannot be turned into an import spec.
    """
    name = "bedrock_trio"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _HERE / "bedrock_trio.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name} from {_HERE / 'bedrock_trio.py'}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        # A half-initialised module must not stay registered for the next import.
        sys.modules.pop(name, None)
        raise
    return module


bt = _load_bedrock_trio()

#: Private results bucket of the rebuttal (created for the rebuttal runs only).
BUCKET: str = "smolbench-rebuttals-414266451290"
#: Region of ``BUCKET``.
REGION: str = "us-west-2"
#: Default destination of the captures: bucket plus key prefix.
DEFAULT_S3_URI: str = f"s3://{BUCKET}/bedrock-trio/attention"
#: The induction arms replayed; the same three the collection ran.
ARMS: Tuple[str, ...] = tuple(bt.INDUCTION_ARMS)
#: Folder that holds ``induction/<model>/seed=<s>/<arm>--<stamp>.yaml``; this is
#: the convention of ``smolbench.induction.repro`` (its ``data`` argument).
DEFAULT_RESULTS_ROOT: Path = bt.RESULTS_DIR / "induction"
#: Directory of the EC2 state file this driver uses. The state holds secrets, and
#: generated files stay inside the repository tree, anchored on this file.
STATE_DIR: Path = _HERE / "attention_state"
#: Prefix of the EC2 experiment tag of a capture box (reattach, recovery, termination).
#: The provider reattaches to a live instance with its tag, so each run gets its own tag
#: and state file (``run_tag``); two runs that shared them would share one box.
EC2_TAG: str = "smolbench-rebuttal-attention"

#: Spot instance types hunted per model, in preference order.
INSTANCE_TYPES: Dict[str, Tuple[str, ...]] = {
    # ~62 GB of BF16 weights: any 8-GPU H100 or H200 box holds them with room for
    # the un-chunked 131072-token prefill and the plugin's float32 chunks.
    "gemma-4-31b": ("p5.48xlarge", "p5e.48xlarge"),
    # ~240 GB of BF16 weights fit in 640 GB (p5) and 1128 GB (p5e) of HBM.
    "nemotron-3-super-120b-a12b": ("p5.48xlarge", "p5e.48xlarge"),
    # The ~690 GB FP8 checkpoint does not fit the p5's 640 GB of HBM, so the
    # larger-memory H200 types only.
    "deepseek-v3.1": ("p5e.48xlarge", "p5en.48xlarge"),
}

#: Models whose capture cannot be trusted, with the reason. ``replay_model``
#: refuses them unless told otherwise. Empty: the plugin covers every roster model.
CAPTURE_UNSUPPORTED: Dict[str, str] = {}

#: Models whose serving on the pinned vLLM image is not verified, with the reason.
#: ``replay_model`` refuses them (``ServeUnverified``) unless told otherwise.
SERVE_UNVERIFIED: Dict[str, str] = {
    "deepseek-v3.1": (
        "on 2026-09-19, on the vLLM image pinned as EC2_VLLM_IMAGE in the EC2 provider "
        "(digest sha256:26354b5e...), this model died at engine start on every attempt with "
        "transformers' error \"Couldn't instantiate the backend tokenizer ... You need to have "
        "sentencepiece or tiktoken installed to convert a slow tokenizer\"; the root cause was "
        "never diagnosed. The model served on EC2 before only on other (nightly) vLLM images. "
        "The capture plugin's multi-head latent attention path has never run live."
    ),
}

#: Context length to serve per model for capture, overriding the spec's
#: ``max_model_len``. DeepSeek-V3.1: vLLM's startup memory-profiling run at the full
#: 131072 tokens under eager mode is unmeasured, so capture uses a shorter context.
CAPTURE_MAX_MODEL_LEN: Dict[str, int] = {"deepseek-v3.1": 49152}


def capture_max_model_len(model: str, spec: Mapping[str, Any]) -> int:
    """Return the context length capture serves `model` with.

    Parameters
    ----------
    model : str
        Roster key.
    spec : Mapping[str, Any]
        The model's deploy spec; must carry ``max_model_len`` unless `model` is
        listed in ``CAPTURE_MAX_MODEL_LEN``.

    Returns
    -------
    int
        The ``CAPTURE_MAX_MODEL_LEN`` override when listed, else ``spec["max_model_len"]``.

    Examples
    --------
    >>> capture_max_model_len("deepseek-v3.1", {"max_model_len": 131072})
    49152
    >>> capture_max_model_len("other", {"max_model_len": 8192})
    8192
    """
    if model in CAPTURE_MAX_MODEL_LEN:
        return CAPTURE_MAX_MODEL_LEN[model]
    return int(spec["max_model_len"])


#: One line per approximation item of the module docstring, same order.
APPROXIMATIONS: Tuple[str, ...] = (
    "1. token ids are re-encoded from stored text; the sampler's own token split is unknown",
    "2. prompt rendered from the pinned repository template by a re-implementation of the HF "
    "rendering environment; the hosted service's template, system prompt and date are unknown",
    "3. thinking delimiters are a hand-written table, checked only for vocabulary and prompt "
    "presence; whitespace around them is not restored",
    "4. reasoning/response were split by the hosted service; missing reasoning is rebuilt empty "
    "and capped generations get an end-of-turn token they never emitted; with label_answer_tokens "
    "the answer (class 4) is the rebuilt response plus that token, from the service's split",
    "5. induction: one user turn, no system message; deduction: one system turn (the cell's "
    "system.md) and one user turn (its prompt.md); server-side defaults are not represented",
    "6. the capture runs the pinned open-weights checkpoint on EC2, teacher-forced on the stored "
    "completion, not the hosted service's computation",
    "7. the pad class is found by rule for noise_intens (longest whitespace run of at least "
    f"{attention.MIN_PAD_RUN_CHARS} characters in the query) and by construction for "
    "related_intens (added rule lines and trailing whitespace, located from the intens query); "
    "with label_added_lines the extens listing (every position line with its newline, located "
    "from the intens query) is class 1, intens has none",
    "8. tokens straddling the query edge take their full token text as their piece",
    "9. induction: only the earliest stored run per seed and arm is replayed; deduction: only "
    "the earliest non-exception row per (rung, arm, seed, rep) cell",
    "10. induction: bedrock_token_counts is None (the stored marks carry no usage field); "
    "deduction: the row's prompt_tokens and completion_tokens as the service counted them",
    "11. deduction: the cell's system.md is rendered as a system turn before the user turn, as "
    "the collection sent it; its tokens are class 2; the template may trim or move it (Gemma-4 "
    "puts it after the thinking marker inside its system turn); by default no class-1 token "
    "exists; with label_added_lines the added lines of a padded arm (the derivation-tree slots, "
    "located from theory.json, each with its own newline) are class 1, a token straddling into "
    "another line is not, and lem has none",
)

#: Message when the plan cannot say how big the capture is.
_BEDROCK_COUNTS_NOTE: str = "not stored in the marks; no comparison possible"
#: The deduction counterpart: each row stores the service's own usage counts.
_HORN_BEDROCK_COUNTS_NOTE: str = (
    "stored per row (prompt_tokens, completion_tokens); summed per arm in per_arm"
)

#: Wire-safe job-id characters; ``attention.mass_job`` accepts exactly these.
_UNSAFE_ID_CHAR = re.compile(r"[^A-Za-z0-9._=+-]")
#: Where the repository vendors each checkpoint's ``config.json`` at its pinned revision.
_ARCH_CONFIGS_PATH: Path = _HERE.parent / "scripts" / "arch" / "arch_configs_raw.json"
#: Suffix of the marker the released-results reader uses for an invalidated run.
_SUPERSEDED_SUFFIX = ".superseded"
#: A special-token string, e.g. ``<think>``, ``<|channel>`` or ``<channel|>``.
_SPECIAL_TOKEN_RE = re.compile(r"<[^<>\s]*>")
#: Allowed deviation of ``mass.sum(-1) + sink`` from 1 in the content audit.
_ROW_SUM_TOL: float = 2e-2
#: Allowed negative excess of an entropy value (float16 rounding of a zero).
_ENTROPY_FLOOR: float = -1e-3
#: Smallest mass or sink entry the audit accepts: float16 rounding only, so a row with a
#: negative entry that compensates a large positive one (sum still 1) is refused.
_MASS_FLOOR: float = -1e-3
#: Slack added to the entropy ceiling ``ln(attended keys)``: the box stores entropy
#: as float16, whose spacing near the largest values (~12 nats) is about 8e-3.
_ENTROPY_CEIL_TOL: float = 1e-2
#: Absolute part of the slack in the ``prompt_entropy`` chain-rule cross-check (nats).
#: Five float16 quantities enter the check (the prompt mass ``m``, the response mass
#: ``r``, the sink mass ``s``, the whole-row entropy ``H`` and ``prompt_entropy`` ``Hp``).
#: float16 keeps about 3 significant decimal digits (relative error up to 2**-11), so ``H``
#: and ``Hp`` of about 11 nats are stored to within about 4e-3, ``m * Hp`` inherits that
#: scaled by ``m`` plus ``m``'s own relative error times ``Hp``, and the grouping term
#: ``G = -(m ln m + r ln r + s ln s)`` has slope ``-(ln p + 1)`` in each mass, which is
#: unbounded as ``p`` goes to 0 or 1 but multiplied by an error proportional to ``p``
#: itself. Measured on clean synthetic captures built from real softmax rows (every
#: combination of global or windowed layer, with or without a sink, flat, peaked and mixed
#: logits, response part random, one-hot or uniform, 8 to 33000 keys, 1200 rows per
#: configuration for the short sequences and about 190 for the long ones), the largest
#: violation of either side before any tolerance was 0.0086 nats, and the largest
#: violation as a fraction of this tolerance was 0.13. The value 0.05 therefore keeps a
#: margin of 5.8 times on the absolute part alone (7.9 times with the relative part);
#: that is above the required 3 times, so the starting value was kept.
_PE_CHAIN_ABS_TOL: float = 0.05
#: Relative part of the slack: ``tol = _PE_CHAIN_ABS_TOL + _PE_CHAIN_REL_TOL * (1 + H)``,
#: since the float16 spacing of ``H`` and ``Hp`` grows with their size.
_PE_CHAIN_REL_TOL: float = 2e-3
#: Mass capture format the shipped plugin writes; version 2 added ``prompt_entropy``. New
#: mass captures come from the plugin in this repository, so the audit requires it.
#: Version 1 (mass without ``prompt_entropy``, no field in the meta) is still readable.
CAPTURE_VERSION: int = 2
#: Capture format the shipped plugin writes in summary mode, so what a summary run requires.
#: The versions tell the kinds of object apart: 1 and 2 are mass captures (see
#: ``CAPTURE_VERSION``), 3 and 4 summary captures, so a version-2 audit can never certify a
#: summary npz or the reverse. Version 4 adds ``sum_prompt_entropy_by_class``.
SUMMARY_CAPTURE_VERSION: int = 4
#: Every summary capture version the audit accepts: 3 (stored in the bucket, no class split)
#: and 4. Version 4 is audited further (the class split; see ``_audit_summary_arrays``).
SUMMARY_CAPTURE_VERSIONS: Tuple[int, ...] = (3, 4)
#: The loosest self-consistency tolerance a capture may declare in its meta
#: (``gate_tol``). The audit refuses a rank above it. A recapture of jobs that lost one rank
#: at a gate figure of 0.031 to 0.040 (against the plugin default, ``PLUGIN_DEFAULT_GATE_TOL``)
#: needs 0.05, and that figure was approved as the ceiling. Design: the cap lives here, in the
#: audit, and not only in the serve call, because a capture must not certify itself with a
#: tolerance as loose as it likes: the audit compares the gate figure with the tolerance the
#: meta declares, so without a cap any figure would pass.
MAX_GATE_TOL: float = 0.05
#: The plugin's tolerance when ``SMOLBENCH_ATTN_GATE_TOL`` is unset (the string ``"3e-2"`` in
#: the plugin source; a test pins the two together). ``serve_settings`` reports it as the
#: effective tolerance of a run that passed no ``gate_tol``.
PLUGIN_DEFAULT_GATE_TOL: float = 0.03
#: Capture modes of the induction replay, ``mass`` first (the default). A subset of
#: ``attention.CAPTURE_MODES``: ``rows`` has no key classes, so this replay never uses it.
MODES: Tuple[str, ...] = ("mass", "summary")
#: Number of eight-byte values a summary npz holds per (layer, head): ``sum_entropy``,
#: ``sum_prompt_entropy``, ``n_prompt_entropy``, ``sum_mass`` (4 classes), ``sum_sink``,
#: ``sum_pad_ratio``, ``n_pad_ratio``, ``sum_m_hp``, ``sum_chain_hi``, ``sum_chain_lo`` and
#: version 4 (what the plugin writes): ``sum_prompt_entropy_by_class`` (3 classes) and the answer
#: sums ``sum_prompt_entropy_answer``, ``n_prompt_entropy_answer``,
#: ``sum_prompt_entropy_by_class_answer`` (3), ``sum_entropy_answer`` and ``sum_mass_answer`` (4).
#: 13 + 3 + 10 = 26. All are float64 or int64.
_SUMMARY_VALUES_PER_HEAD: int = 26
#: Relative part of the tolerance of the version-4 identity
#: ``sum_prompt_entropy_by_class.sum(-1) == sum_prompt_entropy``. Both sides are float64 sums
#: of float32 values the box derived from the SAME float32 ``p ln p`` terms of each row,
#: summed in two orders (a ``torch.sum`` over the prompt keys; a matmul with the class one-hot
#: for the split). Every term has the same sign, so each row's float32 sum has a relative
#: error of at most about ``k * 2**-24`` for ``k`` serial additions; the stored sums were measured
#: to agree to 5.4e-9 relative on the CPU (1000 rows, 11000 prompt keys), and the GPU's blocked
#: reductions at 1.2e5 keys are expected well below 1e-5. The matmul may
#: run in TF32 when ``VLLM_FLOAT32_MATMUL_PRECISION`` is not ``highest`` (the default is), which
#: rounds each term to a relative 2**-11 (4.9e-4); 1e-3 covers that with a margin of 2, as the
#: mass audit's TF32 allowance does, and is still far below any difference between classes.
_BY_CLASS_IDENTITY_RTOL: float = 1e-3
#: Absolute part of that tolerance, per row with a defined prompt entropy (nats): it covers a
#: cell whose prompt entropy is near 0 (every row a point mass), where the relative part vanishes.
_BY_CLASS_IDENTITY_ATOL_PER_ROW: float = 1e-6


#: The two studies this driver replays; ``"induction"`` is the default of every entry point.
STUDIES: Tuple[str, ...] = ("induction", "horn")


def _check_study(study: str) -> str:
    """Return `study` when it is one of ``STUDIES``.

    Raises
    ------
    ValueError
        When `study` is not ``"induction"`` or ``"horn"``.
    """
    if study not in STUDIES:
        raise ValueError(f"study must be one of {STUDIES}, got {study!r}")
    return study


def _resolve_mode(mode: Optional[str], study: str = "induction") -> str:
    """Return the capture mode to use: `mode`, or the study's default for ``None``.

    Design: ``None`` (not ``"mass"``) is the signature default so that a caller who
    passes nothing keeps the behaviour from before summary mode existed, while the
    resolution and the refusal of an unknown value live in this one place. The default
    differs by study: induction keeps ``"mass"``; the deduction responses are long
    (up to 131072 tokens) and a mass capture grows with the response, so deduction
    defaults to ``"summary"``.

    Parameters
    ----------
    mode : Optional[str]
        ``None`` or one of ``MODES``.
    study : str, optional
        ``"induction"`` (default) or ``"horn"``; only picks the default for ``None``.

    Returns
    -------
    str
        An element of ``MODES``.

    Raises
    ------
    ValueError
        When `mode` is neither ``None`` nor in ``MODES`` (``"rows"`` included: this
        replay needs key classes).

    Examples
    --------
    >>> _resolve_mode(None), _resolve_mode(None, "horn"), _resolve_mode("mass", "horn")
    ('mass', 'summary', 'mass')
    """
    if mode is None:
        return "summary" if study == "horn" else "mass"
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    return mode


# --------------------------------------------------------------------------- errors


class ApprovalRequired(PermissionError):
    """Raised by ``replay_model`` unless the caller passed ``approved=True``."""


class CaptureUnsupported(RuntimeError):
    """Raised when a model's capture is known not to work and the caller did not override it."""


class ServeUnverified(RuntimeError):
    """A model whose serving on the pinned image is not verified, and the caller did not override it."""


class ShutdownFailed(RuntimeError):
    """The box could not be terminated after a capture that itself returned.

    ``replay_model`` raises it only after the content audit and the manifests are
    done, so the capture results are not lost: they are on ``report``. A box may
    still be billing, so the caller must treat this as an incident. The original
    error is the ``__cause__``.
    """

    def __init__(self, message: str, report: "ReplayReport") -> None:
        super().__init__(message)
        #: The finished report: verified, failed and audit-failed jobs and the manifests.
        self.report = report


class TemplateUnavailable(RuntimeError):
    """The pinned chat template, config or tokenizer of a model could not be loaded."""


class TemplateMismatch(ValueError):
    """The rendered prompt does not contain the stored query."""


class ReasoningFormatError(ValueError):
    """A model's thinking delimiters fail validation against its tokenizer or template."""


# ------------------------------------------------------------------ reasoning format


@dataclass(frozen=True)
class ReasoningFormat:
    """The hand-written part of the rebuild: how a model delimits its thinking.

    Everything else of the prompt comes from the real chat template. These
    strings are needed because the stored reasoning and response are separate
    fields while the model saw one stream.
    """

    #: Chat-template variables that switch thinking on (e.g. ``{"enable_thinking": True}``).
    template_kwargs: Dict[str, Any]
    #: Text that opens the thinking block.
    think_open: str
    #: Text that closes the thinking block.
    think_close: str
    #: Text that ends the assistant turn.
    end_of_turn: str
    #: Strings the rendered generation prompt must contain when thinking is on.
    prompt_markers: Tuple[str, ...] = ()


#: Thinking delimiters per roster key. See ``check_reasoning_format`` for how
#: each is validated.
REASONING_FORMATS: Dict[str, ReasoningFormat] = {
    "deepseek-v3.1": ReasoningFormat(
        template_kwargs={"thinking": True},
        think_open="<think>",
        think_close="</think>",
        end_of_turn="<｜end▁of▁sentence｜>",
        prompt_markers=(),
    ),
    "nemotron-3-super-120b-a12b": ReasoningFormat(
        template_kwargs={"enable_thinking": True},
        think_open="<think>",
        think_close="</think>",
        end_of_turn="<|im_end|>",
        prompt_markers=(),
    ),
    "gemma-4-31b": ReasoningFormat(
        template_kwargs={"enable_thinking": True},
        think_open="<|channel>thought\n",
        think_close="<channel|>",
        end_of_turn="<turn|>",
        prompt_markers=("<|think|>",),
    ),
}


def check_reasoning_format(
    model: str,
    tokenizer: Any,
    prompt_text: str,
    *,
    fmt: Optional[ReasoningFormat] = None,
) -> None:
    """Validate a model's thinking delimiters against its tokenizer and a rendered prompt.

    Checks two things. (a) Every delimiter that is a special-token string must
    be one vocabulary entry (``tokenizer.token_to_id`` is not ``None``). The
    candidates are the leading ``<...>`` token of ``think_open`` (so
    ``"<|channel>thought\\n"`` checks ``"<|channel>"``; the plain text after it
    is not a token), and ``think_close`` and ``end_of_turn`` as a whole. A
    delimiter that is plain text, not of the ``<...>`` shape, has nothing to
    check. (b) Every ``prompt_markers`` string must occur in `prompt_text`, the
    prompt rendered with thinking on.

    Parameters
    ----------
    model : str
        Roster key; selects ``REASONING_FORMATS[model]`` and names the model in errors.
    tokenizer : Any
        Anything with ``token_to_id(str) -> int | None`` (``HFTokenizer``).
    prompt_text : str
        A prompt rendered by the real template with the format's template kwargs.
    fmt : ReasoningFormat, optional
        Format to check instead of the table entry (``build_jobs`` passes the one
        it uses).

    Raises
    ------
    ReasoningFormatError
        When the model has no format, a special-token delimiter is not a single
        vocabulary entry, or a marker is absent from the prompt. The message
        lists every failure.
    """
    if fmt is None:
        if model not in REASONING_FORMATS:
            raise ReasoningFormatError(f"{model}: no entry in REASONING_FORMATS")
        fmt = REASONING_FORMATS[model]
    failures: List[str] = []

    # Phase 1: special-token delimiters must be single vocabulary entries.
    candidates: List[Tuple[str, str]] = []
    opener = _SPECIAL_TOKEN_RE.match(fmt.think_open.strip())
    if opener:
        candidates.append(("think_open", opener.group(0)))
    if _SPECIAL_TOKEN_RE.fullmatch(fmt.think_close):
        candidates.append(("think_close", fmt.think_close))
    if _SPECIAL_TOKEN_RE.fullmatch(fmt.end_of_turn):
        candidates.append(("end_of_turn", fmt.end_of_turn))
    for field_name, token in candidates:
        if tokenizer.token_to_id(token) is None:
            failures.append(f"{field_name} {token!r} is not a vocabulary entry")

    # Phase 2: the rendered prompt must show the template switched thinking on.
    for marker in fmt.prompt_markers:
        if marker not in prompt_text:
            failures.append(f"prompt marker {marker!r} is absent from the rendered prompt")

    if failures:
        raise ReasoningFormatError(f"{model}: " + "; ".join(failures))


# ------------------------------------------------------------------ chat template


class ChatTemplate:
    """A chat template compiled in a re-implementation of the HF rendering environment.

    Hugging Face renders chat templates in an immutable sandboxed Jinja
    environment with ``trim_blocks`` and ``lstrip_blocks``, the loop-control
    extension, a ``raise_exception`` function, ``strftime_now`` and a ``tojson``
    filter that keeps non-ASCII text. ``transformers`` is not installed in this
    environment, so this class rebuilds that environment (approximation item 2
    of the module docstring). A template that uses anything else fails when
    compiled or rendered; nothing is guessed.

    Parameters
    ----------
    source : str
        Jinja source of the template.
    bos_token : str, optional
        Value of the ``bos_token`` template variable.
    eos_token : str, optional
        Value of the ``eos_token`` template variable.

    Raises
    ------
    jinja2.exceptions.TemplateSyntaxError
        When `source` does not compile.

    Examples
    --------
    >>> t = ChatTemplate("{{ bos_token }}{% for m in messages %}[{{ m['content'] }}]{% endfor %}",
    ...                  bos_token="<s>")
    >>> t.render(messages=[{"role": "user", "content": "hi"}])
    '<s>[hi]'
    """

    def __init__(self, source: str, bos_token: str = "", eos_token: str = "") -> None:
        import jinja2
        import jinja2.exceptions
        import jinja2.sandbox

        def raise_exception(message: str) -> None:
            raise jinja2.exceptions.TemplateError(message)

        def strftime_now(fmt: str) -> str:
            return datetime.now().strftime(fmt)

        def tojson(
            value: Any,
            ensure_ascii: bool = False,
            indent: Optional[int] = None,
            separators: Optional[Tuple[str, str]] = None,
            sort_keys: bool = False,
        ) -> str:
            return json.dumps(
                value, ensure_ascii=ensure_ascii, indent=indent,
                separators=separators, sort_keys=sort_keys,
            )

        env = jinja2.sandbox.ImmutableSandboxedEnvironment(
            trim_blocks=True, lstrip_blocks=True, extensions=["jinja2.ext.loopcontrols"]
        )
        env.globals["raise_exception"] = raise_exception
        env.globals["strftime_now"] = strftime_now
        env.filters["tojson"] = tojson
        self.source = source
        self.bos_token = bos_token
        self.eos_token = eos_token
        self._template = env.from_string(source)

    def render(
        self,
        messages: Sequence[Mapping[str, Any]],
        add_generation_prompt: bool = True,
        **template_kwargs: Any,
    ) -> str:
        """Render `messages` to the prompt text.

        Parameters
        ----------
        messages : Sequence[Mapping[str, Any]]
            Chat turns, each with ``role`` and ``content``.
        add_generation_prompt : bool, optional
            Whether to end with the assistant-turn opener (default True).
        **template_kwargs : Any
            Extra template variables (e.g. ``enable_thinking``).

        Returns
        -------
        str
            The rendered text, unmodified (no strip, no BOS added beyond what the
            template itself emits).

        Raises
        ------
        jinja2.exceptions.TemplateError
            When the template calls ``raise_exception`` or fails to render.
        """
        return self._template.render(
            messages=list(messages),
            add_generation_prompt=add_generation_prompt,
            bos_token=self.bos_token,
            eos_token=self.eos_token,
            **template_kwargs,
        )


def _spec_repo_revision(model: str) -> Tuple[Dict[str, Any], str, Optional[str]]:
    """Return ``(deploy spec, tokenizer repo, pinned revision)`` of `model`.

    The revision rule is the one ``tokenization.for_model`` uses: the spec's pinned
    revision belongs to the weights repository, so it applies only when the
    tokenizer comes from that same repository.

    Raises
    ------
    KeyError
        When `model` has no deploy spec.
    """
    from smolbench.evals.providers import ec2

    spec = ec2.EC2_DEPLOY_SPECS.get(model)
    if spec is None:
        raise KeyError(f"no EC2_DEPLOY_SPECS entry for model {model!r}")
    repo = spec.get("tokenizer_hf_id") or spec["hf_model_id"]
    revision = tokenization._pinned_revision(spec) if repo == spec["hf_model_id"] else None
    return spec, repo, revision


def _hub_json(repo: str, filename: str, revision: Optional[str], local_files_only: bool) -> Any:
    """Download one JSON file from the hub (cache-aware) and parse it."""
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(repo, filename, revision=revision, local_files_only=local_files_only)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _token_text(value: Any) -> str:
    """Return a tokenizer-config special token as text (``str``, ``{"content": ...}`` or absent)."""
    if isinstance(value, Mapping):
        value = value.get("content")
    return value if isinstance(value, str) else ""


def load_chat_template(model: str, *, local_files_only: bool = False) -> ChatTemplate:
    """Load the pinned chat template of `model`'s checkpoint.

    The repository and revision come from the deploy spec (the revision the box
    serves). The template is the repository's ``chat_template.jinja`` when it
    has one, else the ``chat_template`` entry of ``tokenizer_config.json`` (a
    string, or a list of ``{"name", "template"}`` entries of which ``"default"``
    is taken). ``bos_token`` and ``eos_token`` come from the same config. There is
    NEVER a fallback to a hand-written template: a rebuilt prompt from a guessed
    template would silently measure the wrong sequence.

    Parameters
    ----------
    model : str
        Roster key with an ``EC2_DEPLOY_SPECS`` entry.
    local_files_only : bool, optional
        Use only the local Hugging Face cache (no network).

    Returns
    -------
    ChatTemplate
        The compiled template with the config's special tokens.

    Raises
    ------
    KeyError
        When `model` has no deploy spec.
    TemplateUnavailable
        When no template can be read. The message gives the repo, revision and the
        underlying error. A fetch error on ``chat_template.jinja`` that is not
        a real "file absent" answer also raises, because falling back to the
        config's template could then pick a different template than the
        repository's. With `local_files_only`, a file that is merely not cached
        is such an error; only the hub's cached "not in the repository" marker
        (or a live "not in the repository" answer) allows the fallback.
    """
    from huggingface_hub import _CACHED_NO_EXIST, hf_hub_download, try_to_load_from_cache
    from huggingface_hub.errors import EntryNotFoundError, LocalEntryNotFoundError

    _spec, repo, revision = _spec_repo_revision(model)
    where = f"{repo}@{revision or 'HEAD'}"
    try:
        config = _hub_json(repo, "tokenizer_config.json", revision, local_files_only)
    except Exception as exc:  # noqa: BLE001 -- the hub raises a wide family here
        raise TemplateUnavailable(
            f"{model}: cannot load tokenizer_config.json of {where}: {type(exc).__name__}: {exc}"
        ) from exc

    # Preference order: the repository's own template file, then the config entry.
    source: Optional[str] = None
    try:
        path = hf_hub_download(
            repo, "chat_template.jinja", revision=revision, local_files_only=local_files_only
        )
        source = Path(path).read_text(encoding="utf-8")
    except LocalEntryNotFoundError as exc:
        # LocalEntryNotFoundError subclasses EntryNotFoundError, so it must be
        # caught first. Offline, the hub raises it both for a file that is simply
        # not cached and for a file the hub once answered "not in the repository"
        # (recorded as a .no_exist marker). Only the second is a real absence;
        # falling back on the first could pick a different template than the
        # repository's own file.
        marker = try_to_load_from_cache(repo, "chat_template.jinja", revision=revision)
        if marker is not _CACHED_NO_EXIST:
            raise TemplateUnavailable(
                f"{model}: cannot fetch chat_template.jinja of {where}: it is not in the local "
                "cache and no cached 'not in the repository' answer exists: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
    except EntryNotFoundError:
        pass  # the hub said the repository has no template file: the config entry decides
    except Exception as exc:  # noqa: BLE001
        raise TemplateUnavailable(
            f"{model}: cannot fetch chat_template.jinja of {where}: {type(exc).__name__}: {exc}"
        ) from exc
    if source is None:
        entry = config.get("chat_template")
        if isinstance(entry, str):
            source = entry
        elif isinstance(entry, list):
            named = {e.get("name"): e.get("template") for e in entry if isinstance(e, Mapping)}
            source = named.get("default")
    if not isinstance(source, str) or not source:
        raise TemplateUnavailable(
            f"{model}: {where} has no chat_template.jinja and its tokenizer_config.json "
            "has no usable chat_template; refusing to guess a template"
        )
    return ChatTemplate(
        source,
        bos_token=_token_text(config.get("bos_token")),
        eos_token=_token_text(config.get("eos_token")),
    )


def _load_model_config_with_source(
    model: str, *, local_files_only: bool = False
) -> Tuple[Dict[str, Any], str]:
    """Return ``(config.json dict, where it came from)`` for `model`.

    The repository vendors each checkpoint's config at its pinned revision in
    ``scripts/arch/arch_configs_raw.json``. That entry is read first, but only
    when its ``revision`` equals the revision the deploy spec serves, so an
    outdated vendored copy is never used. Otherwise ``config.json`` is downloaded.

    Raises
    ------
    KeyError
        When `model` has no deploy spec.
    TemplateUnavailable
        When the vendored copy does not apply and the download fails.
    """
    _spec, repo, revision = _spec_repo_revision(model)
    if revision is not None:
        try:
            vendored = json.loads(_ARCH_CONFIGS_PATH.read_text(encoding="utf-8"))
            entry = vendored.get(model)
        except (OSError, ValueError) as exc:
            logging.info(f"attention_replay: vendored configs unreadable ({exc!r}); downloading")
            entry = None
        if isinstance(entry, Mapping) and entry.get("revision") == revision and isinstance(
            entry.get("config"), dict
        ):
            return dict(entry["config"]), f"vendored scripts/arch/arch_configs_raw.json @{revision}"
    try:
        config = _hub_json(repo, "config.json", revision, local_files_only)
    except Exception as exc:  # noqa: BLE001
        raise TemplateUnavailable(
            f"{model}: cannot load config.json of {repo}@{revision or 'HEAD'}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    return config, f"downloaded config.json of {repo}@{revision or 'HEAD'}"


def load_model_config(model: str, *, local_files_only: bool = False) -> Dict[str, Any]:
    """Load `model`'s ``config.json`` at the pinned revision.

    Parameters
    ----------
    model : str
        Roster key with an ``EC2_DEPLOY_SPECS`` entry.
    local_files_only : bool, optional
        Use only the local Hugging Face cache when the vendored copy does not apply.

    Returns
    -------
    Dict[str, Any]
        The parsed config. The vendored copy in ``scripts/arch/arch_configs_raw.json``
        is used when its revision equals the spec's; no network is touched then.

    Raises
    ------
    KeyError
        When `model` has no deploy spec.
    TemplateUnavailable
        When the config cannot be loaded.
    """
    return _load_model_config_with_source(model, local_files_only=local_files_only)[0]


def attention_shape(config: Mapping[str, Any]) -> Tuple[int, int]:
    """Return ``(n_attention_layers, n_heads)`` of a model config.

    Reads ``text_config`` when present (multimodal configs), else the config
    itself. Heads are ``num_attention_heads``. Layers are the count of ``"*"`` in
    ``hybrid_override_pattern`` when that key is present (a hybrid stack: its
    state-space blocks never call into the capture plugin), else
    ``num_hidden_layers``.

    Parameters
    ----------
    config : Mapping[str, Any]
        Parsed ``config.json``.

    Returns
    -------
    Tuple[int, int]
        Attention layers, attention heads.

    Raises
    ------
    ValueError
        When the heads or the layer count cannot be read.

    Examples
    --------
    >>> attention_shape({"num_hidden_layers": 61, "num_attention_heads": 128})
    (61, 128)
    >>> attention_shape({"text_config": {"num_hidden_layers": 60, "num_attention_heads": 32}})
    (60, 32)
    >>> attention_shape({"hybrid_override_pattern": "M-M*M-*", "num_attention_heads": 32,
    ...                  "num_hidden_layers": 7})
    (2, 32)
    """
    cfg = config.get("text_config") or config
    heads = cfg.get("num_attention_heads")
    if not isinstance(heads, int):
        raise ValueError("config has no integer num_attention_heads")
    pattern = cfg.get("hybrid_override_pattern")
    if pattern:
        layers = str(pattern).count("*")
    else:
        layers = cfg.get("num_hidden_layers")
    if not isinstance(layers, int) or layers < 1:
        raise ValueError("config has no attention layer count (hybrid_override_pattern / num_hidden_layers)")
    return layers, heads


# ------------------------------------------------------------------- rebuild a mark


@dataclass
class Rebuilt:
    """A mark's rebuilt token sequence and key classes."""

    #: Token ids of the rendered generation prompt.
    prompt_ids: Tuple[int, ...]
    #: Token ids of reasoning, delimiters, response and end-of-turn.
    completion_ids: Tuple[int, ...]
    #: Key class per token of ``prompt + completion`` (see ``attention.token_classes``).
    classes: Tuple[int, ...]
    #: The rendered prompt.
    prompt_text: str
    #: The rebuilt completion text.
    completion_text: str
    #: Places where this mark's rebuild needed a judgement.
    notes: Tuple[str, ...]


def _pad_span_in_pieces(
    offsets: Sequence[Tuple[int, int]],
    pieces: Sequence[str],
    pad_query_span: Tuple[int, int],
    query: str,
    located: str,
    q_start: int,
) -> Tuple[Tuple[int, int], int]:
    """Map a pad range of the query to ``token_classes`` coordinates and count straddlers.

    ``token_classes`` reads a span in the concatenation of the pieces, but
    ``rebuild_sequence`` blanks the piece of every token outside the query, so
    that concatenation starts at the first token that overlaps the query, not at
    the prompt's start. The range is first moved to prompt coordinates, then
    shifted by the start of the first non-empty piece. One shift is exact only
    when the non-empty pieces tile the prompt text, which is checked.

    Parameters
    ----------
    offsets : Sequence[Tuple[int, int]]
        ``(start, end)`` prompt-text character offsets of every prompt token.
    pieces : Sequence[str]
        The piece of each token as ``rebuild_sequence`` builds it (empty outside the query).
    pad_query_span : Tuple[int, int]
        Pad range in `query` coordinates, already validated.
    query : str
        The stored query.
    located : str
        The query as found in the prompt: `query`, or its stripped form.
    q_start : int
        Offset of `located` in the prompt text.

    Returns
    -------
    Tuple[Tuple[int, int], int]
        The span in piece-concatenation coordinates, and the number of tokens
        with a non-empty piece that contain a span edge strictly inside them.

    Raises
    ------
    ValueError
        When the non-empty pieces are not adjacent in the prompt text, so the
        shift between the two coordinate systems is not one number. (A ``ValueError``,
        not an assertion: ``_build`` reports it for the one mark and plans the rest.)
    """
    lead = len(query) - len(query.lstrip()) if located != query else 0
    # Prompt coordinates, clipped to the located text (the template may have stripped the query).
    low = q_start + min(max(pad_query_span[0] - lead, 0), len(located))
    high = q_start + min(max(pad_query_span[1] - lead, 0), len(located))

    # The pieces concatenate to the prompt text from the first overlapping token on
    # only while those tokens tile it without gaps or overlaps.
    kept = [(start, end) for (start, end), piece in zip(offsets, pieces) if piece]
    if any(a_end != b_start for (_s, a_end), (b_start, _e) in zip(kept, kept[1:])):
        raise ValueError(
            "the tokens that overlap the query are not adjacent in the prompt text; "
            "the pad span cannot be mapped to piece coordinates"
        )
    origin = kept[0][0] if kept else 0
    straddling = sum(1 for start, end in kept if start < low < end or start < high < end)
    return (low - origin, high - origin), straddling


def _pad_spans_in_pieces(
    offsets: Sequence[Tuple[int, int]],
    pieces: Sequence[str],
    pad_query_spans: Sequence[Tuple[int, int]],
    query: str,
    located: str,
    q_start: int,
) -> Tuple[List[Tuple[int, int]], FrozenSet[int], int]:
    """Map several pad ranges of the query to ``token_classes`` coordinates.

    The many-span counterpart of ``_pad_span_in_pieces``, built so that it needs no
    tiling: membership is decided per token in PROMPT coordinates (a token with a
    non-empty piece whose ``[start, end)`` lies inside the union of the ranges), and
    each run of consecutive member tokens is then expressed in piece coordinates from
    the cumulative piece lengths, the same sums ``token_classes`` computes.

    Design: a byte-level tokenizer can split one character into tokens whose offsets
    overlap (``(538, 540)`` then ``(539, 540)``), so the pieces then repeat a character
    and no single shift relates the two coordinate systems; ``_pad_span_in_pieces``
    refuses such a prompt. Working from the member tokens sidesteps that, and the caller
    checks the classes ``token_classes`` returns against the member set returned here.

    Parameters
    ----------
    offsets, pieces, query, located, q_start
        As for ``_pad_span_in_pieces``.
    pad_query_spans : Sequence[Tuple[int, int]]
        Pad ranges in `query` coordinates, already validated; they may touch.

    Returns
    -------
    Tuple[List[Tuple[int, int]], FrozenSet[int], int]
        The spans in piece-concatenation coordinates (one per run of member tokens), the
        indexes of the member tokens, and the number of tokens with a non-empty piece that
        overlap the union without lying inside it (they straddle an edge, are not members).
    """
    lead = len(query) - len(query.lstrip()) if located != query else 0
    # Prompt coordinates, clipped to the located text, then joined where they touch, so a
    # token crossing the shared edge of two adjacent ranges lies inside the union.
    ranges = sorted(
        (q_start + min(max(lo - lead, 0), len(located)), q_start + min(max(hi - lead, 0), len(located)))
        for lo, hi in pad_query_spans
    )
    union: List[Tuple[int, int]] = []
    for lo, hi in ranges:
        if lo >= hi:
            continue
        if union and lo <= union[-1][1]:
            union[-1] = (union[-1][0], max(union[-1][1], hi))
        else:
            union.append((lo, hi))

    members: List[int] = []
    straddling = 0
    cursor = 0  # first range that can still hold a token (tokens come in text order)
    for index, ((start, end), piece) in enumerate(zip(offsets, pieces)):
        if not piece:
            continue
        while cursor < len(union) and union[cursor][1] <= start:
            cursor += 1
        # Ranges are disjoint and do not touch, so only the current one can contain the token;
        # the next one may still overlap it (a token that spans a gap between two ranges).
        if cursor < len(union) and union[cursor][0] <= start and end <= union[cursor][1]:
            members.append(index)
        elif any(lo < end and start < hi for lo, hi in union[cursor:cursor + 2]):
            straddling += 1

    # Piece coordinates: cumulative piece lengths, one span per run of consecutive members.
    cum = [0]
    for piece in pieces:
        cum.append(cum[-1] + len(piece))
    piece_spans: List[Tuple[int, int]] = []
    run_start: Optional[int] = None
    for pos, index in enumerate(members):
        if run_start is None:
            run_start = index
        if pos + 1 == len(members) or members[pos + 1] != index + 1:
            piece_spans.append((cum[run_start], cum[index + 1]))
            run_start = None
    return piece_spans, frozenset(members), straddling


def rebuild_sequence(
    query: str,
    reasoning: Optional[str],
    response: str,
    *,
    tokenizer: Any,
    template: Any,
    fmt: ReasoningFormat,
    pad_query_span: Optional[Tuple[int, int]] = None,
    system: Optional[str] = None,
    pad_query_spans: Optional[Sequence[Tuple[int, int]]] = None,
    label_answer: bool = False,
) -> Rebuilt:
    """Rebuild one mark's prompt ids, completion ids and key classes from its stored text.

    Steps. (1) Render the generation prompt of a single user turn holding
    `query` (preceded by a system turn holding `system` when that is given), with
    thinking on, and find the query inside it. (2) Build the
    completion text: if the prompt already ends with the thinking opener the
    template opened the block, so the completion starts at the reasoning;
    otherwise it starts with the opener. Then the closer, the response and the
    end-of-turn token follow, with no whitespace inserted. (3) Encode prompt and
    completion SEPARATELY, without added special tokens. (4) Label the prompt
    tokens by the character offsets of the tokenizer: a token whose span overlaps
    the query keeps its text as its piece, any other prompt token gets an empty
    piece (so ``token_classes`` makes it class 2); completion tokens are class 3.
    The pad class is found by rule unless `pad_query_span` is given (see below).

    With `pad_query_span` the pad is stated by construction. The query must then
    occur exactly once in the rendered prompt; the range is shifted to the
    prompt's coordinates and then into the coordinates of the concatenated pieces
    (the pieces of tokens outside the query are empty, so those coordinates start
    at the first token that overlaps the query), and handed to
    ``token_classes`` as ``pad_span``. A token that straddles an edge of the span
    is not class 1. The notes then say how many tokens are class 1 and how many
    straddle an edge. An EMPTY span (``start == end``, the deduction rebuild passes
    ``(0, 0)``) marks no token: no token is class 1, the note says "no pad class
    (deduction)" instead of the by-construction wording, and the span is not mapped to
    piece coordinates (so byte-split characters with overlapping offsets cannot fail it).

    With `pad_query_spans` the pad is several ranges of the query (the deduction rebuild
    passes the added lines of a padded arm). The query must occur exactly once, as for
    `pad_query_span`; a prompt token is class 1 when its piece is non-empty and its
    character range lies inside the union of the ranges (``_pad_spans_in_pieces``, which
    needs no tiling, so overlapping byte-split offsets are fine). The classes
    ``token_classes`` returns are then checked against that membership. An empty
    sequence marks no token. The notes say how many tokens are class 1, in how many
    ranges, and how many straddle an edge.

    With `label_answer` the answer tokens are class 4 (``attention.ANSWER_CLASS``): the
    completion tokens whose character range starts at or after the start of the stored
    `response` in the completion text (so the response and the end-of-turn token appended
    after it). Reasoning tokens and the thinking delimiters stay class 3, and a token that
    straddles the boundary (part delimiter, part response) is class 3. Without stored
    reasoning every completion token is class 4. The boundary is found from the
    tokenizer's character offsets of the completion text, encoded as one string (the
    same encoding the ids come from). The notes say how many tokens are class 4 and how
    many straddle the boundary. Without `label_answer` the classes are the ones of before
    the parameter existed.

    With `system` the conversation is ``[system, user]``. The template may trim the
    system text (Gemma-4 does) or move it (Gemma-4 puts it after the thinking marker
    inside its own system turn), so the check is only that `system` or its stripped
    form occurs in the rendered prompt. System tokens are class 2: only tokens that
    overlap the user query keep their text as piece (the rule for every prompt token).

    Parameters
    ----------
    query : str
        The stored user message. Must contain a non-whitespace character.
    reasoning : Optional[str]
        The stored reasoning, or ``None``/empty (rebuilt as an empty block, noted).
    response : str
        The stored response text.
    tokenizer : Any
        ``HFTokenizer``-like: ``encode_ids`` and ``encode_offsets``.
    template : Any
        ``ChatTemplate``-like: ``render(messages=, add_generation_prompt=, **kwargs)``.
    fmt : ReasoningFormat
        The model's thinking delimiters and template kwargs.
    pad_query_span : Optional[Tuple[int, int]], optional
        Half-open character range ``[start, end)`` of the pad inside `query`
        (``0 <= start <= end <= len(query)``). Default ``None``: the longest
        whitespace run of the query is the pad, by rule. When the template
        stripped the query, the range is shifted by the stripped leading
        characters and clipped to the stripped text.
    system : Optional[str], optional
        Text of a system message to render before the user turn. Default ``None``: no system
        message (the induction rebuild, byte-identical to before this parameter existed).
    pad_query_spans : Optional[Sequence[Tuple[int, int]]], optional
        Half-open character ranges of the pad inside `query`, each ``0 <= start <= end <=
        len(query)``; they may touch. Default ``None``. Mutually exclusive with
        `pad_query_span`.
    label_answer : bool, optional
        Label the answer tokens class 4 (see above). Default ``False``.

    Returns
    -------
    Rebuilt
        The sequence. ``len(classes) == len(prompt_ids) + len(completion_ids)``.

    Raises
    ------
    TemplateMismatch
        When the query is empty or is not found in the rendered prompt, when (with
        `pad_query_span`) it occurs more than once there, or when `system` is given and
        neither it nor its stripped form occurs in the rendered prompt (a template that
        drops system messages; the message says "system").
    ValueError
        When `pad_query_span` is not ``0 <= start <= end <= len(query)``, or when
        the tokens that overlap the query do not tile it without gaps or overlaps,
        so the span cannot be mapped to piece coordinates. Also when both
        `pad_query_span` and `pad_query_spans` are given, an element of `pad_query_spans`
        is out of bounds, or the class-1 tokens differ from the tokens inside its union.
    AssertionError
        When the tokenizer returns a different number of offsets than ids.

    Notes
    -----
    Pure given its collaborators; cost is two encodes of the full sequence.
    """
    notes: List[str] = []
    if pad_query_span is not None and not 0 <= pad_query_span[0] <= pad_query_span[1] <= len(query):
        raise ValueError(
            f"pad_query_span {tuple(pad_query_span)} must satisfy 0 <= start <= end <= "
            f"{len(query)} (the length of the query)"
        )
    if pad_query_spans is not None:
        if pad_query_span is not None:
            raise ValueError("pass pad_query_span or pad_query_spans, not both")
        for item in pad_query_spans:
            if not 0 <= item[0] <= item[1] <= len(query):
                raise ValueError(
                    f"pad_query_spans element {tuple(item)} must satisfy 0 <= start <= end <= "
                    f"{len(query)} (the length of the query)"
                )
    by_construction = pad_query_span is not None or pad_query_spans is not None

    # Phase 1: render the prompt and locate the query in it.
    messages: List[Dict[str, str]] = [{"role": "user", "content": query}]
    if system is not None:
        messages.insert(0, {"role": "system", "content": system})
    prompt_text = template.render(
        messages=messages,
        add_generation_prompt=True,
        **fmt.template_kwargs,
    )
    if not query.strip():
        raise TemplateMismatch("the stored query is empty or whitespace-only")
    # A template may drop system messages without complaint; the rebuilt prompt would then
    # lack the text the model was given, so refuse instead of measuring another sequence.
    if system is not None and system not in prompt_text and system.strip() not in prompt_text:
        raise TemplateMismatch(
            "the rendered prompt does not contain the system message; the chat template "
            "dropped or rewrote it"
        )
    located = query
    q_start = prompt_text.find(located)
    if q_start < 0:
        located = query.strip()
        q_start = prompt_text.find(located)
        if q_start < 0:
            raise TemplateMismatch("the rendered prompt does not contain the stored query")
        notes.append("template stripped the query")
    q_end = q_start + len(located)
    if by_construction and prompt_text.count(located) != 1:
        # A second copy (say, in a system turn) would make the span's position ambiguous.
        raise TemplateMismatch(
            f"the stored query occurs {prompt_text.count(located)} times in the rendered prompt; "
            "the pad span needs exactly one"
        )

    # Phase 2: completion text. No whitespace is inserted around the delimiters:
    # whatever separated reasoning from answer at collection time is unknown.
    if not reasoning:
        notes.append("no reasoning stored")
    body = reasoning or ""
    if prompt_text.rstrip().endswith(fmt.think_open.strip()):
        notes.append("thinking opened by the template")
        completion_text = body + fmt.think_close + response + fmt.end_of_turn
    else:
        completion_text = fmt.think_open + body + fmt.think_close + response + fmt.end_of_turn

    # Phase 3: encode the two halves separately. Generation never merges a token
    # across the prompt/completion boundary (the prompt was fixed before the
    # first token was sampled), whereas encoding the concatenation could. The
    # template already emits its own BOS, so no special tokens are added.
    prompt_ids = tuple(int(t) for t in tokenizer.encode_ids(prompt_text))
    completion_ids = tuple(int(t) for t in tokenizer.encode_ids(completion_text))

    # Phase 3b: the first answer token, with `label_answer`. The response starts right after
    # the closer (nothing is inserted), so its offset in the completion text is known exactly.
    answer_start: Optional[int] = None
    if label_answer:
        if not reasoning:
            answer_start = 0  # no stored reasoning: the whole completion is the answer
            notes.append(f"answer tokens: all {len(completion_ids)} completion tokens class 4 (no reasoning)")
        else:
            boundary = len(completion_text) - len(fmt.end_of_turn) - len(response)
            c_offsets = tokenizer.encode_offsets(completion_text)
            if len(c_offsets) != len(completion_ids):
                raise AssertionError(
                    f"tokenizer returned {len(c_offsets)} offsets for {len(completion_ids)} completion ids"
                )
            answer_start = next(
                (i for i, (start, _end) in enumerate(c_offsets) if start >= boundary), len(c_offsets)
            )
            straddle = sum(1 for start, end in c_offsets if start < boundary < end)
            notes.append(
                f"answer tokens: {len(completion_ids) - answer_start} class 4, "
                f"{straddle} straddle the reasoning/answer boundary"
            )

    # Phase 4: key classes from character offsets. Offsets, not per-token decode,
    # on purpose: decoding one byte-level BPE token can split a UTF-8 character.
    offsets = tokenizer.encode_offsets(prompt_text)
    if len(offsets) != len(prompt_ids):
        raise AssertionError(
            f"tokenizer returned {len(offsets)} offsets for {len(prompt_ids)} prompt ids"
        )
    pieces = [
        prompt_text[start:end] if start < q_end and end > q_start else ""
        for start, end in offsets
    ]
    pad_span: Optional[Tuple[int, int]] = None
    n_straddle = 0
    if pad_query_spans is not None:
        piece_spans, members, n_straddle = _pad_spans_in_pieces(
            offsets, pieces, pad_query_spans, query, located, q_start
        )
        classes = attention.token_classes(
            prompt_ids, completion_ids, lambda ids: pieces, pad_spans=piece_spans,
            answer_start=answer_start,
        )
        # The member set was decided in prompt coordinates; the classes come from piece
        # coordinates. They must name the same tokens, or the mapping went wrong somewhere
        # (non-monotone offsets, say), and the job would carry a pad it does not have.
        labelled = frozenset(i for i, c in enumerate(classes[: len(prompt_ids)]) if c == 1)
        if labelled != members:
            raise ValueError(
                f"the class-1 tokens ({len(labelled)}) differ from the tokens inside the pad "
                f"ranges ({len(members)}); the ranges cannot be mapped to piece coordinates"
            )
        notes.append(
            f"pad ranges by construction: {len(members)} tokens class 1 in "
            f"{len(pad_query_spans)} ranges, {n_straddle} straddle an edge of a range"
        )
        return Rebuilt(
            prompt_ids=prompt_ids,
            completion_ids=completion_ids,
            classes=tuple(classes),
            prompt_text=prompt_text,
            completion_text=completion_text,
            notes=tuple(notes),
        )
    if pad_query_span is not None and pad_query_span[0] == pad_query_span[1]:
        # An empty span labels nothing, so the piece-coordinate mapping is not needed, and it
        # must be skipped: a tokenizer that splits one character into byte tokens (U+2227 in
        # Nemotron) gives overlapping offsets such as (538, 540) then (539, 540), and the
        # mapping's tiling check would refuse the whole cell. (0, 0) is valid for any text.
        pad_span = (0, 0)
    elif pad_query_span is not None:
        pad_span, n_straddle = _pad_span_in_pieces(
            offsets, pieces, pad_query_span, query, located, q_start
        )
    classes = attention.token_classes(
        prompt_ids, completion_ids, lambda ids: pieces, pad_span=pad_span, answer_start=answer_start
    )
    if pad_query_span is not None:
        if pad_query_span[0] == pad_query_span[1]:
            # An empty span marks nothing; "by construction" would suggest a pad was found.
            notes.append("no pad class (deduction)")
        else:
            n_pad = classes[: len(prompt_ids)].count(1)
            notes.append(
                f"pad span by construction: {n_pad} tokens class 1, "
                f"{n_straddle} straddle an edge of the span"
            )
    return Rebuilt(
        prompt_ids=prompt_ids,
        completion_ids=completion_ids,
        classes=tuple(classes),
        prompt_text=prompt_text,
        completion_text=completion_text,
        notes=tuple(notes),
    )


# ------------------------------------------------------------------- stored results


@dataclass(frozen=True)
class Run:
    """One stored result file: ``<arm>--<stamp>.yaml`` of one seed."""

    model: str
    seed: int
    arm: str
    #: File stem after ``<arm>--`` (an ISO-like UTC stamp; contains ``:``).
    stamp: str
    path: Path


def find_runs(results_root: Path, model: str) -> List[Run]:
    """Return the run that counts for every seed and arm of `model`.

    For each ``seed=<s>`` directory under ``<results_root>/induction/<model>/`` and
    each arm of ``ARMS``, the file with the EARLIEST stamp (lexicographic minimum;
    stamps sort in time order) is chosen. Earliest wins because the results store
    is an append-only log: a later file is a re-collection, and the released
    results count the first collection. Files with a ``.superseded`` marker beside
    them are skipped, as in ``smolbench.induction.repro.select_runs``.

    Parameters
    ----------
    results_root : Path
        Folder holding ``induction/<model>/seed=<s>/<arm>--<stamp>.yaml``.
    model : str
        Roster key.

    Returns
    -------
    List[Run]
        Sorted by seed, then arm order of ``ARMS``; empty when the model has no files.

    Raises
    ------
    ValueError
        When a ``seed=`` directory name does not end in an integer.
    """
    base = Path(results_root) / "induction" / model
    if not base.is_dir():
        return []
    runs: List[Run] = []
    seed_dirs = []
    for seed_dir in base.glob("seed=*"):
        try:
            seed_dirs.append((int(seed_dir.name.removeprefix("seed=")), seed_dir))
        except ValueError as exc:
            raise ValueError(f"{seed_dir}: seed directory name must be seed=<int>") from exc
    for seed, seed_dir in sorted(seed_dirs):
        for arm in ARMS:
            prefix = f"{arm}--"
            stamps = [
                p.stem[len(prefix):]
                for p in seed_dir.glob(f"{prefix}*.yaml")
                if not (seed_dir / (p.stem + _SUPERSEDED_SUFFIX)).exists()
            ]
            if stamps:
                stamp = min(stamps)
                runs.append(Run(model, seed, arm, stamp, seed_dir / f"{prefix}{stamp}.yaml"))
    return runs


def _int_set(values: Optional[Sequence[int]], name: str) -> Optional[FrozenSet[int]]:
    """Return `values` as a frozen set, or ``None`` (select all) when `values` is ``None``.

    An empty sequence stays an empty set: it selects nothing, which is not the same
    as ``None``. A string or a bool is refused so that ``seeds="01"`` or
    ``reps=[True]`` cannot silently select nothing or the value 1.

    Parameters
    ----------
    values : Optional[Sequence[int]]
        The filter, or ``None``.
    name : str
        Name of the filter (``"seeds"`` or ``"reps"``), for the error message.

    Raises
    ------
    ValueError
        When an entry is not an integer.
    """
    if values is None:
        return None
    chosen = set()
    for value in values:
        if isinstance(value, bool) or not isinstance(value, numbers.Integral):
            raise ValueError(f"{name} must be integers, got {value!r}")
        chosen.add(int(value))
    return frozenset(chosen)


def _seed_set(seeds: Optional[Sequence[int]]) -> Optional[FrozenSet[int]]:
    """Return `seeds` as a frozen set, or ``None`` (every seed) when `seeds` is ``None``.

    See ``_int_set``: an empty sequence selects no run, and a string or a bool is refused.

    Raises
    ------
    ValueError
        When an entry is not an integer.
    """
    return _int_set(seeds, "seeds")


@dataclass(frozen=True)
class HornRun:
    """One ``<rung>/<arm>`` folder of one model's deduction (Horn) rows.

    The deduction counterpart of ``Run``: the unit that owns a key prefix and a manifest.
    Frozen so that it is hashable (``_group_by_run`` groups jobs by it).
    """

    model: str
    rung: str
    arm: str
    #: The rows file the cells of this folder were read from.
    rows_path: Path


def run_prefix(s3_prefix: str, run: Union[Run, HornRun]) -> str:
    """Return the key prefix (trailing ``/``) holding one run's captures.

    Parameters
    ----------
    s3_prefix : str
        Key prefix above ``induction/`` or ``deduction/`` (no bucket); may be empty.
    run : Union[Run, HornRun]
        The stored induction run, or the deduction ``<rung>/<arm>`` folder.

    Returns
    -------
    str
        Induction: ``<s3_prefix>/induction/<model>/seed=<seed>/<arm>--<stamp>/``.
        Deduction: ``<s3_prefix>/deduction/horn/<model>/<rung>/<arm>/``.

    Examples
    --------
    >>> r = Run("m", 3, "intens", "2026-01-01T00:00:00Z", Path("x.yaml"))
    >>> run_prefix("a/b", r)
    'a/b/induction/m/seed=3/intens--2026-01-01T00:00:00Z/'
    >>> run_prefix("a/b", HornRun("m", "m64", "lem", Path("m.jsonl")))
    'a/b/deduction/horn/m/m64/lem/'
    """
    if isinstance(run, HornRun):
        parts = [p for p in (s3_prefix.strip("/"), "deduction", "horn", run.model) if p]
        return "/".join(parts) + f"/{run.rung}/{run.arm}/"
    parts = [p for p in (s3_prefix.strip("/"), "induction", run.model) if p]
    return "/".join(parts) + f"/seed={run.seed}/{run.arm}--{run.stamp}/"


def job_id_for(run: Run, mark_index: int) -> str:
    """Return the globally unique wire id of one mark.

    The stamp contains ``:``, which ``attention.mass_job`` rejects, so every
    character outside ``[A-Za-z0-9._=+-]`` becomes ``-``. The id names seed, arm
    and stamp, so it is unique across all runs of a model.

    Examples
    --------
    >>> r = Run("m", 0, "intens", "2026-01-01T00:00:00.5Z", Path("x.yaml"))
    >>> job_id_for(r, 4)
    's0.intens.2026-01-01T00-00-00.5Z.q4'
    """
    safe = _UNSAFE_ID_CHAR.sub("-", run.stamp)
    return f"s{run.seed}.{run.arm}.{safe}.q{mark_index}"


def _horn_job_id(rung: str, arm: str, seed: int, rep: int) -> str:
    """Return the wire id of one deduction cell: ``horn.<rung>.<arm>.s<seed>.rep<rep>``.

    Every character outside the wire-safe set becomes ``-`` (``_UNSAFE_ID_CHAR``).
    ``read_captures`` rebuilds the same id from directory and file names to look a cell up
    in the manifests, so this is the one place that spells it.

    Examples
    --------
    >>> _horn_job_id("m64", "lem", 100, 2)
    'horn.m64.lem.s100.rep2'
    """
    return _UNSAFE_ID_CHAR.sub("-", f"horn.{rung}.{arm}.s{seed}.rep{rep}")


@dataclass(frozen=True)
class PlannedJob:
    """A capture job plus where it came from."""

    job: attention.Job
    #: Induction: the stored result file. Deduction: the ``<rung>/<arm>`` folder.
    run: Union[Run, HornRun]
    #: Induction: the mark's index in its run. Deduction: the row's 0-based line index in the
    #: rows file.
    mark_index: int
    notes: Tuple[str, ...]
    #: Induction: always ``None``: the stored marks carry no token counts, so the rebuilt
    #: length cannot be compared with the hosted service's (approximation 10). Deduction:
    #: ``{"prompt_tokens": ..., "completion_tokens": ...}`` as the service counted them.
    bedrock_token_counts: Optional[Dict[str, int]] = None
    #: Deduction only: the cell's theory seed.
    seed: Optional[int] = None
    #: Deduction only: the cell's replicate number.
    rep: Optional[int] = None
    #: Deduction only: the 16-hex digest of ``prompt.md`` the row recorded and the rebuild checked.
    prompt_sha256: Optional[str] = None


def looks_misdecoded(text: Optional[str]) -> bool:
    """Return whether `text` is UTF-8 text that was read as ISO-8859-1.

    A stored transcript can hold the bytes of a UTF-8 character as separate
    Latin-1 characters (an arrow stored as three characters starting with
    ``"\\u00e2"``). Such text would be rebuilt into a different token sequence
    than the model produced. The test is a round trip: encode the text as
    Latin-1 and decode the bytes as UTF-8. Text that is mis-decoded decodes to
    something different from itself; clean text either fails one of the two
    steps (it holds a character above U+00FF, or its Latin-1 bytes are not valid
    UTF-8) or comes back unchanged (pure ASCII).

    Parameters
    ----------
    text : Optional[str]
        A stored query, reasoning or response; ``None`` is allowed.

    Returns
    -------
    bool
        ``False`` for ``None``, the empty string and pure-ASCII text, and when
        either round-trip step raises. Otherwise ``True`` exactly when the
        round trip succeeds and differs from `text`.

    Notes
    -----
    Text that really holds Latin-1 characters forming a valid UTF-8 sequence
    (a capital A with tilde followed by a copyright sign, written on purpose)
    is flagged too; the check cannot tell it from the defect, and such text is
    far rarer than the defect.

    Examples
    --------
    >>> looks_misdecoded("a \\u00e2\\u0086\\u0092 b")
    True
    >>> looks_misdecoded("a \\u2192 b")
    False
    >>> looks_misdecoded("plain ascii"), looks_misdecoded(""), looks_misdecoded(None)
    (False, False, False)
    """
    if not text or text.isascii():
        return False
    try:
        return text.encode("latin-1").decode("utf-8") != text
    except UnicodeError:
        # UnicodeEncodeError (a character above U+00FF) or UnicodeDecodeError
        # (the bytes are not UTF-8): the text was not produced by the defect.
        return False


#: The arm whose pad is stated by construction (added rule lines plus trailing whitespace).
RELATED_ARM: str = "related_intens"
#: The arm whose query the ``related_intens`` query extends; the pad is located against it.
RELATED_BASE_ARM: str = "intens"
#: The arm whose added lines (the position listing after the rules) are class 1 with
#: ``label_added_lines``; located against the ``intens`` query like the related pad.
EXTENS_ARM: str = "extens"


def _related_pad_span(intens_query: str, related_query: str, arm: str = RELATED_ARM) -> Tuple[int, int]:
    """Return the range a query adds after the rules, by comparison with its ``intens`` query.

    Both arms located this way are the intens query up to the end of the real rule
    lines (its ``head``, everything before ``bt.QUESTION_START``), then lines the arm
    adds, then the question. ``related_intens`` adds irrelevant rule lines and a few
    whitespace characters (its pad); ``extens`` adds the position listing, one line
    per position, each with its newline. The range is everything between the head and
    the LAST ``QUESTION_START`` of the query (the same split
    ``bedrock_trio.check_related_prompts`` uses), so the newline that opens
    ``QUESTION_START`` stays outside it.

    Parameters
    ----------
    intens_query : str
        The ``intens`` query of the same seed and question.
    related_query : str
        The query of `arm`.
    arm : str, optional
        The arm of `related_query`, named in the error messages; default ``RELATED_ARM``
        (the messages of that arm are unchanged).

    Returns
    -------
    Tuple[int, int]
        ``[start, end)`` in `related_query`; ``0 < start < end``.

    Raises
    ------
    ValueError
        With the reason, when `intens_query` has no ``QUESTION_START``, when
        `related_query` does not start with the head, has no ``QUESTION_START``
        after it, or has nothing between the two.
    """
    cut = intens_query.find(bt.QUESTION_START)
    if cut < 0:
        raise ValueError(f"the intens query has no {bt.QUESTION_START!r}; cannot find the head")
    head = intens_query[:cut]
    if not related_query.startswith(head):
        raise ValueError(f"the {arm} query does not start with the intens query's rules")
    end = related_query.rfind(bt.QUESTION_START)
    if end < len(head):
        raise ValueError(f"the {arm} query has no {bt.QUESTION_START!r} after the rules")
    if end == len(head):
        raise ValueError(f"the {arm} query has an empty pad (nothing between rules and question)")
    return len(head), end


def _extens_listing_span(intens_query: str, extens_query: str) -> Tuple[int, int]:
    """Return the range of the position listing in an ``extens`` query (the class-1 lines).

    An ``extens`` prompt is the ``intens`` rules followed by the listing
    (``smolbench.induction.periodic``: its context is ``intensional + extensional``), so
    the listing is what ``_related_pad_span`` finds between the intens head and the last
    ``QUESTION_START``. One check more than for ``related_intens``: the text from
    ``QUESTION_START`` on must equal the ``intens`` query's, so the two marks are the same
    question of the same seed and nothing but the listing lies between head and question.

    Parameters
    ----------
    intens_query : str
        The ``intens`` query of the same seed and question.
    extens_query : str
        The ``extens`` query.

    Returns
    -------
    Tuple[int, int]
        ``[start, end)`` in `extens_query`: every listing line with its own newline;
        ``0 < start < end``.

    Raises
    ------
    ValueError
        As ``_related_pad_span`` (naming ``extens``), or when the question text after the
        listing differs from the intens query's.
    """
    start, end = _related_pad_span(intens_query, extens_query, EXTENS_ARM)
    if extens_query[end:] != intens_query[intens_query.find(bt.QUESTION_START):]:
        raise ValueError(
            "the extens query's question differs from the intens query's; cannot locate the listing"
        )
    return start, end


@dataclass
class _Built:
    """Internal result of reading and rebuilding every run of one model."""

    #: Induction: the stored result files. Deduction: the ``<rung>/<arm>`` folders with a selected cell.
    runs: List[Union[Run, HornRun]] = field(default_factory=list)
    #: Induction: marks read. Deduction: cells selected (planned plus errored).
    marks: int = 0
    unreasoned: int = 0
    planned: List[PlannedJob] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    #: Deduction only: the arms of the plan, in plan order (see ``_horn_arm_order``).
    arm_order: List[str] = field(default_factory=list)
    #: Deduction only: arm -> the plan errors of that arm's cells (a subset of ``errors``).
    errors_by_arm: Dict[str, List[str]] = field(default_factory=dict)
    #: Deduction only: arm -> exception rows left out of the selection.
    exception_rows: Dict[str, int] = field(default_factory=dict)


#: Allowed spelling of a rung or arm name in a rows file. Both become a folder name in the
#: rungs directory and a key component, so ``/`` and every other unusual character is refused
#: (and ``.`` and ``..`` are refused separately: this class admits them).
_HORN_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _horn_name_ok(name: Any) -> bool:
    """Return whether `name` is a usable rung or arm name: ``[A-Za-z0-9._-]+`` and not ``.``/``..``."""
    return isinstance(name, str) and bool(_HORN_NAME_RE.match(name)) and name not in (".", "..")


@dataclass(frozen=True)
class _HornCell:
    """One selected deduction cell: its identity and the row that represents it."""

    #: 0-based physical line index of the row in the rows file (blank lines count).
    line_index: int
    rung: str
    arm: str
    seed: int
    rep: int
    row: Dict[str, Any]


@dataclass
class _HornSelection:
    """Result of ``_horn_select``: the cells to replay and what was refused on the way."""

    rows_path: Path
    #: Selected cells in plan order: rung (natural order), arm (``arm_order``), seed, rep.
    cells: List[_HornCell] = field(default_factory=list)
    #: File- and line-level plan errors (no arm to attach them to).
    errors: List[str] = field(default_factory=list)
    #: arm -> exception rows (after the filters).
    exception_rows: Dict[str, int] = field(default_factory=dict)
    arm_order: List[str] = field(default_factory=list)


def _natural_key(text: str) -> List[Union[int, str]]:
    """Return a sort key that orders ``m20`` before ``m64`` before ``m128`` (digit runs as numbers).

    Even positions are strings and odd ones integers for every input, so two keys always
    compare.
    """
    return [int(tok) if tok.isdigit() else tok for tok in re.split(r"(\d+)", text)]


def _horn_arm_order(seen: Sequence[str], wanted: Optional[Sequence[str]]) -> List[str]:
    """Return the arms of a deduction plan, in plan order.

    With an ``arms`` filter: its order, every arm present (also with no rows). Without: every
    arm of ``bt.HORN_ARMS`` in that order, then the other arms found in the rows, sorted.

    Design: all of ``bt.HORN_ARMS`` is listed even for an arm with no rows, as the induction
    plan lists every one of ``ARMS``, so two plans of one model read the same way.
    """
    if wanted is not None:
        return list(wanted)
    known = list(bt.HORN_ARMS)
    return known + sorted(arm for arm in set(seen) if arm not in known)


def _horn_cell_key(row: Any) -> Tuple[str, str, int, int]:
    """Return ``(rung, arm, seed, rep)`` of a parsed rows-file line.

    Raises
    ------
    ValueError
        With the reason, when the line is not a JSON object, lacks ``rung``, ``arm``,
        ``seed``, ``rep`` or ``verdict``, a name is not ``[A-Za-z0-9._-]+`` (not ``.``/``..``), a
        seed or replicate is not a non-negative integer, or a generation row (verdict other than
        ``"exception"``) has no ``ts`` string. Such a row cannot be placed in a cell or ordered.
    """
    if not isinstance(row, dict):
        raise ValueError(f"the line is JSON but not an object ({type(row).__name__})")
    for name in ("rung", "arm", "seed", "rep", "verdict"):
        if name not in row:
            raise ValueError(f"the row has no {name!r}")
    rung, arm, seed, rep = row["rung"], row["arm"], row["seed"], row["rep"]
    for label, name in (("rung", rung), ("arm", arm)):
        if not _horn_name_ok(name):
            raise ValueError(f"{label} {name!r} is not a folder name made of [A-Za-z0-9._-]")
    for label, number in (("seed", seed), ("rep", rep)):
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            raise ValueError(f"{label} {number!r} is not a non-negative integer")
    if not isinstance(row["verdict"], str):
        raise ValueError(f"verdict {row['verdict']!r} is not a string")
    if row["verdict"] != "exception" and not isinstance(row.get("ts"), str):
        raise ValueError("the row has no 'ts' string to order the cell's rows by")
    return rung, arm, seed, rep


def _horn_select(
    rows_path: Path,
    arms: Optional[Sequence[str]],
    seeds: Optional[FrozenSet[int]],
    reps: Optional[FrozenSet[int]],
) -> _HornSelection:
    """Read a deduction rows file and select one generation row per cell.

    The one reader of a rows file: building, planning, replaying and auditing all go
    through it, so they select the same cells. The file is read once as bytes (a snapshot:
    it may be appended to meanwhile) and split on ``\\n`` only, as ``bt._row_lines`` does
    (``str.splitlines`` also splits on U+2028, which a row's text can hold). Blank lines are
    skipped; the line index of every other line is its physical position, blank lines counted.
    Each line must decode as UTF-8 and parse as a JSON object with the keys of
    ``_horn_cell_key``; one that does not becomes a plan error with its 1-based line number,
    except an unterminated last line, which is reported as torn (a writer was cut off or is
    still writing). A missing or unreadable file is one plan error naming its path.

    The ``arms``, ``seeds`` and ``reps`` filters apply before the cells are formed. A row whose
    verdict is ``"exception"`` holds no generation: it is counted per arm and never selected.
    Of the other rows of a cell the earliest by ``(ts, line index)`` is kept: rows of one
    cell can come from several machines' parts of the file and be out of time order, and
    ``ts`` strings are ISO UTC, so they sort as text.

    Parameters
    ----------
    rows_path : Path
        The model's rows file.
    arms : Optional[Sequence[str]]
        Arms to keep, ``None`` for all. Also fixes the order of the plan's arms.
    seeds, reps : Optional[FrozenSet[int]]
        Theory seeds / replicate numbers to keep, ``None`` for all.

    Returns
    -------
    _HornSelection
        Cells in plan order, the file- and line-level errors, the exception rows per arm and
        the arm order.

    Notes
    -----
    Design: only the best row of each cell is kept while the file is scanned, so memory holds
    one row per cell, not the whole file (a row's reasoning can be hundreds of kilobytes).
    The raw bytes are held once.
    """
    sel = _HornSelection(rows_path=rows_path)
    try:
        data = rows_path.read_bytes()
    except FileNotFoundError:
        sel.errors.append(f"{rows_path}: the rows file does not exist")
        sel.arm_order = _horn_arm_order((), arms)
        return sel
    except OSError as exc:
        sel.errors.append(f"{rows_path}: cannot read the rows file: {type(exc).__name__}: {exc}")
        sel.arm_order = _horn_arm_order((), arms)
        return sel

    wanted_arms = None if arms is None else set(arms)
    chunks = data.split(b"\n")
    terminated = data.endswith(b"\n") or not data
    best: Dict[Tuple[str, str, int, int], Tuple[str, int, Dict[str, Any]]] = {}
    seen_arms: set = set()
    for index, chunk in enumerate(chunks):
        if not chunk.strip():
            continue  # blank line (also the empty piece after the final newline)
        try:
            row = json.loads(chunk.decode("utf-8"))
            rung, arm, seed, rep = _horn_cell_key(row)
        except ValueError as exc:  # UnicodeDecodeError and JSONDecodeError are ValueErrors too
            # Torn: the last line, cut off before its newline, so it does not parse. A last line
            # that parses but has a bad shape is an ordinary bad line.
            parse_failure = isinstance(exc, (json.JSONDecodeError, UnicodeDecodeError))
            if index == len(chunks) - 1 and not terminated and parse_failure:
                sel.errors.append(
                    f"{rows_path}: line {index + 1}: torn last line (no trailing newline and it "
                    f"does not parse: {exc}); a writer was cut off or is still writing"
                )
            else:
                sel.errors.append(f"{rows_path}: line {index + 1}: {exc}")
            continue
        # Filters first: a filtered-out row takes no part in the cells or the counts.
        if wanted_arms is not None and arm not in wanted_arms:
            continue
        if (seeds is not None and seed not in seeds) or (reps is not None and rep not in reps):
            continue
        seen_arms.add(arm)
        if row["verdict"] == "exception":
            sel.exception_rows[arm] = sel.exception_rows.get(arm, 0) + 1
            continue
        key = (rung, arm, seed, rep)
        rank = (row["ts"], index)
        if key not in best or rank < best[key][:2]:
            best[key] = (row["ts"], index, row)

    sel.arm_order = _horn_arm_order(sorted(seen_arms), arms)
    arm_rank = {arm: i for i, arm in enumerate(sel.arm_order)}
    for (rung, arm, seed, rep), (_ts, index, row) in sorted(
        best.items(),
        key=lambda item: (_natural_key(item[0][0]), arm_rank.get(item[0][1], len(arm_rank)), item[0][2], item[0][3]),
    ):
        sel.cells.append(_HornCell(index, rung, arm, seed, rep, row))
    return sel


def _horn_runs(model: str, sel: _HornSelection) -> List[HornRun]:
    """Return the ``<rung>/<arm>`` folders of the selected cells, in plan order (first cell first)."""
    seen: Dict[Tuple[str, str], HornRun] = {}
    for cell in sel.cells:
        seen.setdefault((cell.rung, cell.arm), HornRun(model, cell.rung, cell.arm, sel.rows_path))
    return list(seen.values())


@dataclass(frozen=True)
class _Source:
    """Where one study's stored transcripts come from, as the internal functions take it."""

    study: str = "induction"
    #: Induction: folder holding ``induction/<model>/...``.
    results_root: Path = DEFAULT_RESULTS_ROOT
    #: Deduction: the model's rows file.
    rows_path: Optional[Path] = None
    #: Deduction: the rendered rungs; ``None`` means ``bt.RUNGS_DIR``.
    rungs_dir: Optional[Path] = None
    #: Deduction: arm filter in the order given, ``None`` = all.
    arms: Optional[Tuple[str, ...]] = None
    #: Deduction: replicate filter, ``None`` = all.
    reps: Optional[FrozenSet[int]] = None
    #: Label the added lines as class 1: deduction, the padded arms' added lines
    #: (``_horn_added_line_spans``); induction, the ``extens`` listing (``_extens_listing_span``).
    label_added_lines: bool = False
    #: Label the answer tokens (the completion tokens of the stored response, after the
    #: reasoning block) as class 4, both studies (``rebuild_sequence(label_answer=True)``).
    label_answer_tokens: bool = False


def _horn_rows_file(model: str, horn_rows: Any, n_models: int = 1) -> Path:
    """Return the rows file of `model` from the ``horn_rows`` argument of an entry point.

    ``None`` is ``bt.horn_rows_path(model)``. A mapping must hold `model` (an absent model is
    refused, not defaulted: a typo in a model key would otherwise read another file). A
    directory means ``<dir>/<model>.jsonl``; anything else is the rows file itself, whether or
    not it exists (a missing file is a plan error, not a crash here).

    Raises
    ------
    ValueError
        When a mapping has no entry for `model`, or a rows FILE is given for more than one model
        (`n_models` > 1: one file holds one model's rows).
    """
    if horn_rows is None:
        return bt.horn_rows_path(model)
    if isinstance(horn_rows, Mapping):
        if model not in horn_rows:
            raise ValueError(f"horn_rows has no entry for model {model!r}")
        horn_rows, n_models = horn_rows[model], 1  # the mapping already names one file per model
    path = Path(horn_rows)
    if path.is_dir():
        return path / f"{model}.jsonl"
    if n_models > 1:
        raise ValueError(
            "horn_rows names one rows file, but several models are planned; pass a folder "
            "holding <model>.jsonl or a mapping model -> file"
        )
    return path


def _make_source(
    study: str,
    results_root: Path,
    rows_path: Optional[Path],
    rungs_dir: Optional[Path],
    arms: Optional[Sequence[str]],
    reps: Optional[Sequence[int]],
    label_added_lines: bool = False,
    label_answer_tokens: bool = False,
) -> _Source:
    """Validate the study arguments and return the ``_Source`` the internals take.

    Raises
    ------
    ValueError
        When `study` is unknown; when a deduction-only argument (`rows_path`, `rungs_dir`,
        `arms`, `reps`) is given for the induction study, where it would be silently ignored;
        when `arms` is a string or holds a non-string; `reps` holds a non-integer; or
        `label_added_lines` or `label_answer_tokens` is not a ``bool``. Both flags apply to both
        studies.
    """
    _check_study(study)
    if not isinstance(label_added_lines, bool):
        raise ValueError(f"label_added_lines must be a bool, got {label_added_lines!r}")
    if not isinstance(label_answer_tokens, bool):
        raise ValueError(f"label_answer_tokens must be a bool, got {label_answer_tokens!r}")
    if study == "induction":
        extras = [
            name for name, value in (
                ("horn_rows", rows_path), ("rungs_dir", rungs_dir), ("arms", arms), ("reps", reps),
            ) if value is not None
        ]
        if extras:
            raise ValueError(f"{', '.join(extras)} apply only to study='horn'")
        return _Source(
            "induction", Path(results_root), label_added_lines=label_added_lines,
            label_answer_tokens=label_answer_tokens,
        )
    if rows_path is None:
        raise ValueError("study='horn' needs the rows file (callers resolve it with _horn_rows_file)")
    arm_filter: Optional[Tuple[str, ...]] = None
    if arms is not None:
        if isinstance(arms, str) or not all(isinstance(arm, str) for arm in arms):
            raise ValueError(f"arms must be a sequence of arm names, got {arms!r}")
        arm_filter = tuple(dict.fromkeys(arms))  # drop duplicates, keep the order given
    return _Source(
        "horn", Path(results_root), Path(rows_path),
        None if rungs_dir is None else Path(rungs_dir), arm_filter, _int_set(reps, "reps"),
        label_added_lines, label_answer_tokens,
    )


def _build_induction(
    model: str,
    results_root: Path,
    s3_prefix: str,
    get_tokenizer: Callable[[], Any],
    get_template: Callable[[], Any],
    fmt: Optional[ReasoningFormat],
    seeds: Optional[FrozenSet[int]] = None,
    mode: str = "mass",
    label_added_lines: bool = False,
    label_answer_tokens: bool = False,
) -> _Built:
    """Read the induction runs of `model` and rebuild every mark (see ``_build``).

    Tokenizer and template are fetched through callables on first need, so a model
    with no result files never touches the hub. When `seeds` is given only the runs
    of those seeds are read; the filter is applied before ``run_of`` is built, and
    a ``related_intens`` run looks up its ``intens`` run of the SAME seed, so the
    pairing survives the filter. `mode` (an element of ``MODES``, already resolved by
    the caller) is recorded on every job: the sequence is the same in both modes, only
    what the box stores differs.

    With `label_added_lines` an ``extens`` mark's position listing is class 1, located
    by construction from the ``intens`` query of the same seed and question
    (``_extens_listing_span``), as a ``related_intens`` pad is. A mark whose listing
    cannot be located, or whose rebuild then has no class-1 token, is a plan error and
    is not planned unlabelled. Every other arm keeps its classes, and without the flag
    the rebuild is the one of before the flag existed.

    With `label_answer_tokens` the answer tokens of every mark are class 4
    (``rebuild_sequence(label_answer=True)``); a mark with no class-4 token is a plan error.
    """
    import jinja2.exceptions

    built = _Built(runs=[r for r in find_runs(results_root, model) if seeds is None or r.seed in seeds])
    if not built.runs:
        return built
    tokenizer = get_tokenizer()
    template = get_template()
    if fmt is None:
        if model not in REASONING_FORMATS:
            raise ReasoningFormatError(f"{model}: no entry in REASONING_FORMATS")
        fmt = REASONING_FORMATS[model]

    checked = False
    # The one run per (seed, arm) that find_runs chose, to locate a related_intens pad
    # against the intens run of the same seed; its queries are read once per seed.
    run_of = {(r.seed, r.arm): r for r in built.runs}
    intens_queries: Dict[int, Optional[List[str]]] = {}

    def base_queries(seed: int) -> Optional[List[str]]:
        if seed not in intens_queries:
            base = run_of.get((seed, RELATED_BASE_ARM))
            intens_queries[seed] = None if base is None else [
                m.query for m in Marks.loads(base.path.read_text(encoding="utf-8")).marks
            ]
        return intens_queries[seed]

    for run in built.runs:
        marks = Marks.loads(run.path.read_text(encoding="utf-8")).marks
        prefix = run_prefix(s3_prefix, run)
        for idx, mark in enumerate(marks):
            built.marks += 1
            if not bt.reasoned(mark.reasoning):
                built.unreasoned += 1
            # A mis-decoded field would be re-encoded into tokens the model never
            # saw, and the error would surface only as a skewed class mix. Refuse
            # the mark here, naming the fields; the run's other marks still plan.
            bad_fields = [
                name
                for name, value in (
                    ("query", mark.query), ("reasoning", mark.reasoning), ("response", mark.response)
                )
                if looks_misdecoded(value)
            ]
            if bad_fields:
                built.errors.append(
                    f"{run.path}#q{idx}: mis-decoded text (UTF-8 read as ISO-8859-1) in "
                    f"{', '.join(bad_fields)}; not planned"
                )
                continue
            try:
                # By construction for related_intens: the pad range comes from the intens
                # query of the same seed and question. Any failure here is this mark's error.
                pad_span: Optional[Tuple[int, int]] = None
                # extens is located only with the flag: without it the mark is rebuilt with
                # the by-rule pad exactly as before, so a default plan is unchanged.
                listing = run.arm == EXTENS_ARM and label_added_lines
                if run.arm == RELATED_ARM or listing:
                    what = "the listing of an extens" if listing else "the pad of a related_intens"
                    base = base_queries(run.seed)
                    if base is None:
                        raise ValueError(
                            f"no {RELATED_BASE_ARM} run for seed {run.seed}; "
                            f"cannot locate {what} mark"
                        )
                    if idx >= len(base):
                        raise ValueError(
                            f"question {idx} is missing from the {RELATED_BASE_ARM} run "
                            f"({len(base)} questions); cannot locate the "
                            + ("listing" if listing else "pad")
                        )
                    pad_span = (
                        _extens_listing_span(base[idx], mark.query) if listing
                        else _related_pad_span(base[idx], mark.query)
                    )
                rebuilt = rebuild_sequence(
                    mark.query, mark.reasoning, mark.response,
                    tokenizer=tokenizer, template=template, fmt=fmt, pad_query_span=pad_span,
                    label_answer=label_answer_tokens,
                )
                _check_answer_labelled(rebuilt, label_answer_tokens)
                if listing and rebuilt.classes[: len(rebuilt.prompt_ids)].count(1) == 0:
                    # A labelled extens job without a class-1 token would read as unpadded.
                    raise ValueError(
                        "the extens listing was located but no token is class 1 after the "
                        "rebuild; not planned unlabelled"
                    )
                if not checked:
                    # Once per model: a wrong delimiter table is wrong for every
                    # mark, so it must stop the model, not fill the error list.
                    check_reasoning_format(model, tokenizer, rebuilt.prompt_text, fmt=fmt)
                    checked = True
                job = attention.mass_job(
                    job_id_for(run, idx), rebuilt.prompt_ids, rebuilt.completion_ids,
                    rebuilt.classes, prefix + f"q{idx}.npz", mode=mode,
                )
            except (ValueError, jinja2.exceptions.TemplateError) as exc:
                if isinstance(exc, ReasoningFormatError):
                    raise
                built.errors.append(f"{run.path}#q{idx}: {exc}")
                continue
            built.planned.append(PlannedJob(job, run, idx, rebuilt.notes))
    return built


def _check_answer_labelled(rebuilt: Rebuilt, label_answer_tokens: bool) -> None:
    """Refuse a rebuild that was asked to label answer tokens and labelled none.

    Raises
    ------
    ValueError
        When `label_answer_tokens` is true and no completion token is class 4: such a job would
        read as one without an answer, so it is a plan error, never an unlabelled job.
    """
    if label_answer_tokens and attention.ANSWER_CLASS not in rebuilt.classes[len(rebuilt.prompt_ids):]:
        raise ValueError("label_answer_tokens: no completion token is class 4 after the rebuild; not planned")


class _HornRowError(ValueError):
    """A selected deduction row cannot be rebuilt faithfully; the message says why."""


def _horn_cell_inputs(
    cell: _HornCell, model: str, rungs_dir: Path
) -> Tuple[str, str, str, Optional[str], str, Dict[str, int]]:
    """Check one selected row against its rendered cell; return what the rebuild needs.

    The checks run in a fixed order, and the first failure is the cell's plan error (each
    message holds the quoted word the caller of this module greps for): (1) ``spec_key`` is
    `model`; (2) the collection added no provider system prompt (``provider_system_prompt``;
    its text is not stored, so the prompt cannot be rebuilt); (3) ``prompt.md`` and
    ``system.md`` exist; (4) the digest of ``prompt.md`` equals the row's ``prompt_sha256``,
    so the rung was not re-rendered since the collection; (5) neither ``content`` nor
    ``reasoning`` is mis-decoded text; (6) ``prompt_tokens`` and ``completion_tokens`` are
    integers. The text of the two files is read as the collection read it
    (``Path.read_text`` with UTF-8); the digest is over the bytes.

    Returns
    -------
    Tuple[str, str, str, Optional[str], str, Dict[str, int]]
        ``(query, system, prompt_sha256, reasoning, content, bedrock_token_counts)``.

    Raises
    ------
    _HornRowError
        With the reason, for each failed check above. (A file that cannot be decoded as
        UTF-8 raises ``UnicodeDecodeError``, also a ``ValueError``.)
    """
    row = cell.row
    if row.get("spec_key") != model:
        raise _HornRowError(f"spec_key {row.get('spec_key')!r} is not {model!r}")
    if row.get("provider_system_prompt"):
        raise _HornRowError(
            "the collection added a provider system prompt (provider_system_prompt is true); "
            "its text is not stored, so the prompt cannot be rebuilt"
        )
    cell_dir = rungs_dir / cell.rung / f"s{cell.seed:04d}" / cell.arm
    paths = {name: cell_dir / name for name in ("prompt.md", "system.md")}
    for name, path in paths.items():
        if not path.is_file():
            raise _HornRowError(f"{name} not found at {path}")
    digest = hashlib.sha256(paths["prompt.md"].read_bytes()).hexdigest()[:16]
    if digest != row.get("prompt_sha256"):
        raise _HornRowError(
            f"prompt_sha256 {row.get('prompt_sha256')!r} of the row is not the digest {digest} of "
            f"{paths['prompt.md']}; the rung was rendered again since the collection"
        )
    text: Dict[str, Optional[str]] = {}
    for name in ("content", "reasoning"):
        value = row.get(name)
        if value is not None and not isinstance(value, str):
            raise _HornRowError(f"{name} is {type(value).__name__}, not text")
        text[name] = value
    bad = [name for name, value in text.items() if looks_misdecoded(value)]
    if bad:
        raise _HornRowError(f"mis-decoded text (UTF-8 read as ISO-8859-1) in {', '.join(bad)}; not planned")
    counts: Dict[str, int] = {}
    for name in ("prompt_tokens", "completion_tokens"):
        value = row.get(name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise _HornRowError(f"{name} {value!r} is not an integer (the usage the collection counted)")
        counts[name] = value
    return (
        paths["prompt.md"].read_text(encoding="utf-8"),
        paths["system.md"].read_text(encoding="utf-8"),
        digest, text["reasoning"], text["content"] or "", counts,
    )


#: The heading line that opens the rule list of a rendered deduction prompt.
_HORN_LIBRARY_HEADING = "## Library"


def _library_lines(text: str, where: Path) -> Tuple[int, List[Tuple[int, str]]]:
    """Return the index of the library heading line and every line of `text` with its offset.

    Lines are split on ``\\n`` only (``str.splitlines`` also splits on U+2028); each entry
    is ``(character offset of the line's first character, line text without the newline)``.

    Raises
    ------
    _HornRowError
        When the heading occurs on no line or on more than one (`where` names the file).
    """
    lines: List[Tuple[int, str]] = []
    offset = 0
    for line in text.split("\n"):
        lines.append((offset, line))
        offset += len(line) + 1
    heads = [i for i, (_o, line) in enumerate(lines) if line == _HORN_LIBRARY_HEADING]
    if len(heads) != 1:
        raise _HornRowError(
            f"{where}: {len(heads)} '{_HORN_LIBRARY_HEADING}' lines, expected exactly one; "
            "the added lines cannot be located"
        )
    return heads[0], lines


def _horn_added_line_spans(
    rungs_dir: Path, rung: str, seed: int, arm: str, query: str, cache: Dict[Tuple[str, int], Any]
) -> List[Tuple[int, int]]:
    """Return the character ranges of the ADDED lines of one deduction prompt (empty for ``lem``).

    Which lines are added comes from the theory, not from the text: ``arm_keys`` of the
    rung's renderer gives the rule keys an arm shows, in line order, and a line is added
    exactly when its key is not a lemma key (a derivation-tree slot, whatever the arm puts
    there: filler, a renamed tree rule, a lemma copy or the real tree rule). Design: the
    theory, not a text comparison with the ``lem`` arm, decides, because the ``rep`` arm
    fills a slot with a copy of a lemma line, so a text alignment would be ambiguous. The
    text is used to CHECK the result: (1) the library heading occurs once in `query` and
    is followed by exactly ``len(shown)`` library lines, a blank line and the next heading;
    (2) the arm's lemma lines (with the ``[lemma]`` tag removed where the arm adds it)
    equal the ``lem`` arm's library lines of the same seed, position by position; (3) the
    number of added lines is the theory's number of tree slots for every arm but ``lem``.

    Each range covers the line and its own terminating newline, ``[line start, line end +
    1)``: the newline after an added line belongs to it, the newline before it to the line
    above. Two consecutive added lines therefore form one contiguous range.

    Parameters
    ----------
    rungs_dir : Path
        The rendered rungs (``<rungs_dir>/<rung>/s<seed:04d>/{theory.json,<arm>/prompt.md}``).
    rung, seed, arm : str, int, str
        The cell.
    query : str
        The cell's ``prompt.md`` text, as the rebuild reads it.
    cache : Dict[Tuple[str, int], Any]
        ``(rung, seed) -> (theory, lem library lines)``, filled on first use, so the replicates
        and arms of one theory read its files once.

    Returns
    -------
    List[Tuple[int, int]]
        Ranges in `query` coordinates, in line order; empty for ``lem``.

    Raises
    ------
    _HornRowError
        When ``theory.json`` or the ``lem`` arm's ``prompt.md`` is missing or unreadable, the
        arm is unknown to the renderer, or any check above fails.
    """
    from smolbench.deduction.horn import render as horn_render
    from smolbench.deduction.horn.theory import Theory

    seed_dir = rungs_dir / rung / f"s{seed:04d}"
    key = (rung, seed)
    if key not in cache:
        theory_path, lem_path = seed_dir / "theory.json", seed_dir / "lem" / "prompt.md"
        for path in (theory_path, lem_path):
            if not path.is_file():
                raise _HornRowError(f"{path.name} not found at {path}; the added lines cannot be located")
        try:
            theory = Theory.from_json(theory_path.read_text(encoding="utf-8"))
        except (ValueError, KeyError, TypeError) as exc:
            raise _HornRowError(f"{theory_path}: cannot read the theory: {type(exc).__name__}: {exc}") from exc
        lem_text = lem_path.read_text(encoding="utf-8")
        head, lines = _library_lines(lem_text, lem_path)
        n_lemmas = len(theory.lemmas())
        if len(lines) <= head + 1 + n_lemmas or lines[head + 1 + n_lemmas][1] != "":
            raise _HornRowError(
                f"{lem_path}: the theory has {n_lemmas} lemmas, but the lem arm's library is not "
                f"{n_lemmas} lines followed by a blank line; the prompt and the theory disagree"
            )
        cache[key] = (theory, [line for _o, line in lines[head + 1:head + 1 + n_lemmas]])
    theory, lem_lines = cache[key]
    try:
        shown, _padded = horn_render.arm_keys(theory, arm)
    except ValueError as exc:
        raise _HornRowError(f"arm {arm!r}: {exc}") from exc
    lemma_keys = {rule.key for rule in theory.lemmas()}

    where = seed_dir / arm / "prompt.md"
    head, lines = _library_lines(query, where)
    first, after = head + 1, head + 1 + len(shown)
    tail = [line for _o, line in lines[after:after + 2]]
    if len(lines) < after + 2 or tail[0] != "" or not tail[1].startswith("## "):
        raise _HornRowError(
            f"{where}: the theory shows {len(shown)} library lines for arm {arm!r}, but line "
            f"{after + 1} of the prompt is not the blank line before the next heading; the "
            "prompt and the theory disagree"
        )
    tag = horn_render.LEMMA_TAG if arm == "marked-lemma" else ""
    kept = [line for (_o, line), k in zip(lines[first:after], shown) if k in lemma_keys]
    stripped = [line[len(tag):] if tag and line.startswith(tag) else line for line in kept]
    if len(stripped) != len(lem_lines) or stripped != lem_lines:
        mismatch = next(
            (i for i, (a, b) in enumerate(zip(stripped, lem_lines)) if a != b), min(len(stripped), len(lem_lines))
        )
        raise _HornRowError(
            f"{where}: {len(stripped)} lemma lines, the lem arm has {len(lem_lines)}; first "
            f"difference at lemma line {mismatch + 1}; the lemma lines are not where the theory "
            "puts them"
        )
    spans = [
        (offset, offset + len(line) + 1)
        for (offset, line), k in zip(lines[first:after], shown) if k not in lemma_keys
    ]
    expected = 0 if arm == "lem" else len(theory.tree_keys())
    if len(spans) != expected:
        raise _HornRowError(
            f"{where}: {len(spans)} added lines, the theory has {expected} tree slots for arm {arm!r}"
        )
    return spans


def _build_horn(
    model: str,
    source: _Source,
    s3_prefix: str,
    get_tokenizer: Callable[[], Any],
    get_template: Callable[[], Any],
    fmt: Optional[ReasoningFormat],
    seeds: Optional[FrozenSet[int]],
    mode: str,
) -> _Built:
    """Read the deduction rows of `model` and rebuild every selected cell (see ``_build``).

    Selection is ``_horn_select``. Each selected row is checked and rebuilt in
    ``_horn_cell_inputs`` order and then through ``rebuild_sequence`` with the cell's system
    turn and an empty pad span (the deduction study has no whitespace pad). With
    ``source.label_added_lines`` the pad is instead the cell's added lines
    (``_horn_added_line_spans``, passed as ``pad_query_spans``; none for ``lem``), and an arm
    other than ``lem`` whose rebuild has no class-1 token is a plan error for that cell, never
    an unlabelled job. With ``source.label_answer_tokens`` the answer tokens are class 4 and a
    cell without one is a plan error. A failure of one cell is a plan error for its arm and the other cells
    still plan; a ``ReasoningFormatError`` stops the model, as for induction. Tokenizer and
    template are fetched only when there is a cell to rebuild.
    """
    import jinja2.exceptions

    if source.rows_path is None:
        raise ValueError("the deduction build needs the rows file")
    rungs_dir = source.rungs_dir if source.rungs_dir is not None else bt.RUNGS_DIR
    sel = _horn_select(source.rows_path, source.arms, seeds, source.reps)
    runs = _horn_runs(model, sel)
    built = _Built(
        runs=list(runs), marks=len(sel.cells), errors=list(sel.errors), arm_order=sel.arm_order,
        exception_rows=dict(sel.exception_rows),
    )
    built.unreasoned = sum(1 for cell in sel.cells if not bt.reasoned(cell.row.get("reasoning")))
    if not sel.cells:
        return built
    tokenizer = get_tokenizer()
    template = get_template()
    if fmt is None:
        if model not in REASONING_FORMATS:
            raise ReasoningFormatError(f"{model}: no entry in REASONING_FORMATS")
        fmt = REASONING_FORMATS[model]

    run_of = {(run.rung, run.arm): run for run in runs}
    checked = False
    theories: Dict[Tuple[str, int], Any] = {}  # (rung, seed) -> theory and lem lines, read once
    for cell in sel.cells:
        run = run_of[(cell.rung, cell.arm)]
        where = (
            f"{sel.rows_path} line {cell.line_index + 1} "
            f"({cell.rung}/{cell.arm} seed {cell.seed} rep {cell.rep})"
        )
        try:
            query, system, digest, reasoning, content, counts = _horn_cell_inputs(cell, model, rungs_dir)
            if source.label_added_lines:
                spans = _horn_added_line_spans(rungs_dir, cell.rung, cell.seed, cell.arm, query, theories)
                rebuilt = rebuild_sequence(
                    query, reasoning, content, tokenizer=tokenizer, template=template, fmt=fmt,
                    system=system, pad_query_spans=spans, label_answer=source.label_answer_tokens,
                )
                n_pad = rebuilt.classes[: len(rebuilt.prompt_ids)].count(1)
                if cell.arm != "lem" and n_pad == 0:
                    # A padded arm that labels nothing would read as an arm without a pad.
                    raise _HornRowError(
                        f"{len(spans)} added lines but no class-1 token after the rebuild; not "
                        "planned unlabelled"
                    )
            else:
                # An empty pad span: the deduction study has no whitespace pad, so no token is
                # class 1 (the default; the stored captures were made this way).
                rebuilt = rebuild_sequence(
                    query, reasoning, content, tokenizer=tokenizer, template=template, fmt=fmt,
                    pad_query_span=(0, 0), system=system, label_answer=source.label_answer_tokens,
                )
            _check_answer_labelled(rebuilt, source.label_answer_tokens)
            if not checked:
                # Once per model, as for induction: a wrong delimiter table is wrong for every cell.
                check_reasoning_format(model, tokenizer, rebuilt.prompt_text, fmt=fmt)
                checked = True
            job = attention.mass_job(
                _horn_job_id(cell.rung, cell.arm, cell.seed, cell.rep), rebuilt.prompt_ids,
                rebuilt.completion_ids, rebuilt.classes,
                run_prefix(s3_prefix, run) + f"s{cell.seed}.rep{cell.rep}.npz", mode=mode,
            )
        except (ValueError, jinja2.exceptions.TemplateError) as exc:
            if isinstance(exc, ReasoningFormatError):
                raise
            message = f"{where}: {exc}"
            built.errors.append(message)
            built.errors_by_arm.setdefault(cell.arm, []).append(message)
            continue
        built.planned.append(PlannedJob(
            job, run, cell.line_index, rebuilt.notes, counts, cell.seed, cell.rep, digest,
        ))
    return built


def _build(
    model: str,
    source: _Source,
    s3_prefix: str,
    get_tokenizer: Callable[[], Any],
    get_template: Callable[[], Any],
    fmt: Optional[ReasoningFormat],
    seeds: Optional[FrozenSet[int]] = None,
    mode: str = "mass",
) -> _Built:
    """Read the stored transcripts of `model` and rebuild every mark or cell (shared by ``build_jobs`` and the plan).

    Dispatches on ``source.study``: ``_build_induction`` or ``_build_horn``. Both fetch the
    tokenizer and template through callables on first need, apply `seeds` before reading
    any content, record `mode` (already resolved) on every job, check the reasoning format
    once and report a per-mark failure as an error instead of a crash.
    """
    if source.study == "horn":
        return _build_horn(model, source, s3_prefix, get_tokenizer, get_template, fmt, seeds, mode)
    return _build_induction(
        model, source.results_root, s3_prefix, get_tokenizer, get_template, fmt, seeds, mode,
        source.label_added_lines, source.label_answer_tokens,
    )


def build_jobs(
    model: str,
    results_root: Path,
    s3_prefix: str,
    *,
    tokenizer: Any = None,
    template: Any = None,
    fmt: Optional[ReasoningFormat] = None,
    mode: Optional[str] = None,
    seeds: Optional[Sequence[int]] = None,
    study: str = "induction",
    horn_rows: Optional[Path] = None,
    rungs_dir: Optional[Path] = None,
    arms: Optional[Sequence[str]] = None,
    reps: Optional[Sequence[int]] = None,
    label_added_lines: bool = False,
    label_answer_tokens: bool = False,
) -> Tuple[List[PlannedJob], List[str]]:
    """Rebuild every stored mark or cell of `model` into a capture job, offline.

    Never builds an S3 or EC2 client. The reasoning format is checked once, on the
    first successfully rendered prompt.

    Parameters
    ----------
    model : str
        Roster key.
    results_root : Path
        Induction: folder holding ``induction/<model>/...`` (see ``find_runs``). Ignored for
        ``study="horn"``.
    s3_prefix : str
        Key prefix above ``induction/`` or ``deduction/`` (no bucket).
    tokenizer : Any, optional
        Defaults to ``tokenization.for_model(model)``.
    template : Any, optional
        Defaults to ``load_chat_template(model)``.
    fmt : ReasoningFormat, optional
        Defaults to ``REASONING_FORMATS[model]``.
    mode : Optional[str], optional
        Capture mode recorded on every job, ``"mass"`` or ``"summary"``; ``None``
        (default) means ``"mass"`` for induction and ``"summary"`` for deduction. Keyword-only.
        The token sequences and classes are identical in both modes.
    seeds : Optional[Sequence[int]], optional
        Only the runs (induction) or cells (deduction) of these seeds; ``None`` (default) is
        every seed, an empty sequence selects nothing.
    study : str, optional
        ``"induction"`` (default) or ``"horn"``.
    horn_rows : Optional[Path], optional
        Deduction: the rows file, or a folder holding ``<model>.jsonl``. Default
        ``bt.horn_rows_path(model)``. A rows file that does not exist is a plan error.
    rungs_dir : Optional[Path], optional
        Deduction: the rendered rungs; default ``bt.RUNGS_DIR``.
    arms, reps : Optional[Sequence], optional
        Deduction: keep only these arms / replicate numbers (``None`` = all).
    label_added_lines : bool, optional
        Label the added lines class 1 (see ``plan_replay``; both studies). Default ``False``:
        the classes the stored captures were made with.
    label_answer_tokens : bool, optional
        Label the answer tokens class 4 (see ``plan_replay``; both studies). Default ``False``.

    Returns
    -------
    Tuple[List[PlannedJob], List[str]]
        The jobs, and one error line per mark or cell that could not be rebuilt (induction:
        ``"<path>#q<idx>: <error>"``; deduction: ``"<rows file> line <n> (<cell>): <error>"``,
        plus one line per torn or unparseable line of the rows file). No mark is dropped
        silently. Induction jobs come in run order then mark order, with
        ``bedrock_token_counts`` ``None`` (the stored marks carry no token counts). Deduction
        jobs come by rung, arm, seed and replicate, with ``bedrock_token_counts`` taken from the
        row. Every job's ``mode`` is the resolved `mode`.

    Raises
    ------
    ValueError
        When `mode` or `study` is invalid, `seeds` or `reps` holds a non-integer, `arms` is
        not a sequence of names, or a deduction-only argument is given for the induction
        study (before any file is read).
    TemplateUnavailable
        When the template or tokenizer cannot be loaded (only when there is something to
        rebuild).
    ReasoningFormatError
        When the delimiters fail validation: every mark would be wrong the same way.
    """
    _check_study(study)
    resolved = _resolve_mode(mode, study)
    source = _make_source(
        study, results_root,
        _horn_rows_file(model, horn_rows) if study == "horn" else horn_rows, rungs_dir, arms, reps,
        label_added_lines, label_answer_tokens,
    )
    built = _build(
        model, source, s3_prefix,
        (lambda: tokenizer) if tokenizer is not None else (lambda: _default_tokenizer(model)),
        (lambda: template) if template is not None else (lambda: load_chat_template(model)),
        fmt, _seed_set(seeds), resolved,
    )
    return built.planned, built.errors


def _default_tokenizer(model: str) -> Any:
    """Return the pinned tokenizer, turning its load failure into ``TemplateUnavailable``."""
    try:
        return tokenization.for_model(model)
    except RuntimeError as exc:
        raise TemplateUnavailable(f"{model}: cannot load the tokenizer: {exc}") from exc


# ------------------------------------------------------------------------- the plan


@dataclass
class ReplayPlan:
    """What replaying one model would do. Built offline; nothing here costs money."""

    model: str
    #: Induction: stored runs found (one per seed and arm). Deduction: ``<rung>/<arm>``
    #: folders with a selected cell.
    runs: int
    #: Induction: marks read from those runs. Deduction: cells selected (planned plus errored).
    marks: int
    #: Marks (induction) or cells (deduction) rebuilt into jobs.
    jobs: int
    #: Marks or cells with no stored reasoning.
    unreasoned_marks: int
    #: Per-mark, per-cell and per-model rebuild failures; for deduction also the torn,
    #: unparseable and missing rows-file errors.
    errors: List[str]
    #: Per arm: ``marks`` (rebuilt), ``total_tokens``, ``max_tokens`` and
    #: ``over_context`` (jobs above the capture context, so excluded from the capture).
    #: Per arm because exclusions that differ by arm would bias a mean over responses.
    #: Deduction adds, per arm: ``errors`` (plan errors of the arm's cells), ``exception_rows``
    #: (rows with no generation, never selected), ``prompt_tokens`` (rebuilt prompt lengths
    #: summed over the planned jobs), ``bedrock_prompt_tokens`` and ``bedrock_completion_tokens``
    #: (the rows' own counts summed over the planned jobs) and ``est_capture_bytes`` (the
    #: arm's share of ``ReplayPlan.est_capture_bytes``, ``None`` when that is unknown).
    per_arm: Dict[str, Dict[str, Any]]
    #: Tokens over all rebuilt jobs, prompt plus completion.
    total_tokens: int
    #: Longest rebuilt sequence.
    max_tokens: int
    #: Jobs longer than the spec's ``max_model_len``; they cannot be captured.
    over_context: int
    instance_types: Tuple[str, ...]
    #: Tensor-parallel degree on the first instance type, or ``None`` when none is listed.
    tp_estimate: Optional[int]
    capture_supported: bool
    unsupported_reason: Optional[str]
    #: False when the model is listed in ``SERVE_UNVERIFIED``.
    serve_verified: bool
    serve_unverified_reason: Optional[str]
    #: Context length of the capture serve; jobs above it are ``over_context``.
    capture_max_model_len: int
    #: Estimated bytes of captured arrays (capturable jobs only), or ``None``.
    est_capture_bytes: Optional[int]
    #: Formula, config source and caveats; always starts with ``"ESTIMATE:"``.
    est_basis: str
    bedrock_token_counts: str = _BEDROCK_COUNTS_NOTE
    approximations: List[str] = field(default_factory=lambda: list(APPROXIMATIONS))
    #: Capture mode the plan sizes (an element of ``MODES``); it sets the storage estimate.
    mode: str = "mass"
    #: The study planned: ``"induction"`` or ``"horn"``.
    study: str = "induction"
    #: With a ``job_ids`` allow-list: one dict per selected job, in plan order, ``{"job_id":
    #: str, "n_tokens": int, "over_context": bool}`` (``over_context`` against
    #: ``capture_max_model_len``). ``None`` without an allow-list. With one, every count of
    #: the plan (``jobs``, ``per_arm``, the token totals, ``over_context`` and the storage
    #: estimate) covers only these jobs; ``runs``, ``marks`` and ``errors`` stay as built.
    selected: Optional[List[Dict[str, Any]]] = None
    #: Whether the added lines are labelled class 1 (deduction: the padded arms' added lines;
    #: induction: the ``extens`` listing). When true, ``per_arm`` also holds ``class1_tokens``
    #: (class-1 tokens summed over the arm's planned jobs) and ``class1_tokens_mean`` (per job;
    #: 0.0 for an arm without jobs), for every arm of either study.
    label_added_lines: bool = False
    #: Whether the answer tokens are labelled class 4. When true, ``per_arm`` also holds
    #: ``class4_tokens`` (summed over the arm's planned jobs) and ``class4_tokens_mean``.
    label_answer_tokens: bool = False

    def summary(self) -> str:
        """Return a short multi-line description of the plan.

        Returns
        -------
        str
            Counts, token sizes, the capture mode, capture support, instance types and
            the labelled storage estimate. With a ``job_ids`` allow-list, also the line
            ``  selected jobs (N):`` and one line per selected job (id, token count, and a
            note when it is over the capture context). With ``label_added_lines``, a line
            saying the added lines are class 1, and per arm the class-1 tokens (total and
            mean per job).
        """
        horn = self.study == "horn"
        lines = [
            f"{self.model}: " + (
                f"deduction (horn), {self.runs} rung/arm folders, {self.marks} cells -> {self.jobs} jobs "
                f"({self.unreasoned_marks} cells without stored reasoning)"
                if horn else
                f"{self.runs} runs, {self.marks} marks -> {self.jobs} jobs "
                f"({self.unreasoned_marks} marks without stored reasoning)"
            ) + f", {len(self.errors)} errors",
            f"  capture mode: {self.mode}",
            f"  tokens: total {self.total_tokens}, longest {self.max_tokens}; "
            f"{self.over_context} job(s) over the {self.capture_max_model_len}-token capture "
            "context (excluded)",
        ]
        if self.label_added_lines:
            lines.append(
                "  label_added_lines: the added lines of every padded arm are class 1 "
                "(lem has none); the pad ratio is defined for those arms"
                if horn else
                "  label_added_lines: the extens listing is class 1 (intens, noise_intens and "
                "related_intens keep their classes); the pad ratio is defined for extens"
            )
        if self.label_answer_tokens:
            lines.append(
                "  label_answer_tokens: the completion tokens of the stored response (after the "
                "reasoning) are class 4"
            )
        for arm, stats in self.per_arm.items():
            line = (
                f"  arm {arm}: {stats['marks']} jobs, {stats['total_tokens']} tokens, "
                f"longest {stats['max_tokens']}, {stats['over_context']} over the "
                f"{self.capture_max_model_len}-token capture context"
            )
            if horn:
                line += (
                    f"; {stats['errors']} error(s), {stats['exception_rows']} exception row(s); "
                    f"prompt tokens {stats['prompt_tokens']} rebuilt vs {stats['bedrock_prompt_tokens']} "
                    f"counted by the service, completion tokens {stats['bedrock_completion_tokens']} "
                    "counted by the service"
                )
            if "class1_tokens" in stats:
                line += (
                    f"; class-1 tokens {stats['class1_tokens']} total, "
                    f"{stats['class1_tokens_mean']:.1f} per job"
                )
            if "class4_tokens" in stats:
                line += (
                    f"; class-4 tokens {stats['class4_tokens']} total, "
                    f"{stats['class4_tokens_mean']:.1f} per job"
                )
            lines.append(line)
        if self.selected is not None:
            lines.append(f"  selected jobs ({len(self.selected)}):")
            for item in self.selected:
                lines.append(
                    f"    {item['job_id']}: {item['n_tokens']} tokens"
                    + (
                        f", over the {self.capture_max_model_len}-token capture context (excluded)"
                        if item["over_context"] else ""
                    )
                )
        if self.capture_supported:
            lines.append("  capture: supported")
        else:
            lines.append(f"  capture: NOT SUPPORTED: {self.unsupported_reason}")
        if self.serve_verified:
            lines.append("  serving: no known blocker")
        else:
            lines.append(f"  serving: UNVERIFIED: {self.serve_unverified_reason}")
        lines.append(
            f"  instance types: {', '.join(self.instance_types) or 'none'}; "
            f"tp estimate: {self.tp_estimate}"
        )
        size = "unknown" if self.est_capture_bytes is None else f"{self.est_capture_bytes / 1e9:.2f} GB"
        lines.append(f"  storage {size}; {self.est_basis}")
        lines.append(f"  bedrock_token_counts: {self.bedrock_token_counts}")
        return "\n".join(lines)


def _estimate_bytes(
    planned: Sequence[PlannedJob],
    config: Optional[Mapping[str, Any]],
    tp: Optional[int],
    source: str,
    mode: str = "mass",
) -> Tuple[Optional[int], str]:
    """Return ``(estimated capture bytes, est_basis)`` for the capturable `planned` jobs.

    Mass mode: per job, summed over ranks, ``layers x P x heads x 7 x 2`` bytes plus
    ``tp x n_tokens`` (``P = n_tokens - query_start``). Summary mode: ``layers x heads x
    26 x 8`` bytes plus ``tp x n_tokens``; it has no ``P`` term, which is the point of
    the mode. The ``7 = 4 + 1 + 1 + 1`` and ``26`` count the stored values per
    (layer, head) (see ``_SUMMARY_VALUES_PER_HEAD``). The estimate ignores the small
    geometry arrays, the meta json and S3 overhead.
    """
    if mode == "summary":
        formula = (
            "ESTIMATE: summary mode, per job, summed over ranks, n_attn_layers x n_heads x 26 "
            "eight-byte values (float64 sums and int64 counts: sum_entropy, sum_prompt_entropy, "
            "n_prompt_entropy, sum_mass x 4, sum_sink, sum_pad_ratio, n_pad_ratio, sum_m_hp, "
            "sum_chain_hi, sum_chain_lo, sum_prompt_entropy_by_class x 3, sum_prompt_entropy_answer, "
            "n_prompt_entropy_answer, sum_prompt_entropy_by_class_answer x 3, sum_entropy_answer, "
            "sum_mass_answer x 4) x 8 bytes + tp x n_tokens (uint8 classes per rank); "
            "independent of the number of response rows; uncompressed npz, without the meta "
            "json and S3 overhead"
        )
    else:
        formula = (
            "ESTIMATE: per job, summed over ranks, n_attn_layers x P x n_heads x (4 mass + 1 entropy "
            "+ 1 prompt_entropy + 1 sink) x 2 bytes (float16) + tp x n_tokens (uint8 classes per rank), with "
            "P = n_tokens - query_start; uncompressed npz, without the meta json and S3 overhead"
        )
    if config is None:
        return None, f"{formula}; not computed: {source}"
    if tp is None:
        return None, f"{formula}; not computed: no instance type to derive tp from"
    try:
        layers, heads = attention_shape(config)
    except ValueError as exc:
        return None, f"{formula}; not computed: {exc} (config from {source})"
    total = sum(_job_capture_bytes(item.job, layers, heads, tp, mode) for item in planned)
    return total, f"{formula}; layers={layers}, heads={heads}, tp={tp}; config: {source}"


def _job_capture_bytes(job: attention.Job, layers: int, heads: int, tp: int, mode: str) -> int:
    """Return the estimated captured bytes of one job (the term ``_estimate_bytes`` sums).

    Kept apart so that the per-arm estimates of a deduction plan are sums of the same terms
    and add up to the plan's total exactly.
    """
    if mode == "summary":
        return layers * heads * _SUMMARY_VALUES_PER_HEAD * 8 + tp * job.n_tokens
    queries = job.n_tokens - int(job.query_start)  # type: ignore[arg-type]
    return layers * queries * heads * (4 + 1 + 1 + 1) * 2 + tp * job.n_tokens


def _resolve_capture_len(model: str, spec: Mapping[str, Any], override: Optional[int]) -> int:
    """Return the context length a capture of `model` serves with and is planned against.

    Parameters
    ----------
    model : str
        Roster key.
    spec : Mapping[str, Any]
        The model's deploy spec (``max_model_len`` is the ceiling of an override).
    override : Optional[int]
        The ``capture_max_model_len`` keyword of an entry point, or ``None``.

    Returns
    -------
    int
        `override` when given, else ``capture_max_model_len(model, spec)``.

    Raises
    ------
    ValueError
        When `override` is not an integer (a bool is refused) with ``0 < value <=
        spec["max_model_len"]``. The message names ``capture_max_model_len``.

    Notes
    -----
    A module function called ``capture_max_model_len`` exists, and the keyword of the entry
    points has the same name and shadows it in their bodies; this helper is the one place
    that reaches the function from there.
    """
    if override is None:
        return capture_max_model_len(model, spec)
    ceiling = int(spec["max_model_len"])
    if isinstance(override, bool) or not isinstance(override, numbers.Integral) or not 0 < override <= ceiling:
        raise ValueError(
            f"capture_max_model_len must be an integer with 0 < value <= {ceiling} (the max_model_len "
            f"of the {model} deploy spec), got {override!r}"
        )
    return int(override)


def _job_id_set(job_ids: Optional[Sequence[str]]) -> Optional[FrozenSet[str]]:
    """Validate the ``job_ids`` allow-list and return it as a set (``None`` = no filter).

    Parameters
    ----------
    job_ids : Optional[Sequence[str]]
        ``None`` (no filter), or a non-string sequence (or set) of job id strings.

    Returns
    -------
    Optional[FrozenSet[str]]
        ``None`` for no filter, else the ids with duplicates collapsed.

    Raises
    ------
    ValueError
        When `job_ids` is a single string or bytes, is not a sequence or set, holds a
        non-string, or is empty. The message names ``job_ids``.

    Notes
    -----
    Design: an empty allow-list is refused instead of meaning "nothing". A filter that selects
    nothing is a mistake, and fill mode (``replay_model(fill=True)``) must never act on a
    vague selection: an empty list silently read as "no filter" would re-send everything.
    """
    if job_ids is None:
        return None
    if isinstance(job_ids, (str, bytes)) or not isinstance(job_ids, (Sequence, set, frozenset)):
        raise ValueError(f"job_ids must be a sequence of job id strings or None, got {job_ids!r}")
    ids = list(job_ids)
    if not ids:
        raise ValueError(
            "job_ids is empty: an allow-list that selects nothing is a mistake (pass None for "
            "no filter)"
        )
    bad = [item for item in ids if not isinstance(item, str)]
    if bad:
        raise ValueError(f"job_ids must hold strings only, got {bad[0]!r}")
    return frozenset(ids)


def serve_settings(
    *,
    spec: Mapping[str, Any],
    capture_max_model_len: int,
    fill: bool = False,
    gate_tol: Optional[float] = None,
    execute_model_timeout_s: Optional[int] = None,
    gpu_memory_utilization: Optional[float] = None,
) -> Dict[str, Any]:
    """Validate the capture serve's settings and return the EFFECTIVE values.

    ``replay_model`` calls this before anything else is touched, so a bad value stops the
    run before a box is billed, and records the result in every manifest it writes and on the
    report. A setting left at ``None`` is replaced by the value the serve would use.

    Parameters
    ----------
    spec : Mapping[str, Any]
        The model's deploy spec. Only ``vllm_args`` is read, for the spec's
        ``--gpu-memory-utilization`` (the value after that flag).
    capture_max_model_len : int
        The resolved capture context (see ``_resolve_capture_len``). Reported as
        ``max_model_len`` unchanged; not validated here.
    fill : bool, optional
        Fill mode. Must be exactly a ``bool`` (``1`` is refused).
    gate_tol : Optional[float], optional
        Self-consistency tolerance the plugin declares in each rank's meta. A finite real
        number with ``0 < gate_tol <= MAX_GATE_TOL`` (a ``bool`` is refused). ``None`` means
        ``PLUGIN_DEFAULT_GATE_TOL``.
    execute_model_timeout_s : Optional[int], optional
        Engine step timeout in seconds. An ``int`` (not a ``bool``) of at least
        ``ec2.MIN_CAPTURE_EXECUTE_TIMEOUT_S``. ``None`` means
        ``ec2.DEFAULT_CAPTURE_EXECUTE_TIMEOUT_S``.
    gpu_memory_utilization : Optional[float], optional
        Share of GPU memory vLLM may take. A finite real number in the open interval (0, 1)
        (a ``bool`` is refused). ``None`` means the spec's share, or ``None`` when the spec
        has no ``--gpu-memory-utilization`` flag.

    Returns
    -------
    Dict[str, Any]
        ``{"execute_model_timeout_s": int, "gate_tol": float, "fill": bool,
        "gpu_memory_utilization": Optional[float], "max_model_len": int}``. JSON-serialisable.

    Raises
    ------
    ValueError
        When a setting is invalid, as listed above. The message names the parameter.

    Examples
    --------
    >>> spec = {"vllm_args": ["--gpu-memory-utilization", "0.9"]}
    >>> serve_settings(spec=spec, capture_max_model_len=4096)["gate_tol"]
    0.03
    >>> serve_settings(spec=spec, capture_max_model_len=4096)["gpu_memory_utilization"]
    0.9
    >>> serve_settings(spec=spec, capture_max_model_len=4096, gate_tol=0.06)
    Traceback (most recent call last):
        ...
    ValueError: gate_tol must be a finite number with 0 < gate_tol <= 0.05, got 0.06
    """
    from smolbench.evals.providers import ec2

    # Phase 1: validate each setting on its own, naming it in the message.
    if fill is not True and fill is not False:
        raise ValueError(f"fill must be a bool, got {fill!r}")
    if gate_tol is not None:
        if (
            isinstance(gate_tol, bool) or not isinstance(gate_tol, numbers.Real)
            or not math.isfinite(gate_tol) or not 0 < gate_tol <= MAX_GATE_TOL
        ):
            raise ValueError(
                f"gate_tol must be a finite number with 0 < gate_tol <= {MAX_GATE_TOL}, got {gate_tol!r}"
            )
    if execute_model_timeout_s is not None:
        if (
            isinstance(execute_model_timeout_s, bool) or not isinstance(execute_model_timeout_s, numbers.Integral)
            or execute_model_timeout_s < ec2.MIN_CAPTURE_EXECUTE_TIMEOUT_S
        ):
            raise ValueError(
                f"execute_model_timeout_s must be an int >= {ec2.MIN_CAPTURE_EXECUTE_TIMEOUT_S}, "
                f"got {execute_model_timeout_s!r}"
            )
    if gpu_memory_utilization is not None:
        if (
            isinstance(gpu_memory_utilization, bool) or not isinstance(gpu_memory_utilization, numbers.Real)
            or not math.isfinite(gpu_memory_utilization) or not 0 < gpu_memory_utilization < 1
        ):
            raise ValueError(
                f"gpu_memory_utilization must be a finite number with 0 < value < 1, got {gpu_memory_utilization!r}"
            )

    # Phase 2: replace each unset setting with the value the serve would use.
    if gpu_memory_utilization is None:
        args = list(spec.get("vllm_args") or ())
        flag = "--gpu-memory-utilization"
        share: Optional[float] = float(args[args.index(flag) + 1]) if flag in args else None
    else:
        share = float(gpu_memory_utilization)
    return {
        "execute_model_timeout_s": (
            ec2.DEFAULT_CAPTURE_EXECUTE_TIMEOUT_S if execute_model_timeout_s is None
            else int(execute_model_timeout_s)
        ),
        "gate_tol": PLUGIN_DEFAULT_GATE_TOL if gate_tol is None else float(gate_tol),
        "fill": fill,
        "gpu_memory_utilization": share,
        "max_model_len": int(capture_max_model_len),
    }


def _usage_total(items: Sequence[PlannedJob], name: str) -> int:
    """Return the sum of the service's ``bedrock_token_counts[name]`` over deduction `items`."""
    return sum((item.bedrock_token_counts or {}).get(name, 0) for item in items)


def _plan_one(
    model: str,
    source: _Source,
    s3_prefix: str,
    tokenizer_for: Optional[Callable[[str], Any]],
    template_for: Optional[Callable[[str], Any]],
    config_for: Optional[Callable[[str], Mapping[str, Any]]],
    seeds: Optional[Sequence[int]] = None,
    mode: Optional[str] = None,
    capture_len: Optional[int] = None,
    job_ids: Optional[Sequence[str]] = None,
) -> Tuple[ReplayPlan, List[PlannedJob]]:
    """Build one model's plan and its planned jobs (no AWS access).

    `seeds` restricts the plan to the runs or cells of those seeds (``None`` = every seed), so
    every count, token total and the storage estimate cover only them. `mode` is the
    capture mode (``None`` means the study's default, see ``_resolve_mode``): it is set on
    every job, recorded on the plan and selects the storage formula. `capture_len` replaces the
    capture context of the model (``_resolve_capture_len``). `job_ids` is an allow-list of job
    ids (``None`` = no filter): after the jobs are built only those are kept, so every count
    derived from the planned jobs (``jobs``, ``per_arm``, the storage estimate, the token
    totals, ``over_context``) covers the selection, and ``ReplayPlan.selected`` lists it.
    ``runs``, ``marks`` and ``errors`` stay as built.

    Raises
    ------
    ValueError
        When `mode` is not ``None`` or one of ``MODES``, `seeds` holds a non-integer,
        `capture_len` is not valid for the model's spec, `job_ids` is invalid (see
        ``_job_id_set``), or `job_ids` names an id that is not among the built jobs. The
        message lists every such id, sorted, and no id that was found.
    """
    resolved = _resolve_mode(mode, source.study)
    from smolbench.evals.providers import ec2

    horn = source.study == "horn"
    wanted = _seed_set(seeds)
    wanted_ids = _job_id_set(job_ids)
    spec = ec2.EC2_DEPLOY_SPECS[model]
    max_len = _resolve_capture_len(model, spec, capture_len)
    get_tokenizer = (lambda: tokenizer_for(model)) if tokenizer_for else (lambda: _default_tokenizer(model))
    get_template = (lambda: template_for(model)) if template_for else (lambda: load_chat_template(model))
    try:
        built = _build(model, source, s3_prefix, get_tokenizer, get_template, None, wanted, resolved)
    except (TemplateUnavailable, ReasoningFormatError) as exc:
        # One model's missing template must not stop the other models' plans. The marks are
        # not counted, but the runs (induction) or folders and exception rows (deduction) are.
        message = f"{model}: {exc} (marks not counted)"
        if horn:
            sel = _horn_select(source.rows_path, source.arms, wanted, source.reps)  # type: ignore[arg-type]
            built = _Built(
                runs=list(_horn_runs(model, sel)), errors=[message], arm_order=sel.arm_order,
                exception_rows=dict(sel.exception_rows),
            )
        else:
            built = _Built(
                runs=[r for r in find_runs(source.results_root, model) if wanted is None or r.seed in wanted],
                errors=[message],
            )

    # The allow-list applies AFTER the build, to the jobs that exist: an id that was excluded by
    # another filter, never existed or failed to rebuild is an error, because a recapture of
    # the wrong job is worse than none. Design: filter the built list, not the sources, so the
    # job ids are the ones every other entry point derives and the filters compose.
    all_planned = built.planned
    selected: Optional[List[Dict[str, Any]]] = None
    if wanted_ids is not None:
        built_ids = {p.job.job_id for p in all_planned}
        unknown = sorted(wanted_ids - built_ids)
        if unknown:
            first_error = f" First plan error: {built.errors[0]}" if built.errors else ""
            raise ValueError(
                f"{model}: job_ids names {len(unknown)} job(s) that are unknown, excluded by the "
                f"seeds/arms/reps filters, or failed to rebuild: {', '.join(unknown)}.{first_error}"
            )
        all_planned = [p for p in all_planned if p.job.job_id in wanted_ids]
        selected = [
            {"job_id": p.job.job_id, "n_tokens": p.job.n_tokens, "over_context": p.job.n_tokens > max_len}
            for p in all_planned
        ]

    capturable = [p for p in all_planned if p.job.n_tokens <= max_len]
    per_arm: Dict[str, Dict[str, Any]] = {}
    arms = built.arm_order if horn else list(ARMS)
    for arm in arms:
        jobs_of_arm = [p for p in all_planned if p.run.arm == arm]
        sizes = [p.job.n_tokens for p in jobs_of_arm]
        per_arm[arm] = {
            "marks": len(sizes), "total_tokens": sum(sizes), "max_tokens": max(sizes, default=0),
            "over_context": sum(1 for size in sizes if size > max_len),
        }
        if horn:
            per_arm[arm].update({
                "errors": len(built.errors_by_arm.get(arm, [])),
                "exception_rows": built.exception_rows.get(arm, 0),
                "prompt_tokens": sum(int(p.job.query_start) for p in jobs_of_arm),  # type: ignore[arg-type]
                "bedrock_prompt_tokens": _usage_total(jobs_of_arm, "prompt_tokens"),
                "bedrock_completion_tokens": _usage_total(jobs_of_arm, "completion_tokens"),
                "est_capture_bytes": None,  # filled below once the total is known
            })
        if source.label_added_lines:
            # Only with the labels (both studies): the per-arm dict of a default plan keeps its keys.
            pad_counts = [(p.job.classes or ()).count(1) for p in jobs_of_arm]
            per_arm[arm]["class1_tokens"] = sum(pad_counts)
            per_arm[arm]["class1_tokens_mean"] = (
                sum(pad_counts) / len(pad_counts) if pad_counts else 0.0
            )
        if source.label_answer_tokens:
            answer_counts = [(p.job.classes or ()).count(attention.ANSWER_CLASS) for p in jobs_of_arm]
            per_arm[arm]["class4_tokens"] = sum(answer_counts)
            per_arm[arm]["class4_tokens_mean"] = (
                sum(answer_counts) / len(answer_counts) if answer_counts else 0.0
            )

    instance_types = tuple(INSTANCE_TYPES.get(model, ()))
    tp = ec2.derive_tp(model, instance_types[0], spec) if instance_types else None
    config: Optional[Mapping[str, Any]]
    try:
        if config_for is not None:
            config, source_text = config_for(model), "injected config"
        else:
            config, source_text = _load_model_config_with_source(model)
    except (TemplateUnavailable, OSError, ValueError) as exc:
        config, source_text = None, f"config unavailable: {exc}"
    est_bytes, est_basis = _estimate_bytes(capturable, config, tp, source_text, resolved)
    if horn and est_bytes is not None and config is not None and tp is not None:
        # Per arm, the same terms the total sums: the arm values add up to the total exactly.
        layers, heads = attention_shape(config)  # succeeded inside _estimate_bytes
        for arm, arm_stats in per_arm.items():
            arm_stats["est_capture_bytes"] = sum(
                _job_capture_bytes(p.job, layers, heads, tp, resolved) for p in capturable if p.run.arm == arm
            )

    sizes_all = [p.job.n_tokens for p in all_planned]
    plan = ReplayPlan(
        model=model,
        runs=len(built.runs),
        marks=built.marks,
        jobs=len(all_planned),
        unreasoned_marks=built.unreasoned,
        errors=list(built.errors),
        per_arm=per_arm,
        total_tokens=sum(sizes_all),
        max_tokens=max(sizes_all, default=0),
        over_context=len(all_planned) - len(capturable),
        instance_types=instance_types,
        tp_estimate=tp,
        capture_supported=model not in CAPTURE_UNSUPPORTED,
        unsupported_reason=CAPTURE_UNSUPPORTED.get(model),
        serve_verified=model not in SERVE_UNVERIFIED,
        serve_unverified_reason=SERVE_UNVERIFIED.get(model),
        capture_max_model_len=max_len,
        est_capture_bytes=est_bytes,
        est_basis=est_basis,
        mode=resolved,
        study=source.study,
        bedrock_token_counts=_HORN_BEDROCK_COUNTS_NOTE if horn else _BEDROCK_COUNTS_NOTE,
        selected=selected,
        label_added_lines=source.label_added_lines,
        label_answer_tokens=source.label_answer_tokens,
    )
    return plan, all_planned


def plan_replay(
    results_root: Path = DEFAULT_RESULTS_ROOT,
    models: Optional[Sequence[str]] = None,
    *,
    s3_uri: str = DEFAULT_S3_URI,
    tokenizer_for: Optional[Callable[[str], Any]] = None,
    template_for: Optional[Callable[[str], Any]] = None,
    config_for: Optional[Callable[[str], Mapping[str, Any]]] = None,
    seeds: Optional[Sequence[int]] = None,
    mode: Optional[str] = None,
    study: str = "induction",
    horn_rows: Union[Path, Mapping[str, Path], None] = None,
    rungs_dir: Optional[Path] = None,
    arms: Optional[Sequence[str]] = None,
    reps: Optional[Sequence[int]] = None,
    capture_max_model_len: Optional[int] = None,
    job_ids: Optional[Sequence[str]] = None,
    label_added_lines: bool = False,
    label_answer_tokens: bool = False,
) -> Dict[str, ReplayPlan]:
    """Plan the replay of each model: sizes, errors and a storage estimate. No AWS access.

    Parameters
    ----------
    results_root : Path, optional
        Induction: folder holding ``induction/<model>/...`` (see ``find_runs``). Ignored for
        ``study="horn"``.
    models : Sequence[str], optional
        Roster keys; defaults to the three keys of ``bedrock_trio.TRIO``.
    s3_uri : str, optional
        Destination URI; only its key prefix is used, to name the jobs.
    tokenizer_for, template_for, config_for : Callable, optional
        ``model -> object`` overrides of the pinned tokenizer, chat template and
        ``config.json`` (tests and offline use).
    seeds : Sequence[int], optional
        Plan only the runs (induction) or cells (deduction) of these seeds; every count,
        token total, per-arm number and the storage estimate then cover only them. ``None``
        (default) plans every seed. An empty sequence selects nothing, so every plan has zero
        marks.
    mode : Optional[str], optional
        Capture mode to plan, ``"mass"`` or ``"summary"``; ``None`` (default) means ``"mass"``
        for induction and ``"summary"`` for deduction. Keyword-only. It sets every job's mode,
        ``ReplayPlan.mode`` and the storage estimate (summary storage does not grow with the
        response length). Either mode can be planned for either study.
    study : str, optional
        ``"induction"`` (default) or ``"horn"``. Keyword-only.
    horn_rows : Union[Path, Mapping[str, Path], None], optional
        Deduction only. ``None`` (default): ``bt.horn_rows_path(model)`` for each model. A
        folder: ``<folder>/<model>.jsonl`` for each model. A file: that file, for ONE model
        (refused for several). A mapping: the entry of each model (a model without an entry is
        refused).
    rungs_dir : Optional[Path], optional
        Deduction only: the rendered rungs; default ``bt.RUNGS_DIR``.
    arms, reps : Optional[Sequence], optional
        Deduction only: keep only these arms (their order orders ``per_arm``) / replicate
        numbers. ``None`` keeps all.
    capture_max_model_len : Optional[int], optional
        Plan against this capture context instead of ``capture_max_model_len(model, spec)``
        (both studies): an integer with ``0 < value <= spec["max_model_len"]``. It decides
        which jobs are over-context and is reported as ``ReplayPlan.capture_max_model_len``.
    job_ids : Optional[Sequence[str]], optional
        Allow-list of job ids (both studies); ``None`` (default) keeps every job. Only the
        listed jobs are planned: every count, token total, per-arm number and the storage
        estimate cover them, and ``ReplayPlan.selected`` lists them (see ``ReplayPlan``).
        Duplicates collapse. One list cannot name the jobs of several models, so it is
        accepted for ONE model only.
    label_added_lines : bool, optional
        Both studies. Default ``False``: the classes the stored captures were made with (no
        deduction token is class 1; induction ``extens`` labelled by rule). ``True``, deduction:
        the added lines of every padded arm (each derivation-tree slot of the rendered library,
        whatever the arm fills it with) are class 1, located from the rung's ``theory.json``
        and checked against the ``lem`` arm (``_horn_added_line_spans``); ``lem`` has no
        class-1 token. ``True``, induction: the ``extens`` listing is class 1, located from the
        ``intens`` query of the same seed and question (``_extens_listing_span``); the other
        arms keep their classes. A cell or mark whose added lines cannot be located, or a
        labelled one with no class-1 token after the rebuild, is a plan error. The plan records
        the flag and counts the class-1 tokens per arm (``ReplayPlan.label_added_lines``). The
        job keys do not depend on the flag: capture under a new ``s3_uri`` prefix, since a
        stored job is never re-sent.
    label_answer_tokens : bool, optional
        Both studies. Default ``False``: every completion token is class 3. ``True``: the
        completion tokens that come from the stored response or content (after the reasoning
        block and its closing delimiter, as ``rebuild_sequence`` assembles the completion; the
        appended end-of-turn token included) are class 4, the answer class; reasoning tokens and
        the thinking delimiters stay class 3, and a mark or cell with no stored reasoning has
        every completion token class 4. A job with no class-4 token is a plan error. The plan
        records the flag and counts the class-4 tokens per arm (``ReplayPlan.label_answer_tokens``);
        the job keys do not depend on it, so capture under a new ``s3_uri``.

    Returns
    -------
    Dict[str, ReplayPlan]
        One plan per model. A model with no result files (or no rows file) gets a plan with
        zero marks. A ``TemplateUnavailable`` or ``ReasoningFormatError`` for one model
        is recorded in that plan's ``errors`` (with ``jobs == 0``), so the other
        models still plan. For deduction, ``per_arm`` is keyed by arm (see
        ``ReplayPlan.per_arm``) and ``runs`` counts ``<rung>/<arm>`` folders.

    Raises
    ------
    ValueError
        When `s3_uri` is malformed, `seeds` or `reps` holds a non-integer, `mode` or `study` is
        invalid, `capture_max_model_len` is not valid for a model's spec, `horn_rows` does not fit
        the models (see above), or a deduction-only argument is given for the induction study.
        Also when `job_ids` is invalid (empty, or not a sequence of strings), is given with more
        than one model, or names a job that is not among the model's built jobs (unknown,
        excluded by `seeds`, `arms` or `reps`, or failed to rebuild; the message lists them).
    KeyError
        When a model has no deploy spec.
    """
    _bucket, prefix = parse_s3_uri(s3_uri)
    _check_study(study)
    model_list = list(models) if models is not None else list(bt.TRIO)
    if _job_id_set(job_ids) is not None and len(model_list) > 1:
        raise ValueError(
            f"job_ids selects the jobs of one model, but {len(model_list)} models were given: "
            "plan each model with its own list"
        )
    # Every source is built before any model is planned, so a bad argument fails the call whole.
    sources = {
        model: _make_source(
            study, Path(results_root),
            _horn_rows_file(model, horn_rows, len(model_list)) if study == "horn" else horn_rows,
            rungs_dir, arms, reps, label_added_lines, label_answer_tokens,
        )
        for model in model_list
    }
    resolved = _resolve_mode(mode, study)
    return {
        model: _plan_one(
            model, sources[model], prefix, tokenizer_for, template_for, config_for, seeds, resolved,
            capture_max_model_len, job_ids,
        )[0]
        for model in model_list
    }


# --------------------------------------------------------------- audit and manifest


def _check_workers(workers: Any, name: str) -> None:
    """Raise ``ValueError`` unless `workers` is an integer of at least 1 (``True`` is refused)."""
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ValueError(f"{name} must be an integer >= 1, got {workers!r}")


def _object_size(client: Any, bucket: str, key: str) -> int:
    """Return an object's size: ``head_object`` when the client has it, else the listing's ``Size``."""
    head = getattr(client, "head_object", None)
    if callable(head):
        return int(head(Bucket=bucket, Key=key)["ContentLength"])
    listing = client.list_objects_v2(Bucket=bucket, Prefix=key)
    for obj in listing.get("Contents") or []:
        if obj["Key"] == key:
            return int(obj["Size"])
    raise FileNotFoundError(f"s3://{bucket}/{key} is not listed")


def _first_index(mask: np.ndarray) -> Tuple[int, int, int]:
    """Return the ``(layer, row, head)`` of the first True entry of a 3-d boolean `mask`."""
    layer, row, head = (int(i) for i in np.argwhere(mask)[0])
    return layer, row, head


def _audit_prompt_entropy(
    arrays: Any, job: attention.Job, entropy: np.ndarray, mass: np.ndarray, n_layers: int
) -> Optional[str]:
    """Content-check the ``prompt_entropy`` array of a version-2 rank; return a failure or ``None``.

    Runs only after every version-1 check passed, so `entropy` and `mass` have the
    shapes ``_audit_arrays`` verified. See ``audit_captures`` for the rules.
    """
    if "prompt_entropy" not in arrays:
        return "capture_version 2 npz has no prompt_entropy"
    pe16 = np.asarray(arrays["prompt_entropy"])
    if pe16.shape != entropy.shape:
        return f"prompt_entropy shape {pe16.shape} differs from entropy {entropy.shape}"
    if "sliding_window" not in arrays:
        return "capture_version 2 npz has no sliding_window (needed to place the NaNs of prompt_entropy)"
    window = np.asarray(arrays["sliding_window"])
    if window.shape != (n_layers,):
        return f"sliding_window shape {window.shape} is not ({n_layers},)"

    # Compare in float64 on the stored float16 values, as the other entropy checks do.
    pe = pe16.astype(np.float64)
    finite = np.isfinite(pe)
    query_start = int(job.query_start)  # type: ignore[arg-type]

    # Phase 1: range of the values. NaN is legitimate here, so it is judged in phase 2.
    # Comparisons with NaN are False, so a NaN never trips these masks.
    infinite = np.isinf(pe)
    if infinite.any():
        l, i, h = _first_index(infinite)
        return f"prompt_entropy holds inf at (layer {l}, row {i}, head {h})"
    below = pe < _ENTROPY_FLOOR
    if below.any():
        l, i, h = _first_index(below)
        return (
            f"prompt_entropy {float(pe[l, i, h]):.4g} at (layer {l}, row {i}, head {h}) "
            f"is below {_ENTROPY_FLOOR}"
        )
    # The renormalised distribution lives on the prompt keys a row can attend, with the
    # sink excluded: at most query_start, and on a windowed layer (window w, row i) at
    # most min(query_start, w - 1 - i). ln of that count bounds it; the slack is the
    # float16 spacing, as for the whole-row entropy. With query_start == 0 there is no
    # prompt key and no ceiling: every finite value is then rejected by phase 2. Rows past
    # a window hold no prompt key at all; their count is floored at 1 here (ceiling 0 plus
    # slack) so that phase 2, not this check, reports a finite value there.
    rows = np.arange(mass.shape[1], dtype=np.int64)[None, :]
    win = window.astype(np.int64)[:, None]
    if query_start > 0:
        count = np.where(win > 0, np.minimum(query_start, win - 1 - rows), query_start)
        count = np.maximum(count, 1)  # [L, P]
        ceiling3 = np.broadcast_to(
            (np.log(count.astype(np.float64)) + _ENTROPY_CEIL_TOL)[:, :, None], pe.shape
        )
        above = pe > ceiling3
        if above.any():
            l, i, h = _first_index(above)
            return (
                f"prompt_entropy {float(pe[l, i, h]):.4g} at (layer {l}, row {i}, head {h}) "
                f"is above the ceiling ln(attendable prompt keys) + {_ENTROPY_CEIL_TOL} = "
                f"{float(ceiling3[l, i, h]):.4g} (window {int(window[l])}, query_start {query_start})"
            )

    # Phase 2: NaN placement. A row can see a prompt key unless the layer is windowed
    # and the row has moved past the window (row i is at absolute position
    # query_start + i, and a window w admits keys j >= pos - (w - 1), i.e. a prompt key
    # iff i < w - 1), or there is no prompt at all.
    no_prompt = ((win > 0) & (rows >= win - 1)) | (query_start == 0)  # [L, P]
    no_prompt3 = np.broadcast_to(no_prompt[:, :, None], pe.shape)
    # Masked keys get -inf logits, so softmax gives them EXACTLY 0 and the one-hot class
    # reduction sums exact zeros: where no prompt key is attendable the stored prompt
    # mass is exactly 0, and that is what makes a NaN there trustworthy. The converse is
    # NOT required: a finite value with stored prompt mass 0 is accepted, because a peaked
    # row's tiny prompt mass underflows float16 (below about 6e-8) while the entropy
    # renormalised on the prompt keys is still defined. This rule encodes the plugin's
    # masks (causal plus sliding window); a layer type that masks prompt keys some other
    # way needs its geometry stored in the npz, or its NaNs are rejected here.
    stray = finite & no_prompt3
    if stray.any():
        l, i, h = _first_index(stray)
        return (
            f"prompt_entropy {float(pe[l, i, h]):.4g} at (layer {l}, row {i}, head {h}) is "
            f"finite, but no prompt key is attendable there (window {int(window[l])}, "
            f"query_start {query_start})"
        )
    prompt_mass = np.asarray(mass)[..., :3].astype(np.float64).sum(-1)  # [L, P, H]
    bad_nan = np.isnan(pe) & ~(no_prompt3 & (prompt_mass == 0.0))
    if bad_nan.any():
        l, i, h = _first_index(bad_nan)
        return (
            f"prompt_entropy is NaN at (layer {l}, row {i}, head {h}) with prompt mass "
            f"{float(prompt_mass[l, i, h]):.3g}; NaN is valid only where no prompt key is "
            "attendable and the stored prompt mass is 0"
        )

    # Phase 3: cross-check against the other stored arrays (grouping rule of entropy).
    # Group the row's keys into prompt (mass m), response so far (mass r) and sink (mass
    # s). With G = -(m ln m + r ln r + s ln s) the entropy of the three-group split,
    #     H = G + m * Hp + r * Hr,  0 <= Hr <= ln(attendable response keys) <= ln(i + 1),
    # where Hr is the (unstored) entropy of the renormalised response part and the sink
    # group is a single key. Solving for m * Hp gives an interval, checked on every cell
    # where Hp is finite. Design: an interval (not an equality) because Hr is not stored;
    # it still refuses halved, shuffled and constant arrays. It cannot catch a wrong Hp on
    # rows where the interval is wide: late rows with a large response mass r, where
    # r * ln(i + 1) is large. The whole-row entropy copied in as Hp is caught only when
    # r is large: with a small r, H is close to Hp and the copy stays inside the tolerance.
    return _check_prompt_entropy_chain(pe, np.asarray(mass), np.asarray(arrays["sink"]), entropy)


def _check_prompt_entropy_chain(
    pe: np.ndarray, mass: np.ndarray, sink: np.ndarray, entropy: np.ndarray
) -> Optional[str]:
    """Return a failure when ``m * Hp`` leaves its grouping-rule interval, else ``None``.

    `pe` is the float64 ``prompt_entropy`` (NaN allowed); `mass`, `sink` and `entropy` are
    the stored float16 arrays of the same ``[L, P, H]`` leading shape. Cells with a NaN
    `pe` are skipped. The interval and the tolerance are described in
    ``_audit_prompt_entropy``; the failure names the first offending
    ``(layer, row, head)`` (lowest layer, then row, then head), the side and the numbers.
    """
    m64 = mass[..., :3].astype(np.float64).sum(-1)
    r64 = mass[..., 3].astype(np.float64)
    s64 = sink.astype(np.float64)
    h64 = entropy.astype(np.float64)

    def plogp(p: np.ndarray) -> np.ndarray:
        # A zero probability contributes exactly 0 (the limit of p ln p); the inner
        # where() only keeps the log away from 0, the outer one picks the 0 branch.
        return np.where(p > 0.0, p * np.log(np.where(p > 0.0, p, 1.0)), 0.0)

    group = -(plogp(m64) + plogp(r64) + plogp(s64))
    # Row i holds at most i + 1 response keys, itself included.
    ln_resp = np.log(np.arange(1, mass.shape[1] + 1, dtype=np.float64))[None, :, None]
    tol = _PE_CHAIN_ABS_TOL + _PE_CHAIN_REL_TOL * (1.0 + h64)
    m_hp = m64 * pe  # NaN where pe is NaN, so those cells never trip a mask below
    upper = h64 - group + tol
    lower = h64 - group - r64 * ln_resp - tol
    for side, bad, bound in (
        ("above", m_hp > upper, upper),
        ("below", m_hp < lower, lower),
    ):
        if bad.any():
            l, i, h = _first_index(bad)
            return (
                f"prompt_entropy fails the chain-rule cross-check at (layer {l}, row {i}, head "
                f"{h}): m * prompt_entropy = {float(m_hp[l, i, h]):.4g} is {side} the bound "
                f"{float(bound[l, i, h]):.4g} derived from entropy {float(h64[l, i, h]):.4g}, "
                f"mass {float(m64[l, i, h]):.4g} (prompt) / {float(r64[l, i, h]):.4g} "
                f"(response) / {float(s64[l, i, h]):.4g} (sink)"
            )
    return None


def _audit_arrays(
    arrays: Any,
    job: attention.Job,
    n_layers: int,
    heads_local: int,
    capture_version: int = 1,
) -> Tuple[Optional[str], Optional[Tuple[int, ...]]]:
    """Content-check one rank's arrays; return ``(failure or None, mass.shape[:2])``.

    `n_layers` and `heads_local` are the config's attention layer count and its
    heads per tensor-parallel rank; the entropy ceiling is derived in
    ``audit_captures``. `capture_version` is the rank's meta version: for 2 or
    more, the ``prompt_entropy`` checks run after all the version-1 checks pass;
    version 1 is audited exactly as before.
    """
    classes = np.asarray(arrays["classes"])
    if not np.array_equal(classes, np.asarray(job.classes)):
        return "classes differ from the job's", None
    mass = arrays["mass"]
    expected_p = job.n_tokens - int(job.query_start)  # type: ignore[arg-type]
    if mass.ndim != 4 or mass.shape[1] != expected_p or mass.shape[3] != attention.N_TOKEN_CLASSES:
        return f"mass shape {mass.shape} is not (L, {expected_p}, H_local, {attention.N_TOKEN_CLASSES})", None
    if mass.shape[0] != n_layers or mass.shape[2] != heads_local:
        return (
            f"mass shape {mass.shape} has {mass.shape[0]} layers and {mass.shape[2]} local heads, "
            f"the config gives {n_layers} layers and {heads_local} local heads",
            None,
        )
    entropy, sink = arrays["entropy"], arrays["sink"]
    if entropy.shape != mass.shape[:3] or sink.shape != mass.shape[:3]:
        return f"entropy {entropy.shape} / sink {sink.shape} differ from mass[:3] {mass.shape[:3]}", None
    if "layers" in getattr(arrays, "files", ()) and len(arrays["layers"]) != mass.shape[0]:
        return f"{len(arrays['layers'])} layer ids for {mass.shape[0]} mass layers", None
    mass32, entropy32, sink32 = (np.asarray(a, dtype=np.float32) for a in (mass, entropy, sink))
    if not (np.isfinite(mass32).all() and np.isfinite(entropy32).all() and np.isfinite(sink32).all()):
        return "non-finite values in mass, entropy or sink", None
    # Probabilities are non-negative: the row-sum check alone passes [1.5, -0.5, 0, 0].
    # Cast to float64 so the comparison sees the stored float16 values unrounded further.
    for name, values in (("mass", mass), ("sink", sink)):
        low = float(np.asarray(values, dtype=np.float64).min()) if values.size else 0.0
        if low < _MASS_FLOOR:
            return f"{name} minimum {low:.4g} is below {_MASS_FLOOR}", None
    worst = float(np.abs(mass32.sum(-1) + sink32 - 1.0).max()) if mass32.size else 0.0
    if worst > _ROW_SUM_TOL:
        return f"mass.sum(-1) + sink deviates from 1 by {worst:.4g} (> {_ROW_SUM_TOL})", None
    if entropy32.size and float(entropy32.min()) < _ENTROPY_FLOOR:
        return f"entropy minimum {float(entropy32.min()):.4g} is below {_ENTROPY_FLOOR}", None

    # Entropy ceiling: completion row i sits at absolute position query_start + i
    # and attends at most that many keys plus itself, plus one sink column on the
    # layers that have one; the box computes entropy over exactly those columns,
    # so it cannot exceed ln(count). Sliding windows only shrink the support, so
    # ignoring them keeps the bound valid. Without a has_sink array the looser
    # bound (a sink on every layer) is used.
    if "has_sink" in getattr(arrays, "files", ()):
        has_sink = np.asarray(arrays["has_sink"], dtype=bool)
        if has_sink.shape != (n_layers,):
            return f"has_sink shape {has_sink.shape} is not ({n_layers},)", None
        sink_cols = has_sink.astype(np.int64)
    else:
        sink_cols = np.ones(n_layers, dtype=np.int64)
    attended = (
        int(job.query_start)  # type: ignore[arg-type]
        + np.arange(expected_p, dtype=np.int64)[None, :]
        + 1
        + sink_cols[:, None]
    )
    ceiling = (np.log(attended.astype(np.float64)) + _ENTROPY_CEIL_TOL)[:, :, None]
    excess = entropy32.astype(np.float64) - ceiling
    if excess.size and float(excess.max()) > 0.0:
        layer, row, head = (int(i) for i in np.unravel_index(int(excess.argmax()), excess.shape))
        return (
            f"entropy {float(entropy32[layer, row, head]):.4g} at (layer {layer}, row {row}, "
            f"head {head}) exceeds the ceiling ln(attended keys) + {_ENTROPY_CEIL_TOL} = "
            f"{float(ceiling[layer, row, 0]):.4g}",
            None,
        )
    if capture_version >= 2:
        failure = _audit_prompt_entropy(arrays, job, entropy, mass, n_layers)
        if failure:
            return failure, None
    return None, tuple(mass.shape[:2])


#: Names of the ``[L, H_local]`` arrays of a summary npz (everything in
#: ``attention.SUMMARY_ARRAYS`` except the scalar ``rows`` and the class-axis ``sum_mass``),
#: in the order the audit checks them.
_SUMMARY_HEAD_ARRAYS: Tuple[str, ...] = tuple(
    name for name in attention.SUMMARY_ARRAYS if name not in ("rows", "sum_mass")
)


def _first_cell(mask: np.ndarray) -> Tuple[int, ...]:
    """Return the index (lowest first, in C order) of the first True entry of a non-empty `mask`."""
    return tuple(int(i) for i in np.argwhere(mask)[0])


def _audit_summary_arrays(
    arrays: Any, job: attention.Job, n_layers: int, heads_local: int, capture_version: int = 3
) -> Optional[str]:
    """Content-check one rank's summary npz against the job and the config; return a failure or ``None``.

    The summary holds sums over the ``P = n_tokens - query_start`` response rows, so
    every check here compares a sum or a count with what the geometry of the job
    allows: the audit of the per-row mass arrays, summed over rows. ``audit_captures``
    lists the rules. The checks run in a fixed order and the first failure is
    returned; each failure names the offending npz array and, where it applies, the
    first offending ``(layer, head)`` (lowest layer, then head).

    Parameters
    ----------
    arrays : Any
        The rank's loaded npz (``np.load`` result or a dict of arrays).
    job : attention.Job
        The job the rank captured; its ``classes`` and ``query_start`` are the reference.
    n_layers : int
        Attention layer count of the config.
    heads_local : int
        Heads per tensor-parallel rank (``n_heads // tp``).
    capture_version : int, optional
        The rank's meta version, 3 (default) or 4. Version 4 must also hold
        ``attention.SUMMARY_BY_CLASS_ARRAY`` and pass its checks (shape, finite, non-negative,
        0 where no row is defined, and the identity with ``sum_prompt_entropy``); version 3 is
        audited exactly as before, whatever else the npz holds.

    Returns
    -------
    Optional[str]
        The failure reason, or ``None`` when every check passes.

    Notes
    -----
    Pure; memory is a few float64 copies of ``[L, H_local]`` arrays (no row axis).
    """
    query_start = int(job.query_start)  # type: ignore[arg-type]
    p = job.n_tokens - query_start

    # Phase 1: identity and presence. Classes first: a rank that captured another
    # sequence fails here, before any number is compared with this job's geometry.
    if "classes" not in arrays:
        return "summary npz has no classes"
    classes = np.asarray(arrays["classes"])
    if not np.array_equal(classes, np.asarray(job.classes)):
        return "classes differ from the job's"
    by_class = attention.SUMMARY_BY_CLASS_ARRAY
    v4 = capture_version >= 4
    v4_names = (*attention.SUMMARY_V4_ARRAYS, "rows_answer") if v4 else ()
    required = (*attention.SUMMARY_ARRAYS, "sliding_window", "has_sink") + v4_names
    for name in required:
        if name not in arrays:
            return f"summary npz has no {name}" + (
                f" (capture_version {capture_version})" if name in v4_names else ""
            )
    stored = {name: np.asarray(arrays[name]) for name in required}
    rows = stored["rows"]
    if rows.shape != () or int(rows) != p:
        return f"rows {rows.tolist()!r} != P = {p} (n_tokens {job.n_tokens} - query_start {query_start})"

    # Phase 2: shapes, then finiteness. Later phases index these arrays together, so a
    # wrong shape or a NaN must stop the audit here with its own name.
    head_shape = (n_layers, heads_local)
    expected_shapes: Dict[str, Tuple[int, ...]] = {name: head_shape for name in _SUMMARY_HEAD_ARRAYS}
    expected_shapes["sum_mass"] = head_shape + (attention.N_TOKEN_CLASSES,)
    if v4:
        for name, tail in attention.SUMMARY_V4_ARRAYS.items():
            expected_shapes[name] = head_shape + tail
        expected_shapes["rows_answer"] = ()
    expected_shapes["sliding_window"] = (n_layers,)
    expected_shapes["has_sink"] = (n_layers,)
    for name, shape in expected_shapes.items():
        if stored[name].shape != shape:
            return f"{name} shape {stored[name].shape} is not {shape}"
    if "layers" in arrays:
        layers_ids = np.asarray(arrays["layers"])
        if layers_ids.ndim != 1 or len(layers_ids) != n_layers:
            return f"layers has shape {layers_ids.shape}, expected ({n_layers},)"
    value_names = (*_SUMMARY_HEAD_ARRAYS, "sum_mass") + (tuple(attention.SUMMARY_V4_ARRAYS) if v4 else ())
    for name in value_names:
        finite = np.isfinite(stored[name].astype(np.float64))
        if not finite.all():
            cell = _first_cell(~finite)
            return f"{name} holds a non-finite value at {_cell_text(cell)}"

    values = {name: stored[name].astype(np.float64) for name in value_names}
    window = stored["sliding_window"].astype(np.int64)
    has_sink = stored["has_sink"].astype(bool)
    n_pe = stored["n_prompt_entropy"]
    n_pad = stored["n_pad_ratio"]

    # Phase 3: exact counts. They are integers fixed by the geometry, so equality is
    # the right test and no tolerance enters. Row i is at absolute position
    # query_start + i; a window w admits keys j >= pos - (w - 1), so a row sees a prompt
    # key (j < query_start) iff i < w - 1.
    if query_start == 0:
        expected_pe = np.zeros(n_layers, dtype=np.int64)
    else:
        expected_pe = np.where(window > 0, np.minimum(p, np.maximum(window - 1, 0)), p).astype(np.int64)
    wrong = n_pe != expected_pe[:, None]
    if wrong.any():
        cell = _first_cell(wrong)
        return (
            f"n_prompt_entropy {n_pe[cell].item()} at {_cell_text(cell)} != "
            f"{int(expected_pe[cell[0]])} given by the geometry (window {int(window[cell[0]])}, "
            f"query_start {query_start}, P {p})"
        )
    # The pad ratio is defined on a row once its causal prefix holds a class-1 token, which
    # holds for every row from the first pad token on (the prefix only grows).
    pad_positions = np.flatnonzero(classes == 1)
    expected_pad = 0 if pad_positions.size == 0 else p - min(max(int(pad_positions[0]) - query_start, 0), p)
    wrong = n_pad != expected_pad
    if wrong.any():
        cell = _first_cell(wrong)
        return (
            f"n_pad_ratio {n_pad[cell].item()} at {_cell_text(cell)} != {expected_pad}, the number "
            f"of rows whose causal prefix holds a pad token"
        )

    # Phase 4: floors. A sum of per-row quantities each at least the per-row floor is at
    # least the floor times the row count; the per-row floors are the mass audit's.
    n_pe_f = n_pe.astype(np.float64)
    for name, low in (
        ("sum_mass", _MASS_FLOOR * p),
        ("sum_sink", _MASS_FLOOR * p),
        ("sum_entropy", _ENTROPY_FLOOR * p),
        ("sum_prompt_entropy", _ENTROPY_FLOOR * n_pe_f),
    ):
        bound_array = np.broadcast_to(low, values[name].shape)
        below = values[name] < bound_array
        if below.any():
            cell = _first_cell(below)
            bound = float(bound_array[cell])
            return f"{name} {float(values[name][cell]):.4g} at {_cell_text(cell)} is below {bound:.4g}"
    if v4:
        # No floor below 0: every per-row class contribution is -sum p ln p over keys with
        # 0 < p <= 1, a sum of terms that are each >= 0 in float32 too, and float64 sums of
        # non-negative values stay non-negative. A negative value is not rounding.
        for name in (by_class, "sum_prompt_entropy_by_class_answer"):
            negative = values[name] < 0.0
            if negative.any():
                cell = _first_cell(negative)
                return f"{name} {float(values[name][cell]):.4g} at {_cell_text(cell)} is negative"

    # Phase 5: sums that must be exactly 0 where no row has a prompt entropy.
    undefined = n_pe == 0
    for name in ("sum_prompt_entropy", "sum_m_hp", "sum_chain_hi", "sum_chain_lo"):
        stray = undefined & (values[name] != 0.0)
        if stray.any():
            cell = _first_cell(stray)
            return (
                f"{name} {float(values[name][cell]):.4g} at {_cell_text(cell)} is not 0 although "
                "n_prompt_entropy is 0 there"
            )
    if v4:
        stray = undefined[..., None] & (values[by_class] != 0.0)
        if stray.any():
            cell = _first_cell(stray)
            return (
                f"{by_class} {float(values[by_class][cell]):.4g} at {_cell_text(cell)} is not 0 "
                "although n_prompt_entropy is 0 there"
            )
        # Phase 5b: the class split adds up to the prompt entropy. Per row Hp_0 + Hp_1 + Hp_2
        # = Hp exactly; the stored sums differ only by float32 summation order (and TF32, if
        # enabled), so the tolerance is relative to sum_prompt_entropy plus a tiny absolute part
        # per defined row (see _BY_CLASS_IDENTITY_RTOL).
        split_total = values[by_class].sum(-1)
        allowed = (
            _BY_CLASS_IDENTITY_RTOL * np.abs(values["sum_prompt_entropy"])
            + _BY_CLASS_IDENTITY_ATOL_PER_ROW * n_pe_f
        )
        off = np.abs(split_total - values["sum_prompt_entropy"]) > allowed
        if off.any():
            cell = _first_cell(off)
            return (
                f"{by_class} sums to {float(split_total[cell]):.8g} at {_cell_text(cell)}, but "
                f"sum_prompt_entropy is {float(values['sum_prompt_entropy'][cell]):.8g} (allowed "
                f"difference {float(allowed[cell]):.3g}: {_BY_CLASS_IDENTITY_RTOL} relative + "
                f"{_BY_CLASS_IDENTITY_ATOL_PER_ROW} per defined row)"
            )
        failure = _audit_answer_sums(values, stored, classes, query_start, p, expected_pe, n_pe)
        if failure:
            return failure

    # Phase 6: the masses of a row sum to 1 with the sink, so the sums add up to P.
    # Tolerance: the mass audit allows _ROW_SUM_TOL per row, and the sum over P rows of a
    # per-row deviation of at most _ROW_SUM_TOL is at most _ROW_SUM_TOL * P. The summed
    # rows are float32 (accumulation error near 1e-6 per row), but the per-class reduction
    # on the GPU is a matmul that may run in TF32 (relative error about 2**-11, like
    # float16 storage), so the same per-row allowance as the mass audit is kept.
    deviation = np.abs(values["sum_mass"].sum(-1) + values["sum_sink"] - p)
    too_far = deviation > _ROW_SUM_TOL * p
    if too_far.any():
        cell = _first_cell(too_far)
        total = float(values["sum_mass"][cell].sum() + values["sum_sink"][cell])
        return (
            f"sum_mass.sum(-1) + sum_sink = {total:.6g} at {_cell_text(cell)} deviates from "
            f"P = {p} by {float(deviation[cell]):.4g} (> {_ROW_SUM_TOL} x P = {_ROW_SUM_TOL * p:.4g})"
        )

    # Phase 7: mean-entropy ceilings. The per-row ceiling of the mass audit, ln(attended
    # keys) + slack, is averaged over the rows exactly, so a mean over rows can never
    # exceed the mean of the row ceilings. The slack is the float16-era slack, far above
    # the float32 accumulation error of the sums (about log2(T) * 2**-24 * H, roughly 1e-5
    # nats).
    # Whole-row entropy: row i attends at most query_start + i + 1 keys plus the sink column.
    # Design: only two distinct row-ceiling vectors exist (sink column or not), so the mean is
    # taken twice, not once per layer, which keeps memory at O(P) for responses of 100k+ rows.
    attended = query_start + np.arange(p, dtype=np.float64) + 1.0
    mean_ln = np.array([np.log(attended).mean(), np.log(attended + 1.0).mean()])
    ceiling = mean_ln[has_sink.astype(np.int64)] + _ENTROPY_CEIL_TOL  # [L]
    mean_entropy = values["sum_entropy"] / p
    above = mean_entropy > ceiling[:, None]
    if above.any():
        cell = _first_cell(above)
        return (
            f"sum_entropy {float(values['sum_entropy'][cell]):.6g} at {_cell_text(cell)} gives a mean "
            f"entropy {float(mean_entropy[cell]):.4g} per row above the mean ceiling "
            f"ln(attended keys) + {_ENTROPY_CEIL_TOL} = {float(ceiling[cell[0]]):.4g}"
        )
    # Prompt entropy: over the n defined rows the distribution lives on count_i prompt keys,
    # query_start on a global layer and min(query_start, w - 1 - i) on a window w layer
    # (defined rows are i < w - 1, and there w - 1 - i >= 1).
    for layer in range(n_layers):
        n = int(expected_pe[layer])
        if n == 0:
            continue
        if window[layer] > 0:
            counts = np.minimum(query_start, window[layer] - 1 - np.arange(n, dtype=np.int64))
            log_sum = float(np.log(counts.astype(np.float64)).sum())
        else:
            log_sum = n * float(np.log(query_start))
        layer_ceiling = log_sum / n + _ENTROPY_CEIL_TOL
        mean_prompt = values["sum_prompt_entropy"][layer] / n
        over = mean_prompt > layer_ceiling
        if over.any():
            cell = (layer, int(np.argmax(over)))
            return (
                f"sum_prompt_entropy {float(values['sum_prompt_entropy'][cell]):.6g} at "
                f"{_cell_text(cell)} gives a mean {float(mean_prompt[cell[1]]):.4g} over its {n} "
                f"defined rows above the mean ceiling ln(attendable prompt keys) + "
                f"{_ENTROPY_CEIL_TOL} = {layer_ceiling:.4g} (window {int(window[layer])}, "
                f"query_start {query_start})"
            )

    # Phase 8: chain rule. The mass audit requires, per row where the prompt entropy Hp is
    # finite, H - G - r ln(i + 1) - tol_i <= m * Hp <= H - G + tol_i with
    # tol_i = abs + rel * (1 + H_i). Summed over the n defined rows the three middle
    # terms are sum_chain_lo, sum_m_hp and sum_chain_hi, and the tolerances add to
    # n * (abs + rel) + rel * (sum of H over the defined rows). The entropies are
    # non-negative, so that sum is at most sum_entropy (over all rows), which gives the
    # bound used here. The same TF32 argument as in phase 6 applies: the per-class
    # reduction behind m, r and s may run in TF32, so the per-row tolerance of the mass
    # audit is kept, not tightened to float32 accumulation error. sum_entropy is clamped
    # at 0 so a legitimately tiny negative float rounding cannot shrink the tolerance
    # below 0 (it would then fail the comparison on a cell where all three sums are 0).
    tolerance = n_pe_f * (_PE_CHAIN_ABS_TOL + _PE_CHAIN_REL_TOL) + _PE_CHAIN_REL_TOL * np.maximum(
        values["sum_entropy"], 0.0
    )
    m_hp, chain_hi, chain_lo = values["sum_m_hp"], values["sum_chain_hi"], values["sum_chain_lo"]
    for side, bad, array, bound in (
        ("above", m_hp > chain_hi + tolerance, "sum_chain_hi", chain_hi + tolerance),
        ("below", m_hp < chain_lo - tolerance, "sum_chain_lo", chain_lo - tolerance),
    ):
        if bad.any():
            cell = _first_cell(bad)
            return (
                f"sum_m_hp fails the chain-rule cross-check at {_cell_text(cell)}: "
                f"sum_m_hp = {float(m_hp[cell]):.6g} is {side} the bound {float(bound[cell]):.6g} "
                f"derived from {array} {float(values[array][cell]):.6g} with tolerance "
                f"{float(tolerance[cell]):.4g} (n_prompt_entropy {int(n_pe[cell])})"
            )
    return None


def _audit_answer_sums(
    values: Mapping[str, np.ndarray],
    stored: Mapping[str, np.ndarray],
    classes: np.ndarray,
    query_start: int,
    p: int,
    expected_pe: np.ndarray,
    n_pe: np.ndarray,
) -> Optional[str]:
    """Check the version-4 sums over the answer rows (phase 5c of ``_audit_summary_arrays``).

    The answer rows are the response rows whose own token is class 4. In this order:
    ``rows_answer`` equals their number in ``classes``; ``n_prompt_entropy_answer`` is exact
    (the answer rows among the first ``expected_pe[l]`` rows, the rows with an attendable prompt
    key; so also ``<= n_prompt_entropy``); floors (``sum_prompt_entropy_answer`` at least
    ``-1e-3 * n_prompt_entropy_answer``, ``sum_entropy_answer`` and ``sum_mass_answer`` at least
    ``-1e-3 * rows_answer``); where ``n_prompt_entropy_answer == 0`` the prompt-entropy answer
    sums are exactly 0, and with ``rows_answer == 0`` every answer sum is; every answer sum is at
    most its all-rows counterpart (``1e-9`` relative slack: each is the sum of a subset of the
    counterpart's non-negative terms in the same order, so it cannot exceed it beyond rounding);
    and ``sum_prompt_entropy_by_class_answer.sum(-1)`` equals ``sum_prompt_entropy_answer`` within
    the tolerance of the all-rows identity.

    Returns
    -------
    Optional[str]
        The first failure, naming the array and the cell, or ``None``.
    """
    answer_idx = np.flatnonzero(np.asarray(classes)[query_start:query_start + p] == attention.ANSWER_CLASS)
    rows_answer = int(stored["rows_answer"])
    if rows_answer != answer_idx.size:
        return f"rows_answer {rows_answer} != {answer_idx.size}, the class-4 response rows of classes"
    n_ans = np.asarray(stored["n_prompt_entropy_answer"])
    # Defined rows are a prefix of the response rows (rows i < expected_pe[l]).
    expected_ans = np.searchsorted(answer_idx, expected_pe).astype(np.int64)  # [L]
    wrong = n_ans != expected_ans[:, None]
    if wrong.any():
        cell = _first_cell(wrong)
        return (
            f"n_prompt_entropy_answer {n_ans[cell].item()} at {_cell_text(cell)} != "
            f"{int(expected_ans[cell[0]])}, the answer rows with an attendable prompt key"
        )
    n_ans_f = n_ans.astype(np.float64)
    for name, low in (
        ("sum_prompt_entropy_answer", _ENTROPY_FLOOR * n_ans_f),
        ("sum_entropy_answer", _ENTROPY_FLOOR * rows_answer),
        ("sum_mass_answer", _MASS_FLOOR * rows_answer),
    ):
        bound_array = np.broadcast_to(low, values[name].shape)  # [L, H] or a scalar
        below = values[name] < bound_array
        if below.any():
            cell = _first_cell(below)
            return f"{name} {float(values[name][cell]):.4g} at {_cell_text(cell)} is below {float(bound_array[cell]):.4g}"
    no_rows = n_ans == 0
    for name in ("sum_prompt_entropy_answer", "sum_prompt_entropy_by_class_answer"):
        mask = no_rows if values[name].ndim == 2 else no_rows[..., None]
        stray = mask & (values[name] != 0.0)
        if stray.any():
            cell = _first_cell(stray)
            return (
                f"{name} {float(values[name][cell]):.4g} at {_cell_text(cell)} is not 0 although "
                "n_prompt_entropy_answer is 0 there"
            )
    if rows_answer == 0:
        for name in ("sum_entropy_answer", "sum_mass_answer"):
            if (values[name] != 0.0).any():
                cell = _first_cell(values[name] != 0.0)
                return f"{name} {float(values[name][cell]):.4g} at {_cell_text(cell)} is not 0 although rows_answer is 0"
    for name, whole in (
        ("sum_prompt_entropy_answer", "sum_prompt_entropy"),
        ("sum_prompt_entropy_by_class_answer", attention.SUMMARY_BY_CLASS_ARRAY),
        ("sum_entropy_answer", "sum_entropy"),
        ("sum_mass_answer", "sum_mass"),
    ):
        over = values[name] > values[whole] + 1e-9 * np.maximum(np.abs(values[whole]), 1.0)
        if over.any():
            cell = _first_cell(over)
            return (
                f"{name} {float(values[name][cell]):.8g} at {_cell_text(cell)} exceeds its all-rows "
                f"counterpart {whole} {float(values[whole][cell]):.8g}"
            )
    split_total = values["sum_prompt_entropy_by_class_answer"].sum(-1)
    allowed = (
        _BY_CLASS_IDENTITY_RTOL * np.abs(values["sum_prompt_entropy_answer"])
        + _BY_CLASS_IDENTITY_ATOL_PER_ROW * n_ans_f
    )
    off = np.abs(split_total - values["sum_prompt_entropy_answer"]) > allowed
    if off.any():
        cell = _first_cell(off)
        return (
            f"sum_prompt_entropy_by_class_answer sums to {float(split_total[cell]):.8g} at "
            f"{_cell_text(cell)}, but sum_prompt_entropy_answer is "
            f"{float(values['sum_prompt_entropy_answer'][cell]):.8g} (allowed difference "
            f"{float(allowed[cell]):.3g})"
        )
    return None


def _cell_text(cell: Sequence[int]) -> str:
    """Return ``(layer l, head h[, class c])`` for an index into a summary array."""
    text = f"(layer {cell[0]}, head {cell[1]}"
    return text + (f", class {cell[2]})" if len(cell) > 2 else ")")


def _audit_job(
    client: Any,
    bucket: str,
    job: attention.Job,
    tp: int,
    sampled: bool,
    model: str,
    n_layers: int,
    n_heads: int,
    capture_version: Optional[int] = None,
    mode: Optional[str] = None,
) -> Optional[str]:
    """Audit every rank of one job; return the first failure reason, or ``None``.

    Meta checks run in a fixed order (see ``audit_captures``); the first failing
    check of the first failing rank is the reason. A missing meta key is reported
    as a mismatch against ``None``, not as a crash. A failing meta check returns at
    once; an array failure is held until every rank's arrays have been read. With
    `mode` ``None`` each rank is audited by its own meta mode (``mass`` or
    ``summary``); otherwise every rank's meta mode must equal `mode`. The ranks of
    one job must agree on the mode. A rank's ``gate_tol`` above ``MAX_GATE_TOL`` is refused
    (the message names ``rank <r>``, ``gate_tol`` and the cap). A rank whose meta has
    ``"npz_put": "existing"`` skips the npz size comparison only.
    """
    if n_heads % tp != 0:
        return f"config has {n_heads} heads, not divisible by tp={tp}; local heads are undefined"
    heads_local = n_heads // tp
    expected_p = job.n_tokens - int(job.query_start)  # type: ignore[arg-type]
    shapes = set()
    array_failure: Optional[str] = None
    # Digest of each rank's mass bytes, for the duplicate-rank check below.
    digests: Dict[bytes, int] = {}
    duplicate: Optional[str] = None
    job_mode: Optional[str] = None
    for rank in range(tp):
        npz_key, meta_key = attention.rank_keys(job.key, rank)
        meta = json.loads(client.get_object(Bucket=bucket, Key=meta_key)["Body"].read().decode())
        if meta.get("job_id") != job.job_id:
            return f"rank {rank}: meta job_id {meta.get('job_id')!r} != job's {job.job_id!r}"
        if meta.get("rank") != rank:
            return f"rank {rank}: meta rank {meta.get('rank')!r} != {rank}"
        if meta.get("tp") != tp:
            return f"rank {rank}: meta tp {meta.get('tp')!r} != {tp}"
        if meta.get("model") != model:
            return f"rank {rank}: meta model {meta.get('model')!r} != {model!r}"
        if int(meta["n_tokens"]) != job.n_tokens:
            return f"rank {rank}: meta n_tokens {meta['n_tokens']} != job's {job.n_tokens}"
        rank_mode = meta.get("mode")
        if mode is not None:
            if rank_mode != mode:
                return f"rank {rank}: meta mode {rank_mode!r} is not {mode!r}"
        elif rank_mode not in MODES:
            return f"rank {rank}: meta mode {rank_mode!r} is not one of {MODES}"
        # NOTE: a job whose ranks mix modes cannot be read back (the reader refuses it), so
        # it is refused here instead of being certified rank by rank.
        if job_mode is None:
            job_mode = rank_mode
        elif rank_mode != job_mode:
            return f"rank {rank}: meta mode {rank_mode!r} differs from rank 0's {job_mode!r}"
        # A meta without the field is a version-1 capture (written before the field existed).
        rank_version = int(meta.get("capture_version", 1))
        # The mode and the version must agree whatever the caller asked for: the version is
        # what tells a summary npz from a mass npz, so a disagreement means the meta cannot
        # be trusted to say which arrays the npz holds.
        if rank_mode == "summary":
            version_fits = rank_version in SUMMARY_CAPTURE_VERSIONS
            needs = " or ".join(str(v) for v in SUMMARY_CAPTURE_VERSIONS)
        else:
            version_fits = rank_version in (1, CAPTURE_VERSION)
            needs = f"1 or {CAPTURE_VERSION}"
        if not version_fits:
            return (
                f"rank {rank}: meta capture_version {meta.get('capture_version')!r} does not "
                f"fit mode {rank_mode!r} (needs {needs})"
            )
        if capture_version is not None and rank_version != capture_version:
            return f"rank {rank}: meta capture_version {meta.get('capture_version')!r} != {capture_version}"
        if int(meta["query_start"]) != job.query_start:
            return f"rank {rank}: meta query_start {meta['query_start']} != job's {job.query_start}"
        layers_meta = meta.get("layers")
        if not isinstance(layers_meta, list) or len(layers_meta) != n_layers:
            count = len(layers_meta) if isinstance(layers_meta, list) else layers_meta
            return f"rank {rank}: meta has {count} layers, the config has {n_layers} attention layers"
        if meta.get("num_heads_local") != heads_local:
            return (
                f"rank {rank}: meta num_heads_local {meta.get('num_heads_local')!r} != "
                f"{heads_local} (config heads {n_heads} / tp {tp})"
            )
        expected_shape = [n_layers, expected_p, heads_local, attention.N_TOKEN_CLASSES]
        rows_shape = meta.get("rows_shape")
        if not isinstance(rows_shape, list) or rows_shape != expected_shape:
            return f"rank {rank}: meta rows_shape {rows_shape!r} != {expected_shape}"
        gate, tol = meta.get("gate_max_rel"), meta.get("gate_tol")
        if gate is None or tol is None or not float(gate) <= float(tol):
            return f"rank {rank}: self-consistency gate {gate} exceeds tolerance {tol}"
        # The gate compares the figure with the tolerance the meta itself declares, so a capture
        # could certify itself by declaring a loose one. The cap closes that. Ranks of one job may
        # declare different tolerances (a fill run mixes the plugin default and the cap), so the
        # ranks are not required to agree.
        if float(tol) > MAX_GATE_TOL:
            return (
                f"rank {rank}: meta gate_tol {tol} exceeds the cap {MAX_GATE_TOL} "
                "(no capture may certify itself with a looser tolerance)"
            )
        size = _object_size(client, bucket, npz_key)
        # Design: a rank whose meta says ``npz_put: "existing"`` was uploaded by a fill run whose
        # npz put was refused because the object already existed (the append-only store keeps
        # the first one). Its meta ``bytes`` is the size of the blob THAT run built, which can
        # differ from the stored npz of the earlier run. Only this size comparison is skipped:
        # the object must still exist (``_object_size`` fails on a missing one), and every other
        # meta check and, when sampled, the array content checks still apply.
        if meta.get("npz_put") != "existing" and size != int(meta["bytes"]):
            return f"rank {rank}: npz size {size} != meta bytes {meta['bytes']}"
        if sampled:
            body = client.get_object(Bucket=bucket, Key=npz_key)["Body"].read()
            loaded = np.load(io.BytesIO(body))
            if rank_mode == "summary":
                failure = _audit_summary_arrays(loaded, job, n_layers, heads_local, rank_version)
                shape = (n_layers, expected_p)
                mass_name = "sum_mass"
            else:
                failure, shape = _audit_arrays(loaded, job, n_layers, heads_local, rank_version)
                mass_name = "mass"
            if failure:
                # Deferred, not returned: every rank's arrays are examined, so a
                # defect that sits in one rank only is not hidden behind the first
                # rank that fails. The first failure by rank order is the reason.
                array_failure = array_failure or f"rank {rank}: {failure}"
            else:
                shapes.add(shape)
                # Each rank holds a different slice of the heads, so byte-identical
                # mass means a duplicated or swapped upload. All-zero mass and zero
                # completion positions are skipped: degenerate arrays are identical
                # across ranks legitimately, and must not trip the check.
                mass = np.asarray(loaded[mass_name])
                if mass.size and mass.any():
                    digest = hashlib.sha256(
                        str(mass.shape).encode() + str(mass.dtype).encode() + mass.tobytes()
                    ).digest()
                    if digest in digests and duplicate is None:
                        duplicate = (
                            f"rank {rank} duplicates rank {digests[digest]}: identical "
                            f"{mass_name} arrays"
                        )
                    digests.setdefault(digest, rank)
    if array_failure:
        return array_failure
    if duplicate:
        return duplicate
    if len(shapes) > 1:
        return f"ranks disagree about the (L, P) shape: {sorted(shapes)}"
    return None


#: S3 error codes that mean "this session cannot read the store", not "the object is bad".
_ACCESS_ERROR_CODES = frozenset({
    "ExpiredToken", "ExpiredTokenException", "RequestExpired", "InvalidToken", "TokenRefreshRequired",
    "AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch", "UnrecognizedClientException",
    "SlowDown", "ServiceUnavailable", "InternalError", "RequestTimeout",
})  # fmt: skip


def _is_access_failure(exc: BaseException) -> bool:
    """Return whether `exc` is a failure to reach or read S3, as opposed to a bad capture.

    True for botocore transport and credential errors and for S3 answers that name an
    expired or refused session or a throttled or unavailable service. A missing key
    (``NoSuchKey``, 404) is False: a capture that lacks an object is a bad capture.
    """
    from botocore.exceptions import BotoCoreError, ClientError

    if isinstance(exc, ClientError):
        return exc.response.get("Error", {}).get("Code") in _ACCESS_ERROR_CODES
    return isinstance(exc, BotoCoreError)


def audit_captures(
    client: Any,
    bucket: str,
    jobs: Sequence[attention.Job],
    tp: int,
    *,
    model: str,
    config: Mapping[str, Any],
    sample_per_run: int = 1,
    arrays: str = "sample",
    mode: Optional[str] = None,
    capture_version: Optional[int] = None,
    workers: int = 1,
    client_factory: Optional[Callable[[], Any]] = None,
) -> Dict[str, Optional[str]]:
    """Audit captured objects by content; file counts prove nothing.

    Two kinds of capture are audited: ``mass`` (per-row arrays, capture version 1 or 2)
    and ``summary`` (sums over the rows, version 3, or 4 with the class split of the
    prompt entropy). The `mode` argument fixes the kind
    the caller expects; with ``None`` each rank is audited by the mode its own meta
    declares. The two kinds are never mixed up: whatever the arguments say, the meta's
    mode and version must agree (see below). Everything below describes the mass audit
    first, then what summary mode changes.

    With ``L, H = attention_shape(config)`` and ``H_local = H // tp``, for EVERY
    job and rank the meta json is read and checked, in this order (the first
    failure is the job's reason, each prefixed ``rank <r>: ``): ``job_id`` equals
    the job's; ``rank`` equals the rank read; ``model`` equals `model`;
    ``n_tokens`` and ``query_start`` equal the job's; the meta ``mode`` equals the
    `mode` argument (when ``None``: is ``"mass"`` or ``"summary"``, and all ranks of a
    job agree); the meta's mode and capture version agree (summary needs version 3 or 4,
    mass needs 1 or 2; the failure says ``capture_version``); the meta's
    capture version (``capture_version``, 1 when the field is absent) equals the
    `capture_version` argument, when that is not ``None``; ``len(layers) == L``; ``num_heads_local == H_local``; ``rows_shape ==
    [L, P, H_local, 4]`` with ``P = n_tokens - query_start`` (for both modes: it is the
    shape of the per-row statistics, which a summary has summed away); ``gate_max_rel <=
    gate_tol``; ``gate_tol`` itself is at most ``MAX_GATE_TOL`` (each rank is judged on
    its own meta, so the ranks of a job may declare different tolerances; the failure says
    ``gate_tol`` and the cap); and ``bytes`` equals the npz object's real size
    (``head_object`` when the client has it, else the listing's ``Size``). The size
    comparison alone is skipped for a rank whose meta says ``"npz_put": "existing"``: a fill
    run wrote that meta, its ``bytes`` is the blob that run built, and the stored npz is from an
    earlier run. The npz must still exist and every other check still applies. A missing meta key is a
    failure reason, never a crash of the audit (a mismatch against ``None`` for
    the identity, layer and shape keys, ``audit raised KeyError`` for the others).
    When ``H`` is
    not divisible by `tp`, every job fails with a reason saying so. The version
    check runs for every job, whether or not its arrays are downloaded.

    The arrays are downloaded for the jobs `arrays` selects: ``"sample"`` takes
    the first `sample_per_run` jobs of each run prefix, ``"all"`` takes every
    job. For those jobs every rank's npz must hold ``classes`` equal to the
    job's classes exactly; ``mass`` of shape ``(L, P, H_local, 4)``; entropy and
    sink sharing its first three axes; only finite values;
    ``mass.sum(-1) + sink`` within 2e-2 of 1; mass and sink at least ``-1e-3``; entropy at least ``-1e-3``; and
    entropy at most ``ln(query_start + i + 1 + s_l) + 1e-2`` for completion row
    ``i`` on layer ``l``. The ranks must also agree about ``(L, P)``. A meta
    failure ends a job's audit at once; an array failure is held until every
    rank's arrays have been read, and the first one by rank order is reported.
    Mass and sink must have no entry below ``-1e-3``. When a job's arrays are
    read for more than one rank, no two ranks may hold byte-identical ``mass``
    (each rank holds different heads, so identical arrays mean a duplicated or
    swapped upload); the failure reads ``rank r duplicates rank s``. Ranks whose
    mass is all zeros are not compared.

    The array rules of the paragraph above and of the next two paragraphs (down to the
    cross-check of ``prompt_entropy``) are the mass audit's. A summary rank is checked by the summary
    content audit described after them instead. A mass rank whose meta is version 2 or
    later (``capture_version >= 2``) is checked further, after every check above
    passes. Its npz must hold ``prompt_entropy`` (the entropy of each response row over the prompt keys ``[0, query_start)``,
    renormalised, sink excluded) with the shape of ``entropy``, and a
    ``sliding_window`` array of shape ``(L,)`` (0 marks a global layer). The
    missing-array failures can fire only for the jobs whose arrays are
    downloaded (`arrays`); the version check above runs for every job. Then, in
    this order: no ``+-inf``; every finite value at least ``-1e-3``; every finite
    value at most ``ln(n) + 1e-2``, where ``n`` is the number of prompt keys the
    row can attend (``query_start`` on a global layer; ``min(query_start, w - 1 - i)``
    on a layer with window ``w`` and row ``i < w - 1``; the slack covers float16
    storage; with ``query_start == 0`` there is no ceiling and every finite value
    fails the next rule). NaN is legitimate in ``prompt_entropy`` and is placed
    by rule. A row ``i`` (absolute position ``query_start + i``) can attend a
    prompt key unless ``query_start == 0`` or the layer's window ``w > 0`` has
    ``i >= w - 1``. A finite value where no prompt key is attendable fails. A NaN
    passes only where no prompt key is attendable AND the stored prompt mass
    (``mass[..., 0] + mass[..., 1] + mass[..., 2]``) is exactly 0: masked keys
    get probability exactly 0, so the stored mass there is exactly 0. A finite
    value where a prompt key is attendable passes whatever the stored prompt
    mass, because a peaked row's tiny prompt mass can underflow float16. The
    rule encodes the plugin's masks (causal plus sliding window); a layer type
    that masks prompt keys another way needs its geometry stored in the npz, or
    its NaNs fail this check. The failure names the first offending
    ``(layer, row, head)``.

    Last comes a cross-check of ``prompt_entropy`` against the other arrays, on every
    cell where it is finite. With ``m = mass[..., 0] + mass[..., 1] + mass[..., 2]``,
    ``r = mass[..., 3]``, ``s = sink``, ``H = entropy``, ``Hp = prompt_entropy`` and
    ``G = -(m ln m + r ln r + s ln s)`` (a zero probability contributes 0), the grouping
    rule of entropy gives ``H = G + m * Hp + r * Hr`` with ``Hr``, the entropy of the
    response part, between 0 and ``ln(i + 1)`` for row ``i``. The audit requires
    ``H - G - r ln(i + 1) - tol <= m * Hp <= H - G + tol`` with
    ``tol = 0.05 + 2e-3 * (1 + H)`` (float16 storage of the five quantities; see
    ``_PE_CHAIN_ABS_TOL``). The failure names the first offending cell, the side that
    failed and the numbers. This catches halved, shuffled-across-heads and constant
    arrays, and a copy of the whole-row entropy when the response mass is large (with a
    small response mass the whole-row entropy is close to ``prompt_entropy``, so the
    copy stays inside the tolerance). It cannot catch a wrong ``prompt_entropy`` where
    the interval is wide: late rows with a large response mass ``r``, where the
    unstored ``Hr`` leaves ``r ln(i + 1)`` nats of room. A version-1 capture is audited
    exactly as before.

    The summary content audit (mode ``summary``, version 3 or 4) is the mass audit applied
    to sums over the ``P`` response rows. Every failure names the offending npz array
    and, where it applies, the first ``(layer, head)``. In this order: ``classes``
    equal the job's; every name in ``attention.SUMMARY_ARRAYS``, ``sliding_window`` and
    ``has_sink`` is present; ``rows == P``; shapes are ``[L, H_local]`` for every
    per-head array, ``[L, H_local, 4]`` for ``sum_mass``, ``(L,)`` for
    ``sliding_window`` and ``has_sink`` (and ``layers`` has L entries when present);
    every value is finite; the counts are exact: ``n_prompt_entropy`` is 0 when
    ``query_start == 0``, ``P`` on a global layer, ``min(P, w - 1)`` on a layer with
    window ``w``, and ``n_pad_ratio`` is the number of rows whose causal prefix holds a
    class-1 token; floors: ``sum_mass`` and ``sum_sink`` at least ``-1e-3 * P``,
    ``sum_entropy`` at least ``-1e-3 * P``, ``sum_prompt_entropy`` at least
    ``-1e-3 * n_prompt_entropy``; where ``n_prompt_entropy == 0`` the sums
    ``sum_prompt_entropy``, ``sum_m_hp``, ``sum_chain_hi`` and ``sum_chain_lo`` are
    exactly 0; ``sum_mass.sum(-1) + sum_sink`` is within ``2e-2 * P`` of ``P`` (the mass
    audit's per-row allowance summed over the rows); the mean entropy
    ``sum_entropy / P`` is at most the mean over rows of ``ln(query_start + i + 1 + s_l)``
    plus ``1e-2``, and the mean ``sum_prompt_entropy / n`` is at most the mean over the
    ``n`` defined rows of ``ln(count_i)`` plus ``1e-2`` (``count_i`` is ``query_start`` on
    a global layer and ``min(query_start, w - 1 - i)`` on a windowed one); and the chain
    rule ``sum_chain_lo - tol <= sum_m_hp <= sum_chain_hi + tol`` with
    ``tol = n * (0.05 + 2e-3) + 2e-3 * max(sum_entropy, 0)``, the mass audit's per-row
    tolerance summed over the ``n`` defined rows. As for mass, no two ranks of a job may
    hold byte-identical ``sum_mass`` (all-zero arrays are not compared).

    A version-4 summary rank is checked further, at the matching points of that order:
    ``sum_prompt_entropy_by_class`` is present (a missing array fails, naming the version), has
    shape ``[L, H_local, 3]``, is finite, is non-negative (no floor below 0: each per-row term
    is a sum of non-negative values), is exactly 0 where ``n_prompt_entropy == 0``, and adds up
    over its class axis to ``sum_prompt_entropy`` within ``1e-3 * |sum_prompt_entropy| + 1e-6 *
    n_prompt_entropy`` (``_BY_CLASS_IDENTITY_RTOL``; the failure names the cell and both sums).
    It must also hold the sums over the answer rows (rows whose token is class 4;
    ``attention.SUMMARY_ANSWER_ARRAYS`` and the 0-d ``rows_answer``, zeros allowed), with the
    shapes ``[L, H_local]`` (``[L, H_local, 3]`` / ``[L, H_local, 4]`` for the by-class and mass
    forms), finite, and checked by ``_audit_answer_sums``: exact ``rows_answer`` and
    ``n_prompt_entropy_answer``, floors, zeros where nothing is summed, each answer sum at most
    its all-rows counterpart, and the class-split identity over the answer rows. A version-3
    rank is audited exactly as before.

    The ceiling follows from how the box computes entropy: over the row's
    attended tokens plus the sink column. Row ``i`` sits at absolute position
    ``query_start + i`` and attends at most ``query_start + i + 1`` tokens (itself
    included), plus one sink column when ``has_sink[l]`` is true, so ``s_l`` is 1
    or 0. An entropy over ``n`` columns is at most ``ln(n)``. The 1e-2 slack
    covers float16 storage. Sliding windows only shrink the attended set, so
    ignoring them keeps the bound valid. An npz without a ``has_sink`` array
    gets ``s_l = 1`` on every layer (the looser bound).

    Parameters
    ----------
    client : Any
        S3 client with ``get_object`` and ``head_object`` or ``list_objects_v2``.
        Used when ``workers == 1``; with more workers every worker thread builds
        its own client from `client_factory` and this one is not touched.
    bucket : str
        Bucket holding the captures.
    jobs : Sequence[attention.Job]
        Mass jobs the box reported as captured, in order.
    tp : int
        Tensor-parallel degree: ranks per job. Must be at least 1.
    model : str
        Served model name every rank's meta must carry (required: an audit that
        skips a check silently proves less than it appears to).
    config : Mapping[str, Any]
        Parsed ``config.json`` of the model; gives ``L`` and ``H`` through
        ``attention_shape``. Required for the same reason as `model`.
    sample_per_run : int, optional
        Jobs per run prefix whose arrays are downloaded when `arrays` is
        ``"sample"`` (default 1).
    arrays : str, optional
        ``"sample"`` (default) or ``"all"``: which jobs get their arrays checked.
    mode : Optional[str], optional
        Capture mode every rank's meta must declare, ``"mass"`` or ``"summary"``.
        ``None`` (default) accepts either and audits each rank by its own meta mode
        (anything else fails the job). ``replay_model`` passes the run's mode.
    capture_version : Optional[int], optional
        Capture format every rank's meta must declare (``None``, the default,
        accepts any version and audits each rank by its own). ``replay_model``
        passes ``CAPTURE_VERSION`` (mass) or ``SUMMARY_CAPTURE_VERSION`` (summary, 4);
        ``audit_existing`` passes each stored job's own version, so stored version-3
        summary captures stay auditable.
    workers : int, optional
        Jobs audited at once (default 1: one after the other, on `client`). With
        ``workers > 1`` the jobs run in a thread pool of that size, and the result is
        identical to the sequential one: the same dict in the same job order, with the
        same jobs sampled (the sampling is decided in job order before any job starts).
    client_factory : Optional[Callable[[], Any]], optional
        Returns a NEW S3 client per call. Required when ``workers > 1``: each worker
        thread calls it once and keeps that client for all its jobs, so no client is
        shared between threads.

    Returns
    -------
    Dict[str, Optional[str]]
        Job id -> failure reason, or ``None`` when the job passed, in the order of
        `jobs`. A failure of any kind (including an unreadable object) is a reason,
        never an exception.

    Raises
    ------
    ValueError
        When `arrays` is not ``"sample"`` or ``"all"``, when `mode` is neither ``None``
        nor in ``MODES``, when `workers` is not an
        integer of at least 1, or when ``workers > 1`` and `client_factory` is
        ``None`` (all before any read), or when `config` has no readable attention
        shape (``attention_shape``).
    Exception
        Whatever `client_factory` raises (with ``workers > 1``): that is an
        environment failure, not a verdict on a job, so it stops the audit
        instead of being recorded against the jobs. Jobs not yet started are
        cancelled; jobs already running finish first.

    Notes
    -----
    Network: per job and rank one GET of the meta and one size lookup; the
    jobs selected by `arrays` also download their arrays (``"all"`` downloads
    every capture, which can be large). Read-only.

    Memory: a worker holds the whole body of one array (up to a few GB) and its
    float32 copies at a time, so peak memory grows with `workers`.
    """
    if arrays not in ("sample", "all"):
        raise ValueError(f"arrays must be 'sample' or 'all', got {arrays!r}")
    if mode is not None:
        _resolve_mode(mode)  # refuse an unknown mode here, not as one failure per job
    _check_workers(workers, "workers")
    if workers > 1 and client_factory is None:
        raise ValueError(f"client_factory is required when workers > 1 (workers={workers})")
    n_layers, n_heads = attention_shape(config)

    # Phase 1: decide which jobs get their arrays checked, in job order. The rule
    # depends only on that order, so it is settled before any job starts and the
    # threaded run samples exactly the jobs the sequential run does.
    todo: List[Tuple[attention.Job, bool]] = []
    seen: Dict[str, int] = {}
    for job in jobs:
        prefix = job.key.rsplit("/", 1)[0]
        sampled = arrays == "all" or seen.get(prefix, 0) < sample_per_run
        seen[prefix] = seen.get(prefix, 0) + 1
        todo.append((job, sampled))

    def audit_one(use: Any, job: attention.Job, sampled: bool) -> Optional[str]:
        try:
            return _audit_job(
                use, bucket, job, tp, sampled, model, n_layers, n_heads, capture_version, mode
            )
        except Exception as exc:  # noqa: BLE001 -- recorded per job, none hidden
            if _is_access_failure(exc):
                # Not a verdict on the capture: the store could not be read (expired
                # session, no network). Manifests are append-only, so recording this
                # as an audit failure would retire a good capture for good.
                raise
            return f"audit raised {type(exc).__name__}: {exc}"

    # Phase 2: audit. Outcomes are consumed in job order whichever way they were
    # produced, so the result dict and the log read the same sequentially or threaded.
    pool: Optional[ThreadPoolExecutor] = None
    results: Dict[str, Optional[str]] = {}
    try:
        outcomes: Iterator[Optional[str]]
        if workers == 1 or not todo:
            outcomes = (audit_one(client, job, sampled) for job, sampled in todo)
        else:
            # Design: one client per worker thread (a thread-local, filled on first
            # use) rather than one per job or one shared client: the audit is
            # dominated by multi-GB downloads, so a client per thread costs nothing,
            # and no client object is used by two threads at once.
            local = threading.local()

            def audit_in_thread(job: attention.Job, sampled: bool) -> Optional[str]:
                # Built outside audit_one's try: a failing factory must not be
                # recorded as a verdict on this job (manifests are append-only).
                thread_client = getattr(local, "client", None)
                if thread_client is None:
                    thread_client = local.client = client_factory()  # type: ignore[misc]
                return audit_one(thread_client, job, sampled)

            pool = ThreadPoolExecutor(max_workers=min(workers, len(todo)))
            futures = [pool.submit(audit_in_thread, job, sampled) for job, sampled in todo]
            outcomes = (future.result() for future in futures)
        for (job, _sampled), reason in zip(todo, outcomes):
            if reason:
                logging.warning(f"attention_replay: audit failed for {job.job_id}: {reason}")
            results[job.job_id] = reason
    finally:
        if pool is not None:
            # An error or interrupt: drop the jobs not started; the running ones finish.
            pool.shutdown(wait=True, cancel_futures=True)
    return results


def write_manifest(client: Any, bucket: str, run_prefix: str, payload: Mapping[str, Any]) -> str:
    """Write one run's manifest, never overwriting.

    The key is ``<run_prefix>manifest--<utc stamp with microseconds>.json``. The
    key is shown to be absent with ``list_objects_v2`` before the put, and the put
    carries ``IfNoneMatch="*"`` so S3 itself refuses to replace an object that
    appeared between the listing and the put.

    Parameters
    ----------
    client : Any
        S3 client with ``list_objects_v2`` and ``put_object``.
    bucket : str
        Destination bucket.
    run_prefix : str
        Run key prefix with trailing ``/`` (see ``run_prefix``).
    payload : Mapping[str, Any]
        JSON-serialisable manifest content.

    Returns
    -------
    str
        The key written.

    Raises
    ------
    FileExistsError
        When the key already exists (two writers within one microsecond), whether
        the listing shows it or S3 answers ``PreconditionFailed`` (HTTP 412).
    """
    from botocore.exceptions import ClientError

    key = f"{run_prefix}manifest--{format_run_ts(datetime.now(timezone.utc))}.json"
    listing = client.list_objects_v2(Bucket=bucket, Prefix=key)
    if any(o["Key"] == key for o in listing.get("Contents") or []):
        raise FileExistsError(f"s3://{bucket}/{key} already exists; manifests are append-only")
    body = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
    try:
        client.put_object(
            Bucket=bucket, Key=key, Body=body, ContentType="application/json", IfNoneMatch="*"
        )
    except ClientError as exc:
        if (
            exc.response.get("Error", {}).get("Code") == "PreconditionFailed"
            or exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 412
        ):
            raise FileExistsError(
                f"s3://{bucket}/{key} already exists; manifests are append-only"
            ) from exc
        raise
    return key


# ------------------------------------------------------------------------- replay


@dataclass
class ReplayReport:
    """Outcome of ``replay_model`` or ``audit_existing``, keyed by ``attention.Job.job_id``."""

    model: str
    #: Landed instance type; ``None`` when nothing was provisioned.
    instance_type: Optional[str] = None
    tp: Optional[int] = None
    served_model_name: Optional[str] = None
    #: Jobs that passed the box's report, the upload check AND the content audit.
    verified: List[str] = field(default_factory=list)
    #: job id -> why the capture failed.
    failed: Dict[str, str] = field(default_factory=dict)
    #: job id -> keys already in the bucket; such a job was not sent.
    skipped_existing: Dict[str, List[str]] = field(default_factory=dict)
    #: Skipped jobs that have some but not all expected rank objects (both objects of
    #: every rank ``0..tp-1``; only rank 0 when the plan's tp is unknown). A re-send
    #: could not complete them, so inspect them by hand.
    partial: List[str] = field(default_factory=list)
    #: job id -> reason, for jobs the box reported as captured but the audit rejected.
    audit_failures: Dict[str, str] = field(default_factory=dict)
    #: Jobs longer than the context limit, excluded before sending.
    over_context: List[str] = field(default_factory=list)
    #: Planned jobs with no object in the bucket; counted by ``audit_existing`` only
    #: (``replay_model`` sends such jobs instead).
    not_captured: int = 0
    #: Manifest keys written (each key is added as soon as it is written, so the
    #: keys written before a manifest failure are kept).
    manifests: List[str] = field(default_factory=list)
    #: ``"<ExceptionType>: <message>"`` when writing the manifests failed; the capture
    #: results above are still valid, and the report is returned instead of lost.
    manifest_error: Optional[str] = None
    plan: Optional[ReplayPlan] = None
    #: Jobs of the batches that were never sent because the engine died (``replay_model``
    #: only); they hold no object and can be sent again as they are.
    not_sent: List[str] = field(default_factory=list)
    #: ``"<job id>: <error>"`` of the job in flight when the serving engine died, else ``None``.
    #: Not an exception: the box is still shut down and the verified jobs are audited.
    engine_died: Optional[str] = None
    #: Path of the file holding the box's log tail, written when the engine died; else ``None``.
    engine_log: Optional[str] = None
    #: Fill mode only: the jobs that held some but not all expected objects and were sent
    #: to be completed. A job that was complete is in ``skipped_existing`` instead.
    refilled: List[str] = field(default_factory=list)
    #: The effective serve settings of the run (``serve_settings``), set by ``replay_model``;
    #: ``None`` for ``audit_existing``. The same dict is written to every manifest as ``"serve"``.
    serve_settings: Optional[Dict[str, Any]] = None


def run_tag(model_key: str, run_label: Optional[str] = None, study: str = "induction") -> str:
    """Return the EC2 experiment tag of one replay run.

    The tag names the study (deduction only), the model and, when given, a label, so that
    runs of different models, of different studies, or of one model over different seeds
    each provision and terminate their own box. The state file is named after the tag.

    Parameters
    ----------
    model_key : str
        Roster key.
    run_label : Optional[str]
        Distinguishes concurrent runs of one model, for example ``"s0-14"``.
    study : str, optional
        ``"induction"`` (default; the tag is what it was before the deduction replay
        existed) or ``"horn"``.

    Returns
    -------
    str
        ``EC2_TAG-<model>[-<label>]`` for induction, ``EC2_TAG-horn-<model>[-<label>]`` for
        deduction, with every character outside ``A-Za-z0-9._-`` replaced by ``-``.

    Raises
    ------
    ValueError
        When `study` is neither ``"induction"`` nor ``"horn"``.

    Examples
    --------
    >>> run_tag("gemma-4-31b")
    'smolbench-rebuttal-attention-gemma-4-31b'
    >>> run_tag("deepseek-v3.1", "s0-14")
    'smolbench-rebuttal-attention-deepseek-v3.1-s0-14'
    >>> run_tag("gemma-4-31b", study="horn")
    'smolbench-rebuttal-attention-horn-gemma-4-31b'
    """
    _check_study(study)
    parts = [EC2_TAG] + (["horn"] if study == "horn" else []) + [model_key] + ([run_label] if run_label else [])
    return re.sub(r"[^A-Za-z0-9._-]", "-", "-".join(parts))


@contextlib.contextmanager
def _scoped_env(**env: str) -> Iterator[None]:
    """Set environment variables for the body and restore the previous values after."""
    previous = {name: os.environ.get(name) for name in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _launch_summary(plan: ReplayPlan, instance_types: Sequence[str], regions: Sequence[str]) -> str:
    """Return the text shown before the approval gate: what would be launched and its size."""
    return "\n".join([
        "attention replay launch summary",
        f"  model: {plan.model}",
        f"  instance types to hunt: {', '.join(instance_types)}; count: 1",
        f"  regions: {', '.join(regions)}",
        "  spot price: looked up by the provider at launch; not known offline",
        f"  jobs: {plan.jobs} (over-context jobs excluded: {plan.over_context})",
        f"  tokens: total {plan.total_tokens}, longest {plan.max_tokens}",
        plan.summary(),
    ])


def replay_model(  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
    model_key: str,
    results_root: Path = DEFAULT_RESULTS_ROOT,
    s3_uri: str = DEFAULT_S3_URI,
    *,
    approved: bool = False,
    instance_types: Optional[Sequence[str]] = None,
    allow_unsupported_capture: bool = False,
    allow_unverified_serve: bool = False,
    batch_size: int = attention.DEFAULT_BATCH_SIZE,
    poll_s: int = attention.DEFAULT_POLL_S,
    batch_timeout_s: int = attention.DEFAULT_BATCH_TIMEOUT_S,
    url_ttl_s: int = attention.DEFAULT_URL_TTL_S,
    audit_arrays: str = "all",
    audit_workers: int = 8,
    tokenizer_for: Optional[Callable[[str], Any]] = None,
    template_for: Optional[Callable[[str], Any]] = None,
    config_for: Optional[Callable[[str], Mapping[str, Any]]] = None,
    seeds: Optional[Sequence[int]] = None,
    run_label: Optional[str] = None,
    ec2: Any = None,
    s3_client_factory: Optional[Callable[[], Any]] = None,
    mode: Optional[str] = None,
    study: str = "induction",
    horn_rows: Optional[Path] = None,
    rungs_dir: Optional[Path] = None,
    arms: Optional[Sequence[str]] = None,
    reps: Optional[Sequence[int]] = None,
    capture_max_model_len: Optional[int] = None,
    allow_horn_mass: bool = False,
    job_ids: Optional[Sequence[str]] = None,
    fill: bool = False,
    gate_tol: Optional[float] = None,
    execute_model_timeout_s: Optional[int] = None,
    gpu_memory_utilization: Optional[float] = None,
    engine_log_dir: Optional[Path] = None,
    label_added_lines: bool = False,
    label_answer_tokens: bool = False,
) -> ReplayReport:
    """Capture one model's stored transcripts (induction marks or deduction cells) on one spot box. BILLED.

    Order of events. (0) Refuse fill mode without `job_ids`, and validate the serve
    settings (``serve_settings``); both before the plan is built. (1) Build the plan and
    jobs offline and print the launch summary. (2) Refuse unless ``approved is True``; right
    after it, refuse a deduction run in mass mode unless `allow_horn_mass` says otherwise.
    (3) Refuse a model in ``CAPTURE_UNSUPPORTED`` unless overridden, then one in
    ``SERVE_UNVERIFIED`` unless overridden. (4) Resume: skip every job that already has
    a key in the bucket (never re-sent, never overwritten); in fill mode a job with some but
    not all expected objects is sent instead, to be completed (see `fill`); when nothing
    remains, return without provisioning. (5) Provision one box, serve the checkpoint in
    capture mode and run the batches. If the serving engine dies, the batches stop there: the
    box's log tail is saved to a new file while the box is still up, and the jobs of the later
    batches are recorded as not sent. (6) Terminate the box, however the batches
    ended (an engine death included). (7) Only after the shutdown call, and only when the
    batches returned, audit the uploads by content and write one manifest per run that had
    jobs sent: both need only S3, and the audit downloads every array to this machine
    (about 3.5 minutes per GB in a pilot), so running it before the shutdown
    would leave the box idle and billed. (8) When the shutdown call failed on the
    success path, raise ``ShutdownFailed`` carrying the finished report.

    Parameters
    ----------
    model_key : str
        Roster key; needs a deploy spec and an ``INSTANCE_TYPES`` entry (or
        `instance_types`).
    results_root : Path, optional
        Induction: folder holding ``induction/<model>/...`` (see ``find_runs``). Ignored for
        ``study="horn"``.
    s3_uri : str, optional
        ``s3://bucket/prefix`` destination.
    approved : bool, optional
        Must be the singleton ``True``. Anything else (``1``, ``"yes"``) is refused.
    instance_types : Sequence[str], optional
        Types to hunt, overriding ``INSTANCE_TYPES[model_key]``.
    allow_unsupported_capture : bool, optional
        Run a model listed in ``CAPTURE_UNSUPPORTED`` anyway. Must be the singleton
        ``True``; anything else (``1``, ``"yes"``) leaves the refusal in place.
    allow_unverified_serve : bool, optional
        Run a model listed in ``SERVE_UNVERIFIED`` anyway (its serving on the
        pinned image is unverified and may fail on a billed box). Must be the
        singleton ``True``, like `approved`.
    batch_size, poll_s, batch_timeout_s, url_ttl_s : int, optional
        Passed to ``attention.run_capture_batches``.
    audit_arrays : str, optional
        ``"all"`` (default) downloads and checks the arrays of every captured job;
        ``"sample"`` checks one job per run and only the meta of the rest (see
        ``audit_captures``).
    audit_workers : int, optional
        Jobs audited at once after the box is down (default 8; each worker thread uses
        its own S3 client from `s3_client_factory`). 1 audits one job at a time. Must be
        at least 1. See ``audit_captures``: peak memory grows with it.
    tokenizer_for, template_for, config_for : Callable, optional
        Overrides of the pinned tokenizer, chat template and config (see ``plan_replay``).
    seeds : Sequence[int], optional
        Replay only the runs (induction) or cells (deduction) of these seeds, to split a
        model across several sessions. The plan, the jobs sent and the manifests cover only
        them; skipped and over-context counts too. ``None`` (default) means every seed; an
        empty sequence selects nothing, so nothing is sent and no box is provisioned.
    run_label : str, optional
        Distinguishes concurrent runs of one model; part of the instance tag and of the
        state file name (see ``run_tag``).
    ec2 : Any, optional
        Provider module or fake; defaults to ``smolbench.evals.providers.ec2``.
    s3_client_factory : Callable[[], Any], optional
        Returns a NEW S3 client per call; defaults to a fresh boto3 client in ``REGION``.
    mode : Optional[str], optional
        Capture mode, ``"mass"`` or ``"summary"``; ``None`` (default) means ``"mass"`` for
        induction and ``"summary"`` for deduction.
        Keyword-only. It is set on every job, passed to ``attention.run_capture_batches``,
        required of every rank's meta by the audit (with ``CAPTURE_VERSION`` for mass,
        ``SUMMARY_CAPTURE_VERSION`` for summary), and written to every manifest. Summary
        mode stores sums over the response rows instead of per-row arrays, so its
        objects do not grow with the response length. The captures of the two modes of
        one job share a key, so a job captured in one mode is never re-sent in the other.
    study : str, optional
        ``"induction"`` (default) or ``"horn"`` (the deduction cells; see the module
        docstring). Keyword-only, like every argument below. The approval gate, the refusals,
        the provisioning, the shutdown-before-audit order, the audit, the manifests and the
        no-overwrite upload rule are the same for both.
    horn_rows : Optional[Path], optional
        Deduction only: the model's rows file, or a folder holding ``<model>.jsonl``. Default
        ``bt.horn_rows_path(model_key)``.
    rungs_dir : Optional[Path], optional
        Deduction only: the rendered rungs; default ``bt.RUNGS_DIR``.
    arms, reps : Optional[Sequence], optional
        Deduction only: replay only these arms / replicate numbers (``None`` = all).
    capture_max_model_len : Optional[int], optional
        Capture context for this run (both studies), replacing ``capture_max_model_len(model,
        spec)``: an integer with ``0 < value <= spec["max_model_len"]``. Jobs longer than it are
        excluded as over-context, and it is passed to ``ec2.serve_model`` as ``max_model_len``.
        ``None`` keeps ``CAPTURE_MAX_MODEL_LEN.get(model_key)``.
    allow_horn_mass : bool, optional
        A deduction run in mass mode is refused (``ValueError``) unless this is the singleton
        ``True``: a mass capture grows with the response length, which for deduction is up to
        131072 tokens. Has no effect on induction or on summary mode.
    job_ids : Optional[Sequence[str]], optional
        Allow-list of job ids (see ``plan_replay``): only those jobs are planned, sent, audited
        and manifested. ``None`` (default) means every planned job. Required when `fill` is
        ``True``.
    fill : bool, optional
        Fill mode, a ``bool`` (default ``False``), needs `job_ids`. The replay is a
        deterministic teacher-forced prefill and the store is append-only with
        ``If-None-Match: *``, so a recapture goes under the SAME keys: objects that exist stay
        as they are and only the missing ones are added. In the resume phase a job with every
        expected object (both objects of ranks ``0..tp-1``, ``tp`` from the plan) is skipped as
        complete (``skipped_existing``); a job with some but not all of them is checked with
        ``attention.fill_refusal`` and, when the objects present come from a compatible capture
        (same mode, capture version and tp), sent and listed in ``ReplayReport.refilled``. When
        ANY job is refused the call raises before provisioning and names every refused job.
        Jobs with no object are sent as usual. With ``fill=False`` a job with some objects is
        reported as ``partial`` and never sent. Passed to ``ec2.serve_model`` (when ``True``)
        and ``attention.run_capture_batches``.
    gate_tol : Optional[float], optional
        The plugin's self-consistency tolerance for this run, ``0 < value <= MAX_GATE_TOL``;
        ``None`` keeps the plugin's own default (``PLUGIN_DEFAULT_GATE_TOL``). Passed to
        ``ec2.serve_model`` as given when set; left out when ``None``.
    execute_model_timeout_s : Optional[int], optional
        Engine step timeout in seconds, at least ``ec2.MIN_CAPTURE_EXECUTE_TIMEOUT_S``;
        ``None`` keeps ``ec2.DEFAULT_CAPTURE_EXECUTE_TIMEOUT_S``. Passed to ``ec2.serve_model``
        as given when set; left out when ``None``.
    gpu_memory_utilization : Optional[float], optional
        Share of GPU memory for vLLM, strictly between 0 and 1; ``None`` keeps the spec's.
        Passed to ``ec2.serve_model`` as given when set; left out when ``None``.
    engine_log_dir : Optional[Path], optional
        Folder for the engine log file written when the serving engine dies; default
        ``STATE_DIR``. Created if absent.
    label_added_lines : bool, optional
        Label the added lines class 1 (see ``plan_replay``; both studies). Every manifest
        written then carries ``"label_added_lines": true``.
    label_answer_tokens : bool, optional
        Label the answer tokens class 4 (see ``plan_replay``; both studies). Every manifest
        written then carries ``"label_answer_tokens": true``.
        The keys do not depend on the flag and stored jobs are skipped, so point `s3_uri` at a
        prefix that holds no unlabelled capture.

    Returns
    -------
    ReplayReport
        Verified, failed, skipped and audit-failed job ids, manifests written and the plan
        (``plan.mode`` is the mode run); ``refilled``, ``not_sent``, ``engine_died``,
        ``engine_log`` and ``serve_settings`` as described on ``ReplayReport``.

    Raises
    ------
    ShutdownFailed
        When the batches returned but ``shutdown_instance`` raised an ``Exception``.
        Raised after the audit and the manifests; its ``report`` attribute holds the
        finished report and its ``__cause__`` the shutdown error. A box may still be
        billing.
    ApprovalRequired
        When ``approved is not True``. Raised before any EC2 or S3 client or
        factory is touched.
    CaptureUnsupported
        When the model is in ``CAPTURE_UNSUPPORTED`` and ``allow_unsupported_capture``
        is not ``True`` (also before any AWS call).
    ServeUnverified
        When the model is in ``SERVE_UNVERIFIED`` and ``allow_unverified_serve``
        is not ``True`` (also before any AWS call).
    ValueError
        When no instance type is known for the model, the batch arguments are
        invalid, `audit_workers` is below 1, `seeds` or `reps` holds a non-integer, `mode`
        or `study` is not valid, `capture_max_model_len` is not valid for the model's spec, or
        a deduction-only argument is given for the induction study (before any AWS call, and
        for `mode`, `study` and the context before even the plan is built or printed). Also
        when ``study="horn"`` and the mode is ``"mass"`` without ``allow_horn_mass=True``: raised
        right after the approval gate, before any EC2 or S3 client or factory is touched, with
        the plan's mass estimate in bytes and GB. Also, all before the plan is built (and so
        before the approval gate): `fill` is ``True`` without `job_ids`; `job_ids` is empty or
        malformed; `fill` is not a ``bool``; `gate_tol`, `execute_model_timeout_s` or
        `gpu_memory_utilization` is out of range (``serve_settings``). `job_ids` naming a job
        that is not planned raises when the plan is built. In fill mode, also before
        provisioning: the plan's tp is unknown (completeness cannot be judged), or
        ``attention.fill_refusal`` refuses one or more jobs (the message lists each job id with
        its reason).
    RuntimeError
        When the model could not be planned at all (template or tokenizer
        unavailable), when its ``config.json`` cannot be loaded or has no
        attention shape (the content audit needs it), or when the provider has no
        weight mirror (``EC2_S3_MODEL_CACHE`` unset); all before any AWS call.

    Notes
    -----
    The box is terminated in a ``finally`` block however the capture ends, before
    the audit and the manifests. If that termination itself fails while another
    error propagates, the failure is logged at ERROR level (a box may still be
    billing) and the original error propagates. If it fails on the success path
    (the batches returned), the failure is logged at once, the audit and the
    manifests still run, and then ``ShutdownFailed`` is raised with the report. An
    audit or manifest failure in that case is logged and does not replace the
    shutdown failure. An interrupt (``KeyboardInterrupt`` or another
    ``BaseException``) that escapes ``shutdown_instance`` before it terminated the
    box triggers one retry with ``wait=False`` and SIGINT ignored; a failed retry
    is logged at ERROR and the interrupt is re-raised either way, without an audit
    (the operator asked to stop).

    A capture that raised is never audited and writes no manifest: its jobs have no
    result to check.

    A dead serving engine is not an exception. ``run_capture_batches`` stops sending and
    calls a hook while the box is still up; the hook writes the box's log tail (``log_tail``,
    then ``serve_log_tail`` when it is not empty) to a NEW file
    ``attention_engine_log--<tag>--<utc stamp>.log`` in `engine_log_dir` (or ``STATE_DIR``) and
    sets ``ReplayReport.engine_log``; the log tail is gone once the box is terminated. The box
    is shut down in the ``finally`` as always, the jobs that did verify are audited and
    manifested, ``engine_died`` names the job in flight and ``not_sent`` lists the jobs of the
    later batches (they hold no object and can be sent again). Both are logged at WARNING.

    A failure while writing the manifests does not lose the report: it is recorded
    in ``ReplayReport.manifest_error``, logged at ERROR, the manifests written so
    far stay in ``ReplayReport.manifests`` and the report is returned. An
    exception raised by the audit itself (not a failed job) propagates, as the
    box is already down; with a failed shutdown it is logged and ``ShutdownFailed``
    is raised instead.
    """
    # Phase 0: an unknown study or mode, fill mode without an allow-list and a bad serve setting
    # are refused before anything is read or built (and so before the gate and every client).
    from smolbench.evals.providers import ec2 as real_ec2

    _check_study(study)
    run_mode = _resolve_mode(mode, study)
    run_version = SUMMARY_CAPTURE_VERSION if run_mode == "summary" else CAPTURE_VERSION
    # Design: fill needs an explicit allow-list. Fill adds objects under existing keys, so it
    # must never act on a whole seed range picked by omission.
    if fill is True and _job_id_set(job_ids) is None:
        raise ValueError(
            "fill=True needs job_ids: fill mode completes the named jobs only and must never "
            "re-send a whole seed range"
        )
    # The REAL deploy spec, not the injected provider's: the settings are validated against the
    # spec the serve will use, and the check must not depend on a fake. A KeyError for an unknown
    # model surfaces here exactly as it does when the plan is built.
    serve = serve_settings(
        spec=real_ec2.EC2_DEPLOY_SPECS[model_key],
        capture_max_model_len=_resolve_capture_len(
            model_key, real_ec2.EC2_DEPLOY_SPECS[model_key], capture_max_model_len
        ),
        fill=fill, gate_tol=gate_tol, execute_model_timeout_s=execute_model_timeout_s,
        gpu_memory_utilization=gpu_memory_utilization,
    )
    source = _make_source(
        study, Path(results_root), _horn_rows_file(model_key, horn_rows) if study == "horn" else horn_rows,
        rungs_dir, arms, reps, label_added_lines, label_answer_tokens,
    )

    # Phase 1: offline plan and the launch summary, shown before the gate.
    _bucket_for_plan, plan_prefix = parse_s3_uri(s3_uri)
    plan, planned = _plan_one(
        model_key, source, plan_prefix, tokenizer_for, template_for, config_for, seeds,
        run_mode, capture_max_model_len, job_ids,
    )
    types = tuple(instance_types or INSTANCE_TYPES.get(model_key, ()))
    regions = tuple(getattr(ec2, "EC2_REGIONS", real_ec2.EC2_REGIONS))
    print(_launch_summary(plan, types, regions))

    # Phase 2: the approval gate. Spend needs an explicit decision, so only the
    # True singleton passes (a truthy 1 or "yes" could come from a careless
    # call), and the gate sits before every EC2 or S3 client so a refusal costs nothing.
    if approved is not True:
        raise ApprovalRequired(
            f"replay of {model_key} was not approved: pass approved=True after reading the "
            "launch summary above (it provisions a billed spot GPU box)"
        )
    # Design: the mass refusal sits directly after the gate, before every other check and
    # before any client, so a refused run costs nothing and nothing was touched. A mass
    # capture grows with the response length (deduction responses reach 131072 tokens), so it
    # is allowed only on an explicit True, like the other overrides.
    if study == "horn" and run_mode == "mass" and allow_horn_mass is not True:
        size = (
            "unknown (the config or the tp is not available)" if plan.est_capture_bytes is None
            else f"{plan.est_capture_bytes} bytes (about {plan.est_capture_bytes / 1e9:.1f} GB)"
        )
        raise ValueError(
            f"{model_key}: a mass capture of the deduction cells is refused: its estimated size is "
            f"{size}, and it grows with the response length. Use mode='summary' (the default for "
            "study='horn'), or pass allow_horn_mass=True to capture the mass arrays anyway."
        )
    # The overrides follow the approval gate's rule: only the True singleton lifts a
    # refusal, so a truthy 1 or "yes" from a careless call keeps the refusal in place.
    if model_key in CAPTURE_UNSUPPORTED and allow_unsupported_capture is not True:
        raise CaptureUnsupported(f"{model_key}: {CAPTURE_UNSUPPORTED[model_key]}")
    if model_key in SERVE_UNVERIFIED and allow_unverified_serve is not True:
        raise ServeUnverified(f"{model_key}: {SERVE_UNVERIFIED[model_key]}")
    if not types:
        raise ValueError(f"no instance types known for {model_key!r}; pass instance_types=")
    if batch_size < 1:
        raise ValueError(f"batch_size must be >= 1, got {batch_size}")
    if url_ttl_s <= batch_timeout_s:
        raise ValueError(f"url_ttl_s={url_ttl_s} must exceed batch_timeout_s={batch_timeout_s}")
    if audit_arrays not in ("sample", "all"):
        raise ValueError(f"audit_arrays must be 'sample' or 'all', got {audit_arrays!r}")
    # Checked here, not at the audit: a bad value must not be found after the box is billed.
    _check_workers(audit_workers, "audit_workers")
    if not planned and plan.errors:
        raise RuntimeError(f"{model_key}: nothing to capture, the plan failed: {plan.errors[0]}")

    # The content audit needs the model's attention shape, and it only runs after
    # the box has been paid for. Load and validate the config now so a missing or
    # unreadable one stops the run before any AWS client exists.
    try:
        config = config_for(model_key) if config_for is not None else load_model_config(model_key)
        attention_shape(config)
    except (TemplateUnavailable, ValueError, OSError) as exc:
        raise RuntimeError(
            f"{model_key}: cannot audit captures without the model config: {exc}"
        ) from exc

    # Phase 3: bind the real collaborators now that the gate is passed.
    ec2 = ec2 or real_ec2
    # The fleet serves from its weight mirror. Without it the box fetches the checkpoint
    # from Hugging Face anonymously, and the vLLM workers failed at startup that way on
    # 2026-11-16, after the instance was billed. The provider reads the variable at import.
    if getattr(ec2, "EC2_S3_MODEL_CACHE", None) == "":
        raise RuntimeError(
            f"{model_key}: EC2_S3_MODEL_CACHE is not set, so the instance would have no "
            "weight mirror. Set it (and EC2_S3_CACHE_REGION) in the environment before "
            "Python starts, as the notebook's first cell does."
        )
    make_s3 = s3_client_factory or _default_s3_factory
    bucket, prefix = parse_s3_uri(s3_uri)
    spec = (getattr(ec2, "EC2_DEPLOY_SPECS", None) or real_ec2.EC2_DEPLOY_SPECS)[model_key]
    max_len = _resolve_capture_len(model_key, spec, capture_max_model_len)
    report = ReplayReport(model_key, None, None, None, plan=plan, serve_settings=dict(serve))
    by_id = {p.job.job_id: p for p in planned}
    report.over_context = [p.job.job_id for p in planned if p.job.n_tokens > max_len]
    candidates = [p.job for p in planned if p.job.n_tokens <= max_len]

    # Phase 4: resume. Append-only: a job with any existing key is never sent.
    # The presigned URLs sign ``If-None-Match: *``, so S3 would refuse a PUT onto
    # an existing key with 412; skipping here matters because a re-sent job would
    # only fail that way on a billed box, and a partial rank set cannot be
    # completed by re-sending. Every rank uploads its own two objects, so the
    # complete set is both keys of every rank 0..tp-1. The plan's tp is the one
    # known before the box exists; when it is unknown only rank 0 can be checked.
    # Fill mode (job_ids required, checked in Phase 0) is the one exception to "never send a
    # job with a key": it sends a stem that is INCOMPLETE and compatible, and the plugin puts
    # only the objects that are absent. Completeness needs the rank count, so an unknown tp is
    # refused here, before any client exists, instead of guessing "rank 0 only".
    expected_tp = plan.tp_estimate
    if fill and not isinstance(expected_tp, int):
        raise ValueError(
            f"{model_key}: fill needs the plan's tensor-parallel degree to judge which jobs are "
            f"complete, but it is unknown (tp_estimate={expected_tp!r}); pass instance_types= "
            "that the provider can derive a tp for"
        )
    client = make_s3()
    remaining: List[attention.Job] = []
    refusals: Dict[str, str] = {}
    for job in candidates:
        present = attention.job_keys_present(client, bucket, job)
        if not present:
            remaining.append(job)
            continue
        if fill:
            present_set = set(present)
            complete = all(
                key in present_set
                for rank in range(expected_tp)  # type: ignore[arg-type]  # int, checked above
                for key in attention.rank_keys(job.key, rank)
            )
            if complete:
                report.skipped_existing[job.job_id] = present
                continue
            reason = attention.fill_refusal(
                client, bucket, job, expected_tp, run_mode, present  # type: ignore[arg-type]
            )
            if reason is not None:
                refusals[job.job_id] = reason
                continue
            remaining.append(job)
            report.refilled.append(job.job_id)
            continue
        report.skipped_existing[job.job_id] = present
        expected = [
            key
            for rank in range(expected_tp if isinstance(expected_tp, int) else 1)
            for key in attention.rank_keys(job.key, rank)
        ]
        present_set = set(present)
        missing = [key for key in expected if key not in present_set]
        if missing:
            report.partial.append(job.job_id)
            scope = (
                f"ranks 0..{expected_tp - 1}"
                if isinstance(expected_tp, int)
                else "rank 0 only (tp is unknown, so the higher ranks were not checked)"
            )
            logging.warning(
                f"attention_replay: {job.job_id} has {len(present)} key(s) but is missing "
                f"{len(missing)} expected object(s) ({scope}); inspect it by hand. "
                f"Missing keys: {missing}"
            )
    # Every refusal is collected first so one call names them all, and raised before the box
    # exists: a refused stem would otherwise be found out on billed hardware.
    if refusals:
        raise ValueError(
            f"{model_key}: fill refused {len(refusals)} job(s), nothing was provisioned:\n"
            + "\n".join(f"  {job_id}: {reason}" for job_id, reason in refusals.items())
        )
    if not remaining:
        return report

    # Phase 5: capture, scoped to this driver's tag and state file. The box is shut
    # down in the ``finally`` right after the batches return, BEFORE the audit: the
    # audit downloads every array to this machine and would otherwise keep the box
    # idle and billed for as long as that takes.
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    primary: Optional[BaseException] = None
    shutdown_exc: Optional[Exception] = None
    result: Optional[attention.CaptureResult] = None
    tp: Optional[int] = None
    tag = run_tag(model_key, run_label, study)
    # The caller's raw settings, and only those the caller set: an unset one (``None``, or
    # ``fill`` False) is left out, which is what ``None`` means to the serve (its own default;
    # ``serve_settings`` already worked out the effective value for the record). Design: omit
    # instead of passing ``None`` so a provider or fake that predates a setting is not handed a
    # keyword it does not know when the run does not use it.
    serve_kwargs: Dict[str, Any] = {
        name: value
        for name, value in (
            ("execute_model_timeout_s", execute_model_timeout_s), ("gate_tol", gate_tol),
            ("gpu_memory_utilization", gpu_memory_utilization),
        )
        if value is not None
    }
    if fill:
        serve_kwargs["fill"] = True

    def save_engine_log(status: Mapping[str, Any]) -> None:
        """Write the box's log tail to a new file while the box is still up (see Notes)."""
        directory = Path(engine_log_dir) if engine_log_dir is not None else STATE_DIR
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"attention_engine_log--{tag}--{format_run_ts(datetime.now(timezone.utc))}.log"
        tail, serve_tail = status.get("log_tail"), status.get("serve_log_tail")
        if isinstance(tail, str):
            text = tail
            if isinstance(serve_tail, str) and serve_tail:
                text += "\n--- serve_log_tail ---\n" + serve_tail
        else:
            # An unreadable or partial reply (for example the agent was unreachable): keep the
            # whole reply, it is the only evidence there will be once the box is terminated.
            text = json.dumps(status, indent=2, sort_keys=True, default=str)
        # Mode "x": a log is never overwritten, like every other artefact of this driver.
        with open(path, "x", encoding="utf-8") as handle:
            handle.write(text)
        report.engine_log = str(path)

    with _scoped_env(
        EC2_EXPERIMENT_TAG=tag, EC2_STATE_FILE=str(STATE_DIR / f".ec2_state--{tag}.json")
    ):
        try:
            state = ec2.provision_spot_instance(instance_types=types)
            report.instance_type = state["instance_type"]
            tp = ec2.derive_tp(model_key, state["instance_type"], spec)
            report.tp = tp
            with ec2.serve_model(
                model_key, capture=True,
                max_model_len=(
                    max_len if capture_max_model_len is not None
                    else CAPTURE_MAX_MODEL_LEN.get(model_key)
                ),
                **serve_kwargs,
            ) as served:
                report.served_model_name = served
                result = attention.run_capture_batches(
                    ec2, state, served, remaining, tp, make_s3, bucket, mode=run_mode,
                    batch_size=batch_size, url_ttl_s=url_ttl_s, poll_s=poll_s,
                    batch_timeout_s=batch_timeout_s, fill=fill, on_engine_death=save_engine_log,
                )
        except BaseException as exc:
            primary = exc
            raise
        finally:
            # Spend safety: the box is terminated however the capture ended
            # (provisioning, serving or a batch may raise). Cleanup must not
            # replace the error that matters, but a failed termination may leave a
            # billed box, so it is logged loudly.
            try:
                ec2.shutdown_instance()
            except Exception as exc:  # noqa: BLE001
                logging.error(
                    "attention_replay: shutdown_instance FAILED"
                    + (" while another error was propagating" if primary is not None else "")
                    + f"; a billed instance may still be running: {exc!r}"
                )
                # On the success path the failure is kept and raised after the audit,
                # which needs only S3 and must not be lost to a failed termination.
                # With a primary error in flight, that error propagates instead.
                if primary is None:
                    shutdown_exc = exc
            except BaseException:
                # An interrupt inside shutdown_instance (its graceful /shutdown POST
                # only guards against Exception) escapes before TerminateInstances.
                # Terminate anyway, then let the interrupt continue.
                _retry_shutdown_after_interrupt(ec2)
                raise

    # Phase 6: audit and manifests, after the box is gone. Reached only when the
    # batches returned: any exception above has already propagated, and the audit
    # of a capture that raised would have no result to check.
    assert result is not None and tp is not None  # set whenever the batches returned
    # An engine death is not an error of this call: the box is down, the batches that did
    # finish are audited below, and the unsent jobs are reported so they can be sent again.
    report.not_sent = list(result.not_sent)
    report.engine_died = result.engine_died
    if result.engine_died is not None:
        logging.warning(
            f"attention_replay: the serving engine died ({result.engine_died}); "
            f"{len(result.not_sent)} job(s) were not sent"
            + (f"; the log tail is in {report.engine_log}" if report.engine_log else "")
        )
    try:
        report.failed.update(result.failed)
        for job_id, keys in result.skipped_existing.items():
            report.skipped_existing[job_id] = keys
        verified_set = set(result.verified)
        audit = audit_captures(
            make_s3(), bucket, [j for j in remaining if j.job_id in verified_set], tp,
            model=model_key, config=config, arrays=audit_arrays, mode=run_mode,
            capture_version=run_version, workers=audit_workers, client_factory=make_s3,
        )
        for job_id, reason in audit.items():
            if reason is None:
                report.verified.append(job_id)
            else:
                report.audit_failures[job_id] = reason
        # A manifest failure must not discard the capture results: they are
        # the only record of what the box just did. It is recorded on the
        # report (the manifests written so far are already on it) and is not
        # the primary error.
        try:
            _write_manifests(
                make_s3(), bucket, prefix, model_key, spec, planned, report, result, tp,
                mode=run_mode, serve=report.serve_settings,
                label_added_lines=source.label_added_lines,
                label_answer_tokens=source.label_answer_tokens,
            )
        except Exception as manifest_exc:  # noqa: BLE001 -- recorded, not hidden
            report.manifest_error = f"{type(manifest_exc).__name__}: {manifest_exc}"
            logging.error(
                f"attention_replay: writing the manifests failed after {len(report.manifests)} "
                f"were written; the capture results are kept on the report: "
                f"{report.manifest_error}"
            )
    except Exception as late_exc:  # noqa: BLE001
        # With the box down this error propagates as it always did. With a failed
        # shutdown it must not hide that failure (a box may still be billing), so
        # both are logged and the shutdown failure is the one raised below.
        if shutdown_exc is None:
            raise
        logging.error(
            "attention_replay: the audit raised after the shutdown had failed; the "
            f"shutdown failure is raised instead: {late_exc!r}"
        )
    except BaseException:
        # An interrupt during the audit wins, but the failed shutdown is logged again
        # so it is the last thing on the screen.
        if shutdown_exc is not None:
            logging.error(
                "attention_replay: interrupted during the audit; shutdown_instance had "
                f"FAILED and a billed instance may still be running: {shutdown_exc!r}"
            )
        raise
    if shutdown_exc is not None:
        raise ShutdownFailed(
            f"{model_key}: the capture returned but shutdown_instance FAILED; a billed "
            f"instance may still be running: {shutdown_exc!r}. The capture results are "
            "on this exception's report.",
            report,
        ) from shutdown_exc
    return report


def _retry_shutdown_after_interrupt(ec2: Any) -> None:
    """Terminate the box again after an interrupt cut ``shutdown_instance`` short.

    The interrupted call never reached its state clearing, so the state file still
    names the instance and a second call can terminate it. ``wait=False`` skips the
    termination waiter, which keeps the retry short. SIGINT is ignored while the
    retry runs, so a second Ctrl-C cannot cut it short; the previous handler is
    restored afterwards. The handler is only touched from the main thread (the only
    thread that may set one) and when the current handler is known to Python
    (``signal.getsignal`` returns ``None`` for one installed from C, which cannot be
    restored); otherwise the retry runs without that protection.

    Parameters
    ----------
    ec2 : Any
        Provider module or fake with ``shutdown_instance(wait=...)``.

    Notes
    -----
    Never raises an ``Exception``: a failed retry is logged at ERROR (a billed
    instance may still be running) so the interrupt that triggered it stays the
    error the caller sees.
    """
    logging.warning("attention_replay: retrying termination after an interrupt")
    previous = signal.getsignal(signal.SIGINT)
    can_defer = threading.current_thread() is threading.main_thread() and previous is not None
    if can_defer:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        ec2.shutdown_instance(wait=False)
    except Exception as retry_exc:  # noqa: BLE001 -- must not replace the interrupt
        logging.error(
            "attention_replay: the termination retry after an interrupt FAILED; a billed "
            f"instance may still be running: {retry_exc!r}"
        )
    finally:
        if can_defer:
            signal.signal(signal.SIGINT, previous)


def _default_s3_factory() -> Any:
    """Return a fresh boto3 S3 client in ``REGION`` that presigns with Signature V4.

    boto3 presigns S3 URLs with Signature V2 unless the client is configured
    otherwise, and V2 silently drops the ``IfNoneMatch`` condition (the URL is
    byte-identical with and without it). Only ``signature_version="s3v4"`` puts
    ``if-none-match`` into the signed headers, which is what makes S3 refuse a
    PUT onto an existing key. The client is therefore configured explicitly.

    A NEW ``Session`` is built on every call because credentials rotate: a client
    kept across a long capture would sign with expired ones. The shared helper
    ``smolbench.evals._aws.fresh_client`` also builds a fresh session but takes no
    client config, and other modules depend on it, so it is not used here.

    Returns
    -------
    Any
        A boto3 S3 client for ``REGION`` with ``signature_version="s3v4"``.
    """
    import boto3.session
    from botocore.config import Config

    return boto3.session.Session().client(
        "s3", region_name=REGION, config=Config(signature_version="s3v4")
    )


def _group_by_run(planned: Sequence[PlannedJob]) -> List[List[PlannedJob]]:
    """Group `planned` by the run that owns a manifest, keeping the planned order of both levels.

    Induction: by stored run (seed, arm, stamp). Deduction: by ``HornRun`` (one ``<rung>/<arm>``
    folder). Design: one dict keyed on a hashable per-study key, not two functions, so the
    manifest code that consumes the groups stays single.
    """
    by_run: Dict[Hashable, List[PlannedJob]] = {}
    for item in planned:
        run = item.run
        key: Hashable = run if isinstance(run, HornRun) else (run.seed, run.arm, run.stamp)
        by_run.setdefault(key, []).append(item)
    return list(by_run.values())


def _manifest_entry(item: PlannedJob, status: str, gate_max_rel: Any) -> Dict[str, Any]:
    """Return the manifest's per-job entry (the shape ``read_captures`` reads).

    A deduction entry has the induction entry's keys with ``mark_index`` replaced by
    ``row_index`` (the row's line index in the rows file), plus ``seed``, ``rep`` and
    ``prompt_sha256``. ``read_captures`` finds a deduction cell by its ``job_id``.
    """
    entry: Dict[str, Any] = {"job_id": item.job.job_id}
    if isinstance(item.run, HornRun):
        entry["row_index"] = item.mark_index
    else:
        entry["mark_index"] = item.mark_index
    entry.update({
        "n_tokens": item.job.n_tokens,
        "query_start": item.job.query_start,
        "status": status,
        "gate_max_rel": gate_max_rel,
        "notes": list(item.notes),
    })
    if isinstance(item.run, HornRun):
        entry.update({"seed": item.seed, "rep": item.rep, "prompt_sha256": item.prompt_sha256})
    return entry


def _manifest_payload(
    model: str,
    spec: Mapping[str, Any],
    run: Union[Run, HornRun],
    entries: List[Dict[str, Any]],
    *,
    tp: Optional[int],
    instance_type: Optional[str],
    served_model_name: Optional[str],
    post_hoc_audit: bool = False,
    mode: str = "mass",
    serve: Optional[Mapping[str, Any]] = None,
    label_added_lines: bool = False,
    label_answer_tokens: bool = False,
) -> Dict[str, Any]:
    """Return the manifest content of one run; shared by ``_write_manifests`` and ``audit_existing``.

    ``post_hoc_audit`` adds the key ``"post_hoc_audit": True``; it is absent otherwise,
    so a manifest written at capture time is unchanged. `serve` (the run's effective
    ``serve_settings``) is written as ``"serve"``; ``None`` leaves the key out, which is what
    ``audit_existing`` does because the settings of the original run are unknown to it. `mode` is written as the
    manifest's ``"mode"``: the capture mode of the run's jobs (``"mass"``, ``"summary"``,
    or ``"mixed"`` from ``audit_existing`` when one run directory holds both). For a
    ``HornRun`` the ``"run"`` field is ``{"study": "horn", "rung", "arm", "source_file":
    <rows file name>}``; every other key is the same for both studies. `label_added_lines` adds
    ``"label_added_lines": True`` (the jobs' added lines are class 1) and `label_answer_tokens`
    adds ``"label_answer_tokens": True`` (the jobs' answer tokens are class 4); each is absent
    otherwise, so a manifest of the default classes is unchanged.
    """
    run_field: Dict[str, Any] = (
        {"study": "horn", "rung": run.rung, "arm": run.arm, "source_file": run.rows_path.name}
        if isinstance(run, HornRun) else
        {"seed": run.seed, "arm": run.arm, "stamp": run.stamp, "source_file": run.path.name}
    )
    payload: Dict[str, Any] = {
        "model": model,
        "run": run_field,
        "tp": tp,
        "instance_type": instance_type,
        "served_model_name": served_model_name,
        "hf_repo": spec["hf_model_id"],
        "hf_revision": tokenization._pinned_revision(spec),
        "capture": attention.CAPTURE_MARKER,
        "mode": mode,
        "jobs": entries,
        "approximations": list(APPROXIMATIONS),
        # Induction marks carry no usage; a deduction row carries its own (see approximation 10).
        "bedrock_token_counts": _HORN_BEDROCK_COUNTS_NOTE if isinstance(run, HornRun) else None,
    }
    if post_hoc_audit:
        payload["post_hoc_audit"] = True
    if label_added_lines:
        payload["label_added_lines"] = True
    if label_answer_tokens:
        payload["label_answer_tokens"] = True
    if serve is not None:
        payload["serve"] = dict(serve)
    return payload


def _write_manifests(
    client: Any,
    bucket: str,
    prefix: str,
    model: str,
    spec: Mapping[str, Any],
    planned: Sequence[PlannedJob],
    report: ReplayReport,
    result: attention.CaptureResult,
    tp: int,
    mode: str = "mass",
    serve: Optional[Mapping[str, Any]] = None,
    label_added_lines: bool = False,
    label_answer_tokens: bool = False,
) -> List[str]:
    """Write one manifest per run that had at least one job sent in this invocation.

    `mode` is the run's capture mode, recorded in every manifest. `serve` is the run's
    effective ``serve_settings``, recorded as ``"serve"``. `label_added_lines` is recorded as
    ``"label_added_lines": true`` when set, `label_answer_tokens` as ``"label_answer_tokens": true``
    (see ``_manifest_payload``). A job that an earlier manifest
    recorded as failed and that this run verified is plainly ``"verified"`` here: the reader
    takes the union of the verified entries of all manifests of a folder.

    Each key is appended to ``report.manifests`` as soon as it is written, so the
    manifests written before a later failure stay on the report. The same keys are
    returned.
    """
    sent = set(result.verified) | set(result.failed)
    keys: List[str] = []
    for items in _group_by_run(planned):
        if not any(i.job.job_id in sent for i in items):
            continue
        run = items[0].run
        entries = []
        for item in items:
            job_id = item.job.job_id
            if job_id in report.audit_failures:
                status = f"audit_failed: {report.audit_failures[job_id]}"
            elif job_id in report.verified:
                status = "verified"
            elif job_id in report.failed:
                status = f"failed: {report.failed[job_id]}"
            elif job_id in report.skipped_existing:
                status = "skipped_existing"
            elif job_id in report.over_context:
                status = "excluded_over_context"
            else:
                status = "not_sent"
            entries.append(_manifest_entry(item, status, result.gates.get(job_id)))
        payload = _manifest_payload(
            model, spec, run, entries, tp=tp, instance_type=report.instance_type,
            served_model_name=report.served_model_name, mode=mode, serve=serve,
            label_added_lines=label_added_lines, label_answer_tokens=label_answer_tokens,
        )
        key = write_manifest(client, bucket, run_prefix(prefix, run), payload)
        keys.append(key)
        report.manifests.append(key)
    return keys


# ------------------------------------------------------------ audit of stored captures


def _is_audit_outcome(status: Any) -> bool:
    """Return whether a manifest job status records the result of a content audit.

    ``"verified"`` and ``"audit_failed: ..."`` do. The other statuses
    ``_write_manifests`` writes (``failed:``, ``skipped_existing``, ``not_sent``,
    ``excluded_over_context``) say the job was NOT audited by that run, so a job that
    carries one of them still needs ``audit_existing``.
    """
    # NOTE: the spec said a job any manifest records, with any status, is skipped. That
    # would leave a job unaudited for good when a later ``replay_model`` listed it as
    # ``skipped_existing`` (its keys existed, its audit never ran), so only the two audit
    # outcomes count as recorded here. To follow the spec literally, return ``True`` for
    # every string status.
    return isinstance(status, str) and (status == "verified" or status.startswith("audit_failed"))


def _audited_job_ids(client: Any, bucket: str, manifest_keys: Sequence[str]) -> set:
    """Return the job ids that some manifest in `manifest_keys` records with an audit outcome.

    Raises
    ------
    ValueError
        When a manifest is not valid JSON or lacks the ``jobs`` entries
        ``_write_manifests`` writes (the audit must not guess what it holds).
    """
    audited: set = set()
    for key in manifest_keys:
        try:
            entries = json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read().decode())["jobs"]
            for entry in entries:
                if _is_audit_outcome(entry["status"]):
                    audited.add(entry["job_id"])
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"s3://{bucket}/{key}: unreadable manifest: {exc!r}") from exc
    return audited


def _rank0_tp_and_version(client: Any, bucket: str, job: attention.Job) -> Tuple[int, int, str]:
    """Return ``(tp, capture_version, mode)`` from the job's rank-0 meta json.

    A meta without ``capture_version`` is a version-1 capture; a meta without ``mode``
    is a mass capture (every capture written before summary mode existed).

    Raises
    ------
    ValueError
        When the meta is not valid JSON, is not an object, or has no ``tp`` that is an
        integer of at least 1, or its ``capture_version`` is not an integer, or its
        ``mode`` is not one of ``MODES``.
    """
    meta_key = attention.rank_keys(job.key, 0)[1]
    try:
        meta = json.loads(client.get_object(Bucket=bucket, Key=meta_key)["Body"].read().decode())
        tp = meta["tp"]
        version = meta.get("capture_version", 1)
        mode = meta.get("mode", "mass")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"unreadable rank-0 meta {meta_key}: {exc!r}") from exc
    for name, value, floor in (("tp", tp, 1), ("capture_version", version, 1)):
        if isinstance(value, bool) or not isinstance(value, int) or value < floor:
            raise ValueError(f"rank-0 meta {meta_key}: {name} {value!r} is not an integer >= {floor}")
    # A mode outside MODES is refused here, as a failure of this one job: handed on to
    # audit_captures it would raise for the whole group of jobs sharing its tp and version.
    if mode not in MODES:
        raise ValueError(f"rank-0 meta {meta_key}: mode {mode!r} is not one of {MODES}")
    return tp, version, mode


def audit_existing(
    model_key: str,
    results_root: Path = DEFAULT_RESULTS_ROOT,
    s3_uri: str = DEFAULT_S3_URI,
    *,
    seeds: Optional[Sequence[int]] = None,
    arrays: str = "all",
    workers: int = 8,
    tokenizer_for: Optional[Callable[[str], Any]] = None,
    template_for: Optional[Callable[[str], Any]] = None,
    config_for: Optional[Callable[[str], Mapping[str, Any]]] = None,
    s3_client_factory: Optional[Callable[[], Any]] = None,
    study: str = "induction",
    horn_rows: Optional[Path] = None,
    rungs_dir: Optional[Path] = None,
    arms: Optional[Sequence[str]] = None,
    reps: Optional[Sequence[int]] = None,
    capture_max_model_len: Optional[int] = None,
    job_ids: Optional[Sequence[str]] = None,
    label_added_lines: bool = False,
    label_answer_tokens: bool = False,
) -> ReplayReport:
    """Audit the captures of one model that are already in the bucket, and manifest them.

    ``replay_model`` audits what it just captured, but an audit that outlives the AWS
    session dies before any manifest is written, and a later ``replay_model`` skips
    those jobs because their keys exist. This function audits them afterwards. It reads
    and writes S3 only: it has no EC2 parameter and starts nothing.

    Steps. (1) Plan the jobs offline as ``replay_model`` does (same job ids and keys).
    (2) For each stored run (deduction: each ``<rung>/<arm>`` folder), list its keys once and
    classify every planned job: no key
    is *not captured* (counted in ``report.not_captured``); some but not all of the
    expected rank objects is *partial* (``report.partial``, logged, not audited); the
    rest are candidates. The expected rank count is the ``tp`` in the job's rank-0 meta
    json; when the plan's ``tp_estimate`` differs, the meta wins and the log says so.
    (3) A candidate that a manifest already records as audited (``verified`` or
    ``audit_failed: ...``) is skipped (``report.skipped_existing``). (4) The others are
    audited with ``audit_captures``, grouped by the ``tp``, capture version and mode of
    their rank-0 meta (a meta without a mode is a mass capture; mass and summary
    captures are each audited by their own rules), per run directory, and as soon as one directory is
    done its manifest is written (``write_manifest``, never overwriting) and its key is
    added to ``report.manifests``, so an interrupted call is resumed by calling it again.

    Parameters
    ----------
    model_key : str
        Roster key; needs a deploy spec.
    results_root : Path, optional
        Induction: folder holding ``induction/<model>/...`` (see ``find_runs``); gives the
        planned jobs. Ignored for ``study="horn"``.
    s3_uri : str, optional
        ``s3://bucket/prefix`` where the captures are.
    seeds : Sequence[int], optional
        Only the runs or cells of these seeds (see ``plan_replay``); ``None`` is every seed.
    arrays : str, optional
        ``"all"`` (default) or ``"sample"``: which jobs get their arrays downloaded
        (see ``audit_captures``).
    workers : int, optional
        Jobs audited at once (default 8); each worker thread has its own S3 client from
        `s3_client_factory`. Must be at least 1.
    tokenizer_for, template_for, config_for : Callable, optional
        Overrides of the pinned tokenizer, chat template and config (see ``plan_replay``).
    s3_client_factory : Callable[[], Any], optional
        Returns a NEW S3 client per call; defaults to a fresh boto3 client in ``REGION``.
        A new client is taken for the listing, for every run directory's audit and for
        every manifest write, so rotated credentials are picked up.
    study : str, optional
        ``"induction"`` (default) or ``"horn"``; the listing, the audit and the manifests are
        the same code for both (a deduction run directory is one ``<rung>/<arm>`` folder).
    horn_rows, rungs_dir, arms, reps
        Deduction only, as for ``replay_model``: they select the cells that are planned and so
        audited. ``horn_rows`` is the rows file or a folder holding ``<model>.jsonl``.
    capture_max_model_len : Optional[int], optional
        Capture context to plan against (see ``replay_model``); it only sets the plan's
        ``capture_max_model_len``, since stored captures are audited whatever their length.
    job_ids : Optional[Sequence[str]], optional
        Allow-list of job ids (see ``plan_replay``): only those jobs are planned, listed,
        audited and manifested. ``None`` (default) means every planned job. A job that an
        earlier manifest recorded as ``failed: ...`` (not an audit outcome) is audited once all
        its objects exist, as without the list. There is no fill handling here: this function
        never sends anything.
    label_added_lines : bool, optional
        Plan the jobs with the added lines labelled class 1 (see ``plan_replay``; both
        studies), as the run that captured them did (`label_answer_tokens` likewise for the
        answer tokens, recorded as ``"label_answer_tokens": true``); the audit compares the stored
        classes with the planned ones. Every manifest written then carries
        ``"label_added_lines": true``.

    Returns
    -------
    ReplayReport
        ``verified`` and ``audit_failures`` of this call, ``skipped_existing`` (job id ->
        keys, for the candidates a manifest already records), ``partial``,
        ``not_captured``, ``manifests`` and ``manifest_error``; ``instance_type`` stays
        ``None``. A manifest written here holds only the jobs this call audited and carries
        ``"post_hoc_audit": true`` and ``"mode"``: the audited jobs' mode when they share
        one, else ``"mixed"``. It has no ``"serve"`` key: the serve
        settings of the original run are unknown here.

    Raises
    ------
    ValueError
        When `arrays` or `workers` is invalid, `s3_uri` is malformed, `seeds` or `reps` holds a
        non-integer, `study` is unknown, a deduction-only argument is given for the induction
        study, `capture_max_model_len` is not valid for the spec, `job_ids` is invalid or names
        a job that is not planned (see ``plan_replay``), or an existing manifest is unreadable
        (before any audit starts).
    KeyError
        When the model has no deploy spec.
    RuntimeError
        When the model could not be planned at all, or its ``config.json`` cannot be
        loaded or has no attention shape.

    Notes
    -----
    An exception from an audit propagates; the manifests of the run directories finished
    before it stay in the bucket. A failure writing a manifest does not: it is recorded in
    ``manifest_error``, the report is returned and no further directory is audited (the
    audits could not be recorded). Rerun to resume.

    Cost: one paginated listing per run, one GET per existing manifest, one GET of each
    candidate's rank-0 meta, then ``audit_captures`` (the arrays dominate: ``"all"``
    downloads every capture, up to tens of GB; memory grows with `workers`). Read-only
    except for the manifests.
    """
    # NOTE: planning imports the EC2 provider module (``_plan_one`` and the manifest need
    # its deploy specs). Only the import: nothing here calls provisioning, serving or
    # shutdown, and the function takes no provider argument.
    from smolbench.evals.providers import ec2 as real_ec2

    if arrays not in ("sample", "all"):
        raise ValueError(f"arrays must be 'sample' or 'all', got {arrays!r}")
    _check_workers(workers, "workers")

    # Phase 1: offline plan and config, exactly as replay_model builds them.
    bucket, prefix = parse_s3_uri(s3_uri)
    _check_study(study)
    source = _make_source(
        study, Path(results_root), _horn_rows_file(model_key, horn_rows) if study == "horn" else horn_rows,
        rungs_dir, arms, reps, label_added_lines, label_answer_tokens,
    )
    plan, planned = _plan_one(
        model_key, source, prefix, tokenizer_for, template_for, config_for, seeds, None,
        capture_max_model_len, job_ids,
    )
    if not planned and plan.errors:
        raise RuntimeError(f"{model_key}: nothing to audit, the plan failed: {plan.errors[0]}")
    try:
        config = config_for(model_key) if config_for is not None else load_model_config(model_key)
        attention_shape(config)
    except (TemplateUnavailable, ValueError, OSError) as exc:
        raise RuntimeError(
            f"{model_key}: cannot audit captures without the model config: {exc}"
        ) from exc
    spec = real_ec2.EC2_DEPLOY_SPECS[model_key]
    report = ReplayReport(model_key, None, None, None, plan=plan)
    if not planned:
        return report
    make_s3 = s3_client_factory or _default_s3_factory

    # Phase 2: list and classify, per run, before any audit starts. Listing is cheap and
    # an unreadable manifest should stop the call before hours of downloads, not after.
    # Design: one listing per run prefix, not one per job. It returns the same keys
    # ``attention.job_keys_present`` would (every key under ``<stem>.``) in far fewer calls.
    client = make_s3()
    # (run, planned jobs to audit, {job id: (tp, capture_version, mode) or the reason it has none})
    work: List[Tuple[Union[Run, HornRun], List[PlannedJob], Dict[str, Any]]] = []
    for items in _group_by_run(planned):
        run = items[0].run
        run_keys_prefix = run_prefix(prefix, run)
        keys = [key for key, _size in _list_objects(client, bucket, run_keys_prefix)]
        audited = _audited_job_ids(client, bucket, [
            key for key in keys
            if key.startswith(run_keys_prefix + "manifest--") and key.endswith(".json")
        ])
        candidates: List[PlannedJob] = []
        formats: Dict[str, Any] = {}
        tps_seen: set = set()
        for item in items:
            job = item.job
            stem = job.key[: -len(".npz")] + "."
            present = [key for key in keys if key.startswith(stem)]
            if not present:
                report.not_captured += 1
                continue
            if job.job_id in audited:
                report.skipped_existing[job.job_id] = present
                continue
            # The rank count the capture was made with: its own meta, not the plan's guess.
            # With no rank-0 meta there is nothing to read, so the plan's tp (else 1, as
            # replay_model does) sets the expectation and the missing meta makes it partial.
            tp: Optional[int] = None
            version = 1
            job_mode = "mass"
            if attention.rank_keys(job.key, 0)[1] in present:
                try:
                    tp, version, job_mode = _rank0_tp_and_version(client, bucket, job)
                except ValueError as exc:
                    # Audited as failed, not skipped: the job is stored but cannot be trusted.
                    candidates.append(item)
                    formats[job.job_id] = f"audit raised ValueError: {exc}"
                    continue
                if isinstance(plan.tp_estimate, int) and plan.tp_estimate != tp:
                    tps_seen.add(tp)
            expected_tp = tp if tp is not None else (
                plan.tp_estimate if isinstance(plan.tp_estimate, int) else 1
            )
            present_set = set(present)
            missing = [
                key for rank in range(expected_tp) for key in attention.rank_keys(job.key, rank)
                if key not in present_set
            ]
            if missing:
                report.partial.append(job.job_id)
                logging.warning(
                    f"attention_replay: {job.job_id} has {len(present)} key(s) but is missing "
                    f"{len(missing)} expected object(s) (ranks 0..{expected_tp - 1}); inspect it "
                    f"by hand. Missing keys: {missing}"
                )
                continue
            candidates.append(item)
            formats[job.job_id] = (tp, version, job_mode)
        for tp_meta in sorted(tps_seen):
            logging.warning(
                f"attention_replay: {run_keys_prefix}: capture meta says tp={tp_meta}, the plan "
                f"estimated tp={plan.tp_estimate}; the meta is trusted"
            )
        if candidates:
            work.append((run, candidates, formats))

    # Phase 3: audit and manifest, one run directory at a time. The manifest goes out as
    # soon as its directory is audited: a call cut short (an expired session, an interrupt)
    # keeps everything finished, and a rerun finds those jobs recorded and skips them.
    for run, candidates, formats in work:
        run_keys_prefix = run_prefix(prefix, run)
        outcome: Dict[str, Optional[str]] = {}
        # audit_captures takes one tp, one capture version and one mode per call, so group by
        # them (a run is normally one group; a re-capture under another plugin or in the other
        # mode would be two).
        groups: Dict[Tuple[int, int, str], List[attention.Job]] = {}
        for item in candidates:
            fmt = formats[item.job.job_id]
            if isinstance(fmt, str):
                outcome[item.job.job_id] = fmt
            else:
                groups.setdefault(fmt, []).append(item.job)
        for (tp, version, group_mode), jobs in groups.items():
            outcome.update(audit_captures(
                make_s3(), bucket, jobs, tp, model=model_key, config=config, arrays=arrays,
                mode=group_mode, capture_version=version, workers=workers,
                client_factory=make_s3,
            ))
        entries = []
        for item in candidates:
            reason = outcome[item.job.job_id]
            if reason is None:
                report.verified.append(item.job.job_id)
                status = "verified"
            else:
                report.audit_failures[item.job.job_id] = reason
                status = f"audit_failed: {reason}"
            # The box's gate figure is not known afterwards (the audit only checks that it
            # is within tolerance), so it is recorded as null.
            entries.append(_manifest_entry(item, status, None))
        tps = {fmt[0] for fmt in formats.values() if not isinstance(fmt, str)}
        # The manifest's mode is the mode of the audited jobs when they share one. NOTE: a run
        # directory with no readable meta at all has no known mode (every job there was audited
        # as failed), so it is written as "mixed" like a directory that holds both modes; the
        # reader does not use this field.
        modes = {fmt[2] for fmt in formats.values() if not isinstance(fmt, str)}
        payload = _manifest_payload(
            model_key, spec, run, entries, tp=tps.pop() if len(tps) == 1 else None,
            instance_type=None, served_model_name=None, post_hoc_audit=True,
            mode=modes.pop() if len(modes) == 1 else "mixed",
            label_added_lines=source.label_added_lines,
            label_answer_tokens=source.label_answer_tokens,
        )
        try:
            report.manifests.append(write_manifest(make_s3(), bucket, run_keys_prefix, payload))
        except Exception as manifest_exc:  # noqa: BLE001 -- recorded, not hidden
            report.manifest_error = f"{type(manifest_exc).__name__}: {manifest_exc}"
            logging.error(
                f"attention_replay: writing the manifest of {run_keys_prefix} failed after "
                f"{len(report.manifests)} were written; no further run is audited: "
                f"{report.manifest_error}"
            )
            return report
        print(
            f"attention_replay: audited {len(candidates)} job(s) of {run_keys_prefix}: "
            f"{sum(1 for item in candidates if outcome[item.job.job_id] is None)} verified"
        )
    return report


# --------------------------------------------------------------- offline reader

#: What ``pull_captures`` copies, relative to ``<prefix>/induction/<model>/``: a capture
#: array or its metadata, or a run manifest, inside ``seed=<s>/<arm>--<stamp>/``. Anything
#: else (a ``_probe/`` object, a stray file) does not match and is left in the bucket.
_PULLED_KEY_RE = re.compile(
    r"^seed=\d+/[^/]+--[^/]+/(?:q\d+\.r\d+\.(?:npz|json)|manifest--[^/]+\.json)$"
)
#: The deduction counterpart, relative to ``<prefix>/deduction/horn/<model>/``: a capture array or
#: its metadata of one cell, or a manifest, inside ``<rung>/<arm>/``. The name classes also admit
#: ``.`` and ``..``; ``_pulled_horn_key_ok`` refuses those two.
_HORN_PULLED_KEY_RE = re.compile(
    r"^([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)/(?:s\d+\.rep\d+\.r\d+\.(?:npz|json)|manifest--[^/]+\.json)$"
)


def _pulled_key_ok(study: str, rest: str) -> bool:
    """Return whether `rest` (a key below the model folder) is one ``pull_captures`` copies.

    Induction: ``_PULLED_KEY_RE``. Deduction: ``_HORN_PULLED_KEY_RE`` with neither the rung nor
    the arm being ``.`` or ``..`` (a path component that would climb out of the mirror).
    """
    if study == "induction":
        return bool(_PULLED_KEY_RE.match(rest))
    match = _HORN_PULLED_KEY_RE.match(rest)
    return bool(match) and not {match.group(1), match.group(2)} & {".", ".."}


def _list_objects(client: Any, bucket: str, prefix: str) -> Iterator[Tuple[str, int]]:
    """Yield ``(key, size)`` of every object under `prefix`, following the listing's pages."""
    token: Optional[str] = None
    while True:
        kwargs: Dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
        if token is not None:
            kwargs["ContinuationToken"] = token
        page = client.list_objects_v2(**kwargs)
        for obj in page.get("Contents") or []:
            yield obj["Key"], int(obj["Size"])
        if not page.get("IsTruncated"):
            return
        token = page["NextContinuationToken"]


def pull_captures(
    s3_uri: str,
    local_root: Path,
    models: Optional[Sequence[str]] = None,
    *,
    s3_client_factory: Optional[Callable[[], Any]] = None,
    study: str = "induction",
) -> int:
    """Copy the captures and manifests of the bucket to a local folder, for ``read_captures``.

    Lists every object under ``<prefix>/induction/<model>/`` (``<prefix>`` is the key
    prefix of `s3_uri`) and downloads those named ``seed=<s>/<arm>--<stamp>/q<i>.r<rank>.npz``,
    ``.../q<i>.r<rank>.json`` or ``.../manifest--*.json``, to the same key path below
    `local_root`. Every other object, such as one under ``_probe/``, is ignored. The
    tree this builds is what ``read_captures`` reads: pass `local_root` as its
    ``mirror_root`` argument (it looks for ``<mirror_root>/induction/<model>/seed=...``).

    With ``study="horn"`` it lists ``<prefix>/deduction/horn/<model>/`` (``<prefix>/deduction/horn/``
    when `models` is ``None``) and downloads the keys ``<rung>/<arm>/s<seed>.rep<rep>.r<rank>.npz``,
    ``.../s<seed>.rep<rep>.r<rank>.json`` and ``<rung>/<arm>/manifest--*.json`` (rung and arm
    made of ``A-Za-z0-9._-``, neither ``.`` nor ``..``) to ``<local_root>/deduction/horn/<model>/...``.

    A local file whose size equals the object's listed size is kept as it is. Any other
    object is written to a temporary name (``<name>.<random>.part``) in the destination
    folder and renamed over the final name, so an interrupted pull never leaves a
    partial file under a final name; the temporary file is removed when the download
    fails. A local file of another size is replaced.

    Parameters
    ----------
    s3_uri : str
        ``s3://<bucket>[/<prefix>]``; normally ``DEFAULT_S3_URI``.
    local_root : Path
        Folder to mirror into; created when absent.
    models : Optional[Sequence[str]], optional
        Roster keys to pull. Default ``None``: every model found under
        ``<prefix>/induction/``.
    s3_client_factory : Optional[Callable[[], Any]], optional
        Returns an S3 client with ``list_objects_v2`` and ``get_object``. Default
        ``_default_s3_factory``.
    study : str, optional
        ``"induction"`` (default) or ``"horn"``. Keyword-only.

    Returns
    -------
    int
        Number of files written (kept files are not counted).

    Raises
    ------
    ValueError
        When `s3_uri` is malformed, `study` is unknown, or a model name is empty, ``.``/``..``,
        or holds ``/``.

    Notes
    -----
    Read-only on the bucket: it calls ``list_objects_v2`` (paginated) and ``get_object``
    only. Needs no approval: nothing is written to S3 and nothing is billed beyond the
    requests and the transfer. Cost is one listing per model (one for all when
    `models` is ``None``) and one GET per file it writes.
    """
    bucket, prefix = parse_s3_uri(s3_uri)
    _check_study(study)
    root = Path(local_root)
    for model in models or ():
        if not model or model in (".", "..") or "/" in model:
            raise ValueError(f"model name {model!r} must be a non-empty name without '/'")
    client = (s3_client_factory or _default_s3_factory)()
    # Design: the two studies differ only in the folder below the prefix and in which keys
    # count, so one listing/copy loop serves both.
    study_dirs = ("induction",) if study == "induction" else ("deduction", "horn")
    study_root = "/".join(part for part in (prefix, *study_dirs) if part) + "/"

    # Phase 1: list. With explicit models, one listing per model prefix; otherwise one
    # listing of the whole study folder, grouped by the model folder in the key.
    listings = [study_root + model + "/" for model in models] if models is not None else [study_root]
    written = 0
    for listing_prefix in listings:
        for key, size in _list_objects(client, bucket, listing_prefix):
            below_root = key[len(study_root):]
            model, _, rest = below_root.partition("/")
            if model in ("", ".", "..") or not _pulled_key_ok(study, rest):
                continue
            # Every component is regex-limited or checked above, so none can climb out of `root`.
            dest = root.joinpath(*study_dirs, *below_root.split("/"))
            # Phase 2: keep a same-size file, else download beside it and rename.
            if dest.is_file() and dest.stat().st_size == size:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(dir=dest.parent, prefix=dest.name + ".", suffix=".part")
            try:
                with os.fdopen(fd, "wb") as out:
                    shutil.copyfileobj(client.get_object(Bucket=bucket, Key=key)["Body"], out)
                # os.replace is atomic on one filesystem, which the same-folder name guarantees.
                os.replace(tmp_name, dest)
            except BaseException:
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(tmp_name)
                raise
            written += 1
    return written


class _MirrorClient:
    """Object client over a local directory: ``get_object`` reads ``<root>/<Key>``."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def get_object(self, Bucket: str, Key: str) -> Dict[str, Any]:  # noqa: N803 -- boto3 names
        """Return ``{"Body": <readable>}`` for a key under the mirror root."""
        return {"Body": io.BytesIO((self._root / Key).read_bytes())}


class _MirrorStore:
    """The ``bucket`` + ``_client()`` surface ``attention_analysis.load_mass`` borrows."""

    bucket = "local-mirror"

    def __init__(self, root: Path) -> None:
        self._root = root

    def _client(self) -> _MirrorClient:
        return _MirrorClient(self._root)


_CAPTURE_FILE_RE = re.compile(r"^q(\d+)\.r(\d+)\.npz$")
#: The deduction counterpart: one rank's array of one cell, ``s<seed>.rep<rep>.r<rank>.npz``.
#: It never matches an induction name, nor does ``_CAPTURE_FILE_RE`` match this one.
_HORN_CAPTURE_FILE_RE = re.compile(r"^s(\d+)\.rep(\d+)\.r(\d+)\.npz$")


def _verified_set(run_dir: Path, extract: Callable[[Mapping[str, Any]], Any]) -> set:
    """Return ``extract(entry)`` of every ``verified`` entry of every ``manifest--*.json`` in `run_dir`.

    Raises
    ------
    ValueError
        When a manifest is not valid JSON or lacks the ``jobs`` entries
        ``_write_manifests`` writes, or an entry lacks what `extract` reads (the reader must
        not guess what a manifest holds).
    """
    verified: set = set()
    for path in sorted(run_dir.glob("manifest--*.json")):
        try:
            for entry in json.loads(path.read_text())["jobs"]:
                if entry["status"] == "verified":
                    verified.add(extract(entry))
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"{path}: unreadable manifest: {exc!r}") from exc
    return verified


def _verified_marks(run_dir: Path) -> set:
    """Return the mark indices some ``manifest--*.json`` in `run_dir` records as verified.

    Raises
    ------
    ValueError
        When a manifest is not valid JSON or lacks the ``jobs`` entries
        ``_write_manifests`` writes (the reader must not guess what it holds).
    """
    return _verified_set(run_dir, lambda entry: int(entry["mark_index"]))


def _verified_job_ids(arm_dir: Path) -> set:
    """Return the job ids some ``manifest--*.json`` in the deduction folder `arm_dir` records as verified.

    Raises
    ------
    ValueError
        As for ``_verified_marks``.
    """
    return _verified_set(arm_dir, lambda entry: str(entry["job_id"]))


#: The two entropy statistics ``read_captures`` summarises, in output order.
_ENTROPY_STATS: Tuple[str, ...] = ("prompt_entropy", "entropy")


def _pool_layers(mean: np.ndarray, count: np.ndarray, select: Optional[np.ndarray]) -> float:
    """Pool per-layer means into one mean exactly: ``sum(mean * count) / sum(count)``.

    Only layers in `select` (all layers when ``None``) with ``count > 0`` take part.
    NaN when no layer does. Weighting by the defined-value counts makes the result
    equal to the plain mean of every defined value of those layers.
    """
    keep = count > 0
    if select is not None:
        keep = keep & select
    if not keep.any():
        return float("nan")
    return float((mean[keep] * count[keep]).sum() / count[keep].sum())


def _mean_sd_over_jobs(values: Sequence[float]) -> Tuple[float, int, float]:
    """Return ``(mean, number of defined jobs, sample sd)`` of per-job values, skipping NaN.

    The mean is NaN with no defined job; the sd (ddof=1) is NaN with fewer than two.
    NaN values are filtered first, so no all-NaN reduction (and no RuntimeWarning) occurs.
    """
    defined = np.asarray([v for v in values if not np.isnan(v)], dtype=np.float64)
    if defined.size == 0:
        return float("nan"), 0, float("nan")
    sd = float(defined.std(ddof=1)) if defined.size >= 2 else float("nan")
    return float(defined.mean()), int(defined.size), sd


class _ArmStats:
    """Running reduction of one arm's loaded captures, shared by both studies of ``read_captures``.

    ``add`` takes one loaded job (``attention_analysis.load_capture``) and folds it in;
    ``result`` returns the arm's statistics dict. Design: one accumulator for both studies,
    so a statistic is computed by one code path whatever tree the captures came from.
    """

    def __init__(self) -> None:
        self.sums: Optional[np.ndarray] = None
        self.counts: Optional[np.ndarray] = None
        self.n_jobs = 0
        self.pad_total = 0
        self.n_skipped = 0
        # Per statistic, one entry per job: the job's all-layer, global-layer and
        # window-layer means, and its [L] per-layer means (see _pool_layers).
        self.per_job: Dict[str, Dict[str, List[Any]]] = {
            stat: {"all": [], "global": [], "window": [], "layer": []} for stat in _ENTROPY_STATS
        }
        self.n_v1 = 0
        self.n_summary = 0
        #: ``<folder>/<stem>`` of every job, in the order of the ``per_job`` entries.
        self.labels: List[str] = []
        # Per job, same order: the [4] mean attention mass by class over all layers and over
        # the global layers, and the pad ratio pooled over the job's own defined rows.
        self.mass_per_job: Dict[str, List[np.ndarray]] = {"all": [], "global": []}
        self.ratio_per_job: Dict[str, List[float]] = {"all": [], "global": []}
        # Per job, same order: the [3] mean contribution of prompt classes 0, 1, 2 to the prompt
        # entropy over all layers and over the global layers (NaN for a job without the split).
        self.by_class_per_job: Dict[str, List[np.ndarray]] = {"all": [], "global": []}
        #: Jobs that carry ``sum_prompt_entropy_by_class`` (summary captures of version 4).
        self.n_by_class = 0
        # Per job, same order: the prompt entropy over the ANSWER rows (class-4 tokens), all
        # layers and global layers, and its [3] class split (NaN where not available).
        self.answer_per_job: Dict[str, List[float]] = {"all": [], "global": []}
        self.answer_by_class_per_job: Dict[str, List[np.ndarray]] = {"all": [], "global": []}
        #: Jobs with answer rows the reduction could read (summary: version 4 with
        #: ``rows_answer > 0``; mass: class 4 in ``classes`` and a ``prompt_entropy`` array).
        self.n_answer = 0

    def add(self, job: Mapping[str, Any], label: str, expected_heads: int, tp: int) -> None:
        """Fold one loaded job into the arm.

        Parameters
        ----------
        job : Mapping[str, Any]
            A ``load_capture`` result, mass or summary.
        label : str
            Where the job came from (``<folder>/<stem>``), for error messages.
        expected_heads : int
            The config's head count; the joined job must hold exactly that many.
        tp : int
            Number of rank files the job was joined from, for the error message.

        Raises
        ------
        ValueError
            When the joined job's head count differs from `expected_heads` (a rank is
            missing), or its (layers, heads) shape differs from the arm's earlier jobs.
        """
        is_summary = job["kind"] == "summary"
        # The head axis is axis 2 of the mass arrays [L, P, H, 4] and axis 1 of
        # the summary arrays [L, H]; sum_entropy stands for the summary arrays.
        heads_read = np.shape(job["sum_entropy"])[1] if is_summary else job["mass"].shape[2]
        if heads_read != expected_heads:
            raise ValueError(
                f"{label}: the {tp} rank(s) hold {heads_read} heads in "
                f"total, the config has {expected_heads}; a rank is missing"
            )
        # Design: the per-(layer, head) pad-ratio sum and defined-row count come from
        # attention_analysis.pad_ratio_sums for both kinds. A summary job already holds
        # them (summed on the box); a mass job reduces its rows to the same two arrays.
        # Either way the arm pools sums and counts, so the two kinds mix freely.
        job_sums, job_counts = attention_analysis.pad_ratio_sums(job)
        layers, heads = job_sums.shape
        if self.sums is None:
            self.sums = np.zeros((layers, heads), dtype=np.float64)
            self.counts = np.zeros((layers, heads), dtype=np.int64)
        elif self.sums.shape != (layers, heads):
            raise ValueError(
                f"{label}: shape (L={layers}, H={heads}) differs from the arm's {self.sums.shape}"
            )
        self.sums += job_sums
        self.counts += job_counts  # type: ignore[operator]
        # Entropy means of this job: its own pooled defined values per layer set.
        # A summary job is reduced to ITS OWN means here, before the average over
        # jobs in result(): rows are never pooled across jobs, whichever kind a job is.
        by_layer = attention_analysis.entropy_by_layer(job)
        window = job.get("sliding_window")
        is_global = None if window is None else np.asarray(window) == 0
        is_window = None if window is None else np.asarray(window) > 0
        for stat in _ENTROPY_STATS:
            mean_l, count_l = by_layer[stat], by_layer[f"{stat}_count"]
            self.per_job[stat]["all"].append(_pool_layers(mean_l, count_l, None))
            self.per_job[stat]["global"].append(
                float("nan") if is_global is None else _pool_layers(mean_l, count_l, is_global)
            )
            self.per_job[stat]["window"].append(
                float("nan") if is_window is None else _pool_layers(mean_l, count_l, is_window)
            )
            self.per_job[stat]["layer"].append(mean_l)
        # Mass by class and pad ratio per job. Design: a missing sliding_window array means no
        # windowed layer, so every layer is global here (unlike the entropy's global mean,
        # which stays NaN without the array, as it always has).
        layer_global = np.ones(layers, dtype=bool) if is_global is None else is_global
        layer_mass = _job_layer_mass(job)
        for name, select in (("all", None), ("global", layer_global)):
            chosen = layer_mass if select is None else layer_mass[select]
            self.mass_per_job[name].append(
                chosen.mean(axis=0) if chosen.shape[0] else np.full(4, np.nan)
            )
            rows_sum = job_sums if select is None else job_sums[select]
            rows_n = int((job_counts if select is None else job_counts[select]).sum())
            self.ratio_per_job[name].append(float(rows_sum.sum() / rows_n) if rows_n else float("nan"))
        # Prompt entropy by class, pooled like the job's prompt-entropy mean (_pool_layers over the
        # layers with a defined value): the class sums over the chosen layers and heads divided by
        # the same defined-row count, so the three add up to that job's prompt_entropy value.
        by_class = job.get(attention.SUMMARY_BY_CLASS_ARRAY) if is_summary else None
        if by_class is not None:
            self.n_by_class += 1
            class_totals = np.asarray(by_class, dtype=np.float64).sum(axis=1)  # [L, 3]
            pe_counts = np.asarray(by_layer["prompt_entropy_count"], dtype=np.int64)  # [L]
        for name, select in (("all", None), ("global", is_global)):
            triple = np.full(attention.N_PROMPT_CLASSES, np.nan)
            if by_class is not None and not (name == "global" and select is None):
                keep = pe_counts > 0
                if select is not None:
                    keep = keep & select
                if keep.any():
                    triple = class_totals[keep].sum(axis=0) / pe_counts[keep].sum()
            self.by_class_per_job[name].append(triple)
        # Answer rows: the same pooling as the prompt-entropy mean, over the answer rows only.
        has_answer = "prompt_entropy_answer" in by_layer
        if has_answer:
            self.n_answer += 1
            a_mean, a_count = by_layer["prompt_entropy_answer"], by_layer["prompt_entropy_answer_count"]
        a_split = by_layer.get("prompt_entropy_by_class_answer")
        for name, select in (("all", None), ("global", is_global)):
            value = float("nan")
            triple = np.full(attention.N_PROMPT_CLASSES, np.nan)
            if has_answer and not (name == "global" and select is None):
                value = _pool_layers(a_mean, a_count, select)
                keep = a_count > 0
                if select is not None:
                    keep = keep & select
                if a_split is not None and keep.any():
                    # a_split is the per-layer class mean over a_count rows: weight it back.
                    triple = (a_split[keep] * a_count[keep][:, None]).sum(axis=0) / a_count[keep].sum()
            self.answer_per_job[name].append(value)
            self.answer_by_class_per_job[name].append(triple)
        if is_summary:
            self.n_summary += 1
        elif job.get("prompt_entropy") is None:
            self.n_v1 += 1
        self.n_jobs += 1
        self.labels.append(label)
        self.pad_total += int((np.asarray(job["classes"]) == attention_analysis.PAD_CLASS).sum())

    def result(self) -> Optional[Dict[str, Any]]:
        """Return the arm's statistics (the per-arm value of ``read_captures``), or ``None`` with no job."""
        if self.n_jobs == 0 or self.sums is None or self.counts is None:
            return None  # nothing read; any skips were already logged per folder
        # nan, not 0, where no query had a defined baseline (no pad token anywhere);
        # np.divide with ``where`` never emits a divide warning.
        layer_head = np.full(self.sums.shape, np.nan, dtype=np.float64)
        np.divide(self.sums, self.counts, out=layer_head, where=self.counts > 0)
        total = int(self.counts.sum())
        out: Dict[str, Any] = {
            "jobs": self.n_jobs,
            "pad_tokens_mean": self.pad_total / self.n_jobs,
            "ratio_mean": float(self.sums.sum() / total) if total else float("nan"),
            "ratio_layer_head": layer_head,
            "skipped_unverified": self.n_skipped,
            "prompt_entropy_v1_jobs": self.n_v1,
            "summary_jobs": self.n_summary,
            # One label per job, in the order of the ``<stat>_per_job`` lists below.
            "job_labels": list(self.labels),
        }
        # Every job counts once: mean over a job's positions, heads and layers first,
        # then over jobs (the footnote's "mean per response"), not over pooled rows.
        for stat in _ENTROPY_STATS:
            jobs_stat = self.per_job[stat]
            mean, n_defined, sd = _mean_sd_over_jobs(jobs_stat["all"])
            out[f"{stat}_mean"] = mean
            out[f"{stat}_global_mean"] = _mean_sd_over_jobs(jobs_stat["global"])[0]
            out[f"{stat}_window_mean"] = _mean_sd_over_jobs(jobs_stat["window"])[0]
            stacked = np.vstack(jobs_stat["layer"])  # [jobs, L]
            defined = ~np.isnan(stacked)
            layer_mean = np.full(stacked.shape[1], np.nan, dtype=np.float64)
            np.divide(
                np.where(defined, stacked, 0.0).sum(axis=0), defined.sum(axis=0),
                out=layer_mean, where=defined.any(axis=0),
            )
            out[f"{stat}_layer"] = layer_mean
            out[f"{stat}_jobs"] = n_defined
            out[f"{stat}_sd"] = sd
            # The per-job means behind the two means above (NaN where undefined), for
            # resampling (see ``entropy_ci``).
            out[f"{stat}_per_job"] = [float(v) for v in jobs_stat["all"]]
            out[f"{stat}_global_per_job"] = [float(v) for v in jobs_stat["global"]]
        # Mass by class: each job's own mean first, then the mean over jobs (NaN jobs skipped
        # per class), like the entropy means.
        for name, key in (("all", "mass_mean"), ("global", "mass_global_mean")):
            stacked = np.vstack(self.mass_per_job[name])  # [jobs, 4]
            defined = ~np.isnan(stacked)
            mean = np.full(stacked.shape[1], np.nan, dtype=np.float64)
            np.divide(
                np.where(defined, stacked, 0.0).sum(axis=0), defined.sum(axis=0),
                out=mean, where=defined.any(axis=0),
            )
            out[key] = mean
        out["ratio_per_job"] = list(self.ratio_per_job["all"])
        out["ratio_global_per_job"] = list(self.ratio_per_job["global"])
        # The class split of the prompt entropy, only for an arm with at least one job that
        # carries it (capture version 4); an arm of earlier captures keeps its key set. Per job
        # first, then over the jobs that have a defined triple, per class.
        if self.n_by_class:
            out["prompt_entropy_by_class_jobs"] = self.n_by_class
            for name, per_job_key, mean_key in (
                ("all", "prompt_entropy_by_class_per_job", "prompt_entropy_by_class_mean"),
                ("global", "prompt_entropy_by_class_global_per_job", "prompt_entropy_by_class_global_mean"),
            ):
                stacked = np.vstack(self.by_class_per_job[name])  # [jobs, 3]
                out[per_job_key] = [[float(v) for v in row] for row in stacked]
                defined = ~np.isnan(stacked)
                mean = np.full(stacked.shape[1], np.nan, dtype=np.float64)
                np.divide(
                    np.where(defined, stacked, 0.0).sum(axis=0), defined.sum(axis=0),
                    out=mean, where=defined.any(axis=0),
                )
                out[mean_key] = mean
        # The prompt entropy over the answer rows (class-4 tokens), only for an arm with at least
        # one job that labels them; mass and summary jobs mix (the class split is summary only).
        if self.n_answer:
            mean, n_defined, _sd = _mean_sd_over_jobs(self.answer_per_job["all"])
            out["prompt_entropy_answer_per_job"] = [float(v) for v in self.answer_per_job["all"]]
            out["prompt_entropy_answer_global_per_job"] = [float(v) for v in self.answer_per_job["global"]]
            out["prompt_entropy_answer_mean"] = mean
            out["prompt_entropy_answer_global_mean"] = _mean_sd_over_jobs(self.answer_per_job["global"])[0]
            out["prompt_entropy_answer_jobs"] = n_defined
            for name, per_job_key, mean_key in (
                ("all", "prompt_entropy_by_class_answer_per_job", "prompt_entropy_by_class_answer_mean"),
                ("global", "prompt_entropy_by_class_answer_global_per_job",
                 "prompt_entropy_by_class_answer_global_mean"),
            ):
                stacked = np.vstack(self.answer_by_class_per_job[name])  # [jobs, 3]
                out[per_job_key] = [[float(v) for v in row] for row in stacked]
                defined = ~np.isnan(stacked)
                class_mean = np.full(stacked.shape[1], np.nan, dtype=np.float64)
                np.divide(
                    np.where(defined, stacked, 0.0).sum(axis=0), defined.sum(axis=0),
                    out=class_mean, where=defined.any(axis=0),
                )
                out[mean_key] = class_mean
        return out


def _job_layer_mass(job: Mapping[str, Any]) -> np.ndarray:
    """Return one job's mean attention mass per key class and layer, ``[L, 4]`` float64.

    A mass job averages ``mass`` (``[L, P, H, 4]``, cast to float64 first) over its rows and
    heads (accumulated in float64); a summary job divides ``sum_mass`` (``[L, H, 4]``, summed over the rows) by
    ``rows`` and averages over heads. Both give the mean over the job's (row, head) pairs per
    layer, and every layer has the same number of them, so a plain mean over layers is the
    job's pooled mean. NaN (``[L, 4]``) for a job with no response row.
    """
    if job.get("kind") == "summary":
        sum_mass = np.asarray(job["sum_mass"], dtype=np.float64)
        rows = int(job["rows"])
        if rows == 0:
            return np.full((sum_mass.shape[0], sum_mass.shape[-1]), np.nan)
        return (sum_mass / rows).mean(axis=1)
    mass = np.asarray(job["mass"])
    if mass.shape[1] == 0 or mass.shape[2] == 0:
        return np.full((mass.shape[0], mass.shape[-1]), np.nan)
    # float64 accumulation without a float64 copy of the whole array.
    return mass.mean(axis=(1, 2), dtype=np.float64)


#: The seed in a job label: ``.../seed=<s>/<arm>--<stamp>/q<i>`` (induction) or
#: ``.../<arm>/s<seed>.rep<rep>`` (deduction).
_LABEL_SEED = re.compile(r"/seed=(\d+)/[^/]+/[^/]+$|/s(\d+)\.rep\d+$")


def job_seed(label: str) -> int:
    """Return the seed of a job from its ``job_labels`` entry.

    Parameters
    ----------
    label : str
        ``<folder>/<stem>`` as ``read_captures`` reports it.

    Returns
    -------
    int
        The induction seed, or the deduction theory seed.

    Raises
    ------
    ValueError
        When `label` has neither form.
    """
    match = _LABEL_SEED.search(label)
    if match is None:
        raise ValueError(f"no seed in job label {label!r}")
    return int(match.group(1) if match.group(1) is not None else match.group(2))


def entropy_ci(
    stats: Mapping[str, Any],
    *,
    stat: str = "prompt_entropy",
    layers: str = "all",
    n_boot: int = 10_000,
    level: float = 0.95,
    seed: int = 0,
) -> Tuple[float, float, float, int, int]:
    """Bootstrap a confidence interval for one arm's mean entropy, resampling seeds.

    The point estimate is the mean over responses (``<stat>_mean`` of ``read_captures``).
    Responses of one seed share their context (induction: the 9 questions of a replicate;
    deduction: the replicates of a theory), so they are not independent. Each bootstrap
    draw therefore resamples whole seeds with replacement and takes the mean over the
    responses of the drawn seeds. The interval is the percentile interval of the draws.

    Parameters
    ----------
    stats : Mapping[str, Any]
        One arm's value from ``read_captures`` or ``read_entropy_table``.
    stat : str, optional
        ``"prompt_entropy"`` or ``"entropy"``.
    layers : str, optional
        ``"all"`` for every attention layer, ``"global"`` for global-attention layers only.
    n_boot : int, optional
        Number of bootstrap draws.
    level : float, optional
        Coverage of the interval, between 0 and 1.
    seed : int, optional
        Seed of the resampling generator, so that the interval is reproducible.

    Returns
    -------
    Tuple[float, float, float, int, int]
        ``(mean, lower, upper, number of responses, number of seeds)``. The three numbers
        are NaN when no response has a defined value.

    Raises
    ------
    ValueError
        When `stat` or `layers` is unknown, `n_boot` is below 1, or `level` is not
        strictly between 0 and 1.
    """
    if stat not in _ENTROPY_STATS:
        raise ValueError(f"stat={stat!r}: expected one of {_ENTROPY_STATS}")
    if layers not in ("all", "global"):
        raise ValueError(f"layers={layers!r}: expected 'all' or 'global'")
    if n_boot < 1 or not 0.0 < level < 1.0:
        raise ValueError(f"n_boot={n_boot}, level={level}: need n_boot >= 1 and 0 < level < 1")
    values = np.asarray(stats[f"{stat}_per_job" if layers == "all" else f"{stat}_global_per_job"], dtype=np.float64)
    seeds = np.asarray([job_seed(label) for label in stats["job_labels"]], dtype=np.int64)
    keep = ~np.isnan(values)
    values, seeds = values[keep], seeds[keep]
    if values.size == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    # Per seed: the sum and the number of its responses. A draw of seeds then has the
    # mean sum(sums) / sum(counts), the mean over the responses it holds.
    _unique, index = np.unique(seeds, return_inverse=True)
    sums = np.bincount(index, weights=values)
    counts = np.bincount(index).astype(np.float64)
    draws = np.random.default_rng(seed).integers(0, sums.size, size=(n_boot, sums.size))
    means = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    tail = (1.0 - level) / 2.0
    lower, upper = np.quantile(means, [tail, 1.0 - tail])
    return float(values.mean()), float(lower), float(upper), int(values.size), int(sums.size)


#: One folder to read: ``(folder, [(file stem, ranks present)], verified stems or None for all)``.
_ReadUnit = Tuple[Path, List[Tuple[str, set]], Optional[set]]


def _induction_units(base: Path, arm: str, require_verified: bool) -> Iterator[_ReadUnit]:
    """Yield the run folders of `arm` under ``base`` (``<mirror>/induction/<model>``) to read.

    Several ``<arm>--<stamp>`` folders under one ``seed=<s>`` are re-collections of the same
    arm. As in ``find_runs``, only the folder with the lexicographically smallest stamp
    is read; later ones are logged at INFO. The mirror has no ``.superseded`` markers, so
    that clause of ``find_runs`` does not apply. Units are ``q<idx>`` stems in index order;
    `verified` holds the stems of the marks a manifest records as verified.
    """
    # Earliest wins, per seed and arm: the folders of one seed are
    # re-collections of the same arm, and the released results count the first.
    stamp_prefix = f"{arm}--"
    by_seed: Dict[Path, List[Path]] = {}
    for candidate in base.glob(f"seed=*/{stamp_prefix}*"):
        if candidate.is_dir():
            by_seed.setdefault(candidate.parent, []).append(candidate)
    for seed_dir in sorted(by_seed):
        ordered = sorted(by_seed[seed_dir], key=lambda d: d.name[len(stamp_prefix):])
        run_dir = ordered[0]
        for later in ordered[1:]:
            logging.info(
                f"attention_replay: ignoring {later}: an earlier {arm} run of "
                f"{seed_dir.name} exists ({ordered[0].name})"
            )
        ranks: Dict[int, set] = {}
        for path in run_dir.iterdir():
            match = _CAPTURE_FILE_RE.match(path.name)
            if match:
                ranks.setdefault(int(match.group(1)), set()).add(int(match.group(2)))
        verified = {f"q{i}" for i in _verified_marks(run_dir)} if require_verified else None
        yield run_dir, [(f"q{i}", ranks[i]) for i in sorted(ranks)], verified


def _horn_units(rung_dir: Path, arm: str, require_verified: bool) -> Iterator[_ReadUnit]:
    """Yield the one folder of `arm` under the deduction rung folder `rung_dir`, when it exists.

    Units are ``s<seed>.rep<rep>`` stems in (seed, rep) order. `verified` holds the stems whose
    job id (``horn.<rung>.<arm>.s<seed>.rep<rep>``) some manifest in the folder records as
    verified. Unlike induction there is no earliest-run rule here: the selection of one row
    per cell was made when the jobs were planned, and a cell has one key.
    """
    arm_dir = rung_dir / arm
    if not arm_dir.is_dir():
        return
    ranks: Dict[Tuple[int, int], Tuple[str, set]] = {}
    for path in arm_dir.iterdir():
        match = _HORN_CAPTURE_FILE_RE.match(path.name)
        if match:
            stem = f"s{match.group(1)}.rep{match.group(2)}"
            ranks.setdefault((int(match.group(1)), int(match.group(2))), (stem, set()))[1].add(int(match.group(3)))
    verified: Optional[set] = None
    if require_verified:
        ids = _verified_job_ids(arm_dir)
        verified = {
            stem for (seed, rep), (stem, _r) in ranks.items()
            if _horn_job_id(rung_dir.name, arm, seed, rep) in ids
        }
    yield arm_dir, [ranks[k] for k in sorted(ranks)], verified


def _read_unit(
    stats: _ArmStats, store: Any, mirror_root: Path, unit: _ReadUnit, expected_heads: int
) -> None:
    """Load every verified job of one folder into `stats`.

    A job no manifest records as verified is skipped, counted in ``stats.n_skipped`` and
    reported with one WARNING per folder. The ranks present for a job must be exactly
    ``0..tp-1``.

    Raises
    ------
    ValueError
        When a job's ranks are not exactly ``0..tp-1`` (``tp`` = the number of rank files), or
        ``_ArmStats.add`` refuses the job.
    """
    run_dir, units, verified = unit
    rel = run_dir.relative_to(mirror_root).as_posix() + "/"
    unverified = [stem for stem, _ranks in units if verified is not None and stem not in verified]
    if unverified:
        stats.n_skipped += len(unverified)
        logging.warning(
            f"attention_replay: {run_dir}: skipping {len(unverified)} job(s) no manifest "
            f"records as verified: {', '.join(unverified)}"
        )
    for stem, rank_set in units:
        if stem in unverified:
            continue
        tp = len(rank_set)
        if rank_set != set(range(tp)):
            raise ValueError(f"{run_dir}/{stem}: ranks {sorted(rank_set)} are not exactly 0..{tp - 1}")
        job = attention_analysis.load_capture(store, rel, stem, tp)
        stats.add(job, f"{run_dir}/{stem}", expected_heads, tp)


def read_captures(
    model_key: str,
    mirror_root: Path,
    *,
    study: str = "induction",
    arms: Optional[Sequence[str]] = None,
    rung: Optional[str] = None,
    config: Optional[Mapping[str, Any]] = None,
    require_verified: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """Compute the pad-mass ratio and the attention entropies per arm from a local mirror.

    Offline, no AWS. ``mirror_root`` holds a copy of the S3 tree under the prefix::

        <mirror_root>/induction/<model>/seed=<s>/<arm>--<stamp>/q<idx>.r<rank>.npz
        <mirror_root>/deduction/horn/<model>/<rung>/<arm>/s<seed>.rep<rep>.r<rank>.npz

    (``pull_captures`` builds it; the first line is read for ``study="induction"``, the
    second for ``study="horn"``.) Files are grouped per run directory and ``q<idx>``
    (deduction: per ``<rung>/<arm>`` folder and ``s<seed>.rep<rep>``); ``tp`` is the number of
    rank files, which must be exactly ranks ``0..tp-1``. Each job is loaded with
    ``attention_analysis.load_capture`` (ranks joined head-wise in rank order; the job
    is a mass or a summary capture, as its ``kind`` says) and reduced with
    ``attention_analysis.pad_ratio_sums`` and ``attention_analysis.entropy_by_layer``,
    which give the same numbers from either kind. Mass and summary jobs can be mixed
    within one arm. The ranks present must
    also be the WHOLE set: the head axis of the joined job (axis 2 of ``mass``, axis 1
    of ``sum_entropy``) must equal the
    config's head count, because ranks ``0..6`` of an 8-way job are a valid
    ``0..tp-1`` set for ``tp = 7`` and a missing top rank would otherwise pass. Both
    studies run the same per-job reduction (``_ArmStats``).

    Induction: several ``<arm>--<stamp>`` directories under one ``seed=<s>`` are re-collections
    of the same arm. As in ``find_runs``, only the directory with the
    lexicographically smallest stamp (the part after ``<arm>--``) is read; later
    ones are ignored and logged at INFO. The mirror has no ``.superseded``
    markers, so that clause of ``find_runs`` does not apply.

    By default a job is read only when some ``manifest--<stamp>.json`` in its run
    directory (written by ``_write_manifests``, mirrored with the captures) lists
    it with ``status == "verified"``: induction by ``mark_index``, deduction by
    ``job_id`` (``horn.<rung>.<arm>.s<seed>.rep<rep>``). A capture the audit
    rejected (``audit_failed: ...``), one whose upload failed, and one with no
    manifest at all is skipped, counted, and reported with one WARNING per run
    directory. `require_verified` ``False`` reads every capture file instead.

    Parameters
    ----------
    model_key : str
        Roster key.
    mirror_root : Path
        Root of the local mirror.
    study : str, optional
        ``"induction"`` (default) or ``"horn"``. Keyword-only, like every argument below.
    arms : Optional[Sequence[str]], optional
        Arms to read (deduction: folder names made of ``A-Za-z0-9._-``, else ``ValueError``).
        ``None`` (default): induction reads ``ARMS``; deduction reads every
        arm folder found, in ``bt.HORN_ARMS`` order and then the others sorted.
    rung : Optional[str], optional
        Deduction only: the rung folder to read (e.g. ``"m64"``). ``None`` (default) takes
        the only rung folder of the model, or reads nothing when there is none.
    config : Mapping[str, Any], optional
        Parsed ``config.json`` of the model, for the expected head count
        (``attention_shape``). Defaults to ``load_model_config(model_key)``, which
        may download the file when the vendored copy does not apply.
    require_verified : bool, optional
        Read only jobs a manifest records as verified (default ``True``). Pass
        ``False`` to read every capture file regardless of the manifests.

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Per arm with at least one capture: ``jobs`` (count), ``pad_tokens_mean``
        (mean class-1 token count per job), ``ratio_mean`` (mean over every query,
        layer, head and job that has a defined ratio) and ``ratio_layer_head``
        (``[L, H]`` array, mean over queries and jobs). Queries are pooled, so
        longer completions weigh more (a summary job contributes its summed ratios and
        its defined-row counts, which pools exactly the same rows). An arm without any pad token has an
        undefined ratio: ``nan``, not 0; a deduction arm captured with the default classes is
        such an arm (no class-1 token, ``pad_tokens_mean`` 0), while a padded deduction arm
        captured with ``label_added_lines`` has its added lines as class 1 and so a defined
        ratio. ``skipped_unverified`` counts the jobs of
        the arm left unread because no manifest records them as verified (always 0
        with ``require_verified=False``). An arm whose every job was skipped has no
        entry, as an arm without captures has none; its skips are in the WARNINGs.

        For each statistic ``s`` in ``prompt_entropy`` (entropy in nats of a
        response row's attention over the prompt keys only, renormalised, sink
        excluded; defined only where a prompt key is attendable) and ``entropy``
        (the whole-row entropy), every job is first reduced to its own means by
        pooling the job's defined values exactly (``sum(mean_l * count_l) /
        sum(count_l)`` over the chosen layers with ``count_l > 0``), so every job
        weighs the same whatever its length ("mean per response"):

        ``<s>_mean``
            Float. Mean over jobs of the job's all-layer mean; NaN jobs skipped, NaN
            when no job is defined.
        ``<s>_global_mean``, ``<s>_window_mean``
            Float. The same over the job's global layers (``sliding_window == 0``)
            and over its sliding-window layers (``sliding_window > 0``). A job
            without a ``sliding_window`` array contributes NaN to both. NaN when no
            job is defined.
        ``<s>_layer``
            ``[L]`` float64. Per layer, the mean over jobs of the job's per-layer
            mean; NaN jobs skipped, NaN for a layer no job defines.
        ``<s>_jobs``
            Int. Jobs with a defined all-layer mean.
        ``<s>_sd``
            Float. Sample standard deviation (ddof=1) over those jobs' all-layer
            means; NaN with fewer than two.

        ``prompt_entropy_v1_jobs`` (int) counts the arm's MASS jobs read from a
        version-1 capture, which has no ``prompt_entropy`` array: they give NaN
        prompt-entropy values, are left out of the ``prompt_entropy_*`` means and
        counts, and never raise. Their ``entropy`` is still read. A summary job
        always carries its prompt-entropy sums and is never counted here.

        ``summary_jobs`` (int) counts the arm's jobs read from a summary capture
        (0 when every job is a mass capture). The statistics above are the same for a
        capture read in either mode, up to the float16 rounding that mass mode stores
        and summary mode does not. A summary job is first reduced to its own means
        (sums divided by counts, then pooled over layers as above) and only then
        averaged over jobs: rows are never pooled across jobs, so a long response does
        not outweigh a short one in either mode.

        The attention mass by key class (0 informative prompt, 1 pad, 2 template and
        other whitespace, 3 response), also mean per response first:

        ``mass_mean``
            ``[4]`` float64. Per job, the mean class mass over its response rows, heads
            and layers (mass: ``mass`` averaged; summary: ``sum_mass / rows`` averaged
            over heads and layers); then the mean over jobs, per class, NaN jobs skipped.
        ``mass_global_mean``
            ``[4]`` float64. The same over the global-attention layers only
            (``sliding_window == 0``; a job without a ``sliding_window`` array has no
            windowed layer, so every layer counts). Equal to ``mass_mean`` for a model
            without sliding-window layers; NaN for a class when no job has a global layer.

        For resampling (as ``entropy_ci`` resamples the entropies), in the order of
        ``job_labels``:

        ``ratio_per_job``, ``ratio_global_per_job``
            List of floats. Per job, the pad ratio pooled over its own defined (row,
            head, layer) values (summary: ``sum_pad_ratio`` over ``n_pad_ratio``), over
            all layers and over the global layers (same rule as ``mass_global_mean``);
            NaN where the job has no defined value (no class-1 token).

        The prompt entropy split by prompt key class (0 informative, 1 pad or added lines,
        2 template), only for an arm with at least one job that carries it (a summary
        capture of version 4); an arm of earlier captures has none of these keys. Mass jobs
        and version-3 summary jobs of a mixed arm count as jobs without it:

        ``prompt_entropy_by_class_per_job``, ``prompt_entropy_by_class_global_per_job``
            List (in ``job_labels`` order) of ``[3]`` lists of floats. Per job, the mean
            contribution of each class, pooled exactly like that job's
            ``prompt_entropy_per_job`` / ``prompt_entropy_global_per_job`` value (the class
            sums over the chosen layers and heads divided by the same defined-row count), so
            the three add up to it (up to the capture's float32 summation order). NaN triples
            for a job without the split or with no defined value (and for the global form, a
            job without a ``sliding_window`` array).
        ``prompt_entropy_by_class_mean``, ``prompt_entropy_by_class_global_mean``
            ``[3]`` float64. Per class, the mean over the jobs with a defined triple.
        ``prompt_entropy_by_class_jobs``
            Int. Jobs of the arm that carry the split.

        The prompt entropy over the ANSWER rows only (rows whose own token is class 4, the
        response after the reasoning), only for an arm with at least one job that labels them
        (a version-4 summary job with ``rows_answer > 0``, or a mass job whose ``classes``
        holds class 4); jobs without answer rows give NaN:

        ``prompt_entropy_answer_per_job``, ``prompt_entropy_answer_global_per_job``
            List of floats (``job_labels`` order). Per job, the mean over its answer rows,
            heads and layers (all layers / global layers), pooled like ``prompt_entropy``
            (summary: ``sum_prompt_entropy_answer`` over ``n_prompt_entropy_answer``; mass: the
            per-row ``prompt_entropy`` of the class-4 rows).
        ``prompt_entropy_answer_mean``, ``prompt_entropy_answer_global_mean``
            Float. Mean over the jobs with a defined value.
        ``prompt_entropy_answer_jobs``
            Int. Jobs with a defined all-layer answer value.
        ``prompt_entropy_by_class_answer_per_job``, ``prompt_entropy_by_class_answer_global_per_job``, ``prompt_entropy_by_class_answer_mean``, ``prompt_entropy_by_class_answer_global_mean``
            The class split over the answer rows, per job (``[3]`` lists) and as ``[3]``
            means, as for ``prompt_entropy_by_class_*``; NaN for mass jobs (no split there).

    Raises
    ------
    ValueError
        When the ranks of a job are not exactly ``0..tp-1``, when the joined
        job's head count differs from the config's (a rank is missing), or when
        jobs of one arm differ in layer or head count; also when `config` has no
        readable attention shape, `study` is unknown, `rung` is given for the induction
        study or is not a folder name, or (deduction, `rung` ``None``) the model has more than
        one rung folder (the message says "rung": pass one).
    """
    _check_study(study)
    mirror = Path(mirror_root)
    if study == "induction" and rung is not None:
        raise ValueError("rung applies only to study='horn'")
    if rung is not None and not _horn_name_ok(rung):
        raise ValueError(f"rung {rung!r} is not a folder name made of [A-Za-z0-9._-]")
    if study == "horn" and arms is not None:
        # An arm name becomes a path component below, so a name that could climb out is refused.
        bad_arms = [arm for arm in arms if not _horn_name_ok(arm)]
        if bad_arms:
            raise ValueError(f"arms {bad_arms!r} are not folder names made of [A-Za-z0-9._-]")
    store = _MirrorStore(mirror)
    if config is None:
        config = load_model_config(model_key)
    expected_heads = attention_shape(config)[1]

    # Phase 1: find what to read. Only the discovery differs by study; the reduction below is shared.
    units_of: Callable[[str], Iterator[_ReadUnit]]
    if study == "induction":
        base = mirror / "induction" / model_key
        arm_list = list(arms) if arms is not None else list(ARMS)

        def units_of(arm: str) -> Iterator[_ReadUnit]:
            return _induction_units(base, arm, require_verified)
    else:
        base = mirror / "deduction" / "horn" / model_key
        if rung is None:
            rungs = sorted((d.name for d in base.iterdir() if d.is_dir()), key=_natural_key) if base.is_dir() else []
            if len(rungs) > 1:
                raise ValueError(f"{base} holds several rung folders {rungs}; pass rung= to choose one")
            rung = rungs[0] if rungs else None
        if rung is None or not (base / rung).is_dir():
            return {}
        rung_dir = base / rung
        if arms is not None:
            arm_list = list(arms)
        else:
            found = {d.name for d in rung_dir.iterdir() if d.is_dir()}
            arm_list = [a for a in bt.HORN_ARMS if a in found] + sorted(found - set(bt.HORN_ARMS))

        def units_of(arm: str) -> Iterator[_ReadUnit]:
            return _horn_units(rung_dir, arm, require_verified)

    # Phase 2: reduce every arm's verified jobs with one accumulator per arm.
    out: Dict[str, Dict[str, Any]] = {}
    for arm in arm_list:
        stats = _ArmStats()
        for unit in units_of(arm):
            _read_unit(stats, store, mirror, unit, expected_heads)
        arm_result = stats.result()
        if arm_result is not None:
            out[arm] = arm_result
    return out


def read_entropy_table(
    model_key: str,
    mirror_root: Path,
    *,
    config: Optional[Mapping[str, Any]] = None,
    require_verified: bool = True,
    rung: Optional[str] = None,
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Return the per-arm statistics of both studies in one table, keyed ``(study, arm)``.

    The union of ``read_captures(study="induction")`` and ``read_captures(study="horn")`` over
    the same mirror: every value is the dict ``read_captures`` returns for that arm, so the
    entropy statistics of the two studies are directly comparable. A study with no tree in the
    mirror (or with nothing verified) contributes no entries. Induction entries come first.

    Parameters
    ----------
    model_key : str
        Roster key.
    mirror_root : Path
        Root of the local mirror (see ``pull_captures``).
    config : Mapping[str, Any], optional
        Parsed ``config.json``; loaded once with ``load_model_config`` when ``None``.
    require_verified : bool, optional
        As for ``read_captures``.
    rung : Optional[str], optional
        The deduction rung to read (see ``read_captures``); induction has none.

    Returns
    -------
    Dict[Tuple[str, str], Dict[str, Any]]
        ``(study, arm) -> statistics``; ``study`` is ``"induction"`` or ``"horn"``.

    Raises
    ------
    ValueError
        As for ``read_captures``; in particular a deduction tree with several rung folders and
        ``rung=None``.
    """
    if config is None:
        config = load_model_config(model_key)  # once, not once per study
    table: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for study in STUDIES:
        stats = read_captures(
            model_key, mirror_root, study=study, config=config, require_verified=require_verified,
            rung=rung if study == "horn" else None,
        )
        for arm, value in stats.items():
            table[(study, arm)] = value
    return table
