"""Parse and verify step proofs; certify that an arm has no shortcut.

A proof line is ``derive h(c) from a(c), b(c)``: it applies the library rule
``a(x) ∧ b(x) → h(x)``, which must appear in the prompt. A trailing ``by ...``
is ignored. Lines that do not start with ``derive`` (after optional numbering)
are ignored, so a model may think before it answers. Any valid derivation of
the goal passes, not only the designed one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .render import Rendered, arm_keys, parse_arm
from .theory import DISTRACTOR_KINDS, Rule, Theory

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
    """Outcome of checking one answer."""

    verdict: str
    steps: int = 0
    route: str = ""  # short | long | mixed | "" (for both:j and any success)
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


def _split(atom: str, default_const: str | None) -> tuple[str, str] | None:
    """``pred(c)`` -> ``(pred, c)``; a bare ``pred`` takes ``default_const`` if one."""
    mt = _SPLIT_ATOM_RE.match(atom)
    if mt:
        return mt.group(1), mt.group(2)
    if default_const is not None and re.fullmatch(r"\w+", atom):
        return atom, default_const
    return None


def content_index(theory: Theory, rendered: Rendered) -> dict[Sig, Rule]:
    """``(head, body set) -> rule`` over the rules shown in ``rendered``."""
    out: dict[Sig, Rule] = {}
    for key in rendered.ids.values():
        r = theory.rules[key]
        out[(r.head, frozenset(r.body))] = r
    for r in extra_rules(rendered):
        out[(r.head, frozenset(r.body))] = r
    return out


def extra_rules(rendered: Rendered) -> list[Rule]:
    """Rules shown by ``rendered`` that are not in the theory (junk / disc arms)."""
    return [Rule(**{**d, "body": tuple(d["body"])}) for d in rendered.extra_rules]


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

    Atoms are ``pred(const)``. With a single constant a bare ``pred`` is read
    as that constant; with several it is an invalid step.
    """
    if finish_reason == "length":
        return Verdict("length", reason="finish_reason=length")
    steps, gave_up, ignored = parse(text)
    if not steps:
        return Verdict("given_up" if gave_up else "no_answer", ignored_lines=ignored)
    default = theory.constants[0] if len(theory.constants) == 1 else None
    known = set(theory.fact_atoms())
    goal = _atom(rendered.goal, theory.constants[0])
    content = content_index(theory, rendered)
    kinds: list[str] = []
    lines: list[str] = []
    for i, st in enumerate(steps, 1):
        hd = _split(st.head, default)
        if hd is None:
            return _bad(i, f"atom {st.head!r} needs a constant", ignored, kinds, lines)
        pred, const = hd
        if const not in theory.constants:
            return _bad(i, f"unknown constant {const!r}", ignored, kinds, lines)
        body_preds: set[str] = set()
        body_atoms: set[str] = set()
        for a in st.body:
            sp = _split(a, default)
            if sp is None:
                return _bad(i, f"atom {a!r} needs a constant", ignored, kinds, lines)
            if sp[1] != const:
                return _bad(
                    i,
                    f"premise {a} is about {sp[1]}, head is about {const}",
                    ignored,
                    kinds,
                    lines,
                )
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
        known.add(_atom(pred, const))
        kinds.append(rule.kind)
        lines.append(st.line)
    if goal in known and rendered.max_steps and len(steps) > rendered.max_steps:
        return Verdict(
            "too_long",
            len(steps),
            route=route_of(kinds),
            used_kinds=tuple(kinds),
            reason=f"{len(steps)} steps, budget {rendered.max_steps}",
            ignored_lines=ignored,
            step_lines=lines,
        )
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
    """``short`` if only lemmas, ``long`` if only tree rules, else ``mixed``."""
    path = {k for k in kinds if k not in DISTRACTOR_KINDS}
    if path <= {"lemma"}:
        return "short"
    if "lemma" not in path:
        return "long"
    return "mixed"


# -- closure and certificate --------------------------------------------------


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


def required_heads(theory: Theory, arm: str) -> list[str]:
    """Predicates every proof in ``arm`` must derive."""
    kind, j = parse_arm(arm, theory.max_height)
    if kind == "unf":
        return [theory.rules[k].head for k in theory.cut_keys(j, chain_only=True)]
    return [lk.head for lk in theory.links]


