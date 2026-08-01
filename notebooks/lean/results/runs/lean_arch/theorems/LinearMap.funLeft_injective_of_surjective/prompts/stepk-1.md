## Current goal
```
⊢ Injective ⇑(funLeft R M f)
```

## Full tactic state
```
R : Type u_1
R₁ : Type u_2
R₂ : Type u_3
R₃ : Type u_4
R₄ : Type u_5
S : Type u_6
K : Type u_7
K₂ : Type u_8
M : Type u_9
M' : Type u_10
M₁ : Type u_11
M₂ : Type u_12
M₃ : Type u_13
M₄ : Type u_14
N : Type u_15
N₂ : Type u_16
ι : Type u_17
V : Type u_18
V₂ : Type u_19
inst✝² : Semiring R
inst✝¹ : AddCommMonoid M
inst✝ : Module R M
m : Type u_20
n : Type u_21
p : Type u_22
f : m → n
hf : Surjective f
g : n → m
hg : Function.RightInverse g f
this : LeftInverse ⇑(funLeft R M g) ⇑(funLeft R M f)
⊢ Injective ⇑(funLeft R M f)
```
