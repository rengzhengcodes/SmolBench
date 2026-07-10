"""Content-level decontamination of Lean 4 SFT data against the eval holdout.

`smolbench.deduction.lean.sft` holds eval theorems out of training **by
``full_name``** -- sufficient within LeanDojo Benchmark 4's own splits (the
``random`` and ``novel_premises`` kinds partition one shared theorem pool),
but blind to two leak channels:

1. **Same statement, different name.** Mathlib contains duplicate lemmas;
   an external corpus (autoformalized or machine-generated) shares no
   naming with mathlib at all, so a restatement of an eval theorem passes
   a name-based holdout untouched.
2. **Answer-content overlap without the theorem.** The eval's context
   rungs expose, per theorem, its goal states at every step ``k``, its
   tactic prefix, and its ground-truth tactic tail
   (see ``notebooks/lean/README.md``). Mathlib-derived synthetic corpora
   (e.g. LeanNavigator's state-graph traversal) can reproduce exactly
   those states and tactic chains inside *other* theorems.

This module closes both: `HoldoutIndex` fingerprints every eval theorem's
statement, per-step goal states, and tactic chains, and `HoldoutIndex.check`
reports which (if any) of those keys a candidate training example hits.

Key families
------------
- **K1 name** -- ``full_name`` set (the existing `sft.eval_holdout_names`
  behavior, kept for rows that carry a declaration name).
- **K2 statement** -- normalized step-0 ``state_before`` (full text and
  goal-only variant), matched exactly *and* by MinHash/LSH near-duplicate
  (catches alpha-renamed restatements).
- **K3 goal state** -- exact hash of the normalized ``state_before`` of
  **every** proof step of every eval theorem (sweeps stratify ``k``, so
  every step is answer-conditional, not just step 0).
- **K4 tactic chain** -- (a) the full normalized tactic chain, and any
  3-consecutive-tactic window of it, for eval proofs with >= 3 tactics;
  (b) ``(state, next-tactic)`` pairs -- the exact answer unit of the
  headline ``k=last`` cells. Chains of 1-2 tactics are deliberately NOT
  chain-indexed: single tactics (``simp``) and short generic runs
  (``intro h`` + ``simp``) are ubiquitous idioms whose match reveals no
  answer; the pair key covers them *with* their state, which is the part
  that makes them answer-conditional.

Everything is deterministic -- normalization is pure text processing, the
MinHash permutations are seeded, and no model/embedding calls are made --
so a dataset build is reproducible byte-for-byte from its manifest config.

Like `sft`, this module imports only generation-side siblings (`corpus`,
`context`) -- never `verify` -- so it runs on the main 3.14 venv; no Lean
toolchain is needed to decontaminate a dataset.
"""

from __future__ import annotations

import hashlib
import random
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from . import corpus
from .context import extract_goal_only
from .corpus import Split, SplitKind
from .sft import DEFAULT_EVAL_SPECS

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


# Incidental, context-specific tokens that Lean allocates deterministically
# per elaboration but which differ between two traces of the *same* goal
# (different proof context, or a different mathlib commit -- LeanNavigator
# pins none). Canonicalizing them lets a mathlib-derived corpus's goal states
# and tactic chains match the eval's even when these counters diverge. On a
# full 4.7M-row LeanNavigator scan this recovered 29 goal-state and 22
# (state, tactic) matches that exact byte-match missed, while collapsing only
# 4 of the eval's ~20.5k state variants -- i.e. near-injective on real states,
# so the added recall costs almost no over-drop.
_METAVAR_RE = re.compile(r"\?[\w]+(?:\.\d+)?")  # ?m.248692, ?a, ?_  -> ?m
# Superscript digits span TWO Unicode blocks: ¹²³ are Latin-1 (U+00B9/B2/B3),
# ⁰⁴⁵⁶⁷⁸⁹ are Superscripts-and-Subscripts (U+2070/2074-2079) -- so a range
# class would miss ¹²³. List all ten explicitly.
_AUTONAME_RE = re.compile(r"✝[⁰¹²³⁴⁵⁶⁷⁸⁹]*")  # inst✝⁶, x✝ (inaccessible) -> ✝
_UNIVERSE_RE = re.compile(r"\bu_\d+\b")  # universe params u_1 -> u


