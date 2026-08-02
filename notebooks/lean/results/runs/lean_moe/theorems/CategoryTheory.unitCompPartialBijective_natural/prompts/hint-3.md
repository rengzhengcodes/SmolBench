## Current goal
```
⊢ (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h
```

## Full tactic state
```
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
inst✝¹ : Category.{v₃, u₃} E
i : D ⥤ C
inst✝ : Reflective i
A B B' : C
h : B ⟶ B'
hB : B ∈ Functor.essImage i
hB' : B' ∈ Functor.essImage i
f : A ⟶ B
⊢ (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.unitCompPartialBijective_natural` in `Mathlib/CategoryTheory/Adjunction/Reflective.lean`

## Premises used in the next tactic
- `Equiv.eq_symm_apply`
- `CategoryTheory.unitCompPartialBijective_symm_natural`
- `Equiv.symm_apply_apply`

## Premise signatures
### `Equiv.eq_symm_apply` (commanddeclaration)
```lean
theorem eq_symm_apply {α β} (e : α ≃ β) {x y} : y = e.symm x ↔ e y = x
```

### `CategoryTheory.unitCompPartialBijective_symm_natural` (commanddeclaration)
```lean
theorem unitCompPartialBijective_symm_natural [Reflective i] (A : C) {B B' : C} (h : B ⟶ B')
    (hB : B ∈ i.essImage) (hB' : B' ∈ i.essImage) (f : i.obj ((leftAdjoint i).obj A) ⟶ B) :
    (unitCompPartialBijective A hB').symm (f ≫ h) = (unitCompPartialBijective A hB).symm f ≫ h
```

### `Equiv.symm_apply_apply` (commanddeclaration)
```lean
@[simp] theorem symm_apply_apply (e : α ≃ β) (x : α) : e.symm (e x) = x
```

## Premise full source (with proof)
### `Equiv.eq_symm_apply` (commanddeclaration) at `Mathlib/Logic/Equiv/Defs.lean`
```lean
theorem eq_symm_apply {α β} (e : α ≃ β) {x y} : y = e.symm x ↔ e y = x :=
  (eq_comm.trans e.symm_apply_eq).trans eq_comm
```

### `CategoryTheory.unitCompPartialBijective_symm_natural` (commanddeclaration) at `Mathlib/CategoryTheory/Adjunction/Reflective.lean`
```lean
theorem unitCompPartialBijective_symm_natural [Reflective i] (A : C) {B B' : C} (h : B ⟶ B')
    (hB : B ∈ i.essImage) (hB' : B' ∈ i.essImage) (f : i.obj ((leftAdjoint i).obj A) ⟶ B) :
    (unitCompPartialBijective A hB').symm (f ≫ h) = (unitCompPartialBijective A hB).symm f ≫ h := by
  simp
```

### `Equiv.symm_apply_apply` (commanddeclaration) at `Mathlib/Logic/Equiv/Defs.lean`
```lean
@[simp] theorem symm_apply_apply (e : α ≃ β) (x : α) : e.symm (e x) = x := e.left_inv x
```

## Transitive premise context (1-hop, 6/6 premises, ≈776 tokens)
### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
```

### `eq_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem eq_comm {a b : α} : a = b ↔ b = a := Eq.comm
```

### `CategoryTheory.Reflective` (commanddeclaration) at `Mathlib/CategoryTheory/Adjunction/Reflective.lean`
```lean
/--
A functor is *reflective*, or *a reflective inclusion*, if it is fully faithful and right adjoint.
-/
class Reflective (R : D ⥤ C) extends IsRightAdjoint R, Full R, Faithful R
```

### `CategoryTheory.leftAdjoint` (commanddeclaration) at `Mathlib/CategoryTheory/Adjunction/Basic.lean`
```lean
/-- Extract the left adjoint from the instance giving the chosen adjoint. -/
def leftAdjoint (R : D ⥤ C) [IsRightAdjoint R] : C ⥤ D :=
  IsRightAdjoint.left R
```

### `CategoryTheory.unitCompPartialBijective` (commanddeclaration) at `Mathlib/CategoryTheory/Adjunction/Reflective.lean`
```lean
/-- If `i` has a reflector `L`, then the function `(i.obj (L.obj A) ⟶ B) → (A ⟶ B)` given by
precomposing with `η.app A` is a bijection provided `B` is in the essential image of `i`.
That is, the function `fun (f : i.obj (L.obj A) ⟶ B) ↦ η.app A ≫ f` is bijective,
as long as `B` is in the essential image of `i`.
This definition gives an equivalence: the key property that the inverse can be described
nicely is shown in `unitCompPartialBijective_symm_apply`.

This establishes there is a natural bijection `(A ⟶ B) ≃ (i.obj (L.obj A) ⟶ B)`. In other words,
from the point of view of objects in `D`, `A` and `i.obj (L.obj A)` look the same: specifically
that `η.app A` is an isomorphism.
-/
def unitCompPartialBijective [Reflective i] (A : C) {B : C} (hB : B ∈ i.essImage) :
    (A ⟶ B) ≃ (i.obj ((leftAdjoint i).obj A) ⟶ B) :=
  calc
    (A ⟶ B) ≃ (A ⟶ i.obj (Functor.essImage.witness hB)) := Iso.homCongr (Iso.refl _) hB.getIso.symm
    _ ≃ (i.obj _ ⟶ i.obj (Functor.essImage.witness hB)) := unitCompPartialBijectiveAux _ _
    _ ≃ (i.obj ((leftAdjoint i).obj A) ⟶ B) :=
      Iso.homCongr (Iso.refl _) (Functor.essImage.getIso hB)
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```
