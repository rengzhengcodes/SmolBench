"""Render a theory into one arm's prompt.

The four arms
-------------
``lem``   the lemma library: chain lemmas and open alternatives, in master order.
``both``  the library and every lemma's derivation tree (the axioms), in master
          order: every added line is a true rule on a derivation of the goal.
``pad``   ``lem`` with each axiom's slot filled by a lorem-ipsum line of the same
          token count, so every lemma sits where it sits in ``both`` and the
          prompt has ``both``'s tokens and lines.
``disc``  ``both`` with every tree's leaves (the lemma's body atoms) renamed to
          fresh predicates that are never facts. The trees keep their shape,
          their same-head root rules and their token counts, but no tree can be
          entered from the facts.

Rules are listed without ids; a proof step names a rule by its content (the
derived atom and the ``from`` atoms). ``Rendered.ids`` maps the display index
``R<n>`` (line order) to the rule key for the checker's bookkeeping, and
``Rendered.extra_rules`` holds the disc rules, which are not theory rules.
"""

from __future__ import annotations

import dataclasses
import random
from dataclasses import asdict, dataclass, field

from .theory import Rule, Theory, _Names

#: The arms, in ladder order.
ARMS = ("lem", "pad", "disc", "both")

SYSTEM = (
    "You are a careful theorem prover. Answer with a proof in exactly the "
    "requested format and nothing else."
)


class Tokenizer:
    """``tiktoken`` cl100k counts, else ``len // 4``."""

    def __init__(self) -> None:
        try:
            import tiktoken  # pylint: disable=import-outside-toplevel

            self._enc = tiktoken.get_encoding("cl100k_base")
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            self._enc = None

    def count(self, s: str) -> int:
        """Token count of ``s``."""
        if self._enc is None:
            return len(s) // 4
        return len(self._enc.encode(s))


def check_arm(arm: str) -> str:
    """``arm`` if it is one of ``ARMS``; raises otherwise."""
    if arm not in ARMS:
        raise ValueError(f"bad arm {arm!r}; the arms are {', '.join(ARMS)}")
    return arm


def arm_keys(theory: Theory, arm: str) -> tuple[list[str], set[str]]:
    """Rule keys shown by ``arm`` in master order, and the keys whose slots are filled."""
    check_arm(arm)
    lemmas = {r.key for r in theory.lemmas()}
    trees = set(theory.tree_keys())
    if arm == "lem":
        present, padded = lemmas, set()
    elif arm == "both":
        present, padded = lemmas | trees, set()
    else:  # pad, disc: the axioms' slots hold something else
        present, padded = lemmas, trees
    shown = [k for k in theory.order if k in present or k in padded]
    return shown, padded


@dataclass
class Rendered:
    """One prompt and what the checker needs to score answers to it."""

    arm: str
    seed: int
    prompt: str
    system: str
    ids: dict[str, str]  # "R3" -> rule key (line order; not shown in the prompt)
    constant: str
    facts: tuple[str, ...]
    goal: str
    n_tokens: int
    n_rules: int
    filler_tokens: int = 0
    lemma_offsets: dict[str, int] = field(default_factory=dict)  # key -> token offset
    extra_rules: list[dict] = field(default_factory=list)  # disc rules, as dicts

    @classmethod
    def from_meta(cls, meta: dict, prompt: str = "", system: str = "") -> Rendered:
        """Rebuild from a ``meta.json`` dict; keys that are not fields are ignored."""
        names = {f.name for f in dataclasses.fields(cls)} - {"prompt", "system"}
        kw = {k: v for k, v in meta.items() if k in names}
        kw["facts"] = tuple(kw["facts"])
        return cls(prompt=prompt, system=system, **kw)

    def rule_of(self, rid: str, theory: Theory) -> Rule | None:
        """Rule behind a display id."""
        key = self.ids.get(rid)
        return theory.rules[key] if key else None


_LOREM = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud "
    "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute "
    "irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat "
    "nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui "
    "officia deserunt mollit anim id est laborum"
).split()


def _filler_line(tok: Tokenizer, target: int, salt: int) -> str:
    """One line of lorem text costing ``target`` tokens (binary search on words).

    Prose filler keeps characters per token close to a rule line's, so the
    padded prompt is matched under other tokenizers too. ``salt`` rotates the
    start word so lines differ.
    """
    if target <= 0:
        return ""

    def build(n: int) -> str:
        return " ".join(_LOREM[(salt + k) % len(_LOREM)] for k in range(n))

    lo, hi = 1, max(4, target * 2)
    while tok.count(build(hi)) < target:
        hi *= 2
    while lo < hi:
        mid = (lo + hi) // 2
        if tok.count(build(mid)) < target:
            lo = mid + 1
        else:
            hi = mid
    return build(lo)


