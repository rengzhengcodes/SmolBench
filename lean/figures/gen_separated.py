"""Generate separated open/closed figures.

Runs each paper figure script with --weight-class open and closed and copies
the outputs to figures/separated/. The analysis set is per model (see
_util.load_analysis): each model's curve uses the (theorem, k) pairs where
THAT model has scored rows at every level, and its theorem count is shown in
the legend. Open-weight models come from the full-size run only; closed
models are in both runs.
"""

import subprocess, shutil
from pathlib import Path

fig_dir = Path(__file__).resolve().parent
sep_dir = fig_dir / "separated"
sep_dir.mkdir(exist_ok=True)

import sys
sys.path.insert(0, str(fig_dir))
from _util import DEFAULT_RUNS, FULL_SIZE_RUNS  # noqa: E402

scripts = ["success_rate_bars.py", "marginal_content_vs_noise.py", "none_vs_mpi.py"]
full_runs = [r for r in DEFAULT_RUNS if r in FULL_SIZE_RUNS]

for script in scripts:
    base = Path(script).stem
    for wc in ["open", "closed"]:
        runs = full_runs if wc == "open" else DEFAULT_RUNS
        cmd = ["uv", "run", "python", str(fig_dir / script),
               "--runs"] + runs + ["--weight-class", wc]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           cwd=str(fig_dir.parent))
        last = r.stdout.strip().split("\n")[-1] if r.stdout.strip() else r.stderr.strip()[-200:]
        src = fig_dir / f"{base}.png"
        dst = sep_dir / f"{base}_{wc}.png"
        if src.exists():
            shutil.copy(src, dst)
            print(f"{base}_{wc}: {last}")
        else:
            print(f"{base}_{wc}: FAILED — {r.stderr[-200:]}")

# Restore combined
for script in scripts:
    subprocess.run(["uv", "run", "python", str(fig_dir / script)],
                   capture_output=True, cwd=str(fig_dir.parent))
print("\nrestored combined figures")
