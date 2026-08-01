# OmegaCompletePartialOrder.ContinuousHom.map_continuous'   (k=2, 3 tactics total)

file: `Mathlib/Order/OmegaCompletePartialOrder.lean`  

**Ground-truth tail (from k):**
```lean
apply const_continuous'
```

**True premises at k:** `OmegaCompletePartialOrder.const_continuous'`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.4s, in=390, out=1377)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using continuous'_const
```

**lean_error:** tail step 1/1 ("simpa using continuous'_const"): unknown identifier 'continuous'_const'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 24.0s, verify 0.1s, in=610, out=4254)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Function.comp] using (pure_continuous' (f := f))
```

**lean_error:** tail step 1/1 ("simpa [Function.comp] using (pure_continuous' (f := f))"): unknown identifier 'pure_continuous''

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 22.1s, verify 0.1s, in=1224, out=4137)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Function.comp] using (pure_continuous' (f := f))
```

**lean_error:** tail step 1/1 ("simpa [Function.comp] using (pure_continuous' (f := f))"): unknown identifier 'pure_continuous''

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 0.1s, in=1174, out=2307)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
·
  exact (pure ∘ f)
·
  simpa using (const_continuous' (pure ∘ f))
```

**lean_error:** tail step 1/4 ('·'): <stdin>:1:1: unexpected end of input; expected '{'
