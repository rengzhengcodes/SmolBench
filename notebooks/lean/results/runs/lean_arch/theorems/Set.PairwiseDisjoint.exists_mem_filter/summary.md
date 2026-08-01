# Set.PairwiseDisjoint.exists_mem_filter   (k=4, 5 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨fun i => s i, fun i => (s i).2, hsd.set_of_subtype _ _⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.6s, in=373, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨fun i => (s i).1, _, _⟩
intro i
exact (s i).2
exact hsd
```

**lean_error:** tail step 4/4 ('exact hsd'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=348, out=126)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun i => if hi : i ∈ t then (s ⟨i, hi⟩).1 else ∅, fun i => dite_mem _ (fun hi => (s ⟨i, hi⟩).2) fun _ => mem_of_superset univ_mem fun _ => mem_bot, fun i j hij => (hsd (ht.mem_toFinset.1 hij.1) (ht.mem_toFinset.1 hij.2)).mono (inter_subset_left _ _) (inter_subset_left _ _)⟩
apply hsd
simp only [Set.toFinset_empty, Set.disjoint_empty_left]
```

**lean_error:** tail step 1/3 ('exact ⟨fun i => if hi : i ∈ t then (s ⟨i, hi⟩).1 else ∅, fun i => dite_mem _ (fun hi => (s ⟨i, hi⟩).2) fun _ => mem_of_superset univ_mem fun _ => mem_bot, fun i j hij => (hsd (ht.mem_toFinset.1 hij.1) (ht.mem_toFinset.1 hij.2)).mono (inter_subset_left _ _) (inter_subset_left _ _)⟩'):

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.3s, in=362, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨fun i => (s i).val, fun i => (s i).property, _⟩
convert hsd
```

**final state (truncated):**
```
case a
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι✝ : Sort x
...
```
