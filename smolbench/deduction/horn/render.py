"""Render a theory into one arm's prompt.

Arms
----
``lem``      the lemma library (chain lemmas and extra lemmas)
``unf:j``    every lemma replaced by its level-``j`` cut (``ax`` is the full
             unfolding, ``unf:<max depth>``)
``both:j``   the library and every lemma's level-``j`` cut together
             (``both`` alone: the full unfolding)
``pad:j``    ``lem`` with each cut rule's slot filled by a lorem-ipsum line of
             the same token count, so the lemmas sit where they sit in ``both:j``
             (``pad`` alone: matched to ``both``)
``bothm``, ``padm``   as ``both``/``pad`` but unfolding only the chain and open
             lemmas (the main constant's routes), not the blocked alternatives
``junk:j``   ``pad:j`` with rule-shaped lines instead of lorem: each cut rule's slot
             holds a rule of the same arity and token count over a fresh vocabulary
             that appears nowhere else, so the lines look like library rules but
             can never fire (rule-shaped irrelevant text)
``deep``     the lemmas plus the derivation trees below the given facts (theories
             generated with ``fact_height > 0``): every fact stays given and can
             also be re-derived through a tree and unary chains from deep facts,
             so longer valid routes exist while no lemma head gains a candidate
``dpad``     ``lem`` with each fact-tree rule's slot filled by lorem, matched to ``deep``
``disc:j``   ``both:j`` with every tree's leaves renamed to fresh predicates that
             are never facts, so the trees keep their shape, their same-head root
             rules and their token counts but cannot be entered from the facts
             (disconnected derivations)

Every arm shows the same distractors in the same master order. Rules are
listed without ids; a proof step names the rule by its content (the derived
atom and the ``from`` atoms), and `Rendered.ids` maps the internal display
id ``R<n>`` (line order) to the rule key for the checker's bookkeeping.
"""

from __future__ import annotations

import random
import re
from dataclasses import asdict, dataclass, field

from .theory import Rule, Theory, _Names

