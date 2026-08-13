"""21-lane EC2 fleet supervisor for the family-ladder scaling study.

``notebooks/induction/run_study.py`` (see its own module docstring, "ONE
MODEL PER BOX, driven by a fleet") is written to be launched 21 different
ways -- once per checkpoint -- with ``INDUCTION_MODELS`` pinned to a single
spec key and ``INDUCTION_STATE_FILE`` pinned to a lane-private EC2 state
file. THIS file is the thing that does the launching: it owns the roster
(mapped onto four cost/capacity TIERS, A through D), the per-lane
environment, subprocess lifecycle (launch, log, monitor, restart, halt), the
optional deduction phase on the SAME reused box, and the final S3 spool sync
+ shutdown.

Why tiers
---------
21 spot instances is not 21 identical bids: a ``g6e.4xlarge`` (single L40S)
and a ``p5e.48xlarge`` (8x H200) have wildly different capacity, cost, and
provisioning-tail characteristics. Grouping the roster into four tiers
(``TIER_MEMBERS``) lets this file launch cheap/fast lanes first, hold the
expensive/scarce ones behind a gate (see below), and apply a
capacity-appropriate wall-clock budget (``TIER_BUDGET_HOURS``) per lane
without hand-tuning 21 separate numbers.

Launch order and the family gate
---------------------------------
1. Tier D (longest provisioning tail, scarcest capacity: p5e/p5en) launches
   first, staggered ``LAUNCH_STAGGER_SECONDS`` apart.
2. Tier A (cheapest, fastest to prove out) launches next, staggered.
3. FAMILY GATE (skippable via ``--no-gate``): tiers B and C are held until
   EVERY model in ``GATE_MODELS`` -- three tier-A checkpoints, one per
   *reasoning-toggle style* in the roster -- has logged a healthy serve
   (``is_serve_healthy``). The whole roster serves under
   ``EC2_VLLM_IMAGE=vllm/vllm-openai:nightly`` (no tagged release supports
   these 2026 architectures yet -- see ``ec2.py``'s deploy-spec roster
   comment), an unproven moving target. Gating converts a 21-way bet on that
   image into a cheap 3-way bet on single-GPU boxes: if ``gemma-4-e2b``
   cannot serve, ``gemma-4-31b`` will not either, and finding that out on a
   g6e.4xlarge is a rounding error next to finding it out on six freshly
   provisioned p5e.48xlarge instances.
4. Tiers B and C launch, staggered.

Restart policy
---------------
Every lane's exit is classified by :func:`classify_exit` into ``"reclaim"``
(the box is just gone -- a spot interruption or a capacity-hunt failure) or
``"crash"`` (the process itself failed on a live box). Reclaims get
UNLIMITED retries (there is no reason to give up on a study lane because AWS
reclaimed a spot instance); crashes get ``MAX_CRASH_RELAUNCHES`` (2) retries
and then the lane HALTS while the rest of the fleet keeps running --
distinguishing the two matters because getting the classifier backwards
either abandons a lane on a routine interruption or burns money relaunching
a lane that will always crash the same way.

CoT-ON assertion
-----------------
Every checkpoint in this study is served with reasoning/thinking mode ON
(see ``run_study.COT_ARGS``); :func:`reasoning_fraction` measures, directly
from ``Mark.reasoning``, what fraction of a lane's first landed replicate
actually reasoned. Below ``COT_MIN_FRACTION`` (90%) the lane is HALTED
loudly rather than left to quietly fill 30 replicates of non-reasoning
output -- silently bad data is worse than no data, because nothing else in
this pipeline can tell the two apart after the fact.

Phases and the reuse-then-shutdown lifecycle
----------------------------------------------
``--phase induction`` (the default) runs ONLY the induction driver per lane
and, on the normal path, never shuts the box down -- a later
``--phase deduction`` invocation may reattach to the SAME instance (same
``EC2_EXPERIMENT_TAG``, same state file; see :func:`lane_env`). ``--phase
deduction`` runs ONLY the deduction driver, then -- on a successful exit --
spools its results to S3 (:func:`sync_deduction_spool`) and shuts the
instance down. ``--phase both`` chains induction then deduction on one lane
and shuts down after deduction's spool sync. Under ``--phase induction``
alone, this script prints an explicit reminder that
``scripts/fleet_teardown.py --terminate`` is how the boxes get reclaimed --
there is no automatic teardown to rely on.

Cost warning
------------
Launching the full, ungated roster provisions up to 21 DISTINCT EC2 spot
instances concurrently, spanning single-GPU ``g6e.4xlarge`` up to 8xH200
``p5e.48xlarge`` boxes, each billing for the duration it is up. ``--lanes``
and ``--dry-run`` exist specifically so a launch can be rehearsed (plan,
command, full per-lane environment -- no subprocess, no AWS call) before it
is real. ``--dry-run`` proves the lane WIRING is correct; it does NOT prove
the lanes will actually START -- it deliberately skips `preflight` (the
per-lane HuggingFace tokenizer warm-up and completion-budget derivation) and
the nightly-image digest lookup, both of which do real network I/O and only
run on the live path (see :func:`_print_dry_run_plan`, which prints this
same caveat to the operator).

Run (repo root, main venv)::

    .venv/bin/python scripts/run_fleet.py --dry-run
    .venv/bin/python scripts/run_fleet.py --phase induction
    .venv/bin/python scripts/run_fleet.py --phase deduction --lanes glm-4.7
"""

from __future__ import annotations

import argparse
import functools
import importlib.util
import json
import logging
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from smolbench.evals.results_store import ReplicateAddress, resolve_store

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Anchoring + the induction driver import
# ---------------------------------------------------------------------------
REPO_ROOT: Path = Path(__file__).resolve().parents[1]
VENV_PYTHON: Path = REPO_ROOT / ".venv" / "bin" / "python"

# Loaded by FILE PATH (never `sys.path` + a bare `import run_study`): the
# deduction study ships its OWN `notebooks/deduction/run_study.py`, so a bare
# module name would be ambiguous the moment both trees are on `sys.path` at
# once. `run_study.MODELS` (spec key -> analysis tag) is the single source
# of truth for this study's roster -- LANES below is built FROM it, never a
# re-declaration of it.
#
# Importing this file runs `load_dotenv(notebooks/induction/keys.env)` as a
# side effect (see that module's own docstring) -- DESIRED here: it is how
# AWS profile / results-store / model-cache environment variables reach THIS
# process, so `lane_env` below can pass them through to every lane.
_RUN_STUDY_PATH = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
_run_study_spec = importlib.util.spec_from_file_location("induction_run_study", _RUN_STUDY_PATH)
run_study = importlib.util.module_from_spec(_run_study_spec)
sys.modules[_run_study_spec.name] = run_study
_run_study_spec.loader.exec_module(run_study)

# `run_study`'s own import of `smolbench.induction.experiment` already pulled
# in `smolbench.evals.ec2` (AFTER `load_dotenv` ran -- see the import-order
# note in `run_study`'s docstring), so this is a `sys.modules` cache hit, not
# a second, differently-timed import of `ec2.py`.
from smolbench.evals.ec2 import EC2_DEPLOY_SPECS  # noqa: E402

