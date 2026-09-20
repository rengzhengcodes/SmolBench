"""Packaging and documentation contracts for the lean-interact verifier.

They run without `lean_interact` so a missing package cannot skip its guard.
"""

# pylint: disable=missing-function-docstring

from __future__ import annotations

import re

from tests._paths import NOTEBOOKS, REPO_ROOT


def _lean_extra() -> str:
    """The body of pyproject's ``lean = [...]`` optional-dependency list."""
    text = (REPO_ROOT / "pyproject.toml").read_text()
    match = re.search(r"^lean = \[(.*?)^\]", text, re.S | re.M)
    assert match, "pyproject.toml has no `lean` extra"
    return match.group(1)


def test_pyproject_lean_extra_declares_lean_interact() -> None:
    """Without this declaration, ``uv sync --all-extras`` prunes the verifier's backend."""
    assert "lean-interact" in _lean_extra()


def test_pyproject_lean_extra_still_declares_lean_dojo() -> None:
    """Keep `lean-dojo`: premises and corpus tracing still require it."""
    assert "lean-dojo" in _lean_extra()


def test_verify_module_has_no_lean_dojo_import() -> None:
    """Read `verify.py` directly so the retired-backend guard always runs."""
    src = (REPO_ROOT / "smolbench" / "deduction" / "lean" / "verify.py").read_text()
    assert src, "verify.py not found at the expected path"
    assert "import lean_dojo" not in src
    assert "from lean_dojo" not in src


def test_readme_documents_the_mathlib_root_env_var() -> None:
    text = (NOTEBOOKS / "deduction" / "README.md").read_text()
    assert "SMOLBENCH_MATHLIB_ROOT" in text
    assert "lean-interact" in text


def test_readme_keeps_the_traced_cache_claim_narrow() -> None:
    """`premises.py` still needs the traced cache despite verification changes."""
    text = (NOTEBOOKS / "deduction" / "README.md").read_text()
    assert "~/.cache/lean_dojo/" in text
    idx = text.index("That cache is NOT obsolete")
    paragraph = text[idx : text.index("\n\n", idx)]
    for token in (
        "premises",
        "_traced_root",
        "hint/noise",
        "Only VERIFICATION has stopped depending on it.",
    ):
        assert token in paragraph, (
            f"{token!r} missing from the traced-cache narrowing paragraph; the "
            "claim must stay scoped to verification"
        )


def test_smoke_skill_documents_the_lean_interact_backend() -> None:
    skill = REPO_ROOT / ".claude" / "skills" / "run-smolbench"
    assert "lean-interact" in (skill / "SKILL.md").read_text()
    assert "lean_interact" in (skill / "lean_smoke.sh").read_text()


def test_smoke_skill_tier0_check_cannot_pass_vacuously() -> None:
    """Tier 0 must inspect `sys.modules`, not merely import `runner`."""
    script = (
        REPO_ROOT / ".claude" / "skills" / "run-smolbench" / "lean_smoke.sh"
    ).read_text()
    assert "sys.modules" in script
    assert "'lean_interact' not in sys.modules" in script


def test_smoke_skill_replay_tier_refuses_without_a_mathlib_root() -> None:
    script = (
        REPO_ROOT / ".claude" / "skills" / "run-smolbench" / "lean_smoke.sh"
    ).read_text()
    assert "SMOLBENCH_MATHLIB_ROOT" in script
    assert "need_mathlib_root" in script
