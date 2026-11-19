"""Client half of the vLLM-prefill attention-capture contract, independent of any results store.

The on-box half is ``payloads/attention_capture_plugin.py.txt``; the wire
contract between the two is ``payloads/ATTENTION_CAPTURE_CONTRACT.md``. This
module holds everything the client needs to drive it:

1. ``Job`` and ``mass_job``: one capture request, i.e. the exact prompt and
   completion token ids, the self-consistency gate positions, the per-token
   key classes (``token_classes``) and the stem key its arrays are uploaded
   under (``rank_keys`` names the real per-rank objects);
2. ``presign_put``: mints the presigned PUT URLs through which the box uploads
   straight into the bucket without holding credentials;
3. ``run_capture_batches``: drives the box's ``/attn`` endpoint in batches,
   polls ``/status`` (which also feeds the box's idle watchdog), and gates each
   job twice, once on what the box reported and once on what actually landed in
   the bucket (``verify_capture_uploads``).

Nothing here knows how a caller stores or names its results. The caller
supplies the token sequences, the keys, an S3 client factory and any manifest
it wants to keep. The bucket is treated as APPEND-ONLY: a presigned PUT
silently replaces an existing object, so ``run_capture_batches`` lists every
job's keys first and never sends a job that already has one (see
``job_keys_present``). This module never writes to the bucket itself (the box
uploads) and never deletes.

One opt-in exception to the skip, ``fill=True``: a run that was cut short (the
engine died, a rank lost its upload) leaves stems with SOME of their objects.
Fill mode completes such a stem instead of skipping it, but only when
``fill_refusal`` finds the existing objects compatible with this run (same mode,
same capture version, same tensor-parallel degree, no rank outside
``0 .. tp - 1``). The box then answers a PUT for an object that exists with
"already stored" (S3's 412 on ``If-None-Match: *``), so nothing is replaced; a
complete stem is still skipped and nothing here ever overwrites. Mixing a
refused stem would hand analysis a capture with ranks of two different
formats, which is a wrong dataset and not a smaller one.

Two capture modes exist, matching the plugin's. ``mode="rows"`` stores full
softmax rows at chosen positions. ``mode="mass"`` answers the noise-arm
question (does a RESPONSE token put less mass on the whitespace padding than
the uniform prediction ``|pad| / d``?) for every response token at once, which
the ``T x T`` rows cannot (one 40k-token sequence is ~1.8 GB per layer-head).
The client labels every token with one of four key classes and ships the labels
in the job; the plugin reduces each row against them on the box and uploads
``mass`` ``[L, P, H_local, 4]`` plus the row ``entropy``, with
``P = n_tokens - query_start``. A handful of gate positions still carry full
rows, so the ``rows @ V`` self-consistency check is the same arithmetic in both
modes. Rows mode is supported only as far as the data structures and the
verification checks go; the batch runner defaults to ``"mass"``.

``mode="summary"`` is the compact form of mass mode. The job carries the same
``query_start`` and ``classes``, but the plugin does not keep the per-row
arrays: it sums the mass-mode per-row statistics over the ``P`` response rows
on the box and uploads only those sums, each ``[L, H_local]`` (``sum_mass`` is
``[L, H_local, 4]``), plus the counts of rows where the prompt entropy and the
pad ratio are defined (``SUMMARY_ARRAYS`` names them all) and the same
geometry arrays as mass mode. The upload is small enough to keep for every
mark, at the price that per-row values cannot be recovered afterwards.

Left out on purpose: the HF-transformers replay path, building jobs from
stored marks (``answer_positions``, ``build_jobs``), and any index or resume
bookkeeping tied to one results layout. They depend on a results store this
module deliberately does not import; their replacement is the caller's
manifest plus the append-only skip above.
"""

from __future__ import annotations

import io
import json
import logging
import re
import time
from urllib.parse import parse_qs, urlsplit
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "CAPTURE_MARKER",
    "CAPTURE_MODES",
    "CAPTURE_VERSIONS",
    "CaptureResult",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_BATCH_TIMEOUT_S",
    "DEFAULT_POLL_S",
    "DEFAULT_URL_TTL_S",
    "ENGINE_GONE_MARKERS",
    "Job",
    "MASS_GATE_FRACTIONS",
    "MIN_PAD_RUN_CHARS",
    "N_TOKEN_CLASSES",
    "SUMMARY_ARRAYS",
    "capture_job_failure",
    "fill_refusal",
    "job_keys_present",
    "mass_gate_positions",
    "mass_job",
    "presign_put",
    "rank_keys",
    "run_capture_batches",
    "token_classes",
    "verify_capture_uploads",
]

#: Per-batch ceiling; a batch's presigned URLs must outlive it.
DEFAULT_BATCH_TIMEOUT_S: int = 6 * 3600
#: Default presigned-URL lifetime: the batch ceiling plus an hour. URLs are
#: minted right before each batch. They also die with the credential that
#: signed them, so a batch must not outlive an STS session either.
DEFAULT_URL_TTL_S: int = DEFAULT_BATCH_TIMEOUT_S + 3600
#: Jobs per ``/attn`` call. Every call carries each job's token ids and its int
#: classes inline as JSON, and the rebuttal's sequences are at most ~40k tokens,
#: so 16 jobs stay in the tens of MB (the source's 64-job batch assumed the same
#: size per job but amortised a checkpoint load that one serve no longer repeats).
DEFAULT_BATCH_SIZE: int = 16
#: ``/status`` poll cadence; each poll touches the box's ``last_active``, so
#: it must stay well under the idle watchdog's window.
DEFAULT_POLL_S: int = 30

#: The only capture modes the plugin knows (its ``_read_job`` raises on any
#: other value, and a mode absent from the job file means ``"rows"``).
CAPTURE_MODES: Tuple[str, ...] = ("rows", "mass", "summary")
#: Every array a summary-mode ``.npz`` must hold beyond the geometry arrays it
#: shares with mass mode (``classes``, ``query_start``, ``positions``,
#: ``layers``, ``has_sink``, ``sliding_window``, ``kv_shared_from``). ``rows``
#: is the 0-d response-row count ``P``; the ``sum_*`` arrays are sums of the
#: mass-mode per-row statistics over those rows and ``n_*`` count the rows
#: where the statistic is defined.
SUMMARY_ARRAYS: Tuple[str, ...] = (
    "rows",
    "sum_entropy",
    "sum_prompt_entropy",
    "n_prompt_entropy",
    "sum_mass",
    "sum_sink",
    "sum_pad_ratio",
    "n_pad_ratio",
    "sum_m_hp",
    "sum_chain_hi",
    "sum_chain_lo",
)
#: Number of key classes in mass mode; the plugin's ``N_CLASSES`` and the last
#: axis of its ``mass`` array. Kept as a name so the verification check reads
#: as "the contract's class count", not as a bare 4.
N_TOKEN_CLASSES: int = 4
#: Shortest whitespace run (in CHARACTERS) that can be the noise arm's pad.
#: The arm appends ``pad_unit * n`` to the prompt, which is always far longer
#: than this; the floor is what keeps an ordinary indent or a blank line out of
#: the pad class when a mark has no padding at all.
MIN_PAD_RUN_CHARS: int = 32
#: Where a mass job's full-row gate probes sit inside the completion, as
#: ``(numerator, denominator)`` of its length. The final token is always a gate
#: too, and duplicates collapse, so a short completion yields fewer than three.
MASS_GATE_FRACTIONS: Tuple[Tuple[int, int], ...] = ((1, 3), (2, 3))

#: Marker a caller may record in its own capture manifest to say the arrays
#: came from the vLLM-prefill plugin and not from an HF-transformers replay
#: (which stores different layouts under the same sort of key).
CAPTURE_MARKER: str = "vllm-prefill-plugin"

#: Substrings of the agent's per-job ``{"error": str(exc)}`` that mean the vLLM
#: server did not answer as a live engine. When the engine dies (a model step
#: outlasted vLLM's step timeout) the in-flight request gets ``HTTP Error 500``
#: and every later request of the batch gets a reset, a broken pipe or a refused
#: connection. A rank-collection timeout (``<job>: 3/8 ranks done``) matches
#: none of these on purpose: the engine was alive, only a rank was slow.
ENGINE_GONE_MARKERS: Tuple[str, ...] = (
    "HTTP Error 500",
    "Errno 104",
    "Connection reset",
    "Errno 111",
    "Connection refused",
    "Errno 32",
    "Broken pipe",
)
#: Capture-format version each mode's plugin writes into its metas, mirrored
#: from the plugin's ``CAPTURE_VERSION`` (rows, mass) and
#: ``SUMMARY_CAPTURE_VERSION`` (summary). Fill mode completes a stem only when
#: the stored meta carries the version this run's plugin would write.
CAPTURE_VERSIONS: Dict[str, int] = {"rows": 2, "mass": 2, "summary": 3}

