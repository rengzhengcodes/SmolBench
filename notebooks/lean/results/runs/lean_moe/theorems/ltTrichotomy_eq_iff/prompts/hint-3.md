## Current goal
```
⊢ ltTrichotomy x y p q r = s ↔ x < y ∧ p = s ∨ x = y ∧ q = s ∨ y < x ∧ r = s
```

## Full tactic state
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
r✝ : α → α → Prop
inst✝ : LinearOrder α
P : Sort u_3
x y : α
p q r s : P
h : y < x
⊢ ltTrichotomy x y p q r = s ↔ x < y ∧ p = s ∨ x = y ∧ q = s ∨ y < x ∧ r = s
```

## Proof so far (3 tactics)
```lean
refine ltByCases x y (fun h => ?_) (fun h => ?_) (fun h => ?_)
simp only [ltTrichotomy_lt, false_and, true_and, or_false, h, h.not_lt, h.ne]
simp only [ltTrichotomy_eq, false_and, true_and, or_false, false_or, h, lt_irrefl]
```

## Theorem
`ltTrichotomy_eq_iff` in `Mathlib/Order/Basic.lean`

## Premises used in the next tactic
- `ltTrichotomy_gt`
- `false_and`
- `true_and`
- `false_or`

## Premise signatures
### `ltTrichotomy_gt` (lemma)
```lean
@[simp]
lemma ltTrichotomy_gt (h : y < x) : ltTrichotomy x y p q r = r
```

### `false_and` (commanddeclaration)
```lean
@[simp] theorem false_and (p : Prop) : (False ∧ p) = False
```

### `true_and` (commanddeclaration)
```lean
@[simp] theorem true_and (p : Prop) : (True ∧ p) = p
```

### `false_or` (commanddeclaration)
```lean
@[simp] theorem false_or (p : Prop) : (False ∨ p) = p
```

## Premise full source (with proof)
### `ltTrichotomy_gt` (lemma) at `Mathlib/Order/Basic.lean`
```lean
@[simp]
lemma ltTrichotomy_gt (h : y < x) : ltTrichotomy x y p q r = r := ltByCases_gt h
```

### `false_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem false_and (p : Prop) : (False ∧ p) = False := eq_false (·.1)
```

### `true_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem true_and (p : Prop) : (True ∧ p) = p := propext ⟨(·.2), (⟨trivial, ·⟩)⟩
```

### `false_or` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem false_or (p : Prop) : (False ∨ p) = p := propext ⟨fun (.inr h) => h, .inr⟩
```

## Transitive premise context (1-hop, 4/4 premises, ≈707 tokens)
### `ltTrichotomy` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
/-- Perform a case-split on the ordering of `x` and `y` in a decidable linear order,
non-dependently. -/
abbrev ltTrichotomy (x y : α) (p q r : P) := ltByCases x y (fun _ => p) (fun _ => q) (fun _ => r)
```

### `ltByCases_gt` (lemma) at `Mathlib/Order/Basic.lean`
```lean
@[simp]
lemma ltByCases_gt (h : y < x) {h₁ : x < y → P} {h₂ : x = y → P} {h₃ : y < x → P} :
    ltByCases x y h₁ h₂ h₃ = h₃ h := (dif_neg h.not_lt).trans (dif_pos h)
```

### `eq_false` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
theorem eq_false (h : ¬ p) : p = False :=
  propext ⟨fun h' => absurd h' h, fun h' => False.elim h'⟩
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