# ---------------------------------------------------------------------------
# Constants (exact names/values -- pinned by tests/test_run_fleet.py)
# ---------------------------------------------------------------------------
DEFAULT_REGIONS = "us-east-1,us-east-2,us-west-2"
NIGHTLY_IMAGE = "vllm/vllm-openai:nightly"
# Per-lane image pins (default: NIGHTLY_IMAGE). The V4 lanes run the tagged
# v0.27.1 release: it is the version whose SM90 serving path (Marlin MXFP4 +
# FLASHMLA_SPARSE_DSV4, see the DeepSeek block in EC2_DEPLOY_SPECS) was
# source-verified and issue-proven (vllm#51822 on 4xH200), while nightly
# drifts daily.
LANE_IMAGE_OVERRIDES = {
    "deepseek-v4-flash": "vllm/vllm-openai:v0.27.1-cu129-ubuntu2404",
    "deepseek-v4-pro": "vllm/vllm-openai:v0.27.1-cu129-ubuntu2404",
}
MAX_LIFETIME_MIN = "2160"  # 36h absolute backstop, as a string (env value)
REQUEST_TIMEOUT_SECONDS = "3600"  # long CoT generations, as a string (env value)
# deepseek-v4-pro serves --enforce-eager (see EC2_DEPLOY_SPECS): a budget-
# burning 87k-token generation takes >1h at eager Pro throughput, so under
# the fleet-wide 3600s timeout those cells retry forever (observed at
# attempt 7 on seed 0). 7500s still lost races on the slowest tail cells
# (attempts 2-4 observed at 27/36 on seed 0, each failed attempt burning a
# full ~2h regeneration); 14400s lets a worst-case cell finish in ONE
# attempt. The box-side idle watchdog keys on vLLM metrics activity, so an
# hours-long in-flight generation cannot trip it.
LANE_REQUEST_TIMEOUT_OVERRIDES = {"deepseek-v4-pro": "14400"}

TIER_INSTANCE_TYPES = {
    # g6e.12xlarge appended 2026-08-11: small-G spot in the hunt AZs was
    # reclaimed for hours on end while 12xl capacity (and the raised G quota)
    # sat available -- a 3x-cost fallback beats an idle lane.
    "A": "g6e.4xlarge,g6e.8xlarge,g6e.12xlarge",
    "B": "g6e.12xlarge,g6e.24xlarge",
    "C": "p5.48xlarge,p5e.48xlarge",
    # D switched to p6-b200 (8x B200, SM100) 2026-08-13 for the deepseek-v4-pro
    # experiment: SM90 graph capture IMA'd twice and eager can't finish 30
    # seeds, so Pro's spec dropped its Marlin pin for SM100's native MXFP4
    # path -- and that marlin-less spec MUST NOT serve on p5e/p5en (see the
    # spec comment in ec2.py). glm-4.7 / deepseek-v3.1, the other D lanes,
    # completed on the old p5e/p5en list and never relaunch.
    "D": "p6-b200.48xlarge",
}
# Override for tier D only; every other tier falls back to DEFAULT_REGIONS.
# All 3 study regions stay in the hunt for p6-b200 -- unlike p5e (which
# exists only in us-east-2/us-west-2), B200 placement is still shifting, so
# excluding a region risks starving the experiment.
TIER_REGIONS = {"D": "us-east-1,us-east-2,us-west-2"}
TIER_BUDGET_HOURS = {"A": 9, "B": 9, "C": 10, "D": 14}

TIER_MEMBERS = {
    # gemma-4-12b moved A->B 2026-08-12: its spec is tp=4 (tp=1 on a 4-GPU
    # box wedged every request past the 1h read timeout), and tier A's hunt
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
        "glm-4.5-air", "k-exaone-236b-a23b", "deepseek-v4-flash",
    ),
    "D": ("glm-4.7", "deepseek-v3.1", "deepseek-v4-pro"),
}

GATE_MODELS = ("gemma-4-e2b", "nemotron-3-nano-4b", "ministral-3-3b")
MAX_CRASH_RELAUNCHES = 2
# 0.9 -> 0.5 (2026-08-11, live): with only 9 intens marks, one or two direct
# answers from a capable model read as 78-89% and tripped the halt. A DEAD
# toggle measures ~0-11% (bare integers everywhere); a working-but-variable
# soft protocol measures 78-100%. 0.5 cleanly separates the regimes.
COT_MIN_FRACTION = 0.5
#: A response longer than this counts as a reasoning chain carried in content
#: (the quiz contract asks for a single bare integer; see
#: ``reasoning_fraction``'s Notes for the live incident this encodes).
COT_CONTENT_REASONING_MIN_CHARS = 200
LAUNCH_STAGGER_SECONDS = 30
MONITOR_INTERVAL_SECONDS = 60
DESCRIBE_EVERY_N_TICKS = 5


# ---------------------------------------------------------------------------
# Lane / LANES
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Lane:
    """One study checkpoint's fleet identity: which spec, tag, and tier.

    Everything else a lane needs (instance types, regions, its EC2
    experiment tag, its state-file name, its wall-clock budget) is DERIVED
    from these three fields via the read-only properties below, rather than
    stored redundantly -- so e.g. editing ``TIER_INSTANCE_TYPES["C"]``
    changes every tier-C lane's plan with no risk of a stale per-lane copy.

    Parameters
    ----------
    key : str
        Spec key -- an ``EC2_DEPLOY_SPECS`` / ``run_study.MODELS`` key, and
        also vLLM's ``--served-model-name``.
    tag : str
        Short analysis tag (``run_study.MODELS[key]``), used in result
        directory names and figure legends.
    tier : str
        One of ``"A"``, ``"B"``, ``"C"``, ``"D"`` -- a key of
        ``TIER_INSTANCE_TYPES`` / ``TIER_BUDGET_HOURS``.
    """

    key: str
    tag: str
    tier: str

    @property
    def instance_types(self) -> str:
        """Comma-separated EC2 instance-type capacity-hunt order for this lane's tier."""
        return TIER_INSTANCE_TYPES[self.tier]

    @property
    def regions(self) -> str:
        """Comma-separated AWS regions this lane may provision in.

        ``TIER_REGIONS`` overrides for tier D (p5e-only capacity); every
        other tier uses ``DEFAULT_REGIONS``.
        """
        return TIER_REGIONS.get(self.tier, DEFAULT_REGIONS)

    @property
    def experiment_tag(self) -> str:
        """This lane's ``smolbench:experiment`` tag value: ``f"scaling-{key}"``."""
        return f"scaling-{self.key}"

    @property
    def state_file(self) -> str:
        """This lane's private EC2 state-file basename (repo-root-anchored by the driver)."""
        return f".ec2_state_scaling_{self.key}.json"

    @property
    def budget_hours(self) -> int:
        """This lane's expected wall-clock budget, from ``TIER_BUDGET_HOURS``."""
        return TIER_BUDGET_HOURS[self.tier]


