"""Define fleet lanes, their environments, and subprocess commands.

Load the induction driver before ec2 so its dotenv setup precedes ec2's
environment-derived constants. ``lane_env`` returns a fresh allowlisted
environment, keeping dry-run offline and lanes isolated.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Mapping, Optional

_CONFIG_MODULE_NAME = "smolbench_fleet_config"


def _load_fleet_config() -> ModuleType:
    # _config provides its own loader; scripts/fleet is not a package.
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            _CONFIG_MODULE_NAME, Path(__file__).resolve().parent / "_config.py")
        sys.modules[_CONFIG_MODULE_NAME] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


_config = _load_fleet_config()

# Must precede run_study's module-scope logging, which fixes the root handler.
logging.basicConfig(level=logging.INFO)

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
VENV_PYTHON: Path = REPO_ROOT / ".venv" / "bin" / "python"

# Load by path because induction and deduction both provide run_study.py.
# Its dotenv setup supplies the allowlisted AWS and cache variables.
_RUN_STUDY_PATH = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
run_study = _config.load_module_by_path("induction_run_study", _RUN_STUDY_PATH)

# The cached ec2 import follows run_study's dotenv setup; reuse its hardware tables.
from smolbench.evals.providers.ec2 import (  # noqa: E402
    EC2_DEPLOY_SPECS,
    EC2_VLLM_IMAGE,
    _INSTANCE_GPU_COUNTS as _EC2_INSTANCE_GPU_COUNTS,
    _INSTANCE_GPU_NAMES as _EC2_INSTANCE_GPU_NAMES,
)

#: Shared source avoids a second region list.
DEFAULT_REGIONS = _config.DEFAULT_REGIONS
# Alias ec2's resolved image so fleet and provider cannot pin different digests.
FLEET_IMAGE = EC2_VLLM_IMAGE
# V4 requires this digest's known SM90 serving path.
LANE_IMAGE_OVERRIDES = {
    "deepseek-v4-flash": "vllm/vllm-openai@sha256:0e1ee52750c67718a596ba63176034aa18b439c4a69896ac5a0a8393919aa4df",
    "deepseek-v4-pro": "vllm/vllm-openai@sha256:0e1ee52750c67718a596ba63176034aa18b439c4a69896ac5a0a8393919aa4df",
}
MAX_LIFETIME_MIN = "2160"  # 36h absolute backstop, as a string (env value)
REQUEST_TIMEOUT_SECONDS = "3600"  # long CoT generations, as a string (env value)
# Eager Pro can take over an hour for 87k tokens; 14400s avoids retry loops.
LANE_REQUEST_TIMEOUT_OVERRIDES = {
    "deepseek-v4-pro": "14400",
}

TIER_INSTANCE_TYPES = {
    # One GPU count preserves derive_tp across capacity reclaims.
    "A": "g6e.4xlarge,g6e.8xlarge",
    "B": "g6e.12xlarge,g6e.24xlarge",
    "C": "p5.48xlarge,p5e.48xlarge",
    # Pro's native-SM100 recipe must run on B200, not p5e/p5en.
    "D": "p6-b200.48xlarge",
}


def _tier_gpu_pin(tier: str) -> str:
    """Derive a GPU pin from ec2's hardware tables to catch roster drift.

    Count-only pins permit tier C's H100/H200 alternatives while preserving TP.

    Parameters
    ----------
    tier : str
        Instance-type hunt-list tier.

    Returns
    -------
    str
        EC2 GPU requirement pin.

    Raises
    ------
    SystemExit
        Unmappable or mixed-count hunt list; never ``assert`` under ``python -O``.
    """
    types = TIER_INSTANCE_TYPES[tier].split(",")
    unmapped = [
        t for t in types
        if t not in _EC2_INSTANCE_GPU_COUNTS or t.split(".", 1)[0] not in _EC2_INSTANCE_GPU_NAMES
    ]
    if unmapped:
        raise SystemExit(
            f"run_fleet: _tier_gpu_pin: tier {tier!r} hunts instance type(s) "
            f"{unmapped} that ec2.py's _INSTANCE_GPU_COUNTS/_INSTANCE_GPU_NAMES "
            "cannot map -- an unmappable hunt list cannot be pinned. Add the "
            "type(s) to those tables in ec2.py, or drop them from "
            "TIER_INSTANCE_TYPES."
        )
    counts = {_EC2_INSTANCE_GPU_COUNTS[t] for t in types}
    if len(counts) != 1:
        raise SystemExit(
            f"run_fleet: _tier_gpu_pin: tier {tier!r}'s hunt list {types} spans "
            f"GPU counts {sorted(counts)} -- exactly the tp-changing "
            "capacity-reclaim defect EC2_REQUIRE_GPU exists to prevent. Narrow "
            "TIER_INSTANCE_TYPES so every type in one tier shares one GPU count."
        )
    count = counts.pop()
    names = {_EC2_INSTANCE_GPU_NAMES[t.split(".", 1)[0]] for t in types}
    if len(names) == 1:
        # A shared name can pin silicon and count.
        return f"{names.pop().split()[0]}:{count}"
    # Tier C accepts H100/H200 but requires the shared count.
    return f":{count}"


#: Per-tier GPU pins; a count-only pin allows tier C silicon alternatives.
TIER_REQUIRE_GPU: dict[str, str] = {tier: _tier_gpu_pin(tier) for tier in TIER_INSTANCE_TYPES}

# Tier D retains all study regions because B200 placement is shifting.
TIER_REGIONS = {"D": DEFAULT_REGIONS}
TIER_BUDGET_HOURS = {"A": 9, "B": 9, "C": 10, "D": 14}

TIER_MEMBERS = {
    # gemma-4-12b needs tier B's four GPUs for tp=4.
    "A": ("nemotron-3-nano-4b", "gemma-4-e2b", "ministral-3-3b"),
    "B": (
        "qwen3.5-27b", "nemotron-3-nano-30b-a3b", "gemma-4-12b", "gemma-4-31b",
        "glm-4.7-flash", "ministral-3-8b", "ministral-3-14b", "exaone-4.0-32b",
        "exaone-4.5-33b",
    ),
    "C": (
        "qwen3.5-122b-a10b", "qwen3.5-397b-a17b", "nemotron-3-super-120b-a12b",
        "glm-4.5-air", "k-exaone-236b-a23b",
    ),
    # Flash's SM100 recipe requires tier D's B200 hunt list.
    "D": ("glm-4.7", "deepseek-v3.1", "deepseek-v4-pro", "deepseek-v4-flash"),
}


@dataclass(frozen=True)
class Lane:
    """A checkpoint's spec key, analysis tag, and hardware tier."""

    key: str
    tag: str
    tier: str

    @property
    def instance_types(self) -> str:
        """Return this lane's allowed EC2 instance types."""
        return TIER_INSTANCE_TYPES[self.tier]

    @property
    def regions(self) -> str:
        """Return this lane's allowed EC2 regions."""
        return TIER_REGIONS.get(self.tier, DEFAULT_REGIONS)

    @property
    def experiment_tag(self) -> str:
        """Return the shared ``smolbench:experiment`` tag."""
        return f"{_config.SCALING_TAG_PREFIX}{self.key}"

    @property
    def state_file(self) -> str:
        """Return the driver's state-file basename so deduction reattaches."""
        return f".ec2_state_scaling_{self.key}.json"

    @property
    def budget_hours(self) -> int:
        """Expected wall-clock hours for this tier; ``supervisor._monitor_tick`` alerts past 2x."""
        return TIER_BUDGET_HOURS[self.tier]


