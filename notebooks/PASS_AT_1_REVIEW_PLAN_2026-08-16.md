# pass@1 review plan — family-ladder scaling study (both legs)

**Date:** 2026-08-16 · **Scope:** all 21 models × 2 legs (induction, deduction)
**Status:** PLAN + measurements. No study code, data, or config was changed by this
document's author. Every S3 access was read-only (`list_objects_v2` / `get_object`);
nothing was written, moved, or deleted in the bucket. The live `ministral-3-14b`
re-collection (babysitter pid 203085) was not touched.

---

## 1. What pass@1 means here

A **pass@1 violation is selection on outcome.**

A reported score is pass@1 iff every cell's number comes from **one** generation, and
that generation was chosen by a rule that **cannot see the outcome of any candidate
generation**.

Consequences of that definition, which the rest of this document applies literally:

* **More than one attempt on record is NOT, by itself, a violation.** An append-only
  log that holds two attempts at a cell is pass@1 as long as the analysis picks between
  them by an outcome-blind rule applied uniformly — "always the earliest run
  timestamp", "always the newest run timestamp", "always the attempt from serving-stack
  X". Those rules are functions of provenance, not of the answer.
* **These ARE violations:**
  * "take any attempt that has content" / "take the non-empty one" / "take the one that
    parsed" — because emptiness correlates with failure, this manufactures successes;
  * "take the attempt that verified" / last-wins over a set produced by re-rolling
    failures — pass@N wearing a pass@1 label;
  * a **regrade** that picks the more favourable of two parses of *one* sample. Same
    bias family, one level down: the sample is fixed but the *reading* of it is selected
    on the outcome.
* **Re-requesting after a transport error is NOT selection on outcome** (HTTP 5xx, spot
  kill, unreachable endpoint). The discarded attempt produced no model answer at all, so
  the discard rule does not read the answer. It is still worth auditing (§5) because the
  boundary between "no answer" and "empty answer" is exactly where the deduction leg
  went wrong once.
* **Two different outcome-blind rules can both be legitimate and still give different
  numbers.** That is the substance of §4, and it is a decision for the user, not a
  defect the review can settle.

Practical restatement used throughout: for each cell, ask **"if this attempt had scored
differently, would a different attempt have survived to the analysis?"** If yes → violation.

---

## 2. Findings verified NOW

Everything in this section was measured on 2026-08-16 by this review. Anything I did
*not* verify is labelled. Section 3 (the plan) is deliberately kept separate — nothing
below is a proposal.

### 2.1 Induction: keys are unique per attempt; nothing is ever overwritten

`S3ResultsStore.dump_marks` builds the key as
`self._info_prefix(model, seed, info) + format_run_ts(run_ts) + ".yaml"`
(`smolbench/evals/results_store.py:981`, written by `put_object` at `:982`), and its own
docstring states:
*"Always creates a NEW object … two calls for the same `addr` at different `run_ts`
values write two DIFFERENT keys, never overwriting one another"*
(`smolbench/evals/results_store.py:962-968`).

**Consequence, and it is the load-bearing one:** an induction re-run can never hide.
Every attempt leaves a distinct object. So the duplicate-object sweep is a *complete*
census of induction re-runs — there is no "overwrote the same key" blind spot.
(Deduction is the same shape by a different mechanism: `all_rows.jsonl` is append-only,
`smolbench/deduction/lean/runner.py:40`.)

### 2.2 Induction: an EMPTY result does NOT trigger a re-run — verified in code

This was the sharpest open exposure, because it is the mechanism that inflated
deduction's `ministral-3-3b`, and duplicate counts would understate it. It is **absent
from the induction leg.** Three links:

1. **The resume predicate is existence, not content.** `has_outstanding` and
   `run_replicates` both gate on `self.store.exists(...)`
   (`smolbench/evals/replicates.py:227` and `:294`). The docstring is explicit:
   *"Against `S3ResultsStore`, ANY logged run of a given (info type, seed) counts as
   'not outstanding'"* (`replicates.py:217-219`).
2. **`exists` never opens the object.** It is
   `list_objects_v2(Bucket=..., Prefix=..., MaxKeys=1)` → `bool(resp.get("Contents"))`
   (`smolbench/evals/results_store.py:919-925`). A key with an all-empty payload is
   indistinguishable from a key with a perfect payload. Emptiness is unobservable to the
   resume path **by construction**.
3. **The empty completion is recorded, not retried.** The `WARNING:root:Body returned
   none value` line the live lane is emitting comes from
   `smolbench/evals/openai_compat.py:716`; the very next statement is
   `return ChatResult(content="", ...)`
   (`openai_compat.py:717-726`) — an immediate return inside the `try`, before the
   `except requests.exceptions.RequestException` retry loop
   (`openai_compat.py:752`). An empty body is a delivered answer, not a retryable error.

**Verdict: induction does not carry the manufactured-success mechanism.** The
140-duplicate census is therefore an upper bound on induction's re-run surface, not an
undercount.

Measured corroboration: across the 280 objects in the 140 duplicated cells, the empty
`response` count is 83 (earliest attempts) vs 92 (newest attempts) — empties *survive*
into the log on both sides rather than being retried away.

### 2.3 Induction re-runs are operator-forced whole-seed blocks, not per-cell retries

`INDUCTION_FORCE_RERUN` takes `""` / `"1"` / `"a-b"` — an inclusive **seed range**
(`notebooks/induction/run_study.py:220-241`, wired at `:613-616`). It has no cell
addressing at all: forcing seed *s* re-collects **all four arms** of that seed. The
duplicate structure matches exactly:

