## Current goal
```
⊢ PartiallyWellOrderedOn (insert a s) r ↔ PartiallyWellOrderedOn s r
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
r : α → α → Prop
r' : β → β → Prop
f : α → β
s t : Set α
a : α
inst✝ : IsRefl α r
⊢ PartiallyWellOrderedOn (insert a s) r ↔ PartiallyWellOrderedOn s r
```