def _drift_guard() -> None:
    """Verifies ``TIER_MEMBERS`` agrees with both external sources of truth.

    Raises
    ------
    SystemExit
        Explicit ``raise``, not a bare ``assert`` -- an ``assert`` is
        stripped under ``python -O``, and a roster drift is exactly the kind
        of mistake that must fail loudly in EVERY invocation mode, not only
        when the interpreter happens to be running unoptimized. Two
        conditions are checked, either of which raises, naming the
        symmetric difference so the fix is obvious without re-deriving the
        three sets by hand:

        - The four tiers are NOT pairwise disjoint (a spec key listed twice).
        - ``set(TIER_MEMBERS values)`` does not equal EXACTLY
          ``set(run_study.MODELS)`` and EXACTLY
          ``set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"}``.

    Notes
    -----
    WHY this matters: ``EC2_DEPLOY_SPECS`` and ``run_study.MODELS`` are each,
    independently, someone else's single source of truth (deploy facts and
    study config respectively) -- but ``TIER_MEMBERS`` above is a
    HAND-WRITTEN table that has to agree with both. A rung added to
    ``EC2_DEPLOY_SPECS``/``MODELS`` but forgotten here would silently never
    run: the study would quietly ship 20 of 21 ladders with no error
    anywhere, discovered only much later at analysis time when a family's
    curve is missing a point. Running this at IMPORT time (rather than only
    inside ``main()``) means even a ``--dry-run`` or a bare
    ``import run_fleet`` catches the drift immediately.
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

    study_keys = set(run_study.MODELS)
    spec_keys = set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"}
    problems = []
    if flat_set != study_keys:
        problems.append(
            f"TIER_MEMBERS vs run_study.MODELS differ by "
            f"{sorted(flat_set.symmetric_difference(study_keys))}"
        )
    if flat_set != spec_keys:
        problems.append(
            "TIER_MEMBERS vs EC2_DEPLOY_SPECS (minus qwen2.5-1.5b) differ by "
            f"{sorted(flat_set.symmetric_difference(spec_keys))}"
        )
    if problems:
        raise SystemExit(
            "run_fleet: lane roster drift detected -- " + "; ".join(problems) + ". "
            "A rung added to (or removed from) EC2_DEPLOY_SPECS/run_study.MODELS "
            "without a matching edit to TIER_MEMBERS in this file would silently "
            "never run, shipping 20 of 21 ladders with no error. Fix TIER_MEMBERS."
        )


_drift_guard()

#: Spec key -> Lane, for every model this study runs. Built directly from
#: TIER_MEMBERS x run_study.MODELS -- see _drift_guard for why this is safe
#: to build unconditionally once the guard above has passed.
LANES: dict[str, Lane] = {
    key: Lane(key=key, tag=run_study.MODELS[key], tier=tier)
    for tier, keys in TIER_MEMBERS.items()
    for key in keys
}


# ---------------------------------------------------------------------------
# Per-lane environment
# ---------------------------------------------------------------------------
# Explicit ALLOWLIST, not `dict(os.environ)` plus overrides. `run_study`'s
# own import (above) already froze THIS process's `smolbench.evals.ec2`
# constants from `keys.env` -- meaning `os.environ` here can carry this
# study's OWN `EC2_EXPERIMENT_TAG`/`EC2_INSTANCE_TYPES`/... (a sibling
# study's values, or leftovers from a previous manual run in this shell).
# Copying the whole environment would let those leak into every lane and
# silently override the per-lane config `lane_env` builds below -- an
# allowlist makes that structurally impossible: nothing not named here ever
# crosses into a lane's environment.
PASSTHROUGH_ENV: tuple[str, ...] = (
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR",
    "AWS_PROFILE", "AWS_REGION", "AWS_DEFAULT_REGION",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
    "AWS_SHARED_CREDENTIALS_FILE", "AWS_CONFIG_FILE",
    "HF_TOKEN",
    "SMOLBENCH_RESULTS_S3", "SMOLBENCH_RESULTS_S3_REGION",
    "EC2_S3_MODEL_CACHE", "EC2_S3_CACHE_REGION",
)


def lane_env(
    lane: Lane, phase: str, base_env: Optional[Mapping[str, str]] = None
) -> dict[str, str]:
    """Materialises one lane's complete subprocess environment.

    A PURE function -- it never mutates `base_env` or ``os.environ``, and
    always returns a brand-new ``dict`` -- deliberately, NOT for style: with
    up to 21 lanes launched from one parent process, mutating ``os.environ``
    (the "obvious" implementation) would make lane N+1 inherit lane N's
    ``EC2_EXPERIMENT_TAG``/``INDUCTION_STATE_FILE`` unless every single key
    this function sets were also explicitly popped afterward -- one missed
    key and two lanes reattach to ONE EC2 instance, each swapping the served
    checkpoint out from under the other mid-run. Returning a fresh mapping
    per call makes that failure mode structurally impossible: nothing this
    function does can be observed by any other call to it.

    Parameters
    ----------
    lane : Lane
        The lane to build an environment for.
    phase : str
        One of ``"induction"``, ``"deduction"``, ``"shutdown"``. Only
        ``"deduction"`` adds the ``LEAN_*`` variables (see Returns).
    base_env : Mapping[str, str] or None, optional
        The environment to read ``PASSTHROUGH_ENV`` values from. ``None``
        (the default) reads ``os.environ`` -- passing an explicit mapping
        (as the test suite does) keeps this function testable without
        touching the real process environment at all.

    Returns
    -------
    dict[str, str]
        A NEW ``dict`` containing:

        - Every key of ``PASSTHROUGH_ENV`` present in `base_env`, verbatim
          (a key `base_env` lacks is simply absent from the result -- no
          invented defaults).
        - Unconditionally: ``INFERENCE_PROVIDER``, ``EC2_EXPERIMENT_TAG``,
          ``INDUCTION_STATE_FILE``, ``INDUCTION_MODELS``,
          ``EC2_INSTANCE_TYPES``, ``EC2_REGIONS``, ``EC2_VLLM_IMAGE``,
          ``EC2_MAX_LIFETIME_MIN``, ``EC2_REQUEST_TIMEOUT_SECONDS``.
        - When `phase` is ``"deduction"`` only: ``LEAN_MODEL``,
          ``LEAN_STATE_FILE`` (the SAME value as ``INDUCTION_STATE_FILE`` --
          the reattach contract: the deduction driver reattaches to the box
          the induction phase already provisioned, rather than provisioning
          a second one), and ``LEAN_RUN_NAME``.

        For `phase` ``"induction"`` or ``"shutdown"``, no key starting with
        ``LEAN_`` is present. Every value is a plain ``str``.

    Notes
    -----
    ``notebooks/deduction/run_study.py`` does not exist yet as of this
    writing; its CLI contract was handed down as ``LEAN_MODEL`` +
    ``LEAN_STATE_FILE`` alone. ``LEAN_RUN_NAME`` is added on top of that
    contract because :func:`sync_deduction_spool` (below) reads results from
    ``notebooks/deduction/results/runs/scaling_<key>/``, and
    ``smolbench.deduction.lean.figures`` already documents run directories
    as ``scaling_<model>`` under ``<results_root>/runs/`` (see that module's
    header comment, "directories are named `scaling_<model>`"). This is
    therefore an INFERRED variable: harmless if the eventual driver ignores
    it (nothing else in this environment depends on it), and LOAD-BEARING --
    the only thing that makes the spool sync find the right directory -- if
    the driver honors it.
    """
    if base_env is None:
        import os

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
            "EC2_VLLM_IMAGE": LANE_IMAGE_OVERRIDES.get(lane.key, NIGHTLY_IMAGE),
            "EC2_MAX_LIFETIME_MIN": MAX_LIFETIME_MIN,
            "EC2_REQUEST_TIMEOUT_SECONDS": LANE_REQUEST_TIMEOUT_OVERRIDES.get(
                lane.key, REQUEST_TIMEOUT_SECONDS
            ),
        }
    )
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
# The `-c` snippet run for the "shutdown" phase. `EC2_STATE_FILE` is read at
# CALL time by `ec2._state_path()` (see that module's "Env-read timing"
# docstring section), so this snippet must set it explicitly from the
# already-repo-root-anchored `INDUCTION_STATE_FILE` lane_env provides --
# mirroring exactly what `InductionExperiment._apply_env` does
# (`os.environ["EC2_STATE_FILE"] = str(repo_root() / self.state_file)`)
# rather than relying on `ec2.py`'s own bare-filename default, which would
# resolve relative to the subprocess's cwd instead of the repo root.
_SHUTDOWN_SNIPPET = (
    "import os; "
    "from smolbench.evals.results_store import repo_root; "
    "os.environ['EC2_STATE_FILE'] = str(repo_root() / os.environ['INDUCTION_STATE_FILE']); "
    "from smolbench.evals.ec2 import shutdown_instance; "
    "shutdown_instance()"
)


def lane_command(lane: Lane, phase: str) -> list[str]:
    """Builds the subprocess argv for one lane's phase.

    Parameters
    ----------
    lane : Lane
        The lane to build a command for.
    phase : str
        One of ``"induction"``, ``"deduction"``, ``"shutdown"``.

    Returns
    -------
    list[str]
        - ``"induction"``: ``[VENV_PYTHON, notebooks/induction/run_study.py]``.
        - ``"deduction"``: ``[VENV_PYTHON, notebooks/deduction/run_study.py]``.
        - ``"shutdown"``: ``[VENV_PYTHON, "-c", <snippet>]``, where the
          snippet imports ``smolbench.evals.ec2`` and calls
          ``shutdown_instance()`` -- run under ``lane_env(lane, "shutdown")``
          so ``EC2_EXPERIMENT_TAG``/``EC2_STATE_FILE`` resolve to THIS
          lane's box (see `_SHUTDOWN_SNIPPET`'s comment).

    Raises
    ------
    ValueError
        `phase` is not one of the three known phases.
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
# http://<ip>:8000/v1` once the swapped-in checkpoint is confirmed healthy
# (smolbench/evals/ec2.py, the `logging.info(f"serve_model: {model!r} is up
# at {_base_url()}")` call in `serve_model`). The in-flight line
# (`serve_model: requesting '<model>' ...`) must NOT match -- that is the
# thing the family gate is waiting to stop seeing.
SERVE_HEALTHY_RE = re.compile(r"serve_model: '.+?' is up at http://\S+")


