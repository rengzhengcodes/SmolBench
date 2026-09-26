"""CLI: render the four arms of a rung to a directory, or check an answer.

    python -m smolbench.deduction.horn.cli render --seeds 100-129 --m 12 --out rungs/m12
    python -m smolbench.deduction.horn.cli check rungs/m12/s0100/lem answer.md

A rung is defined by its chain length ``m``: the library holds the ``m`` chain
lemmas and ``5 m`` open alternatives (``--alt-per-lemma``), and every lemma's
derivation tree has depth 2 (``--height``), so the prompt size follows from
``m``. Layout: ``<out>/s<seed>/theory.json`` and
``<out>/s<seed>/<arm>/{prompt.md,system.md,meta.json}``. Every rendered arm
is certified before it is written.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .checker import certify, designed_proof, verify
from .render import ARMS, Rendered, Tokenizer, check_arm, render
from .theory import Theory, generate

DEFAULT_ALT_PER_LEMMA = 5
DEFAULT_HEIGHT = 2


def _seeds(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def build_theory(seed: int, m: int, height: int = 2, alt_per_lemma: int = 5) -> Theory:
    """The rung's theory for ``seed``: ``m`` chain lemmas, ``alt_per_lemma * m`` open
    alternatives, every tree at depth ``height``."""
    if m < 1 or alt_per_lemma < 0:
        raise ValueError("need m >= 1 and alt_per_lemma >= 0")
    th = generate(seed, m=m, height=height, n_extra=alt_per_lemma * m)
    assert th.n_extra == alt_per_lemma * m
    return th


def write_seed(out: Path, theory: Theory, arms: list[str], tok: Tokenizer) -> list[dict]:
    """Render and certify ``arms`` of ``theory`` under ``out/s<seed>``."""
    sd = out / f"s{theory.seed:04d}"
    sd.mkdir(parents=True, exist_ok=True)
    tj = sd / "theory.json"
    text = theory.to_json()
    if tj.exists() and Theory.from_json(tj.read_text(encoding="utf-8")).to_json() != text:
        raise RuntimeError(
            f"{tj} exists with a different theory; rendering into it would desynchronize "
            "arms already rendered there. Use a new --out directory."
        )
    tj.write_text(text, encoding="utf-8")
    rows = []
    for arm in arms:
        r = render(theory, check_arm(arm), tok)
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
        meta["designed_proof"] = designed_proof(theory, "short")
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
        th = build_theory(seed, a.m, a.height, a.alt_per_lemma)
        rows += write_seed(Path(a.out), th, a.arms, tok)
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
    v = verify(theory, Rendered.from_meta(meta), Path(a.answer).read_text(encoding="utf-8"))
    print(json.dumps(asdict(v), ensure_ascii=False, indent=1))
    return 0 if v.verdict == "success" else 1


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    p = argparse.ArgumentParser(prog="horn")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("render")
    pr.add_argument("--seeds", default="100-129", help="comma list or a-b ranges")
    pr.add_argument("--m", type=int, default=12, help="chain length")
    pr.add_argument(
        "--height", type=int, default=DEFAULT_HEIGHT, help="derivation tree depth (>= 2)"
    )
    pr.add_argument(
        "--alt-per-lemma",
        type=int,
        default=DEFAULT_ALT_PER_LEMMA,
        help="open alternatives per chain lemma",
    )
    pr.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS))
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
