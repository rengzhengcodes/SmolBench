"""The study's roster tables, and ONE lane's environment and argv.

This module answers exactly one question -- "what does lane ``<key>`` look
like?" -- and never "what is the fleet doing right now?". It owns the roster
(`TIER_MEMBERS`, `LANES`, and the per-tier instance-type, region, budget and
GPU-pin tables it is projected through), the digest-pinned `FLEET_IMAGE` and
its per-lane overrides, and the two functions that turn a `Lane` into a
subprocess: `lane_env` (that lane's complete, allowlisted child environment)
and `lane_command` (its argv).

It deliberately does NOT own the live supervision loop -- launching,
monitoring, the restart policy, the family gate, the CoT-ON check and the S3
spool are all ``scripts/fleet/supervisor.py``'s -- nor the command line, which
is all ``scripts/fleet/run_fleet.py`` has left.

None of the FUNCTIONS here launches a subprocess, makes an AWS call or
mutates ``os.environ`` -- `lane_env` in particular always returns a fresh
``dict`` (see its Notes). That is what makes ``run_fleet.py --dry-run`` a
genuinely offline preview of the real wiring, and lets
``tests/tooling/test_run_fleet.py`` pin every lane's whole environment with no
network at all. IMPORTING this module is the deliberate exception: the driver
load below runs ``load_dotenv(notebooks/induction/keys.env)``, which is how
the operator's AWS, results-store and model-cache variables reach this process
in the first place -- see that block's comment.

The IMPORT-TIME ORDERING below is load-bearing rather than tidiness, and each
block carries the comment explaining its own position: ``_config`` first, then
the by-path `run_study` load (which runs ``load_dotenv`` and so fills this
process's environment), and only THEN ``smolbench.evals.providers.ec2``, which
freezes its ``EC2_*`` module constants against the environment at ITS import
time. `_drift_guard` likewise runs before `LANES` is built, so the roster
lookup that builds it is already certified total.

It is loaded BY FILE PATH, never a bare ``import lane_env``: ``scripts/fleet``
has no ``__init__.py`` -- it is not a package -- so a bare import name is
absent from ``sys.path`` for a script launched from an arbitrary working
directory. See ``_config.load_fleet_module``, the loader every fleet consumer
now calls. ``run_fleet.py`` and ``supervisor.py`` both reach this module
through it, so they share ONE module object: one roster per process, not a
copy each.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

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
# loaded under a private name by `_config.load_fleet_module`, from
# `run_fleet.py` and `supervisor.py`), so a bare import name would be
# ambiguous at best and simply absent from `sys.path` at worst -- see
# `_config.py`'s own module docstring for the fuller argument. Cached under
# the shared `_CONFIG_MODULE_NAME` key in `sys.modules`: if `fleet_status.py`
# (loaded lazily by `supervisor._fleet_status_module`, by the identical
# pattern) has already loaded `_config.py` this process, this is a cache hit,
# not a second, independent module object.
#
# Bootstrapped BY HAND rather than through `_config.load_fleet_module`, and
# FIRST, before anything below: that loader is a function on the very module
# being loaded here, so it cannot load `_config` itself -- and every block
# after this one needs `_config` to already exist.
_config = _load_fleet_config()

# Configured HERE, immediately before the driver load below, not in
# `run_fleet.py`: `run_study.py` logs at its own module scope, and the first
# `logging` call in a process is what fixes the root handler, so a
# `basicConfig` that ran after the driver load would silently lose to it.
# This is the position the call held in `run_fleet.py` before the split.
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
        """Expected wall-clock hours for this tier; ``supervisor._monitor_tick`` alerts past 2x."""
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
        ``supervisor._advance_finished`` builds the same ``scaling_<key>`` run
        directory name from, to hand to that driver's own ``spool_to_s3``.

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
