## Current goal
```
⊢ i < size as
```

## Full tactic state
```
case intro.h
α : Type u_1
β : Type u_2
f : α → β
as : Array α
i : Nat
h : i < size (map f as)
eq : size (map f as) = size as
w : ∀ (i : Nat) (h : i < size as), (map f as)[i] = f as[{ val := i, isLt := h }]
⊢ i < size as
```