#: A job id doubles as the box's done-file stem (``<job_id>.r<rank>.json``) and
#: as the agent's results key, so it is restricted to characters that are safe
#: in a filename and in a JSON key.
_JOB_ID_RE = re.compile(r"^[A-Za-z0-9._=+-]+$")


def _check_mode(mode: str) -> str:
    """Return `mode` unchanged, or refuse a mode neither half of the contract knows.

    Used by ``run_capture_batches`` and ``verify_capture_uploads`` so the client cannot ship a
    job file the on-box plugin will reject: its ``_read_job`` raises on any
    value outside ``CAPTURE_MODES``, and that failure would only surface after
    a paid serve had already started.

    Parameters
    ----------
    mode : str
        Requested capture mode.

    Returns
    -------
    str
        `mode`, when it is one of ``CAPTURE_MODES``.

    Raises
    ------
    ValueError
        When `mode` is anything else.
    """
    if mode not in CAPTURE_MODES:
        raise ValueError(f"mode must be one of {CAPTURE_MODES}, got {mode!r}")
    return mode


@dataclass(frozen=True)
class Job:
    """One capture request: a token sequence, its gate or answer positions and its upload key."""

    job_id: str
    prompt_token_ids: Tuple[int, ...]
    completion_token_ids: Tuple[int, ...]
    #: Indices into ``prompt + completion``: the graded answer's token(s) in
    #: rows mode, the self-consistency GATE positions in mass mode (where the
    #: queries actually reduced are all of ``query_start .. n_tokens - 1``).
    positions: Tuple[int, ...]
    #: Bucket key of the ``.npz``, treated as a STEM only: the box writes
    #: ``rank_keys(key, rank)`` per tensor-parallel rank. The key is
    #: mode-independent, so one key stem holds one mode's arrays at a time; the
    #: caller's own manifest is where the mode that wrote them is recorded.
    key: str
    #: The mass fields come LAST and default, so a rows job can be built with
    #: the four leading fields alone.
    mode: str = "rows"
    #: First completion index (``len(prompt_token_ids)``); mass mode only.
    query_start: Optional[int] = None
    #: Per-token key class over ``prompt + completion``; mass mode only. See
    #: ``token_classes`` for the four labels.
    classes: Optional[Tuple[int, ...]] = None

    @property
    def n_tokens(self) -> int:
        """Return the full sequence length."""
        return len(self.prompt_token_ids) + len(self.completion_token_ids)

    def mass_keys(self) -> Dict[str, Any]:
        """Return the mass/summary-mode additions to a wire job, or ``{}`` in rows mode.

        The single definition of the three keys, shared by mass and summary
        mode (the plugin validates the same three for both). ``run_capture_batches``
        splices them into each ``/attn`` line, and the plugin's ``_read_job``
        validates exactly these three against ``n_tokens``, so they must not be
        spelled out twice and drift.

        Returns
        -------
        Dict[str, Any]
            ``{}`` when ``mode == "rows"``; otherwise ``mode`` (this job's own,
            ``"mass"`` or ``"summary"``), ``query_start`` (int) and ``classes`` (a JSON-serialisable list, not the tuple).

        Raises
        ------
        TypeError
            When a mass job carries no ``query_start`` or no ``classes``. Both
            conversions below are deliberately unguarded: a job that malformed
            must fail HERE, at the client, rather than ship an empty
            ``classes`` the plugin only rejects after a serve has been paid for.
        """
        if self.mode == "rows":
            return {}
        return {
            "mode": self.mode,
            "query_start": int(self.query_start),  # type: ignore[arg-type]
            "classes": list(self.classes),  # type: ignore[arg-type]
        }


def _longest_whitespace_run(text: str) -> Tuple[int, int]:
    """Return ``(start, length)`` of the longest run of whitespace CHARACTERS in `text`.

    On a tie the FIRST (leftmost) run wins -- the comparison below is a strict
    ``>``. A tie is not expected in practice, because the noise arm's padding
    dwarfs any template whitespace the prompt also carries; the tie-break is
    pinned anyway rather than left to chance, since one that varied would
    silently relabel which tokens count as pad from one tokenizer to the next.

    Parameters
    ----------
    text : str
        Any string; may be empty.

    Returns
    -------
    Tuple[int, int]
        Start index and length. ``(0, 0)`` when `text` holds no whitespace at
        all, so callers can gate on the length without a separate empty case.

    Notes
    -----
    Time O(len(text)), space O(1).
    """
    best_start, best_len = 0, 0
    i, n = 0, len(text)
    while i < n:
        if not text[i].isspace():
            i += 1
            continue
        j = i
        while j + 1 < n and text[j + 1].isspace():
            j += 1
        if j - i + 1 > best_len:  # strict: the leftmost of equal runs is kept
            best_start, best_len = i, j - i + 1
        i = j + 1
    return best_start, best_len


