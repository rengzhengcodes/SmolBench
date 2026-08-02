## Current goal
```
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (algebraMap F[X] (LaurentSeries F)) p / (algebraMap F[X] (LaurentSeries F)) q
```

## Full tactic state
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (algebraMap F[X] (LaurentSeries F)) p / (algebraMap F[X] (LaurentSeries F)) q
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`RatFunc.algebraMap_apply_div` in `Mathlib/FieldTheory/RatFunc.lean`

## Premises used in the next tactic
- `RatFunc.coe_div`
- `algebraMap`
- `RatFunc`
- `algebraMap`
- `RatFunc`
- `RatFunc.mk_one`
- `RatFunc.coe_def`
- `RatFunc.coeAlgHom`
- `RatFunc.mk_eq_div`
- `RatFunc.liftAlgHom_apply_div`
- `map_one`
- `div_one`
- `Algebra.ofId_apply`

## Premise signatures
### `RatFunc.coe_div` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem coe_div :
    ((f / g : RatFunc F) : LaurentSeries F) = (f : LaurentSeries F) / (g : LaurentSeries F)
```

### `algebraMap` (commanddeclaration)
```lean
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A
```

### `RatFunc` (commanddeclaration)
```lean
structure RatFunc [CommRing K] : Type u where ofFractionRing ::
  toFractionRing : FractionRing K[X]
```

### `algebraMap` (commanddeclaration)
```lean
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A
```

### `RatFunc` (commanddeclaration)
```lean
structure RatFunc [CommRing K] : Type u where ofFractionRing ::
  toFractionRing : FractionRing K[X]
```

### `RatFunc.mk_one` (commanddeclaration)
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x
```

### `RatFunc.coe_def` (commanddeclaration)
```lean
theorem coe_def : (f : LaurentSeries F) = coeAlgHom F f
```

### `RatFunc.coeAlgHom` (commanddeclaration)
```lean
def coeAlgHom (F : Type u) [Field F] : RatFunc F →ₐ[F[X]] LaurentSeries F
```

### `RatFunc.mk_eq_div` (commanddeclaration)
```lean
@[simp]
theorem mk_eq_div (p q : K[X]) : RatFunc.mk p q = algebraMap _ _ p / algebraMap _ _ q
```

### `RatFunc.liftAlgHom_apply_div` (commanddeclaration)
```lean
theorem liftAlgHom_apply_div (p q : K[X]) :
    liftAlgHom φ hφ (algebraMap _ _ p / algebraMap _ _ q) = φ p / φ q
```

### `map_one` (commanddeclaration)
```lean
@[to_additive (attr := simp)]
theorem map_one [OneHomClass F M N] (f : F) : f 1 = 1
```

### `div_one` (commanddeclaration)
```lean
@[to_additive (attr := simp)]
theorem div_one (a : G) : a / 1 = a
```

### `Algebra.ofId_apply` (commanddeclaration)
```lean
theorem ofId_apply (r) : ofId R A r = algebraMap R A r
```

## Premise full source (with proof)
### `RatFunc.coe_div` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
@[simp, norm_cast]
theorem coe_div :
    ((f / g : RatFunc F) : LaurentSeries F) = (f : LaurentSeries F) / (g : LaurentSeries F) :=
  map_div₀ (coeAlgHom F) _ _
```

### `algebraMap` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- Embedding `R →+* A` given by `Algebra` structure. -/
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A :=
  Algebra.toRingHom
```

### `RatFunc` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- `RatFunc K` is `K(X)`, the field of rational functions over `K`.

The inclusion of polynomials into `RatFunc` is `algebraMap K[X] (RatFunc K)`,
the maps between `RatFunc K` and another field of fractions of `K[X]`,
especially `FractionRing K[X]`, are given by `IsLocalization.algEquiv`.
-/
structure RatFunc [CommRing K] : Type u where ofFractionRing ::
  toFractionRing : FractionRing K[X]
```

### `algebraMap` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- Embedding `R →+* A` given by `Algebra` structure. -/
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A :=
  Algebra.toRingHom
```

### `RatFunc` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- `RatFunc K` is `K(X)`, the field of rational functions over `K`.

The inclusion of polynomials into `RatFunc` is `algebraMap K[X] (RatFunc K)`,
the maps between `RatFunc K` and another field of fractions of `K[X]`,
especially `FractionRing K[X]`, are given by `IsLocalization.algEquiv`.
-/
structure RatFunc [CommRing K] : Type u where ofFractionRing ::
  toFractionRing : FractionRing K[X]
```

### `RatFunc.mk_one` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x :=
  rfl
```

