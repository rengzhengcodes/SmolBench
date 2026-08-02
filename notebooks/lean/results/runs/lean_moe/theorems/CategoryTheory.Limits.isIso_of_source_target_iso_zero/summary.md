# CategoryTheory.Limits.isIso_of_source_target_iso_zero   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`  

**Ground-truth tail (from k):**
```lean
exact (isIsoZeroEquivIsoZero _ _).invFun ⟨i, j⟩
```

**True premises at k:** `CategoryTheory.Limits.isIsoZeroEquivIsoZero`, `Equiv.invFun`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.6s, verify 0.1s, in=325, out=2384)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (inferInstance : IsIso (i.hom ≫ j.inv))
```

**lean_error:** tail step 1/1 ('simpa using (inferInstance : IsIso (i.hom ≫ j.inv))'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 65.9s, verify 0.2s, in=275, out=7680)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h_zero_factor : (0 : X ⟶ Y) = (0 : X ⟶ 0) ∘ (0 : 0 ⟶ Y) := by rw [zero_eq_zero]
have h1 : (0 : X ⟶ 0) = i.hom := by
  apply HomExt
  exact inst✝.terminal homExt
have h2 : (0 : 0 ⟶ Y) = j.inv := by
  apply HomExt
  exact inst✝.initial homExt
have h_zero_eq : (0 : X ⟶ Y) = i.hom ∘ j.inv := by
  calc
    (0 : X ⟶ Y) = (0 : X ⟶ 0) ∘ (0 : 0 ⟶ Y) := h_zero_factor
    _ = i.hom ∘ (0 : 0 ⟶ Y) := by rw [h1]
    _ = i.hom ∘ j.inv := by rw [h2]
set k : Y ⟶ X := j.hom ∘ i.inv with hk
have h3 : k ∘ (0 : X ⟶ Y) = id_Y := by
  calc
    k ∘ (0 : X ⟶ Y) = (j.hom ∘ i.inv) ∘ (0 : X ⟶ Y) := by rw [hk]
    _ = (j.hom ∘ i.inv) ∘ (i.hom ∘ j.inv) := by rw [h_zero_eq]
    _ = j.hom ∘ (i.inv ∘ i.hom) ∘ j.inv := by
      simp [Function.comp_assoc]
      <;> try simp_all [Category.ext_iff]
      <;> try aesop
    _ = j.hom ∘ id_X ∘ j.inv := by rw [i.inv_comp_hom]
    _ = j.hom ∘ j.inv := by
      simp [id_comp, comp_id]
      <;> try simp_all [Category.ext_iff]
      <;> try aesop
    _ = id_Y := by rw [j.hom_comp_inv]
have h4 : (0 : X ⟶ Y) ∘ k = id_X := by
  calc
    (0 : X ⟶ Y) ∘ k = (0 : X ⟶ Y) ∘ (j.hom ∘ i.inv) := by rw [hk]
    _ = (i.hom ∘ j.inv) ∘ (j.hom ∘ i.inv) := by rw [h_zero_eq]
    _ = i.hom ∘ (j.inv ∘ j.hom) ∘ i.inv := by
      simp [Function.comp_assoc]
      <;> try simp_all [Category.ext_iff]
      <;> try aesop
    _ = i.hom ∘ id_0 ∘ i.inv := by rw [j.inv_comp_hom]
    _ = i.hom ∘ i.inv := by
      simp [id_comp, comp_id]
      <;> try simp_all [Category.ext_iff]
      <;> try aesop
    _ = id_X := by rw [i.hom_comp_inv]
exact ⟨k, h3, h4⟩
```

**lean_error:** tail step 1/42 ('have h_zero_factor : (0 : X ⟶ Y) = (0 : X ⟶ 0) ∘ (0 : 0 ⟶ Y) := by rw [zero_eq_zero]'): application type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.1s, in=271, out=572)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact isIso_zero
```

**lean_error:** tail step 1/1 ('exact isIso_zero'): unknown identifier 'isIso_zero'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.8s, verify 0.1s, in=815, out=523)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ((isIsoZeroEquivIsoZero X Y).symm (i, j))
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 35.0s, verify 0.1s, in=789, out=3994)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm (i, j)
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.8s, verify 0.1s, in=765, out=470)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=2143, out=691)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ((CategoryTheory.Limits.isIsoZeroEquivIsoZero X Y).mpr ⟨i, j⟩)
```

**lean_error:** tail step 1/1 ('exact ((CategoryTheory.Limits.isIsoZeroEquivIsoZero X Y).mpr ⟨i, j⟩)'): invalid field 'mpr', the environment does not contain 'Equiv.mpr'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 48.9s, verify 0.1s, in=2146, out=5639)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [zero_of_source_iso_zero f i]
exact (isIsoZeroEquivIsoZero X Y).invFun ⟨i, j⟩
```

**lean_error:** tail step 1/2 ('rw [zero_of_source_iso_zero f i]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.7s, verify 0.1s, in=2076, out=707)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.4s, verify 1.1s, in=1989, out=677)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).invFun ⟨i, j⟩
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 47.9s, verify 0.1s, in=2319, out=5511)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.1s, in=2071, out=470)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply (isIsoZeroEquivIsoZero X Y).symm
exact ⟨i, j⟩
```

**lean_error:** tail step 1/2 ('apply (isIsoZeroEquivIsoZero X Y).symm'): tactic 'apply' failed, failed to unify