def token_classes(
    prompt_token_ids: Sequence[int],
    completion_token_ids: Sequence[int],
    decode_tokens: Callable[[Sequence[int]], Sequence[str]],
    *,
    pad_span: Optional[Tuple[int, int]] = None,
    pad_spans: Optional[Sequence[Tuple[int, int]]] = None,
) -> List[int]:
    """Label every token of ``prompt + completion`` with its mass-mode key class.

    The four classes of the capture contract, per token:

    * ``0`` -- prompt token carrying information: its decoded piece holds at
      least one non-whitespace character. ``" answer"`` is class 0, not
      whitespace: a piece that CONTAINS a space still carries a word.
    * ``1`` -- prompt PAD token. Without `pad_span`: a whitespace-only piece
      lying inside the prompt's longest whitespace run, when that run is at
      least ``MIN_PAD_RUN_CHARS`` characters long. This is the noise arm's
      appended ``pad_unit * n``; the length floor and the longest-run
      restriction together are what keep an ordinary two-space indent, a
      newline between chat turns, or a blank line out of the pad class. With
      `pad_span`: a non-empty piece (whitespace or not) whose character range
      lies entirely inside `pad_span`, and the whitespace rule is not applied.
      With `pad_spans`: the same, inside the UNION of the spans (a pad made of
      many separate pieces, such as lines interleaved with other lines).
    * ``2`` -- other prompt whitespace or template token: a whitespace-only
      piece outside the pad (short structural whitespace, or a second
      whitespace run), and an EMPTY piece -- chat-template specials decode to
      ``""`` and are structure, not information.
    * ``3`` -- completion token, reasoning and response alike. No completion id
      is decoded: its class does not depend on its text.

    Without `pad_span` only whitespace-only tokens can be class 1, and a
    whitespace-only token can never straddle the boundary of a MAXIMAL
    whitespace run (whitespace on the far side of the boundary would have
    extended the run), so "inside the run" is a plain span containment with no
    partial-overlap case to resolve. With `pad_span` the caller states the pad
    by construction (an arm that pads with non-whitespace text, such as added
    rule lines), and a token CAN straddle an edge of the span (a merge such as
    ``".\\n"`` across the last pad character and the text after it): it is not
    class 1 and takes the class of any other prompt token, 0 or 2 by its piece.

    Parameters
    ----------
    prompt_token_ids : Sequence[int]
        vLLM's exact prompt ids, in order. May be empty.
    completion_token_ids : Sequence[int]
        vLLM's exact completion ids. Only their COUNT is used. May be empty.
    decode_tokens : Callable
        Per-token decoder (``Tokenizer.decode_tokens``): given a list of ids it
        returns one decoded piece per id, same order. The pieces are
        concatenated to recover the prompt text, and each token's
        ``[start, end)`` character span comes from the cumulative lengths.
    pad_span : Optional[Tuple[int, int]], optional
        Half-open character range ``[start, end)`` of the pad in the text those
        pieces concatenate to (the decoded prompt text). Default ``None``: the
        longest-whitespace-run rule decides. Given, it replaces the rule
        entirely, so a long whitespace run elsewhere in the prompt is not
        class 1. An empty span (``start == end``) is valid and labels nothing.
        Must satisfy ``0 <= start <= end <= len(prompt text)``.
    pad_spans : Optional[Sequence[Tuple[int, int]]], optional
        Several half-open ranges in the same coordinates as `pad_span`, in any
        order; they may touch or overlap. Default ``None``. Given, it replaces the
        rule like `pad_span`, and a token is class 1 when its range lies inside
        their union, so a token that crosses from one span into an adjacent one
        is class 1 and one that crosses into text outside every span is not. An
        empty sequence labels nothing. Each span must satisfy the bounds of
        `pad_span`. Mutually exclusive with `pad_span`.

    Returns
    -------
    List[int]
        One class in ``0..3`` per token, of length
        ``len(prompt_token_ids) + len(completion_token_ids)``.

    Raises
    ------
    ValueError
        When `decode_tokens` does not return exactly one piece per prompt id
        (the spans, and hence every prompt class, would be misaligned, and the
        plugin rejects a ``classes`` array that does not cover every token), when
        `pad_span` or an element of `pad_spans` is not ``0 <= start <= end <=
        len(prompt text)``, or when both `pad_span` and `pad_spans` are given.

    Notes
    -----
    Pure: no I/O, no globals, no mutation of its arguments. One decoder call.
    Time O(len(prompt text)), plus O(S log S + len(prompt) log S) for `S` spans in
    `pad_spans`; space O(len(prompt) + S).

    Examples
    --------
    >>> table = {0: "", 1: "Hi", 2: ".", 3: " " * 40, 9: " ok"}
    >>> token_classes([0, 1, 2, 3], [9], lambda ids: [table[i] for i in ids])
    [2, 0, 0, 1, 3]
    >>> pieces = {1: "ab", 2: " ", 3: "cd"}
    >>> token_classes([1, 2, 3], [], lambda ids: [pieces[i] for i in ids], pad_span=(2, 3))
    [0, 1, 0]
    >>> lines = {1: "a\\n", 2: "pad\\n", 3: "b\\n", 4: "pad\\n"}
    >>> token_classes([1, 2, 3, 4], [], lambda ids: [lines[i] for i in ids], pad_spans=[(2, 6), (8, 12)])
    [0, 1, 0, 1]
    """
    if pad_span is not None and pad_spans is not None:
        raise ValueError("pass pad_span or pad_spans, not both")
    prompt_ids = list(prompt_token_ids)
    pieces = list(decode_tokens(prompt_ids))
    if len(pieces) != len(prompt_ids):
        raise ValueError(
            f"decode_tokens returned {len(pieces)} pieces for {len(prompt_ids)} prompt ids; "
            "token classes need one piece per token"
        )

    # Phase 1: prompt text plus each token's character span, from the
    # cumulative piece lengths (the decoder is lossless per token, so the
    # concatenation IS the prompt text the model saw).
    spans: List[Tuple[int, int]] = []
    cursor = 0
    for piece in pieces:
        spans.append((cursor, cursor + len(piece)))
        cursor += len(piece)
    text = "".join(pieces)

    # Phase 2: the span that may hold pad tokens. A caller-given span replaces the
    # rule; otherwise it is the longest whitespace run, and below the floor there
    # is no pad at all (every whitespace token falls to class 2).
    if pad_span is not None:
        if not 0 <= pad_span[0] <= pad_span[1] <= len(text):
            raise ValueError(
                f"pad_span {tuple(pad_span)} must satisfy 0 <= start <= end <= {len(text)} "
                "(the length of the prompt text)"
            )
        span: Optional[Tuple[int, int]] = (int(pad_span[0]), int(pad_span[1]))
    elif pad_spans is not None:
        span = None
        union = _union_of_spans(pad_spans, len(text))
    else:
        run_start, run_len = _longest_whitespace_run(text)
        span = (run_start, run_start + run_len) if run_len >= MIN_PAD_RUN_CHARS else None

    # Phase 3: classify the prompt, then append the completion wholesale. By rule
    # only whitespace-only pieces may be pad; by construction the span decides.
    by_construction = pad_span is not None or pad_spans is not None
    classes: List[int] = []
    for piece, (start, end) in zip(pieces, spans):
        whitespace_only = bool(piece) and all(ch.isspace() for ch in piece)
        if pad_spans is not None:
            in_span = _inside_union(union, start, end)
        else:
            in_span = span is not None and start >= span[0] and end <= span[1]
        if piece and in_span and (whitespace_only or by_construction):
            classes.append(1)
        elif whitespace_only or not piece:
            classes.append(2)
        else:
            classes.append(0)
    classes.extend([3] * len(completion_token_ids))
    return classes


def _union_of_spans(pad_spans: Sequence[Tuple[int, int]], text_len: int) -> List[Tuple[int, int]]:
    """Return the union of `pad_spans` as sorted, disjoint, non-touching ``[start, end)`` ranges.

    Empty spans are dropped (they label nothing). Spans that touch (``a_end == b_start``)
    are joined, so a token that crosses their common edge lies inside one range.

    Raises
    ------
    ValueError
        When a span is not ``0 <= start <= end <= text_len``.
    """
    ordered: List[Tuple[int, int]] = []
    for item in pad_spans:
        start, end = int(item[0]), int(item[1])
        if not 0 <= start <= end <= text_len:
            raise ValueError(
                f"pad_spans element {tuple(item)} must satisfy 0 <= start <= end <= {text_len} "
                "(the length of the prompt text)"
            )
        if start < end:
            ordered.append((start, end))
    ordered.sort()
    union: List[Tuple[int, int]] = []
    for start, end in ordered:
        if union and start <= union[-1][1]:
            union[-1] = (union[-1][0], max(union[-1][1], end))
        else:
            union.append((start, end))
    return union


def _inside_union(union: Sequence[Tuple[int, int]], start: int, end: int) -> bool:
    """Return whether ``[start, end)`` lies inside one range of the sorted disjoint `union`.

    Binary search on the range starts: only the last range starting at or before
    `start` can contain the token, because the ranges neither overlap nor touch.
    """
    lo, hi = 0, len(union)
    while lo < hi:
        mid = (lo + hi) // 2
        if union[mid][0] <= start:
            lo = mid + 1
        else:
            hi = mid
    return lo > 0 and end <= union[lo - 1][1]


