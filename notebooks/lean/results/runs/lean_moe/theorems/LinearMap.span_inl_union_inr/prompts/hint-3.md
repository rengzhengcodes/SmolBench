## Current goal
```
⊢ span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = Submodule.prod (span R s) (span R t)
```

## Full tactic state
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
M₃ : Type y
V₃ : Type y'
M₄ : Type z
ι : Type x
M₅ : Type u_1
M₆ : Type u_2
inst✝⁸ : Semiring R
inst✝⁷ : AddCommMonoid M
inst✝⁶ : AddCommMonoid M₂
inst✝⁵ : AddCommMonoid M₃
inst✝⁴ : AddCommMonoid M₄
inst✝³ : Module R M
inst✝² : Module R M₂
inst✝¹ : Module R M₃
inst✝ : Module R M₄
s : Set M
t : Set M₂
⊢ span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = Submodule.prod (span R s) (span R t)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`LinearMap.span_inl_union_inr` in `Mathlib/LinearAlgebra/Prod.lean`

## Premises used in the next tactic
- `Submodule.span_union`
- `LinearMap.prod_eq_sup_map`
- `Submodule.span_image`
- `Submodule.span_image`

## Premise signatures
### `Submodule.span_union` (commanddeclaration)
```lean
theorem span_union (s t : Set M) : span R (s ∪ t) = span R s ⊔ span R t
```

### `LinearMap.prod_eq_sup_map` (commanddeclaration)
```lean
theorem prod_eq_sup_map (p : Submodule R M) (q : Submodule R M₂) :
    p.prod q = p.map (LinearMap.inl R M M₂) ⊔ q.map (LinearMap.inr R M M₂)
```

### `Submodule.span_image` (commanddeclaration)
```lean
theorem span_image [RingHomSurjective σ₁₂] (f : F) :
    span R₂ (f '' s) = map f (span R s)
```

### `Submodule.span_image` (commanddeclaration)
```lean
theorem span_image [RingHomSurjective σ₁₂] (f : F) :
    span R₂ (f '' s) = map f (span R s)
```

## Premise full source (with proof)
### `Submodule.span_union` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
theorem span_union (s t : Set M) : span R (s ∪ t) = span R s ⊔ span R t :=
  (Submodule.gi R M).gc.l_sup
```

### `LinearMap.prod_eq_sup_map` (commanddeclaration) at `Mathlib/LinearAlgebra/Prod.lean`
```lean
theorem prod_eq_sup_map (p : Submodule R M) (q : Submodule R M₂) :
    p.prod q = p.map (LinearMap.inl R M M₂) ⊔ q.map (LinearMap.inr R M M₂) := by
  rw [← map_coprod_prod, coprod_inl_inr, map_id]
```

### `Submodule.span_image` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
theorem span_image [RingHomSurjective σ₁₂] (f : F) :
    span R₂ (f '' s) = map f (span R s) :=
  (map_span f s).symm
```

### `Submodule.span_image` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
theorem span_image [RingHomSurjective σ₁₂] (f : F) :
    span R₂ (f '' s) = map f (span R s) :=
  (map_span f s).symm
```

## Transitive premise context (1-hop, 7/7 premises, ≈753 tokens)
### `Submodule.gi` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
/-- `span` forms a Galois insertion with the coercion from submodule to set. -/
protected def gi : GaloisInsertion (@span R M _ _ _) (↑)
    where
  choice s _ := span R s
  gc _ _ := span_le
  le_l_u _ := subset_span
  choice_eq _ _ := rfl
```

### `Submodule` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Basic.lean`
```lean
/-- A submodule of a module is one which is closed under vector operations.
  This is a sufficient condition for the subset of vectors in the submodule
  to themselves form a module. -/
structure Submodule (R : Type u) (M : Type v) [Semiring R] [AddCommMonoid M] [Module R M] extends
  AddSubmonoid M, SubMulAction R M : Type v
```

### `LinearMap.inl` (commanddeclaration) at `Mathlib/LinearAlgebra/Prod.lean`
```lean
/-- The left injection into a product is a linear map. -/
def inl : M →ₗ[R] M × M₂ :=
  prod LinearMap.id 0
```

### `LinearMap.inr` (commanddeclaration) at `Mathlib/LinearAlgebra/Prod.lean`
```lean
/-- The right injection into a product is a linear map. -/
def inr : M₂ →ₗ[R] M × M₂ :=
  prod 0 LinearMap.id
```

### `LinearMap.map_coprod_prod` (commanddeclaration) at `Mathlib/LinearAlgebra/Prod.lean`
```lean
theorem map_coprod_prod (f : M →ₗ[R] M₃) (g : M₂ →ₗ[R] M₃) (p : Submodule R M)
    (q : Submodule R M₂) : map (coprod f g) (p.prod q) = map f p ⊔ map g q := by
  refine' le_antisymm _ (sup_le (map_le_iff_le_comap.2 _) (map_le_iff_le_comap.2 _))
  · rw [SetLike.le_def]
    rintro _ ⟨x, ⟨h₁, h₂⟩, rfl⟩
    exact mem_sup.2 ⟨_, ⟨_, h₁, rfl⟩, _, ⟨_, h₂, rfl⟩, rfl⟩
  · exact fun x hx => ⟨(x, 0), by simp [hx]⟩
  · exact fun x hx => ⟨(0, x), by simp [hx]⟩
```

### `RingHomSurjective` (commanddeclaration) at `Mathlib/Algebra/Ring/CompTypeclasses.lean`
```lean
/-- Class expressing the fact that a `RingHom` is surjective. This is needed in the context
of semilinear maps, where some lemmas require this. -/
class RingHomSurjective (σ : R₁ →+* R₂) : Prop where
  /-- The ring homomorphism is surjective -/
  is_surjective : Function.Surjective σ
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```
