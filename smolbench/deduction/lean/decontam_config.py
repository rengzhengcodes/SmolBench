"""Load the committed Lean decontamination policy config.

``decontam_config.toml`` is the one place the decontamination POLICY lives:
`decontam`'s MinHash/LSH near-duplicate parameters, the statement/state
key-length floor, and the identifier stoplist `premises` filters references
through. None of it is logic, which is what makes it worth reviewing in one
file and stamping into a manifest.

`sha256` on :class:`DecontamConfig` hashes the same bytes used to parse the
file, not a second read, so the digest can never describe different content
than what was parsed. Standard library only, so `premises` can import this
leaf module without closing the ``decontam`` -> ``context`` -> ``premises``
cycle. :func:`load_decontam_config` caches on the resolved path, so a
``tmp_path`` fixture never shares the committed file's cache entry.
"""

from __future__ import annotations

import functools
import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

#: The committed config, resolved relative to this module's own file so it is
#: found regardless of the caller's working directory.
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().with_name("decontam_config.toml")


@dataclass(frozen=True)
class MinHashConfig:
    """Parameters of `decontam`'s MinHash + banded-LSH near-duplicate index.

    Parameters
    ----------
    rows : int
        derived as ``num_perm // bands``, never read from the file --
        stating it there too would let the two disagree.
    jaccard_threshold : float
        decision threshold on exact shingle-set Jaccard similarity; the LSH
        only proposes candidates, this is what decides.
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
        minimum normalized length for a goal-only state variant to become an
        index key; ``0`` disables the floor.
    """

    min_goal_key_chars: int


@dataclass(frozen=True)
class DecontamConfig:
    """The whole committed decontamination policy, plus the file's digest.

    Parameters
    ----------
    lean_noise : frozenset[str]
        a frozenset, not a tuple, since every consumer only asks membership
        questions and the duplicate check happens at load time, before
        set-ification could hide one.
    path : Path
        the resolved path :func:`_load_cached` is memoized on, carried here so
        a manifest stamp can't name a different file than the one `sha256`
        covers.
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


def _require_key(section_data: dict, section: str, key: str) -> Any:
    """Return ``section_data[key]``, raising ``ValueError`` naming `section`/`key` if absent."""
    if key not in section_data:
        raise ValueError(
            f"decontam_config.toml [{section}] is missing the required key {key!r}"
        )
    return section_data[key]


def _parse_decontam_config(data: dict, path: Path, sha256: str) -> DecontamConfig:
    """Build and validate a :class:`DecontamConfig` from a parsed TOML document.

    `sha256` is passed in rather than recomputed, so the digest provably
    describes the parsed document. Does not check that a ``lean_noise`` entry
    is a usable identifier -- that's `premises._validate_lean_noise`'s job.
    """
    # Every declared [minhash] key must exist before any is range-checked, so
    # a missing key never surfaces as a confusing KeyError further down.
    minhash_raw = _require_section(data, "minhash")
    shingle_n = _require_key(minhash_raw, "minhash", "shingle_n")
    num_perm = _require_key(minhash_raw, "minhash", "num_perm")
    bands = _require_key(minhash_raw, "minhash", "bands")
    jaccard_threshold = _require_key(minhash_raw, "minhash", "jaccard_threshold")
    perm_seed = _require_key(minhash_raw, "minhash", "perm_seed")

    # Checked before the divisibility guard below so a nonsensical `bands = 0`
    # is reported as a bad band count, not a ZeroDivisionError inside it.
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

    # Bands must partition num_perm exactly, or a leftover slot is silently
    # excluded from every band -- an index that hashes fewer permutations
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

    # An empty stoplist would let every Lean keyword and tactic name resolve
    # as a premise reference, silently changing what hint:3/hint:4 contain.
    if not lean_noise_raw:
        raise ValueError(
            "decontam_config.toml [premises] lean_noise is empty; an empty "
            "stoplist would let every Lean keyword and tactic name resolve as a "
            "premise reference"
        )

    # Checked before set-ification: this is a hand-maintained list, so a
    # repeated entry is a sign of a bad merge, and building the set first
    # would erase that evidence with no change in behaviour.
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

    Split out from :func:`load_decontam_config` so the cache key is always
    the resolved path, never the raw ``Path | None`` a caller passed in.
    """
    raw = resolved_path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    # Decoded here rather than handed to tomllib.load: TOML is defined as
    # UTF-8, so a non-UTF-8 file is not valid TOML, and UnicodeDecodeError says so.
    data = tomllib.loads(raw.decode("utf-8"))
    return _parse_decontam_config(data, resolved_path, sha256)


def load_decontam_config(path: "Optional[Path]" = None) -> DecontamConfig:
    """Load and validate the committed decontamination policy config.
    Cached: repeated calls that resolve to the same file return the SAME
    object, and every field is an immutable scalar or `frozenset`, so a
    consumer cannot mutate it.

    Parameters
    ----------
    path : Optional[Path], optional
        ``None`` (the default) resolves to ``decontam_config.toml`` beside
        this module; tests pass an explicit path to load a scratch fixture.
    """
    resolved = (path if path is not None else _DEFAULT_CONFIG_PATH).resolve()
    return _load_cached(resolved)
