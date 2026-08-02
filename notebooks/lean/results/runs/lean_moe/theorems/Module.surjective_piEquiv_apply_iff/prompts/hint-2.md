## Current goal
```
⊢ Surjective ⇑((piEquiv ι R M) v) ↔ span R (range v) = ⊤
```

## Full tactic state
```
ι : Type u_1
R : Type u_2
M : Type u_3
N : Type u_4
inst✝⁵ : Finite ι
inst✝⁴ : CommSemiring R
inst✝³ : AddCommMonoid M
inst✝² : AddCommMonoid N
inst✝¹ : Module R M
inst✝ : Module R N
v : ι → M
⊢ Surjective ⇑((piEquiv ι R M) v) ↔ span R (range v) = ⊤
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Module.surjective_piEquiv_apply_iff` in `Mathlib/LinearAlgebra/StdBasis.lean`

## Premises used in the next tactic
- `LinearMap.range_eq_top`
- `Module.range_piEquiv`

## Premise signatures
### `LinearMap.range_eq_top` (commanddeclaration)
```lean
theorem range_eq_top [RingHomSurjective τ₁₂] {f : F} : range f = ⊤ ↔ Surjective f
```

### `Module.range_piEquiv` (lemma)
```lean
@[simp] lemma range_piEquiv (v : ι → M) :
    LinearMap.range (piEquiv ι R M v) = span R (range v)
```

## Premise full source (with proof)
### `LinearMap.range_eq_top` (commanddeclaration) at `Mathlib/LinearAlgebra/Basic.lean`
```lean
theorem range_eq_top [RingHomSurjective τ₁₂] {f : F} : range f = ⊤ ↔ Surjective f := by
  rw [SetLike.ext'_iff, range_coe, top_coe, Set.range_iff_surjective]
```

### `Module.range_piEquiv` (lemma) at `Mathlib/LinearAlgebra/StdBasis.lean`
```lean
@[simp] lemma range_piEquiv (v : ι → M) :
    LinearMap.range (piEquiv ι R M v) = span R (range v) :=
  Basis.constr_range _ _
```
