# Set.PairwiseDisjoint.exists_mem_filter   (k=4, 5 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨fun i => s i, fun i => (s i).2, hsd.set_of_subtype _ _⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.6s, in=373, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨fun i => (s i).1, _, _⟩
intro i
exact (s i).2
exact hsd
```

**lean_error:** tail step 4/4 ('exact hsd'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.9s, verify 0.6s, in=373, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨fun i => (s i).1, _, _⟩
intros i
exact (s i).2
exact hsd
```

**lean_error:** tail step 4/4 ('exact hsd'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.5s, verify 0.6s, in=373, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨fun i => (s i).val, _, _⟩
exact fun i => (s i).property
exact hsd
```

**lean_error:** tail step 3/3 ('exact hsd'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 3.1s, verify 0.4s, in=373, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨fun i => (s i).1, _, _⟩
exact fun i => (s i).2
exact hsd
```

**lean_error:** tail step 3/3 ('exact hsd'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=373, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun i => s i, fun i => (s i).2, hsd⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun i => s i, fun i => (s i).2, hsd⟩'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=373, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun i => (s i).1, fun i => (s i).2, hsd⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun i => (s i).1, fun i => (s i).2, hsd⟩'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.2s, in=373, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun i => (s i).1, fun i => (s i).2, hsd.mono fun i j hij => hij.mono inf_le_left⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun i => (s i).1, fun i => (s i).2, hsd.mono fun i j hij => hij.mono inf_le_left⟩'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=373, out=59)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun i => (s i).1, fun i => (s i).2, hsd.mono fun _ _ h => disjoint_iff_inf_le.mpr $ (disjoint_iff_inf_le.mp h).trans $ le_inf (le_refl _) (le_refl _)⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun i => (s i).1, fun i => (s i).2, hsd.mono fun _ _ h => disjoint_iff_inf_le.mpr $ (disjoint_iff_inf_le.mp h).trans $ le_inf (le_refl _) (le_refl _)⟩'): application type mismatch
