# FiniteField.sum_subgroup_units   (k=4, 5 tactics total)

file: `Mathlib/FieldTheory/Finite/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

**True premises at k:** `FiniteField.sum_subgroup_units_eq_zero`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ X |
| `hint:2` | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=270, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sum_units_eq_zero_of_ne_bot G_bot
```

**lean_error:** tail step 1/1 ('exact sum_units_eq_zero_of_ne_bot G_bot'): unknown identifier 'sum_units_eq_zero_of_ne_bot'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 70.3s, verify 0.1s, in=270, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sum_units_eq_zero G_bot
```

**lean_error:** tail step 1/1 ('exact sum_units_eq_zero G_bot'): unknown identifier 'sum_units_eq_zero'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 72.1s, verify 0.1s, in=270, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sum_Units_coe_eq_zero_of_ne_bot G_bot
```

**lean_error:** tail step 1/1 ('exact sum_Units_coe_eq_zero_of_ne_bot G_bot'): unknown identifier 'sum_Units_coe_eq_zero_of_ne_bot'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 81.7s, verify 0.0s, in=0, out=0)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** RuntimeError: Inference endpoint unreachable after 10 consecutive connection failures (instance-state check failed: ClientError: An error occurred (RequestExpired) when calling the DescribeInstances operation: Request has expired.). If the instance is running, your public IP probably changed and the

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=995, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=995, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.5s, verify 0.1s, in=995, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 5.5s, verify 0.1s, in=995, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.7s, verify 0.1s, in=2859, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.8s, verify 0.1s, in=2859, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=2859, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.0s, verify 0.1s, in=2859, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=2883, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=2883, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=2883, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 4.5s, verify 0.1s, in=2883, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```
