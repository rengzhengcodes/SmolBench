## Current goal
```
⊢ m < Max.max n m + 1
```

## Full tactic state
```
case mk.coeq.intro.mk.intro.mk.refine'_2
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : IsFilteredOrEmpty C
α : Type w
f : α → C
j : C
n : ℕ
x : (CategoryTheory.IsFiltered.FilteredClosureSmall.bundledAbstractFilteredClosure f n).fst
hj₁ :
  FilteredClosure f
    (CategoryTheory.IsFiltered.FilteredClosureSmall.abstractFilteredClosureRealization f { fst := n, snd := x })
m : ℕ
y : (CategoryTheory.IsFiltered.FilteredClosureSmall.bundledAbstractFilteredClosure f m).fst
hj₂ :
  FilteredClosure f
    (CategoryTheory.IsFiltered.FilteredClosureSmall.abstractFilteredClosureRealization f { fst := m, snd := y })
g g' :
  CategoryTheory.IsFiltered.FilteredClosureSmall.abstractFilteredClosureRealization f { fst := n, snd := x } ⟶
    CategoryTheory.IsFiltered.FilteredClosureSmall.abstractFilteredClosureRealization f { fst := m, snd := y }
⊢ m < Max.max n m + 1
```

## Proof so far (15 tactics)
```lean
refine' small_of_injective_of_exists (FilteredClosureSmall.abstractFilteredClosureRealization f)
  FullSubcategory.ext _
rintro ⟨j, h⟩
induction h with
| base x => exact ⟨⟨0, ⟨x⟩⟩, rfl⟩
| max hj₁ hj₂ ih ih' =>
  rcases ih with ⟨⟨n, x⟩, rfl⟩
  rcases ih' with ⟨⟨m, y⟩, rfl⟩
  refine' ⟨⟨(Max.max n m).succ, FilteredClosureSmall.InductiveStep.max _ _ x y⟩, rfl⟩
  all_goals apply Nat.lt_succ_of_le
  exacts [Nat.le_max_left _ _, Nat.le_max_right _ _]
| coeq hj₁ hj₂ g g' ih ih' =>
  rcases ih with ⟨⟨n, x⟩, rfl⟩
  rcases ih' with ⟨⟨m, y⟩, rfl⟩
  refine' ⟨⟨(Max.max n m).succ, FilteredClosureSmall.InductiveStep.coeq _ _ x y g g'⟩, rfl⟩
  all_goals apply Nat.lt_succ_of_le
  exacts [Nat.le_max_left _ _, Nat.le_max_right _ _]
exact ⟨⟨0, ⟨x⟩⟩, rfl⟩
rcases ih with ⟨⟨n, x⟩, rfl⟩
rcases ih' with ⟨⟨m, y⟩, rfl⟩
refine' ⟨⟨(Max.max n m).succ, FilteredClosureSmall.InductiveStep.max _ _ x y⟩, rfl⟩
all_goals apply Nat.lt_succ_of_le
exacts [Nat.le_max_left _ _, Nat.le_max_right _ _]
apply Nat.lt_succ_of_le
rcases ih with ⟨⟨n, x⟩, rfl⟩
rcases ih' with ⟨⟨m, y⟩, rfl⟩
refine' ⟨⟨(Max.max n m).succ, FilteredClosureSmall.InductiveStep.coeq _ _ x y g g'⟩, rfl⟩
all_goals apply Nat.lt_succ_of_le
exacts [Nat.le_max_left _ _, Nat.le_max_right _ _]
```

## Theorem
`CategoryTheory.IsFiltered.small_fullSubcategory_filteredClosure` in `Mathlib/CategoryTheory/Filtered/Small.lean`

## Premises used in the next tactic
- `Nat.lt_succ_of_le`

## Premise signatures
### `Nat.lt_succ_of_le` (commanddeclaration)
```lean
theorem lt_succ_of_le {n m : Nat} : n ≤ m → n < succ m
```

## Premise full source (with proof)
### `Nat.lt_succ_of_le` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
theorem lt_succ_of_le {n m : Nat} : n ≤ m → n < succ m := succ_le_succ
```
