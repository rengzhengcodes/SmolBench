"""21-lane EC2 fleet supervisor for the family-ladder scaling study.

Launches ``notebooks/induction/run_study.py`` once per checkpoint with
``INDUCTION_MODELS`` pinned to one spec key and ``INDUCTION_STATE_FILE`` to a
lane-private EC2 state file, and owns the roster (tiers A-D fix a lane's
instance types, regions and budget), the per-lane environment, the subprocess
lifecycle, the optional deduction phase on the SAME reused box, and the final
S3 spool sync plus shutdown.

- Launch order: tier D first (scarcest capacity), then tier A, staggered. The
  FAMILY GATE (``--no-gate`` skips it) holds tiers B/C until all three
  ``GATE_MODELS`` tier-A lanes -- one per reasoning-toggle style -- log a
  healthy serve, turning a 21-way bet on the digest-pinned ``FLEET_IMAGE`` into
  a 3-way bet.
- Restart policy: :func:`classify_exit` gives a reclaim ``MAX_RECLAIM_RELAUNCHES``
  BACKED-OFF relaunches and a crash ``MAX_CRASH_RELAUNCHES`` immediate ones, then
  HALTS that lane either way; the fleet continues.
- CoT-ON: :func:`reasoning_fraction` HALTS any lane whose first landed replicate
  falls below ``COT_MIN_FRACTION``; non-thinking data is indistinguishable later.
- Phases: ``--phase induction`` (default) never shuts a box down; ``deduction``
  may reattach to the SAME instance (same tag and state file) and, on success,
  spools to S3 and shuts down; ``both`` chains them. Only
  ``scripts/fleet/fleet_teardown.py --terminate`` reclaims the boxes an
  induction-only run leaves up.
- COST: an ungated launch provisions up to 21 DISTINCT spot instances at once,
  ``g6e.4xlarge`` up to 8xB200 ``p6-b200.48xlarge``, each billing while up.
"""

from __future__ import annotations

import argparse
import functools
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from smolbench.evals.results_store import ReplicateAddress, resolve_store

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Anchoring + the induction driver import
# ---------------------------------------------------------------------------
REPO_ROOT: Path = Path(__file__).resolve().parents[2]
VENV_PYTHON: Path = REPO_ROOT / ".venv" / "bin" / "python"

# Loaded by FILE PATH, never `sys.path` plus a bare `import run_study`: the
# deduction study ships its OWN `notebooks/deduction/run_study.py`, and a bare
# module name goes ambiguous once both trees sit on `sys.path`. What this
# module is imported FOR is the driver's per-lane RUNTIME facts -- `BASE_SEED`,
# `INFO_TYPES`, `completion_budget` and `EXPERIMENT` -- which describe how a
# lane runs and live nowhere else. It is NOT imported for the roster: the
# driver is one more consumer of `smolbench/evals/study_config.toml`, not its
# owner, so `LANES` and `_drift_guard` below read the roster from that
# committed config instead, through `_config.ROSTER_KEYS`/`ROSTER_TAGS`. The
# import also runs `load_dotenv(notebooks/induction/keys.env)`, which is
# DESIRED here: it is how AWS profile, results-store and model-cache variables
# reach THIS process, for `lane_env` to pass through to every lane.
_RUN_STUDY_PATH = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
_run_study_spec = importlib.util.spec_from_file_location("induction_run_study", _RUN_STUDY_PATH)
run_study = importlib.util.module_from_spec(_run_study_spec)
sys.modules[_run_study_spec.name] = run_study
_run_study_spec.loader.exec_module(run_study)

# `run_study`'s import of `smolbench.induction.experiment` already pulled in
# `smolbench.evals.providers.ec2`, AFTER its own `load_dotenv` ran, so this is a
# `sys.modules` cache hit, not a second, differently-timed import of `ec2.py`.
#
# `_INSTANCE_GPU_COUNTS`/`_INSTANCE_GPU_NAMES` are private to ec2.py (leading
# underscore); imported here on purpose, not re-declared, so `_tier_gpu_pin`
# below can never drift from that module's own hardware tables -- see
# `EC2_REQUIRE_GPU`'s docstring in ec2.py for what the resulting pin defends
# against.
from smolbench.evals.providers.ec2 import (  # noqa: E402
    EC2_DEPLOY_SPECS,
    EC2_VLLM_IMAGE,
    _INSTANCE_GPU_COUNTS as _EC2_INSTANCE_GPU_COUNTS,
    _INSTANCE_GPU_NAMES as _EC2_INSTANCE_GPU_NAMES,
)

_CONFIG_MODULE_NAME = "smolbench_fleet_config"


