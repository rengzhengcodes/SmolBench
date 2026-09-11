"""Compare extensional and noise-padded intensional prompts per model.

Token matching separates information from length; non-compliance identifies broken controls.
Seed-level tests: the 30 seeds are the independent unit; item-level McNemar would treat each
seed's 9 harmonic items, which share one answer vector, as independent. They stay in the
210-contrast family because re-correcting at m=21 after picking the subset would be
data-dependent family sizing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from paired_analysis import (  # noqa: E402
    aligned,
    build_primary_contrasts,
    cmh_unpaired_p,
    holm,
    load_marks,
    mcnemar_exact_p,
    seed_diffs,
    signflip_exact_p,
)

# Import the owned threshold to avoid a divergent local value.
from power_analysis import ALPHA, MODELS  # noqa: E402
from significance_report import (  # noqa: E402
    COLLAPSE_THRESHOLD,
    compliance_census,
    hochberg,
)


def mechanism(nc_e: float, nc_n: float) -> str:
    """Classify which of the two mechanisms a lane's contrast can speak to."""
    if nc_n >= COLLAPSE_THRESHOLD:
        return "COLLAPSE"  # noise arm broken: extens-higher is forced
    if nc_e >= COLLAPSE_THRESHOLD:
        return "extens degraded"  # the OTHER arm is the broken one
    return "information"  # both arms well-formed


