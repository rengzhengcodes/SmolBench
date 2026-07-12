"""Offline tests for the CoT-recipe training pipeline (Package C of the
2026-07-12 CoT SFT plan): the new trainer scheduler flags in
``scripts/lean_lora_sft.py``, their threading through
``scripts/lean_train_ec2.py``, the OPTIONAL_DATASETS upload/warn split, and
the ``scripts/lean_cot_recipe.sh`` orchestrator.

Everything here runs with NO torch/peft/transformers/trl and NO AWS
credentials/network, on both venvs (``.venv``: no torch at all; ``.venv-lean``:
has lean_dojo but not the training stack either). ``lean_lora_sft.py`` defers
its heavy imports into ``main()`` (see its module docstring), so importing
``build_parser`` and the new ``_resolve_sft_kwargs`` helper is safe everywhere
-- the version-guard logic itself is exercised against a FAKE ``sft_fields``
set (a stand-in for ``{f.name for f in dataclasses.fields(SFTConfig)}``)
rather than a real trl install, per the plan's "monkeypatch a fake
SFTConfig-like dataclass" guidance.

The shell orchestrator is exercised two ways: ``bash -n`` (pure syntax check,
no execution) and a live ``DRYRUN=1`` run via subprocess (the script's own
off-box smoke mode -- see its header comment -- which never touches
/opt/train, AWS, or a GPU).
"""

from __future__ import annotations

import os
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import lean_lora_sft as sft  # noqa: E402  (needs the sys.path insert above)
import lean_train_ec2 as lt  # noqa: E402

RECIPE_SH = _SCRIPTS / "lean_cot_recipe.sh"


# ---------------------------------------------------------------------------
# lean_lora_sft.py: --lr-scheduler-type / --warmup-ratio parsing
# ---------------------------------------------------------------------------


def test_sft_parser_accepts_scheduler_and_warmup_flags():
    ns = sft.build_parser().parse_args(
        ["--base-model", "m", "--dataset", "d", "--output-dir", "o",
         "--lr-scheduler-type", "cosine", "--warmup-ratio", "0.03"]
    )
    assert ns.lr_scheduler_type == "cosine"
    assert ns.warmup_ratio == pytest.approx(0.03)


def test_sft_parser_defaults_are_none():
    """Default None means 'leave trl's own default alone' -- distinct from
    a real scheduler choice, and must not silently become a string/float."""
    ns = sft.build_parser().parse_args(["--base-model", "m", "--dataset", "d", "--output-dir", "o"])
    assert ns.lr_scheduler_type is None
    assert ns.warmup_ratio is None


# ---------------------------------------------------------------------------
# lean_lora_sft.py: _resolve_sft_kwargs -- the SFTConfig version guard
# ---------------------------------------------------------------------------


def _args(lr_scheduler_type=None, warmup_ratio=None, max_seq_len=4096):
    return Namespace(lr_scheduler_type=lr_scheduler_type, warmup_ratio=warmup_ratio,
                      max_seq_len=max_seq_len)


def test_resolve_sft_kwargs_modern_trl_gets_everything():
    """A modern SFTConfig (fake field set standing in for a real
    dataclasses.fields(SFTConfig) probe) exposes every optional field, and
    both flags were explicitly set -> all pass through."""
    fields = {"max_length", "loss_type", "lr_scheduler_type", "warmup_ratio"}
    got = sft._resolve_sft_kwargs(_args("cosine", 0.03), fields)
    assert got == {
        "max_length": 4096, "loss_type": "nll",
        "lr_scheduler_type": "cosine", "warmup_ratio": 0.03,
    }


def test_resolve_sft_kwargs_old_trl_drops_everything_optional():
    """An old SFTConfig (pre max_length/loss_type/scheduler rename) must
    fall back to max_seq_length and omit every field it doesn't declare --
    even though the caller explicitly asked for a scheduler/warmup -- so
    SFTConfig(**kwargs) never raises an unknown-kwarg TypeError."""
    fields = {"max_seq_length"}
    got = sft._resolve_sft_kwargs(_args("cosine", 0.03), fields)
    assert got == {"max_seq_length": 4096}


