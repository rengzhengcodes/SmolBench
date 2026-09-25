"""Generate a random Horn-rule theory: an on-path lemma library with trees.

Predicates are unary and every rule is over one variable ``x``. Facts are
atoms about several constants; the goal is about the first (main) one. The
**library** is one derivation DAG whose sink is the goal predicate: every rule
in it has a head that lies on some path to the goal, so every rule is a
statement that could be used to derive the goal for some constant.

The spine is the chain

    F0 ∧ F1 → C1,   C1 ∧ F2 → C2,   ...,   C(m-1) ∧ Fm → Cm = goal

with facts ``F`` about the main constant. Every other rule is an
**alternative** for a predicate already on the way to the goal:

- an *open* alternative is true for the main constant and gives a second
  route (``C(i-1) ∧ F0 → Ci``, or a two-step detour through a fresh
  intermediate);
- a *blocked* alternative needs a premise the main constant never has: a
  fresh intermediate predicate that only further blocked alternatives derive,
  or a decoy-only fact. Blocked alternatives are true for other constants.

A ``full`` decoy constant holds every fact, so every library rule fires for
at least one constant. Other decoys hold most chain facts (never all) and
some decoy-only facts. Integer levels keep the DAG acyclic: a rule's body
predicates all have lower level than its head.

Every lemma ``i`` has a full binary derivation tree of depth ``H_i``:
internal node ``p`` is the two-body axiom ``pred(p0) ∧ pred(p1) → pred(p)``,
the ``2^H_i`` leaves are drawn from the lemma's body atoms (each appears at
least once), and the sub-lemma of node ``p`` is ``leaves under p → pred(p)``.
The level-``j`` cut of a tree is the axioms of nodes at depth < ``j`` plus the
sub-lemmas of nodes at depth ``j`` (none when ``j >= H_i``). Depths may differ
per lemma so a token budget for the derivations can be met.

All names are pseudo-words drawn per seed so nothing can be recalled. Every
rule is unique by content (head and body set).
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field

_CONSONANTS = "bdfgklmnprstvz"
_VOWELS = "aeiou"

#: Rule kinds: every library rule is a lemma; trees hold axioms and sub-lemmas.
PATH_KINDS = frozenset({"lemma", "axiom", "sublemma"})
#: Kept for the checker's route logic; the on-path library has no distractors.
DISTRACTOR_KINDS: frozenset[str] = frozenset({"junk"})  # never on a route


@dataclass(frozen=True)
class Rule:
    """One Horn rule ``body -> head`` over the variable ``x``.

    Parameters
    ----------
    key : str
        Stable internal key (``lem1``, ``ax1.0``, ``sub1.01``, ``dead3``, ...).
    head : str
    body : tuple[str, ...]
        One or two body predicates.
    kind : str
        ``lemma``, ``axiom`` or ``sublemma``.
    link : int
        1-based lemma index (``<= m`` means on the chain).
    depth : int
        Tree depth of the head node for ``axiom``/``sublemma``; 0 for a lemma;
        -1 otherwise.
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
    body atoms.
    """

    index: int
    head: str
    body: tuple[str, ...]
    height: int
    node_pred: dict[str, str]
    role: str = "chain"  # chain | open | blocked

    def nodes_at(self, depth: int) -> list[str]:
        """Node paths at ``depth``, in path order."""
        return sorted(p for p in self.node_pred if len(p) == depth)

    def leaves_under(self, path: str) -> tuple[str, ...]:
        """Distinct leaf predicates under ``path``, in first-seen order."""
        out: list[str] = []
        for p in sorted(self.node_pred):
            if (
                len(p) == self.height
                and p.startswith(path)
                and self.node_pred[p] not in out
            ):
                out.append(self.node_pred[p])
        return tuple(out)


@dataclass
class Theory:  # pylint: disable=too-many-instance-attributes
    """A generated theory: facts, lemma library with trees, distractors, master order."""

    seed: int
    m: int
    height: int  # base tree depth; per-lemma depths are in ``library``
    n_extra: int
    open_frac: float
    constant: str
    facts: tuple[str, ...]
    goal: str
    library: list[Lemma]
    rules: dict[str, Rule]
    order: list[str] = field(default_factory=list)
    constants: tuple[str, ...] = ()
    facts_by_const: dict[str, tuple[str, ...]] = field(default_factory=dict)
    fact_height: int = 0  # depth of the derivation tree below each given fact (0: none)
    fact_chain: int = 0  # unary chain length below each fact-tree leaf
    deep_facts: tuple[str, ...] = ()  # the leaves those trees rest on (also given)

    def __post_init__(self) -> None:
        if not self.constants:
            self.constants = (self.constant,)
        if not self.facts_by_const:
            self.facts_by_const = {self.constant: tuple(self.facts)}

    @property
    def links(self) -> list[Lemma]:
        """The ``m`` chain lemmas, in chain order."""
        return self.library[: self.m]

    @property
    def max_height(self) -> int:
        """Deepest tree in the library."""
        return max(lm.height for lm in self.library)

    def fact_tree_keys(self) -> list[str]:
        """Keys of the rules that derive the given facts from deeper facts."""
        return [k for k, r in self.rules.items() if r.kind in ("factax", "factchain")]

    def fact_atoms(self) -> list[str]:
        """Every fact as ``pred(const)``, main constant first."""
        out: list[str] = []
        for c in self.constants:
            out += [f"{f}({c})" for f in self.facts_by_const[c]]
        return out

    # -- keys -------------------------------------------------------------
    @staticmethod
    def lemma_key(i: int) -> str:
        """Key of lemma ``i``."""
        return f"lem{i}"

    @staticmethod
    def axiom_key(i: int, path: str) -> str:
        """Key of the axiom whose head is node ``path`` of lemma ``i``."""
        return f"ax{i}.{path or 'r'}"

    @staticmethod
    def sublemma_key(i: int, path: str) -> str:
        """Key of the sub-lemma of node ``path``; the root's is the lemma."""
        return f"lem{i}" if path == "" else f"sub{i}.{path}"

    # -- views ------------------------------------------------------------
    def lemmas(self) -> list[Rule]:
        """Every library lemma (chain first)."""
        return [self.rules[self.lemma_key(lm.index)] for lm in self.library]

    def cut(self, i: int, j: int) -> list[Rule]:
        """Level-``j`` cut of lemma ``i``'s tree; ``j == 0`` is the lemma.

        ``j`` is clamped to the lemma's own height.
        """
        if j < 0:
            raise ValueError(f"cut level {j} < 0")
        lm = self.library[i - 1]
        j = min(j, lm.height)
        out: list[Rule] = []
        for d in range(j):
            out += [self.rules[self.axiom_key(i, p)] for p in lm.nodes_at(d)]
        if j < lm.height:
            out += [self.rules[self.sublemma_key(i, p)] for p in lm.nodes_at(j)]
        return out

    def cut_keys(self, j: int, chain_only: bool = False) -> list[str]:
        """Keys of every lemma's level-``j`` cut (chain lemmas only if asked)."""
        n = self.m if chain_only else len(self.library)
        return [r.key for i in range(1, n + 1) for r in self.cut(i, j)]

    def distractors(self) -> list[Rule]:
        """Every distractor rule (none in the on-path library)."""
        return [r for r in self.rules.values() if r.kind in DISTRACTOR_KINDS]

    def alternatives(self, role: str) -> list[Lemma]:
        """Library lemmas with ``role`` (``open`` or ``blocked``)."""
        return [lm for lm in self.library if lm.role == role]

    def cut_steps(self, j: int) -> int:
        """Designed step count of ``unf:j`` (chain lemmas, summed)."""
        total = 0
        for lm in self.links:
            jj = min(j, lm.height)
            total += (2**jj - 1) + (2**jj if jj < lm.height else 0)
        return total

    # -- io ---------------------------------------------------------------
    def to_json(self) -> str:
        """Serialize."""
        d = asdict(self)
        d["rules"] = [asdict(self.rules[k]) for k in self.rules]
        return json.dumps(d, ensure_ascii=False, indent=1)

    @classmethod
    def from_json(cls, text: str) -> Theory:
        """Deserialize."""
        d = json.loads(text)
        d["library"] = [
            Lemma(**{**lm, "body": tuple(lm["body"])}) for lm in d["library"]
        ]
        d["facts"] = tuple(d["facts"])
        d["constants"] = tuple(d.get("constants") or ())
        d["facts_by_const"] = {
            k: tuple(v) for k, v in (d.get("facts_by_const") or {}).items()
        }
        rules = {}
        for r in d["rules"]:
            r["body"] = tuple(r["body"])
            rules[r["key"]] = Rule(**r)
        d["rules"] = rules
        d["deep_facts"] = tuple(d.get("deep_facts", ()))
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
    role: str = "chain",
) -> Lemma:
    """Add lemma ``i`` with a binary derivation tree of depth ``height`` to ``rules``."""
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
            if kids[0] == kids[1]:  # two equal leaves: a one-body axiom
                kids = (kids[0],)
            rules[k] = Rule(k, node_pred[p], kids, "axiom", i, d)
            if d > 0:
                sk = Theory.sublemma_key(i, p)
                rules[sk] = Rule(sk, node_pred[p], lm.leaves_under(p), "sublemma", i, d)
    return lm


