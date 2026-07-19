## Current goal
```
⊢ dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = map e (dualCoannihilator p)
```

## Full tactic state
```
R : Type u_1
M : Type u_2
N : Type u_3
inst✝⁵ : CommRing R
inst✝⁴ : AddCommGroup M
inst✝³ : Module R M
inst✝² : AddCommGroup N
inst✝¹ : Module R N
inst✝ : IsReflexive R M
e : N ≃ₗ[R] Dual R M
p : Submodule R (Dual R N)
this : IsReflexive R N
⊢ dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = map e (dualCoannihilator p)
```

## Proof so far (1 tactic)
```lean
have : IsReflexive R N := e.isReflexive_of_equiv_dual_of_isReflexive
```

## Theorem
`Submodule.dualAnnihilator_map_linearEquiv_flip_symm` in `Mathlib/LinearAlgebra/PerfectPairing.lean`

## Premises used in the next tactic
- `Submodule.map_dualCoannihilator_linearEquiv_flip`
- `LinearEquiv.flip_flip`

## Premise signatures
### `Submodule.map_dualCoannihilator_linearEquiv_flip` (lemma)
```lean
@[simp]
lemma map_dualCoannihilator_linearEquiv_flip (p : Submodule R (Dual R M)) :
    p.dualCoannihilator.map e.flip = (p.map e.symm).dualAnnihilator
```

### `LinearEquiv.flip_flip` (lemma)
```lean
@[simp] lemma flip_flip (h : IsReflexive R N := isReflexive_of_equiv_dual_of_isReflexive e) :
    e.flip.flip = e
```

## Premise full source (with proof)
### `Submodule.map_dualCoannihilator_linearEquiv_flip` (lemma) at `Mathlib/LinearAlgebra/PerfectPairing.lean`
```lean
@[simp]
lemma map_dualCoannihilator_linearEquiv_flip (p : Submodule R (Dual R M)) :
    p.dualCoannihilator.map e.flip = (p.map e.symm).dualAnnihilator := by
  have : IsReflexive R N := e.isReflexive_of_equiv_dual_of_isReflexive
  suffices (p.map e.symm).dualAnnihilator.map e.flip.symm =
      (p.dualCoannihilator.map e.flip).map e.flip.symm by
    exact (Submodule.map_injective_of_injective e.flip.symm.injective this).symm
  erw [← dualCoannihilator_map_linearEquiv_flip, flip_flip, ← map_comp, ← map_comp]
  simp [-coe_toLinearMap_flip]
```

### `LinearEquiv.flip_flip` (lemma) at `Mathlib/LinearAlgebra/PerfectPairing.lean`
```lean
@[simp] lemma flip_flip (h : IsReflexive R N := isReflexive_of_equiv_dual_of_isReflexive e) :
    e.flip.flip = e := by
  ext; rfl

/-- If `M` is reflexive then a linear equivalence `N ≃ Dual R M` is a perfect pairing. -/
```
