# Finset.map_subtype_embedding_Ioi   (k=1, 2 tactics total)

file: `Mathlib/Order/LocallyFinite.lean`  

**Ground-truth tail (from k):**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp (mem_Ioi.1 hx).le a.prop
```

**True premises at k:** `Finset.subtype_map_of_mem`, `Finset.mem_Ioi`, `LT.lt.le`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.8s, in=324, out=61)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp only [mem_map, Embedding.coe_subtype, mem_subtype, mem_Ioi]
constructor
rintro ⟨y, hy, rfl⟩
exact hy
intro hx
refine ⟨⟨x, _⟩, hx, rfl⟩
exact hp a.prop hx
```

**lean_error:** tail step 7/8 ('refine ⟨⟨x, _⟩, hx, rfl⟩'): internal exception #7

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.7s, in=296, out=97)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp only [mem_map, Embedding.subtype, exists_prop, Subtype.coe_mk, mem_Ioi, mem_subtype]
constructor
rintro ⟨y, hy, rfl⟩
exact hp (lt_of_le_of_lt (le_refl _) hy) a.property
intro hx
refine ⟨⟨x, ?_⟩, hx, Subtype.coe_eta _ _⟩
exact hp (le_of_lt hx) a.property
```

**lean_error:** tail step 5/8 ('exact hp (lt_of_le_of_lt (le_refl _) hy) a.property'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 7.2s, in=313, out=145)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Finset.ext
simp only [Finset.mem_map, Finset.mem_subtype, Embedding.coe_subtype, exists_and_distrib_left, exists_eq_right, and_self]
intro x
rw [Ioi]
simp only [OrderDual.Ioi, Set.mem_Ioi, SetLike.coe_sort_coe, Subtype.coe_mk, Subtype.val_eq_coe, Finset.mem_Ioi]
split
intro h
exact h
intro h
dsimp [Finset.subtype]
rw [Finset.mem_filter]
split
apply hp
exact a.2
apply le_of_lt
assumption
apply Finset.mem_Ioi.mpr
assumption
```

**lean_error:** tail step 2/18 ('simp only [Finset.mem_map, Finset.mem_subtype, Embedding.coe_subtype, exists_and_distrib_left, exists_eq_right, and_self]'): unknown identifier 'exists_and_distrib_left'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.4s, in=830, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' Finset.subtype_map_of_mem _
intros x h
rw [Finset.mem_Ioi] at h
exact hp h.le _
```

**lean_error:** tail step 4/4 ('exact hp h.le _'): internal exception #7

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.4s, in=801, out=48)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [subtype_map_of_mem]
intro b
simp only [mem_Ioi, Subtype.coe_mk]
exact hp (le_of_lt ?_)
simp only [mem_Ioi]
exact id
exact Subtype.property a
```

**lean_error:** tail step 4/7 ('exact hp (le_of_lt ?_)'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.3s, in=819, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply subtype_map_of_mem
intro x
rw [mem_Ioi] at x
exact hp (le_of_lt x) a.property
```

**lean_error:** tail step 3/4 ('rw [mem_Ioi] at x'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.4s, in=1924, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine' Finset.subtype_map_of_mem _
intro x h
rw [Finset.mem_Ioi] at h
exact hp h.le _
```

**lean_error:** tail step 4/4 ('exact hp h.le _'): internal exception #7

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.7s, in=1900, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [subtype_Ioi_eq_Ioi_coe]
exact Finset.subtype_map_of_mem fun _ => hp (Subtype.le _) a.property
```
```

**lean_error:** tail step 1/3 ('rw [subtype_Ioi_eq_Ioi_coe]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.0s, verify 0.5s, in=1913, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply subtype_map_of_mem
intro x
rw [mem_Ioi]
intro h
exact hp (le_of_lt h) a.property
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.4s, in=1949, out=32)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine' Finset.subtype_map_of_mem _
intro x h
rw [Finset.mem_Ioi] at h
exact hp h.le _
```

**lean_error:** tail step 4/4 ('exact hp h.le _'): internal exception #7

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=2045, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact subtype_map_of_mem fun x hx => hp (le_of_lt <| mem_Ioi.mp hx) a.property
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.5s, verify 0.5s, in=1938, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply subtype_map_of_mem
intro x
rw [mem_Ioi]
intro h
exact hp (le_of_lt h) a.property
```
