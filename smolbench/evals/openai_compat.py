"""
Shared OpenAI-compatible Chat Completions client used by every provider.

All smolbench inference providers (OpenRouter, Prime Intellect, AWS
Bedrock/SageMaker, self-provisioned EC2 vLLM) speak the same
``/chat/completions`` dialect; they differ only in how the endpoint is
resolved and authenticated, and in a handful of policy knobs (timeouts,
retry backoff, connection-failure escalation). Each provider module builds
one :class:`ChatClient` and re-exports its bound ``query``/``complete``/
``evaluate`` as the module-level functions that ``smolbench.evals.provider``
dispatches to, so a fix or feature added here reaches every provider at once.
``complete`` returns the full :class:`ChatResult` (content, reasoning, token
usage, server-reported model id, finish reason); ``query`` is a thin wrapper
narrowing that down to the ``(content, reasoning)`` 2-tuple every existing
caller (provider modules, ``evaluate``, the notebooks) relies on -- new
callers that need usage or a bounded ``max_retries`` (e.g. a Lean sweep
runner) should call ``complete`` directly instead.

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

from smolbench.evals import Quiz, Mark, Marks

#: HTTP timeout (seconds) for provider METADATA requests -- catalog listings
#: (e.g. ``GET /models``) and context-length lookups -- as distinct from chat
#: completions, which use ``ChatClient.connect_timeout_s`` /
#: ``read_timeout_s`` (or the per-call ``request_timeout`` override) because
#: those must tolerate slow chain-of-thought generations. Metadata calls
#: return a small, fast payload, so one shared constant covers every
#: provider's catalog/context-length lookup instead of each module
#: hardcoding its own ``timeout=120`` literal.
METADATA_TIMEOUT_S: int = 120


def metadata_get(url: str, api_key: str, *, check_status: bool, timeout: float = METADATA_TIMEOUT_S) -> Any:
    """Performs one bearer-authenticated metadata GET and returns its parsed JSON body.

    Extracted from four near-identical copies that had grown independently:
    OpenRouter's and Prime Intellect's ``get_model_context_length`` (a GET
    against ``/models/{model}/endpoints`` or ``/models/{model}``), and AWS's
    and EC2's ``list_models`` (a GET against ``/models``). All four built the
    same ``requests.get(url, headers={"Authorization": f"Bearer {key}"},
    timeout=...).json()`` call and differed only in the URL, the timeout
    (all four use ``METADATA_TIMEOUT_S`` today), and whether the response
    status is checked before parsing -- see the FIDELITY note below for why
    that last difference is preserved via ``check_status`` rather than
    unified. Each call site keeps its own URL construction, ``lru_cache``
    (where applicable), and JSON post-processing; this function only
    performs the GET and returns the raw parsed body.

    Parameters
    ----------
    url : str
        Fully-resolved request URL. Callers build this themselves since each
        provider's path shape differs (OpenRouter's
        ``/models/{model}/endpoints``, Prime Intellect's ``/models/{model}``,
        AWS/EC2's flat ``/models``).
    api_key : str
        Bearer token sent as ``Authorization: Bearer {api_key}``. Callers
        resolve this themselves (an env var, a state file, a minted
        short-lived token, ...); this function only shapes the header.
    check_status : bool
        When True, ``response.raise_for_status()`` is called before parsing,
        raising ``requests.exceptions.HTTPError`` on a 4xx/5xx response --
        this is today's ``list_models`` behavior (AWS, EC2). When False, the
        body is parsed as JSON regardless of status code -- this is today's
        ``get_model_context_length`` behavior (OpenRouter, Prime Intellect).
        Required (no default): every call site has an opinion here, and a
        silently-wrong default would be the kind of behavior change this
        extraction must not introduce. See the FIDELITY note.
    timeout : float, optional
        Read timeout in seconds, forwarded to ``requests.get`` as a scalar
        (no separate connect timeout -- metadata calls are small, fast
        lookups, unlike chat completions; see ``METADATA_TIMEOUT_S``).
        Defaults to ``METADATA_TIMEOUT_S``; pass an explicit value only if a
        call site's timeout genuinely diverges from that shared default.

    Returns
    -------
    Any
        ``response.json()`` -- the parsed JSON body, whatever shape the
        endpoint returns (a bare list, a dict with a top-level ``"data"``
        key, ...). Callers perform their own shape-specific post-processing
        (e.g. ``response["data"]["endpoints"][0]["context_length"]`` vs
        ``[m["id"] for m in response["data"]]``); this function does not
        interpret the body at all.

    Raises
    ------
    requests.exceptions.HTTPError
        Only when ``check_status`` is True and the response status is a
        4xx/5xx.
    requests.exceptions.RequestException
        A connection-level failure (timeout, DNS failure, connection reset),
        regardless of ``check_status``.
    requests.exceptions.JSONDecodeError
        The response body is not valid JSON. Reachable even when
        ``check_status`` is True, if the server returns a 2xx with a
        non-JSON body; when ``check_status`` is True and the status is an
        error, ``raise_for_status()`` raises first and ``.json()`` is never
        reached.

    Notes
    -----
    FIDELITY: the two context-length lookups (OpenRouter, Prime Intellect)
    deliberately do NOT check status before parsing -- an error response's
    JSON body flows straight into the caller's shape-specific indexing
    (``response["data"]["endpoints"][0]["context_length"]`` etc.), which
    raises its own ``KeyError``/``TypeError`` on a malformed or error-shaped
    body. This matches each provider's pre-extraction behavior under the
    retry machinery in ``ChatClient`` and is NOT a bug to "fix" here. The two
    ``list_models`` call sites (AWS, EC2) already DID check status before
    this extraction. ``check_status`` exists to preserve BOTH behaviors
    verbatim, one per call-site kind -- do not change either default when
    calling this function, and do not collapse the parameter to a single
    hardcoded choice.
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


