# symmDiff_sdiff_left   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_idem, sdiff_sdiff_self, bot_sup_eq]
```

**True premises at k:** `symmDiff_def`, `sup_sdiff`, `sdiff_idem`, `sdiff_sdiff_self`, `bot_sup_eq`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=262, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sdiff_comm],
rw [inf_comm]
```

**lean_error:** tail step 1/2 ('rw [sdiff_comm],'): <stdin>:1:15: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.3s, in=232, out=63)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sdiff_eq]
rw [symmDiff_eq]
simp only [sup_comm, inf_sup_distrib_right, sup_inf_distrib_left, sdiff_eq, sup_sdiff]
simp only [inf_sup_distrib_right, sup_inf_distrib_left, sup_idem, sup_sdiff]
```

**lean_error:** tail step 1/4 ('rw [sdiff_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=251, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [diff_symm, diff_eq]
```

**lean_error:** tail step 1/1 ('rw [diff_symm, diff_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=873, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_idem a b, sdiff_sdiff_self b a, bot_sup_eq]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_def, sup_sdiff, sdiff_idem a b, sdiff_sdiff_self b a, bot_sup_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 1.1s, verify 1.3s, in=837, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff, sdiff_idem, sdiff_sdiff_self, bot_sup_eq]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=862, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def, sdiff_idem, sup_sdiff, sdiff_sdiff_self, bot_sup_eq]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_def, sdiff_idem, sup_sdiff, sdiff_sdiff_self, bot_sup_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=1789, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_idem, sdiff_sdiff_self, bot_sup_eq]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=1762, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 33.7s, verify 0.1s, in=1778, out=2104)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_sdiff_left, sup_idem, bot_sup_eq]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=1816, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_idem, sdiff_sdiff_self, bot_sup_eq]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=1887, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1805, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sdiff_idem, sup_sdiff, sdiff_sdiff_self, bot_sup_eq]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_def, sdiff_idem, sup_sdiff, sdiff_sdiff_self, bot_sup_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