def direction(acc_e: float, acc_n: float) -> str:
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
    str
        Label for the higher-scoring arm or an exact tie.
    """
    if acc_n > acc_e:
        return "noise HIGHER"
    if acc_n < acc_e:
        return "extens HIGHER"
    return "exactly tied"


def main() -> None:
    """Print the extens-versus-noise report.

    Three-way direction labels keep lane and aggregate tallies consistent.
    """
    correct, valid, compliance = load_marks()
    census = compliance_census(compliance)

    def nc(key: tuple[str, str]) -> float:
        # Missing cells already fail alignment.
        return census[key]["rate"]

    # Keep the full family: the displayed subset is selected after measurement.
    full = []
    for label, key_a, key_b in build_primary_contrasts():
        a, b, sidx, _hidx = aligned(correct, valid, key_a, key_b, drop_invalid=False)
        nb, ncd = int((a & ~b).sum()), int((~a & b).sum())
        full.append(
            {
                "label": label,
                "key_a": key_a,
                "key_b": key_b,
                "p_cluster": signflip_exact_p(seed_diffs(a, b, sidx)),
                "p_item": mcnemar_exact_p(nb, ncd),
                "acc_a": a.mean(),
                "acc_b": b.mean(),
                "n": a.size,
                "b": nb,
                "c": ncd,
                "n_seeds": int(np.unique(sidx).size),
                "disc": (nb + ncd) / max(a.size, 1),
            }
        )
    holm_full = holm(np.array([r["p_cluster"] for r in full]), ALPHA)
    holm_full_item = holm(np.array([r["p_item"] for r in full]), ALPHA)
    full_idx = {(r["key_a"], r["key_b"]): i for i, r in enumerate(full)}

    rows = []
    for model in MODELS:
        ka, kb = (model, "extens"), (model, "noise_intens")
        # Contrast order matches the table's extens/noise columns.
        i_full = full_idx[(ka, kb)]
        fr = full[i_full]
        # This descriptive column needs the aligned arrays.
        a, b, _sidx, hidx = aligned(correct, valid, ka, kb, drop_invalid=False)
        rows.append(
            {
                "model": model,
                "acc_e": fr["acc_a"],
                "acc_n": fr["acc_b"],
                "n": fr["n"],
                "b": fr["b"],
                "c": fr["c"],
                "n_seeds": fr["n_seeds"],
                "disc": fr["disc"],
                "p_cluster": fr["p_cluster"],
                "p_item": fr["p_item"],
                "p_unp": cmh_unpaired_p(a, b, hidx),
                "holm210": bool(holm_full[i_full]),
                "holm210_item": bool(holm_full_item[i_full]),
                "nc_e": nc(ka),
                "nc_n": nc(kb),
                "mech": mechanism(nc(ka), nc(kb)),
            }
        )

    p21 = np.array([r["p_cluster"] for r in rows])
    h21, hb21 = holm(p21, ALPHA), hochberg(p21, ALPHA)
    p21_item = np.array([r["p_item"] for r in rows])

    print("EXTENSIONAL vs NOISE-PADDED INTENSIONAL, per model")
    print("Both arms token-matched; the contrast isolates INFORMATION from LENGTH")
    print(
        "-- WHERE THE NOISE ARM IS A WORKING CONTROL. Where the padding broke "
        "the output\ncontract instead, the same row is a padding-robustness "
        "result; the `mechanism`\ncolumn says which, from measured "
        "non-compliance on both arms."
    )
    print(
        f"PRIMARY p = exact seed-level sign-flip over "
        f"{min(r['n_seeds'] for r in rows)} replicates (the independent "
        f"unit;\n  the 9 harmonics inside a seed share one answer vector). "
        f"Item-level exact\n  McNemar on "
        f"{min(r['n'] for r in rows)}-{max(r['n'] for r in rows)} matched "
        f"marks is shown beside it as a DESCRIPTIVE figure.\n"
    )
    hdr = (
        f"{'model':13s} {'extens':>7s} {'noise':>7s} {'disc':>6s} {'b/c':>9s} "
        f"{'p_seed':>10s} {'p_item':>10s} {'H210':>5s} {'H21':>4s} "
        f"{'Hoch21':>7s}  mechanism / non-compliance"
    )
    print(hdr)
    print("-" * len(hdr))

    def star(ok: bool) -> str:
        """Render a yes/no table cell."""
        return " yes " if ok else "  .  "

    for i, r in enumerate(rows):
        flags = [r["mech"]]
        for lbl, v in (("extens", r["nc_e"]), ("noise", r["nc_n"])):
            if v >= COLLAPSE_THRESHOLD:
                flags.append(f"{lbl} {v:.0%} non-compliant")
        print(
            f"{r['model']:13s} {r['acc_e']:7.3f} {r['acc_n']:7.3f} "
            f"{r['disc']:6.3f} {r['b']:4d}/{r['c']:<4d} "
            f"{r['p_cluster']:10.2e} {r['p_item']:10.2e} "
            f"{star(r['holm210']):>5s} {star(h21[i]):>4s} "
            f"{star(hb21[i]):>7s}  {'; '.join(flags)}"
        )

    print(
        "\nH210 = Holm over the pre-registered 210-contrast family, on the "
        "SEED-LEVEL p\n  (PRIMARY inference). H21 / Hoch21 = Holm / Hochberg "
        "over these 21 only --\n  SENSITIVITY ONLY; re-sizing the family to a "
        "subset chosen after seeing the data\n  is not a valid primary "
        "analysis."
    )
    print(
        f"  agreement: H210 {sum(r['holm210'] for r in rows)}, "
        f"H21 {int(h21.sum())}, Hoch21 {int(hb21.sum())} of {len(rows)}"
    )
    print(
        f"  the same family under the DESCRIPTIVE item-level p: H210 "
        f"{sum(r['holm210_item'] for r in rows)}, H21 "
        f"{int(holm(p21_item, ALPHA).sum())}, Hoch21 "
        f"{int(hochberg(p21_item, ALPHA).sum())} -- the clustering\n  "
        f"correction changes "
        f"{sum(1 for r in rows if r['holm210'] != r['holm210_item'])} of these "
        f"21 primary decisions."
    )

    sig = [r for r in rows if r["holm210"]]
    print(
        f"\nSIGNIFICANT under the primary (m=210, seed-level) correction: "
        f"{len(sig)} of {len(rows)}"
    )
    for r in sorted(sig, key=lambda r: r["p_cluster"]):
        d = direction(r["acc_e"], r["acc_n"])
        print(
            f"  {r['model']:13s} {r['acc_e']:.3f} vs {r['acc_n']:.3f}   "
            f"{d:13s}  [{r['mech']}]   p={r['p_cluster']:.2e}"
        )

    print(f"\n{'=' * 78}\nTHE TWO MECHANISMS\n{'=' * 78}")
    for mech, title, gloss in (
        (
            "information",
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
            "COLLAPSE",
            "PADDING-ROBUSTNESS COLLAPSE (noise arm >= "
            f"{COLLAPSE_THRESHOLD:.0%} non-compliant)",
            "extens > noise is mechanically forced here: an unparseable arm cannot "
            "score.\n  These rows measure what whitespace padding does to the "
            "output contract",
        ),
        (
            "extens degraded",
            f"EXTENS ARM >= {COLLAPSE_THRESHOLD:.0%} NON-COMPLIANT (noise arm "
            f"intact)",
            "the enumeration, not the pad, is what broke the format -- so a "
            "noise-higher\n  result here is partly a format effect too",
        ),
    ):
        sel = [r for r in rows if r["mech"] == mech]
        sel_sig = [r for r in sel if r["holm210"]]
        print(
            f"\n-- {title}: {len(sel)} lane{'' if len(sel) == 1 else 's'}, "
            f"{len(sel_sig)} significant"
        )
        print(f"  {gloss}.")
        for r in sorted(sel, key=lambda r: r["p_cluster"]):
            d = direction(r["acc_e"], r["acc_n"])
            mark = "SIG " if r["holm210"] else "  . "
            print(
                f"  {mark}{r['model']:13s} {r['acc_e']:.3f} vs "
                f"{r['acc_n']:.3f}   {d:13s} "
                f"nc {r['nc_e']:.0%}/{r['nc_n']:.0%}   "
                f"p={r['p_cluster']:.2e}"
            )
        if sel_sig:
            # Explicit comparison keeps ties out of extens-higher.
            up = sum(1 for r in sel_sig if r["acc_n"] > r["acc_e"])
            down = sum(1 for r in sel_sig if r["acc_n"] < r["acc_e"])
            print(
                f"  => direction among the significant ones: {up} "
                f"noise-higher, {down} extens-higher, "
                f"{len(sel_sig) - up - down} tied."
            )

    up_all = sum(1 for r in rows if r["acc_n"] > r["acc_e"])
    down_all = sum(1 for r in rows if r["acc_n"] < r["acc_e"])
    coll = [r for r in rows if r["mech"] == "COLLAPSE"]
    coll_down = sum(1 for r in coll if r["acc_n"] < r["acc_e"])
    print(
        f"\n{'=' * 78}\nRAW DIRECTION, ALL {len(rows)} LANES, NO SIGNIFICANCE "
        f"FILTER\n{'=' * 78}"
    )
    print(
        f"  {up_all} noise-higher, {down_all} extens-higher, "
        f"{len(rows) - up_all - down_all} exactly tied."
    )
    print(
        f"  {coll_down} of the {down_all} extens-higher lanes are "
        f"collapse lanes, where the direction is\n  forced by an unparseable "
        f"noise arm. Any lane list that removed them would remove\n  almost "
        f"exactly the lanes pointing one way -- which is why they are kept "
        f"here and\n  separated by mechanism instead."
    )
    clean_down = [
        r for r in rows if r["acc_n"] < r["acc_e"] and r["mech"] == "information"
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
