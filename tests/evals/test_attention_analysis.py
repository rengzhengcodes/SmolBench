"""Offline reader for mass-mode capture uploads: rank concatenation and the pad-mass ratio."""

from __future__ import annotations

import io
import json
from typing import Any

import numpy as np
import pytest

from smolbench.evals import attention_analysis


class TinyStore:
    """Just enough of ``S3ResultsStore`` for the loader: a bucket and get_object."""

    bucket = "b"

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.reads: list[str] = []

    def _client(self) -> Any:
        store = self

        class Client:
            def get_object(self, Bucket: str, Key: str) -> dict:
                store.reads.append(Key)
                if Key not in store.objects:
                    raise KeyError(Key)
                return {"Body": io.BytesIO(store.objects[Key])}

        return Client()


def rank_npz(*, heads: int, mass_fill: float, entropy_fill: float, sink_fill: float,
             classes: list[int], query_start: int = 4, n_layers: int = 1,
             positions: list[int] | None = None) -> bytes:
    """One rank's mass-mode npz: ``mass [L, P, H, 4]``, ``entropy``/``sink`` ``[L, P, H]``."""
    p = len(classes) - query_start
    mass = np.full((n_layers, p, heads, 4), mass_fill, np.float16)
    buf = io.BytesIO()
    np.savez(
        buf,
        mass=mass,
        entropy=np.full((n_layers, p, heads), entropy_fill, np.float16),
        sink=np.full((n_layers, p, heads), sink_fill, np.float16),
        classes=np.asarray(classes, np.uint8),
        query_start=np.asarray(query_start, np.int32),
        layers=np.arange(n_layers, dtype=np.int32),
        positions=np.asarray(positions if positions is not None else [len(classes) - 1], np.int32),
    )
    return buf.getvalue()


CLASSES = [0, 1, 1, 0, 3, 3]


def _two_ranks(store: TinyStore, prefix: str = "p/attn/i--ts/", job_id: str = "q0",
               classes_r1: list[int] | None = None) -> None:
    store.objects[f"{prefix}{job_id}.r0.npz"] = rank_npz(
        heads=1, mass_fill=0.25, entropy_fill=1.0, sink_fill=0.1, classes=CLASSES)
    store.objects[f"{prefix}{job_id}.r1.npz"] = rank_npz(
        heads=2, mass_fill=0.5, entropy_fill=2.0, sink_fill=0.2,
        classes=classes_r1 if classes_r1 is not None else CLASSES)


def test_load_mass_concatenates_the_ranks_along_the_head_axis_in_rank_order() -> None:
    """Analysis wants one array per job: rank 0's heads first, then rank 1's."""
    store = TinyStore()
    _two_ranks(store)
    out = attention_analysis.load_mass(store, "p/attn/i--ts/", "q0", 2)

    assert sorted(out) == ["classes", "entropy", "layers", "mass", "prompt_entropy", "query_start",
                           "sink", "sliding_window"]
    # A version-1 capture (no prompt_entropy, no sliding_window array) loads with None there.
    assert out["prompt_entropy"] is None and out["sliding_window"] is None
    # 1 layer, 2 queries, 1 + 2 heads, 4 classes.
    assert out["mass"].shape == (1, 2, 3, 4)
    assert out["entropy"].shape == (1, 2, 3) and out["sink"].shape == (1, 2, 3)
    # Rank order is preserved: head 0 is rank 0's, heads 1-2 are rank 1's.
    assert out["mass"][0, 0, 0, 0] == pytest.approx(0.25)
    assert list(out["mass"][0, 0, :, 0]) == pytest.approx([0.25, 0.5, 0.5])
    assert list(out["entropy"][0, 1, :]) == pytest.approx([1.0, 2.0, 2.0])
    assert list(out["sink"][0, 0, :]) == pytest.approx([0.1, 0.2, 0.2])
    assert list(out["classes"]) == CLASSES
    assert out["query_start"] == 4 and list(out["layers"]) == [0]
    # Exactly tp reads, in rank order.
    assert store.reads == ["p/attn/i--ts/q0.r0.npz", "p/attn/i--ts/q0.r1.npz"]


