"""Builds the paired 500-row micro datasets for the dense fenced micro-smoke.

The 2026-07-18 CoT gate came back RED on Qwen (attention-only LoRA — the
recipe's pre-registered least-favorable configuration): cot-r128 matched
bare-r128 exactly while both beat base, i.e. the r128 recipe works but the
CoT target format added nothing THERE. The pre-registered follow-up
(PREREGISTRATION.md "RED-gate follow-up"; approved plan, live-gate 3) is a
cheap DENSE fenced micro-smoke before any abandon decision. This script
builds its two training sets:

- ``cot_stepk1_fenced_micro500.jsonl`` — 500 rows in the ``fenced`` style
  (``{rationale}\\n\\n```lean\\n{tail}\\n```` ``), the dense-model analogue of
  the Qwen ``think`` style.
- ``cot_stepk1_bare_micro500.jsonl`` — the SAME 500 (full_name, k) rows with
  bare tactic-tail targets, so the arms differ in target format ONLY.

No new annotation spend: the fenced rationales are recomposed byte-for-byte
from the existing ``cot_stepk1_think_8k.jsonl`` (deepseek.v3.2 annotations,
temperature 0) via ``annotate_lean_cot.compose_target`` — the SAME rationale
text a fresh ``--style fenced`` run would have wrapped, since the annotator
prompt is style-independent (the style only affects composition). Tails are
taken from the bare sibling and asserted byte-identical to the tail embedded
in each think row, so the supervision signal is unchanged. Decontamination is
inherited from the 8k build (subset of a decontaminated set; manifest links
the parent).

Selection is the repo's seeded blake2b-priority idiom (stable under source
reordering): rows sorted by ``blake2b(f"{seed}:{full_name}:{k}")`` and the
first N taken.

Usage:
    .venv-lean/bin/python scripts/build_lean_cot_micro.py [--n 500] [--seed 1776]
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SFT_DIR = _REPO_ROOT / "notebooks" / "lean" / "data" / "sft"

sys.path.insert(0, str(_REPO_ROOT / "scripts"))
from annotate_lean_cot import compose_target  # noqa: E402

THINK_PREFIX = "<think>\n"
THINK_SEP = "\n</think>\n\n"


def load_keyed(path: Path) -> dict:
    rows = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            key = (r["meta"]["full_name"], r["meta"]["k"])
            assert key not in rows, f"duplicate key {key} in {path.name}"
            rows[key] = r
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--seed", type=int, default=1776)
    args = ap.parse_args()

    think = load_keyed(_SFT_DIR / "cot_stepk1_think_8k.jsonl")
    bare = load_keyed(_SFT_DIR / "cot_stepk1_bare_8k.jsonl")
    assert set(think) == set(bare), "think/bare 8k files are not row-aligned"

    def priority(key):
        return hashlib.blake2b(
            f"{args.seed}:{key[0]}:{key[1]}".encode(), digest_size=16
        ).hexdigest()

    chosen = sorted(think, key=priority)[: args.n]

    fenced_rows, bare_rows = [], []
    for key in chosen:
        t, b = think[key], bare[key]
        a = t["assistant"]
        assert a.startswith(THINK_PREFIX) and THINK_SEP in a, f"malformed think row {key}"
        rationale, tail = a[len(THINK_PREFIX):].split(THINK_SEP, 1)
        assert tail == b["assistant"], f"tail mismatch think vs bare for {key}"
        fenced_rows.append(
            {
                "system": t["system"],
                "user": t["user"],
                "assistant": compose_target("fenced", rationale, tail),
                "meta": {**t["meta"], "cot_style": "fenced"},
            }
        )
        bare_rows.append(b)

    outputs = {
        "cot_stepk1_fenced_micro500.jsonl": fenced_rows,
        "cot_stepk1_bare_micro500.jsonl": bare_rows,
    }
    for name, rows in outputs.items():
        with open(_SFT_DIR / name, "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    manifest = {
        "config": {
            "n": args.n,
            "seed": args.seed,
            "selection": "blake2b-priority over (full_name, k)",
            "source_think": "cot_stepk1_think_8k.jsonl",
            "source_bare": "cot_stepk1_bare_8k.jsonl",
        },
        "stats": {
            "rows_each": len(fenced_rows),
            "tail_byte_identity_asserted": True,
            "distinct_theorems": len({k[0] for k in chosen}),
        },
        "decontamination": "inherited from cot_stepk1_think_8k.manifest.json (subset)",
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "outputs": list(outputs),
    }
    with open(_SFT_DIR / "cot_stepk1_micro500.manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"built {len(fenced_rows)} paired rows -> {', '.join(outputs)}")
    print(f"distinct theorems: {manifest['stats']['distinct_theorems']}")


if __name__ == "__main__":
    main()