| lane | dup cells | = seeds × arms | seeds covered |
|---|---|---|---|
| `gemma-4-12b` | 56 | 14 × 4 | 0–13 |
| `deepseek-v4-flash` | 48 | 12 × 4 | 0–11 |
| `ministral-3-14b` | 36 | 9 × 4 | 0–8 |

Measured (this review, read-only listing of the three lanes):
`total cells scanned: 332; duplicated cells: 140; max attempts/cell: 2`.
Every duplicated cell has exactly 2 attempts; no cell anywhere has 3.

**This is structurally incompatible with outcome-triggered retry.** An outcome-triggered
rule would produce a ragged, arm-mixed, outcome-correlated set of duplicated cells. What
is on record is contiguous seed blocks, all four arms, uniformly.

### 2.4 The discriminating experiment: induction consumes the NEWEST attempt

The nominated cell was **degenerate** and I am reporting that rather than quietly
swapping it out. `gemma-4-12b` `seed=0` `intens`:

```
intens--20260811T181109Z.yaml   scores: 1 1 1 1 1 1 1 1 1   → 9/9 = 1.000
intens--20260814T014756Z.yaml   scores: 1 1 1 1 1 1 1 1 1   → 9/9 = 1.000
```

Both attempts score 1.000 (that arm is saturated for this model), so this cell cannot
discriminate. The cell that **does** discriminate is `gemma-4-12b` `seed=8` `extens`
(4/9 earliest vs 5/9 newest), and it is pinned by content:

```
extens--20260812T092129Z.yaml (922,083 B)    md5 c654f7d135eae577a5b39338c7b7ddbe
extens--20260814T014842Z.yaml (1,319,921 B)  md5 1c5806dee452ecadcd7245759cd0a976
LOCAL notebooks/induction/results/gemma4_12b_extens/rep_8.yaml
                                             md5 1c5806dee452ecadcd7245759cd0a976
```

The local analysis tree holds the **newest** object, byte for byte. Its score vector
(`1 null null null 1 1 1 null 1` → 5 correct) is the newest attempt's, not the earliest's.

**The chain is closed end to end:**
S3 append-only log → `sync_down` keeps *"the entry with the LEXICOGRAPHICALLY MAXIMUM
`run_ts` per (seed, info)"* (`results_store.py:1347-1352`; fixed-width `run_ts` makes
lexicographic = chronological, `results_store.py:326-334`) → local
`{tag}_{info}/rep_{seed}.yaml` → the headline scripts glob exactly that layout
(`significance_report.py:107`, `extens_vs_noise.py:49`, `paired_analysis.py:95`,
`power_analysis.py:218`, `response_audit.py:100`), regexing `^\s*score:` and counting
`1` as correct (`power_analysis.py:236-241`).

**Induction = newest-wins. Outcome-blind. pass@1-legitimate.**

### 2.5 CONTENT gate on the whole induction tree: 2492/2492 byte-identical

The published analysis verified the local tree against the snapshot **by size**
(`notebooks/FAMILY_LADDER_ANALYSIS_2026-08-16.md:28-40`), with one md5 spot check. Given
the standing "gate on CONTENT, not counts" directive — and that a score flip is
byte-length preserving — I re-ran it as a full md5 sweep of every cell in the log
against the local file:

```
tags parsed: 21
cells in S3 log: 2492
RESULT: {'MATCH': 2492}
local (dir,seed) pairs: 2492
```

Zero mismatches, zero missing, zero local-only. 2492 = 21 × 4 × 30 − 28, the 28 being
`ministral-3-14b`'s seeds that had not landed at the time of the listing. The
size-based claim in the published doc is now confirmed at content level.
(Script: `<scratchpad>/md5_sweep.py`, read-only.)

### 2.6 Deduction: the 2026-08-15 check RE-VALIDATED on the 2026-08-16 snapshot

The stale check (74 cells / 3 lanes) was re-derived from scratch against
`s3://…/analysis/2026-08-16/deduction/<model>/verified_rows.jsonl`, the exact object the
analysis reads. Per lane: group `kind == "cell"` rows at `replicate_idx == 0` by
`(theorem_id, k, rung)`, count groups with >1 row whose verdict is outside
`{exception, replay_failed}`.

| lane | rows | cells | `rep≠0` | multi-attempt | **multi-SURVIVING** | 1st≠success but later success | earliest rate | latest rate | Δ |
|---|---|---|---|---|---|---|---|---|---|
| `ministral-3-3b` | 1524 | 944 | 0 | 479 | **51** | 1 | 0.0661 | 0.0675 | +0.14 pt |
| `gemma-4-31b` | 1587 | 944 | 0 | 638 | **5** | 0 | 0.3511 | 0.3511 | +0.00 |
| `qwen3.5-27b` | 1182 | 944 | 0 | 231 | **5** | 2 | 0.2978 | 0.3006 | +0.28 pt |
| `deepseek-v3.1` | 1359 | 944 | 0 | 415 | **0** | 0 | 0.4410 | 0.4410 | +0.00 |
| `exaone-4.5-33b` | 1414 | 944 | 0 | 470 | **0** | 0 | 0.1601 | 0.1601 | +0.00 |
| `nemotron-3-nano-4b` | 944 | 944 | 0 | **0** | **0** | 0 | 0.0956 | 0.0956 | +0.00 |
| other 15 lanes | 944 | 944 | 0 | 0 | 0 | 0 | — | — | +0.00 |

