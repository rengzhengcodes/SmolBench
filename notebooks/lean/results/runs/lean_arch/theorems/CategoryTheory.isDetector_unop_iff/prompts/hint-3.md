## Current goal
```
⊢ IsDetector G.unop ↔ IsCodetector G
```

## Full tactic state
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetector G.unop ↔ IsCodetector G
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.isDetector_unop_iff` in `Mathlib/CategoryTheory/Generator.lean`

## Premises used in the next tactic
- `CategoryTheory.IsDetector`
- `CategoryTheory.IsCodetector`
- `CategoryTheory.isDetecting_unop_iff`
- `Set.singleton_unop`

## Premise signatures
### `CategoryTheory.IsDetector` (commanddeclaration)
```lean
def IsDetector (G : C) : Prop
```

### `CategoryTheory.IsCodetector` (commanddeclaration)
```lean
def IsCodetector (G : C) : Prop
```

### `CategoryTheory.isDetecting_unop_iff` (commanddeclaration)
```lean
theorem isDetecting_unop_iff (𝒢 : Set Cᵒᵖ) : IsDetecting 𝒢.unop ↔ IsCodetecting 𝒢
```

### `Set.singleton_unop` (commanddeclaration)
```lean
@[simp]
theorem singleton_unop (x : αᵒᵖ) : ({x} : Set αᵒᵖ).unop = {unop x}
```

## Premise full source (with proof)
### `CategoryTheory.IsDetector` (commanddeclaration) at `Mathlib/CategoryTheory/Generator.lean`
```lean
/-- We say that `G` is a detector if the functor `C(G, -)` reflects isomorphisms. -/
def IsDetector (G : C) : Prop :=
  IsDetecting ({G} : Set C)
```

### `CategoryTheory.IsCodetector` (commanddeclaration) at `Mathlib/CategoryTheory/Generator.lean`
```lean
/-- We say that `G` is a codetector if the functor `C(-, G)` reflects isomorphisms. -/
def IsCodetector (G : C) : Prop :=
  IsCodetecting ({G} : Set C)
```

### `CategoryTheory.isDetecting_unop_iff` (commanddeclaration) at `Mathlib/CategoryTheory/Generator.lean`
```lean
theorem isDetecting_unop_iff (𝒢 : Set Cᵒᵖ) : IsDetecting 𝒢.unop ↔ IsCodetecting 𝒢 := by
  rw [← isCodetecting_op_iff, Set.unop_op]
```

### `Set.singleton_unop` (commanddeclaration) at `Mathlib/Data/Set/Opposite.lean`
```lean
@[simp]
theorem singleton_unop (x : αᵒᵖ) : ({x} : Set αᵒᵖ).unop = {unop x} := by
  ext
  constructor
  · apply op_injective
  · apply unop_injective
```

## Transitive premise context (1-hop, 4/4 premises, ≈702 tokens)
### `CategoryTheory.IsDetecting` (commanddeclaration) at `Mathlib/CategoryTheory/Generator.lean`
```lean
/-- We say that `𝒢` is a detecting set if the functors `C(G, -)` collectively reflect isomorphisms,
    i.e., if any `h` with domain in `𝒢` uniquely factors through `f`, then `f` is an isomorphism. -/
def IsDetecting (𝒢 : Set C) : Prop :=
  ∀ ⦃X Y : C⦄ (f : X ⟶ Y), (∀ G ∈ 𝒢, ∀ (h : G ⟶ Y), ∃! h' : G ⟶ X, h' ≫ f = h) → IsIso f
```

### `CategoryTheory.IsCodetecting` (commanddeclaration) at `Mathlib/CategoryTheory/Generator.lean`
```lean
/-- We say that `𝒢` is a codetecting set if the functors `C(-, G)` collectively reflect
    isomorphisms, i.e., if any `h` with codomain in `G` uniquely factors through `f`, then `f` is
    an isomorphism. -/
def IsCodetecting (𝒢 : Set C) : Prop :=
  ∀ ⦃X Y : C⦄ (f : X ⟶ Y), (∀ G ∈ 𝒢, ∀ (h : X ⟶ G), ∃! h' : Y ⟶ G, f ≫ h' = h) → IsIso f
```

### `CategoryTheory.isCodetecting_op_iff` (commanddeclaration) at `Mathlib/CategoryTheory/Generator.lean`
```lean
theorem isCodetecting_op_iff (𝒢 : Set C) : IsCodetecting 𝒢.op ↔ IsDetecting 𝒢 := by
  refine' ⟨fun h𝒢 X Y f hf => _, fun h𝒢 X Y f hf => _⟩
  · refine' (isIso_op_iff _).1 (h𝒢 _ fun G hG h => _)
    obtain ⟨t, ht, ht'⟩ := hf (unop G) (Set.mem_op.1 hG) h.unop
    exact
      ⟨t.op, Quiver.Hom.unop_inj ht, fun y hy => Quiver.Hom.unop_inj (ht' _ (Quiver.Hom.op_inj hy))⟩
  · refine' (isIso_unop_iff _).1 (h𝒢 _ fun G hG h => _)
    obtain ⟨t, ht, ht'⟩ := hf (op G) (Set.op_mem_op.2 hG) h.op
    refine' ⟨t.unop, Quiver.Hom.op_inj ht, fun y hy => Quiver.Hom.op_inj (ht' _ _)⟩
    exact Quiver.Hom.unop_inj (by simpa only using hy)
```

### `Set.unop_op` (commanddeclaration) at `Mathlib/Data/Set/Opposite.lean`
```lean
@[simp]
theorem unop_op (s : Set αᵒᵖ) : s.unop.op = s := rfl
```
