"""The on-box vLLM capture plugin, exercised against a stub vLLM on CPU.

Needs torch (``pytest.importorskip``): the repo venv does not ship it, so run
these under a scratch venv, e.g.
``uv venv /tmp/attnvenv && uv pip install --python /tmp/attnvenv/bin/python
torch numpy requests pytest`` then
``PYTHONPATH=$PWD /tmp/attnvenv/bin/python -m pytest tests/evals/test_attention_capture_plugin.py``.

The stub reproduces exactly what the plugin reads off vLLM: the
``Attention`` class (``layer_name, num_heads, num_kv_heads, head_size,
head_size_v, sliding_window, has_sink, kv_sharing_target_layer_name, impl``
with ``impl.scale / logits_soft_cap / sinks``), ``forward(query, key, value)``
returning ``[T, H*Dv]``, the forward context's ``no_compile_layers`` registry,
and the tensor-parallel rank. Each stub layer computes its output with an
eager reference (float32 softmax over the causal, windowed, soft-capped,
sink-augmented logits), so the plugin's rows must both match that reference
and pass its own ``rows @ V`` gate.
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from tests._paths import REPO_ROOT  # noqa: E402

PLUGIN = REPO_ROOT / "smolbench" / "evals" / "payloads" / "attention_capture_plugin.py.txt"


# --------------------------------------------------------------------------- stub vLLM
class _Impl:
    def __init__(self, scale, logits_soft_cap=0.0, sinks=None):
        self.scale = scale
        self.logits_soft_cap = logits_soft_cap
        self.sinks = sinks


class StubAttention:
    """Behaves like vLLM's Attention for everything the plugin touches."""

    registry: dict = {}

    def __init__(self, name, heads, kv_heads, head_size, *, window=None, sinks=None,
                 soft_cap=0.0, kv_target=None, scale=None, head_size_v=None):
        self.layer_name = name
        self.num_heads = heads
        self.num_kv_heads = kv_heads
        self.head_size = head_size
        self.head_size_v = head_size_v or head_size
        self.sliding_window = window
        self.has_sink = sinks is not None
        self.kv_sharing_target_layer_name = kv_target
        self.impl = _Impl(scale if scale is not None else head_size ** -0.5, soft_cap, sinks)
        StubAttention.registry[name] = self
        self.last_kv = None

    def reference(self, q3, k3, v3):
        """Eager attention output [T, H*Dv] under the layer's masks/sinks/softcap."""
        t, h, d = q3.shape
        g = h // self.num_kv_heads
        q = q3.float().view(t, self.num_kv_heads, g, d)
        k = k3.float().permute(1, 0, 2)
        logits = torch.einsum("tkgd,knd->tkgn", q, k) * getattr(self, "ref_scale", self.impl.scale)
        logits = logits.reshape(t, h, t)
        if self.impl.logits_soft_cap:
            logits = self.impl.logits_soft_cap * torch.tanh(logits / self.impl.logits_soft_cap)
        i = torch.arange(t)[:, None]
        j = torch.arange(t)[None, :]
        mask = j > i
        if self.sliding_window:
            mask |= j < i - (self.sliding_window - 1)
        logits = logits.masked_fill(mask[:, None, :], float("-inf"))
        if self.impl.sinks is not None:
            s = self.impl.sinks.float().view(1, h, 1).expand(t, h, 1)
            probs = torch.softmax(torch.cat([logits, s], dim=-1), dim=-1)[..., :t]
        else:
            probs = torch.softmax(logits, dim=-1)
        r = probs.view(t, self.num_kv_heads, g, t)
        o = torch.einsum("tkgn,knd->tkgd", r, v3.float().permute(1, 0, 2))
        return o.reshape(t, h * self.head_size_v).to(torch.bfloat16)

    def forward(self, query, key, value, output_shape=None, output_dtype=None):
        t = query.shape[0]
        q3 = query.view(t, self.num_heads, self.head_size)
        if key is None:
            k3, v3 = StubAttention.registry[self.kv_sharing_target_layer_name].last_kv
        else:
            k3 = key.view(t, self.num_kv_heads, self.head_size)
            v3 = value.view(t, self.num_kv_heads, self.head_size_v)
            self.last_kv = (k3, v3)
        return self.reference(q3, k3, v3)


