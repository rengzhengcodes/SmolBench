"""Write answers returned by a horn-solve-rung workflow into the rung tree and score it.

usage: collect_rung.py <journal.jsonl> <rung_dir>
"""
import collections, json, re, subprocess, sys
from pathlib import Path

journal, rung = Path(sys.argv[1]), Path(sys.argv[2])
rows = []
labels = {}
for line in journal.read_text(encoding="utf-8").splitlines():
    d = json.loads(line)
    if d.get("type") == "started":
        labels[d.get("agentId")] = d.get("label") or ""
        labels[d.get("key")] = d.get("label") or ""
    if d.get("type") != "result":
        continue
    label = labels.get(d.get("agentId")) or labels.get(d.get("key")) or ""
    mt = re.match(r"(?:(\S+) )?s(\d+) r(\d+)$", label)
    res = d.get("result")
    if not mt or not isinstance(res, dict):
        continue
    rows.append((mt.group(1) or "lem", int(mt.group(2)), int(mt.group(3)), res.get("status"), res.get("answer") or ""))
counts = collections.Counter(r[3] for r in rows)
print(f"{len(rows)} results; status counts {dict(counts)}")
n_written = 0
for arm, seed, sample, status, answer in rows:
    if status == "confused":
        continue
    d = rung / f"s{seed:04d}" / arm
    text = answer if status == "proof" else "give up\n"
    (d / f"answer.s{sample}.md").write_text(text.rstrip() + "\n", encoding="utf-8")
    n_written += 1
print(f"wrote {n_written} answer files")
subprocess.run([sys.executable, "-m", "smolbench.deduction.horn.score", str(rung),
                "--json", str(rung / "scores.jsonl")], cwd=Path(__file__).resolve().parents[3], check=False)
