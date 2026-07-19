# CategoryTheory.GradedObject.ιMapObjOrZero_mapMap   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/GradedObject.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

**True premises at k:** `CategoryTheory.GradedObject.ιMapObjOrZero_eq_zero`, `CategoryTheory.Limits.zero_comp`, `CategoryTheory.Limits.comp_zero`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ · | · ✓ ✘ · |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✓ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ · ✘ ✓ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 55.0s, verify 0.1s, in=417, out=2102)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero_of_ne h], rw [ιMapObjOrZero_eq_zero_of_ne h], simp [zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('rw [ιMapObjOrZero_eq_zero_of_ne h], rw [ιMapObjOrZero_eq_zero_of_ne h], simp [zero_comp, comp_zero]'): <stdin>:1:34: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 79.7s, verify 0.2s, in=417, out=3002)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero_of_ne h, ιMapObjOrZero_eq_zero_of_ne h]
rw [zero_comp, comp_zero]
refl
```

**lean_error:** tail step 1/3 ('rw [ιMapObjOrZero_eq_zero_of_ne h, ιMapObjOrZero_eq_zero_of_ne h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 126.2s, verify 4.9s, in=417, out=4764)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero_of_ne h]
rw [zero_comp]
rw [comp_zero]
rfl
```

**lean_error:** tail step 1/4 ('rw [ιMapObjOrZero_eq_zero_of_ne h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 131.2s, verify 17.1s, in=417, out=4776)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero, if_neg h]
rw [zero_comp, comp_zero]
rfl
```

**lean_error:** tail step 1/3 ('rw [ιMapObjOrZero, if_neg h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.8s, verify 0.1s, in=417, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ιMapObjOrZero, h]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.9s, verify 0.1s, in=417, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ιMapObjOrZero, h]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.1s, in=417, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [ιMapObjOrZero, dif_neg h, comp_zero, zero_comp]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.6s, verify 0.2s, in=417, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [ιMapObjOrZero, if_neg h, zero_comp, comp_zero]
```

**final state (truncated):**
```
case neg
I : Type u_1
J : Type u_2
K : Type u_3
C : Type u_4
inst✝⁵ : Category.{u_5, u_4} C
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 8.3s, verify 0.1s, in=417, out=240)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h, comp_zero, zero_comp]
```

**final state (truncated):**
```
case neg
I : Type u_1
J : Type u_2
K : Type u_3
C : Type u_4
inst✝⁵ : Category.{u_5, u_4} C
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.9s, verify 0.1s, in=417, out=263)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ιMapObjOrZero, h]
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.4s, verify 0.2s, in=417, out=285)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_of_ne _ _ _ _ h, ιMapObjOrZero_of_ne _ _ _ _ h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('rw [ιMapObjOrZero_of_ne _ _ _ _ h, ιMapObjOrZero_of_ne _ _ _ _ h, zero_comp, comp_zero]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 9.6s, verify 0.1s, in=417, out=295)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
```

**final state (truncated):**
```
case neg
I : Type u_1
J : Type u_2
K : Type u_3
C : Type u_4
inst✝⁵ : Category.{u_5, u_4} C
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 41.3s, verify 0.7s, in=1037, out=1600)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero h, ιMapObjOrZero_eq_zero h]
simp only [zero_comp, comp_zero]
```

**lean_error:** tail step 1/2 ('rw [ιMapObjOrZero_eq_zero h, ιMapObjOrZero_eq_zero h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 82.4s, verify 0.4s, in=1037, out=3105)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [X.ιMapObjOrZero_eq_zero h, Y.ιMapObjOrZero_eq_zero h]
simp
```

**lean_error:** tail step 1/2 ('rw [X.ιMapObjOrZero_eq_zero h, Y.ιMapObjOrZero_eq_zero h]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 148.3s, verify 34.7s, in=1037, out=5146)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero h, ιMapObjOrZero_eq_zero h]
simp [zero_comp, comp_zero]
```

**lean_error:** tail step 1/2 ('rw [ιMapObjOrZero_eq_zero h, ιMapObjOrZero_eq_zero h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 193.4s, verify 0.6s, in=1037, out=6989)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero X h]
rw [ιMapObjOrZero_eq_zero Y h]
simp only [zero_comp, comp_zero]
```

**lean_error:** tail step 1/3 ('rw [ιMapObjOrZero_eq_zero X h]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=1037, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=1037, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=1037, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=1037, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 5.7s, verify 0.1s, in=1037, out=166)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.8s, verify 0.1s, in=1037, out=167)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.4s, verify 0.1s, in=1037, out=186)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.5s, verify 0.1s, in=1037, out=188)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 77.3s, verify 0.3s, in=1438, out=1623)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 79.4s, verify 0.2s, in=1438, out=1375)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h]'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 96.3s, verify 0.3s, in=1438, out=1528)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 183.1s, verify 10.3s, in=1438, out=3452)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h]'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=1438, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h]'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1438, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=1438, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.2s, verify 0.1s, in=1438, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.9s, verify 0.1s, in=1438, out=169)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 11.3s, verify 0.1s, in=1438, out=192)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero, zero_comp, comp_zero]
```

**final state (truncated):**
```
case neg
I : Type u_1
J : Type u_2
K : Type u_3
C : Type u_4
inst✝⁵ : Category.{u_5, u_4} C
...
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 11.5s, verify 0.1s, in=1438, out=186)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero, ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero, ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 12.2s, verify 0.1s, in=1438, out=197)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 32.4s, verify 0.6s, in=1462, out=1265)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero h, ιMapObjOrZero_eq_zero h]
simp only [zero_comp, comp_zero]
```

**lean_error:** tail step 1/2 ('rw [ιMapObjOrZero_eq_zero h, ιMapObjOrZero_eq_zero h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 56.6s, verify 0.7s, in=1462, out=2160)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero h, ιMapObjOrZero_eq_zero h]
simp
```

**lean_error:** tail step 1/2 ('rw [ιMapObjOrZero_eq_zero h, ιMapObjOrZero_eq_zero h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 73.0s, verify 0.3s, in=1462, out=2743)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h]'): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 92.7s, verify 0.3s, in=1462, out=3503)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=1462, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=1462, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1462, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=1462, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.5s, verify 0.1s, in=1462, out=159)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.6s, verify 0.1s, in=1462, out=188)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.7s, verify 0.1s, in=1462, out=197)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.0s, verify 0.1s, in=1462, out=239)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```
