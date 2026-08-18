# DojoInit recovery — 151 std cells/lane restored to the record (2026-08-18)

**User-authorized 2026-08-18** ("You can fix and run dojoinit"). This is a
**SCOPE-EXTENSION addendum**: the family-ladder deduction headline (Mathlib
only) is closed and unchanged; this document adds verdicts for the 121
recoverable std-library cells per lane and reclassifies the other 30. Nothing
here may be silently pooled with the published Mathlib-only numbers.

## 1. What was lost, and why (diagnosis, compressed)

151 cells/lane — 45 theorems, byte-identical across all 21 lanes, 100%
`.lake/packages/std/` — were graded `replay_failed` with `DojoInitError:
Cannot find the *.ast.json file`. Root cause (CONFIRMED, full evidence chain
in the 2026-08-18 diagnosis session): both grading waves ran with
`HOME=/root` against a LeanDojo traced cache at `/root/.cache/lean_dojo/…`
that **lacked the std package's build tree** — the third occurrence of
LeanDojo's incomplete-fetch fault on this project (two prior local caches
were moved aside as `CORRUPT-*`). The doc's original D1 mechanism ("the std
tree postdates the pass") was refuted by ctimes: the local std build tree
predates the 08-14 pass by two weeks; the pass simply resolved a different,
incomplete cache. Today's cache opens all 45 theorems (45/45 sanity
replays succeed).

## 2. Method

Tool: `scripts/recover_dojoinit_std.py` (tests: `tests/test_recover_dojoinit.py`).
**Additive contract**: the study's `scaling_*` S3 prefixes were read-only
throughout; recovered rows are NEW objects under
`s3://smolbench-results-414266451290/deduction/runs/dojoinit_recovery_2026-08-18/<lane>/recovered_rows.jsonl`
(+ local copies under `notebooks/deduction/results/dojoinit_recovery_2026-08-18/`),
with an in-code assertion making any other S3 PUT key impossible. The bucket
stays an append-only log.

Gates, all passed before any lane ran:
- **Content gate**: `lake` on PATH; 17/17 std `.ast.json` resolve; 45/45
  sanity replays succeed with zero DojoInitError.
- **Control gate (go/no-go)**: 30 Mathlib control cells across 5 lanes
  spanning BOTH grading waves and all three verdict classes, re-verified by
  today's stack: **30/30 exact verdict agreement** (upgrading the
  diagnosis's 6/6). Any disagreement would have aborted the recovery as an
  unauthorized regrade.

Verification used `scripts/lean_verify_rows.py`'s own code paths (one Dojo
session per (theorem,k), candidate-text dedup, 600 s cap) — the machinery
that graded the published 712.

**Two row-selection defects were caught by the tool's own gates during the
run** — recorded because both are lessons:
1. The 151-distinct count gate fired on qwen3.5-27b (178 std rows): five of
   the six re-collected lanes carry duplicate cell rows from the 2026-08-15
   resampling era (nemotron-3-nano-4b, re-verified cleanly on 08-16, has
   none). Fix: dedupe per cell.
2. The report's denominator arithmetic then exposed that earliest-ANY dedupe
   kept spot-kill **exception placeholders** (empty candidates) over later
   surviving rows — and an audit found 27 of qwen3.5-27b's recovered std
   cells had graded an empty placeholder instead of the real candidate,
   **invisibly**: empty candidates verify into measurable buckets, so the
   cross-lane identity assertions could not catch it. The corrected rule
   keeps the **first row that carries a candidate (first non-exception)** —
   the analysis loader itself (`power_analysis.py load_joint_cells`) drops
   BOTH exception and replay_failed rows, a rule that cannot apply to std
   cells (every std study row IS replay_failed); the two rules were measured
   to coincide on the Mathlib column of all seven S3-streamed lanes.
   **A second adversarial-review catch (2026-08-18, later the same day):
   "only qwen3.5-27b had std duplicates" was FALSE** — an artifact of the
   parallel runner swallowing child logs. Four more lanes (gemma-4-31b 98,
   ministral-3-3b 76, deepseek-v3.1 56, exaone-4.5-33b 66 duplicated std
   cells) were recovered inside the 34-minute window between the dedupe
   commit and the rule fix, grading empty placeholders on those cells. All
   four were force-rerun under the corrected rule and the table below
   carries the corrected numbers.

## 3. Results

Every lane: 121 measurable recovered verdicts + 30 `replay_failed`, and the
30-cell unrecoverable set is **byte-identical across all 21 lanes** (asserted).

