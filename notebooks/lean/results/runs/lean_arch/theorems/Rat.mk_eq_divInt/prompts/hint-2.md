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
