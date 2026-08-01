## Current goal
```
⊢ (((CliffordAlgebra.foldl 0 (LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) ⋯)
          f)
        1 0)
      0 =
    (f 0) 0
```

## Full tactic state
```
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
f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N
⊢ (((CliffordAlgebra.foldl 0 (LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) ⋯)
          f)
        1 0)
      0 =
    (f 0) 0
```
