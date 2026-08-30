"""Build a decontaminated Lean 4 SFT dataset from LeanDojo Benchmark 4.

Turns traced tactics into supervised fine-tuning pairs for the exact task the
``smolbench.deduction.lean`` eval scores: given the proof state at step ``k``,
emit the remaining Lean 4 tactics.

- **Prompt parity.** ``system``/``user`` are built with the *same* `prompt` /
  `context` code the eval runner uses -- no train/serve prompt skew.
- **Decontamination.** Eval theorems are held out by ``full_name``. The
  benchmark's ``random`` and ``novel_premises`` kinds partition one theorem pool
  two *different* ways, so a ``novel_premises/test`` theorem can appear in
  ``random/train``; the name exclusion closes that leak for any ``train_kind``.
  ``novel_premises/train`` additionally inherits premise-level decontamination.
- **Context rung.** ``stepk:1`` by default (full tactic state, no premise
  hints), so training never teaches the model to exploit the eval's
  answer-conditional ``hint`` rungs.
- **Target.** The ground-truth tail, unfenced (`tail_target`). At the default
  ``k_strategy="last"`` the tail is the single final tactic, exactly the cell
  the headline sweep scores (``k.strategy: last``).

Imports only `corpus`/`context`/`prompt`, never `verify`, so it stays importable
without ``lean_dojo``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

from . import context, corpus, prompt
from .context import Chain
from .corpus import BenchmarkTheorem, Split, SplitKind

#: Splits held out of training by default -- everything the eval can draw from:
#: ``novel_premises/test`` (headline slice) and ``novel_premises/val`` (pilot).
#: Held out at *whole-split* level; see `eval_holdout_names`.
DEFAULT_EVAL_SPECS: tuple[tuple[SplitKind, Split], ...] = (
    ("novel_premises", "val"),
    ("novel_premises", "test"),
)

#: Which step(s) ``k`` of a proof become training examples:
#: - ``"last"`` -- final step only (tail = one tactic); matches the headline
#:   sweep's ``k.strategy: last`` exactly.
#: - ``"all"`` -- every step ``0..len-1``; richest curriculum, but
#:   ~avg-proof-length examples per theorem.
#: - ``"sample"`` -- one uniformly-random (seeded) step per theorem, drawn from
#:   states throughout the proof.
KStrategy = str  # Literal["last", "all", "sample"]


@dataclass(frozen=True)
class SFTExample:
    """One supervised fine-tuning example (a chat triple + provenance)."""

    #: System turn -- `prompt.SYSTEM`, identical to the eval.
    system: str
    #: User turn -- rendered context + `prompt.INSTRUCTION`.
    user: str
    #: Assistant target -- the ground-truth tail as raw tactic lines.
    assistant: str
    #: Source theorem's fully-qualified name (provenance / dedup key).
    full_name: str
    #: 0-indexed proof step the context describes (see `context.render`).
    k: int
    #: Number of tactics in the tail (``len(traced_tactics) - k``).
    n_tail: int



def eval_holdout_names(eval_specs: Iterable[tuple[SplitKind, Split]]) -> set[str]:
    """Collect every theorem ``full_name`` in the given eval splits.

    Returns
    -------
    set of str
        Union over `corpus.load_split` -- the *whole* split, not
        `iter_replay_passing`, so the holdout needs no ``filter`` sidecar and is
        a strict superset of what a sweep can evaluate.
    """
    names: set[str] = set()
    for kind, split in eval_specs:
        for t in corpus.load_split(kind, split):
            names.add(t.full_name)
    return names


def tail_target(theorem: BenchmarkTheorem, k: int) -> str:
    """The ground-truth tail from step ``k`` as raw newline-joined tactics.

    Parameters
    ----------
    k : int
        0-indexed start step; ``0 <= k < len(traced_tactics)``.

    Returns
    -------
    str
        Stripped and *unfenced*, as `prompt.SYSTEM` asks for and
        `prompt.extract_tactic_block` parses back unchanged.
    """
    return "\n".join(t.tactic for t in theorem.traced_tactics[k:]).strip()


def _choose_ks(theorem: BenchmarkTheorem, k_strategy: KStrategy, rng: random.Random) -> list[int]:
    """Resolve which proof steps of `theorem` become training examples."""
    n = len(theorem.traced_tactics)
    if n == 0:
        return []
    if k_strategy == "last":
        return [n - 1]
    if k_strategy == "all":
        return list(range(n))
    if k_strategy == "sample":
        return [rng.randrange(n)]
    raise ValueError(f"unknown k_strategy {k_strategy!r}; expected last|all|sample")


def _train_pool(
    kind: SplitKind, split: Split, source: str
) -> Iterator[BenchmarkTheorem]:
    """Yield the training-theorem pool for ``(kind, split)``.

    ``source="with_proof"`` is every theorem with >=1 traced tactic;
    ``"replay_passing"`` needs the ``filter`` sidecar and is far smaller/slower
    but guarantees every target is a machine-verified proof. Any other value
    raises ``ValueError``.
    """
    if source == "with_proof":
        return corpus.iter_with_proof(kind, split)
    if source == "replay_passing":
        return corpus.iter_replay_passing(kind, split)
    raise ValueError(f"unknown source {source!r}; expected with_proof|replay_passing")


def iter_dataset(
    *,
    train_kind: SplitKind = "novel_premises",
    train_split: Split = "train",
    eval_specs: Iterable[tuple[SplitKind, Split]] = DEFAULT_EVAL_SPECS,
    extra_exclude: Iterable[str] = (),
    source: str = "with_proof",
    k_strategy: KStrategy = "last",
    chain: Chain = "stepk",
    level: int = 1,
    seed: int = 1776,
    stats: Optional[dict] = None,
) -> Iterator[SFTExample]:
    """Yield decontaminated `SFTExample`s (one per kept theorem, chosen ``k``).

    Every theorem whose ``full_name`` is in `eval_holdout_names(eval_specs)` or
    in `extra_exclude` is skipped *before* any example is emitted, so this can
    never leak an eval theorem into training. ``chain``/``level`` is the context
    rung passed to `context.render` (default ``stepk:1``).

    Parameters
    ----------
    seed : int
        Seeds the RNG for ``k_strategy="sample"`` only; ignored otherwise.
    stats : dict, optional
        If given, populated in place with ``pool``, ``dropped`` (excluded),
        ``theorems`` (emitted), ``examples``, and ``excluded`` (holdout size).
    """
    exclude = eval_holdout_names(eval_specs) | set(extra_exclude)
    rng = random.Random(seed)
    n_pool = n_dropped = n_theorems = n_examples = 0
    for theorem in _train_pool(train_kind, train_split, source):
        n_pool += 1
        if theorem.full_name in exclude:
            n_dropped += 1
            continue
        emitted_here = 0
        for k in _choose_ks(theorem, k_strategy, rng):
            target = tail_target(theorem, k)
            if not target:
                continue
            rendered = context.render(theorem, k, chain, level)
            yield SFTExample(
                system=prompt.SYSTEM,
                user=prompt.build_user_prompt(rendered),
                assistant=target,
                full_name=theorem.full_name,
                k=k,
                n_tail=len(theorem.traced_tactics) - k,
            )
            emitted_here += 1
            n_examples += 1
        if emitted_here:
            n_theorems += 1
    if stats is not None:
        stats.update(
            pool=n_pool,
            dropped=n_dropped,
            theorems=n_theorems,
            examples=n_examples,
            excluded=len(exclude),
        )
