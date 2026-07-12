## Current goal
```
⊢ { toFractionRing := (algebraMap K[X] (FractionRing K[X])) x } = (algebraMap K[X] (RatFunc K)) x
```

## Full tactic state
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
x : K[X]
⊢ { toFractionRing := (algebraMap K[X] (FractionRing K[X])) x } = (algebraMap K[X] (RatFunc K)) x
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`RatFunc.ofFractionRing_algebraMap` in `Mathlib/FieldTheory/RatFunc.lean`

## Premises used in the next tactic
- `RatFunc.mk_one`
- `RatFunc.mk_one'`

## Premise signatures
### `RatFunc.mk_one` (commanddeclaration)
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x
```

### `RatFunc.mk_one'` (commanddeclaration)
```lean
theorem mk_one' (p : K[X]) :
    RatFunc.mk p 1 = ofFractionRing (algebraMap K[X] (FractionRing K[X]) p)
```

## Premise full source (with proof)
### `RatFunc.mk_one` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x :=
  rfl
```

### `RatFunc.mk_one'` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_one' (p : K[X]) :
    RatFunc.mk p 1 = ofFractionRing (algebraMap K[X] (FractionRing K[X]) p) := by
  -- Porting note: had to hint `M := K[X]⁰` below
  rw [← IsLocalization.mk'_one (M := K[X]⁰) (FractionRing K[X]) p, ← mk_coe_def, Submonoid.coe_one]
```

## Transitive premise context (1-hop, 8/8 premises, ≈1160 tokens)
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

### `Mathlib.Tactic.Hint.hint` (commanddeclaration) at `Mathlib/Tactic/Hint.lean`
```lean
/--
Run all tactics registered using `register_hint`.
Print a "Try these:" suggestion for each of the successful tactics.

If one tactic succeeds and closes the goal, we don't look at subsequent tactics.
-/
-- TODO We could run the tactics in parallel.
-- TODO With widget support, could we run the tactics in parallel
--      and do live updates of the widget as results come in?
def hint (stx : Syntax) : TacticM Unit := do
  let tacs := Nondet.ofList (← getHints)
  let results := tacs.filterMapM fun t : TSyntax `tactic => do
    if let some msgs ← observing? (withMessageLog (withoutInfoTrees (evalTactic t))) then
      return some (← getGoals, ← suggestion t msgs)
    else
      return none
  let results ← (results.toMLList.takeUpToFirst fun r => r.1.1.isEmpty).asArray
  let results := results.qsort (·.1.1.length < ·.1.1.length)
  addSuggestions stx (results.map (·.1.2))
  match results.find? (·.1.1.isEmpty) with
  | some r =>
    -- We don't restore the entire state, as that would delete the suggestion messages.
    setMCtx r.2.term.meta.meta.mctx
  | none => admitGoal (← getMainGoal)

/--
The `hint` tactic tries every tactic registered using `register_hint tac`,
and reports any that succeed.
-/
```

### `IsLocalization.mk'_one` (commanddeclaration) at `Mathlib/RingTheory/Localization/Basic.lean`
```lean
theorem mk'_one (x) : mk' S x (1 : M) = algebraMap R S x :=
  (toLocalizationMap M S).mk'_one _
```

### `RatFunc.mk_coe_def` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_coe_def (p : K[X]) (q : K[X]⁰) :
    -- Porting note: filled in `(FractionRing K[X])` that was an underscore.
    RatFunc.mk p q = ofFractionRing (IsLocalization.mk' (FractionRing K[X]) p q) := by
  simp only [mk_eq_div', ← Localization.mk_eq_mk', FractionRing.mk_eq_div]
```

### `Submonoid.coe_one` (commanddeclaration) at `Mathlib/GroupTheory/Submonoid/Operations.lean`
```lean
@[to_additive (attr := simp, norm_cast)]
theorem coe_one : ((1 : S) : M) = 1 :=
  rfl
```