def mass_gate_positions(query_start: int, n_completion: int) -> Tuple[int, ...]:
    """Return the completion positions whose FULL rows a mass job still captures.

    The last token plus one third and two thirds of the way into the
    completion: three probes across the response, cheap enough that the
    ``rows @ V`` self-consistency gate costs a few rows instead of ``P`` of
    them, and spread out so a drift that only appears deep into a long
    generation is not missed by a gate pinned at the end.

    Parameters
    ----------
    query_start : int
        First completion index (``len(prompt_token_ids)``).
    n_completion : int
        Number of completion tokens; must be at least 1.

    Returns
    -------
    Tuple[int, ...]
        Positions, deduplicated and sorted ascending, every one of them inside
        ``query_start .. query_start + n_completion - 1``. A short completion
        collapses the fractions onto each other (and onto the last token), so
        fewer than three come back.

    Raises
    ------
    ValueError
        When `n_completion` is below 1: with no completion token there is no
        response row to probe, and ``last`` would point into the prompt.

    Examples
    --------
    >>> mass_gate_positions(10, 9)
    (13, 16, 18)
    >>> mass_gate_positions(10, 1)
    (10,)
    """
    if n_completion < 1:
        raise ValueError(f"n_completion must be >= 1, got {n_completion}")
    last = query_start + n_completion - 1
    # Floor division keeps every fraction inside the completion: for every
    # C >= 1 the largest offset, 2C // 3, is at most C - 1.
    fractions = (query_start + (num * n_completion) // den for num, den in MASS_GATE_FRACTIONS)
    return tuple(sorted({last, *fractions}))


def mass_job(
    job_id: str,
    prompt_token_ids: Sequence[int],
    completion_token_ids: Sequence[int],
    classes: Sequence[int],
    key: str,
    *,
    mode: str = "mass",
) -> Job:
    """Build a validated mass- or summary-mode ``Job`` from a sequence and its key classes.

    Both modes take the same job: the sequence, its key classes and the gate
    positions; they differ only in what the plugin stores. Every validation
    below applies to both.

    The gate positions come from ``mass_gate_positions`` and ``query_start`` is
    ``len(prompt_token_ids)``. Every check the plugin's ``_read_job`` would make
    on the wire line is made HERE, so a malformed job fails at the client and
    not after a serve has been paid for.

    Parameters
    ----------
    job_id : str
        Unique id of the job; must match ``^[A-Za-z0-9._=+-]+$``. The box names
        its done files ``<job_id>.r<rank>.json`` and the agent keys its results
        by this id, so it must be a safe filename and JSON key.
    prompt_token_ids : Sequence[int]
        The exact prompt ids the model saw. May be empty.
    completion_token_ids : Sequence[int]
        The exact completion ids. Must be non-empty.
    classes : Sequence[int]
        One key class per token of ``prompt + completion`` (see
        ``token_classes``): prompt tokens in 0..2, completion tokens all 3.
    key : str
        Bucket key stem of the job's ``.npz``; must end in ``.npz``.
    mode : str, optional
        ``"mass"`` (default) or ``"summary"``; recorded on the job. ``"rows"``
        is refused: a rows job has no classes.

    Returns
    -------
    Job
        A frozen job with ``mode=mode``, ``classes`` as a tuple of ints and
        all id sequences as tuples.

    Raises
    ------
    ValueError
        When `mode` is not ``"mass"`` or ``"summary"``, `job_id` has a
        character outside the allowed set, `key` does not
        end in ``.npz``, the completion is empty, ``len(classes)`` differs from
        the sequence length, a class lies outside ``0..N_TOKEN_CLASSES - 1``, a
        prompt token has class 3, or a completion token has a class other
        than 3.

    Examples
    --------
    >>> job = mass_job("q0", [5, 6], [7, 8, 9], [0, 2, 3, 3, 3], "p/q0.npz")
    >>> job.query_start, job.positions, job.n_tokens
    (2, (3, 4), 5)
    """
    if mode not in ("mass", "summary"):
        raise ValueError(f"mode must be 'mass' or 'summary', got {mode!r}")
    if not _JOB_ID_RE.match(job_id):
        raise ValueError(f"job_id {job_id!r} must match {_JOB_ID_RE.pattern}")
    if not key.endswith(".npz"):
        raise ValueError(f"key {key!r} must end in '.npz'")
    prompt = tuple(int(t) for t in prompt_token_ids)
    completion = tuple(int(t) for t in completion_token_ids)
    if not completion:
        raise ValueError(f"job {job_id}: empty completion; a mass job needs a response row to capture")
    cls = tuple(int(c) for c in classes)
    n_tokens = len(prompt) + len(completion)
    if len(cls) != n_tokens:
        raise ValueError(f"job {job_id}: {len(cls)} classes for {n_tokens} tokens")
    bad = sorted({c for c in cls if not 0 <= c < N_TOKEN_CLASSES})
    if bad:
        raise ValueError(f"job {job_id}: classes {bad} outside 0..{N_TOKEN_CLASSES - 1}")
    # Class 3 is exactly "completion token" in the contract: a prompt token
    # carrying it would be reduced as a response key, and a completion token
    # without it would be mislabelled in the uniform baseline.
    if any(c == 3 for c in cls[: len(prompt)]):
        raise ValueError(f"job {job_id}: a prompt token has class 3 (reserved for completion tokens)")
    if any(c != 3 for c in cls[len(prompt):]):
        raise ValueError(f"job {job_id}: a completion token has a class other than 3")
    return Job(
        job_id=job_id,
        prompt_token_ids=prompt,
        completion_token_ids=completion,
        positions=mass_gate_positions(len(prompt), len(completion)),
        key=key,
        mode=mode,
        query_start=len(prompt),
        classes=cls,
    )


def rank_keys(key: str, rank: int) -> Tuple[str, str]:
    """Return one tensor-parallel rank's ``(.npz, .json)`` keys for a job.

    The capture path uploads once PER RANK (each rank holds its own slice of
    the heads), so a job's ``key`` -- ``.../q<idx>.npz`` -- is only the stem:
    rank ``r`` writes ``.../q<idx>.r<r>.npz`` and ``.../q<idx>.r<r>.json``.
    Every producer and consumer of those names goes through this helper.

    Parameters
    ----------
    key : str
        The job's ``.npz`` stem key (``Job.key``).
    rank : int
        Tensor-parallel rank, ``0 .. tp - 1``.

    Returns
    -------
    Tuple[str, str]
        The rank's array key and its meta key.

    Examples
    --------
    >>> rank_keys("p/attn/i--ts/q3.npz", 1)
    ('p/attn/i--ts/q3.r1.npz', 'p/attn/i--ts/q3.r1.json')
    """
    stem = key[: -len(".npz")]
    return f"{stem}.r{rank}.npz", f"{stem}.r{rank}.json"


def presign_put(client: Any, bucket: str, key: str, content_type: str, ttl_s: int) -> str:
    """Return a presigned PUT URL for `key` in `bucket` that refuses to replace.

    The URL pins the ``Content-Type`` and ``If-None-Match: *``: the box must
    upload with exactly that type and that header, or S3 refuses the request,
    and S3 answers 412 when the key already exists instead of overwriting it.

    Parameters
    ----------
    client : Any
        boto3 S3 client (anything with ``generate_presigned_url``). The URL dies
        with the credential that signs it, so pass a client built from current
        credentials. It must sign with SigV4
        (``Config(signature_version="s3v4")``): SigV2 drops ``IfNoneMatch``
        without an error, which would leave the URL able to overwrite.
    bucket : str
        Destination bucket.
    key : str
        Destination object key.
    content_type : str
        ``Content-Type`` the upload must carry.
    ttl_s : int
        URL lifetime in seconds.

    Returns
    -------
    str
        The presigned URL; its ``X-Amz-SignedHeaders`` lists ``if-none-match``.

    Raises
    ------
    ValueError
        The minted URL does not sign ``if-none-match`` (the client signs with
        SigV2), so it would not protect an existing object.
    """
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
            "IfNoneMatch": "*",
        },
        ExpiresIn=ttl_s,
    )
    # Check the URL itself, not the client's config: a client of any type is
    # accepted, and only the minted URL shows whether the header got signed.
    signed = parse_qs(urlsplit(url).query).get("X-Amz-SignedHeaders", [""])[0]
    if "if-none-match" not in signed.split(";"):
        raise ValueError(
            "presigned PUT URL does not sign If-None-Match, so it could replace an "
            "existing object; build the S3 client with "
            'botocore.config.Config(signature_version="s3v4")'
        )
    return url


def _check_url_ttl(url_ttl_s: int, batch_timeout_s: int) -> None:
    """Refuse a presigned-URL lifetime a batch could outlive.

    URLs are minted right before a batch, so a batch allowed to run longer than they live
    would upload its last (largest) jobs into 403s and lose them silently.

    Parameters
    ----------
    url_ttl_s : int
        Presigned-URL lifetime, in seconds.
    batch_timeout_s : int
        Per-batch ceiling, in seconds.

    Raises
    ------
    ValueError
        When ``url_ttl_s <= batch_timeout_s``.
    """
    if url_ttl_s <= batch_timeout_s:
        raise ValueError(
            f"url_ttl_s={url_ttl_s} must exceed batch_timeout_s={batch_timeout_s}: a batch "
            "that outlives its presigned URLs uploads into 403s"
        )


def _check_rows_arrays(arrays: Any, job: Job) -> None:
    """Raise unless a sampled rows-mode ``.npz`` matches `job`.

    The plugin's axis order is ``[L, P, H_local, T]`` -- NOT the HF replay
    path's ``(L, H, P, T)`` -- so only the number of axes, the last axis and
    the positions are checked; the head axis is per-rank local and only the
    tensor-parallel ranks together make up the model's heads.

    Parameters
    ----------
    arrays : Any
        The loaded ``NpzFile`` (mapping of name -> array).
    job : Job
        The job those arrays claim to answer.

    Raises
    ------
    ValueError
        On a wrong number of axes, a last axis that is not the sequence length,
        or stored positions that differ from the job's.
    KeyError
        When ``rows`` is absent -- e.g. a mass-mode upload checked as rows.
    """
    rows = arrays["rows"]
    if rows.ndim != 4:
        raise ValueError(f"rows.ndim {rows.ndim} != 4 (expected [L, P, H_local, T])")
    if rows.shape[-1] != job.n_tokens:
        raise ValueError(f"rows last axis {rows.shape[-1]} != n_tokens {job.n_tokens}")
    if list(arrays["positions"]) != list(job.positions):
        raise ValueError("stored positions differ from the job's")


