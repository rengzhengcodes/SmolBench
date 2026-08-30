"""Response-level audit of the induction results tree.

Per condition, counts what the stored RAW responses contain: empty, scored
correct, containing their own correct answer anywhere in the text, and the
longest response. Tells a genuine low-accuracy result apart from a broken lane.

Two traps this script exists to avoid:

1. ``response`` is a YAML BLOCK SCALAR, so a line-oriented regex silently
   truncates it at the first line that looks like a new key, understating empty
   counts and overstating answer hits. The results YAMLs carry
   ``!!python/object:`` tags that ``yaml.safe_load`` refuses and
   ``yaml.unsafe_load`` would CONSTRUCT; `TagIgnoringLoader` takes the third
   option and maps every unknown tag to plain dict/list/str.
2. The per-harmonic correct answer is ``2520 // k``, NOT ``lcm(1..k)``: the
   queries are COUNTS over one full 2520-position sequence, identical for every
   seed since only the label assignment varies. lcm would produce the
   arithmetically impossible ``scored > answer_in_response``; `audit`'s
   assertions turn that into an error rather than a plausible-looking table.
   ``EXPECTED_ANSWERS`` is verified against a lane at acc 1.000.

The ``scored`` vs ``ans_in_resp`` gap is near-vacuous when a condition's
violation profile is dominated by ``multiple-values``: a rambling list of
integers contains the correct answer by construction.

Run:
    uv run --no-project --with pyyaml python notebooks/induction/audits/response_audit.py
"""

import sys
from pathlib import Path

import yaml

RESULTS = Path(__file__).resolve().parents[1] / "results"

#: Harmonic k (1-indexed) -> correct count over the 2520-position sequence.
EXPECTED_ANSWERS = tuple(2520 // k for k in range(1, 10))

#: Conditions worth auditing by default: the lanes that measure as collapsed
#: or degraded, plus a clean control.
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
    """SafeLoader mapping unknown tags to plain data instead of refusing them.

    Never calls a constructor found in the file, unlike ``yaml.unsafe_load``, so it
    is safe on repository-generated YAML -- see trap 1 in the module docstring.
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
    """Count response-level outcomes for one results subdirectory of `RESULTS`.

    Returns ``{condition, marks, empty, scored, ans_in_resp, longest}``; `main`'s
    table header names what each count means.

    Raises
    ------
    SystemExit
        If `condition`'s results directory does not exist.
    AssertionError
        If a mark's `answer` disagrees with `EXPECTED_ANSWERS` (trap 2), or if
        `scored` exceeds `ans_in_resp` -- arithmetically impossible, and a signal
        that `EXPECTED_ANSWERS` is wrong for this quiz config.
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
    """Print the response-level audit table for `conditions`, in the given order."""
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
