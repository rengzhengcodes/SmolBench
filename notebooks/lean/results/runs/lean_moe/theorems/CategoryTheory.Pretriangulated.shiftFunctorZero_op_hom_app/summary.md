# CategoryTheory.Pretriangulated.shiftFunctorZero_op_hom_app   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Triangulated/Opposite.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.2s, in=506, out=790)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa
```

**lean_error:** tail step 1/1 ('simpa'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 199.3s, verify 0.1s, in=482, out=26400)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h1 : ((shiftFunctorZero C ℤ).inv.app X.unop).op = id X := by
  have h1₁ : (shiftFunctorZero C ℤ).inv.app X.unop = shiftZero (X.unop) := rfl
  rw [h1₁]
  have h1₂ : (X.unop) • 0 = X.unop := unital
  have h1₃ : shiftZero (X.unop) : X.unop → (X.unop) • 0 := rfl
  have h1₄ : shiftZero (X.unop) = id (X.unop) := by
    have h1₅ : shiftZero (X.unop) ; shiftZero ((X.unop) • 0) = shiftZero ((X.unop) + 0 + 0) := by
      rw [show shiftZero (X.unop) ; shiftZero ((X.unop) • 0) = shiftAddHom (shiftFunctor C ℤ) (X.unop) 0 0 by rfl]
      <;> simp [add_zero, zero_add]
      <;> rfl
    have h1₆ : shiftZero ((X.unop) • 0) = shiftZero (X.unop) := by
      rw [h1₂]
    rw [h1₅] at *
    have h1₇ : shiftZero (X.unop) ; shiftZero (X.unop) = shiftZero (X.unop) := by linarith
    have h1₈ : shiftZero (X.unop) ≅ (X.unop) → (X.unop) • 0 := shiftFunctorZero C ℤ.inv_isIso
    have h1₉ : shiftZero (X.unop) : X.unop → X.unop := by
      apply Eq.symm • Eq.symm
      exact Eq.symm_of_eq h1₂
    have h₁₀ : (shiftZero (X.unop) : X.unop → X.unop) ; (shiftZero (X.unop) : X.unop → X.unop) = (shiftZero (X.unop) : X.unop → X.unop) := by
      calc
        (shiftZero (X.unop) : X.unop → X.unop) = (shiftZero (X.unop) : X.unop → (X.unop) • 0) := by
          apply Eq.symm • Eq.symm
          exact Eq.symm_of_eq h1₂
        _ ; (shiftZero (X.unop) : X.unop → X.unop) = ((shiftZero (X.unop) : X.unop → (X.unop) • 0) ; (shiftZero ((X.unop) • 0) : (X.unop) • 0 → (X.unop) • 0)) := by
          simp [h1₆]
          <;>
          aesop
        _ = (shiftZero (X.unop) : X.unop → (X.unop) • 0) := by
          rw [h1₇]
        _ = (shiftZero (X.unop) : X.unop → X.unop) := by
          apply Eq.symm • Eq.symm
          exact Eq.symm_of_eq h1₂
    have h₁₁ : (shiftZero (X.unop) : X.unop → X.unop) = id := by
      apply eq_of_sub_eq_zero
      have h₁₂ : (shiftZero (X.unop) : X.unop → X.unop) - id = 0 := by
        have h₁₃ : (shiftZero (X.unop) : X.unop → X.unop) ; (shiftZero (X.unop) : X.unop → X.unop) = (shiftZero (X.unop) : X.unop → X.unop) := h₁₀
        have h₁₄ : (shiftZero (X.unop) : X.unop → X.unop) ≅ (X.unop) → X.unop := by
          refine' ⟨shiftZero (X.unop), _⟩
          constructor <;>
          (try simp_all [Function.comp_apply]) <;>
          (try aesop) <;>
          (try
            {
              ext x
              simp [h1₂]
              <;>
              aesop
            })
        obtain ⟨g, hg₁, hg₂⟩ := h₁₄
        have h₁₅ : g ; (shiftZero (X.unop) : X.unop → X.unop) = id := by
          exact hg₂.symm
        have h₁₆ : (shiftZero (X.unop) : X.unop → X.unop) ; g = id := by
          exact hg₁
        calc
          (shiftZero (X.unop) : X.unop → X.unop) = (shiftZero (X.unop) : X.unop → X.unop) ; id := by simp
          _ = (shiftZero (X.unop) : X.unop → X.unop) ; (g ; (shiftZero (X.unop) : X.unop → X.unop)) := by
            rw [h₁₅]
          _ = ((shiftZero (X.unop) : X.unop → X.unop) ; g) ; (shiftZero (X.unop) : X.unop → X.unop) := by
            assoc
          _ = id ; (shiftZero (X.unop) : X.unop → X.unop) := by
            rw [h₁₆]
          _ = (shiftZero (X.unop) : X.unop → X.unop) := by simp
      exact h₁₂
    exact h₁₀
  rw [h₁₄]
  have h₁₅ : ((id (X.unop)) : (X.unop) → (X.unop)).op = id ((X.unop)ᵒᵖ) := by
    simp [id]
  rw [h₁₅]
  have h₁₆ : ((X.unop)ᵒᵖ : Cᵒᵖ) = X := rfl
  rw [h₁₆]
  <;> simp [id]
  
have h2 : (pullbackShiftIso (OppositeShift C ℤ) (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0).hom.app X = id X := by
  have h2₁ : (pullbackShiftIso (OppositeShift C ℤ) (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0).hom = 𝟙 (OppositeShift C ℤ) := by
    apply NaturalTransformation.ext
    intro Y
    simp [pullbackShiftIso, OppositeShift, shiftFunctor, shiftFunctorZero, AddMonoidHom.mk']
    <;>
    (try simp_all [shiftFunctor, shiftFunctorZero, AddMonoidHom.mk']) <;>
    (try aesop) <;>
    (try
      {
        ext y
        simp [shiftFunctor, shiftFunctorZero, AddMonoidHom.mk']
        <;>
        aesop
      })
  have h2₂ : (pullbackShiftIso (OppositeShift C ℤ) (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0).hom.app X = (𝟙 (OppositeShift C ℤ)).app X := by
    rw [h2₁]
  rw [h2₂]
  simp [OppositeShift]
  <;>
  (try simp_all [shiftFunctor, shiftFunctorZero]) <;>
  (try aesop)
  
have h3 : (shiftFunctorOpIso C 0 0 ⋯).hom.app X = id X := by
  have h3₁ : (shiftFunctorOpIso C 0 0 ⋯).hom = 𝟙 (OppositeShift C ℤ) := by
    apply NaturalTransformation.ext
    intro Y
    simp [shiftFunctorOpIso, OppositeShift, shiftFunctor, shiftFunctorZero]
    <;>
    (try simp_all [shiftFunctor, shiftFunctorZero]) <;>
    (try aesop) <;>
    (try
      {
        ext y
        simp [shiftFunctor, shiftFunctorZero]
        <;>
        aesop
      })
  have h3₂ : (shiftFunctorOpIso C 0 0 ⋯).hom.app X = (𝟙 (OppositeShift C ℤ)).app X := by
    rw [h3₁]
  rw [h3₂]
  simp [OppositeShift]
  <;>
  (try simp_all [shiftFunctor, shiftFunctorZero]) <;>
  (try aesop)
  
calculations
  (pullbackShiftIso (OppositeShift C ℤ) (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0).hom.app X ≫ ((shiftFunctorZero C ℤ).inv.app X.unop).op = (id X) ≫ ((shiftFunctorZero C ℤ).inv.app X.unop).op := by rw [h2]
  _ = (id X) ≫ (id X) := by rw [h1]
  _ = (id X) := by simp
  _ = (shiftFunctorOpIso C 0 0 ⋯).hom.app X ≫ (id X) := by
    have h4 : (shiftFunctorOpIso C 0 0 ⋯).hom.app X = id X := h3
    rw [h4]
    <;> simp
  _ = (shiftFunctorOpIso C 0 0 ⋯).hom.app X ≫ ((shiftFunctorZero C ℤ).inv.app X.unop).op := by
    rw [h1]
    <;> simp
```

**lean_error:** tail step 1/126 ('have h1 : ((shiftFunctorZero C ℤ).inv.app X.unop).op = id X := by'): <stdin>:1:65: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.6s, verify 1.1s, in=465, out=483)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackShiftIso, shiftFunctorOpIso]
```