def _check_mass_arrays(arrays: Any, job: Job) -> None:
    """Raise unless a sampled mass-mode ``.npz`` matches `job`.

    The enumerated checks ARE the agreed contract with the plugin's owner:
    ``mass`` is ``[L, P, H_local, 4]`` with ``P = n_tokens - query_start``,
    ``entropy`` shares its first three axes, and ``classes`` covers every
    token so the uniform baseline ``n_c(p) / (p + 1)`` is computable offline
    for every query. Deliberately NOT checked: ``positions``. In mass mode
    those are only the self-consistency gate probes, not the data's index --
    the query axis is the full response range, and the plugin is free to gate
    where it must.

    Parameters
    ----------
    arrays : Any
        The loaded ``NpzFile`` (mapping of name -> array).
    job : Job
        The job those arrays claim to answer; must carry ``query_start``.

    Raises
    ------
    ValueError
        When the job carries no ``query_start``, or any enumerated shape check
        fails.
    KeyError
        When ``mass``, ``entropy`` or ``classes`` is absent -- e.g. a rows-mode
        upload checked as mass.
    """
    if job.query_start is None:
        raise ValueError(f"job {job.job_id} has no query_start; it is not a mass job")
    mass = arrays["mass"]
    expected_p = job.n_tokens - int(job.query_start)
    if mass.ndim != 4:
        raise ValueError(f"mass.ndim {mass.ndim} != 4 (expected [L, P, H_local, C])")
    if mass.shape[1] != expected_p:
        raise ValueError(
            f"mass query axis {mass.shape[1]} != n_tokens - query_start "
            f"({job.n_tokens} - {job.query_start} = {expected_p})"
        )
    if mass.shape[-1] != N_TOKEN_CLASSES:
        raise ValueError(f"mass class axis {mass.shape[-1]} != {N_TOKEN_CLASSES}")
    entropy = arrays["entropy"]
    if entropy.shape != mass.shape[:3]:
        raise ValueError(f"entropy shape {entropy.shape} != mass[L, P, H] {mass.shape[:3]}")
    classes = arrays["classes"]
    if len(classes) != job.n_tokens:
        raise ValueError(f"classes covers {len(classes)} of {job.n_tokens} tokens")


def _check_summary_arrays(arrays: Any, job: Job) -> None:
    """Raise unless a sampled summary-mode ``.npz`` matches `job`.

    ``rows`` must equal ``n_tokens - query_start``; ``sum_entropy`` fixes the
    ``[L, H_local]`` shape and every other per-(layer, head) entry of
    ``SUMMARY_ARRAYS`` must share it (``sum_mass`` adds a trailing class axis
    of ``N_TOKEN_CLASSES``); ``classes`` covers every token. As in mass mode,
    ``positions`` is not checked.

    Parameters
    ----------
    arrays : Any
        The loaded ``NpzFile`` (mapping of name -> array).
    job : Job
        The job those arrays claim to answer; must carry ``query_start``.

    Raises
    ------
    ValueError
        When the job carries no ``query_start``, or a shape or ``rows`` check
        fails.
    KeyError
        When any ``SUMMARY_ARRAYS`` entry or ``classes`` is absent -- e.g. a
        mass-mode upload checked as summary.
    """
    if job.query_start is None:
        raise ValueError(f"job {job.job_id} has no query_start; it is not a summary job")
    expected_p = job.n_tokens - int(job.query_start)
    rows = int(arrays["rows"])
    if rows != expected_p:
        raise ValueError(
            f"rows {rows} != n_tokens - query_start "
            f"({job.n_tokens} - {job.query_start} = {expected_p})"
        )
    shape = arrays["sum_entropy"].shape
    if len(shape) != 2:
        raise ValueError(f"sum_entropy.ndim {len(shape)} != 2 (expected [L, H_local])")
    for name in SUMMARY_ARRAYS:
        if name in ("rows", "sum_entropy"):
            continue
        got = arrays[name].shape
        want = shape + (N_TOKEN_CLASSES,) if name == "sum_mass" else shape
        if got != want:
            raise ValueError(f"{name} shape {got} != {want}")
    classes = arrays["classes"]
    if len(classes) != job.n_tokens:
        raise ValueError(f"classes covers {len(classes)} of {job.n_tokens} tokens")


def verify_capture_uploads(
    client: Any,
    bucket: str,
    jobs: Sequence[Job],
    tp: int,
    *,
    sample: int = 1,
    mode: str = "rows",
) -> Tuple[List[str], List[str]]:
    """HEAD every rank's objects and shape-check a sample of the captured arrays.

    Existence alone is not a content gate. Every rank of every job is HEADed
    against the size its own meta claims and against the job's sequence
    length; for the first `sample` jobs rank 0's array is additionally
    downloaded and inspected. A job is verified only when ALL `tp` ranks pass:
    analysis concatenates the ranks along the head axis, so a missing or
    truncated shard is a hole in the head dimension, not a smaller dataset.

    The HEAD/meta phase is mode-independent. What the sampled array must
    contain is not: rows mode stores ``rows`` over the answer positions, mass
    mode stores ``mass``/``entropy``/``classes`` over the whole response,
    summary mode stores the ``SUMMARY_ARRAYS`` sums over it, so
    the checks are named per mode rather than inferred from what happens to be
    in the file.

    Parameters
    ----------
    client : Any
        boto3 S3 client (anything with ``head_object`` and ``get_object``).
    bucket : str
        Bucket holding the uploads.
    jobs : Sequence[Job]
        Jobs the box reported as captured. ``Job.key`` is the ``.npz`` stem;
        the real objects are ``rank_keys(key, rank)``. In mass mode each job's
        ``query_start`` is what the array's query axis is measured against.
    tp : int
        Tensor-parallel degree: how many ranks uploaded per job.
    sample : int, optional
        How many arrays to download and inspect (the first `sample` jobs),
        by default 1.
    mode : str, optional
        Which array layout to expect, ``"rows"`` (default), ``"mass"`` or
        ``"summary"``.
        Passing the wrong one fails every sampled job, which is the point: the
        two modes must never certify each other's objects.

    Returns
    -------
    Tuple[List[str], List[str]]
        Verified job ids and failed job ids (each in input order), taken from
        ``Job.job_id``. Every failure is logged, never raised.

    Raises
    ------
    ValueError
        When `mode` is not one of ``CAPTURE_MODES``. This one IS raised:
        it is a programming error about all the jobs at once, not a fault of
        any one upload.

    Notes
    -----
    Network: one HEAD and one GET of the (small) meta per job per rank, plus
    `sample` downloads of a (large) array. Nothing is mutated. A missing array
    inside the npz raises ``KeyError`` from ``np.load``'s mapping, which the
    per-job handler turns into an ordinary logged failure.

    A rank whose meta says ``npz_put == "existing"`` was completed by a fill
    run: its ``.npz`` was stored by an EARLIER run and the new run's upload was
    refused, so ``meta["bytes"]`` is the size of the npz the new run built, not
    of the stored one. For such a rank, and only for it, the
    ``ContentLength == meta["bytes"]`` comparison is skipped; the HEAD itself
    (the npz must exist), the ``n_tokens`` check and the sampled array check
    still run. Any other ``npz_put`` value gets the normal size check.
    """
    import numpy as np

    _check_mode(mode)
    ok: List[str] = []
    bad: List[str] = []
    for n, job in enumerate(jobs):
        try:
            # Phase 1: every rank must exist and agree with its own meta.
            for rank in range(tp):
                npz_key, meta_key = rank_keys(job.key, rank)
                head = client.head_object(Bucket=bucket, Key=npz_key)
                meta = json.loads(
                    client.get_object(Bucket=bucket, Key=meta_key)["Body"].read().decode()
                )
                # ``bytes`` / ``n_tokens`` are the PLUGIN's meta key names; the
                # HF replay path writes ``npz_bytes`` / ``shape`` instead.
                # Design: skip ONLY the size comparison for a stored-earlier
                # npz (see the docstring); skipping the whole rank would also
                # drop the n_tokens check, which is still meaningful.
                if meta.get("npz_put") != "existing" and int(head["ContentLength"]) != int(meta["bytes"]):
                    raise ValueError(
                        f"rank {rank} size {head['ContentLength']} != meta bytes {meta['bytes']}"
                    )
                if int(meta["n_tokens"]) != job.n_tokens:
                    raise ValueError(
                        f"rank {rank} meta n_tokens {meta['n_tokens']} != job's {job.n_tokens}"
                    )
            # Phase 2: for the sampled jobs, open rank 0's array itself.
            if n < sample:
                npz_key, _ = rank_keys(job.key, 0)
                body = client.get_object(Bucket=bucket, Key=npz_key)["Body"].read()
                arrays = np.load(io.BytesIO(body))
                if mode == "mass":
                    _check_mass_arrays(arrays, job)
                elif mode == "summary":
                    _check_summary_arrays(arrays, job)
                else:
                    _check_rows_arrays(arrays, job)
            ok.append(job.job_id)
        except Exception as exc:  # noqa: BLE001 -- every failure is reported, none hidden
            logging.warning(f"attention: {job.key} failed capture verification: {exc!r}")
            bad.append(job.job_id)
    return ok, bad