def designed_proof(
    theory: Theory, rendered: Rendered, route: str = "short"
) -> list[str]:
    """Proof lines for ``rendered``: the lemma route or the cut route."""
    kind, j = parse_arm(rendered.arm, theory.max_height)
    c = theory.constant
    use_cut = kind == "unf" or (kind == "both" and route == "long")
    j_eff = j if use_cut else 0
    out: list[str] = []
    for i in range(1, theory.m + 1):
        rules = theory.cut(i, j_eff)
        # sub-lemmas first (deepest heads), then axioms bottom-up.
        rules.sort(key=lambda r: (-r.depth, r.key))
        for r in rules:
            out.append(
                f"derive {_atom(r.head, c)} from {', '.join(_atom(b, c) for b in r.body)}"
            )
    return out


@dataclass
class Certificate:
    """Why ``arm`` is sound: ``min_steps`` is the designed route's length (the
    shortest proof when there are no open alternatives)."""

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


def certify(theory: Theory, rendered: Rendered) -> Certificate:
    """Check: goal derivable; rule content unique; every library rule is on a
    path to the goal; blocked alternatives never fire for the main constant
    and open ones do; the chain is necessary when there are no open
    alternatives; the designed route verifies with the designed step count."""
    arm_keys(theory, rendered.arm)  # validates the arm spec
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
    if extra:
        # junk and disc rules must be inert: none fires even with every shown rule,
        # and junk rules must not touch the theory's vocabulary
        preds = {p for ru in theory.rules.values() for p in (ru.head, *ru.body)} | facts
        full_all = closure(rules + extra, facts)
        for r in extra:
            if all(b in full_all for b in r.body):
                reasons.append(f"extra rule {r.key} fires for the main constant")
            if r.kind == "junk" and ({r.head, *r.body} & preds):
                reasons.append(f"junk rule {r.key} uses a theory predicate")
        if closure(rules + extra, facts) - full:
            reasons.append("extra rules derive new atoms")
    if theory.goal not in full:
        reasons.append("goal not derivable")
    anc = on_path_heads(theory)
    off = [lm.index for lm in theory.library if lm.head not in anc]
    if off:
        reasons.append(
            f"{len(off)} library lemmas are not on a path to the goal: {off[:5]}"
        )
    lib_closure = closure(
        [theory.rules[Theory.lemma_key(lm.index)] for lm in theory.library], facts
    )
    for lm in theory.library:
        fires = all(b in lib_closure for b in lm.body)
        if lm.role == "blocked" and fires:
            reasons.append(f"blocked lemma {lm.index} fires for the main constant")
        if lm.role in ("chain", "open") and not fires:
            reasons.append(
                f"{lm.role} lemma {lm.index} does not fire for the main constant"
            )
    req = required_heads(theory, rendered.arm)
    if len(set(req)) != len(req):
        reasons.append("required heads not distinct")
    if not theory.alternatives("open"):
        for q in req:
            without = [r for r in rules if r.head != q]
            if theory.goal in closure(without, facts):
                reasons.append(f"{q} not necessary")
    kind, _ = parse_arm(rendered.arm, theory.max_height)
    if kind == "deep":
        # every given fact must be re-derivable from the deep facts alone
        ftree = [theory.rules[k] for k in theory.fact_tree_keys()]
        given = set(theory.facts) - set(theory.deep_facts)
        missing = given - closure(ftree, set(theory.deep_facts))
        if missing:
            reasons.append(
                f"facts not derivable from deep facts: {sorted(missing)[:5]}"
            )
    proof = designed_proof(theory, rendered, "long" if kind == "unf" else "short")
    v = verify(theory, rendered, "\n".join(proof))
    if v.verdict != "success":
        reasons.append(f"designed proof fails: {v.reason}")
    elif v.steps != len(req):
        reasons.append(f"designed proof has {v.steps} steps, required {len(req)}")
    if kind == "both":
        v2 = verify(
            theory, rendered, "\n".join(designed_proof(theory, rendered, "long"))
        )
        # under a step budget the long route is valid but over budget: too_long
        if v2.verdict not in ("success", "too_long") or v2.route != "long":
            reasons.append(f"long route fails: {v2.reason}")
    return Certificate(rendered.arm, not reasons, len(req), v.steps, reasons)