def _load_fleet_config():
    """Load ``scripts/fleet/_config.py`` by file path (see its docstring)."""
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        path = Path(__file__).resolve().parent / "_config.py"
        spec = importlib.util.spec_from_file_location(_CONFIG_MODULE_NAME, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[_CONFIG_MODULE_NAME] = module
        spec.loader.exec_module(module)
    return module


# By file path, not a bare `import _config`: `scripts/fleet` has no
# `__init__.py` (it is not a package), and every module in it is already
# loaded under a private module name by its own callers (this file itself is
# loaded under a private name by `tests/tooling/test_run_fleet.py`), so a
# bare import name would be ambiguous at best and simply absent from
# `sys.path` at worst -- see `_config.py`'s own module docstring for the
# fuller argument. Cached under the shared `_CONFIG_MODULE_NAME` key in
# `sys.modules`: if `fleet_status.py` (loaded lazily below, by the identical
# pattern, in `_fleet_status_module`) has already loaded `_config.py` this
# process, this is a cache hit, not a second, independent module object.
_config = _load_fleet_config()

# ---------------------------------------------------------------------------
# Constants (exact names/values -- pinned by tests/tooling/test_run_fleet.py)
# ---------------------------------------------------------------------------
#: Sourced from ``scripts/fleet/_config.py`` (loaded above), the ONE place
#: this string is now declared for every fleet script that needs it --
#: previously an independently-typed copy here could silently drift from
#: ``fleet_status.STATUS_REGIONS`` (finding 14-15).
DEFAULT_REGIONS = _config.DEFAULT_REGIONS
# ec2.py's OWN resolved value: `EC2_VLLM_IMAGE` there defaults to a
# digest-pinned, certified-deterministic vLLM nightly build and is read from
# the environment at ec2.py's IMPORT time. This constant used to carry an
# independently-typed COPY of that digest, and `lane_env` set `EC2_VLLM_IMAGE`
# unconditionally FROM this copy -- so bumping the digest in ec2.py alone left
# every lane silently pinned to the stale one here (finding 14-12). Aliasing
# it means an operator's export reaches every lane through the ONE
# resolution -- this module's, via ec2.py -- instead of two that could
# disagree. Bump only on purpose, and bump it in ec2.py.
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
# deepseek-v4-pro serves --enforce-eager (see EC2_DEPLOY_SPECS): a
# budget-burning 87k-token generation takes >1h at eager Pro throughput -- a
# SINGLE-request figure, independent of how many requests are in flight -- so
# under the fleet-wide 3600s timeout those cells retry forever; 14400s lets a
# worst-case cell finish in ONE attempt. The box-side idle watchdog keys on
# vLLM metrics activity, so an hours-long in-flight generation cannot trip it.
#
# NOTE (finding 14-10, recomputed): this dict used to also carry 10800s
# entries for gemma-4-12b and ministral-3-14b, derived as "~90 min at 3
# concurrent with 2x headroom". That assumed 3 requests in flight; the real
# client fan-out is `ChatClient.evaluate`'s `EC2_MAX_PARALLEL_REQUESTS`
# default of 8, against ec2.py's `--max-num-seqs 1` serving, so requests
# actually SERIALIZE and the in-flight count that matters is whatever
# `lane_env` pins -- see that function's `EC2_MAX_PARALLEL_REQUESTS` comment.
# `lane_env` now pins it to "1" for every lane, so the values below all
# assume in-flight 1. Recomputed from this comment's own two anchors:
#   anchor 1 (per-cell wall time): ~90 min at 3 concurrent -> ~30 min
#     (1800s) for one cell alone. At in-flight 1: 1 x 1800s x 2 (headroom)
#     = 3600s -- exactly REQUEST_TIMEOUT_SECONDS, the fleet-wide default --
#     so a per-lane override for these two lanes is now redundant. REMOVED.
#   anchor 2 (aggregate throughput): an 87k-token cell at ~146 tok/s
#     aggregate -> ~596s alone -- an even smaller number, so 3600s is safe
#     under either reading.
LANE_REQUEST_TIMEOUT_OVERRIDES = {
    # >1h at eager Pro throughput (see the comment above) is a SINGLE-request
    # figure that does not depend on the in-flight count, so it is unaffected
    # by the EC2_MAX_PARALLEL_REQUESTS pin.
    "deepseek-v4-pro": "14400",
}

TIER_INSTANCE_TYPES = {
    # NARROWED to one GPU count (finding 14-06): this list used to also hunt
    # g6e.12xlarge (4x L40S) as a capacity fallback, mixing it with the
    # 1-GPU types it hunts alongside (g6e.4xlarge, g6e.8xlarge).
    # `ec2.derive_tp` = gcd(attention heads, landed GPU count), so a reclaim
    # onto that fallback changed a tier-A lane's derived tp from 1 to 4
    # MID-LANE -- rows collected before and after the fallback are not
    # comparable. The TRADE: dropping the 4-GPU fallback means a reclaimed
    # tier-A lane now waits for 1-GPU g6e capacity instead of silently
    # switching tp -- the residual cost is that such a lane can idle longer
    # when 1-GPU g6e capacity is tight. g6e.8xlarge remains as a same-tp,
    # larger-host fallback. `TIER_REQUIRE_GPU` below pins this tier's GPU
    # count/silicon so a mixed-count hunt list here cannot recur unnoticed.
    "A": "g6e.4xlarge,g6e.8xlarge",
    "B": "g6e.12xlarge,g6e.24xlarge",
    "C": "p5.48xlarge,p5e.48xlarge",
    # D is p6-b200 (8x B200, SM100). deepseek-v4-pro's spec drops its
    # Marlin pin for SM100's native MXFP4 path; that marlin-less spec MUST
    # NOT serve on p5e/p5en (see the spec comment in ec2.py).
    "D": "p6-b200.48xlarge",
}


def _tier_gpu_pin(tier: str) -> str:
    """Derive tier `tier`'s ``ec2.EC2_REQUIRE_GPU`` pin from its hunt list.

    Maps every instance type in ``TIER_INSTANCE_TYPES[tier]`` through ec2.py's
    OWN ``_INSTANCE_GPU_COUNTS``/``_INSTANCE_GPU_NAMES`` tables (imported
    above, deliberately, so this pin can never drift from that module's
    hardware data). DERIVED, never a hand-written literal table: the tier's
    hunt list is the single source of truth, and an edit to
    ``TIER_INSTANCE_TYPES`` that is not also safe for this function to run
    against is exactly the drift ``EC2_REQUIRE_GPU`` exists to catch (see
    ``TIER_INSTANCE_TYPES["A"]``'s comment for the incident that motivated it).

    Parameters
    ----------
    tier : str
        A key of ``TIER_INSTANCE_TYPES``.

    Returns
    -------
    str
        ``"<gpu-name-substring>:<count>"`` (e.g. ``"L40S:1"``) when every
        type in the tier's hunt list shares both one GPU count and one GPU
        name; ``":<count>"`` (e.g. ``":8"``) when the count agrees but the
        names differ -- see Notes for why that is still a meaningful pin.

    Raises
    ------
    SystemExit
        Raised explicitly, never via ``assert`` (which ``python -O`` strips),
        naming `tier` and the offending type(s), when: (a) any type in the
        tier's hunt list is absent from ec2.py's ``_INSTANCE_GPU_COUNTS`` or
        ``_INSTANCE_GPU_NAMES``, so its silicon cannot be verified; or (b) the
        tier's types do not share exactly one GPU count. Both are the
        unmappable-or-mixed-count hunt list this pin exists to prevent from
        ever reaching a lane's environment unnoticed.

    Notes
    -----
    A count-only pin (empty name substring) is weaker by construction:
    ``ec2._assert_required_gpu`` checks membership of the pin's name
    substring in the landed box's GPU name string, and an empty substring is
    trivially "in" any string -- so an empty name matches any silicon while
    the count is still enforced. This is deliberate for tier C, whose hunt
    list (``p5.48xlarge`` = 8x H100 80GB, ``p5e.48xlarge`` = 8x H200 141GB)
    is genuinely different silicon that this study accepts as interchangeable
    at the same 8-GPU count: the pin still blocks the tp-changing
    substitution it was added for (a capacity reclaim landing on a DIFFERENT
    GPU COUNT), but it does not -- and, per ``EC2_REQUIRE_GPU``'s own
    "Determinism scope" note, cannot -- pin the reduction-order-changing one
    (same GPU count, different silicon, same tp, different numerics).
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
    # Names differ (e.g. tier C's H100 vs H200) but the count still agrees:
    # a count-only pin -- see this function's Notes for why that is safe.
    return f":{count}"


#: Per-tier ``EC2_REQUIRE_GPU`` pin, set for every lane by `lane_env`. See
#: `_tier_gpu_pin` for how each value is derived (never a hand-written
#: literal) and what a count-only entry (e.g. tier C's) means.
TIER_REQUIRE_GPU: dict[str, str] = {tier: _tier_gpu_pin(tier) for tier in TIER_INSTANCE_TYPES}

# Tier D only; every other tier falls back to DEFAULT_REGIONS. All 3 study
# regions stay in the p6-b200 hunt: unlike p5e (us-east-2/us-west-2 only),
# B200 placement is still shifting, so excluding a region risks starving
# the experiment. Built FROM `DEFAULT_REGIONS` (itself `_config.DEFAULT_REGIONS`)
# rather than its own literal, so this cannot spell a second, independently
# drifting copy of the same three regions.
TIER_REGIONS = {"D": DEFAULT_REGIONS}
TIER_BUDGET_HOURS = {"A": 9, "B": 9, "C": 10, "D": 14}

TIER_MEMBERS = {
    # gemma-4-12b is tier B, not A: its spec runs tp=4, and tier A's hunt
    # list mixes 1-GPU types where tp=4 cannot construct ("World size (4)
    # is larger than the number of available GPUs"). Tier B is all-4-GPU.
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
    # deepseek-v4-flash is tier D. Its spec switched to the
    # marlin-less SM100 recipe (see ec2.py), which must only serve on
    # tier D's p6-b200 hunt list, never on C's p5/p5e.
    "D": ("glm-4.7", "deepseek-v3.1", "deepseek-v4-pro", "deepseek-v4-flash"),
}

GATE_MODELS = ("gemma-4-e2b", "nemotron-3-nano-4b", "ministral-3-3b")
MAX_CRASH_RELAUNCHES = 2
# Finding 14-02: a RECLAIM verdict used to get unlimited relaunches, on the
# theory that a spot reclaim is never the lane's fault. But an empty or
# failed `describe_instances` sweep (see `_Presence`) made EVERY exit look
# like a reclaim, so "unlimited" meant a lane could relaunch forever with no
# crash counting and no budget alert ever firing (`_monitor_tick`'s 2x-budget
# check keys on `lane_started_at`, which a relaunch never resets, but nothing
# stopped the relaunches themselves). Bounding it, with backoff so a lane
# genuinely fighting spot capacity is not hammered every tick:
#   delay before relaunch n = min(RECLAIM_BACKOFF_CAP_SECONDS,
#                                  RECLAIM_BACKOFF_BASE_SECONDS * 2 ** (n - 1))
#   = 60, 120, 240, 480, 960, then 1800s thereafter.
# MAX_RECLAIM_RELAUNCHES=12 relaunches therefore span about 4h of backoff
# (60+120+240+480+960+1800*7 ~= 4.15h) against a 9-14h tier budget
# (TIER_BUDGET_HOURS), so a lane fighting genuine capacity pressure still
# gets most of its budget, while the pathological misclassification above
# stops at 12 relaunches instead of running for the fleet's whole lifetime.
# `run_shards.py`'s flat `CAPACITY_BACKOFF_SECONDS = 300` is the analogous
# existing policy for its own capacity-shaped retries.
MAX_RECLAIM_RELAUNCHES = 12
RECLAIM_BACKOFF_BASE_SECONDS = 60
RECLAIM_BACKOFF_CAP_SECONDS = 1800
# A DEAD toggle measures ~0-11% (bare integers everywhere); a
# working-but-variable soft protocol measures 78-100%. 0.5 cleanly
# separates the two regimes. (With only 9 intens marks, a 0.9 threshold
# trips on one or two direct answers from a capable model.)
COT_MIN_FRACTION = 0.5
#: A response longer than this counts as a reasoning chain carried in content
#: (the quiz contract asks for a single bare integer). See
#: ``reasoning_fraction``'s Notes.
COT_CONTENT_REASONING_MIN_CHARS = 200
LAUNCH_STAGGER_SECONDS = 30
MONITOR_INTERVAL_SECONDS = 60
DESCRIBE_EVERY_N_TICKS = 5


# ---------------------------------------------------------------------------
# Lane / LANES
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Lane:
    """One study checkpoint's fleet identity: spec key, analysis tag, tier.

    `key` is an ``EC2_DEPLOY_SPECS`` / ``_config.ROSTER_KEYS`` key and vLLM's
    ``--served-model-name``; `tag` is ``_config.ROSTER_TAGS[key]``, the
    committed study config's analysis tag for that checkpoint, used in result
    directory names and figure legends; `tier` is ``"A"``-``"D"``. Everything
    else is DERIVED below, so a tier constant cannot go stale in a per-lane copy.
    """

    key: str
    tag: str
    tier: str

    @property
    def instance_types(self) -> str:
        """Comma-separated EC2 instance-type hunt order for this lane's tier."""
        return TIER_INSTANCE_TYPES[self.tier]

    @property
    def regions(self) -> str:
        """Comma-separated AWS regions for this lane's tier."""
        return TIER_REGIONS.get(self.tier, DEFAULT_REGIONS)

    @property
    def experiment_tag(self) -> str:
        """This lane's ``smolbench:experiment`` tag value: ``f"{prefix}{key}"``.

        `prefix` is ``_config.SCALING_TAG_PREFIX`` (``"scaling-"``), the same
        constant ``fleet_status.py`` reads, so the two scripts cannot spell
        this prefix differently.
        """
        return f"{_config.SCALING_TAG_PREFIX}{self.key}"

    @property
    def state_file(self) -> str:
        """This lane's private EC2 state-file basename (repo-root-anchored by the driver).

        Spelled ``.ec2_state_scaling_<key>.json`` literally, NOT derived from
        `experiment_tag`'s ``_config.SCALING_TAG_PREFIX``: ``fleet_teardown.py``'s
        glob depends on this exact ``.ec2_state_scaling_`` spelling, and the
        two prefixes (``"scaling-"`` for the tag, ``"scaling_"`` here) are
        independent strings by construction, not a typo needing to be unified.
        """
        return f".ec2_state_scaling_{self.key}.json"

    @property
    def budget_hours(self) -> int:
        """Expected wall-clock hours for this tier; `_monitor_tick` alerts past 2x."""
        return TIER_BUDGET_HOURS[self.tier]


def _drift_guard() -> None:
    """Verify, at IMPORT time, that ``TIER_MEMBERS`` agrees with both sources of truth.

    ``TIER_MEMBERS`` is HAND-WRITTEN and must match ``_config.ROSTER_KEYS``
    (the committed ``study_config.toml`` roster) and
    ``set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"}``; a rung added there but not
    here would silently never run. At import time, so even a bare import or
    ``--dry-run`` catches the drift.

    Checking against the config's roster rather than the induction driver's
    ``MODELS`` is deliberate: the driver builds ``MODELS`` from that same
    config, so it is a consumer, not an authority, and pinning this guard to
    the config keeps the tier table answerable to the file an operator
    actually edits when the ladder changes.

    Raises
    ------
    SystemExit
        Tiers not pairwise disjoint, or roster drift against either source.
        Raised explicitly, never via ``assert``, which ``python -O`` strips.
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


# Run BEFORE `LANES` is built, so the `_config.ROSTER_TAGS[key]` lookup below
# is already certified total over TIER_MEMBERS and can never KeyError.
_drift_guard()

#: Spec key -> Lane for every model this study runs, built from
#: TIER_MEMBERS x _config.ROSTER_TAGS -- i.e. the tier assignment is this
#: file's, the roster and its analysis tags are the committed study config's;
#: _drift_guard above has already certified the two against each other.
LANES: dict[str, Lane] = {
    key: Lane(key=key, tag=_config.ROSTER_TAGS[key], tier=tier)
    for tier, keys in TIER_MEMBERS.items()
    for key in keys
}


# ---------------------------------------------------------------------------
# Per-lane environment
# ---------------------------------------------------------------------------
# An explicit ALLOWLIST, not `dict(os.environ)` plus overrides: this process's
# `os.environ` can carry `EC2_EXPERIMENT_TAG`/`EC2_INSTANCE_TYPES`/... from a
# sibling study or a leftover manual run in this shell, and a whole-environment
# copy would let those silently override `lane_env`'s per-lane config. Nothing
# not named here ever crosses into a lane's environment.
#
# This module deliberately OWNS, and therefore does NOT list here, the keys
# `lane_env` computes per lane: `EC2_REQUIRE_GPU` (the tier's hardware pin,
# see `TIER_REQUIRE_GPU`), `EC2_MAX_PARALLEL_REQUESTS` (pinned to "1" -- see
# `lane_env`'s body) and the `EC2_EXPERIMENT_TAG`/`EC2_INSTANCE_TYPES`/
# `EC2_REGIONS` family already set below. A stale export from a sibling study
# or an earlier manual run must not silently re-pin a lane's silicon or
# re-widen its request fan-out -- the same argument that makes this whole
# list an allowlist rather than an environment copy. `EC2_VLLM_IMAGE` is the
# deliberate EXCEPTION: it is a fleet-wide artefact an operator may
# legitimately want to bump without editing this file, and a lane's own
# `LANE_IMAGE_OVERRIDES` entry still wins over it (see `lane_env`'s
# Precedence note).
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

    Parameters
    ----------
    phase : str
        ``"induction"``, ``"deduction"`` or ``"shutdown"``.
    base_env : Mapping[str, str] or None, optional
        Source of the passthrough values; ``None`` reads ``os.environ``.

    Returns
    -------
    dict[str, str]
        Every ``PASSTHROUGH_ENV`` key present in `base_env`, verbatim (a missing
        key stays absent -- no invented defaults), plus the per-lane
        ``INFERENCE_PROVIDER``/``EC2_*``/``INDUCTION_*`` settings below. Phase
        ``"deduction"`` also adds ``LEAN_MODEL``, ``LEAN_STATE_FILE`` (the SAME
        value as ``INDUCTION_STATE_FILE`` -- the reattach contract) and
        ``LEAN_RUN_NAME`` = ``scaling_<key>``, which
        ``notebooks/deduction/run_study.py`` defaults to and
        `_advance_finished` builds the same ``scaling_<key>`` run directory
        name from, to hand to that driver's own ``spool_to_s3``.

    Notes
    -----
    PURE: never mutates `base_env`, always returns a NEW ``dict``. Mutating
    ``os.environ`` across 21 lanes launched from one parent would let lane N+1
    inherit lane N's tag and state file, and the two would then reattach to ONE
    instance, swapping each other's checkpoint out.

    Precedence for ``EC2_VLLM_IMAGE``: a lane's own ``LANE_IMAGE_OVERRIDES``
    entry (highest) beats an operator's ``EC2_VLLM_IMAGE`` export, carried
    through ``PASSTHROUGH_ENV`` (middle), beats ec2.py's own digest-pinned
    default (lowest -- this function sets NO key at all for a non-overridden
    lane with no such export in `base_env`, so that lane's own ``ec2.py``
    import resolves the image exactly as this supervisor's did). By contrast,
    ``EC2_REQUIRE_GPU`` and ``EC2_MAX_PARALLEL_REQUESTS`` are set
    UNCONDITIONALLY for every lane and are deliberately NOT in
    ``PASSTHROUGH_ENV`` -- see that tuple's comment for why.
    """
    if base_env is None:

        base_env = os.environ

    env: dict[str, str] = {key: base_env[key] for key in PASSTHROUGH_ENV if key in base_env}
    env.update(
        {
            "INFERENCE_PROVIDER": "ec2",
            "EC2_EXPERIMENT_TAG": lane.experiment_tag,
            "INDUCTION_STATE_FILE": lane.state_file,
            "INDUCTION_MODELS": lane.key,
            "EC2_INSTANCE_TYPES": lane.instance_types,
            "EC2_REGIONS": lane.regions,
            "EC2_REQUIRE_GPU": TIER_REQUIRE_GPU[lane.tier],
            # ec2.py's DETERMINISM_ARGS serve --max-num-seqs 1, so the server
            # executes one request at a time regardless; an 8-way client
            # fan-out (ChatClient.evaluate's EC2_MAX_PARALLEL_REQUESTS
            # default) therefore buys no throughput and multiplies every
            # request's wall-clock by the number in flight -- which is what
            # invalidated LANE_REQUEST_TIMEOUT_OVERRIDES's old 3-concurrent
            # arithmetic (see that dict's comment). Pinning this to 1 makes
            # per-request wall time equal to generation time.
            "EC2_MAX_PARALLEL_REQUESTS": "1",
            "EC2_MAX_LIFETIME_MIN": MAX_LIFETIME_MIN,
            "EC2_REQUEST_TIMEOUT_SECONDS": LANE_REQUEST_TIMEOUT_OVERRIDES.get(
                lane.key, REQUEST_TIMEOUT_SECONDS
            ),
        }
    )
    if lane.key in LANE_IMAGE_OVERRIDES:
        # Per-lane override wins over any operator EC2_VLLM_IMAGE passthrough
        # already copied into `env` above (see this function's Precedence
        # note): a V4 lane must never silently pick up a stray fleet-wide
        # export meant for the other 19 lanes.
        env["EC2_VLLM_IMAGE"] = LANE_IMAGE_OVERRIDES[lane.key]
    if phase == "deduction":
        env.update(
            {
                "LEAN_MODEL": lane.key,
                "LEAN_STATE_FILE": lane.state_file,
                "LEAN_RUN_NAME": f"scaling_{lane.key}",
            }
        )
    return env


# ---------------------------------------------------------------------------
# Lane commands
# ---------------------------------------------------------------------------
# The `-c` snippet run for the "shutdown" phase. `ec2._state_path()` reads
# `EC2_STATE_FILE` at CALL time (see that module's "Env-read timing" docstring
# section), so this snippet must set it from the already-repo-root-anchored
# `INDUCTION_STATE_FILE` that `lane_env` provides, mirroring
# `InductionExperiment._apply_env`: ec2.py's bare-filename default would resolve
# against the subprocess's cwd instead of the repo root.
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
    ``EC2_EXPERIMENT_TAG``/``EC2_STATE_FILE`` resolve to THIS lane's box. Any
    `phase` outside induction/deduction/shutdown raises ``ValueError``.
    """
    if phase == "induction":
        return [str(VENV_PYTHON), str(REPO_ROOT / "notebooks" / "induction" / "run_study.py")]
    if phase == "deduction":
        return [str(VENV_PYTHON), str(REPO_ROOT / "notebooks" / "deduction" / "run_study.py")]
    if phase == "shutdown":
        return [str(VENV_PYTHON), "-c", _SHUTDOWN_SNIPPET]
    raise ValueError(f"lane_command: unknown phase {phase!r}; expected induction/deduction/shutdown")


# ---------------------------------------------------------------------------
# Serve-health line matching
# ---------------------------------------------------------------------------
# `ec2.serve_model` logs exactly `serve_model: '<model>' is up at
# http://<ip>:8000/v1` once the swapped-in checkpoint is confirmed healthy. The
# earlier in-flight line (`serve_model: requesting '<model>' ...`) must NOT
# match -- that line is what the family gate is waiting to stop seeing.
SERVE_HEALTHY_RE = re.compile(r"serve_model: '.+?' is up at http://\S+")


def is_serve_healthy(line: str) -> bool:
    """Check whether `line` (logging prefix allowed) is ec2.py's healthy-serve log line."""
    return SERVE_HEALTHY_RE.search(line) is not None


# ---------------------------------------------------------------------------
# Restart-policy classifier
# ---------------------------------------------------------------------------
# Deliberately EXCLUDES the bare provisioning line (`provision_spot_instance:
# trying <type> in <az> ...`, logged by `ec2._launch_fresh` on EVERY attempt):
# it appears in successful launches too, so matching it would misclassify a
# provisioning-time CRASH -- which also logs "trying ..." before failing -- as a
# reclaim, and reclaims get UNLIMITED retries. Only failure wording counts:
# capacity/quota errors, and the "endpoint unreachable" message ec2.py raises
# after its connection-failure cap trips (the spot-reclaim/IP-drift symptom).
RECLAIM_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"InsufficientInstanceCapacity",
        r"spot quota exhausted",
        r"MaxSpotInstanceCountExceeded",
        r"SpotMaxPriceTooLow",
        r"spot capacity",
        r"capacity-not-available",
        r"spot interruption",
        r"endpoint unreachable",
    )
)


