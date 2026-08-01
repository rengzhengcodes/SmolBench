## Current goal
```
⊢ x ∈ Set.range (⇑(map f) ∘ ⇑(tprod R)) ↔ x ∈ {t_1 | ∃ m, (⨂ₜ[R] (i : ι), (f i) (m i)) = t_1}
```

## Full tactic state
```
case h.h
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝¹¹ : CommSemiring R
R₁ : Type u_5
R₂ : Type u_6
s : ι → Type u_7
inst✝¹⁰ : (i : ι) → AddCommMonoid (s i)
inst✝⁹ : (i : ι) → Module R (s i)
M : Type u_8
inst✝⁸ : AddCommMonoid M
inst✝⁷ : Module R M
E : Type u_9
inst✝⁶ : AddCommMonoid E
inst✝⁵ : Module R E
F : Type u_10
inst✝⁴ : AddCommMonoid F
t : ι → Type u_11
t' : ι → Type u_12
inst✝³ : (i : ι) → AddCommMonoid (t i)
inst✝² : (i : ι) → Module R (t i)
inst✝¹ : (i : ι) → AddCommMonoid (t' i)
inst✝ : (i : ι) → Module R (t' i)
g : (i : ι) → t i →ₗ[R] t' i
f : (i : ι) → s i →ₗ[R] t i
x : ⨂[R] (i : ι), t i
⊢ x ∈ Set.range (⇑(map f) ∘ ⇑(tprod R)) ↔ x ∈ {t_1 | ∃ m, (⨂ₜ[R] (i : ι), (f i) (m i)) = t_1}
```

## Proof so far (3 tactics)
```lean
rw [← Submodule.map_top, ← span_tprod_eq_top, Submodule.map_span, ← Set.range_comp]
apply congrArg
ext x
```

## Theorem
`PiTensorProduct.map_range_eq_span_tprod` in `Mathlib/LinearAlgebra/PiTensorProduct.lean`

## Premises used in the next tactic
- `Set.mem_range`
- `Function.comp_apply`
- `PiTensorProduct.map_tprod`
- `Set.mem_setOf_eq`

## Premise signatures
### `Set.mem_range` (commanddeclaration)
```lean
@[simp] theorem mem_range {x : α} : x ∈ range f ↔ ∃ y, f y = x
```

### `Function.comp_apply` (commanddeclaration)
```lean
@[simp] theorem Function.comp_apply {f : β → δ} {g : α → β} {x : α} : comp f g x = f (g x)
```

### `PiTensorProduct.map_tprod` (lemma)
```lean
@[simp] lemma map_tprod (x : Π i, s i) :
    map f (tprod R x) = tprod R fun i ↦ f i (x i)
```

### `Set.mem_setOf_eq` (commanddeclaration)
```lean
@[simp, mfld_simps] theorem mem_setOf_eq {x : α} {p : α → Prop} : (x ∈ {y | p y}) = p x
```

## Premise full source (with proof)
### `Set.mem_range` (commanddeclaration) at `Mathlib/Data/Set/Defs.lean`
```lean
@[simp] theorem mem_range {x : α} : x ∈ range f ↔ ∃ y, f y = x := Iff.rfl
```

### `Function.comp_apply` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
@[simp] theorem Function.comp_apply {f : β → δ} {g : α → β} {x : α} : comp f g x = f (g x) := rfl
```

### `PiTensorProduct.map_tprod` (lemma) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
@[simp] lemma map_tprod (x : Π i, s i) :
    map f (tprod R x) = tprod R fun i ↦ f i (x i) :=
  lift.tprod _

-- No lemmas about associativity, because we don't have associativity of `PiTensorProduct` yet.
```

### `Set.mem_setOf_eq` (commanddeclaration) at `Mathlib/Data/Set/Defs.lean`
```lean
@[simp, mfld_simps] theorem mem_setOf_eq {x : α} {p : α → Prop} : (x ∈ {y | p y}) = p x := rfl
```

## Transitive premise context (1-hop, 2/2 premises, ≈191 tokens)
### `Iff.rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
protected theorem Iff.rfl {a : Prop} : a ↔ a :=
  Iff.refl a

macro_rules | `(tactic| rfl) => `(tactic| exact Iff.rfl)
```

### `PiTensorProduct` (commanddeclaration) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
/-- `PiTensorProduct R s` with `R` a commutative semiring and `s : ι → Type*` is the tensor
  product of all the `s i`'s. This is denoted by `⨂[R] i, s i`. -/
def PiTensorProduct : Type _ :=
  (addConGen (PiTensorProduct.Eqv R s)).Quotient
```
