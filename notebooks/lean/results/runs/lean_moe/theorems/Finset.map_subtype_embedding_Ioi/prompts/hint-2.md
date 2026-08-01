## Current goal
```
⊢ map (Embedding.subtype p) (Finset.subtype p (Ioi ↑a)) = Ioi ↑a
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝² : Preorder α
p : α → Prop
inst✝¹ : DecidablePred p
inst✝ : LocallyFiniteOrderTop α
a : Subtype p
hp : ∀ ⦃a x : α⦄, a ≤ x → p a → p x
⊢ map (Embedding.subtype p) (Finset.subtype p (Ioi ↑a)) = Ioi ↑a
```

## Proof so far (1 tactic)
```lean
rw [subtype_Ioi_eq]
```

## Theorem
`Finset.map_subtype_embedding_Ioi` in `Mathlib/Order/LocallyFinite.lean`

## Premises used in the next tactic
- `Finset.subtype_map_of_mem`
- `Finset.mem_Ioi`
- `LT.lt.le`

## Premise signatures
### `Finset.subtype_map_of_mem` (commanddeclaration)
```lean
theorem subtype_map_of_mem {p : α → Prop} [DecidablePred p] {s : Finset α} (h : ∀ x ∈ s, p x) :
    (s.subtype p).map (Embedding.subtype _) = s
```

### `Finset.mem_Ioi` (commanddeclaration)
```lean
@[simp]
theorem mem_Ioi : x ∈ Ioi a ↔ a < x
```

### `LT.lt.le` (stdtacticaliasalias)
```lean
alias LT.lt.le
```

## Premise full source (with proof)
### `Finset.subtype_map_of_mem` (commanddeclaration) at `Mathlib/Data/Finset/Image.lean`
```lean
/-- If all elements of a `Finset` satisfy the predicate `p`,
`s.subtype p` converts back to `s` with `Embedding.subtype`. -/
theorem subtype_map_of_mem {p : α → Prop} [DecidablePred p] {s : Finset α} (h : ∀ x ∈ s, p x) :
    (s.subtype p).map (Embedding.subtype _) = s := ext <| by simpa [subtype_map] using h
```

### `Finset.mem_Ioi` (commanddeclaration) at `Mathlib/Order/LocallyFinite.lean`
```lean
@[simp]
theorem mem_Ioi : x ∈ Ioi a ↔ a < x :=
  LocallyFiniteOrderTop.finset_mem_Ioi _ _
```

### `LT.lt.le` (stdtacticaliasalias) at `Mathlib/Order/Basic.lean`
```lean
alias LT.lt.le := le_of_lt

alias LT.lt.trans := lt_trans

alias LT.lt.trans' := lt_trans'

alias LT.lt.trans_le := lt_of_lt_of_le

alias LT.lt.trans_le' := lt_of_lt_of_le'

alias LT.lt.ne := ne_of_lt
```