def classify_exit(log_tail: str, instance_present: bool) -> str:
    """Classify a lane's non-zero exit as a spot reclaim or a real crash.

    Parameters
    ----------
    log_tail : str
        The lane's last ~40 log lines at the moment the exit was observed.
    instance_present : bool
        Whether its ``scaling-<key>`` instance was in the last sweep.

    Returns
    -------
    str
        ``"reclaim"`` when the instance is absent or `log_tail` matches
        ``RECLAIM_PATTERNS``; ``"crash"`` otherwise, INCLUDING an empty tail with
        the instance still present.

    Notes
    -----
    A backwards verdict either abandons a lane on a routine interruption or
    burns money relaunching one that will always fail the same way.
    """
    if not instance_present:
        return "reclaim"
    if any(pattern.search(log_tail) for pattern in RECLAIM_PATTERNS):
        return "reclaim"
    return "crash"


# ---------------------------------------------------------------------------
# CoT-ON assertion
# ---------------------------------------------------------------------------
def reasoning_fraction(
    store: Any,
    model: str,
    tag: str,
    seed: Optional[int] = None,
    infos: Optional[Sequence[str]] = None,
) -> Optional[float]:
    """Measure the fraction of a model's landed marks that carry reasoning evidence.

    Parameters
    ----------
    store : Any
        Duck-typed ``ResultsStore`` (``exists``/``load_marks``), injected so this
        is testable with a fake and no S3; production passes `build_results_store`.
    tag : str
        Analysis tag -- unused by the S3 backend, required by ``ReplicateAddress``.
    seed : int or None, optional
        ``None`` uses ``run_study.BASE_SEED``, the FIRST replicate a lane collects.
    infos : Sequence[str] or None, optional
        Info arms to pool; ``None`` uses ``run_study.INFO_TYPES`` (all four).

    Returns
    -------
    float or None
        ``None`` when no arm has landed yet for (`model`, `seed`); otherwise the
        fraction of pooled marks with a non-empty ``Mark.reasoning`` OR a
        ``Mark.response`` longer than ``COT_CONTENT_REASONING_MIN_CHARS``.

    Notes
    -----
    Response length counts because models on a SOFT thinking protocol
    (Ministral's [THINK] system prompt, EXAONE's ``enable_thinking``) wrap only
    some chains in think markup, leaving 40-60% of marks with the chain in plain
    ``response``. The quiz contract is "exactly one integer and nothing else",
    so a long response is a chain, while a dead toggle -- bare integers, an
    empty reasoning channel -- still fails.
    """
    if seed is None:
        seed = run_study.BASE_SEED
    if infos is None:
        infos = run_study.INFO_TYPES

    pooled = []
    for info in infos:
        addr = ReplicateAddress(tag=tag, info=info, seed=seed, model=model)
        if not store.exists(addr):
            continue
        pooled.extend(store.load_marks(addr).marks)

    if not pooled:
        return None
    return sum(
        1
        for mark in pooled
        if mark.reasoning
        or len(mark.response or "") > COT_CONTENT_REASONING_MIN_CHARS
    ) / len(pooled)


