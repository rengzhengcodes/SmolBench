"""
Shared replicated-evaluation harness for the eval notebooks.

Each (archetype, info type, seed) replicate is addressed by a
``smolbench.evals.results_store.ReplicateAddress`` and persisted through a
``ResultsStore`` IMMEDIATELY after it is graded, so a spot interruption or
kernel restart loses at most one replicate's work; reruns skip
already-persisted replicates, which makes the notebooks' archetype cells
idempotent and resumable. See
``smolbench.evals.results_store`` for the full env contract
(``SMOLBENCH_RESULTS_S3`` / ``SMOLBENCH_RESULTS_S3_REGION``), the S3
append-only log's key layout, and the local-fallback/hermeticity rules.
Every method below talks only to the ``ResultsStore`` interface -- never to
a path or an S3 key directly -- so this module itself carries no
backend-specific logic.

Where a replicate actually lands is a ``ResultsStore`` decision, resolved
once per harness, lazily, the first time ``self.store`` is accessed -- see
that cached property's docstring:

- ``LocalResultsStore``: on local disk, at
  ``{results_dir}/{prefix}{tag}_{info}/rep_{seed}.yaml`` -- exactly what
  every notebook wrote before this indirection existed, still the offline-
  test default, and still the shape every analysis script/notebook reads.
  ONE FILE PER REPLICATE: a rerun overwrites it in place.
- ``S3ResultsStore``: an APPEND-ONLY LOG under
  ``<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml``. A rerun ADDS a
  new timestamped object rather than overwriting anything; every read
  (``summarize``, ``cot_chain_lengths``) resolves the EARLIEST logged run
  per (model, seed, info) -- user ruling 2026-08-16. ``ReplicateHarness.sync_down()`` translates this log
  back into the local layout above for the local-reading analysis tooling.

A seed's outstanding info types are pooled into ONE evaluate() call so the
GPU stays saturated across them instead of draining to zero between separate
per-info barriers; evaluate() preserves input order, so the returned marks
slice back to each info type by its question count and each is still
persisted to its own address -- resume-skip semantics are unaffected. All
info types collected in one seed's pooled call share a SINGLE ``run_ts``
(captured once per seed, before the pooled call -- see
``run_replicates``'s docstring), since they represent one evaluation event
that happened to cover several info types at once.

This module exists because three notebooks (periodic/induction_eval,
chromatic/induction_eval, chromatic/induction_eval_one_hop) previously
carried hand-copied versions of this harness that had already drifted
(cwd-relative results dirs, missing pooling, divergent summaries). Notebooks
now hold only their experiment config and templates.

``make_quizzes`` is keyed on (seed, model), not seed alone: the induction
benchmarks' ``noise_intens`` arm is a length control padded to an exact TOKEN
count under the tokenizer of the model being tested, so that one arm's prompts
are model-specific. The ``intens``/``extens`` arms remain byte-identical across
models, so a cross-model comparison is still a paired comparison on identical
prompts wherever it matters.

Notebook cells no longer construct ``ReplicateHarness`` directly: each
notebook builds one ``smolbench.induction.experiment.InductionExperiment``
instead, which bundles a ``ReplicateHarness`` (unchanged, see its
``harness`` cached property) with the EC2 provisioning lifecycle that
serves the models under test. See that module for the notebook-facing API.
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
    (local disk or S3 -- see the module docstring and ``store`` below) plus a
    quiz factory."""

    #: Directory holding the per-condition replicate dirs (or, when
    #: ``store`` resolves to an ``S3ResultsStore``, the anchor this
    #: experiment's S3 log path segment is derived from -- see
    #: ``smolbench.evals.results_store.experiment_name``). Callers MUST pass
    #: an absolute, package/file-anchored path (never cwd-relative: notebook
    #: kernels can run with temp-dir cwds, and the power-analysis scripts
    #: read this same tree) -- this path is mapped relative to
    #: ``smolbench.evals.results_store.repo_root()`` to build the S3
    #: experiment name, so a cwd-relative path would break that mapping
    #: exactly as it would break the local tree.
    results_dir: Path
    #: model name -> short archetype tag used in result dir names
    #: (e.g. {"olmo-3.1-32b-instruct": "decode"}).
    archetype_tags: Mapping[str, str]
    #: (seed, model) -> {info type: quiz}. Called on demand per outstanding
    #: seed -- never eagerly for all seeds -- to keep notebook memory bounded
    #: (a chromatic replicate embeds the full interval history in ~120
    #: prompts). It takes the MODEL as well as the seed because the induction
    #: benchmarks' noise arm is a token-length control sized with the
    #: tokenizer of the model under test, so its prompts differ per model
    #: (the intensional and extensional arms do not -- see
    #: ``smolbench.induction.periodic``'s tokenizer discipline).
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    #: Replicate seeds; each doubles as the per-request decoding seed.
    seeds: Sequence[int]
    #: Info types evaluated per replicate, in serialization order.
    info_types: Sequence[str] = ("intens", "extens", "noise_intens")
    #: Optional namespace so experiments can share one results_dir (e.g.
    #: "one_hop_" -> results/one_hop_{tag}_{info}/; readers of the unprefixed
    #: dirs never see the prefixed experiment). On the S3 log this becomes a
    #: sub-level of the experiment name -- see
    #: ``smolbench.evals.results_store.experiment_name``.
    prefix: str = ""
    #: Seeds whose (info type, seed) replicates are treated as outstanding
    #: even when the store already has them -- the ``store.exists``
    #: resume-skip is bypassed for exactly these seeds and each is
    #: re-collected and re-logged under a fresh ``run_ts``. ``None`` (the
    #: default) disables forcing entirely.
    #:
    #: WARNING (user ruling 2026-08-16, earliest-wins reads): against an
    #: S3-backed store this knob can no longer SUPERSEDE anything. It was
    #: built when readers resolved the LATEST run_ts (and was used
    #: 2026-08-13 to re-collect early seeds on new hardware); readers now
    #: resolve the EARLIEST, so a forced re-collection of an already-logged
    #: seed appends an object that no reader in this codebase will ever
    #: return -- it spends real GPU money producing log history. Forcing is
    #: only meaningful for seeds with no logged run (where it is redundant
    #: with the normal outstanding check) or against a LOCAL store (which
    #: overwrites in place). If logged data must be replaced, that is an
    #: explicit-exclusion problem -- see the results_store module docstring.
    force_seeds: Optional[AbstractSet[int]] = None

    @functools.cached_property
    def store(self) -> ResultsStore:
        """The :class:`~smolbench.evals.results_store.ResultsStore` backing
        this harness's replicates.

        Design: ``functools.cached_property`` works on a frozen dataclass
        even though ``@dataclass(frozen=True)`` overrides ``__setattr__`` to
        raise ``FrozenInstanceError`` -- ``cached_property.__get__`` writes
        the computed value directly into ``instance.__dict__`` on first
        access, bypassing ``__setattr__`` entirely rather than calling it,
        which a frozen dataclass instance still has since ``frozen=True``
        alone does not add ``__slots__``. This is the same trick
        ``InductionExperiment.harness`` uses on top of this class; see that
        property's docstring for the fuller version of the rationale.

        Caching also has a second, load-bearing effect here, distinct from
        the "build it once" benefit: it makes ``SMOLBENCH_RESULTS_S3`` /
        ``SMOLBENCH_RESULTS_S3_REGION`` get read ONCE, at this property's
        first access, rather than once per replicate. A notebook's actual
        cell order calls ``load_dotenv(keys.env)`` before ever touching a
        harness method, so that one resolution sees the fully-configured
        environment and every subsequent ``exists``/``dump_marks``/
        ``load_marks``/``list_seeds`` call for this harness instance's whole
        lifetime consistently goes to the same store, rather than
        re-resolving (and re-reading possibly-since-mutated env vars) on
        every single call.

        Returns
        -------
        ResultsStore
            ``resolve_store(self.results_dir, self.prefix)`` -- a
            ``LocalResultsStore`` or ``S3ResultsStore`` depending on the
            environment at first access; see that function's docstring for
            the full resolution order (including the repo-anchor
            hermeticity fallback that keeps the offline test suite on the
            local store unconditionally).
        """
        return resolve_store(self.results_dir, self.prefix)

    def _address(self, model: Optional[str], tag: str, info: str, seed: int) -> ReplicateAddress:
        """Builds one replicate's store address.

        Thin, single-purpose wrapper around ``ReplicateAddress`` -- every
        call site below builds one this same way, so the field/keyword
        mapping lives in exactly one place rather than being repeated at
        every call site.

        Parameters
        ----------
        model : str or None
            Forwarded verbatim. ``None`` is valid: see
            ``ReplicateAddress.model``'s docstring for the tag-only-read
            case (``cot_chain_lengths`` when no configured model carries
            the requested tag).
        tag : str
            Archetype tag.
        info : str
            Info type.
        seed : int
            Replicate seed.

        Returns
        -------
        ReplicateAddress
        """
        return ReplicateAddress(tag=tag, info=info, seed=seed, model=model)

    def has_outstanding(self, model: str) -> bool:
        """Whether any replicate for `model` still needs to be evaluated.

        Lets a caller skip SERVING a model it has no work for. That matters
        on a resumed run: swapping vLLM to a finished archetype means pulling
        and loading its checkpoint -- hundreds of GB for the large models --
        only to discover every replicate is already stored. Cheap to ask (it
        is the same ``store.exists`` check ``run_replicates`` makes) and it
        consults the store each time, so it stays correct as replicates
        land. Against an S3-backed store this costs one listing request per
        (info type, seed) checked -- on the order of seconds even for a
        3-arm, 30-replicate model (~90 requests), against a serve step that
        pulls hundreds of GB of model weights onto the instance.

        Parameters
        ----------
        model:
            Model id; must be a key of ``archetype_tags``, as for
            ``run_replicates``.

        Returns
        -------
        bool
            True when at least one (info type, seed) has no stored
            replicate yet. Against ``S3ResultsStore``, ANY logged run of a
            given (info type, seed) counts as "not outstanding" -- see
            ``ResultsStore.exists``.
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
        """Runs all outstanding replicates of every info type against model.

        Only the tuning kwargs the caller passes are forwarded, so
        decode/moe archetypes keep evaluate()'s defaults while cot gets its
        wide-parallel / long-timeout settings uniformly across info types and
        replicates (the long timeout must cover the longest chain on attempt
        1, or long-CoT requests get censored -> non-deterministic,
        top-truncated output).

        ``server_config``, when given, is stamped onto every ``Marks``
        dumped by this call (``Marks.server_config``) so each stored
        replicate self-describes the serving stack that generated it --
        instance type, GPUs, tp, image (see ``ec2.server_config``). None
        (the default) leaves the field None, exactly as before it existed.

        Notes
        -----
        Captures ``run_ts = utcnow()`` ONCE PER SEED ITERATION, before that
        seed's pooled ``evaluate()`` call, and passes the SAME value to
        every ``dump_marks`` call made for that seed's outstanding info
        types. This means one seed's whole collection event -- however many
        info types it happened to cover -- is stamped with one timestamp in
        the S3 log, rather than each info type getting its own, which would
        make one evaluation event look like several unrelated ones once
        logged. (``LocalResultsStore.dump_marks`` ignores ``run_ts``
        entirely, so this only matters for an S3-backed store.)
        """
        tag: str = self.archetype_tags[model]
        # Logged once, unconditionally, before the resume-skip/eval work
        # below -- so a DIRECT call to this method still logs even when
        # every replicate is already stored (the loop below then does
        # nothing). That guarantee is local to run_replicates itself: it
        # does NOT extend through InductionExperiment.run, which checks
        # has_outstanding() and returns BEFORE ever calling run_replicates
        # when nothing is outstanding (see experiment.py's run()) -- so on
        # that facade path, a fully-resumed model logs nothing here at all.
        # On a direct call that does reach this line on a resumed run, it is
        # the only visible difference between a real S3 run and a silent
        # local fallback (see `store`'s docstring for how -- and when --
        # that resolution happens).
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
                continue  # every info type for this seed already graded
            # One timestamp per SEED, not per info type -- see this method's
            # "Notes" section above. Captured before make_quizzes/evaluate so
            # it reflects when this collection event actually started, not
            # when it happened to finish serializing.
            run_ts = utcnow()
            quizzes = self.make_quizzes(seed, model)
            # Pooled evaluation across the outstanding info types; see the
            # module docstring. The shared decode seed is unchanged.
            combined: list = [q for info in outstanding for q in quizzes[info]]
            pooled: Marks = provider.evaluate(combined, model, seed, **eval_kwargs)
            start: int = 0
            for info in outstanding:
                n: int = len(quizzes[info])
                marks = Marks(
                    model=model,
                    marks=tuple(pooled.marks[start:start + n]),
                    # dict(): a private copy per dump, so a caller mutating
                    # its mapping later cannot retroactively alter what one
                    # replicate claims it ran on.
                    server_config=dict(server_config) if server_config else None,
                )
                start += n
                # No mkdir here: LocalResultsStore.dump_marks owns creating
                # its parent directory, and S3ResultsStore.dump_marks needs
                # no directory at all -- see ResultsStore.dump_marks.
                self.store.dump_marks(marks, self._address(model, tag, info, seed), run_ts)
                logging.info(
                    f"{tag}/{info} seed={seed}: "
                    f"{marks.correct}/{len(marks.marks)} correct"
                )

    def summarize(self, model: str) -> None:
        """Prints per-info-type totals over every DISTINCT SEED with a stored replicate.

        Against an S3-backed store, "stored" means "has at least one logged
        run" and the totals are computed from the EARLIEST logged run of
        each such seed (later re-collections are never read; user ruling
        2026-08-16) -- see
        ``ResultsStore.list_seeds``/``ResultsStore.load_marks``. The printed
        line's replicate count is ``len(seeds)``: the number of DISTINCT
        seeds with a stored replicate, never the number of underlying log
        objects (a re-collected seed still counts once).
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
        """Prints reasoning-chain word-count stats from the stored CoT replicates.

        Word count is a reliable proxy for token count (~1.3 tokens/word for
        Llama-style tokenizers). A top-truncated distribution here flags a
        too-tight CoT request_timeout (see run_replicates).

        Notes
        -----
        `tag` is a TAG, not a model -- but the S3 log is keyed by model (see
        ``ReplicateAddress.model``). This method reverse-looks-up `tag`
        through ``archetype_tags`` to the FIRST model whose tag equals it
        (``None`` when no configured model does), and uses that single
        model for every address it builds.

        First-match is the right resolution here, not an arbitrary
        shortcut: the LOCAL layout has no per-model dimension at all --
        every model sharing one `tag` already reads and writes the SAME
        ``{prefix}{tag}_{info}/rep_{seed}.yaml`` directory, so a local-store
        run of this method has only ever read that one directory regardless
        of how many models share the tag. Picking the first matching model
        for the S3 case preserves that same "one directory/log,
        tag-scoped" behavior instead of introducing a new "which model's
        log wins" ambiguity that the local store never had to answer. When
        NO model carries `tag` (an existing test calls this with no model
        configured at all), the resolved model is ``None`` -- which
        ``S3ResultsStore.exists`` handles by returning ``False``
        unconditionally, so this method's ``if not self.store.exists(addr):
        continue`` guard skips every (seed, info) cleanly rather than ever
        calling ``load_marks`` with a ``None`` model.
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
        """Pulls this harness's S3-backed replicate log into the local layout.

        Thin delegate to
        ``smolbench.evals.results_store.sync_down(self.results_dir,
        self.archetype_tags, self.prefix)`` -- the PRIMARY way to bring an
        S3-backed experiment's results onto local disk for the
        local-reading analysis tooling (``power_analysis.py``, the figure
        scripts), because this harness is the only place the model -> tag
        mapping (``archetype_tags``) already lives. The module-level CLI
        (``python -m smolbench.evals.results_store``) exists purely for
        out-of-notebook use, where that mapping has to be re-typed by hand.

        Returns
        -------
        int
            The number of objects downloaded; see
            ``smolbench.evals.results_store.sync_down``.

        Raises
        ------
        RuntimeError
            ``self.store`` does not resolve to an S3-backed store -- see the
            module function's docstring for the two possible reasons.
        ValueError
            The resolved S3 log prefix is empty, or a listed entry's local
            destination resolves outside ``results_dir`` -- see the module
            function's docstring.
        """
        return results_store.sync_down(self.results_dir, self.archetype_tags, self.prefix)
