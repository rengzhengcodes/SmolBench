"""Turn the fetched configs into the per-model spec the atlas page draws.

``fetch_arch_facts.py`` produces faithful-but-shapeless config records. This
script turns them into the two things a block diagram needs:

**A per-layer track pair.** Every checkpoint's stack is expanded into one entry
per layer holding ``{"mix": ..., "ffn": ...}`` -- what mixes tokens in that
layer, and what its feed-forward is. The distinction matters because the
families disagree about what a "layer" is:

- ``layer_types`` families (Qwen3.5, Gemma-4, EXAONE, and by convention the
  families with no per-layer array at all) treat a layer as *mixer then FFN*, so
  both slots are filled on every layer.
- ``hybrid_override_pattern`` families (Nemotron-H) treat a layer as *mixer OR
  FFN*, so exactly one slot is filled and the other is ``None``. Drawing this as
  two tracks with gaps is the honest rendering: it shows at a glance that
  Nemotron interleaves its Mamba-2 mixers and MLPs rather than stacking them.

**A repeating motif.** The shortest layer pattern that tiles the stack, which is
what the schematic actually draws with an ``x N`` multiplier instead of 92
individual layers.

Annotations
-----------
Config fields cannot say *what a mechanism is called* or when a checkpoint was
released. Those come from ``annotations.json`` (hand-written from the family
research briefs in ``scripts/arch/research/``) and are merged in here, keyed by
spec key. Merging happens in this one place so the page never mixes a measured
field and a written claim without the reader being able to tell which is which:
every annotation value carries its own provenance in the page.

Usage
-----
``.venv/bin/python scripts/arch/build_page_data.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))

from smolbench.evals.ec2 import EC2_DEPLOY_SPECS  # noqa: E402
_FACTS_PATH = _HERE / "arch_facts.json"
#: Page-level copy (masthead, legend, method) -- written by hand.
_ANNOTATIONS_PATH = _HERE / "annotations.json"
#: Per-model copy, synthesised from the family research briefs. Kept in its own
#: file so regenerating the model prose can never clobber the page's own voice.
_MODEL_ANNOTATIONS_PATH = _HERE / "annotations_models.json"
_OUT_PATH = _HERE / "page_data.json"

#: Family -> (display name, vendor, ordered spec keys smallest-to-largest).
#: Order is the ladder order the page reads in, NOT alphabetical.
FAMILIES: List[Dict[str, Any]] = [
    {"id": "qwen3.5", "name": "Qwen3.5", "vendor": "Alibaba",
     "rungs": ["qwen3.5-27b", "qwen3.5-122b-a10b", "qwen3.5-397b-a17b"]},
    {"id": "nemotron-3", "name": "Nemotron-3", "vendor": "NVIDIA",
     "rungs": ["nemotron-3-nano-4b", "nemotron-3-nano-30b-a3b", "nemotron-3-super-120b-a12b"]},
    {"id": "gemma-4", "name": "Gemma 4", "vendor": "Google",
     "rungs": ["gemma-4-e2b", "gemma-4-12b", "gemma-4-31b"]},
    {"id": "glm", "name": "GLM-4.x", "vendor": "Z.ai (Zhipu)",
     "rungs": ["glm-4.7-flash", "glm-4.5-air", "glm-4.7"]},
    {"id": "ministral-3", "name": "Ministral-3", "vendor": "Mistral AI",
     "rungs": ["ministral-3-3b", "ministral-3-8b", "ministral-3-14b"]},
    {"id": "exaone", "name": "EXAONE", "vendor": "LG AI Research",
     "rungs": ["exaone-4.0-32b", "exaone-4.5-33b", "k-exaone-236b-a23b"]},
    {"id": "deepseek", "name": "DeepSeek", "vendor": "DeepSeek",
     "rungs": ["deepseek-v4-flash", "deepseek-v3.1", "deepseek-v4-pro"]},
]

#: Nemotron-H's ``hybrid_override_pattern`` alphabet. Each character is one
#: layer that is EITHER a token mixer OR a feed-forward, never both.
_NEMOTRON_ALPHABET = {
    "M": {"mix": "ssm", "ffn": None},
    "*": {"mix": "full", "ffn": None},
    "-": {"mix": None, "ffn": "dense"},
    "E": {"mix": None, "ffn": "moe"},
}

#: ``layer_types`` values -> mixer kind used by the page's colour system.
_MIXER_KIND = {
    "full_attention": "full",
    "sliding_attention": "sliding",
    "linear_attention": "linear",
}


def _get(model: Dict[str, Any], group: str, key: str, default: Any = None) -> Any:
    return model.get("derived", {}).get(group, {}).get(key, default)


def _is_moe(model: Dict[str, Any]) -> bool:
    """True when the checkpoint routes tokens to experts.

    Deliberately checks for a *positive* expert count rather than the presence
    of the key: Gemma-4 ships ``num_experts: null`` alongside
    ``enable_moe_block: false``, i.e. an MoE code path the checkpoint does not
    use, and a key-presence test would mislabel all three Gemma rungs.
    """
    moe = model.get("derived", {}).get("moe", {})
    for key in ("n_routed_experts", "num_experts", "num_local_experts"):
        if isinstance(moe.get(key), int) and moe[key] > 0:
            return True
    return False


def _sliding_windows(model: Dict[str, Any], n_layers: int) -> List[Optional[int]]:
    """Per-layer attention window, ``None`` where the layer attends globally.

    Two encodings exist. K-EXAONE ships an explicit ``sliding_windows`` array
    with ``0`` marking the global layers; everyone else declares one scalar
    ``sliding_window`` that applies to whichever layers ``layer_types`` marks
    sliding. The explicit array wins when present.
    """
    explicit = model.get("derived", {}).get("unclassified", {}).get("sliding_windows")
    if isinstance(explicit, list) and len(explicit) == n_layers:
        return [w if isinstance(w, int) and w > 0 else None for w in explicit]
    scalar = _get(model, "attention", "sliding_window")
    return [scalar if isinstance(scalar, int) and scalar > 0 else None] * n_layers


def _ffn_kinds(model: Dict[str, Any], n_layers: int) -> List[str]:
    """Per-layer feed-forward kind for a mixer-then-FFN family.

    Three encodings, most-explicit first: an ``mlp_layer_types`` array
    (K-EXAONE), a ``first_k_dense_replace`` dense prefix (DeepSeek, GLM,
    Nemotron-style MoE configs), or a uniform kind.
    """
    explicit = model.get("derived", {}).get("unclassified", {}).get("mlp_layer_types")
    if isinstance(explicit, list) and len(explicit) == n_layers:
        return ["moe" if kind == "sparse" else "dense" for kind in explicit]
    if not _is_moe(model):
        return ["dense"] * n_layers
    dense_prefix = _get(model, "moe", "first_k_dense_replace", 0) or 0
    return ["dense" if i < dense_prefix else "moe" for i in range(n_layers)]


def _layer(mix: Optional[str] = None, ffn: Optional[str] = None,
           window: Optional[int] = None, variant: Optional[str] = None,
           ffnVariant: Optional[str] = None) -> Dict[str, Any]:
    """One layer record, with every key always present.

    Uniform keys matter: run-length encoding and motif detection compare these
    dicts for equality, so a record that omits a key would never compare equal
    to one that carries it as ``None``.
    """
    return {"mix": mix, "ffn": ffn, "window": window,
            "variant": variant, "ffnVariant": ffnVariant}


#: DeepSeek-V4's per-layer ``compress_ratios`` alphabet. The array is one entry
#: longer than the layer count -- the tail entry belongs to the MTP module --
#: and its value is the compression ratio the layer's attention runs at.
_DSV4_COMPRESS = {
    0: {"mix": "sliding", "variant": "local", "window": 128},
    4: {"mix": "full", "variant": "csa", "window": None},
    128: {"mix": "full", "variant": "hca", "window": None},
}


def _deepseek_v4_tracks(model: Dict[str, Any], n_layers: int) -> List[Dict[str, Any]]:
    """Per-layer records for DeepSeek-V4, whose layer types live in a ratio array.

    V4 declares no ``layer_types``; its attention schedule is
    ``compress_ratios``, which alternates a 4:1 compressed-sparse layer with a
    128:1 compressed layer, after a short prefix. Reading only the scalar
    ``sliding_window: 128`` -- the uncompressed local window every layer also
    keeps -- would flatten the whole stack into "windowed attention" and lose
    the alternation entirely.

    Routing also differs at the bottom of the stack: ``num_hash_layers`` layers
    route through a frozen token-id-to-expert table rather than a learned
    router, which is V4's replacement for V3's dense prefix.
    """
    unclassified = model.get("derived", {}).get("unclassified", {})
    ratios = unclassified.get("compress_ratios") or []
    hash_layers = unclassified.get("num_hash_layers") or 0
    out: List[Dict[str, Any]] = []
    for i in range(n_layers):
        ratio = ratios[i] if i < len(ratios) else None
        spec = _DSV4_COMPRESS.get(ratio, {"mix": "full", "variant": None, "window": None})
        out.append(_layer(
            mix=spec["mix"], ffn="moe", window=spec["window"],
            variant=spec["variant"],
            ffnVariant="hash" if i < hash_layers else None,
        ))
    return out


def _tracks(model: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Expand a checkpoint into one ``{mix, ffn, window}`` record per layer."""
    layers = model.get("layers", {})
    n_layers = _get(model, "shape", "num_hidden_layers") or layers.get("length") or 0
    sequence = layers.get("sequence")

    if _get(model, "shape", "model_type") == "deepseek_v4":
        return _deepseek_v4_tracks(model, n_layers)

    if layers.get("source") == "hybrid_override_pattern":
        return [
            _layer(**_NEMOTRON_ALPHABET.get(ch, {"mix": None, "ffn": None}))
            for ch in sequence
        ]

    windows = _sliding_windows(model, n_layers)
    ffns = _ffn_kinds(model, n_layers)
    if layers.get("source") == "layer_types":
        mixers = [_MIXER_KIND.get(t, "full") for t in sequence]
    else:
        # No per-layer array: every layer attends globally (GLM, DeepSeek,
        # Ministral). A declared scalar sliding_window still applies -- DeepSeek
        # V4 declares 128 with no layer_types at all.
        scalar = _get(model, "attention", "sliding_window")
        kind = "sliding" if isinstance(scalar, int) and scalar > 0 else "full"
        mixers = [kind] * n_layers

    return [
        _layer(mix=mixers[i], ffn=ffns[i],
               window=windows[i] if mixers[i] == "sliding" else None)
        for i in range(n_layers)
    ]


