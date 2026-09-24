"""Command-line entry points for ``python -m smolbench.deduction.lean.cli``.

Lean-verifying commands need ``lean_interact``, ``elan``/``lake``, and
``SMOLBENCH_MATHLIB_ROOT``; lazy ``cmd_replay``/``cmd_filter`` imports and
``runner._default_verifier()`` keep other commands usable without them.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

from .corpus import iter_with_proof, metadata, replay_passing_path
from .runner import (
    DEFAULT_DOJO_TIMEOUT,
    NEVER_MEASURED_VERDICTS,
    analyze_rows,
    jsonl_line,
    load_sweep_config,
    model_totals,
    new_run_id,
    reject_superseded_rows,
    results_root,
    run_cell,
    sweep,
    write_jsonl,
)


def cmd_metadata(_: argparse.Namespace) -> int:
    """Print the benchmark's `metadata.json` as indented JSON; always returns 0.

    Parameters
    ----------
    _ : argparse.Namespace

    Returns
    -------
    int
        0.

    Raises
    ------
    FileNotFoundError
        Unbootstrapped dataset.
    """
    print(json.dumps(metadata(), indent=2))
    return 0


def cmd_build_derivation_index(_: argparse.Namespace) -> int:
    """Write the trace-based derivation sidecar for the active corpus; returns 0.

    ``hint:3`` closures read this index so that a traced theorem's edges are
    the premises its proof used, not a text scan of its statement. Without
    the sidecar the index is rebuilt in memory on every process start, which
    re-reads ``train.json``.

    Parameters
    ----------
    _ : argparse.Namespace

    Returns
    -------
    int
        0.
    """
    from .premises import write_derivation_index

    path = write_derivation_index()
    n = len(json.loads(path.read_text()))
    print(f"wrote {path} ({n} traced theorems)")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List theorems with traced tactics in a ``(kind, split)`` slice; returns 0.

    ``--limit`` caps printing, not the reported total.

    Parameters
    ----------
    args : argparse.Namespace

    Returns
    -------
    int
        0.
    """
    items = list(iter_with_proof(args.kind, args.split))
    print(f"# {len(items)} theorems with traced tactics in {args.kind}/{args.split}")
    for t in items[: args.limit]:
        print(f"  {t.full_name}\t({len(t.traced_tactics)} tactics)\t{t.file_path}")
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    """Replay ground-truth tactics through a Lean REPL session for a sample of theorems.

    Requires ``lean_interact``. ``--full-name`` bypasses seeded sampling.

    Parameters
    ----------
    args : argparse.Namespace

    Returns
    -------
    int
        2 for no theorem, 0 for all successes, else 1.
    """
    # ``verify`` needs lean_interact; defer it so other commands import.
    from .verify import replay_ground_truth

    pool = list(iter_with_proof(args.kind, args.split))
    rng = random.Random(args.seed)

    if args.full_name:
        targets = [t for t in pool if t.full_name == args.full_name]
        if not targets:
            print(f"theorem not found: {args.full_name}", file=sys.stderr)
            return 2
    else:
        # Short proofs make smoke replays faster and likelier to pass.
        max_len = args.max_tactics
        candidates = [t for t in pool if 1 <= len(t.traced_tactics) <= max_len]
        targets = rng.sample(candidates, min(args.n, len(candidates)))

    n_ok = 0
    for i, t in enumerate(targets, 1):
        t0 = time.monotonic()
        result = replay_ground_truth(t, timeout=args.timeout)
        dt = time.monotonic() - t0
        ok = result.verdict == "success"
        n_ok += int(ok)
        marker = "OK " if ok else "FAIL"
        print(
            f"[{i}/{len(targets)}] {marker} {result.verdict:<10} "
            f"{result.tactics_applied}/{result.tactics_total} tac  {dt:>6.1f}s  "
            f"{t.full_name}",
            flush=True,
        )
        if result.error:
            print(f"           err: {error_summary(result.error, 200)}", flush=True)

    print(f"\n{n_ok}/{len(targets)} succeeded")
    return 0 if n_ok == len(targets) else 1


def error_summary(text: str, limit: int = 300) -> str:
    """One-line summary of a verifier error: its first three non-empty lines.

    A REPL-level failure's first line is the bare header ``ReplError: REPL error:
    Lean error:``; the message that explains it is on the lines after, so a
    first-line-only summary hid every such cause behind one string.
    """
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return " | ".join(lines[:3])[:limit]