_ARM_RE = re.compile(
    r"^(lem|ax|unf|both|pad|bothm|padm|junk|disc|deep|dpad)(?::(\d+))?$"
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


def parse_arm(arm: str, height: int) -> tuple[str, int]:
    """``"both:2"`` -> ``("both", 2)``; ``"ax"`` -> ``("unf", H)``; ``"both"``/``"pad"`` -> full
    depth ``H``; ``"lem"`` -> ``("lem", 0)``."""
    mt = _ARM_RE.match(arm)
    if not mt:
        raise ValueError(f"bad arm {arm!r}")
    kind, j = mt.group(1), mt.group(2)
    if kind in ("bothm", "padm"):  # main-route derivations only (chain + open lemmas)
        kind = kind[:-1]
    if kind == "ax":
        return "unf", height
    if kind in ("lem", "deep", "dpad"):
        if j is not None:
            raise ValueError(f"{kind} takes no level")
        return kind, 0
    if j is None:
        if kind == "unf":
            raise ValueError("unf needs a level, e.g. unf:1 (or use ax)")
        return kind, height  # both / pad without a level: the full unfolding
    level = int(j)
    if level < 1:
        raise ValueError(f"level {level} < 1 (level 0 is lem)")
    return kind, min(level, height)  # past the deepest tree means the full unfolding


def arm_keys(theory: Theory, arm: str) -> tuple[list[str], set[str]]:
    """Rule keys shown by ``arm`` in master order, and the keys whose slots are padded."""
    kind, j = parse_arm(arm, theory.max_height)
    distract = {r.key for r in theory.distractors()}
    lemmas = {r.key for r in theory.lemmas()}
    cut = set(theory.cut_keys(j))
    if arm.startswith(("bothm", "padm")):  # only the trees of chain and open lemmas
        main = {lm.index for lm in theory.library if lm.role != "blocked"}
        cut = {k for k in cut if theory.rules[k].link in main}
    padded: set[str] = set()
    ftree = set(theory.fact_tree_keys())
    if kind in ("deep", "dpad") and not ftree:
        raise ValueError(f"{kind} needs a theory generated with --fact-height > 0")
    if kind == "deep":
        present = lemmas | distract | ftree
    elif kind == "dpad":
        present = lemmas | distract
        padded = ftree
    elif kind == "lem":
        present = lemmas | distract
    elif kind == "unf":
        present = cut | distract
    elif kind == "both":
        present = lemmas | cut | distract
    else:  # pad, junk, disc: the cut rules' slots hold something else
        present = lemmas | distract
        padded = cut
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
    lemma_offsets: dict[str, int] = field(
        default_factory=dict
    )  # key -> token offset of its line
    max_steps: int = 0  # 0 = no step budget; else longer proofs are rejected
    extra_rules: list[dict] = field(
        default_factory=list
    )  # rules shown that are not in the theory (junk / disc arms), as Rule dicts

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
    padded prompt is matched under other tokenizers too and stays readable;
    whitespace runs are not (cl100k packs ~150 spaces into one token).
    ``salt`` rotates the start word so lines differ.
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
    names.used.update(theory.constants)
    return names


def _junk_rule(  # pylint: disable=too-many-arguments
    slot: Rule,
    tok: Tokenizer,
    want: int,
    pool: list[str],
    rng: random.Random,
    sigs: set[tuple[str, frozenset[str]]],
    index: int,
) -> Rule:
    """A rule of ``slot``'s arity over the junk vocabulary, closest to ``want`` tokens."""
    best: Rule | None = None
    best_gap = 10**9
    for _ in range(24):
        body = tuple(rng.sample(pool, len(slot.body)))
        head = rng.choice([p for p in pool if p not in body])
        sig = (head, frozenset(body))
        if sig in sigs:
            continue
        cand = Rule(f"junk{index}", head, body, "junk")
        gap = abs(tok.count(cand.text() + "\n") - want)
        if gap < best_gap:
            best, best_gap = cand, gap
            if gap == 0:
                break
    assert best is not None
    sigs.add((best.head, frozenset(best.body)))
    return best


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
    """Fact atoms of every constant, shuffled once per seed."""
    atoms = theory.fact_atoms()
    random.Random(theory.seed * 7919 + 1).shuffle(atoms)
    return atoms


def render(
    theory: Theory, arm: str, tok: Tokenizer | None = None, max_steps: int = 0
) -> Rendered:
    """Render ``arm`` of ``theory``; ``max_steps > 0`` states a step budget in the prompt."""
    tok = tok or Tokenizer()
    shown, padded = arm_keys(theory, arm)
    kind, _ = parse_arm(arm, theory.max_height)
    extra: list[Rule] = []
    names = _fresh_names(theory, 3) if kind in ("junk", "disc") else None
    rng = random.Random(theory.seed * 7919 + 5)
    pool: list[str] = []
    if kind == "junk" and names is not None:
        pool = [names.word() for _ in range(max(6, len(padded) // 3))]
    sigs: set[tuple[str, frozenset[str]]] = set()
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
    target = 0  # tokens the padded slots should have cost so far
    prefix = "\n".join(head) + "\n"
    n = 0
    for key in shown:
        rule = theory.rules[key]
        if key in padded:
            target += tok.count(f"{rule.text()}\n")
            if kind == "junk" and names is not None:
                jr = _junk_rule(rule, tok, target - filler, pool, rng, sigs, len(extra))
                extra.append(jr)
                block = jr.text()
                n += 1
            elif kind == "disc" and names is not None:
                dr = _disc_rule(rule, theory, tok, names, leafmap)
                extra.append(dr)
                block = dr.text()
                n += 1
            else:
                block = _filler_line(
                    tok, target - filler, len(lines)
                )  # carry rounding debt
            filler += tok.count(block + "\n")
            lines.append(block)
            continue
        n += 1
        ids[f"R{n}"] = key
        if rule.kind == "lemma":
            offsets[key] = tok.count(
                prefix + "\n".join(lines) + ("\n" if lines else "")
            )
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
    if max_steps > 0:
        tail.append(
            f"Your proof must have at most {max_steps} steps; a longer proof is rejected. "
            "Use the shortest derivation you can find."
        )
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
        max_steps=max_steps,
        extra_rules=[asdict(r) for r in extra],
    )
