"""Compare extensional and noise-padded intensional prompts per model.

Token matching separates information from length; non-compliance identifies broken controls.
Seed-level tests use the registered replicates as the independent unit; item-level McNemar
would treat each seed's harmonic items, which share one answer vector, as independent. They
stay in the primary contrast family because re-correcting after picking the subset would be
data-dependent family sizing.
"""

import sys
from collections import Counter
from enum import StrEnum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from paired_analysis import hochberg, holm, labeled_rows, load_marks  # noqa: E402
from power_analysis import (  # noqa: E402
    ALPHA,
    MODELS,
    N_HARMONICS,
    N_PRIMARY,
    RESULTS_DIR,
    build_primary_contrasts,
)
from significance_report import (  # noqa: E402
    COLLAPSE_THRESHOLD,
    common_seed_rate,
    compliance_census,
)


class Mechanism(StrEnum):
    """Compliance mechanism labels."""

    INFORMATION = "information"
    NOISE_COLLAPSED = "noise COLLAPSED"
    EXTENS_COLLAPSED = "extens COLLAPSED"
    BOTH_COLLAPSED = "both COLLAPSED"


class Direction(StrEnum):
    """Which arm scored higher on the compared seeds."""

    NOISE = "noise HIGHER"
    EXTENS = "extens HIGHER"
    TIED = "exactly tied"


def mechanism(nc_e: float, nc_n: float) -> Mechanism:
    """Annotate which arms crossed the collapse threshold.

    The label says only which arm(s) failed the output contract on the compared
    seeds, never which scored higher; direction is always read from `direction`.

    Parameters
    ----------
    nc_e : float
        Non-compliance rate of the extens arm on the compared seeds.
    nc_n : float
        Non-compliance rate of the noise arm on the compared seeds.

    Returns
    -------
    Mechanism
        Compliance annotation for the lane.
    """
    e_bad, n_bad = nc_e >= COLLAPSE_THRESHOLD, nc_n >= COLLAPSE_THRESHOLD
    if e_bad and n_bad:
        return Mechanism.BOTH_COLLAPSED
    if n_bad:
        return Mechanism.NOISE_COLLAPSED
    if e_bad:
        return Mechanism.EXTENS_COLLAPSED
    return Mechanism.INFORMATION


def direction(acc_e: float, acc_n: float) -> Direction:
    """Label the higher-scoring arm or an exact tie.

    Ties need their own branch so tallies do not award them to ``extens``.

    Parameters
    ----------
    acc_e : float
        Accuracy for the extens arm.
    acc_n : float
        Accuracy for the noise arm.

    Returns
    -------
    Direction
        Label for the higher-scoring arm or an exact tie.
    """
    if acc_n > acc_e:
        return Direction.NOISE
    if acc_n < acc_e:
        return Direction.EXTENS
    return Direction.TIED


def noncompliance_rate(
    census: dict[tuple[str, str], dict],
    key: tuple[str, str],
    seeds: list[int],
) -> float:
    """Return one arm's non-compliance rate over the compared seeds.

    Parameters
    ----------
    census : dict[tuple[str, str], dict]
        `compliance_census` output.
    key : tuple[str, str]
        ``(model, info)`` cell of the arm.
    seeds : list[int]
        Seeds both arms of the contrast cover.

    Returns
    -------
    float
        Pooled non-compliance rate over `seeds`.

    Raises
    ------
    RuntimeError
        If the arm has no marks on `seeds`.
    """
    rate = common_seed_rate(census[key], seeds)
    if rate is None:
        raise RuntimeError(f"no compared-seed marks for {key}")
    return rate


def _star(ok: bool) -> str:
    """Render a yes/no table cell.

    Parameters
    ----------
    ok : bool
        Whether the cell is a rejection.

    Returns
    -------
    str
        Fixed-width ``yes`` or ``.`` cell.
    """
    return " yes " if ok else "  .  "


