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

``StubMLAAttention`` does the same for vLLM's multi-head latent attention layer
(DeepSeek-V3.1): ``forward(q, kv_c_normed, k_pe)`` rebuilds per-head keys and values
with its ``kv_b_proj`` as vLLM's prefill path does, and the forward context carries
the per-layer ``attn_metadata`` the plugin's MLA guards read.
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


class _KVBProj:
    """Stands in for vLLM's ``ColumnParallelLinear`` ``kv_b_proj``: returns ``(x @ W.T, None)``.

    ``W`` is ``[heads * (P + V), L]``, each head's rows laid out ``[k_nope P | v V]``,
    as in the checkpoint.
    """

    def __init__(self, weight):
        self.weight = weight

    def __call__(self, x):
        return x @ self.weight.T, None


class StubMLAAttention:
    """Behaves like vLLM's ``MLAAttention`` for everything the plugin may touch.

    Carries the real class's attribute traps: ``num_kv_heads = 1`` and
    ``head_size = kv_lora_rank + qk_rope_head_dim`` describe the latent cache, not the
    per-head keys, so a plugin that reads them as per-head shapes mis-reshapes. The
    forward reproduces vLLM's prefill path (``forward_mha``): per-head keys and values
    come from ``kv_b_proj(kv_c_normed)``, the shared rotated ``k_pe`` is broadcast to
    every head, causal float32 softmax with the layer's scale, output ``[T, H*V]`` bf16.
    """

    registry: dict = StubAttention.registry   # one no_compile_layers registry for both classes
    metadata: dict = {}                       # the forward context's attn_metadata, by layer name

    def __init__(self, name, heads=2, qk_nope=4, qk_rope=2, v_head_dim=3, kv_lora_rank=5,
                 scale=0.37, weight=None, seed=0):
        self.layer_name = name
        self.num_heads = heads
        self.qk_nope_head_dim = qk_nope
        self.qk_rope_head_dim = qk_rope
        self.qk_head_dim = qk_nope + qk_rope
        self.v_head_dim = v_head_dim
        self.kv_lora_rank = kv_lora_rank
        self.scale = scale
        self.num_kv_heads = 1                          # trap: the latent cache has one "head"
        self.head_size = kv_lora_rank + qk_rope        # trap: the latent cache row, not 192/P+R
        self.sliding_window = None
        self.dcp_q_replicate = False
        self.use_pcp = False
        self.use_sparse = False
        self.kv_cache_dtype = "auto"
        self.impl = types.SimpleNamespace(scale=scale, dcp_world_size=1)
        if weight is None:
            gen = torch.Generator().manual_seed(1000 + seed)
            weight = (torch.randn(heads * (qk_nope + v_head_dim), kv_lora_rank, generator=gen)
                      * kv_lora_rank ** -0.5).to(torch.bfloat16)
        self.kv_b_proj = _KVBProj(weight)
        self.out_dtype = torch.bfloat16
        StubMLAAttention.registry[name] = self
        StubMLAAttention.metadata[name] = types.SimpleNamespace(
            num_decode_tokens=0,
            prefill=types.SimpleNamespace(chunked_context=None, q_data_type=torch.bfloat16))

    def keys_values(self, kv_c_normed, k_pe):
        """Per-head (k [T, H, P+R], v [T, H, V]) exactly as the prefill path builds them."""
        t, h = kv_c_normed.shape[0], self.num_heads
        p, r, dv = self.qk_nope_head_dim, self.qk_rope_head_dim, self.v_head_dim
        kv = self.kv_b_proj(kv_c_normed)[0].view(t, h, p + dv)
        k_nope, v = kv.split([p, dv], dim=-1)
        k = torch.cat([k_nope, k_pe.view(t, 1, r).expand(t, h, r)], dim=-1)
        return k, v

    def forward(self, q, kv_c_normed, k_pe, output_shape=None, q_dcp_replicated=None):
        if getattr(self, "forced_output_numel", None) is not None:
            # A malformed-input probe: the tensors do not fit the layer's dimensions, so the
            # real math below cannot run. The plugin's shape guards must see them anyway.
            return torch.zeros(self.forced_output_numel, dtype=self.out_dtype)
        t, h = q.shape[0], self.num_heads
        k, v = self.keys_values(kv_c_normed, k_pe)
        if getattr(self, "ref_v_perm", None) is not None:   # a kernel that mixed up value heads
            v = v[:, list(self.ref_v_perm)]
        logits = torch.einsum("thd,nhd->htn", q.float(), k.float()) * getattr(self, "ref_scale", self.scale)
        mask = torch.arange(t)[None, :] > torch.arange(t)[:, None]
        probs = torch.softmax(logits.masked_fill(mask[None], float("-inf")), dim=-1)
        o = torch.einsum("htn,nhd->thd", probs, v.float())
        return o.reshape(t, h * self.v_head_dim).to(self.out_dtype)


#: The unwrapped forward. ``register()`` wraps the class attribute in place, so without a
#: reset every earlier test's plugin instance stays in the chain and captures (and PUTs)
#: again on each later forward.
_STUB_FORWARD = StubAttention.forward
_STUB_MLA_FORWARD = StubMLAAttention.forward


def _install_stub_vllm(monkeypatch, with_mla=True):
    vllm = types.ModuleType("vllm")
    layers_pkg = types.ModuleType("vllm.model_executor.layers.attention.attention")
    layers_pkg.Attention = StubAttention
    mla_pkg = types.ModuleType("vllm.model_executor.layers.attention.mla_attention")
    mla_pkg.MLAAttention = StubMLAAttention
    fwd = types.ModuleType("vllm.forward_context")

    class _Ctx:
        no_compile_layers = StubAttention.registry
        attn_metadata = StubMLAAttention.metadata

    fwd.get_forward_context = lambda: _Ctx()
    dist = types.ModuleType("vllm.distributed.parallel_state")
    dist.get_tensor_model_parallel_rank = lambda: 0
    modules = {
        "vllm": vllm,
        "vllm.model_executor": types.ModuleType("vllm.model_executor"),
        "vllm.model_executor.layers": types.ModuleType("vllm.model_executor.layers"),
        "vllm.model_executor.layers.attention": types.ModuleType("vllm.model_executor.layers.attention"),
        "vllm.model_executor.layers.attention.attention": layers_pkg,
        "vllm.forward_context": fwd,
        "vllm.distributed": types.ModuleType("vllm.distributed"),
        "vllm.distributed.parallel_state": dist,
    }
    if with_mla:
        modules["vllm.model_executor.layers.attention.mla_attention"] = mla_pkg
    else:
        monkeypatch.delitem(sys.modules, "vllm.model_executor.layers.attention.mla_attention",
                            raising=False)
    for name, mod in modules.items():
        monkeypatch.setitem(sys.modules, name, mod)


