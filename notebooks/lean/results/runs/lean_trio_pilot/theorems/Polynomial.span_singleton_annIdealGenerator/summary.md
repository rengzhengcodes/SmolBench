# Polynomial.span_singleton_annIdealGenerator   (k=7, 8 tactics total)

file: `Mathlib/LinearAlgebra/AnnihilatingPolynomial.lean`  

**Ground-truth tail (from k):**
```lean
apply (mul_ne_zero_iff.mp h).1
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.2s, verify 0.1s, in=293, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=293, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa only [annIdealGenerator] using h
```

**lean_error:** tail step 1/1 ('simpa only [annIdealGenerator] using h'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=282, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsPrincipal.generator_eq] at h,
exact h
```

**lean_error:** tail step 1/2 ('rw [IsPrincipal.generator_eq] at h,'): <stdin>:1:34: expected end of input

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 0.5s, verify 0.6s, in=273, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsPrincipal.generator_eq] at h,
exact h
```

**lean_error:** tail step 1/2 ('rw [IsPrincipal.generator_eq] at h,'): <stdin>:1:34: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 8.7s, verify 0.1s, in=264, out=524)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=264, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [annIdealGenerator, h]
```

**lean_error:** tail step 1/1 ('simp [annIdealGenerator, h]'): simp made no progress
