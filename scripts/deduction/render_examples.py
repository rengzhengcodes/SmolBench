"""Render every rung of the library-block design for N cells into a directory tree.

Layout::

    <out>/index.json                       per-cell, per-rung token counts
    <out>/README.md                        what each rung is
    <out>/<theorem>__k<k>/meta.json        theorem, step, ground truth, MPI names
    <out>/<theorem>__k<k>/<rung>/system.md the fixed system message
    <out>/<theorem>__k<k>/<rung>/prompt.md the user turn, exactly as sent
    <out>/<theorem>__k<k>/<rung>/meta.json prompt tokens, block entries, trivial flag

Cells are the last step (``k = n_tactics - 1``) of replay-passing theorems
with at most ``--max-tactics`` tactics whose final step cites at least one
corpus premise, sampled with ``--seed``; a rung that is trivial for a cell
(adds nothing over the rung below) is still rendered and flagged.

Run::

    SMOLBENCH_LEAN_DATA=<corpus> .venv/bin/python scripts/deduction/render_examples.py \\
        --out examples --n 100 --max-level 4 [--allow-precutoff]

``--allow-precutoff`` accepts a Benchmark 4 export without ``postcutoff``
row flags (the July 2026 pilot corpus); the sweep itself never does.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from smolbench.deduction.lean import context, corpus, prompt  # noqa: E402
from smolbench.deduction.lean.premises import lookup  # noqa: E402
from smolbench.deduction.lean.runner import slug_rung, slug_theorem  # noqa: E402

RUNG_DOC = {
    "stepk:2": "None: goal, full state, proof so far, theorem name. No premises.",
    "hint:N": "Flagged ladder: stepk:2 + 'Premises used in the next tactic' (0), + signatures (1), + full source (2), + (N-2)-hop closure (3+).",
    "noise:N": "hint:(N-1) whitespace-padded to hint:N's prompt token count.",
    "sig:N": "Unflagged library block, signatures: MPI lemmas + N-hop closure, import order, nothing marked.",
    "proof:N": "Same block as sig:N with full source and proofs.",
    "signoise:N": "sig:0 padded to sig:N (the hops as blank length).",
    "proofnoise:N": "sig:N padded to proof:N (the proof bodies as blank length).",
    "hoponly:N": "sig:N with the MPI lemmas removed: the N-hop closure alone, signatures.",
    "sigpad:N": "sig:N with every non-MPI entry replaced in place by same-token whitespace lines (MPI at the same depth).",
    "proofpad:N": "proof:N with every proof body replaced in place by same-token whitespace lines (signatures at the same depth).",
    "siglorem:N": "sigpad:N with lorem-ipsum prose as the filler instead of whitespace.",
    "prooflorem:N": "proofpad:N with lorem-ipsum prose as the filler instead of whitespace.",
}


def _rungs(max_level: int) -> list[str]:
    out = ["stepk:2"]
    out += [f"hint:{i}" for i in range(0, max_level + 1)]
    out += [f"noise:{i}" for i in range(1, max_level + 1)]
    out += [f"sig:{i}" for i in range(0, max_level + 1)]
    out += [f"proof:{i}" for i in range(0, max_level + 1)]
    out += [f"signoise:{i}" for i in range(1, max_level + 1)]
    out += [f"hoponly:{i}" for i in range(1, max_level + 1)]
    out += [f"sigpad:{i}" for i in range(1, max_level + 1)]
    out += [f"proofpad:{i}" for i in range(0, max_level + 1)]
    out += [f"siglorem:{i}" for i in range(1, max_level + 1)]
    out += [f"prooflorem:{i}" for i in range(0, max_level + 1)]
    out += [f"proofnoise:{i}" for i in range(0, max_level + 1)]
    return out


def _count_tokens(text: str) -> int:
    import tiktoken

    return len(tiktoken.get_encoding("cl100k_base").encode(text))


def is_linear(theorem: corpus.BenchmarkTheorem) -> bool:
    """True when every traced tactic starts from the previous tactic's end state.

    LeanDojo records tactics in pre-order and never records ``·`` bullets, so a
    structured proof's list interleaves nested tactics with top-level ones; its
    "last tactic" may be the inner step of a case and its prefix may close the
    goal early. A linear chain is exactly the top-level tactic sequence, so
    step ``k`` and the replayed prefix mean what the prompt says they mean.
    """
    ts = theorem.traced_tactics
    return all(ts[i].state_before == ts[i - 1].state_after for i in range(1, len(ts)))


def select_cells(
    n: int,
    max_tactics: int,
    seed: int,
    kind: str = "random",
    split: str = "val",
    linear: bool = False,
) -> list[tuple[corpus.BenchmarkTheorem, int]]:
    """Sample ``n`` last-step cells whose final tactic cites a corpus premise."""
    pool = [
        t
        for t in corpus.iter_replay_passing(kind, split)  # type: ignore[arg-type]
        if t.has_proof
        and (max_tactics <= 0 or len(t.traced_tactics) <= max_tactics)
        and (not linear or is_linear(t))
    ]
    rng = random.Random(seed)
    rng.shuffle(pool)
    cells = []
    for t in pool:
        k = len(t.traced_tactics) - 1
        if any(lookup(p["full_name"]) is not None for p in t.traced_tactics[k].premises):
            cells.append((t, k))
        if len(cells) == n:
            break
    if len(cells) < n:
        raise SystemExit(f"only {len(cells)} eligible cells in the pool; wanted {n}")
    return cells


def render_cell(
    theorem: corpus.BenchmarkTheorem, k: int, rungs: list[str], out_dir: Path
) -> dict:
    """Write one cell's directory; return its index record."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tt = theorem.traced_tactics[k]
    (out_dir / "meta.json").write_text(
        json.dumps(
            {
                "theorem": theorem.full_name,
                "file_path": theorem.file_path,
                "k": k,
                "n_tactics": len(theorem.traced_tactics),
                "linear": is_linear(theorem),
                "ground_truth_tactic": tt.tactic,
                "mpi_premises": [p["full_name"] for p in tt.premises],
                "mpi_in_corpus": [
                    p["full_name"] for p in tt.premises if lookup(p["full_name"]) is not None
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    rec: dict = {"theorem": theorem.full_name, "k": k, "rungs": {}}
    for rung in rungs:
        chain, level_s = rung.split(":", 1)
        level = int(level_s)
        rdir = out_dir / slug_rung(rung)
        rdir.mkdir(exist_ok=True)
        try:
            rc = context.render(theorem, k, chain, level)  # type: ignore[arg-type]
        except ValueError as exc:  # a control whose base is longer than its target
            (rdir / "meta.json").write_text(json.dumps({"error": str(exc)}, indent=2))
            rec["rungs"][rung] = {"error": str(exc)}
            continue
        user = prompt.build_user_prompt(rc)
        (rdir / "system.md").write_text(prompt.SYSTEM + "\n")
        (rdir / "prompt.md").write_text(user + "\n")
        entries = sum(1 for line in rc.text.splitlines() if line.startswith("### "))
        meta = {
            "rung": rung,
            "prompt_tokens_cl100k": _count_tokens(user),
            "block_entries": entries,
            "trivial": context.is_trivial_rung(theorem, k, chain, level),  # type: ignore[arg-type]
        }
        (rdir / "meta.json").write_text(json.dumps(meta, indent=2))
        rec["rungs"][rung] = meta
    return rec


def write_readme(out: Path, rungs: list[str], n: int, max_level: int) -> None:
    lines = [
        "# Rendered examples of the library-block design",
        "",
        f"{n} cells, every rung through level {max_level}. Each cell directory holds `meta.json`",
        "(theorem, step, ground-truth tactic, MPI names) and one subdirectory per rung with",
        "`system.md`, `prompt.md` (the user turn exactly as sent) and `meta.json` (cl100k prompt",
        "tokens, block entries, trivial flag). `index.json` collects every rung's numbers.",
        "",
        "| rung | meaning |",
        "| --- | --- |",
    ]
    lines += [f"| `{k}` | {v} |" for k, v in RUNG_DOC.items()]
    lines += ["", "Rungs rendered: " + ", ".join(f"`{r}`" for r in rungs), ""]
    (out / "README.md").write_text("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("examples"))
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--max-level", type=int, default=4)
    ap.add_argument("--max-tactics", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--kind", default="random")
    ap.add_argument("--split", default="val")
    ap.add_argument(
        "--allow-precutoff",
        action="store_true",
        help="accept split rows without a postcutoff flag (pilot corpus)",
    )
    ap.add_argument(
        "--linear",
        action="store_true",
        help="only theorems whose traced tactics form one state chain (no nested tactics)",
    )
    args = ap.parse_args(argv)

    if args.allow_precutoff:
        _orig = corpus._from_json

        def _lenient(rec: dict) -> corpus.BenchmarkTheorem:
            rec.setdefault("postcutoff", False)
            return _orig(rec)

        corpus._from_json = _lenient  # type: ignore[assignment]
        corpus.reset_caches()

    rungs = _rungs(args.max_level)
    cells = select_cells(
        args.n, args.max_tactics, args.seed, args.kind, args.split, linear=args.linear
    )
    args.out.mkdir(parents=True, exist_ok=True)
    index = []
    for i, (t, k) in enumerate(cells, 1):
        name = f"{slug_theorem(t.full_name)}__k{k}"
        rec = render_cell(t, k, rungs, args.out / name)
        rec["dir"] = name
        index.append(rec)
        toks = rec["rungs"].get(f"sig:{args.max_level}", {}).get("prompt_tokens_cl100k")
        print(f"[{i:3d}/{len(cells)}] {name}  sig:{args.max_level}={toks} tok", flush=True)
    (args.out / "index.json").write_text(json.dumps(index, indent=1))
    write_readme(args.out, rungs, len(cells), args.max_level)
    print(f"wrote {len(index)} cells x {len(rungs)} rungs under {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
