"""Load the committed Lean decontamination policy config.

``smolbench/deduction/lean/decontam_config.toml`` (parsed here) is the ONE
place the decontamination POLICY is written down: the MinHash/LSH
near-duplicate parameters `decontam` fingerprints eval statements with, the
statement/state key-length floor, and the identifier stoplist `premises`
filters premise references through. Before this module existed, each of those
was a code constant -- ``decontam._SHINGLE_N``/``_NUM_PERM``/``_BANDS``/
``_JACCARD_THRESHOLD``/``_PERM_SEED``/``_MIN_GOAL_KEY_CHARS`` and
``premises._LEAN_NOISE``, a hand-maintained ~100-entry list. None of them is
logic: they decide what a run CONTAINS, which is what makes them worth
reviewing in one file and stamping into a manifest.

Digest
------
:class:`DecontamConfig` carries `sha256`, the hex SHA-256 of the config
file's RAW BYTES, produced from the SAME single read that is parsed. Hashing
and parsing one byte string, rather than re-reading the file to hash it, is
deliberate: a second read opens a window in which the digest and the parsed
values describe different file contents. ``notebooks/deduction/run_study.py``
stamps that digest into every run's ``manifest.json``, so an archived run
records which stoplist produced its prompts.

Imports
-------
STANDARD LIBRARY ONLY, deliberately, so this stays a leaf module `premises`
can import without closing an import cycle. ``decontam`` -> ``context`` ->
``premises`` already exists; a ``premises`` -> ``decontam`` edge would close
the loop.

Caching
-------
:func:`load_decontam_config` is memoized with :func:`functools.lru_cache`,
keyed on the RESOLVED config path (not the raw argument), so the file is
parsed at most once per distinct path -- typically exactly once, since every
production caller uses the default path. That matters here beyond mere
economy: `premises.referenced_premises` consults the stoplist once per
identifier token of every premise body it scans, so re-parsing per lookup
would be a per-token file read. Keying on the resolved path rather than the
raw argument means ``Path("decontam_config.toml")`` and an equivalent
absolute path share one cache entry, and a test that points the loader at a
``tmp_path`` fixture never collides with the committed file's entry.
"""

from __future__ import annotations

import functools
import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

#: The committed config, resolved relative to this module's own file so it is
#: found regardless of the caller's working directory.
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().with_name("decontam_config.toml")


@dataclass(frozen=True)
class MinHashConfig:
    """Parameters of `decontam`'s MinHash + banded-LSH near-duplicate index.

    Parameters
    ----------
    shingle_n : int
        Character n-gram width of a shingle set. ``>= 1``.
    num_perm : int
        MinHash permutation count, i.e. the signature length. ``>= 1``, and
        an exact multiple of `bands`.
    bands : int
        LSH band count. ``>= 1``.
    rows : int
        Rows per band. DERIVED as ``num_perm // bands``, never configured --
        stating it in the file as well would let the two disagree.
    jaccard_threshold : float
        Decision threshold on EXACT shingle-set Jaccard similarity, in
        ``(0, 1]``. The LSH only proposes candidates; this is what actually
        makes a row a near-duplicate.
    perm_seed : int
        Seed for the MinHash permutations, so every index built anywhere
        hashes identically.
    """

    shingle_n: int
    num_perm: int
    bands: int
    rows: int
    jaccard_threshold: float
    perm_seed: int


@dataclass(frozen=True)
class KeyConfig:
    """Eligibility rules for `decontam`'s statement/state index keys.

    Parameters
    ----------
    min_goal_key_chars : int
        Minimum normalized length for a goal-only state variant to become an
        index key. ``>= 0``; ``0`` disables the floor.
    """

    min_goal_key_chars: int


@dataclass(frozen=True)
class DecontamConfig:
    """The whole committed decontamination policy, plus the file's digest.

    Parameters
    ----------
    minhash : MinHashConfig
        The ``[minhash]`` section.
    keys : KeyConfig
        The ``[keys]`` section.
    lean_noise : frozenset of str
        The ``[premises]`` section's ``lean_noise`` list, as a set. A
        `frozenset` rather than a tuple because every consumer asks
        membership questions of it and nothing depends on its order; the
        duplicate check happens at LOAD time (see
        :func:`_parse_decontam_config`), before set-ification could hide one.
    path : pathlib.Path
        RESOLVED path the config was read from -- the same value
        :func:`_load_cached` is memoized on, so it cannot disagree with the
        bytes `sha256` covers. The other half of the provenance pair: `path`
        says WHICH file, `sha256` says WHICH bytes of it, and
        ``notebooks/deduction/run_study.py`` stamps both into a run's
        manifest. Carried here, rather than left for a consumer to re-spell,
        precisely so a stamp cannot name a different file from the one that
        was loaded. ``smolbench/evals/study_config.py`` -- which this module is
        otherwise modelled on closely -- deliberately carries no such field;
        it feeds no provenance stamp and so has nothing to keep honest.
    sha256 : str
        Hex SHA-256 of the config file's raw bytes -- see the module
        docstring's "Digest" section for why it is computed from the parsed
        bytes rather than from a second read.
    """

    minhash: MinHashConfig
    keys: KeyConfig
    lean_noise: "frozenset[str]"
    path: Path
    sha256: str


