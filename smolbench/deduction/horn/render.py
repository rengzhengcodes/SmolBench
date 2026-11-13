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

Review arms (``REVIEW_ARMS``; not in the default ladder)
--------------------------------------------------------
Each changes only what ``both``'s tree slots hold. A tree touches the rest of
the theory at its leaves (the lemma's body atoms) and its root head (the
lemma's head); its internal predicates are private to it.

``fwd``          ``both`` with every tree's root head renamed to a fresh
                 predicate: each tree fires from the facts but derives nothing
                 any other rule uses (the mirror of ``disc``).
``tjunk``        ``both`` with leaves and root head renamed: the same tree
                 shapes, connected to nothing.
``rep``          ``lem`` with each tree slot holding a copy of its own lemma:
                 the same proof graph, each lemma shown ``1 + |tree|`` times.
``marked-lemma`` ``both`` with every lemma line tagged ``[lemma]`` and one line
                 stating that a proof using only ``[lemma]`` rules exists.

Rules are listed without ids; a proof step names a rule by its content (the
derived atom and the ``from`` atoms). ``Rendered.ids`` maps the display index
``R<n>`` (line order) to the rule key for the checker's bookkeeping, and
``Rendered.extra_rules`` holds the rules of ``disc``, ``fwd`` and ``tjunk``,
which are not theory rules.
"""

from __future__ import annotations

import dataclasses
import random
from dataclasses import asdict, dataclass, field

from .theory import Rule, Theory, _Names

#: The arms, in ladder order.
ARMS = ("lem", "pad", "disc", "both")
#: Control arms added for the ICLR 2027 review round; rendered on request only.
REVIEW_ARMS = ("fwd", "tjunk", "rep", "marked-lemma")
ALL_ARMS = ARMS + REVIEW_ARMS
#: Arms whose tree slots hold renamed tree rules.
RENAMED_ARMS = frozenset({"disc", "fwd", "tjunk"})
#: Arms in which the trees can be used to reach the goal.
USABLE_TREE_ARMS = frozenset({"both", "marked-lemma"})

LEMMA_TAG = "[lemma] "
MARKED_NOTE = (
    "Rules marked [lemma] are enough: the goal has a proof that uses only [lemma] rules."
)

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
    """``arm`` if it is one of ``ALL_ARMS``; raises otherwise."""
    if arm not in ALL_ARMS:
        raise ValueError(f"bad arm {arm!r}; the arms are {', '.join(ALL_ARMS)}")
    return arm


def arm_keys(theory: Theory, arm: str) -> tuple[list[str], set[str]]:
    """Rule keys shown by ``arm`` in master order, and the keys whose slots are filled."""
    check_arm(arm)
    lemmas = {r.key for r in theory.lemmas()}
    trees = set(theory.tree_keys())
    if arm == "lem":
        present, padded = lemmas, set()
    elif arm in USABLE_TREE_ARMS:
        present, padded = lemmas | trees, set()
    else:  # pad, disc, fwd, tjunk, rep: the axioms' slots hold something else
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
    extra_rules: list[dict] = field(default_factory=list)  # disc/fwd/tjunk rules, as dicts

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


def _fresh_like(
    pred: str, tok: Tokenizer, names: _Names, cache: dict[tuple[int, str], str], key: tuple[int, str]
) -> str:
    """A fresh word costing as many tokens as ``pred`` in ``pred(x)``, memoized on ``key``."""
    if key not in cache:
        want = tok.count(f"{pred}(x)")
        best, best_gap = None, 10**9
        for _ in range(40):
            w = names.word()
            gap = abs(tok.count(f"{w}(x)") - want)
            if gap < best_gap:
                best, best_gap = w, gap
                if gap == 0:
                    break
        cache[key] = best or names.word()
    return cache[key]


def _renamed_rule(
    slot: Rule,
    arm: str,
    theory: Theory,
    tok: Tokenizer,
    names: _Names,
    cache: dict[tuple[int, str], str],
) -> Rule:
    """``slot`` (an axiom) as ``arm`` shows it.

    ``disc`` and ``tjunk`` rename the leaf predicates (the lemma's body atoms),
    so the tree cannot be entered from the facts. ``fwd`` and ``tjunk`` rename
    the root head (the lemma's head), so the tree derives nothing on a path to
    the goal. Renames are per tree and token-matched; internal predicates are
    private to the tree and kept.
    """
    lemma = theory.library[slot.link - 1]
    body, head = slot.body, slot.head
    if arm in ("disc", "tjunk"):
        leaves = set(lemma.body)
        body = tuple(
            _fresh_like(b, tok, names, cache, (slot.link, b)) if b in leaves else b
            for b in body
        )
    if arm in ("fwd", "tjunk") and slot.depth == 0:
        head = _fresh_like(head, tok, names, cache, (slot.link, "^" + head))
    return Rule(f"{arm}.{slot.key}", head, body, arm, slot.link, slot.depth)


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
    # disc keeps its September salt so its renames reproduce; fwd/tjunk get their own.
    salt = {"disc": 3, "fwd": 5, "tjunk": 7}.get(arm)
    names = _fresh_names(theory, salt) if salt is not None else None
    cache: dict[tuple[int, str], str] = {}
    c = theory.constant
    tag = LEMMA_TAG if arm == "marked-lemma" else ""
    head = [
        "Prove the goal from the facts using the library rules. The goal is always "
        "provable from the facts and the library rules.",
        *([MARKED_NOTE] if arm == "marked-lemma" else []),
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
            if arm in RENAMED_ARMS and names is not None:
                dr = _renamed_rule(rule, arm, theory, tok, names, cache)
                extra.append(dr)
                block = dr.text()
                n += 1
            elif arm == "rep":
                block = theory.rules[Theory.lemma_key(rule.link)].text()
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
        lines.append(tag + rule.text() if rule.kind == "lemma" else rule.text())
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
