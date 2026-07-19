## Current goal
```
⊢ (LinearEquiv.symm (reindex R (fun x => M) e)) x = (reindex R (fun x => M) e.symm) x
```

## Full tactic state
```
case h
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝⁷ : CommSemiring R
R₁ : Type u_5
R₂ : Type u_6
s : ι → Type u_7
inst✝⁶ : (i : ι) → AddCommMonoid (s i)
inst✝⁵ : (i : ι) → Module R (s i)
M : Type u_8
inst✝⁴ : AddCommMonoid M
inst✝³ : Module R M
E : Type u_9
inst✝² : AddCommMonoid E
inst✝¹ : Module R E
F : Type u_10
inst✝ : AddCommMonoid F
e : ι ≃ ι₂
x : ⨂[R] (i : ι₂), M
⊢ (LinearEquiv.symm (reindex R (fun x => M) e)) x = (reindex R (fun x => M) e.symm) x
```
