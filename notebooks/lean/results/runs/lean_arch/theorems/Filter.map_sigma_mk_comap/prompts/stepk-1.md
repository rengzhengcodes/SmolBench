## Current goal
```
⊢ Sigma.mk a '' (g a ⁻¹' id x✝) = Sigma.map f g ⁻¹' (Sigma.mk (f a) '' id x✝)
```

## Full tactic state
```
case h.e'_5.h
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
π : α → Type u_6
π' : β → Type u_7
f : α → β
hf : Function.Injective f
g : (a : α) → π a → π' (f a)
a : α
l : Filter (π' (f a))
x✝ : Set (π' (f a))
⊢ Sigma.mk a '' (g a ⁻¹' id x✝) = Sigma.map f g ⁻¹' (Sigma.mk (f a) '' id x✝)
```
