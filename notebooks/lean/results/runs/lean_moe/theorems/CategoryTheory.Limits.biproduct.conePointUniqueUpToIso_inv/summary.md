# CategoryTheory.Limits.biproduct.conePointUniqueUpToIso_inv   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
rw [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app,
  biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π, b.toCone_π_app, b.ι_π]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp`, `CategoryTheory.Limits.Bicone.toCone_π_app`, `CategoryTheory.Limits.biproduct.bicone_π`, `CategoryTheory.Limits.biproduct.ι_desc`, `CategoryTheory.Limits.biproduct.ι_π`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | · | ✘ | · |
| `hint:3` | · | ✘ | · |
| `noise:3` | · | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 20.7s, verify 0.1s, in=469, out=3829)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Bicone.desc, Category.assoc]
```

**lean_error:** tail step 1/1 ('simp [Bicone.desc, Category.assoc]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 287.6s, verify 0.2s, in=432, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv = desc b.ι := by sorry
-- then use this to rewrite the goal
```

**lean_error:** tail step 2/2 ('-- then use this to rewrite the goal'): <stdin>:1:36: unexpected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.2s, in=424, out=649)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
<;> simp [IsLimit.conePointUniqueUpToIso]
<;> aesop
```

**lean_error:** tail step 2/3 ('<;> simp [IsLimit.conePointUniqueUpToIso]'): <stdin>:1:0: expected tactic

### `hint:2` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 24.9s, verify 0.2s, in=1756, out=4848)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Category.assoc]
```

**final state (truncated):**
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
...
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 287.5s, verify 0.1s, in=1785, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hPQ : (inv ≫ (Bicone.toCone b).π.app j') = (desc b.ι ≫ (Bicone.toCone b).π.app j') := by
  have h₁ : ∀ (i : J), (biproduct.ι f i) ≫ (inv ≫ (Bicone.toCone b).π.app j') = (biproduct.ι f i) ≫ (desc b.ι ≫ (Bicone.toCone b).π.app j') := by
    sorry
  have h₂ : (inv ≫ (Bicone.toCone b).π.app j') = (desc b.ι ≫ (Bicone.toCone b).π.app j') := by
    apply (biproduct.isColimit f).epic
    intro i
    exact h₁ i
  exact h₂
rw [← Category.comp_assoc]
rw [hPQ]
rw [Category.comp_assoc]
```

**lean_error:** tail step 1/11 ("have hPQ : (inv ≫ (Bicone.toCone b).π.app j') = (desc b.ι ≫ (Bicone.toCone b).π.app j') := by"): <stdin>:1:93: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 12.8s, verify 0.1s, in=1730, out=1215)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp, CategoryTheory.Limits.Bicone.toCone_π_app, CategoryTheory.Limits.biproduct.ι_desc, CategoryTheory.Category.assoc]
```

**final state (truncated):**
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 28.4s, verify 1.3s, in=3563, out=5790)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Category.assoc]
```

**final state (truncated):**
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
...
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 266.1s, verify 0.1s, in=3642, out=30355)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h1 : (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv ≫ (Bicone.toCone b).π.app j' = (isLimit f).π.app j' := by sorry
have h2 : (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j' = (ι f j ≫ b.π j'.as) := by sorry
have h3 : (isLimit f).π.app j' = b.π j'.as := by sorry
have h4 : (ι f j ≫ (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv) ≫ (Bicone.toCone b).π.app j' = ι f j ≫ (isLimit f).π.app j' := by
  rw [← CategoryTheory.Category.comp_assoc]
have h5 : (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j' = (ι f j ≫ b.π j'.as) := h2
have h6 : (isLimit f).π.app j' = b.π j'.as := h3
have h7 : (ι f j ≫ (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv) ≫ (Bicone.toCone b).π.app j' = ι f j ≫ b.π j'.as := by
  rw [h4]
  rw [h6]
have h8 : (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j' = ι f j ≫ b.π j'.as := by
  exact h5
have h9 : (ι f j ≫ (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv) ≫ (Bicone.toCone b).π.app j' = (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j' := by
  rw [h7]
  rw [h8]
exact h9
```

**lean_error:** tail step 1/16 ("have h1 : (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv ≫ (Bicone.toCone b).π.app j' = (isLimit f).π.app j' := by sorry"): invalid field 'π', the environment does not contain 'CategoryTheory.Limits.IsLimit.π'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 12.7s, verify 0.1s, in=3581, out=1206)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, biproduct.ι_desc]
```

**final state (truncated):**
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
...
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 25.1s, verify 0.2s, in=3392, out=4866)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Category.assoc]
```

**final state (truncated):**
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
...
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 287.6s, verify 0.1s, in=3920, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
biproduct.iota f i ≫ biproduct.pi f j = if i = j then id else 0
```

**lean_error:** tail step 1/1 ('biproduct.iota f i ≫ biproduct.pi f j = if i = j then id else 0'): <stdin>:1:1: unknown tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.5s, verify 0.1s, in=3549, out=1101)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp,
  CategoryTheory.Limits.Bicone.toCone_π_app, CategoryTheory.Limits.biproduct.ι_desc]
```

**lean_error:** tail step 1/2 ('simp only [CategoryTheory.Category.assoc, CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp,'): <stdin>:1:104: unexpected end of input; expected ']'
