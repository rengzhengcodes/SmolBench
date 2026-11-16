"""Replay the rebuttal's stored induction transcripts through an open-weights attention capture.

The rebuttal collected the three induction arms (``intens``, ``noise_intens``,
``extens``) from three hosted models and stored, per mark, only text: the
query, the reasoning, the response. Those hosted models expose no attention.
This module asks what the same text looks like to the matching open-weights
checkpoint: it rebuilds each mark's token sequence, sends it to a spot GPU box
running the vLLM attention-capture plugin (``smolbench.evals.attention`` is the
store-agnostic client half), and keeps the per-class attention mass arrays in
a private S3 bucket. The offline reader (``read_captures``) then computes the
pad-mass ratio the noise arm is about.

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
4. ``read_captures``: offline, over a local mirror of the S3 tree.

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
   end-of-turn token it never emitted.
5. The conversation is one user turn with no system message, matching the
   collection harness. Server-side defaults the harness did not send (a system
   prompt, guardrails, sampling settings) are not represented.
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
   undefined ratio (reported as nan).
8. Tokens that straddle the edge of the query (template text merged into the
   query's first or last token) take the full token text as their piece. The
   template tokens next to the query are class 2, never class 0.
9. When a seed and arm has more than one stored run, only the earliest run
   (lexicographic minimum of the stamp) is replayed, as in the released-results
   reader. Marks of later runs are never captured.
10. ``bedrock_token_counts`` is always ``None``: the stored marks carry no usage
    field, so the rebuilt length cannot be compared with the length the hosted
    service counted.

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

Spending money needs an explicit decision. ``replay_model`` raises
``ApprovalRequired`` unless ``approved is True`` (the singleton; ``1`` and
``"yes"`` are refused) and does so before any EC2 or S3 client exists. The
provider's own spend guards stay in force: the idle watchdog from the default
provisioning arguments, the lifetime backstop, and termination in a
``finally`` block.

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
excluded as over-context, in the plan and in the run.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import logging
import numbers
import os
import re
import signal
import shutil
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, FrozenSet, Iterator, List, Mapping, Optional, Sequence, Tuple

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
    "ChatTemplate",
    "DEFAULT_RESULTS_ROOT",
    "DEFAULT_S3_URI",
    "EC2_TAG",
    "run_tag",
    "INSTANCE_TYPES",
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
    "rebuild_sequence",
    "replay_model",
    "run_prefix",
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
    "and capped generations get an end-of-turn token they never emitted",
    "5. one user turn, no system message; server-side defaults are not represented",
    "6. the capture runs the pinned open-weights checkpoint on EC2, teacher-forced on the stored "
    "completion, not the hosted service's computation",
    "7. the pad class is found by rule for noise_intens (longest whitespace run of at least "
    f"{attention.MIN_PAD_RUN_CHARS} characters in the query) and by construction for "
    "related_intens (added rule lines and trailing whitespace, located from the intens query)",
    "8. tokens straddling the query edge take their full token text as their piece",
    "9. only the earliest stored run per seed and arm is replayed",
    "10. bedrock_token_counts is None: the stored marks carry no usage field",
)

#: Message when the plan cannot say how big the capture is.
_BEDROCK_COUNTS_NOTE: str = "not stored in the marks; no comparison possible"

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
#: Capture format the shipped plugin writes; version 2 added ``prompt_entropy``. New
#: captures come from the plugin in this repository, so the audit requires it.
CAPTURE_VERSION: int = 2

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


def rebuild_sequence(
    query: str,
    reasoning: Optional[str],
    response: str,
    *,
    tokenizer: Any,
    template: Any,
    fmt: ReasoningFormat,
    pad_query_span: Optional[Tuple[int, int]] = None,
) -> Rebuilt:
    """Rebuild one mark's prompt ids, completion ids and key classes from its stored text.

    Steps. (1) Render the generation prompt of a single user turn holding
    `query`, with thinking on, and find the query inside it. (2) Build the
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
    straddle an edge.

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

    Returns
    -------
    Rebuilt
        The sequence. ``len(classes) == len(prompt_ids) + len(completion_ids)``.

    Raises
    ------
    TemplateMismatch
        When the query is empty or is not found in the rendered prompt, or (with
        `pad_query_span`) when it occurs more than once there.
    ValueError
        When `pad_query_span` is not ``0 <= start <= end <= len(query)``, or when
        the tokens that overlap the query do not tile it without gaps or overlaps,
        so the span cannot be mapped to piece coordinates.
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

    # Phase 1: render the prompt and locate the query in it.
    prompt_text = template.render(
        messages=[{"role": "user", "content": query}],
        add_generation_prompt=True,
        **fmt.template_kwargs,
    )
    if not query.strip():
        raise TemplateMismatch("the stored query is empty or whitespace-only")
    located = query
    q_start = prompt_text.find(located)
    if q_start < 0:
        located = query.strip()
        q_start = prompt_text.find(located)
        if q_start < 0:
            raise TemplateMismatch("the rendered prompt does not contain the stored query")
        notes.append("template stripped the query")
    q_end = q_start + len(located)
    if pad_query_span is not None and prompt_text.count(located) != 1:
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
    if pad_query_span is not None:
        pad_span, n_straddle = _pad_span_in_pieces(
            offsets, pieces, pad_query_span, query, located, q_start
        )
    classes = attention.token_classes(
        prompt_ids, completion_ids, lambda ids: pieces, pad_span=pad_span
    )
    if pad_query_span is not None:
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


def _seed_set(seeds: Optional[Sequence[int]]) -> Optional[FrozenSet[int]]:
    """Return `seeds` as a frozen set, or ``None`` (every seed) when `seeds` is ``None``.

    An empty sequence stays an empty set: it selects no run, which is not the same
    as ``None``. A string or a bool is refused so that ``seeds="01"`` or
    ``seeds=[True]`` cannot silently select nothing or seed 1.

    Raises
    ------
    ValueError
        When an entry is not an integer.
    """
    if seeds is None:
        return None
    chosen = set()
    for seed in seeds:
        if isinstance(seed, bool) or not isinstance(seed, numbers.Integral):
            raise ValueError(f"seeds must be integers, got {seed!r}")
        chosen.add(int(seed))
    return frozenset(chosen)