#: The unwrapped forward. ``register()`` wraps the class attribute in place, so without a
#: reset every earlier test's plugin instance stays in the chain and captures (and PUTs)
#: again on each later forward.
_STUB_FORWARD = StubAttention.forward


def _install_stub_vllm(monkeypatch):
    vllm = types.ModuleType("vllm")
    layers_pkg = types.ModuleType("vllm.model_executor.layers.attention.attention")
    layers_pkg.Attention = StubAttention
    fwd = types.ModuleType("vllm.forward_context")

    class _Ctx:
        no_compile_layers = StubAttention.registry

    fwd.get_forward_context = lambda: _Ctx()
    dist = types.ModuleType("vllm.distributed.parallel_state")
    dist.get_tensor_model_parallel_rank = lambda: 0
    for name, mod in {
        "vllm": vllm,
        "vllm.model_executor": types.ModuleType("vllm.model_executor"),
        "vllm.model_executor.layers": types.ModuleType("vllm.model_executor.layers"),
        "vllm.model_executor.layers.attention": types.ModuleType("vllm.model_executor.layers.attention"),
        "vllm.model_executor.layers.attention.attention": layers_pkg,
        "vllm.forward_context": fwd,
        "vllm.distributed": types.ModuleType("vllm.distributed"),
        "vllm.distributed.parallel_state": dist,
    }.items():
        monkeypatch.setitem(sys.modules, name, mod)


def _load_plugin(monkeypatch, tmp_path):
    _install_stub_vllm(monkeypatch)
    StubAttention.registry.clear()
    monkeypatch.setattr(StubAttention, "forward", _STUB_FORWARD)
    spec = importlib.util.spec_from_loader("smolbench_attn", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(PLUGIN.read_text(), str(PLUGIN), "exec"), module.__dict__)
    monkeypatch.setenv("SMOLBENCH_ATTN_DIR", str(tmp_path))
    monkeypatch.setenv("SMOLBENCH_ATTN_GATE_TOL", "3e-2")
    uploads: dict = {}

    class _Resp:
        status_code = 200

    def fake_put(url, data=None, headers=None, timeout=None):
        uploads[url] = bytes(data)
        return _Resp()

    requests_mod = types.ModuleType("requests")
    requests_mod.put = fake_put
    monkeypatch.setitem(sys.modules, "requests", requests_mod)
    module.register()
    return module, uploads


def _arm(tmp_path, job_id, seq, n_tokens, positions, tp=1):
    job = {"job_id": job_id, "seq": seq, "n_tokens": n_tokens, "positions": positions,
           "put_urls": [f"put://{job_id}/r{r}.npz" for r in range(tp)],
           "meta_put_urls": [f"put://{job_id}/r{r}.json" for r in range(tp)]}
    (tmp_path / "current.json").write_text(json.dumps(job))
    return job


def _run_forward(layers, t, head_size, dv=None, seed=0):
    """Feed random q/k/v through every stub layer as vLLM would in one prefill."""
    gen = torch.Generator().manual_seed(seed)
    outs = {}
    for layer in layers:
        h, kv = layer.num_heads, layer.num_kv_heads
        q = torch.randn(t, h * head_size, generator=gen).to(torch.bfloat16)
        if layer.kv_sharing_target_layer_name:
            outs[layer.layer_name] = (layer, q, None, None)
            continue
        k = torch.randn(t, kv * head_size, generator=gen).to(torch.bfloat16)
        v = torch.randn(t, kv * (dv or head_size), generator=gen).to(torch.bfloat16)
        outs[layer.layer_name] = (layer, q, k, v)
    for name, (layer, q, k, v) in outs.items():
        layer.forward(q, k, v)
    return outs