def test_resolve_sft_kwargs_unset_flags_omitted_even_when_field_exists():
    """CLI defaults (None) must be omitted even on a modern SFTConfig that
    COULD accept them -- None means 'don't touch trl's own default', not
    'pass None explicitly'."""
    fields = {"max_length", "loss_type", "lr_scheduler_type", "warmup_ratio"}
    got = sft._resolve_sft_kwargs(_args(), fields)
    assert got == {"max_length": 4096, "loss_type": "nll"}
    assert "lr_scheduler_type" not in got and "warmup_ratio" not in got


def test_resolve_sft_kwargs_partial_field_set_is_independent_per_flag():
    """A field set with scheduler but not warmup (or vice versa) must gate
    each flag independently, not all-or-nothing."""
    fields = {"max_length", "lr_scheduler_type"}  # no loss_type, no warmup_ratio
    got = sft._resolve_sft_kwargs(_args("linear", 0.1), fields)
    assert got == {"max_length": 4096, "lr_scheduler_type": "linear"}


# ---------------------------------------------------------------------------
# lean_train_ec2.py: --epochs / --lr-scheduler-type / --warmup-ratio parsing
# ---------------------------------------------------------------------------


def test_train_ec2_parser_accepts_new_flags():
    ns = lt.build_parser().parse_args(
        ["train", "--model", "qwen3-235b-a22b", "--epochs", "2",
         "--lr-scheduler-type", "cosine", "--warmup-ratio", "0.03"]
    )
    assert ns.epochs == pytest.approx(2.0)
    assert ns.lr_scheduler_type == "cosine"
    assert ns.warmup_ratio == pytest.approx(0.03)


def test_train_ec2_parser_defaults():
    ns = lt.build_parser().parse_args(["train", "--model", "qwen3-235b-a22b"])
    assert ns.epochs == pytest.approx(1.0)
    assert ns.lr_scheduler_type is None
    assert ns.warmup_ratio is None


def test_dataset_file_choices_include_optional_cot_sets():
    ns = lt.build_parser().parse_args(
        ["train", "--model", "qwen3-235b-a22b", "--dataset-file", "cot_stepk1_think_8k.jsonl"]
    )
    assert ns.dataset_file == "cot_stepk1_think_8k.jsonl"
    with pytest.raises(SystemExit):
        lt.build_parser().parse_args(
            ["train", "--model", "qwen3-235b-a22b", "--dataset-file", "not_a_real_dataset.jsonl"]
        )


# ---------------------------------------------------------------------------
# lean_train_ec2.py: _train_cmd threading (emit-when-non-default)
# ---------------------------------------------------------------------------


def _train_args(**overrides):
    """Mirrors tests/test_lean_capacity_blocks.py's `_train_args` builder,
    extended with the new flags this package added to `_add_train_args`."""
    args = dict(model="qwen3-235b-a22b", attach=False, checkpoint_dest="hub",
                s3_prefix="lean-train-checkpoints", org="rengz",
                dataset_file=lt.DEFAULT_DATASET, init_adapter_s3=None, out_name="",
                cap=8000, full=False, max_steps=-1, save_steps=200, lora_r=128,
                lora_alpha=256, batch_size=1, grad_accum=16, seed=1776,
                full_determinism=False, poll=1, timeout=1,
                epochs=1.0, lr_scheduler_type=None, warmup_ratio=None)
    args.update(overrides)
    return Namespace(**args)


def test_train_cmd_omits_default_epochs_and_unset_scheduler():
    cmd = lt._train_cmd(lt._TRIO_BY_KEY["qwen3-235b-a22b"], _train_args())
    assert "--epochs" not in cmd
    assert "--lr-scheduler-type" not in cmd
    assert "--warmup-ratio" not in cmd


def test_train_cmd_includes_epochs_and_scheduler_when_set():
    cmd = lt._train_cmd(
        lt._TRIO_BY_KEY["qwen3-235b-a22b"],
        _train_args(epochs=2.0, lr_scheduler_type="cosine", warmup_ratio=0.03),
    )
    assert "--epochs 2.0" in cmd
    assert "--lr-scheduler-type cosine" in cmd
    assert "--warmup-ratio 0.03" in cmd


def test_train_cmd_epochs_one_point_zero_explicit_is_still_default():
    """1.0 is the CLI default regardless of whether argparse filled it in or
    the caller passed --epochs 1.0 explicitly -- both must omit the flag
    (the trainer's own default already matches)."""
    cmd = lt._train_cmd(lt._TRIO_BY_KEY["qwen3-235b-a22b"], _train_args(epochs=1.0))
    assert "--epochs" not in cmd


