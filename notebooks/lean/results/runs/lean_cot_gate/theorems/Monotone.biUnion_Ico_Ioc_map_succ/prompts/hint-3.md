## Current goal
```
⊢ ⋃ i ∈ Ico m (succ k), Ioc (f i) (f (succ i)) = Ioc (f k) (f (succ k)) ∪ ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i))
```

## Full tactic state
```
case neg
α : Type u_1
β : Type u_2
inst✝³ : LinearOrder α
inst✝² : SuccOrder α
inst✝¹ : IsSuccArchimedean α
inst✝ : LinearOrder β
f : α → β
hf : Monotone f
m n : α
hmn : m ≤ n
k : α
hmk : m ≤ k
ihk : ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i)) = Ioc (f m) (f k)
hk : ¬IsMax k
⊢ ⋃ i ∈ Ico m (succ k), Ioc (f i) (f (succ i)) = Ioc (f k) (f (succ k)) ∪ ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i))
```

## Proof so far (8 tactics)
```lean
rcases le_total n m with hnm | hmn
rw [Ico_eq_empty_of_le hnm, Ioc_eq_empty_of_le (hf hnm), biUnion_empty]
refine' Succ.rec _ _ hmn
simp only [Ioc_self, Ico_self, biUnion_empty]
intro k hmk ihk
rw [← Ioc_union_Ioc_eq_Ioc (hf hmk) (hf <| le_succ _), union_comm, ← ihk]
by_cases hk : IsMax k
rw [hk.succ_eq, Ioc_self, empty_union]
```

## Theorem
`Monotone.biUnion_Ico_Ioc_map_succ` in `Mathlib/Order/SuccPred/IntervalSucc.lean`

## Premises used in the next tactic
- `Order.Ico_succ_right_eq_insert_of_not_isMax`
- `Set.biUnion_insert`

## Premise signatures
### `Order.Ico_succ_right_eq_insert_of_not_isMax` (commanddeclaration)
```lean
theorem Ico_succ_right_eq_insert_of_not_isMax (h₁ : a ≤ b) (h₂ : ¬IsMax b) :
    Ico a (succ b) = insert b (Ico a b)
```

### `Set.biUnion_insert` (commanddeclaration)
```lean
theorem biUnion_insert (a : α) (s : Set α) (t : α → Set β) :
    ⋃ x ∈ insert a s, t x = t a ∪ ⋃ x ∈ s, t x
```

## Premise full source (with proof)
### `Order.Ico_succ_right_eq_insert_of_not_isMax` (commanddeclaration) at `Mathlib/Order/SuccPred/Basic.lean`
```lean
theorem Ico_succ_right_eq_insert_of_not_isMax (h₁ : a ≤ b) (h₂ : ¬IsMax b) :
    Ico a (succ b) = insert b (Ico a b) := by
  simp_rw [← Iio_inter_Ici, Iio_succ_eq_insert_of_not_isMax h₂, insert_inter_of_mem (mem_Ici.2 h₁)]
```

### `Set.biUnion_insert` (commanddeclaration) at `Mathlib/Data/Set/Lattice.lean`
```lean
theorem biUnion_insert (a : α) (s : Set α) (t : α → Set β) :
    ⋃ x ∈ insert a s, t x = t a ∪ ⋃ x ∈ s, t x := by simp
```

## Transitive premise context (1-hop, 3/3 premises, ≈255 tokens)
### `IsMax` (commanddeclaration) at `Mathlib/Order/Max.lean`
```lean
/-- `a` is a maximal element of `α` if no element is strictly greater than it. We spell it without
`<` to avoid having to convert between `≤` and `<`. Instead, `isMax_iff_forall_not_lt` does the
conversion. -/
def IsMax (a : α) : Prop :=
  ∀ ⦃b⦄, a ≤ b → b ≤ a
```

### `Set.Iio_inter_Ici` (commanddeclaration) at `Mathlib/Data/Set/Intervals/Basic.lean`
```lean
theorem Iio_inter_Ici : Iio a ∩ Ici b = Ico b a :=
  inter_comm _ _
```

### `Order.Iio_succ_eq_insert_of_not_isMax` (commanddeclaration) at `Mathlib/Order/SuccPred/Basic.lean`
```lean
theorem Iio_succ_eq_insert_of_not_isMax (h : ¬IsMax a) : Iio (succ a) = insert a (Iio a) :=
  ext fun _ => lt_succ_iff_eq_or_lt_of_not_isMax h
```
