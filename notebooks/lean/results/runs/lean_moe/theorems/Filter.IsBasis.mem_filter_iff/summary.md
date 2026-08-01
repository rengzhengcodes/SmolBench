# Filter.IsBasis.mem_filter_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
simp only [IsBasis.filter, FilterBasis.mem_filter_iff, mem_filterBasis_iff,
  exists_exists_and_eq_and]
```

**True premises at k:** `Filter.IsBasis.filter`, `FilterBasis.mem_filter_iff`, `Filter.IsBasis.mem_filterBasis_iff`, `exists_exists_and_eq_and`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✓ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=341, out=928)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using h.mem_iff
```

**lean_error:** tail step 1/1 ('simpa using h.mem_iff'): invalid field 'mem_iff', the environment does not contain 'Filter.IsBasis.mem_iff'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.1s, in=1091, out=1049)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff,
  exists_exists_and_eq_and]
```

**lean_error:** tail step 1/2 ('simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff,'): <stdin>:1:79: unexpected end of input; expected '*' or '-'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.6s, verify 0.2s, in=1942, out=1542)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff, exists_exists_and_eq_and]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=1864, out=1304)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff,
  exists_exists_and_eq_and]
```

**lean_error:** tail step 1/2 ('simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff,'): <stdin>:1:79: unexpected end of input; expected '*' or '-'