def run_prefix(s3_prefix: str, run: Run) -> str:
    """Return the key prefix (trailing ``/``) holding one run's captures.

    Parameters
    ----------
    s3_prefix : str
        Key prefix above ``induction/`` (no bucket); may be empty.
    run : Run
        The stored run.

    Returns
    -------
    str
        ``<s3_prefix>/induction/<model>/seed=<seed>/<arm>--<stamp>/``.

    Examples
    --------
    >>> r = Run("m", 3, "intens", "2026-01-01T00:00:00Z", Path("x.yaml"))
    >>> run_prefix("a/b", r)
    'a/b/induction/m/seed=3/intens--2026-01-01T00:00:00Z/'
    """
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


@dataclass(frozen=True)
class PlannedJob:
    """A capture job plus where it came from."""

    job: attention.Job
    run: Run
    mark_index: int
    notes: Tuple[str, ...]
    #: Always ``None``: the stored marks carry no token counts, so the rebuilt
    #: length cannot be compared with the hosted service's (approximation 10).
    bedrock_token_counts: None = None


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


def _related_pad_span(intens_query: str, related_query: str) -> Tuple[int, int]:
    """Return the pad range of a ``related_intens`` query, by comparison with its ``intens`` query.

    The related query is the intens query up to the end of the real rule lines
    (its ``head``, everything before ``bt.QUESTION_START``), then added rule
    lines and a few whitespace characters, then the question. The pad is
    everything between the head and the LAST ``QUESTION_START`` of the related
    query (the same split ``bedrock_trio.check_related_prompts`` uses).

    Parameters
    ----------
    intens_query : str
        The ``intens`` query of the same seed and question.
    related_query : str
        The ``related_intens`` query.

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
        raise ValueError("the related_intens query does not start with the intens query's rules")
    end = related_query.rfind(bt.QUESTION_START)
    if end < len(head):
        raise ValueError(f"the related_intens query has no {bt.QUESTION_START!r} after the rules")
    if end == len(head):
        raise ValueError("the related_intens query has an empty pad (nothing between rules and question)")
    return len(head), end


@dataclass
class _Built:
    """Internal result of reading and rebuilding every run of one model."""

    runs: List[Run] = field(default_factory=list)
    marks: int = 0
    unreasoned: int = 0
    planned: List[PlannedJob] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _build(
    model: str,
    results_root: Path,
    s3_prefix: str,
    get_tokenizer: Callable[[], Any],
    get_template: Callable[[], Any],
    fmt: Optional[ReasoningFormat],
    seeds: Optional[FrozenSet[int]] = None,
) -> _Built:
    """Read the runs of `model` and rebuild every mark (shared by ``build_jobs`` and the plan).

    Tokenizer and template are fetched through callables on first need, so a model
    with no result files never touches the hub. When `seeds` is given only the runs
    of those seeds are read; the filter is applied before ``run_of`` is built, and
    a ``related_intens`` run looks up its ``intens`` run of the SAME seed, so the
    pairing survives the filter.
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
                if run.arm == RELATED_ARM:
                    base = base_queries(run.seed)
                    if base is None:
                        raise ValueError(
                            f"no {RELATED_BASE_ARM} run for seed {run.seed}; "
                            "cannot locate the pad of a related_intens mark"
                        )
                    if idx >= len(base):
                        raise ValueError(
                            f"question {idx} is missing from the {RELATED_BASE_ARM} run "
                            f"({len(base)} questions); cannot locate the pad"
                        )
                    pad_span = _related_pad_span(base[idx], mark.query)
                rebuilt = rebuild_sequence(
                    mark.query, mark.reasoning, mark.response,
                    tokenizer=tokenizer, template=template, fmt=fmt, pad_query_span=pad_span,
                )
                if not checked:
                    # Once per model: a wrong delimiter table is wrong for every
                    # mark, so it must stop the model, not fill the error list.
                    check_reasoning_format(model, tokenizer, rebuilt.prompt_text, fmt=fmt)
                    checked = True
                job = attention.mass_job(
                    job_id_for(run, idx), rebuilt.prompt_ids, rebuilt.completion_ids,
                    rebuilt.classes, prefix + f"q{idx}.npz",
                )
            except (ValueError, jinja2.exceptions.TemplateError) as exc:
                if isinstance(exc, ReasoningFormatError):
                    raise
                built.errors.append(f"{run.path}#q{idx}: {exc}")
                continue
            built.planned.append(PlannedJob(job, run, idx, rebuilt.notes))
    return built