def build_results_store() -> Any:
    """Build the production ``ResultsStore`` for this study's results directory.

    ``resolve_store`` picks S3 when ``SMOLBENCH_RESULTS_S3`` is set, local
    otherwise; kept out of :func:`reasoning_fraction` so that stays fake-able.
    """
    return resolve_store(run_study.EXPERIMENT.results_dir)


# ---------------------------------------------------------------------------
# Pre-flight (before any subprocess.Popen)
# ---------------------------------------------------------------------------
def preflight(lanes: Sequence[Lane]) -> dict[str, int]:
    """Warm every lane's tokenizer and derive its completion budget.

    Calls ``run_study.completion_budget`` per lane BEFORE any subprocess or EC2
    provisioning -- pure CPU plus HuggingFace downloads, on a machine not yet
    billing -- so a tokenizer-fetch failure or an under-budget verdict cannot
    surface between a live GPU box and its first request.

    Returns
    -------
    dict[str, int]
        Spec key -> completion-token budget, only when EVERY lane succeeded.

    Raises
    ------
    SystemExit
        If any lane failed, by exception or by ``completion_budget``'s own
        ``SystemExit`` for a budget below ``run_study.MIN_VIABLE_BUDGET``. Both
        kinds are COLLECTED across all lanes (hence ``except (Exception,
        SystemExit)``, since ``SystemExit`` is not an ``Exception``) and printed
        as one table.
    """
    budgets: dict[str, int] = {}
    failures: list[tuple[str, str, str]] = []
    seeds = range(run_study.BASE_SEED, run_study.BASE_SEED + run_study.N_REPLICATES)
    for lane in lanes:
        try:
            budgets[lane.key] = run_study.completion_budget(lane.key, seeds)
        except (Exception, SystemExit) as exc:  # noqa: BLE001 -- collected, see docstring
            failures.append((lane.key, type(exc).__name__, str(exc)))

    if failures:
        header = f"{'lane':<32}{'exception':<20}message"
        lines = [header, "-" * len(header)]
        for key, exc_type, message in failures:
            lines.append(f"{key:<32}{exc_type:<20}{message}")
        raise SystemExit(
            f"run_fleet: preflight failed for {len(failures)} lane(s); aborting before any "
            "subprocess is launched (no billing box was ever touched):\n" + "\n".join(lines)
        )
    logging.info(f"run_fleet: preflight OK for {len(budgets)} lane(s).")
    return budgets


