"""One facade over the induction eval harness and its EC2 lifecycle.

:class:`InductionExperiment` bundles
:class:`~smolbench.evals.replicates.ReplicateHarness` with the EC2 spot
lifecycle that serves the models under test. The family-ladder scaling study
builds one module-level ``EXPERIMENT`` in ``notebooks/induction/run_study.py``,
launched per lane by ``scripts/fleet/run_fleet.py``.

Seed convention. A "replicate" is the SAME quiz regenerated under a fresh seed;
``seeds`` is always ``tuple(base_seed + r for r in range(n_replicates))``. That
seed drives the quiz's own randomness AND the per-request decoding seed, so a
replicate is reproducible from its ``rep_{seed}.yaml`` path alone.
``make_quizzes`` also takes the model, because the noise arm is padded to an
exact token count under the model's own tokenizer.

Results and resume. ``results_store.resolve_store`` picks local disk vs S3 at
call time; its module docstring is the canonical home for the env contract, the
append-only S3 key layout and earliest-wins (= pass@1) reads, and pooling and
resume-skip belong to ``ReplicateHarness``. What this class pins is the
``<experiment>`` key segment (``results_store.experiment_name``: ``notebook_dir``
plus ``prefix`` minus its trailing ``"_"``) and the local layout analysis
scripts read, ``{prefix}{tag}_{info}/rep_{seed}.yaml`` under ``results_dir``,
overwritten on rerun. ``harness.sync_down()`` renders the log back into that
layout, ``archetype_tags`` supplying the model-to-tag mapping a log key cannot
carry.

COST: ``provision()``, ``run()``, ``agent_status()`` and ``teardown()`` are LIVE
AWS calls against a self-provisioned spot instance, billed while it is up; the
hourly rate varies with the instance tier the experiment requests (``ec2.py``
owns the rate notes). ``summarize()`` and ``cot_chain_lengths()`` spend no
EC2/inference cost but do issue S3 reads under an S3-backed store.

CRITICAL -- never import ``smolbench.evals.providers.ec2`` at module scope: its
``EC2_*`` constants are captured from ``os.environ`` at IMPORT time (notebooks
``load_dotenv(keys.env)`` first), so an eager import silently freezes them to
un-overridden defaults for any process importing this module ahead of its
``load_dotenv``. Every method needing the lifecycle imports ``ec2`` INSIDE its
body, after ``_apply_env()``. (``smolbench.evals.replicates`` is safe at module
scope: its provider dispatch resolves at CALL time.)
"""

import functools
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from smolbench.evals import Quiz
from smolbench.evals.replicates import ReplicateHarness


# Canonical definition lives in smolbench.evals.results_store.
from smolbench.evals.results_store import repo_root