def test_train_cmd_tolerates_namespace_missing_new_attrs():
    """A hand-built Namespace that predates these flags (e.g.
    tests/test_lean_capacity_blocks.py's own `_train_args`, which this
    package must not break) must not raise AttributeError -- _train_cmd
    falls back to the CLI defaults via getattr."""
    args = _train_args()
    del args.epochs
    del args.lr_scheduler_type
    del args.warmup_ratio
    cmd = lt._train_cmd(lt._TRIO_BY_KEY["qwen3-235b-a22b"], args)
    assert "--epochs" not in cmd
    assert "--lr-scheduler-type" not in cmd
    assert "--warmup-ratio" not in cmd


# ---------------------------------------------------------------------------
# lean_train_ec2.py: OPTIONAL_DATASETS upload/warn split (pure functions)
# ---------------------------------------------------------------------------


def test_optional_datasets_registered_with_coordination_constant_names():
    """These four names are a cross-package coordination constant (shared
    with the annotation/CoT-recipe packages) -- pin them exactly.
    ``cot_stepk1_bare_8k.jsonl`` is the paired bare-control sibling
    annotate_lean_cot.py now emits alongside ``cot_stepk1_think_8k.jsonl``
    (Fix 1 / paired attribution control)."""
    assert set(lt.OPTIONAL_DATASETS) == {
        "cot_stepk1_think_8k.jsonl",
        "cot_stepk1_think_full.jsonl",
        "cot_stepk1_fenced_full.jsonl",
        "cot_stepk1_bare_8k.jsonl",
    }
    assert all(p.parent == lt._SFT_DIR for p in lt.OPTIONAL_DATASETS.values())


def test_existing_and_missing_optional_datasets_partition_the_dict(tmp_path, monkeypatch):
    present = tmp_path / "cot_stepk1_think_8k.jsonl"
    present.write_text("{}\n")
    absent1 = tmp_path / "cot_stepk1_think_full.jsonl"
    absent2 = tmp_path / "cot_stepk1_fenced_full.jsonl"
    monkeypatch.setattr(lt, "OPTIONAL_DATASETS", {
        "cot_stepk1_think_8k.jsonl": present,
        "cot_stepk1_think_full.jsonl": absent1,
        "cot_stepk1_fenced_full.jsonl": absent2,
    })
    assert lt._existing_optional_datasets() == [("cot_stepk1_think_8k.jsonl", present)]
    assert set(lt._missing_optional_datasets()) == {
        "cot_stepk1_think_full.jsonl", "cot_stepk1_fenced_full.jsonl",
    }


def test_existing_and_missing_optional_datasets_all_present(tmp_path, monkeypatch):
    paths = {}
    for name in ("a.jsonl", "b.jsonl"):
        p = tmp_path / name
        p.write_text("{}\n")
        paths[name] = p
    monkeypatch.setattr(lt, "OPTIONAL_DATASETS", paths)
    assert lt._missing_optional_datasets() == []
    assert len(lt._existing_optional_datasets()) == 2


def test_cot_orchestrator_constant_points_at_the_new_script():
    assert lt.COT_ORCHESTRATOR == RECIPE_SH
    assert lt.COT_ORCHESTRATOR.name == "lean_cot_recipe.sh"


# ---------------------------------------------------------------------------
# scripts/lean_cot_recipe.sh: syntax + DRYRUN=1 smoke
# ---------------------------------------------------------------------------


def test_recipe_script_exists_and_is_executable():
    assert RECIPE_SH.exists()
    assert RECIPE_SH.stat().st_mode & 0o111, "lean_cot_recipe.sh must be executable (chmod +x)"