def _drift_guard() -> None:
    """Reject tier overlap or drift from the config and deployment roster."""
    flat = [key for keys in TIER_MEMBERS.values() for key in keys]
    flat_set = set(flat)
    if len(flat) != len(flat_set):
        seen: set[str] = set()
        dupes: set[str] = set()
        for key in flat:
            (dupes if key in seen else seen).add(key)
        raise SystemExit(
            f"run_fleet: TIER_MEMBERS lists {sorted(dupes)} in more than one tier -- "
            "tiers must be pairwise disjoint."
        )

    roster_key_set = set(_config.ROSTER_KEYS)
    spec_keys = set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"}
    problems = []
    if flat_set != roster_key_set:
        problems.append(
            f"TIER_MEMBERS vs the study config's roster differ by "
            f"{sorted(flat_set.symmetric_difference(roster_key_set))}"
        )
    if flat_set != spec_keys:
        problems.append(
            "TIER_MEMBERS vs EC2_DEPLOY_SPECS (minus qwen2.5-1.5b) differ by "
            f"{sorted(flat_set.symmetric_difference(spec_keys))}"
        )
    if problems:
        raise SystemExit(
            "run_fleet: lane roster drift detected -- " + "; ".join(problems) + ". "
            "A rung added to (or removed from) EC2_DEPLOY_SPECS or "
            "smolbench/evals/study_config.toml's [roster] without a matching "
            "edit to TIER_MEMBERS in this file would silently never run, "
            "shipping 20 of 21 ladders with no error. Fix TIER_MEMBERS."
        )


