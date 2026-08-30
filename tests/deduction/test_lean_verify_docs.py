"""Text-only guarantees about the lean-interact verifier backend's packaging and docs.

Deliberately a SEPARATE module from ``test_lean_repl_verifier.py``, and
deliberately importing nothing from `lean_interact` or
`smolbench.deduction.lean.verify`.

That sibling module opens with ``pytest.importorskip("lean_interact")``, so the
whole file — including any packaging check placed in it — vanishes silently the
moment the package is missing from the venv. Which is exactly the scenario these
tests exist to catch: ``uv.lock`` has not yet been regenerated since
``lean-interact`` was added to pyproject's ``lean`` extra, so a
``uv sync --all-extras`` resolves from the stale lock and prunes it. A guarantee
that disappears under the failure it guards against is not a guarantee, so these
run unconditionally.
"""

from __future__ import annotations

import re

from tests._paths import NOTEBOOKS, REPO_ROOT


def _lean_extra() -> str:
    """The body of pyproject's ``lean = [...]`` optional-dependency list."""
    text = (REPO_ROOT / "pyproject.toml").read_text()
    match = re.search(r"^lean = \[(.*?)^\]", text, re.S | re.M)
    assert match, "pyproject.toml has no `lean` extra"
    return match.group(1)


def test_pyproject_lean_extra_declares_lean_interact():
    """Without this declaration, ``uv sync --all-extras`` prunes the verifier's backend."""
    assert "lean-interact" in _lean_extra()


def test_pyproject_lean_extra_still_declares_lean_dojo():
    """`lean-dojo` is NOT dropped by this change.

    Only VERIFICATION stopped using it; `smolbench.deduction.lean.premises`
    still slices premise source out of a LeanDojo-traced checkout, and corpus
    tracing still needs it. Removing it here would break those silently.
    """
    assert "lean-dojo" in _lean_extra()


def test_readme_documents_the_mathlib_root_env_var():
    text = (NOTEBOOKS / "deduction" / "README.md").read_text()
    assert "SMOLBENCH_MATHLIB_ROOT" in text
    assert "lean-interact" in text


def test_readme_keeps_the_traced_cache_claim_narrow():
    """Verification stopped needing ``~/.cache/lean_dojo``; `premises.py` did not.

    An over-broad "the LeanDojo cache is obsolete" would send an operator to
    delete a tree that hint/noise context rendering still reads.
    """
    text = (NOTEBOOKS / "deduction" / "README.md").read_text()
    assert "premises" in text and "~/.cache/lean_dojo/" in text


def test_smoke_skill_documents_the_lean_interact_backend():
    skill = REPO_ROOT / ".claude" / "skills" / "run-smolbench"
    assert "lean-interact" in (skill / "SKILL.md").read_text()
    assert "lean_interact" in (skill / "lean_smoke.sh").read_text()


def test_smoke_skill_tier0_check_cannot_pass_vacuously():
    """Tier 0 asserts the generation path does not PULL IN the Lean backend.

    A bare ``import smolbench.deduction.lean.runner`` would pass even if runner
    grew a hard dependency on `lean_interact`, because `lean_interact` is
    installed in the project venv. The check must therefore assert on
    ``sys.modules``, not merely that the import succeeded.
    """
    script = (REPO_ROOT / ".claude" / "skills" / "run-smolbench" / "lean_smoke.sh").read_text()
    assert "sys.modules" in script
    assert "'lean_interact' not in sys.modules" in script


def test_smoke_skill_replay_tier_refuses_without_a_mathlib_root():
    script = (REPO_ROOT / ".claude" / "skills" / "run-smolbench" / "lean_smoke.sh").read_text()
    assert "SMOLBENCH_MATHLIB_ROOT" in script
    assert "need_mathlib_root" in script
