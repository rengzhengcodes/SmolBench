"""Run persisted evaluation replicates.

Pool a seed's arms to saturate the GPU while preserving their result order.
"""

import functools
import logging
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet, Callable, Dict, Mapping, Optional, Sequence

from smolbench.evals import Marks, Quiz, provider, results_store
from smolbench.evals.results_store import (
    ReplicateAddress,
    ResultsStore,
    resolve_store,
    utcnow,
)


@dataclass(frozen=True)
class ReplicateHarness:
    """Store-backed replication setup and quiz factory."""

    #: Package-anchored store path, never cwd-relative.
    results_dir: Path
    #: Model names mapped to result-directory tags.
    archetype_tags: Mapping[str, str]
    #: Quiz factory; model-specific padding changes prompts.
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    #: Replicate seeds; each doubles as the per-request decoding seed.
    seeds: Sequence[int]
    #: Required information types in serialization order.
    info_types: Sequence[str]
    #: Optional result-directory namespace.
    prefix: str = ""
    #: Seeds to recollect across all arms, superseding prior runs first.
    force_seeds: Optional[AbstractSet[int]] = None

    @functools.cached_property
    def store(self) -> ResultsStore:
        """Return the cached store for consistent environment resolution."""
        return resolve_store(self.results_dir, self.prefix)

    def _address(
        self, model: Optional[str], tag: str, info: str, seed: int
    ) -> ReplicateAddress:
        """Build one replicate address.

        ``model=None`` permits tag-only reads.

        Parameters
        ----------
        model : Optional[str]
        tag : str
        info : str
        seed : int
        Returns
        -------
        ReplicateAddress
        """
        return ReplicateAddress(tag=tag, info=info, seed=seed, model=model)

    def has_outstanding(self, model: str) -> bool:
        """Return whether `model` has outstanding work.

        Forced seeds remain outstanding to replace stored runs.

        Parameters
        ----------
        model : str
        Returns
        -------
        bool
        """
        forced = self.force_seeds or frozenset()
        if any(seed in forced for seed in self.seeds):
            return True
        tag: str = self.archetype_tags[model]
        return any(
            not self.store.exists(self._address(model, tag, info, seed))
            for seed in self.seeds
            for info in self.info_types
        )

    def run_replicates(
        self,
        model: str,
        extra_args: Optional[dict] = None,
        max_parallel: Optional[int] = None,
        request_timeout: Optional[int] = None,
        server_config: Optional[Mapping] = None,
    ) -> None:
        """Run `model`'s outstanding replicates.

        Supersede forced runs before replacement so readers cannot see stale data.

        Parameters
        ----------
        model : str
        extra_args : Optional[dict], optional
        max_parallel : Optional[int], optional
        request_timeout : Optional[int], optional
        server_config : Optional[Mapping], optional
        """
        tag: str = self.archetype_tags[model]
        logging.info(f"run_replicates: {model} -> {self.store.describe()}")
        eval_kwargs: dict = {}
        if extra_args is not None:
            eval_kwargs["extra_args"] = extra_args
        if max_parallel is not None:
            eval_kwargs["max_parallel"] = max_parallel
        if request_timeout is not None:
            eval_kwargs["request_timeout"] = request_timeout
        forced = self.force_seeds or frozenset()
        for seed in self.seeds:
            outstanding = [
                info
                for info in self.info_types
                if seed in forced
                or not self.store.exists(self._address(model, tag, info, seed))
            ]
            if not outstanding:
                continue
            if seed in forced:
                # Retire first so stale forced runs are never readable.
                reason = f"force_seeds: re-collecting seed={seed}"
                for info in outstanding:
                    self.store.supersede_all(
                        self._address(model, tag, info, seed), reason
                    )
            # Timestamp collection start, not serialization completion.
            run_ts = utcnow()
            quizzes = self.make_quizzes(seed, model)
            combined: list = [q for info in outstanding for q in quizzes[info]]
            pooled: Marks = provider.evaluate(combined, model, seed, **eval_kwargs)
            start: int = 0
            for info in outstanding:
                n: int = len(quizzes[info])
                marks = Marks(
                    model=model,
                    marks=tuple(pooled.marks[start : start + n]),
                    # Copy so later caller mutations cannot alter stored provenance.
                    server_config=dict(server_config) if server_config else None,
                )
                start += n
                self.store.dump_marks(
                    marks, self._address(model, tag, info, seed), run_ts
                )
                logging.info(
                    f"{tag}/{info} seed={seed}: "
                    f"{marks.correct}/{len(marks.marks)} correct"
                )

    def summarize(self, model: str) -> None:
        """Print totals over stored seeds.

        S3 totals use each seed's earliest run.

        Parameters
        ----------
        model : str
        """
        tag: str = self.archetype_tags[model]
        for info in self.info_types:
            correct = incorrect = invalid = 0
            seeds = self.store.list_seeds(model, tag, info)
            for seed in seeds:
                marks = self.store.load_marks(self._address(model, tag, info, seed))
                correct += marks.correct
                incorrect += marks.incorrect
                invalid += marks.invalid
            total = correct + incorrect + invalid
            acc = f"{correct / total:.3f}" if total else "n/a"
            print(
                f"{tag}/{info}: {len(seeds)}/{len(self.seeds)} replicates -- "
                f"correct={correct} incorrect={incorrect} invalid={invalid} "
                f"acc={acc}"
            )

    def cot_chain_lengths(self, tag: str) -> None:
        """Print CoT word counts.

        Shared tags resolve to their first model because they share storage.

        Parameters
        ----------
        tag : str
        """
        model = next((m for m, t in self.archetype_tags.items() if t == tag), None)
        lengths_by_info: Dict[str, list] = {info: [] for info in self.info_types}
        for seed in self.seeds:
            for info in self.info_types:
                addr = self._address(model, tag, info, seed)
                if not self.store.exists(addr):
                    continue
                for mark in self.store.load_marks(addr).marks:
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

    def sync_down(self) -> int:
        """Sync the S3 log into the local layout.

        Raises RuntimeError for a non-S3 store and ValueError for an escaping path.
        """
        return results_store.sync_down(
            self.results_dir, self.archetype_tags, self.prefix
        )
