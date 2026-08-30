"""Build a decontaminated Lean 4 SFT dataset from LeanDojo Benchmark 4.

This module turns the benchmark's *traced tactics* into supervised
fine-tuning pairs. These pairs LoRA-tune a model on the exact task the
``smolbench.deduction.lean`` eval scores: given the proof state at step
``k`` of a theorem, emit the remaining Lean 4 tactics.

Two properties make the dataset a faithful, honest training signal:

- **Prompt-format parity with the eval.** Each example's ``system`` /
  ``user`` text is built with the *same* `smolbench.deduction.lean.prompt`
  / `smolbench.deduction.lean.context` code the runner uses at eval time
  (`prompt.SYSTEM`, `prompt.build_user_prompt`, `context.render`). So the
  LoRA sees the identical wire format it will be evaluated under -- no
  train/serve prompt skew.
- **Decontamination.** Every theorem used in the eval is held out of the
  training pool by ``full_name`` (see `iter_dataset`). The benchmark's
  ``random`` and ``novel_premises`` kinds are two *different*
  partitionings of the same theorem pool, so a ``novel_premises/test``
  theorem can appear in ``random/train``. The explicit ``full_name``
  exclusion here removes that leak, regardless of which ``train_kind`` is
  used. A run trained on ``novel_premises/train`` also inherits that
  split's premise-level decontamination (test premises are
  under-represented in its train split).

Context rung
------------
Examples render at ``stepk:1`` by default: the full tactic state (goal +
hypotheses), with *no* premise hints. This is the canonical
state-to-tactic formulation used by neural theorem provers. It
deliberately avoids teaching the model to exploit the eval's
answer-conditional ``hint`` rungs, which leak the true premises. The eval
then measures how *added* context (the ``hint``/``noise`` rungs) moves a
model that was only ever trained on the bare state.

Target
------
The assistant target is the ground-truth *tail*: the tactics from step
``k`` to the end of the proof, rendered as raw newline-separated tactic
lines (no code fence). This matches what `prompt.SYSTEM` instructs the
model to produce, and what `prompt.extract_tactic_block` parses back out.
At the default ``k_strategy="last"``, the tail is the single final
tactic -- exactly the cell the headline sweep scores (``k.strategy: last``).

This module imports only the generation-side siblings (`corpus`,
`context`, `prompt`), never `verify`. So it stays importable without
``lean_dojo``; dataset construction needs no Lean.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

from . import context, corpus, prompt
from .context import Chain
from .corpus import BenchmarkTheorem, Split, SplitKind

#: Splits held out of training by default: everything the eval can draw
#: from. The headline slice is ``novel_premises/test``; ``novel_premises/val``
#: is the pilot slice. Both are excluded, so neither a pilot nor the
#: headline run can be trained on. This holds out the *whole-split* level
#: (every theorem in the split, via `corpus.load_split`), which is
#: stricter than the replay-passing subset the eval actually uses, and
#: needs no ``filter`` sidecar to compute.
DEFAULT_EVAL_SPECS: tuple[tuple[SplitKind, Split], ...] = (
    ("novel_premises", "val"),
    ("novel_premises", "test"),
)

#: How to pick which step(s) ``k`` of a proof become training examples.
#: - ``"last"`` -- only the final step (tail = one tactic); matches the
#:   headline sweep's ``k.strategy: last`` exactly.
#: - ``"all"`` -- every step ``0..len-1`` (tails of every length; the
#:   richest curriculum, but ~avg-proof-length examples per theorem).
#: - ``"sample"`` -- one uniformly-random step per theorem (seeded), a
#:   middle ground that keeps the dataset ~one example per theorem while
#:   exposing states from throughout the proof.
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

    Parameters
    ----------
    eval_specs : iterable of (kind, split)
        The ``(SplitKind, Split)`` pairs whose theorems must be held out of
        training -- typically `DEFAULT_EVAL_SPECS`.

    Returns
    -------
    set of str
        The union of ``full_name`` over `corpus.load_split(kind, split)` for
        each pair. Uses `load_split` (the whole split), not
        `iter_replay_passing`, so the holdout is independent of whether the
        ``filter`` sidecar has been generated yet, and strictly a superset
        of the theorems any sweep can evaluate.
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
    theorem : BenchmarkTheorem
        Source theorem.
    k : int
        0-indexed step the tail starts at; ``0 <= k < len(traced_tactics)``.

    Returns
    -------
    str
        ``"\\n".join(t.tactic for t in theorem.traced_tactics[k:])``,
        stripped. No code fence: `prompt.SYSTEM` tells the model to emit
        bare tactic lines, and `prompt.extract_tactic_block` returns the
        stripped text unchanged when no fence is present.
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

    ``source="with_proof"`` (default) uses `corpus.iter_with_proof`: every
    theorem LeanDojo traced at least one tactic for. ``source="replay_passing"``
    uses `corpus.iter_replay_passing`, restricted to theorems whose
    recorded ground truth actually replays in Dojo. This needs the
    ``filter`` sidecar, and is far smaller and slower to produce, but it
    guarantees each target is a machine-verified valid proof.
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
    """Yield decontaminated `SFTExample`s from the training pool.

    Every theorem whose ``full_name`` is in the eval holdout
    (`eval_holdout_names(eval_specs)`) or in `extra_exclude` is skipped
    *before* any example is emitted, so the generator can never leak an
    eval theorem into training.

    Parameters
    ----------
    train_kind, train_split : SplitKind, Split
        Which benchmark slice supplies training theorems. Default
        ``novel_premises/train`` -- see the module docstring for why the
        ``novel_premises`` kind is preferred.
    eval_specs : iterable of (kind, split)
        Splits to hold out; default `DEFAULT_EVAL_SPECS`.
    extra_exclude : iterable of str
        Additional ``full_name``s to hold out (e.g. an explicit pilot set),
        unioned with the eval holdout.
    source : {"with_proof", "replay_passing"}
        Training-pool source; see `_train_pool`.
    k_strategy : {"last", "all", "sample"}
        Which proof steps become examples; see `KStrategy`.
    chain, level : Chain, int
        Context rung to render. Default ``stepk:1`` (full tactic state, no
        hints). Forwarded to `context.render`.
    seed : int
        Seeds the RNG used by ``k_strategy="sample"`` (ignored otherwise);
        makes dataset construction reproducible.
    stats : dict, optional
        If given, populated in place with run counters:
        ``pool``, ``dropped`` (excluded theorems), ``theorems`` (emitted),
        ``examples``, and ``excluded`` (holdout-set size).

    Yields
    ------
    SFTExample
        One per (kept theorem, chosen ``k``).
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