def _load_plugin(monkeypatch, tmp_path, with_mla=True):
    _install_stub_vllm(monkeypatch, with_mla=with_mla)
    StubAttention.registry.clear()
    StubMLAAttention.metadata.clear()
    monkeypatch.setattr(StubAttention, "forward", _STUB_FORWARD)
    monkeypatch.setattr(StubMLAAttention, "forward", _STUB_MLA_FORWARD)
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
    done, sent = _one_layer_job(monkeypatch, plugin, tmp_path, [412, 200], "exists")
    assert done["ok"] is False and done["uploaded"] is False, done
    assert done["http_status"] == [412]  # the meta PUT is not attempted
    assert len(sent) == 1
    assert "upload failed" in done["error"]


def test_no_meta_put_is_attempted_when_the_npz_put_fails(monkeypatch, tmp_path: Path) -> None:
    """A meta json without its npz would be a permanently partial job."""
    plugin, _uploads = _load_plugin(monkeypatch, tmp_path)
    done, sent = _one_layer_job(monkeypatch, plugin, tmp_path, [403, 403, 403, 200], "denied")
    assert len(sent) == 3, "only the npz PUT's three attempts, no meta PUT"
    assert done["ok"] is False and done["uploaded"] is False, done
    assert done["http_status"] == [403]
    assert "upload failed" in done["error"]


def test_meta_put_is_attempted_after_a_successful_npz_put(monkeypatch, tmp_path: Path) -> None:
    plugin, _uploads = _load_plugin(monkeypatch, tmp_path)
    done, sent = _one_layer_job(monkeypatch, plugin, tmp_path, [200, 200], "fine")
    assert len(sent) == 2
    assert done["ok"] is True and done["http_status"] == [200, 200], done


# --------------------------------------------------------------------------- prompt entropy
def _prompt_entropy_reference(ref_rows, query_start):
    """Renormalize each full attention row over the prompt keys, then take its entropy (nats).

    Computed from the stored-equivalent rows (the kernel's probabilities over tokens),
    deliberately not from logits, so it is an independent route to the same number.
    Rows with no prompt mass get NaN.
    """
    prompt = ref_rows[..., :query_start].double()
    total = prompt.sum(-1, keepdim=True)
    renorm = prompt / total
    ent = -(torch.where(renorm > 0, renorm * torch.log(renorm), torch.zeros_like(renorm))).sum(-1)
    return torch.where(total[..., 0] > 0, ent, torch.full_like(ent, float("nan")))


def _mass_job(tmp_path, job_id, t, query_start, classes, gate_positions):
    job = _arm(tmp_path, job_id, 1, t, gate_positions)
    job.update({"mode": "mass", "query_start": query_start, "classes": classes})
    (tmp_path / "current.json").write_text(json.dumps(job))
    return job


def test_prompt_entropy_is_the_entropy_of_the_row_renormalized_over_prompt_keys(
    monkeypatch, tmp_path: Path
) -> None:
    """Every response row, layer and head: the stored value equals the direct computation."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    monkeypatch.setattr(plugin, "MASS_CHUNK_ELEMENTS", 8 * 40 * 5)  # several query chunks
    t, d, query_start = 40, 16, 24
    # Large sink logits take a real share of each row, so including the sink column in the
    # renormalization would move the entropy far beyond float16 rounding.
    sinks = torch.full((8,), 3.0)
    layers = [
        StubAttention("model.layers.0.self_attn.attn", 8, 4, d),                       # global GQA
        StubAttention("model.layers.1.self_attn.attn", 8, 8, d, sinks=sinks),          # sink
        StubAttention("model.layers.2.self_attn.attn", 8, 4, d, soft_cap=4.0),         # softcap
        StubAttention("model.layers.3.self_attn.attn", 8, 4, d, window=9),             # sliding
    ]
    classes = [0] * 10 + [1] * 12 + [2] * 2 + [3] * 16
    _mass_job(tmp_path, "pe1", t, query_start, classes, [t - 1, 30])
    tensors = _run_forward(layers, t, d, seed=5)

    done = json.loads((tmp_path / "done" / "pe1.r0.json").read_text())
    assert done["ok"] is True, done
    npz = np.load(io.BytesIO(uploads["put://pe1/r0.npz"]))
    meta = json.loads(uploads["put://pe1/r0.json"])
    assert meta["capture_version"] == 2
    pe = npz["prompt_entropy"]
    assert pe.dtype == np.float16 and pe.shape == npz["entropy"].shape == (4, t - query_start, 8)
    positions = list(range(query_start, t))
    for li, layer in enumerate(layers):
        _, q, k, _ = tensors[layer.layer_name]
        k3 = k.view(t, layer.num_kv_heads, d)
        ref_rows, _ref_sink = _reference_rows(layer, q, k3, positions)
        ref = _prompt_entropy_reference(ref_rows, query_start).float()
        got = torch.from_numpy(pe[li].astype(np.float32))
        assert torch.equal(torch.isnan(got), torch.isnan(ref)), layer.layer_name
        finite = ~torch.isnan(ref)
        assert torch.allclose(got[finite], ref[finite], atol=1e-2, rtol=2e-3), layer.layer_name
        # The prompt-only entropy is not the whole-row entropy (that would be mutation a).
        whole = torch.from_numpy(npz["entropy"][li].astype(np.float32))
        assert float((whole[finite] - got[finite]).abs().max()) > 0.1, layer.layer_name


def test_prompt_entropy_is_nan_once_the_window_has_slid_past_the_prompt(monkeypatch, tmp_path: Path) -> None:
    """window w admits keys j >= p - (w - 1): row i = p - query_start sees a prompt key iff i < w - 1."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, d, query_start, w = 40, 16, 24, 9
    layers = [StubAttention("model.layers.0.self_attn.attn", 4, 4, d, window=w),
              StubAttention("model.layers.1.self_attn.attn", 4, 4, d)]
    classes = [0] * query_start + [3] * (t - query_start)
    _mass_job(tmp_path, "pe2", t, query_start, classes, [t - 1])
    _run_forward(layers, t, d, seed=7)
    npz = np.load(io.BytesIO(uploads["put://pe2/r0.npz"]))
    windowed = npz["prompt_entropy"][0].astype(np.float32)   # [P, H]
    glob = npz["prompt_entropy"][1].astype(np.float32)
    assert np.isfinite(windowed[: w - 1]).all()
    assert np.isnan(windowed[w - 1:]).all()
    # Boundary: row w - 2 sits at p = query_start + w - 2 and admits exactly one prompt key
    # (j = query_start - 1), so its renormalized distribution is a point mass: entropy 0.
    assert (windowed[w - 2] == 0.0).all()
    assert (windowed[: w - 2] > 0.0).all()
    # A global layer always sees the whole prompt.
    assert np.isfinite(glob).all() and (glob > 0).all()
    # The window's rows with no prompt key also carry exactly zero prompt mass.
    prompt_mass = npz["mass"][0, :, :, :3].astype(np.float32).sum(-1)
    assert (prompt_mass[w - 1:] == 0.0).all()


