"""Content-level decontamination of candidate Lean 4 training data against the eval holdout.

The cheap holdout -- drop every candidate row whose ``full_name`` is an eval
theorem's -- is blind to two leak channels: a *restatement* of an eval theorem
under another name (mathlib has duplicate lemmas; an autoformalized corpus
shares no naming at all), and answer-content overlap without the theorem --
mathlib-derived corpora (e.g. LeanNavigator) reproduce eval states and tactic
chains inside *other* theorems. `HoldoutIndex` fingerprints every eval theorem;
`.check` reports which keys a candidate hits.

Key families
------------
- **K1 name** -- ``full_name`` set: the name-only holdout above, subsumed here
  so one `.check` call covers every channel.
- **K2 statement** -- normalized step-0 ``state_before``, exact *and*
  MinHash/LSH near-duplicate (catches alpha-renamed restatements).
- **K3 state** -- normalized ``state_before`` of *every* proof step, since
  sweeps stratify ``k``, making every step answer-conditional (what each rung
  exposes: ``notebooks/deduction/README.md``).
- **K4 tactic chain** -- (a) full chain plus every 3-tactic window, only for
  proofs with >= 3 tactics; (b) ``(state, next-tactic)`` pairs, the answer unit
  of the headline ``k=last`` cells. 1-2-tactic chains are deliberately NOT
  chain-indexed: ``simp`` and ``intro h``+``simp`` are ubiquitous idioms
  revealing no answer, and the pair key covers them *with* the state.

Near-duplicate index: what was measured
---------------------------------------
K2's near-duplicate stage is `datasketch`'s seeded MinHash + banded LSH,
parameterized from ``decontam_config.toml``. On the 840-candidate
near-duplicate corpus ``tests/deduction/test_lean_decontam.py`` builds
(``_LSH_BASE`` perturbed at 0..13 single-character edits, 60 draws each,
seeded), the datasketch-backed index detects 152 of the 152 candidates whose
exact shingle Jaccard is >= 0.85, with zero false positives among the 688
below it. The hand-rolled MinHash/LSH it replaces detected 150 of those 152;
the two it missed both sat at J = 0.8864, just above the decision threshold,
which is where 8x8 banding is weakest. Every decision the old index made is
reproduced, and those two are additionally caught.

Those are MEASUREMENTS on that one fixture corpus, not guarantees: the
banding's recall is probabilistic in the similarity, which is precisely why
the exact-Jaccard confirm sits behind it and is what actually decides.

Deterministic (pure text normalization, seeded MinHash, no model calls), so a
build is byte-reproducible from its manifest config. Imports only
generation-side siblings and `datasketch`, never `verify`: no Lean toolchain
needed.
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

#: The committed decontamination POLICY -- shingle width, MinHash/LSH
#: parameters, statement/state key floor -- resolved ONCE at import. Every
#: constant below is bound from it rather than spelled here, so
#: ``decontam_config.toml`` is the single place the policy is written down and
#: the single thing a run manifest's digest fingerprints; each value's
#: rationale lives beside it in that file. `load_decontam_config` is itself
#: memoized, so this shares one parse with `premises`' own lookup.
_CONFIG = load_decontam_config()

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


# Incidental tokens Lean allocates per elaboration; they differ between two
# traces of the *same* goal (different proof context, or a different mathlib
# commit -- LeanNavigator pins none), so canonicalizing them lets a
# mathlib-derived corpus's states and chains match the eval's. Measured on a full
# 4.7M-row LeanNavigator scan: +29 goal-state and +22 (state, tactic) matches
# over exact byte-match, collapsing only 4 of the eval's ~20.5k state variants --
# near-injective, so the recall costs almost no over-drop.
_METAVAR_RE = re.compile(r"\?[\w]+(?:\.\d+)?")  # ?m.248692, ?a, ?_  -> ?m
# Superscript digits span TWO Unicode blocks: ¹²³ are Latin-1 (U+00B9/B2/B3),
# ⁰⁴⁵⁶⁷⁸⁹ are Superscripts-and-Subscripts (U+2070/2074-2079) -- so a range
# class would miss ¹²³. List all ten explicitly.
_AUTONAME_RE = re.compile(r"✝[⁰¹²³⁴⁵⁶⁷⁸⁹]*")  # inst✝⁶, x✝ (inaccessible) -> ✝
_UNIVERSE_RE = re.compile(r"\bu_\d+\b")  # universe params u_1 -> u


def normalize_text(s: str) -> str:
    """Canonicalize Lean text for fingerprinting.

    In order: Unicode NFC; the three per-elaboration counter collapses above;
    then every whitespace run *including newlines* to one space, stripped, so
    multi-line and one-line renderings of a state collide. Applied identically to
    index and query sides, so the collapses can only *add* matches.
    """
    s = unicodedata.normalize("NFC", s)
    s = _METAVAR_RE.sub("?m", s)
    s = _AUTONAME_RE.sub("✝", s)
    s = _UNIVERSE_RE.sub("u", s)
    return re.sub(r"\s+", " ", s).strip()


def state_variants(state_pp: str) -> list[str]:
    """One or two normalized variants of a pretty-printed tactic state.

    Full form first, empties dropped: the full state and, when it differs, the
    goal-only block (`context.extract_goal_only`, what ``stepk:0`` renders), so a
    hypotheses-stripped copy of an eval state still collides with the eval's
    ``stepk:0`` content.
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
    """`state_variants` filtered to the ones eligible as statement/state keys.

    The `_MIN_GOAL_KEY_CHARS` floor applies to any variant that IS the state's
    goal-only form, not just to a two-variant list's second entry: a
    hypothesis-free state (``⊢ False``) collapses to ONE variant which is its
    own goal-only form, and indexing that short key would drop every training
    row sharing it. Returns ``[]`` in exactly that case -- both callers iterate.
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
#: signature. `_ROWS` is DERIVED by the loader (``num_perm // bands``, which it
#: also refuses to leave a remainder), never configured, so the two cannot
#: drift apart.
_BANDS = _CONFIG.minhash.bands
_ROWS = _CONFIG.minhash.rows
#: Final decision threshold on exact shingle-set Jaccard similarity.
_JACCARD_THRESHOLD = _CONFIG.minhash.jaccard_threshold
#: MinHash permutation seed: fixed, not caller-configurable, so every index
#: built anywhere hashes identically.
_PERM_SEED = _CONFIG.minhash.perm_seed


def _new_stmt_lsh() -> MinHashLSH:
    """A fresh, empty LSH index over statement signatures, banded per config.

    Returns
    -------
    MinHashLSH
        Threshold `_JACCARD_THRESHOLD`, `_NUM_PERM` permutations, banded
        ``(_BANDS, _ROWS)``.

    Notes
    -----
    ``params`` is passed EXPLICITLY, and that is load-bearing. Left at
    ``None``, ``MinHashLSH`` optimizes ``(b, r)`` from the threshold on its
    own; MEASURED at this module's values,
    ``MinHashLSH(threshold=0.85, num_perm=64, params=None).b, .r`` is
    ``(4, 15)`` -- which does not even cover all 64 slots -- while
    ``params=(8, 8)`` gives ``(8, 8)``. Omitting it would therefore silently
    discard the banding ``decontam_config.toml`` documents, and no error would
    be raised.

    ``(1/_BANDS) ** (1 / _ROWS)`` = ``(1/8) ** (1/8)`` ~= 0.771 is the standard
    S-curve approximation of the CANDIDATE threshold for these ``params``: the
    similarity at which a pair becomes about as likely as not to collide in
    some band. It remains true of this banding, and it sits below the 0.85
    decision threshold, which is the point of choosing it. It is an analytic
    approximation, not a recall guarantee -- for what the index actually does
    on a fixture corpus, see this module's docstring, which records the
    measured detection counts rather than leaving the approximation
    unexercised.
    """
    return MinHashLSH(threshold=_JACCARD_THRESHOLD, num_perm=_NUM_PERM, params=(_BANDS, _ROWS))


def _shingles(text: str) -> frozenset[str]:
    """Character `_SHINGLE_N`-gram shingle set of normalized `text`.

    The n-grams THEMSELVES, not hashes of them. Text shorter than the shingle
    width contributes itself as one shingle.

    Parameters
    ----------
    text : str
        Normalized text (`normalize_text` output); not normalized here.

    Returns
    -------
    frozenset of str
        Every distinct `_SHINGLE_N`-character window of `text`, or
        ``{text}`` when `text` is shorter than the window, or the empty set
        when `text` is empty.

    Notes
    -----
    These grams used to be stored as 64-bit ``blake2b`` digests, to make
    shingle sets cheap to hold. Storing the strings instead removes a
    collision surface rather than adding one, and it costs no accuracy here:
    MEASURED over the 840-candidate corpus
    ``tests/deduction/test_lean_decontam.py`` builds, the maximum absolute
    difference between the gram-string Jaccard and the blake2b-hash Jaccard is
    exactly ``0.0`` -- no decision changes.
    """
    if len(text) <= _SHINGLE_N:
        grams = [text] if text else []
    else:
        grams = [text[i : i + _SHINGLE_N] for i in range(len(text) - _SHINGLE_N + 1)]
    return frozenset(grams)


def _minhash(shingles: frozenset[str]) -> MinHash:
    """Seeded MinHash signature of a shingle set.

    Parameters
    ----------
    shingles : frozenset of str
        `_shingles` output. Must be non-empty -- callers guard, since a
        signature over no shingles is the all-max-hash vector, which is a
        meaningless index entry and a query that collides with every other
        one.

    Returns
    -------
    MinHash
        `_NUM_PERM` permutations at `_PERM_SEED`.

    Notes
    -----
    Iteration order over `shingles` (a set, so PYTHONHASHSEED-dependent) does
    not reach the result: a MinHash signature is an elementwise minimum, hence
    order-invariant by construction.
    """
    sig = MinHash(num_perm=_NUM_PERM, seed=_PERM_SEED)
    sig.update_batch([g.encode() for g in shingles])
    return sig


def _stmt_key(full_name: str, variant_index: int) -> str:
    """Spell an ``(eval theorem, statement variant)`` pair as one LSH key.

    ``MinHashLSH`` keys have to be hashable and are stored as-is, so the
    ``(full_name, variant_index)`` tuple this index is really keyed by needs a
    string spelling. `HoldoutIndex._stmt_variants` maps the result back to the
    pair, so a `Hit` still names the theorem and the variant index exactly as
    before.

    Parameters
    ----------
    full_name : str
        Eval theorem's fully-qualified Lean name.
    variant_index : int
        Index of the statement variant within `_index_variants`'s output.

    Returns
    -------
    str
        ``f"{full_name}\\x00{variant_index}"``. The separator is NUL, which no
        Lean identifier can contain, so the spelling is injective: two
        distinct pairs can never produce one key and silently share an entry.
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

    #: Which key family matched: ``"name"`` (K1), ``"statement"`` /
    #: ``"statement_near"`` (K2), ``"state"`` (K3), ``"chain"`` /
    #: ``"tactic_ngram"`` / ``"pair"`` (K4).
    key: str
    #: ``full_name`` of the eval theorem whose content matched.
    theorem: str
    #: Human-readable description of the match, with matched text truncated:
    #: for manifests/logs, not for re-matching.
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
    #: K2 near-dup: the banded-LSH index over indexed statement variants,
    #: keyed by `_stmt_key` strings. Proposes candidates only; `_near_statement`
    #: confirms each against the exact shingle sets below.
    _stmt_lsh: MinHashLSH = field(default_factory=_new_stmt_lsh)
    #: K2 near-dup: shingle set of each indexed statement variant, by
    #: `_stmt_key`. This is what makes precision exact: the LSH proposes, an
    #: exact Jaccard over these sets decides.
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

        Parameters
        ----------
        eval_specs : iterable of (SplitKind, Split), optional
            Which splits make up the holdout. ``None`` (the default) resolves
            `corpus.eval_split_specs` at CALL time -- deliberately not spelled
            as a module-level default argument, which Python evaluates once at
            import and would freeze whichever corpus that first import saw.
            Several callers repoint ``SMOLBENCH_LEAN_DATA`` mid-process, so the
            active corpus is not knowable until the call happens. An explicitly
            passed value is used verbatim, INCLUDING an empty one: a caller that
            asks for an empty holdout gets an empty index rather than a silent
            substitution of the corpus default.

        Returns
        -------
        HoldoutIndex
            Populated across every key family; theorems without traced tactics
            contribute their name (K1) only.

        Raises
        ------
        FileNotFoundError
            Propagated from `corpus.eval_split_specs` (default path only) or
            `corpus.load_split`: the corpus is not bootstrapped.
        ValueError
            Propagated from `corpus.eval_split_specs` (default path only): the
            corpus directory holds no recognised split file.

        Notes
        -----
        Loads via `corpus.load_split` -- the WHOLE split, not
        `corpus.iter_replay_passing`. That is the stricter of the two: a sweep
        can only score replay-passing theorems, so the whole split is a superset
        of everything that could leak, and the index needs no ``filter`` sidecar
        to exist.

        Only the SPEC list is re-read per call. `corpus.load_split` is memoized
        on ``(kind, split)`` alone, so a caller that repoints
        ``SMOLBENCH_LEAN_DATA`` mid-process must also call
        `corpus.reset_caches` to get the new root's theorems -- otherwise the
        specs are fresh and the rows behind them are not.
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
            # Guard, not an expected case: `_index_variants` drops empty
            # variants, so this cannot fire today. A signature over no shingles
            # would be the all-max-hash vector, which every empty query would
            # collide with.
            if not shingles:
                continue
            key = _stmt_key(t.full_name, vi)
            # First-wins, matching `statements.setdefault` above. `MinHashLSH`
            # RAISES on a duplicate key where the old band-bucket dict tolerated
            # one (it re-appended, and the caller's `seen` set deduped), so the
            # re-indexing this skips has to be skipped explicitly. It reaches
            # here whenever one theorem is indexed twice -- the same
            # ``full_name`` appearing in two of the holdout's splits.
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
        # K4a: full chain + 3-windows, only for >= 3-tactic proofs (see
        # module docstring for why shorter chains are pair-covered instead).
        if len(tactics) >= 3:
            self.chains.setdefault("\n".join(tactics), t.full_name)
            for i in range(len(tactics) - 2):
                self.tactic_ngrams.setdefault(tuple(tactics[i : i + 3]), t.full_name)

    # -- querying -----------------------------------------------------------

    def _near_statement(self, variant: str) -> Hit | None:
        """K2 near-dup lookup of one normalized candidate statement variant.

        The LSH proposes candidates; an EXACT Jaccard over the stored shingle
        sets decides, so precision is exact by construction -- an
        under-threshold candidate can never be reported, however the banding
        surfaced it.

        Candidates are walked in SORTED key order. ``MinHashLSH.query``
        collects them into a ``set`` and returns ``list(candidates)``, whose
        order depends on PYTHONHASHSEED; without the sort, an index holding two
        statements that both clear the threshold could report either one, and
        this module promises byte-reproducible results. (The old band-major
        walk was also deterministic but ordered differently, so which of
        several qualifying theorems gets reported can differ from before.)
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

        Callers pass whichever facets their row has; any may be omitted. A row
        should be **dropped** iff the returned list is non-empty.

        Parameters
        ----------
        name : str, optional
            K1.
        statement : str, optional
            K2 exact + near-dup, and K3: a state-shaped row's "statement" may be
            a mid-proof eval state.
        states : iterable of str, optional
            K3, exact only.
        tactics : sequence of str, optional
            K4a; expected in proof order.
        pairs : iterable of (str, str), optional
            K4b, ``(state, next tactic)``.

        Returns
        -------
        list of Hit
            One per matched key family; empty means keep the row.
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

        A row that merely *invokes* an eval theorem (``exact Nat.add_comm ...``)
        reveals its existence -- as mathlib pretraining already does -- but not
        its proof, so it is **not** dropped; builders report this count in their
        manifest instead. Occurrences are non-overlapping and identifier-bounded,
        so ``Nat.add_comm`` fires inside neither ``Nat.add_comm'`` nor
        ``Foo.Nat.add_comm``.
        """
        if self._name_re is None:
            # Longest-first so a name can never be shadowed by a prefix of it,
            # should the identifier boundaries in the pattern below ever loosen.
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
