## Current goal
```
⊢ f (⇑e ∘ ⇑σ) = (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ)
```

## Full tactic state
```
R : Type u_1
inst✝⁶ : CommRing R
M : Type u_2
inst✝⁵ : AddCommGroup M
inst✝⁴ : Module R M
M' : Type u_3
inst✝³ : AddCommGroup M'
inst✝² : Module R M'
ι : Type u_4
inst✝¹ : DecidableEq ι
inst✝ : Fintype ι
e : Basis ι R M
f : M [⋀^ι]→ₗ[R] R
i : ι → ι
h : Injective i
σ : Equiv.Perm ι := Equiv.ofBijective i ⋯
⊢ f (⇑e ∘ ⇑σ) = (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ)
```

## Proof so far (3 tactics)
```lean
refine' Basis.ext_alternating e fun i h => _
let σ : Equiv.Perm ι := Equiv.ofBijective i (Finite.injective_iff_bijective.1 h)
change f (e ∘ σ) = (f e • e.det) (e ∘ σ)
```

## Theorem
`AlternatingMap.eq_smul_basis_det` in `Mathlib/LinearAlgebra/Determinant.lean`

## Premises used in the next tactic
- `AlternatingMap.map_perm`
- `Basis.det_self`

## Premise signatures
### `AlternatingMap.map_perm` (commanddeclaration)
```lean
theorem map_perm [DecidableEq ι] [Fintype ι] (v : ι → M) (σ : Equiv.Perm ι) :
    g (v ∘ σ) = Equiv.Perm.sign σ • g v
```

### `Basis.det_self` (commanddeclaration)
```lean
theorem Basis.det_self : e.det e = 1
```

## Premise full source (with proof)
### `AlternatingMap.map_perm` (commanddeclaration) at `Mathlib/LinearAlgebra/Alternating/Basic.lean`
```lean
theorem map_perm [DecidableEq ι] [Fintype ι] (v : ι → M) (σ : Equiv.Perm ι) :
    g (v ∘ σ) = Equiv.Perm.sign σ • g v := by
  -- Porting note: `apply` → `induction'`
  induction' σ using Equiv.Perm.swap_induction_on' with s x y hxy hI
  · simp
  · -- Porting note: `← Function.comp.assoc` & `-Equiv.Perm.sign_swap'` are required.
    simpa [← Function.comp.assoc, g.map_swap (v ∘ s) hxy,
      Equiv.Perm.sign_swap hxy, -Equiv.Perm.sign_swap'] using hI
```

### `Basis.det_self` (commanddeclaration) at `Mathlib/LinearAlgebra/Determinant.lean`
```lean
theorem Basis.det_self : e.det e = 1 := by simp [e.det_apply]
```
