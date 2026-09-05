"""The root README's package map and Lean-backend prose, pinned against the tree.

The map in ``README.md`` calls itself "an annotated tree of the whole
repository ... this section is the map". A map is only useful if it is
complete: a module absent from it is a module a reader never learns exists,
and ``smolbench/deduction/lean/replbackend.py`` -- the module that actually
drives Lean -- was absent from it while every other module in that package was
listed.

The prose tests here pin the other half of the same drift. Verification moved
off LeanDojo onto ``lean-interact``: ``smolbench/deduction/lean/verify.py``
imports ``lean_interact`` and describes its own contract as "unchanged from the
retired LeanDojo-backed version". ``lean-dojo`` is still a declared dependency
(corpus tracing and premise slicing use it, and it is what pins
``Requires-Python <3.13``), so the check below is deliberately narrow: it
forbids only the claim that lean-dojo VERIFIES, not every mention of it.

Deliberately importing nothing from ``smolbench.deduction.lean``: these are
text-only guarantees about documentation, and they must hold whether or not the
``lean`` extra is installed.
"""

from __future__ import annotations

import re

from tests._paths import REPO_ROOT

README = REPO_ROOT / "README.md"
LEAN_PKG = REPO_ROOT / "smolbench" / "deduction" / "lean"


def _package_map() -> str:
    """Return the fenced ASCII tree under ``## Package layout``."""
    text = README.read_text()
    block = text[text.index("## Package layout"):]
    first = block.index("```")
    return block[first: block.index("```", first + 3)]


def _lean_map_block() -> str:
    """Return just the ``deduction/lean/`` sub-block of the package map.

    Scoped rather than searching the whole tree: names like ``cli.py`` and
    ``runner.py`` recur across packages, so a whole-tree substring search would
    report a Lean module as documented because some other package happens to
    ship a file of that name.
    """
    tree = _package_map()
    rest = tree[tree.index("  deduction/lean/"):]
    end = re.search(r"\n(?=\S)", rest)          # next entry at fence column 0
    return rest[: end.start()] if end else rest


def test_readme_map_names_every_lean_module():
    """Every module under ``smolbench/deduction/lean/`` appears in the map.

    ``__init__.py`` is excluded on purpose: it is package machinery, not one of
    the subsystems the map indexes.
    """
    block = _lean_map_block()
    modules = sorted(p.name for p in LEAN_PKG.glob("*.py") if not p.name.startswith("__"))
    assert modules, f"no modules found under {LEAN_PKG}"
    missing = [m for m in modules if m not in block]
    assert not missing, f"README package map omits {missing}"


def test_map_credits_lean_interact_for_verification():
    """The map's verify.py line must name the backend that actually runs.

    ``verify.py`` imports ``lean_interact`` and raises pointing at the ``lean``
    extra when it is absent; a map line reading "lean-dojo verification" sends
    an operator to install and debug the wrong package.
    """
    # Anchored on a token boundary: a bare ``"verify.py" in line`` also matches
    # ``nullverify.py``, which sits on its own line of the same block.
    verify_lines = [ln for ln in _lean_map_block().splitlines()
                    if re.search(r"(?<![A-Za-z0-9_])verify\.py", ln)]
    assert len(verify_lines) == 1, verify_lines
    assert "lean-interact" in verify_lines[0], verify_lines[0]
    assert "lean-dojo" not in verify_lines[0], verify_lines[0]


#: The three claims the tree contradicts. Narrow substrings, not "any mention
#: of lean-dojo": lean-dojo is still installed and still pins python<3.13, and
#: the README says both of those correctly.
LEAN_DOJO_VERIFICATION_CLAIMS = (
    "lean-dojo verification",
    "lean-dojo verify pass",
    "verification path's `lean-dojo`",
)


def test_readme_does_not_credit_lean_dojo_with_verification():
    text = README.read_text()
    offenders = [claim for claim in LEAN_DOJO_VERIFICATION_CLAIMS if claim in text]
    assert not offenders, f"README still credits lean-dojo with verifying: {offenders}"
    assert "lean-interact" in text


def test_pyproject_lean_comment_does_not_credit_lean_dojo_with_verification():
    """pyproject's own comment block contradicted the comment 6 lines below it.

    The comment above ``lean = [`` said verification needs lean-dojo; the
    comment on the ``lean-dojo`` entry says it stays ONLY for tracing and is no
    longer imported by the verifier. Both cannot be true.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text()
    header = text[text.index("# Lean theorem-proving eval"): text.index("lean = [")]
    assert "verification additionally needs lean-dojo" not in header, header
    assert "lean-interact" in header, header
    # The entry comment below is the authority this header must agree with.
    assert "`lean-dojo` stays ONLY because corpus tracing" in text
