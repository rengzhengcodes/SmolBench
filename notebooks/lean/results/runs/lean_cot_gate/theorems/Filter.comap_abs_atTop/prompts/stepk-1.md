## Current goal
```
⊢ x ∈ Iic (a, b).1 ∪ Ici (a, b).2
```

## Full tactic state
```
case mk
ι : Type u_1
ι' : Type u_2
α : Type u_3
β : Type u_4
γ : Type u_5
inst✝ : LinearOrderedAddCommGroup α
a b x : α
hx : x ≤ a ∧ x ≤ -b ∨ -a ≤ x ∧ b ≤ x
⊢ x ∈ Iic (a, b).1 ∪ Ici (a, b).2
```
