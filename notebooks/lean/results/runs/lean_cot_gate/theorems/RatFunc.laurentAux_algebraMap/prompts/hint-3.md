## Current goal
```
⊢ (laurentAux r) ((algebraMap R[X] (RatFunc R)) p) = (algebraMap R[X] (RatFunc R)) ((taylor r) p)
```

## Full tactic state
```
R : Type u
inst✝ : CommRing R
hdomain : IsDomain R
r s : R
p q : R[X]
f : RatFunc R
⊢ (laurentAux r) ((algebraMap R[X] (RatFunc R)) p) = (algebraMap R[X] (RatFunc R)) ((taylor r) p)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`RatFunc.laurentAux_algebraMap` in `Mathlib/FieldTheory/Laurent.lean`

## Premises used in the next tactic
- `RatFunc.mk_one`
- `RatFunc.mk_one`
- `RatFunc.mk_eq_div`
- `RatFunc.laurentAux_div`
- `RatFunc.mk_eq_div`
- `Polynomial.taylor_one`
- `map_one`
- `map_one`

## Premise signatures
### `RatFunc.mk_one` (commanddeclaration)
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x
```

### `RatFunc.mk_one` (commanddeclaration)
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x
```

### `RatFunc.mk_eq_div` (commanddeclaration)
```lean
@[simp]
theorem mk_eq_div (p q : K[X]) : RatFunc.mk p q = algebraMap _ _ p / algebraMap _ _ q
```

### `RatFunc.laurentAux_div` (commanddeclaration)
```lean
theorem laurentAux_div :
    laurentAux r (algebraMap _ _ p / algebraMap _ _ q) =
      algebraMap _ _ (taylor r p) / algebraMap _ _ (taylor r q)
```

### `RatFunc.mk_eq_div` (commanddeclaration)
```lean
@[simp]
theorem mk_eq_div (p q : K[X]) : RatFunc.mk p q = algebraMap _ _ p / algebraMap _ _ q
```

### `Polynomial.taylor_one` (commanddeclaration)
```lean
@[simp]
theorem taylor_one : taylor r (1 : R[X]) = C 1
```

### `map_one` (commanddeclaration)
```lean
@[to_additive (attr := simp)]
theorem map_one [OneHomClass F M N] (f : F) : f 1 = 1
```

### `map_one` (commanddeclaration)
```lean
@[to_additive (attr := simp)]
theorem map_one [OneHomClass F M N] (f : F) : f 1 = 1
```

## Premise full source (with proof)
### `RatFunc.mk_one` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x :=
  rfl
```

### `RatFunc.mk_one` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x :=
  rfl
```

### `RatFunc.mk_eq_div` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
@[simp]
theorem mk_eq_div (p q : K[X]) : RatFunc.mk p q = algebraMap _ _ p / algebraMap _ _ q := by
  simp only [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

### `RatFunc.laurentAux_div` (commanddeclaration) at `Mathlib/FieldTheory/Laurent.lean`
```lean
theorem laurentAux_div :
    laurentAux r (algebraMap _ _ p / algebraMap _ _ q) =
      algebraMap _ _ (taylor r p) / algebraMap _ _ (taylor r q) :=
  -- Porting note: added `by exact taylor_mem_nonZeroDivisors r`
  map_apply_div _ (by exact taylor_mem_nonZeroDivisors r) _ _
```

### `RatFunc.mk_eq_div` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
@[simp]
theorem mk_eq_div (p q : K[X]) : RatFunc.mk p q = algebraMap _ _ p / algebraMap _ _ q := by
  simp only [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

### `Polynomial.taylor_one` (commanddeclaration) at `Mathlib/Data/Polynomial/Taylor.lean`
```lean
@[simp]
theorem taylor_one : taylor r (1 : R[X]) = C 1 := by rw [← C_1, taylor_C]
```

### `map_one` (commanddeclaration) at `Mathlib/Algebra/Group/Hom/Defs.lean`
```lean
@[to_additive (attr := simp)]
theorem map_one [OneHomClass F M N] (f : F) : f 1 = 1 :=
  OneHomClass.map_one f
```

### `map_one` (commanddeclaration) at `Mathlib/Algebra/Group/Hom/Defs.lean`
```lean
@[to_additive (attr := simp)]
theorem map_one [OneHomClass F M N] (f : F) : f 1 = 1 :=
  OneHomClass.map_one f
```

## Transitive premise context (1-hop, 13/13 premises, ≈1685 tokens)
### `RatFunc.mk` (leanelabcommandcommandirreducibledef) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- `RatFunc.mk (p q : K[X])` is `p / q` as a rational function.

If `q = 0`, then `mk` returns 0.

This is an auxiliary definition used to define an `Algebra` structure on `RatFunc`;
the `simp` normal form of `mk p q` is `algebraMap _ _ p / algebraMap _ _ q`.
-/
protected irreducible_def mk (p q : K[X]) : RatFunc K :=
  ofFractionRing (algebraMap _ _ p / algebraMap _ _ q)
```

