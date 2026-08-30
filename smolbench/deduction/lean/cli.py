"""Command-line entry points: `python -m smolbench.deduction.lean.cli <subcommand>`.

Dependency split: `replay`, `filter`, `run-cell` and `run-sweep` verify proofs
against Lean and so need `.verify`, which requires `lean_dojo` (the `lean`
extra, plus elan and a traced-repo cache at runtime); every other subcommand
needs none of that. To keep the split real, `.verify` is imported lazily inside
`cmd_replay` and `cmd_filter`, and `run-cell`/`run-sweep` reach it only through
`runner._default_verifier()`.
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
    SANITY_FAILURE_VERDICTS, new_run_id, regenerate_run_artifacts,
    reject_superseded_rows, results_root, run_cell, sweep, write_jsonl,
)


def cmd_metadata(_: argparse.Namespace) -> int:
    """Print the benchmark's `metadata.json` as indented JSON; always returns 0.

    Raises
    ------
    FileNotFoundError
        From `corpus.metadata` when the dataset is not bootstrapped.
    """
    print(json.dumps(metadata(), indent=2))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List theorems with traced tactics in a ``(kind, split)`` slice; returns 0.

    ``--limit`` caps only how many are PRINTED; the reported total is the
    full matching count.
    """
    items = list(iter_with_proof(args.kind, args.split))
    print(f"# {len(items)} theorems with traced tactics in {args.kind}/{args.split}")
    for t in items[: args.limit]:
        print(f"  {t.full_name}\t({len(t.traced_tactics)} tactics)\t{t.file_path}")
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    """Replay ground-truth tactics through Dojo for a sample of theorems.

    Requires `lean_dojo` (opens real Dojo sessions). ``--full-name`` replays that
    theorem instead of sampling ``-n`` from the ``--max-tactics`` filtered pool
    under ``--seed``; ``--timeout`` is per-theorem seconds.

    Returns
    -------
    int
        2 if ``--full-name`` matches no theorem, 0 if every replay verdict is
        ``"success"``, else 1.
    """
    # Local import: `.verify` requires `lean_dojo`, so deferring it here
    # keeps every OTHER subcommand importable without lean_dojo installed.
    from .verify import replay_ground_truth

    pool = list(iter_with_proof(args.kind, args.split))
    rng = random.Random(args.seed)

    if args.full_name:
        targets = [t for t in pool if t.full_name == args.full_name]
        if not targets:
            print(f"theorem not found: {args.full_name}", file=sys.stderr)
            return 2
    else:
        # Biases toward short proofs for the smoke: faster, likelier to pass.
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
            err = result.error.strip().splitlines()[0][:200]
            print(f"           err: {err}", flush=True)

    print(f"\n{n_ok}/{len(targets)} succeeded")
    return 0 if n_ok == len(targets) else 1


def cmd_filter(args: argparse.Namespace) -> int:
    """Replay every theorem with traced tactics; persist a passing list to JSONL.

    Requires `lean_dojo`. Appends to `corpus.replay_passing_path(kind, split)`,
    flushing after each theorem and resuming by skipping theorems already
    recorded there, so an interrupt loses at most the in-flight theorem.
    ``--fresh`` deletes the sidecar; ``--limit 0`` means no cap. Always 0.
    """
    # Local import: see `cmd_replay`.
    from .verify import replay_ground_truth

    pool = list(iter_with_proof(args.kind, args.split))
    if args.limit > 0:
        pool = pool[: args.limit]

    out_path = replay_passing_path(args.kind, args.split)

    done: dict[str, str] = {}
    if out_path.exists() and not args.fresh:
        with out_path.open() as f:
            for line in f:
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
                rec["error"] = r.error.strip().splitlines()[0][:300]
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
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

    Requires `lean_dojo`, reached through `runner.run_cell`'s lazily-resolved
    default verifier. ``--k -1`` means the last step; ``--rung`` is
    ``<chain>:<level>``, validated via `context.validate`; ``--seed`` is the base
    decoding seed, replicate ``i`` using ``seed + i``. Writes one row per
    replicate to ``<results_root()>/runs/<new_run_id()>.jsonl``.

    Returns
    -------
    int
        2 if ``--full-name`` matches no theorem or ``--rung`` is malformed or
        out of range, 0 if every replicate verdict is ``"success"``, else 1.
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
    rows = list(run_cell(
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
    ))
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
            err = r["lean_error"].splitlines()[0][:200]
            print(f"    lean_error: {err}")
    return 0 if n_ok == n_written else 1


