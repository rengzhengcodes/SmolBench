# RatFunc.ofFractionRing_algebraMap   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
rw [← mk_one, mk_one']
```

**True premises at k:** `RatFunc.mk_one`, `RatFunc.mk_one'`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✘ ✘ | ✘ ✘ ✘ ✓ | ✓ ✓ ✘ ✓ ✘ ✓ ✓ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✓ ✘ ✓ ✓ ✓ ✘ |
| `noise:3` | ✓ ✘ ✓ ✘ | ✘ ✓ ✘ ✘ | ✘ ✓ ✘ ✓ ✘ ✘ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 20.7s, verify 0.1s, in=265, out=617)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 25.4s, verify 0.1s, in=265, out=791)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 26.9s, verify 0.1s, in=265, out=856)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 120.2s, verify 0.1s, in=265, out=4511)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.6s, verify 0.1s, in=265, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=265, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=265, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.0s, verify 0.1s, in=265, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [RatFunc.algebraMap_def]
```

**lean_error:** tail step 1/1 ('simp [RatFunc.algebraMap_def]'): unknown constant 'RatFunc.algebraMap_def'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.0s, verify 0.1s, in=265, out=176)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.ofFractionRing_eq_algebraMap]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.ofFractionRing_eq_algebraMap]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 7.3s, verify 0.1s, in=265, out=184)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.0s, verify 0.1s, in=265, out=205)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [RatFunc.algebraMap_eq]
```

**lean_error:** tail step 1/1 ('simp [RatFunc.algebraMap_eq]'): unknown constant 'RatFunc.algebraMap_eq'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 12.6s, verify 0.1s, in=265, out=225)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 13.0s, verify 0.1s, in=265, out=234)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.1s, verify 0.1s, in=265, out=236)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 17.1s, verify 0.1s, in=265, out=238)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 18.2s, verify 0.1s, in=265, out=361)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [RatFunc.coe_def]
```

**lean_error:** tail step 1/1 ('simp [RatFunc.coe_def]'): unknown constant 'RatFunc.coe_def'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 43.6s, verify 0.2s, in=634, out=1502)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one x]
rw [mk_one' x]
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 52.8s, verify 0.1s, in=634, out=1847)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 58.5s, verify 0.1s, in=634, out=2059)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 75.6s, verify 0.1s, in=634, out=2717)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=634, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=634, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("simp [mk_one, mk_one']"): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=634, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one, ← mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, ← mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.8s, verify 0.1s, in=634, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one, mk_one']
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 13.6s, verify 0.1s, in=634, out=245)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one, ← mk_one']
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 14.1s, verify 0.1s, in=634, out=258)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one, mk_one']
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 15.0s, verify 0.1s, in=634, out=184)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one]
```

**lean_error:** tail step 1/1 ('rw [mk_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 16.4s, verify 0.1s, in=634, out=319)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one, mk_one']
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 22.0s, verify 0.1s, in=634, out=282)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 6 → **success**  (gen 23.9s, verify 0.1s, in=634, out=301)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one', mk_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 5 → **success**  (gen 24.8s, verify 0.1s, in=634, out=355)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one', ← mk_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 27.3s, verify 0.1s, in=634, out=355)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa only [← ofFractionRing_algebraMap, mk_one'] using mk_one x
```

**lean_error:** tail step 1/1 ("simpa only [← ofFractionRing_algebraMap, mk_one'] using mk_one x"): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 67.4s, verify 0.1s, in=1825, out=1416)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_one', mk_one]
rfl
```

**lean_error:** tail step 1/2 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 78.1s, verify 0.1s, in=1825, out=1307)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_one, mk_one']
rfl
```

**lean_error:** tail step 1/2 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 82.9s, verify 0.1s, in=1825, out=2141)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one', RatFunc.mk_one]
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one', RatFunc.mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 88.1s, verify 0.1s, in=1825, out=2569)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=1825, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=1825, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("simp [mk_one, mk_one']"): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1825, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [RatFunc.mk, RatFunc.mk_one', mk_coe_def, IsLocalization.mk'_one, Submonoid.coe_one]
```

**lean_error:** tail step 1/1 ("simp [RatFunc.mk, RatFunc.mk_one', mk_coe_def, IsLocalization.mk'_one, Submonoid.coe_one]"): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 71.1s, verify 0.1s, in=1825, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one, RatFunc.mk_one']
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one, RatFunc.mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 36.3s, verify 0.1s, in=1825, out=195)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("simp [mk_one, mk_one']"): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 38.6s, verify 0.1s, in=1825, out=301)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 4 → **success**  (gen 39.0s, verify 0.1s, in=1825, out=292)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← mk_one', mk_one]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 39.5s, verify 0.1s, in=1825, out=221)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 40.4s, verify 0.1s, in=1825, out=277)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← mk_one, ← mk_one']
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 7 → **success**  (gen 40.6s, verify 0.1s, in=1825, out=313)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← mk_one, mk_one']
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 41.5s, verify 0.1s, in=1825, out=397)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← mk_one, mk_one']
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 107.7s, verify 0.1s, in=1825, out=425)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← mk_one, ← mk_one', transitivity RatFunc.mk x 1]
```

**lean_error:** tail step 1/1 ("rw [← mk_one, ← mk_one', transitivity RatFunc.mk x 1]"): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 81.2s, verify 0.1s, in=1850, out=2937)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← mk_one, mk_one']
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 89.4s, verify 0.1s, in=1850, out=3240)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 126.3s, verify 0.1s, in=1850, out=4747)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← mk_one', mk_one]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 149.1s, verify 0.1s, in=1850, out=5708)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=1850, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("simp [mk_one, mk_one']"): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.6s, verify 0.2s, in=1850, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← mk_one', ← mk_one]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.9s, verify 0.1s, in=1850, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_one, ← mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, ← mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.0s, verify 0.1s, in=1850, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 24.5s, verify 0.1s, in=1850, out=248)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one, RatFunc.mk_one']
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one, RatFunc.mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 26.9s, verify 0.1s, in=1850, out=333)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← mk_one, ← mk_one']
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 27.1s, verify 0.1s, in=1850, out=318)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one x, ← RatFunc.mk_one' x, RatFunc.ofFractionRing_algebraMap]
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one x, ← RatFunc.mk_one' x, RatFunc.ofFractionRing_algebraMap]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 6 → **success**  (gen 28.2s, verify 0.1s, in=1850, out=268)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← mk_one, mk_one']
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 34.7s, verify 0.1s, in=1850, out=483)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("simpa only [mk_one, mk_one']"): tactic 'assumption' failed

### `noise:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 34.8s, verify 0.1s, in=1850, out=312)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← mk_one, ← mk_one', RatFunc.ofFractionRing_algebraMap]
```

**lean_error:** tail step 1/1 ("rw [← mk_one, ← mk_one', RatFunc.ofFractionRing_algebraMap]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 37.9s, verify 0.1s, in=1850, out=513)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
trans (RatFunc.mk_one' x) (RatFunc.mk_one x)
```

**lean_error:** tail step 1/1 ("trans (RatFunc.mk_one' x) (RatFunc.mk_one x)"): function expected at

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 95.7s, verify 0.1s, in=1850, out=398)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [← mk_one, mk_one']
```
