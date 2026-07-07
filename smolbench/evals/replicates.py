"""
Shared replicated-evaluation harness for the eval notebooks.

Each (archetype, info type, seed) replicate is serialized to
``{results_dir}/{prefix}{tag}_{info}/rep_{seed}.yaml`` IMMEDIATELY after it is
graded, so a spot interruption or kernel restart loses at most one
replicate's work; reruns skip already-serialized replicates, which makes the
notebooks' archetype cells idempotent and resumable. The filename carries the
seed, keeping every generation reproducible/attributable.

A seed's outstanding info types are pooled into ONE evaluate() call so the
GPU stays saturated across them instead of draining to zero between separate
per-info barriers; evaluate() preserves input order, so the returned marks
slice back to each info type by its question count and each is still
serialized to its own rep file -- resume-skip semantics are unaffected.

This module exists because three notebooks (periodic/induction_eval,
chromatic/induction_eval, chromatic/induction_eval_one_hop) previously
carried hand-copied versions of this harness that had already drifted
(cwd-relative results dirs, missing pooling, divergent summaries). Notebooks
now hold only their experiment config and templates.

Notebook cells no longer construct ``ReplicateHarness`` directly: each
notebook builds one ``smolbench.induction.experiment.InductionExperiment``
instead, which bundles a ``ReplicateHarness`` (unchanged, see its
``harness`` cached property) with the EC2 provisioning lifecycle that
serves the models under test. See that module for the notebook-facing API.
"""

import logging
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, Sequence

from smolbench.evals import Marks, Quiz
from smolbench.evals import provider


@dataclass(frozen=True)
class ReplicateHarness:
    """One experiment's replication setup (results layout + quiz factory)."""

    #: Directory holding the per-condition replicate dirs. Callers MUST pass
    #: an absolute, package/file-anchored path (never cwd-relative: notebook
    #: kernels can run with temp-dir cwds, and the power-analysis scripts
    #: read this same tree).
    results_dir: Path
    #: model name -> short archetype tag used in result dir names
    #: (e.g. {"olmo-3.1-32b-instruct": "decode"}).
    archetype_tags: Mapping[str, str]
    #: seed -> {info type: quiz}. Called on demand per outstanding seed --
    #: never eagerly for all seeds -- to keep notebook memory bounded (a
    #: chromatic replicate embeds the full interval history in ~120 prompts).
    make_quizzes: Callable[[int], Dict[str, Quiz]]
    #: Replicate seeds; each doubles as the per-request decoding seed.
    seeds: Sequence[int]
    #: Info types evaluated per replicate, in serialization order.
    info_types: Sequence[str] = ("intens", "extens", "noise_intens")
    #: Optional namespace so experiments can share one results_dir (e.g.
    #: "one_hop_" -> results/one_hop_{tag}_{info}/; readers of the unprefixed
    #: dirs never see the prefixed experiment).
    prefix: str = ""

    def _rep_path(self, tag: str, info: str, seed: int) -> Path:
        return self.results_dir / f"{self.prefix}{tag}_{info}" / f"rep_{seed}.yaml"

    def run_replicates(
        self,
        model: str,
        extra_args: Optional[dict] = None,
        max_parallel: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> None:
        """Runs all outstanding replicates of every info type against model.

        Only the tuning kwargs the caller passes are forwarded, so
        decode/moe archetypes keep evaluate()'s defaults while cot gets its
        wide-parallel / long-timeout settings uniformly across info types and
        replicates (the long timeout must cover the longest chain on attempt
        1, or long-CoT requests get censored -> non-deterministic,
        top-truncated output).
        """
        tag: str = self.archetype_tags[model]
        eval_kwargs: dict = {}
        if extra_args is not None:
            eval_kwargs["extra_args"] = extra_args
        if max_parallel is not None:
            eval_kwargs["max_parallel"] = max_parallel
        if request_timeout is not None:
            eval_kwargs["request_timeout"] = request_timeout
        for seed in self.seeds:
            outstanding = [
                info
                for info in self.info_types
                if not self._rep_path(tag, info, seed).exists()
            ]
            if not outstanding:
                continue  # every info type for this seed already graded
            quizzes = self.make_quizzes(seed)
            # Pooled evaluation across the outstanding info types; see the
            # module docstring. The shared decode seed is unchanged.
            combined: list = [q for info in outstanding for q in quizzes[info]]
            pooled: Marks = provider.evaluate(combined, model, seed, **eval_kwargs)
            start: int = 0
            for info in outstanding:
                n: int = len(quizzes[info])
                marks = Marks(model=model, marks=tuple(pooled.marks[start:start + n]))
                start += n
                out = self._rep_path(tag, info, seed)
                out.parent.mkdir(parents=True, exist_ok=True)
                marks.dump(out)
                logging.info(
                    f"{tag}/{info} seed={seed}: "
                    f"{marks.correct}/{len(marks.marks)} correct"
                )

    def summarize(self, model: str) -> None:
        """Prints per-info-type totals over every serialized replicate of model."""
        tag: str = self.archetype_tags[model]
        for info in self.info_types:
            correct = incorrect = invalid = 0
            paths = sorted(
                (self.results_dir / f"{self.prefix}{tag}_{info}").glob("rep_*.yaml")
            )
            for path in paths:
                marks = Marks.load(path)
                correct += marks.correct
                incorrect += marks.incorrect
                invalid += marks.invalid
            total = correct + incorrect + invalid
            acc = f"{correct / total:.3f}" if total else "n/a"
            print(
                f"{tag}/{info}: {len(paths)}/{len(self.seeds)} replicates -- "
                f"correct={correct} incorrect={incorrect} invalid={invalid} "
                f"acc={acc}"
            )

    def cot_chain_lengths(self, tag: str = "cot") -> None:
        """Prints reasoning-chain word-count stats from the cached CoT YAMLs.

        Word count is a reliable proxy for token count (~1.3 tokens/word for
        Llama-style tokenizers). A top-truncated distribution here flags a
        too-tight CoT request_timeout (see run_replicates).
        """
        lengths_by_info: Dict[str, list] = {info: [] for info in self.info_types}
        for seed in self.seeds:
            for info in self.info_types:
                path = self._rep_path(tag, info, seed)
                if not path.exists():
                    continue
                for mark in Marks.load(path).marks:
                    if mark.reasoning:
                        lengths_by_info[info].append(len(mark.reasoning.split()))
        for info in self.info_types:
            lengths = lengths_by_info[info]
            if not lengths:
                print(f"{tag}/{info}: no reasoning chains found")
                continue
            print(
                f"{tag}/{info}: n={len(lengths):4d}  "
                f"min={min(lengths):5d}  max={max(lengths):5d}  "
                f"mean={statistics.mean(lengths):6.0f}  "
                f"median={statistics.median(lengths):6.0f}  "
                f"words  (~tokens x 1.3)"
            )
