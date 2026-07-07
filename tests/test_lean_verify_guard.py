"""The lean_dojo import guard on smolbench.lean.verify.

Must PASS (not error) on both interpreters:
  - Python >= 3.13 (the main .venv, no lean_dojo): importing the module must
    raise an actionable ImportError naming the .venv-lean remedy.
  - Python 3.12 (the .venv-lean, lean_dojo installed): the module imports and
    exposes its public verifier surface.
"""

import sys

import pytest


def test_verify_import_guard():
    # A prior test in the session may have imported (or failed to import) the
    # module; drop any cached entry so the guard runs fresh here.
    sys.modules.pop("smolbench.lean.verify", None)

    if sys.version_info >= (3, 13):
        with pytest.raises(ImportError) as excinfo:
            import smolbench.lean.verify  # noqa: F401
        # The message must point at the dedicated 3.12 environment.
        assert ".venv-lean" in str(excinfo.value)
    else:
        pytest.importorskip("lean_dojo")
        import smolbench.lean.verify as verify

        for name in (
            "open_at_step",
            "try_tail",
            "replay_ground_truth",
            "verify_proof_tail",
            "ProofResult",
        ):
            assert hasattr(verify, name), f"verify.{name} missing"
