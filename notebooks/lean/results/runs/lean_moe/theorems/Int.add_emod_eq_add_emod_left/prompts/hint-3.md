## Current goal
```
⊢ (i + m) % n = (i + k) % n
```

## Full tactic state
```
m n k i : Int
H : m % n = k % n
⊢ (i + m) % n = (i + k) % n
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Int.add_emod_eq_add_emod_left` in `.lake/packages/std/Std/Data/Int/DivMod.lean`

## Premises used in the next tactic
- `Int.add_comm`
- `Int.add_emod_eq_add_emod_right`
- `Int.add_comm`

## Premise signatures
### `Int.add_comm` (commanddeclaration)
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
```

### `Int.add_emod_eq_add_emod_right` (commanddeclaration)
```lean
theorem add_emod_eq_add_emod_right {m n k : Int} (i : Int)
    (H : m % n = k % n) : (m + i) % n = (k + i) % n
```

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

### `Int.add_emod_eq_add_emod_right` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/DivModLemmas.lean`
```lean
theorem add_emod_eq_add_emod_right {m n k : Int} (i : Int)
    (H : m % n = k % n) : (m + i) % n = (k + i) % n := by
  rw [← emod_add_emod, ← emod_add_emod k, H]
```

### `Int.add_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
  | ofNat n, ofNat m => by simp [Nat.add_comm]
  | ofNat _, -[_+1]  => rfl
  | -[_+1],  ofNat _ => rfl
  | -[_+1],  -[_+1]  => by simp [Nat.add_comm]
```

## Transitive premise context (1-hop, 3/3 premises, ≈519 tokens)
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

### `Int.emod_add_emod` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/DivModLemmas.lean`
```lean
@[simp] theorem emod_add_emod (m n k : Int) : (m % n + k) % n = (m + k) % n := by
  have := (add_mul_emod_self_left (m % n + k) n (m / n)).symm
  rwa [Int.add_right_comm, emod_add_ediv] at this
```