def test_load_mass_refuses_ranks_that_disagree_about_the_job() -> None:
    """A rank whose classes or query_start differ is a different job: never concatenate."""
    store = TinyStore()
    _two_ranks(store, classes_r1=[0, 0, 0, 0, 3, 3])
    with pytest.raises(ValueError, match="classes"):
        attention_analysis.load_mass(store, "p/attn/i--ts/", "q0", 2)

    store = TinyStore()
    _two_ranks(store)
    store.objects["p/attn/i--ts/q0.r1.npz"] = rank_npz(
        heads=2, mass_fill=0.5, entropy_fill=2.0, sink_fill=0.2, classes=CLASSES + [3],
        query_start=5)
    with pytest.raises(ValueError, match="query_start|classes"):
        attention_analysis.load_mass(store, "p/attn/i--ts/", "q0", 2)

    # A missing rank is an error, not a silently smaller head axis.
    store = TinyStore()
    _two_ranks(store)
    del store.objects["p/attn/i--ts/q0.r1.npz"]
    with pytest.raises(Exception):
        attention_analysis.load_mass(store, "p/attn/i--ts/", "q0", 2)


def test_whitespace_ratio_divides_the_pad_mass_by_the_uniform_baseline() -> None:
    """1.0 means "exactly uniform over the causal prefix"; below 1.0 means pad avoidance."""
    # classes[:5] has 2 pad tokens -> baseline 2/5; classes[:6] -> 2/6.
    mass = np.zeros((1, 2, 1, 4), np.float32)
    mass[0, 0, 0, 1] = 0.4   # == 2/5 exactly
    mass[0, 1, 0, 1] = 0.5   # == 1.5 x 2/6
    ratio = attention_analysis.whitespace_ratio(mass, np.asarray(CLASSES), 4)
    assert ratio.shape == (1, 2, 1)
    assert ratio[0, 0, 0] == pytest.approx(1.0)
    assert ratio[0, 1, 0] == pytest.approx(1.5)

    # Class 1 is the only pad class: mass in classes 0/2/3 never counts.
    other = np.zeros((1, 2, 1, 4), np.float32)
    other[..., 0] = other[..., 2] = other[..., 3] = 1.0
    assert attention_analysis.whitespace_ratio(other, np.asarray(CLASSES), 4).tolist() == [
        [[0.0], [0.0]]]

    # No pad tokens in the prefix -> the baseline is 0 and the ratio is nan,
    # never a division-by-zero inf that would poison a mean.
    nan_ratio = attention_analysis.whitespace_ratio(mass, np.asarray([0, 0, 0, 0, 3, 3]), 4)
    assert np.isnan(nan_ratio).all()

    # classes must cover every query the array carries.
    with pytest.raises(ValueError):
        attention_analysis.whitespace_ratio(mass, np.asarray(CLASSES[:5]), 4)


def test_the_loader_and_the_ratio_compose_over_a_stored_job() -> None:
    """The documented pipeline: load a job, ratio its pad mass, one number per layer-head."""
    store = TinyStore()
    _two_ranks(store)
    out = attention_analysis.load_mass(store, "p/attn/i--ts/", "q0", 2)
    ratio = attention_analysis.whitespace_ratio(
        out["mass"].astype(np.float32), out["classes"], int(out["query_start"]))
    assert ratio.shape == out["entropy"].shape
    # Every head of rank 0 filled 0.25 pad mass at query 4 (baseline 0.4).
    assert ratio[0, 0, 0] == pytest.approx(0.25 / 0.4)
    assert ratio[0, 0, 1] == pytest.approx(0.5 / 0.4)
    assert json.dumps({"finite": bool(np.isfinite(ratio).all())}) == '{"finite": true}'


