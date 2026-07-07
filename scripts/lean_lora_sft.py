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
import sys
from pathlib import Path

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
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--lora-dropout", type=float, default=0.05)
    p.add_argument(
        "--target-modules",
        default="all-linear",
        help="'all-linear' (default, robust across dense/MoE/NAS) or a comma-separated module list",
    )
    # Training hyperparameters
    p.add_argument("--load-in-4bit", action="store_true", default=True, help="QLoRA 4-bit base (default on)")
    p.add_argument("--no-4bit", dest="load_in_4bit", action="store_false")
    p.add_argument("--epochs", type=float, default=1.0)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=16)
    p.add_argument("--max-seq-len", type=int, default=4096)
    p.add_argument("--seed", type=int, default=1776)
    return p


def _load_chat_dataset(path: Path):
    """Read the SFT JSONL into a `datasets.Dataset` of chat-message rows.

    Each row becomes ``{"messages": [system, user, assistant]}`` so trl's
    SFTTrainer applies the base model's own chat template (train/serve format
    parity) and, with ``assistant_only_loss``, masks the prompt from the loss.
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
    return Dataset.from_list(rows)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        import torch
        from peft import LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from trl import SFTConfig, SFTTrainer
    except ImportError as exc:  # pragma: no cover - exercised only on a GPU box
        print(f"error: {exc}\n\n{_INSTALL_HINT}", file=sys.stderr)
        return 1

    dataset = _load_chat_dataset(args.dataset)

    quant_config = None
    if args.load_in_4bit:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quant_config,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,  # Nemotron-Ultra's NAS arch needs this
    )

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

    sft_config = SFTConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        bf16=True,
        gradient_checkpointing=True,
        max_seq_length=args.max_seq_len,
        assistant_only_loss=True,  # train on the tactic tail, not the prompt
        logging_steps=10,
        save_strategy="epoch",
        seed=args.seed,
        report_to=[],
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
    )
    trainer.train()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))

    if args.push_to_hub:
        # HF_TOKEN must be exported for a private push (and, later, for the EC2
        # provisioner to pull it -- see smolbench/evals/ec2.py, HF_TOKEN is
        # baked at provision time).
        trainer.model.push_to_hub(args.push_to_hub, private=args.private)
        tokenizer.push_to_hub(args.push_to_hub, private=args.private)
        print(f"pushed adapter -> {args.push_to_hub} (private={args.private})")

    print(f"done: adapter saved to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
