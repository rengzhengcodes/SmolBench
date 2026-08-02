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
