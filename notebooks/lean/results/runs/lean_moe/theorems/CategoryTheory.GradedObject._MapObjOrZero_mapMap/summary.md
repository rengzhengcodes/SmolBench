# CategoryTheory.GradedObject.ιMapObjOrZero_mapMap   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/GradedObject.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

**True premises at k:** `CategoryTheory.GradedObject.ιMapObjOrZero_eq_zero`, `CategoryTheory.Limits.zero_comp`, `CategoryTheory.Limits.comp_zero`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | · | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.1s, verify 0.1s, in=489, out=615)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ιMapObjOrZero, h]
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 57.3s, verify 0.1s, in=435, out=6452)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : ιMapObjOrZero X p i j = 0 := by
  split_ifs <;> simp_all [h]
  <;> aesop
have h₂ : ιMapObjOrZero Y p i j = 0 := by
  split_ifs <;> simp_all [h]
  <;> aesop
have h₃ : ιMapObjOrZero X p i j ≫ mapMap φ p j = 0 := by
  rw [h₁]
  exact zero_comp _
have h₄ : φ i ≫ ιMapObjOrZero Y p i j = 0 := by
  rw [h₂]
  exact comp_zero _
rw [h₃]
rw [h₄]
```

**lean_error:** tail step 1/14 ('have h₁ : ιMapObjOrZero X p i j = 0 := by'): <stdin>:1:41: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.1s, in=427, out=461)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_all [ιMapObjOrZero, CategoryStruct.comp_zero, CategoryStruct.zero_comp]
```

**lean_error:** tail step 1/1 ('simp_all [ιMapObjOrZero, CategoryStruct.comp_zero, CategoryStruct.zero_comp]'): unknown constant 'CategoryTheory.CategoryStruct.comp_zero'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.7s, verify 0.1s, in=1119, out=2132)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero (X:=X) (p:=p) (i:=i) (j:=j) h,
      ιMapObjOrZero_eq_zero (X:=Y) (p:=p) (i:=i) (j:=j) h]
```

**lean_error:** tail step 1/2 ('simp [ιMapObjOrZero_eq_zero (X:=X) (p:=p) (i:=i) (j:=j) h,'): <stdin>:1:58: unexpected end of input; expected ']'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 288.4s, verify 0.4s, in=1083, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
by_cases h : p i = j
  · simp only [ιMapObjOrZero_eq _ _ _ _ h, ι_mapMap]
    <;>
    simp_all [CategoryTheory.Limits.zero_comp, CategoryTheory.Limits.comp_zero]
    <;>
    aesop
  · simp only [ιMapObjOrZero_eq _ _ _ _ h, ι_mapMap]
    <;>
    simp_all [CategoryTheory.Limits.zero_comp, CategoryTheory.Limits.comp_zero]
    <;>
    aesop
```

**lean_error:** tail step 3/11 ('<;>'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.1s, in=1069, out=454)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.4s, verify 1.2s, in=1534, out=2852)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero (X:=X) (p:=p) (i:=i) (j:=j) h,
      ιMapObjOrZero_eq_zero (X:=Y) (p:=p) (i:=i) (j:=j) h]
```

**lean_error:** tail step 1/2 ('simp [ιMapObjOrZero_eq_zero (X:=X) (p:=p) (i:=i) (j:=j) h,'): <stdin>:1:58: unexpected end of input; expected ']'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 131.9s, verify 0.3s, in=1503, out=14914)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
by_cases h₁ : p i = j
  · -- Case: p i = j
    rfl
  · -- Case: p i ≠ j
    have h₂ : ιMapObjOrZero X p i j = 0 := by
      apply ιMapObjOrZero_eq_zero
      exact h₁
    have h₃ : ιMapObjOrZero Y p i j = 0 := by
      apply ιMapObjOrZero_eq_zero
      exact h₁
    have h₄ : ιMapObjOrZero X p i j ≫ mapMap φ p j = φ i ≫ ιMapObjOrZero Y p i j := by
      rw [h₂, h₃]
      -- Now we need to show that 0 ≫ mapMap φ p j = φ i ≫ 0
      -- Using the properties of zero morphisms
      have h₅ : (0 : X (p i) ⟶ Y (p i)) ≫ mapMap φ p j = 0 := by
        apply zero_comp
      have h₆ : (φ i : X i ⟶ Y i) ≫ (0 : Y (p i) ⟶ Y (p i)) = 0 := by
        apply comp_zero
      -- However, the types in the goal might not exactly match those in h₅ and h₆.
      -- Instead, we use the simp tactic to simplify the expressions using the zero morphism properties.
      simp [zero_comp, comp_zero]
      <;>
      (try rfl) <;>
      (try aesop)
    exact h₄
```

**lean_error:** tail step 2/25 ('· -- Case: p i = j'): <stdin>:1:18: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 32.2s, verify 0.1s, in=1483, out=3458)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 10.5s, verify 0.2s, in=1506, out=2104)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
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

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 288.8s, verify 0.1s, in=1582, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : X.map p h ≫ φ j = φ i ≫ Y.map p h := by
  -- use the fact that φ is a morphism of graded objects to get the naturality condition
  have h₂ : φ j ≫ X.map p h = Y.map p h ≫ φ i := by
    -- this is the commute property from the morphism φ
    exact φ.commute h
  -- now we need to get from h₂ to h₁
  -- but we can't unless we have additional properties
  -- however, if we assume that the category is such that we can compose in the other direction, we can use the following:
  have h₃ : X.map p h ≫ φ j = φ i ≫ Y.map p h := by
    -- use the fact that the category is braided or something
    sorry
  exact h₃
```

**lean_error:** tail step 1/12 ('have h₁ : X.map p h ≫ φ j = φ i ≫ Y.map p h := by'): <stdin>:1:49: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 58.0s, verify 0.1s, in=1498, out=6343)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch
