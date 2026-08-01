## Current goal
```
⊢ (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x =
    (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) x
```

## Full tactic state
```
case h.ι_mul
R : Type u_1
M : Type u_2
N : Type u_3
N' : Type u_4
inst✝⁶ : CommRing R
inst✝⁵ : AddCommGroup M
inst✝⁴ : AddCommGroup N
inst✝³ : AddCommGroup N'
inst✝² : Module R M
inst✝¹ : Module R N
inst✝ : Module R N'
g : N →ₗ[R] N'
x : CliffordAlgebra 0
m : M
hx :
  ∀ (f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N),
    (liftAlternating fun i => (LinearMap.compAlternatingMap g) (f i)) x = g ((liftAlternating f) x)
f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N
⊢ (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x =
    (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) x
```
