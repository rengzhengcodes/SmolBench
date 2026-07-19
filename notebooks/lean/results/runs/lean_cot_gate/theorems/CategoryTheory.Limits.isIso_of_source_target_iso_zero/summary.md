# CategoryTheory.Limits.isIso_of_source_target_iso_zero   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`  

**Ground-truth tail (from k):**
```lean
exact (isIsoZeroEquivIsoZero _ _).invFun ⟨i, j⟩
```

**True premises at k:** `CategoryTheory.Limits.isIsoZeroEquivIsoZero`, `Equiv.invFun`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✘ ✘ ✓ ✘ | ✓ ✘ ✘ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ | ✘ ✘ ✘ ✘ | ✓ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 172.2s, verify 0.1s, in=259, out=7442)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
haveI : IsZero X := IsZero.of_iso i
have h_comp : i.hom ≫ j.inv.hom = 0 := eq_zero_of_source_is_zero
rw [h_comp]
apply IsIso.of_iso (i ≫ j.inv)
```

**lean_error:** tail step 1/4 ('haveI : IsZero X := IsZero.of_iso i'): application type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 179.4s, verify 0.1s, in=259, out=7787)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : i.hom ≫ j.inv.hom = 0 := eq_zero_of_source_iso_zero i,
rw [h],
apply IsIso.comp i.2 j.inv.2
```

**lean_error:** tail step 1/3 ('have h : i.hom ≫ j.inv.hom = 0 := eq_zero_of_source_iso_zero i,'): <stdin>:1:62: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 191.1s, verify 0.1s, in=259, out=8327)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : 0 = i.hom ≫ j.inv := (isZero_of_iso_zero i).hom_ext _ _,
rw [h],
apply IsIso.comp i.isIso j.inv.isIso,
```

**lean_error:** tail step 1/3 ('have h : 0 = i.hom ≫ j.inv := (isZero_of_iso_zero i).hom_ext _ _,'): <stdin>:1:64: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 283.1s, verify 0.1s, in=259, out=12497)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
haveI := is_zero_of_isomorphic_zero i
have h₁ : 0 = i.hom ≫ j.inv := subsingleton.elim _ _
have h₂ := is_iso.comp i.2 j.2
rwa h₁ at h₂
```

**lean_error:** tail step 1/4 ('haveI := is_zero_of_isomorphic_zero i'): internal exception #7

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=259, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): failed to synthesize instance

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=259, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): failed to synthesize instance

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=259, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): failed to synthesize instance

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=259, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply isIso_zero_of_target_isZero
```

**lean_error:** tail step 1/1 ('apply isIso_zero_of_target_isZero'): unknown identifier 'isIso_zero_of_target_isZero'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.7s, verify 0.1s, in=259, out=251)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact isIso_of_isZero_of_isZero (isZero_of_isomorphic i) (isZero_of_isomorphic j)
```

**lean_error:** tail step 1/1 ('exact isIso_of_isZero_of_isZero (isZero_of_isomorphic i) (isZero_of_isomorphic j)'): unknown identifier 'isIso_of_isZero_of_isZero'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.9s, verify 0.1s, in=259, out=374)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
convert IsIso.of_isIso_fac (i.hom ≫ j.inv) (i.hom ≫ j.inv) (i.hom ≫ j.inv)
```

**lean_error:** tail step 1/1 ('convert IsIso.of_isIso_fac (i.hom ≫ j.inv) (i.hom ≫ j.inv) (i.hom ≫ j.inv)'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.5s, verify 0.1s, in=259, out=381)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact isIso_of_isIso_fac i.1 (i.2.trans (congr_arg (fun f => f ≫ j.inv) (zero_comp _)))
```

