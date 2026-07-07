"""Build the decontaminated Lean 4 LoRA SFT dataset (JSONL + manifest).

Wraps `smolbench.deduction.lean.sft.iter_dataset`: streams (system, user,
assistant) chat triples from the LeanDojo Benchmark 4 training pool with
every eval theorem held out by ``full_name``, writes them to a JSONL, and
writes a committed ``manifest.json`` beside it recording the config, the
counts, and a fingerprint of the included/held-out theorem sets.

Runs on the main 3.14 venv (no ``lean_dojo``; construction needs no Lean).
Requires the benchmark to be bootstrapped (see notebooks/lean/README.md) --
i.e. ``notebooks/lean/data/leandojo_benchmark_4/<kind>/<split>.json`` present.

Examples
--------
    .venv/bin/python -m scripts.build_lean_sft            # defaults below
    .venv/bin/python scripts/build_lean_sft.py --k-strategy all --out /tmp/sft.jsonl

Defaults: train on ``novel_premises/train`` at ``stepk:1``, ``k_strategy=last``,
holding out ``novel_premises/{val,test}``; write to
``notebooks/lean/data/sft/novel_premises_train_stepk1.jsonl``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Anchor imports on the repo root (scripts/..), so an ad-hoc `python
# scripts/build_lean_sft.py` works even if the package is not `pip install`ed
# into the active interpreter.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from smolbench.deduction.lean import sft  # noqa: E402
from smolbench.deduction.lean.sft import DEFAULT_EVAL_SPECS, eval_holdout_names  # noqa: E402


def _fingerprint(names: set[str]) -> str:
    """Deterministic sha256 over a sorted name set (audit fingerprint)."""
    h = hashlib.sha256()
    for n in sorted(names):
        h.update(n.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def _parse_spec(s: str) -> tuple[str, str]:
    kind, _, split = s.partition(":")
    if not kind or not split:
        raise argparse.ArgumentTypeError(f"eval-spec must be 'kind:split'; got {s!r}")
    return (kind, split)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--train-kind", default="novel_premises", choices=["random", "novel_premises"])
    p.add_argument("--train-split", default="train", choices=["train", "val", "test"])
    p.add_argument("--source", default="with_proof", choices=["with_proof", "replay_passing"])
    p.add_argument("--k-strategy", default="last", choices=["last", "all", "sample"])
    p.add_argument("--level", type=int, default=1, help="stepk level to render (default 1 = full tactic state)")
    p.add_argument("--seed", type=int, default=1776)
    p.add_argument(
        "--eval-spec",
        type=_parse_spec,
        action="append",
        default=None,
        help="kind:split to hold out (repeatable); default novel_premises:val + novel_premises:test",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=_REPO_ROOT / "notebooks" / "lean" / "data" / "sft" / "novel_premises_train_stepk1.jsonl",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    eval_specs = tuple(args.eval_spec) if args.eval_spec else DEFAULT_EVAL_SPECS

    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)

    holdout = eval_holdout_names(eval_specs)
    emitted: set[str] = set()
    stats: dict = {}

    with out.open("w") as f:
        for ex in sft.iter_dataset(
            train_kind=args.train_kind,
            train_split=args.train_split,
            eval_specs=eval_specs,
            source=args.source,
            k_strategy=args.k_strategy,
            chain="stepk",
            level=args.level,
            seed=args.seed,
            stats=stats,
        ):
            emitted.add(ex.full_name)
            f.write(json.dumps(ex.to_json()) + "\n")

    # Hard decontamination gate: no emitted theorem may be in the holdout.
    leaked = emitted & holdout
    if leaked:
        print(f"FATAL: {len(leaked)} eval theorem(s) leaked into SFT set, e.g. {sorted(leaked)[:5]}", file=sys.stderr)
        return 1

    manifest = {
        "config": {
            "train_kind": args.train_kind,
            "train_split": args.train_split,
            "source": args.source,
            "k_strategy": args.k_strategy,
            "chain": "stepk",
            "level": args.level,
            "seed": args.seed,
            "eval_specs": [list(s) for s in eval_specs],
        },
        "stats": stats,
        "decontamination": {
            "holdout_size": len(holdout),
            "holdout_fingerprint": _fingerprint(holdout),
            "included_theorems": len(emitted),
            "included_fingerprint": _fingerprint(emitted),
            "leaked": 0,
        },
        "output_jsonl": out.name,
    }
    manifest_path = out.with_name(out.stem + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(
        f"wrote {stats.get('examples', 0)} examples from {stats.get('theorems', 0)} theorems "
        f"({stats.get('dropped', 0)} of {stats.get('pool', 0)} pool theorems held out; "
        f"holdout={len(holdout)}) -> {out}\nmanifest -> {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
