"""Build the Lean3-relic REPAIR auxiliary SFT dataset (JSONL + manifest).

Companion to ``scripts/build_lean_sft.py`` / ``scripts/build_lean_synth_sft.py``:
those build "state -> clean Lean 4 tail" examples; this one builds "state +
a Lean-3-tainted PREVIOUS ATTEMPT (+ optionally a synthesized Lean error) ->
the same clean Lean 4 tail" examples, teaching the *repair* move directly
rather than hoping a model that already emits occasional Lean 3 relics
(see ``smolbench.deduction.lean.lean3``'s module docstring for the pilot
evidence) unlearns them purely from more clean-only supervision.

Source rows are read from an already-rendered, already-decontaminated real
SFT JSONL (default: ``scripts/build_lean_synth_sft.py --arm real``'s
output) -- their ``user``/``assistant``/``system`` are reused verbatim as
the base; nothing is re-rendered from the corpus here (contrast
``scripts/harvest_expert_iter.py``, which rebuilds prompts from scratch
because its rollouts came from a *live* sweep against corpus theorems, not
a pre-rendered file).

Per candidate row, in priority order (see `_priority`) until ``--limit``
corrupted rows are emitted:

1. `smolbench.deduction.lean.lean3.corrupt_tail` injects a seeded Lean-3
   relic mix into the row's ground-truth ``assistant`` tail. A tail with no
   applicable transform (`corrupt_tail` returns ``None``) is skipped and
   counted under ``skipped_no_transform`` -- not every ground-truth tail
   admits every relic kind (e.g. a tail with no ``fun``/``λ`` binder cannot
   be given a `binder-comma` relic).
2. A belt-and-suspenders content-decontamination re-check (see
   `_decontam_hits`) -- the source file is already decontaminated by
   `full_name`, but corruption embeds new derived text (the corrupted
   attempt) into the row's ``user`` turn, so this re-runs
   `smolbench.deduction.lean.decontam.HoldoutIndex.check` against BOTH the
   original ground-truth facets and the corrupted-attempt's facets before
   trusting the row is safe to emit.
3. Surviving rows are emitted via
   `smolbench.deduction.lean.lean3.build_repair_user` (attempt + a
   `smolbench.deduction.lean.lean3.synth_error`-synthesized error message),
   with the assistant target UNCHANGED (the clean ground-truth tail).

A further ``floor(limit * identity_frac)`` rows -- the priority-ordered
rows immediately following wherever the corrupted pass stopped -- are
emitted as IDENTITY examples instead: the row's own clean tail stands in as
its own "previous attempt" (no synthesized error), teaching the model that
an already-valid Lean 4 attempt should be echoed back unchanged rather than
"corrected" into something else. Without these, a repair-only-trained model
could learn to always rewrite its input, even when nothing was wrong.

Runs on the main 3.14 venv (no ``lean_dojo``, no torch/datasets):

    .venv/bin/python scripts/build_lean3_repair_sft.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.build_lean_sft import _fingerprint  # noqa: E402
from scripts.build_lean_synth_sft import _facets_from_rendered  # noqa: E402
from smolbench.deduction.lean import corpus  # noqa: E402
from smolbench.deduction.lean.decontam import Hit, HoldoutIndex  # noqa: E402
from smolbench.deduction.lean.lean3 import (  # noqa: E402
    ALIGN_ASSET_NAME,
    AlignMap,
    build_repair_user,
    corrupt_tail,
    find_relics,
    synth_error,
)

#: Extracts the previous-attempt fenced block `build_repair_user` writes,
#: straight back out of an already-assembled `user` string -- used ONLY by
#: `_self_check` (see its docstring) to re-derive what was actually written
#: to the row, rather than trusting this module's own in-loop bookkeeping.
#: Mirrors `_REPAIR_INSTRUCTIONS`' exact layout in
#: `smolbench.deduction.lean.lean3` (a fenced ```` ```lean ```` block headed
#: by ``"## Previous attempt"``) -- if that template ever changes, this
#: regex and it must change together.
_ATTEMPT_RE = re.compile(r"## Previous attempt\n```lean\n(.*?)\n```\n", re.DOTALL)

#: Extracts the synthesized error `build_repair_user` writes for corrupted
#: rows (absent on identity rows) -- `_self_check`'s companion to
#: `_ATTEMPT_RE`, under the same keep-in-sync-with-the-template contract.
_ERROR_RE = re.compile(r"Lean reported:\n```\n(.*?)\n```\n", re.DOTALL)


def _priority(seed: int, full_name: str, k: int) -> int:
    """Deterministic per-row sampling priority (uniform, order-free).

    Parameters
    ----------
    seed : int
        Build seed.
    full_name : str
        Source row's ``meta.full_name``.
    k : int
        Source row's ``meta.k``.

    Returns
    -------
    int
        A 64-bit unsigned integer from ``blake2b(f"{seed}:{full_name}:{k}")``.
        Sorting rows ascending by this value yields a seeded pseudo-random
        permutation that needs no full-corpus shuffle and is independent of
        the source file's own row order -- the same idiom
        ``scripts.build_lean_synth_sft._priority`` uses for its reservoir
        sample, specialized here to key on ``(full_name, k)`` (this
        dataset's natural per-example identity) instead of a raw source
        index.
    """
    return int.from_bytes(
        hashlib.blake2b(f"{seed}:{full_name}:{k}".encode(), digest_size=8).digest(), "big"
    )


def _row_rng(seed: int, full_name: str, k: int) -> random.Random:
    """The per-row `random.Random` `corrupt_tail` is seeded with.

    A FRESH `random.Random` per row (not one shared generator advanced
    row-by-row) keyed on the row's own identity, not its position in the
    priority-ordered scan -- so which relics a given theorem/step gets is
    reproducible regardless of `--limit`, dataset growth, or any future
    change to the priority-order sort, and regardless of how many earlier
    rows were skipped as decontam-dropped or no-transform before reaching
    it. See `_priority` for the sibling ordering hash this deliberately
    does NOT share entropy with (a row's selection order and its corruption
    outcome are independent concerns).

    Parameters
    ----------
    seed : int
        Build seed.
    full_name : str
        Source row's ``meta.full_name``.
    k : int
        Source row's ``meta.k``.

    Returns
    -------
    random.Random
        Seeded with the string ``f"{seed}:{full_name}:{k}"``.
    """
    return random.Random(f"{seed}:{full_name}:{k}")


def _read_rows(path: Path) -> list[dict]:
    """Read a rendered SFT JSONL (``{"system","user","assistant","meta"}`` per line)."""
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _decontam_hits(
    index: HoldoutIndex,
    *,
    full_name: str,
    user: str,
    assistant: str,
    corrupted: str | None = None,
) -> list[Hit]:
    """Content-decontamination check for one candidate repair row.

    Parameters
    ----------
    index : HoldoutIndex
        Built once by the caller (`build`) from `sft.DEFAULT_EVAL_SPECS`.
    full_name : str
        The source theorem's name (K1 check; defense in depth -- the
        source file is already `full_name`-held-out, so this should never
        actually fire, exactly as ``scripts.harvest_expert_iter.build_rows``
        treats its own equivalent redundant check).
    user : str
        The row's (unmodified, pre-repair-template) user turn -- supplies
        the K2/K3 state facets via `_facets_from_rendered`.
    assistant : str
        The row's ground-truth (clean) tail -- supplies the "bare correct
        tail" facets.
    corrupted : str, optional
        The Lean-3-corrupted attempt text, when checking a candidate
        CORRUPTED row (omit for an identity row, whose "attempt" IS
        `assistant`, already covered by the bare check).

    Returns
    -------
    list of Hit
        Every hit found, bare-tail facets first, then (if the bare check
        found nothing and `corrupted` was given) the corrupted-attempt's
        own facets -- checked independently because corruption is a
        deterministic TRANSFORM of the tail, not a re-render from the
        corpus, so it is not axiomatically impossible for a corrupted
        rewrite (e.g. `rename`, which substitutes a *different* dotted
        name) to newly coincide with a holdout facet the bare tail did not.
        Empty when the row is clean by both checks.
    """
    states, tactics, pairs = _facets_from_rendered(user, assistant)
    hits = index.check(
        name=full_name,
        statement=states[0] if states else None,
        states=states,
        tactics=tactics,
        pairs=pairs,
    )
    if hits or corrupted is None:
        return hits
    _states, c_tactics, c_pairs = _facets_from_rendered(user, corrupted)
    # `states` is unaffected by corruption (it comes from `user`, which
    # `corrupt_tail` never touches) -- re-derive only `tactics`/`pairs` from
    # the corrupted text; re-checking `states`/`statement`/`name` again
    # would just repeat work the bare check above already did.
    return index.check(tactics=c_tactics, pairs=c_pairs)


def _record_drop(stats: dict, hits: list[Hit]) -> None:
    """Count one dropped row under its first (most specific) `Hit.key`."""
    key = hits[0].key
    stats["decontam_dropped"][key] = stats["decontam_dropped"].get(key, 0) + 1


def _self_check(pairs: list[tuple[dict, dict]], *, identity: bool, align: AlignMap | None) -> None:
    """Re-derive and verify two invariants of every emitted row, from the artifact.

    Mirrors the "trust the written artifact, not the loop's own bookkeeping"
    spirit of ``scripts.build_lean_synth_sft.build``'s zero-leak re-scan:
    rather than trusting that the code above built each row correctly, this
    independently re-extracts what actually ended up in the row's ``user``
    string (via `_ATTEMPT_RE`) and re-checks it.

    Parameters
    ----------
    pairs : list of (new_row, source_row)
        Every emitted row of one kind (all-corrupted or all-identity),
        paired with the exact source row it was built from.
    identity : bool
        Whether `pairs` holds identity rows (skips the relic-detectability
        check below, which only applies to a Lean-3-tainted attempt) or
        corrupted rows.
    align : AlignMap, optional
        Forwarded to `find_relics` for the corrupted-row checks.

    Raises
    ------
    SystemExit
        With exit code 1 and a diagnostic message, on the FIRST violation
        of either invariant:

        - `new_row["assistant"]` differs from `source_row["assistant"]` --
          the ground-truth tail must never itself be mutated by this
          builder (only the ``user`` turn changes).
        - (corrupted rows only) the previous-attempt block re-extracted
          from `new_row["user"]` has no detectable relic under
          `find_relics` -- would mean `corrupt_tail`'s own post-condition
          (see its docstring) was somehow bypassed, or this builder's
          template assembly diverged from `_ATTEMPT_RE`'s expectation;
          either way, a row whose "error" the model can never observe a
          detector signal for must never reach the training set.
        - (corrupted rows only) the recorded error block re-extracted via
          `_ERROR_RE` differs from ``synth_error(find_relics(attempt,
          align))`` recomputed from the re-extracted attempt -- the
          recorded error must be exactly reproducible from the attempt
          text alone, so it can never (mis)name something the attempt does
          not verifiably contain (the 2026-07-12 review's
          false-`unknown identifier` finding, made structurally
          impossible).
        - (identity rows only) the user turn contains a ``Lean reported:``
          block -- identity rows must never carry a fabricated error about
          a correct attempt.
    """
    for new_row, src in pairs:
        full_name = new_row["meta"]["full_name"]
        if new_row["assistant"] != src["assistant"]:
            raise SystemExit(
                f"FATAL: self-check failed -- emitted row for {full_name!r} has an assistant "
                "that differs from its source row's assistant byte-for-byte"
            )
        if identity:
            if _ERROR_RE.search(new_row["user"]):
                raise SystemExit(
                    f"FATAL: self-check failed -- identity row for {full_name!r} carries a "
                    "'Lean reported:' block (a fabricated error about a correct attempt)"
                )
            continue
        m = _ATTEMPT_RE.search(new_row["user"])
        if m is None:
            raise SystemExit(
                f"FATAL: self-check failed -- could not re-extract a previous-attempt block "
                f"from the emitted row for {full_name!r}"
            )
        attempt = m.group(1)
        detected = find_relics(attempt, align)
        if not detected:
            raise SystemExit(
                f"FATAL: self-check failed -- the previous-attempt text for {full_name!r} has no "
                "detectable Lean 3 relic (corrupt_tail's shared-vocabulary post-condition should "
                "have made this impossible)"
            )
        err_m = _ERROR_RE.search(new_row["user"])
        if err_m is None or err_m.group(1) != synth_error(detected):
            raise SystemExit(
                f"FATAL: self-check failed -- the recorded error for {full_name!r} is missing or "
                "not reproducible as synth_error(find_relics(attempt)); the error text must be "
                "derivable from the attempt alone (never a phantom claim about it)"
            )


def build(args: argparse.Namespace, *, align: AlignMap, align_path: Path) -> tuple[Path, dict]:
    """Run the repair-dataset build end to end; write the output JSONL + manifest.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI args from `build_parser()`, with `args.dataset`/`args.out`
        already resolved to concrete paths by `main`.
    align : AlignMap
        Already-loaded Lean3<->Lean4 name map (see `main` -- loading is
        pulled out of this function so a missing asset can be reported and
        exit before any of this function's work happens).
    align_path : Path
        Where `align` was loaded from -- recorded (as a sha256) in the
        manifest for provenance, so a manifest reader can tell which align
        asset build produced a given repair dataset.

    Returns
    -------
    (manifest_path, manifest) : (Path, dict)
        Where the manifest was written (``args.out`` with a
        ``.manifest.json`` suffix, matching every other builder in this
        package) and its contents.

    Raises
    ------
    SystemExit
        Propagated from `_self_check` on an internal-consistency violation
        (see its docstring) -- distinguished from `main`'s user-facing
        "missing input" exit-1 paths, which print-and-return rather than
        raise: a self-check failure means THIS build's own bookkeeping is
        wrong, not that the caller passed bad arguments.
    """
    index = HoldoutIndex.build()  # DEFAULT_EVAL_SPECS -- see module docstring.
    rows = _read_rows(args.dataset)
    # Ascending priority = the seeded pseudo-random processing order (see
    # `_priority`); Python's sort is stable, and `rows`' own order is
    # already deterministic (file read order), so any (vanishingly
    # unlikely) priority collision still resolves deterministically.
    ordered = sorted(rows, key=lambda r: _priority(args.seed, r["meta"]["full_name"], r["meta"]["k"]))

    identity_target = int(args.limit * args.identity_frac)  # floor, per the spec.

    stats = {
        "source_rows": len(rows),
        "corrupted_emitted": 0,
        "identity_emitted": 0,
        "skipped_no_transform": 0,
        "decontam_dropped": {},
        "transform_histogram": {},
    }
    corrupted_pairs: list[tuple[dict, dict]] = []  # (new_row, source_row)
    identity_pairs: list[tuple[dict, dict]] = []

    idx = 0
    n = len(ordered)

    # Phase 1: corrupted rows, in priority order, until `--limit` or the
    # dataset is exhausted.
    while idx < n and len(corrupted_pairs) < args.limit:
        row = ordered[idx]
        idx += 1
        meta = row["meta"]
        full_name, k = meta["full_name"], meta["k"]

        rng = _row_rng(args.seed, full_name, k)
        result = corrupt_tail(row["assistant"], rng, align)
        if result is None:
            stats["skipped_no_transform"] += 1
            continue
        corrupted, injected = result

        hits = _decontam_hits(
            index, full_name=full_name, user=row["user"], assistant=row["assistant"], corrupted=corrupted
        )
        if hits:
            _record_drop(stats, hits)
            continue

        # Synthesize the error from what the DETECTOR reports on the final
        # corrupted text -- not from `injected` -- so the recorded message
        # describes something verifiably present in the attempt (the
        # detector is the truth anchor; `injected` is corroborated intent).
        # An adversarially-confirmed review finding (2026-07-12) showed the
        # injected-first variant emitting `unknown identifier 'X'` for
        # valid Lean 4 names when a no-op rename claimed a phantom relic.
        error = synth_error(find_relics(corrupted, align))
        # Unique-preserving (not deduped-then-sorted): a row that applied
        # both `rename` and `trailing` records both kinds once each, in
        # application order -- readable provenance without inflating a row
        # that happened to apply `trailing` to 3 lines into 3 histogram
        # entries for the same row (that granularity lives in
        # `find_relics`'s own per-relic list, not this summary).
        transform_kinds = list(dict.fromkeys(r.kind for r in injected))
        new_row = {
            "system": row["system"],
            "user": build_repair_user(row["user"], corrupted, error),
            "assistant": row["assistant"],
            "meta": {**meta, "repair": {"identity": False, "transforms": transform_kinds}},
        }
        corrupted_pairs.append((new_row, row))
        for kind in transform_kinds:
            stats["transform_histogram"][kind] = stats["transform_histogram"].get(kind, 0) + 1

    # Phase 2: identity rows -- the NEXT `identity_target` priority rows
    # after wherever phase 1 stopped (disjoint from the corrupted set by
    # construction, since `idx` only ever advances).
    while idx < n and len(identity_pairs) < identity_target:
        row = ordered[idx]
        idx += 1
        meta = row["meta"]
        full_name = meta["full_name"]

        hits = _decontam_hits(index, full_name=full_name, user=row["user"], assistant=row["assistant"])
        if hits:
            _record_drop(stats, hits)
            continue

        new_row = {
            "system": row["system"],
            "user": build_repair_user(row["user"], row["assistant"], None),
            "assistant": row["assistant"],
            "meta": {**meta, "repair": {"identity": True}},
        }
        identity_pairs.append((new_row, row))

    _self_check(corrupted_pairs, identity=False, align=align)
    _self_check(identity_pairs, identity=True, align=align)

    stats["corrupted_emitted"] = len(corrupted_pairs)
    stats["identity_emitted"] = len(identity_pairs)
    stats["decontam_dropped"] = dict(sorted(stats["decontam_dropped"].items()))
    stats["transform_histogram"] = dict(sorted(stats["transform_histogram"].items()))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        # Corrupted rows first, then identity rows -- a fixed, readable
        # block order; any shuffling for training curriculum purposes is
        # the trainer/recipe-wiring work package's job, not this builder's.
        for new_row, _src in (*corrupted_pairs, *identity_pairs):
            f.write(json.dumps(new_row, ensure_ascii=False) + "\n")

    manifest = {
        "config": {
            "dataset": str(args.dataset),
            "out": str(args.out),
            "limit": args.limit,
            "identity_frac": args.identity_frac,
            "seed": args.seed,
            "align_asset": {"path": str(align_path), "sha256": hashlib.sha256(align_path.read_bytes()).hexdigest()},
        },
        "stats": {
            **stats,
            "decontam_dropped_total": sum(stats["decontam_dropped"].values()),
        },
        "decontamination": {
            "holdout_size": len(index.names),
            "holdout_fingerprint": _fingerprint(index.names),
            "index": index.stats(),
        },
        "output_jsonl": args.out.name,
    }
    manifest_path = args.out.with_name(args.out.stem + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest_path, manifest


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help="source rendered SFT JSONL (default: data_root().parent/sft/novel_premises_train_stepk1_decontam.jsonl)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output JSONL path (default: data_root().parent/sft/lean3_repair_stepk1_1k6.jsonl)",
    )
    p.add_argument("--limit", type=int, default=1600, help="corrupted rows to emit")
    p.add_argument("--identity-frac", type=float, default=0.10, help="identity rows, as a fraction of --limit")
    p.add_argument("--seed", type=int, default=1776)
    p.add_argument(
        "--align",
        type=Path,
        default=None,
        help="explicit Lean3 align asset path (default: data_root().parent/" + ALIGN_ASSET_NAME + ")",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # `.parent`: the sft/ dir and the align asset are SIBLINGS of the
    # gitignored leandojo_benchmark_4/ dataset dir that `data_root()` names
    # (`notebooks/lean/data/sft/`, `notebooks/lean/data/lean3_align.json.gz`)
    # -- the committed-sidecar layout `corpus.replay_passing_path` documents.
    root = corpus.data_root().parent
    args.dataset = args.dataset or root / "sft" / "novel_premises_train_stepk1_decontam.jsonl"
    args.out = args.out or root / "sft" / "lean3_repair_stepk1_1k6.jsonl"

    if not args.dataset.exists():
        print(
            f"error: source dataset {args.dataset} not found -- build it first: "
            "scripts/build_lean_synth_sft.py --arm real (see notebooks/lean/README.md)",
            file=sys.stderr,
        )
        return 1

    align_path = args.align if args.align is not None else root / ALIGN_ASSET_NAME
    align = AlignMap.load(align_path)
    if align is None:
        print(
            f"error: Lean3 align asset not found at {align_path} -- build it first: "
            "scripts/build_lean3_align_map.py",
            file=sys.stderr,
        )
        return 1

    manifest_path, manifest = build(args, align=align, align_path=align_path)
    s = manifest["stats"]
    print(
        f"[{args.dataset.name}] {s['source_rows']} source rows -> {s['corrupted_emitted']} corrupted + "
        f"{s['identity_emitted']} identity emitted ({s['skipped_no_transform']} skipped-no-transform, "
        f"{s['decontam_dropped_total']} decontam-dropped {s['decontam_dropped']})\n"
        f"transforms: {s['transform_histogram']}\n"
        f"-> {args.out}\nmanifest -> {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