**TOTAL multi-surviving cells across 21 lanes: 61** (was 74 on 2026-08-15).

Five things this establishes, all new:

1. **`replicate_idx ∈ {0}` still holds everywhere.** 0 rows at `rep≠0` in all 21 lanes.
2. **The `nemotron-3-nano-4b` full re-run REPLACED rather than appended.** 944 rows for
   944 cells, zero duplicates. The pre-re-run data was archived under names the loader
   never reads — `verified_rows_STALE-pre-rerun-2026-08-16.jsonl`,
   `all_rows_SUPERSEDED-mixed-4xl-2xl-2026-08-15.jsonl` — and the S3 fetch path names
   the two filenames literally (`("verified_rows.jsonl", "all_rows.jsonl")`,
   `notebooks/deduction/power_analysis.py:1440`), it does not glob. **This was the one
   scenario that would have broken the earliest-wins rule** (earliest-wins over an
   appended re-run would silently keep the pre-decontamination attempt). It did not happen.
3. **The `deepseek-v3.1` 415-cell repair is clean.** 415 cells hold >1 row but **0** hold
   >1 *surviving* row: the repair re-ran cells whose only record was an `exception`,
   which is the outcome-blind case (nothing was ever measured). Same for
   `exaone-4.5-33b`'s 470.
4. **The sharded-lane merge introduced no duplicates.** All merged lanes report exactly
   944 rows / 944 cells.
5. **Verification absorbed nearly all of the 2026-08-15 resampling inflation.** The
   +5.9 pt figure was measured on *candidate proofs* in `all_rows.jsonl` under the
   **any-attempt-with-content** rule. I re-ran the *same* rule — "success if ANY
   surviving attempt verified" — against the verified verdicts, so the comparison
   matches the one being cited:

   | lane | measured cells | earliest-surviving | **any-surviving-success** | Δ |
   |---|---|---|---|---|
   | `ministral-3-3b` | 711 | 47 = 0.0661 | 48 = 0.0675 | **+0.14 pt** (was +5.9 on candidates) |
   | `qwen3.5-27b` | 712 | 212 = 0.2978 | 214 = 0.3006 | **+0.28 pt** (was +0.6) |
   | `gemma-4-31b` | 712 | 250 = 0.3511 | 250 = 0.3511 | **+0.00 pt** (was +0.5) |

   Any-success and latest-wins coincide exactly here (48/48, 214/214, 250/250), so the
   two columns in the table above are the same number by measurement, not by assumption.
   Only 1 + 2 + 0 = 3 cells in the whole study flip from non-success-first to
   success-later. The resampled candidate proofs largely did not verify.
   *This does not make the rule optional* (§5 R3), but it bounds the exposure.
   (Script: `<scratchpad>/ded_any.py`, read-only.)

The earliest-rule rates reproduce the published table exactly where comparable
(`deepseek-v3.1` 0.441, `gemma-4-31b` 0.351, `qwen3.5-27b` 0.298, `exaone-4.5-33b` 0.160,
`nemotron-3-nano-4b` 0.096, `gemma-4-12b` 0.183 vs published 0.184 rounding), which
independently confirms the published numbers **are** the earliest-surviving numbers.
(Script: `<scratchpad>/ded_scan.py`, read-only.)

### 2.7 The deduction selection rule, read directly

`load_joint_cells` (`notebooks/deduction/power_analysis.py:659-665`):

```python
if row.get("verdict") in UNMEASURABLE_VERDICTS:
    continue                       # exception / replay_failed: never measured
...
if model in by_model:
    continue                       # an earlier attempt already answered this cell
by_model[model] = 1 if row.get("verdict") == "success" else 0
```

Order matters and is correct: unmeasurable rows are dropped *first*, then **first-wins**
over what remains. `incomplete` (an empty answer from a model that was asked) is **not**
in `UNMEASURABLE_VERDICTS` — so an `incomplete` first attempt beats a `success` second
attempt. That is precisely the anti-manufacturing rule. Both downstream scripts import
this same loader (`error_bars.py:65-73,230,365`; `hint_vs_noise.py:42,55-75`), so there
is one selection rule, not three.

### 2.8 The generation-side resume rule is outcome-blind (post-`aab747e4`)

`smolbench/deduction/lean/runner.py:396-477`. The predicate is **"did a request for this
cell ever complete a round trip?"**, evidenced by `prompt_tokens > 0`:

```python
survived = [r for r in rows if r.get("verdict") != "exception"]
if any((r.get("candidate_proof") or "").strip() for r in survived):
    keys.add(key)                  # done: a surviving attempt produced a proof
elif any(int(r.get("prompt_tokens") or 0) > 0 for r in survived):
    keys.add(key)                  # done: asked and answered emptily -- DATA
# else: nothing ever both reached the model AND survived -- re-run
```

An empty answer is **terminal**. The rule cannot re-roll a cell because its answer was
bad, only because no answer was ever obtained. Outcome-blind. The docstring records the
measured non-determinism that makes this matter: *"8/8 byte-identical within one vLLM
process, 0/8 across two"* (`runner.py:425-427`).

### 2.9 `scripts/regrade.py` — cannot have touched this study

The compliance-aware regrade **is** in the selection-on-outcome family (it re-parses a
fixed sample and can flip its verdict). It is, however, **structurally locked out of this
study**: `STUDIES = {"induction": "notebooks/induction/results"}` (`scripts/regrade.py:85-93` (map at `:85-93`)),
and before doing *any* work it resolves each study's store and **refuses outright,
nonzero exit, no file read or written, regardless of `--write`**, if any resolves to
`S3ResultsStore` (`scripts/regrade.py:140-149`, rationale at `:37-64`). The
family-ladder induction study is S3-backed, so the guard fires.

