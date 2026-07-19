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

## Transitive premise context (1-hop, 8/8 premises, ≈1237 tokens)
### `CategoryTheory.IsIso` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
/-- `IsIso` typeclass expressing that a morphism is invertible. -/
class IsIso (f : X ⟶ Y) : Prop where
  /-- The existence of an inverse morphism. -/
  out : ∃ inv : Y ⟶ X, f ≫ inv = 𝟙 X ∧ inv ≫ f = 𝟙 Y
```

### `Prod` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Product type (aka pair). You can use `α × β` as notation for `Prod α β`.
Given `a : α` and `b : β`, `Prod.mk a b : Prod α β`. You can use `(a, b)`
as notation for `Prod.mk a b`. Moreover, `(a, b, c)` is notation for
`Prod.mk a (Prod.mk b c)`.
Given `p : Prod α β`, `p.1 : α` and `p.2 : β`. They are short for `Prod.fst p`
and `Prod.snd p` respectively. You can also write `p.fst` and `p.snd`.
For more information: [Constructors with Arguments](https://lean-lang.org/theorem_proving_in_lean4/inductive_types.html?highlight=Prod#constructors-with-arguments)
-/
structure Prod (α : Type u) (β : Type v) where
  /-- The first projection out of a pair. if `p : α × β` then `p.1 : α`. -/
  fst : α
  /-- The second projection out of a pair. if `p : α × β` then `p.2 : β`. -/
  snd : β
```

### `LieAlgebra.Orthogonal.so` (commanddeclaration) at `Mathlib/Algebra/Lie/Classical.lean`
```lean
/-- The definite orthogonal Lie subalgebra: skew-adjoint matrices with respect to the symmetric
bilinear form defined by the identity matrix. -/
def so [Fintype n] : LieSubalgebra R (Matrix n n R) :=
  skewAdjointMatricesLieSubalgebra (1 : Matrix n n R)
```

### `Equiv.prodCongr` (commanddeclaration) at `Mathlib/Logic/Equiv/Basic.lean`
```lean
/-- Product of two equivalences. If `α₁ ≃ α₂` and `β₁ ≃ β₂`, then `α₁ × β₁ ≃ α₂ × β₂`. This is
`Prod.map` as an equivalence. -/
-- Porting note: in Lean 3 there was also a @[congr] tag
@[simps (config := .asFn) apply]
def prodCongr (e₁ : α₁ ≃ α₂) (e₂ : β₁ ≃ β₂) : α₁ × β₁ ≃ α₂ × β₂ :=
  ⟨Prod.map e₁ e₂, Prod.map e₁.symm e₂.symm, fun ⟨a, b⟩ => by simp, fun ⟨a, b⟩ => by simp⟩
```

### `CategoryTheory.Limits.isIsoZeroEquiv` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
/-- A zero morphism `0 : X ⟶ Y` is an isomorphism if and only if
the identities on both `X` and `Y` are zero.
-/
@[simps]
def isIsoZeroEquiv (X Y : C) : IsIso (0 : X ⟶ Y) ≃ 𝟙 X = 0 ∧ 𝟙 Y = 0 where
  toFun := by
    intro i
    rw [← IsIso.hom_inv_id (0 : X ⟶ Y)]
    rw [← IsIso.inv_hom_id (0 : X ⟶ Y)]
    simp only [eq_self_iff_true,comp_zero,and_self,zero_comp]
  invFun h := ⟨⟨(0 : Y ⟶ X), by aesop_cat⟩⟩
  left_inv := by aesop_cat
  right_inv := by aesop_cat
```

### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `CategoryTheory.Limits.idZeroEquivIsoZero` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
/-- An object `X` has `𝟙 X = 0` if and only if it is isomorphic to the zero object.

Because `X ≅ 0` contains data (even if a subsingleton), we express this `↔` as an `≃`.
-/
def idZeroEquivIsoZero (X : C) : 𝟙 X = 0 ≃ (X ≅ 0) where
  toFun h :=
    { hom := 0
      inv := 0 }
  invFun i := zero_of_target_iso_zero (𝟙 X) i
  left_inv := by aesop_cat
  right_inv := by aesop_cat
```
