"""One facade over the eval harness and its EC2 lifecycle, study-NEUTRAL.

:class:`Experiment` bundles :class:`~smolbench.evals.replicates.ReplicateHarness`
with the EC2 spot lifecycle that serves the models under test. A driver builds
one module-level ``EXPERIMENT`` in its own study's ``run_study.py`` and
supplies every study-specific choice through the fields below -- including
``info_types`` and, when the study runs a CoT archetype, the tag
:meth:`Experiment.cot_chain_lengths` scans, both of which have no
study-neutral default and so are required here (a study subclass such as
:class:`~smolbench.induction.experiment.InductionExperiment` supplies its own
defaults for them). Lanes may be launched from that driver directly or under
an external supervisor (``scripts/fleet/run_fleet.py`` -- lands in slice 4).

Seed convention. A "replicate" is the SAME quiz regenerated under a fresh seed.
Unsharded, ``seeds`` is ``tuple(base_seed + r for r in range(n_replicates))``.
Under ``shard=(index, count)`` it STRIDES that tuple instead, keeping the
``r % count == index`` entries, so N shards of one experiment partition the same
seed set without overlapping (see the ``seeds`` property). Either way the seed
drives the quiz's own randomness AND the per-request decoding seed, so a
replicate is reproducible from its ``rep_{seed}.yaml`` path alone.
``make_quizzes`` also takes the model, because a noise arm (where a study has
one) is padded to an exact token count under the model's own tokenizer.

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

from smolbench.evals import Quiz, study_config
from smolbench.evals.replicates import ReplicateHarness


# Canonical definition lives in smolbench.evals.results_store.
from smolbench.evals.results_store import repo_root


@dataclass(frozen=True)
class Experiment:
    """Configure one replicated-evaluation experiment, EC2 lifecycle included.

    Lifecycle order: ``provision()`` once, ``run(model, ...)`` once per
    archetype, ``summarize(model)`` / ``cot_chain_lengths()`` any number of
    times (offline), ``teardown()`` once at the end. Frozen, like
    ``ReplicateHarness``: configuration must not mutate mid-run.

    Study-neutral: every field a study MUST supply its own value for (there is
    no shared default across studies) is declared without a default, ahead of
    the fields below that do have a sensible study-neutral default. A study
    subclass (e.g. ``InductionExperiment``) narrows those required fields to
    its own default by overriding them with a ``field(default=...)``.
    """

    #: Locates results at ``repo_root()/notebooks/<notebook_dir>/results``.
    notebook_dir: str
    #: Model name -> short archetype tag used in result directory names (e.g.
    #: ``{"olmo-3.1-32b-instruct": "decode"}``). Forwarded to ``ReplicateHarness``.
    archetype_tags: Mapping[str, str]
    #: (seed, model) -> {info type: quiz}. Forwarded to ``ReplicateHarness``,
    #: which calls it lazily per outstanding seed. Only a noise arm (where a
    #: study has one) varies per model -- see the module docstring's "Seed
    #: convention" section.
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    # Design: REQUIRED, not defaulted. There is no study-neutral set of
    # information conditions -- the induction three-arm set (intens/extens/
    # noise_intens) is ONE study's choice, and giving it a default here is how
    # that study's prose ended up spelled into a module every other study
    # would inherit from. A subclass with a real default (e.g.
    # ``InductionExperiment``) overrides this field to supply one.
    #: Info types evaluated per replicate, in serialization order. Forwarded to
    #: ``ReplicateHarness``.
    info_types: Tuple[str, ...]
    #: Number of replicate seeds. Every induction study to date uses 30; the
    #: sizing evidence lives in each study's ``analysis/power_analysis.py``.
    n_replicates: int = 30
    #: First replicate's seed; replicate 0 uses it exactly. Default 1776 (the
    #: July 4th nod). A study may override it -- see its own ``run_study.py``.
    base_seed: int = 1776
    #: Optional namespace prefix on result directory names (e.g.
    #: ``"one_hop_"``) so two experiments can share one ``results_dir`` without
    #: their replicate directories colliding. Forwarded to ``ReplicateHarness``.
    prefix: str = ""
    #: Repo-root-anchored basename (e.g. ``".ec2_state_induction.json"``) for
    #: this experiment's EC2 state file, or None to use ``ec2.py``'s default.
    #: Set it whenever two lifecycles could be live at once, so they do not
    #: clobber each other's instance record; see ``_apply_env``. That covers two
    #: different experiments sharing a checkout AND -- the case easily missed --
    #: two SHARDS of ONE experiment, which need one state file EACH. A sharded
    #: run that leaves this at the default gives every shard the same record;
    #: see the ``shard`` field for the failure that produces.
    state_file: Optional[str] = None
    #: ``(index, count)`` selecting a disjoint slice of the replicates, so N
    #: processes on N instances can collect one model's replicates in parallel;
    #: None runs all of them. The RESULTS need no coordination -- replicates are
    #: independent by construction (fresh seed each, results keyed by
    #: (tag, info, seed)) and ``seeds`` hands each shard a disjoint set -- but
    #: the EC2 LIFECYCLE does. Every shard MUST be given its own ``state_file``
    #: AND its own ``EC2_EXPERIMENT_TAG``. Without both, shard 1's
    #: ``provision()`` discovers shard 0's live instance by tag/state and
    #: reattaches to it, and its ``run()`` then calls ``serve_model`` on that
    #: shared box, swapping the served model out from under shard 0's run in
    #: progress. A driver derives both per-shard values from the lane rather
    #: than defaulting them; see its own ``run_study.py``'s shard handling.
    shard: Optional[Tuple[int, int]] = None
    #: Forwarded to ``ReplicateHarness.force_seeds``: seeds re-collected past
    #: the resume-skip; ``None`` disables it. On EITHER backend the re-run now
    #: supersedes and replaces whatever was stored before, so it is what every
    #: reader returns -- see ``ReplicateHarness.force_seeds``'s own docstring
    #: for the mechanism.
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

    def cot_chain_lengths(self, tag: str) -> None:
        """Print reasoning-chain word-count stats from the stored CoT replicates.

        Like :meth:`summarize`, a pure ``ReplicateHarness`` delegate (no EC2 or
        inference cost, but S3 reads under an S3-backed store).

        Parameters
        ----------
        tag : str
            Selects the archetype scanned. REQUIRED here: a study with no CoT
            archetype must not inherit one's default tag (e.g. induction's
            "cot"). A subclass whose study always uses the same tag may
            override this method to default it -- see
            ``InductionExperiment.cot_chain_lengths``.
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
        A driver running under an external supervisor must NOT call this: the
        supervisor owns the instance's lifetime and may still have lanes queued
        against it, so such a driver gates teardown behind an explicit opt-in
        flag (or omits it) and leaves the decision to whoever provisioned.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's CRITICAL section.
        from smolbench.evals.providers import ec2

        # Return value discarded, per the -> None annotation.
        ec2.shutdown_instance()


