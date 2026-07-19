# Polynomial.span_singleton_annIdealGenerator   (k=7, 8 tactics total)

file: `Mathlib/LinearAlgebra/AnnihilatingPolynomial.lean`  

**Ground-truth tail (from k):**
```lean
apply (mul_ne_zero_iff.mp h).1
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.3s, verify 0.1s, in=293, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.4s, verify 0.1s, in=293, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.5s, verify 0.1s, in=293, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=293, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.4s, verify 0.1s, in=293, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 0.6s, verify 0.1s, in=293, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=293, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 1.3s, in=293, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa only [annIdealGenerator] using h
```

**lean_error:** tail step 1/1 ('simpa only [annIdealGenerator] using h'): type mismatch
