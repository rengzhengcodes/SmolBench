"""The study's roster tables, and ONE lane's environment and argv.

Answers what lane ``<key>`` looks like, never what the fleet is doing right
now: owns the roster (`TIER_MEMBERS`, `LANES`, the per-tier tables), the
digest-pinned `FLEET_IMAGE`, and the two functions that turn a `Lane` into a
subprocess (`lane_env`, `lane_command`). The live loop and command line
belong to ``supervisor.py``/``run_fleet.py``.

No function here launches a subprocess, calls AWS, or mutates `os.environ`
(`lane_env` always returns a fresh dict) -- which is what makes
``run_fleet.py --dry-run`` a genuinely offline preview. Importing this
module is the exception: the driver load below runs
``load_dotenv(notebooks/induction/keys.env)``, how AWS/results-store/
model-cache variables reach this process at all.

Import-time ordering is load-bearing, not tidiness: `_config`, then the
by-path `run_study` load (`load_dotenv`), then
``smolbench.evals.providers.ec2`` (which freezes its `EC2_*` constants
against the environment at that moment); each block below carries its own
comment on why it can't move. `run_fleet.py`/`supervisor.py` reach this
module through `_config.load_fleet_module`'s cache, so they share one
module object -- one roster per process, not a copy each.
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
    # Bootstrapped by hand: load_module_by_path lives on _config itself,
    # and scripts/fleet isn't a package.
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            _CONFIG_MODULE_NAME, Path(__file__).resolve().parent / "_config.py")
        sys.modules[_CONFIG_MODULE_NAME] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


_config = _load_fleet_config()

# Must run before the driver load below, not in run_fleet.py: run_study.py
# logs at its own module scope, and the first logging call in a process
# fixes the root handler, so a later basicConfig would silently lose to it.
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Anchoring + the induction driver import
# ---------------------------------------------------------------------------
REPO_ROOT: Path = Path(__file__).resolve().parents[2]
VENV_PYTHON: Path = REPO_ROOT / ".venv" / "bin" / "python"

# Loaded by file path, not a bare `import run_study`: the deduction study
# ships its own `notebooks/deduction/run_study.py`, and a bare module name
# goes ambiguous once both trees sit on `sys.path`. Imported for the
# driver's per-lane runtime facts (`BASE_SEED`, `INFO_TYPES`,
# `completion_budget`, `EXPERIMENT`), not for the roster -- the driver is a
# consumer of `smolbench/evals/study_config.toml`, not its owner, so `LANES`
# reads that config directly via `_config.ROSTER_KEYS`/`ROSTER_TAGS`. The
# import's `load_dotenv(notebooks/induction/keys.env)` side effect is
# desired: it's how AWS, results-store and model-cache variables reach this
# process, for `lane_env` to pass through to every lane.
_RUN_STUDY_PATH = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
run_study = _config.load_module_by_path("induction_run_study", _RUN_STUDY_PATH)

# A sys.modules cache hit, not a second, differently-timed import: run_study
# already pulled in ec2.py, after its own load_dotenv ran.
#
# _INSTANCE_GPU_COUNTS/_INSTANCE_GPU_NAMES are private to ec2.py; imported
# here rather than re-declared, so _tier_gpu_pin below can never drift from
# that module's own hardware tables.
from smolbench.evals.providers.ec2 import (  # noqa: E402
    EC2_DEPLOY_SPECS,
    EC2_VLLM_IMAGE,
    _INSTANCE_GPU_COUNTS as _EC2_INSTANCE_GPU_COUNTS,
    _INSTANCE_GPU_NAMES as _EC2_INSTANCE_GPU_NAMES,
)

# ---------------------------------------------------------------------------
# Constants (exact names/values -- pinned by tests/tooling/test_run_fleet.py)
# ---------------------------------------------------------------------------
#: Sourced from ``_config.py``, the one place this string is declared.
DEFAULT_REGIONS = _config.DEFAULT_REGIONS
# ec2.py's OWN resolved value, aliased rather than re-typed, so a lane and this
# supervisor cannot pin two different digests. Bump it in ec2.py.
FLEET_IMAGE = EC2_VLLM_IMAGE
# Per-lane image pins (default: FLEET_IMAGE). The V4 lanes run the tagged
# v0.27.1 release, digest-pinned: that version's SM90 serving path (Marlin
# MXFP4 + FLASHMLA_SPARSE_DSV4, see the DeepSeek block in EC2_DEPLOY_SPECS) is
# the one V4 is known to serve on.
LANE_IMAGE_OVERRIDES = {
    "deepseek-v4-flash": "vllm/vllm-openai@sha256:0e1ee52750c67718a596ba63176034aa18b439c4a69896ac5a0a8393919aa4df",
    "deepseek-v4-pro": "vllm/vllm-openai@sha256:0e1ee52750c67718a596ba63176034aa18b439c4a69896ac5a0a8393919aa4df",
}
MAX_LIFETIME_MIN = "2160"  # 36h absolute backstop, as a string (env value)
REQUEST_TIMEOUT_SECONDS = "3600"  # long CoT generations, as a string (env value)
# deepseek-v4-pro serves --enforce-eager: a budget-burning 87k-token
# generation takes >1h at eager Pro throughput, a single-request figure
# independent of in-flight count, so the fleet-wide 3600s timeout would
# retry those cells forever; 14400s lets a worst-case cell finish in one
# attempt. The box-side idle watchdog keys on vLLM metrics activity, so an
# hours-long generation can't trip it. Every other lane fits inside
# REQUEST_TIMEOUT_SECONDS at the in-flight count `lane_env` pins (1).
LANE_REQUEST_TIMEOUT_OVERRIDES = {
    "deepseek-v4-pro": "14400",
}

TIER_INSTANCE_TYPES = {
    # One GPU count per tier: ec2.derive_tp is gcd(attention heads, landed
    # GPU count), so a reclaim onto a differently-sized fallback would
    # change a lane's derived tp mid-lane. Cost: a reclaimed tier-A lane
    # waits for 1-GPU g6e capacity.
    "A": "g6e.4xlarge,g6e.8xlarge",
    "B": "g6e.12xlarge,g6e.24xlarge",
    "C": "p5.48xlarge,p5e.48xlarge",
    # D is p6-b200 (8x B200, SM100). deepseek-v4-pro's spec drops its Marlin
    # pin for SM100's native MXFP4 path, which must not serve on p5e/p5en.
    "D": "p6-b200.48xlarge",
}


def _tier_gpu_pin(tier: str) -> str:
    """Derive tier `tier`'s ``ec2.EC2_REQUIRE_GPU`` pin from its hunt list.

    Maps every instance type in ``TIER_INSTANCE_TYPES[tier]`` through ec2.py's
    own ``_INSTANCE_GPU_COUNTS``/``_INSTANCE_GPU_NAMES`` tables, so this pin
    can never drift from that module's hardware data. Derived, never a
    hand-written table: an edit to ``TIER_INSTANCE_TYPES`` unsafe for this
    function to run against is exactly the drift ``EC2_REQUIRE_GPU`` exists
    to catch.

    An empty-name, count-only result (e.g. ``":8"``) is a weaker pin by
    construction -- ``ec2._assert_required_gpu``'s membership check treats an
    empty substring as trivially "in" any string, so it matches any silicon
    while still enforcing the count. Deliberate for tier C, whose hunt list
    (``p5.48xlarge`` H100, ``p5e.48xlarge`` H200) is genuinely different
    silicon accepted as interchangeable at the same 8-GPU count: the pin
    still blocks a tp-changing GPU-count substitution, but cannot (and is not
    meant to) catch the same-count, different-silicon substitution that
    changes numerics without changing tp.

    Parameters
    ----------
    tier : str
        Tier whose instance-type hunt list is pinned.

    Returns
    -------
    str
        ``EC2_REQUIRE_GPU`` pin for the tier.

    Raises
    ------
    SystemExit
        When the hunt list is unmappable or spans more than one GPU count (never ``assert``,
        stripped under ``python -O``).
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
        # One shared GPU name across the tier: pin both silicon and count.
        return f"{names.pop().split()[0]}:{count}"
    # Names differ (tier C's H100 vs H200) but count agrees: count-only pin.
    return f":{count}"