**lean_error:** tail step 1/1 ('exact isIso_of_isIso_fac i.1 (i.2.trans (congr_arg (fun f => f ≫ j.inv) (zero_comp _)))'): unknown identifier 'isIso_of_isIso_fac'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 14.1s, verify 0.1s, in=259, out=408)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [i.hom_comp_eq_zero_iff, i.inv_comp_eq_zero_iff, j.hom_comp_eq_zero_iff, j.inv_comp_eq_zero_iff]
```

**lean_error:** tail step 1/1 ('simp only [i.hom_comp_eq_zero_iff, i.inv_comp_eq_zero_iff, j.hom_comp_eq_zero_iff, j.inv_comp_eq_zero_iff]'): invalid field 'hom_comp_eq_zero_iff', the environment does not contain 'CategoryTheory.Iso.hom_comp_eq_zero_iff'

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 13.5s, verify 0.1s, in=739, out=524)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply (isIsoZeroEquivIsoZero X Y).invFun ⟨i, j⟩
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 35.6s, verify 0.1s, in=739, out=1448)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 71.3s, verify 0.1s, in=739, out=2918)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Equiv.invFun (isIsoZeroEquivIsoZero X Y) ⟨i, j⟩
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 105.8s, verify 0.1s, in=739, out=4479)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=739, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=739, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y (IsIso.of_iso i ≫ IsIso.of_iso j.inv)
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y (IsIso.of_iso i ≫ IsIso.of_iso j.inv)'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=739, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y (isIsoZeroEquiv X Y (isIsoOfIsIsoZero _))
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y (isIsoZeroEquiv X Y (isIsoOfIsIsoZero _))'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.3s, verify 0.1s, in=739, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y (isIsoZeroEquiv X Y ⟨i, j⟩)
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y (isIsoZeroEquiv X Y ⟨i, j⟩)'): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 5.0s, verify 0.1s, in=739, out=160)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Equiv.invFun (isIsoZeroEquivIsoZero X Y) (i, j)
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.5s, verify 0.1s, in=739, out=241)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Equiv.invFun (isIsoZeroEquivIsoZero X Y) ⟨i, j⟩
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.8s, verify 0.1s, in=739, out=251)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (isIsoZeroEquivIsoZero X Y).invFun ⟨i, j⟩
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 9.0s, verify 0.1s, in=739, out=257)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 24.2s, verify 0.1s, in=2004, out=617)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Equiv.invFun (isIsoZeroEquivIsoZero X Y) ⟨i, j⟩
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 44.2s, verify 0.1s, in=2004, out=1265)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 54.2s, verify 0.1s, in=2004, out=1457)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 66.1s, verify 0.1s, in=2004, out=1728)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=2004, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=2004, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.6s, verify 0.1s, in=2004, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).invFun ⟨i, j⟩
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.9s, verify 0.1s, in=2004, out=42)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y (isIsoZeroEquiv X Y ⟨zero_of_source_iso_zero f i, zero_of_target_iso_zero f j⟩).2
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y (isIsoZeroEquiv X Y ⟨zero_of_source_iso_zero f i, zero_of_target_iso_zero f j⟩).2'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 15.1s, verify 0.1s, in=2004, out=200)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Equiv.invFun (isIsoZeroEquivIsoZero X Y) ⟨i, j⟩
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 15.2s, verify 0.1s, in=2004, out=282)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact CategoryTheory.Limits.isIsoZeroEquivIsoZero.2 ⟨i, j⟩
```

**lean_error:** tail step 1/1 ('exact CategoryTheory.Limits.isIsoZeroEquivIsoZero.2 ⟨i, j⟩'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 15.5s, verify 0.1s, in=2004, out=295)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y _root_.Equiv.invFun ⟨i, j⟩
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y _root_.Equiv.invFun ⟨i, j⟩'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 16.4s, verify 0.1s, in=2004, out=241)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Equiv.invFun (isIsoZeroEquivIsoZero X Y) ⟨i, j⟩
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 8.8s, verify 0.1s, in=2032, out=347)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 18.5s, verify 0.6s, in=2032, out=734)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 23.4s, verify 0.1s, in=2032, out=935)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Equiv.invFun (isIsoZeroEquivIsoZero X Y) ⟨i, j⟩
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 25.5s, verify 0.1s, in=2032, out=1020)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm ⟨i, j⟩
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=2032, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=2032, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y ⟨i, j⟩'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=2032, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y (isIsoZeroEquiv X Y).symm ⟨i, j⟩
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y (isIsoZeroEquiv X Y).symm ⟨i, j⟩'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=2032, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isIsoZeroEquivIsoZero X Y (IsIso.of_iso i ≫ IsIso.of_iso j)
```

**lean_error:** tail step 1/1 ('exact isIsoZeroEquivIsoZero X Y (IsIso.of_iso i ≫ IsIso.of_iso j)'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 5.1s, verify 0.1s, in=2032, out=162)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).invFun (i, j)
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.4s, verify 0.1s, in=2032, out=242)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Equiv.invFun _ ⟨i, j⟩
```

**lean_error:** tail step 1/1 ('exact Equiv.invFun _ ⟨i, j⟩'): internal exception #7

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.6s, verify 0.1s, in=2032, out=244)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (isIsoZeroEquivIsoZero X Y).symm (i, j)
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.1s, verify 0.1s, in=2032, out=262)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Equiv.invFun (isIsoZeroEquivIsoZero X Y) (i.prod j)
```

**lean_error:** tail step 1/1 ('exact Equiv.invFun (isIsoZeroEquivIsoZero X Y) (i.prod j)'): application type mismatch
