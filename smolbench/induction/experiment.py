"""
Per-notebook facade over the induction eval harness + EC2 lifecycle.

Three notebooks (``notebooks/periodic/induction_eval.ipynb``,
``notebooks/chromatic/induction_eval.ipynb``, and
``notebooks/chromatic/induction_eval_one_hop.ipynb``) each hand-copied the
same handful of cells: build a :class:`~smolbench.evals.replicates.
ReplicateHarness`, provision an EC2 spot instance, run each archetype's
replicates inside a ``serve_model`` block, and tear the instance down.
:class:`InductionExperiment` collects that copy-pasted glue into one
dataclass so a notebook only supplies its experiment-specific config
(results directory name, archetype tags, quiz factory, replicate count,
optional EC2 state-file namespace) and calls
``provision()`` / ``run(model, ...)`` / ``summarize(model)`` / ``teardown()``.

Seed convention
----------------
A "replicate" is the SAME quiz regenerated under a fresh seed: the seed
drives both the quiz's own randomness (label/interval/color sampling --
see ``PeriodicConfig.seed`` / ``ChromaticIntervalsConfig.seed``) AND, in the
very same call, is threaded through as the per-request decoding seed. This
double duty is deliberate -- it is what makes a replicate's on-disk artifact
(``rep_{seed}.yaml``) fully reproducible from its filename alone: regenerate
``make_quizzes(seed, model)`` and you get byte-identical prompts, and the
recorded decoding seed tells you exactly what was asked for. (The model is
part of that call because the noise arm is padded to an exact token count
under the model's own tokenizer; a rep file's DIRECTORY already names the
archetype it belongs to, so a replicate stays regenerable from its path.)
``seeds`` is always
``tuple(base_seed + r for r in range(n_replicates))`` -- replicate 0 uses
``base_seed`` itself, matching every notebook's original preliminary run.

Results layout and resume semantics
------------------------------------
Every (archetype, info type, seed) replicate is addressed by a
``smolbench.evals.results_store.ReplicateAddress`` (archetype tag, info
type, seed, and -- for the S3 backend only -- model id) -- see
:class:`~smolbench.evals.replicates.ReplicateHarness` for the pooling and
resume-skip mechanics (delegated to unchanged here). ``prefix`` exists so
more than one experiment can share one ``results_dir`` without their
replicates colliding (``induction_eval_one_hop.ipynb`` sets
``prefix="one_hop_"`` to share ``notebooks/chromatic/results`` with
``induction_eval.ipynb``).

Where a replicate actually lives -- local disk or S3 -- is decided by
:func:`smolbench.evals.results_store.resolve_store` (``results_dir``,
``prefix``), keyed off ``SMOLBENCH_RESULTS_S3=s3://<bucket>[/<base-prefix>]``
(unset/empty selects the local store; set, it selects S3) and
``SMOLBENCH_RESULTS_S3_REGION`` (defaulting to ``AWS_REGION``, else boto3's
own resolution chain), both read at call time.

The LOCAL layout is unchanged and byte-identical to every prior release:
``{prefix}{tag}_{info}/rep_{seed}.yaml`` under ``results_dir`` -- one file
per replicate, overwritten on rerun. Every analysis script, notebook, and
already-committed results tree depends on this shape staying exactly as it
is.

The S3 layout is a clean, APPEND-ONLY EXPERIMENT LOG organised by model,
seed, and collection time -- NOT a mirror of the local tree::

    <base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml

``experiment`` is derived from ``results_dir`` by
``results_store.experiment_name``: ``repo_root()/notebooks/<notebook_dir>/
results`` maps to ``<notebook_dir>``, with ``prefix`` (e.g. ``"one_hop_"``)
folded in as a sub-level with its trailing ``"_"`` stripped --
``notebook_dir="chromatic"``, ``prefix="one_hop_"`` therefore maps to
``"chromatic/one_hop"``. ``run_ts`` is a fixed-width UTC
``YYYYMMDDTHHMMSSZ`` stamp, so lexicographic key order is chronological
order. A worked example -- ``notebook_dir="periodic_moe"``, model
``"gpt-oss-120b"``, seed 1776, info ``"extens"``, empty base prefix::

    periodic_moe/gpt-oss-120b/seed=1776/extens--20260810T193000Z.yaml

A run NEVER overwrites a prior run's object in the S3 log -- re-running an
experiment APPENDS a new timestamped object rather than replacing anything,
so a superseded verdict stays recoverable as log history rather than being
destroyed. Every READ path (``summarize()``, ``cot_chain_lengths()``,
``harness.sync_down()``) resolves the LATEST ``run_ts`` per (model, seed,
info) and treats only that one as live.

``InductionExperiment.harness.sync_down()`` translates an S3-backed
experiment's append-only log back into the local layout above, for tooling
(``power_analysis.py``, the figure scripts) that reads a local tree and is
not itself store-aware -- it supplies this experiment's own
``archetype_tags`` as the model -> tag mapping the log cannot carry (a log
key names a model, never a tag). See
``smolbench.evals.results_store.sync_down`` for the full contract
(including why this is a translation rather than a mirror, and why it
remains a one-way, destructive S3 -> local operation).

Cost warning
-------------
``provision()``, ``run()``, ``agent_status()``, and ``teardown()`` are LIVE
AWS calls against a self-provisioned EC2 spot instance billed for the
duration it is up (~$30-45/h for the p5e/p5 family at the time of writing --
see ``smolbench/evals/ec2.py``). ``summarize()`` and ``cot_chain_lengths()``
never touch EC2 or inference spend -- but with an S3-backed results store
(see "Results layout and resume semantics" above) they DO issue S3 reads
(``list_objects_v2``/``get_object`` per replicate), so "never touch AWS or
the network" is only true for the default local store; the point of this
warning -- that these two calls cannot trigger GPU billing -- still holds
either way.

CRITICAL: no ``smolbench.evals.ec2`` import at module scope
--------------------------------------------------------------
This module must NOT ``import smolbench.evals.ec2`` at the top level, and
none of its lazy imports may be hoisted there either. ``ec2.py``'s own
module docstring documents that its ``EC2_*`` module-level constants
(``EC2_EXPERIMENT_TAG``, ``EC2_INSTANCE_TYPES``, ... ) are captured at
IMPORT time from ``os.environ`` -- they are deliberately ordinary module
attributes, not call-time getters, because notebooks read them back as
``ec2.EC2_EXPERIMENT_TAG`` etc. Every notebook's first cell calls
``load_dotenv(keys.env)`` to populate those variables (e.g.
``EC2_EXPERIMENT_TAG=chromatic-induction``) BEFORE ``smolbench.evals.ec2``
is ever imported. If this facade imported ``ec2`` eagerly, then a notebook
executing ``import smolbench.induction.experiment`` ahead of its
``load_dotenv`` call (a perfectly ordinary cell order) would freeze those
constants to their un-overridden defaults for the rest of the kernel's
life, with no error to signal it. Every method below that needs the EC2
lifecycle therefore does ``from smolbench.evals import ec2`` INSIDE the
method body, after ``_apply_env()`` has run and after the caller has had
every opportunity to ``load_dotenv`` first. (Importing
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


# Canonical definition now lives in smolbench.evals.results_store: the
# results store maps a repo-anchored results directory onto an S3 key
# prefix, and needs this same repo-root anchor to do it. Re-exported here so
# every existing `from smolbench.induction.experiment import repo_root`
# caller (including this module's own uses below) keeps working unchanged.
from smolbench.evals.results_store import repo_root  # noqa: F401 -- re-exported


@dataclass(frozen=True)
class InductionExperiment:
    """One notebook's replicated-evaluation experiment, EC2 lifecycle included.

    Bundles a :class:`~smolbench.evals.replicates.ReplicateHarness` (results
    layout + quiz factory) with the EC2 spot-instance lifecycle
    (``smolbench.evals.ec2``) that serves the models under test, so a
    notebook cell reduces to constructing one ``InductionExperiment`` and
    then calling its methods in the lifecycle order documented on each one:
    ``provision()`` once, ``run(model, ...)`` once per archetype section,
    ``summarize(model)`` / ``cot_chain_lengths()`` any number of times
    (offline), ``teardown()`` once at the end.

    Frozen like ``ReplicateHarness``: an experiment's configuration should
    not mutate mid-notebook. The one exception is ``harness``, a
    ``functools.cached_property`` -- see that property's docstring for why
    a cached, lazily-built attribute is safe on a frozen dataclass.
    """

    #: Which notebook this experiment belongs to -- "periodic" or
    #: "chromatic" -- used only to locate results:
    #: ``repo_root()/notebooks/<notebook_dir>/results``. The one-hop
    #: chromatic notebook also uses "chromatic" (see ``prefix`` below for
    #: how it avoids colliding with the sibling experiment).
    notebook_dir: str
    #: Model name -> short archetype tag used in result directory names
    #: (e.g. ``{"olmo-3.1-32b-instruct": "decode"}``). Forwarded verbatim to
    #: ``ReplicateHarness``.
    archetype_tags: Mapping[str, str]
    #: (seed, model) -> {info type: quiz}. Forwarded verbatim to
    #: ``ReplicateHarness``; see that class for why this is called lazily per
    #: outstanding seed rather than eagerly for every seed up front, and why
    #: it takes the model (the noise arm is token-matched with the tokenizer
    #: of the model under test, so only that arm varies per model).
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    #: Number of replicate seeds. Every notebook currently uses 30 (see
    #: each notebook's ``power_analysis.py``-backed replication-setup
    #: comment for the derivation).
    n_replicates: int = 30
    #: First replicate's seed; replicate 0 uses this seed exactly, matching
    #: every notebook's original preliminary run (seed 1776 == the July 4th,
    #: 1776 nod baked into every notebook to date).
    base_seed: int = 1776
    #: Info types evaluated per replicate, in serialization order. Forwarded
    #: verbatim to ``ReplicateHarness``.
    info_types: Tuple[str, ...] = ("intens", "extens", "noise_intens")
    #: Optional namespace prefix on result directory names (e.g.
    #: ``"one_hop_"``) so more than one experiment can share one
    #: ``results_dir`` without their replicate directories colliding.
    #: Forwarded verbatim to ``ReplicateHarness``.
    prefix: str = ""
    #: Repo-root-anchored basename (e.g. ``".ec2_state_chromatic.json"``)
    #: for this experiment's EC2 state file, or None to use ``ec2.py``'s own
    #: default (the periodic experiment shares that default; only the
    #: chromatic experiments need a private state file to avoid clobbering
    #: each other's instance record -- see ``_apply_env``).
    state_file: Optional[str] = None
    #: ``(index, count)`` selecting a disjoint slice of the replicates, so N
    #: processes on N instances can collect one model's replicates in
    #: parallel; None (the default) means this process runs all of them.
    #:
    #: Sharding is what removes the LAST serialisation in a study. Splitting
    #: by model already lets three checkpoints run at once, but a single
    #: model's 30 replicates still run one after another on one box, so
    #: wall-clock is set by the slowest model alone. Shards divide that too.
    #:
    #: Replicates are independent by construction -- each is a fresh
    #: ``PeriodicConfig`` seed, and results are keyed by (tag, info, seed) --
    #: so no coordination is needed BEYOND disjointness, which
    #: ``seeds`` guarantees.
    shard: Optional[Tuple[int, int]] = None
    #: Forwarded to ``ReplicateHarness.force_seeds``: seeds whose replicates
    #: are re-collected and re-logged past the resume-skip (newest run_ts
    #: supersedes on read). ``None`` disables. For deliberate re-collection
    #: only.
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
        """The replicate seeds this process is responsible for.

        Unsharded that is ``base_seed``, ``base_seed + 1``, ... Sharded it is
        every ``count``-th one starting at ``index``.

        Returns
        -------
        Tuple[int, ...]
            Length ``n_replicates`` unsharded. Replicate ``r``'s seed is
            ``base_seed + r`` -- this same value both regenerates replicate
            ``r``'s quiz (see the module docstring's seed convention) and is
            sent as the per-request decoding seed, so a seed means the same
            replicate no matter which shard collects it.

        Notes
        -----
        Shards stride (``r % count == index``) rather than taking contiguous
        blocks. Striding keeps the shards within one replicate of each other
        in size when ``count`` does not divide ``n_replicates`` -- 30 seeds
        over 4 shards splits 8/8/7/7 instead of 8/8/8/6 -- which matters
        because the slowest shard sets the wall-clock the sharding was meant
        to reduce. Every replicate lands in exactly one shard, so parallel
        shards never contend for the same ``rep_{seed}.yaml``.
        """
        every = tuple(self.base_seed + r for r in range(self.n_replicates))
        if self.shard is None:
            return every
        index, count = self.shard
        return tuple(s for r, s in enumerate(every) if r % count == index)

    @property
    def results_dir(self) -> Path:
        """Where this experiment's replicate YAML files live.

        Returns
        -------
        Path
            ``repo_root() / "notebooks" / notebook_dir / "results"``. Never
            cwd-relative -- see ``repo_root()``.
        """
        return repo_root() / "notebooks" / self.notebook_dir / "results"

    @functools.cached_property
    def harness(self) -> ReplicateHarness:
        """The :class:`ReplicateHarness` built from this experiment's config.

        Design: ``functools.cached_property`` works on a frozen dataclass
        even though ``@dataclass(frozen=True)`` overrides ``__setattr__`` to
        raise ``FrozenInstanceError`` -- ``cached_property.__get__`` writes
        the computed value directly into ``instance.__dict__`` on first
        access (bypassing ``__setattr__`` entirely, not calling it), which a
        frozen dataclass instance still has since ``frozen=True`` alone does
        not add ``__slots__``. Building this once and reusing it matters
        because ``ReplicateHarness`` is itself immutable and cheap to
        share -- there is no reason for every ``run()``/``summarize()`` call
        to reconstruct it, and reconstruction would be observably different
        on retry only if ``seeds``/``archetype_tags``/etc. changed, which a
        frozen dataclass forbids anyway.

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
        """Sets the environment ``smolbench.evals.ec2`` reads at call time.

        Sets ``INFERENCE_PROVIDER=ec2`` so ``smolbench.evals.provider``
        dispatches to the EC2 vLLM provider (read at CALL time -- see that
        module's docstring -- so it is safe to set this right before use
        rather than before import). When ``state_file`` is configured, also
        points ``EC2_STATE_FILE`` (also read at call time, per ``ec2.py``'s
        "Env-read timing" docstring section) at this experiment's private,
        repo-root-anchored state file.

        When ``state_file`` is None, EXPLICITLY POPS ``EC2_STATE_FILE``
        rather than leaving whatever was there. Design: this makes the
        facade deterministic regardless of call order within one kernel --
        without the pop, running a chromatic experiment (which sets
        ``EC2_STATE_FILE``) and then a periodic experiment (``state_file=
        None``) in the same session would leave the periodic experiment
        silently talking to the chromatic instance's state file. The
        periodic experiment instead relies on ``ec2.py``'s own default
        state path (a fixed location at the repo root), which is exactly
        what popping the override restores.

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
        """Provisions (or reattaches to) this experiment's EC2 spot instance.

        Mirrors the notebooks' "Provision" cell exactly: applies this
        experiment's env (provider + optional state-file namespace), then
        provisions with no argument overrides (every notebook calls
        ``provision_spot_instance()`` bare, relying entirely on the
        ``EC2_*`` environment for instance types/regions/volume/idle
        timeout/max lifetime), and prints the same one-line instance
        summary the notebooks do.

        Notes
        -----
        Live AWS call -- see the module docstring's cost warning. Imports
        ``smolbench.evals.ec2`` lazily; see the module docstring's CRITICAL
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
        from smolbench.evals import ec2

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
        """Serves ``model`` and runs every outstanding replicate against it.

        Mirrors an archetype section cell: swaps the provisioned instance's
        vLLM container to ``model`` (``ec2.serve_model`` is idempotent --
        the swap is skipped if the instance is already serving it
        unchanged) and, while it is up, runs every info type's outstanding
        replicates via ``self.harness.run_replicates``. Safe to re-run after
        an interruption: both ``serve_model`` and ``run_replicates`` are
        idempotent/resumable on their own.

        Parameters
        ----------
        model:
            The archetype's model id -- must be a key of ``archetype_tags``
            (``run_replicates`` raises ``KeyError`` immediately otherwise;
            see ``ReplicateHarness.run_replicates``) and of
            ``smolbench.evals.ec2.EC2_DEPLOY_SPECS`` (``serve_model`` raises
            its own ``KeyError`` otherwise).
        extra_args:
            Extra chat-completions request-body fields (e.g. a CoT
            archetype's ``{"max_completion_tokens": 16384}``). Passed
            through to ``run_replicates`` UNCHANGED -- None (the default)
            means "no override", exactly as if this parameter had not been
            passed at all.
        max_parallel:
            Fan-out cap override (CoT archetypes widen this; see
            ``ReplicateHarness.run_replicates``). Passed through unchanged.
        request_timeout:
            Per-request read-timeout override in seconds (CoT archetypes
            raise this so the longest reasoning chain finishes on attempt
            1). Passed through unchanged.

        Notes
        -----
        Live AWS call (the ``serve_model`` container swap) followed by live
        inference calls. Imports ``smolbench.evals.ec2`` lazily; see the
        module docstring's CRITICAL section.

        Returns
        -------
        None
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals import ec2

        # Nothing to do => do not SERVE. Entering serve_model swaps the
        # instance's vLLM container to this checkpoint, which for the large
        # archetypes means pulling and loading hundreds of GB; doing that to
        # then discover every replicate is already on disk is pure billed
        # time. Hit for real on a resumed run, where the completed arms are
        # re-served before the outstanding one is reached.
        if not self.harness.has_outstanding(model):
            logging.info(
                f"run: {model!r} has no outstanding replicates; skipping serve"
            )
            return

        # Design: forward exactly what the caller passed, with no filtering
        # here -- ReplicateHarness.run_replicates already implements
        # "only forward what's given" at the evaluate() call level (it only
        # populates its own eval_kwargs for non-None values), so passing
        # None through for an omitted parameter is behaviorally identical to
        # omitting it there too.
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
        """Prints per-info-type totals for ``model`` over every stored replicate.

        Pure ``ReplicateHarness.summarize`` delegate: no environment
        applied, no EC2/inference spend -- but reads through
        ``ReplicateHarness.store``, which issues S3 requests instead of
        local reads when this experiment's ``results_dir`` resolves to an
        S3-backed store (see the module docstring's "Results layout and
        resume semantics" section).

        Parameters
        ----------
        model:
            Must be a key of ``archetype_tags`` (``KeyError`` otherwise).

        Returns
        -------
        None
        """
        self.harness.summarize(model)

    def cot_chain_lengths(self, tag: str = "cot") -> None:
        """Prints reasoning-chain word-count stats from the stored CoT replicates.

        Pure ``ReplicateHarness.cot_chain_lengths`` delegate: no environment
        applied, no EC2/inference spend -- but reads through
        ``ReplicateHarness.store``, which issues S3 requests instead of
        local reads when this experiment's ``results_dir`` resolves to an
        S3-backed store (see the module docstring's "Results layout and
        resume semantics" section).

        Parameters
        ----------
        tag:
            Archetype tag whose cached replicates to scan. Defaults to
            "cot", matching every notebook's bare ``cot_chain_lengths()``
            call (all three CoT archetypes are tagged "cot").

        Returns
        -------
        None
        """
        self.harness.cot_chain_lengths(tag)

    def agent_status(self) -> Dict[str, Any]:
        """Returns the provisioned instance's control-agent status.

        Container state, health, and recent docker logs -- useful for
        diagnosing a stuck ``run()``/``provision()`` from the notebook
        without re-triggering either.

        Notes
        -----
        Live AWS call. Imports ``smolbench.evals.ec2`` lazily; see the
        module docstring's CRITICAL section.

        Returns
        -------
        Dict[str, Any]
            Identical to ``ec2.agent_status()``'s return value.

        Raises
        ------
        RuntimeError
            No instance has been provisioned yet (propagated from
            ``ec2.agent_status()``'s internal ``_require_state()``).
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals import ec2

        return ec2.agent_status()

    def teardown(self) -> None:
        """Terminates this experiment's EC2 spot instance and clears its state.

        Mirrors the notebooks' final "Teardown" cell exactly: applies this
        experiment's env, then calls ``ec2.shutdown_instance()`` with no
        argument overrides. Safe to call even if provisioning already
        failed or the state file was lost -- ``shutdown_instance`` falls
        back to the ``smolbench:experiment`` instance tag.

        Notes
        -----
        Live AWS call. Imports ``smolbench.evals.ec2`` lazily; see the
        module docstring's CRITICAL section.

        Returns
        -------
        None
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals import ec2

        return ec2.shutdown_instance()