#: Per-tier ``EC2_REQUIRE_GPU`` pin, set for every lane by `lane_env`. See
#: `_tier_gpu_pin` for how each value is derived and what a count-only entry
#: (e.g. tier C's) means.
TIER_REQUIRE_GPU: dict[str, str] = {tier: _tier_gpu_pin(tier) for tier in TIER_INSTANCE_TYPES}

# Tier D only; every other tier falls back to DEFAULT_REGIONS. All 3 study
# regions stay in the p6-b200 hunt: unlike p5e (us-east-2/us-west-2 only),
# B200 placement is still shifting, so excluding a region risks starving the
# experiment. Built from `DEFAULT_REGIONS` rather than a literal, so this
# can't spell a second, independently drifting copy of the same regions.
TIER_REGIONS = {"D": DEFAULT_REGIONS}
TIER_BUDGET_HOURS = {"A": 9, "B": 9, "C": 10, "D": 14}

TIER_MEMBERS = {
    # gemma-4-12b is tier B, not A: its spec runs tp=4, and tier A's hunt
    # list mixes 1-GPU types where tp=4 can't construct. Tier B is all-4-GPU.
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
    # deepseek-v4-flash's spec uses the marlin-less SM100 recipe, which must
    # only serve on tier D's p6-b200 hunt list, never on C's p5/p5e.
    "D": ("glm-4.7", "deepseek-v3.1", "deepseek-v4-pro", "deepseek-v4-flash"),
}


