# Filter.IsBasis.mem_filter_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
simp only [IsBasis.filter, FilterBasis.mem_filter_iff, mem_filterBasis_iff,
  exists_exists_and_eq_and]
```

**True premises at k:** `Filter.IsBasis.filter`, `FilterBasis.mem_filter_iff`, `Filter.IsBasis.mem_filterBasis_iff`, `exists_exists_and_eq_and`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.8s, in=296, out=72)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro hU
    obtain ⟨i, hpi, hUi⟩ := h.mem_filter_iff.mp hU
    exact ⟨i, hpi, hUi⟩
  · rintro ⟨i, hpi, hUi⟩
    exact h.mem_filter_iff.mpr ⟨i, hpi, hUi⟩
```

**lean_error:** tail step 2/6 ('· intro hU'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=263, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsBasis.filter, Set.mem_iUnion₂]
simp only [exists_prop, mem_setOf_eq, and_comm]
```

**lean_error:** tail step 1/2 ('rw [IsBasis.filter, Set.mem_iUnion₂]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=285, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold IsBasis.filter
exact h.mem_filter_iff
```

**lean_error:** tail step 2/2 ('exact h.mem_filter_iff'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 2.0s, verify 0.9s, in=989, out=40)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.IsBasis.filter, FilterBasis.mem_filter_iff]
simp only [exists_exists_and_eq_and, Filter.IsBasis.mem_filterBasis_iff]
exact Iff.rfl
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=931, out=41)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff]
simp only [exists_exists_and_eq_and, exists_prop, and_comm (a := _ = _)]
```

**lean_error:** tail step 1/2 ('rw [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=978, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.filter, FilterBasis.mem_filter_iff, mem_filterBasis_iff]
simp only [exists_exists_and_eq_and]
```

**lean_error:** tail step 1/2 ('rw [h.filter, FilterBasis.mem_filter_iff, mem_filterBasis_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.8s, verify 0.2s, in=1811, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.IsBasis.filter, FilterBasis.mem_filter_iff]
simp only [exists_exists_and_eq_and, Filter.IsBasis.mem_filterBasis_iff]
exact Iff.rfl
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1755, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsBasis.filter, ← FilterBasis.mem_filter_iff, h.mem_filterBasis_iff]
simp only [exists_exists_and_eq_and, exists_prop, and_comm]
```

**lean_error:** tail step 1/2 ('rw [IsBasis.filter, ← FilterBasis.mem_filter_iff, h.mem_filterBasis_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1800, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h.filter, FilterBasis.mem_filter_iff]
rw [h.mem_filterBasis_iff]
simp only [exists_exists_and_eq_and]
```

**lean_error:** tail step 1/3 ('rw [h.filter, FilterBasis.mem_filter_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=1835, out=45)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.filter, FilterBasis.mem_filter_iff]
rw [h.mem_filterBasis_iff]
apply exists_exists_and_eq_and
simp only [exists_and_distrib_left, exists_eq_left, exists_prop]
```

**lean_error:** tail step 1/4 ('rw [h.filter, FilterBasis.mem_filter_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1873, out=45)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsBasis.filter, mem_filter_iff]
rw [h.mem_filterBasis_iff]
simp only [exists_exists_and_eq_and, ← subset_antisymm_iff, and_comm (a := s _ = U)]
```

**lean_error:** tail step 1/3 ('rw [IsBasis.filter, mem_filter_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1824, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.mem_filter_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [h.mem_filter_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
