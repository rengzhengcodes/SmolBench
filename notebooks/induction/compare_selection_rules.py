"""Isolate the EARLIEST-vs-NEWEST selection rule's effect on induction conclusions.

Both trees carry the SAME seed set, including the 4 fresh ministral
seeds that landed today. So the only difference between them is which
logged attempt each of the 140 multi-attempt cells resolves to. Any
change in the Holm rejection set is attributable to the selection rule,
and nothing else.
"""
import importlib
import sys
from pathlib import Path

import numpy as np

S = Path("/tmp/claude-1001/-workspace-SmolBench/54dbdffb-0485-4ced-9231-fa52049df286/scratchpad")


def run(tree: str) -> dict:
    """Run the primary-contrast McNemar analysis against one scratch results tree.

    Parameters
    ----------
    tree : str
        Subdirectory name under `S` holding one full results tree, built
        under one selection rule (for example, ``"ind_earliest"`` or
        ``"ind_newest"``).

    Returns
    -------
    dict of str -> dict
        Maps each contrast label to a dict with keys ``p`` (exact
        McNemar p-value), ``acc_a``, ``acc_b`` (per-arm accuracy),
        ``n`` (paired sample size), and ``kind`` (the contrast's
        classification from `significance_report.classify`).

    Notes
    -----
    # Design: this function reloads `paired_analysis` and
    # `significance_report` fresh from `tree`'s own copy of the modules
    # on `sys.path`, and clears any cached `sys.modules` entries first.
    # That lets it compare two on-disk result trees, each with its own
    # analysis code snapshot, in the same process, without one import
    # shadowing the other.
    """
    for mod in list(sys.modules):
        if mod in ("power_analysis", "paired_analysis", "significance_report",
                   "_power_common", "run_study"):
            del sys.modules[mod]
    sys.path.insert(0, str(S / tree))
    import paired_analysis as pa
    import significance_report as sr
    importlib.reload(pa)
    correct, valid = pa.load_marks()
    out = {}
    for label, ka, kb in pa.build_primary_contrasts():
        a, b, _ = pa.aligned(correct, valid, ka, kb, drop_invalid=False)
        out[label] = dict(p=pa.mcnemar_exact_p(int((a & ~b).sum()),
                                               int((~a & b).sum())),
                          acc_a=float(a.mean()), acc_b=float(b.mean()),
                          n=int(a.size), kind=sr.classify(label, ka, kb))
    sys.path.remove(str(S / tree))
    return out


def holm(p, alpha=0.05):
    """Apply the Holm step-down procedure to a p-value array.

    Parameters
    ----------
    p : ndarray
        p-values for the tests in one family.
    alpha : float, default 0.05
        Family-wise significance threshold.

    Returns
    -------
    ndarray of bool
        Rejection mask, same shape as `p`.
    """
    m = p.size
    order = np.argsort(p)
    rej = np.zeros(m, bool)
    for i, idx in enumerate(order):
        if p[idx] <= alpha / (m - i):
            rej[idx] = True
        else:
            break
    return rej


E = run("ind_earliest")
N = run("ind_newest")
labels = list(E)
pe = np.array([E[l]["p"] for l in labels])
pn = np.array([N[l]["p"] for l in labels])
re_, rn = holm(pe), holm(pn)

print(f"Contrasts: {len(labels)}   n range: "
      f"{min(E[l]['n'] for l in labels)}-{max(E[l]['n'] for l in labels)}")
print(f"Holm rejections   EARLIEST {re_.sum()}   NEWEST {rn.sum()}")
print(f"Identical rejection set: {np.array_equal(re_, rn)}")

flips = [l for i, l in enumerate(labels) if re_[i] != rn[i]]
print(f"\nContrasts that FLIP significance: {len(flips)}")
for l in flips:
    d = "earliest only" if re_[labels.index(l)] else "newest only"
    print(f"  [{d}] {l}")
    print(f"      earliest p={E[l]['p']:.2e} ({E[l]['acc_a']:.3f} vs {E[l]['acc_b']:.3f})"
          f"  kind={E[l]['kind']}")
    print(f"      newest   p={N[l]['p']:.2e} ({N[l]['acc_a']:.3f} vs {N[l]['acc_b']:.3f})")

moved = [(l, abs(E[l]["acc_a"] - N[l]["acc_a"]), abs(E[l]["acc_b"] - N[l]["acc_b"]))
         for l in labels]
moved = [(l, max(x, y)) for l, x, y in moved if max(x, y) > 1e-9]
moved.sort(key=lambda t: -t[1])
print(f"\nContrasts whose accuracies moved at all: {len(moved)} of {len(labels)}")
for l, d in moved[:6]:
    print(f"  {d:+.4f}  {l}")

# the five clean lanes carrying the extens-vs-noise headline
print("\nHEADLINE extens-vs-noise lanes:")
for m in ("nemo3_4b", "nemo3_30b", "nemo3_120b", "gemma4_e2b", "exaone_236b", "glm_47"):
    lab = f"[{m}] extens vs noise_intens"
    if lab in E:
        i = labels.index(lab)
        print(f"  {m:12s} earliest p={E[lab]['p']:.2e} {'SIG' if re_[i] else '  .'}"
              f"   newest p={N[lab]['p']:.2e} {'SIG' if rn[i] else '  .'}")
