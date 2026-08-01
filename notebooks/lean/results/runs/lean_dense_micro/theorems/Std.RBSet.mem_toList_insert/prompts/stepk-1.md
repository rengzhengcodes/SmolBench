## Current goal
```
⊢ v' ∈ toList (insert t v) ↔ v' ∈ toList t ∧ find? t v ≠ some v' ∨ v' = v
```

## Full tactic state
```
α : Type u_1
cmp : α → α → Ordering
v' v : α
inst✝ : TransCmp cmp
t : RBSet α cmp
ht₁ : RBNode.Ordered cmp t.val
w✝¹ : RBColor
w✝ : Nat
ht₂ : RBNode.Balanced t.val w✝¹ w✝
⊢ v' ∈ toList (insert t v) ↔ v' ∈ toList t ∧ find? t v ≠ some v' ∨ v' = v
```