@dataclass(frozen=True)
class InductionExperiment:
    """Configure one replicated-evaluation experiment, EC2 lifecycle included.

    Lifecycle order: ``provision()`` once, ``run(model, ...)`` once per
    archetype, ``summarize(model)`` / ``cot_chain_lengths()`` any number of
    times (offline), ``teardown()`` once at the end. Frozen, like
    ``ReplicateHarness``: configuration must not mutate mid-run.
    """

    #: Locates results at ``repo_root()/notebooks/<notebook_dir>/results``.
    #: The current family-ladder study uses ``"induction"``.
    notebook_dir: str
    #: Model name -> short archetype tag used in result directory names (e.g.
    #: ``{"olmo-3.1-32b-instruct": "decode"}``). Forwarded to ``ReplicateHarness``.
    archetype_tags: Mapping[str, str]
    #: (seed, model) -> {info type: quiz}. Forwarded to ``ReplicateHarness``,
    #: which calls it lazily per outstanding seed. Only the noise arm varies per
    #: model -- see the module docstring's "Seed convention" section.
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    #: Number of replicate seeds. Every induction study to date uses 30; the
    #: sizing evidence lives in each study's ``analysis/power_analysis.py``,
    #: and the family-ladder value is additionally USER-LOCKED (see
    #: ``run_study.py``'s N_REPLICATES comment).
    n_replicates: int = 30
    #: First replicate's seed; replicate 0 uses it exactly. Default 1776 (the
    #: July 4th nod); the family-ladder study overrides it to 0 on purpose --
    #: see ``notebooks/induction/run_study.py``'s "Seeds" paragraph.
    base_seed: int = 1776
    #: Info types evaluated per replicate, in serialization order. Forwarded to
    #: ``ReplicateHarness``. The default is the original three-condition set
    #: (see ``periodic.py``'s "Information conditions"
    #: module docstring section); the family-ladder study adds ``"zero"`` for
    #: :func:`~smolbench.induction.periodic.get_periodic_zero_info_numeric_quiz`.
    info_types: Tuple[str, ...] = ("intens", "extens", "noise_intens")
    #: Optional namespace prefix on result directory names (e.g.
    #: ``"one_hop_"``) so two experiments can share one ``results_dir`` without
    #: their replicate directories colliding. Forwarded to ``ReplicateHarness``.
    prefix: str = ""
    #: Repo-root-anchored basename (e.g. ``".ec2_state_induction.json"``) for
    #: this experiment's EC2 state file, or None to use ``ec2.py``'s default.
    #: Set it when two experiments could run concurrently, so they do not
    #: clobber each other's instance record; see ``_apply_env``.
    state_file: Optional[str] = None
    #: ``(index, count)`` selecting a disjoint slice of the replicates, so N
    #: processes on N instances can collect one model's replicates in parallel;
    #: None runs all of them. Replicates are independent by construction (fresh
    #: seed each, results keyed by (tag, info, seed)), so no coordination is
    #: needed BEYOND the disjointness ``seeds`` guarantees.
    shard: Optional[Tuple[int, int]] = None
    #: Forwarded to ``ReplicateHarness.force_seeds``: seeds re-collected past
    #: the resume-skip; ``None`` disables it. Supersede semantics differ by
    #: backend: S3 reads resolve the EARLIEST run, so a forced re-collection
    #: is never returned by any reader; a LOCAL store overwrites
    #: ``rep_{seed}.yaml`` in place. ``results_store.py``'s docstring says why
    #: the S3 log is append-only.
    force_seeds: Optional[frozenset] = None

    def __post_init__(self) -> None:
        if self.shard is not None:
            index, count = self.shard
            if count < 1 or not (0 <= index < count):
                raise ValueError(
                    f"shard {self.shard!r}: need count >= 1 and 0 <= index < count."
                )

    @property
    def seeds(self) -> Tuple[int, ...]:
        """Return the replicate seeds this process is responsible for.

        Sharded, that is every ``count``-th seed starting at ``index``. Shards
        STRIDE rather than take contiguous blocks, keeping them within one
        replicate of each other in size (30 over 4 shards splits 8/8/7/7, not
        8/8/8/6) -- the slowest shard sets the wall-clock time sharding exists
        to reduce. Every replicate lands in exactly one shard, so parallel
        shards never contend for one ``rep_{seed}.yaml``.
        """
        every = tuple(self.base_seed + r for r in range(self.n_replicates))
        if self.shard is None:
            return every
        index, count = self.shard
        return tuple(s for r, s in enumerate(every) if r % count == index)

    @property
    def results_dir(self) -> Path:
        """Return ``repo_root()/notebooks/<notebook_dir>/results``, never cwd-relative."""
        return repo_root() / "notebooks" / self.notebook_dir / "results"

    @functools.cached_property
    def harness(self) -> ReplicateHarness:
        """Return this experiment's :class:`ReplicateHarness`, built once and reused.

        Caching is safe on a frozen dataclass because ``cached_property.__get__``
        writes straight into ``instance.__dict__`` (``frozen=True`` adds no
        ``__slots__``) rather than through the overridden ``__setattr__``.
        """
        return ReplicateHarness(
            results_dir=self.results_dir,
            archetype_tags=self.archetype_tags,
            make_quizzes=self.make_quizzes,
            seeds=self.seeds,
            info_types=self.info_types,
            prefix=self.prefix,
            force_seeds=self.force_seeds,
        )

    def _apply_env(self) -> None:
        """Set the environment ``smolbench.evals.providers.ec2`` reads at call time.

        Sets ``INFERENCE_PROVIDER=ec2`` and, when ``state_file`` is configured,
        points ``EC2_STATE_FILE`` at this experiment's private,
        repo-root-anchored state file; both are read at CALL time, unlike the
        ``EC2_*`` constants frozen at import. With ``state_file=None`` it
        EXPLICITLY POPS ``EC2_STATE_FILE``, so such an experiment cannot keep
        talking to an earlier one's state file instead of ``ec2.py``'s default.
        """
        os.environ["INFERENCE_PROVIDER"] = "ec2"
        if self.state_file is not None:
            os.environ["EC2_STATE_FILE"] = str(repo_root() / self.state_file)
        else:
            os.environ.pop("EC2_STATE_FILE", None)

    def provision(self) -> Dict[str, Any]:
        """Provision, or reattach to, this experiment's EC2 spot instance.

        LIVE AWS call (see the module docstring's COST paragraph). Calls
        ``ec2.provision_spot_instance()`` bare, relying entirely on the
        ``EC2_*`` environment for instance types/regions/volume/idle
        timeout/max lifetime.

        Returns
        -------
        Dict[str, Any]
            That call's state dict (``instance_id``, ``region``, ``public_ip``,
            ``instance_type``, ``availability_zone``, ``control_token``,
            ``vllm_api_key``, ...), also persisted to ``EC2_STATE_FILE``.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        state = ec2.provision_spot_instance()
        # print, not logging: the operator's receipt that a billing box
        # exists must be visible regardless of logging config.
        print(
            f"instance {state['instance_id']} ({state['instance_type']}) "
            f"in {state['availability_zone']} at {state['public_ip']}"
        )
        return state

    def run(
        self,
        model: str,
        *,
        extra_args: Optional[dict] = None,
        max_parallel: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> None:
        """Serve ``model`` and run every outstanding replicate against it.

        LIVE AWS call (the ``serve_model`` container swap) followed by live
        inference. Swaps the instance's vLLM container to ``model`` and, while
        it is up, runs every info type's outstanding replicates via
        ``self.harness.run_replicates``; safe to re-run after an interruption,
        since both are idempotent and resumable. All three keyword arguments
        reach ``run_replicates`` UNCHANGED, None meaning "no override".

        Parameters
        ----------
        model : str
            Must be a key of ``archetype_tags`` AND of
            ``ec2.EC2_DEPLOY_SPECS``; ``KeyError`` otherwise.
        extra_args : dict, optional
            Extra chat-completions body fields, e.g. a CoT archetype's
            ``{"max_completion_tokens": 16384}``.
        max_parallel : int, optional
            Concurrent request cap forwarded to the evaluator; None keeps the
            provider default.
        request_timeout : int, optional
            Per-request read timeout in seconds; CoT archetypes raise it so the
            longest chain finishes on attempt 1.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        # Nothing to do => do not SERVE. serve_model pulls and loads hundreds
        # of GB for the large archetypes, which is pure billed time if every
        # replicate is already on disk. Hit for real on a resumed run, where
        # the completed arms would otherwise be re-served first.
        if not self.harness.has_outstanding(model):
            logging.info(
                f"run: {model!r} has no outstanding replicates; skipping serve"
            )
            return

        # Forward what the caller passed, unfiltered: run_replicates populates
        # its own eval_kwargs only for non-None values, so passing None through
        # is identical to omitting it.
        with ec2.serve_model(model):
            self.harness.run_replicates(
                model,
                extra_args=extra_args,
                max_parallel=max_parallel,
                request_timeout=request_timeout,
                # Captured INSIDE the serve block so the snapshot describes the
                # box that actually serves these replicates; stamped on every
                # stored Marks (never raises -- see ec2.server_config).
                server_config=ec2.server_config(model),
            )

    def summarize(self, model: str) -> None:
        """Print per-info-type totals for ``model`` over every stored replicate.

        A pure ``ReplicateHarness.summarize`` delegate: no environment applied,
        no EC2/inference cost, but S3 reads under an S3-backed store. ``model``
        must be a key of ``archetype_tags``; ``KeyError`` otherwise.
        """
        self.harness.summarize(model)

    def cot_chain_lengths(self, tag: str = "cot") -> None:
        """Print reasoning-chain word-count stats from the stored CoT replicates.

        Like :meth:`summarize`, a pure ``ReplicateHarness`` delegate (no EC2 or
        inference cost, but S3 reads under an S3-backed store). ``tag`` selects
        the archetype scanned; every CoT archetype is tagged "cot".
        """
        self.harness.cot_chain_lengths(tag)

    def agent_status(self) -> Dict[str, Any]:
        """Return the provisioned instance's control-agent status, verbatim.

        LIVE AWS call. Container state, health and recent docker logs, for
        diagnosing a stuck ``run()``/``provision()`` without re-triggering
        either. Raises ``RuntimeError`` if no instance has been provisioned.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        return ec2.agent_status()

    def teardown(self) -> None:
        """Terminate this experiment's EC2 spot instance and clear its state.

        LIVE AWS call. Calls ``ec2.shutdown_instance()`` with no overrides; safe
        even if provisioning failed or the state file was lost, since
        ``shutdown_instance`` falls back to the ``smolbench:experiment`` tag.
        The family-ladder study invokes this only behind an explicit
        ``--teardown`` flag: ``scripts/fleet/run_fleet.py`` owns teardown there.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        # Return value discarded, per the -> None annotation.
        ec2.shutdown_instance()