def fleet_image_digest() -> Optional[str]:
    """Look up a best-effort ``docker manifest inspect`` digest for ``FLEET_IMAGE``.

    ``FLEET_IMAGE`` is already digest-pinned, so this is only a resolvability
    check for the run banner; it never raises, since it must not block a launch.

    Returns
    -------
    str or None
        For a multi-arch image, a PER-ARCHITECTURE digest (``manifests[0]``),
        which will NOT match the index digest in the ref. ``None``, always
        logged at INFO, when ``docker`` is missing, the inspect call fails, or
        the JSON has no digest field.
    """
    if shutil.which("docker") is None:
        logging.info("fleet_image_digest: docker not found on PATH; skipping digest lookup.")
        return None
    try:
        result = subprocess.run(
            ["docker", "manifest", "inspect", FLEET_IMAGE],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
    except Exception as exc:  # noqa: BLE001 -- best-effort banner info only, never fatal
        logging.info(f"fleet_image_digest: 'docker manifest inspect' failed: {exc}")
        return None

    try:
        manifest = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        logging.info(f"fleet_image_digest: could not parse manifest JSON: {exc}")
        return None

    digest = manifest.get("config", {}).get("digest")
    if not digest:
        # A multi-arch image returns a manifest LIST, not a single manifest with
        # a top-level "config"; fall back to the first platform entry.
        entries = manifest.get("manifests") or []
        if entries:
            digest = entries[0].get("digest")
    if not digest:
        logging.info("fleet_image_digest: manifest JSON had no recognisable digest field.")
        return None
    return digest


# ---------------------------------------------------------------------------
# Lane logs
# ---------------------------------------------------------------------------
# __file__-anchored per repo convention, never cwd-relative, since this script
# may launch from any working directory. It sits inside an already-gitignored
# tree (`notebooks/*/results/`), and `*.log` is separately gitignored on top of
# that, so lane logs -- gigabytes of vLLM/CoT chatter over a study run -- never
# enter a commit either way.
LOG_DIR: Path = REPO_ROOT / "notebooks" / "induction" / "results" / "fleet_logs"

#: Byte budget `_tail_log` reads from the END of a lane's log file. Finding
#: 14-03: `_apply_restart_policy` calls `_tail_log` every tick for every lane
#: whose subprocess just exited, and a live lane's log can reach gigabytes
#: over a multi-hour vLLM serve, so reading the WHOLE file every tick does
#: not scale. 256 KiB is deliberately generous relative to the ~40 lines
#: callers ask for: UNDER-reading is not neutral here -- a `RECLAIM_PATTERNS`
#: match that falls outside the read window would silently reclassify a
#: reclaim as a crash, halting a lane that should have been relaunched.
TAIL_MAX_BYTES = 262144


def _tail_log(log_dir: Path, key: str, n: int = 40, *, max_bytes: int = TAIL_MAX_BYTES) -> str:
    """Return the last `n` lines of lane `key`'s log file, or ``""`` if unreadable.

    Reads at most `max_bytes` (default `TAIL_MAX_BYTES`) from the END of the
    file (seek-from-end), never the whole file -- see `TAIL_MAX_BYTES`'s
    comment for why that budget is generous rather than tight.

    Notes
    -----
    When the file is bigger than `max_bytes`, the read does not start at byte
    0, so its first line is very likely PARTIAL (the seek landed mid-line);
    that line is dropped rather than returned, since a partial line could
    spuriously match or fail to match a pattern a caller checks lines
    against (`is_serve_healthy`, `RECLAIM_PATTERNS`).
    """
    path = log_dir / f"{key}.log"
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            start = max(0, size - max_bytes)
            f.seek(start)
            chunk = f.read()
    except OSError:
        return ""
    lines = chunk.decode("utf-8", errors="replace").splitlines()
    if start > 0 and lines:
        lines = lines[1:]  # drop the partial first line -- see docstring
    return "\n".join(lines[-n:])


def _start_phase(run: "_LaneRun", log_dir: Path) -> None:
    """Launch `run`'s CURRENT phase as a subprocess; append its log to ``<key>.log``."""
    phase = run.current_phase
    if phase is None or phase == "shutdown":
        raise RuntimeError(f"_start_phase: lane {run.lane.key} has no runnable current phase")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{run.lane.key}.log"
    cmd = lane_command(run.lane, phase)
    env = lane_env(run.lane, phase)
    logging.info(f"run_fleet[{run.lane.key}]: launching phase={phase!r}: {' '.join(cmd)}")
    # Append mode lets the family gate scan a lane's WHOLE log -- across a
    # relaunch or a later phase -- for the one-time healthy-serve line; a
    # truncating mode would lose it the moment the lane's phase changed.
    with open(log_path, "a") as log_file:
        run.proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file, env=env)
    run.started_at = time.monotonic()
    if not run.lane_started_at:
        # FIRST launch only -- see `_LaneRun.lane_started_at`'s docstring for
        # why the 2x-budget alert must key on this instead of `started_at`.
        run.lane_started_at = run.started_at


def _launch_batch(runs: dict, keys: Sequence[str], log_dir: Path) -> None:
    """Launch each lane in `keys` at its current phase, ``LAUNCH_STAGGER_SECONDS`` apart."""
    for i, key in enumerate(keys):
        if i:
            time.sleep(LAUNCH_STAGGER_SECONDS)
        _start_phase(runs[key], log_dir)


# ---------------------------------------------------------------------------
# Live orchestration: launch, monitor, restart, phase-advance, gate, shutdown
# ---------------------------------------------------------------------------
# Nothing below this point runs at import time; it is reached only from
# main()'s live (non-`--dry-run`) path.