def is_serve_healthy(line: str) -> bool:
    """Whether `line` is the provider's "checkpoint is live and healthy" log line.

    Parameters
    ----------
    line : str
        One line of a lane's log file (may carry a logging-format prefix,
        e.g. ``"INFO:root:"``).

    Returns
    -------
    bool
        True iff `line` matches ``ec2.py``'s
        ``serve_model: '<model>' is up at http://<ip>:8000/v1`` shape.
        False for the earlier ``serve_model: requesting '<model>' ...`` line
        (and for everything else).
    """
    return SERVE_HEALTHY_RE.search(line) is not None


# ---------------------------------------------------------------------------
# Restart-policy classifier
# ---------------------------------------------------------------------------
# Deliberately EXCLUDES the bare, healthy provisioning line
# (`provision_spot_instance: trying <type> in <az> ...`, logged by
# `ec2._launch_fresh` on EVERY attempt, successful or not) as a reclaim
# signature. That line appears in every successful launch too -- matching it
# would misclassify a genuine provisioning-time CRASH (which necessarily
# also logs a "trying ..." line before failing) as a "reclaim", and reclaims
# get UNLIMITED retries. Only provisioning-FAILURE wording (capacity/quota
# errors, or the actionable "endpoint unreachable" ec2.py raises after its
# connection-failure cap trips -- the documented spot-reclaim/IP-drift
# symptom) counts here.
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
    """Classifies a lane's non-zero exit as a spot reclaim or a real crash.

    Parameters
    ----------
    log_tail : str
        The last ~40 lines of the lane's log file at the moment its process
        was observed to have exited.
    instance_present : bool
        Whether this lane's ``scaling-<key>``-tagged instance was seen in
        the most recent ``describe_instances`` sweep.

    Returns
    -------
    str
        ``"reclaim"`` when `instance_present` is False (the box itself is
        simply gone) OR `log_tail` matches one of ``RECLAIM_PATTERNS`` (a
        capacity/quota failure, or the actionable "endpoint unreachable"
        error -- see that constant's comment for what is deliberately
        excluded). ``"crash"`` otherwise, INCLUDING an empty tail with the
        instance still present (a process that exited with no output at all
        while its box is confirmed alive is not a reclaim signature).

    Notes
    -----
    Restart policy consuming this classification (implemented in the
    monitor loop, documented here since this function is what decides it):
    ``"reclaim"`` -> relaunch, UNLIMITED retries (a spot interruption is
    routine and not the lane's fault); ``"crash"`` -> relaunch up to
    ``MAX_CRASH_RELAUNCHES`` (2) times, then HALT that lane while the rest
    of the fleet continues. Getting this backwards either abandons a lane on
    a routine interruption, or burns money relaunching a lane that will
    always fail the same way.
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
    """Measures the fraction of a model's landed marks that carry a reasoning trace.

    A DIRECT measurement, not a proxy: ``Mark.reasoning`` (see
    ``smolbench/evals/__init__.py``) is persisted per mark, so this reads
    exactly what the served checkpoint returned -- there is no need to infer
    "was CoT on" from response length or latency.

    Parameters
    ----------
    store : Any
        A duck-typed ``ResultsStore``-shaped object exposing ``exists(addr)``
        and ``load_marks(addr)`` (see ``smolbench.evals.results_store.
        ResultsStore``). Injected rather than resolved internally so this
        function is testable with a plain fake and no S3 -- see
        :func:`build_results_store` for the real backend used in
        production.
    model : str
        Spec key -- becomes ``ReplicateAddress.model``.
    tag : str
        Analysis tag -- becomes ``ReplicateAddress.tag`` (unused by the S3
        backend, but required by the address shape).
    seed : int or None, optional
        Replicate seed to inspect. ``None`` (the default) uses
        ``run_study.BASE_SEED`` -- the CoT-ON check runs against the FIRST
        replicate a lane collects, per the module docstring.
    infos : Sequence[str] or None, optional
        Info types to pool across. ``None`` (the default) uses
        ``run_study.INFO_TYPES`` (all four arms).

    Returns
    -------
    float or None
        ``None`` when NO info arm has landed yet for (`model`, `seed`) --
        there is nothing to judge. Otherwise the fraction of pooled marks
        showing REASONING EVIDENCE: a non-empty ``Mark.reasoning``, or a
        ``Mark.response`` longer than ``COT_CONTENT_REASONING_MIN_CHARS``.

    Notes
    -----
    Why response length counts (added 2026-08-11, from live fleet data):
    models whose thinking rides a SOFT protocol reason on essentially every
    mark but only sometimes wrap it in their think markup -- Ministral's
    [THINK] system-prompt protocol and EXAONE's ``enable_thinking`` both
    produced "Alright, let's tackle this step by step..." chains in plain
    ``response`` content on 40-60% of marks, which the reasoning parsers
    (and the client-side ``</think>`` split) rightly leave unsplit. That IS
    chain-of-thought; only the channel differs. Counting channel alone
    halted those lanes as "silently non-thinking" when the transcript shows
    the opposite. The quiz's output contract is "return exactly one integer
    and nothing else", so a TRULY non-thinking mark is a few characters --
    any response beyond ``COT_CONTENT_REASONING_MIN_CHARS`` is a reasoning
    chain in content, not a compliant bare answer. A lane whose toggle is
    genuinely broken (bare integers everywhere, empty reasoning channel)
    still fails this check exactly as before.

    Silently non-thinking data is worse than no data at all: a lane that
    quietly collects 30 replicates of non-reasoning output looks, on disk,
    identical to a successful run -- nothing downstream can tell the two
    apart after the fact. Below ``COT_MIN_FRACTION`` the monitor loop halts
    the lane loudly, right after its first replicate, rather than let that
    happen.
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
    """Builds the real ``ResultsStore`` for production ``reasoning_fraction`` calls.

    Thin wrapper over ``resolve_store(run_study.EXPERIMENT.results_dir)`` --
    kept separate from :func:`reasoning_fraction` itself (which takes
    `store` as a parameter) purely so that function stays testable with a
    fake store and no S3/local-filesystem dependency at all.

    Returns
    -------
    smolbench.evals.results_store.ResultsStore
        Whichever backend ``resolve_store`` selects for this study's
        results directory (S3-backed when ``SMOLBENCH_RESULTS_S3`` is set,
        local otherwise -- see that function's own docstring).
    """
    return resolve_store(run_study.EXPERIMENT.results_dir)


