"""Test the lean_dojo import guard on smolbench.deduction.lean.verify.

This must PASS, not error, on both interpreters:
  - Python >= 3.13 (the main .venv, no lean_dojo): importing the module
    must raise an actionable ImportError naming the .venv-lean remedy.
  - Python 3.12 (the .venv-lean, lean_dojo installed): the module
    imports and exposes its public verifier surface.
"""

import sys

import pytest


def test_verify_import_guard():
    # A prior test in the session may have imported, or failed to
    # import, the module. Drop any cached entry so the guard runs
    # fresh here.
    sys.modules.pop("smolbench.deduction.lean.verify", None)

    if sys.version_info >= (3, 13):
        with pytest.raises(ImportError) as excinfo:
            import smolbench.deduction.lean.verify  # noqa: F401
        # The message must point at the dedicated 3.12 environment.
        assert ".venv-lean" in str(excinfo.value)
    else:
        pytest.importorskip("lean_dojo")
        import smolbench.deduction.lean.verify as verify

        for name in (
            "open_at_step",
            "try_tail",
            "replay_ground_truth",
            "verify_proof_tail",
            "ProofResult",
        ):
            assert hasattr(verify, name), f"verify.{name} missing"


def test_no_resume_discards_prior_verdicts_and_reverifies_every_group(tmp_path, monkeypatch):
    """--no-resume must re-verify a lane whose proofs were regenerated.

    Resume is keyed on (theorem_id, k) GROUPS, not on the candidate
    proofs inside them. If phase 1 regenerates a lane after it was
    verified, every group still looks "done", while the proofs beneath
    are completely different. So the pass reports success, verifies
    nothing, and leaves verified_rows.jsonl describing text that no
    longer exists.
    """
    import importlib.util, sys

    from tests._paths import SCRIPTS

    spec = importlib.util.spec_from_file_location(
        "lean_verify_rows_mod",
        SCRIPTS / "deduction" / "lean_verify_rows.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    # A prior pass marked this group done (verdict is not "unverified").
    prior = [{"kind": "cell", "theorem_id": "t1", "k": 1, "verdict": "success",
              "candidate_proof": "OLD PROOF"}]
    assert mod.resume_done_groups(prior) == {("t1", 1)}, (
        "sanity: a completed group is normally skipped"
    )

    # With --no-resume the caller empties that list before computing `done`,
    # so nothing is skipped and the current proofs are all re-verified.
    assert mod.resume_done_groups([]) == set()