def build_jobs(
    model: str,
    results_root: Path,
    s3_prefix: str,
    *,
    tokenizer: Any = None,
    template: Any = None,
    fmt: Optional[ReasoningFormat] = None,
) -> Tuple[List[PlannedJob], List[str]]:
    """Rebuild every stored mark of `model` into a capture job, offline.

    Never builds an S3 or EC2 client. The reasoning format is checked once, on the
    first successfully rendered prompt.

    Parameters
    ----------
    model : str
        Roster key.
    results_root : Path
        Folder holding ``induction/<model>/...`` (see ``find_runs``).
    s3_prefix : str
        Key prefix above ``induction/`` (no bucket).
    tokenizer : Any, optional
        Defaults to ``tokenization.for_model(model)``.
    template : Any, optional
        Defaults to ``load_chat_template(model)``.
    fmt : ReasoningFormat, optional
        Defaults to ``REASONING_FORMATS[model]``.

    Returns
    -------
    Tuple[List[PlannedJob], List[str]]
        The jobs, in run order then mark order, and one ``"<path>#q<idx>: <error>"``
        line per mark that could not be rebuilt. No mark is dropped silently. The
        ``bedrock_token_counts`` of every job is ``None`` because the stored marks
        carry no token counts.

    Raises
    ------
    TemplateUnavailable
        When the template or tokenizer cannot be loaded (only when there are runs).
    ReasoningFormatError
        When the delimiters fail validation: every mark would be wrong the same way.
    """
    built = _build(
        model, Path(results_root), s3_prefix,
        (lambda: tokenizer) if tokenizer is not None else (lambda: _default_tokenizer(model)),
        (lambda: template) if template is not None else (lambda: load_chat_template(model)),
        fmt,
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
    #: Stored runs found (one per seed and arm).
    runs: int
    #: Marks read from those runs.
    marks: int
    #: Marks rebuilt into jobs.
    jobs: int
    #: Marks with no stored reasoning.
    unreasoned_marks: int
    #: Per-mark and per-model rebuild failures.
    errors: List[str]
    #: Per arm: ``marks`` (rebuilt), ``total_tokens``, ``max_tokens`` and
    #: ``over_context`` (jobs above the capture context, so excluded from the capture).
    #: Per arm because exclusions that differ by arm would bias a mean over responses.
    per_arm: Dict[str, Dict[str, int]]
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

    def summary(self) -> str:
        """Return a short multi-line description of the plan.

        Returns
        -------
        str
            Counts, token sizes, capture support, instance types and the labelled
            storage estimate.
        """
        lines = [
            f"{self.model}: {self.runs} runs, {self.marks} marks -> {self.jobs} jobs "
            f"({self.unreasoned_marks} marks without stored reasoning), {len(self.errors)} errors",
            f"  tokens: total {self.total_tokens}, longest {self.max_tokens}; "
            f"{self.over_context} job(s) over the {self.capture_max_model_len}-token capture "
            "context (excluded)",
        ]
        for arm, stats in self.per_arm.items():
            lines.append(
                f"  arm {arm}: {stats['marks']} jobs, {stats['total_tokens']} tokens, "
                f"longest {stats['max_tokens']}, {stats['over_context']} over the "
                f"{self.capture_max_model_len}-token capture context"
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
    planned: Sequence[PlannedJob], config: Optional[Mapping[str, Any]], tp: Optional[int], source: str
) -> Tuple[Optional[int], str]:
    """Return ``(estimated capture bytes, est_basis)`` for the capturable `planned` jobs."""
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
    total = 0
    for item in planned:
        job = item.job
        queries = job.n_tokens - int(job.query_start)  # type: ignore[arg-type]
        total += layers * queries * heads * (4 + 1 + 1 + 1) * 2 + tp * job.n_tokens
    return total, f"{formula}; layers={layers}, heads={heads}, tp={tp}; config: {source}"


def _plan_one(
    model: str,
    results_root: Path,
    s3_prefix: str,
    tokenizer_for: Optional[Callable[[str], Any]],
    template_for: Optional[Callable[[str], Any]],
    config_for: Optional[Callable[[str], Mapping[str, Any]]],
    seeds: Optional[Sequence[int]] = None,
) -> Tuple[ReplayPlan, List[PlannedJob]]:
    """Build one model's plan and its planned jobs (no AWS access).

    `seeds` restricts the plan to the runs of those seeds (``None`` = every seed), so
    every count, token total and the storage estimate cover only them.
    """
    from smolbench.evals.providers import ec2

    wanted = _seed_set(seeds)
    spec = ec2.EC2_DEPLOY_SPECS[model]
    get_tokenizer = (lambda: tokenizer_for(model)) if tokenizer_for else (lambda: _default_tokenizer(model))
    get_template = (lambda: template_for(model)) if template_for else (lambda: load_chat_template(model))
    runs = [r for r in find_runs(results_root, model) if wanted is None or r.seed in wanted]
    try:
        built = _build(model, results_root, s3_prefix, get_tokenizer, get_template, None, wanted)
    except (TemplateUnavailable, ReasoningFormatError) as exc:
        # One model's missing template must not stop the other models' plans.
        built = _Built(runs=runs, errors=[f"{model}: {exc} (marks not counted)"])

    max_len = capture_max_model_len(model, spec)
    capturable = [p for p in built.planned if p.job.n_tokens <= max_len]
    per_arm: Dict[str, Dict[str, int]] = {}
    for arm in ARMS:
        sizes = [p.job.n_tokens for p in built.planned if p.run.arm == arm]
        per_arm[arm] = {
            "marks": len(sizes), "total_tokens": sum(sizes), "max_tokens": max(sizes, default=0),
            "over_context": sum(1 for size in sizes if size > max_len),
        }

    instance_types = tuple(INSTANCE_TYPES.get(model, ()))
    tp = ec2.derive_tp(model, instance_types[0], spec) if instance_types else None
    config: Optional[Mapping[str, Any]]
    try:
        if config_for is not None:
            config, source = config_for(model), "injected config"
        else:
            config, source = _load_model_config_with_source(model)
    except (TemplateUnavailable, OSError, ValueError) as exc:
        config, source = None, f"config unavailable: {exc}"
    est_bytes, est_basis = _estimate_bytes(capturable, config, tp, source)

    sizes_all = [p.job.n_tokens for p in built.planned]
    plan = ReplayPlan(
        model=model,
        runs=len(built.runs),
        marks=built.marks,
        jobs=len(built.planned),
        unreasoned_marks=built.unreasoned,
        errors=list(built.errors),
        per_arm=per_arm,
        total_tokens=sum(sizes_all),
        max_tokens=max(sizes_all, default=0),
        over_context=len(built.planned) - len(capturable),
        instance_types=instance_types,
        tp_estimate=tp,
        capture_supported=model not in CAPTURE_UNSUPPORTED,
        unsupported_reason=CAPTURE_UNSUPPORTED.get(model),
        serve_verified=model not in SERVE_UNVERIFIED,
        serve_unverified_reason=SERVE_UNVERIFIED.get(model),
        capture_max_model_len=max_len,
        est_capture_bytes=est_bytes,
        est_basis=est_basis,
    )
    return plan, built.planned


def plan_replay(
    results_root: Path = DEFAULT_RESULTS_ROOT,
    models: Optional[Sequence[str]] = None,
    *,
    s3_uri: str = DEFAULT_S3_URI,
    tokenizer_for: Optional[Callable[[str], Any]] = None,
    template_for: Optional[Callable[[str], Any]] = None,
    config_for: Optional[Callable[[str], Mapping[str, Any]]] = None,
    seeds: Optional[Sequence[int]] = None,
) -> Dict[str, ReplayPlan]:
    """Plan the replay of each model: sizes, errors and a storage estimate. No AWS access.

    Parameters
    ----------
    results_root : Path, optional
        Folder holding ``induction/<model>/...`` (see ``find_runs``).
    models : Sequence[str], optional
        Roster keys; defaults to the three keys of ``bedrock_trio.TRIO``.
    s3_uri : str, optional
        Destination URI; only its key prefix is used, to name the jobs.
    tokenizer_for, template_for, config_for : Callable, optional
        ``model -> object`` overrides of the pinned tokenizer, chat template and
        ``config.json`` (tests and offline use).
    seeds : Sequence[int], optional
        Plan only the runs of these seeds; every count, token total, per-arm number
        and the storage estimate then cover only them. ``None`` (default) plans every
        seed. An empty sequence selects no run, so every plan has zero marks.

    Returns
    -------
    Dict[str, ReplayPlan]
        One plan per model. A model with no result files gets a plan with zero
        marks. A ``TemplateUnavailable`` or ``ReasoningFormatError`` for one model
        is recorded in that plan's ``errors`` (with ``jobs == 0``), so the other
        models still plan.

    Raises
    ------
    ValueError
        When `s3_uri` is malformed or `seeds` holds a non-integer.
    KeyError
        When a model has no deploy spec.
    """
    _bucket, prefix = parse_s3_uri(s3_uri)
    root = Path(results_root)
    return {
        model: _plan_one(model, root, prefix, tokenizer_for, template_for, config_for, seeds)[0]
        for model in (list(models) if models is not None else list(bt.TRIO))
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
) -> Optional[str]:
    """Audit every rank of one job; return the first failure reason, or ``None``.

    Meta checks run in a fixed order (see ``audit_captures``); the first failing
    check of the first failing rank is the reason. A missing meta key is reported
    as a mismatch against ``None``, not as a crash. A failing meta check returns at
    once; an array failure is held until every rank's arrays have been read.
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
        if meta.get("mode") != "mass":
            return f"rank {rank}: meta mode {meta.get('mode')!r} is not 'mass'"
        # A meta without the field is a version-1 capture (written before the field existed).
        rank_version = int(meta.get("capture_version", 1))
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
        size = _object_size(client, bucket, npz_key)
        if size != int(meta["bytes"]):
            return f"rank {rank}: npz size {size} != meta bytes {meta['bytes']}"
        if sampled:
            body = client.get_object(Bucket=bucket, Key=npz_key)["Body"].read()
            loaded = np.load(io.BytesIO(body))
            failure, shape = _audit_arrays(loaded, job, n_layers, heads_local, rank_version)
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
                mass = np.asarray(loaded["mass"])
                if mass.size and mass.any():
                    digest = hashlib.sha256(
                        str(mass.shape).encode() + str(mass.dtype).encode() + mass.tobytes()
                    ).digest()
                    if digest in digests and duplicate is None:
                        duplicate = f"rank {rank} duplicates rank {digests[digest]}: identical mass arrays"
                    digests.setdefault(digest, rank)
    if array_failure:
        return array_failure
    if duplicate:
        return duplicate
    if len(shapes) > 1:
        return f"ranks disagree about the (L, P) shape: {sorted(shapes)}"
    return None


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
    capture_version: Optional[int] = None,
    workers: int = 1,
    client_factory: Optional[Callable[[], Any]] = None,
) -> Dict[str, Optional[str]]:
    """Audit captured objects by content; file counts prove nothing.

    With ``L, H = attention_shape(config)`` and ``H_local = H // tp``, for EVERY
    job and rank the meta json is read and checked, in this order (the first
    failure is the job's reason, each prefixed ``rank <r>: ``): ``job_id`` equals
    the job's; ``rank`` equals the rank read; ``model`` equals `model`;
    ``n_tokens`` and ``query_start`` equal the job's; ``mode == "mass"``; the meta's
    capture version (``capture_version``, 1 when the field is absent) equals the
    `capture_version` argument, when that is not ``None``; ``len(layers) == L``; ``num_heads_local == H_local``; ``rows_shape ==
    [L, P, H_local, 4]`` with ``P = n_tokens - query_start``; ``gate_max_rel <=
    gate_tol``; and ``bytes`` equals the npz object's real size (``head_object``
    when the client has it, else the listing's ``Size``). A missing meta key is a
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

    A rank whose meta is version 2 or later (``capture_version >= 2``) is checked
    further, after every check above passes. Its npz must hold ``prompt_entropy``
    (the entropy of each response row over the prompt keys ``[0, query_start)``,
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
    capture_version : Optional[int], optional
        Capture format every rank's meta must declare (``None``, the default,
        accepts any version and audits each rank by its own). ``replay_model``
        passes ``CAPTURE_VERSION``.
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
        When `arrays` is not ``"sample"`` or ``"all"``, when `workers` is not an
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
                use, bucket, job, tp, sampled, model, n_layers, n_heads, capture_version
            )
        except Exception as exc:  # noqa: BLE001 -- recorded per job, none hidden
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


def run_tag(model_key: str, run_label: Optional[str] = None) -> str:
    """Return the EC2 experiment tag of one replay run.

    The tag names the model and, when given, a label, so that runs of different models (or
    two runs of one model over different seeds) each provision and terminate their own
    box. The state file is named after the tag.

    Parameters
    ----------
    model_key : str
        Roster key.
    run_label : Optional[str]
        Distinguishes concurrent runs of one model, for example ``"s0-14"``.

    Returns
    -------
    str
        ``EC2_TAG-<model>[-<label>]`` with every character outside ``A-Za-z0-9._-``
        replaced by ``-``.

    Examples
    --------
    >>> run_tag("gemma-4-31b")
    'smolbench-rebuttal-attention-gemma-4-31b'
    >>> run_tag("deepseek-v3.1", "s0-14")
    'smolbench-rebuttal-attention-deepseek-v3.1-s0-14'
    """
    parts = [EC2_TAG, model_key] + ([run_label] if run_label else [])
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
) -> ReplayReport:
    """Capture one model's stored induction transcripts on one spot box. BILLED.

    Order of events. (1) Build the plan and jobs offline and print the launch
    summary. (2) Refuse unless ``approved is True``. (3) Refuse a model in
    ``CAPTURE_UNSUPPORTED`` unless overridden, then one in ``SERVE_UNVERIFIED``
    unless overridden. (4) Skip every job that already has
    a key in the bucket (never re-sent, never overwritten); when nothing remains,
    return without provisioning. (5) Provision one box, serve the checkpoint in
    capture mode and run the batches. (6) Terminate the box, however the batches
    ended. (7) Only after the shutdown call, and only when the batches returned,
    audit the uploads by content and write one manifest per run that had jobs
    sent: both need only S3, and the audit downloads every array to this machine
    (about 3.5 minutes per GB in a pilot), so running it before the shutdown
    would leave the box idle and billed. (8) When the shutdown call failed on the
    success path, raise ``ShutdownFailed`` carrying the finished report.

    Parameters
    ----------
    model_key : str
        Roster key; needs a deploy spec and an ``INSTANCE_TYPES`` entry (or
        `instance_types`).
    results_root : Path, optional
        Folder holding ``induction/<model>/...`` (see ``find_runs``).
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
        Replay only the runs of these seeds, to split a model across several
        sessions. The plan, the jobs sent and the manifests cover only them; skipped
        and over-context counts too. ``None`` (default) means every seed; an empty
        sequence selects no run, so nothing is sent and no box is provisioned.
    run_label : str, optional
        Distinguishes concurrent runs of one model; part of the instance tag and of the
        state file name (see ``run_tag``).
    ec2 : Any, optional
        Provider module or fake; defaults to ``smolbench.evals.providers.ec2``.
    s3_client_factory : Callable[[], Any], optional
        Returns a NEW S3 client per call; defaults to a fresh boto3 client in ``REGION``.

    Returns
    -------
    ReplayReport
        Verified, failed, skipped and audit-failed job ids, manifests written and the plan.

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
        invalid, `audit_workers` is below 1, or `seeds` holds a non-integer (before
        any AWS call).
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

    A failure while writing the manifests does not lose the report: it is recorded
    in ``ReplayReport.manifest_error``, logged at ERROR, the manifests written so
    far stay in ``ReplayReport.manifests`` and the report is returned. An
    exception raised by the audit itself (not a failed job) propagates, as the
    box is already down; with a failed shutdown it is logged and ``ShutdownFailed``
    is raised instead.
    """
    # Phase 1: offline plan and the launch summary, shown before the gate.
    from smolbench.evals.providers import ec2 as real_ec2

    _bucket_for_plan, plan_prefix = parse_s3_uri(s3_uri)
    plan, planned = _plan_one(
        model_key, Path(results_root), plan_prefix, tokenizer_for, template_for, config_for, seeds
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
    max_len = capture_max_model_len(model_key, spec)
    report = ReplayReport(model_key, None, None, None, plan=plan)
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
    expected_tp = plan.tp_estimate
    client = make_s3()
    remaining: List[attention.Job] = []
    for job in candidates:
        present = attention.job_keys_present(client, bucket, job)
        if not present:
            remaining.append(job)
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
    tag = run_tag(model_key, run_label)
    with _scoped_env(
        EC2_EXPERIMENT_TAG=tag, EC2_STATE_FILE=str(STATE_DIR / f".ec2_state--{tag}.json")
    ):
        try:
            state = ec2.provision_spot_instance(instance_types=types)
            report.instance_type = state["instance_type"]
            tp = ec2.derive_tp(model_key, state["instance_type"], spec)
            report.tp = tp
            with ec2.serve_model(
                model_key, capture=True, max_model_len=CAPTURE_MAX_MODEL_LEN.get(model_key)
            ) as served:
                report.served_model_name = served
                result = attention.run_capture_batches(
                    ec2, state, served, remaining, tp, make_s3, bucket, mode="mass",
                    batch_size=batch_size, url_ttl_s=url_ttl_s, poll_s=poll_s,
                    batch_timeout_s=batch_timeout_s,
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
    try:
        report.failed.update(result.failed)
        for job_id, keys in result.skipped_existing.items():
            report.skipped_existing[job_id] = keys
        verified_set = set(result.verified)
        audit = audit_captures(
            make_s3(), bucket, [j for j in remaining if j.job_id in verified_set], tp,
            model=model_key, config=config, arrays=audit_arrays,
            capture_version=CAPTURE_VERSION, workers=audit_workers, client_factory=make_s3,
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
                make_s3(), bucket, prefix, model_key, spec, planned, report, result, tp
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
    """Group `planned` by stored run (seed, arm, stamp), keeping the planned order of both levels."""
    by_run: Dict[Tuple[int, str, str], List[PlannedJob]] = {}
    for item in planned:
        by_run.setdefault((item.run.seed, item.run.arm, item.run.stamp), []).append(item)
    return list(by_run.values())


def _manifest_entry(item: PlannedJob, status: str, gate_max_rel: Any) -> Dict[str, Any]:
    """Return the manifest's per-job entry (the shape ``read_captures`` reads)."""
    return {
        "job_id": item.job.job_id,
        "mark_index": item.mark_index,
        "n_tokens": item.job.n_tokens,
        "query_start": item.job.query_start,
        "status": status,
        "gate_max_rel": gate_max_rel,
        "notes": list(item.notes),
    }


def _manifest_payload(
    model: str,
    spec: Mapping[str, Any],
    run: Run,
    entries: List[Dict[str, Any]],
    *,
    tp: Optional[int],
    instance_type: Optional[str],
    served_model_name: Optional[str],
    post_hoc_audit: bool = False,
) -> Dict[str, Any]:
    """Return the manifest content of one run; shared by ``_write_manifests`` and ``audit_existing``.

    ``post_hoc_audit`` adds the key ``"post_hoc_audit": True``; it is absent otherwise,
    so a manifest written at capture time is unchanged.
    """
    payload: Dict[str, Any] = {
        "model": model,
        "run": {
            "seed": run.seed, "arm": run.arm, "stamp": run.stamp, "source_file": run.path.name,
        },
        "tp": tp,
        "instance_type": instance_type,
        "served_model_name": served_model_name,
        "hf_repo": spec["hf_model_id"],
        "hf_revision": tokenization._pinned_revision(spec),
        "capture": attention.CAPTURE_MARKER,
        "mode": "mass",
        "jobs": entries,
        "approximations": list(APPROXIMATIONS),
        "bedrock_token_counts": None,
    }
    if post_hoc_audit:
        payload["post_hoc_audit"] = True
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
) -> List[str]:
    """Write one manifest per run that had at least one job sent in this invocation.

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
            served_model_name=report.served_model_name,
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


def _rank0_tp_and_version(client: Any, bucket: str, job: attention.Job) -> Tuple[int, int]:
    """Return ``(tp, capture_version)`` from the job's rank-0 meta json.

    A meta without ``capture_version`` is a version-1 capture.

    Raises
    ------
    ValueError
        When the meta is not valid JSON, is not an object, or has no ``tp`` that is an
        integer of at least 1, or its ``capture_version`` is not an integer.
    """
    meta_key = attention.rank_keys(job.key, 0)[1]
    try:
        meta = json.loads(client.get_object(Bucket=bucket, Key=meta_key)["Body"].read().decode())
        tp = meta["tp"]
        version = meta.get("capture_version", 1)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"unreadable rank-0 meta {meta_key}: {exc!r}") from exc
    for name, value, floor in (("tp", tp, 1), ("capture_version", version, 1)):
        if isinstance(value, bool) or not isinstance(value, int) or value < floor:
            raise ValueError(f"rank-0 meta {meta_key}: {name} {value!r} is not an integer >= {floor}")
    return tp, version


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
) -> ReplayReport:
    """Audit the captures of one model that are already in the bucket, and manifest them.

    ``replay_model`` audits what it just captured, but an audit that outlives the AWS
    session dies before any manifest is written, and a later ``replay_model`` skips
    those jobs because their keys exist. This function audits them afterwards. It reads
    and writes S3 only: it has no EC2 parameter and starts nothing.

    Steps. (1) Plan the jobs offline as ``replay_model`` does (same job ids and keys).
    (2) For each stored run, list its keys once and classify every planned job: no key
    is *not captured* (counted in ``report.not_captured``); some but not all of the
    expected rank objects is *partial* (``report.partial``, logged, not audited); the
    rest are candidates. The expected rank count is the ``tp`` in the job's rank-0 meta
    json; when the plan's ``tp_estimate`` differs, the meta wins and the log says so.
    (3) A candidate that a manifest already records as audited (``verified`` or
    ``audit_failed: ...``) is skipped (``report.skipped_existing``). (4) The others are
    audited with ``audit_captures``, per run directory, and as soon as one directory is
    done its manifest is written (``write_manifest``, never overwriting) and its key is
    added to ``report.manifests``, so an interrupted call is resumed by calling it again.

    Parameters
    ----------
    model_key : str
        Roster key; needs a deploy spec.
    results_root : Path, optional
        Folder holding ``induction/<model>/...`` (see ``find_runs``); gives the planned jobs.
    s3_uri : str, optional
        ``s3://bucket/prefix`` where the captures are.
    seeds : Sequence[int], optional
        Only the runs of these seeds (see ``plan_replay``); ``None`` is every seed.
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

    Returns
    -------
    ReplayReport
        ``verified`` and ``audit_failures`` of this call, ``skipped_existing`` (job id ->
        keys, for the candidates a manifest already records), ``partial``,
        ``not_captured``, ``manifests`` and ``manifest_error``; ``instance_type`` stays
        ``None``. A manifest written here holds only the jobs this call audited and carries
        ``"post_hoc_audit": true``.

    Raises
    ------
    ValueError
        When `arrays` or `workers` is invalid, `s3_uri` is malformed, `seeds` holds a
        non-integer, or an existing manifest is unreadable (before any audit starts).
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
    plan, planned = _plan_one(
        model_key, Path(results_root), prefix, tokenizer_for, template_for, config_for, seeds
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
    # (run, planned jobs to audit, {job id: (tp, capture_version) or the reason it has none})
    work: List[Tuple[Run, List[PlannedJob], Dict[str, Any]]] = []
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
            if attention.rank_keys(job.key, 0)[1] in present:
                try:
                    tp, version = _rank0_tp_and_version(client, bucket, job)
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
            formats[job.job_id] = (tp, version)
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
        # audit_captures takes one tp and one capture version per call, so group by them
        # (a run is normally one group; a re-capture under another plugin would be two).
        groups: Dict[Tuple[int, int], List[attention.Job]] = {}
        for item in candidates:
            fmt = formats[item.job.job_id]
            if isinstance(fmt, str):
                outcome[item.job.job_id] = fmt
            else:
                groups.setdefault(fmt, []).append(item.job)
        for (tp, version), jobs in groups.items():
            outcome.update(audit_captures(
                make_s3(), bucket, jobs, tp, model=model_key, config=config, arrays=arrays,
                capture_version=version, workers=workers, client_factory=make_s3,
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
        payload = _manifest_payload(
            model_key, spec, run, entries, tp=tps.pop() if len(tps) == 1 else None,
            instance_type=None, served_model_name=None, post_hoc_audit=True,
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
) -> int:
    """Copy the captures and manifests of the bucket to a local folder, for ``read_captures``.

    Lists every object under ``<prefix>/induction/<model>/`` (``<prefix>`` is the key
    prefix of `s3_uri`) and downloads those named ``seed=<s>/<arm>--<stamp>/q<i>.r<rank>.npz``,
    ``.../q<i>.r<rank>.json`` or ``.../manifest--*.json``, to the same key path below
    `local_root`. Every other object, such as one under ``_probe/``, is ignored. The
    tree this builds is what ``read_captures`` reads: pass `local_root` as its
    ``mirror_root`` argument (it looks for ``<mirror_root>/induction/<model>/seed=...``).

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

    Returns
    -------
    int
        Number of files written (kept files are not counted).

    Raises
    ------
    ValueError
        When `s3_uri` is malformed, or a model name is empty, ``.``/``..``, or holds ``/``.

    Notes
    -----
    Read-only on the bucket: it calls ``list_objects_v2`` (paginated) and ``get_object``
    only. Needs no approval: nothing is written to S3 and nothing is billed beyond the
    requests and the transfer. Cost is one listing per model (one for all when
    `models` is ``None``) and one GET per file it writes.
    """
    bucket, prefix = parse_s3_uri(s3_uri)
    root = Path(local_root)
    for model in models or ():
        if not model or model in (".", "..") or "/" in model:
            raise ValueError(f"model name {model!r} must be a non-empty name without '/'")
    client = (s3_client_factory or _default_s3_factory)()
    induction = "/".join(part for part in (prefix, "induction") if part) + "/"

    # Phase 1: list. With explicit models, one listing per model prefix; otherwise one
    # listing of the whole induction/ folder, grouped by the model folder in the key.
    listings = [induction + model + "/" for model in models] if models is not None else [induction]
    written = 0
    for listing_prefix in listings:
        for key, size in _list_objects(client, bucket, listing_prefix):
            below_induction = key[len(induction):]
            model, _, rest = below_induction.partition("/")
            if model in ("", ".", "..") or not _PULLED_KEY_RE.match(rest):
                continue
            # Every component is regex-limited or checked above, so none can climb out of `root`.
            dest = root.joinpath("induction", *below_induction.split("/"))
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


def _verified_marks(run_dir: Path) -> set:
    """Return the mark indices some ``manifest--*.json`` in `run_dir` records as verified.

    Raises
    ------
    ValueError
        When a manifest is not valid JSON or lacks the ``jobs`` entries
        ``_write_manifests`` writes (the reader must not guess what it holds).
    """
    verified: set = set()
    for path in sorted(run_dir.glob("manifest--*.json")):
        try:
            for entry in json.loads(path.read_text())["jobs"]:
                if entry["status"] == "verified":
                    verified.add(int(entry["mark_index"]))
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"{path}: unreadable manifest: {exc!r}") from exc
    return verified


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


def read_captures(
    model_key: str,
    mirror_root: Path,
    *,
    arms: Sequence[str] = ARMS,
    config: Optional[Mapping[str, Any]] = None,
    require_verified: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """Compute the pad-mass ratio and the attention entropies per arm from a local mirror.

    Offline, no AWS. ``mirror_root`` holds a copy of the S3 tree under the prefix::

        <mirror_root>/induction/<model>/seed=<s>/<arm>--<stamp>/q<idx>.r<rank>.npz

    Files are grouped per run directory and ``q<idx>``; ``tp`` is the number of
    rank files, which must be exactly ranks ``0..tp-1``. Each job is loaded with
    ``attention_analysis.load_mass`` (ranks joined head-wise in rank order) and
    reduced with ``attention_analysis.whitespace_ratio`` and
    ``attention_analysis.entropy_by_layer``. The ranks present must
    also be the WHOLE set: the head axis of the joined job must equal the
    config's head count, because ranks ``0..6`` of an 8-way job are a valid
    ``0..tp-1`` set for ``tp = 7`` and a missing top rank would otherwise pass.

    Several ``<arm>--<stamp>`` directories under one ``seed=<s>`` are re-collections
    of the same arm. As in ``find_runs``, only the directory with the
    lexicographically smallest stamp (the part after ``<arm>--``) is read; later
    ones are ignored and logged at INFO. The mirror has no ``.superseded``
    markers, so that clause of ``find_runs`` does not apply.

    By default a job is read only when some ``manifest--<stamp>.json`` in its run
    directory (written by ``_write_manifests``, mirrored with the captures) lists
    it, by ``mark_index``, with ``status == "verified"``. A capture the audit
    rejected (``audit_failed: ...``), one whose upload failed, and one with no
    manifest at all is skipped, counted, and reported with one WARNING per run
    directory. `require_verified` ``False`` reads every capture file instead.

    Parameters
    ----------
    model_key : str
        Roster key.
    mirror_root : Path
        Root of the local mirror.
    arms : Sequence[str], optional
        Arms to read (default ``ARMS``).
    config : Mapping[str, Any], optional
        Parsed ``config.json`` of the model, for the expected head count
        (``attention_shape``). Defaults to ``load_model_config(model_key)``, which
        may download the file when the vendored copy does not apply.
    require_verified : bool, optional
        Read only jobs a manifest records as verified (default ``True``). Pass
        ``False`` to read every ``q*.r*.npz`` regardless of the manifests.

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Per arm with at least one capture: ``jobs`` (count), ``pad_tokens_mean``
        (mean class-1 token count per job), ``ratio_mean`` (mean over every query,
        layer, head and job that has a defined ratio) and ``ratio_layer_head``
        (``[L, H]`` array, mean over queries and jobs). Queries are pooled, so
        longer completions weigh more. An arm without any pad token has an
        undefined ratio: ``nan``, not 0. ``skipped_unverified`` counts the jobs of
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

        ``prompt_entropy_v1_jobs`` (int) counts the arm's jobs read from a
        version-1 capture, which has no ``prompt_entropy`` array: they give NaN
        prompt-entropy values, are left out of the ``prompt_entropy_*`` means and
        counts, and never raise. Their ``entropy`` is still read.

    Raises
    ------
    ValueError
        When the ranks of a job are not exactly ``0..tp-1``, when the joined
        job's head count differs from the config's (a rank is missing), or when
        jobs of one arm differ in layer or head count; also when `config` has no
        readable attention shape.
    """
    base = Path(mirror_root) / "induction" / model_key
    store = _MirrorStore(Path(mirror_root))
    if config is None:
        config = load_model_config(model_key)
    expected_heads = attention_shape(config)[1]
    out: Dict[str, Dict[str, Any]] = {}
    for arm in arms:
        sums: Optional[np.ndarray] = None
        counts: Optional[np.ndarray] = None
        n_jobs, pad_total, n_skipped = 0, 0, 0
        # Per statistic, one entry per job: the job's all-layer, global-layer and
        # window-layer means, and its [L] per-layer means (see _pool_layers).
        per_job: Dict[str, Dict[str, List[Any]]] = {
            stat: {"all": [], "global": [], "window": [], "layer": []} for stat in _ENTROPY_STATS
        }
        n_v1 = 0
        # Earliest wins, per seed and arm: the directories of one seed are
        # re-collections of the same arm, and the released results count the first.
        stamp_prefix = f"{arm}--"
        by_seed: Dict[Path, List[Path]] = {}
        for candidate in base.glob(f"seed=*/{stamp_prefix}*"):
            if candidate.is_dir():
                by_seed.setdefault(candidate.parent, []).append(candidate)
        run_dirs: List[Path] = []
        for seed_dir in sorted(by_seed):
            ordered = sorted(by_seed[seed_dir], key=lambda d: d.name[len(stamp_prefix):])
            run_dirs.append(ordered[0])
            for later in ordered[1:]:
                logging.info(
                    f"attention_replay: ignoring {later}: an earlier {arm} run of "
                    f"{seed_dir.name} exists ({ordered[0].name})"
                )
        for run_dir in run_dirs:
            ranks: Dict[int, set] = {}
            for path in run_dir.iterdir():
                match = _CAPTURE_FILE_RE.match(path.name)
                if match:
                    ranks.setdefault(int(match.group(1)), set()).add(int(match.group(2)))
            rel = run_dir.relative_to(Path(mirror_root)).as_posix() + "/"
            verified = _verified_marks(run_dir) if require_verified else None
            unverified = [i for i in sorted(ranks) if verified is not None and i not in verified]
            if unverified:
                n_skipped += len(unverified)
                logging.warning(
                    f"attention_replay: {run_dir}: skipping {len(unverified)} job(s) no manifest "
                    f"records as verified: q{unverified}"
                )
            for idx in sorted(ranks):
                if idx in unverified:
                    continue
                tp = len(ranks[idx])
                if ranks[idx] != set(range(tp)):
                    raise ValueError(
                        f"{run_dir}/q{idx}: ranks {sorted(ranks[idx])} are not exactly 0..{tp - 1}"
                    )
                job = attention_analysis.load_mass(store, rel, f"q{idx}", tp)
                if job["mass"].shape[2] != expected_heads:
                    raise ValueError(
                        f"{run_dir}/q{idx}: the {tp} rank(s) hold {job['mass'].shape[2]} heads in "
                        f"total, the config has {expected_heads}; a rank is missing"
                    )
                ratio = attention_analysis.whitespace_ratio(
                    job["mass"].astype(np.float32), job["classes"], job["query_start"]
                )
                layers, _p, heads = ratio.shape
                if sums is None:
                    sums = np.zeros((layers, heads), dtype=np.float64)
                    counts = np.zeros((layers, heads), dtype=np.int64)
                elif sums.shape != (layers, heads):
                    raise ValueError(
                        f"{run_dir}/q{idx}: shape (L={layers}, H={heads}) differs from the arm's "
                        f"{sums.shape}"
                    )
                defined = ~np.isnan(ratio)
                sums += np.where(defined, ratio, 0.0).sum(axis=1, dtype=np.float64)
                counts += defined.sum(axis=1)
                # Entropy means of this job: its own pooled defined values per layer set.
                by_layer = attention_analysis.entropy_by_layer(job)
                window = job.get("sliding_window")
                is_global = None if window is None else np.asarray(window) == 0
                is_window = None if window is None else np.asarray(window) > 0
                for stat in _ENTROPY_STATS:
                    mean_l, count_l = by_layer[stat], by_layer[f"{stat}_count"]
                    per_job[stat]["all"].append(_pool_layers(mean_l, count_l, None))
                    per_job[stat]["global"].append(
                        float("nan") if is_global is None else _pool_layers(mean_l, count_l, is_global)
                    )
                    per_job[stat]["window"].append(
                        float("nan") if is_window is None else _pool_layers(mean_l, count_l, is_window)
                    )
                    per_job[stat]["layer"].append(mean_l)
                if job.get("prompt_entropy") is None:
                    n_v1 += 1
                n_jobs += 1
                pad_total += int((np.asarray(job["classes"]) == attention_analysis.PAD_CLASS).sum())
        if n_jobs == 0 or sums is None or counts is None:
            continue  # nothing read; any skips were already logged per run directory
        # nan, not 0, where no query had a defined baseline (no pad token anywhere);
        # np.divide with ``where`` never emits a divide warning.
        layer_head = np.full(sums.shape, np.nan, dtype=np.float64)
        np.divide(sums, counts, out=layer_head, where=counts > 0)
        total = int(counts.sum())
        out[arm] = {
            "jobs": n_jobs,
            "pad_tokens_mean": pad_total / n_jobs,
            "ratio_mean": float(sums.sum() / total) if total else float("nan"),
            "ratio_layer_head": layer_head,
            "skipped_unverified": n_skipped,
            "prompt_entropy_v1_jobs": n_v1,
        }
        # Every job counts once: mean over a job's positions, heads and layers first,
        # then over jobs (the footnote's "mean per response"), not over pooled rows.
        for stat in _ENTROPY_STATS:
            jobs_stat = per_job[stat]
            mean, n_defined, sd = _mean_sd_over_jobs(jobs_stat["all"])
            out[arm][f"{stat}_mean"] = mean
            out[arm][f"{stat}_global_mean"] = _mean_sd_over_jobs(jobs_stat["global"])[0]
            out[arm][f"{stat}_window_mean"] = _mean_sd_over_jobs(jobs_stat["window"])[0]
            stacked = np.vstack(jobs_stat["layer"])  # [jobs, L]
            defined = ~np.isnan(stacked)
            layer_mean = np.full(stacked.shape[1], np.nan, dtype=np.float64)
            np.divide(
                np.where(defined, stacked, 0.0).sum(axis=0), defined.sum(axis=0),
                out=layer_mean, where=defined.any(axis=0),
            )
            out[arm][f"{stat}_layer"] = layer_mean
            out[arm][f"{stat}_jobs"] = n_defined
            out[arm][f"{stat}_sd"] = sd
    return out