# ---------------------------------------------------------------------------
# Pre-flight (before any subprocess.Popen)
# ---------------------------------------------------------------------------
def preflight(lanes: Sequence[Lane]) -> dict[str, int]:
    """Warms every lane's tokenizer and derives its completion budget.

    Calls ``run_study.completion_budget(lane.key, seeds)`` for every lane in
    `lanes` BEFORE this script launches a single subprocess (and therefore
    before any EC2 instance is provisioned).

    Parameters
    ----------
    lanes : Sequence[Lane]
        The lanes about to be launched.

    Returns
    -------
    dict[str, int]
        Spec key -> derived completion-token budget, for every lane in
        `lanes` -- only returned when EVERY lane succeeded (see Raises).

    Raises
    ------
    SystemExit
        If ANY lane failed -- either a genuine exception (e.g. a HuggingFace
        tokenizer fetch failure) or ``run_study.completion_budget``'s own
        ``SystemExit`` when the derived budget would fall below
        ``run_study.MIN_VIABLE_BUDGET``. Both are COLLECTED across every
        lane (not raised on the first failure) so a single pre-flight pass
        reports every broken lane at once; a table of
        ``lane / exception type / message`` is printed before this function
        raises.

    Notes
    -----
    This work is pure CPU plus HuggingFace tokenizer downloads -- it costs
    only wall clock on a machine that is not yet billing anything. Running
    it BEFORE ``EXPERIMENT.provision()`` (which this function never calls)
    means a tokenizer-fetch failure or an under-budget verdict can never
    land in the far more expensive position of "between a live, billing GPU
    box and the first inference request".

    ``except (Exception, SystemExit)`` below is intentional and not a bare
    ``except:`` -- ``run_study.completion_budget`` itself raises
    ``SystemExit`` (not a plain ``Exception``) on the budget-floor failure,
    and ``SystemExit`` does not subclass ``Exception``, so a plain
    ``except Exception`` would let that specific, very-plausible failure
    mode escape this loop's "collect, don't abort on the first one"
    contract.
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


def nightly_image_digest() -> Optional[str]:
    """Best-effort ``docker manifest inspect`` digest lookup for ``NIGHTLY_IMAGE``.

    Returns
    -------
    str or None
        The manifest's content digest, or ``None`` when ``docker`` is not on
        ``PATH``, the inspect call fails (network, auth, rate limit), or the
        returned JSON carries no digest field in a shape this function
        recognises. Every ``None`` path logs why at INFO level.

    Notes
    -----
    Purely informational: this is recorded in the run banner so a launch's
    exact ``:nightly`` build is written down somewhere durable (lane logs,
    stdout) -- ``:nightly`` is a MOVING tag, and "which nightly build did
    this study actually run against" is otherwise unanswerable after the
    fact. Never raises; a digest-lookup failure must never block a launch.
    """
    if shutil.which("docker") is None:
        logging.info("nightly_image_digest: docker not found on PATH; skipping digest lookup.")
        return None
    try:
        result = subprocess.run(
            ["docker", "manifest", "inspect", NIGHTLY_IMAGE],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
    except Exception as exc:  # noqa: BLE001 -- best-effort banner info only, never fatal
        logging.info(f"nightly_image_digest: 'docker manifest inspect' failed: {exc}")
        return None

    try:
        manifest = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        logging.info(f"nightly_image_digest: could not parse manifest JSON: {exc}")
        return None

    digest = manifest.get("config", {}).get("digest")
    if not digest:
        # Multi-arch images return a manifest LIST rather than a single
        # manifest with a top-level "config" -- fall back to the first
        # platform entry's own digest.
        entries = manifest.get("manifests") or []
        if entries:
            digest = entries[0].get("digest")
    if not digest:
        logging.info("nightly_image_digest: manifest JSON had no recognisable digest field.")
        return None
    return digest


# ---------------------------------------------------------------------------
# Lane logs
# ---------------------------------------------------------------------------
# __file__-anchored per repo convention (never cwd-relative -- this script
# may be launched from any working directory). Lives inside an
# already-gitignored tree (`notebooks/*/results/`), and `*.log` is
# separately gitignored on top of that (see .gitignore), so lane logs -- one
# per subprocess, potentially gigabytes of vLLM/CoT chatter over a study run
# -- never enter a commit either way.
LOG_DIR: Path = REPO_ROOT / "notebooks" / "induction" / "results" / "fleet_logs"


def _tail_log(log_dir: Path, key: str, n: int = 40) -> str:
    """Returns the last `n` lines of lane `key`'s log file, or ``""`` if unreadable."""
    path = log_dir / f"{key}.log"
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-n:])


