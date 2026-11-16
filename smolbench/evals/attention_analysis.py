"""Offline reader for mass-mode attention captures: rank concatenation and the pad-mass ratio.

What mass mode is
-----------------
The capture plugin (``payloads/attention_capture_plugin.py.txt``, contract in
``payloads/ATTENTION_CAPTURE_CONTRACT.md``) cannot store the ``T x T``
attention matrix of a 40k-token mark -- that is ~1.8 GB per layer-head, times
22k marks. In ``mode: "mass"`` the job therefore carries a uint8 CLASS label
per token (``0`` informative prompt token, ``1`` whitespace PAD token appended
by the noise arm, ``2`` other prompt whitespace / chat-template special, ``3``
completion token) and the plugin reduces every response row on the box: it
stores, per layer and per response query, the row's attention mass summed
over each of the four key classes, plus the row entropy and the sink mass.

Why the ranks are concatenated head-wise, in rank order
-------------------------------------------------------
Under tensor parallelism each rank owns a SLICE of every layer's attention
heads and uploads its own npz, so the stored head axis (``H_local``) is
rank-local and one job's heads are spread over ``tp`` objects. Rank ``r``
holds heads ``r * H_local .. (r + 1) * H_local - 1`` of the full head set, so
concatenating the ranks along the head axis IN RANK ORDER is what reproduces
the model's own head numbering; any other order silently relabels heads and
makes per-head statements (``layer 12 head 3 is the induction head``) wrong.

What the ratio means
--------------------
:func:`whitespace_ratio` answers the study's actual question: do the response
tokens attend to the appended whitespace padding LESS than dispersion alone
would predict? The uniform-dispersion prediction for a query at position ``p``
is the contract's ``|pad| / d`` -- the pad share of the causal context. The
ratio divides the observed class-1 mass by that prediction, so

* ``1.0`` -- exactly the uniform-dispersion prediction (the row spreads its
  mass over the prefix without regard to what the tokens are);
* ``< 1.0`` -- the response attends to the padding LESS than dispersion would
  predict, i.e. pad avoidance, which is the effect the noise arm looks for;
* ``> 1.0`` -- the response over-attends to the padding.

Prompt entropy
--------------
From capture version 2 the plugin also stores ``prompt_entropy``: the entropy
of each response row's attention restricted to the prompt keys and
renormalized to 1 (NaN where a row has no attendable prompt key).
:func:`entropy_by_layer` reduces it, and the whole-row entropy, to one mean per
layer together with the counts of defined values.

Scope
-----
This is a small OFFLINE helper: it reads finished uploads out of the results
bucket and computes. It never drives a box and never writes. Unlike
``attention.py``, which imports numpy inside the few functions that need it,
this module is numpy-only by nature, so ``numpy`` is imported at module level.
``boto3`` is deliberately NOT imported here: the results store owns the
client, and this module only borrows it.

Examples
--------
The documented pipeline is load-then-ratio::

    job = load_mass(store, prefix, "q0", tp=8)
    ratio = whitespace_ratio(
        job["mass"].astype(np.float32), job["classes"], job["query_start"]
    )   # [L, P, H]; nanmean over P is one number per layer-head
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Mapping

import numpy as np

__all__ = [
    "PAD_CLASS",
    "entropy_by_layer",
    "load_mass",
    "whitespace_ratio",
]

#: Index into the class axis of ``mass`` of the whitespace PAD class -- the
#: appended ``pad_unit * n`` run of the noise arm. Fixed by the capture
#: contract's class encoding (0 info, 1 pad, 2 other whitespace, 3 completion).
PAD_CLASS: int = 1

#: Axis of ``mass`` / ``entropy`` / ``sink`` holding heads. Rank-local in each
#: stored npz, global after :func:`load_mass` concatenates the ranks.
_HEAD_AXIS: int = 2


def load_mass(store: Any, prefix: str, job_id: str, tp: int) -> Dict[str, Any]:
    """Download one job's ``tp`` rank captures and join them into whole-model arrays.

    Reads ``<prefix><job_id>.r<rank>.npz`` for ``rank = 0 .. tp - 1``, in rank
    order, and concatenates the per-rank head slices along the head axis so
    the caller sees one array per statistic with the model's full head set.

    Every rank must AGREE about which job it captured before anything is
    concatenated: the ranks of one job are separate uploads from separate
    processes, and a mismatch in ``classes``, ``query_start`` or ``layers``
    means the objects describe different sequences. Concatenating those would
    produce a head axis mixing two jobs -- a silent, unrecoverable data fault
    -- so a disagreement raises instead.

    Parameters
    ----------
    store : Any
        Any object exposing ``bucket`` and ``_client()`` whose
        ``get_object(Bucket=, Key=)`` returns ``{"Body": <readable>}`` -- the
        results store, or a local-mirror adapter. Only that surface is used:
        ``store.bucket`` and
        ``store._client().get_object(Bucket=..., Key=...)["Body"].read()``.
        Typed loosely on purpose -- the store owns the boto3 client, this
        module only borrows it.
    prefix : str
        Key prefix of the job's capture address, INCLUDING its trailing
        ``"/"`` (e.g. ``"<exp>/<model>/seed=0/attn/<info>--<run_ts>/"``).
    job_id : str
        The job's id, which is also its key stem (e.g. ``"q0"``).
    tp : int
        Tensor-parallel degree: how many ranks uploaded for this job. Must be
        at least 1.

    Returns
    -------
    Dict[str, Any]
        Exactly these keys:

        ``mass``
            ``[L, P, H_total, 4]`` float16, ranks joined on the head axis:
            attention mass per key class.
        ``entropy``
            ``[L, P, H_total]`` float16, ranks joined on the head axis: row
            entropy in nats, the dispersion statistic itself.
        ``sink``
            ``[L, P, H_total]`` float16, ranks joined on the head axis: mass
            on the attention sink column (zeros for models without sinks).
        ``classes``
            ``[T]`` uint8, the job's per-token class labels (rank 0's).
        ``query_start``
            ``int``, the first completion index (rank 0's); the queries the
            arrays carry are ``query_start .. query_start + P - 1``.
        ``layers``
            ``[L]`` int32, the captured layer indices (rank 0's), in the same
            order as axis 0 of the arrays.
        ``prompt_entropy``
            ``[L, P, H_total]`` float16 (as stored), ranks joined on the head
            axis: entropy in nats of each response row's attention restricted
            to the prompt keys and renormalized to 1; NaN where the row has no
            attendable prompt key. ``None`` for a version-1 capture, which
            stores no such array.
        ``sliding_window``
            ``[L]`` int32, rank 0's per-layer window size (0 = global
            attention). ``None`` when the capture stores none.

    Raises
    ------
    ValueError
        When ``tp < 1``, or when a rank's ``classes``, ``query_start`` or
        ``layers`` differ from rank 0's. Also when ``prompt_entropy`` is
        present on some ranks and absent on others, or ``sliding_window``
        presence or values differ from rank 0's. The message names the
        offending field and the rank.
    Exception
        Whatever the store raises for a missing or unreadable object is
        propagated unchanged. A missing rank must be an error: swallowing it
        would yield a short head axis that still looks like a valid capture.

    Notes
    -----
    Network: exactly ``tp`` GETs, one per rank, in rank order; nothing is
    written. Array dtypes are returned AS STORED (float16) and never cast --
    the caller decides, because float16 accumulates badly: cast to float32
    (``job["mass"].astype(np.float32)``) before summing or averaging over
    queries, layers or heads.

    Examples
    --------
    >>> job = load_mass(store, "exp/m/seed=0/attn/i--ts/", "q0", 8)  # doctest: +SKIP
    >>> job["mass"].shape  # 36 layers, 1200 queries, 8 x 8 heads  # doctest: +SKIP
    (36, 1200, 64, 4)
    """
    # Guard first: ``range(0)`` would read nothing and leave rank 0 -- the
    # reference every agreement check is made against -- undefined.
    if tp < 1:
        raise ValueError(f"tp must be >= 1, got {tp}")

    # One client for all ranks: the store's ``_client()`` is deliberately
    # UNCACHED (it builds a fresh boto3 client so rotated credentials apply),
    # and the ``tp`` reads here are one logical read of one job -- short
    # enough that a credential cannot rotate underneath them.
    client = store._client()

    mass_parts: List[np.ndarray] = []
    entropy_parts: List[np.ndarray] = []
    sink_parts: List[np.ndarray] = []
    prompt_entropy_parts: List[np.ndarray] = []
    sliding_window: np.ndarray | None = None
    classes: np.ndarray | None = None
    layers: np.ndarray | None = None
    query_start: int = 0

    for rank in range(tp):
        # Key layout mirrors ``attention.rank_keys`` (``<stem>.r<rank>.npz``).
        # Spelled out rather than imported: this offline, numpy-only reader
        # stays independent of the capture client module.
        key = f"{prefix}{job_id}.r{rank}.npz"
        # No try/except: a missing rank propagates the store's own error.
        body = client.get_object(Bucket=store.bucket, Key=key)["Body"].read()
        # ``np.load`` over a BytesIO is lazy, so every array wanted is pulled
        # out inside this block -- the object itself is fetched exactly once.
        arrays = np.load(io.BytesIO(body))
        rank_classes = arrays["classes"]
        rank_layers = arrays["layers"]
        rank_query_start = int(arrays["query_start"])
        # Version-1 captures (and old fixtures) lack these two arrays.
        rank_prompt_entropy = arrays["prompt_entropy"] if "prompt_entropy" in arrays else None
        rank_sliding_window = arrays["sliding_window"] if "sliding_window" in arrays else None

        if rank == 0:
            classes, layers, query_start = rank_classes, rank_layers, rank_query_start
            sliding_window = rank_sliding_window
        else:
            # Check BEFORE appending, so a disagreeing rank can never reach
            # the concatenation. ``array_equal`` is length-aware: a rank whose
            # sequence is a different length is unequal, not a broadcast error.
            if not np.array_equal(rank_classes, classes):
                raise ValueError(
                    f"rank {rank} of job {job_id!r} disagrees about classes: the ranks "
                    "captured different jobs, refusing to concatenate their heads"
                )
            if rank_query_start != query_start:
                raise ValueError(
                    f"rank {rank} of job {job_id!r} disagrees about query_start "
                    f"({rank_query_start} != {query_start}): the ranks captured "
                    "different jobs, refusing to concatenate their heads"
                )
            if not np.array_equal(rank_layers, layers):
                raise ValueError(
                    f"rank {rank} of job {job_id!r} disagrees about layers: the ranks "
                    "captured different jobs, refusing to concatenate their heads"
                )
            # A version-1 rank beside a version-2 rank is a different capture:
            # joining them would silently drop or misalign prompt_entropy.
            if (rank_prompt_entropy is None) != (not prompt_entropy_parts):
                raise ValueError(
                    f"rank {rank} of job {job_id!r} disagrees about prompt_entropy "
                    "presence: the ranks come from different captures, refusing "
                    "to concatenate their heads"
                )
            if (rank_sliding_window is None) != (sliding_window is None) or (
                sliding_window is not None
                and not np.array_equal(rank_sliding_window, sliding_window)
            ):
                raise ValueError(
                    f"rank {rank} of job {job_id!r} disagrees about sliding_window: "
                    "the ranks captured different jobs, refusing to concatenate "
                    "their heads"
                )

        mass_parts.append(arrays["mass"])
        entropy_parts.append(arrays["entropy"])
        sink_parts.append(arrays["sink"])
        if rank_prompt_entropy is not None:
            prompt_entropy_parts.append(rank_prompt_entropy)

    # Rank order is list order, so a plain concatenate reproduces the model's
    # own head numbering. Dtypes are preserved (no ``astype``) by design.
    return {
        "mass": np.concatenate(mass_parts, axis=_HEAD_AXIS),
        "entropy": np.concatenate(entropy_parts, axis=_HEAD_AXIS),
        "sink": np.concatenate(sink_parts, axis=_HEAD_AXIS),
        "classes": classes,
        "query_start": query_start,
        "layers": layers,
        "prompt_entropy": (
            np.concatenate(prompt_entropy_parts, axis=_HEAD_AXIS)
            if prompt_entropy_parts
            else None
        ),
        "sliding_window": sliding_window,
    }


def entropy_by_layer(job: Mapping[str, Any]) -> Dict[str, np.ndarray]:
    """Reduce the row entropies of a joined job to one NaN-aware mean per layer.

    Averages ``job["entropy"]`` and ``job.get("prompt_entropy")`` over the
    response positions and heads of each layer, skipping NaN. The number of
    defined values per layer is returned beside each mean so a caller can pool
    several layers exactly: sum ``mean * count`` over the chosen layers and
    divide by the summed count.

    Parameters
    ----------
    job : Mapping[str, Any]
        A joined job as returned by :func:`load_mass`. Only ``"entropy"``
        (``[L, P, H]``) and ``"prompt_entropy"`` (``[L, P, H]`` or ``None``;
        a missing key counts as ``None``) are read. Not mutated.

    Returns
    -------
    Dict[str, np.ndarray]
        Exactly these keys:

        ``prompt_entropy``
            ``[L]`` float64, per-layer mean of the prompt entropy over
            positions and heads; NaN for a layer with no defined value, and
            all NaN (L taken from ``entropy``) when the job has none.
        ``prompt_entropy_count``
            ``[L]`` int64, defined (non-NaN) values per layer; all zeros when
            the job has none.
        ``entropy``
            ``[L]`` float64, the same mean of the whole-row entropy.
        ``entropy_count``
            ``[L]`` int64, defined values per layer.

    Raises
    ------
    ValueError
        When ``entropy`` is not 3-d, or ``prompt_entropy`` is given with a
        shape different from ``entropy``'s.

    Notes
    -----
    Values are cast to float64 before summing, since float16 accumulates
    badly. Sums and counts are divided with ``np.divide(..., where=count > 0)``
    into a NaN-filled array rather than ``np.nanmean``, so an all-NaN layer
    gives NaN without a RuntimeWarning.

    Examples
    --------
    >>> e = np.asarray([[[1.0, 3.0]], [[2.0, 2.0]]], np.float16)  # [L=2, P=1, H=2]
    >>> out = entropy_by_layer({"entropy": e, "prompt_entropy": None})
    >>> out["entropy"].tolist(), out["prompt_entropy_count"].tolist()
    ([2.0, 2.0], [0, 0])
    """
    entropy = np.asarray(job["entropy"])
    if entropy.ndim != 3:
        raise ValueError(f"entropy must be 3-d [L, P, H], got ndim {entropy.ndim}")
    prompt_entropy = job.get("prompt_entropy")
    if prompt_entropy is not None:
        prompt_entropy = np.asarray(prompt_entropy)
        if prompt_entropy.shape != entropy.shape:
            raise ValueError(
                f"prompt_entropy shape {prompt_entropy.shape} differs from "
                f"entropy shape {entropy.shape}"
            )

    def _mean_and_count(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Per-layer NaN-skipping mean and defined-value count of ``[L, P, H]``."""
        values = values.astype(np.float64)
        defined = ~np.isnan(values)
        count = defined.sum(axis=(1, 2)).astype(np.int64)
        total = np.where(defined, values, 0.0).sum(axis=(1, 2))
        mean = np.full(total.shape, np.nan, dtype=np.float64)
        np.divide(total, count, out=mean, where=count > 0)
        return mean, count

    n_layers = entropy.shape[0]
    if prompt_entropy is None:
        pe_mean = np.full(n_layers, np.nan, dtype=np.float64)
        pe_count = np.zeros(n_layers, dtype=np.int64)
    else:
        pe_mean, pe_count = _mean_and_count(prompt_entropy)
    e_mean, e_count = _mean_and_count(entropy)
    return {
        "prompt_entropy": pe_mean,
        "prompt_entropy_count": pe_count,
        "entropy": e_mean,
        "entropy_count": e_count,
    }


def whitespace_ratio(mass: np.ndarray, classes: np.ndarray, query_start: int) -> np.ndarray:
    """Divide the observed whitespace-PAD mass by the uniform-dispersion baseline.

    Pure function, no IO. For the query at absolute position
    ``p = query_start + i`` the baseline is the contract's ``|pad| / d``:
    ``n_pad(p) / (p + 1)``, where ``n_pad(p)`` counts the class-1 entries of
    ``classes[: p + 1]``. That prefix INCLUDES the query position itself,
    which is exactly the causal context length ``d`` the prediction divides by
    (a causal row at ``p`` has ``p + 1`` key columns).

    Parameters
    ----------
    mass : np.ndarray
        ``[L, P, H, C]`` per-class attention mass, as returned by
        :func:`load_mass` under key ``"mass"``. Cast it to float32 first if
        anything downstream averages it. Not mutated.
    classes : np.ndarray
        ``[T]`` per-token class labels (array-like is accepted and converted).
        Must cover ``query_start + P`` positions.
    query_start : int
        Absolute position of the first query in `mass`, i.e. the first
        completion index.

    Returns
    -------
    np.ndarray
        ``[L, P, H]``, float32 (or float64 if `mass` is float64): observed
        class-1 mass over the uniform-dispersion prediction. ``1.0`` is
        exactly that prediction, ``< 1.0`` is pad avoidance. Entries whose
        baseline is 0 -- no pad token anywhere in the causal prefix, so the
        prediction is undefined -- are ``nan``, never ``inf``.

    Raises
    ------
    ValueError
        When `mass` is not 4-dimensional, or when `classes` is shorter than
        ``query_start + mass.shape[1]``; the message names both numbers.

    Notes
    -----
    Vectorised: one cumulative sum over `classes` gives every query's pad
    count, so the cost is ``O(T + L * P * H)`` with no Python loop over
    queries. ``nan`` rather than ``inf`` is deliberate: an ``inf`` would
    poison any downstream mean, whereas ``nan`` is skipped by ``np.nanmean``.

    Examples
    --------
    >>> classes = np.asarray([0, 1, 1, 0, 3, 3], np.uint8)
    >>> mass = np.zeros((1, 2, 1, 4), np.float32)
    >>> mass[0, 0, 0, 1] = 0.4      # classes[:5] holds 2 pads: baseline 2/5
    >>> float(whitespace_ratio(mass, classes, 4)[0, 0, 0])
    1.0
    """
    if mass.ndim != 4:
        raise ValueError(f"mass must be 4-d [L, P, H, C], got ndim {mass.ndim}")

    classes = np.asarray(classes)
    n_queries = mass.shape[1]
    needed = query_start + n_queries
    # Checked BEFORE the cumsum is sliced: a short ``classes`` would otherwise
    # slice down to fewer than P baselines and surface as an opaque broadcast
    # error instead of naming the two lengths that actually disagree.
    if classes.shape[0] < needed:
        raise ValueError(
            f"classes covers {classes.shape[0]} positions but the array carries queries "
            f"up to {needed - 1}, needing {needed}"
        )

    # ``cum[j]`` = pad tokens in ``classes[: j + 1]``, so the baseline's
    # numerator for query p is simply ``cum[p]`` -- one cumsum for all queries.
    cum = np.cumsum(classes == PAD_CLASS)
    n_pad = cum[query_start:needed].astype(np.float64)
    context_len = np.arange(query_start, needed, dtype=np.float64) + 1.0
    baseline = n_pad / context_len

    # Broadcast the per-query baseline over layers and heads.
    baseline = baseline.reshape(1, n_queries, 1)
    observed = mass[..., PAD_CLASS]

    # float16 in -> float32 out: the ratio is what gets averaged, and nan (the
    # undefined-baseline marker) must be representable in the result dtype.
    out_dtype = np.result_type(mass.dtype, np.float32)
    result = np.full(observed.shape, np.nan, dtype=out_dtype)
    # ``where=`` is the mechanism that keeps a zero baseline out of the divide
    # (those entries keep the pre-filled nan, so no inf is ever produced);
    # ``errstate`` is belt-and-braces so no numpy warning can print per call.
    with np.errstate(divide="ignore", invalid="ignore"):
        np.divide(observed, baseline, out=result, where=baseline > 0)
    return result
