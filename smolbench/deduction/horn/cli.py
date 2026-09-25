"""CLI: render arms of seeds to a directory, or check an answer.

    python -m smolbench.deduction.horn.cli render --seeds 0-9 --m 12 --height 2 \
        --n-constants 4 --open-frac 0.25 \
        --lemma-tokens 20000 --unfold-tokens 100000 \
        --arms lem both pad --out examples_horn
    python -m smolbench.deduction.horn.cli check examples_horn/s0007/lem answer.md

``--lemma-tokens`` grows the extra-lemma count until the ``lem`` prompt
reaches the budget; ``--unfold-tokens`` sets per-lemma tree depths until the
added derivation material (``both`` minus ``lem``) reaches the budget. Layout:
``<out>/s<seed>/theory.json`` and ``<out>/s<seed>/<arm>/{prompt.md,
system.md,meta.json}``. Every rendered arm is certified before it is written.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict
from pathlib import Path

from .checker import certify, designed_proof, verify
from .render import Rendered, Tokenizer, render
from .theory import Theory, generate


def _seeds(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def _fit_budgets(a: argparse.Namespace, seed: int, tok: Tokenizer) -> Theory:
    """Generate with the CLI knobs, then fit the two token budgets if given."""
    kw = {
        "m": a.m,
        "height": a.height,
        "n_constants": a.n_constants,
        "open_frac": a.open_frac,
        "fact_height": a.fact_height,
        "fact_chain": a.fact_chain,
        "n_unused_facts": a.n_unused_facts,
    }
    n_extra = a.n_extra
    if a.match_library:
        # Same library as an already rendered rung: its n_extra and per-lemma depths
        # for this seed, so only the fact trees differ between the two rungs.
        ref = Theory.from_json(
            (Path(a.match_library) / f"s{seed:04d}" / "theory.json").read_text(
                encoding="utf-8"
            )
        )
        depths = {lm.index: lm.height for lm in ref.library}
        th = generate(seed, n_extra=ref.n_extra, depths=depths, **kw)
        if [(lm.head, lm.body) for lm in th.library] != [
            (lm.head, lm.body) for lm in ref.library
        ]:
            raise SystemExit(
                f"seed {seed}: library differs from {a.match_library}; same --m/--height/--open-frac?"
            )
        if a.fact_tokens:
            th = _fit_fact_chain(seed, th, kw, ref.n_extra, a.fact_tokens, tok)
        return th
    th = generate(seed, n_extra=n_extra, **kw)
    if a.lemma_tokens:
        base = render(generate(seed, n_extra=0, **kw), "lem", tok).n_tokens
        n = render(th, "lem", tok).n_tokens
        for _ in range(12):
            if abs(n - a.lemma_tokens) <= max(50, a.lemma_tokens // 50):
                break
            per = max(8.0, (n - base) / max(1, n_extra))
            n_extra = max(0, int(n_extra + (a.lemma_tokens - n) / per))
            th = generate(seed, n_extra=n_extra, **kw)
            n = render(th, "lem", tok).n_tokens
    if a.unfold_tokens:
        th = _fit_unfold(seed, th, kw, n_extra, a.unfold_tokens, tok)
    if a.fact_tokens:
        th = _fit_fact_chain(seed, th, kw, n_extra, a.fact_tokens, tok)
    return th


def _fit_fact_chain(  # pylint: disable=too-many-arguments
    seed: int, th: Theory, kw: dict, n_extra: int, target: int, tok: Tokenizer
) -> Theory:
    """Unary chain length below each fact-tree leaf so that tokens(deep) - tokens(lem)
    is close to ``target`` (binary search; the lemma trees keep their fitted depths)."""
    if kw.get("fact_height", 0) < 1:
        raise SystemExit("--fact-tokens needs --fact-height >= 1")
    depths = {lm.index: lm.height for lm in th.library}

    def unfold(chain: int) -> tuple[Theory, int]:
        t = generate(
            seed, n_extra=n_extra, depths=depths, **{**kw, "fact_chain": chain}
        )
        return t, render(t, "deep", tok).n_tokens - render(t, "lem", tok).n_tokens

    lo, hi = 0, 1
    best, cur = unfold(hi)
    while cur < target and hi < 4096:
        lo, hi = hi, hi * 2
        best, cur = unfold(hi)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        t, u = unfold(mid)
        if u <= target:
            lo, best = mid, t
        else:
            hi = mid - 1
    return best


def _fit_unfold(  # pylint: disable=too-many-arguments,too-many-locals
    seed: int, th: Theory, kw: dict, n_extra: int, target: int, tok: Tokenizer
) -> Theory:
    """Per-lemma depths so that tokens(both) - tokens(lem) is close to ``target``.

    Raise the base depth while the full unfolding stays under target, then
    promote a prefix of the lemmas (seeded random order) one level to close
    the gap. Never exceeds the target.
    """
    n = len(th.library)

    def unfold(depths: dict[int, int]) -> tuple[Theory, int]:
        t = generate(seed, n_extra=n_extra, depths=depths, **kw)
        return t, render(t, "both", tok).n_tokens - render(t, "lem", tok).n_tokens

    base = kw["height"]
    best, cur = unfold({})
    while cur < target:
        nxt, cur_nxt = unfold({i: base + 1 for i in range(1, n + 1)})
        if cur_nxt > target:
            break
        base += 1
        best, cur = nxt, cur_nxt
    if cur >= target:
        return best
    order = list(range(1, n + 1))
    random.Random(seed * 31 + 7).shuffle(order)
    lo, hi = 0, n  # promote the first k lemmas of `order`
    while lo < hi:
        mid = (lo + hi + 1) // 2
        depths = {i: base + 1 for i in order[:mid]}
        depths.update({i: base for i in order[mid:]})
        t, u = unfold(depths)
        if u <= target:
            lo, best = mid, t
        else:
            hi = mid - 1
    return best


def write_seed(  # pylint: disable=too-many-locals
    out: Path, theory: Theory, arms: list[str], tok: Tokenizer, max_steps: int = 0
) -> list[dict]:
    """Render and certify ``arms`` of ``theory`` under ``out/s<seed>``."""
    sd = out / f"s{theory.seed:04d}"
    sd.mkdir(parents=True, exist_ok=True)
    tj = sd / "theory.json"
    text = theory.to_json()
    # Compare theories, not bytes: an older file lacks fields added since with defaults.
    if (
        tj.exists()
        and Theory.from_json(tj.read_text(encoding="utf-8")).to_json() != text
    ):
        raise RuntimeError(
            f"{tj} exists with a different theory; rendering into it would desynchronize "
            "arms already rendered there. Use a new --out directory."
        )
    tj.write_text(text, encoding="utf-8")
    rows = []
    for arm in arms:
        r = render(theory, arm, tok, max_steps=max_steps)
        cert = certify(theory, r)
        if not cert.ok:
            raise RuntimeError(f"seed {theory.seed} {arm}: {cert.reasons}")
        ad = sd / arm
        ad.mkdir(exist_ok=True)
        (ad / "prompt.md").write_text(r.prompt, encoding="utf-8")
        (ad / "system.md").write_text(r.system, encoding="utf-8")
        meta = asdict(r)
        meta.pop("prompt")
        meta.pop("system")
        meta["designed_proof"] = designed_proof(
            theory, r, "long" if arm.startswith(("unf", "ax")) else "short"
        )
        meta["certificate"] = asdict(cert)
        meta["depths"] = {lm.index: lm.height for lm in theory.library}
        (ad / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        rows.append(
            {
                "seed": theory.seed,
                "arm": arm,
                "tokens": r.n_tokens,
                "rules": r.n_rules,
                "filler": r.filler_tokens,
                "min_steps": cert.min_steps,
                "lines": r.prompt.count("\n"),
            }
        )
    return rows


def cmd_render(a: argparse.Namespace) -> int:
    """Render every seed and arm; print a per-arm summary."""
    tok = Tokenizer()
    rows: list[dict] = []
    for seed in _seeds(a.seeds):
        th = _fit_budgets(a, seed, tok)
        cap = th.m * a.max_steps_x if a.max_steps_x else a.max_steps
        rows += write_seed(Path(a.out), th, a.arms, tok, max_steps=int(cap))
    by_arm: dict[str, list[dict]] = {}
    for r in rows:
        by_arm.setdefault(r["arm"], []).append(r)
    print(
        f"{'arm':8s} {'n':>4s} {'rules':>6s} {'tokens':>8s} {'filler':>7s} {'steps':>6s} {'lines':>6s}"
    )
    for arm, rs in by_arm.items():
        n = len(rs)
        print(
            f"{arm:8s} {n:4d} {sum(r['rules'] for r in rs)/n:6.1f} "
            f"{sum(r['tokens'] for r in rs)/n:8.0f} {sum(r['filler'] for r in rs)/n:7.0f} "
            f"{sum(r['min_steps'] for r in rs)/n:6.1f} {max(r['lines'] for r in rs):6d}"
        )
    return 0


def cmd_check(a: argparse.Namespace) -> int:
    """Verify an answer file against a rendered arm directory."""
    ad = Path(a.arm_dir)
    theory = Theory.from_json((ad.parent / "theory.json").read_text(encoding="utf-8"))
    meta = json.loads((ad / "meta.json").read_text(encoding="utf-8"))
    for k in ("designed_proof", "certificate", "depths"):
        meta.pop(k, None)
    meta["facts"] = tuple(meta["facts"])
    r = Rendered(prompt="", system="", **meta)
    v = verify(theory, r, Path(a.answer).read_text(encoding="utf-8"))
    print(json.dumps(asdict(v), ensure_ascii=False, indent=1))
    return 0 if v.verdict == "success" else 1


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    p = argparse.ArgumentParser(prog="horn")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("render")
    pr.add_argument("--seeds", default="0-9")
    pr.add_argument("--m", type=int, default=4)
    pr.add_argument("--height", type=int, default=2, help="base tree depth")
    pr.add_argument(
        "--n-extra", type=int, default=4, help="alternative rules in the library"
    )
    pr.add_argument("--n-constants", type=int, default=3)
    pr.add_argument(
        "--n-unused-facts",
        type=int,
        default=0,
        help="given facts no rule uses (default 0: every given fact is on a derivation of the "
        "goal; rungs rendered before 2026-09-25 used 2, pass 2 to add arms to them)",
    )
    pr.add_argument(
        "--open-frac",
        type=float,
        default=0.25,
        help="alternatives true for the main constant",
    )
    pr.add_argument(
        "--lemma-tokens",
        type=int,
        default=0,
        help="grow n_extra until lem reaches this",
    )
    pr.add_argument(
        "--unfold-tokens",
        type=int,
        default=0,
        help="set depths so both - lem reaches this",
    )
    pr.add_argument(
        "--max-steps", type=int, default=0, help="step budget stated in the prompt"
    )
    pr.add_argument(
        "--max-steps-x",
        type=float,
        default=0.0,
        help="step budget as a multiple of the chain length",
    )
    pr.add_argument(
        "--fact-height",
        type=int,
        default=0,
        help="derivation tree depth below each fact",
    )
    pr.add_argument(
        "--fact-chain",
        type=int,
        default=0,
        help="unary chain length below each fact-tree leaf",
    )
    pr.add_argument(
        "--fact-tokens",
        type=int,
        default=0,
        help="fit --fact-chain so tokens(deep) - tokens(lem) is close to this",
    )
    pr.add_argument(
        "--match-library",
        default=None,
        help="rung dir whose per-seed library (n_extra, depths) to reuse; skips token fitting",
    )
    pr.add_argument("--arms", nargs="+", default=["lem", "both", "pad"])
    pr.add_argument("--out", required=True)
    pr.set_defaults(func=cmd_render)
    pc = sub.add_parser("check")
    pc.add_argument("arm_dir")
    pc.add_argument("answer")
    pc.set_defaults(func=cmd_check)
    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
