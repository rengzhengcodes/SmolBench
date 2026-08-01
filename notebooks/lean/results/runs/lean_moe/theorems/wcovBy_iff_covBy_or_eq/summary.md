# wcovBy_iff_covBy_or_eq   (k=0, 1 tactics total)

file: `Mathlib/Order/Cover.lean`  

**Ground-truth tail (from k):**
```lean
rw [le_antisymm_iff, wcovBy_iff_covBy_or_le_and_le]
```

**True premises at k:** `le_antisymm_iff`, `wcovBy_iff_covBy_or_le_and_le`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=292, out=701)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.2s, verify 0.1s, in=753, out=1987)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [le_antisymm_iff] using (wcovBy_iff_covBy_or_le_and_le (a:=a) (b:=b))
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.1s, verify 0.1s, in=899, out=476)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [le_antisymm_iff] using (wcovBy_iff_covBy_or_le_and_le (a:=a) (b:=b))
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.7s, verify 0.1s, in=907, out=1597)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [le_antisymm_iff] using (wcovBy_iff_covBy_or_le_and_le (a:=a) (b:=b))
```
