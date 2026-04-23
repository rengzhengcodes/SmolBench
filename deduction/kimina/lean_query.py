"""Wrap kimina-lean-server `/verify` to issue `#print` / `#check` queries
and return the resulting info-severity text.

We piggyback on the existing verify endpoint because it already sits in
front of a warm Lean process with Mathlib imported. Sending a file
containing just `import Mathlib; #print <name>` gets the elaborator to
produce the definition's text as an `info` diagnostic, which comes back
in the response's `messages` list.
"""
from __future__ import annotations

import requests


_BASE_OPTS = (
    "set_option pp.notation false\n"
    "set_option pp.fullNames true\n"
    "set_option pp.universes false\n"
    "set_option pp.structureProjections false\n"
)


def _verify(server_url: str, code: str, timeout: int = 60) -> list[dict]:
    r = requests.post(
        f"{server_url}/verify",
        json={"codes": [{"custom_id": "x", "proof": code}]},
        timeout=timeout,
    )
    return r.json()["results"][0].get("response", {}).get("messages", [])


def _collect_info(msgs: list[dict]) -> list[str]:
    return [
        str(m.get("data", ""))
        for m in msgs
        if m.get("severity") == "info"
    ]


def print_decl(name: str, server_url: str) -> str | None:
    """Return the raw text of `#print <name>`. None if the response has no
    info message (e.g., the name is unknown)."""
    code = f"import Mathlib\n\n{_BASE_OPTS}#print {name}\n"
    infos = _collect_info(_verify(server_url, code))
    return infos[0] if infos else None


def check_type(expr: str, server_url: str) -> str | None:
    """Return the type of `expr` as a string — the text of `#check @<expr>`.

    For a theorem name `@Foo.bar`, this returns the full Pi-type with all
    implicits explicit, notation disabled, full names. Useful for getting a
    parseable signature to unfold.
    """
    code = f"import Mathlib\n\n{_BASE_OPTS}#check @{expr}\n"
    infos = _collect_info(_verify(server_url, code))
    return infos[0] if infos else None


def extract_def_body(print_output: str | None) -> str | None:
    """Given a `#print Foo` output like
        `def Foo.Bar : Type :=\nWithTop NNReal`
    or  `theorem Foo : P := proofterm`
    return the body (right-hand side of `:=`). For structures/inductives
    (`structure Foo where ...`, `inductive Bar where ...`), return None
    because there is no RHS — caller should handle those differently.
    """
    if print_output is None:
        return None
    idx = print_output.find(":=")
    if idx >= 0:
        return print_output[idx + 2:].strip()
    return None