# ---------------------------------------------------------------------------
# Lane / LANES
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Lane:
    """One study checkpoint's fleet identity: spec key, analysis tag, tier.

    `key` is an ``EC2_DEPLOY_SPECS``/``_config.ROSTER_KEYS`` key and vLLM's
    ``--served-model-name``; `tag` is ``_config.ROSTER_TAGS[key]``, used in
    result directory names and figure legends; `tier` is ``"A"``-``"D"``.
    Everything else is derived below, so a tier constant can't go stale in a
    per-lane copy.
    """

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
        """This lane's ``smolbench:experiment`` tag: ``f"{prefix}{key}"``.

        `prefix` is ``_config.SCALING_TAG_PREFIX``, the same constant
        ``fleet_status.py`` reads, so the two scripts can't spell it
        differently.
        """
        return f"{_config.SCALING_TAG_PREFIX}{self.key}"

    @property
    def state_file(self) -> str:
        """This lane's private EC2 state-file basename (repo-root-anchored by the driver).

        Spelled ``.ec2_state_scaling_<key>.json`` literally, not derived from
        `experiment_tag`: must match what
        ``notebooks/deduction/run_study.py``'s ``lane_env_defaults`` derives
        for the same lane, or deduction silently provisions a second box
        instead of reattaching (``test_run_fleet.py`` pins the equality).
        The two prefixes (``"scaling-"`` for the tag, ``"scaling_"`` here)
        are independent by construction, not a typo: one answers to AWS, the
        other to that driver.
        """
        return f".ec2_state_scaling_{self.key}.json"

    @property
    def budget_hours(self) -> int:
        """Expected wall-clock hours for this tier; ``supervisor._monitor_tick`` alerts past 2x."""
        return TIER_BUDGET_HOURS[self.tier]


def _drift_guard() -> None:
    """Verify, at import time, that ``TIER_MEMBERS`` agrees with both sources of truth.

    ``TIER_MEMBERS`` is hand-written and must match ``_config.ROSTER_KEYS``
    (the committed config roster) and ``set(EC2_DEPLOY_SPECS) -
    {"qwen2.5-1.5b"}``; a rung added there but not here would silently never
    run. Checked at import time so even a bare import or ``--dry-run``
    catches the drift, and against the config's roster rather than the
    induction driver's ``MODELS`` because the driver builds ``MODELS`` from
    that same config -- a consumer, not an authority. Raises `SystemExit`
    (never ``assert``, stripped under ``python -O``) for tiers that aren't
    pairwise disjoint, or roster drift against either source.
    """
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