### `algebraMap` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- Embedding `R →+* A` given by `Algebra` structure. -/
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A :=
  Algebra.toRingHom
```

### `RatFunc.mk_eq_div'` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_eq_div' (p q : K[X]) :
    RatFunc.mk p q = ofFractionRing (algebraMap _ _ p / algebraMap _ _ q) := by rw [RatFunc.mk]
```

### `RatFunc.ofFractionRing_div` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem ofFractionRing_div (p q : FractionRing K[X]) :
    ofFractionRing (p / q) = ofFractionRing p / ofFractionRing q := by
  simp only [Div.div, HDiv.hDiv, RatFunc.div]
```

### `RatFunc.ofFractionRing_algebraMap` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem ofFractionRing_algebraMap (x : K[X]) :
    ofFractionRing (algebraMap _ (FractionRing K[X]) x) = algebraMap _ _ x := by
  rw [← mk_one, mk_one']
```

### `RatFunc.laurentAux` (commanddeclaration) at `Mathlib/FieldTheory/Laurent.lean`
```lean
/-- The Laurent expansion of rational functions about a value.
Auxiliary definition, usage when over integral domains should prefer `RatFunc.laurent`. -/
def laurentAux : RatFunc R →+* RatFunc R :=
  RatFunc.mapRingHom
    ( { toFun := taylor r
        map_add' := map_add (taylor r)
        map_mul' := taylor_mul _
        map_zero' := map_zero (taylor r)
        map_one' := taylor_one r } : R[X] →+* R[X])
    (taylor_mem_nonZeroDivisors _)
```

### `Polynomial.taylor` (commanddeclaration) at `Mathlib/Data/Polynomial/Taylor.lean`
```lean
/-- The Taylor expansion of a polynomial `f` at `r`. -/
def taylor (r : R) : R[X] →ₗ[R] R[X] where
  toFun f := f.comp (X + C r)
  map_add' f g := add_comp
  map_smul' c f := by simp only [smul_eq_C_mul, C_mul_comp, RingHom.id_apply]
```

### `Lean.MVarId.note` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Tactic/Assert.lean`
```lean
/-- Add the hypothesis `h : t`, given `v : t`, and return the new `FVarId`. -/
def _root_.Lean.MVarId.note (g : MVarId) (h : Name) (v : Expr) (t? : Option Expr := .none) :
    MetaM (FVarId × MVarId) := do
  (← g.assert h (← match t? with | some t => pure t | none => inferType v) v).intro1P

/--
  Convert the given goal `Ctx |- target` into `Ctx |- let name : type := val; target`.
  It assumes `val` has type `type` -/
```

### `RatFunc.taylor_mem_nonZeroDivisors` (commanddeclaration) at `Mathlib/FieldTheory/Laurent.lean`
```lean
theorem taylor_mem_nonZeroDivisors (hp : p ∈ R[X]⁰) : taylor r p ∈ R[X]⁰ := by
  rw [mem_nonZeroDivisors_iff]
  intro x hx
  have : x = taylor (r - r) x := by simp
  rwa [this, sub_eq_add_neg, ← taylor_taylor, ← taylor_mul,
    LinearMap.map_eq_zero_iff _ (taylor_injective _), mul_right_mem_nonZeroDivisors_eq_zero_iff hp,
    LinearMap.map_eq_zero_iff _ (taylor_injective _)] at hx
```

### `RatFunc.map_apply_div` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
@[simp]
theorem map_apply_div {R F : Type*} [CommRing R] [IsDomain R]
    [FunLike F K[X] R[X]] [MonoidWithZeroHomClass F K[X] R[X]]
    (φ : F) (hφ : K[X]⁰ ≤ R[X]⁰.comap φ) (p q : K[X]) :
    map φ hφ (algebraMap _ _ p / algebraMap _ _ q) =
      algebraMap _ _ (φ p) / algebraMap _ _ (φ q) := by
  rcases eq_or_ne q 0 with (rfl | hq)
  · have : (0 : RatFunc K) = algebraMap K[X] _ 0 / algebraMap K[X] _ 1 := by simp
    rw [map_zero, map_zero, map_zero, div_zero, div_zero, this, map_apply_div_ne_zero, map_one,
      map_one, div_one, map_zero, map_zero]
    exact one_ne_zero
  exact map_apply_div_ne_zero _ _ _ _ hq
```

### `Polynomial.taylor_C` (commanddeclaration) at `Mathlib/Data/Polynomial/Taylor.lean`
```lean
@[simp]
theorem taylor_C (x : R) : taylor r (C x) = C x := by simp only [taylor_apply, C_comp]
```

### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `OneHomClass` (commanddeclaration) at `Mathlib/Algebra/Group/Hom/Defs.lean`
```lean
/-- `OneHomClass F M N` states that `F` is a type of one-preserving homomorphisms.
You should extend this typeclass when you extend `OneHom`.
-/
@[to_additive]
class OneHomClass (F : Type*) (M N : outParam Type*) [One M] [One N] [FunLike F M N] : Prop where
  /-- The proposition that the function preserves 1 -/
  map_one : ∀ f : F, f 1 = 1
```
