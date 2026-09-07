"""One facade over the eval harness and its EC2 lifecycle, study-neutral.

:class:`Experiment` bundles :class:`~smolbench.evals.replicates.ReplicateHarness` with the EC2
spot lifecycle that serves the models under test. A driver builds one module-level ``EXPERIMENT``
in its own study's ``run_study.py``. Fields with no study-neutral default (``info_types``, and
the CoT tag :meth:`Experiment.cot_chain_lengths` scans) are required here; a study subclass such
as ``InductionExperiment`` supplies its own defaults for them.

Seed convention: a replicate is the same quiz regenerated under a fresh seed,
``base_seed + r for r in range(n_replicates)``, strided under ``shard=(index, count)`` so N
shards partition one seed set without overlap (see the ``seeds`` property). The seed drives both
the quiz's own randomness and the per-request decoding seed, so a replicate is reproducible from
its ``rep_{seed}.yaml`` path alone.

Results: ``results_store.resolve_store`` picks local disk vs S3; its module docstring is the
canonical home for the env contract, the S3 key layout and earliest-wins reads. This class pins
the ``<experiment>`` key segment and the local layout analysis scripts read,
``{prefix}{tag}_{info}/rep_{seed}.yaml`` under ``results_dir``, overwritten on rerun.

COST: ``provision()``, ``run()``, ``agent_status()`` and ``teardown()`` are live, billed AWS
calls against a self-provisioned spot instance. ``summarize()`` and ``cot_chain_lengths()`` spend
no EC2/inference cost but do issue S3 reads under an S3-backed store.

Never import ``smolbench.evals.providers.ec2`` at module scope: its ``EC2_*`` constants are read
from ``os.environ`` at import time, so an eager import here would freeze them ahead of a
notebook's ``load_dotenv(keys.env)``. Every method needing the lifecycle imports ``ec2`` inside
its body, after ``_apply_env()``.
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

    Lifecycle order: ``provision()`` once, ``run(model, ...)`` once per archetype,
    ``summarize(model)`` / ``cot_chain_lengths()`` any number of times (offline), ``teardown()``
    once at the end. Frozen, like ``ReplicateHarness``: configuration must not mutate mid-run.
    """

    #: Locates results at ``repo_root()/notebooks/<notebook_dir>/results``.
    notebook_dir: str
    #: Model name -> short archetype tag used in result directory names (e.g.
    #: ``{"olmo-3.1-32b-instruct": "decode"}``). Forwarded to ``ReplicateHarness``.
    archetype_tags: Mapping[str, str]
    #: (seed, model) -> {info type: quiz}. Forwarded to ``ReplicateHarness``, which calls it
    #: lazily per outstanding seed. Only a noise arm (where a study has one) varies per model.
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    # No study-neutral default: the induction three-arm set (intens/extens/noise_intens) is one
    # study's choice, so defaulting it here would bake that study's prose into every subclass.
    #: Info types evaluated per replicate, in serialization order. Forwarded to ``ReplicateHarness``.
    info_types: Tuple[str, ...]
    #: Number of replicate seeds. Every induction study to date uses 30; sizing evidence lives in
    #: each study's ``analysis/power_analysis.py``.
    n_replicates: int = 30
    #: First replicate's seed; replicate 0 uses it exactly. Default 1776 (the July 4th nod); a
    #: study may override it.
    base_seed: int = 1776
    #: Optional namespace prefix on result directory names (e.g. ``"one_hop_"``) so two
    #: experiments can share one ``results_dir`` without their replicate directories colliding.
    prefix: str = ""
    #: Repo-root-anchored basename for this experiment's EC2 state file, or None for ``ec2.py``'s
    #: default. Set it whenever two lifecycles could be live at once -- including two SHARDS of
    #: one experiment, which need one state file EACH -- so they don't clobber each other's
    #: instance record; see the ``shard`` field for the failure a shared one produces.
    state_file: Optional[str] = None
    #: ``(index, count)`` selecting a disjoint slice of the replicates so N processes can collect
    #: one model's replicates in parallel; None runs all of them. Results need no coordination
    #: (each replicate has its own seed and key), but the EC2 lifecycle does: every shard MUST get
    #: its own ``state_file`` AND its own ``EC2_EXPERIMENT_TAG``, or shard 1's ``provision()``
    #: reattaches to shard 0's live instance and its ``run()`` swaps the served model out from
    #: under shard 0's run in progress.
    shard: Optional[Tuple[int, int]] = None
    #: Forwarded to ``ReplicateHarness.force_seeds``: seeds re-collected past the resume-skip;
    #: None disables it. The re-run supersedes whatever was stored before, on either backend.
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

        Sharded, every ``count``-th seed starting at ``index``. Striding rather than taking
        contiguous blocks keeps shard sizes within one replicate of each other (30 over 4 shards
        splits 8/8/7/7, not 8/8/8/6), since the slowest shard sets the wall-clock time sharding
        exists to reduce.
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

        Caching works on a frozen dataclass because ``cached_property.__get__`` writes straight
        into ``instance.__dict__``, bypassing the overridden ``__setattr__``.
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

        Sets ``INFERENCE_PROVIDER=ec2`` and, when ``state_file`` is set, points
        ``EC2_STATE_FILE`` at this experiment's state file; else explicitly pops it, so this
        experiment can't keep talking to an earlier one's state file instead of ``ec2.py``'s
        default.
        """
        os.environ["INFERENCE_PROVIDER"] = "ec2"
        if self.state_file is not None:
            os.environ["EC2_STATE_FILE"] = str(repo_root() / self.state_file)
        else:
            os.environ.pop("EC2_STATE_FILE", None)

    def provision(self) -> Dict[str, Any]:
        """Provision, or reattach to, this experiment's EC2 spot instance.

        Live AWS call (see the module docstring's COST section). Calls
        ``ec2.provision_spot_instance()`` bare, relying on the ``EC2_*`` environment for instance
        type/region/volume/timeout. Returns that call's state dict, also persisted to
        ``EC2_STATE_FILE``.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's note on importing ec2 at module scope.
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

        Live AWS call (container swap) followed by live inference; safe to re-run after an
        interruption since both are idempotent and resumable. All three keyword arguments are
        forwarded to ``run_replicates`` unchanged.

        Parameters
        ----------
        model : str
            must be a key of both ``archetype_tags`` and ``ec2.EC2_DEPLOY_SPECS``.
        request_timeout : int, optional
            CoT archetypes raise this so the longest chain finishes on attempt 1.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's note on importing ec2 at module scope.
        from smolbench.evals.providers import ec2

        # Skip serve_model entirely when nothing is outstanding: it pulls/loads hundreds of GB
        # for the large archetypes, pure billed time if every replicate is already on disk (hit
        # for real on a resumed run).
        if not self.harness.has_outstanding(model):
            logging.info(
                f"run: {model!r} has no outstanding replicates; skipping serve"
            )
            return

        # Unfiltered forward: run_replicates only populates eval_kwargs for non-None values, so
        # passing None through is the same as omitting it.
        with ec2.serve_model(model):
            self.harness.run_replicates(
                model,
                extra_args=extra_args,
                max_parallel=max_parallel,
                request_timeout=request_timeout,
                # Captured inside the serve block so the snapshot describes the box that
                # actually serves these replicates; stamped on every stored Marks.
                server_config=ec2.server_config(model),
            )

    def summarize(self, model: str) -> None:
        """Print per-info-type totals for ``model`` over every stored replicate.

        A pure ``ReplicateHarness.summarize`` delegate: no environment applied,
        no EC2/inference cost, but S3 reads under an S3-backed store.

        Parameters
        ----------
        model : str
            must be a key of ``archetype_tags``.

        Raises
        ------
        KeyError
            otherwise.
        """
        self.harness.summarize(model)

    def cot_chain_lengths(self, tag: str) -> None:
        """Print reasoning-chain word-count stats from the stored CoT replicates.

        Like :meth:`summarize`, a pure ``ReplicateHarness`` delegate (no EC2/inference cost, S3
        reads only).

        Parameters
        ----------
        tag : str
            required -- a study with no CoT archetype must not inherit another's default tag
            (e.g. induction's "cot"). A subclass whose study always uses one tag may override
            this method to default it.
        """
        self.harness.cot_chain_lengths(tag)

    def agent_status(self) -> Dict[str, Any]:
        """Return the provisioned instance's control-agent status, verbatim.

        LIVE AWS call. Container state, health and recent docker logs, for
        diagnosing a stuck ``run()``/``provision()`` without re-triggering
        either. Raises ``RuntimeError`` if no instance has been provisioned.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's note on importing ec2 at module scope.
        from smolbench.evals.providers import ec2

        return ec2.agent_status()

    def teardown(self) -> None:
        """Terminate this experiment's EC2 spot instance and clear its state.

        Live AWS call; safe even if provisioning failed or the state file was lost, since
        ``shutdown_instance`` falls back to the ``smolbench:experiment`` tag. A driver running
        under an external supervisor must NOT call this: the supervisor owns the instance's
        lifetime and may still have lanes queued against it.
        """
        self._apply_env()
        # Lazy by design -- see the module docstring's note on importing ec2 at module scope.
        from smolbench.evals.providers import ec2

        ec2.shutdown_instance()


def validate_experiment_tag(tag: str, lane: Optional[str]) -> None:
    """Raise if `tag` is unsafe to run an experiment lifecycle under.

    ``ec2``'s tag-based recovery reattaches ``provision()`` to any live instance carrying `tag`,
    and a teardown terminates every instance carrying it -- so an empty tag or a bare
    shared-fleet prefix is not a per-driver identity, it's a way to collide with, or destroy, a
    box this process doesn't own. A driver calls this on its resolved ``EC2_EXPERIMENT_TAG``
    before provisioning.

    Raises ValueError if `tag` (or its lane-stripped base) is empty/whitespace-only, or if the
    base is the shared fleet prefix (``study_config.load_study_config().fleet.tag_prefix``)
    exactly or with its trailing ``"-"`` removed -- a bare prefix names every lane in the fleet
    at once, and fleet teardown terminates by tag. Every raised message names the full `tag`,
    lane suffix included.

    Parameters
    ----------
    lane : str, optional
        the suffix already appended to `tag` (e.g. ``"-s0of3"``), stripped before every check
        below so a sharded lane's suffix can't defeat the exact-match guard.
    """
    # Strip the lane suffix first: every check below reasons about the study identity the tag
    # names, not about which lane is attached to it.
    base = tag
    if lane and tag.endswith(lane):
        base = tag[: -len(lane)]

    if not tag.strip() or not base.strip():
        raise ValueError(
            f"EC2_EXPERIMENT_TAG={tag!r} is empty or whitespace-only, so it "
            "names no experiment. ec2's tag-based recovery and teardown both "
            "key off this string; export a real tag."
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
