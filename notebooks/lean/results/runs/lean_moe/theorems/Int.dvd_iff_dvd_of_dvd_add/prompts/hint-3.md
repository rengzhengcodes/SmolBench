## Current goal
```
⊢ a ∣ b ↔ a ∣ c
```

## Full tactic state
```
a b c : Int
H : a ∣ b - -c
⊢ a ∣ b ↔ a ∣ c
```

## Proof so far (1 tactic)
```lean
rw [← Int.sub_neg] at H
```

## Theorem
`Int.dvd_iff_dvd_of_dvd_add` in `.lake/packages/std/Std/Data/Int/DivMod.lean`

## Premises used in the next tactic
- `Int.dvd_iff_dvd_of_dvd_sub`
- `Int.dvd_neg`

## Premise signatures
### `Int.dvd_iff_dvd_of_dvd_sub` (commanddeclaration)
```lean
protected theorem dvd_iff_dvd_of_dvd_sub {a b c : Int} (H : a ∣ b - c) : a ∣ b ↔ a ∣ c
```

### `Int.dvd_neg` (commanddeclaration)
```lean
protected theorem dvd_neg {a b : Int} : a ∣ -b ↔ a ∣ b
```

## Premise full source (with proof)
### `Int.dvd_iff_dvd_of_dvd_sub` (commanddeclaration) at `.lake/packages/std/Std/Data/Int/DivMod.lean`
```lean
protected theorem dvd_iff_dvd_of_dvd_sub {a b c : Int} (H : a ∣ b - c) : a ∣ b ↔ a ∣ c :=
  ⟨fun h => Int.sub_sub_self b c ▸ Int.dvd_sub h H,
   fun h => Int.sub_add_cancel b c ▸ Int.dvd_add H h⟩
```

### `Int.dvd_neg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/DivModLemmas.lean`
```lean
protected theorem dvd_neg {a b : Int} : a ∣ -b ↔ a ∣ b := by
  constructor <;> exact fun ⟨k, e⟩ =>
    ⟨-k, by simp [← e, Int.neg_mul, Int.mul_neg, Int.neg_neg]⟩
```

## Transitive premise context (1-hop, 10/10 premises, ≈1080 tokens)
### `dvd_iff_dvd_of_dvd_sub` (commanddeclaration) at `Mathlib/Algebra/Ring/Divisibility/Basic.lean`
```lean
theorem dvd_iff_dvd_of_dvd_sub (h : a ∣ b - c) : a ∣ b ↔ a ∣ c := by
  rw [← sub_add_cancel b c, dvd_add_right h]
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

### `Int.sub_sub_self` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem sub_sub_self (a b : Int) : a - (a - b) = b := by
  simp [Int.sub_eq_add_neg, ← Int.add_assoc]
```

### `Int.dvd_sub` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/DivModLemmas.lean`
```lean
protected theorem dvd_sub : ∀ {a b c : Int}, a ∣ b → a ∣ c → a ∣ b - c
  | _, _, _, ⟨d, rfl⟩, ⟨e, rfl⟩ => ⟨d - e, by rw [Int.mul_sub]⟩
```

### `Int.sub_add_cancel` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
@[simp] protected theorem sub_add_cancel (a b : Int) : a - b + b = a :=
  Int.neg_add_cancel_right a b
```

### `Int.dvd_add` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/DivModLemmas.lean`
```lean
protected theorem dvd_add : ∀ {a b c : Int}, a ∣ b → a ∣ c → a ∣ b + c
  | _, _, _, ⟨d, rfl⟩, ⟨e, rfl⟩ => ⟨d + e, by rw [Int.mul_add]⟩
```

### `dvd_neg` (commanddeclaration) at `Mathlib/Algebra/Ring/Divisibility/Basic.lean`
```lean
/-- An element `a` of a semigroup with a distributive negation divides the negation of an element
`b` iff `a` divides `b`. -/
@[simp]
theorem dvd_neg : a ∣ -b ↔ a ∣ b :=
  -- Porting note: `simpa` doesn't close the goal with `rfl` anymore
  (Equiv.neg _).exists_congr_left.trans <| by simp only [Equiv.neg_symm, Equiv.neg_apply, mul_neg,
                                                neg_inj]; rfl
```

### `Int.neg_mul` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
@[local simp] protected theorem neg_mul (a b : Int) : -a * b = -(a * b) :=
  (Int.neg_mul_eq_neg_mul a b).symm
```

### `Int.mul_neg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
@[local simp] protected theorem mul_neg (a b : Int) : a * -b = -(a * b) :=
  (Int.neg_mul_eq_mul_neg a b).symm
```

### `Int.neg_neg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
@[simp] protected theorem neg_neg : ∀ a : Int, -(-a) = a
  | 0      => rfl
  | succ _ => rfl
  | -[_+1] => rfl
```
