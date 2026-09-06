"""The decontamination POLICY lives in a committed TOML, not in code constants.

`decontam.py` used to spell the near-duplicate parameters as private module
constants (`_SHINGLE_N`, `_NUM_PERM`, `_BANDS`, `_JACCARD_THRESHOLD`,
`_PERM_SEED`, `_MIN_GOAL_KEY_CHARS`), and `premises.py` carried `_LEAN_NOISE`,
a hand-maintained stoplist that decides which identifiers resolve to premise
references -- and therefore what the `hint:3` and `hint:4` rungs actually
contain. Both are policy: they decide what a run CONTAINS, not how it is
computed.

These tests pin three things:

* the parsed values still equal the ones the code carried, so moving them to a
  file was not a re-tuning in disguise;
* every structural defect a hand-edit of that file could introduce is REFUSED
  at load, naming the offending value, rather than silently changing what a
  decontamination pass drops;
* the digest recorded in a run's manifest is the digest of the file's raw
  bytes.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

import smolbench.deduction.lean.premises as premises
from smolbench.deduction.lean.decontam_config import load_decontam_config
from tests._paths import REPO_ROOT

CONFIG_PATH = (
    Path(premises.__file__).resolve().with_name("decontam_config.toml")
)

#: The values `decontam.py`/`premises.py` carried as code constants before the
#: move. Pinned as literals HERE, on purpose: reading them back out of the file
#: under test would make this assertion vacuous, and the point of the pin is
#: that relocating a constant did not change it.
EXPECTED_MINHASH = {
    "shingle_n": 5,
    "num_perm": 64,
    "bands": 8,
    "rows": 8,  # DERIVED: num_perm // bands, never configured twice
    "jaccard_threshold": 0.85,
    "perm_seed": 1776,
}
EXPECTED_MIN_GOAL_KEY_CHARS = 24


def _write_config(tmp_path: Path, mutate) -> Path:
    """A scratch copy of the committed TOML with `mutate` applied to its text."""
    path = tmp_path / "decontam_config.toml"
    path.write_text(mutate(CONFIG_PATH.read_text()))
    return path


def test_parsed_policy_equals_the_constants_it_replaced():
    cfg = load_decontam_config()
    got = {
        "shingle_n": cfg.minhash.shingle_n,
        "num_perm": cfg.minhash.num_perm,
        "bands": cfg.minhash.bands,
        "rows": cfg.minhash.rows,
        "jaccard_threshold": cfg.minhash.jaccard_threshold,
        "perm_seed": cfg.minhash.perm_seed,
    }
    assert got == EXPECTED_MINHASH
    assert cfg.keys.min_goal_key_chars == EXPECTED_MIN_GOAL_KEY_CHARS


#: The 97 entries `premises._LEAN_NOISE` held as a hand-written frozenset before
#: the move to config, FROZEN here as a literal.
#:
#: Not read back out of the file under test (that would be vacuous) and not
#: recovered from ``git show HEAD:...`` either: HEAD carried the pre-move
#: literal only until the move was committed, after which such a test SKIPS
#: forever and silently stops checking anything. This list was verified equal
#: to that literal, by exact set comparison, at the commit immediately before
#: the move; freezing it is what keeps the check live.
#:
#: This set decides which identifiers resolve to premise references and so what
#: the `hint:3`/`hint:4` rungs CONTAIN. An entry silently dropped or added here
#: changes prompt content across the whole study, which is why it is pinned
#: entry-by-entry rather than by count.
PRE_MOVE_LEAN_NOISE = frozenset({
    'False', 'Prop', 'Set', 'Sort', 'True', 'Type', 'abbrev', 'all_goals',
    'and', 'any_goals', 'apply', 'assumption', 'attribute', 'axiom', 'by',
    'cases', 'class', 'constructor', 'decide', 'def', 'deriving', 'do',
    'elab', 'else', 'end', 'eq', 'exact', 'example', 'exists', 'false',
    'field_simp', 'forall', 'from', 'fun', 'ge', 'gt', 'h1', 'h2', 'h3',
    'have', 'id', 'if', 'iff', 'import', 'in', 'inductive', 'instance',
    'intro', 'intros', 'le', 'lemma', 'let', 'linarith', 'lt', 'macro',
    'match', 'mutual', 'namespace', 'ne', 'nlinarith', 'noncomputable',
    'not', 'obtain', 'of', 'omega', 'open', 'or', 'partial', 'private',
    'protected', 'rcases', 'refine', "refine'", 'rewrite', 'rfl', 'ring',
    'rintro', 'rw', 'section', 'set_option', 'show', 'simp', 'split',
    'structure', 'syntax', 'tauto', 'then', 'theorem', 'this', 'to',
    'trivial', 'true', 'use', 'variable', 'variables', 'where', 'with'
})


def test_the_stoplist_is_membership_identical_to_the_one_it_replaced():
    """`lean_noise` is exactly the stoplist `premises` carried before the move."""
    assert load_decontam_config().lean_noise == PRE_MOVE_LEAN_NOISE
    assert premises._LEAN_NOISE == PRE_MOVE_LEAN_NOISE


def test_the_digest_is_over_the_files_raw_bytes():
    """Comments included: they are part of what a run's provenance record claims."""
    assert load_decontam_config().sha256 == hashlib.sha256(
        CONFIG_PATH.read_bytes()).hexdigest()


