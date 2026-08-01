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
