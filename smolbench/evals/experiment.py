"""Study-neutral replicated evaluation and EC2 lifecycle facade.

Replicates use ``base_seed + r`` and shard by stride, so shards partition seeds.
``ec2`` (and boto3) is imported lazily so configuration-only uses
(``summarize``, tests) never pay for it; the experiment-owned
``EC2_EXPERIMENT_TAG`` is resolved and frozen at construction, then exported
before each live call and read at call time. Remaining import-time ``EC2_*``
provisioning knobs (instance types, regions, timeouts, and similar settings)
stay process-global, as tracked in issue #19.
Live EC2 methods are billed; summaries may read S3 but do not invoke inference.
"""

import functools
import logging
import os
import re
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
        First replicate seed; defaults to 0.
    prefix : str, optional
        Result-directory namespace prefix.
    state_file : str, optional
        Repo-relative EC2 state-file name; defaults to
        ``.ec2_state_<experiment_tag>.json`` so distinct experiments never
        reattach to each other's instance. Tags are restricted to a
        filename-safe charset.
    experiment_tag : str, optional
        Explicit tag, else the driver's exported ``EC2_EXPERIMENT_TAG``, else
        the study's standalone tag; sharded experiments get a
        ``-s<index>of<count>`` suffix if not already present, so shards never
        share an instance. Resolved and frozen at construction.
    shard : Tuple[int, int], optional
        ``(index, count)`` stride for disjoint shard seed subsets; concurrent
        shards get distinct ``experiment_tag`` values and derived state files.
    force_seeds : frozenset[int], optional
        Seeds to collect despite resume skipping them.

    Raises
    ------
    ValueError
        If ``state_file`` is blank, ``experiment_tag`` is unsafe (see
        ``validate_experiment_tag``), or shard bounds are invalid.
    """

    notebook_dir: str
    archetype_tags: Mapping[str, str]
    make_quizzes: Callable[[int, str], Dict[str, Quiz]]
    info_types: Tuple[str, ...]
    n_replicates: int = 30
    base_seed: int = 0
    prefix: str = ""
    state_file: Optional[str] = None
    experiment_tag: Optional[str] = None
    shard: Optional[Tuple[int, int]] = None
    force_seeds: Optional[frozenset[int]] = None

    def __post_init__(self) -> None:
        # Snapshot: the frozen field must not alias a caller-mutable mapping.
        object.__setattr__(self, "archetype_tags", dict(self.archetype_tags))
        if self.state_file is not None and not self.state_file.strip():
            raise ValueError(
                "state_file must name a file; an empty value resolves to the "
                "repo root and ec2 cannot persist state there."
            )
        if self.shard is not None:
            index, count = self.shard
            if count < 1 or not 0 <= index < count:
                raise ValueError(
                    f"shard {self.shard!r}: need count >= 1 and 0 <= index < count."
                )
        tag = (
            self.experiment_tag
            if self.experiment_tag is not None
            else (
                os.environ.get("EC2_EXPERIMENT_TAG")
                or study_config.load_study_config().fleet.standalone_tag
            )
        )
        if self.shard is not None:
            index, count = self.shard
            suffix = f"-s{index}of{count}"
            if not tag.endswith(suffix):
                tag += suffix
        validate_experiment_tag(tag, None)
        object.__setattr__(self, "experiment_tag", tag)

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

        EC2 is configured through ``INFERENCE_PROVIDER``, ``EC2_STATE_FILE``,
        and ``EC2_EXPERIMENT_TAG`` environment knobs rather than method
        arguments, so each experiment exports its resolved identity before
        invoking EC2. The state-file default is derived from that identity to
        prevent experiments from inheriting each other's lifecycle state.
        """
        os.environ["INFERENCE_PROVIDER"] = "ec2"
        state_file = self.state_file or f".ec2_state_{self.experiment_tag}.json"
        os.environ["EC2_STATE_FILE"] = str(repo_root() / state_file)
        os.environ["EC2_EXPERIMENT_TAG"] = self.experiment_tag

    def _ec2(self) -> ModuleType:
        """Apply the call-time environment, then import ``ec2`` lazily.

        ``ec2`` pulls in boto3, so it is imported only by live methods.
        ``EC2_STATE_FILE`` and ``INFERENCE_PROVIDER`` are read at call time;
        ``EC2_EXPERIMENT_TAG`` is resolved and frozen by the owning experiment,
        exported before this call, and read at call time. Remaining import-time
        ``EC2_*`` provisioning knobs are process-global; consolidation is
        tracked in issue #19.

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
            EC2 instance state as persisted to ``EC2_STATE_FILE``:
            ``instance_id``, ``region``, ``availability_zone``,
            ``instance_type``, ``public_ip``, ``security_group_id``, and the
            secrets ``control_token`` / ``vllm_api_key`` — do not log the dict.
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

    def sync_down(self) -> int:
        """Materialize the S3 results log into the local results tree.

        Reads S3 only; no EC2 or inference calls.

        Returns
        -------
        int
            Number of result files written locally.

        Raises
        ------
        RuntimeError
            If the store is not S3-backed.
        """
        return self.harness.sync_down()

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

    Reject empty, filename-unsafe, and bare fleet-prefix tags because recovery
    and teardown operate by tag.

    Parameters
    ----------
    tag : str
        Experiment tag to validate.
    lane : str, optional
        Optional lane suffix already appended to ``tag``.

    Raises
    ------
    ValueError
        If ``tag`` is unsafe (charset, length, emptiness, bare prefix).
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
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", tag) or tag in (".", ".."):
        raise ValueError(
            f"EC2_EXPERIMENT_TAG={tag!r} may only contain letters, digits, '.', '_' "
            "and '-' and be at most 128 characters; it names the default EC2 "
            "state file."
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
