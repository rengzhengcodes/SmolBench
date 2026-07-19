"""Drive the Lean 4 deduction sweep over the >200B trio on one EC2 spot box.

The trio's base + LoRA variants cannot share a single sweep config: the lean
runner interleaves ``models`` at the innermost loop, but the EC2 box serves
ONE model at a time (``ec2.serve_model`` swaps the vLLM container). So this
driver provisions once, then for each model-variant does
``serve_model(key)`` -> ``runner.sweep(single-model config)`` into a shared
per-phase ``run_dir`` (rows are keyed by ``(model, theorem, k, rung,
rollout)``, so variants never collide), and tears the box down at the end --
the same serve-swap pattern ``InductionExperiment`` uses for the induction
archetypes.

**LoRA delivery.** The adapters were trained on the BF16 bases but are served
on the FP8 bases (both arms share the same FP8 base, so the base-vs-LoRA delta
isolates the adapter). Each adapter's target modules were statically verified
present in its FP8 base index. The read-only HF token cannot push adapters to
the Hub, so instead of ``--lora-modules name=<hf_repo>`` the LoRA specs carry an
``adapters`` block: the box stages the adapter from S3 (its instance profile
grants read) into the mounted hub cache before launch, and vLLM loads it from
the local path (see ``ec2.py`` ``_serve``). This needs ``EC2_S3_MODEL_CACHE``
set at provision time (attaches the instance profile) -- source
``notebooks/periodic/keys.env`` first.

Runs on ``.venv-lean`` (the sweep verifies proofs via ``lean_dojo``). Needs
AWS creds for provisioning + ``HF_TOKEN`` (the FP8 bases are ungated, but the
token is baked in for parity and future gated adds).

Examples
--------
    set -a; source notebooks/periodic/keys.env; set +a

    # Cheap capped pilot, base + LoRA for all three (serve-swapped):
    .venv-lean/bin/python scripts/lean_ec2_sweep.py --phase pilot

    # Base-only (skip the LoRA arms):
    .venv-lean/bin/python scripts/lean_ec2_sweep.py --phase pilot --no-lora

    # Full base+LoRA headline once the pilot gate is green:
    .venv-lean/bin/python scripts/lean_ec2_sweep.py --phase headline
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# EC2_EXPERIMENT_TAG is captured at import time (see ec2.py's env-timing note),
# so set the experiment's identity BEFORE importing ec2. Isolate this
# experiment's instance + state from notebooks/periodic and notebooks/chromatic.
os.environ.setdefault("EC2_EXPERIMENT_TAG", "lean-deduction")
os.environ.setdefault("EC2_STATE_FILE", str(_REPO_ROOT / ".ec2_state_lean.json"))
# The LoRA arms need vLLM >= v0.23.0: v0.11.1 (the ec2.py default, since periodic's
# keys.env doesn't override it) crashes at the LoRA logits processor for adapters
# that add no vocab ("expanded size (0) must match (256)"). v0.23.0 (chromatic's pin)
# serves them fine -- confirmed live 2026-07-08. Self-contained so periodic is untouched.
os.environ.setdefault("EC2_VLLM_IMAGE", "vllm/vllm-openai:v0.23.0")

# The base-model trio (EC2_DEPLOY_SPECS keys). Each has a LoRA adapter in S3
# under <lora-s3-prefix>/<base_key>/ (adapter_config.json + adapter_model.safetensors).
# Default: the >200B LoRA trio. Override via LEAN_TRIO (comma-separated
# EC2_DEPLOY_SPECS keys) to sweep a different base set base-only, e.g. the all-MoE
# generalists: LEAN_TRIO=gpt-oss-120b,nemotron-3-super-120b-a12b,qwen3.5-397b-a17b
# with --no-lora (those have no adapters). Non-breaking: the gate uses the default.
TRIO = os.environ.get(
    "LEAN_TRIO", "llama-31-405b,nemotron-ultra-253b,qwen3-235b-a22b"
).split(",")

#: Where the trained adapters live (same bucket as the model cache; the serving
#: box's instance profile grants read). Overridable via --lora-s3-prefix.
_ADAPTER_S3_PREFIX = "s3://smolbench-model-cache-414266451290/lean-train-checkpoints"

# Shared sweep knobs. max_tokens/request_timeout are sized for the reasoning
# arm (nemotron-ultra); non-reasoning models stop early regardless.
_COMMON = dict(
    seed=1776,
    temperature=0.7,
    max_tokens=32768,
    request_timeout=1200,
    max_retries=2,
    dojo_timeout=300,
    concurrent_gen=True,
    skip_trivial=True,
    theorem_workers=8,
    k={"strategy": "last"},
)

PHASES = {
    # Cheap validation of serving + wiring + base-vs-LoRA signal: a seeded
    # 30-theorem sample of novel_premises/val, 4 rungs, 1 rollout, 6 variants.
    "pilot": {
        **_COMMON,
        "run_name": "lean_trio_pilot",
        "n_rollouts": 1,
        "theorems": {"source": "replay_passing", "kind": "novel_premises",
                     "split": "val", "limit": 30, "seed": 1776},
        "rungs": ["stepk:1", "hint:2", "noise:3", "hint:3"],
    },
    # The headline generalization sweep: all 10 rungs on novel_premises/test.
    "headline": {
        **_COMMON,
        "run_name": "lean_trio_headline",
        "n_rollouts": 3,
        "theorems": {"source": "replay_passing", "kind": "novel_premises", "split": "test"},
        "rungs": [
            "stepk:0", "stepk:1", "stepk:2",
            "hint:0", "hint:1", "hint:2", "hint:3", "hint:4",
            "noise:3", "noise:4",
        ],
    },
    # The paired CoT-recipe gate: bare-tail LoRA vs CoT-augmented LoRA (plus
    # base + real-only controls, via --cot-smoke) at pass@8. `limit`/
    # `n_rollouts` below are placeholders -- the actual spend-gating values
    # are PRE-REGISTERED by `scripts/lean_gate_power.py` (a power analysis
    # run BEFORE any money is spent, per the module's docstring) and passed
    # in at invocation time via `--limit`/`--n-rollouts` rather than hand-
    # edited here, so the registered numbers are the ones that shipped.
    "cot-gate": {
        **_COMMON,
        "run_name": "lean_cot_gate",
        "n_rollouts": 8,
        "theorems": {"source": "replay_passing", "kind": "novel_premises",
                     "split": "val", "limit": 150, "seed": 1776},
        "rungs": ["stepk:1", "hint:2", "noise:3", "hint:3"],
    },
    # Expert-iteration harvest pass: sample pass@8 rollouts on TRAIN theorems
    # (never val/test -- see below) at temperature 1.0 for diversity, so
    # scripts/harvest_expert_iter.py has a genuine choice of distinct correct
    # proofs to dedup/cap per theorem. Single rung (stepk:1) matches the base
    # SFT set's context shape -- harvested rows must be prompt-format
    # identical to `sft.iter_dataset`'s default, or the CoT-augmented target
    # would be trained under a context the eval never actually shows.
    "expert-iter": {
        **_COMMON,
        "run_name": "lean_expert_iter",
        "n_rollouts": 8,
        "temperature": 1.0,
        "rungs": ["stepk:1"],
        # source MUST be "with_proof", not the phase-default "replay_passing":
        # the replay_passing sidecar (`corpus.replay_passing_path`) is only
        # ever generated for val/test (`cli filter` is run against the eval
        # splits, never train -- see corpus.iter_replay_passing's docstring),
        # so `iter_replay_passing("novel_premises", "train")` would raise
        # FileNotFoundError. `with_proof` (`corpus.iter_with_proof`) needs no
        # sidecar and is the same source `sft.iter_dataset` trains on.
        "theorems": {"source": "with_proof", "kind": "novel_premises",
                     "split": "train", "limit": 200, "seed": 1776},
    },
}


#: The Qwen 4-way arms (synthetic-pretraining experiment, notebooks/lean):
#: ``(variant key, adapter subprefix under <lora-s3-prefix>/qwen3-235b-a22b/)``.
#: None = the base arm. stage2 adapters ARE the synth+real arms (stage 2
#: annealed the stage-1 synthetic adapter on the decontaminated real set), so
#: the sweep compares base / real-only / goedel+real / leannav+real.
QWEN_4WAY_ARMS: list[tuple[str, str | None]] = [
    ("qwen3-235b-a22b", None),
    ("qwen3-lean-real", "real-only"),
    ("qwen3-lean-goedel", "goedel-stage2"),
    ("qwen3-lean-leannav", "leannav-stage2"),
]


def _qwen_4way_variants(args, ec2) -> list[dict]:
    """The 4 Qwen arms as serve-swappable variants (same proven pattern as
    ``_variants``: one model name per serve, adapter staged from S3).

    All four arms share the ONE BF16 Qwen base (the trio's FP8-can't-serve
    override applies here too), so the on-box HF cache makes swaps cheap:
    the 470 GB download happens once, later swaps only reload GPUs.
    """
    base = ec2.EC2_DEPLOY_SPECS["qwen3-235b-a22b"]
    base["hf_model_id"] = "Qwen/Qwen3-235B-A22B"  # BF16: see _variants' note
    base["max_model_len"] = 40960
    prefix = args.lora_s3_prefix.rstrip("/")
    variants: list[dict] = []
    for key, sub in QWEN_4WAY_ARMS:
        if sub is None:
            variants.append({"key": key, "display": f"{key}-base"})
            continue
        container_path = f"/root/.cache/huggingface/lora/{key}"
        ec2.EC2_DEPLOY_SPECS[key] = {
            "hf_model_id": base["hf_model_id"],
            "tp": base.get("tp", 8),
            "max_model_len": base["max_model_len"],
            "vllm_args": [
                *base.get("vllm_args", []),
                "--enable-lora",
                "--max-lora-rank", str(args.lora_rank),
                # At rank >= 64 the per-GPU LoRA buffers no longer fit the
                # ~30 MiB of VRAM left after the BF16 235B weights load at
                # TP=8 (torch.OutOfMemoryError in _create_lora_modules,
                # root-caused live 2026-07-13: the rank-128 buffer wants
                # 128 MiB where the rank-16 pilot's 16 MiB just fit; same
                # OOM on vLLM v0.23.0 and v0.25.0). Fully-sharded LoRA
                # splits the buffers across TP ranks (~1/8th per GPU) and
                # is vLLM's recommended mode for high ranks anyway.
                *(["--fully-sharded-loras"] if args.lora_rank >= 64 else []),
                "--lora-modules", f"{key}={container_path}",
            ],
            "adapters": [{"name": key, "s3": f"{prefix}/qwen3-235b-a22b/{sub}",
                          "region": args.lora_region}],
        }
        variants.append({"key": key, "display": key})
    return variants


#: The CoT-SFT gate arms (notebooks/lean's CoT-recipe experiment, distinct
#: from the synthetic-pretraining `QWEN_4WAY_ARMS` above): ``(variant key,
#: adapter subprefix under <lora-s3-prefix>/qwen3-235b-a22b/)``. Must match
#: the "Sweep smoke arms" coordination constant exactly -- every other
#: package (the trainer, the harvester, the gate-power script) hard-codes
#: these same four arm identities and S3 subprefixes, so a rename here would
#: silently desync the sweep from the checkpoints it's supposed to load.
COT_SMOKE_ARMS: list[tuple[str, str | None]] = [
    ("qwen3-235b-a22b", None),
    ("qwen3-lean-real", "real-only"),
    ("qwen3-lean-bare-r128", "bare8k-r128"),
    ("qwen3-lean-cot-r128", "cot8k-r128"),
]


def _cot_smoke_variants(args, ec2) -> list[dict]:
    """The 4 CoT-gate arms as serve-swappable variants.

    Structurally identical to `_qwen_4way_variants` (same BF16-override /
    adapter-staging pattern -- see that function's docstring for why the
    base is served in BF16 rather than the trio's FP8), just iterating
    `COT_SMOKE_ARMS` instead of `QWEN_4WAY_ARMS`. Kept as a separate
    function (rather than parameterizing `_qwen_4way_variants` over an arms
    list) so each experiment's arm table and its variant-building code stay
    textually next to each other -- a reviewer diffing one experiment's arms
    never has to reason about the other's call site.
    """
    base = ec2.EC2_DEPLOY_SPECS["qwen3-235b-a22b"]
    base["hf_model_id"] = "Qwen/Qwen3-235B-A22B"  # BF16: see _variants' note
    base["max_model_len"] = 40960
    prefix = args.lora_s3_prefix.rstrip("/")
    variants: list[dict] = []
    for key, sub in COT_SMOKE_ARMS:
        if sub is None:
            variants.append({"key": key, "display": f"{key}-base"})
            continue
        container_path = f"/root/.cache/huggingface/lora/{key}"
        ec2.EC2_DEPLOY_SPECS[key] = {
            "hf_model_id": base["hf_model_id"],
            "tp": base.get("tp", 8),
            "max_model_len": base["max_model_len"],
            "vllm_args": [
                *base.get("vllm_args", []),
                "--enable-lora",
                "--max-lora-rank", str(args.lora_rank),
                # At rank >= 64 the per-GPU LoRA buffers no longer fit the
                # ~30 MiB of VRAM left after the BF16 235B weights load at
                # TP=8 (torch.OutOfMemoryError in _create_lora_modules,
                # root-caused live 2026-07-13: the rank-128 buffer wants
                # 128 MiB where the rank-16 pilot's 16 MiB just fit; same
                # OOM on vLLM v0.23.0 and v0.25.0). Fully-sharded LoRA
                # splits the buffers across TP ranks (~1/8th per GPU) and
                # is vLLM's recommended mode for high ranks anyway.
                *(["--fully-sharded-loras"] if args.lora_rank >= 64 else []),
                "--lora-modules", f"{key}={container_path}",
            ],
            "adapters": [{"name": key, "s3": f"{prefix}/qwen3-235b-a22b/{sub}",
                          "region": args.lora_region}],
        }
        variants.append({"key": key, "display": key})
    return variants


def _variants(args, ec2) -> list[dict]:
    """Resolve the model-variant list, registering LoRA deploy specs as needed.

    Base variants reuse the existing EC2_DEPLOY_SPECS entries. Each LoRA variant
    serves the S3-hosted adapter on top of the SAME FP8 base via vLLM's
    ``--enable-lora``: the ``adapters`` block tells the box to stage the adapter
    from S3 into ``/opt/hf-cache/lora/<lora_key>`` (mounted into the container at
    ``/root/.cache/huggingface/lora/<lora_key>``) before launch, and
    ``--lora-modules`` points vLLM at that local path. The spec key (which the
    client sends as ``model=``) is the lora-module name vLLM routes on.
    """
    variants: list[dict] = []
    prefix = args.lora_s3_prefix.rstrip("/")
    # Qwen3-235B-A22B-FP8 can't serve on vLLM v0.23.0: block-FP8 requires each
    # TP shard's gate/up output divisible by 128, but 1536/8=192 isn't (and TP=4
    # hangs at NVLink multicast init). Its config also caps context at 40960.
    # Serve BF16 instead -- no block-quant constraint at TP=8, it's the adapter's
    # native precision, and 235B BF16 (~470 GB) fits 8x80 GB. (405B/Nemotron stay
    # FP8: 405B BF16 would not fit.) Carry the precision difference as a caveat.
    _qwen = ec2.EC2_DEPLOY_SPECS.get("qwen3-235b-a22b")
    if _qwen is not None:
        _qwen["hf_model_id"] = "Qwen/Qwen3-235B-A22B"
        _qwen["max_model_len"] = 40960
    for base_key in TRIO:
        variants.append({"key": base_key, "display": f"{base_key}-base"})
        if args.no_lora:
            continue
        lora_key = f"{base_key}-lean-lora"
        base_spec = ec2.EC2_DEPLOY_SPECS[base_key]
        container_path = f"/root/.cache/huggingface/lora/{lora_key}"
        ec2.EC2_DEPLOY_SPECS[lora_key] = {
            "hf_model_id": base_spec["hf_model_id"],
            "tp": base_spec.get("tp", 8),
            "max_model_len": base_spec.get("max_model_len", 131072),
            "vllm_args": [
                *base_spec.get("vllm_args", []),
                "--enable-lora",
                "--max-lora-rank", str(args.lora_rank),
                "--lora-modules", f"{lora_key}={container_path}",
            ],
            # region: the box may land in a different region than the bucket
            # (spot capacity), so the S3 sync must target the bucket's region.
            "adapters": [{"name": lora_key, "s3": f"{prefix}/{base_key}", "region": args.lora_region}],
        }
        variants.append({"key": lora_key, "display": lora_key})
    return variants


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--phase", choices=list(PHASES), default="pilot")
    p.add_argument("--lora-s3-prefix", default=_ADAPTER_S3_PREFIX,
                   help="S3 prefix with <base_key>/adapter_model.safetensors for each model")
    p.add_argument("--no-lora", action="store_true", help="run base variants only (skip the LoRA arms)")
    # --qwen-4way and --cot-smoke both replace the trio variant list wholesale
    # with a different fixed arm table (QWEN_4WAY_ARMS / COT_SMOKE_ARMS) --
    # there is no sensible way to combine them, so a mutually exclusive group
    # makes the conflict an argparse-time SystemExit instead of a silent
    # "whichever `if` branch runs first wins" footgun.
    _arms = p.add_mutually_exclusive_group()
    _arms.add_argument("--qwen-4way", action="store_true",
                        help="sweep the Qwen synthetic-pretraining 4-way (base / real-only / "
                             "goedel+real / leannav+real) instead of the trio; run_name gains a "
                             "'qwen4way' infix so results never mix with trio runs")
    _arms.add_argument("--cot-smoke", action="store_true",
                        help="sweep the CoT-SFT gate arms (base / real-only / bare8k-r128 / "
                             "cot8k-r128, see COT_SMOKE_ARMS) instead of the trio -- pair with "
                             "--phase cot-gate")
    # default=None (not 16) so _resolve_config can tell "user didn't pass
    # --lora-rank" apart from "user explicitly passed --lora-rank 16" and
    # pick the right per-experiment default -- see _resolve_config.
    p.add_argument("--lora-rank", type=int, default=None,
                   help="--max-lora-rank; must be >= the served adapter's rank (16 for the trio "
                        "and real-only arms, 128 for the cot8k/bare8k arms; default resolved by "
                        "--cot-smoke -- see _resolve_config)")
    p.add_argument("--lora-region", default=os.environ.get("EC2_S3_CACHE_REGION", "us-west-2"),
                   help="AWS region of the adapter S3 bucket (the box may run in another region)")
    p.add_argument("--only", default=None,
                   help="comma-separated variant keys to restrict to (e.g. the Nemotron-first smoke)")
    p.add_argument("--limit", type=int, default=None,
                   help="override the phase's theorem count (e.g. --limit 1 for a warm-theorem smoke)")
    p.add_argument("--n-rollouts", type=int, default=None,
                   help="override the phase's rollout count (e.g. the expert-iteration harvest "
                        "pass, or a cot-gate re-run at the scripts/lean_gate_power.py-recommended N)")
    p.add_argument("--theorem-workers", type=int, default=None,
                   help="override parallel Dojo verifiers (local RAM-bound; lower if verification OOMs)")
    p.add_argument("--no-teardown", action="store_true", help="leave the instance up after the sweep")
    return p


def _resolve_config(args: argparse.Namespace) -> tuple[dict, list[dict], Path]:
    """Resolve parsed CLI `args` into a sweep config, variant list, and run_dir.

    Pulled out of `main` so the CLI-flag -> sweep-config mapping (phase
    lookup, the ``--limit``/``--theorem-workers``/``--n-rollouts`` overrides,
    ``--qwen-4way``/``--cot-smoke`` arm-list selection, the ``--lora-rank``
    default, and ``--only`` filtering) is unit-testable in isolation from
    `main`'s remaining body -- provisioning an EC2 box, serving each variant,
    and running the (expensive, network-dependent) sweep itself -- none of
    which can run under the offline test suite.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI args from `build_parser()`. Mutated in place: if
        ``args.lora_rank`` is `None` (the argparse default -- see
        `build_parser`), it is resolved here to 16 (the trio/real-only
        adapters' native rank) or 128 (the cot8k/bare8k arms' rank, when
        ``--cot-smoke`` is set) and written back onto `args`, since
        `_variants`/`_qwen_4way_variants`/`_cot_smoke_variants` all read
        ``args.lora_rank`` directly for their ``--max-lora-rank`` value.

    Returns
    -------
    (config, variants, run_dir) : (dict, list[dict], pathlib.Path)
        `config` -- the resolved sweep config (the phase's base dict plus
        any ``--limit``/``--theorem-workers``/``--n-rollouts`` overrides;
        ``models`` is NOT yet populated -- `main` fills that in per-variant
        inside its serve loop). `variants` -- the resolved model-variant
        list to serve-swap through, already filtered by ``--only`` if given.
        `run_dir` -- ``runner.results_root() / "runs" / config["run_name"]``.

    Raises
    ------
    SystemExit
        If ``--only`` is given but matches no variant of the resolved
        variant list.

    Notes
    -----
    Registers LoRA variant specs into ``ec2.EC2_DEPLOY_SPECS`` as a side
    effect (via `_variants`/`_qwen_4way_variants`/`_cot_smoke_variants`) --
    an in-memory dict mutation, not I/O or a network call, so this stays
    safe to call repeatedly (including from tests) without AWS credentials.
    """
    from smolbench.evals import ec2
    from smolbench.deduction.lean import runner

    if args.lora_rank is None:
        # --max-lora-rank is a serving CEILING, not the adapter's actual
        # rank: vLLM sizes its LoRA workspace to the ceiling regardless of
        # what any given adapter was trained at, so serving a rank-16
        # adapter (the trio/real-only arms) under a rank-128 ceiling is
        # harmless -- it just reserves workspace the r16 adapter doesn't
        # use. The cot8k/bare8k arms, however, ARE trained at rank 128 (see
        # the coordination constants) and need the ceiling to actually
        # cover their rank. Default to 128 only when --cot-smoke selected
        # that arm list; the trio/qwen-4way arms keep their historical
        # rank-16 default.
        args.lora_rank = 128 if args.cot_smoke else 16

    config = dict(PHASES[args.phase])
    # Override the result run-name (dir under notebooks/lean/results/runs/) so a
    # different base set (e.g. the all-MoE LEAN_TRIO) writes to its own dir rather
    # than mixing into the default trio run.
    if os.environ.get("LEAN_RUN_NAME"):
        config["run_name"] = os.environ["LEAN_RUN_NAME"]
    if args.limit is not None:
        # Override the phase's theorem count (seeded sample); e.g. --limit 1 smoke.
        config["theorems"] = {**config["theorems"], "limit": args.limit, "seed": config["theorems"].get("seed", 1776)}
    if args.theorem_workers is not None:
        config["theorem_workers"] = args.theorem_workers
    if args.n_rollouts is not None:
        # Override the phase's rollout count (e.g. expert-iteration harvest
        # passes, or a gate re-run at the power-analysis-recommended N).
        config["n_rollouts"] = args.n_rollouts

    if args.qwen_4way:
        config["run_name"] = config["run_name"].replace("trio", "qwen4way")
        variants = _qwen_4way_variants(args, ec2)
    elif args.cot_smoke:
        variants = _cot_smoke_variants(args, ec2)
    else:
        variants = _variants(args, ec2)

    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        # Fix: capture the RESOLVED variant list's own keys before filtering
        # -- not the raw `TRIO` constant, which only names the base trio and
        # is flatly wrong here under --qwen-4way/--cot-smoke (whose variant
        # keys are qwen3-lean-*/-base names, none of which are in TRIO at
        # all), and is incomplete even in the default arm list (`_variants`
        # also emits each base's `<key>-lean-lora` variant, which TRIO alone
        # doesn't name either).
        available_keys = [v["key"] for v in variants]
        variants = [v for v in variants if v["key"] in wanted]
        if not variants:
            raise SystemExit(f"--only {sorted(wanted)} matched no variant of {available_keys}")

    run_dir = runner.results_root() / "runs" / config["run_name"]
    return config, variants, run_dir


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # The sweep verifies proofs via lean_dojo, which shells out to `lake`/`elan`.
    # Ensure the elan toolchain is on PATH (installed at ~/.elan/bin but often not
    # exported) or every theorem SANITY-FAILs with "lake: command not found".
    elan_bin = Path.home() / ".elan" / "bin"
    if elan_bin.is_dir() and str(elan_bin) not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = f"{elan_bin}{os.pathsep}{os.environ.get('PATH', '')}"

    config, variants, run_dir = _resolve_config(args)

    from smolbench.evals import ec2
    from smolbench.deduction.lean import runner

    if args.no_lora:
        print("note: --no-lora -> BASE variants only", flush=True)

    ec2.provision_spot_instance()
    failures: list[tuple[str, str]] = []
    try:
        for v in variants:
            cfg = {**config, "models": [{"provider": "ec2", "model": v["key"], "display_name": v["display"]}]}
            print(f"=== {args.phase}: serving {v['key']} -> sweep display={v['display']} ===", flush=True)
            # Isolate each variant: a serve/sweep failure (e.g. one arm that vLLM
            # can't load) is logged and skipped so the rest of the pass still runs
            # and produces data, instead of aborting the whole (expensive) sweep.
            try:
                with ec2.serve_model(v["key"]):
                    runner.sweep(cfg, run_dir)
            except Exception as exc:  # noqa: BLE001
                msg = (str(exc).splitlines() or [type(exc).__name__])[0][:200]
                failures.append((v["key"], msg))
                print(f"!! {v['key']} FAILED — skipping: {type(exc).__name__}: {msg}", flush=True)
        runner.write_run_analysis(run_dir)
        if failures:
            print(f"note: {len(failures)}/{len(variants)} variant(s) failed: {failures}", flush=True)
        print(f"done: {args.phase} sweep -> {run_dir}", flush=True)
    finally:
        if not args.no_teardown:
            ec2.shutdown_instance()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
