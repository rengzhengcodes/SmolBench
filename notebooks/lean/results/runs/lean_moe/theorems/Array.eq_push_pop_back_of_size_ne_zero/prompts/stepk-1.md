## Current goal
```
⊢ as[size (pop as)] = get as { val := size (pop as), isLt := h }
```

## Full tactic state
```
case refl
α : Type u_1
inst✝ : Inhabited α
as : Array α
h✝ : size as ≠ 0
h : size (pop as) < size as
h' : size (pop as) < size (push (pop as) (back as))
hlt : ¬size (pop as) < size (pop as)
⊢ as[size (pop as)] = get as { val := size (pop as), isLt := h }
```
