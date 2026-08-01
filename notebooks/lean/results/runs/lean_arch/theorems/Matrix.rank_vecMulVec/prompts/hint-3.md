## Current goal
```
⊢ Module.rank K (Unit → K) = 1
```

## Full tactic state
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
inst✝¹ : Fintype n
inst✝ : DecidableEq n
w : m → K
v : n → K
a✝ : Nontrivial K
⊢ Module.rank K (Unit → K) = 1
```

## Proof so far (4 tactics)
```lean
nontriviality K
rw [Matrix.vecMulVec_eq, Matrix.toLin'_mul]
refine' le_trans (LinearMap.rank_comp_le_left _ _) _
refine' (LinearMap.rank_le_domain _).trans_eq _
```

## Theorem
`Matrix.rank_vecMulVec` in `Mathlib/LinearAlgebra/FreeModule/Finite/Matrix.lean`

## Premises used in the next tactic
- `rank_fun'`
- `Fintype.card_unit`
- `Nat.cast_one`

## Premise signatures
### `rank_fun'` (commanddeclaration)
```lean
theorem rank_fun' : Module.rank R (η → R) = Fintype.card η
```

### `Fintype.card_unit` (commanddeclaration)
```lean
theorem Fintype.card_unit : Fintype.card Unit = 1
```

### `Nat.cast_one` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem cast_one [AddMonoidWithOne R] : ((1 : ℕ) : R) = 1
```

## Premise full source (with proof)
### `rank_fun'` (commanddeclaration) at `Mathlib/LinearAlgebra/Dimension/Constructions.lean`
```lean
theorem rank_fun' : Module.rank R (η → R) = Fintype.card η := by
  rw [rank_fun_eq_lift_mul, rank_self, Cardinal.lift_one, mul_one]
```

### `Fintype.card_unit` (commanddeclaration) at `Mathlib/Data/Fintype/Card.lean`
```lean
theorem Fintype.card_unit : Fintype.card Unit = 1 :=
  rfl
```

### `Nat.cast_one` (commanddeclaration) at `Mathlib/Data/Nat/Cast/Defs.lean`
```lean
@[simp, norm_cast]
theorem cast_one [AddMonoidWithOne R] : ((1 : ℕ) : R) = 1 := by
  rw [cast_succ, Nat.cast_zero, zero_add]
```

## Transitive premise context (1-hop, 9/9 premises, ≈1051 tokens)
### `Module.rank` (leanelabcommandcommandirreducibledef) at `Mathlib/LinearAlgebra/Dimension/Basic.lean`
```lean
/-- The rank of a module, defined as a term of type `Cardinal`.

We define this as the supremum of the cardinalities of linearly independent subsets.

For a free module over any ring satisfying the strong rank condition
(e.g. left-noetherian rings, commutative rings, and in particular division rings and fields),
this is the same as the dimension of the space (i.e. the cardinality of any basis).

In particular this agrees with the usual notion of the dimension of a vector space.

-/
protected irreducible_def Module.rank : Cardinal :=
  ⨆ ι : { s : Set M // LinearIndependent R ((↑) : s → M) }, (#ι.1)
```

### `Fintype.card` (commanddeclaration) at `Mathlib/Data/Fintype/Card.lean`
```lean
/-- `card α` is the number of elements in `α`, defined when `α` is a fintype. -/
def card (α) [Fintype α] : ℕ :=
  (@univ α _).card
```

### `rank_fun_eq_lift_mul` (commanddeclaration) at `Mathlib/LinearAlgebra/Dimension/Constructions.lean`
```lean
theorem rank_fun_eq_lift_mul : Module.rank R (η → M) =
    (Fintype.card η : Cardinal.{max u₁' v}) * Cardinal.lift.{u₁'} (Module.rank R M) :=
  by rw [rank_pi, Cardinal.sum_const, Cardinal.mk_fintype, Cardinal.lift_natCast]
```

### `rank_self` (commanddeclaration) at `Mathlib/LinearAlgebra/Dimension/StrongRankCondition.lean`
```lean
@[simp]
theorem rank_self : Module.rank R R = 1 := by
  rw [← Cardinal.lift_inj, ← (Basis.singleton PUnit R).mk_eq_rank, Cardinal.mk_punit]
```

### `Cardinal.lift_one` (commanddeclaration) at `Mathlib/SetTheory/Cardinal/Basic.lean`
```lean
@[simp]
theorem lift_one : lift 1 = 1 := mk_eq_one _
```

### `mul_one` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive (attr := simp)]
theorem mul_one : ∀ a : M, a * 1 = a :=
  MulOneClass.mul_one
```

### `Unit` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
The unit type, the canonical type with one element, named `unit` or `()`.
In other words, it describes only a single value, which consists of said constructor applied
to no arguments whatsoever.
The `Unit` type is similar to `void` in languages derived from C.

`Unit` is actually defined as `PUnit.{1}` where `PUnit` is the universe
polymorphic version. The `Unit` should be preferred over `PUnit` where possible to avoid
unnecessary universe parameters.

In functional programming, `Unit` is the return type of things that "return
nothing", since a type with one element conveys no additional information.
When programming with monads, the type `m Unit` represents an action that has
some side effects but does not return a value, while `m α` would be an action
that has side effects and returns a value of type `α`.
-/
abbrev Unit : Type := PUnit

/--
`Unit.unit : Unit` is the canonical element of the unit type.
It can also be written as `()`.
-/
```

### `AddMonoidWithOne` (commanddeclaration) at `Mathlib/Data/Nat/Cast/Defs.lean`
```lean
/-- An `AddMonoidWithOne` is an `AddMonoid` with a `1`.
It also contains data for the unique homomorphism `ℕ → R`. -/
class AddMonoidWithOne (R : Type u) extends NatCast R, AddMonoid R, One R where
  natCast := Nat.unaryCast
  /-- The canonical map `ℕ → R` sends `0 : ℕ` to `0 : R`. -/
  natCast_zero : natCast 0 = 0 := by intros; rfl
  /-- The canonical map `ℕ → R` is a homomorphism. -/
  natCast_succ : ∀ n, natCast (n + 1) = natCast n + 1 := by intros; rfl
```

### `Nat.cast_zero` (commanddeclaration) at `Mathlib/Data/Nat/Cast/Defs.lean`
```lean
@[simp, norm_cast]
theorem cast_zero : ((0 : ℕ) : R) = 0 :=
  AddMonoidWithOne.natCast_zero
```
