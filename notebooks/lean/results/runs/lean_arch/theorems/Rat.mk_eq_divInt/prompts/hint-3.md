## Current goal
```
⊢ { num := num, den := den, den_nz := nz, reduced := c } = num /. ↑den
```

## Full tactic state
```
num : Int
den : Nat
nz : den ≠ 0
c : Nat.Coprime (Int.natAbs num) den
⊢ { num := num, den := den, den_nz := nz, reduced := c } = num /. ↑den
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Rat.mk_eq_divInt` in `.lake/packages/std/Std/Data/Rat/Lemmas.lean`

## Premises used in the next tactic
- `Rat.mk_eq_mkRat`

## Premise signatures
### `Rat.mk_eq_mkRat` (commanddeclaration)
```lean
theorem mk_eq_mkRat (num den nz c) : ⟨num, den, nz, c⟩ = mkRat num den
```

## Premise full source (with proof)
### `Rat.mk_eq_mkRat` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem mk_eq_mkRat (num den nz c) : ⟨num, den, nz, c⟩ = mkRat num den := by
  simp [mk_eq_normalize, normalize_eq_mkRat]
```

## Transitive premise context (1-hop, 3/3 premises, ≈272 tokens)
### `mkRat` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Basic.lean`
```lean
/--
Construct a rational number from a numerator and denominator.
This is a "smart constructor" that divides the numerator and denominator by
the gcd to ensure that the resulting rational number is normalized, and returns
zero if `den` is zero.
-/
def mkRat (num : Int) (den : Nat) : Rat :=
  if den_nz : den = 0 then { num := 0 } else Rat.normalize num den den_nz
```

### `Rat.mk_eq_normalize` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem mk_eq_normalize (num den nz c) : ⟨num, den, nz, c⟩ = normalize num den nz := by
  simp [normalize_eq, c.gcd_eq_one]
```

### `Rat.normalize_eq_mkRat` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem normalize_eq_mkRat {num den} (den_nz) : normalize num den den_nz = mkRat num den := by
  simp [mkRat, den_nz]
```
