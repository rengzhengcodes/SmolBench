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