# Validate keys before building LANES from ROSTER_TAGS.
_drift_guard()

#: Spec key to validated lane.
LANES: dict[str, Lane] = {
    key: Lane(key=key, tag=_config.ROSTER_TAGS[key], tier=tier)
    for tier, keys in TIER_MEMBERS.items()
    for key in keys
}


# Allowlist prevents stale per-lane exports from overriding computed settings.
# EC2_VLLM_IMAGE remains operator-overridable unless a lane pin wins.
PASSTHROUGH_ENV: tuple[str, ...] = (
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR",
    "AWS_PROFILE", "AWS_REGION", "AWS_DEFAULT_REGION",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
    "AWS_SHARED_CREDENTIALS_FILE", "AWS_CONFIG_FILE",
    "HF_TOKEN",
    "SMOLBENCH_RESULTS_S3", "SMOLBENCH_RESULTS_S3_REGION",
    "EC2_S3_MODEL_CACHE", "EC2_S3_CACHE_REGION",
    "EC2_VLLM_IMAGE",
)


def lane_env(
    lane: Lane, phase: str, base_env: Optional[Mapping[str, str]] = None
) -> dict[str, str]:
    """Build an isolated lane environment.

    Share the derived state-file path so deduction reattaches; lane image pins
    override operator exports, which override ec2's default.

    Parameters
    ----------
    lane : Lane
        Lane configuration.
    phase : str
        Subprocess phase.
    base_env : Optional[Mapping[str, str]], optional
        Source environment; ``None`` reads ``os.environ``.

    Returns
    -------
    dict[str, str]
        Lane subprocess environment.
    """
    if base_env is None:
        base_env = os.environ

    env: dict[str, str] = {key: base_env[key] for key in PASSTHROUGH_ENV if key in base_env}
    env.update(
        {
            "INFERENCE_PROVIDER": "ec2",
            "EC2_EXPERIMENT_TAG": lane.experiment_tag,
            # A private state file prevents cross-lane reattachment.
            "INDUCTION_STATE_FILE": lane.state_file,
            "INDUCTION_MODELS": lane.key,
            "EC2_INSTANCE_TYPES": lane.instance_types,
            "EC2_REGIONS": lane.regions,
            "EC2_REQUIRE_GPU": TIER_REQUIRE_GPU[lane.tier],
            # vLLM serves one sequence, so client fan-out only increases latency.
            "EC2_MAX_PARALLEL_REQUESTS": "1",
            "EC2_MAX_LIFETIME_MIN": MAX_LIFETIME_MIN,
            "EC2_REQUEST_TIMEOUT_SECONDS": LANE_REQUEST_TIMEOUT_OVERRIDES.get(
                lane.key, REQUEST_TIMEOUT_SECONDS
            ),
        }
    )
    if lane.key in LANE_IMAGE_OVERRIDES:
        # V4's known-good image must override a fleet-wide export.
        env["EC2_VLLM_IMAGE"] = LANE_IMAGE_OVERRIDES[lane.key]
    if phase == "deduction":
        env.update(
            {
                # Leave LEAN_STATE_FILE unset to use the shared derivation.
                "LEAN_MODEL": lane.key,
                "LEAN_RUN_NAME": f"scaling_{lane.key}",
            }
        )
    return env


# Shutdown resolves the lane state file from the repo root, never cwd.
_SHUTDOWN_SNIPPET = (
    "import os; "
    "from smolbench.evals.results_store import repo_root; "
    "os.environ['EC2_STATE_FILE'] = str(repo_root() / os.environ['INDUCTION_STATE_FILE']); "
    "from smolbench.evals.providers.ec2 import shutdown_instance; "
    "shutdown_instance()"
)


def lane_command(lane: Lane, phase: str) -> list[str]:
    """Build a lane subprocess command.

    Shutdown requires the lane environment to resolve its state file.

    Parameters
    ----------
    lane : Lane
        Lane configuration.
    phase : str
        Subprocess phase.

    Returns
    -------
    list[str]
        Argument vector.

    Raises
    ------
    ValueError
        Phase outside induction, deduction, or shutdown.
    """
    if phase == "induction":
        return [str(VENV_PYTHON), str(REPO_ROOT / "notebooks" / "induction" / "run_study.py")]
    if phase == "deduction":
        return [str(VENV_PYTHON), str(REPO_ROOT / "notebooks" / "deduction" / "run_study.py")]
    if phase == "shutdown":
        return [str(VENV_PYTHON), "-c", _SHUTDOWN_SNIPPET]
    raise ValueError(f"lane_command: unknown phase {phase!r}; expected induction/deduction/shutdown")
