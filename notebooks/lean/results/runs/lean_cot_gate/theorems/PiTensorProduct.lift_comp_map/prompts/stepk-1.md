## Current goal
```
⊢ (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ =
    (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝
```

## Full tactic state
```
case H.H
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝¹¹ : CommSemiring R
R₁ : Type u_5
R₂ : Type u_6
s : ι → Type u_7
inst✝¹⁰ : (i : ι) → AddCommMonoid (s i)
inst✝⁹ : (i : ι) → Module R (s i)
M : Type u_8
inst✝⁸ : AddCommMonoid M
inst✝⁷ : Module R M
E : Type u_9
inst✝⁶ : AddCommMonoid E
inst✝⁵ : Module R E
F : Type u_10
inst✝⁴ : AddCommMonoid F
t : ι → Type u_11
t' : ι → Type u_12
inst✝³ : (i : ι) → AddCommMonoid (t i)
inst✝² : (i : ι) → Module R (t i)
inst✝¹ : (i : ι) → AddCommMonoid (t' i)
inst✝ : (i : ι) → Module R (t' i)
g : (i : ι) → t i →ₗ[R] t' i
f : (i : ι) → s i →ₗ[R] t i
h : MultilinearMap R t E
x✝ : (i : ι) → s i
⊢ (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ =
    (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝
```
