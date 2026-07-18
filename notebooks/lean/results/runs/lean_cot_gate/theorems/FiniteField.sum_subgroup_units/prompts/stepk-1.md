## Current goal
```
⊢ ∑ x : ↥G, ↑↑x = 0
```

## Full tactic state
```
case neg
K : Type u_1
R : Type u_2
inst✝³ : Ring K
inst✝² : NoZeroDivisors K
G : Subgroup Kˣ
inst✝¹ : Fintype ↥G
inst✝ : Decidable (G = ⊥)
G_bot : ¬G = ⊥
⊢ ∑ x : ↥G, ↑↑x = 0
```
