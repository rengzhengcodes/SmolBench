"""Run persisted evaluation replicates.

Pool a seed's arms to saturate the GPU while preserving their result order.
"""

import functools
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet, Callable, Dict, Mapping, Optional, Sequence

from smolbench.evals import Marks, Quiz, provider, results_store
from smolbench.evals.results_store import (
    ReplicateAddress,
    ResultsStore,
    S3ResultsStore,
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

        Forced seeds write their replacement before retiring the run it supersedes.

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
            reason = f"force_seeds: re-collecting seed={seed}"
            retiring: Dict[str, list] = {}
            if seed in forced:
                for info in outstanding:
                    addr = self._address(model, tag, info, seed)
                    if isinstance(self.store, S3ResultsStore):
                        # S3 runs are immutable and ``exists`` is marker-blind, so
                        # retiring before a failed recollect would strand the seed:
                        # the survivors retire only after their replacement lands.
                        retiring[info] = self.store.list_runs(addr)
                    else:
                        # Local ``exists`` is file-based, so a failed recollect
                        # stays outstanding; the audit marker can move first.
                        self.store.supersede_all(addr, reason)
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
                addr = self._address(model, tag, info, seed)
                self.store.dump_marks(marks, addr, run_ts)
                for stamp in retiring.get(info, ()):  # S3 only
                    # The S3 supersede signature takes the stamp.
                    # pylint: disable-next=too-many-function-args
                    self.store.supersede(addr, stamp, reason)
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

    def sync_down(self) -> int:
        """Sync the S3 log into the local layout.

        Raises RuntimeError for a non-S3 store and ValueError for an escaping path.
        """
        return results_store.sync_down(
            self.results_dir, self.archetype_tags, self.prefix
        )