def _motif(tracks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Shortest exact tiling of the track list, or ``None`` when it does not tile."""
    n = len(tracks)
    if not n:
        return None
    for period in range(1, n // 2 + 1):
        if n % period:
            continue
        head = tracks[:period]
        if all(tracks[i] == head[i % period] for i in range(n)):
            return {"pattern": head, "repeats": n // period}
    return None


def _rle(tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse consecutive identical layers into ``{count, ...layer}`` runs."""
    runs: List[Dict[str, Any]] = []
    for layer in tracks:
        if runs and {k: v for k, v in runs[-1].items() if k != "count"} == layer:
            runs[-1]["count"] += 1
        else:
            runs.append({**layer, "count": 1})
    return runs


def _fold_inner_repeat(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse a repeated tail of a segment into one nested group.

    Nemotron-H's group between two attention layers is five alternating
    Mamba-2 and MoE layers, which run-length encoding cannot compress at all --
    no two *adjacent* layers are alike. Drawn literally that is eleven stacked
    blocks saying one thing. Folding the repeat turns it into "one attention
    layer, then (Mamba-2 -> MoE) x 5", which is both a fifth of the height and
    a truer statement of the structure.

    Returns the list unchanged when no tail repeats at least twice.
    """
    n = len(runs)
    for period in range(1, n // 2 + 1):
        for start in range(0, n - 2 * period + 1):
            tail = runs[start:]
            if len(tail) % period:
                continue
            block = tail[:period]
            repeats = len(tail) // period
            if repeats < 2:
                continue
            if all(tail[i] == block[i % period] for i in range(len(tail))):
                return runs[:start] + [{"group": block, "repeat": repeats}]
    return runs


def _schematic(tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compress a stack into the few blocks a schematic can actually draw.

    A block diagram draws a repeating unit and a multiplier, never 92 boxes.
    Three cases, in order of how faithfully they compress:

    1. The stack tiles (Qwen3.5, Gemma-4, EXAONE-4.x, Ministral) -- draw the
       motif once with its repeat count. ``exact`` is true.
    2. The stack tiles *after* a short prefix (K-EXAONE: one dense layer, then
       a clean 3-sliding + 1-global body) -- draw the prefix, then the motif.
       Peeling matters: without it K-EXAONE's regular body reads as irregular.
    3. The stack does not tile but has few distinct runs (GLM, DeepSeek V3.1:
       a dense prefix then a uniform MoE body) -- draw the runs in order.
    4. None of the above (Nemotron-H, whose Mamba/MLP groups vary in length
       between attention layers) -- split the stack *before* each occurrence of
       its rarest mixer, draw the most common group, and record every group
       length so the page can say out loud that the drawing is a dominant
       pattern rather than a tiling. ``exact`` is false.
    """
    if not tracks:
        return {"segments": [], "exact": True}

    motif = _motif(tracks)
    if motif and len(motif["pattern"]) <= 8:
        return {
            "segments": [{"repeat": motif["repeats"],
                          "layers": _fold_inner_repeat(_rle(motif["pattern"]))}],
            "exact": True,
        }

    for prefix_len in range(1, min(8, len(tracks) // 2) + 1):
        body_motif = _motif(tracks[prefix_len:])
        if body_motif and len(body_motif["pattern"]) <= 8:
            return {
                "segments": [
                    {"repeat": 1, "layers": _rle(tracks[:prefix_len])},
                    {"repeat": body_motif["repeats"],
                     "layers": _fold_inner_repeat(_rle(body_motif["pattern"]))},
                ],
                "exact": True,
            }

    runs = _rle(tracks)
    if len(runs) <= 10:
        return {"segments": [{"repeat": 1, "layers": _fold_inner_repeat(runs)}],
                "exact": True}

    # Quasi-periodic. Split BEFORE the rarest mixer so each group opens with
    # that layer -- "one attention layer, then N Mamba/MoE pairs" is how the
    # Nemotron stack actually reads, and grouping the other way round buries
    # the attention layer at the end of the block.
    counts: Dict[Any, int] = {}
    for layer in tracks:
        counts[layer["mix"]] = counts.get(layer["mix"], 0) + 1
    rare = min(counts, key=lambda k: counts[k])

    groups: List[List[Dict[str, Any]]] = [[]]
    for layer in tracks:
        if layer["mix"] == rare and groups[-1]:
            groups.append([])
        groups[-1].append(layer)

    prefix = groups.pop(0) if groups and groups[0][0]["mix"] != rare else []
    signatures = [json.dumps(g, sort_keys=True) for g in groups]
    modal = max(set(signatures), key=signatures.count)

    segments = []
    if prefix:
        segments.append({"repeat": 1, "layers": _fold_inner_repeat(_rle(prefix))})
    segments.append({
        "repeat": len(groups),
        "layers": _fold_inner_repeat(_rle(json.loads(modal))),
        "varies": [len(g) for g in groups],
    })
    return {"segments": segments, "exact": False}


def _rotary_fraction(model: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Fraction of each attention head's dimensions that RoPE actually rotates.

    The roster's most striking shared trait is that hardly any of it rotates a
    whole head any more, and the config states the fraction three different
    ways, so it is normalised here rather than left to prose:

    - **MLA** splits the head explicitly -- only ``qk_rope_head_dim`` of
      ``qk_nope_head_dim + qk_rope_head_dim`` is rotated (DeepSeek-V3.1: 64 of
      192; GLM-4.7-Flash: 64 of 256).
    - **``partial_rotary_factor``** states it directly (GLM's 0.5, Qwen3.5's
      0.25), either at the top level or inside a per-layer-type
      ``rope_parameters`` block (Gemma-4 rotates 25% of its *global* layers and
      100% of its sliding ones).
    - **Absence of any RoPE field** means the layer is NoPE.

    Returned per mixer kind, because two families treat their layer types
    differently. Values here are config-derived only; where a config declares a
    RoPE field that the reference implementation never reads -- Nemotron-3's
    inert ``rope_theta`` is the case in this roster -- the model's annotation
    overrides this with the implementation's real behaviour.
    """
    pos = model.get("derived", {}).get("positional", {})
    mla = model.get("derived", {}).get("mla", {})
    kinds = {t for t in ("full", "sliding", "linear", "ssm")}
    out: Dict[str, Optional[float]] = {}

    def scalar_fraction(params: Dict[str, Any]) -> Optional[float]:
        if not isinstance(params, dict):
            return None
        if params.get("partial_rotary_factor") is not None:
            return float(params["partial_rotary_factor"])
        if params.get("rope_theta") or params.get("rope_type"):
            return 1.0
        return None

    per_type = pos.get("rope_parameters")
    if isinstance(per_type, dict) and any(
        isinstance(v, dict) for v in per_type.values()
    ):
        for layer_type, params in per_type.items():
            kind = _MIXER_KIND.get(layer_type)
            if kind:
                out[kind] = scalar_fraction(params)
        return out

    if mla.get("qk_rope_head_dim"):
        rope = mla["qk_rope_head_dim"]
        nope = mla.get("qk_nope_head_dim") or 0
        total = rope + nope if nope else (_get(model, "attention", "head_dim") or rope)
        base = round(rope / total, 4) if total else None
    elif pos.get("partial_rotary_factor") is not None:
        base = float(pos["partial_rotary_factor"])
    elif isinstance(per_type, dict):
        base = scalar_fraction(per_type)
    elif pos.get("rope_theta") or scalar_fraction(pos.get("rope_scaling")):
        # EXAONE-4.5 nests ``rope_theta`` inside ``rope_scaling`` where its
        # 4.0 sibling declares it at the top level; reading only the top level
        # would report that checkpoint as having no rotary at all.
        base = 1.0
    else:
        base = 0.0

    for kind in kinds:
        out[kind] = base
    # Recurrent mixers hold no per-head rotary geometry at all; position is
    # implicit in the recurrence.
    for kind in ("linear", "ssm"):
        out[kind] = 0.0
    return out


def _head_dim(model: Dict[str, Any]) -> Optional[int]:
    """Attention head dimension, falling back to the implied one.

    ``head_dim`` is optional in a HF config: when it is absent the loader
    derives ``hidden_size // num_attention_heads``. EXAONE-4.5 omits it (and
    the derived 128 matches EXAONE-4.0's explicit value), so reading only the
    literal field would silently blank that rung's head dimension and KV figure.
    MLA checkpoints are excluded -- their per-head geometry is the split
    ``qk_nope_head_dim``/``qk_rope_head_dim`` pair, and the implied division
    produces a meaningless number (56 on DeepSeek-V3.1).
    """
    explicit = _get(model, "attention", "head_dim")
    if explicit:
        return explicit
    if model.get("derived", {}).get("mla"):
        return None
    heads = _get(model, "attention", "num_attention_heads")
    hidden = _get(model, "shape", "hidden_size")
    if heads and hidden and hidden % heads == 0:
        return hidden // heads
    return None


def _kv_bytes_per_token(model: Dict[str, Any]) -> Optional[int]:
    """Rough KV-cache bytes per token at BF16, for the fact strip.

    Counts only the layers that keep a KV cache (SSM and gated-linear layers
    keep a fixed-size state instead, which does not grow with sequence length --
    that asymmetry is the whole point of the hybrid designs, so folding them in
    would erase it). MLA checkpoints cache the compressed latent plus the
    decoupled RoPE slice rather than full K and V. Returns ``None`` when the
    config does not carry enough to compute it honestly.
    """
    tracks = _tracks(model)
    attn_layers = sum(1 for t in tracks if t["mix"] in ("full", "sliding"))
    if not attn_layers:
        return None
    mla = model.get("derived", {}).get("mla", {})
    if mla.get("kv_lora_rank"):
        per_layer = mla["kv_lora_rank"] + (mla.get("qk_rope_head_dim") or 0)
        return 2 * per_layer * attn_layers
    kv_heads = _get(model, "attention", "num_key_value_heads")
    head_dim = _head_dim(model)
    if not kv_heads or not head_dim:
        return None
    shared = _get(model, "attention", "num_kv_shared_layers", 0) or 0
    return 2 * 2 * kv_heads * head_dim * max(attn_layers - shared, 1)


def build() -> Dict[str, Any]:
    facts = json.loads(_FACTS_PATH.read_text())
    annotations = (
        json.loads(_ANNOTATIONS_PATH.read_text()) if _ANNOTATIONS_PATH.exists() else {}
    )
    if _MODEL_ANNOTATIONS_PATH.exists():
        model_notes = json.loads(_MODEL_ANNOTATIONS_PATH.read_text())
        families = model_notes.pop("_families", {})
        annotations = {**annotations, **model_notes}
        annotations.setdefault("_intro", {}).setdefault("families", {}).update(families)
    models: Dict[str, Any] = {}

    for family in FAMILIES:
        for rung_index, key in enumerate(family["rungs"]):
            model = facts["models"][key]
            tracks = _tracks(model)
            attn = model.get("derived", {}).get("attention", {})
            shape = model.get("derived", {}).get("shape", {})
            moe = model.get("derived", {}).get("moe", {})
            mla = model.get("derived", {}).get("mla", {})

            models[key] = {
                "key": key,
                "family": family["id"],
                "familyName": family["name"],
                "vendor": family["vendor"],
                "rung": ["small", "middle", "large"][rung_index],
                "repo": model["repo"],
                "revision": model["revision"],
                "architecture": model["architecture"],
                "modelType": shape.get("model_type"),
                "towers": model.get("wrapper_towers", []),
                # Read live rather than from the fetch snapshot: the serving
                # config changes on its own schedule (the DeepSeek-V4 lanes
                # were re-pinned to an SM90 path hours after the configs were
                # fetched), and a page that reports a stale serve is worse than
                # one that reports none.
                "served": {
                    "tp": EC2_DEPLOY_SPECS[key].get("tp"),
                    "max_model_len": EC2_DEPLOY_SPECS[key].get("max_model_len"),
                    "vllm_args": EC2_DEPLOY_SPECS[key].get("vllm_args", []),
                },
                "layers": len(tracks),
                "tracks": tracks,
                "motif": _motif(tracks),
                "schematic": _schematic(tracks),
                "counts": {
                    "full": sum(1 for t in tracks if t["mix"] == "full"),
                    "sliding": sum(1 for t in tracks if t["mix"] == "sliding"),
                    "linear": sum(1 for t in tracks if t["mix"] == "linear"),
                    "ssm": sum(1 for t in tracks if t["mix"] == "ssm"),
                    "dense": sum(1 for t in tracks if t["ffn"] == "dense"),
                    "moe": sum(1 for t in tracks if t["ffn"] == "moe"),
                },
                "shape": shape,
                "attention": {**attn, "head_dim_effective": _head_dim(model)},
                "mla": mla,
                "moe": moe,
                "ssm": model.get("derived", {}).get("ssm", {}),
                "positional": model.get("derived", {}).get("positional", {}),
                # Config-derived; a model annotation overrides it wherever the
                # reference implementation ignores a declared RoPE field
                # (Nemotron-3's inert rope_theta, EXAONE's NoPE global layers).
                "rotaryByMixer": {**_rotary_fraction(model),
                                  **(annotations.get(key, {}).get("rotaryByMixer") or {})},
                "quantization": model.get("derived", {}).get("quantization"),
                "unclassified": model.get("derived", {}).get("unclassified", {}),
                "kvBytesPerToken": _kv_bytes_per_token(model),
                "isMoE": _is_moe(model),
                "note": annotations.get(key, {}),
            }

    return {
        "fetchedAt": facts["fetched_at"],
        "families": FAMILIES,
        "models": models,
        "legend": annotations.get("_legend", {}),
        "intro": annotations.get("_intro", {}),
    }


def main() -> int:
    data = build()
    _OUT_PATH.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    n_annotated = sum(1 for m in data["models"].values() if m["note"])
    print(f"wrote {_OUT_PATH.name}: {len(data['models'])} models, "
          f"{n_annotated} annotated")
    for key, model in data["models"].items():
        motif = model["motif"]
        motif_text = (
            f"motif {len(motif['pattern'])}x{motif['repeats']}" if motif else "no tiling"
        )
        print(f"  {key:<28} {model['layers']:>3} layers  {motif_text:<16} "
              f"mix={model['counts']['full']}F/{model['counts']['sliding']}W/"
              f"{model['counts']['linear']}L/{model['counts']['ssm']}S  "
              f"ffn={model['counts']['dense']}D/{model['counts']['moe']}E")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
