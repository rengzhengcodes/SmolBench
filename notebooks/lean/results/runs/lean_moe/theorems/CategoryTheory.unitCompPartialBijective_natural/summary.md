# CategoryTheory.unitCompPartialBijective_natural   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Adjunction/Reflective.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural A h, Equiv.symm_apply_apply]
```

**True premises at k:** `Equiv.eq_symm_apply`, `CategoryTheory.unitCompPartialBijective_symm_natural`, `Equiv.symm_apply_apply`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 1.6s, verify 0.2s, in=430, out=305)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [unitCompPartialBijective]
```

**final state (truncated):**
```
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
inst✝¹ : Category.{v₃, u₃} E
...
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 235.8s, verify 0.1s, in=374, out=29503)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have hA : unitCompPartialBijective A hB f = f := by
  have hunitB_iso : ((unit : B ⟶ i (L B))).isIso := by
    apply Reflective.unit_iso_iff_mem_essentialImage.mp
    exact hB
  have h_unit_eta : ((unit : B ⟶ i (L B))) ∘ (unitCompPartialBijective A hB f) = i.map ((L).map f) ∘ ((unit : A ⟶ i (L A))) := by
    apply unitCompPartialBijective_eta
  have h3 : ((unit : B ⟶ i (L B))) ∘ (unitCompPartialBijective A hB f) = ((unit : B ⟶ i (L B))) ∘ f := by
    calc
      ((unit : B ⟶ i (L B))) ∘ (unitCompPartialBijective A hB f) = i.map ((L).map f) ∘ ((unit : A ⟶ i (L A))) := h_unit_eta
      _ = ((unit : B ⟶ i (L B))) ∘ f := by
        rw [unit.naturality f]
        <;> simp [Function.comp_assoc]
  have hA : unitCompPartialBijective A hB f = f := by
    apply hunitB_iso.left_cancel
    exact h3
  exact hA

have hB' : unitCompPartialBijective A hB' (f ≫ h) = f ≫ h := by
  have hunitB'_iso : ((unit : B' ⟶ i (L B'))).isIso := by
    apply Reflective.unit_iso_iff_mem_essentialImage.mp
    exact hB'
  have h_unit_eta' : ((unit : B' ⟶ i (L B'))) ∘ (unitCompPartialBijective A hB' (f ≫ h)) = i.map ((L).map (f ≫ h)) ∘ ((unit : A ⟶ i (L A))) := by
    apply unitCompPartialBijective_eta
  have h3' : ((unit : B' ⟶ i (L B'))) ∘ (unitCompPartialBijective A hB' (f ≫ h)) = ((unit : B' ⟶ i (L B'))) ∘ (f ≫ h) := by
    calc
      ((unit : B' ⟶ i (L B'))) ∘ (unitCompPartialBijective A hB' (f ≫ h)) = i.map ((L).map (f ≫ h)) ∘ ((unit : A ⟶ i (L A))) := h_unit_eta'
      _ = ((unit : B' ⟶ i (L B'))) ∘ (f ≫ h) := by
        rw [unit.naturality (f ≫ h)]
        <;> simp [Function.comp_assoc]
  have hB' : unitCompPartialBijective A hB' (f ≫ h) = f ≫ h := by
    apply hunitB'_iso.left_cancel
    exact h3'
  exact hB'

calc
  (unitCompPartialBijective A hB') (f ≫ h) = f ≫ h := hB'
  _ = (unitCompPartialBijective A hB) f ≫ h := by rw [hA]
```