# Run before `LANES` is built, so the `_config.ROSTER_TAGS[key]` lookup below
# is already certified total over TIER_MEMBERS and can never KeyError.
_drift_guard()

#: Spec key -> Lane for every model this study runs: tier assignment is
#: this file's, roster and analysis tags are the committed config's, and
#: _drift_guard above has already certified the two agree.
LANES: dict[str, Lane] = {
    key: Lane(key=key, tag=_config.ROSTER_TAGS[key], tier=tier)
    for tier, keys in TIER_MEMBERS.items()
    for key in keys
}


# ---------------------------------------------------------------------------
# Per-lane environment
# ---------------------------------------------------------------------------
# An explicit allowlist, not `dict(os.environ)` plus overrides: this
# process's os.environ can carry EC2_EXPERIMENT_TAG/EC2_INSTANCE_TYPES/...
# from a sibling study or a leftover manual run, and a whole-environment copy
# would let those silently override lane_env's per-lane config.
#
# Deliberately excludes the keys `lane_env` computes per lane
# (EC2_REQUIRE_GPU, EC2_MAX_PARALLEL_REQUESTS, EC2_EXPERIMENT_TAG/
# EC2_INSTANCE_TYPES/EC2_REGIONS): a stale export from elsewhere must not
# silently re-pin a lane's silicon or re-widen its request fan-out.
# EC2_VLLM_IMAGE is the exception -- a fleet-wide artefact an operator may
# legitimately want to bump without editing this file, and a lane's own
# LANE_IMAGE_OVERRIDES entry still wins over it (see `lane_env`'s
# precedence note).
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
    """Build one lane's complete subprocess environment.
    Reattach contract: both drivers must resolve the same state-file path
    for a lane -- induction from `INDUCTION_STATE_FILE` set below, deduction
    from its own `lane_env_defaults` derivation -- so deduction reattaches
    to induction's box rather than starting a second one; no
    `LEAN_STATE_FILE` is set, since a second spelling of the same path is
    exactly what would drift.

    Pure: always returns a new dict, never mutates `base_env`. Mutating
    `os.environ` across 21 lanes from one parent would let lane N+1 inherit
    lane N's tag and state file, reattaching both to one instance.

    `EC2_VLLM_IMAGE` precedence: a lane's `LANE_IMAGE_OVERRIDES` entry beats
    an operator's export (via `PASSTHROUGH_ENV`) beats ec2.py's own
    digest-pinned default (no key set at all for a non-overridden lane with
    no such export, so `ec2.py` resolves the image itself).
    `EC2_REQUIRE_GPU`/`EC2_MAX_PARALLEL_REQUESTS` are set unconditionally
    instead, deliberately excluded from `PASSTHROUGH_ENV`.

    Parameters
    ----------
    lane : Lane
        Lane whose environment is constructed.
    phase : str
        Driver phase for the subprocess.
    base_env : Optional[Mapping[str, str]], optional
        `None` reads `os.environ`. Returns every `PASSTHROUGH_ENV` key present
        verbatim (missing stays absent) plus the per-lane
        `INFERENCE_PROVIDER`/`EC2_*`/`INDUCTION_*` settings; phase
        ``"deduction"`` also adds `LEAN_MODEL` and `LEAN_RUN_NAME` =
        ``scaling_<key>`` -- the run-directory name
        `supervisor._advance_finished` rebuilds to spool from, so the two must
        stay equal (a mismatch makes that confirming re-spool a silent no-op).

    Returns
    -------
    dict[str, str]
        Complete environment for the lane subprocess.
    """
    if base_env is None:
        base_env = os.environ

    env: dict[str, str] = {key: base_env[key] for key in PASSTHROUGH_ENV if key in base_env}
    env.update(
        {
            "INFERENCE_PROVIDER": "ec2",
            "EC2_EXPERIMENT_TAG": lane.experiment_tag,
            # Required: the driver's own default resolves to the same
            # .ec2_state_induction.json for all 21 lanes, and
            # ec2._reattach_existing_instance trusts that file without
            # re-checking the tag, so every lane would reattach to whichever
            # box it last named.
            "INDUCTION_STATE_FILE": lane.state_file,
            "INDUCTION_MODELS": lane.key,
            "EC2_INSTANCE_TYPES": lane.instance_types,
            "EC2_REGIONS": lane.regions,
            "EC2_REQUIRE_GPU": TIER_REQUIRE_GPU[lane.tier],
            # ec2.py's DETERMINISM_ARGS serve --max-num-seqs 1, so the server
            # executes one request at a time regardless; an 8-way client
            # fan-out would buy no throughput and multiply each request's
            # wall-clock by the in-flight count. Pinning this to 1 makes
            # per-request wall time equal generation time.
            "EC2_MAX_PARALLEL_REQUESTS": "1",
            "EC2_MAX_LIFETIME_MIN": MAX_LIFETIME_MIN,
            "EC2_REQUEST_TIMEOUT_SECONDS": LANE_REQUEST_TIMEOUT_OVERRIDES.get(
                lane.key, REQUEST_TIMEOUT_SECONDS
            ),
        }
    )
    if lane.key in LANE_IMAGE_OVERRIDES:
        # Wins over any operator EC2_VLLM_IMAGE passthrough already copied
        # into env above: a V4 lane must never silently pick up a stray
        # fleet-wide export meant for the other 19 lanes.
        env["EC2_VLLM_IMAGE"] = LANE_IMAGE_OVERRIDES[lane.key]
    if phase == "deduction":
        env.update(
            {
                # No LEAN_STATE_FILE: lane_env_defaults derives the
                # identical path when it's unset (reattach contract above).
                "LEAN_MODEL": lane.key,
                "LEAN_RUN_NAME": f"scaling_{lane.key}",
            }
        )
    return env


