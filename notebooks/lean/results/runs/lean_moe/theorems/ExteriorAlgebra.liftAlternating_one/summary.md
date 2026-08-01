# ExteriorAlgebra.liftAlternating_one   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
rw [foldl_one]
```

**True premises at k:** `CliffordAlgebra.foldl_one`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✓ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.5s, verify 0.7s, in=497, out=612)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 9.4s, verify 0.8s, in=753, out=1977)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.4s, verify 0.8s, in=1284, out=1527)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.4s, verify 0.8s, in=1239, out=1784)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```
