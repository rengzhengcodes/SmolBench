"""
Share one OpenAI-compatible Chat Completions client across every provider.

OpenRouter, Prime Intellect, AWS Bedrock/SageMaker and EC2 vLLM speak the same
``/chat/completions`` dialect, differing only in endpoint resolution, auth and
a few policy knobs. Each builds one :class:`ChatClient` and re-exports its
bound ``query``/``complete``/``evaluate`` for ``smolbench.evals.provider`` to
dispatch to, keeping providers substitutable behind ``INFERENCE_PROVIDER``.
``query`` narrows ``complete``'s :class:`ChatResult` to ``(content,
reasoning)``; callers needing usage or a bounded ``max_retries`` (the Lean
sweep runner) call ``complete``.

Response handling covers every provider's quirks at once:

- Reasoning comes from ``message.reasoning_content`` (vLLM/Bedrock/SageMaker),
  falling back to ``message.reasoning`` (OpenRouter/Prime Intellect).
- With no server-side channel, a plain-text ``<think>...</think>`` block is
  split client-side so scoring sees only the answer (models whose tokenizers
  lack think token ids: Nemotron-Ultra, Olmo-Think; see ``EC2_DEPLOY_SPECS``
  in ``smolbench.evals.providers.ec2``).
- ``usage`` may be absent entirely (some SageMaker containers omit it), as may
  ``model``/``finish_reason``: those are read defensively and the context guard
  then does not fire. ``choices[0].message.content`` is NOT optional -- a body
  without it raises ``KeyError``/``IndexError`` out of the retry loop, since a
  server that answers 200 with no message is broken rather than transient.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
from joblib import Parallel, delayed

from smolbench.evals import Quiz, Mark, Marks
from smolbench.evals.quiz import COMPLIANT

#: HTTP timeout (seconds) for provider METADATA requests (``GET /models``,
#: context-length lookups): small, fast payloads, so one shared constant covers
#: every provider. Chat completions use ``ChatClient.connect_timeout_s`` /
#: ``read_timeout_s`` (or the per-call ``request_timeout``) instead, which must
#: tolerate slow chain-of-thought generations.
METADATA_TIMEOUT_S: int = 120


def metadata_get(url: str, api_key: str, *, check_status: bool, timeout: float = METADATA_TIMEOUT_S) -> Any:
    """Perform one bearer-authenticated metadata GET and return its parsed JSON body.

    Callers build the URL, resolve the key and do all shape-specific
    post-processing; this function never interprets the body.

    Parameters
    ----------
    check_status : bool
        True raises before parsing (``list_models``: AWS, EC2); False parses
        regardless of status (``get_model_context_length``: OpenRouter, Prime
        Intellect, where an error body instead raises in the caller's own
        indexing). Keyword-only with NO default, so the split can never be
        silently unified -- do not collapse it.

    Raises
    ------
    requests.exceptions.HTTPError
        4xx/5xx, when ``check_status`` is True.
    requests.exceptions.RequestException
        Connection-level failure, either way.
    requests.exceptions.JSONDecodeError
        Non-JSON body, even on a 2xx.
    """
    response = requests.get(
        url=url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=timeout,
    )
    if check_status:
        response.raise_for_status()
    return response.json()


def is_retryable_request_error(err: requests.exceptions.RequestException) -> bool:
    """Return whether a chat-completions request error should be retried.

    HTTP 429 and 5xx are transient, as is any non-HTTP failure (connection
    reset, timeout, DNS); other 4xx are permanent auth/validation errors.
    """
    if isinstance(err, requests.exceptions.HTTPError):
        response = err.response
        if response is None:
            return True
        return response.status_code == 429 or 500 <= response.status_code < 600
    return True


def collect_stream(response: requests.Response) -> Dict[str, Any]:
    """Reassemble an SSE completion stream into a NON-streamed response body.

    A non-streaming completion is silent on the wire for the whole generation,
    and a long-quiet socket can be dropped in transit -- a loss selective by
    generation LENGTH. SSE keeps bytes flowing. The result is rebuilt into
    exactly the non-streamed shape so no downstream parsing forks on transport
    and streamed runs stay comparable with non-streamed ones. Sampling is
    server-side and untouched.

    Parameters
    ----------
    response : requests.Response
        An open ``requests.post(..., stream=True)`` response.

    Returns
    -------
    dict
        ``{"choices": [{"message": {...}, "finish_reason": ...}], "usage":
        {...}, "model": ...}``. ``reasoning_content`` is present only if the
        server sent reasoning deltas; ``usage`` only if the request sent
        ``stream_options: {"include_usage": true}``, else empty (tolerated
        downstream, but the study loses its token counts).

    Raises
    ------
    requests.exceptions.ChunkedEncodingError
        A malformed SSE chunk, or a stream that ended without ``[DONE]`` or
        any ``finish_reason`` (truncated body) -- retryable, like the
        non-streamed transport's parse failure on a truncated body.
    """
    content_parts: List[str] = []
    reasoning_parts: List[str] = []
    finish_reason: Optional[str] = None
    usage: Dict[str, Any] = {}
    reported_model: Optional[str] = None
    saw_reasoning = False
    saw_content = False
    saw_done = False

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        if not line.startswith("data:"):
            continue  # SSE comment/keepalive line
        payload = line[len("data:"):].strip()
        if payload == "[DONE]":
            saw_done = True
            break
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError as err:
            # Stdlib JSONDecodeError is a ValueError, NOT a RequestException,
            # so it would escape complete()'s retry loop and abort a whole
            # pooled evaluate(). Re-raise as the stream-broke class the retry
            # loop already handles, keeping the two transports' error
            # handling identical.
            raise requests.exceptions.ChunkedEncodingError(
                f"malformed SSE chunk: {payload[:200]!r}"
            ) from err
        reported_model = chunk.get("model") or reported_model
        # The usage-only final chunk (include_usage) carries an EMPTY
        # choices list, so this must not assume choices[0] exists.
        if chunk.get("usage"):
            usage = chunk["usage"]
        for choice in chunk.get("choices") or []:
            delta = choice.get("delta") or {}
            if delta.get("content"):
                content_parts.append(delta["content"])
                saw_content = True
            reasoning_delta = delta.get("reasoning_content") or delta.get("reasoning")
            if reasoning_delta:
                reasoning_parts.append(reasoning_delta)
                saw_reasoning = True
            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]

    # Completeness gate: an intermediary closing the stream cleanly at a
    # chunk boundary raises nothing from iter_lines, so without this a
    # half-generated body would be graded as a finished one. A stream that
    # produced neither [DONE] nor any finish_reason is truncated; raise the
    # retryable stream-broke class, exactly what a truncated non-streamed
    # body produces via response.json().
    if not saw_done and finish_reason is None:
        raise requests.exceptions.ChunkedEncodingError(
            "SSE stream ended without [DONE] or a finish_reason; body is incomplete"
        )

    # NO content deltas -> content is None, NOT "": vLLM's non-streamed body
    # sends `"content": null` when a generation spends its whole budget in the
    # reasoning channel, and the caller's early-return for that case retains
    # the reasoning. "" would skip it, so the two transports would disagree on
    # retention for exactly the cap-length population.
    message: Dict[str, Any] = {"content": "".join(content_parts) if saw_content else None}
    if saw_reasoning:
        message["reasoning_content"] = "".join(reasoning_parts)
    return {
        "choices": [{"message": message, "finish_reason": finish_reason}],
        "usage": usage,
        "model": reported_model,
    }


def _identity_body_model(model: str) -> str:
    """Default: the caller-facing model id goes in the request body verbatim."""
    return model


def _no_system_prompt(model: str) -> Optional[str]:
    """Default: no provider-injected system prompt for any model."""
    return None


def _no_extra_headers(model: str) -> Dict[str, str]:
    """Default: no provider-specific request headers beyond auth/content-type."""
    return {}


def grade(quiz: Quiz, responses: List[Tuple[str, Optional[str]]], model: str,
          log_invalid: bool = False) -> Marks:
    """Grade raw ``(content, reasoning)`` responses, one per question in quiz order.

    Each ``Mark`` records ``score`` (1 correct / 0 wrong / None invalid) and
    ``compliance`` (``parsing.parse_for``'s label for how the response
    disobeyed the output contract, `COMPLIANT` when it obeyed) INDEPENDENTLY, so a
    right answer in the wrong shape stays distinguishable from a wrong one --
    what the induction ``noise_intens`` arm needs, its whitespace padding
    controlling prompt LENGTH while measurably degrading instruction
    following. A response yielding no answer at all (empty, repetition
    collapse, truncated chain) scores None; recovery from long responses is
    deliberately conservative (see ``smolbench.evals.parsing``).

    Parameters
    ----------
    log_invalid : bool
        Log unparseable responses at INFO.
    """
    from smolbench.evals.parsing import parse_for

    mark_list: List[Mark] = []
    for q, (raw, reasoning) in zip(quiz, responses):
        try:
            parsed = parse_for(q, raw)
        except Exception as exc:  # noqa: BLE001 -- see below; deliberate
            # A parser bug must not destroy a run that already cost hours of
            # GPU time and cannot be recovered by retrying. An unreadable
            # response is exactly what `score=None` means, so degrading to
            # "invalid" loses one mark; raw text is kept for offline re-grading.
            logging.warning(
                f"grade: parser raised on a response, marking invalid: "
                f"{type(exc).__name__}: {exc}"
            )
            mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw,
                                  reasoning=reasoning, score=None,
                                  compliance="parser-error"))
            continue
        if parsed.value is None:
            if log_invalid:
                logging.info(
                    f"unparseable response ({parsed.violation}): {raw[:120]!r}"
                )
            mark_list.append(Mark(query=q.prompt, answer=q.answer,
                                  response=raw, reasoning=reasoning, score=None,
                                  compliance=parsed.violation))
            continue
        # `parsing.ParseResult.violation` keeps its own None-means-no-violation
        # contract (see that module); `grade` is the boundary where a stored
        # ``Mark`` is built, so the translation to the explicit `COMPLIANT`
        # label happens here, once, rather than pushing "None means compliant"
        # out to every reader of a `Mark.compliance` value. Written as an
        # explicit `is None` check, not `parsed.violation or COMPLIANT`: a
        # falsy-but-real violation label would silently read as compliant
        # under `or` (none of today's labels are falsy strings, but the check
        # should not depend on that staying true).
        compliance = COMPLIANT if parsed.violation is None else parsed.violation
        mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw,
                              reasoning=reasoning,
                              score=int(q.score(parsed.value)),
                              compliance=compliance))
    return Marks(model=model, marks=tuple(mark_list))


def _render_progress(done: int, total: int, model: str, width: int = 30) -> None:
    """Render a single-line "N/total prompted" bar (no tqdm dependency).

    Driven by joblib's as-completed generator, so the bar advances as responses
    land, not as tasks dispatch. Emits a trailing newline once ``done >= total``.
    """
    filled: int = width if total == 0 else int(width * done / total)
    bar: str = "#" * filled + "-" * (width - filled)
    pct: float = 100.0 if total == 0 else 100.0 * done / total
    end: str = "\n" if done >= total else ""
    print(f"\r{model}: [{bar}] {done}/{total} prompted ({pct:3.0f}%)", end=end, flush=True)


@dataclass(frozen=True)
class ChatResult:
    """Hold the full per-call response from :meth:`ChatClient.complete`.

    The usage/``model``/``finish_reason`` fields are populated DEFENSIVELY via
    ``.get`` chains: some SageMaker containers omit ``usage`` entirely and not
    every server echoes the others, so their absence is non-exceptional.
    ``content``/``reasoning`` come from a REQUIRED ``choices[0].message`` (see
    the module docstring).
    """

    #: The message content. Empty string on the server's null-content path
    #: (``ChatClient.complete``'s empty-content warning branch).
    content: str
    #: Reasoning-channel text: server-reported (``reasoning_content`` /
    #: ``reasoning``) or client-side-split from a plain-text ``<think>``
    #: block (see the module docstring). None when neither is present.
    reasoning: Optional[str]
    #: ``usage.prompt_tokens``; 0 when absent.
    prompt_tokens: int
    #: ``usage.completion_tokens``; 0 when absent.
    completion_tokens: int
    #: ``usage.prompt_tokens_details.cached_tokens``. OpenRouter/OpenAI
    #: report Anthropic/OpenAI prompt-cache hits here; 0 when absent.
    cached_prompt_tokens: int
    #: ``usage.total_tokens``; None when absent, which skips
    #: ``ChatClient.complete``'s context-length guard.
    total_tokens: Optional[int]
    #: ``body["model"]`` when the server echoes it back, else the requested
    #: model id (some containers -- and the empty-content path -- don't).
    model: str
    #: ``choices[0].finish_reason`` (e.g. ``"stop"``, ``"length"``); None
    #: when the server omits it.
    finish_reason: Optional[str]


@dataclass(frozen=True)
class ChatClient:
    """Represent one OpenAI-compatible chat-completions endpoint family.

    Providers configure the deltas; the retry loop, response parsing and
    parallel evaluation live here once. All ``Callable`` fields are resolved at
    CALL time, never import time, so environment changes (a re-provisioned EC2
    instance, a refreshed SageMaker token) take effect without re-import.
    """

    #: Human-readable provider name, used as the log-line prefix.
    name: str
    #: Env-var prefix P: ``{P}_INFO``, ``{P}_INFO_RESPONSE`` (verbose logging)
    #: and ``{P}_MAX_PARALLEL_REQUESTS`` (evaluate's default fan-out, default
    #: 8), all read at call time.
    env_prefix: str
    #: model -> (chat-completions URL, bearer token). Called once per request
    #: ATTEMPT, so an endpoint that moves between retries (an EC2 spot instance
    #: re-provisioned under a new IP) is picked up mid-loop, and URL and token
    #: always come from one consistent snapshot.
    connection: Callable[[str], Tuple[str, str]]
    #: model -> context window; used by ``evaluate`` for the token guard.
    context_length: Callable[[str], int]
    #: model -> the OpenAI ``model`` field for the request body (SageMaker
    #: routes by URL and may need a container-specific id; everyone else
    #: sends the caller's id verbatim).
    body_model: Callable[[str], str] = _identity_body_model
    #: model -> system prompt injected ahead of the user prompt, or None.
    #: Lets model-specific toggles (Nemotron's "detailed thinking on") live
    #: in a deploy spec while user prompts stay byte-identical across models.
    system_prompt: Callable[[str], Optional[str]] = _no_system_prompt
    #: model -> extra request headers merged into every chat-completions
    #: request (e.g. Prime Intellect's ``X-Prime-Team-ID`` billing header).
    #: Resolved per request attempt, as ``connection`` is. On a key collision
    #: the client's own ``Authorization``/``Content-Type`` wins; extra headers
    #: must never silently clobber auth.
    extra_headers: Callable[[str], Dict[str, str]] = _no_extra_headers
    #: Seconds slept between retryable failures.
    retry_backoff_s: int = 60
    #: Connect timeout, kept SHORT and separate from the read timeout: a
    #: generous scalar timeout would make a dead endpoint blackhole every
    #: connect for the full read budget before retrying.
    connect_timeout_s: float = 10.0
    #: Default per-request read timeout; long CoT generations may need the
    #: per-call ``request_timeout`` override instead.
    read_timeout_s: int = 120
    #: When set, this many CONSECUTIVE connection-level failures abort the
    #: retry loop via ``on_unreachable``. Connection-level means
    #: ``requests.exceptions.ConnectionError`` (refused, reset, DNS,
    #: ConnectTimeout) -- never an HTTP error, and never a ReadTimeout, which
    #: is a server that ANSWERED and then generated slowly. For self-managed
    #: endpoints that can vanish (spot reclaim, caller-IP drift); None
    #: (default) retries forever, correct for managed APIs.
    max_connection_failures: Optional[int] = None
    #: Diagnosis hook called once the failure cap trips; it normally raises an
    #: actionable error, but the caller does not rely on that (a plain return
    #: falls through to the generic error below).
    on_unreachable: Optional[Callable[[Exception], None]] = None

    def _flag(self, suffix: str) -> bool:
        """Read boolean env flag ``{env_prefix}_{suffix}`` at call time.

        Accepts the common boolean spellings; anything else raises naming the
        variable, instead of a bare ``int()`` ValueError deep in the hot path.
        """
        var = f"{self.env_prefix}_{suffix}"
        raw = os.getenv(var, "0").strip().lower()
        if raw in ("1", "true", "yes", "on"):
            return True
        if raw in ("", "0", "false", "no", "off"):
            return False
        raise ValueError(
            f"{var}={raw!r} is not a boolean flag (use 1/0/true/false/yes/no/on/off)"
        )

    def _default_max_parallel(self) -> int:
        return int(os.getenv(f"{self.env_prefix}_MAX_PARALLEL_REQUESTS", "8"))

    def complete(
        self,
        prompt: str,
        model: str,
        seed: int,
        *,
        system: Optional[str] = None,
        context_length: int = 0,
        extra_args: Optional[Dict[str, Any]] = None,
        request_timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> ChatResult:
        """Query ``model`` once, and return the full response as a ``ChatResult``.

        Holds the message assembly, retry loop, ``<think>``-splitting, usage
        guard and logging; ``query()`` narrows the result.

        Parameters
        ----------
        seed : int
            Decoding seed, sent with every request; this repo requires seeded,
            reproducible generations, so never drop it to dodge an error.
        system : str, optional
            Extra system message. Order is ``[provider system_prompt(model),
            system, user prompt]``: the provider-level prompt goes FIRST
            because it carries deploy-spec toggles (Nemotron's "detailed
            thinking on"; see ``EC2_DEPLOY_SPECS``) this must layer onto,
            never shadow.
        context_length : int, optional
            Token-budget guard: logs a WARNING when the response reports
            ``usage.total_tokens`` above it, and when the response omits
            ``usage`` so the guard cannot be enforced. Soft and post-hoc by
            design -- the generation is already billed, so an overrun returns
            for grading rather than aborting a pooled ``evaluate()``. Pass
            ``get_model_context_length(model)``.
        extra_args : dict, optional
            Merged into the request body (e.g. ``max_completion_tokens``,
            ``reasoning_effort``), BEFORE ``seed`` and the streaming keys, so
            it can never override those.
        request_timeout : int, optional
            Per-request read timeout in seconds, overriding ``read_timeout_s``.
            Raise it so long CoT generations complete on attempt 1.
        max_retries : int, optional
            Cap on retryable failures (HTTP 429/5xx or connection-level); the
            Nth re-raises instead of sleeping again. None (default) retries
            them indefinitely; non-retryable errors (4xx other than 429) always
            raise at once. On a connection-level failure ``on_unreachable``
            still fires before the re-raise even when this cap exhausts first
            (the Lean sweep's 4 vs EC2's 10), so a vanished self-managed
            endpoint is diagnosed rather than surfaced as a generic connection
            error.

        Raises
        ------
        requests.exceptions.RequestException
            A non-retryable HTTP error (4xx other than 429), or any retryable
            HTTP/connection failure once ``max_retries`` is exhausted.
        RuntimeError
            ``max_connection_failures`` consecutive connection-level failures
            tripped first; takes precedence over ``max_retries``.
        """
        sys_prompt = self.system_prompt(model)
        messages: List[Dict[str, str]] = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        if system:
            # Second system message, AFTER the provider's own -- see the
            # ``system`` parameter doc above for why this order is load-bearing.
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # OPT-IN streaming transport, off by default; chunks are reassembled
        # into the ordinary response shape (``collect_stream``) so the study's
        # data path does not fork. Enabled per LANE, never globally: rows
        # already on disk came over the non-streamed path.
        stream: bool = self._flag("STREAM_COMPLETIONS")

        attempt: int = 0
        connection_failures: int = 0
        # Every retryable failure (connection-level OR HTTP 429/5xx), kept
        # separate from `connection_failures` (non-HTTP only, for the
        # max_connection_failures escalation) so the two caps cannot interfere.
        retry_failures: int = 0
        while True:
            attempt += 1
            # Resolved per attempt -- see the ``connection`` field docs.
            url, token = self.connection(model)
            try:
                # Context-managed so a streamed response's socket is released
                # on every path, including the error raised below.
                with requests.post(
                    url=url,
                    # Extra headers first, base pair second: on collision the
                    # base Authorization/Content-Type wins (``extra_headers``).
                    headers=self.extra_headers(model) | {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=(
                        {"model": self.body_model(model), "messages": messages}
                        | (extra_args if extra_args else {})
                        # seed and the transport keys are applied AFTER
                        # extra_args, so a caller's sampling arguments cannot
                        # silently override either. This repo requires seeded
                        # generations, so extra_args must not drop the seed.
                        # include_usage puts the token counters on the final
                        # chunk; without it a streamed row loses them.
                        | {"seed": seed}
                        | ({"stream": True, "stream_options": {"include_usage": True}}
                           if stream else {})
                    ),
                    timeout=(
                        self.connect_timeout_s,
                        request_timeout or self.read_timeout_s,
                    ),
                    stream=stream,
                ) as response:
                    # The server answered, so the endpoint is alive: only
                    # SUSTAINED connection failures count toward unreachable.
                    connection_failures = 0

                    if not response.ok:
                        # Surface the API's error body, not just the status
                        # line: provider 4xx bodies carry the actionable detail
                        # (context-too-long, invalid model id, billing) and
                        # callers persist str(err) into durable artifacts (the
                        # Lean sweep's exception rows). ``response=`` stays
                        # attached -- is_retryable_request_error reads its
                        # status_code, which outlives the closed socket.
                        raise requests.exceptions.HTTPError(
                            f"{response.status_code} {response.reason} for url "
                            f"{response.url}: {response.text[:1000]}",
                            response=response,
                        )
                    body = collect_stream(response) if stream else response.json()
                if self._flag("INFO") and self._flag("INFO_RESPONSE"):
                    logging.info(body)

                choice = body["choices"][0]
                msg = choice["message"]
                # Read once, reused by the empty-content and normal-content
                # return paths; `.get` chains because `usage` may be absent
                # entirely (see the module docstring).
                usage = body.get("usage") or {}
                prompt_tokens: int = int(usage.get("prompt_tokens") or 0)
                completion_tokens: int = int(usage.get("completion_tokens") or 0)
                cached_prompt_tokens: int = int(
                    (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
                )
                total_tokens: Optional[int] = usage.get("total_tokens")
                reported_model: str = body.get("model") or model
                finish_reason: Optional[str] = choice.get("finish_reason")

                if msg["content"] is None:
                    logging.warning("Body returned none value: \n" f"{body}")
                    # Never hardcode reasoning=None here: a reasoning-only
                    # cap-hit (whole budget spent in the reasoning channel,
                    # content=null) would become an indistinguishably empty row
                    # -- measured live as a 106,545-character reasoning body
                    # collapsed to a "1 chars" result. Both channel spellings
                    # are read as in the normal branch below, so the transports
                    # agree on retention. `content` stays "" so a cap-hit still
                    # grades as an empty candidate rather than a proof.
                    return ChatResult(
                        content="",
                        reasoning=msg.get("reasoning_content") or msg.get("reasoning"),
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cached_prompt_tokens=cached_prompt_tokens,
                        total_tokens=total_tokens,
                        model=reported_model,
                        finish_reason=finish_reason,
                    )
                content = msg["content"]
                reasoning = msg.get("reasoning_content") or msg.get("reasoning")
                if reasoning is None and "</think>" in content:
                    # Plain-text think block (no server-side reasoning parser):
                    # split so scoring sees only the answer (module docstring).
                    reasoning, _, content = content.partition("</think>")
                    reasoning = reasoning.removeprefix("<think>").strip()
                    content = content.lstrip()
                # Post-hoc token guard, soft by design: one over-budget (or
                # usage-less) response must not abort a pooled evaluate()
                # whose other generations are already paid for -- warn loudly
                # and return the response for grading instead of raising.
                if total_tokens is None:
                    if context_length:
                        logging.warning(
                            f"{self.name}: response omitted usage.total_tokens; "
                            f"context-length guard ({context_length}) unenforceable -- "
                            f"a window-truncated response would grade as a wrong answer"
                        )
                elif context_length and total_tokens > context_length:
                    logging.warning(
                        f"Response:\n{body}\n was {total_tokens} > {context_length}"
                    )
                elif self._flag("INFO"):
                    logging.info(f"Response:\n{body}\n was {total_tokens} <= {context_length}")
                return ChatResult(
                    content=content,
                    reasoning=reasoning,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cached_prompt_tokens=cached_prompt_tokens,
                    total_tokens=total_tokens,
                    model=reported_model,
                    finish_reason=finish_reason,
                )

            except requests.exceptions.RequestException as err:
                if not is_retryable_request_error(err):
                    raise
                # ConnectionError (refused/reset/DNS/ConnectTimeout), not
                # "everything that is not an HTTPError": a ReadTimeout means
                # the endpoint ANSWERED and then generated slowly, which must
                # not count toward "the endpoint has vanished".
                connection_level = isinstance(err, requests.exceptions.ConnectionError)
                if self.max_connection_failures is not None and connection_level:
                    connection_failures += 1
                    if connection_failures >= self.max_connection_failures:
                        if self.on_unreachable is not None:
                            self.on_unreachable(err)
                        raise RuntimeError(
                            f"{self.name} endpoint unreachable after "
                            f"{self.max_connection_failures} consecutive connection failures."
                        ) from err
                if max_retries is not None:
                    retry_failures += 1
                    if retry_failures >= max_retries:
                        # Nth retryable failure: surface the error instead of
                        # sleeping again, but route a connection-level one
                        # through ``on_unreachable`` first so the
                        # spot-reclaim/IP-drift diagnosis is not lost (see the
                        # max_retries parameter doc).
                        if (
                            self.on_unreachable is not None
                            and connection_failures > 0
                            and connection_level
                        ):
                            self.on_unreachable(err)
                        raise
                logging.info(
                    f"{self.name} request failed on attempt {attempt}: {err}. "
                    f"Retrying in {self.retry_backoff_s} seconds."
                )
                time.sleep(self.retry_backoff_s)

    def query(
        self,
        prompt: str,
        model: str,
        seed: int,
        context_length: int = 0,
        extra_args: Optional[Dict[str, Any]] = None,
        request_timeout: Optional[int] = None,
        *,
        system: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> Tuple[str, Optional[str]]:
        """Query ``model`` once, returning only ``(content, reasoning)``.

        A thin wrapper over ``complete()`` -- see it for the parameter docs and
        the ``ChatResult`` fields this discards.
        """
        result = self.complete(
            prompt,
            model,
            seed,
            system=system,
            context_length=context_length,
            extra_args=extra_args,
            request_timeout=request_timeout,
            max_retries=max_retries,
        )
        return result.content, result.reasoning

    def _indexed_query(self, index: int, *args: Any, **kwargs: Any) -> Tuple[int, Tuple[str, Optional[str]]]:
        """Tag ``query()``'s result with the question's quiz position ``index``.

        Results stream back out of order (``return_as="generator_unordered"``);
        the index lets ``evaluate`` restore quiz order before grading.
        """
        return index, self.query(*args, **kwargs)

    def evaluate(
        self,
        quiz: Quiz,
        model: str,
        seed: int,
        extra_args: Optional[Dict[str, Any]] = None,
        max_parallel: Optional[int] = None,
        request_timeout: Optional[int] = None,
        show_progress: bool = True,
    ) -> Marks:
        """Evaluate ``model`` on one quiz (a sequence of ``QnA`` questions).

        Queries every question in parallel threads under the shared decoding
        ``seed``, then grades the responses back in quiz order (see ``grade``).

        Parameters
        ----------
        extra_args : dict, optional
            Forwarded to every ``query``, as is ``request_timeout``.
        max_parallel : int, optional
            Thread fan-out; defaults to ``{env_prefix}_MAX_PARALLEL_REQUESTS``
            (8). CoT runs may lower it and raise ``request_timeout`` so the
            longest chain finishes on attempt 1; otherwise long generations
            time out under contention and censor the measured CoT-length
            distribution from the top.
        show_progress : bool
            Print a live "N/total prompted" bar (default True).
        """
        ctx_len: int = self.context_length(model)
        total: int = len(quiz)
        max_workers: int = max(1, min(total, max_parallel or self._default_max_parallel()))

        # Stream results as they complete, so the progress bar reflects
        # finished prompts; each result carries its index to restore quiz order.
        results_by_index: Dict[int, Tuple[str, Optional[str]]] = {}
        completed: int = 0
        if show_progress:
            _render_progress(completed, total, model)
        stream = Parallel(n_jobs=max_workers, prefer="threads", return_as="generator_unordered")(
            delayed(self._indexed_query)(
                i, q.prompt, model, seed, ctx_len,
                extra_args=extra_args, request_timeout=request_timeout,
            )
            for i, q in enumerate(quiz)
        )
        for index, resp in stream:
            results_by_index[index] = resp
            completed += 1
            if show_progress:
                _render_progress(completed, total, model)
        responses: List[Tuple[str, Optional[str]]] = [results_by_index[i] for i in range(total)]

        return grade(quiz, responses, model, log_invalid=self._flag("INFO"))
