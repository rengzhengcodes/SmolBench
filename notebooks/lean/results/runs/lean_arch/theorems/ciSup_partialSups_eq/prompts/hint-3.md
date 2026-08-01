## Current goal
```
⊢ BddAbove (Set.range fun n => (partialSups f) n)
```

## Full tactic state
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range fun n => (partialSups f) n)
```

## Proof so far (3 tactics)
```lean
refine' (ciSup_le fun n => _).antisymm (ciSup_mono _ <| le_partialSups f)
rw [partialSups_eq_ciSup_Iic]
exact ciSup_le fun i => le_ciSup h _
```

## Theorem
`ciSup_partialSups_eq` in `Mathlib/Order/PartialSups.lean`

## Premises used in the next tactic
- `bddAbove_range_partialSups`

## Premise signatures
### `bddAbove_range_partialSups` (commanddeclaration)
```lean
@[simp]
theorem bddAbove_range_partialSups {f : ℕ → α} :
    BddAbove (Set.range (partialSups f)) ↔ BddAbove (Set.range f)
```

## Premise full source (with proof)
### `bddAbove_range_partialSups` (commanddeclaration) at `Mathlib/Order/PartialSups.lean`
```lean
@[simp]
theorem bddAbove_range_partialSups {f : ℕ → α} :
    BddAbove (Set.range (partialSups f)) ↔ BddAbove (Set.range f) :=
  .of_eq <| congr_arg Set.Nonempty <| upperBounds_range_partialSups f
```

## Transitive premise context (1-hop, 7/7 premises, ≈633 tokens)
### `BddAbove` (commanddeclaration) at `Mathlib/Order/Bounds/Basic.lean`
```lean
/-- A set is bounded above if there exists an upper bound. -/
def BddAbove (s : Set α) :=
  (upperBounds s).Nonempty
```

### `Set.range` (commanddeclaration) at `Mathlib/Data/Set/Defs.lean`
```lean
/-- Range of a function.

This function is more flexible than `f '' univ`, as the image requires that the domain is in Type
and not an arbitrary Sort. -/
def range (f : ι → α) : Set α := {x | ∃ y, f y = x}
```

### `partialSups` (commanddeclaration) at `Mathlib/Order/PartialSups.lean`
```lean
/-- The monotone sequence whose value at `n` is the supremum of the `f m` where `m ≤ n`. -/
def partialSups (f : ℕ → α) : ℕ →o α :=
  ⟨@Nat.rec (fun _ => α) (f 0) fun (n : ℕ) (a : α) => a ⊔ f (n + 1),
    monotone_nat_of_le_succ fun _ => le_sup_left⟩
```

### `of_eq` (commanddeclaration) at `Mathlib/Order/RelClasses.lean`
```lean
theorem of_eq [IsRefl α r] : ∀ {a b}, a = b → r a b
  | _, _, .refl _ => refl _
```

### `congr_arg` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_arg := congrArg
alias congr_arg₂ := congrArg₂
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```

### `Set.Nonempty` (commanddeclaration) at `Mathlib/Init/Set.lean`
```lean
/-- The property `s.Nonempty` expresses the fact that the set `s` is not empty. It should be used
in theorem assumptions instead of `∃ x, x ∈ s` or `s ≠ ∅` as it gives access to a nice API thanks
to the dot notation. -/
protected def Nonempty (s : Set α) : Prop :=
  ∃ x, x ∈ s
```

### `upperBounds_range_partialSups` (lemma) at `Mathlib/Order/PartialSups.lean`
```lean
@[simp]
lemma upperBounds_range_partialSups (f : ℕ → α) :
    upperBounds (Set.range (partialSups f)) = upperBounds (Set.range f) := by
  ext a
  simp only [mem_upperBounds, Set.forall_mem_range, partialSups_le_iff]
  exact ⟨fun h _ ↦ h _ _ le_rfl, fun h _ _ _ ↦ h _⟩
```
