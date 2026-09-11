"""Share an OpenAI-compatible Chat Completions client across providers.

Reasoning uses either server channel or a ``<think>`` block so scoring sees
only answers. Missing usage and metadata are tolerated; missing message
content is a broken successful response, not a retryable one.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
from joblib import Parallel, delayed

from smolbench.evals import Mark, Marks, Quiz
from smolbench.evals.quiz import COMPLIANT

#: Metadata calls are small; completions need separate long read timeouts.
METADATA_TIMEOUT_S: int = 120


def metadata_get(url: str, api_key: str, *, check_status: bool) -> Any:
    """Fetch a bearer-authenticated metadata JSON body.

    Parameters
    ----------
    url : str
        Metadata endpoint URL.
    api_key : str
        Bearer token for the request.
    check_status : bool
        True raises before parsing (``list_models``: AWS, EC2).

    Returns
    -------
    Any
        Parsed JSON response body.

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
        timeout=METADATA_TIMEOUT_S,
    )
    if check_status:
        response.raise_for_status()
    return response.json()


def is_retryable_request_error(err: requests.exceptions.RequestException) -> bool:
    """Classify retryable chat-completions errors.

    Retry 429, 5xx, and non-HTTP failures; other 4xx are permanent.

    Parameters
    ----------
    err : requests.exceptions.RequestException
        Request failure to classify.

    Returns
    -------
    bool
        Whether the request should be retried.
    """
    if isinstance(err, requests.exceptions.HTTPError):
        response = err.response
        if response is None:
            return True
        return response.status_code == 429 or 500 <= response.status_code < 600
    return True