def _reference_rows(layer, q, k3, positions):
    t = q.shape[0]
    q3 = q.view(t, layer.num_heads, layer.head_size)
    g = layer.num_heads // layer.num_kv_heads
    qp = q3[positions].float().view(len(positions), layer.num_kv_heads, g, -1)
    logits = torch.einsum("pkgd,knd->pkgn", qp, k3.float().permute(1, 0, 2)) * layer.impl.scale
    logits = logits.reshape(len(positions), layer.num_heads, t)
    if layer.impl.logits_soft_cap:
        logits = layer.impl.logits_soft_cap * torch.tanh(logits / layer.impl.logits_soft_cap)
    p = torch.tensor(positions)[:, None]
    j = torch.arange(t)[None, :]
    mask = j > p
    if layer.sliding_window:
        mask |= j < p - (layer.sliding_window - 1)
    logits = logits.masked_fill(mask[:, None, :], float("-inf"))
    if layer.impl.sinks is not None:
        s = layer.impl.sinks.float().view(1, -1, 1).expand(len(positions), layer.num_heads, 1)
        full = torch.softmax(torch.cat([logits, s], dim=-1), dim=-1)
        return full[..., :t], full[..., t]
    return torch.softmax(logits, dim=-1), None


# --------------------------------------------------------------------------- tests
def test_rows_match_eager_reference_across_window_gqa_sink_softcap_and_kv_sharing(
    monkeypatch, tmp_path: Path
) -> None:
    """Every family feature the three lanes need, in one stacked model."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, d = 40, 16
    sinks = torch.randn(8)
    layers = [
        StubAttention("model.layers.0.self_attn.attn", 8, 4, d),                      # plain GQA
        StubAttention("model.layers.1.self_attn.attn", 8, 4, d, window=7),            # sliding
        StubAttention("model.layers.2.self_attn.attn", 8, 8, d, sinks=sinks),         # gpt-oss sink
        StubAttention("model.layers.3.self_attn.attn", 8, 4, d, soft_cap=5.0),        # softcap
        StubAttention("model.layers.4.self_attn.attn", 8, 4, d,
                      kv_target="model.layers.1.self_attn.attn", window=7),           # Gemma-4 KV share
    ]
    positions = [33, 39]
    _arm(tmp_path, "q7", 1, t, positions)
    tensors = _run_forward(layers, t, d)

    done = json.loads((tmp_path / "done" / "q7.r0.json").read_text())
    assert done["ok"] is True, done
    assert done["gate_max_rel"] < 3e-2
    npz = np.load(io.BytesIO(uploads["put://q7/r0.npz"]))
    meta = json.loads(uploads["put://q7/r0.json"])
    assert list(npz["layers"]) == [0, 1, 2, 3, 4] and meta["layers"] == [0, 1, 2, 3, 4]
    assert npz["rows"].shape == (5, 2, 8, t) and npz["rows"].dtype == np.float16
    assert list(npz["has_sink"]) == [False, False, True, False, False]
    assert list(npz["sliding_window"]) == [0, 7, 0, 0, 7]
    assert list(npz["kv_shared_from"]) == [-1, -1, -1, -1, 1]
    assert list(npz["positions"]) == positions
    for li, layer in enumerate(layers):
        _, q, k, _ = tensors[layer.layer_name]
        k3 = (k if k is not None else tensors["model.layers.1.self_attn.attn"][2]).view(
            t, layer.num_kv_heads, d)
        ref_rows, ref_sink = _reference_rows(layer, q, k3, positions)
        got = torch.from_numpy(npz["rows"][li].astype(np.float32))
        assert torch.allclose(got, ref_rows, atol=2e-3), layer.layer_name
        # Rows sum to 1 except where a sink took mass; with the sink column
        # restored they sum to 1 again.
        total = got.sum(-1) + torch.from_numpy(npz["sink"][li].astype(np.float32))
        assert torch.allclose(total, torch.ones_like(total), atol=5e-3)
        if ref_sink is not None:
            assert torch.allclose(torch.from_numpy(npz["sink"][li].astype(np.float32)),
                                  ref_sink, atol=2e-3)
        # Causality and the window are exact zeros in the stored rows.
        for pi, p in enumerate(positions):
            if p + 1 < t:
                assert float(got[pi, :, p + 1:].abs().max()) == 0.0
            if layer.sliding_window and p - (layer.sliding_window - 1) > 0:
                assert float(got[pi, :, : p - (layer.sliding_window - 1)].abs().max()) == 0.0
    assert meta["n_tokens"] == t and meta["rank"] == 0 and meta["gate_tol"] == 3e-2
    assert set(meta["gate"]) == {l.layer_name for l in layers}


def test_gate_fails_the_job_when_the_layer_lies_about_its_scale(monkeypatch, tmp_path: Path) -> None:
    """A wrong scale makes rows @ V diverge from the kernel output: no upload, ok=false."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, d = 24, 16
    good = StubAttention("model.layers.0.self_attn.attn", 4, 4, d)
    liar = StubAttention("model.layers.1.self_attn.attn", 4, 4, d)
    liar.ref_scale = 4.0      # what the "kernel" (reference output) really used
    liar.impl.scale = 0.01    # what the layer reports to the plugin
    _arm(tmp_path, "bad", 3, t, [t - 1])
    _run_forward([good, liar], t, d)
    done = json.loads((tmp_path / "done" / "bad.r0.json").read_text())
    assert done["ok"] is False and "gate failed" in done["error"]
    assert done["gate_max_rel"] > 3e-2
    assert not uploads