# --------------------------------------------------------------------------- prompt entropy
def rank_npz_v2(*, heads: int, prompt_entropy: np.ndarray, entropy_fill: float = 1.0,
                classes: list[int] = CLASSES, query_start: int = 4,
                sliding_window: list[int] | None = None) -> bytes:
    """A version-2 rank: ``rank_npz`` plus ``prompt_entropy`` and ``sliding_window``."""
    n_layers = prompt_entropy.shape[0]
    base = np.load(io.BytesIO(rank_npz(heads=heads, mass_fill=0.25, entropy_fill=entropy_fill,
                                       sink_fill=0.0, classes=classes, query_start=query_start,
                                       n_layers=n_layers)))
    arrays = {k: base[k] for k in base.files}
    arrays["prompt_entropy"] = prompt_entropy.astype(np.float16)
    arrays["sliding_window"] = np.asarray(sliding_window or [0] * n_layers, np.int32)
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    return buf.getvalue()


def test_load_mass_joins_prompt_entropy_head_wise_and_carries_the_windows() -> None:
    store = TinyStore()
    pe0 = np.asarray([[[1.0], [np.nan]], [[0.5], [0.25]]])            # [L=2, P=2, H=1]
    pe1 = np.asarray([[[2.0, 3.0], [np.nan, np.nan]], [[1.5, 1.0], [0.75, 0.5]]])
    store.objects["p/q0.r0.npz"] = rank_npz_v2(heads=1, prompt_entropy=pe0, sliding_window=[4, 0])
    store.objects["p/q0.r1.npz"] = rank_npz_v2(heads=2, prompt_entropy=pe1, sliding_window=[4, 0])
    out = attention_analysis.load_mass(store, "p/", "q0", 2)
    assert out["prompt_entropy"].shape == (2, 2, 3) and out["prompt_entropy"].dtype == np.float16
    np.testing.assert_array_equal(out["prompt_entropy"][0, 0], np.asarray([1.0, 2.0, 3.0], np.float16))
    assert np.isnan(out["prompt_entropy"][0, 1]).all()
    assert list(out["sliding_window"]) == [4, 0]


def test_load_mass_refuses_ranks_that_disagree_about_prompt_entropy() -> None:
    """A version-1 rank beside a version-2 rank is two different captures: never join them."""
    store = TinyStore()
    store.objects["p/q0.r0.npz"] = rank_npz_v2(heads=1, prompt_entropy=np.ones((1, 2, 1)))
    store.objects["p/q0.r1.npz"] = rank_npz(heads=1, mass_fill=0.25, entropy_fill=1.0, sink_fill=0.0,
                                            classes=CLASSES)
    with pytest.raises(ValueError, match="prompt_entropy"):
        attention_analysis.load_mass(store, "p/", "q0", 2)


def test_entropy_by_layer_averages_over_positions_and_heads_skipping_nan() -> None:
    nan = np.nan
    # [L=3, P=2, H=2]. Layer 0: all defined. Layer 1: half NaN (a window past the prompt).
    # Layer 2: no defined value at all.
    pe = np.asarray([
        [[1.0, 2.0], [3.0, 4.0]],
        [[0.5, nan], [nan, 1.5]],
        [[nan, nan], [nan, nan]],
    ])
    ent = np.asarray([
        [[2.0, 2.0], [2.0, 6.0]],
        [[1.0, 1.0], [1.0, 1.0]],
        [[0.0, 4.0], [2.0, 2.0]],
    ])
    job = {"prompt_entropy": pe.astype(np.float16), "entropy": ent.astype(np.float16)}
    out = attention_analysis.entropy_by_layer(job)
    np.testing.assert_allclose(out["prompt_entropy"][:2], [2.5, 1.0])
    assert np.isnan(out["prompt_entropy"][2])
    assert list(out["prompt_entropy_count"]) == [4, 2, 0]
    np.testing.assert_allclose(out["entropy"], [3.0, 1.0, 2.0])
    assert list(out["entropy_count"]) == [4, 4, 4]
    assert out["prompt_entropy"].dtype == np.float64 and out["entropy"].dtype == np.float64