def _require_section(data: dict, section: str) -> dict:
    """Return ``data[section]``, raising ``ValueError`` naming `section` if absent."""
    if section not in data:
        raise ValueError(
            f"decontam_config.toml is missing the required [{section}] section"
        )
    return data[section]


def _require_key(section_data: dict, section: str, key: str):
    """Return ``section_data[key]``, raising ``ValueError`` naming `section`/`key` if absent."""
    if key not in section_data:
        raise ValueError(
            f"decontam_config.toml [{section}] is missing the required key {key!r}"
        )
    return section_data[key]


def _parse_decontam_config(data: dict, path: Path, sha256: str) -> DecontamConfig:
    """Build and validate a :class:`DecontamConfig` from a parsed TOML document.

    Parameters
    ----------
    data : dict
        The document ``tomllib.loads``/``tomllib.load`` produced.
    path : Path
        Resolved path `data` was read from, passed through onto the result.
    sha256 : str
        Hex digest of the bytes `data` was parsed from, passed in rather than
        recomputed so the digest provably describes the parsed document.

    Returns
    -------
    DecontamConfig
        Fully validated: every declared section/key present, every numeric
        bound satisfied, ``num_perm`` exactly partitioned by ``bands``, and
        the stoplist non-empty and duplicate-free.

    Raises
    ------
    ValueError
        On any structural or range defect. The message names the offending
        section, key, or VALUE, so the failure points straight at the line to
        fix in ``decontam_config.toml``.

    Notes
    -----
    Deliberately does NOT check that a ``lean_noise`` entry is a usable
    identifier. That check belongs to `premises`, which owns the
    ``_IDENT_RE`` an entry has to match and the ``len(tok) <= 1`` arm that
    makes a one-character entry dead; see `premises._validate_lean_noise`.
    """
    # Phase 1: presence and interpretation of [minhash]. Every declared key
    # must exist before any is range-checked, so a missing key never surfaces
    # as a confusing KeyError further down.
    minhash_raw = _require_section(data, "minhash")
    shingle_n = _require_key(minhash_raw, "minhash", "shingle_n")
    num_perm = _require_key(minhash_raw, "minhash", "num_perm")
    bands = _require_key(minhash_raw, "minhash", "bands")
    jaccard_threshold = _require_key(minhash_raw, "minhash", "jaccard_threshold")
    perm_seed = _require_key(minhash_raw, "minhash", "perm_seed")

    # Phase 2: range guards, each naming the value it rejected. Checked before
    # the divisibility guard below so a nonsensical `bands = 0` is reported as
    # a bad band count rather than as a ZeroDivisionError inside it.
    if shingle_n < 1:
        raise ValueError(
            f"decontam_config.toml [minhash] shingle_n must be >= 1, got {shingle_n}"
        )
    if num_perm < 1:
        raise ValueError(
            f"decontam_config.toml [minhash] num_perm must be >= 1, got {num_perm}"
        )
    if bands < 1:
        raise ValueError(
            f"decontam_config.toml [minhash] bands must be >= 1, got {bands}"
        )
    if not 0 < jaccard_threshold <= 1:
        raise ValueError(
            "decontam_config.toml [minhash] jaccard_threshold must be in (0, 1], "
            f"got {jaccard_threshold}"
        )

    # Guard: the bands must partition the signature EXACTLY. A leftover slot
    # would be silently excluded from every band, so a `num_perm` the band
    # count does not divide describes an index that hashes fewer permutations
    # than the file claims.
    if num_perm % bands:
        raise ValueError(
            f"decontam_config.toml [minhash] num_perm={num_perm} is not divisible "
            f"by bands={bands}: the LSH bands must partition the signature "
            f"exactly, leaving no slot outside a band. Pick a num_perm that is a "
            f"multiple of bands (or a bands that divides num_perm)."
        )

    minhash = MinHashConfig(
        shingle_n=shingle_n,
        num_perm=num_perm,
        bands=bands,
        # DERIVED, never read from the file: see MinHashConfig.rows.
        rows=num_perm // bands,
        jaccard_threshold=jaccard_threshold,
        perm_seed=perm_seed,
    )

    keys_raw = _require_section(data, "keys")
    min_goal_key_chars = _require_key(keys_raw, "keys", "min_goal_key_chars")
    if min_goal_key_chars < 0:
        raise ValueError(
            "decontam_config.toml [keys] min_goal_key_chars must be >= 0, got "
            f"{min_goal_key_chars}"
        )
    keys = KeyConfig(min_goal_key_chars=min_goal_key_chars)

    premises_raw = _require_section(data, "premises")
    lean_noise_raw = list(_require_key(premises_raw, "premises", "lean_noise"))

    # Guard: a non-empty stoplist. An empty one would let every Lean keyword
    # and tactic name resolve as a premise reference, silently changing what
    # the hint:3/hint:4 rungs contain rather than failing.
    if not lean_noise_raw:
        raise ValueError(
            "decontam_config.toml [premises] lean_noise is empty; an empty "
            "stoplist would let every Lean keyword and tactic name resolve as a "
            "premise reference"
        )

    # Guard: no duplicates, checked BEFORE set-ification -- which is the whole
    # point. This is a hand-maintained list, so a repeated entry is a sign of a
    # bad merge (two branches appending to the same tail), and building the set
    # first would erase that evidence with no change in behaviour.
    seen: "set[str]" = set()
    for entry in lean_noise_raw:
        if entry in seen:
            raise ValueError(
                f"decontam_config.toml [premises] lean_noise lists {entry!r} more "
                "than once. The list is hand-maintained, so a duplicate is a sign "
                "of a bad merge; it is refused rather than deduplicated, because "
                "set-ification would hide it."
            )
        seen.add(entry)

    return DecontamConfig(
        minhash=minhash,
        keys=keys,
        lean_noise=frozenset(lean_noise_raw),
        path=path,
        sha256=sha256,
    )