def test_prompt_entropy_is_nan_everywhere_without_a_prompt(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, d = 12, 8
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, d)
    _mass_job(tmp_path, "pe3", t, 0, [3] * t, [t - 1])
    _run_forward([layer], t, d, seed=2)
    npz = np.load(io.BytesIO(uploads["put://pe3/r0.npz"]))
    assert npz["prompt_entropy"].shape == (1, t, 4) and np.isnan(npz["prompt_entropy"]).all()


def test_rows_mode_meta_carries_the_capture_version(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, 8)
    _arm(tmp_path, "rv", 1, 10, [9])
    _run_forward([layer], 10, 8)
    npz = np.load(io.BytesIO(uploads["put://rv/r0.npz"]))
    assert json.loads(uploads["put://rv/r0.json"])["capture_version"] == 2
    assert "prompt_entropy" not in npz.files  # mass mode only


# --------------------------------------------------------------------------- MLA (DeepSeek-V3.1)
def _run_mla_forward(layers, t, seed=0):
    """Feed random post-RoPE q, latent kv_c_normed and shared k_pe through each MLA stub layer.

    Called the way vLLM's ``MultiHeadLatentAttentionWrapper`` calls the layer: the three
    tensors positionally, ``output_shape`` and ``q_dcp_replicated`` by keyword.
    """
    gen = torch.Generator().manual_seed(seed)
    tensors = {}
    for layer in layers:
        h, p, r = layer.num_heads, layer.qk_nope_head_dim, layer.qk_rope_head_dim
        q = torch.randn(t, h, p + r, generator=gen).to(torch.bfloat16)
        kv_c = torch.randn(t, layer.kv_lora_rank, generator=gen).to(torch.bfloat16)
        k_pe = torch.randn(t, 1, r, generator=gen).to(torch.bfloat16)
        tensors[layer.layer_name] = (layer, q, kv_c, k_pe)
    for _name, (layer, q, kv_c, k_pe) in tensors.items():
        layer.forward(q, kv_c, k_pe, output_shape=(t, layer.num_heads * layer.v_head_dim),
                      q_dcp_replicated=None)
    return tensors


def _mla_reference_rows(layer, q, kv_c, k_pe, positions):
    """Softmax rows [P, H, T] from first principles: scale * (q_nope.k_nope + q_pe.k_pe), causal."""
    t, p = q.shape[0], layer.qk_nope_head_dim
    kv = (kv_c @ layer.kv_b_proj.weight.T).view(t, layer.num_heads, p + layer.v_head_dim)
    k_nope = kv[..., :p].float()                                   # [T, H, P]
    qp = q[positions].float()                                      # [P, H, P+R]
    logits = (torch.einsum("phd,nhd->phn", qp[..., :p], k_nope)
              + torch.einsum("phd,nd->phn", qp[..., p:], k_pe.view(t, -1).float())) * layer.scale
    mask = torch.arange(t)[None, :] > torch.tensor(positions)[:, None]
    return torch.softmax(logits.masked_fill(mask[:, None, :], float("-inf")), dim=-1)


@pytest.mark.parametrize("qk_nope, v_head_dim", [(4, 3), (3, 3)])
def test_mla_rows_equal_the_reference_softmax(monkeypatch, tmp_path: Path, qk_nope, v_head_dim) -> None:
    """MLA-only model: per-head keys rebuilt from the latent, rows exact, the gate passes.

    (3, 3) makes the key and value halves of ``kv_b_proj`` the same width, as in
    DeepSeek-V3.1 (128 | 128), so swapping them is shape-preserving and only the rows
    can catch it.
    """
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t = 24
    layers = [StubMLAAttention(f"model.layers.{i}.self_attn.attn", heads=2, qk_nope=qk_nope,
                               v_head_dim=v_head_dim, seed=i) for i in range(3)]
    positions = [5, 17, 23]
    _arm(tmp_path, "mla1", 1, t, positions)
    tensors = _run_mla_forward(layers, t, seed=11)

    done = json.loads((tmp_path / "done" / "mla1.r0.json").read_text())
    assert done["ok"] is True, done
    assert done["gate_max_rel"] < 3e-2
    npz = np.load(io.BytesIO(uploads["put://mla1/r0.npz"]))
    assert list(npz["layers"]) == [0, 1, 2]
    assert npz["rows"].shape == (3, len(positions), 2, t)
    assert list(npz["kv_shared_from"]) == [-1, -1, -1]
    assert list(npz["sliding_window"]) == [0, 0, 0] and not npz["has_sink"].any()
    for li, layer in enumerate(layers):
        _, q, kv_c, k_pe = tensors[layer.layer_name]
        ref = _mla_reference_rows(layer, q, kv_c, k_pe, positions)
        got = torch.from_numpy(npz["rows"][li].astype(np.float32))
        assert torch.allclose(got, ref, atol=2e-3), layer.layer_name
        for pi, p in enumerate(positions):
            if p + 1 < t:
                assert float(got[pi, :, p + 1:].abs().max()) == 0.0


