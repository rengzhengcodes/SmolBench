## Current goal
```
⊢ succ a = succ b ↔ a = b
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝¹ : PartialOrder α
inst✝ : SuccOrder α
a b : α
ha : ¬IsMax a
hb : ¬IsMax b
⊢ succ a = succ b ↔ a = b
```
