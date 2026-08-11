"""Convert the decontaminated Lean SFT JSONL to NeMo 2.0 FineTuningDataModule format.

The Nemotron-Ultra-253B reasoning slot is trained via NVIDIA NeMo (the HF/peft/bnb
stack cannot handle its DeciLM NAS arch -- see the trio memory). NeMo's
``FineTuningDataModule`` expects **NDJSON with ``input``/``output`` keys**, split into
``training``/``validation``/``test``.jsonl under a ``dataset_root``, and does NOT apply
a chat template. So this:

- selects the **exact same** capped subsample the HF-pipeline models trained on
  (``datasets.Dataset.from_list(rows).shuffle(seed).select(range(cap))`` -- identical
  algorithm to ``scripts/lean_lora_sft.py::_load_chat_dataset``), so the cohort is
  comparable across models;
- pre-renders the chat prompt into ``input`` with Nemotron-Ultra's chat template
  (verified byte-identical to the standard Llama-3.1 template, so training matches
  what the vLLM eval serves), ``output`` = the assistant tactic tail + ``<|eot_id|>``;
- writes the three NeMo splits (val/test are tiny -- just NeMo bookkeeping; the real
  eval is the deduction sweep on the replay_passing sidecars).

Runs on a venv with ``datasets`` (e.g. the throwaway train venv). No Lean, no GPU.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

#: Nemotron-Ultra-253B chat template == standard Llama-3.1 (verified against
#: nvidia/Llama-3_1-Nemotron-Ultra-253B-v1's tokenizer.apply_chat_template). Rendering
#: it here keeps train/serve parity with the vLLM deduction eval (which sends the same
#: system+user messages and lets vLLM apply this template).
_TMPL = (
    "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
    "<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
    "<|start_header_id|>assistant<|end_header_id|>\n\n"
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sft", type=Path,
                   default=_REPO_ROOT / "notebooks" / "lean" / "data" / "sft" / "novel_premises_train_stepk1.jsonl")
    p.add_argument("--out", type=Path,
                   default=_REPO_ROOT / "notebooks" / "lean" / "data" / "sft" / "nemo" / "nemotron_ultra")
    p.add_argument("--cap", type=int, default=3000,
                   help="same first-run cap as the HF models (0 = all); selected with the identical seeded shuffle")
    p.add_argument("--seed", type=int, default=1776, help="must match the HF runs' --seed for the same subsample")
    p.add_argument("--n-eval", type=int, default=20, help="held-out val + test rows each (NeMo bookkeeping only)")
    p.add_argument("--no-bos", action="store_true",
                   help="omit the leading <|begin_of_text|> (use if NeMo's tokenizer adds BOS -> avoid double-BOS)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    from datasets import Dataset  # local: training-side dep

    rows = [json.loads(line) for line in args.sft.open()]
    # EXACT same subsample as scripts/lean_lora_sft.py::_load_chat_dataset:
    # Dataset.from_list(rows).shuffle(seed).select(range(cap)).
    ds = Dataset.from_list(rows)
    if args.cap and args.cap < len(ds):
        ds = ds.shuffle(seed=args.seed).select(range(args.cap))
    sel = list(ds)

    def render(r: dict) -> dict:
        inp = _TMPL.format(system=r["system"], user=r["user"])
        if args.no_bos:
            inp = inp.replace("<|begin_of_text|>", "", 1)
        return {"input": inp, "output": r["assistant"] + "<|eot_id|>",
                "full_name": (r.get("meta") or {}).get("full_name")}

    out_rows = [render(r) for r in sel]
    v = min(args.n_eval, max(1, len(out_rows) // 10))
    splits = {"test": out_rows[:v], "validation": out_rows[v:2 * v], "training": out_rows[2 * v:]}

    args.out.mkdir(parents=True, exist_ok=True)
    for name, data in splits.items():
        with (args.out / f"{name}.jsonl").open("w") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(splits['training'])} train / {len(splits['validation'])} val / "
          f"{len(splits['test'])} test (cap={args.cap}, seed={args.seed}) -> {args.out}")
    # Show one rendered example so the format is auditable.
    ex = splits["training"][0]
    print("--- example input (repr, first 240 chars) ---")
    print(repr(ex["input"][:240]))
    print("--- example output (repr) ---")
    print(repr(ex["output"][:160]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