def cmd_prompt_stats(args: argparse.Namespace) -> int:
    """Render prompts for each (theorem, k=last, rung) and report token stats.

    No Lean toolchain needed. The pool is replay-passing theorems only
    (`corpus.iter_replay_passing`), filtered by ``--max-tactics`` and sub-sampled
    by ``--limit``/``--seed``; ``--rungs`` defaults to
    `context.IMPLEMENTED_RUNGS`. Tokens come from `tiktoken` ``cl100k_base`` with
    NO char-based fallback, unlike `context._count_tokens`, so a missing
    `tiktoken` surfaces as `ImportError`. A `render` exception counts as a render
    error and is skipped.

    Returns
    -------
    int
        1 on an empty pool, else 0.
    """
    import statistics as stats
    import tiktoken
    from .context import IMPLEMENTED_RUNGS, render
    from .corpus import iter_replay_passing

    enc = tiktoken.get_encoding("cl100k_base")
    pool = list(iter_replay_passing(args.kind, args.split))
    if args.max_tactics > 0:
        pool = [t for t in pool if 1 <= len(t.traced_tactics) <= args.max_tactics]
    if args.limit > 0 and len(pool) > args.limit:
        rng = random.Random(args.seed)
        pool = rng.sample(pool, args.limit)
    if not pool:
        print("empty pool", file=sys.stderr)
        return 1

    if args.rungs:
        rungs = args.rungs.split(",")
    else:
        rungs = [f"{c}:{l}" for c, l in IMPLEMENTED_RUNGS]

    by_rung: dict[str, list[int]] = {r: [] for r in rungs}
    n_render_err = 0
    for t in pool:
        k = len(t.traced_tactics) - 1
        for rung in rungs:
            chain, lvl = rung.split(":", 1)
            try:
                rc = render(t, k, chain, int(lvl))  # type: ignore[arg-type]
            except Exception:
                n_render_err += 1
                continue
            by_rung[rung].append(len(enc.encode(rc.text)))

    print(f"# {len(pool)} theorems, k=last_step")
    if n_render_err:
        print(f"# {n_render_err} render errors (skipped)")
    print(f"\n{'rung':<10} {'n':>4} {'min':>6} {'med':>6} {'mean':>7} {'p95':>6} {'max':>6}")
    print("-" * 50)
    for rung in rungs:
        counts = sorted(by_rung[rung])
        if not counts:
            print(f"{rung:<10} {0:>4}  (no successful renders)")
            continue
        p95 = counts[min(int(0.95 * len(counts)), len(counts) - 1)]
        print(
            f"{rung:<10} {len(counts):>4} {counts[0]:>6} {stats.median(counts):>6.0f} "
            f"{stats.mean(counts):>7.0f} {p95:>6} {counts[-1]:>6}"
        )
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Aggregate a sweep JSONL into a pass-rate table by (rung, model).

    Pure aggregation over ``path`` (a sweep's ``all_rows.jsonl`` or any file with
    the same row schema): no Lean toolchain, no Dojo session, no writes. The
    ``trunc`` column counts rows that opened a ``<think>`` block without closing
    it, or died in the reasoning channel. A pass@N table follows only when some
    cell recorded more than one replicate: a cell passes if ANY replicate
    verified, and N is the max replicate count seen IN THE DATA, not the sweep
    config, so mixed-replicate sweeps stay correct. `path` is checked against
    `runner.reject_superseded_rows` before it is opened.

    Returns
    -------
    int
        1 if `path` has no cell rows, else 0.
    """
    from collections import defaultdict

    cells: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {
            "n": 0, "success": 0, "lean_error": 0, "incomplete": 0,
            "given_up": 0, "replay_failed": 0, "exception": 0,
            "unverified": 0,
            "tok_in": 0, "tok_out": 0, "ms": 0, "trunc": 0,
        }
    )
    # Keyed on full cell identity (model, rung, theorem_id, k), not folded into
    # `cells`: pass@N asks "did ANY replicate of *this exact* (theorem, k)
    # succeed", which the (rung, model)-only `cells` aggregation has lost.
    groups: dict[tuple[str, str, str, int], list[str]] = defaultdict(list)

    n_rows = 0
    n_sanity_pass = 0
    n_sanity_fail = 0
    n_sanity_skipped = 0
    # Unlike the run-directory globs elsewhere in this file, `path` is
    # unfiltered upstream -- the likeliest place to point at a retired
    # `all_rows_SUPERSEDED-<stamp>.jsonl` (runner.RETIRED_MARKERS).
    reject_superseded_rows([args.path])
    with open(args.path) as f:
        for line in f:
            r = json.loads(line)
            kind = r.get("kind", "cell")
            if kind == "sanity":
                if r.get("verdict") == "success":
                    n_sanity_pass += 1
                elif r.get("verdict") in SANITY_FAILURE_VERDICTS:
                    n_sanity_fail += 1
                else:
                    # "skipped": a generation-only sweep deferred the replay.
                    n_sanity_skipped += 1
                continue
            n_rows += 1
            key = (r.get("rung", "?"), r.get("model", "?"))
            c = cells[key]
            c["n"] += 1
            v = r.get("verdict", "exception")
            if v in c:
                c[v] += 1
            else:
                c["exception"] += 1
            c["tok_in"] += r.get("prompt_tokens", 0)
            c["tok_out"] += r.get("completion_tokens", 0)
            c["ms"] += r.get("gen_ms", 0) + r.get("verify_ms", 0)

            # Truncation smell: a reasoning model cut off mid-<think> emits
            # no tactic block, which otherwise looks like an ordinary
            # `incomplete`/`given_up` verdict; counting it separately keeps
            # a wave of truncations from reading as reasoning dead ends.
            # `raw_response` is the field runner.py writes; `content` is a
            # fallback for row variants using the provider SDK's key name.
            raw_text = r.get("raw_response", "") or r.get("content", "")
            unclosed_think_in_raw = "<think>" in raw_text and "</think>" not in raw_text
            # Parser-path case: under a vLLM --reasoning-parser the server
            # splits <think> into `reasoning_content`, so a generation that
            # died in the think channel leaves `raw_response` EMPTY rather
            # than unclosed, and the check above reads 0. Deliberately tests
            # `raw_response` alone, not the `content`-fallback `raw_text`,
            # matching the row schema runner.py writes in that mode.
            died_in_reasoning_channel = bool(r.get("reasoning_content")) and not (r.get("raw_response") or "").strip()
            if unclosed_think_in_raw or died_in_reasoning_channel:
                c["trunc"] += 1

            group_key = (
                r.get("model", "?"), r.get("rung", "?"),
                r.get("theorem_id", "?"), r.get("k", -1),
            )
            groups[group_key].append(v)

    if not cells:
        print(f"empty: no rows in {args.path}", file=sys.stderr)
        return 1

    print(f"# {n_rows} cells from {args.path}")
    print(
        f"# sanity gate: {n_sanity_pass} pass / {n_sanity_fail} fail"
        + (f" / {n_sanity_skipped} deferred" if n_sanity_skipped else "")
    )
    if n_sanity_fail:
        print(f"!! {n_sanity_fail} sanity-gate failures — investigate before trusting cell rates")
    if n_sanity_skipped:
        print(
            f"# {n_sanity_skipped} sanity replays deferred (generation-only sweep); "
            "run the verification pass before trusting cell rates"
        )
    print()

    from .runner import _rung_sort_key, slug_model
    sort_key = lambda kv: (_rung_sort_key(kv[0][0]), kv[0][1])

    # ---- Per-model rung ladder (ASCII bars) ----
    by_model_rung: dict[tuple[str, str], dict[str, int]] = {(m, r): cells[(r, m)] for (r, m) in cells.keys()}
    models_in_data = sorted({m for (_, m) in cells.keys()})
    rungs_in_data = sorted({r for (r, _) in cells.keys()}, key=_rung_sort_key)

    print("# rate per rung × model")
    bar_w = 30
    for model in models_in_data:
        print(f"\n  {slug_model(model)}:")
        for rung in rungs_in_data:
            c = by_model_rung.get((model, rung))
            if not c or not c["n"]:
                continue
            rate = c["success"] / c["n"]
            filled = int(round(rate * bar_w))
            bar = "█" * filled + "░" * (bar_w - filled)
            print(f"    {rung:<8} {bar} {rate:>5.1%}  ({c['success']}/{c['n']})")

    print()
    header = (
        f"{'rung':<10} {'model':<36} {'pass':>5}/{'N':<4} "
        f"{'rate':>6} {'lerr':>5} {'incp':>5} {'gvup':>5} {'rplf':>5} {'exc':>4} {'unvf':>5} "
        f"{'avg_in':>7} {'avg_out':>7} {'avg_s':>6} {'trunc':>6}"
    )
    print(header)
    print("-" * len(header))

    for (rung, model), c in sorted(cells.items(), key=sort_key):
        n = c["n"]
        rate = c["success"] / n if n else 0
        avg_in = c["tok_in"] / n if n else 0
        avg_out = c["tok_out"] / n if n else 0
        avg_s = c["ms"] / n / 1000 if n else 0
        print(
            f"{rung:<10} {model:<36} {c['success']:>5}/{n:<4} "
            f"{rate:>6.1%} {c['lean_error']:>5} {c['incomplete']:>5} "
            f"{c['given_up']:>5} {c['replay_failed']:>5} {c['exception']:>4} {c['unverified']:>5} "
            f"{avg_in:>7.0f} {avg_out:>7.0f} {avg_s:>6.1f} {c['trunc']:>6}"
        )

    # Per-model rollup
    print("\n# per-model totals")
    by_model: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, "success": 0, "tok_in": 0, "tok_out": 0}
    )
    for (_, model), c in cells.items():
        by_model[model]["n"] += c["n"]
        by_model[model]["success"] += c["success"]
        by_model[model]["tok_in"] += c["tok_in"]
        by_model[model]["tok_out"] += c["tok_out"]
    for model, m in sorted(by_model.items()):
        rate = m["success"] / m["n"] if m["n"] else 0
        print(f"  {model:<36}  {m['success']:>4}/{m['n']:<4}  {rate:>6.1%}  "
              f"({m['tok_in']:,} in / {m['tok_out']:,} out tokens)")

    # ---- pass@N; skipped at n_replicates==1, where it would duplicate the
    # plain success rate above. N comes from the data, not the sweep config. ----
    n_max_replicates = max((len(vs) for vs in groups.values()), default=1)
    if n_max_replicates > 1:
        passn_cells: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: {"groups": 0, "pass": 0}
        )
        for (model, rung, _theorem_id, _k), verdicts in groups.items():
            pc = passn_cells[(rung, model)]
            pc["groups"] += 1
            if "success" in verdicts:
                pc["pass"] += 1

        print(f"\n# pass@N per rung × model (N={n_max_replicates})")
        header2 = f"{'rung':<10} {'model':<36} {'pass':>5}/{'grp':<4} {'rate':>6}"
        print(header2)
        print("-" * len(header2))
        for (rung, model), pc in sorted(passn_cells.items(), key=sort_key):
            rate = pc["pass"] / pc["groups"] if pc["groups"] else 0
            print(f"{rung:<10} {model:<36} {pc['pass']:>5}/{pc['groups']:<4} {rate:>6.1%}")

        print("\n# pass@N per-model totals")
        by_model_passn: dict[str, dict[str, int]] = defaultdict(
            lambda: {"groups": 0, "pass": 0}
        )
        for (_rung, model), pc in passn_cells.items():
            by_model_passn[model]["groups"] += pc["groups"]
            by_model_passn[model]["pass"] += pc["pass"]
        for model, m in sorted(by_model_passn.items()):
            rate = m["pass"] / m["groups"] if m["groups"] else 0
            print(f"  {model:<36}  {m['pass']:>4}/{m['groups']:<4}  {rate:>6.1%}")

    return 0


def cmd_run_sweep(args: argparse.Namespace) -> int:
    """Run a YAML-described sweep with resumability; requires `lean_dojo`.

    ``--config`` is `yaml.safe_load`ed into `runner.sweep`'s `config`; ``--out``
    defaults to ``results_root()/runs/<config["run_name"] or new_run_id()>``;
    ``--fresh`` passes ``resume=False``. All side effects (output layout, resume,
    manifest/analysis writing) belong to `runner.sweep`.

    Returns
    -------
    int
        0 in practice — `sweep` never returns a negative count.
    """
    import yaml
    cfg = yaml.safe_load(Path(args.config).read_text())
    run_name = cfg.get("run_name") or new_run_id()
    run_dir = Path(args.out) if args.out else results_root() / "runs" / run_name
    n = sweep(cfg, run_dir, resume=not args.fresh)
    return 0 if n >= 0 else 1


def cmd_compare(args: argparse.Namespace) -> int:
    """For one model, compare two rungs cell-by-cell on a run dir.

    Pure JSONL comparison over ``<run_dir>/all_rows.jsonl``: no Lean toolchain,
    no writes. Reports regressions (rung_a ✓ → rung_b ✘) and, unless
    ``--regressions-only``, improvements; compares only replicate
    ``--replicate``.

    Returns
    -------
    int
        2 if ``all_rows.jsonl`` is missing, else 0.
    """
    run_dir = Path(args.run_dir)
    all_rows = run_dir / "all_rows.jsonl"
    if not all_rows.exists():
        print(f"no all_rows.jsonl under {run_dir}", file=sys.stderr)
        return 2

    by_thm: dict[str, dict[str, dict]] = {}
    for line in all_rows.open():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("kind") != "cell":
            continue
        if r.get("model") != args.model:
            continue
        if r.get("rung") not in (args.rung_a, args.rung_b):
            continue
        if r.get("replicate_idx", 0) != args.replicate:
            continue
        by_thm.setdefault(r["theorem_id"], {})[r["rung"]] = r

    regressions: list[tuple[str, dict, dict]] = []
    improvements: list[tuple[str, dict, dict]] = []
    both_pass = 0
    both_fail = 0
    only_a = 0
    only_b = 0
    for t, d in by_thm.items():
        a = d.get(args.rung_a)
        b = d.get(args.rung_b)
        if a is None or b is None:
            if a is None: only_b += 1
            if b is None: only_a += 1
            continue
        a_ok = a.get("verdict") == "success"
        b_ok = b.get("verdict") == "success"
        if a_ok and b_ok:
            both_pass += 1
        elif a_ok and not b_ok:
            regressions.append((t, a, b))
        elif b_ok and not a_ok:
            improvements.append((t, a, b))
        else:
            both_fail += 1

    print(f"# {args.model}  rung {args.rung_a} vs {args.rung_b}  (replicate {args.replicate})")
    print(f"  both pass:      {both_pass}")
    print(f"  both fail:      {both_fail}")
    print(f"  regressions ({args.rung_a} ✓ → {args.rung_b} ✘): {len(regressions)}")
    print(f"  improvements ({args.rung_a} ✘ → {args.rung_b} ✓): {len(improvements)}")
    if only_a:
        print(f"  only-{args.rung_a}-present: {only_a}  (likely trivial-skipped at {args.rung_b})")
    if only_b:
        print(f"  only-{args.rung_b}-present: {only_b}  (likely trivial-skipped at {args.rung_a})")

    def _dump(label: str, items: list[tuple[str, dict, dict]]) -> None:
        """Print one labeled section of ``(theorem_id, row_a, row_b)`` triples.

        Prints nothing at all, not even `label`, when `items` is empty.
        """
        if not items:
            return
        print(f"\n== {label} ==")
        for t, a, b in items:
            d_tok = b.get("prompt_tokens", 0) - a.get("prompt_tokens", 0)
            print(f"\n## {t}   k={a.get('k')}  Δtokens={d_tok:+d}")
            print(f"   ground-truth tail: {a.get('ground_truth_remaining', '')[:160]}")
            print(f"\n   {args.rung_a}  →  {a.get('verdict')}")
            print(f"     candidate: {(a.get('candidate_proof') or '')[:240]}")
            if a.get("lean_error"):
                print(f"     lean_error: {a['lean_error'].splitlines()[0][:200]}")
            print(f"\n   {args.rung_b}  →  {b.get('verdict')}")
            print(f"     candidate: {(b.get('candidate_proof') or '')[:240]}")
            if b.get("lean_error"):
                print(f"     lean_error: {b['lean_error'].splitlines()[0][:200]}")

    _dump(f"REGRESSIONS — context-pollution evidence ({args.rung_a} → {args.rung_b})", regressions)
    if not args.regressions_only:
        _dump(f"IMPROVEMENTS — extra context helped ({args.rung_a} → {args.rung_b})", improvements)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Print a theorem's summary.md, or list theorems with pass counts.

    Reads only ``summary.md``/``outputs/*.jsonl``; no Lean toolchain. Listing
    mode (no ``theorem`` argument) tallies rates by re-scanning each theorem's
    ``outputs/*.jsonl``, not its possibly-stale `summary.md`.

    Returns
    -------
    int
        2 if ``<run_dir>/theorems`` is missing, 1 if a named theorem has no
        ``summary.md``, else 0.
    """
    from .runner import slug_theorem
    run_dir = Path(args.run_dir)
    theorems_dir = run_dir / "theorems"
    if not theorems_dir.exists():
        print(f"no theorems dir under {run_dir}", file=sys.stderr)
        return 2

    if args.theorem:
        slug = slug_theorem(args.theorem)
        summary = theorems_dir / slug / "summary.md"
        if not summary.exists():
            print(f"not found: {summary}", file=sys.stderr)
            return 1
        print(summary.read_text())
        return 0

    rows: list[tuple[str, int, int]] = []
    for d in sorted(theorems_dir.iterdir()):
        if not d.is_dir():
            continue
        out_dir = d / "outputs"
        n_total = 0
        n_ok = 0
        if out_dir.exists():
            jsonl_files = sorted(out_dir.glob("*.jsonl"))
            reject_superseded_rows(jsonl_files)
            for f in jsonl_files:
                with f.open() as fh:
                    for line in fh:
                        try:
                            r = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        n_total += 1
                        if r.get("verdict") == "success":
                            n_ok += 1
        rows.append((d.name, n_ok, n_total))

    print(f"# {len(rows)} theorems in {run_dir}\n")
    for name, n_ok, n_total in rows:
        rate = f"{n_ok / n_total:>5.1%}" if n_total else "  -  "
        print(f"  {name:<60}  {n_ok:>3}/{n_total:<3}  {rate}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Regenerate analysis.txt + per-theorem summary.md from a run dir's durable artifacts.

    Delegates to `runner.regenerate_run_artifacts`, which reads only
    `all_rows.jsonl` and each theorem's `meta.json`/`outputs/*.jsonl` (no Lean
    toolchain) and OVERWRITES `analysis.txt` and every `theorems/*/summary.md`.

    Returns
    -------
    int
        2 if ``all_rows.jsonl`` is missing, else 0.
    """
    run_dir = Path(args.run_dir)
    if not (run_dir / "all_rows.jsonl").exists():
        print(f"not a run dir (no all_rows.jsonl): {run_dir}", file=sys.stderr)
        return 2
    regenerate_run_artifacts(run_dir)
    print(f"regenerated artifacts in {run_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser: one required subcommand (``dest="cmd"``).

    Each subparser sets a `func` default pointing at its `cmd_*` handler, so
    `main` dispatches via ``args.func(args)`` with no name switch.
    """
    p = argparse.ArgumentParser(prog="python -m smolbench.deduction.lean.cli")
    sub = p.add_subparsers(required=True, dest="cmd")

    p_meta = sub.add_parser("metadata", help="print benchmark metadata.json")
    p_meta.set_defaults(func=cmd_metadata)

    p_list = sub.add_parser("list", help="list theorems in a split")
    p_list.add_argument("--kind", choices=["random", "novel_premises"], default="random")
    p_list.add_argument("--split", choices=["train", "val", "test"], default="val")
    p_list.add_argument("--limit", type=int, default=10)
    p_list.set_defaults(func=cmd_list)

    p_replay = sub.add_parser("replay", help="replay ground-truth tactics in Dojo")
    p_replay.add_argument("--kind", choices=["random", "novel_premises"], default="random")
    p_replay.add_argument("--split", choices=["train", "val", "test"], default="val")
    p_replay.add_argument("-n", type=int, default=5, help="number of theorems to replay")
    p_replay.add_argument("--seed", type=int, default=0)
    p_replay.add_argument("--max-tactics", type=int, default=5)
    p_replay.add_argument("--timeout", type=int, default=600)
    p_replay.add_argument("--full-name", default=None, help="replay this specific theorem")
    p_replay.set_defaults(func=cmd_replay)

    p_filter = sub.add_parser("filter", help="replay every traced theorem; persist pass/fail list")
    p_filter.add_argument("--kind", choices=["random", "novel_premises"], default="random")
    p_filter.add_argument("--split", choices=["train", "val", "test"], default="val")
    p_filter.add_argument("--limit", type=int, default=0, help="cap number of theorems (0 = no cap)")
    p_filter.add_argument("--timeout", type=int, default=300)
    p_filter.add_argument("--fresh", action="store_true", help="delete existing JSONL and start over")
    p_filter.set_defaults(func=cmd_filter)

    p_cell = sub.add_parser("run-cell", help="run one (theorem,k,rung) cell with N replicates")
    p_cell.add_argument("--full-name", required=True)
    p_cell.add_argument("--kind", choices=["random", "novel_premises"], default="random")
    p_cell.add_argument("--split", choices=["train", "val", "test"], default="val")
    p_cell.add_argument("--k", type=int, default=-1, help="step index (default: last step = len-1)")
    p_cell.add_argument(
        "--rung",
        default="stepk:1",
        help="context rung as <chain>:<level>, e.g. stepk:0..3 or hint:0..4",
    )
    p_cell.add_argument("--n-replicates", type=int, default=1)
    p_cell.add_argument(
        "--provider", default="primeintellect",
        choices=["openrouter", "primeintellect", "aws", "ec2"],
    )
    p_cell.add_argument("--model", default="anthropic/claude-haiku-4.5")
    p_cell.add_argument("--temperature", type=float, default=0.7)
    p_cell.add_argument("--max-tokens", type=int, default=4096)
    p_cell.add_argument("--timeout", type=int, default=600)
    p_cell.add_argument(
        "--seed", type=int, default=1776,
        help="base decoding seed; replicate i uses seed+i",
    )
    p_cell.set_defaults(func=cmd_run_cell)

    p_sweep = sub.add_parser("run-sweep", help="run a YAML-described sweep across (theorem, k, rung, model, replicate)")
    p_sweep.add_argument("--config", required=True, help="path to sweep YAML")
    p_sweep.add_argument("--out", default=None, help="output run dir (default: results/runs/<run_name>/)")
    p_sweep.add_argument("--fresh", action="store_true", help="ignore existing JSONL; start from empty")
    p_sweep.set_defaults(func=cmd_run_sweep)

    p_an = sub.add_parser("analyze", help="aggregate a sweep JSONL into a (rung, model) pass-rate table")
    p_an.add_argument("path", help="path to sweep JSONL (e.g. <run_dir>/all_rows.jsonl)")
    p_an.set_defaults(func=cmd_analyze)

    p_rep = sub.add_parser("report", help="regenerate analysis.txt + per-theorem summary.md in a run dir")
    p_rep.add_argument("run_dir", help="path to a run directory")
    p_rep.set_defaults(func=cmd_report)

    p_show = sub.add_parser("show", help="print a theorem's summary.md, or list theorems with pass counts")
    p_show.add_argument("run_dir", help="path to a run directory (e.g. results/runs/latest)")
    p_show.add_argument("theorem", nargs="?", default=None, help="theorem full_name (omit to list all)")
    p_show.set_defaults(func=cmd_show)

    p_cmp = sub.add_parser("compare", help="diff two rungs for one model: regressions + improvements")
    p_cmp.add_argument("run_dir", help="path to a run directory")
    p_cmp.add_argument("model", help="model identifier, e.g. 'anthropic/claude-sonnet-4.6'")
    p_cmp.add_argument("rung_a", help="baseline rung, e.g. 'hint:1'")
    p_cmp.add_argument("rung_b", help="comparison rung, e.g. 'hint:2'")
    p_cmp.add_argument("--replicate", type=int, default=0)
    p_cmp.add_argument("--regressions-only", action="store_true",
                       help="show only rung_a ✓ → rung_b ✘ cases")
    p_cmp.set_defaults(func=cmd_compare)

    p_ps = sub.add_parser("prompt-stats", help="token-count distribution of rendered prompts per rung")
    p_ps.add_argument("--kind", choices=["random", "novel_premises"], default="random")
    p_ps.add_argument("--split", choices=["train", "val", "test"], default="val")
    p_ps.add_argument("--limit", type=int, default=50)
    p_ps.add_argument("--max-tactics", type=int, default=5)
    p_ps.add_argument("--seed", type=int, default=0)
    p_ps.add_argument("--rungs", default=None, help="comma-separated rungs (default: all implemented)")
    p_ps.set_defaults(func=cmd_prompt_stats)

    return p


def main(argv: list[str] | None = None) -> int:
    """Parse `argv` (`None` = ``sys.argv[1:]``) and return the subcommand's exit code.

    `argparse` calls `sys.exit` on ``-h``, a missing/unknown subcommand, or
    malformed arguments, before this function returns.
    """
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
