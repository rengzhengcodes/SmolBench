# CategoryTheory.GradedObject.singleObjApplyIso_inv_single_map   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/GradedObject/Single.lean`  

**Ground-truth tail (from k):**
```lean
apply singleObjApplyIsoOfEq_inv_single_map
```

**True premises at k:** `CategoryTheory.GradedObject.singleObjApplyIsoOfEq_inv_single_map`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=360, out=1283)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 73.9s, verify 0.1s, in=310, out=9413)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
dsimp [singleObjApplyIso, single_map_apply]
<;>
simp [id_right, id_left]
<;>
rfl
<;>
try aesop
```

**lean_error:** tail step 1/7 ('dsimp [singleObjApplyIso, single_map_apply]'): unknown identifier 'single_map_apply'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=304, out=526)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [category_theory.iso.inv_hom_id, category_theory.iso.hom_inv_id, category_theory.category.assoc]
```

**lean_error:** tail step 1/1 ('simp [category_theory.iso.inv_hom_id, category_theory.iso.hom_inv_id, category_theory.category.assoc]'): unknown identifier 'category_theory.iso.inv_hom_id'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.8s, verify 0.1s, in=708, out=810)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (singleObjApplyIsoOfEq_inv_single_map (j:=j) (f:=f) (i:=j) (h:=rfl))
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 19.0s, verify 0.1s, in=679, out=2192)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  (singleObjApplyIso j X).inv ≫ (single j).map f j = (singleObjApplyIsoOfEq j X j (rfl : j = j)).inv ≫ (single j).map f j := by simp [singleObjApplyIso]
  _ = f ≫ (singleObjApplyIsoOfEq j Y j (rfl : j = j)).inv := by apply singleObjApplyIsoOfEq_inv_single_map
  _ = f ≫ (singleObjApplyIso j Y).inv := by simp [singleObjApplyIso]
```

**lean_error:** tail step 1/4 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.4s, verify 0.1s, in=664, out=525)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=866, out=598)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [singleObjApplyIso] using
  (singleObjApplyIsoOfEq_inv_single_map (j:=j) (X:=X) (Y:=Y) (f:=f) (i:=j) (h:=rfl))
```

**lean_error:** tail step 1/2 ('simpa [singleObjApplyIso] using'): <stdin>:1:31: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 30.5s, verify 0.2s, in=842, out=3790)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
dsimp [singleObjApplyIso]
apply singleObjApplyIsoOfEq_inv_single_map j X Y f j (by rfl)
```

**lean_error:** tail step 2/2 ('apply singleObjApplyIsoOfEq_inv_single_map j X Y f j (by rfl)'): application type mismatch

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.5s, verify 0.1s, in=828, out=530)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.5s, verify 0.1s, in=875, out=746)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [singleObjApplyIso] using
  (singleObjApplyIsoOfEq_inv_single_map (j:=j) (f:=f) (i:=j) (h:=rfl))
```

**lean_error:** tail step 1/2 ('simpa [singleObjApplyIso] using'): <stdin>:1:31: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 40.0s, verify 0.3s, in=892, out=4989)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : singleObjApplyIso j X = singleObjApplyIsoOfEq j X j (by rfl) := rfl
have h₂ : singleObjApplyIso j Y = singleObjApplyIsoOfEq j Y j (by rfl) := rfl
calc
  (singleObjApplyIso j X).inv ≫ (single j).map f j = (singleObjApplyIsoOfEq j X j (by rfl)).inv ≫ (single j).map f j := by rw [h₁]
  _ = f ≫ (singleObjApplyIsoOfEq j Y j (by rfl)).inv := by apply singleObjApplyIsoOfEq_inv_single_map
  _ = f ≫ (singleObjApplyIso j Y).inv := by rw [h₂.symm]
```

**lean_error:** tail step 3/6 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.1s, verify 0.1s, in=846, out=496)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply singleObjApplyIsoOfEq_inv_single_map j f j rfl
```
