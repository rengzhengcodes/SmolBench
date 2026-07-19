## Current goal
```
⊢ Cocone.extend (colimitCocone h) (homOfCocone h s) = coconeOfHom h (homOfCocone h s)
```

## Full tactic state
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
F : J ⥤ C
t : Cocone F
X : C
h : coyoneda.obj (op X) ⋙ uliftFunctor.{u₁, v₃} ≅ Functor.cocones F
s : Cocone F
⊢ Cocone.extend (colimitCocone h) (homOfCocone h s) = coconeOfHom h (homOfCocone h s)
```

## Proof so far (2 tactics)
```lean
rw [← coconeOfHom_homOfCocone h s]
conv_lhs => simp only [homOfCocone_cooneOfHom]
```

## Theorem
`CategoryTheory.Limits.IsColimit.OfNatIso.cocone_fac` in `Mathlib/CategoryTheory/Limits/IsLimit.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.IsColimit.OfNatIso.coconeOfHom_fac`
- `Eq.symm`

## Premise signatures
### `CategoryTheory.Limits.IsColimit.OfNatIso.coconeOfHom_fac` (commanddeclaration)
```lean
theorem coconeOfHom_fac {Y : C} (f : X ⟶ Y) : coconeOfHom h f = (colimitCocone h).extend f
```

### `Eq.symm` (commanddeclaration)
```lean
theorem Eq.symm {α : Sort u} {a b : α} (h : Eq a b) : Eq b a
```

## Premise full source (with proof)
### `CategoryTheory.Limits.IsColimit.OfNatIso.coconeOfHom_fac` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/IsLimit.lean`
```lean
/-- If `F.cocones` is corepresented by `X`, the cocone corresponding to a morphism `f : Y ⟶ X` is
the colimit cocone extended by `f`. -/
theorem coconeOfHom_fac {Y : C} (f : X ⟶ Y) : coconeOfHom h f = (colimitCocone h).extend f := by
  dsimp [coconeOfHom, colimitCocone, Cocone.extend]
  congr with j
  have t := congrFun (h.hom.naturality f) ⟨𝟙 X⟩
  dsimp at t
  simp only [id_comp] at t
  rw [congrFun (congrArg NatTrans.app t) j]
  rfl
```

### `Eq.symm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Equality is symmetric: if `a = b` then `b = a`.

Because this is in the `Eq` namespace, if you have a variable `h : a = b`,
`h.symm` can be used as shorthand for `Eq.symm h` as a proof of `b = a`.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem Eq.symm {α : Sort u} {a b : α} (h : Eq a b) : Eq b a :=
  h ▸ rfl

/--
Equality is transitive: if `a = b` and `b = c` then `a = c`.

Because this is in the `Eq` namespace, if you have variables or expressions
`h₁ : a = b` and `h₂ : b = c`, you can use `h₁.trans h₂ : a = c` as shorthand
for `Eq.trans h₁ h₂`.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
```