def test_entropy_by_layer_of_a_version_1_job_has_no_prompt_entropy() -> None:
    ent = np.full((2, 3, 1), 1.25, np.float16)
    out = attention_analysis.entropy_by_layer({"prompt_entropy": None, "entropy": ent})
    assert out["prompt_entropy"].shape == (2,) and np.isnan(out["prompt_entropy"]).all()
    assert list(out["prompt_entropy_count"]) == [0, 0]
    np.testing.assert_allclose(out["entropy"], [1.25, 1.25])


# --------------------------------------------------------------------------- summary captures
#: Every per-(layer, head) array of a summary capture, and its trailing shape after [L, H].
SUMMARY_FIELDS = {
    "sum_entropy": (), "sum_prompt_entropy": (), "n_prompt_entropy": (), "sum_mass": (4,),
    "sum_sink": (), "sum_pad_ratio": (), "n_pad_ratio": (), "sum_m_hp": (), "sum_chain_hi": (),
    "sum_chain_lo": (),
}
COUNT_FIELDS = ("n_prompt_entropy", "n_pad_ratio")
#: The arrays a version-4 summary adds (trailing shape after [L, H]); plus the 0-d rows_answer.
V4_FIELDS = {
    "sum_prompt_entropy_by_class": (3,), "sum_prompt_entropy_answer": (), "n_prompt_entropy_answer": (),
    "sum_prompt_entropy_by_class_answer": (3,), "sum_entropy_answer": (), "sum_mass_answer": (4,),
}
V4_COUNT_FIELDS = ("n_prompt_entropy_answer",)


def _plogp(p: np.ndarray) -> np.ndarray:
    return np.where(p > 0.0, p * np.log(np.where(p > 0.0, p, 1.0)), 0.0)


def summarize_rows(mass, entropy, sink, prompt_entropy, classes, query_start,
                   prompt_entropy_by_class=None) -> dict:
    """The summary-mode definition, applied to per-row arrays ``[L, P, H(, 4)]`` in float64.

    This is the reference the plugin's summary must match: the sums over the response rows of
    the mass-mode per-row statistics, with ``prompt_entropy`` summed and counted where it is
    defined (not NaN), the pad ratio (``whitespace_ratio``'s per-row quantity) summed and
    counted where its baseline is positive, and the three chain-rule sums over the rows where
    ``prompt_entropy`` is defined. Version 4: the same sums restricted to the answer rows (row
    token class 4) and ``rows_answer``; with ``prompt_entropy_by_class`` (``[L, P, H, 3]``, NaN
    where ``prompt_entropy`` is) also the class split, over all rows and over the answer rows.
    """
    mass = np.asarray(mass, np.float64)
    entropy = np.asarray(entropy, np.float64)
    sink = np.asarray(sink, np.float64)
    pe = np.asarray(prompt_entropy, np.float64)
    classes = np.asarray(classes)
    n_layers, p, heads = entropy.shape
    defined = ~np.isnan(pe)
    cum = np.cumsum(classes == 1)
    baseline = cum[query_start:query_start + p] / (np.arange(query_start, query_start + p) + 1.0)
    ratio_defined = np.broadcast_to((baseline > 0)[None, :, None], entropy.shape)
    ratio = np.where(ratio_defined, mass[..., 1] / np.where(baseline > 0, baseline, 1.0)[None, :, None], 0.0)
    m = mass[..., :3].sum(-1)
    r = mass[..., 3]
    group = -(_plogp(m) + _plogp(r) + _plogp(sink))
    ln_resp = np.log(np.arange(1, p + 1, dtype=np.float64))[None, :, None]
    zero = np.zeros_like(entropy)
    answer = np.broadcast_to((classes[query_start:query_start + p] == 4)[None, :, None], entropy.shape)
    a_defined = defined & answer
    pe0 = np.where(defined, pe, 0.0)
    v4 = {
        "rows_answer": int(answer[0, :, 0].sum()) if entropy.size else 0,
        "sum_prompt_entropy_answer": np.where(a_defined, pe0, 0.0).sum(1),
        "n_prompt_entropy_answer": a_defined.sum(1).astype(np.int64),
        "sum_entropy_answer": np.where(answer, entropy, 0.0).sum(1),
        "sum_mass_answer": np.where(answer[..., None], mass, 0.0).sum(1),
    }
    if prompt_entropy_by_class is not None:
        bc = np.where(defined[..., None], np.asarray(prompt_entropy_by_class, np.float64), 0.0)
        v4["sum_prompt_entropy_by_class"] = bc.sum(1)
        v4["sum_prompt_entropy_by_class_answer"] = np.where(answer[..., None], bc, 0.0).sum(1)
    return {
        **v4,
        "rows": p,
        "sum_entropy": entropy.sum(1),
        "sum_prompt_entropy": np.where(defined, pe, 0.0).sum(1),
        "n_prompt_entropy": defined.sum(1).astype(np.int64),
        "sum_mass": mass.sum(1),
        "sum_sink": sink.sum(1),
        "sum_pad_ratio": ratio.sum(1),
        "n_pad_ratio": ratio_defined.sum(1).astype(np.int64),
        "sum_m_hp": np.where(defined, m * np.where(defined, pe, 0.0), zero).sum(1),
        "sum_chain_hi": np.where(defined, entropy - group, zero).sum(1),
        "sum_chain_lo": np.where(defined, entropy - group - r * ln_resp, zero).sum(1),
    }