def cmd_filter(args: argparse.Namespace) -> int:
    """Replay every theorem with traced tactics; persist a passing list to JSONL.

    Requires ``lean_interact``. Flush ``replay_passing_path`` after each result
    so interruption loses at most one theorem; ``--fresh`` deletes it and
    ``--limit 0`` has no cap.

    Parameters
    ----------
    args : argparse.Namespace

    Returns
    -------
    int
        0.
    """
    # ``verify`` needs lean_interact; defer it for other commands.
    from .verify import replay_ground_truth

    pool = list(iter_with_proof(args.kind, args.split))
    if args.limit > 0:
        pool = pool[: args.limit]

    out_path = replay_passing_path(args.kind, args.split)

    done: dict[str, str] = {}
    if out_path.exists() and not args.fresh:
        for line in out_path.open():
            rec = json.loads(line)
            done[rec["full_name"]] = rec["verdict"]
        print(f"resume: {len(done)} already recorded in {out_path.name}", flush=True)

    if args.fresh and out_path.exists():
        out_path.unlink()
        done = {}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_total = len(pool)
    n_pass = sum(1 for v in done.values() if v == "success")
    n_fail = sum(1 for v in done.values() if v != "success")

    with out_path.open("a") as f:
        for t in pool:
            if t.full_name in done:
                continue
            t0 = time.monotonic()
            r = replay_ground_truth(t, timeout=args.timeout)
            ms = int((time.monotonic() - t0) * 1000)
            rec = {
                "full_name": t.full_name,
                "file_path": t.file_path,
                "n_tactics": len(t.traced_tactics),
                "verdict": r.verdict,
                "wall_ms": ms,
            }
            if r.error:
                rec["error"] = error_summary(r.error)
            f.write(jsonl_line(rec))
            f.flush()

            if r.verdict == "success":
                n_pass += 1
            else:
                n_fail += 1
            done[t.full_name] = r.verdict
            n_done = len(done)
            print(
                f"[{n_done}/{n_total}] {r.verdict:<14} "
                f"({n_pass} pass / {n_fail} fail)  {ms/1000:>5.1f}s  {t.full_name}",
                flush=True,
            )

    print(f"\n{n_pass} pass / {n_fail} fail / {n_total} total")
    print(f"output: {out_path}")
    return 0


def cmd_run_cell(args: argparse.Namespace) -> int:
    """Run one (theorem, k, rung) cell with N replicates and write a JSONL row file.

    Requires ``lean_interact`` through ``runner.run_cell``. ``--k -1`` is the
    last step, ``context.validate`` validates rungs, replicate ``i`` uses seed
    ``--seed + i``, and output is under ``results_root()/runs/``.

    Parameters
    ----------
    args : argparse.Namespace

    Returns
    -------
    int
        2 for bad theorem/rung, 0 for all successes, else 1.
    """
    pool = list(iter_with_proof(args.kind, args.split))
    matches = [t for t in pool if t.full_name == args.full_name]
    if not matches:
        print(f"theorem not found: {args.full_name}", file=sys.stderr)
        return 2
    theorem = matches[0]

    k = len(theorem.traced_tactics) - 1 if args.k == -1 else args.k

    from .context import validate as validate_rung

    chain_str, _, level_str = args.rung.partition(":")
    try:
        level = int(level_str)
    except ValueError:
        print(f"bad level in --rung {args.rung!r}", file=sys.stderr)
        return 2
    try:
        validate_rung(chain_str, level)  # type: ignore[arg-type]
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    out_path = results_root() / "runs" / f"{new_run_id()}.jsonl"
    rows = list(
        run_cell(
            provider=args.provider,
            model=args.model,
            theorem=theorem,
            k=k,
            chain=chain_str,
            level=level,
            n_replicates=args.n_replicates,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            dojo_timeout=args.timeout,
            seed=args.seed,
        )
    )
    n_written = write_jsonl(rows, out_path)
    n_ok = sum(1 for r in rows if r["verdict"] == "success")
    print(f"wrote {n_written} rows -> {out_path}", flush=True)
    print(f"verdicts: {n_ok}/{n_written} success")
    for r in rows:
        print(
            f"  replicate {r['replicate_idx']}: {r['verdict']:<14} "
            f"prompt_tok={r['prompt_tokens']} comp_tok={r['completion_tokens']} "
            f"gen={r['gen_ms']}ms verify={r['verify_ms']}ms"
        )
        if r["candidate_proof"]:
            preview = r["candidate_proof"].splitlines()
            for line in preview[:5]:
                print(f"    > {line}")
            if len(preview) > 5:
                print(f"    > ... ({len(preview)} lines total)")
        if r["lean_error"]:
            print(f"    lean_error: {error_summary(r['lean_error'], 200)}")
    return 0 if n_ok == n_written else 1


