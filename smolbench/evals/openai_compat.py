"""
Shared OpenAI-compatible Chat Completions client used by every provider.

All smolbench inference providers (OpenRouter, Prime Intellect, AWS
Bedrock/SageMaker, self-provisioned EC2 vLLM) speak the same
``/chat/completions`` dialect; they differ only in how the endpoint is
resolved and authenticated, and in a handful of policy knobs (timeouts,
retry backoff, connection-failure escalation). Each provider module builds
one :class:`ChatClient` and re-exports its bound ``query``/``evaluate`` as
the module-level functions that ``smolbench.evals.provider`` dispatches to,
so a fix or feature added here reaches every provider at once.

Unified response handling (the superset of what the providers had grown
separately, so no provider loses behavior):

- The reasoning channel is read from ``message.reasoning_content`` first
  (vLLM/Bedrock/SageMaker) and falls back to ``message.reasoning``
  (OpenRouter/Prime Intellect).
- When no server-side reasoning channel is present but the content carries a
  plain-text ``<think>...</think>`` block (models whose tokenizers have no
  think token ids, e.g. Nemotron-Ultra and Olmo-Think -- see the
  ``EC2_DEPLOY_SPECS`` notes in ``smolbench.evals.ec2``), the block is split
  out client-side so scoring sees only the answer.
- The ``usage.total_tokens`` context guard only fires when the server
  actually reports usage (some SageMaker containers omit it).
- Timeouts are a ``(connect, read)`` pair: a short connect timeout fails
  fast on a dead endpoint while a long read timeout lets slow chain-of-
  thought generations finish on attempt 1 instead of surviving only via the
  retry lottery (which would censor the CoT-length distribution from the
  top).

Per-call tuning (``max_parallel``, ``request_timeout``, ``show_progress``)
is therefore available under EVERY provider, keeping providers substitutable
behind ``INFERENCE_PROVIDER``.
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple

import requests
from joblib import Parallel, delayed

from smolbench.evals import Answer, Quiz, Mark, Marks

#: HTTP timeout (seconds) for provider METADATA requests -- catalog listings
#: (e.g. ``GET /models``) and context-length lookups -- as distinct from chat
#: completions, which use ``ChatClient.connect_timeout_s`` /
#: ``read_timeout_s`` (or the per-call ``request_timeout`` override) because
#: those must tolerate slow chain-of-thought generations. Metadata calls
#: return a small, fast payload, so one shared constant covers every
#: provider's catalog/context-length lookup instead of each module
#: hardcoding its own ``timeout=120`` literal.
METADATA_TIMEOUT_S: int = 120


def is_retryable_request_error(err: requests.exceptions.RequestException) -> bool:
    """Returns whether a chat-completions request error should be retried.

    HTTP 429 (throttled) and 5xx (transient server trouble) are retryable, as
    is any non-HTTP request failure (connection reset, timeout, DNS); other
    HTTP codes (4xx auth/validation errors) are permanent and re-raised.
    """
    if isinstance(err, requests.exceptions.HTTPError):
        response = err.response
        if response is None:
            return True
        return response.status_code == 429 or 500 <= response.status_code < 600
    return True


def _identity_body_model(model: str) -> str:
    """Default: the caller-facing model id goes in the request body verbatim."""
    return model


def _no_system_prompt(model: str) -> Optional[str]:
    """Default: no provider-injected system prompt for any model."""
    return None


def grade(quiz: Quiz, responses: List[Tuple[str, Optional[str]]], model: str,
          log_invalid: bool = False) -> Marks:
    """Grades raw (content, reasoning) responses against a quiz.

    Each response is conditioned by its question's ``QnA.condition``; a
    ``ValueError`` there means the response could not be turned into an
    ``Answer`` and the question is marked invalid (``score=None``) rather
    than wrong -- ``Marks.invalid`` counts these separately downstream.

    Parameters
    ----------
    quiz:
        The questions, in the order they were asked.
    responses:
        One ``(content, reasoning)`` pair per question, in quiz order.
    model:
        Model identifier recorded on the returned ``Marks``.
    log_invalid:
        When True, conditioning failures are logged at INFO level.

    Returns
    -------
    A ``Marks`` with one ``Mark`` per question (score 1 correct / 0 wrong /
    None invalid).
    """
    mark_list: List[Mark] = []
    for q, (raw, reasoning) in zip(quiz, responses):
        try:
            conditioned: Answer = q.condition(raw)
        except ValueError as e:
            if log_invalid:
                logging.info(e)
            mark_list.append(Mark(query=q.prompt, answer=q.answer,
                                  response=raw, reasoning=reasoning, score=None))
            continue
        mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw,
                              reasoning=reasoning, score=int(q.score(conditioned))))
    return Marks(model=model, marks=tuple(mark_list))


def _render_progress(done: int, total: int, model: str, width: int = 30) -> None:
    """Renders a single-line "N/total prompted" bar (no tqdm dependency).

    Driven by joblib's as-completed generator, so the bar advances as each
    prompt's response actually lands -- not merely as tasks are dispatched.
    A trailing newline is emitted once the run is complete.
    """
    filled: int = width if total == 0 else int(width * done / total)
    bar: str = "#" * filled + "-" * (width - filled)
    pct: float = 100.0 if total == 0 else 100.0 * done / total
    end: str = "\n" if done >= total else ""
    print(f"\r{model}: [{bar}] {done}/{total} prompted ({pct:3.0f}%)", end=end, flush=True)


@dataclass(frozen=True)
class ChatClient:
    """One OpenAI-compatible chat-completions endpoint family.

    Providers configure the deltas; the retry loop, response parsing, and
    parallel evaluation live here once. All ``Callable`` fields are plain
    functions resolved at CALL time, never import time, so environment
    changes (a re-provisioned EC2 instance, a refreshed SageMaker token)
    take effect without re-importing anything.
    """

    #: Human-readable provider name, used as the log-line prefix.
    name: str
    #: Env-var prefix P: ``{P}_INFO``, ``{P}_INFO_RESPONSE`` (verbose logging)
    #: and ``{P}_MAX_PARALLEL_REQUESTS`` (evaluate's default fan-out, default
    #: 8) are read from the environment at call time.
    env_prefix: str
    #: model -> (chat-completions URL, bearer token). Called once per request
    #: ATTEMPT so endpoints that move between retries (an EC2 spot instance
    #: re-provisioned under a new IP) are picked up mid-loop, and so the URL
    #: and token always come from one consistent snapshot.
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
    #: Seconds slept between retryable failures.
    retry_backoff_s: int = 60
    #: Connect timeout, kept SHORT and separate from the read timeout: a
    #: generous scalar timeout would make a dead endpoint blackhole every
    #: connect for the full read budget before retrying.
    connect_timeout_s: float = 10.0
    #: Default per-request read timeout; long CoT generations may need the
    #: per-call ``request_timeout`` override instead.
    read_timeout_s: int = 120
    #: When set, this many CONSECUTIVE connection-level failures (never HTTP
    #: errors) abort the retry loop via ``on_unreachable`` -- for self-managed
    #: endpoints that can genuinely vanish (spot reclaim, caller-IP drift).
    #: None (default) retries forever, correct for managed APIs.
    max_connection_failures: Optional[int] = None
    #: Diagnosis hook raising an actionable error once the failure cap trips.
    on_unreachable: Optional[Callable[[Exception], NoReturn]] = None

    def _flag(self, suffix: str) -> bool:
        """Reads boolean env flag ``{env_prefix}_{suffix}`` at call time."""
        return bool(int(os.getenv(f"{self.env_prefix}_{suffix}", "0")))

    def _default_max_parallel(self) -> int:
        return int(os.getenv(f"{self.env_prefix}_MAX_PARALLEL_REQUESTS", "8"))

    def query(
        self,
        prompt: str,
        model: str,
        seed: int,
        context_length: int = 0,
        extra_args: Optional[Dict[str, Any]] = None,
        request_timeout: Optional[int] = None,
    ) -> Tuple[str, Optional[str]]:
        """Queries ``model`` once, retrying transient failures indefinitely.

        Parameters
        ----------
        prompt:
            The user message posed to the LLM.
        model:
            Provider-specific model id.
        seed:
            Decoding seed, sent with every request (repo rule: seeded,
            reproducible generations -- never drop it to dodge an error).
        context_length:
            Token-budget guard: raises ``ValueError`` when the response
            reports ``usage.total_tokens`` above this. Pass
            ``get_model_context_length(model)``; the default 0 fails any
            usage-reporting response, so direct callers must supply it.
        extra_args:
            Extra key/values merged into the request body (e.g.
            ``max_completion_tokens``, ``reasoning_effort``).
        request_timeout:
            Per-request read timeout in seconds; falls back to the client's
            ``read_timeout_s``. Raise it for long CoT generations so they
            complete on attempt 1.

        Returns
        -------
        ``(content, reasoning)``: the message content, and the model's
        separate reasoning channel (or client-side-split ``<think>`` block)
        or None when absent.
        """
        sys_prompt = self.system_prompt(model)
        messages: List[Dict[str, str]] = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.append({"role": "user", "content": prompt})

        attempt: int = 0
        connection_failures: int = 0
        while True:
            attempt += 1
            # Resolved per attempt -- see the ``connection`` field docs.
            url, token = self.connection(model)
            try:
                response = requests.post(
                    url=url,
                    headers={
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
                    ),
                    timeout=(
                        self.connect_timeout_s,
                        request_timeout or self.read_timeout_s,
                    ),
                )
                # The server answered, so the endpoint is alive: only
                # SUSTAINED connection failures count toward unreachable.
                connection_failures = 0

                if not response.ok:
                    logging.info(response.text)

                response.raise_for_status()
                body = response.json()
                if self._flag("INFO") and self._flag("INFO_RESPONSE"):
                    logging.info(body)

                msg = body["choices"][0]["message"]
                if msg["content"] is None:
                    logging.warning("Body returned none value: \n" f"{body}")
                    return "", None
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
                usage = body.get("usage") or {}
                tokens = usage.get("total_tokens")
                if tokens is not None and tokens > context_length:
                    raise ValueError(f"Response:\n{body}\n was {tokens} > {context_length}")
                if self._flag("INFO"):
                    logging.info(f"Response:\n{body}\n was {tokens} <= {context_length}")
                return content, reasoning

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
                logging.info(
                    f"{self.name} request failed on attempt {attempt}: {err}. "
                    f"Retrying in {self.retry_backoff_s} seconds."
                )
                time.sleep(self.retry_backoff_s)

    def _indexed_query(self, index: int, *args: Any, **kwargs: Any) -> Tuple[int, Tuple[str, Optional[str]]]:
        """``query()`` tagged with its quiz index.

        Results stream back out of order (``return_as="generator_unordered"``);
        the index lets ``evaluate`` restore quiz order before scoring.
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
        """Evaluates ``model`` on one quiz (a sequence of ``QnA`` questions).

        All questions are queried in parallel threads with the shared
        decoding ``seed``, streaming completions into a live progress bar,
        then graded in quiz order.

        Parameters
        ----------
        quiz:
            The questions to pose (ONE quiz; each element is a ``QnA``).
        model:
            Provider-specific model id.
        seed:
            Decoding seed shared by every request in the quiz.
        extra_args:
            Extra request-body key/values, forwarded to every ``query``.
        max_parallel:
            Fan-out cap; defaults to ``{env_prefix}_MAX_PARALLEL_REQUESTS``
            (8). CoT runs may lower it and raise ``request_timeout`` so the
            longest chain finishes on attempt 1 -- otherwise long generations
            time out under contention and the measured CoT-length
            distribution gets censored from the top.
        request_timeout:
            Per-request read-timeout override, forwarded to every ``query``.
        show_progress:
            Prints a live "N/total prompted" bar as responses land.

        Returns
        -------
        A ``Marks`` whose per-question ``Mark.score`` is 1/0 for
        correct/incorrect and None when the response could not be
        conditioned into an ``Answer``.
        """
        ctx_len: int = self.context_length(model)
        total: int = len(quiz)
        max_workers: int = max(1, min(total, max_parallel or self._default_max_parallel()))

        # Stream results as they complete so the progress bar reflects
        # finished prompts; each carries its index so quiz order is restored.
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