def _capture_rank_records(entry: Any) -> Dict[str, Mapping[str, Any]]:
    """Return the per-rank done-file bodies inside one ``/status`` results entry.

    The agent keys a job's entry by rank string (``{"0": done-json, ...}``)
    and may add a top-level ``"error"`` when the job never reached its ranks;
    that key is not a rank and is dropped here.

    Parameters
    ----------
    entry : Any
        One value of ``status["attn"]["results"]``, or ``None``.

    Returns
    -------
    Dict[str, Mapping[str, Any]]
        Rank string -> done-file body; empty when `entry` is not a mapping.
    """
    if not isinstance(entry, Mapping):
        return {}
    return {k: v for k, v in entry.items() if k != "error" and isinstance(v, Mapping)}


def capture_job_failure(entry: Any, tp: int) -> Optional[str]:
    """Return why a reported job failed, or ``None`` when every rank succeeded.

    A job is only as good as its worst rank: analysis concatenates the ranks
    along the head axis, so a job with a silent rank is not a partial result,
    it is a wrong one.

    Parameters
    ----------
    entry : Any
        The job's ``status["attn"]["results"]`` entry, or ``None`` when the
        box never reported it.
    tp : int
        Tensor-parallel degree: how many ranks must report.

    Returns
    -------
    Optional[str]
        A human-readable reason, or ``None`` if the job passed.
    """
    if entry is None:
        return "the box never reported the job"
    if isinstance(entry, Mapping) and "error" in entry:
        # The agent's shape for a job whose prefill (or done-file wait) raised.
        return f"the agent reported an error: {entry['error']!r}"
    ranks = _capture_rank_records(entry)
    missing = [str(r) for r in range(tp) if str(r) not in ranks]
    if missing:
        return f"ranks {missing} of {tp} did not report"
    failed = sorted(r for r, rec in ranks.items() if not rec.get("ok"))
    if failed:
        reasons = "; ".join(f"r{r}: {ranks[r].get('error')!r}" for r in failed)
        return f"ranks {failed} reported ok=false ({reasons})"
    return None


def _poll_attn(
    ec2: Any,
    state: Dict[str, Any],
    *,
    poll_s: int,
    timeout_s: int,
    label: str,
) -> Dict[str, Any]:
    """Poll ``/status["attn"]`` until the run stops; return the last status body.

    The agent sets ``running`` synchronously before it answers ``attn_start``,
    so the first poll after a start always observes ``True`` -- no "has it
    begun yet?" grace period is needed, and a ``running`` that is already
    false means the batch is genuinely over.

    Parameters
    ----------
    ec2 : Any
        Anything with ``attn_status(state)``; the EC2 provider module is the
        production one, injected so tests can fake it.
    state : Dict[str, Any]
        Provisioned-instance state.
    poll_s : int
        Seconds between polls. Each poll also touches the box's
        ``last_active``, so it must stay well under the idle watchdog window.
    timeout_s : int
        Ceiling for the whole batch, measured on ``time.monotonic()`` (immune
        to a wall-clock step).
    label : str
        Batch description used in the timeout message.

    Returns
    -------
    Dict[str, Any]
        The final ``attn`` status block (the one with ``running`` false).

    Raises
    ------
    TimeoutError
        When the deadline passes with the run still going.
    """
    deadline = time.monotonic() + timeout_s
    while True:
        status = ec2.attn_status(state)
        if not status.get("running"):
            return status
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"attention capture batch ({label}) did not finish within {timeout_s}s"
            )
        time.sleep(poll_s)


def job_keys_present(client: Any, bucket: str, job: Job) -> List[str]:
    """Return every key already in `bucket` that belongs to `job`.

    A job's objects are ``<stem>.r<rank>.npz`` and ``<stem>.r<rank>.json``, with
    ``<stem>`` the job key minus ``.npz``. The listing prefix is ``<stem>.``
    (dot included), so ``q3.`` never matches ``q30.r0.npz``. It is NOT limited
    to ranks ``0 .. tp - 1``: a leftover from a run with a different ``tp`` is
    still an existing key that a new upload must not touch.

    Parameters
    ----------
    client : Any
        boto3 S3 client; only ``list_objects_v2`` is used (existence needs no
        HEAD, and a listing also reveals partial uploads).
    bucket : str
        Bucket to look in.
    job : Job
        The job whose key stem is listed.

    Returns
    -------
    List[str]
        Existing keys in listing order; empty when the job has none.

    Notes
    -----
    Follows ``ContinuationToken`` while ``IsTruncated``, so a stem with more
    than 1000 keys is still listed completely. Read-only.
    """
    prefix = job.key[: -len(".npz")] + "."
    found: List[str] = []
    token: Optional[str] = None
    while True:
        kwargs: Dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
        if token is not None:
            kwargs["ContinuationToken"] = token
        listing = client.list_objects_v2(**kwargs)
        found.extend(o["Key"] for o in listing.get("Contents") or [])
        if not listing.get("IsTruncated"):
            return found
        token = listing["NextContinuationToken"]


def fill_refusal(
    client: Any,
    bucket: str,
    job: Job,
    tp: int,
    mode: str,
    present: Sequence[str],
) -> Optional[str]:
    """Return why a stem holding the keys `present` must NOT be completed, else ``None``.

    Fill mode (``run_capture_batches(fill=True)``) completes a stem that an
    earlier run left partly uploaded. That is only sound when the objects that
    already exist were written by the same kind of capture as the ones this run
    will add, because analysis concatenates the ranks of a job along the head
    axis. Checked in this order:

    1. a present key outside the expected set (both objects of ranks
       ``0 .. tp - 1``): a leftover rank from a run with another tensor-parallel
       degree (message contains ``unexpected``);
    2. no ``.json`` meta among the expected present keys, so the mode cannot be
       read (``meta``);
    3. the lowest-rank present meta is not a JSON object (``meta``);
    4. that meta's mode differs from `mode` (``mode``), its ``capture_version``
       differs from ``CAPTURE_VERSIONS[mode]`` (``capture_version``), or its
       ``tp`` differs from `tp` (``tp``).

    A meta without ``mode`` is a mass capture and one without
    ``capture_version`` is version 1: both fields were added after the first
    captures were written, so their absence dates the object. Every refusal
    message starts ``"fill refused: "``.

    Parameters
    ----------
    client : Any
        boto3 S3 client; only ``get_object`` is used.
    bucket : str
        Bucket holding the stem.
    job : Job
        The job about to be completed; ``job.key`` names the stem.
    tp : int
        Tensor-parallel degree of this run. At least 1.
    mode : str
        The run's capture mode, one of ``CAPTURE_MODES``.
    present : Sequence[str]
        Keys that exist under the stem (``job_keys_present``). Non-empty in
        practice; an empty sequence is refused as having no meta.

    Returns
    -------
    Optional[str]
        The refusal reason, or ``None`` when the stem may be completed.

    Raises
    ------
    ValueError
        When `mode` is not one of ``CAPTURE_MODES``.

    Notes
    -----
    Reads exactly one meta object (the lowest-rank one present); one meta is
    enough because the box writes every rank of a run with the same mode,
    version and ``tp``, and rank-mixing across runs is what check 1 and the
    per-run version pin are for. A meta that lacks ``tp`` is refused like a
    differing one: it cannot be shown compatible. Read-only.
    """
    _check_mode(mode)
    # Design: the expected set is built from rank_keys, the one place that
    # knows the object names, so this check cannot drift from the uploader.
    expected = {rank: rank_keys(job.key, rank) for rank in range(tp)}
    expected_keys = {key for pair in expected.values() for key in pair}
    unexpected = sorted(k for k in present if k not in expected_keys)
    if unexpected:
        return (
            f"fill refused: unexpected key(s) {unexpected} outside ranks 0..{tp - 1} "
            "(a capture with another tensor-parallel degree)"
        )
    present_set = set(present)
    meta_key = next(
        (expected[rank][1] for rank in range(tp) if expected[rank][1] in present_set), None
    )
    if meta_key is None:
        return "fill refused: no meta (.json) among the existing objects, so the capture mode cannot be read"
    try:
        meta = json.loads(client.get_object(Bucket=bucket, Key=meta_key)["Body"].read().decode())
    except ValueError as exc:  # JSONDecodeError and UnicodeDecodeError are both ValueErrors
        return f"fill refused: meta {meta_key} is not valid JSON ({exc})"
    if not isinstance(meta, dict):
        return f"fill refused: meta {meta_key} is not a JSON object"
    stored_mode = meta.get("mode", "mass")
    if stored_mode != mode:
        return f"fill refused: mode of the existing capture is {stored_mode!r}, this run is {mode!r}"
    stored_version = meta.get("capture_version", 1)
    if stored_version != CAPTURE_VERSIONS[mode]:
        return (
            f"fill refused: capture_version of the existing capture is {stored_version!r}, "
            f"this run writes {CAPTURE_VERSIONS[mode]}"
        )
    if meta.get("tp") != tp:
        return f"fill refused: tp of the existing capture is {meta.get('tp')!r}, this run is {tp}"
    return None


