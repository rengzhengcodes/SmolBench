"""What the solver explored in its reasoning, per arm: reasoning length, distinct
predicates mentioned by kind (fact / chain head / other lemma head / tree intermediate),
same-head candidates listed for the goal, and tool use. Successes vs failures.

A predicate counts only when written as an atom, ``pred(`` (``pred(x)`` or ``pred(c)``),
so English words that happen to look like invented names are not counted. Cells that used
any tool other than Read (grep, shell) are listed, since those searched the file instead of
reading it.

usage: transcript_search.py <rung_dir> <workflow_dir>
"""
import collections, glob, json, re, statistics, sys
from pathlib import Path
from smolbench.deduction.horn.theory import Theory

root, wf = Path(sys.argv[1]), Path(sys.argv[2])
lab = {}
for l in (wf / "journal.jsonl").read_text().splitlines():
    j = json.loads(l)
    if j.get("type") == "started": lab[j.get("label")] = j.get("agentId")
rows = [json.loads(l) for l in (root / "scores.jsonl").read_text().splitlines()]
th = {}
stats = collections.defaultdict(list)
searched = []
for r in rows:
    t = th.setdefault(r["seed"], Theory.from_json((root / f"s{r['seed']:04d}" / "theory.json").read_text()))
    facts = {a.split("(")[0] for a in t.fact_atoms()}
    chain = {lm.head for lm in t.library[: t.m]}
    other = {lm.head for lm in t.library} - chain
    tree = {p for lm in t.library for k, p in lm.node_pred.items() if 0 < len(k) < lm.height}
    aid = lab.get(f"{r['arm']} s{r['seed']} r{r['sample']}")
    fs = glob.glob(str(wf / f"*{aid}*.jsonl")) if aid else []
    if not fs: continue
    text = []
    tools = collections.Counter()
    for line in open(fs[0], encoding="utf-8", errors="replace"):
        try: j = json.loads(line)
        except json.JSONDecodeError: continue
        msg = j.get("message") or {}
        if msg.get("role") != "assistant": continue
        for part in msg.get("content") or []:
            if part.get("type") in ("text", "thinking"):
                text.append(part.get("text") or part.get("thinking") or "")
            elif part.get("type") == "tool_use":
                tools[part.get("name")] += 1
    non_read = {k: v for k, v in tools.items() if k not in ("Read", "StructuredOutput")}
    if non_read: searched.append((r["arm"], r["seed"], r["sample"], non_read))
    txt = "\n".join(text)
    words = set(re.findall(r"\b([a-z]{3,6})\(", txt))
    # rules listed for the goal: lines like "... → goal(x)" in the reasoning
    goal_rules = len(set(re.findall(r"([\w∧ ()]+?)\s*(?:→|->)\s*" + re.escape(t.goal) + r"\(\w+\)", txt)))
    key = (r["arm"], "ok" if r["verdict"] == "success" else "fail")
    stats[key].append(dict(chars=len(txt), fact=len(words & facts), chain=len(words & chain), other=len(words & other), tree=len(words & tree), goal_rules=goal_rules))
print(f"{'arm':6s} {'':4s} {'n':>3s} {'reason kchars':>13s} {'facts':>6s} {'chain':>6s} {'other-lemma':>11s} {'tree-int':>8s} {'goal rules listed':>17s}")
for key in sorted(stats):
    v = stats[key]
    def mean_of(k, v=v):
        return statistics.mean(x[k] for x in v)
    print(f"{key[0]:6s} {key[1]:4s} {len(v):3d} {mean_of('chars')/1000:13.1f} {mean_of('fact'):6.1f} {mean_of('chain'):6.1f} {mean_of('other'):11.1f} {mean_of('tree'):8.1f} {mean_of('goal_rules'):17.1f}")
print(f"\ncells that used tools other than Read: {len(searched)}")
for arm, seed, sample, other in searched:
    print(f"  {arm} s{seed} r{sample} {other}")
