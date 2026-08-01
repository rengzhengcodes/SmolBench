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

## Transitive premise context (1-hop, 9/9 premises, ≈893 tokens)
### `Submodule` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Basic.lean`
```lean
/-- A submodule of a module is one which is closed under vector operations.
  This is a sufficient condition for the subset of vectors in the submodule
  to themselves form a module. -/
structure Submodule (R : Type u) (M : Type v) [Semiring R] [AddCommMonoid M] [Module R M] extends
  AddSubmonoid M, SubMulAction R M : Type v
```

### `Submodule.dualAnnihilator` (commanddeclaration) at `Mathlib/LinearAlgebra/Dual.lean`
```lean
/-- The `dualAnnihilator` of a submodule `W` is the set of linear maps `φ` such
  that `φ w = 0` for all `w ∈ W`. -/
def dualAnnihilator {R : Type u} {M : Type v} [CommSemiring R] [AddCommMonoid M] [Module R M]
    (W : Submodule R M) : Submodule R <| Module.Dual R M :=
-- Porting note (#11036): broken dot notation lean4#1910 LinearMap.ker
  LinearMap.ker W.dualRestrict
```

### `Module.IsReflexive` (commanddeclaration) at `Mathlib/LinearAlgebra/Dual.lean`
```lean
/-- A reflexive module is one for which the natural map to its double dual is a bijection.

Any finitely-generated free module (and thus any finite-dimensional vector space) is reflexive.
See `Module.IsReflexive.of_finite_of_free`. -/
class IsReflexive : Prop where
  /-- A reflexive module is one for which the natural map to its double dual is a bijection. -/
  bijective_dual_eval' : Bijective (Dual.eval R M)
```

### `Lean.Parser.Term.suffices` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
@[builtin_term_parser] def «suffices» := leading_parser:leadPrec
  withPosition ("suffices " >> sufficesDecl) >> optSemicolon termParser
```

### `Submodule.map_injective_of_injective` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Map.lean`
```lean
theorem map_injective_of_injective : Function.Injective (map f) :=
  (gciMapComap hf).l_injective
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `Submodule.dualCoannihilator_map_linearEquiv_flip` (lemma) at `Mathlib/LinearAlgebra/PerfectPairing.lean`
```lean
@[simp]
lemma dualCoannihilator_map_linearEquiv_flip (p : Submodule R M) :
    (p.map e.flip).dualCoannihilator = p.dualAnnihilator.map e.symm := by
  ext; simp [LinearEquiv.symm_apply_eq, Submodule.mem_dualCoannihilator]
```

### `LinearEquiv.coe_toLinearMap_flip` (lemma) at `Mathlib/LinearAlgebra/PerfectPairing.lean`
```lean
@[simp] lemma coe_toLinearMap_flip : e.flip = (↑e : N →ₗ[R] Dual R M).flip := rfl
```

### `LinearEquiv.isReflexive_of_equiv_dual_of_isReflexive` (lemma) at `Mathlib/LinearAlgebra/PerfectPairing.lean`
```lean
/-- If `N` is in perfect pairing with `M`, then it is reflexive. -/
lemma isReflexive_of_equiv_dual_of_isReflexive : IsReflexive R N := by
  constructor
  rw [← trans_dualMap_symm_flip e]
  exact LinearEquiv.bijective _
```
