# CategoryTheory.GradedObject.singleObjApplyIso_inv_single_map   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/GradedObject/Single.lean`  

**Ground-truth tail (from k):**
```lean
apply singleObjApplyIsoOfEq_inv_single_map
```

**True premises at k:** `CategoryTheory.GradedObject.singleObjApplyIsoOfEq_inv_single_map`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ · | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✘ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ · |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 72.7s, verify 0.1s, in=294, out=3244)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (singleObjApplyIso j).symm.naturality f
```

**lean_error:** tail step 1/1 ('exact (singleObjApplyIso j).symm.naturality f'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 159.9s, verify 0.1s, in=294, out=7002)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [(singleObjApplyIso j).naturality f], simp [category.assoc, iso.hom_inv_id]
```

**lean_error:** tail step 1/1 ('rw [(singleObjApplyIso j).naturality f], simp [category.assoc, iso.hom_inv_id]'): <stdin>:1:39: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 180.0s, verify 0.1s, in=294, out=7784)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [singleObjApplyIso.inv.naturality f]
```

**lean_error:** tail step 1/1 ('rw [singleObjApplyIso.inv.naturality f]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 224.2s, verify 0.1s, in=294, out=9765)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [(singleObjApplyIso j).symm.naturality f]
```

**lean_error:** tail step 1/1 ('rw [(singleObjApplyIso j).symm.naturality f]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=294, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.6s, verify 0.1s, in=294, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.7s, verify 0.1s, in=294, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.8s, verify 0.1s, in=294, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [singleObjApplyIso]
```

**final state (truncated):**
```
J : Type u_1
C : Type u_2
inst✝² : Category.{u_3, u_2} C
inst✝¹ : HasInitial C
inst✝ : DecidableEq J
j : J
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.6s, verify 0.1s, in=294, out=282)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.8s, verify 0.2s, in=294, out=360)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

**lean_error:** tail step 1/1 ('aesop_cat'): tactic 'aesop' failed, failed to prove the goal after exhaustive search.

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 11.4s, verify 0.1s, in=294, out=381)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 15.5s, verify 0.1s, in=294, out=553)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 26.7s, verify 0.1s, in=644, out=1143)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 43.5s, verify 0.1s, in=644, out=1908)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 44.6s, verify 0.1s, in=644, out=1956)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 47.7s, verify 0.1s, in=644, out=2075)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.1s, in=644, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=644, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleObjApplyIso, singleObjApplyIsoOfEq_inv_single_map]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.4s, verify 0.1s, in=644, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleObjApplyIso, singleObjApplyIsoOfEq_inv_single_map]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=644, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleObjApplyIso, singleObjApplyIsoOfEq_inv_single_map]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 5.5s, verify 0.1s, in=644, out=177)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map _ _ _ _ rfl
```

**lean_error:** tail step 1/1 ('exact singleObjApplyIsoOfEq_inv_single_map _ _ _ _ rfl'): function expected at

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 6.5s, verify 0.1s, in=644, out=212)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.2s, verify 0.1s, in=644, out=237)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 7.6s, verify 0.1s, in=644, out=252)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 34.2s, verify 0.1s, in=801, out=912)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 44.7s, verify 0.1s, in=801, out=936)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 52.2s, verify 0.1s, in=801, out=1153)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 62.2s, verify 0.1s, in=801, out=1378)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=801, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=801, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.7s, verify 0.1s, in=801, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.8s, verify 0.1s, in=801, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 12.2s, verify 0.1s, in=801, out=212)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.6s, verify 0.1s, in=801, out=248)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map _ _ _ _ rfl
```

**lean_error:** tail step 1/1 ('exact singleObjApplyIsoOfEq_inv_single_map _ _ _ _ rfl'): function expected at

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 12.8s, verify 0.1s, in=801, out=223)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 13.9s, verify 0.1s, in=801, out=239)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleObjApplyIsoOfEq, single]
```

**final state (truncated):**
```
J : Type u_1
C : Type u_2
inst✝² : Category.{u_3, u_2} C
inst✝¹ : HasInitial C
inst✝ : DecidableEq J
j : J
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 14.1s, verify 0.1s, in=825, out=562)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 23.9s, verify 0.1s, in=825, out=1021)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 32.2s, verify 0.1s, in=825, out=1391)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 38.3s, verify 0.1s, in=825, out=1648)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=825, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.1s, verify 0.1s, in=825, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=825, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=825, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleObjApplyIso, ← singleObjApplyIsoOfEq_inv_single_map j f j rfl]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 5.9s, verify 0.1s, in=825, out=192)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleObjApplyIsoOfEq_inv_single_map j f j rfl]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 7.5s, verify 0.1s, in=825, out=247)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleObjApplyIsoOfEq_inv_single_map _ _ _ rfl]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.7s, verify 0.1s, in=825, out=282)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [singleObjApplyIso] using singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.8s, verify 0.1s, in=825, out=292)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```
