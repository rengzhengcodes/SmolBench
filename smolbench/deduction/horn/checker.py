"""Parse and verify step proofs; certify that a rendered arm is sound.

A proof line is ``derive h(c) from a(c), b(c)``: it applies the rule
``a(x) ∧ b(x) → h(x)``, which must appear in the prompt. A trailing ``by ...``
is ignored. Lines that do not start with ``derive`` (after optional numbering)
are ignored, so a model may think before it answers. Any valid derivation of
the goal passes, not only the designed one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .render import Rendered, arm_keys
from .theory import Rule, Theory

_STEP_RE = re.compile(
    r"^\s*(?:(?:step\s*)?\d+\s*[.):-]\s*)?derive\s+(?P<head>\w+(?:\(\w+\))?)"
    r"\s+from\s+(?P<body>.+?)(?:\s+by\s+\S+)?\s*\.?\s*$",
    re.IGNORECASE,
)
_ATOM_RE = re.compile(r"\w+(?:\(\w+\))?")
_SPLIT_ATOM_RE = re.compile(r"^(\w+)\((\w+)\)$")
_GIVE_UP_RE = re.compile(r"^\s*give\s+up\s*\.?\s*$", re.IGNORECASE)

#: Verdicts. ``success`` is the only pass. ``exception`` is infra, not scored.
VERDICTS = (
    "success",
    "invalid_step",
    "incomplete",
    "given_up",
    "no_answer",
    "length",
    "exception",
)

Sig = tuple[str, frozenset[str]]


@dataclass(frozen=True)
class Step:
    """One parsed proof line."""

    head: str
    body: tuple[str, ...]
    line: str


@dataclass
class Verdict:
    """Outcome of checking one answer.

    ``route`` is ``short`` (lemma steps only), ``long`` (tree steps only) or
    ``mixed``, over the valid steps plus, for a failure, the failing step's
    rule. ``used_kinds`` lists those rules' kinds in order.
    """

    verdict: str
    steps: int = 0
    route: str = ""
    used_kinds: tuple[str, ...] = ()
    reason: str = ""
    ignored_lines: int = 0
    step_lines: list[str] = field(default_factory=list)


def parse(text: str) -> tuple[list[Step], bool, int]:
    """Parse ``text`` into steps.

    Returns
    -------
    tuple[list[Step], bool, int]
        Steps, whether a ``give up`` line appeared, and ignored line count.
    """
    steps: list[Step] = []
    gave_up = False
    ignored = 0
    for raw in text.splitlines():
        line = raw.strip().strip("`")
        if not line:
            continue
        if _GIVE_UP_RE.match(line):
            gave_up = True
            continue
        mt = _STEP_RE.match(line)
        if not mt:
            ignored += 1
            continue
        atoms = tuple(
            a for a in _ATOM_RE.findall(mt.group("body")) if a.lower() != "and"
        )
        steps.append(Step(mt.group("head").lower(), atoms, line))
    return steps, gave_up, ignored


def _atom(pred: str, c: str) -> str:
    return f"{pred}({c})"


def _split(atom: str, default_const: str) -> tuple[str, str] | None:
    """``pred(c)`` -> ``(pred, c)``; a bare ``pred`` takes ``default_const``."""
    mt = _SPLIT_ATOM_RE.match(atom)
    if mt:
        return mt.group(1), mt.group(2)
    if re.fullmatch(r"\w+", atom):
        return atom, default_const
    return None


def extra_rules(rendered: Rendered) -> list[Rule]:
    """Rules shown by ``rendered`` that are not in the theory (the disc arm)."""
    return [Rule(**{**d, "body": tuple(d["body"])}) for d in rendered.extra_rules]


def content_index(theory: Theory, rendered: Rendered) -> dict[Sig, Rule]:
    """``(head, body set) -> rule`` over every rule shown in ``rendered``."""
    out: dict[Sig, Rule] = {}
    for key in rendered.ids.values():
        r = theory.rules[key]
        out[(r.head, frozenset(r.body))] = r
    for r in extra_rules(rendered):
        out[(r.head, frozenset(r.body))] = r
    return out


def _bad(  # pylint: disable=too-many-arguments
    i: int, why: str, ignored: int, kinds: list[str] = (), lines: list[str] = ()
) -> Verdict:
    """Invalid step ``i``; ``kinds`` are the rules the earlier, valid steps used."""
    return Verdict(
        "invalid_step",
        i,
        route=route_of(kinds) if kinds else "",
        used_kinds=tuple(kinds),
        reason=f"step {i}: {why}",
        ignored_lines=ignored,
        step_lines=list(lines),
    )


def verify(  # pylint: disable=too-many-locals,too-many-return-statements
    theory: Theory, rendered: Rendered, text: str, finish_reason: str = "stop"
) -> Verdict:
    """Score ``text`` as an answer to ``rendered``.

    Atoms are ``pred(c)``; a bare ``pred`` is read as the theory's constant.
    """
    if finish_reason == "length":
        return Verdict("length", reason="finish_reason=length")
    steps, gave_up, ignored = parse(text)
    if not steps:
        return Verdict("given_up" if gave_up else "no_answer", ignored_lines=ignored)
    c = theory.constant
    known = set(theory.fact_atoms())
    goal = _atom(rendered.goal, c)
    content = content_index(theory, rendered)
    kinds: list[str] = []
    lines: list[str] = []
    for i, st in enumerate(steps, 1):
        hd = _split(st.head, c)
        if hd is None:
            return _bad(i, f"atom {st.head!r} is malformed", ignored, kinds, lines)
        pred, const = hd
        if const != c:
            return _bad(i, f"unknown constant {const!r}", ignored, kinds, lines)
        body_preds: set[str] = set()
        body_atoms: set[str] = set()
        for a in st.body:
            sp = _split(a, c)
            if sp is None:
                return _bad(i, f"atom {a!r} is malformed", ignored, kinds, lines)
            if sp[1] != c:
                return _bad(i, f"unknown constant {sp[1]!r}", ignored, kinds, lines)
            body_preds.add(sp[0])
            body_atoms.add(_atom(*sp))
        rule = content.get((pred, frozenset(body_preds)))
        if rule is None:
            return _bad(
                i,
                f"no library rule {' ∧ '.join(sorted(body_preds))} → {pred}",
                ignored,
                kinds,
                lines,
            )
        missing = body_atoms - known
        if missing:
            return _bad(
                i,
                f"premise not derived: {sorted(missing)}",
                ignored,
                kinds + [rule.kind],
                lines,
            )
        known.add(_atom(pred, c))
        kinds.append(rule.kind)
        lines.append(st.line)
    if goal not in known:
        return Verdict(
            "incomplete",
            len(steps),
            route=route_of(kinds),
            used_kinds=tuple(kinds),
            reason="goal not derived",
            ignored_lines=ignored,
            step_lines=lines,
        )
    return Verdict(
        "success",
        len(steps),
        route=route_of(kinds),
        used_kinds=tuple(kinds),
        ignored_lines=ignored,
        step_lines=lines,
    )


def route_of(kinds: list[str] | tuple[str, ...]) -> str:
    """``short`` if only lemmas, ``long`` if only tree rules, else ``mixed``.

    ``disc`` rules count as tree rules (an attempt to enter a tree).
    """
    path = set(kinds)
    if path <= {"lemma"}:
        return "short"
    if "lemma" not in path:
        return "long"
    return "mixed"


# -- closure, designed proofs and the certificate ---------------------------


def closure(rules: list[Rule], facts: set[str]) -> set[str]:
    """Predicates derivable from ``facts`` by forward chaining."""
    known = set(facts)
    changed = True
    while changed:
        changed = False
        for r in rules:
            if r.head not in known and all(b in known for b in r.body):
                known.add(r.head)
                changed = True
    return known


def designed_proof(theory: Theory, route: str = "short") -> list[str]:
    """Proof lines along the chain: the ``short`` route applies each chain lemma,
    the ``long`` route applies each chain lemma's tree (axioms, leaves first)."""
    if route not in ("short", "long"):
        raise ValueError(f"route {route!r}")
    c = theory.constant
    out: list[str] = []
    for i in range(1, theory.m + 1):
        rules = [theory.rules[Theory.lemma_key(i)]] if route == "short" else theory.tree(i)
        rules.sort(key=lambda r: (-r.depth, r.key))
        for r in rules:
            out.append(
                f"derive {_atom(r.head, c)} from {', '.join(_atom(b, c) for b in r.body)}"
            )
    return out