def normalize_text(s: str) -> str:
    """Canonicalize Lean text for fingerprinting.

    Steps, in order:

    1. Unicode NFC (so composed/decomposed forms of e.g. ``ℕ`` collide).
    2. Collapse incidental per-elaboration counters that carry no semantic
       meaning but differ between two traces of the same goal:
       metavariables (``?m.248692`` -> ``?m``), inaccessible-hypothesis
       autoname suffixes (``inst✝⁶`` -> ``inst✝``), and fresh universe
       parameters (``u_1`` -> ``u``). See `_METAVAR_RE` et al. for why.
    3. Collapse every whitespace run -- including newlines, so multi-line
       goal states and one-line renderings of the same state collide --
       to a single space, then strip.

    Parameters
    ----------
    s : str
        Raw statement / goal-state / tactic text.

    Returns
    -------
    str
        The normalized form used by every exact-match key in this module.
        Applied identically to index and query sides, so the collapses
        above can only *add* matches, never desynchronize the two.
    """
    s = unicodedata.normalize("NFC", s)
    s = _METAVAR_RE.sub("?m", s)
    s = _AUTONAME_RE.sub("✝", s)
    s = _UNIVERSE_RE.sub("u", s)
    return re.sub(r"\s+", " ", s).strip()


def state_variants(state_pp: str) -> list[str]:
    """Normalized matchable variants of a pretty-printed tactic state.

    Returns the normalized full state and, when it differs, the normalized
    goal-only block (`context.extract_goal_only` -- what ``stepk:0``
    renders). Indexing/checking both means a hypotheses-stripped copy of an
    eval state still collides with the eval's ``stepk:0`` rung content.

    Parameters
    ----------
    state_pp : str
        A Lean tactic-state pretty-print (or a bare goal expression).

    Returns
    -------
    list of str
        One or two normalized strings, full form first. Empty strings are
        dropped.
    """
    full = normalize_text(state_pp)
    goal = normalize_text(extract_goal_only(state_pp))
    out = [v for v in (full, goal) if v]
    return out[:1] if len(out) == 2 and out[0] == out[1] else out


#: Minimum normalized length for a *goal-only* variant to become a
#: statement/state index key. Bare goals shorter than this (``⊢ False``,
#: ``⊢ a = b``) recur across unrelated theorems all over mathlib -- they
#: identify nothing, and indexing them would mass-drop harmless training
#: rows. The full-state variant (hypotheses included) is always indexed,
#: and `pairs` keys keep even short goal variants: a (state, tactic) match
#: must reproduce the eval cell's *answer*, which is answer-conditional at
#: any length.
_MIN_GOAL_KEY_CHARS = 24


def _index_variants(state_pp: str) -> list[str]:
    """`state_variants` filtered to the ones eligible as statement/state keys."""
    variants = state_variants(state_pp)
    if len(variants) == 2 and len(variants[1]) < _MIN_GOAL_KEY_CHARS:
        return variants[:1]
    return variants


# ---------------------------------------------------------------------------
# MinHash / LSH near-duplicate index (statements only)
# ---------------------------------------------------------------------------

#: Character-shingle width for MinHash. 5 chars spans roughly one Lean token
#: plus its neighborhood, so renaming one hypothesis perturbs only the
#: shingles that touch it -- the signature stays close for alpha-renames.
_SHINGLE_N = 5
#: MinHash permutations. 64 keeps signatures cheap while the band structure
#: below puts the LSH candidate threshold safely under `_JACCARD_THRESHOLD`.
_NUM_PERM = 64
#: LSH banding: 8 bands x 8 rows over the 64-slot signature. Candidate
#: recall threshold ~ (1/8)^(1/8) ~= 0.77 -- below the decision threshold,
#: so true near-dups at 0.85 are reliably surfaced as candidates and then
#: confirmed by exact Jaccard (no false drops from LSH alone).
_BANDS = 8
_ROWS = _NUM_PERM // _BANDS
#: Final decision threshold on exact shingle-set Jaccard similarity.
_JACCARD_THRESHOLD = 0.85
#: Mersenne prime for the universal-hash permutations.
_MERSENNE = (1 << 61) - 1
#: Seed for the permutation parameters. Fixed (not caller-configurable) so
#: every index built anywhere hashes identically; the value is arbitrary.
_PERM_SEED = 1776


