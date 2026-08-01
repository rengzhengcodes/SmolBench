# Int.neg_le_sub_left_of_le_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/Int/Order.lean`  

**Ground-truth tail (from k):**
```lean
rwa [Int.add_comm] at h
```

**True premises at k:** `Int.add_comm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=232, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sub_eq_add_neg] at *
exact h
```

**lean_error:** tail step 1/2 ('rw [sub_eq_add_neg] at *'): tactic 'rewrite' failed, did not find instance of the pattern in the current goal

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=206, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sub_eq_add_neg, add_comm]
exact h
```

**lean_error:** tail step 1/2 ('rw [sub_eq_add_neg, add_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=221, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sub_eq_add_neg] at h,
exact h
```

**lean_error:** tail step 1/2 ('rw [sub_eq_add_neg] at h,'): <stdin>:1:24: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=479, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm] at h,
exact h
```

**lean_error:** tail step 1/2 ('rw [Int.add_comm] at h,'): <stdin>:1:22: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=453, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm] at h
exact h
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=468, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_eq_add_neg, add_comm]
exact h
```

**lean_error:** tail step 1/2 ('rw [sub_eq_add_neg, add_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=897, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.add_comm] at h
exact h
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=865, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.add_comm] at h
exact h
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=886, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.add_comm] at h
exact h
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=921, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.add_comm] at h,
exact h
```

**lean_error:** tail step 1/2 ('rw [Int.add_comm] at h,'): <stdin>:1:22: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.7s, in=943, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.add_comm] at h
exact h
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=910, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [sub_eq_add_neg, add_comm b (-c)]
```

**lean_error:** tail step 1/1 ('rw [sub_eq_add_neg, add_comm b (-c)]'): tactic 'rewrite' failed, equality or iff proof expected
