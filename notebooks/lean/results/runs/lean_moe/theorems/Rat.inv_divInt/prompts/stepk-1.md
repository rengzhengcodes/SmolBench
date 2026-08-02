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
