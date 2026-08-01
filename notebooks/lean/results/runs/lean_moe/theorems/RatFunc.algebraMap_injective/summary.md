# RatFunc.algebraMap_injective   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
exact ofFractionRing_injective.comp (IsFractionRing.injective _ _)
```

**True premises at k:** `IsFractionRing.injective`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.2s, in=300, out=1081)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro p q h
simpa [Function.comp] using h
```

**lean_error:** tail step 2/2 ('simpa [Function.comp] using h'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.1s, in=476, out=967)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.5s, in=854, out=720)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.3s, in=829, out=1091)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('simpa using IsFractionRing.injective'): type mismatch