def synthetic_capture(seed: int, *, n_prompt: int = 14, n_completion: int = 11,
                      layers=((0, False), (5, False), (0, True), (9, True)), heads: int = 4,
                      pad: tuple[int, int] | None = (4, 10), scale: float = 1.5,
                      boost: float = 0.0, classes: np.ndarray | None = None) -> dict:
    """One sequence's attention statistics from real softmax rows, as the plugin computes them.

    ``layers`` holds ``(sliding window, has sink)`` per layer (window 0 = global). Classes:
    0 informative prompt token, 1 pad (``pad`` range, or none), 2 the last prompt token,
    3 completion. Returns the per-row float64 statistics, their float16 mass-mode copies, the
    summary of the UNROUNDED rows (what the plugin's summary mode stores) and the summary of
    the float16 rows (``summarize_rows`` of the mass-mode arrays). A given ``classes`` vector
    (a planned job's) replaces the built one; ``n_prompt`` is then its query_start and the
    completion is the rest.
    """
    rng = np.random.default_rng(seed)
    if classes is not None:
        classes = np.asarray(classes, np.uint8)
        n_completion = len(classes) - n_prompt
    qs, t = n_prompt, n_prompt + n_completion
    if classes is None:
        classes = np.zeros(t, np.uint8)
        if pad is not None:
            classes[pad[0]:pad[1]] = 1
        classes[qs - 1] = 2
        classes[qs:] = 3
    n_layers, p = len(layers), n_completion
    mass = np.zeros((n_layers, p, heads, 4))
    ent = np.zeros((n_layers, p, heads))
    sink = np.zeros((n_layers, p, heads))
    pe = np.full((n_layers, p, heads), np.nan)
    pe_bc = np.full((n_layers, p, heads, 3), np.nan)
    key_classes = np.minimum(classes, 3)  # an answer token (4) is a response key like 3
    j = np.arange(t)
    for li, (window, has_sink) in enumerate(layers):
        for h in range(heads):
            sink_logit = rng.normal(1.0, 1.0) if has_sink else None
            for i in range(p):
                pos = qs + i
                allowed = (j <= pos) & ((window == 0) | (j >= pos - (window - 1)))
                logits = rng.normal(0.0, scale, t)
                logits[qs:] += boost
                full = np.where(allowed, logits, -np.inf)
                if has_sink:
                    full = np.append(full, sink_logit)
                probs = np.exp(full - full.max())
                probs /= probs.sum()
                mass[li, i, h] = np.bincount(key_classes, weights=probs[:t], minlength=4)
                ent[li, i, h] = -_plogp(probs).sum()
                sink[li, i, h] = probs[t] if has_sink else 0.0
                keys = allowed & (j < qs)
                if keys.any():
                    sub = logits[keys]
                    logp = sub - (sub.max() + np.log(np.exp(sub - sub.max()).sum()))
                    pe[li, i, h] = -(np.exp(logp) * logp).sum()
                    pe_bc[li, i, h] = np.bincount(classes[keys], weights=-(np.exp(logp) * logp),
                                                  minlength=3)[:3]
    f16 = {name: arr.astype(np.float16) for name, arr in
           (("mass", mass), ("entropy", ent), ("sink", sink), ("prompt_entropy", pe))}
    bc16 = pe_bc.astype(np.float16)
    return {
        "classes": classes, "query_start": qs, "n_tokens": t,
        "sliding_window": np.asarray([w for w, _s in layers], np.int32),
        "has_sink": np.asarray([s for _w, s in layers], bool),
        "rows64": {"mass": mass, "entropy": ent, "sink": sink, "prompt_entropy": pe,
                   "prompt_entropy_by_class": pe_bc},
        **f16,
        "summary": summarize_rows(mass, ent, sink, pe, classes, qs, pe_bc),
        "summary_f16": summarize_rows(f16["mass"], f16["entropy"], f16["sink"], f16["prompt_entropy"],
                                      classes, qs, bc16),
    }


