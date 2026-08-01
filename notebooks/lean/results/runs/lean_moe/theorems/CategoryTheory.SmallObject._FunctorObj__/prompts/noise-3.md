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

## Filler (hint:2 → hint:3 token-match, ≈156 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum
