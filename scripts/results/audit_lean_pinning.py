"""Audit that all 21 deduction lanes ran the SAME pinned theorems.

WHY THIS EXISTS
---------------
The family-ladder deduction study compares 21 model checkpoints against
each other. Every cross-model claim it makes -- ladder contrasts, paired
McNemar tests, the block bootstrap -- assumes the lanes are *paired*:
that model A and model B were asked the same questions. Nothing in the
pipeline enforced that. `notebooks/deduction/run_study.py`'s
`build_config` draws the theorem pool with
``random.Random(0).sample(iter_replay_passing(...), 300)``, so the pinned
set is only as stable as (a) the 805-theorem
``replay_passing_novel_premises_val.jsonl`` sidecar and (b) the ordering
of ``novel_premises/val.json``. Both are external data. Neither is in the
repo any more -- the 2026-08-25 archive moved them to S3 -- so a clean
clone cannot even *name* the 300 theorems the study ran, let alone check
them.

This script closes that gap two ways. It reproduces the pin from its
documented derivation, and -- independently -- it reads back what the 21
lanes ACTUALLY ran from the S3 spool and diffs those sets against each
other. The second check is the load-bearing one: config equality proves
intent, not outcome.

WHAT IT CHECKS, WEAKEST TO STRONGEST
------------------------------------
Each layer can pass while the next one fails, which is exactly why all
five run:

1. **Config** -- every lane's as-run ``manifest.json`` carries a
   byte-identical ``theorems`` block and base ``seed``. Proves the lanes
   were *launched* the same. Says nothing about what came back.
2. **Theorem sets** -- the ``theorems/<slug>/`` prefixes in each lane's
   spool are the same 300. Proves the same theorems were reached.
3. **Cell keys** -- the ``(theorem, rung)`` output files are the same 944
   in every lane. A lane can hold all 300 theorems and still be missing
   rungs.
4. **Prompt bytes** -- the ``prompts/<rung>.md`` objects are byte-identical
   across lanes, compared by S3 ETag (MD5, no download). This is the
   strongest available pairing gate: identical bytes prove the same
   theorem AT THE SAME STEP ``k`` under the same rendered context, which
   set equality alone does not. It also catches a model-dependent
   ``noise:N`` padding, since that rung is token-matched and *could*
   legitimately differ per tokenizer.
5. **Side-run containment** -- every other run under ``deduction/runs/``
   sharing this study's ``theorems`` block stays inside the pinned 944-cell
   set rather than extending it. Two kinds exist, and they feed different
   pools: ``dojoinit_recovery_2026-08-18`` is ADDITIVE (its rows were folded
   into the headline analysis), while ``flip_``/``flip2_nemotron-3-nano-4b``
   are the process-nondeterminism (flip-rate) measurement and are
   deliberately NOT folded into headlines. Both are checked, because a
   side-run reaching a theorem outside the pin would mean the draw was not
   deterministic, whichever pool it feeds.

Layer 4 needs one wrinkle to be correct: on-disk theorem directories are
slugged by `runner.slug_theorem` (``[^a-zA-Z0-9._-] -> _``), so
``List.get?_set_eq`` and ``Int.mul_div_assoc'`` become
``List.get__set_eq`` and ``Int.mul_div_assoc_``. Comparing raw
``theorem_id`` values from the recovery rows against directory names
without slugging reports ~18 phantom out-of-set cells per lane. This
script slugs both sides.

WHAT IT DELIBERATELY DOES NOT CHECK
-----------------------------------
**Whether the ANALYZED subsets match.** This script proves the 21 lanes
were *asked* the identical 944 questions. It does not prove their
surviving data is identical. A cell can be present and DEAD (empty
``candidate_proof``), and the published analysis ran on smaller pools
(707 / 828 / 833 cells) precisely because dead cells and verdict
filtering shrink 944 unevenly. Nothing here shows dead cells fall in the
same places across lanes -- that is a different axis, owned by
``scripts/results/audit_run_completeness.py`` and by the study's explicit
dual-pool reporting. Do not read a pass here as "the analysis was
paired"; read it as "the questions were".

**Whether the theorems are appropriate content for these models.** They
are not: see ``notebooks/deduction/README.md``, "Corpus date vs. model
cutoffs". Every theorem is
from mathlib4 at commit ``fe4454af`` (traced 2024-03-24) and every model
on the roster has a knowledge cutoff after that date. Pinning and recency
are independent properties; this script measures only the first.

USAGE
-----
    python scripts/results/audit_lean_pinning.py                # S3 audit (layers 1-5)
    python scripts/results/audit_lean_pinning.py --reproduce    # + rederive the pin from corpus data
    python scripts/results/audit_lean_pinning.py --emit-manifest OUT.json

``--reproduce`` needs the LeanDojo split and the replay sidecar; point
``--val-json`` / ``--replay-jsonl`` at local copies or S3 URLs under
``archives/2026-08-25/``. Credentials come from the ambient AWS
environment (the ``smolbench-llm-operator`` key is sufficient: this
script only reads).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

BUCKET = "smolbench-results-414266451290"
REGION = "us-west-2"
RUN_PREFIX = "deduction/runs"
RECOVERY_RUN = "dojoinit_recovery_2026-08-18"

#: Side-runs that share the study's `theorems` block but live under their
#: own run prefix, as ``(run_name, lane)``. These are the flip-rate
#: (process-nondeterminism) re-runs: NOT folded into headline pools, but
#: still required to stay inside the pin, since a stray theorem would mean
#: the draw was not deterministic.
FLIP_RUNS = [("flip_nemotron-3-nano-4b", "nemotron-3-nano-4b"),
             ("flip2_nemotron-3-nano-4b", "nemotron-3-nano-4b")]

#: The 21 lane spec keys, in roster order (7 families x 3 rungs). Kept
#: literal rather than imported from ``notebooks/induction/run_study.py``
#: so this audit does not depend on the driver it is auditing.
LANES = [
    "qwen3.5-27b", "qwen3.5-122b-a10b", "qwen3.5-397b-a17b",
    "nemotron-3-nano-4b", "nemotron-3-nano-30b-a3b", "nemotron-3-super-120b-a12b",
    "gemma-4-e2b", "gemma-4-12b", "gemma-4-31b",
    "glm-4.7-flash", "glm-4.5-air", "glm-4.7",
    "ministral-3-3b", "ministral-3-8b", "ministral-3-14b",
    "exaone-4.0-32b", "exaone-4.5-33b", "k-exaone-236b-a23b",
    "deepseek-v4-flash", "deepseek-v3.1", "deepseek-v4-pro",
]

#: Expected shape of the pinned set, asserted rather than discovered so a
#: shrunken spool fails loudly instead of quietly re-baselining.
EXPECTED_THEOREMS = 300
EXPECTED_CELLS = 944


def slug_theorem(name: str) -> str:
    """Filesystem-safe theorem name; mirrors `runner.slug_theorem` exactly.

    Duplicated (not imported) for the same reason ``LANES`` is: this audit
    must not inherit a bug from the module under audit. The two are pinned
    together by ``tests/deduction/test_lean_pinning_audit.py``.
    """
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)


def _client():
    import boto3

    return boto3.client("s3", region_name=REGION)


def _read(s3, key: str) -> str:
    return s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()


def fetch_manifests(s3) -> dict[str, dict]:
    """Per-lane as-run ``manifest.json`` (the config actually launched)."""
    return {k: json.loads(_read(s3, f"{RUN_PREFIX}/scaling_{k}/manifest.json")) for k in LANES}


def fetch_spool_index(s3) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    """List each lane's output-cell keys and prompt ETags in one pass.

    Returns
    -------
    cells : dict[str, set[str]]
        Lane -> ``{"<theorem-slug>|<rung-slug>"}`` for every ``outputs/``
        object. Presence only; content is gated by `prompts` and by
        ``scripts/results/audit_run_completeness.py``.
    prompts : dict[str, dict[str, str]]
        Lane -> cell key -> S3 ETag of the rendered ``prompts/<rung>.md``.
        ETag is the object MD5 for these (small, single-part) uploads, so
        equality across lanes is byte equality without downloading ~19 MB
        x 21 of spool.
    """
    cells: dict[str, set[str]] = {}
    prompts: dict[str, dict[str, str]] = {}
    for lane in LANES:
        pref = f"{RUN_PREFIX}/scaling_{lane}/theorems/"
        c: set[str] = set()
        p: dict[str, str] = {}
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=pref):
            for obj in page.get("Contents", []):
                parts = obj["Key"][len(pref):].split("/")
                if len(parts) != 3:
                    continue
                thm, kind, leaf = parts
                if kind == "outputs":
                    c.add(f"{thm}|{leaf.split('__')[0]}")
                elif kind == "prompts" and leaf.endswith(".md"):
                    p[f"{thm}|{leaf[:-3]}"] = obj["ETag"].strip('"')
        cells[lane], prompts[lane] = c, p
    return cells, prompts


def fetch_recovery(s3) -> dict[str, set[str]]:
    """Cell keys touched by the additive dojoinit recovery, per lane."""
    out: dict[str, set[str]] = {}
    for lane in LANES:
        key = f"{RUN_PREFIX}/{RECOVERY_RUN}/{lane}/recovered_rows.jsonl"
        try:
            body = _read(s3, key)
        except Exception:
            out[lane] = set()
            continue
        out[lane] = {
            f"{slug_theorem(r['theorem_id'])}|{r['rung'].replace(':', '-')}"
            for r in (json.loads(x) for x in body.splitlines() if x.strip())
        }
    return out


def fetch_flip_cells(s3) -> dict[str, set[str]]:
    """Cell keys reached by the flip-rate side-runs, per run name.

    These spool in the same ``theorems/<slug>/outputs/`` layout as a
    normal lane, so this reuses the layer-2/3 listing shape rather than
    the recovery run's flat ``recovered_rows.jsonl``.
    """
    out: dict[str, set[str]] = {}
    for run, _lane in FLIP_RUNS:
        pref = f"{RUN_PREFIX}/{run}/theorems/"
        cells: set[str] = set()
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=pref):
            for obj in page.get("Contents", []):
                parts = obj["Key"][len(pref):].split("/")
                if len(parts) == 3 and parts[1] == "outputs":
                    cells.add(f"{parts[0]}|{parts[2].split('__')[0]}")
        out[run] = cells
    return out


def reproduce_pin(val_json: Path, replay_jsonl: Path) -> list[str]:
    """Re-derive the pinned 300 from the documented recipe.

    Mirrors `runner._select_theorems` for this study's spec: take the
    ``novel_premises``/``val`` split, keep the theorems whose ground-truth
    proof replays (``verdict == "success"`` in the sidecar) IN SPLIT
    ORDER, then ``random.Random(0).sample(pool, 300)``. Split order is
    load-bearing -- ``rng.sample`` is order-sensitive, so a re-sorted pool
    yields a different 300 under the same seed.
    """
    val = json.loads(val_json.read_text())
    passing = {
        json.loads(line)["full_name"]
        for line in replay_jsonl.read_text().splitlines()
        if line.strip() and json.loads(line).get("verdict") == "success"
    }
    pool = [t for t in val if t["full_name"] in passing]
    return [t["full_name"] for t in random.Random(0).sample(pool, 300)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reproduce", action="store_true",
                    help="also re-derive the pin from corpus data (needs --val-json/--replay-jsonl)")
    ap.add_argument("--val-json", type=Path,
                    default=Path("notebooks/deduction/data/leandojo_benchmark_4/novel_premises/val.json"))
    ap.add_argument("--replay-jsonl", type=Path,
                    default=Path("notebooks/deduction/data/replay_passing_novel_premises_val.jsonl"))
    ap.add_argument("--emit-manifest", type=Path, default=None,
                    help="write the reproduced pin to this path as pinned_theorems.json")
    args = ap.parse_args(argv)

    failures: list[str] = []
    s3 = _client()

    # -- Layer 1: as-run config --------------------------------------
    mans = fetch_manifests(s3)
    blocks = {k: json.dumps(m["config"]["theorems"], sort_keys=True) for k, m in mans.items()}
    seeds = {k: m["config"]["seed"] for k, m in mans.items()}
    if len(set(blocks.values())) != 1:
        failures.append(f"theorems blocks differ across lanes: {sorted(set(blocks.values()))}")
    if len(set(seeds.values())) != 1:
        failures.append(f"base seeds differ across lanes: {sorted(set(seeds.values()))}")
    print(f"[1/5] config      : {len(set(blocks.values()))} distinct theorems block, "
          f"{len(set(seeds.values()))} distinct seed  -> {next(iter(blocks.values()))}")

    # -- Layers 2-4: what actually landed in the spool ----------------
    cells, prompts = fetch_spool_index(s3)
    thm_sets = {k: {c.split("|")[0] for c in v} for k, v in cells.items()}
    inter, union = set.intersection(*thm_sets.values()), set.union(*thm_sets.values())
    if not (len(inter) == len(union) == EXPECTED_THEOREMS):
        failures.append(f"theorem sets differ: intersection={len(inter)} union={len(union)}")
    print(f"[2/5] theorem sets: intersection={len(inter)} union={len(union)} "
          f"(expected {EXPECTED_THEOREMS} == {EXPECTED_THEOREMS})")

    cinter, cunion = set.intersection(*cells.values()), set.union(*cells.values())
    if not (len(cinter) == len(cunion) == EXPECTED_CELLS):
        failures.append(f"cell key sets differ: intersection={len(cinter)} union={len(cunion)}")
    print(f"[3/5] cell keys   : intersection={len(cinter)} union={len(cunion)} "
          f"(expected {EXPECTED_CELLS} == {EXPECTED_CELLS})")

    # Byte equality of the rendered prompt, per cell, across all 21 lanes.
    variants = {key: len({prompts[l].get(key) for l in LANES}) for key in cunion}
    divergent = {k: v for k, v in variants.items() if v != 1}
    if divergent:
        failures.append(f"{len(divergent)} cells have model-dependent prompt bytes: "
                        f"{sorted(divergent)[:5]}")
    print(f"[4/5] prompt bytes: {len(cunion) - len(divergent)}/{len(cunion)} cells "
          f"byte-identical across all {len(LANES)} lanes")

    # -- Layer 5: side-runs stay inside the pinned set -----------------
    rec = fetch_recovery(s3)
    outside = {k: v - cells[k] for k, v in rec.items()}
    if any(outside.values()):
        failures.append(f"recovery rows outside the pinned cell set: "
                        f"{ {k: len(v) for k, v in outside.items() if v} }")
    flips = fetch_flip_cells(s3)
    flip_outside = {r: v - cells[lane] for (r, lane), v in
                    ((rl, flips[rl[0]]) for rl in FLIP_RUNS)}
    if any(flip_outside.values()):
        failures.append(f"flip-run cells outside the pinned cell set: "
                        f"{ {k: len(v) for k, v in flip_outside.items() if v} }")
    print(f"[5/5] side-runs   : recovery {sum(len(v) for v in rec.values())} cells "
          f"(additive), flip {sum(len(v) for v in flips.values())} cells "
          f"(not folded into headlines); "
          f"{sum(len(v) for v in outside.values()) + sum(len(v) for v in flip_outside.values())}"
          f" outside the pinned set")

    # -- Optional: rederive the pin from its documented recipe --------
    if args.reproduce or args.emit_manifest:
        names = reproduce_pin(args.val_json, args.replay_jsonl)
        slugged = {slug_theorem(n) for n in names}
        if slugged != inter:
            failures.append(f"reproduced pin != spooled set "
                            f"(missing {len(inter - slugged)}, extra {len(slugged - inter)})")
        digest = hashlib.sha256("\n".join(sorted(names)).encode()).hexdigest()
        print(f"[+  ] reproduce   : seeded sample matches spool={slugged == inter} sha256={digest[:16]}")
        if args.emit_manifest:
            args.emit_manifest.write_text(json.dumps({
                "count": len(names),
                "sha256_of_sorted_full_names": digest,
                "full_names": sorted(names),
            }, indent=2))
            print(f"        wrote {args.emit_manifest}")

    print()
    if failures:
        print("PINNING AUDIT FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"PINNING AUDIT PASSED: all {len(LANES)} lanes ran the identical "
          f"{EXPECTED_THEOREMS} theorems / {EXPECTED_CELLS} cells, byte-identical prompts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
