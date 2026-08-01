# Polynomial.span_singleton_annIdealGenerator   (k=7, 8 tactics total)

file: `Mathlib/LinearAlgebra/AnnihilatingPolynomial.lean`  

**Ground-truth tail (from k):**
```lean
apply (mul_ne_zero_iff.mp h).1
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.2s, verify 0.1s, in=293, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.3s, in=267, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsPrincipal.generator]
simp only [annIdeal, Ideal.span_singleton_generator]
exact h
```

**lean_error:** tail step 3/3 ('exact h'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=282, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsPrincipal.generator_eq] at h,
exact h
```

**lean_error:** tail step 1/2 ('rw [IsPrincipal.generator_eq] at h,'): <stdin>:1:34: expected end of input
