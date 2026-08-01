## Current goal
```
⊢ HasColimit F
```

## Full tactic state
```
J : Type u₁
inst✝³ : Category.{v₁, u₁} J
K : Type u₂
inst✝² : Category.{v₂, u₂} K
C : Type u
inst✝¹ : Category.{v, u} C
F : J ⥤ C
e : K ≌ J
inst✝ : HasColimit (e.functor ⋙ F)
this : HasColimit (e.inverse ⋙ e.functor ⋙ F)
⊢ HasColimit F
```

## Proof so far (1 tactic)
```lean
haveI : HasColimit (e.inverse ⋙ e.functor ⋙ F) := Limits.hasColimit_equivalence_comp e.symm
```

## Theorem
`CategoryTheory.Limits.hasColimit_of_equivalence_comp` in `Mathlib/CategoryTheory/Limits/HasLimits.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.hasColimitOfIso`
- `CategoryTheory.Iso.symm`

## Premise signatures
### `CategoryTheory.Limits.hasColimitOfIso` (commanddeclaration)
```lean
theorem hasColimitOfIso {F G : J ⥤ C} [HasColimit F] (α : G ≅ F) : HasColimit G
```

### `CategoryTheory.Iso.symm` (commanddeclaration)
```lean
@[symm, pp_dot]
def symm (I : X ≅ Y) : Y ≅ X where
  hom
```

## Premise full source (with proof)
### `CategoryTheory.Limits.hasColimitOfIso` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
/-- If `F` has a colimit, so does any naturally isomorphic functor.
-/
theorem hasColimitOfIso {F G : J ⥤ C} [HasColimit F] (α : G ≅ F) : HasColimit G :=
  HasColimit.mk
    { cocone := (Cocones.precompose α.hom).obj (colimit.cocone F)
      isColimit := (IsColimit.precomposeHomEquiv _ _).symm (colimit.isColimit F) }
```

### `CategoryTheory.Iso.symm` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
/-- Inverse isomorphism. -/
@[symm, pp_dot]
def symm (I : X ≅ Y) : Y ≅ X where
  hom := I.inv
  inv := I.hom
```

## Filler (hint:2 → hint:3 token-match, ≈286 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est labor
