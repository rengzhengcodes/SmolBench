## Current goal
```
⊢ -a ≤ b - c
```

## Full tactic state
```
a b c : Int
h✝ : c ≤ a + b
h : -a ≤ -c + b
⊢ -a ≤ b - c
```

## Proof so far (1 tactic)
```lean
have h := Int.le_neg_add_of_add_le (Int.sub_left_le_of_le_add h)
```

## Theorem
`Int.neg_le_sub_left_of_le_add` in `.lake/packages/std/Std/Data/Int/Order.lean`

## Premises used in the next tactic
- `Int.add_comm`

## Premise signatures
### `Int.add_comm` (commanddeclaration)
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
```

## Premise full source (with proof)
### `Int.add_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
  | ofNat n, ofNat m => by simp [Nat.add_comm]
  | ofNat _, -[_+1]  => rfl
  | -[_+1],  ofNat _ => rfl
  | -[_+1],  -[_+1]  => by simp [Nat.add_comm]
```

## Transitive premise context (1-hop, 2/2 premises, ≈397 tokens)
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

### `Nat.add_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_comm : ∀ (n m : Nat), n + m = m + n
  | n, 0   => Eq.symm (Nat.zero_add n)
  | n, m+1 => by
    have : succ (n + m) = succ (m + n) := by apply congrArg; apply Nat.add_comm
    rw [succ_add m n]
    apply this
```
