# Set.partiallyWellOrderedOn_insert   (k=0, 1 tactics total)

file: `Mathlib/Order/WellFoundedSet.lean`  

**Ground-truth tail (from k):**
```lean
simp only [← singleton_union, partiallyWellOrderedOn_union,
  partiallyWellOrderedOn_singleton, true_and_iff]
```

**True premises at k:** `Set.singleton_union`, `Set.partiallyWellOrderedOn_union`, `Set.partiallyWellOrderedOn_singleton`, `true_and_iff`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | · |
| `noise:3` | ✘ | · | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.3s, in=312, out=51)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h x hx
    refine' h x (Set.mem_insert_of_mem _ hx)
  · intro h x hx
    cases hx
    · exact IsRefl.refl _ _
    · exact h _ hx
```

**lean_error:** tail step 2/7 ('· intro h x hx'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=286, out=78)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [PartiallyWellOrderedOn, PartiallyWellOrderedOn, wellFoundedOn_insert]
simp only [IsRefl.refl, true_and]
rw [← wellFoundedOn_iff_no_descending_seq]
simp only [no_descending_seq_iff_no_infinite_descending_seq, ←
  IsRefl.refl]
rw [no_infinite_descending_seq_insert]
```

**lean_error:** tail step 1/6 ('rw [PartiallyWellOrderedOn, PartiallyWellOrderedOn, wellFoundedOn_insert]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.4s, in=301, out=56)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  intro h
  apply h.subset
  intro x
  exact subset_insert s
next
  intro h
  apply partiallyWellOrderedOn.insert
  exact h
  intro x
  exact irrefl r a
```

**lean_error:** tail step 3/11 ('apply h.subset'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=851, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleton_union],
rw partiallyWellOrderedOn_union,
rw partiallyWellOrderedOn_singleton,
rw true_and_iff
```

**lean_error:** tail step 1/4 ('rw [← singleton_union],'): <stdin>:1:22: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.7s, verify 0.4s, in=825, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleton_union]
simp_rw [partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton]
rw [true_and_iff]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=840, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('rw [← singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1176, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← singleton_union],
rw partiallyWellOrderedOn_union,
rw partiallyWellOrderedOn_singleton,
exact true_and_iff
```

**lean_error:** tail step 1/4 ('rw [← singleton_union],'): <stdin>:1:22: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.1s, verify 0.3s, in=1150, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← singleton_union]
simp_rw [partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton]
simp only [true_and_iff]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.1s, verify 0.2s, in=1165, out=30)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← singleton_union]
simp [partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
r : α → α → Prop
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1200, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union],
rw partiallyWellOrderedOn_union,
simp only [partiallyWellOrderedOn_singleton, and_true, true_and_iff]
```

**lean_error:** tail step 1/3 ('rw [← singleton_union],'): <stdin>:1:22: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.5s, verify 0.2s, in=1211, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union]
simp [partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
r : α → α → Prop
...
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.3s, in=1189, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union, partiallyWellOrderedOn_union]
simp [partiallyWellOrderedOn_singleton, true_and_iff]
```