# ---------------------------------------------------------------------------
# Lane commands
# ---------------------------------------------------------------------------
# The -c snippet for the "shutdown" phase. ec2._state_path() reads
# EC2_STATE_FILE at call time, so this must set it from the already
# repo-root-anchored INDUCTION_STATE_FILE lane_env provides: ec2.py's
# bare-filename default would otherwise resolve against the subprocess's
# cwd instead of the repo root.
_SHUTDOWN_SNIPPET = (
    "import os; "
    "from smolbench.evals.results_store import repo_root; "
    "os.environ['EC2_STATE_FILE'] = str(repo_root() / os.environ['INDUCTION_STATE_FILE']); "
    "from smolbench.evals.providers.ec2 import shutdown_instance; "
    "shutdown_instance()"
)


def lane_command(lane: Lane, phase: str) -> list[str]:
    """Build the subprocess argv for one lane's `phase`.

    The ``"shutdown"`` argv must run under ``lane_env(lane, "shutdown")`` so
    ``EC2_EXPERIMENT_TAG``/``EC2_STATE_FILE`` resolve to THIS lane's box.

    Parameters
    ----------
    lane : Lane
        Lane whose subprocess command is built.
    phase : str
        Subprocess phase to run.

    Returns
    -------
    list[str]
        Subprocess argument vector.

    Raises
    ------
    ValueError
        Any `phase` outside induction/deduction/shutdown.
    """
    if phase == "induction":
        return [str(VENV_PYTHON), str(REPO_ROOT / "notebooks" / "induction" / "run_study.py")]
    if phase == "deduction":
        return [str(VENV_PYTHON), str(REPO_ROOT / "notebooks" / "deduction" / "run_study.py")]
    if phase == "shutdown":
        return [str(VENV_PYTHON), "-c", _SHUTDOWN_SNIPPET]
    raise ValueError(f"lane_command: unknown phase {phase!r}; expected induction/deduction/shutdown")
