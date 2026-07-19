# Polynomial.span_singleton_annIdealGenerator   (k=7, 8 tactics total)

file: `Mathlib/LinearAlgebra/AnnihilatingPolynomial.lean`  

**Ground-truth tail (from k):**
```lean
apply (mul_ne_zero_iff.mp h).1
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=339, out=291)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [annIdealGenerator] using h
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 120.0s, verify 0.1s, in=292, out=13779)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 16.6s, verify 0.1s, in=276, out=364)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch
