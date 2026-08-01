# LinearMap.range_eq_top_of_cancel   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/Quotient.lean`  

**Ground-truth tail (from k):**
```lean
exact ker_zero
```

**True premises at k:** `LinearMap.ker_zero`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.8s, in=538, out=614)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
  constructor
  · intro hx
    trivial
  · intro _
    change (0 : M₂ →ₗ[R₂] M₂ ⧸ range f) x = 0
    simp
```

**lean_error:** tail step 3/7 ('· intro hx'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.4s, verify 0.5s, in=812, out=295)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using LinearMap.ker_zero
```
