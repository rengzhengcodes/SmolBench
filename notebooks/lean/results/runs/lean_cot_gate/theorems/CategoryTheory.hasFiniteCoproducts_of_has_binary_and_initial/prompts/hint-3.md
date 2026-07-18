## Current goal
```
⊢ HasColimit K
```

## Full tactic state
```
J : Type v
inst✝⁴ : SmallCategory J
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasBinaryCoproducts C
inst✝ : HasInitial C
n : ℕ
K : Discrete (Fin n) ⥤ C
this : HasCoproduct fun n_1 => K.obj { as := n_1 } := CategoryTheory.hasCoproduct_fin n fun n_1 => K.obj { as := n_1 }
that : K ≅ Discrete.functor fun n_1 => K.obj { as := n_1 } :=
  Discrete.natIso fun x =>
    match x with
    | { as := i } => Iso.refl (K.obj { as := i })
⊢ HasColimit K
```

## Proof so far (3 tactics)
```lean
refine' ⟨fun n => ⟨fun K => _⟩⟩
letI := hasCoproduct_fin n fun n => K.obj ⟨n⟩
let that : K ≅ Discrete.functor fun n => K.obj ⟨n⟩ := Discrete.natIso fun ⟨i⟩ => Iso.refl _
```

## Theorem
`CategoryTheory.hasFiniteCoproducts_of_has_binary_and_initial` in `Mathlib/CategoryTheory/Limits/Constructions/FiniteProductsOfBinaryProducts.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.hasColimitOfIso`

## Premise signatures
### `CategoryTheory.Limits.hasColimitOfIso` (commanddeclaration)
```lean
theorem hasColimitOfIso {F G : J ⥤ C} [HasColimit F] (α : G ≅ F) : HasColimit G
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
