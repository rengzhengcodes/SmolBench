"""Characterizes unparseable model responses, and what a robust parser recovers.

Why
---
The token-matched whitespace pad in the ``noise_intens`` arm turned out to cost
FORMAT COMPLIANCE, not just accuracy: on chromatic/decode the arm went from 0%
invalid (the old random-character pad) to ~19%, and the invalid responses are
not garbage -- they are right-looking answers in the wrong shape
(``"Answer: False"`` instead of ``"False"``). Because an invalid mark scores as
a failure, that silently mixes "could not follow the format" into an arm whose
only job is to control for length.

The grader is strict by construction. ``smolbench.evals.ToF.condition`` strips
every non-alphabetic character and requires the remainder to be exactly
``true``/``false``, so ``"Answer: False"`` becomes ``"AnswerFalse"`` and
raises. ``Numeric.condition`` is the opposite failure mode: it takes the FIRST
integer anywhere in the response, so a chatty answer is not flagged at all --
it is silently graded on whatever number appeared first.

What this does
--------------
Reads every replicate YAML (all studies, models, arms), classifies each
response, and reports:

1. invalid rate per (study, model, arm) -- the shape of the problem;
2. a taxonomy of the failure patterns, with counts and examples;
3. how many invalids a more robust parser would recover, tier by tier, so the
   recovery rule can be judged rather than trusted;
4. for Numeric, how often the first-integer rule disagrees with more
   defensible rules -- i.e. how much SILENT mis-grading is already happening;
5. a no-regression check: on every mark the current parser scored, the robust
   parser must produce the identical score. A recovery rule that changes an
   existing grade would silently re-write results that were already collected,
   which is strictly worse than leaving them invalid.

Because the raw response text is stored in every mark, all of this is
retroactive: nothing here needs a model, a GPU, or a re-run.

Run (repo root, main venv):
    .venv/bin/python scripts/characterize_format_errors.py
    .venv/bin/python scripts/characterize_format_errors.py --examples 5
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from smolbench.evals import Marks, Numeric, ToF  # noqa: E402

# study -> (results dir, answer kind). Chromatic is True/False; both periodic
# studies ask for a bare integer.
STUDIES = {
    "periodic": ("notebooks/periodic/results", "tof_or_numeric"),
    "chromatic": ("notebooks/chromatic/results", "tof"),
    "periodic_moe": ("notebooks/periodic_moe/results", "numeric"),
}

_TOF_TOKEN = re.compile(r"\b(true|false)\b", re.IGNORECASE)
_YES_NO = re.compile(r"\b(yes|no)\b", re.IGNORECASE)
_INT = re.compile(r"-?\d+")
# "Answer: X" / "Answer -- X" / "**Answer:** X" and friends: the single most
# common way these models break the "nothing else" instruction.
_ANSWER_LEAD = re.compile(r"answer\s*[:\-=]*\s*\**\s*", re.IGNORECASE)


# A response is only mined for a verdict if it is short enough to BE a verdict.
# Beyond this, a "no" or the word "answer" is almost always a step inside a
# reasoning chain rather than a conclusion -- see the cot_intens taxonomy,
# where the invalids are chains TRUNCATED by the completion budget. Recovering
# those would manufacture verdicts out of thoughts that never finished, which
# is far worse than leaving them invalid.
_SHORT_RESPONSE = 200
# How much of the tail counts as "the concluding statement".
_TAIL_WINDOW = 60
# A response that ENDS in a verdict, optionally behind an "Answer:" lead-in
# and optional markdown/punctuation. This is the safe recovery: it only fires
# when the final thing the model said was the verdict itself.
_TERMINAL_VERDICT = re.compile(
    r"(?:answer\s*[:\-=]*\s*)?\**\s*(true|false)\s*[.!*\"']*\s*$",
    re.IGNORECASE,
)
_TERMINAL_YES_NO = re.compile(
    r"(?:answer\s*[:\-=]*\s*)?\**\s*(yes|no)\s*[.!*\"']*\s*$", re.IGNORECASE
)


def robust_tof(ans: str) -> Tuple[Optional[bool], str]:
    """Extracts a True/False verdict, reporting WHICH rule fired.

    Tiered so each rule can be judged separately -- a recovery rule is only
    worth adopting if the tier that fires is one a reader would accept. The
    tiers are deliberately conservative about long responses: see
    ``_SHORT_RESPONSE``.

    Returns
    -------
    (verdict, tier)
        ``verdict`` is None when nothing decisive was found.
    """
    try:
        return ToF.condition(ans), "strict"  # unchanged current behaviour
    except ValueError:
        pass

    stripped = ans.strip()

    # Tier 2: the response ENDS in a verdict ("... Answer: False"). Safe at any
    # length -- a model that finished with the verdict did conclude, however
    # much it said first.
    terminal = _TERMINAL_VERDICT.search(stripped[-_TAIL_WINDOW:])
    if terminal:
        return terminal.group(1).lower() == "true", "terminal-verdict"

    # Tier 3: a SHORT response containing exactly one distinct verdict token.
    if len(stripped) <= _SHORT_RESPONSE:
        tokens = [t.lower() for t in _TOF_TOKEN.findall(stripped)]
        if tokens and len(set(tokens)) == 1:
            return tokens[0] == "true", "short-sole-token"

        # Tier 4: a SHORT response that is just yes/no. Decisive in meaning but
        # not what was asked for, so it stays a compliance failure even when
        # its verdict is recovered.
        terminal_yn = _TERMINAL_YES_NO.search(stripped)
        if terminal_yn:
            return terminal_yn.group(1).lower() == "yes", "short-yes-no"

    # Everything else -- notably long chains truncated mid-thought -- stays
    # invalid on purpose.
    return None, "unrecoverable"


def is_degenerate(ans: str) -> bool:
    """True when the response is repetition collapse rather than an answer.

    A distinct failure class from a format break, and the reason it needs its
    own label: no parser can recover it, because there is no answer in there.
    Observed live -- Nemotron-Ultra-253B under the whitespace-padded noise arm
    emitted 24,576 characters of "0" (8,192 tokens of "000", i.e. the entire
    completion budget) instead of an integer, on every question.

    Detected structurally rather than by pattern: a long response built from a
    tiny alphabet is degenerate whatever character it repeats.
    """
    stripped = ans.strip()
    if len(stripped) < 500:
        return False
    return len(set(stripped)) <= 3


def robust_numeric(ans: str) -> Tuple[Optional[int], str]:
    """Extracts an integer, reporting which rule fired.

    The current rule (first integer anywhere) is kept as tier 1 so behaviour
    is preserved; the point of the other tiers is to measure how often it
    disagrees with a more defensible reading.
    """
    ints = _INT.findall(ans)
    if not ints:
        return None, "unrecoverable"
    if len(ints) == 1:
        return int(ints[0]), "sole-integer"
    lead = _ANSWER_LEAD.split(ans, maxsplit=1)
    if len(lead) > 1:
        after = _INT.findall(lead[1])
        if after:
            return int(after[0]), "answer-prefix"
    return int(ints[-1]), "last-of-many"


def classify(mark, kind: str):
    """Returns (currently_valid, robust_value, tier) for one mark."""
    if is_degenerate(mark.response):
        # Labelled before anything else: repetition collapse is not a parsing
        # problem, and counting it as one would overstate what a better parser
        # can buy.
        return False, None, "degenerate-repetition"
    if kind == "tof":
        try:
            ToF.condition(mark.response)
            current_ok = True
        except ValueError:
            current_ok = False
        value, tier = robust_tof(mark.response)
    else:
        try:
            Numeric.condition(mark.response)
            current_ok = True
        except ValueError:
            current_ok = False
        value, tier = robust_numeric(mark.response)
    return current_ok, value, tier


def kind_for(study: str, tag_arm: str) -> str:
    """Chromatic asks True/False; the periodic studies ask for an integer."""
    return "tof" if study == "chromatic" else "numeric"


def main() -> int:
    """Scans every replicate and prints the characterization."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--examples", type=int, default=3)
    parser.add_argument("--study", choices=sorted(STUDIES), action="append")
    parser.add_argument(
        "--max-reps",
        type=int,
        default=0,
        help="cap replicates scanned per condition (0 = all). Chromatic "
        "replicates are ~8MB of YAML each, so a full scan is slow; a cap makes "
        "this usable while a run is still in flight.",
    )
    parser.add_argument(
        "--arm",
        action="append",
        help="only scan conditions whose name ends with this arm "
        "(e.g. --arm noise_intens). Repeatable.",
    )
    args = parser.parse_args()
    studies = args.study or sorted(STUDIES)

    grand_regressions = 0
    grand_recovered = 0
    grand_invalid = 0

    for study in studies:
        results = REPO / STUDIES[study][0]
        if not results.is_dir():
            continue
        print(f"\n{'=' * 78}\n### {study}\n{'=' * 78}")
        kind = kind_for(study, "")

        per_condition = defaultdict(lambda: {"n": 0, "invalid": 0, "recovered": 0})
        tiers = Counter()
        per_cond_tiers = defaultdict(Counter)
        # Invalids inside a long response are a different animal from invalids
        # in a short one: a stray "no" mid-reasoning is not a verdict, so a
        # recovery rule that mines long chains deserves more suspicion.
        long_invalids = Counter()
        examples = defaultdict(list)
        regressions = []
        misgrades = []

        for cond_dir in sorted(results.glob("*_*")):
            if not cond_dir.is_dir():
                continue
            cond = cond_dir.name
            if args.arm and not any(cond.endswith(a) for a in args.arm):
                continue
            reps = sorted(cond_dir.glob("rep_*.yaml"))
            if args.max_reps:
                reps = reps[: args.max_reps]
            for rep in reps:
                marks = Marks.load(rep)
                for mark in marks.marks:
                    current_ok, value, tier = classify(mark, kind)
                    stats = per_condition[cond]
                    stats["n"] += 1
                    if current_ok:
                        expected = (
                            ToF.condition(mark.response)
                            if kind == "tof"
                            else Numeric.condition(mark.response)
                        )
                        if value != expected:
                            # For ToF the current parser is strict, so any
                            # disagreement really is a regression to justify.
                            # For Numeric it is the opposite: condition()
                            # grabs the FIRST integer, which on a worked
                            # answer like "2520 // 8 = 315\n\n315" scores the
                            # operand instead of the result. Those
                            # disagreements are evidence of PRE-EXISTING
                            # silent mis-grading, so they are reported as
                            # candidate fixes with the truth value attached
                            # rather than as regressions to be avoided.
                            record = (
                                cond,
                                rep.name,
                                repr(mark.response[:70]),
                                expected,
                                value,
                                mark.answer,
                            )
                            if kind == "tof":
                                regressions.append(record)
                            else:
                                misgrades.append(record)
                    else:
                        stats["invalid"] += 1
                        tiers[tier] += 1
                        per_cond_tiers[cond][tier] += 1
                        if len(mark.response) > 200:
                            long_invalids[cond] += 1
                        if value is not None:
                            stats["recovered"] += 1
                        key = (cond, tier)
                        if len(examples[key]) < args.examples:
                            # Show the TAIL: a verdict lands at the end of a
                            # response, and the head of a reasoning chain says
                            # nothing about how it concluded.
                            examples[key].append(repr(mark.response[-110:]))

        if not per_condition:
            print("  (no replicates yet)")
            continue

        print(f"\n{'condition':28s} {'n':>6s} {'invalid':>9s} {'rate':>7s} {'recoverable':>12s}")
        for cond in sorted(per_condition):
            s = per_condition[cond]
            rate = s["invalid"] / s["n"] if s["n"] else 0
            print(
                f"  {cond:26s} {s['n']:6d} {s['invalid']:9d} {rate:6.1%} "
                f"{s['recovered']:12d}"
            )
            grand_invalid += s["invalid"]
            grand_recovered += s["recovered"]

        if tiers:
            print("\n  failure taxonomy per condition (which rule recovers it):")
            for cond in sorted(per_cond_tiers):
                total_long = long_invalids[cond]
                print(
                    f"    {cond}  ({sum(per_cond_tiers[cond].values())} invalid, "
                    f"{total_long} of them >200 chars i.e. reasoning chains)"
                )
                for tier, count in per_cond_tiers[cond].most_common():
                    print(f"      {tier:22s} {count:6d}")
                    for ex in examples[(cond, tier)]:
                        print(f"          tail: {ex}")

        if misgrades:
            # How many of these actually flip correct/incorrect -- the number
            # that matters, since a disagreement that lands on the same
            # verdict changes nothing.
            flips = sum(
                1 for _c, _r, _s, cur, rob, truth in misgrades
                if (cur == truth) != (rob == truth)
            )
            print(
                f"\n  !! {len(misgrades)} marks were graded on the FIRST integer while a "
                f"later one is more defensible ({flips} change correct/incorrect):"
            )
            for cond, rep, resp, cur, rob, truth in misgrades[:5]:
                verdict = "FIXES" if (rob == truth) and (cur != truth) else "changes"
                print(
                    f"     {cond}/{rep}: {resp}\n"
                    f"        current={cur} robust={rob} truth={truth}  -> {verdict}"
                )

        if regressions:
            grand_regressions += len(regressions)
            print(f"\n  !! {len(regressions)} TRUE/FALSE REGRESSIONS (robust parser "
                  "changes an already-valid verdict):")
            for cond, rep, resp, cur, rob, truth in regressions[:5]:
                print(f"     {cond}/{rep}: {resp} current={cur} robust={rob} truth={truth}")
        else:
            print("\n  no-regression check: PASSED (no already-valid verdict changed)")

    print(f"\n{'=' * 78}")
    print(f"TOTAL invalid: {grand_invalid} | recoverable by a robust parser: "
          f"{grand_recovered} | regressions: {grand_regressions}")
    return 1 if grand_regressions else 0


if __name__ == "__main__":
    sys.exit(main())
