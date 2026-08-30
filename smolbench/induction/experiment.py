"""Provide one facade over the induction eval harness and EC2 lifecycle.

:class:`InductionExperiment` bundles the induction eval harness with the EC2
spot-instance lifecycle that serves the models under test, so a caller
supplies only its experiment-specific config and calls ``provision()`` /
``run(model, ...)`` / ``summarize(model)`` / ``teardown()``. The family-ladder
scaling study builds one module-level ``EXPERIMENT`` in
``notebooks/induction/run_study.py``, launched per lane by
``scripts/fleet/run_fleet.py``.

Seeds. A "replicate" is the SAME quiz regenerated under a fresh seed, and
``seeds`` is always ``tuple(base_seed + r for r in range(n_replicates))``.
That seed drives both the quiz's own randomness (``PeriodicConfig.seed`` /
``ChromaticIntervalsConfig.seed``) and the per-request decoding seed, which is
what makes a replicate reproducible from its ``rep_{seed}.yaml`` path alone:
``make_quizzes(seed, model)`` regenerates byte-identical prompts. (The model
is in that call because the noise arm is padded to an exact token count under
the model's own tokenizer; the rep file's DIRECTORY already names its
archetype.)

Results and resume. ``results_store.resolve_store`` picks local disk vs S3 at
call time from ``SMOLBENCH_RESULTS_S3=s3://<bucket>[/<base-prefix>]``
(unset/empty selects local) and ``SMOLBENCH_RESULTS_S3_REGION`` (default
``AWS_REGION``, else boto3's own chain); pooling and resume-skip belong to
:class:`~smolbench.evals.replicates.ReplicateHarness`, keyed per replicate by
a ``results_store.ReplicateAddress``. The LOCAL layout, which every analysis
script, notebook and committed results tree depends on, is
``{prefix}{tag}_{info}/rep_{seed}.yaml`` under ``results_dir``, one file per
replicate, overwritten on rerun. The S3 layout is instead an APPEND-ONLY
EXPERIMENT LOG::

    <base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml

``results_store.experiment_name`` maps
``repo_root()/notebooks/<notebook_dir>/results`` to ``<notebook_dir>``, with
``prefix`` folded in as a sub-level minus its trailing ``"_"``
(``notebook_dir="induction"``, ``prefix="one_hop_"`` -> ``"induction/one_hop"``).
``run_ts`` is a fixed-width UTC ``YYYYMMDDTHHMMSSZ`` stamp, so lexicographic
key order is chronological. A rerun APPENDS and NEVER overwrites, so a
superseded verdict stays recoverable, and every READ path resolves the
EARLIEST ``run_ts`` per (model, seed, info) and treats only that one as live
-- which is what makes the first logged run the pass@1 measurement.
``harness.sync_down()`` renders that log back into the local layout for
store-unaware tooling, supplying ``archetype_tags`` as the model-to-tag
mapping a log key cannot carry; it is one-way and destructive.

COST: ``provision()``, ``run()``, ``agent_status()`` and ``teardown()`` are
LIVE AWS calls against a self-provisioned EC2 spot instance, billed for as
long as it is up (~$30-45/h for the p5e/p5 family; see
``smolbench/evals/providers/ec2.py``). ``summarize()`` and
``cot_chain_lengths()`` spend no EC2 or inference cost, but under an S3-backed
store they DO issue S3 reads.

CRITICAL -- never import ``smolbench.evals.providers.ec2`` at module scope.
Its ``EC2_*`` constants are ordinary module attributes captured from
``os.environ`` at IMPORT time (callers read them back as
``ec2.EC2_EXPERIMENT_TAG``, and notebooks ``load_dotenv(keys.env)`` before
importing ``ec2``), so an eager import here would freeze them to their
un-overridden defaults, with no error, for any process that imports this
module ahead of its ``load_dotenv``. Every method that needs the lifecycle
therefore imports ``ec2`` INSIDE its body, after ``_apply_env()``.
(``smolbench.evals.replicates`` is safe at module scope: its provider dispatch
resolves at CALL time.)
"""

import functools
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from smolbench.evals import Quiz
from smolbench.evals.replicates import ReplicateHarness


# Canonical definition lives in smolbench.evals.results_store; re-exported
# here for this module's own path construction.
from smolbench.evals.results_store import repo_root  # noqa: F401 -- re-exported