def _engine_gone_error(entry: Any) -> Optional[str]:
    """Return the agent's error string when `entry` carries an engine-gone error, else ``None``.

    Parameters
    ----------
    entry : Any
        One ``status["attn"]["results"]`` value, or ``None`` for a job the
        agent never reported.

    Returns
    -------
    Optional[str]
        The top-level ``"error"`` string when `entry` is a mapping whose error
        contains any of ``ENGINE_GONE_MARKERS``; ``None`` otherwise. A per-rank
        error inside the rank records is not looked at: the agent puts the
        server's answer at the top level, and a rank's own failure is not the
        server's.
    """
    if not isinstance(entry, Mapping):
        return None
    error = entry.get("error")
    if isinstance(error, str) and any(marker in error for marker in ENGINE_GONE_MARKERS):
        return error
    return None


def _trailing_engine_errors(
    sent: Mapping[str, Job], results: Mapping[str, Any]
) -> List[Tuple[str, str]]:
    """Return ``(job_id, error)`` for the longest suffix of `sent` where every job has an engine-gone error.

    Parameters
    ----------
    sent : Mapping[str, Job]
        The batch's jobs in SEND order (the order of the ``/attn`` lines).
    results : Mapping[str, Any]
        The agent's results; jobs it did not report are simply absent.

    Returns
    -------
    List[Tuple[str, str]]
        The run in send order; empty when the last sent job does not carry an
        engine-gone error (including when it was never reported).

    Notes
    -----
    Walked over `sent`, not over `results`: the results dict omits unreported
    jobs, so its order cannot say which jobs came last.
    """
    run: List[Tuple[str, str]] = []
    for job_id in reversed(list(sent)):
        error = _engine_gone_error(results.get(job_id))
        if error is None:
            break
        run.append((job_id, error))
    run.reverse()
    return run


@dataclass
class CaptureResult:
    """What ``run_capture_batches`` produced, keyed by ``Job.job_id``.

    Every job id lands in exactly one of ``verified``, ``failed``,
    ``skipped_existing`` and ``not_sent``.
    """

    #: Jobs that passed both gates (the box's report and the upload check).
    verified: List[str] = field(default_factory=list)
    #: job_id -> why the job failed. Includes jobs that fill mode refused to
    #: complete (never sent) and jobs the agent attempted while the engine died.
    failed: Dict[str, str] = field(default_factory=dict)
    #: job_id -> the keys already in the bucket; such a job was NOT sent.
    skipped_existing: Dict[str, List[str]] = field(default_factory=dict)
    #: Jobs never handed to the agent because the engine had died in an earlier
    #: batch, in run order. Nothing was listed or presigned for them, so they
    #: can be sent again unchanged on a fresh box.
    not_sent: List[str] = field(default_factory=list)
    #: ``"<job_id>: <error>"`` for the job in flight when the engine died, or
    #: ``None`` when it did not die during this run.
    engine_died: Optional[str] = None
    #: job_id -> rank string -> the box's ``gate_max_rel`` (``None`` if the rank
    #: reported none). Recorded for failed jobs too: a near-miss is told from a
    #: broken capture by this number.
    gates: Dict[str, Dict[str, Optional[float]]] = field(default_factory=dict)


