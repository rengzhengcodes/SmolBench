"""
Share one OpenAI-compatible Chat Completions client across every provider.

Every provider (OpenRouter, Prime Intellect, AWS Bedrock/SageMaker, EC2 vLLM)
speaks the same ``/chat/completions`` dialect and differs only in endpoint
resolution, auth, and a few policy knobs. Each builds one :class:`ChatClient`
and re-exports its bound ``query``/``complete``/``evaluate`` as the functions
``smolbench.evals.provider`` dispatches to, so providers stay substitutable
behind ``INFERENCE_PROVIDER``. ``complete`` returns the full
:class:`ChatResult`; ``query`` narrows it to the ``(content, reasoning)``
2-tuple. Callers needing usage or a bounded ``max_retries`` (e.g. a Lean
sweep runner) should call ``complete``.

Response handling is the SUPERSET of what the providers had grown separately:

- The reasoning channel is read from ``message.reasoning_content``
  (vLLM/Bedrock/SageMaker) first, falling back to ``message.reasoning``
  (OpenRouter/Prime Intellect).
- With no server-side channel, a plain-text ``<think>...</think>`` block is
  split out client-side so scoring sees only the answer (models whose
  tokenizers lack think token ids, e.g. Nemotron-Ultra and Olmo-Think; see
  the ``EC2_DEPLOY_SPECS`` notes in ``smolbench.evals.providers.ec2``).
- The ``usage.total_tokens`` context guard fires only when the server
  actually reports usage (some SageMaker containers omit it).
- Timeouts are a ``(connect, read)`` pair: a short connect fails fast on a
  dead endpoint, while a long read lets slow CoT generations finish on
  attempt 1 instead of surviving only via the retry lottery, which would
  censor the CoT-length distribution from the top.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple

import requests
from joblib import Parallel, delayed

from smolbench.evals import Quiz, Mark, Marks

#: HTTP timeout (seconds) for provider METADATA requests: catalog listings
#: (e.g. ``GET /models``) and context-length lookups. This is distinct from
#: chat completions, which use ``ChatClient.connect_timeout_s`` /
#: ``read_timeout_s`` (or the per-call ``request_timeout`` override),
#: because those must tolerate slow chain-of-thought generations. Metadata
#: calls return a small, fast payload, so one shared constant covers every
#: provider's catalog/context-length lookup, instead of each module
#: hardcoding its own ``timeout=120`` literal.
METADATA_TIMEOUT_S: int = 120


def metadata_get(url: str, api_key: str, *, check_status: bool, timeout: float = METADATA_TIMEOUT_S) -> Any:
    """Perform one bearer-authenticated metadata GET and return its parsed JSON body.

    Shared by the providers' ``get_model_context_length`` and ``list_models``
    lookups; callers build the URL, resolve the key, and do all
    shape-specific post-processing. This function never interprets the body.

    ``check_status`` is keyword-only with NO default so the split can never be
    silently unified -- do not collapse it. True calls ``raise_for_status()``
    before parsing (``list_models``: AWS, EC2), raising ``HTTPError`` on
    4xx/5xx; False parses regardless of status (``get_model_context_length``:
    OpenRouter, Prime Intellect, where an error body instead raises in the
    caller's own indexing). ``timeout`` is a scalar read timeout -- metadata
    calls are small and fast, unlike chat completions. A connection-level
    failure raises ``RequestException`` either way, and a non-JSON body raises
    ``JSONDecodeError`` even on a 2xx.
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

    HTTP 429 (throttled) and 5xx (transient) are retryable, as is any
    non-HTTP failure (connection reset, timeout, DNS). Other 4xx
    (auth/validation) are permanent.
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
    generation LENGTH, since short responses in the same batch arrive
    normally. SSE keeps bytes flowing. The result is rebuilt into exactly the
    non-streamed shape so that NO downstream parsing (usage accounting, the
    ``content is None`` guard, the ``</think>`` split, logging hooks) forks on
    transport; streamed runs stay comparable with non-streamed ones. Sampling
    is server-side and untouched.

    ``response`` must be an open ``requests.post(..., stream=True)`` response.
    Returns ``{"choices": [{"message": {...}, "finish_reason": ...}],
    "usage": {...}, "model": ...}``, with ``reasoning_content`` present only
    if the server sent reasoning deltas. ``usage`` arrives only if the request
    sent ``stream_options: {"include_usage": true}``; otherwise it is empty
    (tolerated downstream, but the study loses its token counts).
    """
    content_parts: List[str] = []
    reasoning_parts: List[str] = []
    finish_reason: Optional[str] = None
    usage: Dict[str, Any] = {}
    reported_model: Optional[str] = None
    saw_reasoning = False
    saw_content = False

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        if not line.startswith("data:"):
            continue  # SSE comment/keepalive line
        payload = line[len("data:"):].strip()
        if payload == "[DONE]":
            break
        chunk = json.loads(payload)
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

    # NO content deltas -> content is None, NOT "". vLLM's non-streamed body
    # sends `"content": null` when a generation spends its whole budget in
    # the reasoning channel, and the caller has a dedicated early-return for
    # that case which retains the reasoning. Returning "" here would skip
    # that branch, so the two transports would disagree on retention for
    # exactly the cap-length population.
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

    ``smolbench.evals.parsing.parse_for`` yields both the extracted answer and
    a label for how the response disobeyed the prompt's output contract (None
    when it obeyed), and the two are recorded INDEPENDENTLY on each ``Mark``:
    ``score`` (1 correct / 0 wrong / None invalid) says whether the model was
    right, ``compliance`` whether it followed the format. Without that split,
    a right answer in the wrong shape (``"Answer: False"`` where a bare
    ``False`` was demanded) is indistinguishable from a wrong one -- which
    matters for the induction ``noise_intens`` arm, whose whitespace padding
    controls prompt LENGTH but measurably degrades instruction following. A
    response yielding no answer at all (empty, repetition collapse, truncated
    chain) scores None; recovery is deliberately conservative about long
    responses (see ``smolbench.evals.parsing``). ``log_invalid`` logs
    unparseable responses at INFO.
    """
    from smolbench.evals.parsing import parse_for

    mark_list: List[Mark] = []
    for q, (raw, reasoning) in zip(quiz, responses):
        try:
            parsed = parse_for(q, raw)
        except Exception as exc:  # noqa: BLE001 -- see below; deliberate
            # A parser bug must not destroy a run: this step runs after hours
            # of GPU time, and an exception here throws away work retrying
            # cannot recover.
            #
            # An unreadable response is exactly what `score=None` means, so
            # degrading to "invalid" loses nothing but the one mark. The raw
            # text is still stored for re-grading offline once the parser is
            # fixed.
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
        mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw,
                              reasoning=reasoning,
                              score=int(q.score(parsed.value)),
                              compliance=parsed.violation))
    return Marks(model=model, marks=tuple(mark_list))


