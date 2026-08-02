## Current goal
```
⊢ (trace R M) ((dualTensorHom R M M) x) = (contractLeft R M) x
```

## Full tactic state
```
R : Type u_1
inst✝¹² : CommRing R
M : Type u_2
inst✝¹¹ : AddCommGroup M
inst✝¹⁰ : Module R M
N : Type u_3
P : Type u_4
inst✝⁹ : AddCommGroup N
inst✝⁸ : Module R N
inst✝⁷ : AddCommGroup P
inst✝⁶ : Module R P
ι : Type u_5
inst✝⁵ : Module.Free R M
inst✝⁴ : Module.Finite R M
inst✝³ : Module.Free R N
inst✝² : Module.Finite R N
inst✝¹ : Module.Free R P
inst✝ : Module.Finite R P
x : Module.Dual R M ⊗[R] M
⊢ (trace R M) ((dualTensorHom R M M) x) = (contractLeft R M) x
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`LinearMap.trace_eq_contract_apply` in `Mathlib/LinearAlgebra/Trace.lean`

## Premises used in the next tactic
- `LinearMap.comp_apply`
- `LinearMap.trace_eq_contract`

## Premise signatures
### `LinearMap.comp_apply` (commanddeclaration)
```lean
theorem comp_apply (x : M₁) : f.comp g x = f (g x)
```

### `LinearMap.trace_eq_contract` (commanddeclaration)
```lean
@[simp]
theorem trace_eq_contract : LinearMap.trace R M ∘ₗ dualTensorHom R M M = contractLeft R M
```

## Premise full source (with proof)
### `LinearMap.comp_apply` (commanddeclaration) at `Mathlib/Algebra/Module/LinearMap/Basic.lean`
```lean
theorem comp_apply (x : M₁) : f.comp g x = f (g x) :=
  rfl
```

### `LinearMap.trace_eq_contract` (commanddeclaration) at `Mathlib/LinearAlgebra/Trace.lean`
```lean
/-- When `M` is finite free, the trace of a linear map correspond to the contraction pairing under
the isomorphism `End(M) ≃ M* ⊗ M`-/
@[simp]
theorem trace_eq_contract : LinearMap.trace R M ∘ₗ dualTensorHom R M M = contractLeft R M :=
  trace_eq_contract_of_basis (Module.Free.chooseBasis R M)
```

## Transitive premise context (1-hop, 9/9 premises, ≈1052 tokens)
### `free` (commanddeclaration) at `Mathlib/Algebra/Category/MonCat/Adjunctions.lean`
```lean
/-- The free functor `Type u ⥤ MonCat` sending a type `X` to the free monoid on `X`. -/
def free : Type u ⥤ MonCat.{u} where
  obj α := MonCat.of (FreeMonoid α)
  map := FreeMonoid.map
  map_id _ := FreeMonoid.hom_eq (fun _ => rfl)
  map_comp _ _ := FreeMonoid.hom_eq (fun _ => rfl)
```

### `Polynomial.HasSeparableContraction.contraction` (commanddeclaration) at `Mathlib/RingTheory/Polynomial/SeparableDegree.lean`
```lean
/-- A choice of a separable contraction. -/
def HasSeparableContraction.contraction : F[X] :=
  Classical.choose hf
```

### `RootPairing.pairing` (commanddeclaration) at `Mathlib/LinearAlgebra/RootSystem/Defs.lean`
```lean
/-- This is the pairing between roots and coroots. -/
def pairing : R := P.toLin (P.root i) (P.coroot j)

/-- The Coxeter Weight of a pair gives the weight of an edge in a Coxeter diagram, when it is
finite.  It is `4 cos² θ`, where `θ` describes the dihedral angle between hyperplanes. -/
```

### `CategoryTheory.Injective.under` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Injective.lean`
```lean
/-- `Injective.under X` provides an arbitrarily chosen injective object equipped with
a monomorphism `Injective.ι : X ⟶ Injective.under X`.
-/
def under (X : C) : C :=
  (EnoughInjectives.presentation X).some.J
```

### `LinearMap.trace` (commanddeclaration) at `Mathlib/LinearAlgebra/Trace.lean`
```lean
/-- Trace of an endomorphism independent of basis. -/
def trace : (M →ₗ[R] M) →ₗ[R] R :=
  if H : ∃ s : Finset M, Nonempty (Basis s R M) then traceAux R H.choose_spec.some else 0
```

### `dualTensorHom` (commanddeclaration) at `Mathlib/LinearAlgebra/Contraction.lean`
```lean
/-- The natural map associating a linear map to the tensor product of two modules. -/
def dualTensorHom : Module.Dual R M ⊗[R] N →ₗ[R] M →ₗ[R] N :=
  let M' := Module.Dual R M
  (uncurry R M' N (M →ₗ[R] N) : _ → M' ⊗ N →ₗ[R] M →ₗ[R] N) LinearMap.smulRightₗ
```

### `contractLeft` (commanddeclaration) at `Mathlib/LinearAlgebra/Contraction.lean`
```lean
/-- The natural left-handed pairing between a module and its dual. -/
def contractLeft : Module.Dual R M ⊗[R] M →ₗ[R] R :=
  (uncurry _ _ _ _).toFun LinearMap.id
```

### `LinearMap.trace_eq_contract_of_basis` (commanddeclaration) at `Mathlib/LinearAlgebra/Trace.lean`
```lean
/-- The trace of a linear map correspond to the contraction pairing under the isomorphism
 `End(M) ≃ M* ⊗ M`-/
theorem trace_eq_contract_of_basis [Finite ι] (b : Basis ι R M) :
    LinearMap.trace R M ∘ₗ dualTensorHom R M M = contractLeft R M := by
  classical
    cases nonempty_fintype ι
    apply Basis.ext (Basis.tensorProduct (Basis.dualBasis b) b)
    rintro ⟨i, j⟩
    simp only [Function.comp_apply, Basis.tensorProduct_apply, Basis.coe_dualBasis, coe_comp]
    rw [trace_eq_matrix_trace R b, toMatrix_dualTensorHom]
    by_cases hij : i = j
    · rw [hij]
      simp
    rw [Matrix.StdBasisMatrix.trace_zero j i (1 : R) hij]
    simp [Finsupp.single_eq_pi_single, hij]
```

### `Module.Free.chooseBasis` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- If `Module.Free R M` then `chooseBasis : ι → M` is the basis.
Here `ι = ChooseBasisIndex R M`. -/
noncomputable def chooseBasis : Basis (ChooseBasisIndex R M) R M :=
  ((Module.free_iff_set R M).mp ‹_›).choose_spec.some
```
