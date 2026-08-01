## Current goal
```
⊢ Module.rank (↥(subfield G F)) F ≤ ↑(Fintype.card G)
```

## Full tactic state
```
M : Type u
inst✝⁵ : Monoid M
G : Type u
inst✝⁴ : Group G
F : Type v
inst✝³ : Field F
inst✝² : MulSemiringAction M F
inst✝¹ : MulSemiringAction G F
m : M
inst✝ : Fintype G
⊢ Module.rank (↥(subfield G F)) F ≤ ↑(Fintype.card G)
```

## Proof so far (1 tactic)
```lean
rw [← Cardinal.natCast_le, finrank_eq_rank]
```

## Theorem
`FixedPoints.finrank_le_card` in `Mathlib/FieldTheory/Fixed.lean`

## Premises used in the next tactic
- `FixedPoints.rank_le_card`

## Premise signatures
### `FixedPoints.rank_le_card` (commanddeclaration)
```lean
theorem rank_le_card : Module.rank (FixedPoints.subfield G F) F ≤ Fintype.card G
```

## Premise full source (with proof)
### `FixedPoints.rank_le_card` (commanddeclaration) at `Mathlib/FieldTheory/Fixed.lean`
```lean
theorem rank_le_card : Module.rank (FixedPoints.subfield G F) F ≤ Fintype.card G :=
  rank_le fun s hs => by
    simpa only [rank_fun', Cardinal.mk_coe_finset, Finset.coe_sort_coe, Cardinal.lift_natCast,
      Cardinal.natCast_le] using
      (linearIndependent_smul_of_linearIndependent G F hs).cardinal_lift_le_rank
```

## Transitive premise context (1-hop, 12/12 premises, ≈1787 tokens)
### `rank_le_card` (commanddeclaration) at `Mathlib/LinearAlgebra/Dimension/Basic.lean`
```lean
theorem rank_le_card : Module.rank R M ≤ #M :=
  (Module.rank_def _ _).trans_le (ciSup_le' fun _ ↦ mk_set_le _)
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

### `FixedPoints.subfield` (commanddeclaration) at `Mathlib/FieldTheory/Fixed.lean`
```lean
/-- The subfield of fixed points by a monoid action. -/
def subfield : Subfield F :=
  Subfield.copy (⨅ m : M, FixedBy.subfield F m) (fixedPoints M F)
    (by ext z; simp [fixedPoints, FixedBy.subfield, iInf, Subfield.mem_sInf]; rfl)
```

### `Fintype.card` (commanddeclaration) at `Mathlib/Data/Fintype/Card.lean`
```lean
/-- `card α` is the number of elements in `α`, defined when `α` is a fintype. -/
def card (α) [Fintype α] : ℕ :=
  (@univ α _).card
```

### `rank_le` (commanddeclaration) at `Mathlib/LinearAlgebra/Dimension/Finite.lean`
```lean
theorem rank_le {n : ℕ}
    (H : ∀ s : Finset M, (LinearIndependent R fun i : s => (i : M)) → s.card ≤ n) :
    Module.rank R M ≤ n := by
  rw [Module.rank_def]
  apply ciSup_le'
  rintro ⟨s, li⟩
  exact linearIndependent_bounded_of_finset_linearIndependent_bounded H _ li
```

### `rank_fun'` (commanddeclaration) at `Mathlib/LinearAlgebra/Dimension/Constructions.lean`
```lean
theorem rank_fun' : Module.rank R (η → R) = Fintype.card η := by
  rw [rank_fun_eq_lift_mul, rank_self, Cardinal.lift_one, mul_one]
```

### `Cardinal.mk_coe_finset` (commanddeclaration) at `Mathlib/SetTheory/Cardinal/Basic.lean`
```lean
theorem mk_coe_finset {α : Type u} {s : Finset α} : #s = ↑(Finset.card s) := by simp
```

### `Finset.coe_sort_coe` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
@[simp, norm_cast]
theorem coe_sort_coe (s : Finset α) : ((s : Set α) : Sort _) = s :=
  rfl