def collect_stream(response: requests.Response) -> Dict[str, Any]:
    """Reassemble SSE into the non-streamed response shape.

    Streaming keeps long generations from being dropped during a quiet socket.

    Parameters
    ----------
    response : requests.Response
        An open ``requests.post(..., stream=True)`` response.

    Returns
    -------
    dict
        Parsed stream containing choices and token usage.

    Raises
    ------
    requests.exceptions.ChunkedEncodingError
        A malformed SSE chunk.
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
        payload = line[len("data:") :].strip()
        if payload == "[DONE]":
            saw_done = True
            break
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError as err:
            # Preserve retry handling shared with truncated non-streamed bodies.
            raise requests.exceptions.ChunkedEncodingError(
                f"malformed SSE chunk: {payload[:200]!r}"
            ) from err
        reported_model = chunk.get("model") or reported_model
        # Usage-only final chunks have no choices.
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

    # A clean intermediary close must not grade a partial answer.
    if not saw_done and finish_reason is None:
        raise requests.exceptions.ChunkedEncodingError(
            "SSE stream ended without [DONE] or a finish_reason; body is incomplete"
        )

    # None matches vLLM's reasoning-only non-streamed response.
    message: Dict[str, Any] = {
        "content": "".join(content_parts) if saw_content else None
    }
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


def grade(
    quiz: Quiz,
    responses: List[Tuple[str, Optional[str]]],
    model: str,
    log_invalid: bool = False,
) -> Marks:
    """Grade ``(content, reasoning)`` responses in quiz order.

    Preserve compliance independently of score so malformed correct answers remain visible.

    Parameters
    ----------
    quiz : Quiz
        Questions whose responses are graded.
    responses : List[Tuple[str, Optional[str]]]
        Content and reasoning responses in quiz order.
    model : str
        Model whose response parser is selected.
    log_invalid : bool
        Log unparseable responses at INFO.

    Returns
    -------
    Marks
        Marks for the quiz responses.
    """
    from smolbench.evals.parsing import parse_for

    mark_list: List[Mark] = []
    for q, (raw, reasoning) in zip(quiz, responses):
        try:
            parsed = parse_for(q, raw)
        except Exception as exc:  # noqa: BLE001 -- preserve expensive runs.
            logging.warning(
                f"grade: parser raised on a response, marking invalid: "
                f"{type(exc).__name__}: {exc}"
            )
            mark_list.append(
                Mark(
                    query=q.prompt,
                    answer=q.answer,
                    response=raw,
                    reasoning=reasoning,
                    score=None,
                    compliance="parser-error",
                )
            )
            continue
        if parsed.value is None:
            if log_invalid:
                logging.info(
                    f"unparseable response ({parsed.violation}): {raw[:120]!r}"
                )
            mark_list.append(
                Mark(
                    query=q.prompt,
                    answer=q.answer,
                    response=raw,
                    reasoning=reasoning,
                    score=None,
                    compliance=parsed.violation,
                )
            )
            continue
        # Avoid treating a future falsy violation label as compliant.
        compliance = COMPLIANT if parsed.violation is None else parsed.violation
        mark_list.append(
            Mark(
                query=q.prompt,
                answer=q.answer,
                response=raw,
                reasoning=reasoning,
                score=int(q.score(parsed.value)),
                compliance=compliance,
            )
        )
    return Marks(model=model, marks=tuple(mark_list))


def _render_progress(done: int, total: int, model: str) -> None:
    """Render the completion progress bar.

    Parameters
    ----------
    done : int
        Number of completed prompts.
    total : int
        Total prompts being evaluated.
    model : str
        Model name shown in the bar.
    """
    filled: int = 30 if total == 0 else int(30 * done / total)
    filled_bar: str = "#" * filled + "-" * (30 - filled)
    pct: float = 100.0 if total == 0 else 100.0 * done / total
    end: str = "\n" if done >= total else ""
    print(
        f"\r{model}: [{filled_bar}] {done}/{total} prompted ({pct:3.0f}%)",
        end=end,
        flush=True,
    )


@dataclass(frozen=True)
class ChatResult:
    """Hold a complete chat response; missing usage metadata is normal."""

    #: Message content; empty for null content.
    content: str
    #: Server reasoning or client-split ``<think>`` text.
    reasoning: Optional[str]
    #: Prompt tokens; 0 when absent.
    prompt_tokens: int
    #: Completion tokens; 0 when absent.
    completion_tokens: int
    #: Cached prompt tokens; 0 when absent.
    cached_prompt_tokens: int
    #: Total tokens; None skips the context guard.
    total_tokens: Optional[int]
    #: Reported model or requested model.
    model: str
    #: Finish reason, if reported.
    finish_reason: Optional[str]


@dataclass(frozen=True)
class ChatClient:
    """Represent an OpenAI-compatible endpoint family.

    Resolve provider callables per request so refreshed endpoints take effect.
    """

    #: Log-line prefix.
    name: str
    #: Prefix for call-time configuration.
    env_prefix: str
    #: Model URL and token, resolved per attempt for moving endpoints.
    connection: Callable[[str], Tuple[str, str]]
    #: Model context window.
    context_length: Callable[[str], int]
    #: Request-body model id.
    body_model: Callable[[str], str] = _identity_body_model
    #: Provider system prompt, keeping user prompts byte-identical.
    system_prompt: Callable[[str], Optional[str]] = _no_system_prompt
    #: Extra headers; client auth/content type win on collisions.
    extra_headers: Callable[[str], Dict[str, str]] = _no_extra_headers
    #: Retry delay.
    retry_backoff_s: int = 60
    #: Short connect timeout so dead endpoints retry promptly.
    connect_timeout_s: float = 10.0
    #: Default read timeout; long generations may override it.
    read_timeout_s: int = 120
    #: Consecutive ConnectionError cap for vanish-prone endpoints; ReadTimeout
    #: and HTTP errors never count.
    max_connection_failures: Optional[int] = None
    #: Diagnosis hook for an unreachable endpoint.
    on_unreachable: Optional[Callable[[Exception], None]] = None

    def _flag(self, suffix: str) -> bool:
        """Read a call-time boolean environment flag.

        Parameters
        ----------
        suffix : str
            Suffix appended to ``env_prefix`` to form the environment-variable name.

        Returns
        -------
        bool
            The parsed flag value.
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
        """Query a model and return its complete response.

        Extra arguments cannot override the seed or streaming keys.

        Parameters
        ----------
        prompt : str
            User prompt to send.
        model : str
            Model to query.
        seed : int
            Decoding seed, sent with every request.
        system : str, optional
            Extra system message.
        context_length : int, optional
        Token budget used to warn when responses approach the limit.
        extra_args : dict, optional
            Merged into the request body (e.g.
        request_timeout : int, optional
            Per-request read timeout in seconds, overriding ``read_timeout_s``.
        max_retries : int, optional
            Cap on retryable failures (HTTP 429/5xx or connection-level).

        Returns
        -------
        ChatResult
            Full chat-completion result.

        Raises
        ------
        requests.exceptions.RequestException
            A non-retryable HTTP error (4xx other than 429).
        RuntimeError
            ``max_connection_failures`` consecutive connection-level failures tripped first.
        """
        sys_prompt = self.system_prompt(model)
        messages: List[Dict[str, str]] = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        if system:
            # Provider instructions must precede caller instructions.
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Per-lane streaming preserves existing non-streamed rows.
        stream: bool = self._flag("STREAM_COMPLETIONS")

        attempt: int = 0
        connection_failures: int = 0
        # Keep retry and connection caps independent.
        retry_failures: int = 0
        while True:
            attempt += 1
            # Re-resolve moving endpoints each attempt.
            url, token = self.connection(model)
            try:
                # Always release streamed sockets.
                with requests.post(
                    url=url,
                    # Client auth/content type win on collisions.
                    headers=self.extra_headers(model)
                    | {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=(
                        {"model": self.body_model(model), "messages": messages}
                        | (extra_args if extra_args else {})
                        # Preserve seed and streamed usage over caller additions.
                        | {"seed": seed}
                        | (
                            {"stream": True, "stream_options": {"include_usage": True}}
                            if stream
                            else {}
                        )
                    ),
                    timeout=(
                        self.connect_timeout_s,
                        request_timeout or self.read_timeout_s,
                    ),
                    stream=stream,
                ) as response:
                    # A response proves the endpoint is reachable.
                    connection_failures = 0

                    if not response.ok:
                        # Retain actionable error bodies and retry status.
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
                # Usage is absent from some containers.
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
                    # Retain reasoning from a cap-hit response.
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
                    # Score only the answer when no reasoning channel exists.
                    reasoning, _, content = content.partition("</think>")
                    reasoning = reasoning.removeprefix("<think>").strip()
                    content = content.lstrip()
                # Paid responses still return for grading after a guard warning.
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
                    logging.info(
                        f"Response:\n{body}\n was {total_tokens} <= {context_length}"
                    )
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
                # ReadTimeouts may be slow generation, not endpoint loss.
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
                        # Diagnose exhausted connection failures first.
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
        """Query a model for content and reasoning.

        Parameters
        ----------
        prompt : str
            User prompt sent to the model.
        model : str
            Model to query.
        seed : int
            Decoding seed.
        context_length : int, optional
            Token-budget guard passed to ``complete()``.
        extra_args : Optional[Dict[str, Any]], optional
            Extra request-body arguments passed to ``complete()``.
        request_timeout : Optional[int], optional
            Per-request read timeout passed to ``complete()``.
        system : Optional[str], optional
            Extra system message passed to ``complete()``.
        max_retries : Optional[int], optional
            Retry cap passed to ``complete()``.

        Returns
        -------
        Tuple[str, Optional[str]]
            content and reasoning.
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

    def _indexed_query(
        self, index: int, *args: Any, **kwargs: Any
    ) -> Tuple[int, Tuple[str, Optional[str]]]:
        """Tag a query result with its quiz position.

        The index restores order from unordered parallel results.

        Parameters
        ----------
        index : int
            Question's quiz position.
        *args : Any
            Positional arguments forwarded to ``query()``.
        **kwargs : Any
            Keyword arguments forwarded to ``query()``.

        Returns
        -------
        Tuple[int, Tuple[str, Optional[str]]]
            the quiz position and ``query()`` result.
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
        """Evaluate and grade a model on one quiz.

        Parameters
        ----------
        quiz : Quiz
            Questions to evaluate.
        model : str
            Model to query and grade.
        seed : int
            Shared decoding seed.
        extra_args : dict, optional
            Forwarded to every ``query``, as is ``request_timeout``.
        max_parallel : int, optional
            Thread fan-out; defaults to ``{env_prefix}_MAX_PARALLEL_REQUESTS`` (8).
        request_timeout : Optional[int], optional
            Per-request timeout forwarded to ``query``.
        show_progress : bool
            Print a live "N/total prompted" bar (default True).

        Returns
        -------
        Marks
            Marks for every quiz question.
        """
        ctx_len: int = self.context_length(model)
        total: int = len(quiz)
        max_workers: int = max(
            1, min(total, max_parallel or self._default_max_parallel())
        )

        # Preserve quiz order after unordered completion.
        results_by_index: Dict[int, Tuple[str, Optional[str]]] = {}
        completed: int = 0
        if show_progress:
            _render_progress(completed, total, model)
        stream = Parallel(
            n_jobs=max_workers, prefer="threads", return_as="generator_unordered"
        )(
            delayed(self._indexed_query)(
                i,
                q.prompt,
                model,
                seed,
                ctx_len,
                extra_args=extra_args,
                request_timeout=request_timeout,
            )
            for i, q in enumerate(quiz)
        )
        for index, resp in stream:
            results_by_index[index] = resp
            completed += 1
            if show_progress:
                _render_progress(completed, total, model)
        responses: List[Tuple[str, Optional[str]]] = [
            results_by_index[i] for i in range(total)
        ]

        return grade(quiz, responses, model, log_invalid=self._flag("INFO"))
