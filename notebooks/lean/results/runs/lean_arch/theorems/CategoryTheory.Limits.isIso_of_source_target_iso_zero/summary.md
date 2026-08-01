# CategoryTheory.Limits.isIso_of_source_target_iso_zero   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`  

**Ground-truth tail (from k):**
```lean
exact (isIsoZeroEquivIsoZero _ _).invFun ⟨i, j⟩
```

**True premises at k:** `CategoryTheory.Limits.isIsoZeroEquivIsoZero`, `Equiv.invFun`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=287, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact isIso_zero
```

**lean_error:** tail step 1/1 ('exact isIso_zero'): unknown identifier 'isIso_zero'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=258, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← IsIso.unit_comp_eq_id j.hom, Category.comp_zero]
infer_instance
```

**lean_error:** tail step 1/2 ('rw [← IsIso.unit_comp_eq_id j.hom, Category.comp_zero]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=276, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply isIso_zero_morphism
```

**lean_error:** tail step 1/1 ('apply isIso_zero_morphism'): unknown identifier 'isIso_zero_morphism'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=767, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero Y 0).invFun ⟨j, Iso.refl 0⟩
```

**lean_error:** tail step 1/1 ('exact (isIsoZeroEquivIsoZero Y 0).invFun ⟨j, Iso.refl 0⟩'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=725, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← isIsoZeroEquivIsoZero Y Y]
exact ⟨j, (CategoryTheory.Iso.refl Y)⟩
```

**lean_error:** tail step 1/2 ('rw [← isIsoZeroEquivIsoZero Y Y]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.0s, verify 0.2s, in=756, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply (isIsoZeroEquivIsoZero X Y).invFun
exact ⟨i, j⟩
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=2032, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).invFun ⟨i, j⟩
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1978, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isIsoZeroEquivIsoZero]
exact ⟨i, j⟩
```

**lean_error:** tail step 1/2 ('rw [isIsoZeroEquivIsoZero]'): failed to rewrite using equation theorems for 'CategoryTheory.Limits.isIsoZeroEquivIsoZero'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=2021, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (isIsoZeroEquivIsoZero X Y).inv_fun
exact ⟨i, j⟩
```

**lean_error:** tail step 1/2 ('apply (isIsoZeroEquivIsoZero X Y).inv_fun'): invalid field 'inv_fun', the environment does not contain 'Equiv.inv_fun'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=2057, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero Y 0).invFun ⟨j, Iso.refl 0⟩
```

**lean_error:** tail step 1/1 ('exact (isIsoZeroEquivIsoZero Y 0).invFun ⟨j, Iso.refl 0⟩'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=2159, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero _ _).invFun ⟨i, j⟩
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.2s, verify 0.2s, in=2046, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply (isIsoZeroEquivIsoZero X Y).invFun
exact ⟨i, j⟩
```
