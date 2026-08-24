"""Run a seed-fixed golden regression for the induction generation pipelines.

The hashes in tests/fixtures/golden_quizzes.json were captured from the
pre-refactor code (2026-07-01, branch periodic-induction) at the
notebooks' production configs. Any change to label sampling, interval
assignment, noise padding, prompt rendering, or the query generators shows
up here as a hash mismatch. This matters because committed results are
only attributable to their recorded seeds while generation stays
byte-stable.

The ``noise_intens`` hashes were re-recorded on 2026-08-02, when that arm
switched from random characters matched on character count to whitespace
matched on token count (see ``smolbench.induction._common``). The
``intens``/``extens`` hashes are unchanged from the 2026-07-01 capture and
must stay that way: they are the check that the change is confined to the
noise arm.

The noise arm now depends on a tokenizer, and these hashes are recorded
against ``conftest.StubTokenizer``, not a real model's tokenizer. That
keeps the fixture offline and byte-stable. (A downloaded tokenizer would
make the golden depend on a network fetch and on an upstream repo nobody
here controls.) What it pins is the generation pipeline, while
tests/test_noise_token_match.py is what checks the pad behaves correctly
under real tokenizers.
"""

import hashlib
import json
import string
from pathlib import Path

import pytest

from conftest import StubTokenizer

from smolbench.induction.periodic import (
    PeriodicConfig,
    Prompter as PeriodicPrompter,
    get_periodic_numeric_quiz,
    get_periodic_quiz,
    numeric_count_query_gen,
    tof_membership_query_gen,
)
from smolbench.induction.chromatic import (
    ChromaticIntervalsConfig,
    Prompter as ChromaticPrompter,
    get_random_exclusive_quiz,
    succession_query_gen,
    one_hop_year_query_gen,
)

GOLDEN = json.loads(
    (Path(__file__).parent / "fixtures" / "golden_quizzes.json").read_text()
)

# Minimal templates exercising every placeholder each generator produces.
PERIODIC_TMPL = string.Template(
    "CTX:\n$positive_info\nQ: How many of positions 1..$seq_len include '$label'?"
)
PERIODIC_TOF_TMPL = string.Template(
    "CTX:\n$positive_info\nQ: Does position $pos include '$label'? True/False."
)
CHROM_TMPL = string.Template(
    "ROLE $role PARADE $parade\n$positive_info\nQ: Has $color1 handed to $color2?"
)
CHROM_EXT_TMPL = string.Template(
    "ROLE $role PARADE $parade EXT\n$positive_info\nQ: Has $color1 handed to $color2?"
)
ONEHOP_TMPL = string.Template(
    "ROLE $role PARADE $parade\n$positive_info\nQ: In year $year, could $color head?"
)
ONEHOP_EXT_TMPL = string.Template(
    "ROLE $role PARADE $parade EXT\n$positive_info\nQ: In year $year, could $color head?"
)


def quiz_hash(quiz) -> str:
    h = hashlib.sha256()
    for q in quiz:
        h.update(q.prompt.encode())
        h.update(repr(q.answer).encode())
        h.update(type(q).__name__.encode())
    return h.hexdigest()


def assert_matches(key: str, quizzes) -> None:
    got = {k: quiz_hash(q) for k, q in zip(("intens", "extens", "noise_intens"), quizzes)}
    assert got == GOLDEN[key], f"generation drifted from pre-refactor golden {key}"


# The tokenizer the noise arm is sized against. It is fixed and offline;
# see the module docstring for why it is a stub, not a served model's.
TOKENIZER = StubTokenizer()


@pytest.mark.parametrize("seed", (1776, 1777))
def test_periodic_golden(seed):
    # The periodic notebook's production config: n=9 harmonics, random labels.
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    assert_matches(
        f"periodic_numeric_{seed}",
        get_periodic_numeric_quiz(
            cfg,
            PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
            tokenizer=TOKENIZER,
        ),
    )
    assert_matches(
        f"periodic_tof_{seed}",
        get_periodic_quiz(
            cfg,
            PeriodicPrompter(PERIODIC_TOF_TMPL, {}, tof_membership_query_gen),
            tokenizer=TOKENIZER,
        ),
    )


@pytest.mark.parametrize("seed", (1776, 1777))
def test_chromatic_golden(seed):
    # The chromatic notebooks' production config: 3000 years, 62 intervals.
    cfg = ChromaticIntervalsConfig(n=int(12 * 250), intervals=250 // 4, colors=45, seed=seed)
    sub = {"role": "Twislax", "parade": "Gildane"}
    assert_matches(
        f"chromatic_succession_{seed}",
        get_random_exclusive_quiz(
            cfg,
            ChromaticPrompter(CHROM_TMPL, sub, succession_query_gen, CHROM_EXT_TMPL),
            tokenizer=TOKENIZER,
        ),
    )
    assert_matches(
        f"chromatic_one_hop_{seed}",
        get_random_exclusive_quiz(
            cfg,
            ChromaticPrompter(ONEHOP_TMPL, sub, one_hop_year_query_gen, ONEHOP_EXT_TMPL),
            tokenizer=TOKENIZER,
        ),
    )
