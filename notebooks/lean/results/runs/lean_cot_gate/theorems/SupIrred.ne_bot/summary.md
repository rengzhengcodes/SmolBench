# SupIrred.ne_bot   (k=1, 2 tactics total)

file: `Mathlib/Order/Irreducible.lean`  

**Ground-truth tail (from k):**
```lean
exact not_supIrred_bot ha
```

**True premises at k:** `not_supIrred_bot`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✘ ✘ ✘ ✓ | ✓ ✓ ✓ ✘ |
| `hint:3` | ✓ ✓ ✘ ✓ | ✘ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✘ ✓ ✓ ✓ | ✘ ✘ ✘ ✓ | ✓ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 33.7s, verify 0.2s, in=230, out=1517)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h := ha.1
contradiction
```

**lean_error:** tail step 2/2 ('contradiction'): tactic 'contradiction' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 47.7s, verify 0.1s, in=230, out=2182)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.not_bot rfl
```

**lean_error:** tail step 1/1 ('exact ha.not_bot rfl'): invalid field 'not_bot', the environment does not contain 'SupIrred.not_bot'

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 48.7s, verify 0.1s, in=230, out=2231)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.1
```

**lean_error:** tail step 1/1 ('exact ha.1'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 176.3s, verify 0.1s, in=230, out=7996)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exfalso
apply Bot.not_sup_irred ha
```

**lean_error:** tail step 2/2 ('apply Bot.not_sup_irred ha'): unknown constant 'Bot.not_sup_irred'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=230, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.ne_bot rfl
```

**lean_error:** tail step 1/1 ('exact ha.ne_bot rfl'): invalid field 'ne_bot', the environment does not contain 'SupIrred.ne_bot'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=230, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.ne_bot rfl
```

**lean_error:** tail step 1/1 ('exact ha.ne_bot rfl'): invalid field 'ne_bot', the environment does not contain 'SupIrred.ne_bot'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=230, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.ne_bot rfl
```

**lean_error:** tail step 1/1 ('exact ha.ne_bot rfl'): invalid field 'ne_bot', the environment does not contain 'SupIrred.ne_bot'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=230, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.ne_bot rfl
```

**lean_error:** tail step 1/1 ('exact ha.ne_bot rfl'): invalid field 'ne_bot', the environment does not contain 'SupIrred.ne_bot'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 3.5s, verify 0.1s, in=230, out=108)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.ne_bot rfl
```

**lean_error:** tail step 1/1 ('exact ha.ne_bot rfl'): invalid field 'ne_bot', the environment does not contain 'SupIrred.ne_bot'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 5.4s, verify 0.1s, in=230, out=167)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.ne_bot
```

**lean_error:** tail step 1/1 ('exact ha.ne_bot'): invalid field 'ne_bot', the environment does not contain 'SupIrred.ne_bot'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=230, out=170)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sup_irred_bot.1 ha
```

**lean_error:** tail step 1/1 ('exact sup_irred_bot.1 ha'): unknown identifier 'sup_irred_bot'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.7s, verify 0.1s, in=230, out=224)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ha.1 rfl
```

**lean_error:** tail step 1/1 ('exact ha.1 rfl'): application type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 6.4s, verify 0.1s, in=397, out=291)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply not_supIrred_bot ha
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 43.7s, verify 0.1s, in=397, out=1980)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 51.8s, verify 0.1s, in=397, out=2372)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 105.7s, verify 0.1s, in=397, out=4764)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.5s, verify 0.1s, in=397, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ha.ne_bot
```

**lean_error:** tail step 1/1 ('exact ha.ne_bot'): invalid field 'ne_bot', the environment does not contain 'SupIrred.ne_bot'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=397, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ha.not_bot
```

**lean_error:** tail step 1/1 ('exact ha.not_bot'): invalid field 'not_bot', the environment does not contain 'SupIrred.not_bot'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.7s, verify 0.1s, in=397, out=8)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ha.not
```

**lean_error:** tail step 1/1 ('exact ha.not'): invalid field 'not', the environment does not contain 'SupIrred.not'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=397, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 3.6s, verify 0.1s, in=397, out=111)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp at ha
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 3.8s, verify 0.1s, in=397, out=111)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 5.2s, verify 0.1s, in=397, out=166)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.3s, verify 0.1s, in=397, out=168)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 34.0s, verify 0.1s, in=514, out=493)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 34.7s, verify 0.1s, in=514, out=1265)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 39.6s, verify 0.1s, in=514, out=250)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot
```

**lean_error:** tail step 1/1 ('exact not_supIrred_bot'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 100.2s, verify 0.1s, in=514, out=3783)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=514, out=8)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ha.left
```

**lean_error:** tail step 1/1 ('exact ha.left'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.6s, verify 0.1s, in=514, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.7s, verify 0.1s, in=514, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.7s, verify 0.1s, in=514, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ha.1 isMin_bot
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 6.6s, verify 0.1s, in=514, out=107)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 6.8s, verify 0.1s, in=514, out=106)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.6s, verify 0.1s, in=514, out=111)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.2s, verify 0.1s, in=514, out=168)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 16.2s, verify 0.1s, in=540, out=740)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
contradiction
```

**lean_error:** tail step 1/1 ('contradiction'): tactic 'contradiction' failed

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 22.7s, verify 0.1s, in=540, out=1030)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 84.3s, verify 0.1s, in=540, out=3880)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact absurd ha not_supIrred_bot
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 103.4s, verify 0.1s, in=540, out=4656)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.4s, verify 0.1s, in=540, out=8)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ha.not
```

**lean_error:** tail step 1/1 ('exact ha.not'): invalid field 'not', the environment does not contain 'SupIrred.not'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=540, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ha.not_bot
```

**lean_error:** tail step 1/1 ('exact ha.not_bot'): invalid field 'not_bot', the environment does not contain 'SupIrred.not_bot'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=540, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ha.ne_bot
```

**lean_error:** tail step 1/1 ('exact ha.ne_bot'): invalid field 'ne_bot', the environment does not contain 'SupIrred.ne_bot'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.5s, verify 0.1s, in=540, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 3.9s, verify 0.1s, in=540, out=111)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 4.1s, verify 0.1s, in=540, out=125)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 4.2s, verify 0.1s, in=540, out=130)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.5s, verify 0.1s, in=540, out=170)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rintro rfl
```

**lean_error:** tail step 1/1 ('rintro rfl'): tactic 'introN' failed, insufficient number of binders
