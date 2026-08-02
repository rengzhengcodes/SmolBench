## Current goal
```
⊢ (shiftFunctorAdd D a b).hom.app (F.obj X) =
    (i (a + b)).hom.app X ≫
      F.map ((shiftFunctorAdd C a b).hom.app X) ≫ (i b).inv.app ((shiftFunctor C a).obj X) ≫ (s b).map ((i a).inv.app X)
```

## Full tactic state
```
C : Type u_4
D : Type u_2
inst✝³ : Category.{u_5, u_4} C
inst✝² : Category.{u_1, u_2} D
F : C ⥤ D
A : Type u_3
inst✝¹ : AddMonoid A
inst✝ : HasShift C A
s : A → D ⥤ D
i : (a : A) → F ⋙ s a ≅ shiftFunctor C a ⋙ F
hF : Nonempty (Full ((whiskeringLeft C D D).obj F)) ∧ Faithful ((whiskeringLeft C D D).obj F)
a b : A
X : C
this : Nonempty (Full ((whiskeringLeft C D D).obj F)) ∧ Faithful ((whiskeringLeft C D D).obj F) → HasShift D A :=
  HasShift.induced F A s i
⊢ (shiftFunctorAdd D a b).hom.app (F.obj X) =
    (i (a + b)).hom.app X ≫
      F.map ((shiftFunctorAdd C a b).hom.app X) ≫ (i b).inv.app ((shiftFunctor C a).obj X) ≫ (s b).map ((i a).inv.app X)
```

## Proof so far (1 tactic)
```lean
letI := HasShift.induced F A s i
```

## Theorem
`CategoryTheory.shiftFunctorAdd_hom_app_obj_of_induced` in `Mathlib/CategoryTheory/Shift/Induced.lean`

## Premises used in the next tactic
- `CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq`
- `CategoryTheory.HasShift.Induced.add_hom_app_obj`

## Premise signatures
### `CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq` (lemma)
```lean
lemma ShiftMkCore.shiftFunctorAdd_eq (h : ShiftMkCore C A) (a b : A) :
    letI
```

### `CategoryTheory.HasShift.Induced.add_hom_app_obj` (lemma)
```lean
@[simp]
lemma add_hom_app_obj (a b : A) (X : C) :
    (add F s i hF a b).hom.app (F.obj X) =
      (i (a + b)).hom.app X ≫ F.map ((shiftFunctorAdd C a b).hom.app X) ≫
        (i b).inv.app ((shiftFunctor C a).obj X) ≫ (s b).map ((i a).inv.app X)
```

## Premise full source (with proof)
### `CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq` (lemma) at `Mathlib/CategoryTheory/Shift/Basic.lean`
```lean
lemma ShiftMkCore.shiftFunctorAdd_eq (h : ShiftMkCore C A) (a b : A) :
    letI := hasShiftMk C A h;
    shiftFunctorAdd C a b = h.add a b := by
  letI := hasShiftMk C A h
  change (shiftFunctorAdd C a b).symm.symm = (h.add a b).symm.symm
  congr 1
  ext
  rfl
```

### `CategoryTheory.HasShift.Induced.add_hom_app_obj` (lemma) at `Mathlib/CategoryTheory/Shift/Induced.lean`
```lean
@[simp]
lemma add_hom_app_obj (a b : A) (X : C) :
    (add F s i hF a b).hom.app (F.obj X) =
      (i (a + b)).hom.app X ≫ F.map ((shiftFunctorAdd C a b).hom.app X) ≫
        (i b).inv.app ((shiftFunctor C a).obj X) ≫ (s b).map ((i a).inv.app X) := by
  letI := hF.1.some
  have h : whiskerLeft F (add F s i hF a b).hom = _ :=
    ((whiskeringLeft C D D).obj F).image_preimage _
  exact (NatTrans.congr_app h X).trans (by simp)
```

