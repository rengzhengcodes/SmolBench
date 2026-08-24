"""Run a response-level audit of the induction results tree.

For each condition, this script measures what the stored RAW responses
actually contain: how many are empty, how many scored correct, how many
contain their own correct answer anywhere in the text, and the longest
response. Use it to tell a genuine low-accuracy result apart from a
broken lane -- see PAIRED_ANALYSIS_RESULTS.md.

Two traps this script exists to avoid
--------------------------------------
1. ``response`` is a YAML BLOCK SCALAR. A line-oriented regex over the
   file silently truncates it at the first line that looks like a new
   key. That bug understated glm_air's empty count as 16 (true value
   48), and overstated exaone_33b's answer hits as 24 (true value 5).
   Any pass over ``response`` text must use a real parser.

   The results YAMLs carry ``!!python/object:`` tags, which
   ``yaml.safe_load`` refuses. But ``yaml.unsafe_load`` CONSTRUCTS
   arbitrary objects from repository-generated files, which the repo
   convention (see ``notebooks/_power_common.py``) declines to do. The
   loader below takes the third option: it maps every unknown tag to a
   plain dict/list/str. This is safe, and correct on block scalars.

2. The per-harmonic correct answer is NOT ``lcm(1..k)``. The queries are
   COUNTS over one full 2520-position sequence, so harmonic k's answer
   is 2520 // k = (2520, 1260, 840, 630, 504, 420, 360, 315, 280),
   identical for every seed, since only the label assignment varies with
   the seed. lcm would instead produce ``scored > answer_in_response``,
   which is arithmetically impossible. The assertion below turns that
   mistake into an error, instead of a plausible-looking table.
   ``EXPECTED_ANSWERS`` is verified against a lane at acc 1.000.

Interpreting ``ans_in_resp``
-----------------------------
The gap between ``scored`` and ``ans_in_resp`` is only informative when
the condition's violation profile is NOT dominated by
``multiple-values``. A response that rambles through a long list of
integers contains the correct one by construction. So for a
multiple-values-dominated lane (min3_8b noise: 181 vs 58) the metric is
near-vacuous, and does NOT indicate recoverable signal. Where the
profile is empty- or collapse-dominated (glm_flash 39 vs 33, glm_air 176
vs 164), the small gap genuinely does show the parser is recovering what
is there.

Run:
    uv run --no-project --with pyyaml python notebooks/induction/response_audit.py
"""

import sys
from pathlib import Path

import yaml

RESULTS = Path(__file__).resolve().parent / "results"

#: Harmonic k (1-indexed) -> correct count over the 2520-position sequence.
EXPECTED_ANSWERS = tuple(2520 // k for k in range(1, 10))

#: Conditions worth auditing by default: the lanes flagged as collapsed or
#: degraded in PAIRED_ANALYSIS_RESULTS.md, plus a clean control.
DEFAULT_CONDITIONS = (
    "qwen35_397b_intens",  # control: acc 1.000, used to verify EXPECTED_ANSWERS
    "glm_air_noise_intens",
    "glm_flash_noise_intens",
    "exaone_32b_noise_intens",
    "exaone_33b_noise_intens",
    "min3_8b_noise_intens",
    "min3_14b_noise_intens",
)


class TagIgnoringLoader(yaml.SafeLoader):
    """SafeLoader that maps unknown tags to plain data instead of refusing them.

    Unlike ``yaml.unsafe_load`` this never calls a constructor found in the
    file, so it is safe on repository-generated YAML -- see trap 1 above.
    """


def _ignore_tag(loader, _suffix, node):
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node, deep=True)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node, deep=True)
    return loader.construct_scalar(node)


TagIgnoringLoader.add_multi_constructor("", _ignore_tag)
TagIgnoringLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/object:", _ignore_tag
)


def audit(condition: str) -> dict:
    """Compute per-condition response-level counts.

    Parameters
    ----------
    condition : str
        Name of the results subdirectory to audit (for example,
        ``"glm_air_noise_intens"``), under `RESULTS`.

    Returns
    -------
    dict
        Keys ``condition``, ``marks``, ``empty``, ``scored``,
        ``ans_in_resp``, ``longest``. See `main`'s printed table header
        for what each count means.

    Raises
    ------
    SystemExit
        If `condition`'s results directory does not exist.
    AssertionError
        If a mark's `answer` disagrees with `EXPECTED_ANSWERS` (trap 2 in
        the module docstring), or if `scored` exceeds `ans_in_resp`
        (which is arithmetically impossible and signals a wrong
        `EXPECTED_ANSWERS`).
    """
    cdir = RESULTS / condition
    if not cdir.is_dir():
        raise SystemExit(
            f"No such condition: {cdir}\nRun "
            f"InductionExperiment.harness.sync_down() first."
        )
    n = empty = scored = hit = 0
    longest = 0
    for path in sorted(cdir.glob("rep_*.yaml")):
        for k, mark in enumerate(yaml.load(path.read_text(), Loader=TagIgnoringLoader)["marks"]):
            answer = mark.get("answer")
            if k < len(EXPECTED_ANSWERS) and answer != EXPECTED_ANSWERS[k]:
                raise AssertionError(
                    f"{path} mark {k}: answer {answer!r} != expected "
                    f"{EXPECTED_ANSWERS[k]} -- either the quiz config changed or "
                    f"the marks are not in ascending-period order, and every "
                    f"positional assumption in this study's analysis is void."
                )
            n += 1
            response = mark.get("response") or ""
            if not isinstance(response, str):
                response = str(response)
            longest = max(longest, len(response))
            if not response.strip():
                empty += 1
            if mark.get("score") == 1:
                scored += 1
            if str(answer) in response:
                hit += 1
    # A mark cannot be graded correct without containing its own answer. This
    # fires on a wrong EXPECTED_ANSWERS (trap 2) rather than letting it through.
    assert scored <= hit, (
        f"{condition}: scored ({scored}) > answer-in-response ({hit}), which is "
        f"impossible -- EXPECTED_ANSWERS is probably wrong for this quiz config."
    )
    return dict(
        condition=condition, marks=n, empty=empty, scored=scored,
        ans_in_resp=hit, longest=longest,
    )


def main(conditions=DEFAULT_CONDITIONS) -> None:
    """Print a response-level audit table for `conditions`.

    Parameters
    ----------
    conditions : tuple of str, default DEFAULT_CONDITIONS
        Condition names to audit, in print order.
    """
    print(
        f"{'condition':26s} {'marks':>6s} {'empty':>6s} {'scored':>7s} "
        f"{'ans_in_resp':>12s} {'longest':>9s}"
    )
    for cond in conditions:
        r = audit(cond)
        print(
            f"{r['condition']:26s} {r['marks']:6d} {r['empty']:6d} "
            f"{r['scored']:7d} {r['ans_in_resp']:12d} {r['longest']:9d}"
        )
    print(
        "\nans_in_resp is near-vacuous for multiple-values-dominated lanes "
        "(a rambling\nlist of integers contains the answer by construction) -- "
        "see the module docstring."
    )


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or DEFAULT_CONDITIONS)