def test_recipe_script_bash_syntax_ok():
    proc = subprocess.run(["bash", "-n", str(RECIPE_SH)], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr


def _run_dryrun(env_extra: dict) -> subprocess.CompletedProcess:
    env = os.environ | {"DRYRUN": "1"} | env_extra
    return subprocess.run(["bash", str(RECIPE_SH)], env=env, capture_output=True, text=True, timeout=30)


def test_dryrun_smoke_mode_prints_both_stages_with_right_flags():
    """Default (FULL unset): bare8k-r128 then cot8k-r128, both Qwen,
    r128/cosine/2-epoch, in that order -- and nothing is executed (no
    aws/python subprocess actually runs; DRYRUN just echoes).

    Fix 1 (paired bare-control dataset): bare8k-r128 now trains on
    cot_stepk1_bare_8k.jsonl -- annotate_lean_cot.py's paired bare-control
    sibling of cot_stepk1_think_8k.jsonl -- with cap 0 (the file IS already
    exactly the paired 8k set), not the old novel_premises_train_stepk1_
    decontam.jsonl + --max-examples 8000 (an INDEPENDENTLY seeded ~8k
    sample, ~86% disjoint from cot8k-r128's own sample -- see Fix 1's
    problem statement). So the two arms' --max-examples now differ by
    design; only cot8k-r128 keeps the 8000 cap.
    """
    proc = _run_dryrun({})
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout

    bare_idx = out.index("bare8k-r128")
    cot_idx = out.index("cot8k-r128")
    assert bare_idx < cot_idx  # bare (control) runs before cot (treatment)

    assert "qwen3-235b-a22b/bare8k-r128" in out
    assert "cot_stepk1_bare_8k.jsonl" in out
    assert "novel_premises_train_stepk1_decontam.jsonl" not in out  # no longer the bare-arm dataset
    assert "qwen3-235b-a22b/cot8k-r128" in out
    assert "cot_stepk1_think_8k.jsonl" in out

    bare_line = next(l for l in out.splitlines() if "bare8k-r128:" in l)
    cot_line = next(l for l in out.splitlines() if "cot8k-r128:" in l)
    for line in (bare_line, cot_line):
        assert "--lora-r 128" in line
        assert "--lora-alpha 256" in line
        assert "--epochs 2" in line
        assert "--lr-scheduler-type cosine" in line
        assert "--warmup-ratio 0.03" in line
        assert "--target-modules q_proj,k_proj,v_proj,o_proj" in line
        assert "--moe-unquantized" in line
    assert "cot_stepk1_bare_8k.jsonl" in bare_line
    assert "--max-examples 0" in bare_line  # already exactly the paired 8k -- no further subsampling
    assert "cot_stepk1_think_8k.jsonl" in cot_line
    assert "--max-examples 8000" in cot_line
    assert "COT_RECIPE_SMOKE_DONE" in out
    assert "shutdown" not in out  # DRYRUN never self-halts


def test_dryrun_full_mode_prints_trio_stages():
    proc = _run_dryrun({"FULL": "1"})
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout

    assert "qwen3-235b-a22b/cot-full-r128" in out
    assert "cot_stepk1_think_full.jsonl" in out
    assert "llama-31-405b/cot-full-r128" in out
    assert "nemotron-ultra-253b/cot-full-r128" in out
    assert "cot_stepk1_fenced_full.jsonl" in out.replace("\n", " ")  # used by both dense arms

    # Dense arms get attn+MLP target modules; Nemotron additionally needs
    # trust_remote_code for its NAS modeling code; Qwen stays attention-only.
    lines = {name: next(l for l in out.splitlines() if f"{name}/cot-full-r128:" in l)
             for name in ("qwen3-235b-a22b", "llama-31-405b", "nemotron-ultra-253b")}
    assert "--moe-unquantized" in lines["qwen3-235b-a22b"]
    assert "gate_proj,up_proj,down_proj" in lines["llama-31-405b"]
    assert "--trust-remote-code" not in lines["llama-31-405b"]
    assert "gate_proj,up_proj,down_proj" in lines["nemotron-ultra-253b"]
    assert "--trust-remote-code" in lines["nemotron-ultra-253b"]
    assert all("--max-examples 0" in l for l in lines.values())  # cap 0 = all rows
    assert "COT_RECIPE_FULL_DONE" in out


def test_dryrun_never_touches_filesystem_or_aws(tmp_path):
    """DRYRUN=1 must be safe to run with no /opt/train tree, no HF_TOKEN, and
    no aws/python on PATH doing anything -- it only prints. Run from a tmp
    cwd with a minimal PATH (just enough for bash builtins + `date`/`echo`)
    so a stray real `python`/`aws` invocation would fail loudly instead of
    silently succeeding."""
    env = {"DRYRUN": "1", "PATH": "/usr/bin:/bin"}
    proc = subprocess.run(["bash", str(RECIPE_SH)], env=env, cwd=str(tmp_path),
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert list(tmp_path.iterdir()) == []  # nothing written under the tmp cwd
