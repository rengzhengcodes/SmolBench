# LinearMap.range_eq_top_of_cancel   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/Quotient.lean`  

**Ground-truth tail (from k):**
```lean
exact ker_zero
```

**True premises at k:** `LinearMap.ker_zero`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=478, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
simp [mem_ker, ker_zero],
exact Submodule.mem_top
```

**lean_error:** tail step 1/3 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 1.0s, in=448, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp only [mem_ker, mem_top, Submodule.mem_top, iff_true]
exact map_zero _
```

**lean_error:** tail step 3/3 ('exact map_zero _'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.3s, in=467, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
exact ker_zero_le_top
exact top_le_ker_zero
```

**lean_error:** tail step 2/3 ('exact ker_zero_le_top'): unknown identifier 'ker_zero_le_top'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=739, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Submodule.ker_mkQ]
exact LinearMap.ker_zero
```

**lean_error:** tail step 1/2 ('rw [Submodule.ker_mkQ]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=704, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.ker_zero]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=728, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ker_zero]
```
