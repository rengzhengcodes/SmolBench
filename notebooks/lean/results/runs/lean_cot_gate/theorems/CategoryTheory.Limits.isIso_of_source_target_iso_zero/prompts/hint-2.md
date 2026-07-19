## Current goal
```
⊢ IsIso 0
```

## Full tactic state
```
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasZeroMorphisms C
inst✝ : HasZeroObject C
X Y : C
f : X ⟶ Y
i : X ≅ 0
j : Y ≅ 0
⊢ IsIso 0
```

## Proof so far (1 tactic)
```lean
rw [zero_of_source_iso_zero f i]
```

## Theorem
`CategoryTheory.Limits.isIso_of_source_target_iso_zero` in `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.isIsoZeroEquivIsoZero`
- `Equiv.invFun`

## Premise signatures
### `CategoryTheory.Limits.isIsoZeroEquivIsoZero` (commanddeclaration)
```lean
def isIsoZeroEquivIsoZero (X Y : C) : IsIso (0 : X ⟶ Y) ≃ (X ≅ 0) × (Y ≅ 0)
```

### `Equiv.invFun`
_(not found in premise corpus)_

## Premise full source (with proof)
### `CategoryTheory.Limits.isIsoZeroEquivIsoZero` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
/-- A zero morphism `0 : X ⟶ Y` is an isomorphism if and only if
`X` and `Y` are isomorphic to the zero object.
-/
def isIsoZeroEquivIsoZero (X Y : C) : IsIso (0 : X ⟶ Y) ≃ (X ≅ 0) × (Y ≅ 0) := by
  -- This is lame, because `Prod` can't cope with `Prop`, so we can't use `Equiv.prodCongr`.
  refine' (isIsoZeroEquiv X Y).trans _
  symm
  fconstructor
  · rintro ⟨eX, eY⟩
    fconstructor
    exact (idZeroEquivIsoZero X).symm eX
    exact (idZeroEquivIsoZero Y).symm eY
  · rintro ⟨hX, hY⟩
    fconstructor
    exact (idZeroEquivIsoZero X) hX
    exact (idZeroEquivIsoZero Y) hY
  · aesop_cat
  · aesop_cat
```

### `Equiv.invFun`
_(not found in premise corpus)_
