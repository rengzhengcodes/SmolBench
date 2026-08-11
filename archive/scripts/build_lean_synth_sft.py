"""Build decontaminated SYNTHETIC Lean 4 SFT datasets (JSONL + manifest).

Companion to ``scripts/build_lean_sft.py`` (which builds the *real*
LeanDojo-train set): this script ingests an external synthetic corpus,
runs every candidate row through the content-level decontamination index
(`smolbench.deduction.lean.decontam.HoldoutIndex` -- statements, goal
states, tactic chains, (state, tactic) pairs; not just names), renders the
survivors in the eval's wire format, subsamples to a seeded cap, and
writes a JSONL + committed manifest.

Arms (``--arm``):

- ``goedel`` -- `Goedel-LM/SFT_dataset_v2 <https://huggingface.co/datasets/
  Goedel-LM/Goedel-Prover-V2>`_ (1.74M rows, Apache-2.0, compiler-verified;
  statements autoformalized from competition problems). Each row's theorem
  declaration is converted to a pseudo initial tactic state (binders as
  hypotheses, conclusion behind ``⊢``) and rendered ``stepk:1``-shaped at
  ``k=0``; the target is the whole tactic proof. The chain-of-thought
  "proof plan" in the source rows is stripped -- the eval's SYSTEM prompt
  demands bare tactic lines.
- ``leannavigator`` -- `LeanNavigator <https://zenodo.org/records/13989482>`_
  (state-graph traversal over mathlib4): a flat array of
  ``[tactic state, next tactic]`` pairs -- already exactly the eval's
  state->tactic cell shape. Being mathlib-derived by construction, this is
  the HIGH-leak-risk arm: eval goal states and tactic answers can appear
  verbatim, which is precisely what the K3 state and K4b pair keys drop.
- ``real`` -- re-filter the JSONL that ``build_lean_sft.py`` produced
  through the content-level keys. Its ``full_name`` holdout already
  guarantees no eval *theorem* is present; this pass additionally drops
  same-statement/different-name mathlib duplicates and any train row whose
  (state, tactic) answer pair coincides with an eval cell.

Subsampling: candidate rows are ranked by a seeded blake2b priority over
their source index (a uniform random sample without replacement that needs
no full-corpus shuffle), deduplicated, and processed in priority order
until ``--cap`` clean rows are emitted. Fully deterministic given
``(source snapshot, seed, cap)``.

Runs on the main 3.14 venv plus ``pyarrow`` for the ``goedel`` arm (the
snapshot is parquet); no Lean, no GPU, no ``datasets``:

    uv run --no-project --with pyarrow --python .venv/bin/python \
        scripts/build_lean_synth_sft.py --arm goedel
    .venv/bin/python scripts/build_lean_synth_sft.py --arm leannavigator
    .venv/bin/python scripts/build_lean_synth_sft.py --arm real
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.build_lean_sft import _fingerprint, _parse_spec  # noqa: E402
from smolbench.deduction.lean import prompt  # noqa: E402
from smolbench.deduction.lean.context import RenderedContext, extract_goal_only  # noqa: E402
from smolbench.deduction.lean.decontam import Hit, HoldoutIndex  # noqa: E402
from smolbench.deduction.lean.sft import DEFAULT_EVAL_SPECS  # noqa: E402

_DATA = _REPO_ROOT / "notebooks" / "lean" / "data"

#: Per-arm defaults: (source path, output JSONL, cap). ``cap=0`` = no cap --
#: the ``real`` arm keeps every clean row (build_lean_sft already sized it).
_ARM_DEFAULTS: dict[str, tuple[Path, Path, int]] = {
    "goedel": (
        _DATA / "synth" / "goedel_v2",
        _DATA / "sft" / "synth_goedel_v2_24k.jsonl",
        24_000,
    ),
    "leannavigator": (
        _DATA / "synth" / "leannavigator" / "leannavigator_dataset.json",
        _DATA / "sft" / "synth_leannavigator_24k.jsonl",
        24_000,
    ),
    "real": (
        _DATA / "sft" / "novel_premises_train_stepk1.jsonl",
        _DATA / "sft" / "novel_premises_train_stepk1_decontam.jsonl",
        0,
    ),
}


# ---------------------------------------------------------------------------
# Candidate rows (arm adapters normalize into this)
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    """One raw corpus row rendered to the eval wire format, plus provenance.

    The *content* decontamination facets (states, tactics, (state, tactic)
    pairs) are NOT stored here: they are derived from the rendered
    ``user``/``assistant`` by `_facets_from_rendered`, once, so the in-loop
    filter and the zero-leak gate check byte-identical facets and cannot
    drift (an earlier bug: a LeanNavigator "tactic" is sometimes a
    multi-line focus block whose inner lines reproduce an eval tactic chain
    -- invisible to a parser that treated the tactic as atomic, caught by
    the gate that split the rendered assistant into lines). Only the two
    facets that are NOT recoverable from the rendered text live here:
    ``name`` (K1) and ``statement`` (the K2 near-duplicate source).
    """

    #: Rendered chat triple (eval wire format).
    system: str
    user: str
    assistant: str
    #: Provenance recorded under the JSONL row's ``meta``.
    meta: dict
    #: Declaration name for the K1 name key (None for nameless state rows).
    name: Optional[str] = None
    #: Statement text for the K2 near-duplicate check (None to fall back to
    #: the rendered full-state block).
    statement: Optional[str] = None

    def to_json(self) -> dict:
        return {
            "system": self.system,
            "user": self.user,
            "assistant": self.assistant,
            "meta": self.meta,
        }


def render_state_user(state: str) -> str:
    """Render a tactic state in the eval's ``stepk:1`` user-prompt shape.

    Mirrors ``context._render_stepk_parts(theorem, k, 1)`` -- "Current goal"
    (goal block only) then "Full tactic state" -- and assembles through
    `prompt.build_user_prompt`, so a synthetic row's user turn is
    byte-compatible with what the eval runner sends at ``stepk:1``.
    """
    parts = [
        f"## Current goal\n```\n{extract_goal_only(state)}\n```",
        f"## Full tactic state\n```\n{state}\n```",
    ]
    return prompt.build_user_prompt(
        RenderedContext(chain="stepk", level=1, text="\n\n".join(parts))
    )


# ---------------------------------------------------------------------------
# Lean declaration -> pseudo initial tactic state (goedel arm)
# ---------------------------------------------------------------------------

_OPEN = {"(": ")", "{": "}", "[": "]", "⦃": "⦄", "⟨": "⟩"}
_CLOSE = set(_OPEN.values())

#: Name must not swallow a glued colon (``theorem foo: ∀ ...``): the colon
#: belongs to the signature, where the top-level scan below expects it.
_DECL_RE = re.compile(r"^\s*(?:theorem|lemma)\s+([^\s:]+)\s*(.*)$", re.DOTALL)


def decl_to_state(decl: str) -> Optional[tuple[str, str]]:
    """Convert ``theorem <name> <binders> : <goal>`` to ``(name, state)``.

    The initial tactic state of a theorem is its binders as hypotheses plus
    its conclusion behind ``⊢`` -- which is what the eval's ``stepk`` rungs
    show and what `HoldoutIndex` fingerprints. Converting the declaration
    (instead of matching its raw text) is what lets a synthetic restatement
    of an eval theorem collide with the eval's step-0 state.

    Parameters
    ----------
    decl : str
        The declaration with any ``:= by ...`` tail already removed.

    Returns
    -------
    (str, str) or None
        ``(theorem name, pretty-state text)`` -- hypothesis lines (one per
        binder group; instance binders without a ``:`` get an ``inst :``
        prefix, approximating Lean's ``inst✝``) followed by ``⊢ <goal>`` --
        or None when the signature does not scan (counted as
        ``parse_failures`` by the caller, never silently kept).
    """
    m = _DECL_RE.match(decl)
    if not m:
        return None
    name, rest = m.group(1), m.group(2)
    hyps: list[str] = []
    depth = 0
    group_start = -1
    i = 0
    while i < len(rest):
        ch = rest[i]
        if ch in _OPEN:
            if depth == 0:
                group_start = i
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
            if depth == 0 and group_start >= 0:
                inner = rest[group_start + 1 : i].strip()
                if inner:
                    hyps.append(inner if ":" in inner else f"inst : {inner}")
                group_start = -1
            elif depth < 0:
                return None
        elif depth == 0:
            if ch == ":":
                goal = rest[i + 1 :].strip()
                if not goal:
                    return None
                lines = [re.sub(r"\s+", " ", h) for h in hyps]
                lines.append(f"⊢ {goal}")
                return name, "\n".join(lines)
            if not ch.isspace():
                # Stray top-level token outside any binder group before the
                # colon (universe params, weird syntax) -> don't guess.
                return None
        i += 1
    return None


_FENCE_RE = re.compile(r"```(?:lean4|lean)\s*\n(.*?)```", re.DOTALL)
_HEADER_RE = re.compile(r"^\s*(import|set_option|open|--)\b")
_BY_SPLIT_RE = re.compile(r":=\s*by\b")
#: ``/- ... -/`` and ``/-- ... -/`` block comments -- the source rows carry
#: the informal problem as a doc comment right before ``theorem``. Non-greedy,
#: so it does not handle *nested* block comments (vanishingly rare here;
#: a row it garbles fails declaration parsing and is counted, not kept).
_BLOCK_COMMENT_RE = re.compile(r"/-.*?-/", re.DOTALL)


def _tactic_block(code: str) -> Optional[str]:
    """The dedented tactic block after the first top-level ``:= by``."""
    m = _BY_SPLIT_RE.search(code)
    if m is None:
        return None
    tail = code[m.end() :]
    lines = [ln for ln in tail.splitlines() if ln.strip()]
    if not lines:
        return None
    # Dedent to the block's own margin, preserving relative indentation
    # (nested `have ... := by` sub-blocks keep their structure).
    indents = [len(ln) - len(ln.lstrip()) for ln in lines if ln.strip()]
    margin = min(indents) if indents else 0
    return "\n".join(ln[margin:] if len(ln) >= margin else ln.strip() for ln in lines).strip()


def _parse_goedel(user: str, assistant: str, idx: int) -> Optional[Candidate]:
    """Adapt one Goedel-V2 chat row to a `Candidate` (None = unparseable)."""
    blocks = _FENCE_RE.findall(user)
    if not blocks:
        return None
    decl_src = _BLOCK_COMMENT_RE.sub("", blocks[0])
    decl_lines = [ln for ln in decl_src.splitlines() if ln.strip() and not _HEADER_RE.match(ln)]
    decl_full = "\n".join(decl_lines)
    m = _BY_SPLIT_RE.search(decl_full)
    if m is None:
        return None
    parsed = decl_to_state(decl_full[: m.start()])
    if parsed is None:
        return None
    name, state = parsed

    answers = _FENCE_RE.findall(assistant)
    if not answers:
        return None
    proof = _tactic_block(_BLOCK_COMMENT_RE.sub("", answers[-1]))
    if proof is None or "sorry" in proof:
        return None
    tactic_lines = [ln.strip() for ln in proof.splitlines() if ln.strip() and not ln.strip().startswith("--")]
    if not tactic_lines:
        return None

    return Candidate(
        system=prompt.SYSTEM,
        user=render_state_user(state),
        assistant=proof,
        meta={"arm": "goedel", "source": "Goedel-LM/SFT_dataset_v2", "source_index": idx, "decl_name": name},
        name=name,
        statement=state,
    )


# ---------------------------------------------------------------------------
# Arm iterators: yield (source_index, dedup_key, payload)
# ---------------------------------------------------------------------------


def _iter_goedel_raw(source: Path) -> Iterator[tuple[int, bytes, tuple]]:
    """Stream (index, dedup key, (user, assistant)) from the parquet snapshot.

    Dedup key = hash of the user turn: rows restating the same theorem have
    identical user content, so duplicates collapse before sampling.
    """
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise SystemExit(
            f"error: {exc}\nthe goedel arm reads parquet; run via\n"
            "  uv run --no-project --with pyarrow --python .venv/bin/python "
            "scripts/build_lean_synth_sft.py --arm goedel"
        )
    files = sorted((source / "data").glob("*.parquet"))
    if not files:
        raise SystemExit(f"no parquet files under {source}/data -- snapshot not downloaded?")
    idx = 0
    for f in files:
        pf = pq.ParquetFile(f)
        for batch in pf.iter_batches(batch_size=512, columns=["messages"]):
            for messages in batch.column("messages").to_pylist():
                user = assistant = None
                for msg in messages:
                    if msg["role"] == "user" and user is None:
                        user = msg["content"]
                    elif msg["role"] == "assistant":
                        assistant = msg["content"]
                if user and assistant:
                    key = hashlib.blake2b(user.encode(), digest_size=8).digest()
                    yield idx, key, (user, assistant)
                idx += 1


def _iter_json_array(path: Path, chunk: int = 1 << 20) -> Iterator:
    """Stream top-level elements of a (possibly huge) JSON array file.

    ``json.load`` of LeanNavigator's 2.7 GB array would need several times
    that in RAM; this walks it element-by-element with `raw_decode` over a
    sliding buffer instead, keeping memory at ~one chunk.
    """
    dec = json.JSONDecoder()
    with path.open(encoding="utf-8") as f:
        buf = f.read(chunk)
        i = buf.index("[") + 1
        buf = buf[i:]
        while True:
            buf = buf.lstrip(" \t\r\n,")
            if not buf:
                more = f.read(chunk)
                if not more:
                    return
                buf = more
                continue
            if buf[0] == "]":
                return
            try:
                obj, end = dec.raw_decode(buf)
            except json.JSONDecodeError:
                more = f.read(chunk)
                if not more:
                    raise
                buf += more
                continue
            yield obj
            buf = buf[end:]


def _iter_leannavigator_raw(source: Path) -> Iterator[tuple[int, bytes, tuple]]:
    """Stream (index, dedup key, (state, tactic)) pairs from the JSON array."""
    for idx, item in enumerate(_iter_json_array(source)):
        if not (isinstance(item, list) and len(item) == 2):
            continue
        state, tactic = item
        if not (isinstance(state, str) and isinstance(tactic, str) and state.strip() and tactic.strip()):
            continue
        key = hashlib.blake2b(f"{state}\x00{tactic}".encode(), digest_size=8).digest()
        yield idx, key, (state, tactic)


def _parse_leannavigator(state: str, tactic: str, idx: int) -> Candidate:
    """Adapt one LeanNavigator (state, tactic) pair to a `Candidate`."""
    state = state.strip()
    tactic = tactic.strip()
    return Candidate(
        system=prompt.SYSTEM,
        user=render_state_user(state),
        assistant=tactic,
        meta={"arm": "leannavigator", "source": "zenodo:13989482", "source_index": idx},
        statement=state,
    )


def _iter_real_raw(source: Path) -> Iterator[tuple[int, bytes, tuple]]:
    """Stream rows of an already-rendered SFT JSONL (the ``real`` arm)."""
    with source.open() as f:
        for idx, line in enumerate(f):
            rec = json.loads(line)
            key = hashlib.blake2b(rec["user"].encode(), digest_size=8).digest()
            yield idx, key, (rec,)


_STATE_BLOCK_RE = re.compile(r"## Full tactic state\n```\n(.*?)\n```", re.DOTALL)
_GOAL_BLOCK_RE = re.compile(r"## Current goal\n```\n(.*?)\n```", re.DOTALL)


def _facets_from_rendered(user: str, assistant: str) -> tuple[tuple, tuple, tuple]:
    """Recover (states, tactics, pairs) facets from a rendered chat row.

    Used both by the ``real`` arm (whose input is already-rendered JSONL)
    and by the zero-leak re-scan gate, which re-derives every emitted row's
    facets from the artifact itself rather than trusting builder bookkeeping.
    """
    states = tuple(
        dict.fromkeys(m.group(1) for m in (*(_STATE_BLOCK_RE.finditer(user)), *(_GOAL_BLOCK_RE.finditer(user))))
    )
    tactics = tuple(ln.strip() for ln in assistant.splitlines() if ln.strip() and not ln.strip().startswith("--"))
    pairs = tuple((s, tactics[0]) for s in states) if tactics else ()
    return states, tactics, pairs


def _parse_real(rec: dict, idx: int) -> Candidate:
    """Adapt one already-rendered real-set row to a `Candidate`."""
    states, _tactics, _pairs = _facets_from_rendered(rec["user"], rec["assistant"])
    meta = dict(rec.get("meta", {}))
    meta.setdefault("arm", "real")
    return Candidate(
        system=rec["system"],
        user=rec["user"],
        assistant=rec["assistant"],
        meta=meta,
        name=meta.get("full_name"),
        statement=states[0] if states else None,
    )


# ---------------------------------------------------------------------------
# Seeded priority sampling + the build loop
# ---------------------------------------------------------------------------


def _priority(seed: int, arm: str, idx: int) -> int:
    """Deterministic per-row sampling priority (uniform, order-free)."""
    return int.from_bytes(
        hashlib.blake2b(f"{seed}:{arm}:{idx}".encode(), digest_size=8).digest(), "big"
    )


@dataclass
class BuildStats:
    scanned: int = 0
    duplicates: int = 0
    pooled: int = 0
    processed: int = 0
    parse_failures: int = 0
    dropped: dict = field(default_factory=dict)
    emitted: int = 0
    mention_rows: int = 0
    mention_total: int = 0

    def record_hits(self, hits: list[Hit]) -> None:
        # One count per row, keyed by the FIRST (most specific) hit.
        self.dropped[hits[0].key] = self.dropped.get(hits[0].key, 0) + 1


def build(args: argparse.Namespace) -> tuple[Path, dict]:
    """Run one arm end-to-end; returns (manifest path, manifest dict)."""
    eval_specs = tuple(args.eval_spec) if args.eval_spec else DEFAULT_EVAL_SPECS
    index = HoldoutIndex.build(eval_specs)
    stats = BuildStats()

    raw_iters = {
        "goedel": _iter_goedel_raw,
        "leannavigator": _iter_leannavigator_raw,
        "real": _iter_real_raw,
    }
    parsers = {
        "goedel": lambda payload, i: _parse_goedel(*payload, i),
        "leannavigator": lambda payload, i: _parse_leannavigator(*payload, i),
        "real": lambda payload, i: _parse_real(*payload, i),
    }
    parse = parsers[args.arm]

    # Scan: dedupe, then either pool a seeded uniform sample (cap > 0) or
    # keep everything in source order (cap == 0, the `real` arm's default).
    seen: set[bytes] = set()
    pool: list[tuple[int, int, tuple]] = []  # (-priority) max-heap when capped
    ordered: list[tuple[int, tuple]] = []
    pool_size = args.cap * args.pool_factor if args.cap else 0
    for idx, key, payload in raw_iters[args.arm](args.source):
        if args.limit and stats.scanned >= args.limit:
            break
        stats.scanned += 1
        if key in seen:
            stats.duplicates += 1
            continue
        seen.add(key)
        if args.cap:
            prio = _priority(args.seed, args.arm, idx)
            if len(pool) < pool_size:
                heapq.heappush(pool, (-prio, idx, payload))
            elif prio < -pool[0][0]:
                heapq.heapreplace(pool, (-prio, idx, payload))
        else:
            ordered.append((idx, payload))
    del seen
    if args.cap:
        candidates = [(idx, payload) for negp, idx, payload in sorted(pool, reverse=True)]
    else:
        candidates = ordered
    stats.pooled = len(candidates)

    # Process in priority (or source) order: parse -> check -> emit until cap.
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for idx, payload in candidates:
            if args.cap and stats.emitted >= args.cap:
                break
            stats.processed += 1
            cand = parse(payload, idx)
            if cand is None:
                stats.parse_failures += 1
                continue
            # Derive the content facets from the RENDERED row via the same
            # helper the zero-leak gate uses, so the in-loop filter checks
            # byte-identical facets to the gate and the two cannot disagree.
            states, tactics, pairs = _facets_from_rendered(cand.user, cand.assistant)
            hits = index.check(
                name=cand.name,
                statement=cand.statement or (states[0] if states else None),
                states=states,
                tactics=tactics,
                pairs=pairs,
            )
            if hits:
                stats.record_hits(hits)
                continue
            mentions = index.count_name_mentions(cand.assistant)
            if mentions:
                stats.mention_rows += 1
                stats.mention_total += mentions
                cand.meta["holdout_name_mentions"] = mentions
            f.write(json.dumps(cand.to_json()) + "\n")
            stats.emitted += 1

    if args.cap and stats.emitted < args.cap:
        print(
            f"WARNING: emitted {stats.emitted} < cap {args.cap}; the priority pool "
            f"(factor {args.pool_factor}) was exhausted -- rerun with a larger --pool-factor",
            file=sys.stderr,
        )

    # Zero-leak gate: re-derive every emitted row's facets from the written
    # artifact and re-check them -- independent of the loop's bookkeeping.
    leaks = 0
    with args.out.open() as f:
        for line in f:
            rec = json.loads(line)
            states, tactics, pairs = _facets_from_rendered(rec["user"], rec["assistant"])
            if index.check(
                statement=states[0] if states else None,
                states=states,
                tactics=tactics,
                pairs=pairs,
            ):
                leaks += 1
    if leaks:
        print(f"FATAL: zero-leak re-scan found {leaks} leaking row(s) in {args.out}", file=sys.stderr)
        raise SystemExit(1)

    manifest = {
        "config": {
            "arm": args.arm,
            "source": str(args.source),
            "cap": args.cap,
            "pool_factor": args.pool_factor,
            "seed": args.seed,
            "limit": args.limit,
            "eval_specs": [list(s) for s in eval_specs],
        },
        "stats": {
            "scanned": stats.scanned,
            "duplicates": stats.duplicates,
            "pooled": stats.pooled,
            "processed": stats.processed,
            "parse_failures": stats.parse_failures,
            "dropped": dict(sorted(stats.dropped.items())),
            "dropped_total": sum(stats.dropped.values()),
            "emitted": stats.emitted,
            "holdout_name_mention_rows": stats.mention_rows,
            "holdout_name_mentions_total": stats.mention_total,
        },
        "decontamination": {
            "holdout_size": len(index.names),
            "holdout_fingerprint": _fingerprint(index.names),
            "index": index.stats(),
            "zero_leak_rescan": "passed",
        },
        "output_jsonl": args.out.name,
    }
    manifest_path = args.out.with_name(args.out.stem + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest_path, manifest


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arm", required=True, choices=sorted(_ARM_DEFAULTS))
    p.add_argument("--source", type=Path, default=None, help="corpus path (default: per --arm)")
    p.add_argument("--out", type=Path, default=None, help="output JSONL (default: per --arm)")
    p.add_argument("--cap", type=int, default=None, help="clean rows to emit; 0 = keep all (default: per --arm)")
    p.add_argument("--pool-factor", type=int, default=3, help="sampling pool = cap * this (drop-rate headroom)")
    p.add_argument("--seed", type=int, default=1776)
    p.add_argument("--limit", type=int, default=0, help="debug: stop scanning after N raw rows (0 = all)")
    p.add_argument(
        "--eval-spec",
        type=_parse_spec,
        action="append",
        default=None,
        help="kind:split to hold out (repeatable); default novel_premises:val + novel_premises:test",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    src_default, out_default, cap_default = _ARM_DEFAULTS[args.arm]
    args.source = args.source or src_default
    args.out = args.out or out_default
    args.cap = cap_default if args.cap is None else args.cap
    if not args.source.exists():
        print(f"error: source {args.source} not found -- see module docstring for downloads", file=sys.stderr)
        return 1

    manifest_path, manifest = build(args)
    s = manifest["stats"]
    print(
        f"[{args.arm}] scanned {s['scanned']} ({s['duplicates']} dups) -> pool {s['pooled']}; "
        f"processed {s['processed']}: {s['parse_failures']} unparseable, "
        f"{s['dropped_total']} dropped {s['dropped']}, {s['emitted']} emitted "
        f"({s['holdout_name_mention_rows']} rows mention holdout names)\n"
        f"-> {args.out}\nmanifest -> {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