@functools.lru_cache(maxsize=1)
def _fleet_status_module():
    """Lazily load ``scripts/fleet/fleet_status.py`` by file path; cached.

    By path, like `run_study` above, to avoid colliding with the private module
    name ``tests/tooling/test_run_fleet.py`` loads this file under.
    """
    path = Path(__file__).resolve().parent / "fleet_status.py"
    spec = importlib.util.spec_from_file_location("run_fleet_fleet_status_dep", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@functools.lru_cache(maxsize=1)
def _deduction_driver():
    """Lazily load ``notebooks/deduction/run_study.py`` by file path; cached.

    Finding 14-11: this supervisor used to re-implement the S3 spool upload
    itself (`sync_deduction_spool`, now DELETED), without the driver's own
    ``head_object``/``ContentLength`` verification -- an unverified upload
    followed by a local delete can lose rows silently. Loading the driver and
    calling its OWN ``spool_to_s3`` instead means one verified implementation,
    not two that can drift.

    LAZY on purpose, never imported at module scope: that module pulls in
    ``smolbench.deduction.lean.runner`` (which pulls ``tiktoken``, unneeded by
    every OTHER path through this supervisor) and, at MODULE SCOPE, runs
    ``os.environ.setdefault`` work keyed on ``LEAN_MODEL`` plus a guard that
    raises ``SystemExit`` when ``EC2_EXPERIMENT_TAG`` is not exactly
    ``f"scaling-{LEAN_MODEL}"`` (see that file's module docstring). Neither
    variable is set in THIS process's environment (they are per-lane
    subprocess env, built by `lane_env` and never written to `os.environ`
    here), so that guard's ``if _RAW_LEAN_MODEL:`` gate is false and the
    whole block -- setdefaults and guard alike -- is skipped on load,
    regardless of which lane's `_advance_finished` call triggers it first.
    Called only from `_advance_finished`.

    Registered in `sys.modules` under a distinct private name BEFORE
    ``exec_module``, exactly as the induction loader at the top of this file
    does (a ``@dataclass`` applied inside a module not yet in `sys.modules`
    raises ``AttributeError`` -- see that loader's comment).
    """
    path = REPO_ROOT / "notebooks" / "deduction" / "run_study.py"
    spec = importlib.util.spec_from_file_location("run_fleet_deduction_run_study_dep", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class _Presence:
    """Last describe sweep's lane set, plus whether any lane has EVER been seen.

    Distinguishes three states a `fleet_status.fleet_rows()` sweep can leave a
    lane's presence in: seen THIS sweep (`lanes` is the fresh set), seen
    BEFORE and now gone (`lanes` is an explicit empty ``set()`` -- the fleet
    really is empty), and never seen YET (`lanes` is ``None`` -- unknown).
    Collapsing the last two into "empty" is finding 14-02: a fleet that has
    not finished provisioning its first box looks IDENTICAL, via
    `fleet_rows`, to every region's ``describe_instances`` raising -- both
    return ``[]`` -- so reading an early empty sweep as "everything is gone"
    turned every lane's exit into an unlimited-retry reclaim before a single
    box had even been described successfully.

    Attributes
    ----------
    lanes : set or None
        Lane keys from the most recent sweep that did not raise; ``None``
        means no such sweep has landed yet (or every one so far has come back
        empty with nothing ever seen -- see `observe`).
    ever_seen : bool
        Whether any past sweep has returned a NON-EMPTY lane set.
    """

    lanes: Optional[set] = None
    ever_seen: bool = False

    def observe(self, swept: set) -> None:
        """Update presence from one sweep's raw lane set.

        Parameters
        ----------
        swept : set
            Lane keys ``fleet_status.fleet_rows()`` returned THIS sweep. Call
            only for a sweep that did NOT raise -- see `_monitor_tick`, which
            treats a raising sweep as a separate case (logged and skipped,
            `observe` never runs, `lanes` keeps its last value).

        Notes
        -----
        PURE: no I/O, no AWS, no monitor-loop dependency -- directly
        unit-testable against a bare ``set``. Semantics:

        * non-empty `swept` -> ``lanes = set(swept)``, ``ever_seen = True``.
        * empty `swept` and `ever_seen` -> ``lanes = set()``: a fleet that HAS
          been seen non-empty before and is now empty really is empty -- a
          lane exiting now IS a reclaim.
        * empty `swept` and NOT `ever_seen` -> `lanes` is left UNCHANGED
          (``None`` on the first such call). On a fleet's very first sweeps,
          "not yet provisioned" and "describe_instances failed everywhere"
          both present as an empty list from `fleet_rows`, with no way to
          tell them apart from here; treating either as "everything is gone"
          is exactly the defect this type exists to prevent.
        """
        if swept:
            self.lanes = set(swept)
            self.ever_seen = True
        elif self.ever_seen:
            self.lanes = set()
        # else: nothing has ever been seen and this sweep was also empty --
        # leave `lanes` as-is (unknown), per the docstring above.

    def present(self, key: str) -> bool:
        """Whether lane `key` should be treated as present right now.

        Keys off `ever_seen`, NOT merely ``lanes is None``: nothing has been
        CONFIRMED yet whenever ``ever_seen`` is ``False``, regardless of
        whatever placeholder `lanes` happens to hold, so that state is
        UNKNOWN and must default to present -- the same "unknown counts as
        present" rule the ``None`` case exists for (see `observe`'s
        docstring, third bullet). Only once `ever_seen` is ``True`` -- a real
        sweep has actually seen this fleet non-empty at least once -- does an
        empty `lanes` mean the fleet is genuinely gone, and only then is a
        lane's absence from `lanes` allowed to mean "not present".

        Returns
        -------
        bool
            ``True`` when `ever_seen` is ``False`` (preserves the historical
            first-tick behaviour, so an unchecked lane is never wrongly
            reclassified as reclaimed), or when `lanes` is ``None`` or `key`
            is in `lanes`; ``False`` otherwise.
        """
        if not self.ever_seen:
            return True
        return self.lanes is None or key in self.lanes


@dataclass
class _LaneRun:
    """Mutable per-lane runtime state, carried across monitor-loop ticks."""

    lane: Lane
    #: Ordered subprocess phases this invocation runs for this lane, e.g.
    #: ``("induction",)``, ``("deduction",)``, or ``("induction", "deduction")``.
    phases: tuple[str, ...]
    phase_index: int = 0
    proc: Optional[subprocess.Popen] = None
    #: Timestamp of the most recent (re)launch; reset by every relaunch.
    started_at: float = 0.0
    #: Timestamp of this lane's FIRST launch ONLY -- never reset by a
    #: relaunch. `_monitor_tick`'s 2x-budget alert keys on THIS, not
    #: `started_at`: an alert keyed on a value every relaunch resets could
    #: never fire for the one lane it exists to catch -- one being relaunched
    #: over and over (see `_start_phase`).
    lane_started_at: float = 0.0
    crash_relaunches: int = 0
    #: Reclaim relaunches so far this invocation; bounded by
    #: `MAX_RECLAIM_RELAUNCHES` (see that constant's comment for why a
    #: reclaim is no longer unlimited).
    reclaim_relaunches: int = 0
    #: `time.monotonic()` deadline for a pending backed-off reclaim relaunch;
    #: ``None`` means nothing is pending. Set by `_apply_restart_policy` on a
    #: reclaim verdict, cleared when that relaunch fires.
    pending_relaunch_at: Optional[float] = None
    cot_checked: bool = False
    #: Latches True once `_lane_gate_passed` has found the healthy-serve line
    #: for this lane; makes every later gate check an O(1) no-I/O return.
    gate_passed: bool = False
    #: Byte offset `_lane_gate_passed` has already scanned up to, so each
    #: call reads only newly appended bytes. Reset to 0 if the log file is
    #: ever found shorter than this (truncated/replaced).
    gate_scan_offset: int = 0
    halted: bool = False
    halt_reason: str = ""
    done: bool = False
    #: Non-empty when this lane's post-deduction S3 spool failed; surfaced in
    #: `_run_fleet`'s closing report. A spool failure does NOT halt the lane
    #: (its data is already collected; this is a reporting matter -- see
    #: `_advance_finished`).
    spool_error: str = ""

    @property
    def current_phase(self) -> Optional[str]:
        """The phase this lane runs now, or None once `phases` is exhausted."""
        if self.phase_index >= len(self.phases):
            return None
        return self.phases[self.phase_index]


def _phase_sequence(phase: str) -> tuple[str, ...]:
    """Map a ``--phase`` CLI value onto the ordered subprocess phases each lane runs.

    A lane's instance shuts down (`_advance_finished`) only once its LAST
    scheduled phase exits successfully AND that phase was ``"deduction"``, so an
    induction-only invocation never shuts its boxes down.

    Returns
    -------
    tuple[str, ...]
        ``("induction",)``, ``("deduction",)`` or ``("induction", "deduction")``.

    Raises
    ------
    ValueError
        For any other `phase`.
    """
    if phase == "induction":
        return ("induction",)
    if phase == "deduction":
        return ("deduction",)
    if phase == "both":
        return ("induction", "deduction")
    raise ValueError(f"run_fleet: unknown --phase {phase!r}; expected induction/deduction/both")


def _lane_gate_passed(run: _LaneRun, log_dir: Path) -> bool:
    """Check whether `run`'s log has ever produced a healthy-serve line.

    STICKY and INCREMENTAL -- deliberately NOT a plain `_tail_log` bounded
    read (finding 14-03): the healthy-serve line (`is_serve_healthy`) is a
    ONE-TIME event near the start of a lane's log, which scrolls out of any
    fixed byte window under gigabytes of later vLLM/CoT chatter, so a bounded
    tail would silently stop finding it. Instead:

    * once found, `run.gate_passed` latches ``True`` and every later call for
      this lane is an O(1) return with no file I/O at all;
    * until then, only the bytes APPENDED since `run.gate_scan_offset` are
      read and scanned, so total work across many calls is O(log size), not
      O(calls x log size);
    * the offset only ever advances over WHOLE lines: if the newly read
      chunk does not end in a newline (a write may be mid-flight), the scan
      trims back to the last complete newline and advances the offset only
      that far -- so a healthy-serve line split across two reads is not
      half-consumed on the first call and then missed (already past the
      offset) on the second;
    * if the log file is found SHORTER than `gate_scan_offset` (truncated or
      replaced under the same name), the offset resets to 0 and the scan
      restarts from the beginning, rather than seeking past EOF and reading
      nothing forever.
    """
    if run.gate_passed:
        return True

    path = log_dir / f"{run.lane.key}.log"
    try:
        size = path.stat().st_size
    except OSError:
        return False

    offset = run.gate_scan_offset
    if size < offset:
        offset = 0  # file shrank -- rescan from the start, see docstring

    try:
        with open(path, "rb") as f:
            f.seek(offset)
            chunk = f.read()
    except OSError:
        return False

    if not chunk:
        run.gate_scan_offset = offset
        return False

    consumed = len(chunk)
    if not chunk.endswith(b"\n"):
        last_newline = chunk.rfind(b"\n")
        if last_newline == -1:
            # No complete line yet at all; do not advance the offset -- the
            # next call re-reads this same (still-growing) partial line.
            run.gate_scan_offset = offset
            return False
        consumed = last_newline + 1
        chunk = chunk[:consumed]

    run.gate_scan_offset = offset + consumed
    text = chunk.decode("utf-8", errors="replace")
    if any(is_serve_healthy(line) for line in text.splitlines()):
        run.gate_passed = True
        return True
    return False


def _monitor_tick(
    runs: dict[str, _LaneRun], log_dir: Path, tick: int, presence: _Presence
) -> None:
    """Run one polling pass over every lane: refresh presence, print the table, alert.

    Parameters
    ----------
    tick : int
        1-based. The ``describe_instances`` sweep (read-only
        ``fleet_status.fleet_rows``) runs on tick 1 -- so the table has instance
        data immediately -- and every ``DESCRIBE_EVERY_N_TICKS``-th tick after.
    presence : _Presence
        Mutated in place. A sweep that RAISES is logged and skipped, leaving
        `presence` untouched -- the previous "could not check" behaviour. A
        sweep that RETURNS, even with an empty result, calls
        ``presence.observe`` and lets that type's own rules (see its
        docstring) decide whether an empty result means unknown or genuinely
        gone -- these are different cases: a failed sweep tells you nothing,
        while an empty but successful one is real information.
    """
    if tick == 1 or tick % DESCRIBE_EVERY_N_TICKS == 0:
        try:
            rows = _fleet_status_module().fleet_rows()
        except Exception as exc:  # noqa: BLE001 -- one bad sweep must not crash the monitor
            logging.warning(f"run_fleet: describe_instances sweep failed this tick: {exc}")
        else:
            presence.observe({row["lane"] for row in rows})

    print(f"\n=== fleet tick {tick} ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")
    for key in sorted(runs):
        run = runs[key]
        alive = run.proc is not None and run.proc.poll() is None
        status = "halted" if run.halted else ("done" if run.done else (run.current_phase or "?"))
        last_line = _tail_log(log_dir, key, n=1)
        print(f"{key:<28} status={status:<10} alive={str(alive):<5} last: {last_line[-120:]}")

        if run.proc is not None and not alive and not run.halted and not run.done:
            rc = run.proc.returncode
            if rc not in (0, None):
                print(f"ALERT [{key}]: process exited non-zero (rc={rc}).")

        if presence.lanes is not None and alive and key not in presence.lanes:
            print(f"ALERT [{key}]: subprocess is still running but its instance is "
                  "gone or shutting down.")

        if run.lane_started_at:
            # `lane_started_at`, NOT `started_at`: see `_LaneRun.lane_started_at`'s
            # docstring for why this alert must key on the lane's CUMULATIVE
            # age across relaunches, not the most recent launch's timestamp.
            age_hours = (time.monotonic() - run.lane_started_at) / 3600
            budget = 2 * run.lane.budget_hours
            if age_hours > budget:
                print(f"ALERT [{key}]: wall clock {age_hours:.1f}h exceeds 2x budget "
                      f"({budget}h).")


def _apply_restart_policy(runs: dict[str, _LaneRun], log_dir: Path, presence: _Presence) -> None:
    """Relaunch or halt every lane whose subprocess exited non-zero this tick.

    Enforces `classify_exit`'s verdict: a CRASH gets `MAX_CRASH_RELAUNCHES`
    immediate relaunches then a halt; a RECLAIM gets `MAX_RECLAIM_RELAUNCHES`
    BACKED-OFF relaunches (see that constant's comment for the schedule) then
    a halt too. Reclaims are no longer unlimited -- finding 14-02: an empty or
    failed describe sweep used to make every exit look like a reclaim, so an
    unbounded retry policy on that misclassification meant a lane could
    relaunch forever with no crash counting and no budget alert ever firing.

    A lane whose previous reclaim verdict is still waiting out its backoff
    (`pending_relaunch_at` in the future) is left alone this tick: neither
    relaunched early nor re-classified against a log tail that has not
    changed.
    """
    now = time.monotonic()
    for key, run in runs.items():
        if run.halted or run.done or run.proc is None:
            continue

        if run.pending_relaunch_at is not None:
            if now < run.pending_relaunch_at:
                continue  # still backing off; do not touch this lane this tick
            run.pending_relaunch_at = None
            _start_phase(run, log_dir)
            continue

        rc = run.proc.poll()
        if rc is None or rc == 0:
            continue  # still running, or a clean exit (handled by _advance_finished)

        tail = _tail_log(log_dir, key)
        verdict = classify_exit(tail, presence.present(key))
        if verdict == "reclaim":
            run.reclaim_relaunches += 1
            if run.reclaim_relaunches > MAX_RECLAIM_RELAUNCHES:
                run.halted = True
                run.halt_reason = (
                    f"reclaimed {run.reclaim_relaunches} time(s) (last rc={rc}); exceeded "
                    f"MAX_RECLAIM_RELAUNCHES={MAX_RECLAIM_RELAUNCHES}"
                )
                logging.error(f"run_fleet[{key}]: HALTED -- {run.halt_reason}")
            else:
                delay = min(
                    RECLAIM_BACKOFF_CAP_SECONDS,
                    RECLAIM_BACKOFF_BASE_SECONDS * 2 ** (run.reclaim_relaunches - 1),
                )
                run.pending_relaunch_at = now + delay
                logging.warning(
                    f"run_fleet[{key}]: exited rc={rc}, classified RECLAIM -- relaunch "
                    f"{run.reclaim_relaunches}/{MAX_RECLAIM_RELAUNCHES} in {delay:.0f}s."
                )
        else:
            run.crash_relaunches += 1
            if run.crash_relaunches > MAX_CRASH_RELAUNCHES:
                run.halted = True
                run.halt_reason = (
                    f"crashed {run.crash_relaunches} time(s) (last rc={rc}); exceeded "
                    f"MAX_CRASH_RELAUNCHES={MAX_CRASH_RELAUNCHES}"
                )
                logging.error(f"run_fleet[{key}]: HALTED -- {run.halt_reason}")
            else:
                logging.warning(
                    f"run_fleet[{key}]: exited rc={rc}, classified CRASH -- relaunch "
                    f"{run.crash_relaunches}/{MAX_CRASH_RELAUNCHES}."
                )
                _start_phase(run, log_dir)


def _check_cot(runs: dict[str, _LaneRun], store_factory: Callable[[], Any] = build_results_store) -> None:
    """Run the CoT-ON assertion once per lane; halt any lane below `COT_MIN_FRACTION`."""
    for key, run in runs.items():
        if run.cot_checked or run.halted or run.done or run.current_phase != "induction":
            continue
        try:
            store = store_factory()
            # intens ONLY: this is a WIRING check -- "did the thinking toggle
            # reach the model" -- and intens is the short, well-formed arm where
            # every wired model reasons. An all-arms pool would halt lanes that
            # collapse on the ~30k-token extens listing or confabulate on noise,
            # which is the phenomenon the study measures, not a fault.
            fraction = reasoning_fraction(
                store, run.lane.key, run.lane.tag, infos=("intens",)
            )
        except Exception as exc:  # noqa: BLE001 -- a store failure must not crash the monitor
            logging.warning(f"run_fleet[{key}]: reasoning_fraction check failed: {exc}")
            continue
        if fraction is None:
            continue  # nothing landed yet -- check again next tick
        run.cot_checked = True
        if fraction < COT_MIN_FRACTION:
            run.halted = True
            run.halt_reason = f"CoT-ON check failed: {fraction:.1%} < {COT_MIN_FRACTION:.0%}"
            if run.proc is not None and run.proc.poll() is None:
                run.proc.terminate()
            logging.error(
                "\n".join(
                    [
                        "=" * 72,
                        f"run_fleet[{key}]: HALTING LANE -- silently non-thinking data.",
                        f"  measured reasoning fraction : {fraction:.1%}",
                        f"  required minimum (COT_MIN_FRACTION): {COT_MIN_FRACTION:.0%}",
                        "  Below-threshold data is worse than no data -- this lane will "
                        "NOT be relaunched automatically.",
                        "=" * 72,
                    ]
                )
            )


def _advance_finished(runs: dict[str, _LaneRun], log_dir: Path) -> None:
    """Advance every cleanly exited lane to its next phase, or shut it down."""
    for key, run in runs.items():
        if run.halted or run.done or run.proc is None:
            continue
        if run.proc.poll() != 0:
            continue  # not a clean exit (still running, or handled by the restart policy)

        finished_phase = run.current_phase
        if finished_phase == "deduction":
            # `run_dir` is built from `REPO_ROOT` EXPLICITLY, not from the
            # driver's own `runner.results_root()`: that helper reads
            # `SMOLBENCH_LEAN_RESULTS` from whatever process calls it -- here,
            # THIS supervisor, whose environment is not the lane's.
            # `SMOLBENCH_LEAN_RESULTS` is not in `PASSTHROUGH_ENV`, so the lane
            # subprocess resolved the repo-root-anchored default; anchoring
            # here on `REPO_ROOT` reproduces exactly that, while
            # `results_root()` would instead follow a stray supervisor-side
            # export to a directory no lane ever wrote to.
            run_dir = (
                REPO_ROOT / "notebooks" / "deduction" / "results" / "runs" / f"scaling_{run.lane.key}"
            )
            try:
                # WHY spool again here, given the driver already spools before
                # it can exit 0 (`lane_command` passes no `--no-s3`): its own
                # prune leaves only `manifest.json`, so this is normally a
                # cheap re-upload of one file -- but it is the LAST thing
                # between "the lane process exited 0" and this supervisor
                # shutting that instance down under `--phase deduction`/`both`.
                # Going through the driver's OWN verified implementation
                # (upload, head_object ContentLength check, only then prune)
                # confirms the spool before destroying the box, rather than
                # trusting an already-exited process's own earlier attempt.
                #
                # `SystemExit` explicitly, alongside `Exception`: the
                # deduction driver's module-scope guard raises `SystemExit`
                # (not caught by a bare `except Exception`), and a failure
                # loading or running it here must not kill this supervisor.
                _deduction_driver().spool_to_s3(run_dir, run.lane.key)
            except (Exception, SystemExit) as exc:  # noqa: BLE001 -- see docstring above
                run.spool_error = f"{type(exc).__name__}: {exc}"
                logging.error(f"run_fleet[{key}]: spool sync failed: {run.spool_error}")

        run.phase_index += 1
        if run.current_phase is not None:
            _start_phase(run, log_dir)
            continue

        # No more scheduled phases. Shut down only if a deduction phase ran THIS
        # invocation: an induction-only run leaves the instance up on purpose
        # (see the module docstring's "Phases" bullet) for a later
        # `--phase deduction` invocation.
        if "deduction" in run.phases:
            logging.info(f"run_fleet[{key}]: all phases complete; shutting down its instance.")
            cmd = lane_command(run.lane, "shutdown")
            env = lane_env(run.lane, "shutdown")
            subprocess.run(cmd, env=env, check=False)
        run.done = True


def _all_terminal(runs: dict[str, _LaneRun]) -> bool:
    """Check whether every lane has halted or fully finished its phase sequence."""
    return all(run.halted or run.done for run in runs.values())


def _run_fleet(
    lanes: dict[str, Lane], phase_sequence: tuple[str, ...], *, gate: bool, log_dir: Path, phase_name: str
) -> None:
    """Launch and supervise every lane in `lanes` to completion or halt.

    Tier D, then tier A, staggered. Then, unless `gate` is False or no
    ``GATE_MODELS`` lane is selected, a blocking wait for every gate lane to
    report a healthy serve -- that wait runs full monitor ticks, so a gate
    lane's crash is still retried or halted promptly. Then tiers B and C, and a
    monitor loop until every lane is halted or done.
    """
    runs = {key: _LaneRun(lane=lane, phases=phase_sequence) for key, lane in lanes.items()}

    tier_d = [k for k in lanes if lanes[k].tier == "D"]
    tier_a = [k for k in lanes if lanes[k].tier == "A"]
    tier_bc = [k for k in lanes if lanes[k].tier in ("B", "C")]

    _launch_batch(runs, tier_d, log_dir)
    _launch_batch(runs, tier_a, log_dir)

    presence = _Presence()
    tick = 0

    gate_keys = [k for k in GATE_MODELS if k in runs] if gate else []
    while gate_keys and not all(_lane_gate_passed(runs[k], log_dir) for k in gate_keys):
        tick += 1
        time.sleep(MONITOR_INTERVAL_SECONDS)
        _monitor_tick(runs, log_dir, tick, presence)
        _apply_restart_policy(runs, log_dir, presence)
        _check_cot(runs)
        _advance_finished(runs, log_dir)
        if all(runs[k].halted for k in gate_keys):
            logging.error(
                "run_fleet: FAMILY GATE FAILED -- every GATE_MODELS lane halted; NOT "
                "launching tiers B/C. Investigate FLEET_IMAGE before retrying."
            )
            # Finding 14-03: these tier B/C lanes were never launched (proc is
            # still None), so without marking them HALTED here they sit
            # forever with halted=False, done=False -- `_all_terminal` never
            # returns True, both policy loops `continue` on `proc is None`,
            # and the supervisor spins with the tier-D boxes still up,
            # printing ticks forever and never reaching the closing report or
            # the teardown reminder below. HALT, not `done`: these lanes
            # produced no data and the operator must see them in the closing
            # summary, not have them silently disappear from it.
            for bc_key in tier_bc:
                runs[bc_key].halted = True
                runs[bc_key].halt_reason = (
                    "never launched: family gate failed (every GATE_MODELS lane halted)"
                )
            gate_keys = []  # stop waiting; skip the else-clause launch below
            break
    else:
        logging.info("run_fleet: family gate passed (or was skipped) -- launching tiers B and C.")
        _launch_batch(runs, tier_bc, log_dir)

    while not _all_terminal(runs):
        tick += 1
        time.sleep(MONITOR_INTERVAL_SECONDS)
        _monitor_tick(runs, log_dir, tick, presence)
        _apply_restart_policy(runs, log_dir, presence)
        _check_cot(runs)
        _advance_finished(runs, log_dir)

    halted = {key: run.halt_reason for key, run in runs.items() if run.halted}
    if halted:
        logging.error(f"run_fleet: fleet finished with {len(halted)} halted lane(s): {halted}")
    # Printed unconditionally -- even when no lane halted -- because a spool
    # failure (finding 14-11) does not halt a lane; it is the only place this
    # would otherwise surface.
    spool_errors = {key: run.spool_error for key, run in runs.items() if run.spool_error}
    if spool_errors:
        logging.error(
            f"run_fleet: {len(spool_errors)} lane(s) had a post-deduction spool failure "
            f"(data is collected locally, NOT confirmed in S3): {spool_errors}"
        )
    if phase_name == "induction":
        print(
            "\nrun_fleet: induction-only run complete. Boxes are left RUNNING on purpose "
            "(the deduction phase may reuse them) -- run "
            "`scripts/fleet/fleet_teardown.py --terminate` when you are done with them."
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="21-lane EC2 fleet supervisor for the family-ladder scaling study."
    )
    parser.add_argument(
        "--phase", choices=("induction", "deduction", "both"), default="induction",
        help="Which subprocess phase(s) each lane runs this invocation (default: induction).",
    )
    parser.add_argument(
        "--lanes", default="",
        help="Comma-separated spec keys to run (default: all 21 lanes in LANES).",
    )
    parser.add_argument(
        "--no-gate", action="store_true",
        help="Skip the family gate: launch tiers B/C immediately after tiers D/A.",
    )
    parser.add_argument(
        "--log-dir", default=None,
        help=f"Directory for per-lane log files (default: {LOG_DIR}).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the launch plan (tier, command, full environment per lane) "
        "and exit. Launches no subprocess and makes no AWS call. Does NOT run "
        "preflight (tokenizer warm-up + completion-budget derivation) or check "
        "that FLEET_IMAGE resolves -- those steps only run on a live launch. "
        "This proves the wiring is correct, not that the lanes will actually "
        "start.",
    )
    return parser


def _selected_lanes(raw: str) -> dict[str, Lane]:
    """Resolve ``--lanes`` into a ``{key: Lane}`` map, in ``LANES`` declaration order.

    Raises ``SystemExit`` if `raw` names a key that is not in `LANES`.
    """
    if not raw.strip():
        return dict(LANES)
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    unknown = [k for k in keys if k not in LANES]
    if unknown:
        raise SystemExit(f"run_fleet: unknown --lanes key(s) {unknown}; choose from {sorted(LANES)}")
    chosen = set(keys)
    return {k: LANES[k] for k in LANES if k in chosen}


#: Printed verbatim under the DRY RUN header, worded for the OPERATOR: one who
#: reads a clean `--dry-run` as "the launch will work" would otherwise meet a
#: tokenizer-fetch failure or a budget-floor `SystemExit` only on the live run,
#: which is what `preflight()` exists to surface EARLIER.
_DRY_RUN_NOTICE = (
    "NOTE: this is a WIRING preview only. It did NOT run preflight (per-lane\n"
    "HuggingFace tokenizer warm-up + completion-budget derivation) and did NOT\n"
    "check that the digest-pinned FLEET_IMAGE resolves -- both do real\n"
    "network I/O (HuggingFace, Docker Hub) and only run on the live path\n"
    "(drop --dry-run). A clean plan below means the commands and per-lane\n"
    "environment are correct; it does NOT mean the lanes will actually start --\n"
    "a tokenizer fetch failure or a too-small completion budget can still\n"
    "surface for the first time on the live launch.\n"
)


def _print_dry_run_plan(lanes: dict[str, Lane], phase_name: str) -> None:
    """Print, per lane, its tier, every scheduled phase's command, and full env.

    Prints `_DRY_RUN_NOTICE` under the header: this preview never calls
    `preflight`/`fleet_image_digest` (both do real network I/O).
    """
    phases = _phase_sequence(phase_name)
    print(f"run_fleet DRY RUN -- phase={phase_name!r}, {len(lanes)} lane(s) selected\n")
    print(_DRY_RUN_NOTICE)
    for key, lane in lanes.items():
        print(f"=== {key} (tier {lane.tier}, budget {lane.budget_hours}h) ===")
        for phase in phases:
            print(f"  [{phase}] command: {' '.join(lane_command(lane, phase))}")
            print(f"  [{phase}] env:")
            for env_key, env_val in sorted(lane_env(lane, phase).items()):
                print(f"        {env_key}={env_val}")
        if "deduction" in phases:
            print(
                f"  [shutdown] command (after a successful deduction exit): "
                f"{' '.join(lane_command(lane, 'shutdown'))}"
            )
        print()


def main(argv: Optional[list[str]] = None) -> int:
    """Parse args, then print the dry-run plan or launch the fleet live.

    Returns
    -------
    int
        ``0`` after a dry run, or once the live fleet is all-terminal --
        individual lanes may still be halted; see the printed summary.
    """
    args = _build_arg_parser().parse_args(argv)
    lanes = _selected_lanes(args.lanes)

    if args.dry_run:
        _print_dry_run_plan(lanes, args.phase)
        return 0

    log_dir = Path(args.log_dir).resolve() if args.log_dir else LOG_DIR

    preflight(list(lanes.values()))
    digest = fleet_image_digest()
    logging.info(f"run_fleet: launching against {FLEET_IMAGE} (digest={digest or 'unknown'}).")

    _run_fleet(
        lanes,
        _phase_sequence(args.phase),
        gate=not args.no_gate,
        log_dir=log_dir,
        phase_name=args.phase,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