def test_mla_meta_reports_per_head_shapes_not_the_latent_traps(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layer = StubMLAAttention("model.layers.0.self_attn.attn", heads=2, qk_nope=4, qk_rope=2,
                             v_head_dim=3, kv_lora_rank=5)
    _arm(tmp_path, "mm", 1, 12, [11])
    _run_mla_forward([layer], 12)
    meta = json.loads(uploads["put://mm/r0.json"])
    assert meta["num_heads_local"] == 2
    assert meta["num_kv_heads_local"] == meta["num_heads_local"]     # not the latent's 1
    assert meta["head_size"] == 4 + 2                                 # P + R, not L + R = 7
    assert meta["attention"] == "mla"
    assert meta["qk_head_dim"] == 6 and meta["v_head_dim"] == 3 and meta["kv_lora_rank"] == 5
    assert isinstance(meta["head_order"], str) and meta["head_order"]
    assert meta["capture_version"] == 2


def test_plain_attention_meta_says_mha_and_carries_no_mla_fields(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 2, 8)
    _arm(tmp_path, "pa", 1, 10, [9])
    _run_forward([layer], 10, 8)
    meta = json.loads(uploads["put://pa/r0.json"])
    assert meta["attention"] == "mha"
    assert meta["num_kv_heads_local"] == 2 and meta["head_size"] == 8
    assert not {"qk_head_dim", "v_head_dim", "kv_lora_rank"} & set(meta)


def test_mla_gate_fails_under_a_wrong_reference_scale(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layer = StubMLAAttention("model.layers.0.self_attn.attn")
    layer.ref_scale = 4.0       # what the "kernel" used; the layer reports 0.37
    _arm(tmp_path, "msc", 1, 20, [19])
    _run_mla_forward([layer], 20, seed=2)
    done = json.loads((tmp_path / "done" / "msc.r0.json").read_text())
    assert done["ok"] is False and "gate failed" in done["error"], done
    assert done["gate_max_rel"] > 3e-2
    assert not uploads


def test_mla_gate_fails_when_the_kernel_permuted_the_value_heads(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layer = StubMLAAttention("model.layers.0.self_attn.attn", heads=2)
    layer.ref_v_perm = (1, 0)
    _arm(tmp_path, "mvp", 1, 20, [19, 12])
    _run_mla_forward([layer], 20, seed=4)
    done = json.loads((tmp_path / "done" / "mvp.r0.json").read_text())
    assert done["ok"] is False and "gate failed" in done["error"], done
    assert not uploads


def test_mla_two_rank_split_concatenates_to_the_full_model(monkeypatch, tmp_path: Path) -> None:
    """Local head j of rank r is global head 2r + j: rank rows concatenated in rank order
    equal the 4-head model's rows."""
    t, heads, P, R, V, L = 18, 4, 4, 2, 3, 5
    gen = torch.Generator().manual_seed(21)
    weight = (torch.randn(heads * (P + V), L, generator=gen) * L ** -0.5).to(torch.bfloat16)
    q = torch.randn(t, heads, P + R, generator=gen).to(torch.bfloat16)
    kv_c = torch.randn(t, L, generator=gen).to(torch.bfloat16)
    k_pe = torch.randn(t, 1, R, generator=gen).to(torch.bfloat16)
    positions = [9, 17]
    full = StubMLAAttention.__new__(StubMLAAttention)      # reference only, never registered
    full.num_heads, full.qk_nope_head_dim, full.v_head_dim, full.scale = heads, P, V, 0.37
    full.kv_b_proj = _KVBProj(weight)
    ref = _mla_reference_rows(full, q, kv_c, k_pe, positions)            # [P, 4, T]

    per_rank = []
    for rank in range(2):
        rank_dir = tmp_path / f"r{rank}"
        rank_dir.mkdir()
        plugin, uploads = _load_plugin(monkeypatch, rank_dir)           # one process per rank
        monkeypatch.setattr(plugin, "_rank", lambda rank=rank: rank)
        rows = slice(rank * 2 * (P + V), (rank + 1) * 2 * (P + V))      # ColumnParallel shard
        layer = StubMLAAttention("model.layers.0.self_attn.attn", heads=2, qk_nope=P, qk_rope=R,
                                 v_head_dim=V, kv_lora_rank=L, weight=weight[rows])
        _arm(rank_dir, "tp2", 1, t, positions, tp=2)
        layer.forward(q[:, 2 * rank: 2 * rank + 2].contiguous(), kv_c, k_pe,
                      output_shape=(t, 2 * V), q_dcp_replicated=None)
        done = json.loads((rank_dir / "done" / f"tp2.r{rank}.json").read_text())
        assert done["ok"] is True and done["rank"] == rank, done
        meta = json.loads(uploads[f"put://tp2/r{rank}.json"])
        assert meta["rank"] == rank and meta["tp"] == 2 and meta["num_heads_local"] == 2
        per_rank.append(np.load(io.BytesIO(uploads[f"put://tp2/r{rank}.npz"]))["rows"][0])
    got = torch.from_numpy(np.concatenate(per_rank, axis=1).astype(np.float32))   # [P, 4, T]
    assert torch.allclose(got, ref, atol=2e-3)


def _set(obj_path, value):
    """Return a mutator setting a dotted attribute path on an MLA stub layer."""
    def apply(layer):
        target = layer
        *head, last = obj_path.split(".")
        for part in head:
            target = getattr(target, part)
        setattr(target, last, value)
    return apply


def _metadata(mutate):
    def apply(layer):
        mutate(StubMLAAttention.metadata, layer.layer_name)
    return apply


_GUARD_CASES = {
    # design item 2: decode/prefill split
    "decode-tokens": (_metadata(lambda md, n: setattr(md[n], "num_decode_tokens", 3)), "prefill-only"),
    "no-prefill": (_metadata(lambda md, n: setattr(md[n], "prefill", None)), "prefill-only"),
    "no-metadata": (_metadata(lambda md, n: md.pop(n)), "prefill-only"),
    # design item 3: chunked context
    "chunked-context": (_metadata(lambda md, n: setattr(md[n].prefill, "chunked_context", object())),
                        "chunked-context"),
    # design item 4: FP8 prefill query
    "fp8-kv-cache": (_set("kv_cache_dtype", "fp8"), "fp8-prefill"),
    "fp8-query": (_metadata(lambda md, n: setattr(md[n].prefill, "q_data_type", torch.float8_e4m3fn)),
                  "fp8-prefill"),
    # design item 7: context parallelism, DCP query replication, sparse attention, sliding window
    "dcp-q-replicate": (_set("dcp_q_replicate", True), "dcp"),
    "dcp-world-size": (_set("impl.dcp_world_size", 2), "dcp"),
    "pcp": (_set("use_pcp", True), "pcp"),
    "sparse": (_set("use_sparse", True), "sparse"),
    "sliding-window": (_set("sliding_window", 3), "sliding-window"),
    # design item 9: fused output quantisation
    "output-dtype": (_set("out_dtype", torch.float16), "output-dtype"),
    # the scale is read from the layer, and the two copies vLLM keeps must agree
    "scale-disagrees": (_set("impl.scale", 0.5), "scale"),
}


@pytest.mark.parametrize("case", sorted(_GUARD_CASES))
def test_every_mla_guard_fails_the_job_loudly(monkeypatch, tmp_path: Path, case) -> None:
    """Each condition under which the capture could be silently wrong fails the job through
    the done file with a reason naming the guard; nothing is uploaded, serving continues."""
    mutate, guard = _GUARD_CASES[case]
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layers = [StubMLAAttention(f"model.layers.{i}.self_attn.attn", seed=i) for i in range(2)]
    mutate(layers[0])
    _arm(tmp_path, "g", 1, 16, [15])
    tensors = _run_mla_forward(layers, 16, seed=6)
    assert tensors  # the forward pass itself completed
    done = json.loads((tmp_path / "done" / "g.r0.json").read_text())
    assert done["ok"] is False, done
    assert f"MLA guard {guard}" in done["error"], done["error"]
    assert not uploads


def _guard_failure(tmp_path: Path, uploads: dict, job_id: str) -> str:
    """The error of a job that failed through the done file; asserts the failure is clean."""
    done = json.loads((tmp_path / "done" / f"{job_id}.r0.json").read_text())
    assert done["ok"] is False, done
    assert not uploads
    return done["error"]


@pytest.mark.parametrize("value, detail", [
    (float("nan"), "not a finite positive number"),
    (float("inf"), "not a finite positive number"),
    (0.0, "not a finite positive number"),
    (-0.37, "not a finite positive number"),
    ("abc", "is not a number"),       # float() raises ValueError
    (None, "is not a number"),        # float() raises TypeError
    ([0.37], "is not a number"),      # float() raises TypeError
])
def test_mla_scale_guard_rejects_a_scale_that_is_not_a_finite_positive_number(
        monkeypatch, tmp_path: Path, value, detail) -> None:
    """The two branches of the scale check (not a number; not finite or not positive) both
    fail the job through the done file; nothing is uploaded."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layers = [StubMLAAttention(f"model.layers.{i}.self_attn.attn", seed=i) for i in range(2)]
    layers[0].impl.scale = value
    _arm(tmp_path, "sc", 1, 16, [15])
    assert _run_mla_forward(layers, 16, seed=6)
    error = _guard_failure(tmp_path, uploads, "sc")
    assert "MLA guard scale failed" in error and detail in error, error


# Each shape guard of ``_mla_guard`` with the tensors that trip it (and no earlier guard):
# the stub's own math is switched off (``forced_output_numel``) because the tensors do not
# fit the layer, so the plugin sees them as vLLM would hand them over after a mismatch.
# Layer dims: 2 heads, qk_nope 4, qk_rope 2, v 3, lora 5; t = 16 tokens.
_SHAPE_CASES = {
    "q": (dict(q_shape=(16, 2, 7)), "q.shape="),                        # last dim 7, expected 6
    "kv_c-too-few-rows": (dict(kv_c_shape=(15, 5)), "kv_c_normed.shape="),
    "kv_c-wrong-width": (dict(kv_c_shape=(16, 6)), "kv_c_normed.shape="),
    "k_pe-too-few-rows": (dict(k_pe_shape=(15, 1, 2)), "k_pe.shape="),
    "k_pe-wrong-numel": (dict(k_pe_shape=(16, 1, 3)), "k_pe.shape="),
    "output": (dict(output_numel=16 * 2 * 3 + 1), "output.numel()="),
}


@pytest.mark.parametrize("case", sorted(_SHAPE_CASES))
def test_every_mla_shape_guard_fails_the_job_loudly(monkeypatch, tmp_path: Path, case) -> None:
    sizes, detail = _SHAPE_CASES[case]
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t = 16
    layer = StubMLAAttention("model.layers.0.self_attn.attn")
    layer.forced_output_numel = sizes.get("output_numel", t * 2 * 3)
    gen = torch.Generator().manual_seed(3)
    q = torch.randn(*sizes.get("q_shape", (t, 2, 6)), generator=gen).to(torch.bfloat16)
    kv_c = torch.randn(*sizes.get("kv_c_shape", (t, 5)), generator=gen).to(torch.bfloat16)
    k_pe = torch.randn(*sizes.get("k_pe_shape", (t, 1, 2)), generator=gen).to(torch.bfloat16)
    _arm(tmp_path, "sh", 1, t, [15])
    layer.forward(q, kv_c, k_pe, output_shape=(t, 6), q_dcp_replicated=None)
    error = _guard_failure(tmp_path, uploads, "sh")
    assert "MLA guard shape failed" in error and detail in error, error


def test_mla_shape_probe_with_matching_tensors_is_not_refused(monkeypatch, tmp_path: Path) -> None:
    """Control for the shape cases: the same driver with well-formed tensors passes every guard
    (it then fails only at the later gate, as the stub's zero output is not the kernel's)."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t = 16
    layer = StubMLAAttention("model.layers.0.self_attn.attn")
    layer.forced_output_numel = t * 2 * 3
    gen = torch.Generator().manual_seed(3)
    q = torch.randn(t, 2, 6, generator=gen).to(torch.bfloat16)
    kv_c = torch.randn(t, 5, generator=gen).to(torch.bfloat16)
    k_pe = torch.randn(t, 1, 2, generator=gen).to(torch.bfloat16)
    _arm(tmp_path, "ctl", 1, t, [15])
    layer.forward(q, kv_c, k_pe, output_shape=(t, 6), q_dcp_replicated=None)
    done = json.loads((tmp_path / "done" / "ctl.r0.json").read_text())
    assert done["ok"] is False and "MLA guard" not in done["error"], done
    assert "gate failed" in done["error"], done


def test_mla_mass_mode_prompt_entropy_matches_a_direct_computation(monkeypatch, tmp_path: Path) -> None:
    """Mass, entropy and prompt_entropy of an MLA layer go through the shared tail."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    monkeypatch.setattr(plugin, "MASS_CHUNK_ELEMENTS", 2 * 30 * 4)   # several query chunks
    t, query_start = 30, 18
    layers = [StubMLAAttention(f"model.layers.{i}.self_attn.attn", heads=2, seed=i) for i in range(2)]
    classes = [0] * 8 + [1] * 8 + [2] * 2 + [3] * 12
    _mass_job(tmp_path, "mpe", t, query_start, classes, [t - 1, 20])
    tensors = _run_mla_forward(layers, t, seed=8)

    done = json.loads((tmp_path / "done" / "mpe.r0.json").read_text())
    assert done["ok"] is True, done
    npz = np.load(io.BytesIO(uploads["put://mpe/r0.npz"]))
    meta = json.loads(uploads["put://mpe/r0.json"])
    assert meta["capture_version"] == 2 and meta["attention"] == "mla"
    assert npz["prompt_entropy"].shape == (2, t - query_start, 2)
    onehot = torch.zeros(t, 4)
    onehot[torch.arange(t), torch.tensor(classes)] = 1.0
    positions = list(range(query_start, t))
    for li, layer in enumerate(layers):
        _, q, kv_c, k_pe = tensors[layer.layer_name]
        ref_rows = _mla_reference_rows(layer, q, kv_c, k_pe, positions)
        ref_pe = _prompt_entropy_reference(ref_rows, query_start).float()
        got_pe = torch.from_numpy(npz["prompt_entropy"][li].astype(np.float32))
        assert not torch.isnan(ref_pe).any() and not torch.isnan(got_pe).any()
        assert torch.allclose(got_pe, ref_pe, atol=1e-2, rtol=2e-3), layer.layer_name
        got_mass = torch.from_numpy(npz["mass"][li].astype(np.float32))
        assert torch.allclose(got_mass, torch.einsum("phn,nc->phc", ref_rows, onehot), atol=3e-3)
        ref_ent = -(ref_rows * torch.log(ref_rows.clamp_min(1e-30))).sum(-1)
        got_ent = torch.from_numpy(npz["entropy"][li].astype(np.float32))
        assert torch.allclose(got_ent, ref_ent, atol=2e-2)


def test_a_model_mixing_both_layer_classes_finalizes_once_after_all_of_them(monkeypatch, tmp_path: Path) -> None:
    """The plugin counts the union of both classes, so neither class finalizes the job early."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, d = 16, 8
    plain0 = StubAttention("model.layers.0.self_attn.attn", 2, 2, d)
    mla1 = StubMLAAttention("model.layers.1.self_attn.attn", heads=2)
    plain2 = StubAttention("model.layers.2.self_attn.attn", 2, 1, d)
    _arm(tmp_path, "mix", 1, t, [15])
    _run_forward([plain0], t, d, seed=1)
    _run_mla_forward([mla1], t, seed=2)
    assert not uploads                       # two of three layers seen: not finalized yet
    _run_forward([plain2], t, d, seed=3)
    done = json.loads((tmp_path / "done" / "mix.r0.json").read_text())
    assert done["ok"] is True, done
    meta = json.loads(uploads["put://mix/r0.json"])
    assert meta["layers"] == [0, 1, 2]
    assert meta["attention"] == "mixed"


def test_attention_only_model_works_when_vllm_has_no_mla_module(monkeypatch, tmp_path: Path) -> None:
    """An older vLLM without the MLA module: register() still wraps Attention and captures."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path, with_mla=False)
    assert StubMLAAttention.forward is _STUB_MLA_FORWARD      # nothing to wrap, nothing wrapped
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, 8)
    _arm(tmp_path, "nomla", 1, 10, [9])
    _run_forward([layer], 10, 8)
    assert json.loads((tmp_path / "done" / "nomla.r0.json").read_text())["ok"] is True
    assert "put://nomla/r0.npz" in uploads


def test_register_wraps_mla_forward_once(monkeypatch, tmp_path: Path) -> None:
    plugin, _uploads = _load_plugin(monkeypatch, tmp_path)
    first = StubMLAAttention.forward
    assert first is not _STUB_MLA_FORWARD
    plugin.register()
    assert StubMLAAttention.forward is first


def _stub_flashattn_mla(monkeypatch, threshold):
    """Install a stub of vLLM's flash-attention MLA backend module and return its builder class."""
    class FlashAttnMLAMetadataBuilder:
        reorder_batch_threshold = threshold

    for name in ("vllm.v1", "vllm.v1.attention", "vllm.v1.attention.backends", "vllm.v1.attention.backends.mla"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    mod = types.ModuleType("vllm.v1.attention.backends.mla.flashattn_mla")
    mod.FlashAttnMLAMetadataBuilder = FlashAttnMLAMetadataBuilder
    monkeypatch.setitem(sys.modules, mod.__name__, mod)
    return FlashAttnMLAMetadataBuilder


def test_register_lowers_the_mla_decode_threshold_so_short_sequences_prefill(monkeypatch, tmp_path: Path) -> None:
    """vLLM sends sequences of up to 512 tokens down the decode path; the plugin makes that 1."""
    builder = _stub_flashattn_mla(monkeypatch, 512)
    _load_plugin(monkeypatch, tmp_path)
    assert builder.reorder_batch_threshold == 1


def test_register_leaves_a_threshold_of_one_and_tolerates_a_missing_builder(monkeypatch, tmp_path: Path) -> None:
    builder = _stub_flashattn_mla(monkeypatch, 1)
    _load_plugin(monkeypatch, tmp_path)
    assert builder.reorder_batch_threshold == 1
    # No such module (an older vLLM, or another MLA backend): register() still wraps both classes.
    monkeypatch.delitem(sys.modules, "vllm.v1.attention.backends.mla.flashattn_mla")
    _load_plugin(monkeypatch, tmp_path)
    assert StubMLAAttention.forward is not _STUB_MLA_FORWARD


def test_the_decode_threshold_is_untouched_without_mla_layers(monkeypatch, tmp_path: Path) -> None:
    builder = _stub_flashattn_mla(monkeypatch, 512)
    _load_plugin(monkeypatch, tmp_path, with_mla=False)
    assert builder.reorder_batch_threshold == 512


# --------------------------------------------------------------------------- summary mode
from tests.evals.test_attention_analysis import summarize_rows  # noqa: E402

#: Per-(layer, head) arrays of a summary npz (float64 sums and int64 counts).
_SUMMARY_SUMS = ("sum_entropy", "sum_prompt_entropy", "sum_mass", "sum_sink", "sum_pad_ratio",
                 "sum_m_hp", "sum_chain_hi", "sum_chain_lo")
_SUMMARY_COUNTS = ("n_prompt_entropy", "n_pad_ratio")


def _reduced_job(tmp_path, job_id, seq, t, query_start, classes, gate_positions, mode):
    job = _arm(tmp_path, job_id, seq, t, gate_positions)
    job.update({"mode": mode, "query_start": query_start, "classes": classes})
    (tmp_path / "current.json").write_text(json.dumps(job))
    return job


def _capture_both_ways(tmp_path, uploads, run, t, query_start, classes, gate_positions):
    """Run the same forward as a mass job, then as a summary job; return both npz and the meta."""
    _reduced_job(tmp_path, "mass1", 1, t, query_start, classes, gate_positions, "mass")
    run()
    _reduced_job(tmp_path, "sum1", 2, t, query_start, classes, gate_positions, "summary")
    run()
    for job_id in ("mass1", "sum1"):
        done = json.loads((tmp_path / "done" / f"{job_id}.r0.json").read_text())
        assert done["ok"] is True, done
    mass = np.load(io.BytesIO(uploads["put://mass1/r0.npz"]))
    summary = np.load(io.BytesIO(uploads["put://sum1/r0.npz"]))
    return mass, summary, json.loads(uploads["put://sum1/r0.json"])


def _assert_summary_matches_mass(mass, summary, classes, query_start):
    """The summary equals the float64 sums of the same sequence's float16 mass-mode rows.

    Tolerance: the summary is summed from the unrounded float32 rows, the reference from the
    rows rounded to float16 (relative error up to 2**-11 ~ 4.9e-4 each). For the direct sums
    that is rtol 1e-3 on sums of non-negative terms; the derived chain-rule terms (G = -sum p
    ln p over three groups, m * Hp) carry a few such errors scaled by values of order 1-10
    nats, so they get 5e-3 nats per row. Counts are exact.
    """
    p = mass["mass"].shape[1]
    ref = summarize_rows(mass["mass"], mass["entropy"], mass["sink"], mass["prompt_entropy"],
                         classes, query_start)
    assert int(summary["rows"]) == p
    for name in _SUMMARY_COUNTS:
        np.testing.assert_array_equal(summary[name], ref[name], err_msg=name)
    for name in ("sum_entropy", "sum_prompt_entropy", "sum_mass", "sum_sink", "sum_pad_ratio"):
        np.testing.assert_allclose(summary[name], ref[name], rtol=1e-3, atol=1e-4 * p, err_msg=name)
    for name in ("sum_m_hp", "sum_chain_hi", "sum_chain_lo"):
        np.testing.assert_allclose(summary[name], ref[name], rtol=1e-3, atol=5e-3 * p, err_msg=name)


def test_summary_mode_equals_the_float64_sums_of_the_mass_mode_rows(monkeypatch, tmp_path: Path) -> None:
    """Window, sink, soft cap, GQA and KV sharing; several query chunks with an uneven last one."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, d, query_start = 40, 16, 24
    # 8 heads x 40 keys x 5 rows per chunk: P = 16 rows run as chunks of 5, 5, 5 and 1.
    monkeypatch.setattr(plugin, "MASS_CHUNK_ELEMENTS", 8 * 40 * 5)
    sinks = torch.full((8,), 3.0)   # a large sink share keeps H far from the prompt entropy
    layers = [
        StubAttention("model.layers.0.self_attn.attn", 8, 4, d, window=9),
        StubAttention("model.layers.1.self_attn.attn", 8, 8, d, sinks=sinks),
        StubAttention("model.layers.2.self_attn.attn", 8, 4, d, soft_cap=4.0,
                      kv_target="model.layers.0.self_attn.attn", window=9),
        StubAttention("model.layers.3.self_attn.attn", 8, 4, d),
    ]
    classes = [0] * 10 + [1] * 12 + [2] * 2 + [3] * 16
    mass, summary, meta = _capture_both_ways(
        tmp_path, uploads, lambda: _run_forward(layers, t, d, seed=3), t, query_start, classes, [t - 1, 30])
    _assert_summary_matches_mass(mass, summary, classes, query_start)
    # Window 9: rows i < 8 see a prompt key, the global layers all 16 rows.
    assert summary["n_prompt_entropy"][:, 0].tolist() == [8, 16, 8, 16]
    assert (summary["n_pad_ratio"] == 16).all()
    # The prompt entropy is not the whole-row entropy (the sink takes a real share).
    assert float(np.abs(summary["sum_entropy"] - summary["sum_prompt_entropy"]).max()) > 1.0


def test_summary_mode_equals_the_sums_for_latent_attention_layers(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, query_start = 30, 18
    monkeypatch.setattr(plugin, "MASS_CHUNK_ELEMENTS", 2 * 30 * 5)   # chunks of 5, 5 and 2 rows
    layers = [StubMLAAttention(f"model.layers.{i}.self_attn.attn", heads=2, seed=i) for i in range(2)]
    classes = [0] * 8 + [1] * 8 + [2] * 2 + [3] * 12
    mass, summary, meta = _capture_both_ways(
        tmp_path, uploads, lambda: _run_mla_forward(layers, t, seed=8), t, query_start, classes, [t - 1, 20])
    _assert_summary_matches_mass(mass, summary, classes, query_start)
    assert meta["attention"] == "mla" and (summary["n_prompt_entropy"] == 12).all()


def test_summary_npz_holds_sums_not_rows_and_the_meta_names_the_mode(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, d, query_start = 20, 8, 12
    layers = [StubAttention("model.layers.0.self_attn.attn", 4, 2, d),
              StubAttention("model.layers.1.self_attn.attn", 4, 2, d, window=5)]
    classes = [0] * 12 + [3] * 8
    _reduced_job(tmp_path, "s", 1, t, query_start, classes, [t - 1], "summary")
    _run_forward(layers, t, d, seed=1)
    done = json.loads((tmp_path / "done" / "s.r0.json").read_text())
    assert done["ok"] is True and done["gate_max_rel"] < 3e-2, done
    npz = np.load(io.BytesIO(uploads["put://s/r0.npz"]))
    meta = json.loads(uploads["put://s/r0.json"])
    assert meta["mode"] == "summary" and meta["capture_version"] == 3
    assert meta["rows_shape"] == [2, t - query_start, 4, 4] and meta["query_start"] == query_start
    assert meta["n_classes"] == 4 and meta["bytes"] == len(uploads["put://s/r0.npz"])
    assert not {"mass", "entropy", "prompt_entropy", "sink"} & set(npz.files)
    assert int(npz["rows"]) == t - query_start and npz["rows"].shape == ()
    assert int(npz["capture_version"]) == 3
    for name in _SUMMARY_SUMS:
        assert npz[name].dtype == np.float64, name
        assert npz[name].shape == ((2, 4, 4) if name == "sum_mass" else (2, 4)), name
    for name in _SUMMARY_COUNTS:
        assert np.issubdtype(npz[name].dtype, np.integer) and npz[name].shape == (2, 4), name
    for name in ("classes", "query_start", "layers", "positions", "has_sink", "sliding_window",
                 "kv_shared_from"):
        assert name in npz.files, name
    assert list(npz["sliding_window"]) == [0, 5] and list(npz["classes"]) == classes
    # Every array the client's verification and the audit expect is present.
    from smolbench.evals import attention as client
    assert set(client.SUMMARY_ARRAYS) <= set(npz.files)


def test_summary_without_a_prompt_has_zero_counts_and_zero_sums(monkeypatch, tmp_path: Path) -> None:
    """query_start == 0: prompt entropy is undefined on every row, so it adds 0, never NaN."""
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, d = 12, 8
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, d)
    _reduced_job(tmp_path, "z", 1, t, 0, [3] * t, [t - 1], "summary")
    _run_forward([layer], t, d, seed=2)
    npz = np.load(io.BytesIO(uploads["put://z/r0.npz"]))
    assert int(npz["rows"]) == t
    for name in ("n_prompt_entropy", "n_pad_ratio", "sum_prompt_entropy", "sum_pad_ratio", "sum_m_hp",
                 "sum_chain_hi", "sum_chain_lo"):
        assert (npz[name] == 0).all(), name
    assert np.isfinite(npz["sum_entropy"]).all() and (npz["sum_entropy"] > 0).all()


def test_summary_mode_still_runs_the_gate(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    t, d = 24, 16
    good = StubAttention("model.layers.0.self_attn.attn", 4, 4, d)
    liar = StubAttention("model.layers.1.self_attn.attn", 4, 4, d)
    liar.ref_scale, liar.impl.scale = 4.0, 0.01
    _reduced_job(tmp_path, "badsum", 3, t, 10, [0] * 10 + [3] * 14, [t - 1], "summary")
    _run_forward([good, liar], t, d)
    done = json.loads((tmp_path / "done" / "badsum.r0.json").read_text())
    assert done["ok"] is False and "gate failed" in done["error"] and not uploads


def test_summary_mode_rejects_malformed_class_vectors(monkeypatch, tmp_path: Path) -> None:
    plugin, uploads = _load_plugin(monkeypatch, tmp_path)
    layer = StubAttention("model.layers.0.self_attn.attn", 4, 4, 8)
    _reduced_job(tmp_path, "bad", 2, 10, 5, [0] * 9, [9], "summary")   # one class short
    _run_forward([layer], 10, 8)
    assert not uploads and not (tmp_path / "done").exists()