def run_capture_batches(
    ec2: Any,
    state: Dict[str, Any],
    served_model_name: str,
    jobs: Sequence[Job],
    tp: int,
    s3_client_factory: Callable[[], Any],
    bucket: str,
    *,
    mode: str = "mass",
    batch_size: int = DEFAULT_BATCH_SIZE,
    url_ttl_s: int = DEFAULT_URL_TTL_S,
    poll_s: int = DEFAULT_POLL_S,
    batch_timeout_s: int = DEFAULT_BATCH_TIMEOUT_S,
    fill: bool = False,
    on_engine_death: Optional[Callable[[Mapping[str, Any]], None]] = None,
) -> CaptureResult:
    """Send `jobs` to a serving capture box in batches and verify what lands in `bucket`.

    Billed: the box is already serving in capture mode (the caller owns that),
    and each batch is one ``/attn`` call. Jobs are ordered LONGEST SEQUENCE
    FIRST so a prefill too big for the box's memory fails before the cheap work.
    Per batch, one fresh S3 client mints the presigned URLs; a job that already
    has ANY key under its stem is skipped, never sent (unless `fill` is set).
    After each batch every job is gated on the box's per-rank report
    (``capture_job_failure``) and then on the bucket
    (``verify_capture_uploads``). When a batch shows that the vLLM engine died,
    no further batch is started (see Notes).

    Parameters
    ----------
    ec2 : Any
        Anything with ``attn_start(state, payload)`` and ``attn_status(state)``;
        the provider module ``smolbench.evals.providers.ec2`` is the production
        one. Not imported here.
    state : Dict[str, Any]
        Provisioned-instance state, handed to `ec2` unchanged.
    served_model_name : str
        The name the box serves the model under.
    jobs : Sequence[Job]
        Jobs to capture. Ids must be unique; every job's ``mode`` must equal
        `mode`. Not mutated.
    tp : int
        Tensor-parallel degree of the box: ranks, hence uploads, per job.
        At least 1.
    s3_client_factory : Callable[[], Any]
        Returns a NEW boto3 S3 client on each call. The client must be built
        with ``Config(signature_version="s3v4")`` so the presigned URLs sign
        ``If-None-Match`` (``presign_put`` raises otherwise).
    bucket : str
        Destination bucket.
    mode : str, optional
        ``"mass"`` (default), ``"summary"`` or ``"rows"``; selects the array
        checks. Every job must have been built for the same mode.
    batch_size : int, optional
        Jobs per ``/attn`` call.
    url_ttl_s : int, optional
        Presigned-URL lifetime in seconds; must exceed `batch_timeout_s`.
    poll_s : int, optional
        ``/status`` cadence in seconds.
    batch_timeout_s : int, optional
        Per-batch ceiling in seconds.
    fill : bool, optional
        Complete stems that an earlier run left partly uploaded, by default
        ``False`` (any existing key skips the job, as before). When ``True`` a
        job with existing keys is first checked by ``fill_refusal``; a refused
        stem goes to ``failed`` with the refusal and is not sent. Otherwise a
        stem holding every expected object (both objects of ranks
        ``0 .. tp - 1``) goes to ``skipped_existing`` and an incomplete one is
        sent with presigned URLs for EVERY rank: the box answers the objects
        that exist with "already stored" and uploads the rest. The serve must
        have been started with fill enabled (``SMOLBENCH_ATTN_FILL=1``),
        otherwise the box reports the existing objects as failed uploads.
    on_engine_death : Callable[[Mapping[str, Any]], None], optional
        Called once, when the engine is declared dead, with the full
        ``ec2.attn_full_status(state)`` reply (log tail included), or with
        ``{"error": "<ExceptionType>: <message>"}`` when that call raised. It
        runs before the batch's upload verification. An ``Exception`` it raises
        is logged and swallowed: a hook must never lose the result.

    Returns
    -------
    CaptureResult
        Every job id lands in exactly one of ``verified``, ``failed``,
        ``skipped_existing`` and ``not_sent``; ``gates`` carries the reported
        gate numbers and ``engine_died`` names the job in flight when the
        engine died (``None`` otherwise).

    Raises
    ------
    ValueError
        When `mode` is unknown, `url_ttl_s` does not exceed `batch_timeout_s`,
        `tp` or `batch_size` is below 1, a job id repeats, or a job's mode
        differs from `mode`. All raised before `ec2` or S3 is touched.
    TimeoutError
        When a batch outlives `batch_timeout_s`.

    Notes
    -----
    Writes nothing to S3 itself (the box uploads through the presigned URLs;
    the caller writes any manifest) and never deletes. Memory is O(batch) token
    ids on top of the caller's `jobs`.

    Engine death. The agent runs EVERY job of a batch and never abandons it, so
    after vLLM's engine dies (a step of a ~87K-token cell outlasting vLLM's step
    timeout) the rest of the batch is attempted against a dead server: the job
    in flight reports ``HTTP Error 500`` and each later job a reset, broken pipe
    or refused connection (``ENGINE_GONE_MARKERS``). The driver sees none of it
    until the batch ends, so the batch's results are inspected afterwards: the
    sent jobs are walked in SEND order (not ``results`` order, which omits
    unreported jobs) and the TRAILING RUN, the longest suffix in which every
    job carries an engine-gone error, is taken. An engine error followed by a
    job that did not carry one is never a death, because a dead engine cannot
    serve the later job; a suffix is the only shape a death can leave. A
    non-empty run is then corroborated with one ``ec2.attn_full_status(state)``
    call, since a live engine can also end a batch on a transient connection
    error. The engine is declared dead when that call raises (stopping is the
    cheap mistake: the unsent jobs are recorded in ``not_sent`` and can be sent
    again) or when ``healthy`` is not ``True`` or ``container`` is not
    ``"running"``. The status is asked ONLY when the run is non-empty. When
    dead, the first job of the run is failed ``"engine died during this job: "``
    and the others ``"engine already dead: "`` (the agent attempted them, so
    they are failures, not ``not_sent``); every job of every later batch goes to
    ``not_sent`` without listing keys or minting a URL, and the result is
    returned normally. When not dead, those jobs are gated like any other.
    """
    # Phase 1: argument checks, before anything touches the box or the bucket.
    _check_mode(mode)
    _check_url_ttl(url_ttl_s, batch_timeout_s)
    if tp < 1:
        raise ValueError(f"tp must be >= 1, got {tp}")
    if batch_size < 1:
        raise ValueError(f"batch_size must be >= 1, got {batch_size}")
    seen: set = set()
    for job in jobs:
        if job.job_id in seen:
            raise ValueError(f"duplicate job id {job.job_id!r}")
        seen.add(job.job_id)
        if job.mode != mode:
            raise ValueError(f"job {job.job_id!r} has mode {job.mode!r}, run is {mode!r}")

    result = CaptureResult()
    # Phase 2: longest first. The sort is stable, so equal lengths keep the
    # caller's order.
    ordered = sorted(jobs, key=lambda j: j.n_tokens, reverse=True)

    for start in range(0, len(ordered), batch_size):
        batch = ordered[start:start + batch_size]
        label = f"jobs {start}..{start + len(batch) - 1} of {len(ordered)}"
        # A fresh client per batch: credentials rotate, and a long run must not
        # sign its later URLs with an expired session. Never reused across batches.
        client = s3_client_factory()

        # Phase 3: append-only skip, then mint URLs for the rest. The skip is
        # decided BEFORE any URL exists: each URL carries If-None-Match: *, so S3
        # answers 412 for a key that already exists, and the pre-check avoids
        # sending a job with any key present at all. Fill mode relaxes this for
        # a stem that is compatible but incomplete: it is sent, and the
        # If-None-Match on every URL still guarantees nothing is replaced.
        sent: Dict[str, Job] = {}
        lines: List[Dict[str, Any]] = []
        for job in batch:
            present = job_keys_present(client, bucket, job)
            if present and fill:
                # Refusals come first: a stem with a stray rank is refused even
                # when every expected object is also there.
                refusal = fill_refusal(client, bucket, job, tp, mode, present)
                if refusal is not None:
                    logging.warning(f"attention: {job.job_id} not sent: {refusal}")
                    result.failed[job.job_id] = refusal
                    continue
                expected_keys = {k for rank in range(tp) for k in rank_keys(job.key, rank)}
                if expected_keys.issubset(present):
                    logging.warning(f"attention: {job.job_id} not sent, all {len(present)} object(s) already exist")
                    result.skipped_existing[job.job_id] = present
                    continue
                logging.warning(
                    f"attention: {job.job_id} has {len(present)} of {len(expected_keys)} "
                    "object(s); sending it to complete the stem"
                )
            elif present:
                logging.warning(f"attention: {job.job_id} not sent, {len(present)} key(s) already exist")
                result.skipped_existing[job.job_id] = present
                continue
            put_urls: List[str] = []
            meta_put_urls: List[str] = []
            for rank in range(tp):
                npz_key, meta_key = rank_keys(job.key, rank)
                put_urls.append(presign_put(client, bucket, npz_key, "application/octet-stream", url_ttl_s))
                meta_put_urls.append(presign_put(client, bucket, meta_key, "application/json", url_ttl_s))
            # The wire id IS the job id: ids are unique across the whole run
            # (checked above), so no address-qualified alias is needed, and the
            # box's done files and the agent's results line up with the caller's
            # ids directly.
            sent[job.job_id] = job
            lines.append({
                "job_id": job.job_id,
                "prompt_token_ids": list(job.prompt_token_ids),
                "completion_token_ids": list(job.completion_token_ids),
                "positions": list(job.positions),
                "put_urls": put_urls,
                "meta_put_urls": meta_put_urls,
                # The agent copies these into ``current.json`` verbatim and the
                # plugin validates them against ``n_tokens``.
                **job.mass_keys(),
            })
        if not lines:
            # Everything in this batch already exists: no ``/attn`` call to pay for.
            continue

        # Phase 4: run the batch on the box.
        ec2.attn_start(state, {"served_model_name": served_model_name, "tp": tp, "jobs": lines})
        status = _poll_attn(ec2, state, poll_s=poll_s, timeout_s=batch_timeout_s, label=label)
        if status.get("error"):
            # The capture thread itself died; every job below will be absent
            # from ``results``, but the cause must not be lost.
            logging.warning(f"attention: capture batch ({label}) reported: {status['error']!r}")
        results = status.get("results") or {}

        # Phase 5a: engine death. Only a non-empty trailing run of engine-gone
        # errors makes ``attn_full_status`` worth asking about (and fakes
        # without it keep working); see the Notes for why a suffix and why the
        # corroboration.
        dead_run: List[Tuple[str, str]] = []
        trailing = _trailing_engine_errors(sent, results)
        if trailing:
            full_status: Mapping[str, Any]
            try:
                reply = ec2.attn_full_status(state)
                full_status = reply if isinstance(reply, Mapping) else {"error": f"unreadable status: {reply!r}"}
                dead = full_status.get("healthy") is not True or full_status.get("container") != "running"
            except Exception as exc:  # noqa: BLE001 -- an unreadable box is treated as a dead one
                full_status = {"error": f"{type(exc).__name__}: {exc}"}
                dead = True
            if dead:
                dead_run = trailing
                first_id, first_error = trailing[0]
                result.engine_died = f"{first_id}: {first_error}"
                logging.warning(f"attention: engine died ({result.engine_died}); no further batch is sent")
                if on_engine_death is not None:
                    try:
                        on_engine_death(full_status)
                    except Exception as exc:  # noqa: BLE001 -- a hook must never lose the result
                        logging.warning(f"attention: on_engine_death hook raised {exc!r}; ignored")
        dead_ids = {job_id for job_id, _ in dead_run}

        # Phase 5, gate 1: what the box itself reported, per rank.
        ok_jobs: List[Job] = []
        for job_id, job in sent.items():
            if job_id in dead_ids:
                # The agent attempted these jobs, so they failed (they are not
                # "not sent"); the first one is the job in flight at the death.
                error = results[job_id]["error"]
                prefix = "engine died during this job: " if job_id == dead_run[0][0] else "engine already dead: "
                result.failed[job_id] = f"{prefix}{error!r}"
                logging.warning(f"attention: {job.key} ({job_id}) failed: {result.failed[job_id]}")
                continue
            entry = results.get(job_id)
            reported = _capture_rank_records(entry)
            if reported:
                # A failed rank's gate number is evidence too.
                result.gates[job_id] = {r: rec.get("gate_max_rel") for r, rec in reported.items()}
            reason = capture_job_failure(entry, tp)
            if reason is None:
                ok_jobs.append(job)
            else:
                logging.warning(f"attention: {job.key} ({job_id}) failed: {reason}")
                result.failed[job_id] = reason

        # Phase 6, gate 2: what actually landed in the bucket. A second fresh
        # client: the batch may have run for hours since the first one was built.
        if ok_jobs:
            verified, failed = verify_capture_uploads(
                s3_client_factory(), bucket, ok_jobs, tp, mode=mode
            )
            result.verified.extend(verified)
            for job_id in failed:
                result.failed[job_id] = "upload verification failed"

        # Phase 7: a dead engine ends the run. Later batches are recorded, not
        # sent: no key listing, no presigned URL, so they can be re-sent as is.
        if dead_run:
            remaining = [j.job_id for j in ordered[start + batch_size:]]
            result.not_sent.extend(remaining)
            logging.warning(
                f"attention: engine dead: {len(dead_run)} job(s) failed in this batch, "
                f"{len(remaining)} job(s) not sent"
            )
            break
    return result
