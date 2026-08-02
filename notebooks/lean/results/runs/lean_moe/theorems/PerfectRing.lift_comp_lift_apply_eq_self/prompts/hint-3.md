## Current goal
```
⊢ (lift j i p) ((lift i j p) x) = x
```

## Full tactic state
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹² : CommRing K
inst✝¹¹ : CommRing L
inst✝¹⁰ : CommRing M
inst✝⁹ : CommRing N
i : K →+* L
j : K →+* M
k : K →+* N
f : L →+* M
g : L →+* N
p : ℕ
inst✝⁸ : ExpChar K p
inst✝⁷ : ExpChar L p
inst✝⁶ : ExpChar M p
inst✝⁵ : ExpChar N p
inst✝⁴ : PerfectRing M p
inst✝³ : IsPRadical i p
inst✝² : PerfectRing N p
inst✝¹ : IsPRadical j p
inst✝ : PerfectRing L p
x : L
⊢ (lift j i p) ((lift i j p) x) = x
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`PerfectRing.lift_comp_lift_apply_eq_self` in `Mathlib/FieldTheory/IsPerfectClosure.lean`

## Premises used in the next tactic
- `PerfectRing.lift_comp_lift_apply`
- `PerfectRing.lift_self_apply`

## Premise signatures
### `PerfectRing.lift_comp_lift_apply` (commanddeclaration)
```lean
@[simp]
theorem lift_comp_lift_apply (x : L) : lift j k p (lift i j p x) = lift i k p x
```

### `PerfectRing.lift_self_apply` (commanddeclaration)
```lean
theorem lift_self_apply [PerfectRing L p] (x : L) : lift i i p x = x
```

## Premise full source (with proof)
### `PerfectRing.lift_comp_lift_apply` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
@[simp]
theorem lift_comp_lift_apply (x : L) : lift j k p (lift i j p x) = lift i k p x :=
  congr($(lift_comp_lift i j k p) x)
```

### `PerfectRing.lift_self_apply` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
theorem lift_self_apply [PerfectRing L p] (x : L) : lift i i p x = x := liftAux_self_apply i p x
```

## Transitive premise context (1-hop, 3/3 premises, ≈467 tokens)
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

### `PerfectRing` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
/-- A perfect ring of characteristic `p` (prime) in the sense of Serre.

NB: This is not related to the concept with the same name introduced by Bass (related to projective
covers of modules). -/
class PerfectRing (R : Type*) (p : ℕ) [CommSemiring R] [ExpChar R p] : Prop where
  /-- A ring is perfect if the Frobenius map is bijective. -/
  bijective_frobenius : Bijective <| frobenius R p
```

### `PerfectRing.liftAux_self_apply` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
@[simp]
theorem liftAux_self_apply [PerfectRing L p] (x : L) : liftAux i i p x = x := by
  rw [liftAux, Classical.choose_spec (lift_aux i p x), ← iterateFrobenius_def,
    ← iterateFrobeniusEquiv_apply, RingEquiv.symm_apply_apply]
```
