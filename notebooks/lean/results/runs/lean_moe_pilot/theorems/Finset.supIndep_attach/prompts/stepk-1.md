## Current goal
```
⊢ i ∈ t
```

## Full tactic state
```
α : Type u_1
β : Type u_2
ι : Type u_3
ι' : Type u_4
inst✝¹ : Lattice α
inst✝ : OrderBot α
s t✝ : Finset ι
f : ι → α
i✝ : ι
h : SupIndep (attach s) fun a => f ↑a
t : Finset ι
ht : t ⊆ s
i : ι
his : i ∈ s
hit : i ∉ t
hi : { val := i, property := his } ∈ filter (fun i => ↑i ∈ t) (attach s)
⊢ i ∈ t
```
