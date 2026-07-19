# LinearMap.range_eq_top_of_cancel   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/Quotient.lean`  

**Ground-truth tail (from k):**
```lean
exact ker_zero
```

**True premises at k:** `LinearMap.ker_zero`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ |
| `hint:2` | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=478, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext,
simp [mem_ker, LinearMap.zero_apply],
trivial
```

**lean_error:** tail step 1/3 ('ext,'): <stdin>:1:3: expected end of input

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=478, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact set_like.ext' (λ x, iff_true_intro (zero_apply x))
```

**lean_error:** tail step 1/1 ("exact set_like.ext' (λ x, iff_true_intro (zero_apply x))"): <stdin>:1:24: expected '↦', '=>'

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=478, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
simp [mem_ker, ker_zero],
exact Submodule.mem_top,
```

**lean_error:** tail step 1/3 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=478, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
simp only [ker, mem_set_of_eq],
simp only [LinearMap.comp_apply, LinearMap.zero_apply],
trivial
```

**lean_error:** tail step 1/4 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=478, out=4)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ker_zero
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.0s, verify 0.1s, in=478, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact LinearMap.ker_zero
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=478, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact LinearMap.ker_zero
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.4s, verify 0.1s, in=478, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact LinearMap.ker_zero
```

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 0.6s, verify 0.1s, in=739, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact LinearMap.ker_zero
```

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 0.7s, verify 0.1s, in=739, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact LinearMap.ker_zero
```

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=739, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact LinearMap.ker_zero
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=739, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Submodule.ker_mkQ]
exact LinearMap.ker_zero
```

**lean_error:** tail step 1/2 ('rw [Submodule.ker_mkQ]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=739, out=2)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 0.9s, verify 0.1s, in=739, out=4)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ker_zero
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.1s, verify 0.1s, in=739, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact LinearMap.ker_zero
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.3s, verify 0.1s, in=739, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact LinearMap.ker_zero
```