def main(results_dir: Path = RESULTS_DIR) -> None:
    """Print the extens-versus-noise report.

    Three-way direction labels keep lane and aggregate tallies consistent.

    Parameters
    ----------
    results_dir : Path
        Results tree read by `paired_analysis.load_marks`.
    """
    marks = load_marks(results_dir)
    census = compliance_census(marks)

    # Keep the full family: the displayed subset is selected after measurement.
    full = labeled_rows(marks, build_primary_contrasts())
    holm_full = holm(np.array([r["p_cluster"] for r in full]), ALPHA)
    holm_full_item = holm(np.array([r["p_item"] for r in full]), ALPHA)
    full_idx = {(r["key_a"], r["key_b"]): i for i, r in enumerate(full)}

    # One lane per model: its family contrast row (``a`` = extens, ``b`` = noise)
    # plus the family-level Holm decisions and the compliance annotation.
    rows = []
    for model in MODELS:
        ka, kb = (model, "extens"), (model, "noise_intens")
        i_full = full_idx[(ka, kb)]
        fr = full[i_full]
        nc_e, nc_n = noncompliance_rate(census, ka, fr["seeds"]), noncompliance_rate(
            census, kb, fr["seeds"]
        )
        rows.append(
            {
                **fr,
                "model": model,
                "dir": direction(fr["acc_a"], fr["acc_b"]),
                "holm_full": bool(holm_full[i_full]),
                "holm_full_item": bool(holm_full_item[i_full]),
                "nc_e": nc_e,
                "nc_n": nc_n,
                "mech": mechanism(nc_e, nc_n),
            }
        )

    p_sub = np.array([r["p_cluster"] for r in rows])
    h_sub, hb_sub = holm(p_sub, ALPHA), hochberg(p_sub, ALPHA)
    p_sub_item = np.array([r["p_item"] for r in rows])

    n_models = len(MODELS)
    hdr = (
        f"{'model':13s} {'extens':>7s} {'noise':>7s} {'disc':>6s} {'b/c':>9s} "
        f"{'p_seed':>10s} {'p_item':>10s} {f'H{N_PRIMARY}':>5s} "
        f"{f'H{n_models}':>4s} "
        f"{f'Hoch{n_models}':>7s}  mechanism / non-compliance"
    )
    print(
        "EXTENSIONAL vs NOISE-PADDED INTENSIONAL, per model\n"
        "Both arms token-matched; the contrast isolates INFORMATION from LENGTH\n"
        "-- WHERE THE NOISE ARM IS A WORKING CONTROL. Where the padding broke the output\n"
        "contract instead, the same row is a padding-robustness result; the `mechanism`\n"
        "column says which, from measured non-compliance on both arms over the seeds the\n"
        "two arms share. It annotates compliance only; the direction of every row is the\n"
        "measured one.\n"
        f"PRIMARY p = exact seed-level sign-flip over {min(r['n_seeds'] for r in rows)} "
        f"replicates (the independent unit;\n  the {N_HARMONICS} harmonics inside a seed "
        f"share one answer vector). Item-level exact\n  McNemar on "
        f"{min(r['n'] for r in rows)}-{max(r['n'] for r in rows)} matched marks is "
        f"shown beside it as a DESCRIPTIVE figure.\n\n{hdr}\n" + "-" * len(hdr)
    )

    for i, r in enumerate(rows):
        flags = [r["mech"]]
        for lbl, v in (("extens", r["nc_e"]), ("noise", r["nc_n"])):
            if v >= COLLAPSE_THRESHOLD:
                flags.append(f"{lbl} {v:.0%} non-compliant")
        print(
            f"{r['model']:13s} {r['acc_a']:7.3f} {r['acc_b']:7.3f} "
            f"{r['disc']:6.3f} {r['b']:4d}/{r['c']:<4d} "
            f"{r['p_cluster']:10.2e} {r['p_item']:10.2e} "
            f"{_star(r['holm_full']):>5s} {_star(h_sub[i]):>4s} "
            f"{_star(hb_sub[i]):>7s}  {'; '.join(flags)}"
        )

    sig = [r for r in rows if r["holm_full"]]
    print(
        f"\nH{N_PRIMARY} = Holm over the pre-registered {N_PRIMARY}-contrast family, "
        f"on the SEED-LEVEL p\n  (PRIMARY inference). H{n_models} / Hoch{n_models} = "
        f"Holm / Hochberg over these {n_models} only --\n  SENSITIVITY ONLY; re-sizing "
        "the family to a subset chosen after seeing the data\n  is not a valid primary "
        "analysis.\n"
        f"  agreement: H{N_PRIMARY} {len(sig)}, H{n_models} {int(h_sub.sum())}, "
        f"Hoch{n_models} {int(hb_sub.sum())} of {n_models}\n"
        f"  the same family under the DESCRIPTIVE item-level p: H{N_PRIMARY} "
        f"{sum(r['holm_full_item'] for r in rows)}, H{n_models} "
        f"{int(holm(p_sub_item, ALPHA).sum())}, Hoch{n_models} "
        f"{int(hochberg(p_sub_item, ALPHA).sum())} -- the clustering\n  "
        f"correction changes "
        f"{sum(1 for r in rows if r['holm_full'] != r['holm_full_item'])} of "
        f"these {n_models} primary decisions.\n"
        f"\nSIGNIFICANT under the primary (m={N_PRIMARY}, seed-level) "
        f"correction: {len(sig)} of {n_models}"
    )
    for r in sorted(sig, key=lambda r: r["p_cluster"]):
        print(
            f"  {r['model']:13s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}   "
            f"{r['dir']:13s}  [{r['mech']}]   p={r['p_cluster']:.2e}"
        )

    print(f"\n{'=' * 78}\nTHE TWO MECHANISMS\n{'=' * 78}")
    for mech, title, gloss in (
        (
            Mechanism.INFORMATION,
            "INFORMATION / LABEL-DENSITY (both arms well-formed)",
            "the noise arm obeys the output contract, so the comparison is not "
            "about whether\n  the model could answer at all. CAVEAT: the "
            "compliance criterion is a FORMAT gate --\n  `parse_numeric` accepts "
            "any bare integer, so an answer that is well-formed and\n  "
            "systematically wrong is invisible to it. A lane can therefore be "
            "clean and directionally\n  correct while its effect is one "
            "saturated failure mode repeated, not graded induction difficulty",
        ),
        (
            Mechanism.NOISE_COLLAPSED,
            "PADDING-ROBUSTNESS COLLAPSE (noise arm >= "
            f"{COLLAPSE_THRESHOLD:.0%} non-compliant, extens arm intact)",
            "the pad broke the output contract on the noise arm, so this row "
            "measures\n  what whitespace padding does to compliance as much as "
            "to accuracy. Direction is\n  reported as measured, not inferred "
            "from the compliance gap",
        ),
        (
            Mechanism.EXTENS_COLLAPSED,
            f"EXTENS ARM >= {COLLAPSE_THRESHOLD:.0%} NON-COMPLIANT (noise arm "
            f"intact)",
            "the enumeration, not the pad, is what broke the format -- so the "
            "accuracy\n  contrast here is partly a format effect too",
        ),
        (
            Mechanism.BOTH_COLLAPSED,
            f"BOTH ARMS >= {COLLAPSE_THRESHOLD:.0%} NON-COMPLIANT",
            "neither arm is a working control; the row is a compliance result "
            "on both\n  sides and its accuracy direction is not attributable to "
            "either mechanism",
        ),
    ):
        sel = [r for r in rows if r["mech"] == mech]
        sel_sig = [r for r in sel if r["holm_full"]]
        print(
            f"\n-- {title}: {len(sel)} lane{'' if len(sel) == 1 else 's'}, "
            f"{len(sel_sig)} significant\n  {gloss}."
        )
        for r in sorted(sel, key=lambda r: r["p_cluster"]):
            print(
                f"  {'SIG ' if r['holm_full'] else '  . '}{r['model']:13s} "
                f"{r['acc_a']:.3f} vs {r['acc_b']:.3f}   {r['dir']:13s} "
                f"nc {r['nc_e']:.0%}/{r['nc_n']:.0%}   p={r['p_cluster']:.2e}"
            )
        if sel_sig:
            sig_dirs = Counter(r["dir"] for r in sel_sig)
            up, down = sig_dirs[Direction.NOISE], sig_dirs[Direction.EXTENS]
            print(
                f"  => direction among the significant ones: {up} "
                f"noise-higher, {down} extens-higher, "
                f"{len(sel_sig) - up - down} tied."
            )

    dirs = Counter(r["dir"] for r in rows)
    up_all, down_all = dirs[Direction.NOISE], dirs[Direction.EXTENS]
    coll_dirs = Counter(r["dir"] for r in rows if r["mech"] != Mechanism.INFORMATION)
    print(
        f"\n{'=' * 78}\nRAW DIRECTION, ALL {n_models} LANES, NO SIGNIFICANCE "
        f"FILTER\n{'=' * 78}\n"
        f"  {up_all} noise-higher, {down_all} extens-higher, "
        f"{n_models - up_all - down_all} exactly tied.\n"
        f"  {coll_dirs[Direction.EXTENS]} of the {down_all} extens-higher and "
        f"{coll_dirs[Direction.NOISE]} of the {up_all} noise-higher lanes have at least "
        f"one\n  arm over the {COLLAPSE_THRESHOLD:.0%} non-compliance threshold."
        # The retention rationale describes collapsed lanes, so it prints only
        # when there is at least one.
        + (
            " Those lanes are kept and annotated rather\n  than removed: dropping "
            "them would select on a covariate of the outcome."
            if coll_dirs.total()
            else ""
        )
    )
    clean_down = [
        r
        for r in rows
        if r["dir"] == Direction.EXTENS and r["mech"] == Mechanism.INFORMATION
    ]
    if clean_down:
        print(
            f"  Extens-higher on WELL-FORMED arms: "
            f"{', '.join(r['model'] for r in clean_down)} -- the genuine "
            f"counter-example(s),\n  reported at their own p: "
            + "; ".join(f"{r['model']} p={r['p_cluster']:.2e}" for r in clean_down)
            + "."
        )


if __name__ == "__main__":
    main()