*Belt and braces:* even if a regrade had been forced through, §2.5 proves it left no
trace — all 2492 local files are byte-identical to their S3 originals, and `sync_down`
is documented as a one-way overwrite that *"silently DISCARDS"* local-only edits
(`results_store.py:1289-1294`). **Not verified:** I did not audit shell history for an
attempted invocation; the code-level guard plus the byte-level identity is what I have.

### 2.10 `scripts/merge_lean_shards.py` — collisions are FATAL, never resolved

A gated merge is where two attempts at one cell would collide, so the collision rule is
the whole question. It does not have one, deliberately:

* duplicate cell key `(model, theorem_id, k, rung, replicate_idx)` across shards →
  `raise SystemExit(f"duplicate cell across shards: {k}")` (`merge_lean_shards.py:101-103`);
* duplicate sanity theorem → `SystemExit` (`:104-108`);
* `theorems/` path collision → `SystemExit` (`:124-126`);
* pre-existing canonical `all_rows.jsonl` → `SystemExit(… refusing to clobber)` (`:87`);
* merged totals must equal `--expect-cells` / `--expect-sanity` (944 / 300) (`:109-114`).

All gates run **before anything is written** (`:89`), and shard dirs are pruned only
after a verified spool. There is no picking, so there is nothing to pick wrongly.
Corroborated by measurement: every merged lane shows exactly 944 rows / 944 cells (§2.6).

### 2.11 No reported metric is best-of-N

* `notebooks/deduction/power_analysis.py` contains `pass_at_n(p, n) = 1 - (1-p)**n`
  (`:322`) and `passn_power` (`:923-1005`). Both live **only** inside a Beta-mixture
  Monte Carlo that draws simulated abilities (`rng.beta(...)`, `:1000-1001`) to answer
  "how many replicates *would* be needed". Observed data enters as `marginal_rates`,
  documented as *"Per-model pass@1 rate over all paired cells"* (`:681`). The projection
  is explicitly labelled advisory and is reported alongside the theorem-count sizing
  that the study actually used (`:78-99`).
* `smolbench/evals/replicates.py` has no pass@N construct at all; R=30 replicates are
  independent quiz draws at different seeds, each scored on its own — the study reports
  a rate over 30 × 9 marks, never "did any of 30 succeed".
* `scripts/posterior_power.py` is a DECIDED/EQUIVALENT/UNDECIDED contrast classifier
  (`:22-40`); it explicitly refuses observed-power reasoning and produces no score. Grep
  finds no consumer of it anywhere in the repo.

**Verdict: no headline number is best-of-N.**

### 2.12 Earliest vs newest, quantified (induction, the three duplicate lanes)

Full-lane accuracy under each rule, computed by scoring **every** object in the three
lanes and applying earliest-per-cell vs newest-per-cell:

| lane | arm | cells | earliest | **newest (published)** | Δ (newest − earliest) |
|---|---|---|---|---|---|
| `gemma-4-12b` | intens | 30 | 1.0000 | 0.9963 | −0.37 pt |
| | extens | 30 | 0.5481 | 0.5407 | −0.74 pt |
| | noise_intens | 30 | 0.9926 | 0.9926 | ±0.00 |
| | zero | 30 | 0.0074 | 0.0037 | −0.37 pt |
| `deepseek-v4-flash` | intens | 30 | 0.9593 | 0.9630 | +0.37 pt |
| | extens | 30 | 0.9630 | 0.9667 | +0.37 pt |
| | noise_intens | 30 | 0.9926 | 0.9815 | −1.11 pt |
| | zero | 30 | 0.0296 | 0.0259 | −0.37 pt |
| `ministral-3-14b` † | intens | 23 | 0.5024 | 0.5024 | ±0.00 |
| | extens | 23 | 0.0676 | 0.0918 | **+2.42 pt** |
| | noise_intens | 23 | 0.0290 | 0.0386 | +0.97 pt |
| | zero | 23 | 0.0000 | 0.0000 | ±0.00 |

† **PROVISIONAL.** This lane is live; the listing above is a point-in-time snapshot at
23 of 30 seeds. Seeds 19 and 24–29 have not landed and will change the denominator (and
therefore the deltas) without adding duplicates — those seeds have no prior attempt.

Restricted to the duplicated cells alone the swings are larger (`ministral-3-14b` extens
+6.17 pt over 9 cells; `deepseek-v4-flash` `noise_intens` −2.78 pt over 12) but that is
the wrong denominator for a reported lane rate. **55 of the 140 duplicated cells differ
between the two attempts at all**; the rest are identical, which is why the lane-level
deltas are ≤ 2.42 pt.

**No induction contrast in the published analysis is close enough to a threshold for
these deltas to flip a conclusion — NOT VERIFIED.** I did not re-run
`significance_report.py` under the earliest rule; see Check I-7.

---

## 3. The review plan

Ordered; each check is independent, so a failure does not block the rest. "Status"
distinguishes what this document already ran from what still needs running or writing.

Preamble for every check: `set -a && source notebooks/ec2-operator.env && set +a`,
main venv `.venv/bin/python`, Lean venv `.venv-lean/bin/python`. **All checks are
read-only.** None may run `fleet_teardown.py`, any `aws ec2` mutation, or any S3 write.

### Leg A — induction

