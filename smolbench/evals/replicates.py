"""
Replicated-evaluation harness shared by the eval notebooks.

Each (archetype, info type, seed) replicate is addressed by a
``results_store.ReplicateAddress`` and persisted IMMEDIATELY after grading, so
an interruption loses at most one replicate and a rerun skips already-persisted
ones. Only the ``ResultsStore`` interface is used here, never a path or S3 key;
see ``smolbench.evals.results_store`` for both backends' layouts, store
resolution and the ``SMOLBENCH_RESULTS_S3`` /
``SMOLBENCH_RESULTS_S3_REGION`` env contract.

A seed's outstanding info types are pooled into ONE ``evaluate()`` call to keep
the GPU saturated; ``evaluate()`` preserves input order, so the marks slice
back per info type by question count, under one shared ``run_ts``.
"""

import functools
import logging
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet, Callable, Dict, Mapping, Optional, Sequence

from smolbench.evals import Marks, Quiz
from smolbench.evals import provider
from smolbench.evals import results_store
from smolbench.evals.results_store import ReplicateAddress, ResultsStore, resolve_store, utcnow


@dataclass(frozen=True)
class ReplicateHarness:
    """One experiment's replication setup: a store-backed results layout
    (local disk or S3 -- see the module docstring) plus a quiz factory."""

    #: Directory holding the per-condition replicate dirs; against an
    #: ``S3ResultsStore`` it is instead the anchor the experiment's S3 log path
    #: segment is derived from (``results_store.experiment_name``, which maps it
    #: relative to ``results_store.repo_root()``).
    #:
    #: MUST be absolute and package/file-anchored, never cwd-relative: a
    #: notebook kernel can run with a temp-dir cwd, and the power-analysis
    #: scripts read this same tree.
    results_dir: Path
    #: model name -> short archetype tag used in result dir names
    #: (e.g. {"olmo-3.1-32b-instruct": "decode"}).
    archetype_tags: Mapping[str, str]
    #: (seed, model) -> {info type: quiz}, called on demand per outstanding seed
    #: rather than eagerly, to keep notebook memory bounded (an extens replicate
    #: embeds the fully enumerated listing in every prompt). Keyed
    #: on the MODEL because the ``noise_intens`` arm is padded to an exact TOKEN
    #: count under the tested model's own tokenizer, so its prompts differ per
    #: model; ``intens``/``extens`` stay byte-identical across models, keeping
    #: cross-model comparisons paired on identical prompts (see
    #: ``smolbench.induction.periodic``'s tokenizer discipline).
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    #: Replicate seeds; each doubles as the per-request decoding seed.
    seeds: Sequence[int]
    #: Info types evaluated per replicate, in serialization order.
    info_types: Sequence[str] = ("intens", "extens", "noise_intens")
    #: Optional namespace so experiments can share one results_dir (e.g.
    #: "one_hop_" -> results/one_hop_{tag}_{info}/; readers of the unprefixed
    #: dirs never see the prefixed experiment). On the S3 log it becomes a
    #: sub-level of the experiment name (``results_store.experiment_name``).
    prefix: str = ""
    #: Seeds counted as outstanding even when the store already has them: the
    #: ``store.exists`` resume-skip is bypassed for exactly these, each being
    #: re-collected and re-logged under a fresh ``run_ts``. ``None`` (default)
    #: disables forcing entirely.
    #:
    #: WARNING: against an S3-backed store this cannot SUPERSEDE anything. Reads
    #: resolve the EARLIEST logged run, so forcing an already-logged seed spends
    #: real GPU money appending an object no reader here will return. Forcing is
    #: meaningful only for a seed with no logged run, or against a LOCAL store
    #: (which overwrites in place). Replacing logged data is an
    #: explicit-exclusion problem -- see the results_store module docstring.
    force_seeds: Optional[AbstractSet[int]] = None

    @functools.cached_property
    def store(self) -> ResultsStore:
        """Return the ``ResultsStore`` backing this harness's replicates.

        See ``resolve_store`` for the resolution order, including the
        repo-anchor fallback pinning the offline test suite to the local store.
        The caching is load-bearing: the env is read once at FIRST access, after
        a notebook's ``load_dotenv(keys.env)`` cell, so every later call reaches
        the same store. ``cached_property`` works on a frozen dataclass because
        it writes straight into ``instance.__dict__``.
        """
        return resolve_store(self.results_dir, self.prefix)

    def _address(self, model: Optional[str], tag: str, info: str, seed: int) -> ReplicateAddress:
        """Build one replicate's store address.

        ``model=None`` is the valid tag-only-read case (see
        ``ReplicateAddress.model``), used by `cot_chain_lengths`.
        """
        return ReplicateAddress(tag=tag, info=info, seed=seed, model=model)

    def has_outstanding(self, model: str) -> bool:
        """Return whether any (info type, seed) for `model` still needs evaluation.

        Lets a caller skip SERVING a model it has no work for. `model` must be a
        key of ``archetype_tags``. The store is consulted on every call (against
        S3, one listing request per (info type, seed)); ANY logged S3 run counts
        as "not outstanding", a seed in ``force_seeds`` always as outstanding.
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
        """Run every outstanding replicate, across every info type, for `model`.

        Only the tuning kwargs actually passed are forwarded, so an archetype
        passing none keeps ``evaluate()``'s defaults. A CoT archetype's long
        `request_timeout` must cover the longest chain on attempt 1, or the
        request is censored into non-deterministic, top-truncated output.
        `server_config` is stamped onto every dumped ``Marks``, so a stored
        replicate self-describes its serving stack (see ``ec2.server_config``).

        Notes
        -----
        ``run_ts`` is captured ONCE PER SEED, before that seed's pooled
        ``evaluate()``, so one collection event gets one timestamp in the S3 log
        (``LocalResultsStore`` ignores ``run_ts``).
        """
        tag: str = self.archetype_tags[model]
        # Before the resume-skip loop, so a direct call still names the
        # resolved store even when nothing is outstanding.
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
            # One timestamp per SEED (see this method's "Notes" section),
            # captured before make_quizzes/evaluate so it dates the start of the
            # collection event, not the end of serialization.
            run_ts = utcnow()
            quizzes = self.make_quizzes(seed, model)
            # Pooled across the outstanding info types (see the module
            # docstring); the shared decode seed is unchanged.
            combined: list = [q for info in outstanding for q in quizzes[info]]
            pooled: Marks = provider.evaluate(combined, model, seed, **eval_kwargs)
            start: int = 0
            for info in outstanding:
                n: int = len(quizzes[info])
                marks = Marks(
                    model=model,
                    marks=tuple(pooled.marks[start:start + n]),
                    # A private copy per dump, so a caller mutating its mapping
                    # later cannot alter what a replicate claims it ran on.
                    server_config=dict(server_config) if server_config else None,
                )
                start += n
                # No mkdir: LocalResultsStore.dump_marks creates its own parent
                # directory, and S3ResultsStore.dump_marks needs none.
                self.store.dump_marks(marks, self._address(model, tag, info, seed), run_ts)
                logging.info(
                    f"{tag}/{info} seed={seed}: "
                    f"{marks.correct}/{len(marks.marks)} correct"
                )

    def summarize(self, model: str) -> None:
        """Print per-info-type totals, over every DISTINCT SEED with a stored replicate.

        Against S3, "stored" means "has at least one logged run"; totals come
        from the EARLIEST logged run of each seed, and the printed count is of
        distinct seeds, not log objects.
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

    def cot_chain_lengths(self, tag: str = "cot") -> None:
        """Print reasoning-chain word-count stats from the stored CoT replicates.

        Word count proxies token count (about 1.3 tokens/word for Llama-style
        tokenizers); a top-truncated distribution flags a too-tight CoT
        ``request_timeout`` (see `run_replicates`).

        `tag` is a TAG, not a model, but the S3 log is keyed by model, so it is
        reverse-looked-up through ``archetype_tags`` to the FIRST model carrying
        it (models sharing a tag already share one local
        ``{prefix}{tag}_{info}/`` directory). With NO such model the address
        model is ``None``, ``S3ResultsStore.exists`` returns False, and every
        (seed, info) is skipped.
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
        """Pull this harness's S3-backed replicate log into the local layout.

        Thin delegate to ``results_store.sync_down``, and the PRIMARY way to feed
        the local-reading analysis tooling: the model -> tag mapping it needs
        already lives here (the ``python -m smolbench.evals.results_store`` CLI
        needs it re-typed by hand).

        Returns
        -------
        int
            Number of objects downloaded.

        Raises
        ------
        RuntimeError
            ``self.store`` is not S3-backed.
        ValueError
            The resolved S3 log prefix is empty, or a listed entry's local
            destination resolves outside ``results_dir``.
        """
        return results_store.sync_down(self.results_dir, self.archetype_tags, self.prefix)
