## Current goal
```
⊢ IsCompl p (ker (codRestrict ?m.413479))

R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
F : Type u_3
inst✝⁶ : AddCommGroup F
inst✝⁵ : Module R F
G : Type u_4
inst✝⁴ : AddCommGroup G
inst✝³ : Module R G
p q : Submodule R E
S : Type u_5
inst✝² : Semiring S
M : Type u_6
inst✝¹ : AddCommMonoid M
inst✝ : Module S M
m : Submodule S M
f : E →ₗ[R] E
h : IsProj p f
⊢ IsProj ?m.413208 f

R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
F : Type u_3
inst✝⁶ : AddCommGroup F
inst✝⁵ : Module R F
G : Type u_4
inst✝⁴ : AddCommGroup G
inst✝³ : Module R G
p q : Submodule R E
S : Type u_5
inst✝² : Semiring S
M : Type u_6
inst✝¹ : AddCommMonoid M
inst✝ : Module S M
m : Submodule S M
f : E →ₗ[R] E
h : IsProj p f
⊢ Submodule R E
```

## Full tactic state
```
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
F : Type u_3
inst✝⁶ : AddCommGroup F
inst✝⁵ : Module R F
G : Type u_4
inst✝⁴ : AddCommGroup G
inst✝³ : Module R G
p q : Submodule R E
S : Type u_5
inst✝² : Semiring S
M : Type u_6
inst✝¹ : AddCommMonoid M
inst✝ : Module S M
m : Submodule S M
f : E →ₗ[R] E
h : IsProj p f
⊢ IsCompl p (ker (codRestrict ?m.413479))

R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
F : Type u_3
inst✝⁶ : AddCommGroup F
inst✝⁵ : Module R F
G : Type u_4
inst✝⁴ : AddCommGroup G
inst✝³ : Module R G
p q : Submodule R E
S : Type u_5
inst✝² : Semiring S
M : Type u_6
inst✝¹ : AddCommMonoid M
inst✝ : Module S M
m : Submodule S M
f : E →ₗ[R] E
h : IsProj p f
⊢ IsProj ?m.413208 f

R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
F : Type u_3
inst✝⁶ : AddCommGroup F
inst✝⁵ : Module R F
G : Type u_4
inst✝⁴ : AddCommGroup G
inst✝³ : Module R G
p q : Submodule R E
S : Type u_5
inst✝² : Semiring S
M : Type u_6
inst✝¹ : AddCommMonoid M
inst✝ : Module S M
m : Submodule S M
f : E →ₗ[R] E
h : IsProj p f
⊢ Submodule R E
```

## Proof so far (1 tactic)
```lean
rw [← codRestrict_ker]
```

## Theorem
`LinearMap.IsProj.isCompl` in `Mathlib/LinearAlgebra/Projection.lean`

## Premises used in the next tactic
- `LinearMap.isCompl_of_proj`

## Premise signatures
### `LinearMap.isCompl_of_proj` (commanddeclaration)
```lean
theorem isCompl_of_proj {f : E →ₗ[R] p} (hf : ∀ x : p, f x = x) : IsCompl p (ker f)
```

## Premise full source (with proof)
### `LinearMap.isCompl_of_proj` (commanddeclaration) at `Mathlib/LinearAlgebra/Projection.lean`
```lean
theorem isCompl_of_proj {f : E →ₗ[R] p} (hf : ∀ x : p, f x = x) : IsCompl p (ker f) := by
  constructor
  · rw [disjoint_iff_inf_le]
    rintro x ⟨hpx, hfx⟩
    erw [SetLike.mem_coe, mem_ker, hf ⟨x, hpx⟩, mk_eq_zero] at hfx
    simp only [hfx, SetLike.mem_coe, zero_mem]
  · rw [codisjoint_iff_le_sup]
    intro x _
    rw [mem_sup']
    refine' ⟨f x, ⟨x - f x, _⟩, add_sub_cancel _ _⟩
    rw [mem_ker, LinearMap.map_sub, hf, sub_self]
```