```

### `Cardinal.lift_natCast` (commanddeclaration) at `Mathlib/SetTheory/Cardinal/Basic.lean`
```lean
@[simp]
theorem lift_natCast (n : ℕ) : lift.{u} (n : Cardinal.{v}) = n := by induction n <;> simp [*]
```

### `Cardinal.natCast_le` (commanddeclaration) at `Mathlib/SetTheory/Cardinal/Basic.lean`
```lean
@[norm_cast]
theorem natCast_le {m n : ℕ} : (m : Cardinal) ≤ n ↔ m ≤ n := by
  rw [← lift_mk_fin, ← lift_mk_fin, lift_le, le_def, Function.Embedding.nonempty_iff_card_le,
    Fintype.card_fin, Fintype.card_fin]
```

### `FixedPoints.linearIndependent_smul_of_linearIndependent` (commanddeclaration) at `Mathlib/FieldTheory/Fixed.lean`
```lean
theorem linearIndependent_smul_of_linearIndependent {s : Finset F} :
    (LinearIndependent (FixedPoints.subfield G F) fun i : (s : Set F) => (i : F)) →
      LinearIndependent F fun i : (s : Set F) => MulAction.toFun G F i := by
  haveI : IsEmpty ((∅ : Finset F) : Set F) := by simp
  refine' Finset.induction_on s (fun _ => linearIndependent_empty_type) fun a s has ih hs => _
  rw [coe_insert] at hs ⊢
  rw [linearIndependent_insert (mt mem_coe.1 has)] at hs
  rw [linearIndependent_insert' (mt mem_coe.1 has)]; refine' ⟨ih hs.1, fun ha => _⟩
  rw [Finsupp.mem_span_image_iff_total] at ha; rcases ha with ⟨l, hl, hla⟩
  rw [Finsupp.total_apply_of_mem_supported F hl] at hla
  suffices ∀ i ∈ s, l i ∈ FixedPoints.subfield G F by
    replace hla := (sum_apply _ _ fun i => l i • toFun G F i).symm.trans (congr_fun hla 1)
    simp_rw [Pi.smul_apply, toFun_apply, one_smul] at hla
    refine' hs.2 (hla ▸ Submodule.sum_mem _ fun c hcs => _)
    change (⟨l c, this c hcs⟩ : FixedPoints.subfield G F) • c ∈ _
    exact Submodule.smul_mem _ _ (Submodule.subset_span <| mem_coe.2 hcs)
  intro i his g
  refine'
    eq_of_sub_eq_zero
      (linearIndependent_iff'.1 (ih hs.1) s.attach (fun i => g • l i - l i) _ ⟨i, his⟩
          (mem_attach _ _) :
        _)
  refine' (sum_attach s fun i ↦ (g • l i - l i) • MulAction.toFun G F i).trans _
  ext g'; dsimp only
  conv_lhs =>
    rw [sum_apply]
    congr
    · skip
    · ext
      rw [Pi.smul_apply, sub_smul, smul_eq_mul]
  rw [sum_sub_distrib, Pi.zero_apply, sub_eq_zero]
  conv_lhs =>
    congr
    · skip
    · ext x
      rw [toFun_apply, ← mul_inv_cancel_left g g', mul_smul, ← smul_mul', ← toFun_apply _ x]
  show
    (∑ x in s, g • (fun y => l y • MulAction.toFun G F y) x (g⁻¹ * g')) =
      ∑ x in s, (fun y => l y • MulAction.toFun G F y) x g'
  rw [← smul_sum, ← sum_apply _ _ fun y => l y • toFun G F y, ←
    sum_apply _ _ fun y => l y • toFun G F y]
  rw [hla, toFun_apply, toFun_apply, smul_smul, mul_inv_cancel_left]
```

### `LinearIndependent.cardinal_lift_le_rank` (commanddeclaration) at `Mathlib/LinearAlgebra/Dimension/Basic.lean`
```lean
theorem cardinal_lift_le_rank {ι : Type w} {v : ι → M}
    (hv : LinearIndependent R v) :
    Cardinal.lift.{v} #ι ≤ Cardinal.lift.{w} (Module.rank R M) := by
  rw [Module.rank]
  refine le_trans ?_ (lift_le.mpr <| le_ciSup (bddAbove_range.{v, v} _) ⟨_, hv.coe_range⟩)
  exact lift_mk_le'.mpr ⟨(Equiv.ofInjective _ hv.injective).toEmbedding⟩
```