def _perm_params() -> list[tuple[int, int]]:
    """The seeded ``(a, b)`` parameters of the 64 universal-hash permutations."""
    rng = random.Random(_PERM_SEED)
    return [(rng.randrange(1, _MERSENNE), rng.randrange(0, _MERSENNE)) for _ in range(_NUM_PERM)]


_PERMS = _perm_params()


def _shingles(text: str) -> frozenset[int]:
    """Hashed character `_SHINGLE_N`-gram shingle set of normalized `text`.

    Each shingle is reduced to a 64-bit ``blake2b`` integer (stable across
    processes and Python versions, unlike built-in ``hash``); the MinHash
    permutations then act on these integers. Texts shorter than the shingle
    width contribute their whole text as a single shingle.
    """
    if len(text) <= _SHINGLE_N:
        grams = [text] if text else []
    else:
        grams = [text[i : i + _SHINGLE_N] for i in range(len(text) - _SHINGLE_N + 1)]
    return frozenset(
        int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "big")
        for g in grams
    )


def _signature(shingles: frozenset[int]) -> tuple[int, ...] | None:
    """MinHash signature of a shingle set (None for an empty set)."""
    if not shingles:
        return None
    return tuple(min((a * s + b) % _MERSENNE for s in shingles) for a, b in _PERMS)


