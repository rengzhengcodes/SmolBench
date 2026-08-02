# CategoryTheory.Limits.inl_inl_pushoutLeftPushoutInrIso_hom   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Category.assoc, ← Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Iso.eq_comp_inv`, `CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.8s, verify 0.1s, in=405, out=3999)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Category.assoc]
```

**lean_error:** tail step 1/1 ('simp [Category.assoc]'): simp made no progress

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 273.9s, verify 0.1s, in=353, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem pushoutLeftPushoutInrIso {f : X ⟶ Y} {g : X ⟶ Z} {g' : Z ⟶ W} :
    Pushout f (g ≫ g') ≅ Pushout (Pushout.inr f g) g' :=
  ...
```

**lean_error:** tail step 1/3 ("theorem pushoutLeftPushoutInrIso {f : X ⟶ Y} {g : X ⟶ Z} {g' : Z ⟶ W} :"): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 12.4s, verify 0.2s, in=349, out=1187)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pushoutLeftPushoutInrIso]
```

**final state (truncated):**
```
C : Type u
inst✝⁴ : Category.{v, u} C
D : Type u₂
inst✝³ : Category.{v₂, u₂} D
W X Y Z : C
f : X ⟶ Y
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.3s, verify 0.2s, in=971, out=1879)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply ((Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')).mpr ?_)
simpa using (inl_pushoutLeftPushoutInrIso_inv (f:=f) (g:=g) (g':=g')).symm
```

**lean_error:** tail step 1/2 ("apply ((Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')).mpr ?_)"): tactic 'apply' failed, failed to unify

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 53.6s, verify 0.1s, in=948, out=6142)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : pushout.inl ≫ pushout.inl = pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv := by
  rw [inl_pushoutLeftPushoutInrIso_inv.symm]
have h₂ : (pushout.inl ≫ pushout.inl) ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl := by
  apply (CategoryTheory.Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')).mp
  exact h₁
exact h₂
```

**lean_error:** tail step 1/6 ("have h₁ : pushout.inl ≫ pushout.inl = pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv := by"): <stdin>:1:95: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 18.0s, verify 0.2s, in=915, out=1721)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← CategoryTheory.Iso.eq_comp_inv]
exact CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv
```

**lean_error:** tail step 1/2 ('rw [← CategoryTheory.Iso.eq_comp_inv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.8s, verify 0.2s, in=2067, out=2229)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')).mpr
  simpa using (inl_pushoutLeftPushoutInrIso_inv (f:=f) (g:=g) (g':=g')).symm
```

**lean_error:** tail step 1/2 ("apply (Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')).mpr"): tactic 'apply' failed, failed to unify

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 52.0s, verify 0.1s, in=2082, out=5954)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem CategoryTheory.Limits.inl_inl_pushoutLeftPushoutInrIso_hom {C : Type u} [Category.{v, u} C] {D : Type u₂} [Category.{v₂, u₂} D] {W X Y Z : C} {f : X ⟶ Y} {g : X ⟶ Z} {g' : Z ⟶ W} (inst✝² : HasPushout f g) (inst✝¹ : HasPushout pushout.inr g') (inst✝ : HasPushout f (g ≫ g')) :
    pushout.inl ≫ pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl := by
  have h₁ : pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv = pushout.inl ≫ pushout.inl := inl_pushoutLeftPushoutInrIso_inv
  have h₂ : pushout.inl ≫ pushout.inl = pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv := by
    rw [h₁.symm]
  have h₃ : pushout.inl ≫ pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl := by
    have h₄ : pushout.inl ≫ pushout.inl = pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv := h₂
    have h₅ : pushout.inl ≫ pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl := by
      apply (CategoryTheory.Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')).mp
      exact h₄
    exact h₅
  exact h₃
```

**lean_error:** tail step 1/12 ("theorem CategoryTheory.Limits.inl_inl_pushoutLeftPushoutInrIso_hom {C : Type u} [Category.{v, u} C] {D : Type u₂} [Category.{v₂, u₂} D] {W X Y Z : C} {f : X ⟶ Y} {g : X ⟶ Z} {g' : Z ⟶ W} (inst✝² : HasPushout f g) (inst✝¹ : HasPushout pushout.inr g') (inst✝ : HasPushout f (g ≫ g')) :

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 48.9s, verify 0.2s, in=1990, out=4993)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('rw [← eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.0s, verify 0.1s, in=1936, out=1566)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : pushout.inl ≫ pushout.inl = pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv := by
    simpa using (inl_pushoutLeftPushoutInrIso_inv (f:=f) (g:=g) (g':=g')).symm
  have h₂ : (pushout.inl ≫ pushout.inl) ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl :=
    (Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')).mp h₁
  simpa [Category.assoc] using h₂
```

**lean_error:** tail step 1/5 ("have h₁ : pushout.inl ≫ pushout.inl = pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv := by"): <stdin>:1:95: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 35.7s, verify 0.2s, in=2209, out=4074)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv = pushout.inl ≫ pushout.inl := inl_pushoutLeftPushoutInrIso_inv
have h₂ : pushout.inl ≫ pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl := by
  calc
    pushout.inl ≫ pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').hom = (pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv) ≫ (pushoutLeftPushoutInrIso f g g').hom := by rw [h₁]
    _ = pushout.inl ≫ ((pushoutLeftPushoutInrIso f g g').inv ≫ (pushoutLeftPushoutInrIso f g g').hom) := by
      rw [CategoryTheory.assoc]
    _ = pushout.inl ≫ 1 := by
      have h₃ : (pushoutLeftPushoutInrIso f g g').inv ≫ (pushoutLeftPushoutInrIso f g g').hom = 1 := by
        exact CategoryTheory.inv_comp (pushoutLeftPushoutInrIso f g g')
      rw [h₃]
    _ = pushout.inl := by simp [CategoryTheory.right_id]
exact h₂
```

**lean_error:** tail step 1/12 ("have h₁ : pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv = pushout.inl ≫ pushout.inl := inl_pushoutLeftPushoutInrIso_inv"): type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 16.4s, verify 0.2s, in=1988, out=1601)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')]
exact inl_pushoutLeftPushoutInrIso_inv
```

**lean_error:** tail step 1/2 ("rw [← Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
