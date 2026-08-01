## Current goal
```
⊢ Rat.inv { num := num✝, den := den✝, den_nz := den_nz✝, reduced := reduced✝ } = ↑den✝ * g /. (num✝ * g)
```

## Full tactic state
```
case mk'.intro.intro.intro
num✝ : Int
den✝ : Nat
den_nz✝ : den✝ ≠ 0
reduced✝ : Nat.Coprime (Int.natAbs num✝) den✝
g : Int
zg : g ≠ 0
z : ¬↑den✝ * g = 0
e : num✝ * g /. (↑den✝ * g) = { num := num✝, den := den✝, den_nz := den_nz✝, reduced := reduced✝ }
⊢ Rat.inv { num := num✝, den := den✝, den_nz := den_nz✝, reduced := reduced✝ } = ↑den✝ * g /. (num✝ * g)
```

## Proof so far (4 tactics)
```lean
if z : d = 0 then simp [z] else
cases e : n /. d; rcases divInt_num_den z e with ⟨g, zg, rfl, rfl⟩
simp [inv_def, divInt_mul_right zg]
simp [z]
cases e : n /. d
rcases divInt_num_den z e with ⟨g, zg, rfl, rfl⟩
```

## Theorem
`Rat.inv_divInt` in `.lake/packages/std/Std/Data/Rat/Lemmas.lean`

## Premises used in the next tactic
- `Rat.inv_def`
- `Rat.divInt_mul_right`

## Premise signatures
### `Rat.inv_def` (commanddeclaration)
```lean
theorem inv_def (a : Rat) : a.inv = a.den /. a.num
```

### `Rat.divInt_mul_right` (commanddeclaration)
```lean
theorem divInt_mul_right {a : Int} (a0 : a ≠ 0) : (n * a) /. (d * a) = n /. d
```

## Premise full source (with proof)
### `Rat.inv_def` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem inv_def (a : Rat) : a.inv = a.den /. a.num := by
  unfold Rat.inv; split
  · next h => rw [mk_eq_divInt, ← Int.natAbs_neg,
      Int.natAbs_of_nonneg (Int.le_of_lt <| Int.neg_pos_of_neg h), neg_divInt_neg]
  split
  · next h => rw [mk_eq_divInt, Int.natAbs_of_nonneg (Int.le_of_lt h)]
  · next h₁ h₂ =>
    apply (divInt_self _).symm.trans
    simp [Int.le_antisymm (Int.not_lt.1 h₂) (Int.not_lt.1 h₁)]
```

### `Rat.divInt_mul_right` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem divInt_mul_right {a : Int} (a0 : a ≠ 0) : (n * a) /. (d * a) = n /. d := by
  simp [← divInt_mul_left (d := d) a0, Int.mul_comm]
```

## Transitive premise context (1-hop, 13/13 premises, ≈1717 tokens)
### `Rat` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Basic.lean`
```lean
/--
Rational numbers, implemented as a pair of integers `num / den` such that the
denominator is positive and the numerator and denominator are coprime.
-/
-- `Rat` is not tagged with the `ext` attribute, since this is more often than not undesirable
structure Rat where
  /-- Constructs a rational number from components.
  We rename the constructor to `mk'` to avoid a clash with the smart constructor. -/
  mk' ::
  /-- The numerator of the rational number is an integer. -/
  num : Int
  /-- The denominator of the rational number is a natural number. -/
  den : Nat := 1
  /-- The denominator is nonzero. -/
  den_nz : den ≠ 0 := by decide
  /-- The numerator and denominator are coprime: it is in "reduced form". -/
  reduced : num.natAbs.Coprime den := by decide
  deriving DecidableEq
```

### `Rat.inv` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Basic.lean`
```lean
/--
The inverse of a rational number. Note: `inv 0 = 0`. (This definition is `@[irreducible]`
because you don't want to unfold it. Use `Rat.inv_def` instead.)
-/
@[irreducible] protected def inv (a : Rat) : Rat :=
  if h : a.num < 0 then
    { num := -a.den, den := a.num.natAbs
      den_nz := Nat.ne_of_gt (Int.natAbs_pos.2 (Int.ne_of_lt h))
      reduced := Int.natAbs_neg a.den ▸ a.reduced.symm }
  else if h : a.num > 0 then
    { num := a.den, den := a.num.natAbs
      den_nz := Nat.ne_of_gt (Int.natAbs_pos.2 (Int.ne_of_gt h))
      reduced := a.reduced.symm }
  else
    a

/-- Division of rational numbers. Note: `div a 0 = 0`. -/
```

### `Rat.mk_eq_divInt` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem mk_eq_divInt (num den nz c) : ⟨num, den, nz, c⟩ = num /. (den : Nat) := by
  simp [mk_eq_mkRat]
```

### `Int.natAbs_neg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Order.lean`
```lean
@[simp] theorem natAbs_neg : ∀ (a : Int), natAbs (-a) = natAbs a
  | 0      => rfl
  | succ _ => rfl
  | -[_+1] => rfl
```

### `Int.natAbs_of_nonneg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Order.lean`
```lean
theorem natAbs_of_nonneg {a : Int} (H : 0 ≤ a) : (natAbs a : Int) = a :=
  match a, eq_ofNat_of_zero_le H with
  | _, ⟨_, rfl⟩ => rfl
```

### `Int.le_of_lt` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Order.lean`
```lean
protected theorem le_of_lt {a b : Int} (h : a < b) : a ≤ b :=
  let ⟨_, hn⟩ := lt.dest h; le.intro _ hn
```

### `Int.neg_pos_of_neg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Order.lean`
```lean
protected theorem neg_pos_of_neg {a : Int} (h : a < 0) : 0 < -a := by
  have : -0 < -a := Int.neg_lt_neg h
  rwa [Int.neg_zero] at this
```

### `Rat.neg_divInt_neg` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem neg_divInt_neg (num den) : -num /. -den = num /. den := by
  match den with
  | Nat.succ n => simp [divInt, Int.neg_ofNat_succ, normalize_eq_mkRat, Int.neg_neg]
  | 0 => rfl
  | Int.negSucc n => simp [divInt, Int.neg_negSucc, normalize_eq_mkRat, Int.neg_neg]
```

### `Rat.divInt_self` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem divInt_self (a : Rat) : a.num /. a.den = a := by rw [divInt_ofNat, mkRat_self]
```

### `Int.le_antisymm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Order.lean`
```lean
protected theorem le_antisymm {a b : Int} (h₁ : a ≤ b) (h₂ : b ≤ a) : a = b := by
  let ⟨n, hn⟩ := le.dest h₁; let ⟨m, hm⟩ := le.dest h₂
  have := hn; rw [← hm, Int.add_assoc, ← ofNat_add] at this
  have := Int.ofNat.inj <| Int.add_left_cancel <| this.trans (Int.add_zero _).symm
  rw [← hn, Nat.eq_zero_of_add_eq_zero_left this, ofNat_zero, Int.add_zero a]
```

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