| lane | Mathlib rate (n) | extended rate (n) | recovered success |
|---|---|---|---|
| qwen3.5-27b | 0.2978 (712) | 0.3037 (833) | 41 |
| qwen3.5-122b-a10b | 0.3455 (712) | 0.3505 (833) | 46 |
| qwen3.5-397b-a17b | 0.3919 (712) | 0.3950 (833) | 50 |
| nemotron-3-nano-4b | 0.0956 (711) | 0.0998 (832) | 15 |
| nemotron-3-nano-30b-a3b | 0.0407 (712) | 0.0504 (833) | 13 |
| nemotron-3-super-120b-a12b | 0.1629 (712) | 0.1753 (833) | 30 |
| gemma-4-e2b | 0.1096 (712) | 0.1248 (833) | 26 |
| gemma-4-12b | 0.1826 (712) | 0.1909 (833) | 29 |
| gemma-4-31b | 0.3511 (712) | 0.3589 (833) | 49 |
| glm-4.7-flash | 0.1461 (712) | 0.1501 (833) | 21 |
| glm-4.5-air | 0.2163 (712) | 0.2329 (833) | 40 |
| glm-4.7 | 0.3601 (711) | 0.3702 (832) | 52 |
| ministral-3-3b | 0.0661 (711) | 0.0649 (832) | 7 |
| ministral-3-8b | 0.0730 (712) | 0.0756 (833) | 11 |
| ministral-3-14b | 0.1027 (711) | 0.1046 (832) | 14 |
| exaone-4.0-32b | 0.1814 (711) | 0.1815 (832) | 22 |
| exaone-4.5-33b | 0.1601 (712) | 0.1705 (833) | 28 |
| k-exaone-236b-a23b | 0.1039 (712) | 0.1140 (833) | 21 |
| deepseek-v4-flash | 0.3469 (712) | 0.3481 (833) | 43 |
| deepseek-v3.1 | 0.4410 (712) | 0.4442 (833) | 56 |
| deepseek-v4-pro | 0.4045 (712) | 0.4166 (833) | 59 |

("rate" = pooled-over-rungs success share of measurable cells, computed
under the study loader's first-surviving-row selection; it is a
self-consistent comparison column, not the study's per-rung headline
statistic. Full verdict distributions and per-cell data:
`notebooks/deduction/results/dojoinit_recovery_2026-08-18/report.json`.
The five (711)-lanes are exactly the coverage diagnosis's five
exception-only-cell lanes — three DojoTacticTimeoutError cells and two
DojoCrashError ("Unexpected EOF") cells on cap-length generations, per the
primary rows — a clean cross-consistency check on the lane set.)

**Accounting (replaces the coverage doc's, per its own §6):**
- DojoInit class: **151 → 0** (pure cache artifact, fully recovered or
  reclassified).
- Prefix/F8 class: **81 → 111** (81 Mathlib + 30 std whose ground-truth
  prefix closes the goal before step k — model-independent, identical in
  every lane).
- Measurable denominator: **712 → 833** per lane (711 → 832 in the five
  exception-cell lanes); block-bootstrap effective blocks **218 → 252 per
  lane** (217 → 251 in `glm-4.7` and `nemotron-3-nano-4b`, whose exception
  cell consumes a whole theorem); the 21-way PAIRED intersection used by
  the analysis is **216 → 250 blocks (707 → 828 cells)**.
- Scope: "Mathlib only" → "Mathlib + 34 of the 45 sampled std theorems".

Notable — and itself a verification lesson: the first published version of
this table showed three lanes scoring LOWER on the extension. That pattern
was **manufactured by the placeholder-grading defect** (§2): once the four
affected lanes were re-graded on their real candidates, gemma-4-31b,
deepseek-v3.1 and exaone-4.5-33b all moved ABOVE their Mathlib rates, and
only ministral-3-3b remains lower by a noise-level 0.12 points. The
corrected picture: the std extension scores at or slightly above Mathlib
for essentially every lane.

## 4. Caveats that must ride any use of these numbers

1. **Different verifier-cache instance than the published 712.** The grading
   cache is on a terminated box (possibly surviving on the stopped
   `verify-lean` instance's EBS in us-west-2 — deliberately left stopped,
   untouched). Substitute evidence: 30/30 control cells agree exactly across
   both grading waves and all verdict classes.
2. `verify_ms` is mixed-provenance (recovered cells timed on this box).
3. The published Mathlib-only headline is UNCHANGED. Any analysis using the
   extension must say so and use the join in `report.json`, not re-pool.
4. Recovered rows carry `recovery_source: dojoinit-recovery-2026-08-18`
   so provenance survives any downstream join.
