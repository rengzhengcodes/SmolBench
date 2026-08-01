## Current goal
```
⊢ Tendsto (fun x => f ↑x) atBot l ↔ Tendsto (f ∘ Subtype.val) atBot l
```

## Full tactic state
```
ι : Type u_1
ι' : Type u_2
α : Type u_3
β : Type u_4
γ : Type u_5
inst✝¹ : SemilatticeInf α
inst✝ : NoMinOrder α
a : α
f : α → β
l : Filter β
⊢ Tendsto (fun x => f ↑x) atBot l ↔ Tendsto (f ∘ Subtype.val) atBot l
```