def _jaccard(a: frozenset[int], b: frozenset[int]) -> float:
    """Exact Jaccard similarity of two shingle sets."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------------------
# The holdout index
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Hit:
    """One decontamination-key match found by `HoldoutIndex.check`."""

    #: Which key family matched: ``"name"`` (K1), ``"statement"`` /
    #: ``"statement_near"`` (K2), ``"state"`` (K3), ``"chain"`` /
    #: ``"tactic_ngram"`` / ``"pair"`` (K4).
    key: str
    #: ``full_name`` of the eval theorem whose content matched.
    theorem: str
    #: Short human-readable description of what matched (matched text is
    #: truncated -- this is for manifests/logs, not for re-matching).
    detail: str


@dataclass
class HoldoutIndex:
    """Content fingerprints of every eval-holdout theorem.

    Build with `HoldoutIndex.build`; query with `check`. All lookup
    structures map back to the eval theorem's ``full_name`` so a `Hit`
    can name its source.
    """

    #: K1: eval theorem names.
    names: set[str] = field(default_factory=set)
    #: K2: normalized step-0 state variants -> theorem name.
    statements: dict[str, str] = field(default_factory=dict)
    #: K2 near-dup: shingle sets of each indexed statement variant, keyed by
    #: (theorem name, variant index) -- the LSH buckets point into this.
    _stmt_shingles: dict[tuple[str, int], frozenset[int]] = field(default_factory=dict)
    #: K2 near-dup: LSH band buckets -> the statement keys hashed there.
    _lsh: dict[tuple[int, tuple[int, ...]], list[tuple[str, int]]] = field(default_factory=dict)
    #: K3: normalized state variants (every step k) -> theorem name.
    states: dict[str, str] = field(default_factory=dict)
    #: K4a: normalized full tactic chains (>= 3 tactics) -> theorem name.
    chains: dict[str, str] = field(default_factory=dict)
    #: K4a: 3-consecutive-tactic windows -> theorem name.
    tactic_ngrams: dict[tuple[str, str, str], str] = field(default_factory=dict)
    #: K4b: (normalized state, normalized next tactic) pairs -> theorem name.
    pairs: dict[tuple[str, str], str] = field(default_factory=dict)
    #: Compiled alternation over `names` for mention *counting* (see
    #: `count_name_mentions`); built lazily on first use.
    _name_re: re.Pattern | None = field(default=None, repr=False)

    # -- construction -------------------------------------------------------

    @classmethod
    def build(
        cls, eval_specs: Iterable[tuple[SplitKind, Split]] = DEFAULT_EVAL_SPECS
    ) -> "HoldoutIndex":
        """Index every theorem of the given eval splits.

        Parameters
        ----------
        eval_specs : iterable of (kind, split)
            Splits whose theorems' content must never appear in training;
            default `sft.DEFAULT_EVAL_SPECS` (``novel_premises`` val+test).
            Loaded via `corpus.load_split` -- the *whole* split, matching
            `sft.eval_holdout_names`' stricter-than-replay-passing stance.

        Returns
        -------
        HoldoutIndex
            The populated index. Theorems without traced tactics still
            contribute their name (K1); they have no recorded states or
            tactics to index.
        """
        idx = cls()
        for kind, split in eval_specs:
            for t in corpus.load_split(kind, split):
                idx._add_theorem(t)
        return idx

    def _add_theorem(self, t: corpus.BenchmarkTheorem) -> None:
        """Fingerprint one eval theorem into every key family."""
        self.names.add(t.full_name)
        if not t.traced_tactics:
            return
        # K2: the statement is the step-0 state (what stepk:0/1 render at
        # the start of the proof, and what an external corpus would restate).
        for vi, variant in enumerate(_index_variants(t.traced_tactics[0].state_before)):
            self.statements.setdefault(variant, t.full_name)
            shingles = _shingles(variant)
            sig = _signature(shingles)
            if sig is not None:
                key = (t.full_name, vi)
                self._stmt_shingles[key] = shingles
                for band in range(_BANDS):
                    bucket = (band, sig[band * _ROWS : (band + 1) * _ROWS])
                    self._lsh.setdefault(bucket, []).append(key)
        # K3 + K4b: every step's state (and its goal-only variant), plus the
        # (state, next-tactic) answer pair.
        tactics = [normalize_text(tt.tactic) for tt in t.traced_tactics]
        for tt, tactic in zip(t.traced_tactics, tactics):
            for variant in _index_variants(tt.state_before):
                self.states.setdefault(variant, t.full_name)
            for variant in state_variants(tt.state_before):
                self.pairs.setdefault((variant, tactic), t.full_name)
        # K4a: full chain + 3-windows, only for >= 3-tactic proofs (see
        # module docstring for why shorter chains are pair-covered instead).
        if len(tactics) >= 3:
            self.chains.setdefault("\n".join(tactics), t.full_name)
            for i in range(len(tactics) - 2):
                self.tactic_ngrams.setdefault(tuple(tactics[i : i + 3]), t.full_name)

    # -- querying -----------------------------------------------------------

    def _near_statement(self, variant: str) -> Hit | None:
        """K2 near-dup lookup of one normalized candidate statement variant."""
        shingles = _shingles(variant)
        sig = _signature(shingles)
        if sig is None:
            return None
        seen: set[tuple[str, int]] = set()
        for band in range(_BANDS):
            bucket = (band, sig[band * _ROWS : (band + 1) * _ROWS])
            for key in self._lsh.get(bucket, ()):
                if key in seen:
                    continue
                seen.add(key)
                j = _jaccard(shingles, self._stmt_shingles[key])
                if j >= _JACCARD_THRESHOLD:
                    return Hit(
                        key="statement_near",
                        theorem=key[0],
                        detail=f"jaccard={j:.3f} vs statement variant {key[1]}",
                    )
        return None

    def check(
        self,
        *,
        name: str | None = None,
        statement: str | None = None,
        states: Iterable[str] = (),
        tactics: Sequence[str] = (),
        pairs: Iterable[tuple[str, str]] = (),
    ) -> list[Hit]:
        """Check one candidate training example against every key family.

        Callers pass whichever facets their corpus row has; any facet may
        be omitted. A row should be **dropped** iff the returned list is
        non-empty.

        Parameters
        ----------
        name : str, optional
            The row's declaration name, if it has one (K1).
        statement : str, optional
            The row's theorem statement / initial goal text (K2: exact and
            near-dup; also checked against K3, since a "statement" of a
            state-shaped corpus row may be a mid-proof eval state).
        states : iterable of str
            Any goal states embedded in the row -- e.g. the rendered
            ``stepk`` state of a state->tactic example (K3; exact only).
        tactics : sequence of str
            The row's target tactic lines, in order (K4a: full-chain match
            for >= 3 tactics, plus every 3-consecutive window).
        pairs : iterable of (str, str)
            ``(state, tactic)`` pairs the row teaches -- for state-shaped
            rows, the state with the first target tactic (K4b).

        Returns
        -------
        list of Hit
            Every key match found (deduplicated per family), empty when
            the row is clean.
        """
        hits: list[Hit] = []
        if name is not None and name in self.names:
            hits.append(Hit(key="name", theorem=name, detail="full_name in holdout"))
        if statement is not None:
            for variant in state_variants(statement):
                owner = self.statements.get(variant)
                if owner is not None:
                    hits.append(Hit(key="statement", theorem=owner, detail="exact statement match"))
                    break
                owner = self.states.get(variant)
                if owner is not None:
                    hits.append(Hit(key="state", theorem=owner, detail="statement matches a step-k state"))
                    break
                near = self._near_statement(variant)
                if near is not None:
                    hits.append(near)
                    break
        for s in states:
            for variant in state_variants(s):
                owner = self.states.get(variant)
                if owner is not None:
                    hits.append(Hit(key="state", theorem=owner, detail="step-k state match"))
                    break
            else:
                continue
            break
        if tactics:
            norm = [normalize_text(t) for t in tactics if normalize_text(t)]
            if len(norm) >= 3:
                owner = self.chains.get("\n".join(norm))
                if owner is not None:
                    hits.append(Hit(key="chain", theorem=owner, detail="full tactic chain match"))
                for i in range(len(norm) - 2):
                    owner = self.tactic_ngrams.get(tuple(norm[i : i + 3]))
                    if owner is not None:
                        hits.append(
                            Hit(key="tactic_ngram", theorem=owner, detail=f"3-gram at tactic {i}")
                        )
                        break
        for state, tactic in pairs:
            found = False
            for variant in state_variants(state):
                owner = self.pairs.get((variant, normalize_text(tactic)))
                if owner is not None:
                    hits.append(Hit(key="pair", theorem=owner, detail="(state, tactic) answer pair"))
                    found = True
                    break
            if found:
                break
        return hits

    def count_name_mentions(self, text: str) -> int:
        """Count eval-theorem names appearing *inside* `text` (report-only).

        A synthetic proof that merely *invokes* an eval theorem as a premise
        (``exact Nat.add_comm ...``) reveals the eval theorem's existence --
        which pretraining on mathlib already does -- but not its proof, so
        such rows are **not** dropped; builders report this count in their
        manifest for transparency instead.

        Parameters
        ----------
        text : str
            Any row text (statement + proof).

        Returns
        -------
        int
            Number of (non-overlapping) holdout-name occurrences, matched
            with identifier boundaries so ``Nat.add_comm`` does not fire
            inside ``Nat.add_comm'`` or ``Foo.Nat.add_comm``.
        """
        if self._name_re is None:
            # Longest-first so a name that prefixes another (Foo.bar vs
            # Foo.bar_baz would otherwise be reachable if boundaries ever
            # loosen) can never be shadowed by its prefix.
            alternation = "|".join(re.escape(n) for n in sorted(self.names, key=len, reverse=True))
            self._name_re = (
                re.compile(rf"(?<![\w.'])(?:{alternation})(?![\w.'])")
                if alternation
                else re.compile(r"(?!)")
            )
        return len(self._name_re.findall(text))

    def stats(self) -> dict:
        """Sizes of every key family, for manifests.

        Returns
        -------
        dict
            ``{"names", "statements", "states", "chains", "tactic_ngrams",
            "pairs"}`` -> entry counts.
        """
        return {
            "names": len(self.names),
            "statements": len(self.statements),
            "states": len(self.states),
            "chains": len(self.chains),
            "tactic_ngrams": len(self.tactic_ngrams),
            "pairs": len(self.pairs),
        }