@dataclass(frozen=True)
class InductionExperiment:
    """Configure one replicated-evaluation experiment, EC2 lifecycle included.

    Lifecycle order: ``provision()`` once, ``run(model, ...)`` once per
    archetype, ``summarize(model)`` / ``cot_chain_lengths()`` any number of
    times (offline), ``teardown()`` once at the end. Frozen, like
    ``ReplicateHarness``: an experiment's configuration must not mutate
    mid-run. ``harness`` is the one lazily built attribute.
    """

    #: Which results tree this experiment belongs to. Used only to locate
    #: results: ``repo_root()/notebooks/<notebook_dir>/results``. The
    #: current family-ladder study uses ``"induction"``.
    notebook_dir: str
    #: Model name -> short archetype tag used in result directory names
    #: (e.g. ``{"olmo-3.1-32b-instruct": "decode"}``). Forwarded verbatim to
    #: ``ReplicateHarness``.
    archetype_tags: Mapping[str, str]
    #: (seed, model) -> {info type: quiz}. Forwarded verbatim to
    #: ``ReplicateHarness``. See that class for why this is called lazily,
    #: per outstanding seed, rather than eagerly for every seed up front,
    #: and why it takes the model: the noise arm is token-matched with the
    #: tokenizer of the model under test, so only that arm varies per model.
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    #: Number of replicate seeds. Every induction study to date uses 30
    #: (see each study's ``power_analysis.py``-backed replication-setup
    #: comment for the derivation).
    n_replicates: int = 30
    #: First replicate's seed; replicate 0 uses this seed exactly. The
    #: default is 1776 (the July 4th, 1776 nod). The current family-ladder
    #: study overrides this to 0 on purpose; see the module docstring's
    #: "Seed convention" section.
    base_seed: int = 1776
    #: Info types evaluated per replicate, in serialization order. Forwarded
    #: verbatim to ``ReplicateHarness``. The field default lists the
    #: original three-condition set (see ``periodic.py`` / ``chromatic.py``'s
    #: "Information conditions" module docstring section); the family-ladder
    #: study passes an explicit 4-tuple that adds ``"zero"`` for
    #: :func:`~smolbench.induction.periodic.get_periodic_zero_info_numeric_quiz`.
    info_types: Tuple[str, ...] = ("intens", "extens", "noise_intens")
    #: Optional namespace prefix on result directory names (e.g.
    #: ``"one_hop_"``) so more than one experiment can share one
    #: ``results_dir`` without their replicate directories colliding.
    #: Forwarded verbatim to ``ReplicateHarness``.
    prefix: str = ""
    #: Repo-root-anchored basename (e.g. ``".ec2_state_induction.json"``)
    #: for this experiment's EC2 state file, or None to use ``ec2.py``'s own
    #: default. Set this when two experiments could run concurrently, so
    #: they do not clobber each other's instance record; see
    #: ``_apply_env``. The current family-ladder study sets a private state
    #: file (see ``INDUCTION_STATE_FILE`` in
    #: ``notebooks/induction/run_study.py``).
    state_file: Optional[str] = None
    #: ``(index, count)`` that selects a disjoint slice of the replicates,
    #: so N processes on N instances can collect one model's replicates in
    #: parallel. None (the default) means this process runs all of them.
    #:
    #: Replicates are independent by construction: each is a fresh
    #: ``PeriodicConfig`` seed, and results are keyed by (tag, info, seed).
    #: So no coordination is needed BEYOND disjointness, which ``seeds``
    #: guarantees.
    shard: Optional[Tuple[int, int]] = None
    #: Forwarded to ``ReplicateHarness.force_seeds``: seeds whose replicates
    #: get re-collected past the resume-skip. ``None`` disables this. Against
    #: an S3 store, reads resolve the EARLIEST run, so a forced re-collection
    #: of an already-logged seed is never returned by any reader -- see
    #: ``ReplicateHarness.force_seeds``.
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

        Replicate ``r``'s seed is ``base_seed + r``, so a seed names the same
        replicate no matter which shard collects it. Unsharded this is all
        ``n_replicates`` of them; sharded it is every ``count``-th one
        starting at ``index``. Shards STRIDE rather than take contiguous
        blocks, which keeps them within one replicate of each other in size
        when ``count`` does not divide ``n_replicates`` (30 over 4 shards
        splits 8/8/7/7, not 8/8/8/6) -- the slowest shard sets the wall-clock
        time sharding exists to reduce. Every replicate lands in exactly one
        shard, so parallel shards never contend for the same
        ``rep_{seed}.yaml``.
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
        """Return the :class:`ReplicateHarness` built from this experiment's config.

        Built once and reused. Caching is safe on a frozen dataclass because
        ``cached_property.__get__`` writes straight into ``instance.__dict__``
        (which still exists -- ``frozen=True`` adds no ``__slots__``) rather
        than going through the overridden ``__setattr__``.
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
        repo-root-anchored state file; both are read at CALL time (per
        ``ec2.py``'s "Env-read timing" section), unlike the ``EC2_*`` constants
        frozen at import. When ``state_file`` is None it EXPLICITLY POPS
        ``EC2_STATE_FILE``, so a later ``state_file=None`` experiment in the
        same process cannot silently keep talking to an earlier one's state
        file instead of ``ec2.py``'s default path.
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
        timeout/max lifetime. Returns that call's state dict (``instance_id``,
        ``region``, ``public_ip``, ``instance_type``, ``availability_zone``,
        ``control_token``, ``vllm_api_key``, ...), which it also persists to
        ``EC2_STATE_FILE``.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        state = ec2.provision_spot_instance()
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
        inference calls. Swaps the instance's vLLM container to ``model`` and,
        while it is up, runs every info type's outstanding replicates via
        ``self.harness.run_replicates``; safe to re-run after an interruption,
        since both are idempotent and resumable. ``model`` must be a key of
        ``archetype_tags`` AND of ``ec2.EC2_DEPLOY_SPECS`` (``KeyError``
        otherwise). ``extra_args`` (extra chat-completions body fields, e.g. a
        CoT archetype's ``{"max_completion_tokens": 16384}``),
        ``max_parallel`` (fan-out cap) and ``request_timeout`` (per-request
        read timeout in seconds, which CoT archetypes raise so the longest
        chain finishes on attempt 1) reach ``run_replicates`` UNCHANGED, with
        None meaning "no override".
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        # Nothing to do => do not SERVE. The serve_model block swaps the
        # instance's vLLM container to this checkpoint. For the large
        # archetypes, that means pulling and loading hundreds of GB. If
        # every replicate then turns out to already be on disk, that pull
        # is pure billed time. This case is hit for real on a resumed run,
        # where the completed arms get re-served before this function
        # reaches the outstanding one.
        if not self.harness.has_outstanding(model):
            logging.info(
                f"run: {model!r} has no outstanding replicates; skipping serve"
            )
            return

        # Design: this forwards exactly what the caller passed, with no
        # filtering here. ``ReplicateHarness.run_replicates`` already
        # implements "only forward what's given" at the ``evaluate()`` call
        # level (it only populates its own ``eval_kwargs`` for non-None
        # values), so passing None through for an omitted parameter is
        # behaviorally identical to omitting it there too.
        with ec2.serve_model(model):
            self.harness.run_replicates(
                model,
                extra_args=extra_args,
                max_parallel=max_parallel,
                request_timeout=request_timeout,
                # Captured INSIDE the serve block so the snapshot describes
                # the box that actually serves these replicates; stamped on
                # every stored Marks (never raises -- see ec2.server_config).
                server_config=ec2.server_config(model),
            )

    def summarize(self, model: str) -> None:
        """Print per-info-type totals for ``model`` over every stored replicate.

        A pure ``ReplicateHarness.summarize`` delegate: applies no environment
        and spends no EC2/inference cost, but issues S3 reads under an
        S3-backed store. ``model`` must be a key of ``archetype_tags``;
        ``KeyError`` otherwise.
        """
        self.harness.summarize(model)

    def cot_chain_lengths(self, tag: str = "cot") -> None:
        """Print reasoning-chain word-count stats from the stored CoT replicates.

        A pure ``ReplicateHarness.cot_chain_lengths`` delegate: applies no
        environment and spends no EC2/inference cost, but issues S3 reads
        under an S3-backed store. ``tag`` selects which archetype's stored
        replicates to scan; every CoT archetype is tagged "cot".
        """
        self.harness.cot_chain_lengths(tag)

    def agent_status(self) -> Dict[str, Any]:
        """Return the provisioned instance's control-agent status.

        LIVE AWS call. Container state, health and recent docker logs, for
        diagnosing a stuck ``run()``/``provision()`` without re-triggering
        either. Returns ``ec2.agent_status()``'s value verbatim, and raises its
        ``RuntimeError`` if no instance has been provisioned yet.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        return ec2.agent_status()

    def teardown(self) -> None:
        """Terminate this experiment's EC2 spot instance and clear its state.

        LIVE AWS call. Calls ``ec2.shutdown_instance()`` with no overrides;
        safe even if provisioning failed or the state file was lost, since
        ``shutdown_instance`` falls back to the ``smolbench:experiment``
        instance tag. The family-ladder study invokes this only behind an
        explicit ``--teardown`` flag, because ``scripts/fleet/run_fleet.py``
        owns teardown there (with ``scripts/fleet/fleet_teardown.py`` as a
        safety net).
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        return ec2.shutdown_instance()
