# RatFunc.ofFractionRing_sub   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Sub.sub, HSub.hSub, RatFunc.sub]
```

**True premises at k:** `Sub.sub`, `HSub.hSub`, `RatFunc.sub`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.1s, in=301, out=697)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=604, out=601)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=763, out=340)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [RatFunc.sub]
```

**lean_error:** tail step 1/1 ('simpa [RatFunc.sub]'): tactic 'assumption' failed

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=777, out=441)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch
