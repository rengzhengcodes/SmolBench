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

## Transitive premise context (1-hop, 3/3 premises, ≈263 tokens)
### `LieAlgebra.Orthogonal.so` (commanddeclaration) at `Mathlib/Algebra/Lie/Classical.lean`
```lean
/-- The definite orthogonal Lie subalgebra: skew-adjoint matrices with respect to the symmetric
bilinear form defined by the identity matrix. -/
def so [Fintype n] : LieSubalgebra R (Matrix n n R) :=
  skewAdjointMatricesLieSubalgebra (1 : Matrix n n R)
```

### `CategoryTheory.Limits.HasColimit` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
/-- `HasColimit F` represents the mere existence of a colimit for `F`. -/
class HasColimit (F : J ⥤ C) : Prop where mk' ::
  /-- There exists a colimit for `F` -/
  exists_colimit : Nonempty (ColimitCocone F)
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```
