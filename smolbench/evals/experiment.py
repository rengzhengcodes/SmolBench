"""Study-neutral replicated evaluation and EC2 lifecycle facade.

Replicates use ``base_seed + r`` and shard by stride, so shards partition seeds.
Import ``ec2`` only after ``_apply_env()``: its ``EC2_*`` settings are read at import time.
Live EC2 methods are billed; summaries may read S3 but do not invoke inference.
"""

import functools
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from smolbench.evals import Quiz, study_config
from smolbench.evals.replicates import ReplicateHarness
from smolbench.evals.results_store import repo_root


@dataclass(frozen=True)
class Experiment:
    """Configure a replicated evaluation and EC2 lifecycle.

    Frozen configuration prevents mid-run changes.

    Parameters
    ----------
    notebook_dir : str
        Notebook directory containing the experiment's results.
    archetype_tags : Mapping[str, str]
        Mapping from model names to result-directory tags.
    make_quizzes : Callable[[int, str], Dict[str, Quiz]]
        Factory creating quizzes for a seed and model.
    info_types : Tuple[str, ...]
        Study-specific information arms in serialization order; no default.
    n_replicates : int, optional
        Number of replicate seeds.
    base_seed : int, optional
        First replicate seed.
    prefix : str, optional
        Result-directory namespace prefix.
    state_file : str, optional
        Repo-relative EC2 state-file name for this lifecycle.
    shard : Tuple[int, int], optional
        ``(index, count)`` stride for disjoint shard seed subsets.
    force_seeds : frozenset[int], optional
        Seeds to collect despite resume skipping them.

    Raises
    ------
    ValueError
        If shard bounds are invalid or a shard has no explicit state file.
    """

    notebook_dir: str
    archetype_tags: Mapping[str, str]
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    info_types: Tuple[str, ...]
    n_replicates: int = 30
    base_seed: int = 1776
    prefix: str = ""
    state_file: Optional[str] = None
    shard: Optional[Tuple[int, int]] = None
    force_seeds: Optional[frozenset[int]] = None

    def __post_init__(self) -> None:
        if self.shard is not None:
            if self.state_file is None:
                raise ValueError(
                    f"shard {self.shard!r} requires an explicit state_file: "
                    "shards sharing ec2's default state file would reattach to "
                    "each other's instance."
                )
            index, count = self.shard
            if count < 1 or not 0 <= index < count:
                raise ValueError(
                    f"shard {self.shard!r}: need count >= 1 and 0 <= index < count."
                )

    @property
    def seeds(self) -> Tuple[int, ...]:
        """Return this process's replicate seeds.

        Striding balances shard sizes.

        Returns
        -------
        Tuple[int, ...]
            This shard's seeds, ``base_seed + r`` strided by the shard.
        """
        every = tuple(self.base_seed + r for r in range(self.n_replicates))
        if self.shard is None:
            return every
        index, count = self.shard
        return tuple(s for r, s in enumerate(every) if r % count == index)

    @property
    def results_dir(self) -> Path:
        """Return the repo-rooted results directory, never cwd-relative.

        Returns
        -------
        Path
            ``repo_root()/notebooks/<notebook_dir>/results``.
        """
        return repo_root() / "notebooks" / self.notebook_dir / "results"

    @functools.cached_property
    def harness(self) -> ReplicateHarness:
        """Return the cached :class:`ReplicateHarness`.

        ``cached_property`` writes ``__dict__`` despite dataclass freezing.

        Returns
        -------
        ReplicateHarness
            Harness configured for this experiment's seeds and result store.
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
        """Set EC2's environment from the experiment configuration.

        EC2 is configured through ``INFERENCE_PROVIDER`` and ``EC2_STATE_FILE``
        environment knobs rather than method arguments. Pop
        ``EC2_STATE_FILE`` when unset to avoid inheriting another experiment's
        state.
        """
        os.environ["INFERENCE_PROVIDER"] = "ec2"
        if self.state_file is not None:
            os.environ["EC2_STATE_FILE"] = str(repo_root() / self.state_file)
        else:
            os.environ.pop("EC2_STATE_FILE", None)

    def _ec2(self) -> ModuleType:
        """Apply the call-time environment, then import ``ec2``.

        ``ec2`` reads its ``EC2_*`` settings at import time (consolidation
        tracked in issue #19), so the environment must be set first.

        Returns
        -------
        ModuleType
            The ``smolbench.evals.providers.ec2`` module.
        """
        self._apply_env()
        from smolbench.evals.providers import ec2

        return ec2

    def provision(self) -> Dict[str, Any]:
        """Provision or reattach to this experiment's EC2 spot instance.

        This is a billed AWS call. Print the receipt so it remains visible
        regardless of logging configuration.

        Returns
        -------
        Dict[str, Any]
            EC2 instance state: ``instance_id``, ``instance_type``,
            ``availability_zone``, and ``public_ip``.
        """
        ec2 = self._ec2()
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
        extra_args: Optional[dict[str, Any]] = None,
        max_parallel: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> None:
        """Serve ``model`` and run outstanding replicates.

        Resuming is safe because serving and collection are idempotent.

        Parameters
        ----------
        model : str
            Must be a key of both ``archetype_tags`` and ``ec2.EC2_DEPLOY_SPECS``.
        extra_args : Optional[dict[str, Any]], optional
            Arguments forwarded to ``run_replicates``.
        max_parallel : Optional[int], optional
            Maximum parallel requests forwarded to ``run_replicates``.
        request_timeout : int, optional
            Request timeout; CoT archetypes need a longer budget.

        Raises
        ------
        KeyError
            If ``model`` is not a key of ``archetype_tags``.
        """
        ec2 = self._ec2()
        # Avoid a billed model load when resume has nothing outstanding.
        if not self.harness.has_outstanding(model):
            logging.info(
                f"run: {model!r} has no outstanding replicates; skipping serve"
            )
            return

        # ``run_replicates`` omits ``None`` evaluation arguments.
        with ec2.serve_model(model):
            self.harness.run_replicates(
                model,
                extra_args=extra_args,
                max_parallel=max_parallel,
                request_timeout=request_timeout,
                # Capture the server actually serving these stored marks.
                server_config=ec2.server_config(model),
            )

    def summarize(self, model: str) -> None:
        """Print per-information-type totals for ``model``.

        Reads may use S3 but do not invoke EC2 or inference.

        Parameters
        ----------
        model : str
            Key of ``archetype_tags``.

        Raises
        ------
        KeyError
            ``model`` is not a key of ``archetype_tags``.
        """
        self.harness.summarize(model)

    def agent_status(self) -> Dict[str, Any]:
        """Return the provisioned instance's control-agent status.

        This billed AWS call diagnoses lifecycle problems without serving.

        Returns
        -------
        Dict[str, Any]
            Control-agent status payload from the provisioned instance.
        """
        ec2 = self._ec2()
        return ec2.agent_status()

    def teardown(self) -> None:
        """Terminate this experiment's EC2 spot instance and clear its state.

        Do not call under an external lifecycle supervisor: it owns the
        instance and may have lanes queued.
        """
        ec2 = self._ec2()
        ec2.shutdown_instance()


def validate_experiment_tag(tag: str, lane: Optional[str]) -> None:
    """Raise for an unsafe experiment lifecycle tag.

    Reject empty and bare fleet-prefix tags because recovery and teardown operate by tag.

    Parameters
    ----------
    tag : str
        Experiment tag to validate.
    lane : str, optional
        Optional lane suffix already appended to ``tag``.

    Raises
    ------
    ValueError
        If ``tag`` is empty or equals the bare fleet prefix.
    """
    # Validate the study identity rather than its lane suffix.
    base = tag
    if lane and tag.endswith(lane):
        base = tag[: -len(lane)]

    if not tag.strip() or not base.strip():
        raise ValueError(
            f"EC2_EXPERIMENT_TAG={tag!r} is empty; ec2's tag-based recovery "
            "and teardown key off it."
        )

    fleet_prefix = study_config.load_study_config().fleet.tag_prefix
    # Remove exactly one trailing dash.
    fleet_prefix_bare = (
        fleet_prefix[:-1] if fleet_prefix.endswith("-") else fleet_prefix
    )
    if base in (fleet_prefix, fleet_prefix_bare):
        raise ValueError(
            f"EC2_EXPERIMENT_TAG={tag!r} is the bare fleet prefix "
            f"{fleet_prefix!r}, which names every lane; fleet teardown "
            "terminates by tag, so include a spec key or study identity."
        )
