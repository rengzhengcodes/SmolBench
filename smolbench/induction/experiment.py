"""Provide one facade over the induction eval harness and EC2 lifecycle.

:class:`InductionExperiment` bundles the induction eval harness with the EC2
spot-instance lifecycle that serves the models under test. A caller supplies
only its experiment-specific config (results directory name, archetype tags,
quiz factory, replicate count, optional EC2 state-file namespace) and calls
``provision()`` / ``run(model, ...)`` / ``summarize(model)`` / ``teardown()``.
The family-ladder scaling study drives this from a plain script:
``notebooks/induction/run_study.py`` builds one module-level
``EXPERIMENT = InductionExperiment(...)``, launched per lane by
``scripts/fleet/run_fleet.py``.

Seed convention
----------------
A "replicate" is the SAME quiz regenerated under a fresh seed. The seed
drives both the quiz's own randomness (label/interval/color sampling; see
``PeriodicConfig.seed`` / ``ChromaticIntervalsConfig.seed``) AND, in the
very same call, gets threaded through as the per-request decoding seed.
This double duty is deliberate. It is what makes a replicate's on-disk
artifact (``rep_{seed}.yaml``) fully reproducible from its filename alone:
regenerating ``make_quizzes(seed, model)`` gives byte-identical prompts,
and the recorded decoding seed tells you exactly what was asked for. (The
model is part of that call because the noise arm is padded to an exact
token count under the model's own tokenizer. A rep file's DIRECTORY already
names the archetype it belongs to, so a replicate stays regenerable from
its path.) ``seeds`` is always
``tuple(base_seed + r for r in range(n_replicates))``, so replicate 0 uses
``base_seed`` itself. The current family-ladder study
overrides it to ``base_seed=0`` on purpose, so its own seed range (0..29)
can never alias a sibling study's 1776-based range; see
``notebooks/induction/run_study.py``'s ``BASE_SEED`` comment.

Results layout and resume semantics
------------------------------------
Every (archetype, info type, seed) replicate is addressed by a
``smolbench.evals.results_store.ReplicateAddress`` (archetype tag, info
type, seed, and, for the S3 backend only, model id). See
:class:`~smolbench.evals.replicates.ReplicateHarness` for the pooling and
resume-skip mechanics (delegated to unchanged here). ``prefix`` exists so
more than one experiment can share one ``results_dir`` without their
replicates colliding.

A choice between local disk and S3 decides where a replicate actually
lives. :func:`smolbench.evals.results_store.resolve_store` makes that
choice from ``results_dir`` and ``prefix``, keyed off
``SMOLBENCH_RESULTS_S3=s3://<bucket>[/<base-prefix>]`` (unset or empty
selects the local store; set, it selects S3) and
``SMOLBENCH_RESULTS_S3_REGION`` (default: ``AWS_REGION``, else boto3's own
resolution chain). Both env vars are read at call time.

The LOCAL layout is
``{prefix}{tag}_{info}/rep_{seed}.yaml`` under ``results_dir``, one file
per replicate, overwritten on rerun. Every analysis script, notebook, and
already-committed results tree depends on this shape staying exactly as it
is.

The S3 layout is a clean, APPEND-ONLY EXPERIMENT LOG, organized by model,
seed, and collection time. It is NOT a mirror of the local tree::

    <base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml

``results_store.experiment_name`` derives ``experiment`` from
``results_dir``: ``repo_root()/notebooks/<notebook_dir>/results`` maps to
``<notebook_dir>``, with ``prefix`` (e.g. ``"one_hop_"``) folded in as a
sub-level with its trailing ``"_"`` stripped. So ``notebook_dir="induction"``,
``prefix="one_hop_"`` maps to ``"induction/one_hop"``. ``run_ts`` is a
fixed-width UTC ``YYYYMMDDTHHMMSSZ`` stamp, so lexicographic key order is
chronological order. A worked example: ``notebook_dir="induction"``,
model ``"gemma-4-12b"``, seed 0, info ``"extens"``, empty base prefix::

    induction/gemma-4-12b/seed=0/extens--20260810T193000Z.yaml

A run NEVER overwrites a prior run's object in the S3 log. Re-running an
experiment APPENDS a new timestamped object rather than replacing anything,
so a superseded verdict stays recoverable as log history instead of being
destroyed. Every READ path (``summarize()``, ``cot_chain_lengths()``,
``harness.sync_down()``) resolves the EARLIEST ``run_ts`` per (model,
seed, info) and treats only that one as live. The first logged run is the
pass@1 measurement, and later re-collections are log history.

``InductionExperiment.harness.sync_down()`` translates an S3-backed
experiment's append-only log back into the local layout above, for tooling
(``notebooks/*/analysis/power_analysis.py``, the figure scripts) that reads
a local tree and is not itself store-aware. It supplies this experiment's own
``archetype_tags`` as the model-to-tag mapping the log cannot carry (a log
key names a model, never a tag). See
``smolbench.evals.results_store.sync_down`` for the full contract,
including why this is a translation rather than a mirror, and why it
remains a one-way, destructive S3-to-local operation.

Cost warning
-------------
``provision()``, ``run()``, ``agent_status()``, and ``teardown()`` are LIVE
AWS calls against a self-provisioned EC2 spot instance, billed for the
duration it is up (~$30-45/h for the p5e/p5 family at the time of writing;
see ``smolbench/evals/providers/ec2.py``). ``summarize()`` and ``cot_chain_lengths()``
never touch EC2 or inference spend. But with an S3-backed results store
(see "Results layout and resume semantics" above) they DO issue S3 reads
(``list_objects_v2``/``get_object`` per replicate). So "never touch AWS or
the network" is only true for the default local store.

CRITICAL: no ``smolbench.evals.providers.ec2`` import at module scope
---------------------------------------------------------------------
This module must NOT ``import smolbench.evals.providers.ec2`` at the top level, and
none of its lazy imports may be hoisted there either. ``ec2.py``'s own
module docstring documents that its ``EC2_*`` module-level constants
(``EC2_EXPERIMENT_TAG``, ``EC2_INSTANCE_TYPES``, ...) are captured at
IMPORT time from ``os.environ``. They are deliberately ordinary module
attributes, not call-time getters, because a caller reads them back as
``ec2.EC2_EXPERIMENT_TAG`` etc. Every notebook's or script's first cell (or
top-level code) calls ``load_dotenv(keys.env)`` to populate those variables
(e.g. ``EC2_EXPERIMENT_TAG=chromatic-induction``) BEFORE
``smolbench.evals.providers.ec2`` is ever imported. If this facade imported ``ec2``
eagerly, then code that executes ``import smolbench.induction.experiment``
ahead of its ``load_dotenv`` call (a perfectly ordinary import order) would
freeze those constants to their un-overridden defaults for the rest of the
process's life, with no error to signal it. Every method below that needs
the EC2 lifecycle therefore does ``from smolbench.evals.providers import ec2`` INSIDE
the method body, after ``_apply_env()`` has run and after the caller has
had every opportunity to ``load_dotenv`` first. (Importing
``smolbench.evals.replicates`` at module scope is safe: it only imports
``smolbench.evals.provider``, whose provider dispatch is itself resolved at
CALL time, not import time -- see that module's docstring.)
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

    This class bundles a :class:`~smolbench.evals.replicates.ReplicateHarness`
    (results layout + quiz factory) with the EC2 spot-instance lifecycle
    (``smolbench.evals.providers.ec2``) that serves the models under test. A caller
    then only needs to construct one ``InductionExperiment`` and call its
    methods in the lifecycle order documented on each one: ``provision()``
    once, ``run(model, ...)`` once per archetype section,
    ``summarize(model)`` / ``cot_chain_lengths()`` any number of times
    (offline), ``teardown()`` once at the end.

    This class is frozen, like ``ReplicateHarness``: an experiment's
    configuration should not mutate mid-run. The one exception is
    ``harness``, a ``functools.cached_property``. See that property's
    docstring for why a cached, lazily-built attribute is safe on a frozen
    dataclass.
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

        Unsharded, this is ``base_seed``, ``base_seed + 1``, ... Sharded,
        it is every ``count``-th one, starting at ``index``.

        Returns
        -------
        Tuple[int, ...]
            Length ``n_replicates`` unsharded. Replicate ``r``'s seed is
            ``base_seed + r``. This same value both regenerates replicate
            ``r``'s quiz (see the module docstring's seed convention) and
            gets sent as the per-request decoding seed. So a seed means the
            same replicate no matter which shard collects it.

        Notes
        -----
        Shards stride (``r % count == index``) rather than take contiguous
        blocks. This stride keeps the shards within one replicate of each
        other in size when ``count`` does not divide ``n_replicates``: 30
        seeds over 4 shards splits 8/8/7/7 instead of 8/8/8/6. This matters
        because the slowest shard sets the wall-clock time the sharding was
        meant to reduce. Every replicate lands in exactly one shard, so
        parallel shards never contend for the same ``rep_{seed}.yaml``.
        """
        every = tuple(self.base_seed + r for r in range(self.n_replicates))
        if self.shard is None:
            return every
        index, count = self.shard
        return tuple(s for r, s in enumerate(every) if r % count == index)

    @property
    def results_dir(self) -> Path:
        """Return where this experiment's replicate YAML files live.

        Returns
        -------
        Path
            ``repo_root() / "notebooks" / notebook_dir / "results"``. Never
            cwd-relative; see ``repo_root()``.
        """
        return repo_root() / "notebooks" / self.notebook_dir / "results"

    @functools.cached_property
    def harness(self) -> ReplicateHarness:
        """Return the :class:`ReplicateHarness` built from this experiment's config.

        Design: ``functools.cached_property`` works on a frozen dataclass,
        even though ``@dataclass(frozen=True)`` overrides ``__setattr__`` to
        raise ``FrozenInstanceError``. ``cached_property.__get__`` writes
        the computed value directly into ``instance.__dict__`` on first
        access. This bypasses ``__setattr__`` entirely; it does not call
        it. A frozen dataclass instance still has that ``__dict__``, since
        ``frozen=True`` alone does not add ``__slots__``. This property
        builds the harness once and reuses it, because ``ReplicateHarness``
        is itself immutable and cheap to share. There is no reason for every
        ``run()``/``summarize()`` call to reconstruct it. A reconstruction
        would be observably different on retry only if
        ``seeds``/``archetype_tags``/etc. changed, which a frozen dataclass
        forbids anyway.

        Returns
        -------
        ReplicateHarness
            Configured with this experiment's ``results_dir``,
            ``archetype_tags``, ``make_quizzes``, ``seeds``, ``info_types``,
            and ``prefix``.
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

        Sets ``INFERENCE_PROVIDER=ec2``, so ``smolbench.evals.provider``
        dispatches to the EC2 vLLM provider (read at CALL time; see that
        module's docstring). So it is safe to set this right before use,
        rather than before import. When ``state_file`` is configured, this
        method also points ``EC2_STATE_FILE`` (also read at call time, per
        ``ec2.py``'s "Env-read timing" docstring section) at this
        experiment's private, repo-root-anchored state file.

        When ``state_file`` is None, this method EXPLICITLY POPS
        ``EC2_STATE_FILE``, rather than leaving whatever was there. Design:
        this makes the facade deterministic regardless of call order within
        one process. Without the pop, running an experiment that sets
        ``EC2_STATE_FILE`` and then one with ``state_file=None`` in the
        same session would leave the second experiment silently talking to
        the first experiment's instance state file. The ``state_file=None``
        experiment instead relies on ``ec2.py``'s own default state path (a
        fixed location at the repo root), which is exactly what popping the
        override restores.

        Returns
        -------
        None
        """
        os.environ["INFERENCE_PROVIDER"] = "ec2"
        if self.state_file is not None:
            os.environ["EC2_STATE_FILE"] = str(repo_root() / self.state_file)
        else:
            os.environ.pop("EC2_STATE_FILE", None)

    def provision(self) -> Dict[str, Any]:
        """Provision, or reattach to, this experiment's EC2 spot instance.

        Applies this experiment's env (provider + optional state-file
        namespace), then provisions with no argument overrides. This method
        always calls ``provision_spot_instance()`` bare, relying entirely on
        the ``EC2_*`` environment for instance types/regions/volume/idle
        timeout/max lifetime, and prints a one-line instance summary.

        Notes
        -----
        Live AWS call; see the module docstring's cost warning. Imports
        ``smolbench.evals.providers.ec2`` lazily; see the module docstring's CRITICAL
        section for why that import cannot be hoisted to module scope.

        Returns
        -------
        Dict[str, Any]
            The provisioned instance's state dict (``instance_id``,
            ``region``, ``public_ip``, ``instance_type``,
            ``availability_zone``, ``control_token``, ``vllm_api_key``,
            ...), identical to ``ec2.provision_spot_instance()``'s return
            value -- also persisted to ``EC2_STATE_FILE`` as a side effect
            of that call.
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

        Swaps the provisioned instance's vLLM container to ``model``
        (``ec2.serve_model`` is idempotent; it
        skips the swap when the instance already serves it unchanged), and,
        while it is up, runs every info type's outstanding replicates via
        ``self.harness.run_replicates``. Safe to re-run after an
        interruption: both ``serve_model`` and ``run_replicates`` are
        idempotent and resumable on their own.

        Parameters
        ----------
        model : str
            The archetype's model id. Must be a key of ``archetype_tags``
            (``run_replicates`` raises ``KeyError`` immediately otherwise;
            see ``ReplicateHarness.run_replicates``) and of
            ``smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS`` (``serve_model`` raises
            its own ``KeyError`` otherwise).
        extra_args : dict, optional
            Extra chat-completions request-body fields (e.g. a CoT
            archetype's ``{"max_completion_tokens": 16384}``). Passed
            through to ``run_replicates`` UNCHANGED. None (the default)
            means "no override", exactly as if the caller had not passed
            this parameter at all.
        max_parallel : int, optional
            Fan-out cap override (CoT archetypes widen this; see
            ``ReplicateHarness.run_replicates``). Passed through unchanged.
        request_timeout : int, optional
            Per-request read-timeout override in seconds (CoT archetypes
            raise this, so the longest reasoning chain finishes on attempt
            1). Passed through unchanged.

        Notes
        -----
        Live AWS call (the ``serve_model`` container swap), followed by
        live inference calls. Imports ``smolbench.evals.providers.ec2`` lazily; see
        the module docstring's CRITICAL section.

        Returns
        -------
        None
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

        This is a pure ``ReplicateHarness.summarize`` delegate: it applies
        no environment and spends no EC2/inference cost. But it reads
        through ``ReplicateHarness.store``, which issues S3 requests
        instead of local reads when this experiment's ``results_dir``
        resolves to an S3-backed store (see the module docstring's
        "Results layout and resume semantics" section).

        Parameters
        ----------
        model : str
            Must be a key of ``archetype_tags`` (``KeyError`` otherwise).

        Returns
        -------
        None
        """
        self.harness.summarize(model)

    def cot_chain_lengths(self, tag: str = "cot") -> None:
        """Print reasoning-chain word-count stats from the stored CoT replicates.

        This is a pure ``ReplicateHarness.cot_chain_lengths`` delegate: it
        applies no environment and spends no EC2/inference cost. But it
        reads through ``ReplicateHarness.store``, which issues S3 requests
        instead of local reads when this experiment's ``results_dir``
        resolves to an S3-backed store (see the module docstring's
        "Results layout and resume semantics" section).

        Parameters
        ----------
        tag : str, default "cot"
            Archetype tag whose cached replicates to scan; every CoT
            archetype is tagged "cot".

        Returns
        -------
        None
        """
        self.harness.cot_chain_lengths(tag)

    def agent_status(self) -> Dict[str, Any]:
        """Return the provisioned instance's control-agent status.

        Reports container state, health, and recent docker logs. This is
        useful for diagnosing a stuck ``run()``/``provision()`` call
        without re-triggering either.

        Notes
        -----
        Live AWS call. Imports ``smolbench.evals.providers.ec2`` lazily; see the
        module docstring's CRITICAL section.

        Returns
        -------
        Dict[str, Any]
            Identical to ``ec2.agent_status()``'s return value.

        Raises
        ------
        RuntimeError
            If this experiment has not yet provisioned an instance (propagated from
            ``ec2.agent_status()``'s internal ``_require_state()``).
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        return ec2.agent_status()

    def teardown(self) -> None:
        """Terminate this experiment's EC2 spot instance and clear its state.

        Applies this experiment's env, then calls ``ec2.shutdown_instance()``
        with no argument overrides. Safe to call even if provisioning
        already failed or the state file was lost: ``shutdown_instance``
        falls back to the ``smolbench:experiment`` instance tag. The
        current family-ladder study calls this method itself only behind
        an explicit ``--teardown`` flag: the fleet supervisor
        (``scripts/fleet/run_fleet.py``) owns instance teardown end-to-end for
        that study, with ``scripts/fleet/fleet_teardown.py`` as a safety net (see
        ``notebooks/induction/run_study.py``'s module docstring).

        Notes
        -----
        Live AWS call. Imports ``smolbench.evals.providers.ec2`` lazily; see the
        module docstring's CRITICAL section.

        Returns
        -------
        None
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        return ec2.shutdown_instance()