def test_unarmed_forwards_and_length_mismatches_are_ignored(monkeypatch, tmp_path: Path) -> None:
    """Warm-up forwards (no job) and a forward of another length capture nothing."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, 8)
    _run_forward([layer], 12, 8)  # no current.json
    _arm(tmp_path, "q1", 5, 20, [19])
    _run_forward([layer], 12, 8)  # wrong length
    assert not (tmp_path / "done").exists() and not uploads
    _run_forward([layer], 20, 8)  # the job's forward
    assert json.loads((tmp_path / "done" / "q1.r0.json").read_text())["ok"] is True
    # The same job is never captured twice: a later forward of the same
    # length is ignored until a new seq is armed.
    uploads.clear()
    _run_forward([layer], 20, 8)
    assert not uploads
    _arm(tmp_path, "q1", 6, 20, [19])
    _run_forward([layer], 20, 8)
    assert "put://q1/r0.npz" in uploads


def test_bad_positions_fail_without_touching_the_kernel_output(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, 8)
    _arm(tmp_path, "oob", 9, 10, [10])
    _run_forward([layer], 10, 8)
    done = json.loads((tmp_path / "done" / "oob.r0.json").read_text())
    assert done["ok"] is False and "outside sequence" in done["error"] and not uploads


def test_register_is_idempotent_and_never_raises_into_serving(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    first = StubAttention.forward
    plugin.register()
    assert StubAttention.forward is first
    # A broken job file (positions not a list) must not break the forward pass.
    (tmp_path / "current.json").write_text(json.dumps({"job_id": "x", "seq": 1,
                                                       "n_tokens": 10, "positions": None}))
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, 8)
    out = _run_forward([layer], 10, 8)
    assert out and not uploads


def test_mass_mode_reduces_every_response_row_by_key_class(monkeypatch, tmp_path: Path) -> None:
    """Per-class masses and entropies of every completion row match the eager reference."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    monkeypatch.setattr(plugin, "MASS_CHUNK_ELEMENTS", 8 * 40 * 7)  # force several query chunks
    t, d = 40, 16
    sinks = torch.randn(8)
    layers = [
        StubAttention("model.layers.0.self_attn.attn", 8, 4, d, window=9),
        StubAttention("model.layers.1.self_attn.attn", 8, 8, d, sinks=sinks),
        StubAttention("model.layers.2.self_attn.attn", 8, 4, d, soft_cap=4.0,
                      kv_target="model.layers.0.self_attn.attn", window=9),
    ]
    # Prompt = 24 tokens: 10 informative, a 12-token pad run, 2 template; then 16 completion tokens.
    classes = [0] * 10 + [1] * 12 + [2] * 2 + [3] * 16
    query_start = 24
    job = _arm(tmp_path, "m1", 1, t, [t - 1, 30])
    job.update({"mode": "mass", "query_start": query_start, "classes": classes})
    (tmp_path / "current.json").write_text(json.dumps(job))
    tensors = _run_forward(layers, t, d, seed=3)

    done = json.loads((tmp_path / "done" / "m1.r0.json").read_text())
    assert done["ok"] is True, done
    npz = np.load(io.BytesIO(uploads["put://m1/r0.npz"]))
    meta = json.loads(uploads["put://m1/r0.json"])
    assert "rows" not in npz.files
    assert npz["mass"].shape == (3, t - query_start, 8, 4) and npz["mass"].dtype == np.float16
    assert npz["entropy"].shape == (3, t - query_start, 8)
    assert npz["sink"].shape == (3, t - query_start, 8)
    assert list(npz["classes"]) == classes and int(npz["query_start"]) == query_start
    assert meta["mode"] == "mass" and meta["query_start"] == query_start and meta["n_classes"] == 4
    assert meta["rows_shape"] == [3, t - query_start, 8, 4]
    onehot = torch.zeros(t, 4)
    onehot[torch.arange(t), torch.tensor(classes)] = 1.0
    for li, layer in enumerate(layers):
        _, q, k, _ = tensors[layer.layer_name]
        k3 = (k if k is not None else tensors["model.layers.0.self_attn.attn"][2]).view(t, layer.num_kv_heads, d)
        positions = list(range(query_start, t))
        ref_rows, ref_sink = _reference_rows(layer, q, k3, positions)     # [P, H, T]
        ref_mass = torch.einsum("phn,nc->phc", ref_rows, onehot)
        got_mass = torch.from_numpy(npz["mass"][li].astype(np.float32))
        assert torch.allclose(got_mass, ref_mass, atol=3e-3), layer.layer_name
        full = ref_rows if ref_sink is None else torch.cat([ref_rows, ref_sink[..., None]], dim=-1)
        ref_ent = -(full * torch.log(full.clamp_min(1e-30))).sum(-1)
        got_ent = torch.from_numpy(npz["entropy"][li].astype(np.float32))
        assert torch.allclose(got_ent, ref_ent, atol=2e-2), layer.layer_name
        got_sink = torch.from_numpy(npz["sink"][li].astype(np.float32))
        if ref_sink is not None:
            assert torch.allclose(got_sink, ref_sink, atol=3e-3)
            # Four classes plus the sink column account for the whole row.
            assert torch.allclose(got_mass.sum(-1) + got_sink, torch.ones_like(got_sink), atol=5e-3)
        else:
            assert float(got_sink.abs().max()) == 0.0
            assert torch.allclose(got_mass.sum(-1), torch.ones(t - query_start, 8), atol=5e-3)
        # Class-1 (pad) mass is exactly zero once the window has slid past the pad run.
        if layer.sliding_window:
            far = [p - query_start for p in positions if p - (layer.sliding_window - 1) > 21]
            assert float(got_mass[far, :, 1].abs().max()) == 0.0