def _print_table_header(header: str) -> None:
    """Print a table header followed by its full-width rule."""
    print(header)
    print("-" * len(header))


def cmd_analyze(args: argparse.Namespace) -> int:
    """Aggregate a sweep JSONL into a pass-rate table by (rung, model).

    No Lean toolchain or writes. Reject superseded input and use
    ``runner.dedupe_cell_rows`` so tables count cells, not raw rows. ``trunc``
    marks unclosed ``<think>`` or reasoning-channel failures. pass@N uses the
    observed maximum replicate count so partial runs report honestly.

    Parameters
    ----------
    args : argparse.Namespace

    Returns
    -------
    int
        1 for no cell rows, else 0.
    """
    # Explicit paths can select retired JSONL, unlike filtered run-dir globs.
    reject_superseded_rows([args.path])
    cells, groups, sanity = analyze_rows(Path(args.path))
    n_sanity_pass, n_sanity_fail, n_sanity_skipped = sanity
    n_rows = sum(counter["n"] for counter in cells.values())

    if not cells:
        print(f"empty: no rows in {args.path}", file=sys.stderr)
        return 1

    print(f"# {n_rows} cells from {args.path}")
    print(
        f"# sanity gate: {n_sanity_pass} pass / {n_sanity_fail} fail"
        + (f" / {n_sanity_skipped} deferred" if n_sanity_skipped else "")
    )
    if n_sanity_fail:
        print(
            f"!! {n_sanity_fail} sanity-gate failures — investigate before trusting cell rates"
        )
    if n_sanity_skipped:
        print(
            f"# {n_sanity_skipped} sanity replays deferred (generation-only sweep); "
            "run the verification pass before trusting cell rates"
        )
    print()

    from .runner import _rung_sort_key, slug_model

    def sort_key(kv):
        return _rung_sort_key(kv[0][0]), kv[0][1]

    models_in_data = sorted({m for (_, m) in cells.keys()})
    rungs_in_data = sorted({r for (r, _) in cells.keys()}, key=_rung_sort_key)

    print("# rate per rung × model")
    bar_w = 30
    for model in models_in_data:
        print(f"\n  {slug_model(model)}:")
        for rung in rungs_in_data:
            c = cells.get((rung, model))
            if not c or not c["n"]:
                continue
            rate = c["success"] / c["n"]
            filled = int(round(rate * bar_w))
            meter = "█" * filled + "░" * (bar_w - filled)
            print(f"    {rung:<8} {meter} {rate:>5.1%}  ({c['success']}/{c['n']})")

    print()
    print(
        "# pass/N omits never-measured rows (missing data, not failures; "
        "see NEVER_MEASURED_VERDICTS), which the rplf and exc columns count"
    )
    header = (
        f"{'rung':<10} {'model':<36} {'pass':>5}/{'N':<4} "
        f"{'rate':>6} {'lerr':>5} {'incp':>5} {'gvup':>5} {'tmout':>5} "
        f"{'rplf':>5} {'exc':>4} {'noans':>5} {'unvf':>5} "
        f"{'avg_in':>7} {'avg_out':>7} {'avg_s':>6} {'trunc':>6}"
    )
    _print_table_header(header)

    for (rung, model), c in sorted(cells.items(), key=sort_key):
        n = c["n"]
        scored = n - sum(c[v] for v in NEVER_MEASURED_VERDICTS)
        rate = c["success"] / scored if scored else 0
        avg_in = c["tok_in"] / n if n else 0
        avg_out = c["tok_out"] / n if n else 0
        avg_s = c["ms"] / n / 1000 if n else 0
        print(
            f"{rung:<10} {model:<36} {c['success']:>5}/{scored:<4} "
            f"{rate:>6.1%} {c['lean_error']:>5} {c['incomplete']:>5} "
            f"{c['given_up']:>5} {c['timeout']:>5} "
            f"{c['replay_failed']:>5} {c['exception']:>4} "
            f"{c['no_answer']:>5} {c['unverified']:>5} "
            f"{avg_in:>7.0f} {avg_out:>7.0f} {avg_s:>6.1f} {c['trunc']:>6}"
        )

    print("\n# per-model totals (N excludes never-measured rows)")
    for model, m in sorted(model_totals(cells).items()):
        scored = m["n"] - sum(m.get(v, 0) for v in NEVER_MEASURED_VERDICTS)
        rate = m["success"] / scored if scored else 0
        print(
            f"  {model:<36}  {m['success']:>4}/{scored:<4}  {rate:>6.1%}  "
            f"({m['tok_in']:,} in / {m['tok_out']:,} out tokens)"
        )

    # Skip pass@N for one replicate because it duplicates success rate; use observed N.
    n_max_replicates = max((len(vs) for vs in groups.values()), default=1)
    if n_max_replicates > 1:
        passn_cells: dict[tuple[str, str], dict[str, int]] = {}
        for (model, rung, _theorem_id, _k), verdicts in groups.items():
            pc = passn_cells.setdefault((rung, model), {"groups": 0, "pass": 0})
            pc["groups"] += 1
            if "success" in verdicts:
                pc["pass"] += 1

        print(f"\n# pass@N per rung × model (N={n_max_replicates})")
        header2 = f"{'rung':<10} {'model':<36} {'pass':>5}/{'grp':<4} {'rate':>6}"
        _print_table_header(header2)
        for (rung, model), pc in sorted(passn_cells.items(), key=sort_key):
            rate = pc["pass"] / pc["groups"] if pc["groups"] else 0
            print(
                f"{rung:<10} {model:<36} {pc['pass']:>5}/{pc['groups']:<4} {rate:>6.1%}"
            )

        print("\n# pass@N per-model totals")
        by_model_passn: dict[str, dict[str, int]] = {}
        for (_rung, model), pc in passn_cells.items():
            total = by_model_passn.setdefault(model, {"groups": 0, "pass": 0})
            total["groups"] += pc["groups"]
            total["pass"] += pc["pass"]
        for model, m in sorted(by_model_passn.items()):
            rate = m["pass"] / m["groups"] if m["groups"] else 0
            print(f"  {model:<36}  {m['pass']:>4}/{m['groups']:<4}  {rate:>6.1%}")

    return 0


