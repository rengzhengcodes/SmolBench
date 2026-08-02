# OmegaCompletePartialOrder.ContinuousHom.map_continuous'   (k=2, 3 tactics total)

file: `Mathlib/Order/OmegaCompletePartialOrder.lean`  

**Ground-truth tail (from k):**
```lean
apply const_continuous'
```

**True premises at k:** `OmegaCompletePartialOrder.const_continuous'`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.4s, in=390, out=1377)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using continuous'_const
```

**lean_error:** tail step 1/1 ("simpa using continuous'_const"): unknown identifier 'continuous'_const'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 191.1s, verify 0.1s, in=345, out=23295)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : TopologicalSpace (β → Part γ) := discreteTopology (β → Part γ)
have h₂ : Continuous (fun x => pure ∘ f) := by
  apply continuous_const
  <;> assumption
exact h₂
```

**lean_error:** tail step 1/5 ('have h₁ : TopologicalSpace (β → Part γ) := discreteTopology (β → Part γ)'): unknown identifier 'TopologicalSpace'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.3s, in=337, out=423)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply continuous_const
```

**lean_error:** tail step 1/1 ('apply continuous_const'): tactic 'apply' failed, failed to unify

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 24.0s, verify 0.1s, in=610, out=4254)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Function.comp] using (pure_continuous' (f := f))
```

**lean_error:** tail step 1/1 ("simpa [Function.comp] using (pure_continuous' (f := f))"): unknown identifier 'pure_continuous''

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 159.5s, verify 0.1s, in=559, out=19132)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply OmegaCompletePartialOrder.const_continuous'
<;> try
  (try
    {
      exact pure ∘ f
    }) <;>
  (try
    {
      infer_instance
    }) <;>
  (try
    {
      infer_instance
    })
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.2s, in=550, out=691)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply continuous_const
```

**lean_error:** tail step 1/1 ('apply continuous_const'): tactic 'apply' failed, failed to unify

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 22.1s, verify 0.1s, in=1224, out=4137)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Function.comp] using (pure_continuous' (f := f))
```

**lean_error:** tail step 1/1 ("simpa [Function.comp] using (pure_continuous' (f := f))"): unknown identifier 'pure_continuous''

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 148.8s, verify 0.1s, in=1185, out=17593)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h : Continuous' (fun (x : α') => pure ∘ f) := by
  apply const_continuous'
exact h
```

**lean_error:** tail step 1/3 ("have h : Continuous' (fun (x : α') => pure ∘ f) := by"): <stdin>:1:53: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.2s, verify 0.1s, in=1171, out=719)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply const_continuous'
```

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

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 47.3s, verify 0.1s, in=1290, out=5353)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply OmegaCompletePartialOrder.const_continuous' (pure ∘ f)
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 9.9s, verify 0.7s, in=1176, out=1163)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact const_continuous' (pure ∘ f)
```
