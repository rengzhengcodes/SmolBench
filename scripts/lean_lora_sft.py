"""QLoRA fine-tune one trio base model on the decontaminated Lean 4 SFT set.

Phase 2 of notebooks/lean's fine-tune plan. Trains a LoRA adapter on the
JSONL produced by ``scripts/build_lean_sft.py`` (chat triples whose targets
are the ground-truth Lean 4 tactic tails, with every eval theorem held out),
then saves / optionally pushes the adapter for serving through the EC2 vLLM
provider (``--enable-lora`` or a merged repo -- see smolbench/evals/ec2.py).

This is the ONLY training code in the repo and it is **greenfield**: it runs
on a dedicated GPU box, NOT the eval venvs, and its dependencies live in
``scripts/requirements-train.txt`` (kept out of uv.lock on purpose). The heavy
imports are deferred into `main` so this file stays syntactically importable
anywhere; running it without the training stack prints an actionable install
hint instead of an ImportError traceback.

Scale notes (per the plan): QLoRA 4-bit fits all three bases on one 8-GPU
H200/H100 box -- Llama-3.1-405B (~200 GB 4-bit), Nemotron-Ultra-253B (~130 GB),
Qwen3-235B-A22B (~120 GB). ``--target-modules all-linear`` is the robust
default across the three heterogeneous architectures; validate it on a tiny
run for Nemotron-Ultra first (its NAS/irregular per-layer widths are the
highest PEFT risk of the three).

Example
-------
    python scripts/lean_lora_sft.py \
        --base-model Qwen/Qwen3-235B-A22B \
        --dataset notebooks/lean/data/sft/novel_premises_train_stepk1.jsonl \
        --output-dir out/qwen3-235b-lean-lora \
        --push-to-hub <org>/qwen3-235b-a22b-lean-lora --private
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Reduce CUDA fragmentation on the big pipeline-parallel loads (set before torch
# initializes CUDA). Helps reclaim "reserved but unallocated" memory near the edge.
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_INSTALL_HINT = (
    "the training stack is not installed in this interpreter.\n"
    "Training runs on a dedicated GPU env, separate from the eval venvs:\n"
    "  python -m venv .venv-train && . .venv-train/bin/activate\n"
    "  pip install -r scripts/requirements-train.txt && pip install -e .\n"
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-model", required=True, help="HF repo of the base model to LoRA-tune")
    p.add_argument("--dataset", type=Path, required=True, help="SFT JSONL from scripts/build_lean_sft.py")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--push-to-hub", default=None, help="HF repo id to push the trained adapter to")
    p.add_argument("--private", action="store_true", help="push as a private repo")
    # LoRA hyperparameters
    p.add_argument(
        "--init-adapter",
        default=None,
        help="path or HF repo of a previously trained LoRA adapter to CONTINUE training "
             "(staged SFT: stage-1 pretrains on the synthetic set, stage-2 anneals on the "
             "real set with this flag). The adapter's own saved config wins: --lora-r/"
             "--lora-alpha/--lora-dropout/--target-modules are ignored when set",
    )
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    # 0, not 0.05: Qwen3-MoE stores experts as fused nn.Parameters, so LoRA wraps
    # them with peft's ParamWrapper, which requires lora_dropout == 0. Negligible
    # regularization impact on short capped runs; keeps one config across the trio.
    p.add_argument("--lora-dropout", type=float, default=0.0)
    p.add_argument(
        "--target-modules",
        # Explicit Llama/Qwen attention + MLP projection names. peft 0.19.1's
        # "all-linear" shorthand does not expand under trl's get_peft_model path
        # (it gets iterated as characters -> "Target modules {'a','l',...}"), so
        # target the standard projections directly. Qwen3-MoE experts also use
        # gate/up/down_proj. Pass a different comma list for other architectures
        # (e.g. verify Nemotron-Ultra's NAS module names before its run).
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
        help="comma-separated LoRA target module names, or 'all-linear' (peft shorthand; may not expand under trl)",
    )
    # Training hyperparameters
    p.add_argument("--load-in-4bit", action="store_true", default=True, help="QLoRA 4-bit base (default on)")
    p.add_argument("--no-4bit", dest="load_in_4bit", action="store_false")
    p.add_argument(
        "--moe-unquantized",
        action="store_true",
        help="base is a MoE whose fused-Parameter experts bnb does NOT 4-bit-quantize (e.g. Qwen3-235B); "
             "size the device map at bf16 so the ~bf16 footprint spreads correctly across GPUs",
    )
    p.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="execute the repo's custom modeling code (needed for Nemotron-Ultra's NAS arch); leave OFF "
             "for standard Llama/Qwen architectures so NO third-party code runs (only weights are loaded)",
    )
    p.add_argument("--bf16", action="store_true", default=True, help="bf16 training (default on; needs a bf16-capable GPU)")
    p.add_argument("--no-bf16", dest="bf16", action="store_false", help="disable bf16 (CPU smoke / fp16-only GPU)")
    p.add_argument(
        "--assistant-only-loss",
        action="store_true",
        default=True,
        help="mask prompt tokens from the loss (needs a training-compatible chat template)",
    )
    p.add_argument(
        "--no-assistant-only-loss",
        dest="assistant_only_loss",
        action="store_false",
        help="train on the full sequence (auto-used as fallback when the template lacks generation markers)",
    )
    p.add_argument("--epochs", type=float, default=1.0)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument(
        "--lr-scheduler-type",
        default=None,
        help="TrainingArguments lr_scheduler_type (e.g. 'cosine', 'linear'); the CoT recipe "
             "uses cosine. Default None = leave trl's own scheduler default in place.",
    )
    p.add_argument(
        "--warmup-ratio",
        type=float,
        default=None,
        help="TrainingArguments warmup_ratio -- fraction of total steps spent warming up the "
             "LR (e.g. 0.03). Default None = leave trl's own default (0.0) in place.",
    )
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=16)
    p.add_argument("--max-seq-len", type=int, default=4096)
    p.add_argument("--seed", type=int, default=1776, help="seeds RNG, data sampler, and adapter init (reproducibility)")
    p.add_argument(
        "--full-determinism",
        action="store_true",
        help="enable transformers full_determinism (bitwise-reproducible but slower; may error on GPU ops lacking a deterministic kernel)",
    )
    # First-run cost caps. The full novel_premises/train pool is ~55.9k examples;
    # with device_map="auto" (naive pipeline-MP, one GPU hot at a time) a 405B
    # epoch is 10-40h. Cap a de-risking run with --max-steps and/or --max-examples,
    # confirm the base-vs-LoRA signal at the pilot gate, THEN scale to the full set.
    p.add_argument("--max-steps", type=int, default=-1, help="cap optimizer steps (-1 = full --epochs); small = cheap first run")
    p.add_argument("--max-examples", type=int, default=0, help="subsample dataset to N seeded rows (0 = all)")
    p.add_argument(
        "--resume-from-checkpoint",
        default=None,
        help="resume an interrupted run: a checkpoint-* dir path, or 'auto' to resume the latest "
             "checkpoint in --output-dir (spot-interruption recovery). Requires the checkpoint to "
             "match this run's config (same dataset cap / max_steps).",
    )
    # Durability against spot interruption (the box terminates on interruption and
    # its local output_dir dies with it): checkpoint every --save-steps AND push the
    # adapter to the Hub as each checkpoint is written, so the SFT'd checkpoint is
    # saved off-box continuously, not just at the end.
    p.add_argument("--save-steps", type=int, default=200, help="checkpoint + Hub-push cadence in optimizer steps")
    p.add_argument(
        "--no-device-map",
        dest="device_map_auto",
        action="store_false",
        default=True,
        help="disable device_map='auto' (set when launching under accelerate/FSDP/DeepSpeed multi-GPU)",
    )
    return p


def _load_chat_dataset(path: Path, max_examples: int = 0, seed: int = 1776):
    """Read the SFT JSONL into a `datasets.Dataset` of chat-message rows.

    Each row becomes ``{"messages": [system, user, assistant]}`` so trl's
    SFTTrainer applies the base model's own chat template (train/serve format
    parity) and, with ``assistant_only_loss``, masks the prompt from the loss.

    ``max_examples > 0`` subsamples to that many rows after a seeded shuffle --
    a reproducible first-run cost cap (see ``--max-examples``).
    """
    from datasets import Dataset  # local import: training-only dep

    rows = []
    with path.open() as f:
        for line in f:
            r = json.loads(line)
            rows.append(
                {
                    "messages": [
                        {"role": "system", "content": r["system"]},
                        {"role": "user", "content": r["user"]},
                        {"role": "assistant", "content": r["assistant"]},
                    ]
                }
            )
    if not rows:
        raise SystemExit(f"empty dataset: {path}")
    ds = Dataset.from_list(rows)
    if max_examples and max_examples < len(ds):
        ds = ds.shuffle(seed=seed).select(range(max_examples))
    return ds


def _resolve_sft_kwargs(args: argparse.Namespace, sft_fields: set[str]) -> dict:
    """Version-guarded kwargs to splat into ``SFTConfig(...)``.

    Isolated from `main` -- which needs a live torch/peft/transformers/trl
    install to reach the point where these kwargs matter -- so the guard
    logic itself (which of ``{max_length, max_seq_length, loss_type,
    lr_scheduler_type, warmup_ratio}`` to include, and under what condition)
    is unit-testable against a fake ``sft_fields`` set with NO training
    stack installed (see ``tests/test_lean_cot_recipe.py``).

    Two independent guards are folded together here, both version/config
    driven:

    - ``max_length`` vs ``max_seq_length``: trl renamed the field; exactly
      one of the two is always emitted, whichever ``sft_fields`` exposes.
    - ``loss_type`` / ``lr_scheduler_type`` / ``warmup_ratio``: emitted only
      when BOTH the caller asked for something non-default (``loss_type`` is
      unconditional -- see below -- but the other two are ``None``-gated)
      AND the installed trl/transformers actually declares the field, so an
      older pin in ``requirements-train.txt`` silently falls back to trl's
      own default instead of ``SFTConfig()`` raising an unknown-kwarg
      ``TypeError``.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI args. Reads ``max_seq_len``, ``lr_scheduler_type``,
        ``warmup_ratio``.
    sft_fields : set of str
        Field names exposed by the installed ``trl.SFTConfig``, i.e.
        ``{f.name for f in dataclasses.fields(SFTConfig)}``.

    Returns
    -------
    dict
        Keys are a subset of ``{"max_length", "max_seq_length", "loss_type",
        "lr_scheduler_type", "warmup_ratio"}``; always contains exactly one
        of the first two.
    """
    kwargs: dict = {
        ("max_length" if "max_length" in sft_fields else "max_seq_length"): args.max_seq_len,
    }
    # Force the STANDARD nll loss. trl >=1.7 defaults loss_type="chunked_nll",
    # which patches lm_head.forward at SFTTrainer init via
    # inspect.signature(forward.__func__) -- but on a device_map (accelerate-
    # hooked) model that forward is a functools.partial with no __func__, so
    # init raises AttributeError; and its compute_loss then needs
    # outputs.num_valid_tokens, absent without the patch. "nll" is the SAME loss
    # math (trl's own error recommends switching to it), just without the
    # lm-head-chunking memory optimization we don't need (Qwen's 151k-vocab
    # logits at seq 4096 are ~1.2 GB, fine on an H100). Version-guarded: older
    # trl lacks the loss_type field (and the crashing patch).
    if "loss_type" in sft_fields:
        kwargs["loss_type"] = "nll"
    # --lr-scheduler-type / --warmup-ratio: standard TrainingArguments fields,
    # guarded the SAME way as loss_type above, PLUS a None check -- the
    # caller leaving them at the CLI default (None) means "don't touch trl's
    # own default", distinct from the unconditional loss_type override.
    if args.lr_scheduler_type is not None and "lr_scheduler_type" in sft_fields:
        kwargs["lr_scheduler_type"] = args.lr_scheduler_type
    if args.warmup_ratio is not None and "warmup_ratio" in sft_fields:
        kwargs["warmup_ratio"] = args.warmup_ratio
    return kwargs


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        import torch
        from peft import LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
        from trl import SFTConfig, SFTTrainer
    except ImportError as exc:  # pragma: no cover - exercised only on a GPU box
        print(f"error: {exc}\n\n{_INSTALL_HINT}", file=sys.stderr)
        return 1

    # Seed BEFORE anything random happens (model/LoRA-adapter init, dropout, the
    # data sampler) so a run is reproducible from the CLI seed. SFTTrainer also
    # seeds from SFTConfig.seed, but do it explicitly here too -- adapter weights
    # (lora_A kaiming-random) are initialized during trainer construction, and an
    # up-front set_seed makes that init deterministic regardless of trl internals.
    set_seed(args.seed)

    # Compat shim for trust_remote_code models authored against older transformers
    # (Nemotron-Ultra's DeciLM modeling imports NEED_SETUP_CACHE_CLASSES_MAPPING,
    # removed in transformers 5.x). Inject known-removed symbols so the remote module
    # imports; they are generation-only and unused on the training path
    # (use_cache=False). hasattr-guarded, so a no-op for standard architectures.
    import transformers.generation.utils as _gu

    if not hasattr(_gu, "NEED_SETUP_CACHE_CLASSES_MAPPING"):
        try:
            from transformers.cache_utils import StaticCache, SlidingWindowCache

            _gu.NEED_SETUP_CACHE_CLASSES_MAPPING = {"static": StaticCache, "sliding_window": SlidingWindowCache}
        except Exception:  # noqa: BLE001
            _gu.NEED_SETUP_CACHE_CLASSES_MAPPING = {}

    dataset = _load_chat_dataset(args.dataset, max_examples=args.max_examples, seed=args.seed)

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=args.trust_remote_code)

    # Architecture scan on meta weights (config-only, no download). Two consumers:
    # the device map (sizing) and bitsandbytes' int32 guard -- bnb's 4-bit kernel
    # indexes with int32 and crashes ("invalid argument" at ops.cu) on any matrix
    # with >= 2**31 elements. Nemotron-Ultra's NAS blocks have FFN matrices up to
    # ~7e9 elements; those few stay bf16 via llm_int8_skip_modules, the rest quantize.
    _meta = None
    oversized: list = []
    if args.load_in_4bit or (args.device_map_auto and torch.cuda.is_available()):
        from accelerate import init_empty_weights
        from transformers import AutoConfig

        _cfg = AutoConfig.from_pretrained(args.base_model, trust_remote_code=args.trust_remote_code)
        with init_empty_weights():
            _meta = AutoModelForCausalLM.from_config(_cfg, trust_remote_code=args.trust_remote_code)
        if args.load_in_4bit:
            oversized = [
                name
                for name, mod in _meta.named_modules()
                if isinstance(mod, torch.nn.Linear) and mod.weight.numel() >= 2**31
            ]
            if oversized:
                print(f"bnb int32 guard: {len(oversized)} oversized matrices stay bf16: {oversized}")

    quant_config = None
    if args.load_in_4bit:
        # Supplying llm_int8_skip_modules REPLACES the default skip list (which
        # protects lm_head / tied embeddings), so merge the defaults back in.
        skip_modules = None
        if oversized:
            try:
                from transformers.quantizers.base import get_keys_to_not_convert
            except ImportError:  # older transformers
                from transformers.integrations import get_keys_to_not_convert
            skip_modules = sorted(set(oversized) | set(get_keys_to_not_convert(_meta)))
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            llm_int8_skip_modules=skip_modules,
        )

    # Build an EXPLICIT device map. device_map="auto" mis-offloads big models to
    # CPU/disk (bnb 4-bit forbids that) via its get_balanced_memory rebalancing;
    # infer_auto_device_map with an explicit per-GPU budget keeps every layer on GPU.
    # Sizing subtleties this handles:
    #  - bnb 4-bit quantizes ONLY nn.Linear. A MoE's fused-Parameter experts (most of
    #    its weight) stay bf16 -- so with ``--moe-unquantized`` we size at bf16, else
    #    at ~1 byte/param (4-bit, conservative).
    #  - int32-guarded matrices (above) also stay bf16: sized at 2 bytes/param via
    #    special_dtypes so bin-packing doesn't overfill their GPU, and their huge
    #    gradient-checkpoint recompute activations (~3 x seq x intermediate x bf16)
    #    get an extra per-GPU reserve.
    #  - SPREAD across all GPUs with headroom (a 7-GPU pack left too little and OOM'd
    #    the MoE LoRA forward): per-GPU cap = ceil(model / n_gpu) + 8 GiB, capped at
    #    VRAM minus the reserve.
    device_map = None
    if args.device_map_auto and torch.cuda.is_available():
        from accelerate.utils import infer_auto_device_map

        n_gpu = torch.cuda.device_count()
        vram_gib = int(torch.cuda.get_device_properties(0).total_memory / 1024**3)
        n_params = sum(p.numel() for p in _meta.parameters())
        is_4bit_eff = args.load_in_4bit and not args.moe_unquantized
        bytes_per = 1.0 if is_4bit_eff else 2.0
        special_dtypes = None
        skip_params = 0
        reserve = 10
        if is_4bit_eff and oversized:
            skip_params = sum(_meta.get_submodule(n).weight.numel() for n in oversized)
            special_dtypes = {f"{n}.weight": torch.bfloat16 for n in oversized}
            max_dim = max(max(_meta.get_submodule(n).weight.shape) for n in oversized)
            reserve += -(-(3 * args.max_seq_len * max_dim * 2) // 1024**3)
        model_gib = ((n_params - skip_params) * bytes_per + skip_params * 2.0) / 1024**3
        total_vram = vram_gib * n_gpu
        # Generous per-GPU cap for a model that fits COMFORTABLY: pack onto fewer GPUs
        # with big headroom and no risk of a large (NAS-irregular, e.g. Nemotron) layer
        # being offloaded to CPU by a tight budget. Reserve the tight all-GPU spread for
        # a NEAR-FULL model (e.g. Qwen's ~bf16 MoE) that would otherwise OOM the forward.
        if model_gib < 0.55 * total_vram:
            cap = vram_gib - reserve
        else:
            cap = max(int(model_gib / n_gpu) + 8, 8)
        budget = {i: f"{cap}GiB" for i in range(n_gpu)}
        device_map = infer_auto_device_map(
            _meta,
            max_memory=budget,
            no_split_module_classes=getattr(_meta, "_no_split_modules", None),
            dtype=torch.uint8 if is_4bit_eff else torch.bfloat16,
            special_dtypes=special_dtypes,
        )
    del _meta

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quant_config,
        torch_dtype=torch.bfloat16,
        device_map=device_map,
        trust_remote_code=args.trust_remote_code,  # Nemotron-Ultra's NAS arch needs this
    )

    # accelerate's device_map offload hooks are inference-only: a CPU/disk-offloaded
    # (or unplaced) weight only surfaces as "expected device meta but got cuda" deep
    # in BACKWARD. Fail fast at load instead -- training requires every parameter
    # resident on a GPU.
    if device_map is not None:
        off_gpu = [(n, str(p.device)) for n, p in model.named_parameters() if p.device.type != "cuda"]
        if off_gpu:
            raise RuntimeError(
                f"{len(off_gpu)} parameters are not on GPU (offloaded or meta); backward "
                f"would fail. First few: {off_gpu[:5]}. The model does not fit the "
                f"per-GPU budget -- use fewer reserve GiB, more/larger GPUs, or 4-bit."
            )

    # Two adapter paths into SFTTrainer:
    #  - fresh (default): hand trl a LoraConfig; it applies get_peft_model (and,
    #    for a quantized base, its k-bit prep) itself.
    #  - --init-adapter (staged SFT): load the stage-1 adapter as TRAINABLE and
    #    hand trl the already-wrapped PeftModel with peft_config=None. The k-bit
    #    prep trl would have done for the fresh path is replicated here, minus
    #    peft's optional fp32 upcast of non-quantized params -- the int32-guarded
    #    bf16 FFN matrices of the NAS bases are far too large to upcast.
    peft_config = None
    if args.init_adapter:
        from peft import PeftModel

        # Deliberately NOT prepare_model_for_kbit_training here. peft 0.19.1's
        # prepare upcasts EVERY non-``Params4bit`` fp16/bf16 parameter to fp32
        # -- which for the int32-guarded bases means the giant NAS FFN matrices
        # kept in bf16 (Nemotron-Ultra's 12 skip-quantized layers, ~72B params)
        # would balloon to fp32 (+~144 GB) and blow the device-map placement
        # this script carefully sized at bf16. trl's own fresh path calls prepare
        # only when the base is NOT sharded across devices; our fully-on-GPU
        # device_map load is the case where that upcast bites. The stage-1
        # adapter was trained on an already-k-bit-prepared base, and LoRA freezes
        # the layernorms prepare would have upcast, so the only prep the continue
        # path actually needs is the gradient-checkpointing input-grad hook below.
        model = PeftModel.from_pretrained(model, args.init_adapter, is_trainable=True)
        # Gradient checkpointing over a frozen base needs the inputs to carry
        # requires_grad, or backward finds nothing to differentiate through.
        model.enable_input_require_grads()
        n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"continuing adapter {args.init_adapter}: {n_trainable} trainable params")
        if n_trainable == 0:
            raise RuntimeError(
                f"adapter {args.init_adapter} loaded with 0 trainable parameters -- "
                "not a LoRA adapter, or is_trainable was ignored"
            )
    else:
        target_modules = (
            "all-linear"
            if args.target_modules == "all-linear"
            else [m.strip() for m in args.target_modules.split(",") if m.strip()]
        )
        peft_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            target_modules=target_modules,
            bias="none",
            task_type="CAUSAL_LM",
        )

    # assistant_only_loss masks the prompt from the loss, but trl requires the
    # chat template to expose `{% generation %}` markers (and some templates
    # can't be auto-patched). Decide UP FRONT with a read-only probe so the
    # trainer is built exactly once: retrying construction would stack a second
    # LoRA adapter (SFTTrainer applies peft_config to `model` in place before it
    # raises on the template). If trl is too old to expose the probe, trust the
    # flag. When the template is incompatible, fall back to full-sequence loss.
    use_assistant_only = args.assistant_only_loss
    if use_assistant_only:
        try:
            from trl.chat_template_utils import get_training_chat_template

            get_training_chat_template(tokenizer)  # raises if not training-compatible
        except ImportError:
            pass  # older trl without the probe: trust the flag
        except Exception as exc:  # noqa: BLE001 - any template-incompat error
            print(
                f"WARNING: {args.base_model}'s chat template is not training-compatible for "
                f"assistant-only loss; falling back to FULL-SEQUENCE loss (prompt tokens will "
                f"contribute to the loss). Original error: {exc}",
                file=sys.stderr,
            )
            use_assistant_only = False

    # Durable checkpointing (satisfies "save the SFT'd checkpoint"): save every
    # --save-steps AND, when a Hub repo is given, push the adapter as each
    # checkpoint lands. A spot box terminates on interruption and its local
    # output_dir dies with it, so an end-only save would lose a multi-hour run;
    # every_save keeps a reloadable adapter in the private Hub repo continuously.
    hub_kwargs: dict = {}
    if args.push_to_hub:
        hub_kwargs = dict(
            push_to_hub=True,
            hub_model_id=args.push_to_hub,
            hub_strategy="every_save",
            hub_private_repo=args.private,
        )

    # trl renamed SFTConfig.max_seq_length -> max_length; pick whichever the
    # installed version exposes so this works across the requirements-train.txt
    # range (an old trl still has max_seq_length; trl >=1.x has max_length).
    import dataclasses

    _sft_fields = {f.name for f in dataclasses.fields(SFTConfig)}
    _seq_kwargs = _resolve_sft_kwargs(args, _sft_fields)

    sft_config = SFTConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,  # -1 = full --epochs; >0 caps a first run
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        bf16=args.bf16,
        gradient_checkpointing=True,
        assistant_only_loss=use_assistant_only,  # mask the prompt from the loss (probed above)
        logging_steps=10,
        save_strategy="steps",
        save_steps=args.save_steps,
        save_total_limit=3,  # cap local disk; the Hub keeps the durable history
        seed=args.seed,
        data_seed=args.seed,  # deterministic data sampler/shuffle order
        full_determinism=args.full_determinism,
        report_to=[],
        **_seq_kwargs,
        **hub_kwargs,
    )

    # trl 1.7's chunked-CE loss assumes hidden states and labels share a device
    # (true for FSDP/DDP/single-GPU). With a device_map-sharded (pipeline-parallel)
    # model the hidden states land on the LAST device but the Trainer keeps labels on
    # the first -> "indices should be on the same device as the indexed tensor". Move
    # labels to the hidden-states device inside the loss (no-op when co-located;
    # backward still flows across devices via autograd).
    try:
        import trl.trainer.sft_trainer as _sftmod

        _orig_cce = _sftmod._chunked_cross_entropy_loss

        def _cce_on_hidden_device(hidden_states, *a, labels=None, shift_labels=None, **kw):
            dev = hidden_states.device
            if labels is not None:
                labels = labels.to(dev)
            if shift_labels is not None:
                shift_labels = shift_labels.to(dev)
            return _orig_cce(hidden_states, *a, labels=labels, shift_labels=shift_labels, **kw)

        _sftmod._chunked_cross_entropy_loss = _cce_on_hidden_device
    except (ImportError, AttributeError):
        pass  # a trl without this internal -- rely on its own device handling

    class _PipelineSFTTrainer(SFTTrainer):
        """Return the loss on the Trainer's INPUT device for device_map pipeline models.

        trl computes the loss on the model's LAST pipeline device (cuda:N-1), but
        transformers' Trainer asserts the per-step loss shares the running-loss
        accumulator's device (the first/input device, cuda:0) -- "Calculated loss must
        be on the original device". Move the final loss back; backward still flows
        across devices via autograd. No-op when the model is single-device.
        """

        def compute_loss(self, model, inputs, *a, **kw):  # type: ignore[override]
            out = super().compute_loss(model, inputs, *a, **kw)
            dev = inputs["input_ids"].device
            if isinstance(out, tuple):
                return (out[0].to(dev),) + tuple(out[1:])
            return out.to(dev)

    trainer = _PipelineSFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
    )
    # Resume from a checkpoint (spot-interruption recovery). "auto" lets the HF
    # Trainer pick the latest checkpoint-* in --output-dir (which the orchestrator
    # has pre-synced from S3); a path resumes that exact checkpoint. Restores model
    # weights, optimizer, scheduler, RNG, and the step counter, so an interrupted
    # stage continues instead of restarting. Only valid against a checkpoint from
    # the SAME config (dataset subsample + max_steps) -- a cap change invalidates it.
    resume = args.resume_from_checkpoint
    if resume == "auto":
        resume = True
    trainer.train(resume_from_checkpoint=resume)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))

    if args.push_to_hub:
        # Final durable push, on top of the per-save pushes above. HF_TOKEN must
        # be set for a private push -- and, later, for the EC2 provisioner to pull
        # the adapter for serving (baked at provision time; see ec2.py).
        trainer.push_to_hub()  # pushes output_dir (adapter + adapter_config) to hub_model_id
        tokenizer.push_to_hub(args.push_to_hub, private=args.private)
        print(f"pushed adapter -> {args.push_to_hub} (private={args.private})")

    print(f"done: adapter saved to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