**I-1 · Keys are unique per attempt (no overwrite blind spot).**
*Asserts:* every generation event leaves a distinct S3 object, so a duplicate census is
complete.
*Run:* read `results_store.py:962-983`; assert the key contains `format_run_ts(run_ts)`
and that `dump_marks` performs no existence check or delete.
*Accept:* key template ends `…/<info>--<run_ts>.yaml`; no `delete_object` in the module.
*If it fails:* the entire duplicate census is a lower bound and every other induction
check must be re-scoped. **Status: DONE, PASS (§2.1).**

**I-2 · A present-but-empty result never triggers a re-run.**
*Asserts:* induction cannot manufacture successes the way deduction once did.
*Run:* trace `has_outstanding` → `store.exists` → `list_objects_v2(MaxKeys=1)`
(`replicates.py:227`, `results_store.py:919-925`); and
`openai_compat.py:715-726` for the `content is None` early return.
*Accept:* the resume predicate never opens an object; the empty-body path returns rather
than retries.
*If it fails:* induction carries the `ministral-3-3b` mechanism, the duplicate census
understates it, and every lane needs a per-cell empty-then-refilled audit.
**Status: DONE, PASS (§2.2).**

**I-3 · Every duplicate is an operator-forced whole-seed block.**
*Asserts:* re-runs are provenance-driven, not outcome-driven.
*Run:* re-list the 3 lanes; assert dup cells partition as (contiguous seed block) × (all
4 arms) and that `max attempts/cell == 2`. Cross-check `INDUCTION_FORCE_RERUN`'s
range-only grammar (`run_study.py:220-241`).
*Accept:* dup-cell count ≡ 0 (mod 4); every duplicated seed has all four arms duplicated;
no cell has 3+ attempts.
*If it fails* (a lone arm duplicated, or a ragged seed set): that duplicate was not
produced by `INDUCTION_FORCE_RERUN` and needs individual provenance.
**Status: DONE, PASS (§2.3). Tooling: `<scratchpad>/dup_scan.py` — worth promoting into
`scripts/` if this is to be re-run after the live lane finishes.**

**I-4 · The analysis consumes the NEWEST attempt (empirical pin, not docstring).**
*Asserts:* which of the 140 duplicates the study's numbers actually rest on.
*Run:* pick a duplicated cell whose two attempts *differ* (`gemma-4-12b` seed=8
`extens`); `md5sum` both S3 objects and the local `rep_8.yaml`.
*Accept:* local md5 == newest object's md5.
*If it fails:* the published numbers are not the newest-rule numbers and §4 is moot —
find what rule actually produced them before anything else.
**Status: DONE, PASS (§2.4). Note the originally nominated cell (seed=0 `intens`) was
degenerate — both attempts 9/9 — and could not discriminate.**

**I-5 · Content gate on the whole local tree.**
*Asserts:* no local file diverges from its S3 original (a score flip is byte-length
preserving, so size cannot see it).
*Run:* `<scratchpad>/md5_sweep.py` — for every (model, seed, info), md5 the newest S3
object against the local `{tag}_{info}/rep_{seed}.yaml`.
*Accept:* MATCH on 100% of cells; 0 MISSING_LOCAL; 0 local-only.
*If it fails:* a local edit (regrade, hand-fix) is in the analysis path and every
affected number is suspect.
**Status: DONE, PASS — 2492/2492 (§2.5). Tooling: promote `md5_sweep.py` to
`scripts/verify_local_tree.py`; it is ~40 lines and should be re-run after the live lane
lands.**

**I-6 · RE-RUN AFTER `ministral-3-14b` FINISHES.**
*Asserts:* the live lane's fresh seeds (19, 24–29) added no duplicates and no new
selection surface.
*Run:* I-3 + I-4 + I-5 again, plus assert the lane reaches 120 + 36 = 156 objects (128
now + 28 fresh).
*Accept:* dup-cell count still 36; no cell with 3 attempts; md5 sweep 100% MATCH at 2520
cells.
*If it fails:* a fresh seed collided with an existing one — investigate before
republishing.
**Status: NOT RUN — blocked on the live run. This is the single most important
outstanding check.**

**I-7 · Sensitivity: does earliest-vs-newest flip any published conclusion?**
*Asserts:* the §4 decision is (or is not) consequential for the paper's claims, not just
for point estimates.
*Run:* NEEDS WRITING. Add an env-gated selector to the *analysis* side only — e.g.
`INDUCTION_DUP_RULE=earliest|newest` consumed by a copy of `sync_down`'s per-(seed,info)
`max(run_ts)` reduction (`results_store.py:1347-1352`) → sync into a **separate**
scratch tree → re-run `significance_report.py` and `extens_vs_noise.py` against it and
diff the Holm/BH decisions. ~60 lines; must not touch S3 or the canonical local tree.
*Accept:* identical DECIDED/UNDECIDED sets under both rules.
*If it fails:* the §4 decision is load-bearing for a published claim and must be settled
by the user before republication.
**Status: NOT RUN. Point estimates measured (§2.12, max Δ 2.42 pt on a provisional
lane); the significance impact is UNVERIFIED.**

**I-8 · Transport-error retries did not censor the sample.**
*Asserts:* the request-level retry loop discards only attempts that produced no model
answer.
*Run:* read `openai_compat.py:752-790` and `is_retryable_request_error` (`:159`); confirm
retry is triggered only by `requests.exceptions.RequestException` subclasses, never by
inspecting `content`/`finish_reason`.
*Accept:* no branch reads response content to decide to retry.
*If it fails:* a truncated or empty generation is being silently re-drawn inside a single
"attempt" and no duplicate object records it.
**Status: PARTIAL. §2.2 verified the empty-content path returns rather than retries;
I did not read the full retry loop or the streaming transport added in `50ea57f5`.
See R5.**