def test_mass_mode_rejects_malformed_class_vectors(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, 8)
    job = _arm(tmp_path, "bad", 2, 10, [9])
    job.update({"mode": "mass", "query_start": 5, "classes": [0] * 9})  # one short
    (tmp_path / "current.json").write_text(json.dumps(job))
    _run_forward([layer], 10, 8)
    assert not uploads and not (tmp_path / "done").exists()  # unreadable job: ignored, never armed


# --------------------------------------------------------------------------- no-overwrite PUT
def _scripted_put(monkeypatch, plugin, script):
    """Replace ``requests.put`` with a scripted sequence of statuses or exceptions.

    Returns the list of header dicts the plugin sent, one per attempt. The
    retry back-off is stubbed so the tests do not sleep.
    """
    import time as real_time

    sent = []

    def put(url, data=None, headers=None, timeout=None):
        sent.append(dict(headers or {}))
        step = script.pop(0)
        if isinstance(step, BaseException):
            raise step
        return types.SimpleNamespace(status_code=step)

    monkeypatch.setattr(sys.modules["requests"], "put", put)
    monkeypatch.setattr(plugin, "time", types.SimpleNamespace(sleep=lambda s: None,
                                                               time=real_time.time))
    return sent


def test_put_sends_the_no_overwrite_condition(monkeypatch, tmp_path: Path) -> None:
    plugin, _uploads = _load_plugin(monkeypatch, tmp_path)
    sent = _scripted_put(monkeypatch, plugin, [200])
    assert plugin._put("put://x", b"blob", "application/octet-stream") == 200
    assert len(sent) == 1
    assert sent[0]["If-None-Match"] == "*"
    assert sent[0]["Content-Type"] == "application/octet-stream"