## Transitive premise context (1-hop, 6/6 premises, ≈1381 tokens)
### `CategoryTheory.ShiftMkCore` (commanddeclaration) at `Mathlib/CategoryTheory/Shift/Basic.lean`
```lean
/-- A helper structure to construct the shift functor `(Discrete A) ⥤ (C ⥤ C)`. -/
structure ShiftMkCore where
  /-- the family of shift functors -/
  F : A → C ⥤ C
  /-- the shift by 0 identifies to the identity functor -/
  zero : F 0 ≅ 𝟭 C
  /-- the composition of shift functors identifies to the shift by the sum -/
  add : ∀ n m : A, F (n + m) ≅ F n ⋙ F m
  /-- compatibility with the associativity -/
  assoc_hom_app : ∀ (m₁ m₂ m₃ : A) (X : C),
    (add (m₁ + m₂) m₃).hom.app X ≫ (F m₃).map ((add m₁ m₂).hom.app X) =
      eqToHom (by rw [add_assoc]) ≫ (add m₁ (m₂ + m₃)).hom.app X ≫
        (add m₂ m₃).hom.app ((F m₁).obj X) := by aesop_cat
  /-- compatibility with the left addition with 0 -/
  zero_add_hom_app : ∀ (n : A) (X : C), (add 0 n).hom.app X =
    eqToHom (by dsimp; rw [zero_add]) ≫ (F n).map (zero.inv.app X) := by aesop_cat
  /-- compatibility with the right addition with 0 -/
  add_zero_hom_app : ∀ (n : A) (X : C), (add n 0).hom.app X =
    eqToHom (by dsimp; rw [add_zero]) ≫ zero.inv.app ((F n).obj X) := by aesop_cat
```

### `Lean.Parser.Term.letI` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
/-- `letI` behaves like `let`, but inlines the value instead of producing a `let_fun` term. -/
@[builtin_term_parser] def «letI» := leading_parser
  withPosition ("letI " >> haveDecl) >> optSemicolon termParser
```

### `CategoryTheory.hasShiftMk` (commanddeclaration) at `Mathlib/CategoryTheory/Shift/Basic.lean`
```lean
/-- Constructs a `HasShift C A` instance from `ShiftMkCore`. -/
@[simps]
def hasShiftMk (h : ShiftMkCore C A) : HasShift C A :=
  ⟨{ Discrete.functor h.F with
      ε := h.zero.inv
      μ := fun m n => (h.add m.as n.as).inv
      μ_natural_left := by
        rintro ⟨X⟩ ⟨Y⟩ ⟨⟨⟨rfl⟩⟩⟩ ⟨X'⟩
        ext
        dsimp
        simp
      μ_natural_right := by
        rintro ⟨X⟩ ⟨Y⟩ ⟨X'⟩ ⟨⟨⟨rfl⟩⟩⟩
        ext
        dsimp
        simp
      associativity := by
        rintro ⟨m₁⟩ ⟨m₂⟩ ⟨m₃⟩
        ext X
        simp [endofunctorMonoidalCategory, h.assoc_inv_app_assoc]
      left_unitality := by
        rintro ⟨n⟩
        ext X
        simp [endofunctorMonoidalCategory, h.zero_add_inv_app, ← Functor.map_comp]
      right_unitality := by
        rintro ⟨n⟩
        ext X
        simp [endofunctorMonoidalCategory, h.add_zero_inv_app]}⟩
```

### `congr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Congruence in both function and argument. If `f₁ = f₂` and `a₁ = a₂` then
`f₁ a₁ = f₂ a₂`. This only works for nondependent functions; the theorem
statement is more complex in the dependent case.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem congr {α : Sort u} {β : Sort v} {f₁ f₂ : α → β} {a₁ a₂ : α} (h₁ : Eq f₁ f₂) (h₂ : Eq a₁ a₂) : Eq (f₁ a₁) (f₂ a₂) :=
  h₁ ▸ h₂ ▸ rfl

/-- Congruence in the function part of an application: If `f = g` then `f a = g a`. -/
```

### `CategoryTheory.whiskeringLeft` (commanddeclaration) at `Mathlib/CategoryTheory/Whiskering.lean`
```lean
/-- Left-composition gives a functor `(C ⥤ D) ⥤ ((D ⥤ E) ⥤ (C ⥤ E))`.

`(whiskeringLeft.obj F).obj G` is `F ⋙ G`, and
`(whiskeringLeft.obj F).map α` is `whiskerLeft F α`.
-/
@[simps]
def whiskeringLeft : (C ⥤ D) ⥤ (D ⥤ E) ⥤ C ⥤ E where
  obj F :=
    { obj := fun G => F ⋙ G
      map := fun α => whiskerLeft F α }
  map τ :=
    { app := fun H =>
        { app := fun c => H.map (τ.app c)
          naturality := fun X Y f => by dsimp; rw [← H.map_comp, ← H.map_comp, ← τ.naturality] }
      naturality := fun X Y f => by ext; dsimp; rw [f.naturality] }
```

### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
```
