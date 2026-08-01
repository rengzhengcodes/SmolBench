# CategoryTheory.GradedObject.singleObjApplyIso_inv_single_map   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/GradedObject/Single.lean`  

**Ground-truth tail (from k):**
```lean
apply singleObjApplyIsoOfEq_inv_single_map
```

**True premises at k:** `CategoryTheory.GradedObject.singleObjApplyIsoOfEq_inv_single_map`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=321, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Iso.inv_comp_eq, Iso.eq_comp_inv]
simp only [singleObjApplyIso_hom, single_map_hom]
```

**lean_error:** tail step 1/2 ('rw [Iso.inv_comp_eq, Iso.eq_comp_inv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=295, out=46)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Category.assoc, ← (single j).map_comp, singleObjApplyIso_inv, singleObjApplyIso_inv, ← Category.assoc, Category.assoc]
simp only [Functor.id_map]
rfl
```

**lean_error:** tail step 1/3 ('rw [← Category.assoc, ← (single j).map_comp, singleObjApplyIso_inv, singleObjApplyIso_inv, ← Category.assoc, Category.assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 3.3s, in=310, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iso.inv_comp_eq
simp [singleObjApplyIso_hom]
```

**lean_error:** tail step 1/2 ('apply Iso.inv_comp_eq'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.6s, verify 0.2s, in=671, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [singleObjApplyIso, singleObjApplyIsoOfEq]
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=642, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleObjApplyIsoOfEq_inv_single_map j f j rfl]
simp [singleObjApplyIso]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 3.9s, verify 0.1s, in=660, out=46)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j (rfl)
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.8s, verify 0.2s, in=825, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [singleObjApplyIso, singleObjApplyIsoOfEq]
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=792, out=42)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← singleObjApplyIsoOfEq j X j rfl, ← singleObjApplyIsoOfEq j Y j rfl]
simp only [singleObjApplyIsoOfEq_inv_single_map]
```

**lean_error:** tail step 1/2 ('rw [← singleObjApplyIsoOfEq j X j rfl, ← singleObjApplyIsoOfEq j Y j rfl]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 9.7s, verify 0.1s, in=814, out=604)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=849, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [singleObjApplyIso],
exact singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

**lean_error:** tail step 1/2 ('rw [singleObjApplyIso],'): <stdin>:1:22: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=839, out=45)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleObjApplyIsoOfEq j X j rfl, ← singleObjApplyIsoOfEq j Y j rfl]
simp only [singleObjApplyIsoOfEq_inv_single_map, eq_self]
```

**lean_error:** tail step 1/2 ('rw [← singleObjApplyIsoOfEq j X j rfl, ← singleObjApplyIsoOfEq j Y j rfl]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 3.9s, verify 0.1s, in=838, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map
exact f
exact j
exact rfl
```