def generate(  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
    seed: int,
    m: int = 4,
    height: int = 2,
    n_extra: int = 4,
    n_unused_facts: int = 0,
    n_constants: int = 3,
    open_frac: float = 0.25,
    fact_height: int = 0,
    fact_chain: int = 0,
    depths: dict[int, int] | None = None,
) -> Theory:
    """Build a theory.

    Parameters
    ----------
    seed : int
    m : int
        Chain length: lemmas in the designed proof.
    height : int
        Base derivation-tree depth, at least 2 (at 1 the root axiom would
        equal the lemma).
    n_extra : int
        Alternative rules in the library (each on some path to the goal).
    n_unused_facts : int
        Facts nothing needs.
    n_constants : int
        Constants in the facts section: the main one, a ``full`` decoy that
        holds every fact, and partial decoys. With 1 constant every
        alternative is open.
    open_frac : float
        Fraction of alternatives that are true for the main constant.
    depths : dict[int, int], optional
        Per-lemma tree depth overrides (1-based lemma index -> depth >= 2).

    Returns
    -------
    Theory
    """
    if m < 1 or height < 2 or n_constants < 1 or not 0.0 <= open_frac <= 1.0:
        raise ValueError(
            "need m >= 1, height >= 2, n_constants >= 1, 0 <= open_frac <= 1"
        )
    depths = depths or {}
    if any(h < 2 for h in depths.values()):
        raise ValueError("every depth must be >= 2")
    if n_constants == 1:
        open_frac = 1.0
    rng = random.Random(seed)
    names = _Names(rng)
    constants = tuple(names.word(1) for _ in range(n_constants))
    constant = constants[0]
    fact_preds = [names.word() for _ in range(m + 1)]
    unused = [names.word() for _ in range(n_unused_facts)]
    heads = [names.word() for _ in range(m)]
    rules: dict[str, Rule] = {}
    library: list[Lemma] = []

    # Levels keep the DAG acyclic: facts 0, chain head i at level i.
    level: dict[str, float] = {f: 0.0 for f in fact_preds + unused}
    for i, h in enumerate(heads, 1):
        level[h] = float(i)
    main_derivable: set[str] = set(fact_preds) | set(unused)
    decoy_only: list[str] = []
    used_sigs: set[tuple[str, frozenset[str]]] = set()

    def add(i: int, head: str, body: tuple[str, ...], role: str) -> Lemma:
        sig = (head, frozenset(body))
        assert sig not in used_sigs
        used_sigs.add(sig)
        return _build_tree(
            rng, names, rules, i, head, body, depths.get(i, height), role
        )

    for i in range(1, m + 1):
        body = (fact_preds[0] if i == 1 else heads[i - 2], fact_preds[i])
        library.append(add(i, heads[i - 1], body, "chain"))
        main_derivable.add(heads[i - 1])

    # Alternatives. Targets are heads already on the way to the goal.
    targets: list[str] = list(heads)
    i = m
    guard = 0
    while len(library) < m + n_extra and guard < 50 * (n_extra + 1):
        guard += 1
        head = rng.choice(targets)
        lv = level[head]
        lower = [p for p in level if level[p] < lv]
        if head in main_derivable and rng.random() < open_frac:
            # Open: a second route for the main constant, no skipping more
            # than one level: one premise sits just below the head.
            near = [p for p in sorted(main_derivable) if lv - 1 <= level[p] < lv]
            if not near:
                continue
            p1 = rng.choice(near)
            others = [p for p in sorted(main_derivable) if level[p] < lv and p != p1]
            body = (
                (p1,) if not others or rng.random() < 0.3 else (p1, rng.choice(others))
            )
            if rng.random() < 0.4 and lv - 0.5 > 0:
                # two-step detour through a fresh open intermediate
                mid = names.word()
                level[mid] = lv - 0.5
                if (mid, frozenset(body)) in used_sigs or (
                    head,
                    frozenset((mid,)),
                ) in used_sigs:
                    continue
                i += 1
                library.append(add(i, mid, body, "open"))
                main_derivable.add(mid)
                i += 1
                library.append(add(i, head, (mid,), "open"))
                targets.append(mid)
            else:
                if (head, frozenset(body)) in used_sigs:
                    continue
                i += 1
                library.append(add(i, head, body, "open"))
            continue
        # Blocked: needs a premise the main constant never has.
        if lv - 1 >= 1 and rng.random() < 0.7:
            blocker = (
                names.word()
            )  # fresh intermediate, derived only by later blocked rules
            level[blocker] = lv - 1
            targets.append(blocker)
        else:
            if not decoy_only or rng.random() < 0.5:
                blocker = names.word()
                level[blocker] = 0.0
                decoy_only.append(blocker)
            else:
                blocker = rng.choice([d for d in decoy_only if level[d] < lv])
        lower = [q for q in lower if q != blocker]
        body = (
            (blocker,)
            if not lower or rng.random() < 0.3
            else (rng.choice(lower), blocker)
        )
        if (head, frozenset(body)) in used_sigs:
            continue
        i += 1
        library.append(add(i, head, body, "blocked"))

    # Intermediates that never received a rule become decoy-only facts, so
    # every blocked rule still fires for the full decoy.
    heads_with_rules = {lm.head for lm in library}
    for p, lv in list(level.items()):
        if (
            p not in heads_with_rules
            and p not in fact_preds
            and p not in unused
            and p not in decoy_only
        ):
            decoy_only.append(p)

    facts = list(fact_preds) + unused
    rng.shuffle(facts)
    facts_by_const: dict[str, tuple[str, ...]] = {constant: tuple(facts)}
    for k, d in enumerate(constants[1:]):
        if k == 0:  # the full decoy: every fact, so every rule fires for it
            fs = list(fact_preds) + unused + decoy_only
        else:
            keep = list(fact_preds)
            for _ in range(rng.randint(1, max(1, m // 2))):
                keep.remove(rng.choice(keep[1:]))
            fs = keep + unused + [x for x in decoy_only if rng.random() < 0.5]
        rng.shuffle(fs)
        facts_by_const[d] = tuple(fs)

    deep: list[str] = []
    if fact_height > 0:
        # Derivations below the facts: every given fact gets a binary tree of
        # depth ``fact_height`` whose leaves continue as unary chains of length
        # ``fact_chain`` down to fresh deep facts. The fact stays given, so no
        # lemma head gains a candidate; a longer valid route appears below it.
        for j, f in enumerate(list(fact_preds) + unused):
            node: dict[str, str] = {"": f}
            for d in range(1, fact_height + 1):
                for p in _paths(d):
                    node[p] = names.word()
            for d in range(fact_height):
                for p in _paths(d):
                    k = f"fax{j}.{p or 'r'}"
                    rules[k] = Rule(
                        k, node[p], (node[p + "0"], node[p + "1"]), "factax", 0, d
                    )
            for p in _paths(fact_height):
                cur = node[p]
                for s in range(fact_chain):
                    nxt = names.word()
                    k = f"fch{j}.{p}.{s}"
                    rules[k] = Rule(k, cur, (nxt,), "factchain", 0, fact_height + s)
                    cur = nxt
                deep.append(cur)
        facts = facts + deep
        rng.shuffle(facts)
        facts_by_const = {c: tuple(list(fs) + deep) for c, fs in facts_by_const.items()}
    order = list(rules)
    rng.shuffle(order)
    return Theory(
        seed=seed,
        m=m,
        height=height,
        n_extra=len(library) - m,
        open_frac=open_frac,
        constant=constant,
        facts=tuple(facts),
        goal=heads[-1],
        library=library,
        rules=rules,
        order=order,
        constants=constants,
        facts_by_const=facts_by_const,
        fact_height=fact_height,
        fact_chain=fact_chain,
        deep_facts=tuple(deep),
    )


def _paths(depth: int) -> list[str]:
    """All node paths at ``depth``, in path order."""
    if depth == 0:
        return [""]
    return [format(n, f"0{depth}b") for n in range(2**depth)]
