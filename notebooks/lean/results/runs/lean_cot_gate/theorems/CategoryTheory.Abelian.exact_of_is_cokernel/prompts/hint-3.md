## Current goal
```
⊢ kernel.ι g ≫ cokernel.π f = 0
```

## Full tactic state
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
inst✝ : Abelian C
X Y Z : C
f : X ⟶ Y
g : Y ⟶ Z
w : f ≫ g = 0
h : IsColimit (CokernelCofork.ofπ g w)
this : g ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) ⋯) = cokernel.π f
⊢ kernel.ι g ≫ cokernel.π f = 0
```

## Proof so far (3 tactics)
```lean
refine' (exact_iff _ _).2 ⟨w, _⟩
have := h.fac (CokernelCofork.ofπ _ (cokernel.condition f)) WalkingParallelPair.one
simp only [Cofork.ofπ_ι_app] at this
```

## Theorem
`CategoryTheory.Abelian.exact_of_is_cokernel` in `Mathlib/CategoryTheory/Abelian/Exact.lean`

## Premises used in the next tactic
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Limits.kernel.condition`
- `CategoryTheory.Limits.zero_comp`

## Premise signatures
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.kernel.condition` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem kernel.condition : kernel.ι f ≫ f = 0
```

### `CategoryTheory.Limits.zero_comp` (commanddeclaration)
```lean
@[simp]
theorem zero_comp [HasZeroMorphisms C] {X : C} {Y Z : C} {f : Y ⟶ Z} :
    (0 : X ⟶ Y) ≫ f = (0 : X ⟶ Z)
```

## Premise full source (with proof)
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.kernel.condition` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Kernels.lean`
```lean
@[reassoc (attr := simp)]
theorem kernel.condition : kernel.ι f ≫ f = 0 :=
  KernelFork.condition _
```

### `CategoryTheory.Limits.zero_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
@[simp]
theorem zero_comp [HasZeroMorphisms C] {X : C} {Y Z : C} {f : Y ⟶ Z} :
    (0 : X ⟶ Y) ≫ f = (0 : X ⟶ Z) :=
  HasZeroMorphisms.zero_comp X f
```

## Transitive premise context (1-hop, 2/2 premises, ≈345 tokens)
### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `CategoryTheory.Limits.HasZeroMorphisms` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
/-- A category "has zero morphisms" if there is a designated "zero morphism" in each morphism space,
and compositions of zero morphisms with anything give the zero morphism. -/
class HasZeroMorphisms where
  /-- Every morphism space has zero -/
  [zero : ∀ X Y : C, Zero (X ⟶ Y)]
  /-- `f` composed with `0` is `0` -/
  comp_zero : ∀ {X Y : C} (f : X ⟶ Y) (Z : C), f ≫ (0 : Y ⟶ Z) = (0 : X ⟶ Z) := by aesop_cat
  /-- `0` composed with `f` is `0` -/
  zero_comp : ∀ (X : C) {Y Z : C} (f : Y ⟶ Z), (0 : X ⟶ Y) ≫ f = (0 : X ⟶ Z) := by aesop_cat
```