@dataclass
class Certificate:
    """Why ``arm`` is sound. ``min_steps`` is the chain length ``m``: every route
    to the goal applies at least one rule per chain level, and the lemma route
    applies exactly one."""

    arm: str
    ok: bool
    min_steps: int
    designed_steps: int
    reasons: list[str] = field(default_factory=list)


def on_path_heads(theory: Theory) -> set[str]:
    """Predicates that lie on some path to the goal (ancestor closure over the library)."""
    anc = {theory.goal}
    changed = True
    while changed:
        changed = False
        for lm in theory.library:
            if lm.head in anc:
                for b in lm.body:
                    if b not in anc:
                        anc.add(b)
                        changed = True
    return anc


def certify(theory: Theory, rendered: Rendered) -> Certificate:  # pylint: disable=too-many-locals,too-many-branches
    """Check that ``rendered`` is a sound instance of its arm.

    Every arm: rule content is unique; the goal is derivable; every library
    lemma lies on a path to the goal and fires for the constant; every given
    fact is a premise of a chain lemma; the chain heads are distinct; the
    lemma route verifies in ``m`` steps. Control arms (``pad``, ``disc``): the
    added rules never fire and derive nothing new; the tree route is invalid.
    ``both``: the tree route verifies as a ``long`` route.
    """
    arm_keys(theory, rendered.arm)  # validates the arm
    rules = [theory.rules[k] for k in rendered.ids.values()]
    extra = extra_rules(rendered)
    facts = set(theory.facts)
    reasons: list[str] = []
    seen: dict[Sig, str] = {}
    for r in rules + extra:
        sig: Sig = (r.head, frozenset(r.body))
        if sig in seen:
            reasons.append(f"duplicate rule content: {r.key} = {seen[sig]}")
        seen[sig] = r.key
    full = closure(rules, facts)
    if theory.goal not in full:
        reasons.append("goal not derivable")
    anc = on_path_heads(theory)
    off = [lm.index for lm in theory.library if lm.head not in anc]
    if off:
        reasons.append(f"{len(off)} library lemmas are not on a path to the goal: {off[:5]}")
    lib_closure = closure(theory.lemmas(), facts)
    dead = [lm.index for lm in theory.library if not all(b in lib_closure for b in lm.body)]
    if dead:
        reasons.append(f"{len(dead)} library lemmas do not fire for the constant: {dead[:5]}")
    idle = facts - {b for lm in theory.links for b in lm.body}
    if idle:
        reasons.append(f"given facts no chain lemma uses: {sorted(idle)[:5]}")
    heads = [lk.head for lk in theory.links]
    if len(set(heads)) != len(heads):
        reasons.append("chain heads not distinct")
    if extra:
        full_all = closure(rules + extra, facts)
        for r in extra:
            if all(b in full_all for b in r.body):
                reasons.append(f"extra rule {r.key} fires for the constant")
        if full_all - full:
            reasons.append("extra rules derive new atoms")
    short = verify(theory, rendered, "\n".join(designed_proof(theory, "short")))
    if short.verdict != "success":
        reasons.append(f"lemma route fails: {short.reason}")
    elif short.steps != theory.m:
        reasons.append(f"lemma route has {short.steps} steps, expected {theory.m}")
    long = verify(theory, rendered, "\n".join(designed_proof(theory, "long")))
    if rendered.arm == "both":
        if long.verdict != "success" or long.route != "long":
            reasons.append(f"tree route fails in both: {long.reason}")
    elif long.verdict == "success":
        reasons.append(f"tree route is valid in {rendered.arm}")
    return Certificate(rendered.arm, not reasons, theory.m, short.steps, reasons)
