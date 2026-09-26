"""Generate a random Horn-rule theory for the Horn bench.

The setup is fixed (``smolbench/deduction/horn/README.md`` describes it in full):

- one constant ``c``; predicates are unary; every rule is over the variable ``x``;
- ``m + 1`` facts ``F0 .. Fm`` about ``c``; each is a premise of a chain lemma;
- the chain ``F0 ∧ F1 → C1``, ``C1 ∧ F2 → C2``, ..., ``C(m-1) ∧ Fm → Cm``,
  where ``Cm`` is the goal;
- ``n_extra`` **open alternatives** (the rung fixes ``n_extra = 5 m``, five per
  chain lemma): lemmas whose head is a chain head (or an
  intermediate introduced by an earlier alternative), whose body is derivable
  for ``c`` and has one premise at most one level below the head, so no route
  skips a chain level. An alternative is either one rule or a two-step detour
  through a fresh intermediate. The goal therefore has many valid routes, and
  every route is at least ``m`` steps long;
- a binary **derivation tree** of depth ``H_i`` (the rung fixes ``H_i = 2``) for
  every lemma ``i``:
  the internal node ``p`` is the two-premise axiom ``pred(p0) ∧ pred(p1) →
  pred(p)`` over fresh intermediate predicates; the ``2^H_i`` leaves are the
  lemma's body atoms (each appears at least once). The axioms derive the
  lemma's head from its body in ``2^H_i - 1`` steps, and the root axiom shares
  the lemma's head.

Names are pseudo-words drawn per seed, so nothing can be recalled. Every rule
is unique by content (head and body set). ``order`` is one shuffle of every
rule per seed; an arm shows a subset of it, so a lemma has the same position
in every arm.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass

_CONSONANTS = "bdfgklmnprstvz"
_VOWELS = "aeiou"

#: Kinds of rules a theory holds.
PATH_KINDS = frozenset({"lemma", "axiom"})
#: Kind of rule the ``disc`` control adds at render time; never part of a theory.
EXTRA_KINDS = frozenset({"disc"})

_RETIRED_FIELDS = {"open_frac": 1.0, "fact_height": 0, "fact_chain": 0, "deep_facts": []}


@dataclass(frozen=True)
class Rule:
    """One Horn rule ``body -> head`` over the variable ``x``.

    Parameters
    ----------
    key : str
        Stable internal key (``lem3``, ``ax3.r``, ``ax3.01``).
    head : str
    body : tuple[str, ...]
        One or two body predicates.
    kind : str
        ``lemma`` or ``axiom`` (``disc`` for the rules the ``disc`` arm adds).
    link : int
        1-based lemma index (``<= m`` means on the chain).
    depth : int
        Tree depth of the head node for an ``axiom`` (0 is the root, which
        shares the lemma's head); 0 for a lemma; -1 otherwise.
    """

    key: str
    head: str
    body: tuple[str, ...]
    kind: str
    link: int = 0
    depth: int = -1

    def text(self, var: str = "x") -> str:
        """Render as ``a(x) ∧ b(x) → c(x)``."""
        return " ∧ ".join(f"{b}({var})" for b in self.body) + f" → {self.head}({var})"


@dataclass
class Lemma:
    """Library lemma ``index`` and its derivation tree.

    ``node_pred`` maps a node path (``""`` root, ``"0"``/``"1"`` children, ...)
    of length ``<= height`` to its predicate. Leaves (length ``height``) are
    body atoms. ``role`` is ``chain`` or ``open`` (an alternative).
    """

    index: int
    head: str
    body: tuple[str, ...]
    height: int
    node_pred: dict[str, str]
    role: str = "chain"

    def nodes_at(self, depth: int) -> list[str]:
        """Node paths at ``depth``, in path order."""
        return sorted(p for p in self.node_pred if len(p) == depth)


@dataclass
class Theory:
    """A generated theory: facts, lemma library with trees, master order."""

    seed: int
    m: int
    height: int  # base tree depth; per-lemma depths are in ``library``
    n_extra: int
    constant: str
    facts: tuple[str, ...]
    goal: str
    library: list[Lemma]
    rules: dict[str, Rule]
    order: list[str]

    @property
    def links(self) -> list[Lemma]:
        """The ``m`` chain lemmas, in chain order."""
        return self.library[: self.m]

    @property
    def max_height(self) -> int:
        """Deepest tree in the library."""
        return max(lm.height for lm in self.library)

    def fact_atoms(self) -> list[str]:
        """Every fact as ``pred(c)``."""
        return [f"{f}({self.constant})" for f in self.facts]

    # -- keys -------------------------------------------------------------
    @staticmethod
    def lemma_key(i: int) -> str:
        """Key of lemma ``i``."""
        return f"lem{i}"

    @staticmethod
    def axiom_key(i: int, path: str) -> str:
        """Key of the axiom whose head is node ``path`` of lemma ``i``."""
        return f"ax{i}.{path or 'r'}"

    # -- views ------------------------------------------------------------
    def lemmas(self) -> list[Rule]:
        """Every library lemma (chain first)."""
        return [self.rules[self.lemma_key(lm.index)] for lm in self.library]

    def tree(self, i: int) -> list[Rule]:
        """The axioms of lemma ``i``'s derivation tree, root first."""
        lm = self.library[i - 1]
        return [
            self.rules[self.axiom_key(i, p)]
            for d in range(lm.height)
            for p in lm.nodes_at(d)
        ]

    def tree_keys(self) -> list[str]:
        """Keys of every axiom (all trees)."""
        return [r.key for i in range(1, len(self.library) + 1) for r in self.tree(i)]

    def alternatives(self) -> list[Lemma]:
        """The open alternatives (every library lemma that is not on the chain)."""
        return [lm for lm in self.library if lm.role == "open"]

    # -- io ---------------------------------------------------------------
    def to_json(self) -> str:
        """Serialize."""
        d = asdict(self)
        d["rules"] = [asdict(self.rules[k]) for k in self.rules]
        return json.dumps(d, ensure_ascii=False, indent=1)

    @classmethod
    def from_json(cls, text: str) -> Theory:
        """Deserialize.

        Files written before the setup was fixed carry fields of retired
        variants. They load when those fields hold this setup's values (one
        constant, no derivations below the facts); their partial-cut rules
        (``sublemma``), which no arm shows, are dropped. Anything else raises.
        """
        d = json.loads(text)
        for k, v in _RETIRED_FIELDS.items():
            if d.pop(k, v) != v:
                raise ValueError(f"theory.json uses a retired setup: {k}={d.get(k)!r}")
        constants = d.pop("constants", None)
        if constants and list(constants) != [d["constant"]]:
            raise ValueError("theory.json uses a retired setup: several constants")
        d.pop("facts_by_const", None)
        for lm in d["library"]:
            if lm.get("role") not in ("chain", "open"):
                raise ValueError("theory.json uses a retired setup: blocked lemmas")
        d["library"] = [
            Lemma(**{**lm, "body": tuple(lm["body"])}) for lm in d["library"]
        ]
        d["facts"] = tuple(d["facts"])
        rules: dict[str, Rule] = {}
        for r in d["rules"]:
            if r["kind"] == "sublemma":
                continue
            r["body"] = tuple(r["body"])
            rules[r["key"]] = Rule(**r)
        d["rules"] = rules
        d["order"] = [k for k in d["order"] if k in rules]
        return cls(**d)


class _Names:
    """Unique pseudo-words from one RNG."""

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.used: set[str] = set()

    def word(self, syllables: int = 2) -> str:
        """A fresh CVCV(C) word."""
        while True:
            w = "".join(
                self.rng.choice(_CONSONANTS) + self.rng.choice(_VOWELS)
                for _ in range(syllables)
            )
            if self.rng.random() < 0.5:
                w += self.rng.choice(_CONSONANTS)
            if w not in self.used:
                self.used.add(w)
                return w


def _build_tree(  # pylint: disable=too-many-arguments
    rng: random.Random,
    names: _Names,
    rules: dict[str, Rule],
    i: int,
    head: str,
    body: tuple[str, ...],
    height: int,
    role: str,
) -> Lemma:
    """Add lemma ``i`` and its binary derivation tree of depth ``height`` to ``rules``."""
    node_pred: dict[str, str] = {"": head}
    for d in range(1, height):
        for p in _paths(d):
            node_pred[p] = names.word()
    leaves = _paths(height)
    leaf_pred = [rng.choice(body) for _ in leaves]
    for k, b in enumerate(body):  # every body atom appears at least once
        if b not in leaf_pred:
            leaf_pred[k if k < len(leaf_pred) else -1] = b
    for p, pred in zip(leaves, leaf_pred):
        node_pred[p] = pred
    lm = Lemma(
        index=i, head=head, body=body, height=height, node_pred=node_pred, role=role
    )
    rules[Theory.lemma_key(i)] = Rule(Theory.lemma_key(i), head, body, "lemma", i, 0)
    for d in range(height):
        for p in lm.nodes_at(d):
            k = Theory.axiom_key(i, p)
            kids = (node_pred[p + "0"], node_pred[p + "1"])
            if kids[0] == kids[1]:  # two equal leaves: a one-premise axiom
                kids = (kids[0],)
            rules[k] = Rule(k, node_pred[p], kids, "axiom", i, d)
    return lm


def generate(  # pylint: disable=too-many-locals
    seed: int,
    m: int = 12,
    height: int = 2,
    n_extra: int = 4,
    depths: dict[int, int] | None = None,
) -> Theory:
    """Build a theory.

    Parameters
    ----------
    seed : int
    m : int
        Chain length: steps in the shortest proof.
    height : int
        Base derivation-tree depth, at least 2 (at 1 the root axiom would
        equal the lemma).
    n_extra : int
        Open alternatives to add, exactly (a detour counts as two).
    depths : dict[int, int], optional
        Per-lemma tree depth overrides (1-based lemma index -> depth >= 2);
        the token fitter uses them to meet a derivation budget.

    Returns
    -------
    Theory
    """
    if m < 1 or height < 2 or n_extra < 0:
        raise ValueError("need m >= 1, height >= 2, n_extra >= 0")
    depths = depths or {}
    if any(h < 2 for h in depths.values()):
        raise ValueError("every depth must be >= 2")
    rng = random.Random(seed)
    names = _Names(rng)
    constant = names.word(1)
    fact_preds = [names.word() for _ in range(m + 1)]
    heads = [names.word() for _ in range(m)]
    rules: dict[str, Rule] = {}
    library: list[Lemma] = []

    # Levels keep the library acyclic: facts 0, chain head i at level i, a
    # detour's intermediate half a level below its head.
    level: dict[str, float] = {f: 0.0 for f in fact_preds}
    for i, h in enumerate(heads, 1):
        level[h] = float(i)
    derivable: set[str] = set(fact_preds)
    used_sigs: set[tuple[str, frozenset[str]]] = set()

    def add(i: int, head: str, body: tuple[str, ...], role: str) -> Lemma:
        sig = (head, frozenset(body))
        assert sig not in used_sigs
        used_sigs.add(sig)
        return _build_tree(rng, names, rules, i, head, body, depths.get(i, height), role)

    for i in range(1, m + 1):
        body = (fact_preds[0] if i == 1 else heads[i - 2], fact_preds[i])
        library.append(add(i, heads[i - 1], body, "chain"))
        derivable.add(heads[i - 1])

    # Open alternatives: a second route into a head already on the way to the
    # goal. One premise sits just below the head (no level is skipped); a
    # second, if any, is any lower derivable predicate.
    targets: list[str] = list(heads)
    i = m
    guard = 0
    while len(library) < m + n_extra and guard < 50 * (n_extra + 1):
        guard += 1
        head = rng.choice(targets)
        lv = level[head]
        near = [p for p in sorted(derivable) if lv - 1 <= level[p] < lv]
        if not near:
            continue
        p1 = rng.choice(near)
        others = [p for p in sorted(derivable) if level[p] < lv and p != p1]
        body = (p1,) if not others or rng.random() < 0.3 else (p1, rng.choice(others))
        room = m + n_extra - len(library)
        if room >= 2 and rng.random() < 0.4 and lv - 0.5 > 0:
            # two-step detour through a fresh intermediate
            mid = names.word()
            level[mid] = lv - 0.5
            if (mid, frozenset(body)) in used_sigs or (head, frozenset((mid,))) in used_sigs:
                continue
            i += 1
            library.append(add(i, mid, body, "open"))
            derivable.add(mid)
            i += 1
            library.append(add(i, head, (mid,), "open"))
            targets.append(mid)
        else:
            if (head, frozenset(body)) in used_sigs:
                continue
            i += 1
            library.append(add(i, head, body, "open"))

    facts = list(fact_preds)
    rng.shuffle(facts)
    order = list(rules)
    rng.shuffle(order)
    return Theory(
        seed=seed,
        m=m,
        height=height,
        n_extra=len(library) - m,
        constant=constant,
        facts=tuple(facts),
        goal=heads[-1],
        library=library,
        rules=rules,
        order=order,
    )


def _paths(depth: int) -> list[str]:
    """All node paths at ``depth``, in path order."""
    if depth == 0:
        return [""]
    return [format(n, f"0{depth}b") for n in range(2**depth)]
