## Current goal
```
⊢ ltTrichotomy x y p q r = s ↔ x < y ∧ p = s ∨ x = y ∧ q = s ∨ y < x ∧ r = s
```

## Full tactic state
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
r✝ : α → α → Prop
inst✝ : LinearOrder α
P : Sort u_3
x y : α
p q r s : P
h : y < x
⊢ ltTrichotomy x y p q r = s ↔ x < y ∧ p = s ∨ x = y ∧ q = s ∨ y < x ∧ r = s
```