def _render_progress(done: int, total: int, model: str, width: int = 30) -> None:
    """Render a single-line "N/total prompted" bar (no tqdm dependency).

    Driven by joblib's as-completed generator, so the bar advances as
    responses land, not as tasks dispatch. Emits a trailing newline once
    ``done >= total``.
    """
    filled: int = width if total == 0 else int(width * done / total)
    bar: str = "#" * filled + "-" * (width - filled)
    pct: float = 100.0 if total == 0 else 100.0 * done / total
    end: str = "\n" if done >= total else ""
    print(f"\r{model}: [{bar}] {done}/{total} prompted ({pct:3.0f}%)", end=end, flush=True)


@dataclass(frozen=True)
class ChatResult:
    """Hold the full per-call response from :meth:`ChatClient.complete`.

    A superset of the ``(content, reasoning)`` 2-tuple
    :meth:`ChatClient.query` returns, for callers needing usage, the reported
    model id, or the finish reason. Every field is populated DEFENSIVELY via
    ``.get`` chains: some SageMaker containers omit ``usage`` entirely and not
    every server echoes ``model``/``finish_reason``, so absence is
    non-exceptional, never a ``KeyError``.
    """

    #: The message content. Empty string on the server's null-content path
    #: (see ``ChatClient.complete``'s empty-content warning branch).
    content: str
    #: Reasoning-channel text: server-reported (``reasoning_content`` /
    #: ``reasoning``) or client-side-split from a plain-text ``<think>``
    #: block (see the module docstring). None when neither is present.
    reasoning: Optional[str]
    #: ``usage.prompt_tokens``; 0 when ``usage`` is absent or omits the field.
    prompt_tokens: int
    #: ``usage.completion_tokens``; 0 when ``usage`` is absent or omits the
    #: field.
    completion_tokens: int
    #: ``usage.prompt_tokens_details.cached_tokens``. OpenRouter/OpenAI
    #: report Anthropic/OpenAI prompt-cache hits here; 0 when absent.
    cached_prompt_tokens: int
    #: ``usage.total_tokens``; None when ``usage`` is absent or omits the
    #: field. This is the field ``ChatClient.complete``'s context-length
    #: guard reads -- see that method for why it tolerates absence.
    total_tokens: Optional[int]
    #: ``body["model"]`` when the server echoes it back in the response,
    #: else the model id that was requested (some containers -- and the
    #: empty-content path -- don't echo one back).
    model: str
    #: ``choices[0].finish_reason`` (e.g. ``"stop"``, ``"length"``); None
    #: when the server omits it.
    finish_reason: Optional[str]


