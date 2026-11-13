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
    "CaptureResult",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_BATCH_TIMEOUT_S",
    "DEFAULT_POLL_S",
    "DEFAULT_URL_TTL_S",
    "Job",
    "MASS_GATE_FRACTIONS",
    "MIN_PAD_RUN_CHARS",
    "N_TOKEN_CLASSES",
    "capture_job_failure",
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
CAPTURE_MODES: Tuple[str, ...] = ("rows", "mass")
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
        """Return the mass-mode additions to a wire job, or ``{}`` in rows mode.

        The single definition of the three mass keys. ``run_capture_batches``
        splices them into each ``/attn`` line, and the plugin's ``_read_job``
        validates exactly these three against ``n_tokens``, so they must not be
        spelled out twice and drift.

        Returns
        -------
        Dict[str, Any]
            ``{}`` when ``mode == "rows"``; otherwise ``mode``, ``query_start``
            (int) and ``classes`` (a JSON-serialisable list, not the tuple).

        Raises
        ------
        TypeError
            When a mass job carries no ``query_start`` or no ``classes``. Both
            conversions below are deliberately unguarded: a job that malformed
            must fail HERE, at the client, rather than ship an empty
            ``classes`` the plugin only rejects after a serve has been paid for.
        """
        if self.mode != "mass":
            return {}
        return {
            "mode": "mass",
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
) -> List[int]:
    """Label every token of ``prompt + completion`` with its mass-mode key class.

    The four classes of the capture contract, per token:

    * ``0`` -- prompt token carrying information: its decoded piece holds at
      least one non-whitespace character. ``" answer"`` is class 0, not
      whitespace: a piece that CONTAINS a space still carries a word.
    * ``1`` -- prompt whitespace PAD token: a whitespace-only piece lying
      inside the prompt's longest whitespace run, when that run is at least
      ``MIN_PAD_RUN_CHARS`` characters long. This is the noise arm's appended
      ``pad_unit * n``; the length floor and the longest-run restriction
      together are what keep an ordinary two-space indent, a newline between
      chat turns, or a blank line out of the pad class.
    * ``2`` -- other prompt whitespace or template token: a whitespace-only
      piece outside the pad run (short structural whitespace, or a second
      whitespace run), and an EMPTY piece -- chat-template specials decode to
      ``""`` and are structure, not information.
    * ``3`` -- completion token, reasoning and response alike. No completion id
      is decoded: its class does not depend on its text.

    Only whitespace-only tokens can be class 1, and a whitespace-only token can
    never straddle the boundary of a MAXIMAL whitespace run (whitespace on the
    far side of the boundary would have extended the run), so "inside the run"
    is a plain span containment with no partial-overlap case to resolve.

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
        plugin rejects a ``classes`` array that does not cover every token).

    Notes
    -----
    Pure: no I/O, no globals, no mutation of its arguments. One decoder call.
    Time O(len(prompt text)); space O(len(prompt)).

    Examples
    --------
    >>> table = {0: "", 1: "Hi", 2: ".", 3: " " * 40, 9: " ok"}
    >>> token_classes([0, 1, 2, 3], [9], lambda ids: [table[i] for i in ids])
    [2, 0, 0, 1, 3]
    """
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

    # Phase 2: the one run that may hold pad tokens. Below the floor there is
    # no pad run at all, and every whitespace token falls to class 2.
    run_start, run_len = _longest_whitespace_run(text)
    pad_span: Optional[Tuple[int, int]] = (
        (run_start, run_start + run_len) if run_len >= MIN_PAD_RUN_CHARS else None
    )

    # Phase 3: classify the prompt, then append the completion wholesale.
    classes: List[int] = []
    for piece, (start, end) in zip(pieces, spans):
        whitespace_only = bool(piece) and all(ch.isspace() for ch in piece)
        if whitespace_only and pad_span is not None and start >= pad_span[0] and end <= pad_span[1]:
            classes.append(1)
        elif whitespace_only or not piece:
            classes.append(2)
        else:
            classes.append(0)
    classes.extend([3] * len(completion_token_ids))
    return classes


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
) -> Job:
    """Build a validated mass-mode ``Job`` from a sequence and its key classes.

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

    Returns
    -------
    Job
        A frozen job with ``mode="mass"``, ``classes`` as a tuple of ints and
        all id sequences as tuples.

    Raises
    ------
    ValueError
        When `job_id` has a character outside the allowed set, `key` does not
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
        mode="mass",
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
    mode stores ``mass``/``entropy``/``classes`` over the whole response, so
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
        Which array layout to expect, ``"rows"`` (default) or ``"mass"``.
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
        When `mode` is neither ``"rows"`` nor ``"mass"``. This one IS raised:
        it is a programming error about all the jobs at once, not a fault of
        any one upload.

    Notes
    -----
    Network: one HEAD and one GET of the (small) meta per job per rank, plus
    `sample` downloads of a (large) array. Nothing is mutated. A missing array
    inside the npz raises ``KeyError`` from ``np.load``'s mapping, which the
    per-job handler turns into an ordinary logged failure.
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
                if int(head["ContentLength"]) != int(meta["bytes"]):
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


@dataclass
class CaptureResult:
    """What ``run_capture_batches`` produced, keyed by ``Job.job_id``."""

    #: Jobs that passed both gates (the box's report and the upload check).
    verified: List[str] = field(default_factory=list)
    #: job_id -> why the job failed. A job is in at most one of the three groups.
    failed: Dict[str, str] = field(default_factory=dict)
    #: job_id -> the keys already in the bucket; such a job was NOT sent.
    skipped_existing: Dict[str, List[str]] = field(default_factory=dict)
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
) -> CaptureResult:
    """Send `jobs` to a serving capture box in batches and verify what lands in `bucket`.

    Billed: the box is already serving in capture mode (the caller owns that),
    and each batch is one ``/attn`` call. Jobs are ordered LONGEST SEQUENCE
    FIRST so a prefill too big for the box's memory fails before the cheap work.
    Per batch, one fresh S3 client mints the presigned URLs; a job that already
    has ANY key under its stem is skipped, never sent. After each batch every
    job is gated on the box's per-rank report (``capture_job_failure``) and then
    on the bucket (``verify_capture_uploads``).

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
        ``"mass"`` (default) or ``"rows"``; selects the array checks.
    batch_size : int, optional
        Jobs per ``/attn`` call.
    url_ttl_s : int, optional
        Presigned-URL lifetime in seconds; must exceed `batch_timeout_s`.
    poll_s : int, optional
        ``/status`` cadence in seconds.
    batch_timeout_s : int, optional
        Per-batch ceiling in seconds.

    Returns
    -------
    CaptureResult
        Every job id lands in exactly one of ``verified``, ``failed`` and
        ``skipped_existing``; ``gates`` carries the reported gate numbers.

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
        # decided BEFORE any URL exists: a presigned PUT replaces an existing
        # object without complaint, so a job with any key present is never sent.
        sent: Dict[str, Job] = {}
        lines: List[Dict[str, Any]] = []
        for job in batch:
            present = job_keys_present(client, bucket, job)
            if present:
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

        # Phase 5, gate 1: what the box itself reported, per rank.
        ok_jobs: List[Job] = []
        for job_id, job in sent.items():
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
    return result
