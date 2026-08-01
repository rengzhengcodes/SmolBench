## Current goal
```
⊢ n * a /. (d * a) = n /. d
```

## Full tactic state
```
n d a : Int
a0 : a ≠ 0
⊢ n * a /. (d * a) = n /. d
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Rat.divInt_mul_right` in `.lake/packages/std/Std/Data/Rat/Lemmas.lean`

## Premises used in the next tactic
- `Rat.divInt_mul_left`
- `Int.mul_comm`

## Premise signatures
### `Rat.divInt_mul_left` (commanddeclaration)
```lean
theorem divInt_mul_left {a : Int} (a0 : a ≠ 0) : (a * n) /. (a * d) = n /. d
```

### `Int.mul_comm` (commanddeclaration)
```lean
protected theorem mul_comm (a b : Int) : a * b = b * a
```

## Premise full source (with proof)
### `Rat.divInt_mul_left` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem divInt_mul_left {a : Int} (a0 : a ≠ 0) : (a * n) /. (a * d) = n /. d := by
  if d0 : d = 0 then simp [d0] else
  simp [divInt_eq_iff (Int.mul_ne_zero a0 d0) d0, Int.mul_assoc, Int.mul_left_comm]
```

### `Int.mul_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem mul_comm (a b : Int) : a * b = b * a := by
  cases a <;> cases b <;> simp [Nat.mul_comm]
```

## Transitive premise context (1-hop, 7/7 premises, ≈883 tokens)
### `Int` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Basic.lean`
```lean
/--
The type of integers. It is defined as an inductive type based on the
natural number type `Nat` featuring two constructors: "a natural
number is an integer", and "the negation of a successor of a natural
number is an integer". The former represents integers between `0`
(inclusive) and `∞`, and the latter integers between `-∞` and `-1`
(inclusive).

This type is special-cased by the compiler. The runtime has a special
representation for `Int` which stores "small" signed numbers directly,
and larger numbers use an arbitrary precision "bignum" library
(usually [GMP](https://gmplib.org/)). A "small number" is an integer
that can be encoded with 63 bits (31 bits on 32-bits architectures).
-/
inductive Int : Type where
  /-- A natural number is an integer (`0` to `∞`). -/
  | ofNat   : Nat → Int
  /-- The negation of the successor of a natural number is an integer
    (`-1` to `-∞`). -/
  | negSucc : Nat → Int
```

### `Rat.divInt_eq_iff` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem divInt_eq_iff (z₁ : d₁ ≠ 0) (z₂ : d₂ ≠ 0) :
    n₁ /. d₁ = n₂ /. d₂ ↔ n₁ * d₂ = n₂ * d₁ := by
  rcases Int.eq_nat_or_neg d₁ with ⟨_, rfl | rfl⟩ <;>
  rcases Int.eq_nat_or_neg d₂ with ⟨_, rfl | rfl⟩ <;>
  simp_all [divInt_neg', Int.ofNat_eq_zero, Int.neg_eq_zero,
    mkRat_eq_iff, Int.neg_mul, Int.mul_neg, Int.eq_neg_comm, eq_comm]
```

### `Int.mul_ne_zero` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem mul_ne_zero {a b : Int} (a0 : a ≠ 0) (b0 : b ≠ 0) : a * b ≠ 0 :=
  Or.rec a0 b0 ∘ Int.mul_eq_zero.mp
```

### `Int.mul_assoc` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem mul_assoc (a b c : Int) : a * b * c = a * (b * c) := by
  cases a <;> cases b <;> cases c <;> simp [Nat.mul_assoc]
```

### `Int.mul_left_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem mul_left_comm (a b c : Int) : a * (b * c) = b * (a * c) := by
  rw [← Int.mul_assoc, ← Int.mul_assoc, Int.mul_comm a]
```

### `mul_comm` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive]
theorem mul_comm : ∀ a b : G, a * b = b * a := CommMagma.mul_comm
```

### `Nat.mul_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem mul_comm : ∀ (n m : Nat), n * m = m * n
  | n, 0      => (Nat.zero_mul n).symm ▸ (Nat.mul_zero n).symm ▸ rfl
  | n, succ m => (mul_succ n m).symm ▸ (succ_mul m n).symm ▸ (Nat.mul_comm n m).symm ▸ rfl
```