def test_put_412_on_the_first_attempt_is_a_failure(monkeypatch, tmp_path: Path) -> None:
    """The key existed before this upload: report 412 and do not retry."""
    plugin, _uploads = _load_plugin(monkeypatch, tmp_path)
    sent = _scripted_put(monkeypatch, plugin, [412, 200, 200])
    status = plugin._put("put://x", b"blob", "application/json")
    assert status == 412
    assert len(sent) == 1


@pytest.mark.parametrize("first", [ConnectionError("connection reset"), 503])
def test_put_412_after_an_ambiguous_attempt_means_the_earlier_put_landed(
    monkeypatch, tmp_path: Path, first
) -> None:
    """An attempt that raised (or got a 5xx) may have stored the object; its retry then sees 412."""
    plugin, _uploads = _load_plugin(monkeypatch, tmp_path)
    sent = _scripted_put(monkeypatch, plugin, [first, 412])
    status = plugin._put("put://x", b"blob", "application/octet-stream")
    assert status == plugin.PUT_LANDED_EARLIER
    assert status != 412 and len(sent) == 2
    assert all(h["If-None-Match"] == "*" for h in sent)


def test_put_412_after_a_definite_refusal_is_still_a_failure(monkeypatch, tmp_path: Path) -> None:
    """A 403 stored nothing, so a later 412 means someone else's object: a failure."""
    plugin, _uploads = _load_plugin(monkeypatch, tmp_path)
    _scripted_put(monkeypatch, plugin, [403, 412])
    assert plugin._put("put://x", b"blob", "application/octet-stream") == 412


def _one_layer_job(monkeypatch, plugin, tmp_path, script, job_id):
    sent = _scripted_put(monkeypatch, plugin, script)
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, 8)
    _arm(tmp_path, job_id, 1, 12, [11])
    _run_forward([layer], 12, 8)
    return json.loads((tmp_path / "done" / f"{job_id}.r0.json").read_text()), sent


def test_done_file_records_a_put_that_landed_on_an_earlier_attempt(monkeypatch, tmp_path: Path) -> None:
    plugin, _uploads = _load_plugin(monkeypatch, tmp_path)
    # npz: the first attempt raises, the retry sees 412 (it landed); meta: 200.
    done, sent = _one_layer_job(monkeypatch, plugin, tmp_path,
                                [ConnectionError("reset"), 412, 200], "landed")
    assert done["ok"] is True and done["uploaded"] is True, done
    assert done["http_status"] == [plugin.PUT_LANDED_EARLIER, 200]
    assert len(sent) == 3


def test_done_file_fails_a_job_whose_key_already_existed(monkeypatch, tmp_path: Path) -> None:
    plugin, _uploads = _load_plugin(monkeypatch, tmp_path)
    done, _sent = _one_layer_job(monkeypatch, plugin, tmp_path, [412, 200], "exists")
    assert done["ok"] is False and done["uploaded"] is False, done
    assert done["http_status"] == [412, 200]
    assert "upload failed" in done["error"]
