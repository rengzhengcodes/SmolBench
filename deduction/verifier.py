"""
Minimal Lean proof verifier backed by LeanDojo Dojo.

Accepts a proof as either a single tactic string or a list of tactics; feeds
each through `dojo.run_tac` in sequence. ok=True iff some intermediate state
reaches `ProofFinished` and no tactic raised an error.

Known limitation: Dojo's tactic parser expects *one* tactic per `run_tac` call.
Multi-line tactics (e.g. `have f : T := <value-on-next-line>`) are treated as
one string by LeanDojo's traced_tactics (with embedded `\n`), so passing the
list directly works. A raw multi-tactic blob from an LLM needs to be split
upstream (caller's responsibility to produce the list).

Known replay gap: not every theorem's canonical proof replays cleanly through
Dojo even when submitted tactic-by-tactic — published LeanDojo replay rates
are ~80-90%. Pre-filter samples with `ground_truth_passes()` before using them
as pilot targets, so we're not measuring against a ceiling Dojo can't reach.

SSL_CERT_FILE is set for NixOS before `lean_dojo` is imported (Python's stdlib
urllib otherwise fails to verify `dl.fbaipublicfiles.com` on this system).
CACHE_DIR points LeanDojo's pre-traced repo cache at the project's data dir so
the 19 GB expanded cache lives next to the rest of our artifacts.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Union

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/certs/ca-bundle.crt")
os.environ.setdefault("CACHE_DIR", str(ROOT / "data" / "lean_dojo_cache"))

from lean_dojo import LeanGitRepo, Theorem, Dojo, ProofFinished, LeanError  # noqa: E402

MATHLIB_URL = "https://github.com/leanprover-community/mathlib4"
MATHLIB_COMMIT = "29dcec074de168ac2bf835a77ef68bbe069194c5"


@dataclass(frozen=True, slots=True)
class VerifyResult:
    ok: bool
    error: Optional[str]
    final_state_pp: Optional[str]
    tactics_applied: int


def _normalize(proof: Union[str, Sequence[str]]) -> List[str]:
    """Accept either a list of tactics or a single string (split on newlines,
    drop blank lines). Embedded newlines inside a list entry (multi-line
    tactics) are preserved as-is."""
    if isinstance(proof, str):
        return [line for line in (ln.rstrip() for ln in proof.splitlines()) if line.strip()]
    return list(proof)


def verify(
    file_path: str,
    theorem_name: str,
    proof: Union[str, Sequence[str]],
    repo_url: str = MATHLIB_URL,
    commit: str = MATHLIB_COMMIT,
) -> VerifyResult:
    """Run tactics through Dojo. ok=True iff some state reaches ProofFinished."""
    tactics = _normalize(proof)
    if not tactics:
        return VerifyResult(False, "empty proof", None, 0)
    repo = LeanGitRepo(repo_url, commit)
    thm = Theorem(repo, file_path, theorem_name)
    with Dojo(thm) as (dojo, state):
        for i, tac in enumerate(tactics, start=1):
            state = dojo.run_tac(state, tac)
            if isinstance(state, ProofFinished):
                return VerifyResult(True, None, None, i)
            if isinstance(state, LeanError):
                return VerifyResult(False, state.error, None, i)
        pp = getattr(state, "pp", None)
        return VerifyResult(False, "proof incomplete", str(pp) if pp else None, len(tactics))


def ground_truth_passes(
    file_path: str,
    theorem_name: str,
    traced_tactics: Sequence[dict],
) -> bool:
    """Pre-filter helper: does the benchmark's own canonical proof pass?
    Use this to filter pilot samples to ones Dojo can actually verify."""
    tactics = [t["tactic"] for t in traced_tactics]
    return verify(file_path, theorem_name, tactics).ok


if __name__ == "__main__":
    FILE = "Mathlib/Data/NNReal/Basic.lean"
    NAME = "NNReal.le_inv_iff_mul_le"
    GT = "rw [← mul_le_mul_left (pos_iff_ne_zero.2 h), mul_inv_cancel h, mul_comm]"

    cases = [
        ("ground-truth (str)", GT, True),
        ("ground-truth (list)", [GT], True),
        ("wrong proof rfl", "rfl", False),
        ("syntax error", "this is not valid lean", False),
        ("empty proof", "", False),
    ]
    for name, proof, expected in cases:
        r = verify(FILE, NAME, proof)
        print(f"{name:25s}: ok={r.ok}  tactics_applied={r.tactics_applied}  "
              f"{'PASS' if r.ok == expected else 'FAIL'}")
        assert r.ok == expected, f"{name}: expected ok={expected}, got {r.ok}: {r.error}"

    print("\nAll cases behaved as expected.")