**I-9 · The live lane's streaming transport is scoring-equivalent.**
*Asserts:* the opt-in streaming path (`50ea57f5`, `73469ad7`) parses into the same
`ChatResult` shape and does not, e.g., drop trailing tokens.
*Run:* NEEDS WRITING — a unit-level comparison of `collect_stream(response)` vs
`response.json()` on a captured body.
*If it fails:* the `ministral-3-14b` tail is not comparable to its head, which is a
homogeneity problem *and* a hidden selection surface if the two transports differ in
empty-response rate.
**Status: NOT RUN.**

### Leg B — deduction

**D-1 · Configured `n_replicates == 1` on all 21 lanes.**
*Run:* read each lane's `manifest.json` / `server_config.yaml` in the snapshot.
*Accept:* 1 everywhere.
**Status: NOT RE-RUN by me — asserted in `CONTAMINATION_INVENTORY_2026-08-15.md:208`.
The recorded-side check (D-2) supersedes it in strength but not in scope; re-run it.**

**D-2 · `replicate_idx ∈ {0}` on all 21 lanes, on the CURRENT snapshot.**
*Run:* `<scratchpad>/ded_scan.py` (`rep≠0` column).
*Accept:* 0 rows at `replicate_idx != 0` in every lane.
**Status: DONE, PASS — 0/21 lanes have any (§2.6).**

**D-3 · Multi-surviving-attempt census on the CURRENT snapshot.**
*Asserts:* how many cells the earliest-wins rule is actually protecting, after the
`nemotron-3-nano-4b` re-run, the `deepseek-v3.1` repair, the shard merge, and the
verification pass.
*Run:* `<scratchpad>/ded_scan.py`, reading `analysis/2026-08-16/deduction/<m>/verified_rows.jsonl`.
*Accept:* the count is *known and bounded*, and the earliest-vs-latest delta is reported
per lane. (There is no "must be zero" criterion — duplicates are legal; unruled
duplicates are not.)
*If it fails* (count grows without an explained cause): a resume path regressed.
**Status: DONE — 61 cells / 3 lanes; max delta +0.28 pt (§2.6). Tooling: promote
`ded_scan.py` to `scripts/audit_pass_at_1.py`; it should run on every future snapshot.**

**D-4 · A re-run lane REPLACES, it does not append.**
*Asserts:* earliest-wins does not silently resurrect pre-decontamination data.
*Run:* for every lane with a `*_SUPERSEDED*` / `*_STALE*` sibling in the snapshot, assert
`verified_rows.jsonl` has exactly 944 cell rows and 0 multi-attempt cells; assert the
loader names files literally rather than globbing (`power_analysis.py:1440`).
*Accept:* re-run lanes show 944/944.
*If it fails:* earliest-wins is the WRONG rule for that lane and the study needs a
per-lane rule keyed on provenance.
**Status: DONE, PASS — `nemotron-3-nano-4b` 944 rows / 944 cells / 0 duplicates (§2.6).
This was the highest-value new check and it came back clean.**

**D-5 · The analysis selection rule is earliest-surviving, applied after the
unmeasurable filter, and is the ONLY such rule.**
*Run:* read `power_analysis.py:659-665` (with `UNMEASURABLE_VERDICTS` at `:518`); confirm `error_bars.py` and `hint_vs_noise.py`
import `load_joint_cells` rather than reimplementing.
*Accept:* `UNMEASURABLE_VERDICTS` filter precedes `if model in by_model: continue`;
`incomplete` is NOT in `UNMEASURABLE_VERDICTS`.
*If it fails* (`incomplete` were excluded as unmeasurable): empty answers would stop
counting as failures and the first-wins protection would be void.
**Status: DONE, PASS (§2.7).**

**D-6 · The generation-side resume rule is outcome-blind.**
*Run:* read `runner.py:396-477`; confirm the predicate is `prompt_tokens > 0`, not
"has content".
*Accept:* a surviving row with `prompt_tokens > 0` and no content marks the cell DONE.
*If it fails:* new collection is resampling again and every lane collected since the
regression needs re-auditing.
**Status: DONE, PASS (§2.8).**

**D-7 · `UNMEASURABLE_VERDICTS` exclusions are genuinely model-independent.**
*Asserts:* dropping `exception` / `replay_failed` is not itself outcome selection.
*Run:* NEEDS WRITING (partially): assert the `replay_failed` cell set is byte-identical
across all 21 lanes (the study claims exactly 232 cells, 100% overlap —
`power_analysis.py:631-637`) and that the `exception` cell set correlates with
infrastructure events, not with model or difficulty.
*Accept:* `replay_failed` set identical across lanes; `nMeas` = 712 (or 711) per lane.
*If it fails:* the denominator is model-dependent and every rate is biased.
**Status: PARTIAL — my scan shows `nMeas` = 712 in 16 lanes and **711** in 5
(`exaone-4.0-32b`, `glm-4.7`, `ministral-3-14b`, `nemotron-3-nano-4b`, `ministral-3-3b`).
One cell in each of those lanes is unmeasurable-only. Small, but it means the denominator
is NOT perfectly constant across lanes and the "232 identical" claim needs the exact
re-check above. NOT VERIFIED by me.**