def capture_npz(cap: dict, rank: int, tp: int, kind: str, *, summary: str = "summary",
                drop: tuple[str, ...] = (), version: int = 4) -> bytes:
    """One rank's upload of ``cap`` in the plugin's layout: ``kind`` is "mass" or "summary".

    ``summary`` picks which summary goes in ("summary" from the unrounded rows, "summary_f16"
    from the float16 rows); ``drop`` leaves arrays out. ``version`` is the summary capture
    version: 4 (default, what the plugin writes) adds the class split and the answer sums, 3
    is the layout of the stored earlier captures.
    """
    heads = cap["entropy"].shape[2]
    local = heads // tp
    sl = slice(rank * local, (rank + 1) * local)
    n_layers = cap["entropy"].shape[0]
    arrays = {
        "classes": cap["classes"], "query_start": np.asarray(cap["query_start"], np.int32),
        "layers": np.arange(n_layers, dtype=np.int32),
        "positions": np.asarray([cap["n_tokens"] - 1], np.int32),
        "has_sink": cap["has_sink"], "sliding_window": cap["sliding_window"],
        "kv_shared_from": np.full(n_layers, -1, np.int32),
    }
    if kind == "mass":
        for name in ("mass", "entropy", "sink", "prompt_entropy"):
            arrays[name] = cap[name][:, :, sl]
    else:
        source = cap[summary]
        arrays["rows"] = np.asarray(source["rows"], np.int64)
        arrays["capture_version"] = np.asarray(version, np.int32)
        fields = {**SUMMARY_FIELDS, **(V4_FIELDS if version >= 4 else {})}
        for name in fields:
            dtype = np.int64 if name in COUNT_FIELDS + V4_COUNT_FIELDS else np.float64
            arrays[name] = np.ascontiguousarray(source[name][:, sl], dtype=dtype)
        if version >= 4:
            arrays["rows_answer"] = np.asarray(source["rows_answer"], np.int64)
    for name in drop:
        arrays.pop(name, None)
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    return buf.getvalue()


def _store_capture(store: TinyStore, prefix: str, job_id: str, cap: dict, kind: str, tp: int = 2,
                   **kw: Any) -> None:
    for rank in range(tp):
        store.objects[f"{prefix}{job_id}.r{rank}.npz"] = capture_npz(cap, rank, tp, kind, **kw)


