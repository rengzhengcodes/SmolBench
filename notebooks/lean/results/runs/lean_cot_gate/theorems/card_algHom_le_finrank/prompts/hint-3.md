## Current goal
```
⊢ Module.rank K M < ℵ₀
```

## Full tactic state
```
R : Type u
S : Type u'
M✝ : Type v
N : Type w
K : Type u_1
M : Type u_2
L : Type v
inst✝⁷ : CommRing K
inst✝⁶ : Ring M
inst✝⁵ : Algebra K M
inst✝⁴ : Module.Free K M
inst✝³ : Module.Finite K M
inst✝² : CommRing L
inst✝¹ : IsDomain L
inst✝ : Algebra K L
this : Nontrivial K
⊢ Module.rank K M < ℵ₀
```

## Proof so far (4 tactics)
```lean
convert toNat_le_toNat (cardinal_mk_algHom_le_rank K M L) ?_
rw [toNat_lift, finrank]
rw [lift_lt_aleph0]
have := Module.nontrivial K L
```

## Theorem
`card_algHom_le_finrank` in `Mathlib/LinearAlgebra/FreeModule/Finite/Matrix.lean`

## Premises used in the next tactic
- `rank_lt_aleph0`

## Premise signatures
### `rank_lt_aleph0` (commanddeclaration)
```lean
theorem rank_lt_aleph0 [Module.Finite R M] : Module.rank R M < ℵ₀
```

## Premise full source (with proof)
### `rank_lt_aleph0` (commanddeclaration) at `Mathlib/LinearAlgebra/Dimension/StrongRankCondition.lean`
```lean
/-- The rank of a finite module is finite. -/
theorem rank_lt_aleph0 [Module.Finite R M] : Module.rank R M < ℵ₀ := by
  simp only [Module.rank_def]
  -- Porting note: can't use `‹_›` as that pulls the unused `N` into the context
  obtain ⟨S, hS⟩ := Module.finite_def.mp ‹Module.Finite R M›
  refine' (ciSup_le' fun i => _).trans_lt (nat_lt_aleph0 S.card)
  exact linearIndependent_le_span_finset _ i.prop S hS
```

## Transitive premise context (1-hop, 6/6 premises, ≈788 tokens)
### `Module.Finite` (commanddeclaration) at `Mathlib/RingTheory/Finiteness.lean`
```lean
/-- A module over a semiring is `Finite` if it is finitely generated as a module. -/
class Module.Finite [Semiring R] [AddCommMonoid M] [Module R M] : Prop where
  out : (⊤ : Submodule R M).FG
```

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

### `ciSup_le'` (commanddeclaration) at `Mathlib/Order/ConditionallyCompleteLattice/Basic.lean`
```lean
theorem ciSup_le' {f : ι → α} {a : α} (h : ∀ i, f i ≤ a) : ⨆ i, f i ≤ a :=
  csSup_le' <| forall_mem_range.2 h
```

### `Cardinal.nat_lt_aleph0` (commanddeclaration) at `Mathlib/SetTheory/Cardinal/Basic.lean`
```lean
theorem nat_lt_aleph0 (n : ℕ) : (n : Cardinal.{u}) < ℵ₀ :=
  succ_le_iff.1
    (by
      rw [← nat_succ, ← lift_mk_fin, aleph0, lift_mk_le.{u}]
      exact ⟨⟨(↑), fun a b => Fin.ext⟩⟩)
```

### `linearIndependent_le_span_finset` (commanddeclaration) at `Mathlib/LinearAlgebra/Dimension/StrongRankCondition.lean`
```lean
/-- A version of `linearIndependent_le_span` for `Finset`. -/
theorem linearIndependent_le_span_finset {ι : Type*} (v : ι → M) (i : LinearIndependent R v)
    (w : Finset M) (s : span R (w : Set M) = ⊤) : #ι ≤ w.card := by
  simpa only [Finset.coe_sort_coe, Fintype.card_coe] using linearIndependent_le_span v i w s
```
