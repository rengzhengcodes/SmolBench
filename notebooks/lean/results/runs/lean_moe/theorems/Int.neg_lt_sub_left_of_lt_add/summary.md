# Int.neg_lt_sub_left_of_lt_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/Int/Order.lean`  

**Ground-truth tail (from k):**
```lean
rwa [Int.add_comm] at h
```

**True premises at k:** `Int.add_comm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=270, out=313)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [sub_eq_add_neg, add_comm] using h
```

**lean_error:** tail step 1/1 ('simpa [sub_eq_add_neg, add_comm] using h'): unknown identifier 'sub_eq_add_neg'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 9.5s, verify 0.1s, in=215, out=1071)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
linarith
```

**lean_error:** tail step 1/1 ('linarith'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.1s, in=215, out=437)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
linarith
```

**lean_error:** tail step 1/1 ('linarith'): <stdin>:1:1: unknown tactic

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.1s, in=523, out=793)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [sub_eq, add_comm] using h
```

**lean_error:** tail step 1/1 ('simpa [sub_eq, add_comm] using h'): unknown identifier 'add_comm'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 83.4s, verify 0.1s, in=480, out=9644)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
linarith
```

**lean_error:** tail step 1/1 ('linarith'): <stdin>:1:1: unknown tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.1s, in=471, out=666)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Int.add_comm]
exact h
```

**lean_error:** tail step 1/2 ('rw [← Int.add_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.1s, in=946, out=764)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 52.1s, verify 0.1s, in=912, out=6028)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 39.1s, verify 0.1s, in=908, out=4455)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.add_comm]
exact h
```

**lean_error:** tail step 1/2 ('rw [Int.add_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.4s, verify 0.1s, in=930, out=1096)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [sub_eq, add_comm] using h
```

**lean_error:** tail step 1/1 ('simpa [sub_eq, add_comm] using h'): unknown identifier 'add_comm'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 81.3s, verify 0.1s, in=1004, out=9398)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [add_comm] at *
linarith
```

**lean_error:** tail step 1/2 ('rw [add_comm] at *'): tactic 'rewrite' failed, did not find instance of the pattern in the current goal

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.3s, verify 0.1s, in=920, out=499)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.sub_eq_add_neg, Int.add_comm]
exact h
```