**D-8 · The shard merge cannot resolve a collision.**
*Run:* read `merge_lean_shards.py:87-114,124-126`; confirm every collision path is
`SystemExit` and every gate precedes the first write.
*Accept:* no branch chooses between two rows for the same cell key.
**Status: DONE, PASS (§2.10).**

### Cross-cutting

**X-1 · No headline number is best-of-N.**
*Run:* grep `pass_at_n` / `passn_power` / Beta-mixture call sites; confirm each is inside
a simulation, and that observed data reaches reports only via `marginal_rates`.
*Accept:* zero call sites apply `pass_at_n` to observed outcomes.
**Status: DONE, PASS (§2.11).**

**X-2 · No regrade output feeds a reported number.**
*Run:* read `regrade.py:85-93,140-150`; confirm the S3 refusal covers the induction tree.
Combine with I-5 (byte identity) as independent corroboration.
**Status: DONE, PASS (§2.9). Shell-history audit NOT performed.**

**X-3 · Reproduce the published rates from the snapshot under the stated rules.**
*Run:* re-run `significance_report.py`, `extens_vs_noise.py`, and
`error_bars.py --mode report` from a clean sync of the snapshot and diff against
`FAMILY_LADDER_ANALYSIS_2026-08-16.md`.
*Accept:* every published rate reproduces exactly.
**Status: PARTIAL — deduction marginal rates reproduce from my independent scan
(§2.6). The induction headline tables were NOT re-run by me.**

---

## 4. The earliest-vs-newest decision — FOR THE USER

**This review cannot settle this and does not attempt to.** Both candidate rules are
outcome-independent, so both are pass@1-legitimate. They select different data.

**The conflict.** There is a standing directive that *"the analysis should use the
earliest result"*, issued in the deduction-resampling context where earliest-surviving is
what removes the manufactured-success bias. The induction leg currently uses **newest**
(§2.4), because its three duplicate lanes are deliberate hardware decontaminations where
newest is the homogeneity-correct pick.

**The framing that dissolves it.** The two legs' duplicates have *different causes*, and
the cause is visible in provenance without ever looking at an outcome:

| | induction | deduction |
|---|---|---|
| what made the duplicate | operator forced a **seed range**, all 4 arms, contiguous from seed 0 (`INDUCTION_FORCE_RERUN`) | a resume rule re-ran **individual cells** that had already answered |
| granularity | whole seed × all arms — cannot address a cell | per cell |
| correlated with outcome? | no — a whole block was re-collected regardless of results | **yes, before `aab747e4`** — retries were triggered by contentlessness |
| the newer attempt is | the *decontaminated* one (homogeneous hardware) | the *resampled* one |
| correct rule | **newest** | **earliest** |

So the rule should be chosen by **cause of duplication**, which is a provenance fact, not
by a single global preference. Under that framing newest-for-induction and
earliest-for-deduction are **one coherent policy**, not a contradiction: *"prefer the
attempt whose provenance is the one you intended to measure; where duplicates arose from
outcome-triggered retry, prefer the earliest, because earliest is the only choice a
retry cannot have biased."*

**Option A — keep the split rule (RECOMMENDED).**
Induction = newest, deduction = earliest.
*For:* each leg gets the rule its duplicate-generating mechanism requires; the three
induction lanes stay serving-stack-homogeneous, which is the whole point of the
2026-08-13/14 re-runs; the published numbers stand unchanged; deduction keeps the
anti-resampling protection. The `ministral-3-14b` case is strengthened by
`50ea57f5`/`73469ad7` putting the live lane on a **different (streaming) transport** —
its fresh objects are not transport-homogeneous with the 2026-08-11 originals either way,
so mixing rules within the lane would be worse.
*Against:* it is two rules, and a reader must be told why. **Mitigation: state the
provenance test in the methods section verbatim.**

**Option B — earliest everywhere.**
*For:* one sentence to defend; matches the standing directive literally; maximally
conservative against any *undiscovered* outcome-triggered induction retry.
*Against:* it silently reverts the hardware decontamination — the numbers would come from
the mixed/pre-migration hardware the re-runs were performed to eliminate. It trades a
confirmed-absent bias (§2.2: induction cannot resample on outcome) for a confirmed-present
confound (heterogeneous serving stacks). It also disagrees with `sync_down`'s
lexicographic-max design (`results_store.py:1347-1352`), so it needs new analysis-side
tooling (Check I-7).

**Cost of switching, measured (§2.12).** Per-arm lane rates move by at most:
`ministral-3-14b` extens **+2.42 pt** (provisional, 23/30 seeds),
`deepseek-v4-flash` `noise_intens` **−1.11 pt**, `gemma-4-12b` extens **−0.74 pt**; the
other nine arms move ≤ 0.37 pt. 18 of 21 lanes are unaffected entirely.
Whether any of these flips a *significance* decision is **NOT VERIFIED** — that is
Check I-7, and it should be run before the decision is finalised if the user is inclined
toward Option B.

**Recommendation: Option A**, with the provenance test in the table above written verbatim
into the methods section. This is a recommendation, not a caveat: the point-estimate cost
of Option B is ≤ 2.42 pt on one provisional lane and ≤ 1.11 pt everywhere else, and 18 of
21 lanes are identical under both rules. **If the user leans toward Option B, run Check
I-7 first** — it is the only check that could make the choice consequential for a
published conclusion rather than for a decimal place.

---

## 5. Residual risks this review cannot close

**R1 · The live lane is unfinished.** Every induction number here is a point-in-time
snapshot at 2492 cells; `ministral-3-14b` is at 23 of 30 seeds. Its earliest-vs-newest
deltas *will* move. Checks I-3/I-4/I-5 must be re-run after it lands (I-6). **Open.**