def cmd_run_sweep(args: argparse.Namespace) -> int:
    """Run a YAML-described sweep with resumability; requires `lean_interact`.

    ``load_sweep_config`` is shared with ``run_study.py`` so schemas cannot
    drift; it rejects non-mappings before a mid-sweep ``AttributeError``.

    Parameters
    ----------
    args : argparse.Namespace

    Returns
    -------
    int
        Exit status.

    Raises
    ------
    FileNotFoundError
        Unreadable config.
    ValueError
        Invalid config structure.
    yaml.YAMLError
        Invalid YAML.
    """
    # No provenance sidecar exists here to record a config-file digest.
    cfg, _ = load_sweep_config(args.config)
    run_name = cfg.get("run_name") or new_run_id()
    run_dir = Path(args.out) if args.out else results_root() / "runs" / run_name
    n = sweep(cfg, run_dir, resume=not args.fresh)
    return 0 if n >= 0 else 1


def _add_split_args(parser: argparse.ArgumentParser) -> None:
    """Add the shared corpus-family and partition options to `parser`.

    Centralization prevents inconsistent corpus schemas.

    Parameters
    ----------
    parser : argparse.ArgumentParser

    Returns
    -------
    None
        Modified parser.
    """
    parser.add_argument("--kind", choices=["random"], default="random")
    parser.add_argument("--split", choices=["train", "val", "test"], default="val")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser: one required subcommand (``dest="cmd"``).

    ``func`` defaults allow ``main`` to dispatch without a name switch.
    """
    p = argparse.ArgumentParser(prog="python -m smolbench.deduction.lean.cli")
    sub = p.add_subparsers(required=True, dest="cmd")

    p_meta = sub.add_parser("metadata", help="print benchmark metadata.json")
    p_meta.set_defaults(func=cmd_metadata)

    p_didx = sub.add_parser(
        "build-derivation-index",
        help="write <data_root>/derivation_index.json from the traced splits",
    )
    p_didx.set_defaults(func=cmd_build_derivation_index)

    p_list = sub.add_parser("list", help="list theorems in a split")
    _add_split_args(p_list)
    p_list.add_argument("--limit", type=int, default=10)
    p_list.set_defaults(func=cmd_list)

    p_replay = sub.add_parser(
        "replay", help="replay ground-truth tactics via a Lean REPL session"
    )
    _add_split_args(p_replay)
    p_replay.add_argument(
        "-n", type=int, default=5, help="number of theorems to replay"
    )
    p_replay.add_argument("--seed", type=int, default=0)
    p_replay.add_argument("--max-tactics", type=int, default=5)
    # Share 600 with run-cell; names persist in sweep YAML and manifest.json.
    p_replay.add_argument("--timeout", type=int, default=DEFAULT_DOJO_TIMEOUT)
    p_replay.add_argument(
        "--full-name", default=None, help="replay this specific theorem"
    )
    p_replay.set_defaults(func=cmd_replay)

    p_filter = sub.add_parser(
        "filter", help="replay every traced theorem; persist pass/fail list"
    )
    _add_split_args(p_filter)
    p_filter.add_argument(
        "--limit", type=int, default=0, help="cap number of theorems (0 = no cap)"
    )
    # Filter uses 300, not 600: hundreds of stalled replays magnify worst-case runtime.
    # See `test_dojo_timeout_has_one_default_across_all_three_entry_points`.
    p_filter.add_argument("--timeout", type=int, default=300)
    p_filter.add_argument(
        "--fresh", action="store_true", help="delete existing JSONL and start over"
    )
    p_filter.set_defaults(func=cmd_filter)

    p_cell = sub.add_parser(
        "run-cell", help="run one (theorem,k,rung) cell with N replicates"
    )
    p_cell.add_argument("--full-name", required=True)
    _add_split_args(p_cell)
    p_cell.add_argument(
        "--k", type=int, default=-1, help="step index (default: last step = len-1)"
    )
    p_cell.add_argument(
        "--rung",
        default="stepk:1",
        help="context rung as <chain>:<level>, e.g. stepk:0..3 or hint:0..4",
    )
    p_cell.add_argument("--n-replicates", type=int, default=1)
    p_cell.add_argument(
        "--provider",
        default="ec2",
        choices=["aws", "ec2"],
    )
    p_cell.add_argument("--model", default="anthropic/claude-haiku-4.5")
    p_cell.add_argument("--temperature", type=float, default=0.7)
    p_cell.add_argument("--max-tokens", type=int, default=4096)
    # This library fallback stays 600, unlike filter's full-corpus 300.
    p_cell.add_argument("--timeout", type=int, default=DEFAULT_DOJO_TIMEOUT)
    p_cell.add_argument(
        "--seed",
        type=int,
        default=1776,
        help="base decoding seed; replicate i uses seed+i",
    )
    p_cell.set_defaults(func=cmd_run_cell)

    p_sweep = sub.add_parser(
        "run-sweep",
        help="run a YAML-described sweep across (theorem, k, rung, model, replicate)",
    )
    p_sweep.add_argument("--config", required=True, help="path to sweep YAML")
    p_sweep.add_argument(
        "--out", default=None, help="output run dir (default: results/runs/<run_name>/)"
    )
    p_sweep.add_argument(
        "--fresh", action="store_true", help="ignore existing JSONL; start from empty"
    )
    p_sweep.set_defaults(func=cmd_run_sweep)

    p_an = sub.add_parser(
        "analyze", help="aggregate a sweep JSONL into a (rung, model) pass-rate table"
    )
    p_an.add_argument(
        "path", help="path to sweep JSONL (e.g. <run_dir>/all_rows.jsonl)"
    )
    p_an.set_defaults(func=cmd_analyze)

    return p


def main(argv: list[str] | None = None) -> int:
    """Parse `argv` (`None` = ``sys.argv[1:]``) and return the subcommand's exit code.

    ``argparse`` exits before return for help or malformed commands.

    Parameters
    ----------
    argv : list[str] | None, optional

    Returns
    -------
    int
        Subcommand exit code.
    """
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
