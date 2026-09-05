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


def test_verify_module_has_no_lean_dojo_import():
    """13-19: the retired backend is gone from `verify.py`'s SOURCE, checked here.

    Moved out of `test_lean_repl_verifier.py`, which opens with
    ``pytest.importorskip("lean_interact")``: the check that a `lean_dojo`
    import has not crept back would have vanished exactly when the packaging
    failure this module exists to catch occurs. Reads the file by PATH rather
    than importing it, so it needs neither `lean_interact` nor a Lean
    toolchain. The runtime half -- that a cold import does not pull `lean_dojo`
    in transitively -- stays in that sibling module, which can actually import
    the verifier.
    """
    src = (REPO_ROOT / "smolbench" / "deduction" / "lean" / "verify.py").read_text()
    assert src, "verify.py not found at the expected path"
    assert "import lean_dojo" not in src
    assert "from lean_dojo" not in src


def test_readme_documents_the_mathlib_root_env_var():
    text = (NOTEBOOKS / "deduction" / "README.md").read_text()
    assert "SMOLBENCH_MATHLIB_ROOT" in text
    assert "lean-interact" in text


def test_readme_keeps_the_traced_cache_claim_narrow():
    """Verification stopped needing ``~/.cache/lean_dojo``; `premises.py` did not.

    An over-broad "the LeanDojo cache is obsolete" would send an operator to
    delete a tree that hint/noise context rendering still reads.

    13-20: this used to assert only ``"premises" in text and
    "~/.cache/lean_dojo/" in text``. Both substrings occur a dozen times
    apiece across the README for unrelated reasons, so the guard passed on
    prose saying the OPPOSITE of what it claims to protect (verified: an
    over-broad "the cache is obsolete" sentence still gave 7 passed). It now
    anchors on the narrowing SENTENCE itself, in one paragraph, and on the
    named function that keeps the claim narrow, so an edit that widens the
    claim has to delete something this test names.
    """
    text = (NOTEBOOKS / "deduction" / "README.md").read_text()
    assert "~/.cache/lean_dojo/" in text
    idx = text.index("That cache is NOT obsolete")
    paragraph = text[idx:text.index("\n\n", idx)]
    for token in ("premises", "_traced_root", "hint/noise",
                  "Only VERIFICATION has stopped depending on it."):
        assert token in paragraph, (
            f"{token!r} missing from the traced-cache narrowing paragraph; the "
            "claim must stay scoped to verification"
        )


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
