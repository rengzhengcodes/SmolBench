## Current goal
```
⊢ Fintype.card β ≤ Fintype.card α
```

## Full tactic state
```
R : Type u
inst✝³ : Semiring R
inst✝² : RankCondition R
α : Type u_1
β : Type u_2
inst✝¹ : Fintype α
inst✝ : Fintype β
f : (α →₀ R) →ₗ[R] β →₀ R
i : Surjective ⇑f
P : (β →₀ R) ≃ₗ[R] β → R := Finsupp.linearEquivFunOnFinite R R β
Q : (α → R) ≃ₗ[R] α →₀ R := LinearEquiv.symm (Finsupp.linearEquivFunOnFinite R R α)
⊢ Fintype.card β ≤ Fintype.card α
```

## Proof so far (2 tactics)
```lean
let P := Finsupp.linearEquivFunOnFinite R R β
let Q := (Finsupp.linearEquivFunOnFinite R R α).symm
```

## Theorem
`card_le_of_surjective'` in `Mathlib/LinearAlgebra/InvariantBasisNumber.lean`

## Premises used in the next tactic
- `card_le_of_surjective`
- `LinearMap.comp`
- `Function.Surjective.comp`

## Premise signatures
### `card_le_of_surjective` (commanddeclaration)
```lean
theorem card_le_of_surjective [RankCondition R] {α β : Type*} [Fintype α] [Fintype β]
    (f : (α → R) →ₗ[R] β → R) (i : Surjective f) : Fintype.card β ≤ Fintype.card α
```

### `LinearMap.comp` (commanddeclaration)
```lean
def comp : M₁ →ₛₗ[σ₁₃] M₃ where
  toFun
```

### `Function.Surjective.comp` (commanddeclaration)
```lean
theorem Surjective.comp {g : β → φ} {f : α → β} (hg : Surjective g) (hf : Surjective f) :
    Surjective (g ∘ f)
```

## Premise full source (with proof)
### `card_le_of_surjective` (commanddeclaration) at `Mathlib/LinearAlgebra/InvariantBasisNumber.lean`
```lean
theorem card_le_of_surjective [RankCondition R] {α β : Type*} [Fintype α] [Fintype β]
    (f : (α → R) →ₗ[R] β → R) (i : Surjective f) : Fintype.card β ≤ Fintype.card α := by
  let P := LinearEquiv.funCongrLeft R R (Fintype.equivFin α)
  let Q := LinearEquiv.funCongrLeft R R (Fintype.equivFin β)
  exact
    le_of_fin_surjective R ((Q.symm.toLinearMap.comp f).comp P.toLinearMap)
      (((LinearEquiv.symm Q).surjective.comp i).comp (LinearEquiv.surjective P))
```

### `LinearMap.comp` (commanddeclaration) at `Mathlib/Algebra/Module/LinearMap/Basic.lean`
```lean
/-- Composition of two linear maps is a linear map -/
def comp : M₁ →ₛₗ[σ₁₃] M₃ where
  toFun := f ∘ g
  map_add' := by simp only [map_add, forall_const, Function.comp_apply]
  -- Note that #8386 changed `map_smulₛₗ` to `map_smulₛₗ _`
  map_smul' r x := by simp only [Function.comp_apply, map_smulₛₗ _, RingHomCompTriple.comp_apply]
```

### `Function.Surjective.comp` (commanddeclaration) at `Mathlib/Init/Function.lean`
```lean
theorem Surjective.comp {g : β → φ} {f : α → β} (hg : Surjective g) (hf : Surjective f) :
    Surjective (g ∘ f) := fun c : φ =>
  Exists.elim (hg c) fun b hb =>
    Exists.elim (hf b) fun a ha =>
      Exists.intro a (show g (f a) = c from Eq.trans (congr_arg g ha) hb)
```
