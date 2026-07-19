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
