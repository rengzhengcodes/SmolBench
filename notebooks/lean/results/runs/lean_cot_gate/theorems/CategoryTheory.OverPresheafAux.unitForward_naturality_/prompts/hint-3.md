## Current goal
```
⊢ unitForward μ X (YonedaCollection.map₁ (restrictedYonedaObjMap₁ ε hε) p) = ε.app (op X) (unitForward η X p)
```

## Full tactic state
```
C : Type u
inst✝ : Category.{v, u} C
A F G : Cᵒᵖ ⥤ Type v
η : F ⟶ A
μ : G ⟶ A
ε : F ⟶ G
hε : ε ≫ μ = η
X : C
p : YonedaCollection (restrictedYonedaObj η) X
⊢ unitForward μ X (YonedaCollection.map₁ (restrictedYonedaObjMap₁ ε hε) p) = ε.app (op X) (unitForward η X p)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.OverPresheafAux.unitForward_naturality₁` in `Mathlib/CategoryTheory/Comma/Presheaf.lean`

## Premises used in the next tactic
- `CategoryTheory.OverPresheafAux.unitForward`

## Premise signatures
### `CategoryTheory.OverPresheafAux.unitForward` (commanddeclaration)
```lean
def unitForward {F : Cᵒᵖ ⥤ Type v} (η : F ⟶ A) (X : C) :
    YonedaCollection (restrictedYonedaObj η) X → F.obj (op X)
```

## Premise full source (with proof)
### `CategoryTheory.OverPresheafAux.unitForward` (commanddeclaration) at `Mathlib/CategoryTheory/Comma/Presheaf.lean`
```lean
/-- Forward direction of the unit. -/
def unitForward {F : Cᵒᵖ ⥤ Type v} (η : F ⟶ A) (X : C) :
    YonedaCollection (restrictedYonedaObj η) X → F.obj (op X) :=
  fun p => p.snd.val
```

## Transitive premise context (1-hop, 3/3 premises, ≈600 tokens)
### `AffineSubspace.direction` (commanddeclaration) at `Mathlib/LinearAlgebra/AffineSpace/AffineSubspace.lean`
```lean
/-- The direction of an affine subspace is the submodule spanned by
the pairwise differences of points.  (Except in the case of an empty
affine subspace, where the direction is the zero submodule, every
vector in the direction is the difference of two points in the affine
subspace.) -/
def direction (s : AffineSubspace k P) : Submodule k V :=
  vectorSpan k (s : Set P)
```

### `CategoryTheory.OverPresheafAux.YonedaCollection` (commanddeclaration) at `Mathlib/CategoryTheory/Comma/Presheaf.lean`
```lean
/-- To give an object of `Over A`, we will in particular need a presheaf `Cᵒᵖ ⥤ Type v`. This is the
    definition of that presheaf on objects.

    We would prefer to think of this sigma type to be indexed by natural transformations
    `yoneda.obj X ⟶ A` instead of `A.obj (op X)`. These are equivalent by the Yoneda lemma, but
    we cannot use the former because that type lives in the wrong universe. Hence, we will provide
    a lot of API that will enable us to pretend that we are really indexing over
    `yoneda.obj X ⟶ A`. -/
def YonedaCollection (F : (CostructuredArrow yoneda A)ᵒᵖ ⥤ Type v) (X : C) : Type v :=
  Σ s : A.obj (op X), F.obj (op (CostructuredArrow.mk (yonedaEquiv.symm s)))
```

### `CategoryTheory.OverPresheafAux.restrictedYonedaObj` (commanddeclaration) at `Mathlib/CategoryTheory/Comma/Presheaf.lean`
```lean
/-- This is basically just `yoneda.obj η : (Over A)ᵒᵖ ⥤ Type (max u v)` restricted along the
    forgetful functor `CostructuredArrow yoneda A ⥤ Over A`, but done in a way that we land in a
    smaller universe. -/
@[simps]
def restrictedYonedaObj {F : Cᵒᵖ ⥤ Type v} (η : F ⟶ A) :
    (CostructuredArrow yoneda A)ᵒᵖ ⥤ Type v where
  obj s := OverArrows η s.unop.hom
  map f u := u.map₂ f.unop.left f.unop.w

/-- Functoriality of `restrictedYonedaObj η` in `η`. -/
```
