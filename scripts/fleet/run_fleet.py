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
- Restart policy: :func:`classify_exit` gives a reclaim unlimited relaunches and
  a crash ``MAX_CRASH_RELAUNCHES``, then HALTS that lane; the fleet continues.
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
# module name goes ambiguous once both trees sit on `sys.path`. `run_study.MODELS`
# (spec key -> analysis tag) is the single source of truth for this study's
# roster; LANES below is built FROM it. The import also runs
# `load_dotenv(notebooks/induction/keys.env)`, which is DESIRED here: it is how
# AWS profile, results-store and model-cache variables reach THIS process, for
# `lane_env` to pass through to every lane.
_RUN_STUDY_PATH = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
_run_study_spec = importlib.util.spec_from_file_location("induction_run_study", _RUN_STUDY_PATH)
run_study = importlib.util.module_from_spec(_run_study_spec)
sys.modules[_run_study_spec.name] = run_study
_run_study_spec.loader.exec_module(run_study)

# `run_study`'s import of `smolbench.induction.experiment` already pulled in
# `smolbench.evals.providers.ec2`, AFTER its own `load_dotenv` ran, so this is a
# `sys.modules` cache hit, not a second, differently-timed import of `ec2.py`.
from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS  # noqa: E402

# ---------------------------------------------------------------------------
# Constants (exact names/values -- pinned by tests/tooling/test_run_fleet.py)
# ---------------------------------------------------------------------------
DEFAULT_REGIONS = "us-east-1,us-east-2,us-west-2"
# Digest-pinned, certified-deterministic build: vLLM 0.27.2rc1.dev122+g8efa13b70,
# Docker Hub tag nightly-8efa13b700f1836657699cae2503dc2feab27fa0. Mirrors
# ec2.py's EC2_VLLM_IMAGE default, which the fleet's per-lane env would
# otherwise render dead letter. Bump only on purpose.
FLEET_IMAGE = "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7"
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
# budget-burning 87k-token generation takes >1h at eager Pro throughput, so
# under the fleet-wide 3600s timeout those cells retry forever; 14400s lets a
# worst-case cell finish in ONE attempt. The box-side idle watchdog keys on vLLM
# metrics activity, so an hours-long in-flight generation cannot trip it.
# NOTE: every timeout here was computed against BATCHED serving; ec2.py's
# DETERMINISM_ARGS serve --max-num-seqs 1 fleet-wide, so concurrent requests
# serialize and per-request wall time multiplies by the in-flight count.
# Recompute before the next paid fleet run.
LANE_REQUEST_TIMEOUT_OVERRIDES = {
    "deepseek-v4-pro": "14400",
    # gemma-4-12b and ministral-3-14b serve on g6e.12xl (4x L40S) at ~146
    # tok/s AGGREGATE, so concurrent 87k-token budget-burner cells run
    # >1h each and die at the 3600s read timeout. 10800s covers the worst
    # case (~90 min at 3 concurrent) with 2x headroom.
    "gemma-4-12b": "10800",
    "ministral-3-14b": "10800",
}

TIER_INSTANCE_TYPES = {
    # g6e.12xlarge is the fallback when small-G spot is reclaimed in the
    # hunt AZs: a 3x-cost fallback beats an idle lane.
    "A": "g6e.4xlarge,g6e.8xlarge,g6e.12xlarge",
    "B": "g6e.12xlarge,g6e.24xlarge",
    "C": "p5.48xlarge,p5e.48xlarge",
    # D is p6-b200 (8x B200, SM100). deepseek-v4-pro's spec drops its
    # Marlin pin for SM100's native MXFP4 path; that marlin-less spec MUST
    # NOT serve on p5e/p5en (see the spec comment in ec2.py).
    "D": "p6-b200.48xlarge",
}
# Tier D only; every other tier falls back to DEFAULT_REGIONS. All 3 study
# regions stay in the p6-b200 hunt: unlike p5e (us-east-2/us-west-2 only),
# B200 placement is still shifting, so excluding a region risks starving
# the experiment.
TIER_REGIONS = {"D": "us-east-1,us-east-2,us-west-2"}
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

    `key` is an ``EC2_DEPLOY_SPECS`` / ``run_study.MODELS`` key and vLLM's
    ``--served-model-name``; `tag` is ``run_study.MODELS[key]``, used in result
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
        """This lane's ``smolbench:experiment`` tag value: ``f"scaling-{key}"``."""
        return f"scaling-{self.key}"

    @property
    def state_file(self) -> str:
        """This lane's private EC2 state-file basename (repo-root-anchored by the driver)."""
        return f".ec2_state_scaling_{self.key}.json"

    @property
    def budget_hours(self) -> int:
        """Expected wall-clock hours for this tier; `_monitor_tick` alerts past 2x."""
        return TIER_BUDGET_HOURS[self.tier]


def _drift_guard() -> None:
    """Verify, at IMPORT time, that ``TIER_MEMBERS`` agrees with both sources of truth.

    ``TIER_MEMBERS`` is HAND-WRITTEN and must match ``run_study.MODELS`` and
    ``set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"}``; a rung added there but not
    here would silently never run. At import time, so even a bare import or
    ``--dry-run`` catches the drift.

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

#: Spec key -> Lane for every model this study runs, built from
#: TIER_MEMBERS x run_study.MODELS; _drift_guard above has already
#: certified both against each other.
LANES: dict[str, Lane] = {
    key: Lane(key=key, tag=run_study.MODELS[key], tier=tier)
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
        :func:`sync_deduction_spool` looks the local spool up under.

    Notes
    -----
    PURE: never mutates `base_env`, always returns a NEW ``dict``. Mutating
    ``os.environ`` across 21 lanes launched from one parent would let lane N+1
    inherit lane N's tag and state file, and the two would then reattach to ONE
    instance, swapping each other's checkpoint out.
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
            "EC2_VLLM_IMAGE": LANE_IMAGE_OVERRIDES.get(lane.key, FLEET_IMAGE),
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


def _tail_log(log_dir: Path, key: str, n: int = 40) -> str:
    """Returns the last `n` lines of lane `key`'s log file, or ``""`` if unreadable."""
    path = log_dir / f"{key}.log"
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return ""
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