def test_the_config_is_loaded_once_per_resolved_path():
    """Memoized: `lean_noise` is consulted per token inside `referenced_premises`."""
    assert load_decontam_config() is load_decontam_config()
    assert load_decontam_config(CONFIG_PATH) is load_decontam_config()


@pytest.mark.parametrize("mutate, expected", [
    pytest.param(lambda s: s.replace("num_perm = 64", "num_perm = 65"),
                 "65", id="bands-do-not-partition-num_perm"),
    pytest.param(lambda s: s.replace("jaccard_threshold = 0.85",
                                     "jaccard_threshold = 1.5"),
                 "1.5", id="threshold-above-one"),
    pytest.param(lambda s: s.replace("jaccard_threshold = 0.85",
                                     "jaccard_threshold = 0.0"),
                 "0.0", id="threshold-at-zero"),
    pytest.param(lambda s: s.replace("shingle_n = 5", "shingle_n = 0"),
                 "0", id="zero-shingle-width"),
    pytest.param(lambda s: s.replace('"theorem", "lemma"', '"theorem", "theorem"'),
                 "theorem", id="duplicate-stoplist-entry"),
])
def test_a_structurally_broken_config_is_refused_by_value(tmp_path, mutate, expected):
    """Every refusal names the offending VALUE, not just the section.

    A near-duplicate policy that loads with a silently corrected parameter is
    worse than one that will not load: it keeps dropping rows, just not the
    ones anyone reviewed. The duplicate case matters for its own reason --
    `lean_noise` becomes a set, so set-ification would hide a bad merge unless
    the duplicate is caught before it.
    """
    with pytest.raises(ValueError, match=re.escape(expected)):
        load_decontam_config(_write_config(tmp_path, mutate))


def test_an_empty_stoplist_is_refused(tmp_path):
    """An empty stoplist would let every Lean keyword resolve as a premise."""
    def _empty(source: str) -> str:
        return re.sub(r"lean_noise = \[.*?\n\]", "lean_noise = []", source, flags=re.S)

    with pytest.raises(ValueError, match="lean_noise"):
        load_decontam_config(_write_config(tmp_path, _empty))


def test_a_missing_section_or_key_is_refused_by_name(tmp_path):
    with pytest.raises(ValueError, match=r"\[minhash\]"):
        load_decontam_config(
            _write_config(tmp_path, lambda s: s.replace("[minhash]", "[nothash]")))
    with pytest.raises(ValueError, match="perm_seed"):
        load_decontam_config(
            _write_config(tmp_path, lambda s: s.replace("perm_seed = 1776", "")))


def test_the_config_module_imports_only_the_standard_library():
    """It is a LEAF module, which is what lets `premises` import it.

    `decontam` -> `context` -> `premises` already exists, so a `premises` ->
    `decontam` edge would close a cycle. Keeping the loader stdlib-only is what
    makes that a non-question rather than an import-order hazard.
    """
    import smolbench.deduction.lean.decontam_config as module

    source = Path(module.__file__).read_text()
    offenders = [
        line for line in source.splitlines()
        if re.match(r"\s*(import|from)\s+(smolbench|datasketch|numpy|yaml)\b", line)
    ]
    assert not offenders, offenders


@pytest.mark.parametrize("entry, why", [
    ("x", "one character: referenced_premises's `len(tok) <= 1` arm drops it "
           "whether or not the stoplist lists it"),
    ("trivial!", "not an _IDENT_RE token: `!` is outside its character class"),
    ("3foo", "not an _IDENT_RE token: an identifier cannot start with a digit"),
])
def test_a_provably_dead_stoplist_entry_is_refused(tmp_path, entry, why):
    """`premises` refuses a stoplist entry that could never change an outcome.

    `referenced_premises` skips a token on ``tok in _LEAN_NOISE or len(tok) <= 1``
    -- membership is evaluated FIRST, but the outcome is the same either way: a
    one-character token is skipped by the second arm whether or not the first
    matched, so listing it changes nothing. And only `_IDENT_RE.findall` output
    is ever tested for membership at all. So a one-character entry, or one
    `_IDENT_RE` could not have produced, is
    documentation asserting a filter that never runs -- which is exactly the
    dead weight a past cleanup already stripped from the hand-written list
    (22 single-character entries plus ``"trivial!"``). Editing the list as
    DATA rather than as code makes that regression easy to reintroduce, so it
    is refused at load.

    The check lives in `premises`, not in the config loader, because `premises`
    is what owns `_IDENT_RE` and the `len(tok) <= 1` short-circuit that make
    those entries dead. `%s`
    """ % why
    path = _write_config(
        tmp_path, lambda s: s.replace('"theorem", "lemma"', f'"theorem", "{entry}"'))
    entries = load_decontam_config(path).lean_noise
    assert entry in entries, "the fixture did not actually inject the entry"
    with pytest.raises(ValueError, match=re.escape(repr(entry))):
        premises._validate_lean_noise(entries)


def test_the_committed_stoplist_passes_its_own_validation():
    """The control: every committed entry is a real, reachable `_IDENT_RE` token."""
    entries = load_decontam_config().lean_noise
    assert premises._validate_lean_noise(entries) is entries