**lean_error:** tail step 1/35 ('have hA : unitCompPartialBijective A hB f = f := by'): <stdin>:1:51: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.4s, verify 0.2s, in=367, out=554)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [unitCompPartialBijective]
```

**final state (truncated):**
```
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
inst✝¹ : Category.{v₃, u₃} E
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.9s, verify 1.0s, in=1107, out=1396)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply (Equiv.eq_symm_apply (unitCompPartialBijective A hB')).mpr
  simpa [Equiv.symm_apply_apply] using
    (unitCompPartialBijective_symm_natural (i:=i) A h hB hB' ((unitCompPartialBijective A hB) f))
```

**lean_error:** tail step 1/3 ("apply (Equiv.eq_symm_apply (unitCompPartialBijective A hB')).mpr"): tactic 'apply' failed, failed to unify

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 260.2s, verify 0.1s, in=1074, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
f ≫ h = e ((unitCompPartialBijective A hB).symm f ≫ h)   (1)
```

**lean_error:** tail step 1/1 ('f ≫ h = e ((unitCompPartialBijective A hB).symm f ≫ h)   (1)'): <stdin>:1:1: unknown tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=1038, out=502)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Equiv.eq_symm_apply.mpr
apply unitCompPartialBijective_symm_natural
```

**lean_error:** tail step 1/2 ('apply Equiv.eq_symm_apply.mpr'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.3s, verify 0.2s, in=1933, out=2024)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (Equiv.eq_symm_apply (unitCompPartialBijective A hB')).mpr
simp [unitCompPartialBijective_symm_natural]
```

**lean_error:** tail step 1/2 ("apply (Equiv.eq_symm_apply (unitCompPartialBijective A hB')).mpr"): tactic 'apply' failed, failed to unify

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 89.2s, verify 0.1s, in=1898, out=9952)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem unitCompPartialBijective_natural [Reflective i] (A : C) {B B' : C} (h : B ⟶ B')
    (hB : B ∈ i.essImage) (hB' : B' ∈ i.essImage) (f : A ⟶ B) :
    (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h := by
  have h_main : (f ≫ h) = (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) := by
    have h₂ : (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) = f ≫ h := by
      have h₃ : (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) = (unitCompPartialBijective A hB).symm ((unitCompPartialBijective A hB) f) ≫ h := by sorry
      have h₄ : (unitCompPartialBijective A hB).symm ((unitCompPartialBijective A hB) f) = f := by sorry
      calc
        (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) = (unitCompPartialBijective A hB).symm ((unitCompPartialBijective A hB) f) ≫ h := h₃
        _ = f ≫ h := by rw [h₄]
    rw [h₂]
    <;> rfl
  
  have h_final : (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h := by
    have h₁ : (f ≫ h) = (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) := h_main
    have h₂ : (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h := by
      apply (Equiv.eq_symm_apply (unitCompPartialBijective A hB') (f ≫ h) ((unitCompPartialBijective A hB) f ≫ h)).mp
      exact h₁
    exact h₂
  
  exact h_final
```

**lean_error:** tail step 1/19 ("theorem unitCompPartialBijective_natural [Reflective i] (A : C) {B B' : C} (h : B ⟶ B')"): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 25.6s, verify 0.3s, in=1866, out=2645)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Equiv.eq_symm_apply (unitCompPartialBijective A hB')]
apply unitCompPartialBijective_symm_natural
```

**lean_error:** tail step 2/2 ('apply unitCompPartialBijective_symm_natural'): tactic 'apply' failed, failed to unify

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.6s, verify 0.2s, in=1861, out=1887)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply (unitCompPartialBijective A hB').injective
simp [Equiv.symm_apply_apply, unitCompPartialBijective_symm_natural]
```

**lean_error:** tail step 1/2 ("apply (unitCompPartialBijective A hB').injective"): tactic 'apply' failed, failed to unify

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 228.3s, verify 0.1s, in=2053, out=28377)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h1 : (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) = f ≫ h := by
  have h2 : (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) = (unitCompPartialBijective A hB).symm ((unitCompPartialBijective A hB) f) ≫ h := by
    apply unitCompPartialBijective_symm_natural
  rw [h2]
  have h3 : (unitCompPartialBijective A hB).symm ((unitCompPartialBijective A hB) f) = f := by
    apply Equiv.symm_apply_apply
  rw [h3]
  <;> simp [Function.comp_apply]
  
have h4 : (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB') (f ≫ h)) = f ≫ h := by
  apply Equiv.symm_apply_apply
  
have h5 : (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB') (f ≫ h)) = (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) := by
  calc
    (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB') (f ≫ h)) = f ≫ h := by rw [h4]
    _ = (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) := by
      rw [h1]
      <;> simp [Function.comp_apply]
  
have h6 : (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h := by
  apply (unitCompPartialBijective A hB').symm.injective
  exact h5
  
exact h6
```

**lean_error:** tail step 1/20 ("have h1 : (unitCompPartialBijective A hB').symm ((unitCompPartialBijective A hB) f ≫ h) = f ≫ h := by"): <stdin>:1:101: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 19.1s, verify 0.3s, in=1874, out=1914)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Equiv.eq_symm_apply (unitCompPartialBijective A hB')]
apply unitCompPartialBijective_symm_natural
```

**lean_error:** tail step 2/2 ('apply unitCompPartialBijective_symm_natural'): tactic 'apply' failed, failed to unify