def _launch_batch(runs: dict, keys: Sequence[str], log_dir: Path) -> None:
    """Launch each lane in `keys` at its current phase, ``LAUNCH_STAGGER_SECONDS`` apart."""
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
    """Upload one lane's local deduction spool to S3, then prune it.

    Parameters
    ----------
    client : Any, optional
        boto3 S3 client; ``None`` builds one lazily, so importing ``run_fleet``
        needs no AWS SDK. Pass a fake to test without AWS.

    Returns
    -------
    int
        Files uploaded; ``0``, nothing uploaded or deleted, when the source
        directory does not exist (not an error).

    Notes
    -----
    ``notebooks/deduction/results/runs/scaling_<key>/`` (repo-root anchored) ->
    ``s3://smolbench-results-414266451290/<runner.spool_prefix()>/scaling_<key>/<rel>``
    in ``us-west-2``. The destination prefix is resolved via
    ``smolbench.deduction.lean.runner.spool_prefix()`` at CALL time (imported
    lazily below, matching this function's existing ``boto3`` lazy import),
    never a module constant here -- it defaults to the re-collection's prefix
    and refuses the published pre-cutoff study's ``deduction/runs`` unless
    ``LEAN_ALLOW_LEGACY_PREFIX=1`` is set, so this writer cannot silently
    overwrite that unrecoverable record. Once every file uploads the local
    spool is PRUNED (uploaded files deleted, now-empty subdirectories removed)
    EXCEPT ``manifest.json`` at the run root -- the config/run-id record, kept
    so a later resume recognises the run.
    """
    source = REPO_ROOT / "notebooks" / "deduction" / "results" / "runs" / f"scaling_{lane.key}"
    if not source.is_dir():
        logging.info(f"sync_deduction_spool[{lane.key}]: no spool at {source}; nothing to sync.")
        return 0

    # Lazy import: `smolbench.deduction.lean.runner` pulls in `tiktoken` (via
    # `.context`), which this fleet supervisor otherwise never needs -- match
    # the file's existing lazy-`boto3` pattern just below.
    from smolbench.deduction.lean.runner import spool_prefix

    if client is None:
        import boto3  # lazy -- see docstring

        client = boto3.client("s3", region_name=SPOOL_REGION)

    dest_prefix = f"{spool_prefix()}/scaling_{lane.key}/"
    files = sorted(p for p in source.rglob("*") if p.is_file())
    for path in files:
        rel = path.relative_to(source).as_posix()
        client.upload_file(str(path), SPOOL_BUCKET, dest_prefix + rel)

    manifest_path = source / "manifest.json"
    for path in files:
        if path != manifest_path:
            path.unlink()

    # Deepest-first, so a parent is only attempted once its children are
    # cleared. `source` itself is never removed; it still holds manifest.json.
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


@dataclass
class _LaneRun:
    """Mutable per-lane runtime state, carried across monitor-loop ticks."""

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
    """Check whether `run`'s log has a healthy-serve line (see `is_serve_healthy`)."""
    tail = _tail_log(log_dir, run.lane.key, n=100_000)
    return any(is_serve_healthy(line) for line in tail.splitlines())


def _monitor_tick(
    runs: dict[str, _LaneRun], log_dir: Path, tick: int, present_lanes: Optional[set]
) -> Optional[set]:
    """Run one polling pass over every lane: refresh presence, print the table, alert.

    Parameters
    ----------
    tick : int
        1-based. The ``describe_instances`` sweep (read-only
        ``fleet_status.fleet_rows``) runs on tick 1 -- so the table has instance
        data immediately -- and every ``DESCRIBE_EVERY_N_TICKS``-th tick after.
    present_lanes : set or None
        Lane keys from the last sweep; ``None`` if none has run yet.

    Returns
    -------
    set or None
        The possibly refreshed `present_lanes`. A failed sweep is logged and
        SKIPPED, leaving the last-known value, rather than reading "could not
        check" as "everything is gone".
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
    """Relaunch or halt every lane whose subprocess exited non-zero this tick.

    Enforces `classify_exit`'s verdict: unlimited relaunches for a reclaim,
    `MAX_CRASH_RELAUNCHES` for a crash, then a halt.
    """
    for key, run in runs.items():
        if run.halted or run.done or run.proc is None:
            continue
        rc = run.proc.poll()
        if rc is None or rc == 0:
            continue  # still running, or a clean exit (handled by _advance_finished)

        tail = _tail_log(log_dir, key)
        # No describe sweep has landed yet. Default to "present": treating an
        # unchecked lane as reclaimed would force a relaunch on every lane's
        # very first tick, with no signal.
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
            try:
                sync_deduction_spool(run.lane)
            except Exception as exc:  # noqa: BLE001 -- a failed spool sync must not crash the monitor
                logging.error(f"run_fleet[{key}]: spool sync failed: {exc}")

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
                "launching tiers B/C. Investigate FLEET_IMAGE before retrying."
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
