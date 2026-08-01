## Current goal
```
⊢ ρFunctorObj f πX ≫ πFunctorObj f πX = π'FunctorObj f πX
```

## Full tactic state
```
C : Type u
inst✝⁴ : Category.{v, u} C
I : Type w
A B : I → C
f : (i : I) → A i ⟶ B i
S X Y Z : C
πX : X ⟶ S
πY : Y ⟶ S
φ : X ⟶ Y
hφ : φ ≫ πY = πX
inst✝³ : HasColimitsOfShape (Discrete (FunctorObjIndex f πX)) C
inst✝² : HasColimitsOfShape (Discrete (FunctorObjIndex f πY)) C
inst✝¹ : HasPushout (functorObjTop f πX) (functorObjLeft f πX)
inst✝ : HasPushout (functorObjTop f πY) (functorObjLeft f πY)
⊢ ρFunctorObj f πX ≫ πFunctorObj f πX = π'FunctorObj f πX
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.SmallObject.ρFunctorObj_π` in `Mathlib/CategoryTheory/SmallObject/Construction.lean`

## Premises used in the next tactic
- `CategoryTheory.SmallObject.πFunctorObj`

## Premise signatures
### `CategoryTheory.SmallObject.πFunctorObj` (commanddeclaration)
```lean
noncomputable def πFunctorObj : functorObj f πX ⟶ S
```

## Premise full source (with proof)
### `CategoryTheory.SmallObject.πFunctorObj` (commanddeclaration) at `Mathlib/CategoryTheory/SmallObject/Construction.lean`
```lean
/-- The canonical projection on the base object. -/
noncomputable def πFunctorObj : functorObj f πX ⟶ S :=
  pushout.desc πX (π'FunctorObj f πX) (by ext; simp [π'FunctorObj])
```

## Transitive premise context (1-hop, 1/1 premises, ≈135 tokens)
### `CategoryTheory.SmallObject.functorObj` (commanddeclaration) at `Mathlib/CategoryTheory/SmallObject/Construction.lean`
```lean
/-- The functor `SmallObject.functor f S : Over S ⥤ Over S` that is part of
the small object argument for a family of morphisms `f`, on an object given
as a morphism `πX : X ⟶ S`. -/
noncomputable abbrev functorObj : C :=
  pushout (functorObjTop f πX) (functorObjLeft f πX)

/-- The canonical morphism `X ⟶ functorObj f πX`. -/
```