@functools.lru_cache(maxsize=None)
def _load_cached(resolved_path: Path) -> DecontamConfig:
    """Parse, digest and validate `resolved_path`, memoized on the resolved path.

    Split out from :func:`load_decontam_config` so the cache key is always the
    fully resolved path (see that function's docstring), never the raw
    ``Path | None`` argument a caller passed in.

    The file is read ONCE, into `raw`; the digest and the parsed document both
    come from those bytes. See the module docstring's "Digest" section.
    """
    raw = resolved_path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    # tomllib.loads takes str, so the bytes are decoded here rather than handed
    # to tomllib.load -- TOML is defined as UTF-8, so a file that is not valid
    # UTF-8 is not valid TOML and raising UnicodeDecodeError says so precisely.
    data = tomllib.loads(raw.decode("utf-8"))
    return _parse_decontam_config(data, resolved_path, sha256)


def load_decontam_config(path: "Optional[Path]" = None) -> DecontamConfig:
    """Load and validate the committed decontamination policy config.

    Parameters
    ----------
    path : pathlib.Path or None, optional
        Config file to load. ``None`` (the default) resolves to
        ``decontam_config.toml`` beside this module -- the committed file
        every production caller should use; tests pass an explicit `path` to
        load a scratch fixture instead.

    Returns
    -------
    DecontamConfig
        Validated and cached: repeated calls with a path that resolves to the
        same file return the SAME object (see the module docstring's
        "Caching" section), so a consumer must never mutate it. Every field is
        either an immutable scalar or a `frozenset`, which makes that
        impossible rather than merely discouraged.

    Raises
    ------
    ValueError
        The file is structurally invalid: see :func:`_parse_decontam_config`
        for the specific checks and their messages.
    FileNotFoundError
        `path` (or the default) does not exist.
    UnicodeDecodeError
        The file is not valid UTF-8, and so is not valid TOML.
    tomllib.TOMLDecodeError
        The file is not valid TOML.

    Notes
    -----
    Reads no environment variables and imports only the standard library --
    see the module docstring's "Imports" section for the import-cycle reason
    that second point is load-bearing. Pure I/O + parsing.

    Examples
    --------
    >>> cfg = load_decontam_config()
    >>> cfg.minhash.num_perm, cfg.minhash.bands, cfg.minhash.rows
    (64, 8, 8)
    >>> "simp" in cfg.lean_noise
    True
    >>> cfg.path.name, len(cfg.sha256)
    ('decontam_config.toml', 64)
    """
    resolved = (path if path is not None else _DEFAULT_CONFIG_PATH).resolve()
    return _load_cached(resolved)
