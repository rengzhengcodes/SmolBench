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
