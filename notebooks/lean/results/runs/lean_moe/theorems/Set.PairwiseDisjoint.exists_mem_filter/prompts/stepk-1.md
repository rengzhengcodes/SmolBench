## Current goal
```
⊢ ∃ s, (∀ (i : ι), s i ∈ l i) ∧ PairwiseDisjoint t s
```

## Full tactic state
```
case intro.intro.intro.intro
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι✝ : Sort x
f g : Filter α
s✝ t✝ : Set α
ι : Type u_2
l : ι → Filter α
t : Set ι
hd : PairwiseDisjoint t l
ht : Set.Finite t
this : Finite ↑t
s : (i : ι) → { s // s ∈ l i }
hsd : Pairwise (Disjoint on fun i => ↑((fun i => s ↑i) i))
⊢ ∃ s, (∀ (i : ι), s i ∈ l i) ∧ PairwiseDisjoint t s
```