def test_the_synthetic_summary_matches_its_definition_on_known_rows() -> None:
    """Guards the test helper itself: the summary's sums are the row sums, counts are exact."""
    cap = synthetic_capture(1)
    s = cap["summary"]
    rows = cap["rows64"]
    assert s["rows"] == 11
    np.testing.assert_allclose(s["sum_entropy"], rows["entropy"].sum(1))
    # The windowed layer (w = 5) sees a prompt key only on rows i < 4; the global layers on all.
    assert s["n_prompt_entropy"][1].tolist() == [4] * 4 and s["n_prompt_entropy"][0].tolist() == [11] * 4
    assert s["n_prompt_entropy"][3].tolist() == [8] * 4                     # w = 9: rows i < 8
    # Mass plus sink is 1 per row, so P per (layer, head).
    np.testing.assert_allclose(s["sum_mass"].sum(-1) + s["sum_sink"], 11.0)
    # The chain rule's two-sided bound holds row by row, so on the sums.
    assert (s["sum_chain_lo"] <= s["sum_m_hp"] + 1e-9).all()
    assert (s["sum_m_hp"] <= s["sum_chain_hi"] + 1e-9).all()


def test_load_capture_joins_a_summary_capture_head_wise_in_rank_order() -> None:
    cap = synthetic_capture(2)
    store = TinyStore()
    _store_capture(store, "p/", "q0", cap, "summary")
    out = attention_analysis.load_capture(store, "p/", "q0", 2)
    assert out["kind"] == "summary" and out["rows"] == 11 and out["query_start"] == 14
    for name, tail in SUMMARY_FIELDS.items():
        assert out[name].shape == (4, 4) + tail, name
        np.testing.assert_array_equal(out[name], cap["summary"][name], err_msg=name)
    assert list(out["sliding_window"]) == [0, 5, 0, 9] and list(out["layers"]) == [0, 1, 2, 3]
    np.testing.assert_array_equal(out["classes"], cap["classes"])
    assert store.reads == ["p/q0.r0.npz", "p/q0.r1.npz"]


def test_load_capture_of_a_mass_capture_is_load_mass_plus_its_kind() -> None:
    cap = synthetic_capture(3)
    store = TinyStore()
    _store_capture(store, "p/", "q0", cap, "mass")
    out = attention_analysis.load_capture(store, "p/", "q0", 2)
    ref = attention_analysis.load_mass(store, "p/", "q0", 2)
    assert out["kind"] == "mass"
    assert set(out) == set(ref) | {"kind"}
    for name in ("mass", "entropy", "sink", "prompt_entropy"):
        np.testing.assert_array_equal(out[name], ref[name])


@pytest.mark.parametrize("field", ["classes", "query_start", "layers", "sliding_window", "rows", "kind"])
def test_load_capture_refuses_summary_ranks_that_disagree(field) -> None:
    cap = synthetic_capture(4)
    store = TinyStore()
    _store_capture(store, "p/", "q0", cap, "summary")
    if field == "kind":
        store.objects["p/q0.r1.npz"] = capture_npz(cap, 1, 2, "mass")
    else:
        other = np.load(io.BytesIO(store.objects["p/q0.r1.npz"]))
        arrays = {k: other[k] for k in other.files}
        bumped = {"classes": np.roll(arrays["classes"], 1), "query_start": arrays["query_start"] + 1,
                  "layers": arrays["layers"] + 1, "sliding_window": arrays["sliding_window"] + 1,
                  "rows": arrays["rows"] + 1}
        arrays[field] = bumped[field]
        buf = io.BytesIO()
        np.savez(buf, **arrays)
        store.objects["p/q0.r1.npz"] = buf.getvalue()
    with pytest.raises(ValueError, match="mass|summary|kind" if field == "kind" else field):
        attention_analysis.load_capture(store, "p/", "q0", 2)


def test_load_mass_refuses_a_summary_capture_by_name() -> None:
    cap = synthetic_capture(5)
    store = TinyStore()
    _store_capture(store, "p/", "q0", cap, "summary")
    with pytest.raises(ValueError, match="summary"):
        attention_analysis.load_mass(store, "p/", "q0", 2)


