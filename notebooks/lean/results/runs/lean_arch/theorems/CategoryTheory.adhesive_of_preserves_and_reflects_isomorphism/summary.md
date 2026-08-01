# CategoryTheory.adhesive_of_preserves_and_reflects_isomorphism   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Adhesive.lean`  

**Ground-truth tail (from k):**
```lean
exact adhesive_of_preserves_and_reflects F
```

**True premises at k:** `CategoryTheory.adhesive_of_preserves_and_reflects`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✘ |
| `hint:3` | ✓ | ✓ | ✘ |
| `noise:3` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=399, out=40)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Adhesive.of_preserves_and_reflects
assumption
assumption
assumption
assumption
assumption
assumption
assumption
assumption
assumption
done
```

**lean_error:** tail step 1/11 ('apply Adhesive.of_preserves_and_reflects'): unknown constant 'CategoryTheory.Adhesive.of_preserves_and_reflects'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=371, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Adhesive.of_reflects_limits_of_shape_reflects_colimits_of_shape
exact inferInstance
exact inferInstance
exact inferInstance
exact inferInstance
```

**lean_error:** tail step 1/5 ('apply Adhesive.of_reflects_limits_of_shape_reflects_colimits_of_shape'): unknown constant 'CategoryTheory.Adhesive.of_reflects_limits_of_shape_reflects_colimits_of_shape'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=388, out=67)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=1056, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects F
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=1034, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1045, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects
```

**lean_error:** tail step 1/1 ('apply CategoryTheory.adhesive_of_preserves_and_reflects'): failed to synthesize

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=2932, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects F
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=2931, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=2921, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects
```

**lean_error:** tail step 1/1 ('apply CategoryTheory.adhesive_of_preserves_and_reflects'): failed to synthesize

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=2973, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects F
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=3169, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=2962, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects
```

**lean_error:** tail step 1/1 ('apply CategoryTheory.adhesive_of_preserves_and_reflects'): failed to synthesize
