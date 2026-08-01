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

## Transitive premise context (1-hop, 6/6 premises, ≈597 tokens)
### `CategoryTheory.ShortComplex.RightHomologyData.IsPreservedBy.hf` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/PreservesHomology.lean`
```lean
/-- When a right homology data is preserved by a functor `F`, this functor
preserves the cokernel of `S.f : S.X₁ ⟶ S.X₂`. -/
def IsPreservedBy.hf : PreservesColimit (parallelPair S.f 0) F :=
  @IsPreservedBy.f _ _ _ _ _ _ _ h F _ _

/-- When a right homology data `h` is preserved by a functor `F`, this functor
preserves the kernel of `h.g' : h.Q ⟶ S.X₃`. -/
```

### `IsCompl` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
/-- Two elements `x` and `y` are complements of each other if `x ⊔ y = ⊤` and `x ⊓ y = ⊥`. -/
structure IsCompl [PartialOrder α] [BoundedOrder α] (x y : α) : Prop where
  /-- If `x` and `y` are to be complementary in an order, they should be disjoint. -/
  protected disjoint : Disjoint x y
  /-- If `x` and `y` are to be complementary in an order, they should be codisjoint. -/
  protected codisjoint : Codisjoint x y
```

### `disjoint_iff_inf_le` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
theorem disjoint_iff_inf_le : Disjoint a b ↔ a ⊓ b ≤ ⊥ :=
  ⟨fun hd ↦ hd inf_le_left inf_le_right, fun h _ ha hb ↦ (le_inf ha hb).trans h⟩
```

### `SetLike.mem_coe` (commanddeclaration) at `Mathlib/Data/SetLike/Basic.lean`
```lean
@[simp]
theorem mem_coe {x : B} : x ∈ (p : Set B) ↔ x ∈ p :=
  Iff.rfl
```

### `codisjoint_iff_le_sup` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
theorem codisjoint_iff_le_sup : Codisjoint a b ↔ ⊤ ≤ a ⊔ b :=
  @disjoint_iff_inf_le αᵒᵈ _ _ _ _
```

### `LinearMap.map_sub` (commanddeclaration) at `Mathlib/Algebra/Module/LinearMap/Basic.lean`
```lean
protected theorem map_sub (x y : M) : f (x - y) = f x - f y :=
  map_sub f x y
```
