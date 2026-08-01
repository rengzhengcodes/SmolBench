## Current goal
```
⊢ ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p)
```

## Full tactic state
```
R✝ : Type u_1
p✝ m n : ℕ
inst✝⁶ : CommSemiring R✝
inst✝⁵ : ExpChar R✝ p✝
inst✝⁴ : PerfectRing R✝ p✝
R : Type u_2
p : ℕ
inst✝³ : CommSemiring R
inst✝² : Fact (Nat.Prime p)
inst✝¹ : CharP R p
inst✝ : PerfectRing R p
f : R[X]
⊢ ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p)
```

## Proof so far (1 tactic)
```lean
rw [polynomial_expand_eq]
```

## Theorem
`not_irreducible_expand` in `Mathlib/FieldTheory/Perfect.lean`

## Premises used in the next tactic
- `not_irreducible_pow`
- `Fact.out`
- `Nat.Prime.ne_one`

## Premise signatures
### `not_irreducible_pow` (commanddeclaration)
```lean
theorem not_irreducible_pow {α} [Monoid α] {x : α} {n : ℕ} (hn : n ≠ 1) :
    ¬ Irreducible (x ^ n)
```

### `Fact.out`
_(not found in premise corpus)_

### `Nat.Prime.ne_one` (commanddeclaration)
```lean
theorem Prime.ne_one {p : ℕ} (hp : p.Prime) : p ≠ 1
```

## Premise full source (with proof)
### `not_irreducible_pow` (commanddeclaration) at `Mathlib/Algebra/Associated.lean`
```lean
theorem not_irreducible_pow {α} [Monoid α] {x : α} {n : ℕ} (hn : n ≠ 1) :
    ¬ Irreducible (x ^ n) := by
  cases n with
  | zero => simp
  | succ n =>
    intro ⟨h₁, h₂⟩
    have := h₂ _ _ (pow_succ _ _)
    rw [isUnit_pow_iff (Nat.succ_ne_succ.mp hn), or_self] at this
    exact h₁ (this.pow _)
```

### `Fact.out`
_(not found in premise corpus)_

### `Nat.Prime.ne_one` (commanddeclaration) at `Mathlib/Data/Nat/Prime.lean`
```lean
theorem Prime.ne_one {p : ℕ} (hp : p.Prime) : p ≠ 1 :=
  hp.one_lt.ne'
```

## Transitive premise context (1-hop, 6/6 premises, ≈675 tokens)
### `Monoid` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
/-- A `Monoid` is a `Semigroup` with an element `1` such that `1 * a = a * 1 = a`. -/
@[to_additive]
class Monoid (M : Type u) extends Semigroup M, MulOneClass M where
  /-- Raising to the power of a natural number. -/
  protected npow : ℕ → M → M := npowRec
  /-- Raising to the power `(0 : ℕ)` gives `1`. -/
  protected npow_zero : ∀ x, npow 0 x = 1 := by intros; rfl
  /-- Raising to the power `(n + 1 : ℕ)` behaves as expected. -/
  protected npow_succ : ∀ (n : ℕ) (x), npow (n + 1) x = x * npow n x := by intros; rfl
```

### `Irreducible` (commanddeclaration) at `Mathlib/Algebra/Associated.lean`
```lean
/-- `Irreducible p` states that `p` is non-unit and only factors into units.

We explicitly avoid stating that `p` is non-zero, this would require a semiring. Assuming only a
monoid allows us to reuse irreducible for associated elements.
-/
structure Irreducible [Monoid α] (p : α) : Prop where
  /-- `p` is not a unit -/
  not_unit : ¬IsUnit p
  /-- if `p` factors then one factor is a unit -/
  isUnit_or_isUnit' : ∀ a b, p = a * b → IsUnit a ∨ IsUnit b
```

### `pow_succ` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive succ_nsmul]
theorem pow_succ (a : M) (n : ℕ) : a ^ (n + 1) = a * a ^ n :=
  Monoid.npow_succ n a
```

### `isUnit_pow_iff` (lemma) at `Mathlib/Algebra/Group/Commute/Units.lean`
```lean
@[to_additive (attr := simp)] lemma isUnit_pow_iff (hn : n ≠ 0) : IsUnit (a ^ n) ↔ IsUnit a :=
  ⟨fun ⟨u, hu⟩ ↦ (u.ofPow a hn hu.symm).isUnit, IsUnit.pow n⟩
```

### `or_self` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem or_self (p : Prop) : (p ∨ p) = p := propext ⟨fun | .inl h | .inr h => h, .inl⟩
```

### `Prime.ne_one` (commanddeclaration) at `Mathlib/Algebra/Associated.lean`
```lean
theorem ne_one : p ≠ 1 := fun h => hp.2.1 (h.symm ▸ isUnit_one)
```