def validate_experiment_tag(
    tag: str, lane: Optional[str], *, retired: Tuple[str, ...] = ("periodic-induction",)
) -> None:
    """Raise if `tag` is unsafe to run an experiment lifecycle under.

    ``ec2``'s tag-based recovery reattaches ``provision()`` to ANY live
    instance carrying `tag`, and a teardown terminates every instance carrying
    it -- so a tag that is empty, retired, or a bare shared-fleet prefix is not
    a per-driver identity, it is a way to collide with, or destroy, a box this
    process does not own. A driver calls this on its RESOLVED
    ``EC2_EXPERIMENT_TAG`` before provisioning.

    Parameters
    ----------
    tag : str
        The resolved ``EC2_EXPERIMENT_TAG`` value (after any lane suffix has
        already been appended) that the caller is about to provision under.
    lane : str or None
        The lane suffix appended to `tag` (e.g. ``"-s0of3"``), or None/empty
        for an unsharded run. Stripped from `tag` before every check below,
        because a sharded lane appends this suffix to whatever tag resolved --
        an exact-match guard compared against the unstripped `tag` would then
        never fire on the very (sharded, unattended) invocations most likely
        to run this into a collision.
    retired : tuple of str, optional
        Study tags that are no longer live; defaults to the one retired study
        known here. Caller-overridable so a later study can retire its own tag
        without editing this function. Passing ``()`` disables only this
        check -- the empty-tag and bare-shared-fleet-prefix checks below are
        structural and always apply.

    Returns
    -------
    None
        On success -- `tag` is safe to provision under.

    Raises
    ------
    ValueError
        If `tag` (or its lane-suffix-stripped base) is empty or
        whitespace-only; if the base is in `retired`; or if the base is the
        shared fleet prefix (``study_config.load_study_config().fleet.
        tag_prefix``, e.g. ``"scaling-"``) either exactly or with its trailing
        ``"-"`` removed (``"scaling"``) -- a bare prefix names every lane in
        the fleet at once, and fleet teardown terminates BY TAG.

    Notes
    -----
    Every raised message names `tag` (not just its stripped base), so an
    operator sees exactly what was exported, lane suffix included.
    """
    # Design: strip the lane suffix BEFORE any check, per the `lane` parameter
    # doc above -- every check below reasons about the study identity the tag
    # names, not about which lane happens to be attached to it.
    base = tag
    if lane and tag.endswith(lane):
        base = tag[: -len(lane)]

    if not tag.strip() or not base.strip():
        raise ValueError(
            f"EC2_EXPERIMENT_TAG={tag!r} is empty or whitespace-only, so it "
            "names no experiment. ec2's tag-based recovery and teardown both "
            "key off this string; export a real tag."
        )

    if base in retired:
        raise ValueError(
            f"EC2_EXPERIMENT_TAG={tag!r} resolves to the RETIRED {base!r} "
            "study's tag. Running under it would let ec2's tag-based recovery "
            "reattach `provision()` to any live box still carrying it -- "
            "swapping that box's served model out from under whichever driver "
            "owns it -- and would make a `teardown()` terminate a box this "
            "process does not own. Export a distinct EC2_EXPERIMENT_TAG."
        )

    fleet_prefix = study_config.load_study_config().fleet.tag_prefix
    # "with its trailing '-' removed": exactly one trailing dash, not every
    # dash a naive rstrip("-") would eat.
    fleet_prefix_bare = fleet_prefix[:-1] if fleet_prefix.endswith("-") else fleet_prefix
    if base == fleet_prefix or base == fleet_prefix_bare:
        raise ValueError(
            f"EC2_EXPERIMENT_TAG={tag!r} is the BARE shared fleet prefix "
            f"({fleet_prefix!r}), which names every lane in the fleet at "
            "once, not one driver's instance. ec2's tag-based recovery would "
            "reattach `provision()` to any live box in the fleet, and fleet "
            "teardown terminates BY TAG -- running under the bare prefix "
            "would take the whole fleet down instead of one box. Export a "
            "tag that includes a spec key or study identity beyond the prefix."
        )