def _no_extra_headers(model: str) -> Dict[str, str]:
    """Default: no provider-specific request headers beyond auth/content-type."""
    return {}


def grade(quiz: Quiz, responses: List[Tuple[str, Optional[str]]], model: str,
          log_invalid: bool = False) -> Marks:
    """Grades raw (content, reasoning) responses against a quiz.

    Each response goes through ``smolbench.evals.parsing.parse_for``, which
    returns both the extracted answer and a label for how the response
    disobeyed the prompt's output contract (None when it obeyed exactly).
    Those two results are recorded independently: ``score`` says whether the
    model was RIGHT, ``compliance`` says whether it followed the FORMAT.

    That separation is the point. Grading used to call ``QnA.condition``
    directly, so a right answer in the wrong shape (``"Answer: False"`` when
    the prompt demanded a bare ``False``) raised and scored as invalid --
    indistinguishable from a wrong answer. The induction ``noise_intens`` arm
    made that costly: it is supposed to control for prompt LENGTH only, but
    its whitespace padding measurably degrades instruction following, so a
    chunk of its marks were failing on formatting rather than reasoning.
    Recovering the answer while flagging the violation keeps both facts.

    A response that genuinely yields no answer -- empty, repetition collapse,
    or a reasoning chain truncated before any verdict -- still scores None.
    Recovery is deliberately conservative about long responses; see
    ``smolbench.evals.parsing``.

    Parameters
    ----------
    quiz:
        The questions, in the order they were asked.
    responses:
        One ``(content, reasoning)`` pair per question, in quiz order.
    model:
        Model identifier recorded on the returned ``Marks``.
    log_invalid:
        When True, unparseable responses are logged at INFO level.

    Returns
    -------
    A ``Marks`` with one ``Mark`` per question (score 1 correct / 0 wrong /
    None invalid), each carrying its ``compliance`` label.
    """
    from smolbench.evals.parsing import parse_for

    mark_list: List[Mark] = []
    for q, (raw, reasoning) in zip(quiz, responses):
        parsed = parse_for(q, raw)
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
class ChatResult:
    """Full per-call response from :meth:`ChatClient.complete`.

    A superset of the ``(content, reasoning)`` 2-tuple :meth:`ChatClient.query`
    has always returned: it adds token usage, the model id the server
    actually reports, and the finish reason. Introduced so callers that need
    more than content/reasoning -- e.g. a Lean theorem-proving sweep runner
    that budgets retries against token usage inside an open verification
    session -- don't have to change ``query()``'s signature or return type,
    which every existing provider module and notebook relies on (see
    ``ChatClient.query``).

    Every field is populated DEFENSIVELY from the response body (``.get``
    chains in ``ChatClient.complete``): some servers (certain SageMaker
    containers) omit ``usage`` entirely, and not every server echoes
    ``model``/``finish_reason``, so absence is a documented, non-exceptional
    case here rather than a ``KeyError``.
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
    #: ``usage.prompt_tokens_details.cached_tokens`` -- OpenRouter/OpenAI
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
    #: model -> extra request headers merged into every chat-completions
    #: request (e.g. Prime Intellect's ``X-Prime-Team-ID`` billing-routing
    #: header). Resolved at CALL time once per request attempt, same
    #: rationale as ``connection``. On a key collision the client's own
    #: ``Authorization``/``Content-Type`` pair wins -- extra headers must
    #: never be able to silently clobber auth.
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
        """Queries ``model`` once, returning the full response as a ``ChatResult``.

        This holds the message assembly, retry loop, ``<think>``-splitting,
        usage guard, and logging that used to live directly in ``query()``;
        ``query()`` is now a thin wrapper that narrows this method's
        ``ChatResult`` down to the ``(content, reasoning)`` 2-tuple every
        existing provider module, ``evaluate()``/``_indexed_query``, and the
        notebooks rely on (see ``query``'s docstring for that compatibility
        contract). New callers that need token usage, the server-reported
        model id, or a bounded retry count -- e.g. a Lean sweep runner that
        must not spin forever inside an open verification session -- should
        call this method directly.

        Parameters
        ----------
        prompt:
            The user message posed to the LLM.
        model:
            Provider-specific model id.
        seed:
            Decoding seed, sent with every request (repo rule: seeded,
            reproducible generations -- never drop it to dodge an error).
        system:
            Optional per-call system prompt. Design: message order is
            ``[provider system_prompt(model) (if any), system (if given),
            user prompt]`` -- the provider-level prompt goes FIRST because it
            carries deploy-spec toggles that must survive a per-call system
            message unshadowed (e.g. Nemotron's "detailed thinking on" CoT
            toggle; see ``EC2_DEPLOY_SPECS``), and the per-call ``system`` is
            additive context layered after it, never replacing it. The user
            prompt is always last.
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
        max_retries:
            Caps retryable failures (HTTP 429/5xx, or connection-level
            errors) at N: the Nth retryable failure re-raises the last error
            instead of sleeping again. None (default) preserves the original
            behavior of retrying retryable errors forever. Non-retryable
            errors (4xx other than 429) always raise immediately on first
            occurrence, regardless of this cap. The existing
            ``max_connection_failures``/``on_unreachable`` escalation is
            unchanged and takes precedence when it trips first -- this cap
            is only consulted afterward. When THIS cap exhausts first on a
            connection-level failure (a retry budget smaller than
            ``max_connection_failures``, e.g. the Lean sweep's 4 vs EC2's
            10), the ``on_unreachable`` diagnosis hook still fires before
            the re-raise, so a self-managed endpoint that vanishes is
            diagnosed (spot reclaim, caller-IP drift) rather than surfaced
            as a generic connection error. Intended for callers (e.g. a
            Lean verification sweep) that must bound how long a single
            query can spin against a wedged endpoint.

        Returns
        -------
        A ``ChatResult`` with the message content, reasoning channel, token
        usage (defensively defaulted when the server omits ``usage``), the
        model id the server reports (or the requested one), and the finish
        reason.

        Raises
        ------
        requests.exceptions.HTTPError
            A non-retryable HTTP error (4xx other than 429), or a retryable
            one (429/5xx) once ``max_retries`` is exhausted.
        requests.exceptions.RequestException
            A non-HTTP connection-level failure, once ``max_retries`` is
            exhausted (or immediately if not retryable).
        RuntimeError
            ``max_connection_failures`` consecutive connection-level
            failures tripped first (see the field's docs); takes precedence
            over ``max_retries``.
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

        attempt: int = 0
        connection_failures: int = 0
        # Counts every retryable failure (connection-level OR HTTP
        # 429/5xx), independent of `connection_failures` (which counts only
        # non-HTTP connection failures, for the separate
        # max_connection_failures escalation below). Kept as its own
        # counter so the two caps -- which serve different callers (a
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
                    # Extra headers first, base pair second: on collision the
                    # base Authorization/Content-Type wins (see the
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
                    # Surface the API's error body, not just the status line
                    # -- most provider 4xx errors carry the actionable detail
                    # (context-too-long, invalid model id, billing) in the
                    # JSON body, and callers persist str(err) into durable
                    # artifacts (e.g. the Lean sweep's exception rows).
                    # ``response=`` stays attached: is_retryable_request_error
                    # reads ``err.response.status_code`` to classify the
                    # failure as retryable (429/5xx) or permanent.
                    raise requests.exceptions.HTTPError(
                        f"{response.status_code} {response.reason} for url "
                        f"{response.url}: {response.text[:1000]}",
                        response=response,
                    )
                body = response.json()
                if self._flag("INFO") and self._flag("INFO_RESPONSE"):
                    logging.info(body)

                choice = body["choices"][0]
                msg = choice["message"]
                # Usage/model/finish_reason are read once here and reused on
                # both the empty-content and normal-content return paths, so
                # ChatResult is populated defensively (`.get` chains) even
                # when `usage` is entirely absent (some SageMaker containers
                # omit it -- see the module docstring).
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
                    return ChatResult(
                        content="",
                        reasoning=None,
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
                        # first: a caller-supplied retry cap smaller than
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
        """Queries ``model`` once, retrying transient failures indefinitely.

        Thin wrapper over ``complete()``: the positional signature and
        ``(content, reasoning)`` return type are UNCHANGED from before
        ``complete()`` existed (every provider module and the notebooks call
        this positionally), and ``system``/``max_retries`` are new
        keyword-only parameters appended at the end so no existing call
        site -- positional or keyword -- breaks. See ``complete()`` for the
        full parameter docs (including these two) and for the additional
        ``ChatResult`` fields (token usage, server-reported model,
        finish_reason) this wrapper discards; callers that need those should
        call ``complete()`` directly.

        Returns
        -------
        ``(content, reasoning)``: the message content, and the model's
        separate reasoning channel (or client-side-split ``<think>`` block)
        or None when absent.
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