**R2 · Cell-level identity between the two attempts — spot-verified, not swept.** I
matched duplicates on `(model, seed, info)` and scored them positionally, relying on marks
being serialized in the generator's ascending-period order (`power_analysis.py:214-217`).
If a re-run had generated a *different quiz* for the same seed, the two attempts would not
be comparable and every delta in §2.12 would be meaningless. **Closed on two pairs:** for
`gemma-4-12b` seed=0 `intens` and seed=8 `extens`, all 9 `query` blocks are byte-identical
(md5-per-mark) between the earliest and the newest attempt — quiz generation is
seed-deterministic across the hardware migration. **Not swept across all 140 duplicated
cells**; extend the same md5-per-query comparison in `dup_scan.py` to close it fully.

**R3 · The verified-side inflation bound is not a licence to drop the rule.** §2.6 shows
earliest-vs-latest moves `ministral-3-3b` by only +0.14 pt on *verified* verdicts,
against +5.9 pt on candidates. That is a property of *this* verification pass on *this*
data, not a general guarantee. If verification is ever re-run with a different prover
budget, the resampled candidates could start verifying. The earliest rule must stay.

**R4 · Per-lane denominator is not perfectly constant.** Five deduction lanes measure 711
cells rather than 712 (D-7). Tiny, but it contradicts the clean "944 − 232 = 712"
statement in `power_analysis.py:645-646` and should be explained before the next
publication.

**R5 · Retry-loop and streaming transport unaudited.** I verified that an empty *body*
is not retried (§2.2) but did not read the whole retry loop, and the streaming transport
landed in `50ea57f5` after most lanes were collected. A retry that fires on a mid-stream
truncation would discard a partial generation with no duplicate object to show for it.
Checks I-8/I-9. **Open.**

**R6 · Provenance of `exception` rows.** Dropping them is outcome-blind *if* they are
infrastructure. The study argues this convincingly for `replay_failed` (byte-identical
cell set across 21 lanes) but for `exception` the argument is causal, not statistical.

**Downgraded from "largest unquantified selection risk" — the `deepseek-v3.1` case that
motivated it does not exist** (orchestrator check, 2026-08-16) [VERIFIED]. The 415 figure
is a count of *rows*, not of cells: this lane has 529 single-row cells and 415 two-row
cells, the second row of each being the authorised p5e repair. Resolved per cell under
the earliest-surviving rule the lane lands at exactly **712 measurable / 232 unmeasurable
— the same split as every other lane**, with the 232 breaking down as 139 cells whose
only row is `replay_failed` plus 93 whose first row is an `exception` and whose repair
row is `replay_failed`. So the repair is fully represented in the published snapshot,
nothing is excluded that other lanes keep, and this independently corroborates the
"same 232 cells in every lane" claim from a lane that reached them by a different route.

```
distinct cells: 944 | rows per cell: {1: 529, 2: 415}
earliest-surviving verdict: lean_error 386 · success 314 · incomplete 12
                            ONLY-replay_failed 139 · ONLY-exception 93   -> 232 unmeasurable
```

The general concern survives at much smaller scale: across the other lanes `exception` is
rare, and whether *those* correlate with difficulty is still unverified. Sized as a minor
open item, not the leading risk. See `DEDUCTION_COVERAGE_DIAGNOSIS_2026-08-16.md`, which
owns the question of whether the 232 are a biased subsample.

**R7 · Exception rows that carry an unverified proof are re-drawn.** `runner.py:410-415`
re-runs a cell whose only record is an `exception`, *even when that row carries proof
text*, because the exception may have come from the verifier. Correct for its purpose,
but it does discard a candidate proof and take a fresh draw. Since no verdict ever
existed for the discarded attempt, it is outcome-blind under §1's definition — but it is
the closest thing in the current code to a re-roll, and it deserves a count: how many
cells took this path, per lane? **Not measured.**

**R8 · Nothing here audits the scorer itself.** Every check above concerns *which
generation* is reported. If the parser in `smolbench.evals.parsing` is itself lenient in
an outcome-correlated way, pass@1 integrity would be intact and the numbers still wrong.
Out of scope.

**R9 · Shell-history / manual-intervention audit not performed.** §2.9 and §2.10 are
code-level guarantees plus byte-level corroboration; I did not check whether anyone ever
ran a script with the guards bypassed, nor whether an object was ever hand-placed in the
bucket. The append-only design makes hand-placement visible (it would show as an extra
duplicate), and the census found none beyond the 140 explained ones.

---

### Appendix — read-only tooling written for this review

All in the session scratchpad, none committed, none touching study data:

| script | what it does | promote to |
|---|---|---|
| `dup_scan.py` | census + scores every duplicated induction cell, earliest vs newest | `scripts/audit_induction_duplicates.py` |
| `lane_scan.py` | full-lane accuracy under both rules for the 3 duplicate lanes | fold into the above |
| `md5_sweep.py` | content-gates all 2492 local files against newest S3 object | `scripts/verify_local_tree.py` |
| `ded_scan.py` | multi-surviving-cell census + earliest/latest rates, 21 deduction lanes | `scripts/audit_pass_at_1.py` |
| `ded_any.py` | earliest-surviving vs **any-surviving-success** on the 3 affected lanes | fold into the above |

Still to write: the `INDUCTION_DUP_RULE` analysis-side selector (I-7), the streaming/
non-streaming parse equivalence test (I-9), and the `replay_failed`/`exception` set
comparison across lanes (D-7).
