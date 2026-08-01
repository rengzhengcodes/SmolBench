# CategoryTheory.SmallObject.ρFunctorObj_π   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/SmallObject/Construction.lean`  

**Ground-truth tail (from k):**
```lean
simp [πFunctorObj]
```

**True premises at k:** `CategoryTheory.SmallObject.πFunctorObj`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=465, out=353)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.4s, verify 0.2s, in=683, out=764)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [πFunctorObj, ρFunctorObj]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.1s, verify 0.2s, in=849, out=907)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [πFunctorObj, ρFunctorObj]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.3s, verify 0.2s, in=851, out=927)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [πFunctorObj, ρFunctorObj]
```
