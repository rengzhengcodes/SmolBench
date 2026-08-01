## Current goal
```
⊢ { X := X✝, p := p✝¹, idem := idem✝¹ } = { X := X✝, p := p✝, idem := idem✝ }
```

## Full tactic state
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
p✝ : X✝ ⟶ X✝
idem✝ : p✝ ≫ p✝ = p✝
h_p : p✝¹ ≫ eqToHom ⋯ = eqToHom ⋯ ≫ p✝
⊢ { X := X✝, p := p✝¹, idem := idem✝¹ } = { X := X✝, p := p✝, idem := idem✝ }
```

## Proof so far (4 tactics)
```lean
cases P
cases Q
dsimp at h_X h_p
subst h_X
```

## Theorem
`CategoryTheory.Idempotents.Karoubi.ext` in `Mathlib/CategoryTheory/Idempotents/Karoubi.lean`

## Premises used in the next tactic
- `heq_eq_eq`
- `true_and`
- `CategoryTheory.eqToHom_refl`
- `CategoryTheory.Category.comp_id`
- `CategoryTheory.Category.id_comp`

## Premise signatures
### `heq_eq_eq` (commanddeclaration)
```lean
@[simp] theorem heq_eq_eq {α : Sort u} (a b : α) : HEq a b = (a = b)
```

### `true_and` (commanddeclaration)
```lean
@[simp] theorem true_and (p : Prop) : (True ∧ p) = p
```

### `CategoryTheory.eqToHom_refl` (commanddeclaration)
```lean
@[simp]
theorem eqToHom_refl (X : C) (p : X = X) : eqToHom p = 𝟙 X
```

### `CategoryTheory.Category.comp_id`
_(not found in premise corpus)_

### `CategoryTheory.Category.id_comp`
_(not found in premise corpus)_

## Premise full source (with proof)
### `heq_eq_eq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem heq_eq_eq {α : Sort u} (a b : α) : HEq a b = (a = b) := propext <| Iff.intro eq_of_heq heq_of_eq
```

### `true_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem true_and (p : Prop) : (True ∧ p) = p := propext ⟨(·.2), (⟨trivial, ·⟩)⟩
```

### `CategoryTheory.eqToHom_refl` (commanddeclaration) at `Mathlib/CategoryTheory/EqToHom.lean`
```lean
@[simp]
theorem eqToHom_refl (X : C) (p : X = X) : eqToHom p = 𝟙 X :=
  rfl
```

### `CategoryTheory.Category.comp_id`
_(not found in premise corpus)_

### `CategoryTheory.Category.id_comp`
_(not found in premise corpus)_

## Transitive premise context (1-hop, 4/4 premises, ≈1118 tokens)
### `HEq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Heterogeneous equality. `HEq a b` asserts that `a` and `b` have the same
type, and casting `a` across the equality yields `b`, and vice versa.

You should avoid using this type if you can. Heterogeneous equality does not
have all the same properties as `Eq`, because the assumption that the types of
`a` and `b` are equal is often too weak to prove theorems of interest. One
important non-theorem is the analogue of `congr`: If `HEq f g` and `HEq x y`
and `f x` and `g y` are well typed it does not follow that `HEq (f x) (g y)`.
(This does follow if you have `f = g` instead.) However if `a` and `b` have
the same type then `a = b` and `HEq a b` are equivalent.
-/
inductive HEq : {α : Sort u} → α → {β : Sort u} → β → Prop where
  /-- Reflexivity of heterogeneous equality. -/
  | refl (a : α) : HEq a a

/-- A version of `HEq.refl` with an implicit argument. -/
```

### `propext` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
The axiom of **propositional extensionality**. It asserts that if propositions
`a` and `b` are logically equivalent (i.e. we can prove `a` from `b` and vice versa),
then `a` and `b` are *equal*, meaning that we can replace `a` with `b` in all
contexts.

For simple expressions like `a ∧ c ∨ d → e` we can prove that because all the logical
connectives respect logical equivalence, we can replace `a` with `b` in this expression
without using `propext`. However, for higher order expressions like `P a` where
`P : Prop → Prop` is unknown, or indeed for `a = b` itself, we cannot replace `a` with `b`
without an axiom which says exactly this.

This is a relatively uncontroversial axiom, which is intuitionistically valid.
It does however block computation when using `#reduce` to reduce proofs directly
(which is not recommended), meaning that canonicity,
the property that all closed terms of type `Nat` normalize to numerals,
fails to hold when this (or any) axiom is used:
```
set_option pp.proofs true

def foo : Nat := by
  have : (True → True) ↔ True := ⟨λ _ => trivial, λ _ _ => trivial⟩
  have := propext this ▸ (2 : Nat)
  exact this

#reduce foo
-- propext { mp := fun x x => True.intro, mpr := fun x => True.intro } ▸ 2

#eval foo -- 2
```
`#eval` can evaluate it to a numeral because the compiler erases casts and
does not evaluate proofs, so `propext`, whose return type is a proposition,
can never block it.
-/
axiom propext {a b : Prop} : (a ↔ b) → a = b
```

### `eq_of_heq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
theorem eq_of_heq {α : Sort u} {a a' : α} (h : HEq a a') : Eq a a' :=
  have : (α β : Sort u) → (a : α) → (b : β) → HEq a b → (h : Eq α β) → Eq (cast h a) b :=
    fun _ _ _ _ h₁ =>
      h₁.rec (fun _ => rfl)
  this α α a a' h rfl

/--
Product type (aka pair). You can use `α × β` as notation for `Prod α β`.
Given `a : α` and `b : β`, `Prod.mk a b : Prod α β`. You can use `(a, b)`
as notation for `Prod.mk a b`. Moreover, `(a, b, c)` is notation for
`Prod.mk a (Prod.mk b c)`.
Given `p : Prod α β`, `p.1 : α` and `p.2 : β`. They are short for `Prod.fst p`
and `Prod.snd p` respectively. You can also write `p.fst` and `p.snd`.
For more information: [Constructors with Arguments](https://lean-lang.org/theorem_proving_in_lean4/inductive_types.html?highlight=Prod#constructors-with-arguments)
-/
```

### `heq_of_eq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem heq_of_eq (h : a = a') : HEq a a' :=
  Eq.subst h (HEq.refl a)
```
