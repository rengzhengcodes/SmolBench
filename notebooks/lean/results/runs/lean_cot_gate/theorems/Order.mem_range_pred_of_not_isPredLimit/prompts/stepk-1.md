## Current goal
```
⊢ a ∈ range pred
```

## Full tactic state
```
case intro
α : Type u_1
inst✝¹ : PartialOrder α
inst✝ : PredOrder α
a b✝ : α
C : α → Sort u_2
h : ¬IsPredLimit a
b : α
hb : ¬IsMin b ∧ pred b = a
⊢ a ∈ range pred
```
