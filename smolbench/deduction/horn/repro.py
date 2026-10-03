"""Reproduce the Horn benchmark results of the ICLR 2027 submission.

    python -m smolbench.deduction.horn.repro models
    python -m smolbench.deduction.horn.repro render --model glm-4.7 --out rungs/m48
    python -m smolbench.deduction.horn.repro verify rungs/m48 --m 48
    python -m smolbench.deduction.horn.repro command --model glm-4.7 --rung rungs/m48 --out rows.jsonl
    python -m smolbench.deduction.horn.repro report rows.jsonl
    python -m smolbench.deduction.horn.repro check-data <results folder>

``iclr.json`` (next to this file) records the protocol: seeds, replicates, sampling, the
chain length ``m`` and serving settings of every model, a SHA-256 digest of every
rendered theory, and the published pass rates. ``render`` regenerates a model's rung from
its seeds and checks it against the digests, so a rung that verifies is byte-identical to
the prompts the models were served. ``command`` prints the vLLM serve command (for
self-hosted models) and the sweep command with the protocol's settings. ``report``
summarizes result rows and prints them next to the published numbers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shlex
import sys
from pathlib import Path

from .cli import build_theory, parse_seeds, write_seed
from .render import ARMS, Tokenizer
from .stats import arm_order, contrast, format_p, load_rows, pass_rate

PROTOCOL_PATH = Path(__file__).with_name("iclr.json")
#: Files of one theory that the digest covers, relative to ``<rung>/s<seed>/``.
ARM_FILES = ("prompt.md", "system.md", "meta.json")
DELTAS = (("lem", "both"), ("pad", "both"), ("disc", "both"))
SWEEP = "scripts/deduction/horn/sweep.py"
BEDROCK_SWEEP = "scripts/deduction/horn/bedrock_sweep.py"


def load_protocol() -> dict:
    """The recorded protocol (``iclr.json``)."""
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def seed_digest(seed_dir: Path, arms: tuple[str, ...] = ARMS) -> str:
    """SHA-256 over ``theory.json`` and every arm's prompt, system prompt and metadata."""
    h = hashlib.sha256()
    names = ["theory.json"] + [f"{arm}/{f}" for arm in arms for f in ARM_FILES]
    for name in names:
        h.update(name.encode() + b"\0")
        h.update((seed_dir / name).read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def rung_digests(rung: Path, seeds: list[int]) -> dict[str, str]:
    """``{seed: digest}`` for the given seeds of a rendered rung."""
    return {str(s): seed_digest(rung / f"s{s:04d}") for s in seeds}


def verify_rung(rung: Path, m: int, seeds: list[int] | None = None) -> list[str]:
    """Problems found when comparing ``rung`` with the recorded digests (empty: identical)."""
    recorded = load_protocol()["rung_digests"].get(str(m))
    if recorded is None:
        return [f"no recorded digests for m={m}; recorded levels: {sorted(load_protocol()['rung_digests'], key=int)}"]
    problems = []
    for s in seeds or [int(x) for x in recorded]:
        sd = rung / f"s{s:04d}"
        if str(s) not in recorded:
            problems.append(f"s{s:04d}: seed not in the protocol")
        elif not (sd / "theory.json").exists():
            problems.append(f"s{s:04d}: missing")
        else:
            try:
                got = seed_digest(sd)
            except FileNotFoundError as err:
                problems.append(f"s{s:04d}: {err.filename} missing")
                continue
            if got != recorded[str(s)]:
                problems.append(f"s{s:04d}: digest differs from the served rung")
    return problems


def check_data(data: Path) -> list[str]:
    """Problems found when checking a results folder against its ``MANIFEST.json``.

    Checks every listed file's SHA-256 and every prompt directory's ``seed_digest``.
    """
    manifest_path = data / "MANIFEST.json"
    if not manifest_path.exists():
        return [f"{manifest_path} not found"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems = []
    for rel, info in manifest["files"].items():
        path = data / rel
        if not path.exists():
            problems.append(f"{rel}: missing")
            continue
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != info["sha256"]:
            problems.append(f"{rel}: checksum differs from the MANIFEST")
    for rung, info in manifest.get("prompts", {}).items():
        for seed, digest in info["digests"].items():
            rel = f"horn/prompts/{rung}/s{int(seed):04d}"
            try:
                got = seed_digest(data / rel, tuple(info["arms"]))
            except FileNotFoundError as err:
                problems.append(f"{rel}: {Path(err.filename).name} missing")
                continue
            if got != digest:
                problems.append(f"{rel}: digest differs from the MANIFEST")
    return problems


def render_rung(out: Path, m: int, seeds: list[int]) -> None:
    """Render and certify the four arms of every seed at chain length ``m``."""
    proto = load_protocol()
    tok = Tokenizer()
    for seed in seeds:
        theory = build_theory(seed, m, proto["height"], proto["alt_per_lemma"])
        write_seed(out, theory, list(ARMS), tok)


def model_entry(key: str) -> dict:
    """One model's record, or SystemExit listing the known keys."""
    models = load_protocol()["models"]
    if key not in models:
        raise SystemExit(f"unknown model {key!r}; known: {', '.join(models)}")
    return models[key]


def serve_command(key: str) -> list[str]:
    """``vllm serve`` for a self-hosted model: the pinned checkpoint and the served context.

    The serving arguments come from the deployment spec
    (``smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS``). The single-sequence settings there
    (``--max-num-seqs 1``, ``--enforce-eager``) were dropped for the Horn runs, which
    batched requests.
    """
    from smolbench.evals.providers.ec2 import (  # pylint: disable=import-outside-toplevel
        EC2_DEPLOY_SPECS,
    )

    spec = EC2_DEPLOY_SPECS[key]
    args = list(spec.get("vllm_args", []))
    for flag, n in (("--max-num-seqs", 2), ("--enforce-eager", 1)):
        if flag in args:
            i = args.index(flag)
            del args[i : i + n]
    proto = load_protocol()
    return [
        "vllm", "serve", spec["hf_model_id"],
        "--served-model-name", key,
        "--tensor-parallel-size", str(spec.get("tp", 1)),
        "--max-model-len", str(proto["sampling"]["context_length"]),
        "--max-num-seqs", "256",
        *args,
    ]  # fmt: skip


def sweep_command(key: str, rung: Path, out: Path, endpoint: str | None, api_key: str | None) -> list[str]:
    """The sweep command that runs ``key`` on ``rung`` with the protocol's settings."""
    proto = load_protocol()
    entry = model_entry(key)
    samp = proto["sampling"]
    common = [
        "--rung-dir", str(rung),
        "--seeds", proto["seeds"],
        "--replicates", str(proto["replicates"]),
        "--max-tokens", str(samp["max_tokens"]),
        "--temperature", str(samp["temperature"]),
        "--context-length", str(samp["context_length"]),
        "--scoring", proto["scoring"],
        "--out", str(out),
    ]  # fmt: skip
    if entry["backend"] == "bedrock":
        cmd = [
            "python", BEDROCK_SWEEP,
            "--model", entry["bedrock_model_id"],
            "--spec-key", key,
            "--region", entry["bedrock_region"],
        ]  # fmt: skip
        if entry.get("bedrock_extra_fields"):
            cmd += ["--extra-fields", json.dumps(entry["bedrock_extra_fields"])]
        return cmd + common
    cmd = [
        "python", SWEEP,
        "--endpoint", endpoint or "http://127.0.0.1:8000/v1",
        "--model", key,
        "--spec-key", key,
    ]  # fmt: skip
    if api_key:
        cmd += ["--api-key", api_key]
    return cmd + common


def report(paths: list[Path], rng_seed: int = 0) -> str:
    """Pass rates and deltas per model and rung, next to the published values."""
    cells, dropped = load_rows(paths)
    models = load_protocol()["models"]
    rng = random.Random(rng_seed)
    scorings = _scorings(paths)
    lines = []
    for (model, rung), arms in sorted(cells.items()):
        published = models.get(model, {}).get("results", {})
        ref = published.get(scorings[0]) if len(scorings) == 1 else None
        seeds = sorted({s for arm in arms.values() for s in arm})
        n = sum(len(v) for arm in arms.values() for v in arm.values())
        lines.append(f"== {model} {rung}: {n} cells, {len(seeds)} seeds, scoring {'/'.join(scorings)}")
        head = f"   {'':10s} {'pass %':>8s}"
        lines.append(head + (f" {'published':>10s}" if ref else ""))
        for arm in sorted(arms, key=arm_order):
            row = f"   {arm:10s} {pass_rate(arms[arm]):8.1f}"
            if ref and arm in ref:
                row += f" {ref[arm]:10.1f}"
            lines.append(row)
        for x, y in DELTAS:
            if x in arms and y in arms:
                mean, lo, hi, p, k = contrast(arms[x], arms[y], rng)
                name = f"{x}-{y}"
                row = f"   {name:10s} {mean:+8.1f}  [{lo:+.1f}, {hi:+.1f}]  {format_p(p, k)}  ({k} seeds)"
                if ref and name in ref:
                    row += f"  published {ref[name]:+.1f}"
                lines.append(row)
    if dropped:
        lines.append(f"dropped rows: {dropped}")
    return "\n".join(lines)


def _scorings(paths: list[Path]) -> list[str]:
    """The scoring modes found in the rows (rows without the field were scored ``iclr``)."""
    found: set[str] = set()
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    found.add(json.loads(line).get("scoring") or "iclr")
                except json.JSONDecodeError:
                    continue
    return sorted(found) or ["iclr"]


def cmd_models(_: argparse.Namespace) -> int:
    """List the models, their chain lengths and backends."""
    proto = load_protocol()
    print(f"{'model':28s} {'m':>3s}  {'backend':8s} {'lem':>6s} {'pad':>6s} {'both':>6s}  notes")
    for key, e in proto["models"].items():
        r = e["results"]["iclr"]
        print(f"{key:28s} {e['m']:3d}  {e['backend']:8s} {r['lem']:6.1f} {r['pad']:6.1f} {r['both']:6.1f}  {e.get('notes', '')}")
    return 0


def cmd_render(a: argparse.Namespace) -> int:
    """Render a rung, then check it against the recorded digests."""
    proto = load_protocol()
    m = a.m if a.m is not None else model_entry(a.model)["m"]
    seeds = parse_seeds(a.seeds or proto["seeds"])
    out = Path(a.out)
    render_rung(out, m, seeds)
    print(f"rendered m={m}, {len(seeds)} seeds x {len(ARMS)} arms to {out}")
    if str(m) not in proto["rung_digests"]:
        print(f"m={m} is not a level of the ICLR run; nothing to verify against")
        return 0
    return _print_verify(out, m, seeds)


def cmd_verify(a: argparse.Namespace) -> int:
    """Compare a rendered rung with the recorded digests."""
    return _print_verify(Path(a.rung), a.m, parse_seeds(a.seeds) if a.seeds else None)


def _print_verify(rung: Path, m: int, seeds: list[int] | None) -> int:
    problems = verify_rung(rung, m, seeds)
    for p in problems[:20]:
        print(f"  {p}")
    if problems:
        print(f"FAIL: {len(problems)} seeds differ from the ICLR rung m={m}")
        return 1
    print(f"OK: identical to the ICLR rung m={m}")
    return 0


def cmd_command(a: argparse.Namespace) -> int:
    """Print the serve command (self-hosted models) and the sweep command."""
    entry = model_entry(a.model)
    if entry["backend"] == "vllm":
        print("# 1. Serve the model (image " + load_protocol()["vllm_image"] + "):")
        print(shlex.join(serve_command(a.model)))
        print("# 2. Run the sweep:")
    else:
        print("# Run the sweep on AWS Bedrock (uses your AWS credentials):")
    print(shlex.join(sweep_command(a.model, Path(a.rung), Path(a.out), a.endpoint, a.api_key)))
    return 0


def cmd_check_data(a: argparse.Namespace) -> int:
    """Check a results folder against its MANIFEST checksums."""
    problems = check_data(Path(a.data))
    for p in problems:
        print(f"  {p}")
    print(f"FAIL: {len(problems)} problems" if problems else f"OK: {a.data} matches its MANIFEST")
    return 1 if problems else 0


def cmd_report(a: argparse.Namespace) -> int:
    """Summarize result rows next to the published values."""
    print(report([Path(p) for p in a.rows]))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    p = argparse.ArgumentParser(prog="horn-repro", description=(__doc__ or "").split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("models", help="list the models of the ICLR run").set_defaults(func=cmd_models)
    pr = sub.add_parser("render", help="render a rung and verify it")
    g = pr.add_mutually_exclusive_group(required=True)
    g.add_argument("--model", help="render this model's rung (its m)")
    g.add_argument("--m", type=int, help="render this chain length")
    pr.add_argument("--seeds", default=None, help="default: the protocol's seeds (100-199)")
    pr.add_argument("--out", required=True)
    pr.set_defaults(func=cmd_render)
    pv = sub.add_parser("verify", help="compare a rendered rung with the recorded digests")
    pv.add_argument("rung")
    pv.add_argument("--m", type=int, required=True)
    pv.add_argument("--seeds", default=None)
    pv.set_defaults(func=cmd_verify)
    pc = sub.add_parser("command", help="print the serve and sweep commands for a model")
    pc.add_argument("--model", required=True)
    pc.add_argument("--rung", required=True)
    pc.add_argument("--out", required=True, help="rows file the sweep writes")
    pc.add_argument("--endpoint", default=None, help="vLLM base URL (default http://127.0.0.1:8000/v1)")
    pc.add_argument("--api-key", default=None)
    pc.set_defaults(func=cmd_command)
    pd = sub.add_parser("check-data", help="check a results folder against its MANIFEST")
    pd.add_argument("data")
    pd.set_defaults(func=cmd_check_data)
    prep = sub.add_parser("report", help="summarize rows next to the published values")
    prep.add_argument("rows", nargs="+")
    prep.set_defaults(func=cmd_report)
    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())