### `RatFunc.coe_def` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem coe_def : (f : LaurentSeries F) = coeAlgHom F f :=
  rfl
```

### `RatFunc.coeAlgHom` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- The coercion `RatFunc F → LaurentSeries F` as bundled alg hom. -/
def coeAlgHom (F : Type u) [Field F] : RatFunc F →ₐ[F[X]] LaurentSeries F :=
  liftAlgHom (Algebra.ofId _ _) <|
    nonZeroDivisors_le_comap_nonZeroDivisors_of_injective _ <|
      Polynomial.algebraMap_hahnSeries_injective _
```

### `RatFunc.mk_eq_div` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
@[simp]
theorem mk_eq_div (p q : K[X]) : RatFunc.mk p q = algebraMap _ _ p / algebraMap _ _ q := by
  simp only [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

### `RatFunc.liftAlgHom_apply_div` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem liftAlgHom_apply_div (p q : K[X]) :
    liftAlgHom φ hφ (algebraMap _ _ p / algebraMap _ _ q) = φ p / φ q :=
  liftMonoidWithZeroHom_apply_div _ hφ _ _  -- Porting note: gave explicitly the `hφ`
```

### `map_one` (commanddeclaration) at `Mathlib/Algebra/Group/Hom/Defs.lean`
```lean
@[to_additive (attr := simp)]
theorem map_one [OneHomClass F M N] (f : F) : f 1 = 1 :=
  OneHomClass.map_one f
```

### `div_one` (commanddeclaration) at `Mathlib/Algebra/Group/Basic.lean`
```lean
@[to_additive (attr := simp)]
theorem div_one (a : G) : a / 1 = a := by simp [div_eq_mul_inv]
```

### `Algebra.ofId_apply` (commanddeclaration) at `Mathlib/Algebra/Algebra/Hom.lean`
```lean
theorem ofId_apply (r) : ofId R A r = algebraMap R A r :=
  rfl
```

## Transitive premise context (1-hop, 23/23 premises, ≈2684 tokens)
### `LaurentSeries` (commanddeclaration) at `Mathlib/RingTheory/LaurentSeries.lean`
```lean
/-- A `LaurentSeries` is implemented as a `HahnSeries` with value group `ℤ`. -/
abbrev LaurentSeries (R : Type*) [Zero R] :=
  HahnSeries ℤ R
```

### `map_div` (commanddeclaration) at `Mathlib/Algebra/Group/Hom/Defs.lean`
```lean
/-- Group homomorphisms preserve division. -/
@[to_additive (attr := simp) "Additive group homomorphisms preserve subtraction."]
theorem map_div [Group G] [DivisionMonoid H] [MonoidHomClass F G H] (f : F) :
    ∀ a b, f (a / b) = f a / f b := map_div' _ <| map_inv f
```

### `Embedding` (commanddeclaration) at `Mathlib/Topology/Defs/Induced.lean`
```lean
/-- A function between topological spaces is an embedding if it is injective,
  and for all `s : Set X`, `s` is open iff it is the preimage of an open set. -/
@[mk_iff]
structure Embedding [TopologicalSpace X] [TopologicalSpace Y] (f : X → Y) extends
  Inducing f : Prop where
  /-- A topological embedding is injective. -/
  inj : Function.Injective f
```

### `Algebra` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- An associative unital `R`-algebra is a semiring `A` equipped with a map into its center `R → A`.

See the implementation notes in this file for discussion of the details of this definition.
-/
-- Porting note: unsupported @[nolint has_nonempty_instance]
class Algebra (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] extends SMul R A,
  R →+* A where
  commutes' : ∀ r x, toRingHom r * x = x * toRingHom r
  smul_def' : ∀ r x, r • x = toRingHom r * x
```

### `CommSemiring` (commanddeclaration) at `Mathlib/Algebra/Ring/Defs.lean`
```lean
class CommSemiring (R : Type u) extends Semiring R, CommMonoid R
```

### `Semiring` (commanddeclaration) at `Mathlib/Algebra/Ring/Defs.lean`
```lean
/-- A `Semiring` is a type with addition, multiplication, a `0` and a `1` where addition is
commutative and associative, multiplication is associative and left and right distributive over
addition, and `0` and `1` are additive and multiplicative identities. -/
class Semiring (α : Type u) extends NonUnitalSemiring α, NonAssocSemiring α, MonoidWithZero α
```

### `FractionRing` (commanddeclaration) at `Mathlib/RingTheory/Localization/FractionRing.lean`
```lean
/-- The fraction ring of a commutative ring `R` as a quotient type.

We instantiate this definition as generally as possible, and assume that the
commutative ring `R` is an integral domain only when this is needed for proving.

In this generality, this construction is also known as the *total fraction ring* of `R`.
-/
@[reducible]
def FractionRing :=
  Localization (nonZeroDivisors R)
```

### `IsLocalization.algEquiv` (commanddeclaration) at `Mathlib/RingTheory/Localization/Basic.lean`
```lean
/-- If `S`, `Q` are localizations of `R` at the submonoid `M` respectively,
there is an isomorphism of localizations `S ≃ₐ[R] Q`. -/
@[simps!]
noncomputable def algEquiv : S ≃ₐ[R] Q :=
  { ringEquivOfRingEquiv S Q (RingEquiv.refl R) M.map_id with
    commutes' := ringEquivOfRingEquiv_eq _ }
```

### `CommRing` (commanddeclaration) at `Mathlib/Algebra/Ring/Defs.lean`
```lean
class CommRing (α : Type u) extends Ring α, CommMonoid α
```

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

### `FirstOrder.Language.Theory.Model.bundled` (commanddeclaration) at `Mathlib/ModelTheory/Bundled.lean`
```lean
/-- Bundles `M ⊨ T` as a `T.ModelType`. -/
def Model.bundled {M : Type w} [LM : L.Structure M] [ne : Nonempty M] (h : M ⊨ T) : T.ModelType :=
  @ModelType.of L T M LM h ne
```

### `Field` (commanddeclaration) at `Mathlib/Algebra/Field/Defs.lean`
```lean
/-- A `Field` is a `CommRing` with multiplicative inverses for nonzero elements.

An instance of `Field K` includes maps `ratCast : ℚ → K` and `qsmul : ℚ → K → K`.
Those two fields are needed to implement the `DivisionRing K → Algebra ℚ K` instance since we need
to control the specific definitions for some special cases of `K` (in particular `K = ℚ` itself).
See also note [forgetful inheritance].

If the field has positive characteristic `p`, our division by zero convention forces
`ratCast (1 / p) = 1 / 0 = 0`. -/
class Field (K : Type u) extends CommRing K, DivisionRing K
```

### `Algebra.ofId` (commanddeclaration) at `Mathlib/Algebra/Algebra/Hom.lean`
```lean
/-- `AlgebraMap` as an `AlgHom`. -/
def ofId : R →ₐ[R] A :=
  { algebraMap R A with commutes' := fun _ => rfl }
```

### `nonZeroDivisors_le_comap_nonZeroDivisors_of_injective` (commanddeclaration) at `Mathlib/Algebra/GroupWithZero/NonZeroDivisors.lean`
```lean
theorem nonZeroDivisors_le_comap_nonZeroDivisors_of_injective [NoZeroDivisors M']
    [MonoidWithZeroHomClass F M M'] (f : F) (hf : Function.Injective f) : M⁰ ≤ M'⁰.comap f :=
  Submonoid.le_comap_of_map_le _ (map_le_nonZeroDivisors_of_injective _ hf le_rfl)
```

### `Polynomial.algebraMap_hahnSeries_injective` (commanddeclaration) at `Mathlib/RingTheory/HahnSeries/PowerSeries.lean`
```lean
theorem _root_.Polynomial.algebraMap_hahnSeries_injective :
    Function.Injective (algebraMap R[X] (HahnSeries Γ R)) :=
  ofPowerSeries_injective.comp (Polynomial.coe_injective R)
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

### `RatFunc.liftMonoidWithZeroHom_apply_div` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem liftMonoidWithZeroHom_apply_div {L : Type*} [CommGroupWithZero L]
    (φ : MonoidWithZeroHom K[X] L) (hφ : K[X]⁰ ≤ L⁰.comap φ) (p q : K[X]) :
    liftMonoidWithZeroHom φ hφ (algebraMap _ _ p / algebraMap _ _ q) = φ p / φ q := by
  rcases eq_or_ne q 0 with (rfl | hq)
  · simp only [div_zero, map_zero]
  simp only [← mk_eq_div, mk_eq_localization_mk _ hq,
    liftMonoidWithZeroHom_apply_ofFractionRing_mk]
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

### `div_eq_mul_inv` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
/-- Dividing by an element is the same as multiplying by its inverse.

This is a duplicate of `DivInvMonoid.div_eq_mul_inv` ensuring that the types unfold better.
-/
@[to_additive "Subtracting an element is the same as adding by its negative.
This is a duplicate of `SubNegMonoid.sub_eq_mul_neg` ensuring that the types unfold better."]
theorem div_eq_mul_inv (a b : G) : a / b = a * b⁻¹ :=
  DivInvMonoid.div_eq_mul_inv _ _
```
