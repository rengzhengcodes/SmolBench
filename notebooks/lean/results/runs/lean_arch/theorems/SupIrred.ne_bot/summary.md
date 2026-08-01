# SupIrred.ne_bot   (k=1, 2 tactics total)

file: `Mathlib/Order/Irreducible.lean`  

**Ground-truth tail (from k):**
```lean
exact not_supIrred_bot ha
```

**True premises at k:** `not_supIrred_bot`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=254, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.not_le_bot (bot_le (f ⊥))
```

**lean_error:** tail step 1/1 ('exact ha.not_le_bot (bot_le (f ⊥))'): invalid field 'not_le_bot', the environment does not contain 'SupIrred.not_le_bot'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=227, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.1 bot_sup_eq_left rfl.le
```

**lean_error:** tail step 1/1 ('exact ha.1 bot_sup_eq_left rfl.le'): unknown identifier 'bot_sup_eq_left'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=243, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exfalso,
apply ha.1,
apply bot_le
```

**lean_error:** tail step 1/3 ('exfalso,'): <stdin>:1:7: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=423, out=8)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.2s, verify 0.1s, in=393, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ha.not_bot rfl
```

**lean_error:** tail step 1/1 ('exact ha.not_bot rfl'): invalid field 'not_bot', the environment does not contain 'SupIrred.not_bot'

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 10.0s, verify 0.1s, in=412, out=638)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
contradiction
```

**lean_error:** tail step 1/1 ('contradiction'): tactic 'contradiction' failed

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=538, out=8)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=507, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ha.not_isMin.isMin rfl $ isMin_bot.isMin ⊥
```

**lean_error:** tail step 1/1 ('exact ha.not_isMin.isMin rfl $ isMin_bot.isMin ⊥'): invalid field 'isMin', the environment does not contain 'Not.isMin'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 5.3s, verify 0.1s, in=527, out=321)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=563, out=8)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=546, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ha.not_bot rfl
```

**lean_error:** tail step 1/1 ('exact ha.not_bot rfl'): invalid field 'not_bot', the environment does not contain 'SupIrred.not_bot'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=552, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
trivial
```

**lean_error:** tail step 1/1 ('trivial'): tactic 'apply' failed, failed to unify