def _start_phase(run: "_LaneRun", log_dir: Path) -> None:
    """Launches `run`'s CURRENT phase as a subprocess, log appended to ``<key>.log``."""
    phase = run.current_phase
    if phase is None or phase == "shutdown":
        raise RuntimeError(f"_start_phase: lane {run.lane.key} has no runnable current phase")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{run.lane.key}.log"
    cmd = lane_command(run.lane, phase)
    env = lane_env(run.lane, phase)
    logging.info(f"run_fleet[{run.lane.key}]: launching phase={phase!r}: {' '.join(cmd)}")
    # Opening in append mode ("a") is what lets the family gate scan a
    # lane's WHOLE log (across a relaunch, or across a later phase) for the
    # one-time healthy-serve line -- a truncating mode would lose it the
    # moment the lane's phase changed.
    with open(log_path, "a") as log_file:
        run.proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file, env=env)
    run.started_at = time.monotonic()


def _launch_batch(runs: dict, keys: Sequence[str], log_dir: Path) -> None:
    """Launches each lane in `keys` (its current phase), ``LAUNCH_STAGGER_SECONDS`` apart."""
    for i, key in enumerate(keys):
        if i:
            time.sleep(LAUNCH_STAGGER_SECONDS)
        _start_phase(runs[key], log_dir)


# ---------------------------------------------------------------------------
# S3 spool sync (deduction lanes only)
# ---------------------------------------------------------------------------
SPOOL_BUCKET = "smolbench-results-414266451290"
SPOOL_REGION = "us-west-2"


