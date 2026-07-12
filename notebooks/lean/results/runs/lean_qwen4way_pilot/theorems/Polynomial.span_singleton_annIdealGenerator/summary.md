# Polynomial.span_singleton_annIdealGenerator   (k=7, 8 tactics total)

file: `Mathlib/LinearAlgebra/AnnihilatingPolynomial.lean`  

**Ground-truth tail (from k):**
```lean
apply (mul_ne_zero_iff.mp h).1
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 34.9s, verify 0.1s, in=264, out=1951)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=264, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [annIdealGenerator, IsPrincipal.generator]
```

**lean_error:** tail step 1/1 ('rwa [annIdealGenerator, IsPrincipal.generator]'): failed to rewrite using equation theorems for 'Polynomial.annIdealGenerator'

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=264, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [annIdealGenerator, annIdeal_isPrincipal]
```

**lean_error:** tail step 1/1 ('rwa [annIdealGenerator, annIdeal_isPrincipal]'): failed to rewrite using equation theorems for 'Polynomial.annIdealGenerator'

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 0.6s, verify 0.4s, in=264, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [annIdealGenerator, annIdeal_isPrincipal]
```

**lean_error:** tail step 1/1 ('rwa [annIdealGenerator, annIdeal_isPrincipal]'): failed to rewrite using equation theorems for 'Polynomial.annIdealGenerator'