@pytest.mark.parametrize("seed", [6, 7])
def test_entropy_by_layer_gives_the_same_means_and_counts_for_both_kinds(seed) -> None:
    """The same sequence captured both ways: identical counts, identical per-layer means.

    The summary is built from the float16 rows here, so the two kinds hold the same numbers
    and the comparison is exact up to float64 summation order; the gap between the plugin's
    unrounded summary and float16 storage is owned by the plugin test.
    """
    cap = synthetic_capture(seed, boost=1.0)
    store = TinyStore()
    _store_capture(store, "m/", "q0", cap, "mass")
    _store_capture(store, "s/", "q0", cap, "summary", summary="summary_f16", version=3)
    mass_job = attention_analysis.load_capture(store, "m/", "q0", 2)
    summary_job = attention_analysis.load_capture(store, "s/", "q0", 2)
    a = attention_analysis.entropy_by_layer(mass_job)
    b = attention_analysis.entropy_by_layer(summary_job)
    assert sorted(a) == sorted(b) == ["entropy", "entropy_count", "prompt_entropy", "prompt_entropy_count"]
    for name in ("entropy_count", "prompt_entropy_count"):
        assert a[name].dtype == b[name].dtype == np.int64, name
        np.testing.assert_array_equal(a[name], b[name], err_msg=name)
    assert a["prompt_entropy_count"].tolist() == [44, 16, 44, 32]
    for name in ("entropy", "prompt_entropy"):
        np.testing.assert_allclose(a[name], b[name], rtol=1e-12, err_msg=name)


def test_entropy_by_layer_of_a_summary_with_no_defined_prompt_entropy_is_nan() -> None:
    """query_start == 0: no prompt key anywhere, so a count of 0 and NaN, never 0/0 noise."""
    cap = synthetic_capture(8, layers=((0, False),), pad=None)
    s = dict(cap["summary"])
    s["n_prompt_entropy"] = np.zeros_like(s["n_prompt_entropy"])
    s["sum_prompt_entropy"] = np.zeros_like(s["sum_prompt_entropy"])
    job = {"kind": "summary", **s}
    out = attention_analysis.entropy_by_layer(job)
    assert out["prompt_entropy_count"].tolist() == [0] and np.isnan(out["prompt_entropy"]).all()
    assert out["entropy_count"].tolist() == [11 * 4]


@pytest.mark.parametrize("pad", [(4, 10), None])
def test_pad_ratio_sums_agree_for_both_kinds(pad) -> None:
    """The reader's pad-mass ratio: per (layer, head) sum and count over rows with a baseline."""
    cap = synthetic_capture(9, pad=pad)
    store = TinyStore()
    _store_capture(store, "m/", "q0", cap, "mass")
    _store_capture(store, "s/", "q0", cap, "summary", summary="summary_f16")
    sums_m, counts_m = attention_analysis.pad_ratio_sums(attention_analysis.load_capture(store, "m/", "q0", 2))
    sums_s, counts_s = attention_analysis.pad_ratio_sums(attention_analysis.load_capture(store, "s/", "q0", 2))
    assert sums_m.shape == sums_s.shape == counts_m.shape == counts_s.shape == (4, 4)
    assert sums_m.dtype == sums_s.dtype == np.float64
    np.testing.assert_array_equal(counts_m, counts_s)
    np.testing.assert_allclose(sums_m, sums_s, rtol=1e-6, atol=1e-9)
    if pad is None:
        assert (counts_m == 0).all() and (sums_m == 0).all()
    else:
        assert (counts_m == 11).all()
        # The mass branch is exactly the reader's former arithmetic: float32 ratio, float64 sum.
        ratio = attention_analysis.whitespace_ratio(cap["mass"].astype(np.float32), cap["classes"], 14)
        np.testing.assert_array_equal(sums_m, np.where(np.isnan(ratio), 0.0, ratio).sum(axis=1, dtype=np.float64))