def sync_deduction_spool(lane: Lane, *, client: Any = None) -> int:
    """Uploads one lane's local deduction spool to S3, then prunes it.

    Parameters
    ----------
    lane : Lane
        The lane whose deduction results should be spooled.
    client : Any, optional
        A boto3 S3 client (exposing ``upload_file``). ``None`` (the
        default) builds a real one lazily -- see Notes. Injectable for
        testing without AWS.

    Returns
    -------
    int
        Number of files uploaded. ``0`` (with nothing uploaded or deleted)
        when the source directory does not exist -- this is NOT an error;
        a lane that never produced deduction output has nothing to spool.

    Notes
    -----
    Source: ``notebooks/deduction/results/runs/scaling_<key>/`` (repo-root
    anchored). Destination: ``s3://smolbench-results-414266451290/
    deduction/runs/scaling_<key>/<relative path>``, region ``us-west-2``.

    Uses boto3's ``upload_file`` directly rather than shelling out to the
    ``aws`` CLI -- the CLI is not a declared dependency of this repo, while
    boto3 already is (see ``smolbench.evals.ec2``'s own lazy-import
    convention, which this function follows: boto3 is imported INSIDE this
    function, not at module scope, so importing ``run_fleet`` needs no AWS
    SDK at all).

    After every file uploads successfully, the local spool is PRUNED: every
    uploaded file is deleted, and every now-empty subdirectory is removed --
    EXCEPT ``manifest.json`` at the run directory's root, which is always
    kept. ``manifest.json`` is the run's config/run-id record (see
    ``smolbench.deduction.lean.runner``'s "Output layout" docstring
    section); leaving it behind is what lets a LATER resume of this run
    recognise it already exists without re-downloading the whole spool from
    S3 first just to check.
    """
    source = REPO_ROOT / "notebooks" / "deduction" / "results" / "runs" / f"scaling_{lane.key}"
    if not source.is_dir():
        logging.info(f"sync_deduction_spool[{lane.key}]: no spool at {source}; nothing to sync.")
        return 0

    if client is None:
        import boto3  # lazy -- see docstring

        client = boto3.client("s3", region_name=SPOOL_REGION)

    dest_prefix = f"deduction/runs/scaling_{lane.key}/"
    files = sorted(p for p in source.rglob("*") if p.is_file())
    for path in files:
        rel = path.relative_to(source).as_posix()
        client.upload_file(str(path), SPOOL_BUCKET, dest_prefix + rel)

    manifest_path = source / "manifest.json"
    for path in files:
        if path != manifest_path:
            path.unlink()

    # Remove now-empty subdirectories, deepest-first, so a parent directory
    # is only attempted after all of its children have already been
    # cleared. `source` itself is never removed (it still holds
    # manifest.json).
    subdirs = sorted(
        (p for p in source.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True
    )
    for subdir in subdirs:
        try:
            subdir.rmdir()
        except OSError:
            pass  # not empty -- fine, leave it

    logging.info(f"sync_deduction_spool[{lane.key}]: uploaded {len(files)} file(s) to "
                 f"s3://{SPOOL_BUCKET}/{dest_prefix}")
    return len(files)


# ---------------------------------------------------------------------------
# Live orchestration: launch, monitor, restart, phase-advance, gate, shutdown
# ---------------------------------------------------------------------------
# Nothing below this point runs at import time -- it is all reached only
# from main()'s live (non---dry-run) path.


@functools.lru_cache(maxsize=1)
def _fleet_status_module():
    """Lazily loads ``scripts/fleet_status.py`` by file path, cached after the first call.

    Loaded by path (the same convention as `run_study` above) rather than
    `sys.path` + a bare `import fleet_status`, for the same reason: this
    avoids any risk of colliding with how ``tests/test_run_fleet.py`` loads
    the very same file under its own private module name. Deferred (not a
    module-scope import) so that importing `run_fleet` itself does nothing
    beyond building `LANES` and running its drift guard -- this helper is
    only ever invoked from inside the live monitor loop, never at import
    time.
    """
    path = Path(__file__).resolve().parent / "fleet_status.py"
    spec = importlib.util.spec_from_file_location("run_fleet_fleet_status_dep", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class _LaneRun:
    """Mutable per-lane runtime state tracked across monitor-loop ticks.

    Not part of this file's tested contract (nothing in
    ``tests/test_run_fleet.py`` touches this class) -- it exists purely to
    give the monitor-loop helpers below a single place to carry a lane's
    subprocess handle, its position in its phase sequence, and its
    restart/halt bookkeeping between ticks.
    """

    lane: Lane
    #: Ordered subprocess phases this invocation runs for this lane, e.g.
    #: ``("induction",)``, ``("deduction",)``, or ``("induction", "deduction")``.
    phases: tuple[str, ...]
    phase_index: int = 0
    proc: Optional[subprocess.Popen] = None
    started_at: float = 0.0
    crash_relaunches: int = 0
    cot_checked: bool = False
    halted: bool = False
    halt_reason: str = ""
    done: bool = False

    @property
    def current_phase(self) -> Optional[str]:
        """The phase this lane is currently running, or None once `phases` is exhausted."""
        if self.phase_index >= len(self.phases):
            return None
        return self.phases[self.phase_index]


def _phase_sequence(phase: str) -> tuple[str, ...]:
    """Maps a ``--phase`` CLI value onto the ordered subprocess phases each lane runs.

    Parameters
    ----------
    phase : str
        One of ``"induction"``, ``"deduction"``, ``"both"``.

    Returns
    -------
    tuple[str, ...]
        ``("induction",)``, ``("deduction",)``, or ``("induction",
        "deduction")`` respectively. A lane's instance is shut down (see
        `_advance_finished`) only once its LAST scheduled phase here exits
        successfully AND that phase was ``"deduction"`` -- an
        induction-only invocation never shuts its boxes down, by design
        (see the module docstring's "Phases" section).

    Raises
    ------
    ValueError
        `phase` is not one of the three recognised values.
    """
    if phase == "induction":
        return ("induction",)
    if phase == "deduction":
        return ("deduction",)
    if phase == "both":
        return ("induction", "deduction")
    raise ValueError(f"run_fleet: unknown --phase {phase!r}; expected induction/deduction/both")


def _lane_gate_passed(run: _LaneRun, log_dir: Path) -> bool:
    """Whether `run`'s log already contains a healthy-serve line (see `is_serve_healthy`)."""
    tail = _tail_log(log_dir, run.lane.key, n=100_000)
    return any(is_serve_healthy(line) for line in tail.splitlines())


def _monitor_tick(
    runs: dict[str, _LaneRun], log_dir: Path, tick: int, present_lanes: Optional[set]
) -> Optional[set]:
    """One polling pass over every lane: refresh instance presence, print the fleet table, alert.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Every lane currently under supervision.
    log_dir : Path
        Directory holding ``<key>.log`` for each lane.
    tick : int
        1-based tick counter (used to decide whether this tick also
        refreshes `present_lanes`).
    present_lanes : set[str] or None
        The set of lane keys seen in the most recent
        ``describe_instances`` sweep, or ``None`` if none has run yet.

    Returns
    -------
    set[str] or None
        The (possibly refreshed) `present_lanes`, for the caller to thread
        into the next tick.

    Notes
    -----
    The describe sweep runs on tick 1 (so the fleet table has SOME instance
    data from the very first tick, rather than waiting a full
    ``DESCRIBE_EVERY_N_TICKS`` ticks) and then every
    ``DESCRIBE_EVERY_N_TICKS``-th tick after that -- read-only, reusing
    ``fleet_status.fleet_rows`` rather than duplicating its boto3 call. A
    failed describe (one bad region, a throttled call) is logged and
    SKIPPED, leaving `present_lanes` at its last-known value rather than
    treating "could not check" as "everything is gone".
    """
    if tick == 1 or tick % DESCRIBE_EVERY_N_TICKS == 0:
        try:
            rows = _fleet_status_module().fleet_rows()
            present_lanes = {row["lane"] for row in rows}
        except Exception as exc:  # noqa: BLE001 -- one bad sweep must not crash the monitor
            logging.warning(f"run_fleet: describe_instances sweep failed this tick: {exc}")

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

        if present_lanes is not None and alive and key not in present_lanes:
            print(f"ALERT [{key}]: subprocess is still running but its instance is "
                  "gone or shutting down.")

        if run.started_at:
            age_hours = (time.monotonic() - run.started_at) / 3600
            budget = 2 * run.lane.budget_hours
            if age_hours > budget:
                print(f"ALERT [{key}]: wall clock {age_hours:.1f}h exceeds 2x budget "
                      f"({budget}h).")
    return present_lanes


def _apply_restart_policy(
    runs: dict[str, _LaneRun], log_dir: Path, present_lanes: Optional[set]
) -> None:
    """Relaunches or halts every lane whose subprocess exited non-zero this tick.

    Uses `classify_exit` on the lane's last ~40 log lines and whether its
    tag was present in the latest describe sweep. See `classify_exit`'s
    docstring for the restart policy this enforces (unlimited retries for a
    "reclaim", up to `MAX_CRASH_RELAUNCHES` for a "crash", then a halt).
    """
    for key, run in runs.items():
        if run.halted or run.done or run.proc is None:
            continue
        rc = run.proc.poll()
        if rc is None or rc == 0:
            continue  # still running, or a clean exit (handled by _advance_finished)

        tail = _tail_log(log_dir, key)
        # `present_lanes is None` means no describe sweep has landed yet --
        # default to "present" rather than "gone", since treating an
        # unchecked lane as reclaimed would force an immediate relaunch on
        # every lane's very first tick with no real signal behind it.
        instance_present = present_lanes is None or key in present_lanes
        verdict = classify_exit(tail, instance_present)
        if verdict == "reclaim":
            logging.warning(
                f"run_fleet[{key}]: exited rc={rc}, classified RECLAIM -- relaunching "
                "(unlimited retries)."
            )
            _start_phase(run, log_dir)
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
    """Runs the CoT-ON assertion once per lane, halting any lane below `COT_MIN_FRACTION`.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Every lane currently under supervision.
    store_factory : Callable[[], Any], optional
        Builds the ``ResultsStore`` to check against. Defaults to
        `build_results_store`; overridable for tests.
    """
    for key, run in runs.items():
        if run.cot_checked or run.halted or run.done or run.current_phase != "induction":
            continue
        try:
            store = store_factory()
            # intens ONLY (2026-08-11, live fleet): this is a WIRING check --
            # "did the thinking toggle reach the model" -- and intens is the
            # short, well-formed arm where every correctly-wired model
            # demonstrably reasons. Pooling all arms halted EXAONE-4.0 whose
            # toggle provably works (intens/zero 100% reasoning) because the
            # model COLLAPSES on the ~30k-token extens listing and
            # confabulates on the whitespace-padded noise arm -- which is
            # exactly the phenomenon the study measures (cf. Nemotron-3's
            # extens collapse in the prior study), i.e. data, not a fault.
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
    """Advances every lane whose subprocess exited cleanly to its next phase, or shuts it down."""
    for key, run in runs.items():
        if run.halted or run.done or run.proc is None:
            continue
        if run.proc.poll() != 0:
            continue  # not a clean exit (still running, or handled by the restart policy)

        finished_phase = run.current_phase
        if finished_phase == "deduction":
            try:
                sync_deduction_spool(run.lane)
            except Exception as exc:  # noqa: BLE001 -- a failed spool sync must not crash the monitor
                logging.error(f"run_fleet[{key}]: spool sync failed: {exc}")

        run.phase_index += 1
        if run.current_phase is not None:
            _start_phase(run, log_dir)
            continue

        # No more scheduled phases. Only shut the box down if a deduction
        # phase actually ran THIS invocation -- an induction-only run leaves
        # the instance up on purpose (see the module docstring's "Phases"
        # section); the box may still be needed by a later
        # `--phase deduction` invocation.
        if "deduction" in run.phases:
            logging.info(f"run_fleet[{key}]: all phases complete; shutting down its instance.")
            cmd = lane_command(run.lane, "shutdown")
            env = lane_env(run.lane, "shutdown")
            subprocess.run(cmd, env=env, check=False)
        run.done = True


def _all_terminal(runs: dict[str, _LaneRun]) -> bool:
    """Whether every lane has either halted or fully completed its phase sequence."""
    return all(run.halted or run.done for run in runs.values())


def _run_fleet(
    lanes: dict[str, Lane], phase_sequence: tuple[str, ...], *, gate: bool, log_dir: Path, phase_name: str
) -> None:
    """Launches and supervises every lane in `lanes` to completion (or halt).

    Implements the module docstring's "Launch order and the family gate"
    and "Monitor loop" sections: tier D first, then tier A, both staggered;
    then (unless `gate` is False, or no gate model is among `lanes`) a
    blocking wait -- itself running full monitor ticks, so a crash in a gate
    lane is still caught and retried/halted promptly -- for every
    ``GATE_MODELS`` lane to report a healthy serve; then tiers B and C,
    staggered; then a monitor loop until every lane is halted or done.
    """
    runs = {key: _LaneRun(lane=lane, phases=phase_sequence) for key, lane in lanes.items()}

    tier_d = [k for k in lanes if lanes[k].tier == "D"]
    tier_a = [k for k in lanes if lanes[k].tier == "A"]
    tier_bc = [k for k in lanes if lanes[k].tier in ("B", "C")]

    _launch_batch(runs, tier_d, log_dir)
    _launch_batch(runs, tier_a, log_dir)

    present_lanes: Optional[set] = None
    tick = 0

    gate_keys = [k for k in GATE_MODELS if k in runs] if gate else []
    while gate_keys and not all(_lane_gate_passed(runs[k], log_dir) for k in gate_keys):
        tick += 1
        time.sleep(MONITOR_INTERVAL_SECONDS)
        present_lanes = _monitor_tick(runs, log_dir, tick, present_lanes)
        _apply_restart_policy(runs, log_dir, present_lanes)
        _check_cot(runs)
        _advance_finished(runs, log_dir)
        if all(runs[k].halted for k in gate_keys):
            logging.error(
                "run_fleet: FAMILY GATE FAILED -- every GATE_MODELS lane halted; NOT "
                "launching tiers B/C. Investigate the nightly image before retrying."
            )
            gate_keys = []  # stop waiting; skip the else-clause launch below
            break
    else:
        logging.info("run_fleet: family gate passed (or was skipped) -- launching tiers B and C.")
        _launch_batch(runs, tier_bc, log_dir)

    while not _all_terminal(runs):
        tick += 1
        time.sleep(MONITOR_INTERVAL_SECONDS)
        present_lanes = _monitor_tick(runs, log_dir, tick, present_lanes)
        _apply_restart_policy(runs, log_dir, present_lanes)
        _check_cot(runs)
        _advance_finished(runs, log_dir)

    halted = {key: run.halt_reason for key, run in runs.items() if run.halted}
    if halted:
        logging.error(f"run_fleet: fleet finished with {len(halted)} halted lane(s): {halted}")
    if phase_name == "induction":
        print(
            "\nrun_fleet: induction-only run complete. Boxes are left RUNNING on purpose "
            "(the deduction phase may reuse them) -- run "
            "`scripts/fleet_teardown.py --terminate` when you are done with them."
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
        help="Print the launch plan (tier, command, full environment per lane) and exit; "
        "launches no subprocess and makes no AWS call. Does NOT run preflight (tokenizer "
        "warm-up + completion-budget derivation) or check the nightly image digest -- those "
        "only run on a live launch, so this proves the wiring is correct, not that the "
        "lanes will actually start.",
    )
    return parser


def _selected_lanes(raw: str) -> dict[str, Lane]:
    """Resolves ``--lanes`` into a ``{key: Lane}`` mapping, in ``LANES`` declaration order.

    Raises
    ------
    SystemExit
        `raw` names a key that is not in `LANES`.
    """
    if not raw.strip():
        return dict(LANES)
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    unknown = [k for k in keys if k not in LANES]
    if unknown:
        raise SystemExit(f"run_fleet: unknown --lanes key(s) {unknown}; choose from {sorted(LANES)}")
    chosen = set(keys)
    return {k: LANES[k] for k in LANES if k in chosen}


#: Printed verbatim, right under the DRY RUN header, by `_print_dry_run_plan`.
#: Worded for the OPERATOR running the command, not for a maintainer reading
#: the source -- an operator who treats a clean `--dry-run` as "the launch
#: will work" would otherwise only discover a tokenizer-fetch failure or a
#: budget-floor `SystemExit` on the live run, which is exactly the failure
#: `preflight()` exists to surface EARLIER (see that function's docstring).
_DRY_RUN_NOTICE = (
    "NOTE: this is a WIRING preview only. It did NOT run preflight (per-lane\n"
    "HuggingFace tokenizer warm-up + completion-budget derivation) and did NOT\n"
    "check the current vllm/vllm-openai:nightly image digest -- both do real\n"
    "network I/O (HuggingFace, Docker Hub) and only run on the live path\n"
    "(drop --dry-run). A clean plan below means the commands and per-lane\n"
    "environment are correct; it does NOT mean the lanes will actually start --\n"
    "a tokenizer fetch failure or a too-small completion budget can still\n"
    "surface for the first time on the live launch.\n"
)


def _print_dry_run_plan(lanes: dict[str, Lane], phase_name: str) -> None:
    """Prints, per selected lane, its tier, every scheduled phase's command, and full env.

    Notes
    -----
    Prints `_DRY_RUN_NOTICE` immediately under the header -- this preview
    deliberately never calls `preflight`/`nightly_image_digest` (both do
    real network I/O; see the module docstring's "Cost warning" section),
    so the output says so explicitly rather than letting a clean dry run
    read as "the live launch will also succeed".
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
    """CLI entry point: parse args, then either print the dry-run plan or launch the fleet live.

    Parameters
    ----------
    argv : list[str] or None, optional
        Arguments to parse; ``None`` parses ``sys.argv[1:]``.

    Returns
    -------
    int
        ``0`` on completion of a dry run, or after the live fleet reaches an
        all-terminal state (some lanes may still be individually halted --
        see the printed summary and each lane's log for details).

    Notes
    -----
    ``--dry-run`` performs NO pre-flight (tokenizer warm-up), NO
    ``docker manifest inspect``, and launches no subprocess -- it only
    resolves the lane selection and prints what a live launch WOULD do,
    which is itself pure/local computation (`lane_command`/`lane_env`).
    """
    args = _build_arg_parser().parse_args(argv)
    lanes = _selected_lanes(args.lanes)

    if args.dry_run:
        _print_dry_run_plan(lanes, args.phase)
        return 0

    log_dir = Path(args.log_dir).resolve() if args.log_dir else LOG_DIR

    preflight(list(lanes.values()))
    digest = nightly_image_digest()
    logging.info(f"run_fleet: launching against {NIGHTLY_IMAGE} (digest={digest or 'unknown'}).")

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
