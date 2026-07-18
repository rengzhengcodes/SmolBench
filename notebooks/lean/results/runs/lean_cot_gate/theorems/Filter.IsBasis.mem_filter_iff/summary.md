# Filter.IsBasis.mem_filter_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
simp only [IsBasis.filter, FilterBasis.mem_filter_iff, mem_filterBasis_iff,
  exists_exists_and_eq_and]
```

**True premises at k:** `Filter.IsBasis.filter`, `FilterBasis.mem_filter_iff`, `Filter.IsBasis.mem_filterBasis_iff`, `exists_exists_and_eq_and`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 110.3s, verify 0.1s, in=274, out=4920)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 144.7s, verify 0.1s, in=274, out=6537)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw h.mem_filter
```

**lean_error:** tail step 1/1 ('rw h.mem_filter'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 159.0s, verify 0.1s, in=274, out=7113)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
rintro ⟨i, pi, siU⟩
apply Filter.superset_mem (Filter.generate_sets _ ⟨i, pi, rfl⟩) siU
intro hU
obtain ⟨T, hT, hfinT, hTU⟩ := Filter.mem_generate.1 hU
obtain ⟨j, pj, hj⟩ := h.2.2 T hT hfinT
exact ⟨j, pj, subset.trans hj hTU⟩
```

**lean_error:** tail step 1/7 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 173.3s, verify 0.1s, in=274, out=7707)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
rintro ⟨i, hi, hs⟩
exact filter.generate_sets.mem_of_superset (filter.generate_sets.basic hi) hs
intro hU
rw filter.mem_generate_iff at hU
rcases hU with ⟨c, c_sub, fin_c, inter_sub⟩
obtain ⟨j, hj, hj_sub⟩ : ∃ j, p j ∧ s j ⊆ ⋂₀ c
· apply h.exists_sInter_finset_subset fin_c
  rwa Finset.coe_subset at c_sub
exact ⟨j, hj, hj_sub.trans inter_sub⟩
```

**lean_error:** tail step 1/10 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=274, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.filter_def]
```

**lean_error:** tail step 1/1 ('simp [h.filter_def]'): invalid field 'filter_def', the environment does not contain 'Filter.IsBasis.filter_def'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=274, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.mem_filter_iff]
```

**lean_error:** tail step 1/1 ('simp [h.mem_filter_iff]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=274, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.mem_filter_iff, exists_prop]
```

**lean_error:** tail step 1/1 ('simp [h.mem_filter_iff, exists_prop]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=274, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.mem_filter, exists_prop]
```

**lean_error:** tail step 1/1 ('simp [h.mem_filter, exists_prop]'): invalid field 'mem_filter', the environment does not contain 'Filter.IsBasis.mem_filter'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 64.8s, verify 0.1s, in=967, out=2930)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [FilterBasis.mem_filter_iff, mem_filterBasis_iff]
apply exists_exists_and_eq_and
```

**lean_error:** tail step 1/2 ('rw [FilterBasis.mem_filter_iff, mem_filterBasis_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 106.5s, verify 0.1s, in=967, out=4756)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 113.7s, verify 0.1s, in=967, out=5065)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw mem_filter_iff
rw mem_filterBasis_iff
rw exists_exists_and_eq_and
```

**lean_error:** tail step 1/3 ('rw mem_filter_iff'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 121.7s, verify 0.1s, in=967, out=5409)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=967, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h.mem_filter_iff, h.mem_filterBasis_iff]
```

**lean_error:** tail step 1/1 ('simp [h.mem_filter_iff, h.mem_filterBasis_iff]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=967, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp [h.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=967, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [h.mem_filterBasis_iff, FilterBasis.mem_filter_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp only [h.mem_filterBasis_iff, FilterBasis.mem_filter_iff, exists_exists_and_eq_and]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=967, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [h.mem_filterBasis_iff, h.filter, mem_filter_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp only [h.mem_filterBasis_iff, h.filter, mem_filter_iff, exists_exists_and_eq_and]'): invalid 'simp', proposition expected

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 117.2s, verify 0.1s, in=1792, out=1811)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 151.6s, verify 0.1s, in=1792, out=2139)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [FilterBasis.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [FilterBasis.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 171.8s, verify 0.1s, in=1792, out=2884)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h.filterBasis.mem_filter_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [h.filterBasis.mem_filter_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 210.8s, verify 0.1s, in=1792, out=6348)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mem_filter_iff h.filterBasis, h.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [mem_filter_iff h.filterBasis, h.mem_filterBasis_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=1792, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [h.mem_filterBasis_iff, h.filterBasis.mem_filter_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp [h.mem_filterBasis_iff, h.filterBasis.mem_filter_iff, exists_exists_and_eq_and]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=1792, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [h.mem_filter_iff, h.mem_filterBasis_iff]
```

**lean_error:** tail step 1/1 ('simp [h.mem_filter_iff, h.mem_filterBasis_iff]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 71.2s, verify 0.1s, in=1792, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp [mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 71.5s, verify 0.1s, in=1792, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [h.filter, FilterBasis.mem_filter_iff, Filter.IsBasis.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp [h.filter, FilterBasis.mem_filter_iff, Filter.IsBasis.mem_filterBasis_iff, exists_exists_and_eq_and]'): invalid 'simp', proposition expected

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 75.8s, verify 0.1s, in=1816, out=3408)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [FilterBasis.mem_filter_iff, Filter.IsBasis.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [FilterBasis.mem_filter_iff, Filter.IsBasis.mem_filterBasis_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 104.0s, verify 0.1s, in=1816, out=4649)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [FilterBasis.mem_filter_iff h.filterBasis, h.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [FilterBasis.mem_filter_iff h.filterBasis, h.mem_filterBasis_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 108.3s, verify 0.1s, in=1816, out=4783)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [FilterBasis.mem_filter_iff, mem_filterBasis_iff]
apply exists_exists_and_eq_and
```

**lean_error:** tail step 1/2 ('rw [FilterBasis.mem_filter_iff, mem_filterBasis_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 149.8s, verify 0.1s, in=1816, out=6666)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [FilterBasis.mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('rw [FilterBasis.mem_filter_iff, mem_filterBasis_iff, exists_exists_and_eq_and]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=1816, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp [h.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=1816, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp [h.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=1816, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [h.filter.mem_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp only [h.filter.mem_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]'): invalid field 'mem_iff', the environment does not contain 'Filter.mem_iff'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=1816, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [h.filterBasis.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]
```

**lean_error:** tail step 1/1 ('simp only [h.filterBasis.mem_filter_iff, h.mem_filterBasis_iff, exists_exists_and_eq_and]'): simp made no progress