@dataclass(frozen=True)
class ChatClient:
    """Represent one OpenAI-compatible chat-completions endpoint family.

    Providers configure the deltas; the retry loop, response parsing and
    parallel evaluation live here once. All ``Callable`` fields are resolved
    at CALL time, never import time, so environment changes (a re-provisioned
    EC2 instance, a refreshed SageMaker token) take effect without re-import.
    """

    #: Human-readable provider name, used as the log-line prefix.
    name: str
    #: Env-var prefix P: ``{P}_INFO``, ``{P}_INFO_RESPONSE`` (verbose logging)
    #: and ``{P}_MAX_PARALLEL_REQUESTS`` (evaluate's default fan-out, default
    #: 8) are read from the environment at call time.
    env_prefix: str
    #: model -> (chat-completions URL, bearer token). This is called once
    #: per request ATTEMPT, so endpoints that move between retries (an EC2
    #: spot instance re-provisioned under a new IP) get picked up mid-loop,
    #: and the URL and token always come from one consistent snapshot.
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
    #: request (e.g. Prime Intellect's ``X-Prime-Team-ID`` billing-routing
    #: header). This is resolved at CALL time, once per request attempt,
    #: for the same reason as ``connection``. On a key collision the
    #: client's own ``Authorization``/``Content-Type`` pair wins; extra
    #: headers must never silently clobber auth.
    extra_headers: Callable[[str], Dict[str, str]] = _no_extra_headers
    #: Seconds slept between retryable failures.
    retry_backoff_s: int = 60
    #: Connect timeout, kept SHORT and separate from the read timeout. A
    #: generous scalar timeout would make a dead endpoint blackhole every
    #: connect for the full read budget before retrying.
    connect_timeout_s: float = 10.0
    #: Default per-request read timeout; long CoT generations may need the
    #: per-call ``request_timeout`` override instead.
    read_timeout_s: int = 120
    #: When set, this many CONSECUTIVE connection-level failures (never HTTP
    #: errors) abort the retry loop via ``on_unreachable``. This is for
    #: self-managed endpoints that can genuinely vanish (spot reclaim,
    #: caller-IP drift). None (default) retries forever, correct for
    #: managed APIs.
    max_connection_failures: Optional[int] = None
    #: Diagnosis hook raising an actionable error once the failure cap trips.
    on_unreachable: Optional[Callable[[Exception], NoReturn]] = None

    def _flag(self, suffix: str) -> bool:
        """Read boolean env flag ``{env_prefix}_{suffix}`` at call time."""
        return bool(int(os.getenv(f"{self.env_prefix}_{suffix}", "0")))

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
        guard and logging; ``query()`` is a thin wrapper narrowing the result
        to ``(content, reasoning)``.

        Parameters
        ----------
        seed : int
            Decoding seed, sent with every request. This repo's rule is
            seeded, reproducible generations; never drop it to dodge an error.
        system : str, optional
            Extra per-call system message. Message order is ``[provider
            system_prompt(model), system, user prompt]``: the provider-level
            prompt goes FIRST because it carries deploy-spec toggles (e.g.
            Nemotron's "detailed thinking on"; see ``EC2_DEPLOY_SPECS``) that
            a per-call system message must layer onto, never shadow.
        context_length : int, optional
            Token-budget guard: raises ``ValueError`` when the response
            reports ``usage.total_tokens`` above this value. Pass
            ``get_model_context_length(model)``; the default 0 fails any
            usage-reporting response, so direct callers must supply one.
        extra_args : dict, optional
            Merged into the request body (e.g. ``max_completion_tokens``,
            ``reasoning_effort``).
        request_timeout : int, optional
            Per-request read timeout in seconds, overriding the client's
            ``read_timeout_s``. Raise it so long CoT generations complete on
            attempt 1.
        max_retries : int, optional
            Caps retryable failures (HTTP 429/5xx or connection-level) at N;
            the Nth re-raises the last error instead of sleeping again. None
            (default) retries them indefinitely, while non-retryable errors
            (4xx other than 429) always raise on first occurrence regardless.
            ``max_connection_failures``/``on_unreachable`` takes precedence
            when it trips first; when THIS cap exhausts first on a
            connection-level failure (a smaller retry budget, e.g. the Lean
            sweep's 4 vs EC2's 10), ``on_unreachable`` still fires before the
            re-raise, so a vanished self-managed endpoint is diagnosed (spot
            reclaim, caller-IP drift) rather than surfaced as a generic
            connection error.

        Raises
        ------
        requests.exceptions.RequestException
            A non-retryable HTTP error (4xx other than 429), or any retryable
            HTTP/connection failure once ``max_retries`` is exhausted.
        RuntimeError
            ``max_connection_failures`` consecutive connection-level failures
            tripped first; this takes precedence over ``max_retries``.
        ValueError
            The response reports ``usage.total_tokens`` above
            ``context_length``.
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

        # OPT-IN streaming transport, off by default. When set, the request
        # asks for SSE, and the chunks are reassembled into the ordinary
        # response shape (see ``collect_stream``). The study's data path
        # does not fork. This is enabled per LANE, never globally: rows
        # already on disk came over the non-streamed path, so flipping the
        # default would split the transport under existing data.
        stream: bool = self._flag("STREAM_COMPLETIONS")

        attempt: int = 0
        connection_failures: int = 0
        # Counts every retryable failure (connection-level OR HTTP
        # 429/5xx), independent of `connection_failures` (which counts only
        # non-HTTP connection failures, for the separate
        # max_connection_failures escalation below). This stays its own
        # counter, so the two caps -- which serve different callers (a
        # self-managed endpoint that can vanish vs. any caller that wants a
        # hard retry ceiling) -- can't interfere with each other's
        # bookkeeping.
        retry_failures: int = 0
        while True:
            attempt += 1
            # Resolved per attempt -- see the ``connection`` field docs.
            url, token = self.connection(model)
            try:
                response = requests.post(
                    url=url,
                    # Extra headers first, base pair second: on collision
                    # the base Authorization/Content-Type wins (see the
                    # ``extra_headers`` field docs).
                    headers=self.extra_headers(model) | {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=(
                        {
                            "model": self.body_model(model),
                            "messages": messages,
                            "seed": seed,
                        }
                        | (extra_args if extra_args else {})
                        # This applies AFTER extra_args, so the transport is
                        # decided here and cannot be silently overridden by
                        # a caller's sampling arguments. include_usage
                        # carries the token counters on the final chunk;
                        # without it a streamed row would lose
                        # prompt/completion tokens.
                        | ({"stream": True, "stream_options": {"include_usage": True}}
                           if stream else {})
                    ),
                    timeout=(
                        self.connect_timeout_s,
                        request_timeout or self.read_timeout_s,
                    ),
                    stream=stream,
                )
                # The server answered, so the endpoint is alive: only
                # SUSTAINED connection failures count toward unreachable.
                connection_failures = 0

                if not response.ok:
                    # Surface the API's error body, not just the status
                    # line. Most provider 4xx errors carry the actionable
                    # detail (context-too-long, invalid model id, billing)
                    # in the JSON body, and callers persist str(err) into
                    # durable artifacts (e.g. the Lean sweep's exception
                    # rows). ``response=`` stays attached:
                    # is_retryable_request_error reads
                    # ``err.response.status_code`` to classify the failure
                    # as retryable (429/5xx) or permanent.
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
                # This function reads usage/model/finish_reason once here
                # and reuses them on both the empty-content and
                # normal-content return paths, so ChatResult is populated
                # defensively (`.get` chains) even when `usage` is entirely
                # absent (some SageMaker containers omit it; see the module
                # docstring).
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
                    # Design: never hardcode reasoning=None here. That
                    # would turn a reasoning-only cap-hit (server spends
                    # the whole budget in the reasoning channel and returns
                    # content=null) into an indistinguishably empty row and
                    # destroyed real generations. This was measured live as
                    # a 106,545-character reasoning body collapsed to a "1
                    # chars" empty result. The reasoning channel is now read
                    # with the same key handling as the normal branch below,
                    # so the streamed and non-streamed transports agree on
                    # retention, instead of disagreeing on which spelling of
                    # the channel they honor. `content` deliberately stays
                    # "" here: study-side scoring reads content only, so a
                    # cap-hit still grades as an empty/failed candidate
                    # rather than a proof. Only the raw reasoning text is
                    # preserved, not the pass/fail outcome.
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
                    # Plain-text think block (no server-side reasoning
                    # parser): split the channels so scoring sees only the
                    # answer. See the module docstring.
                    reasoning, _, content = content.partition("</think>")
                    reasoning = reasoning.removeprefix("<think>").strip()
                    content = content.lstrip()
                # Usage may be omitted by some servers; only guard when a
                # token count is actually reported.
                if total_tokens is not None and total_tokens > context_length:
                    raise ValueError(f"Response:\n{body}\n was {total_tokens} > {context_length}")
                if self._flag("INFO"):
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
                if self.max_connection_failures is not None and not isinstance(
                    err, requests.exceptions.HTTPError
                ):
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
                        # Nth retryable failure: stop spinning and surface
                        # the error instead of sleeping again (see the
                        # max_retries parameter doc). When the terminal
                        # failure is connection-level and the client has an
                        # ``on_unreachable`` diagnosis hook, route through it
                        # first. A caller-supplied retry cap smaller than
                        # ``max_connection_failures`` (the Lean sweep's
                        # default 4 vs EC2's 10) would otherwise exhaust
                        # before the hook ever fires, and the actionable
                        # spot-reclaim/IP-drift diagnosis would be lost to a
                        # generic connection error. Bare `raise` re-raises
                        # the RequestException already being handled.
                        if (
                            self.on_unreachable is not None
                            and connection_failures > 0
                            and not isinstance(err, requests.exceptions.HTTPError)
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

        A thin wrapper over ``complete()`` -- see it for the parameter docs
        and the ``ChatResult`` fields this discards. ``reasoning`` is the
        server's separate channel or the client-side-split ``<think>`` block,
        None when absent.
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

        Results stream back out of order (``return_as="generator_unordered"``),
        so the index lets ``evaluate`` restore quiz order before scoring.
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
        ``seed``, streams completions into a live "N/total prompted" bar
        (``show_progress``, default True), then grades them back in quiz
        order: one ``Mark`` per question, ``score`` 1/0/None (None = the
        response could not be conditioned into an ``Answer``).

        ``max_parallel`` defaults to ``{env_prefix}_MAX_PARALLEL_REQUESTS``
        (8). CoT runs may lower it and raise ``request_timeout``, so the
        longest chain finishes on attempt 1; otherwise long generations time
        out under contention and the measured CoT-length distribution gets
        censored from the top. ``extra_args``/``request_timeout`` are
        forwarded to every ``query``.
        """
        ctx_len: int = self.context_length(model)
        total: int = len(quiz)
        max_workers: int = max(1, min(total, max_parallel or self._default_max_parallel()))

        # Stream results as they complete, so the progress bar reflects
        # finished prompts. Each result carries its index, so quiz order is
        # restored.
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
