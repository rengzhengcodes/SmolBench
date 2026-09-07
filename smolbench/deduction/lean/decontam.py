"""Content-level decontamination of candidate Lean 4 training data against the eval holdout.

Matching on ``full_name`` alone misses two leak channels: a restatement of an
eval theorem under another name, and content overlap without the theorem (a
mathlib-derived corpus like LeanNavigator can reproduce an eval state or
tactic chain inside a different theorem). `HoldoutIndex` fingerprints every
eval theorem across key families -- name, statement, per-step state, tactic
chain/pair (see `Hit.key`) -- so `.check` covers all of them in one call.

The MinHash/LSH near-duplicate stage (`datasketch`, seeded) replaces a
hand-rolled one: on the 840-candidate fixture in `test_lean_decontam.py` it
detects 152/152 true near-duplicates with zero false positives among 688,
versus 150/152 before.

Deterministic and Lean-toolchain-free (pure text normalization, seeded
MinHash, no model calls, no import of `verify`), so a build is byte-reproducible
from `decontam_config.toml` alone.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from datasketch import MinHash, MinHashLSH

from . import corpus
from .context import extract_goal_only
from .corpus import Split, SplitKind
from .decontam_config import load_decontam_config

#: Decontamination policy (shingle width, MinHash/LSH params, key-length
#: floor), resolved once at import so every constant below traces back to one
#: file a run manifest can fingerprint. Memoized, so this shares one parse
#: with `premises`'s own lookup.
_CONFIG = load_decontam_config()

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


# Elaboration allocates fresh metavar ids / inaccessible-hyp counters / universe
# params per trace, so two traces of the same goal differ there even when
# equivalent; canonicalizing lets a mathlib-derived corpus's states and chains
# match the eval's. Measured on a 4.7M-row LeanNavigator scan: +29 state and
# +22 (state, tactic) matches over exact byte-match, collapsing only 4 of the
# eval's ~20.5k state variants.
_METAVAR_RE = re.compile(r"\?[\w]+(?:\.\d+)?")  # ?m.248692, ?a, ?_  -> ?m
# Superscript digits span two Unicode blocks (Latin-1 U+00B9/B2/B3, plus
# Superscripts-and-Subscripts U+2070/2074-2079), so a contiguous range would
# miss some; list all ten explicitly.
_AUTONAME_RE = re.compile(r"✝[⁰¹²³⁴⁵⁶⁷⁸⁹]*")  # inst✝⁶, x✝ (inaccessible) -> ✝
_UNIVERSE_RE = re.compile(r"\bu_\d+\b")  # universe params u_1 -> u


def normalize_text(s: str) -> str:
    """Canonicalize Lean text for fingerprinting: NFC, then the counter
    collapses above, then whitespace (incl. newlines) to one space, so
    multi-line and one-line renderings of the same state collide. Applied
    identically on index and query sides, so it can only add matches.

    Parameters
    ----------
    s : str
        Lean text to normalize.

    Returns
    -------
    str
        normalized fingerprint text.
    """
    s = unicodedata.normalize("NFC", s)
    s = _METAVAR_RE.sub("?m", s)
    s = _AUTONAME_RE.sub("✝", s)
    s = _UNIVERSE_RE.sub("u", s)
    return re.sub(r"\s+", " ", s).strip()


def state_variants(state_pp: str) -> list[str]:
    """Full state and, if different, its goal-only form (empties dropped).

    Covers a hypotheses-stripped copy of an eval state matching the eval's own
    ``stepk:0`` rendering, which is goal-only.

    Parameters
    ----------
    state_pp : str
        Pretty-printed Lean state.

    Returns
    -------
    list[str]
        Full state and, if different, its goal-only form (empties dropped).
    """
    full = normalize_text(state_pp)
    goal = normalize_text(extract_goal_only(state_pp))
    out = [v for v in (full, goal) if v]
    return out[:1] if len(out) == 2 and out[0] == out[1] else out


#: Minimum normalized length for a *goal-only* variant to become a
#: statement/state index key; rationale in ``decontam_config.toml``'s ``[keys]``
#: section.
_MIN_GOAL_KEY_CHARS = _CONFIG.keys.min_goal_key_chars


def _index_variants(state_pp: str) -> list[str]:
    """`state_variants` filtered to ones eligible as statement/state keys.

    The `_MIN_GOAL_KEY_CHARS` floor applies whenever a variant IS the goal-only
    form, including a hypothesis-free state (``⊢ False``) that collapses to
    one variant equal to its own goal-only form -- otherwise that short key
    would match every row sharing it.

    Parameters
    ----------
    state_pp : str
        Pretty-printed Lean state.

    Returns
    -------
    list[str]
        State variants eligible as statement/state keys.
    """
    goal_only = normalize_text(extract_goal_only(state_pp))
    return [
        v for v in state_variants(state_pp)
        if v != goal_only or len(v) >= _MIN_GOAL_KEY_CHARS
    ]


# ---------------------------------------------------------------------------
# MinHash / LSH near-duplicate index (statements only)
# ---------------------------------------------------------------------------

#: Character-shingle width; rationale in ``decontam_config.toml``'s
#: ``[minhash]`` section, as for every constant in this block.
_SHINGLE_N = _CONFIG.minhash.shingle_n
#: MinHash permutations, i.e. the signature length.
_NUM_PERM = _CONFIG.minhash.num_perm
#: LSH banding: `_BANDS` bands of `_ROWS` rows over the `_NUM_PERM`-slot
#: signature. `_ROWS` is derived by the loader, never configured, so the two
#: can't drift apart.
_BANDS = _CONFIG.minhash.bands
_ROWS = _CONFIG.minhash.rows
#: Final decision threshold on exact shingle-set Jaccard similarity.
_JACCARD_THRESHOLD = _CONFIG.minhash.jaccard_threshold
#: MinHash permutation seed: fixed, not caller-configurable, so every index
#: built anywhere hashes identically.
_PERM_SEED = _CONFIG.minhash.perm_seed


def _new_stmt_lsh() -> MinHashLSH:
    """Fresh, empty LSH index over statement signatures, banded per config.

    `params` must be passed explicitly: left `None`, `MinHashLSH` re-derives
    `(b, r)` from the threshold on its own -- MEASURED at this module's
    values, that gives ``(4, 15)`` instead of the configured ``(8, 8)``,
    silently discarding `decontam_config.toml`'s banding with no error raised.
    """
    return MinHashLSH(threshold=_JACCARD_THRESHOLD, num_perm=_NUM_PERM, params=(_BANDS, _ROWS))


def _shingles(text: str) -> frozenset[str]:
    """Character `_SHINGLE_N`-gram shingle set of `text` (itself, not hashed).

    Text shorter than the shingle width contributes itself as one shingle.
    Storing gram strings instead of `blake2b` digests removes a collision
    surface rather than adding one, and costs no accuracy: MEASURED over the
    840-candidate corpus in `test_lean_decontam.py`, the max Jaccard
    difference between gram-string and hashed-gram sets is exactly ``0.0``.

    Parameters
    ----------
    text : str
        Text to split into character shingles.

    Returns
    -------
    frozenset[str]
        Character shingle set.
    """
    if len(text) <= _SHINGLE_N:
        grams = [text] if text else []
    else:
        grams = [text[i : i + _SHINGLE_N] for i in range(len(text) - _SHINGLE_N + 1)]
    return frozenset(grams)


def _minhash(shingles: frozenset[str]) -> MinHash:
    """Seeded MinHash signature of a shingle set.

    Iteration order over the set doesn't matter -- a MinHash signature is an
    elementwise minimum.

    Parameters
    ----------
    shingles : frozenset[str]
        Must be non-empty: signing an empty set gives the all-max-hash
        vector, which collides with every other empty query.

    Returns
    -------
    MinHash
        Seeded MinHash signature of the shingle set.
    """
    sig = MinHash(num_perm=_NUM_PERM, seed=_PERM_SEED)
    sig.update_batch([g.encode() for g in shingles])
    return sig


def _stmt_key(full_name: str, variant_index: int) -> str:
    """Spell an ``(eval theorem, variant index)`` pair as one hashable LSH key.

    NUL-separated: no Lean identifier can contain NUL, so the encoding is
    injective and two distinct pairs can never collide into one key.
    `HoldoutIndex._stmt_variants` maps the result back to the pair.

    Parameters
    ----------
    full_name : str
        Eval theorem full name.
    variant_index : int
        Index of the statement variant.

    Returns
    -------
    str
        Hashable LSH key for the theorem and variant pair.
    """
    return f"{full_name}\x00{variant_index}"


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
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

    #: Which key family matched: "name" (K1), "statement"/"statement_near"
    #: (K2), "state" (K3), "chain"/"tactic_ngram"/"pair" (K4).
    key: str
    #: `full_name` of the eval theorem whose content matched.
    theorem: str
    #: Human-readable match description (manifests/logs), not for re-matching.
    detail: str


@dataclass
class HoldoutIndex:
    """Content fingerprints of every eval-holdout theorem.

    Build with `build`, query with `check`. Every lookup structure maps back to
    the eval theorem's ``full_name``, so a `Hit` can name its source.
    """

    #: K1: eval theorem names.
    names: set[str] = field(default_factory=set)
    #: K2: normalized step-0 state variants -> theorem name.
    statements: dict[str, str] = field(default_factory=dict)
    #: K2 near-dup: banded-LSH index over statement variants, keyed by
    #: `_stmt_key`; proposes only, `_near_statement` confirms.
    _stmt_lsh: MinHashLSH = field(default_factory=_new_stmt_lsh)
    #: K2 near-dup: shingle set of each indexed statement variant, by
    #: `_stmt_key` (used for the exact-Jaccard confirm).
    _stmt_shingles: dict[str, frozenset[str]] = field(default_factory=dict)
    #: K2 near-dup: `_stmt_key` -> the ``(theorem full_name, variant index)``
    #: pair it spells, so a `Hit` can report both after an LSH lookup.
    _stmt_variants: dict[str, tuple[str, int]] = field(default_factory=dict)
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
        cls, eval_specs: Iterable[tuple[SplitKind, Split]] | None = None
    ) -> "HoldoutIndex":
        """Index every theorem of the given eval splits.

        `eval_specs=None` resolves `corpus.eval_split_specs` at CALL time, not
        as a module-level default (which Python evaluates once at import):
        callers that repoint ``SMOLBENCH_LEAN_DATA`` mid-process need the
        corpus current at call time. An explicitly passed value is used
        verbatim, including an empty one.

        Loads via `corpus.load_split` (the whole split, a superset of
        anything a sweep could score) rather than `iter_replay_passing`, so no
        ``filter`` sidecar is needed. `load_split` is memoized on
        ``(kind, split)``, so a caller that repoints ``SMOLBENCH_LEAN_DATA``
        must also call `corpus.reset_caches` to see the new root's theorems.

        Parameters
        ----------
        eval_specs : Iterable[tuple[SplitKind, Split]] | None, optional
            Eval split specifications to index.

        Returns
        -------
        HoldoutIndex
            Index built from the eval splits.
        """
        if eval_specs is None:
            eval_specs = corpus.eval_split_specs()
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
        # K2: the statement is the step-0 state -- what an external corpus
        # would restate.
        for vi, variant in enumerate(_index_variants(t.traced_tactics[0].state_before)):
            self.statements.setdefault(variant, t.full_name)
            shingles = _shingles(variant)
            # Guard, not expected to fire: `_index_variants` already drops
            # empty variants; an empty-shingle signature would be the
            # all-max-hash vector that collides with every query.
            if not shingles:
                continue
            key = _stmt_key(t.full_name, vi)
            # First-wins, matching `statements.setdefault`. Skipped explicitly
            # because `MinHashLSH.insert` raises on a duplicate key (the old
            # band-bucket dict tolerated one); reachable only if `build` is
            # given an `eval_specs` list containing one theorem twice.
            if key in self._stmt_shingles:
                continue
            self._stmt_shingles[key] = shingles
            self._stmt_variants[key] = (t.full_name, vi)
            self._stmt_lsh.insert(key, _minhash(shingles))
        # K3 + K4b: every step's state, plus its (state, next-tactic) answer pair.
        tactics = [normalize_text(tt.tactic) for tt in t.traced_tactics]
        for tt, tactic in zip(t.traced_tactics, tactics):
            for variant in _index_variants(tt.state_before):
                self.states.setdefault(variant, t.full_name)
            for variant in state_variants(tt.state_before):
                self.pairs.setdefault((variant, tactic), t.full_name)
        # Only >=3-tactic proofs are chain-indexed: 1-2-tactic chains are
        # ubiquitous idioms (`simp`, `intro h`+`simp`) that reveal no answer,
        # and the pair key above already covers them together with the state.
        if len(tactics) >= 3:
            self.chains.setdefault("\n".join(tactics), t.full_name)
            for i in range(len(tactics) - 2):
                self.tactic_ngrams.setdefault(tuple(tactics[i : i + 3]), t.full_name)

    # -- querying -----------------------------------------------------------

    def _near_statement(self, variant: str) -> Hit | None:
        """K2 near-dup lookup of one normalized candidate statement variant.

        The LSH proposes candidates; an exact Jaccard over the stored shingle
        sets decides, so precision is exact regardless of what the banding
        surfaces. Candidates are walked in sorted key order because
        `MinHashLSH.query` returns a `set`-derived list ordered by
        PYTHONHASHSEED, and this module promises byte-reproducible results.

        Parameters
        ----------
        variant : str
            Normalized candidate statement variant.

        Returns
        -------
        Hit | None
            Matching holdout hit, if one qualifies.
        """
        shingles = _shingles(variant)
        if not shingles:
            return None
        for key in sorted(self._stmt_lsh.query(_minhash(shingles))):
            j = _jaccard(shingles, self._stmt_shingles[key])
            if j >= _JACCARD_THRESHOLD:
                theorem, variant_index = self._stmt_variants[key]
                return Hit(
                    key="statement_near",
                    theorem=theorem,
                    detail=f"jaccard={j:.3f} vs statement variant {variant_index}",
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

        Callers pass whichever facets their row has. A row should be dropped
        iff the returned list is non-empty. `statement` checks K2 (exact +
        near-dup) and K3, since a state-shaped row's "statement" may be a
        mid-proof eval state.

        Parameters
        ----------
        name : str | None, optional
            Candidate theorem name.
        statement : str | None, optional
            Candidate statement or state-shaped row.
        states : Iterable[str], optional
            Candidate proof states.
        tactics : Sequence[str], optional
            Candidate tactic chain.
        pairs : Iterable[tuple[str, str]], optional
            Candidate state and next-tactic pairs.

        Returns
        -------
        list[Hit]
            Matches across every key family.
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

        Merely invoking an eval theorem (``exact Nat.add_comm ...``) reveals
        its existence, as mathlib pretraining already does, but not its
        proof, so such rows are reported, not dropped. Matches are
        non-overlapping and identifier-bounded, so ``Nat.add_comm`` doesn't
        fire inside ``Nat.add_comm'`` or ``Foo.Nat.add_comm``.

        Parameters
        ----------
        text : str
            Text to scan for eval-theorem names.

        Returns
        -------
        int
            Number of non-overlapping, identifier-bounded name matches.
        """
        if self._name_re is None:
            # Longest-first: a name can never be shadowed by a prefix of it,
            # even if the identifier-boundary pattern below loosens later.
            alternation = "|".join(re.escape(n) for n in sorted(self.names, key=len, reverse=True))
            self._name_re = (
                re.compile(rf"(?<![\w.'])(?:{alternation})(?![\w.'])")
                if alternation
                else re.compile(r"(?!)")
            )
        return len(self._name_re.findall(text))

    def stats(self) -> dict:
        """Entry counts per key family, for manifests."""
        return {
            "names": len(self.names),
            "statements": len(self.statements),
            "states": len(self.states),
            "chains": len(self.chains),
            "tactic_ngrams": len(self.tactic_ngrams),
            "pairs": len(self.pairs),
        }