def _fresh_names(theory: Theory, salt: int) -> _Names:
    """Pseudo-word generator that never returns a name already used by ``theory``."""
    names = _Names(random.Random(theory.seed * 104729 + salt))
    for r in theory.rules.values():
        names.used.update((r.head, *r.body))
    names.used.update(theory.facts)
    names.used.add(theory.constant)
    return names


def _disc_rule(
    slot: Rule,
    theory: Theory,
    tok: Tokenizer,
    names: _Names,
    leafmap: dict[tuple[int, str], str],
) -> Rule:
    """``slot`` with its leaf predicates (the lemma's body atoms) renamed to fresh
    words of the same token count, so the tree cannot be entered from the facts."""
    leaves = set(theory.library[slot.link - 1].body)

    def fresh(pred: str) -> str:
        key = (slot.link, pred)
        if key not in leafmap:
            want = tok.count(f"{pred}(x)")
            best, best_gap = None, 10**9
            for _ in range(40):
                w = names.word()
                gap = abs(tok.count(f"{w}(x)") - want)
                if gap < best_gap:
                    best, best_gap = w, gap
                    if gap == 0:
                        break
            leafmap[key] = best or names.word()
        return leafmap[key]

    body = tuple(fresh(b) if b in leaves else b for b in slot.body)
    return Rule(f"disc.{slot.key}", slot.head, body, "disc", slot.link, slot.depth)


def _fact_lines(theory: Theory) -> list[str]:
    """Fact atoms, shuffled once per seed."""
    atoms = theory.fact_atoms()
    random.Random(theory.seed * 7919 + 1).shuffle(atoms)
    return atoms


def render(theory: Theory, arm: str, tok: Tokenizer | None = None) -> Rendered:
    """Render ``arm`` of ``theory``."""
    tok = tok or Tokenizer()
    shown, padded = arm_keys(theory, arm)
    extra: list[Rule] = []
    names = _fresh_names(theory, 3) if arm == "disc" else None
    leafmap: dict[tuple[int, str], str] = {}
    c = theory.constant
    head = [
        "Prove the goal from the facts using the library rules. The goal is always "
        "provable from the facts and the library rules.",
        "",
        "## Facts",
        *_fact_lines(theory),
        "",
        "## Library",
    ]
    ids: dict[str, str] = {}
    lines: list[str] = []
    offsets: dict[str, int] = {}
    filler = 0
    target = 0  # tokens the filled slots should have cost so far
    prefix = "\n".join(head) + "\n"
    n = 0
    for key in shown:
        rule = theory.rules[key]
        if key in padded:
            target += tok.count(f"{rule.text()}\n")
            if arm == "disc" and names is not None:
                dr = _disc_rule(rule, theory, tok, names, leafmap)
                extra.append(dr)
                block = dr.text()
                n += 1
            else:
                block = _filler_line(tok, target - filler, len(lines))  # carry rounding debt
            filler += tok.count(block + "\n")
            lines.append(block)
            continue
        n += 1
        ids[f"R{n}"] = key
        if rule.kind == "lemma":
            offsets[key] = tok.count(prefix + "\n".join(lines) + ("\n" if lines else ""))
        lines.append(rule.text())
    tail = [
        "",
        "## Goal",
        f"{theory.goal}({c})",
        "",
        "## Answer format",
        "One step per line, nothing else:",
        "derive <atom> from <atom>[, <atom>]",
        "A step applies one library rule with x set to one constant. The atoms after "
        "`from` are exactly that rule's body atoms for that constant, each a fact or an "
        "atom derived on an earlier line. The atom after `derive` is the rule's head for "
        "the same constant. Write every atom as predicate(constant). The last line "
        "derives the goal.",
    ]
    prompt = prefix + "\n".join(lines) + "\n" + "\n".join(tail) + "\n"
    return Rendered(
        arm=arm,
        seed=theory.seed,
        prompt=prompt,
        system=SYSTEM,
        ids=ids,
        constant=c,
        facts=theory.facts,
        goal=theory.goal,
        n_tokens=tok.count(prompt),
        n_rules=n,
        filler_tokens=filler,
        lemma_offsets=offsets,
        extra_rules=[asdict(r) for r in extra],
    )
