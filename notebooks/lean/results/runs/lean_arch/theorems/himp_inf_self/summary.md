# himp_inf_self   (k=0, 1 tactics total)

file: `Mathlib/Order/Heyting/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

**True premises at k:** `inf_comm`, `inf_himp`, `inf_comm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=268, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm]
rw [imp_inf_self]
```

**lean_error:** tail step 2/2 ('rw [imp_inf_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=240, out=73)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
· apply le_inf
  · rw [inf_comm, ← le_himp_iff]
    apply inf_le_left
  · apply inf_le_right
· rw [inf_comm]
  apply le_inf
  · apply le_trans (himp_inf_le _ _); apply le_refl
  · apply inf_le_left
```

**lean_error:** tail step 2/9 ('· apply le_inf'): unsolved goals

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 62.0s, verify 0.3s, in=257, out=3898)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
apply inf_le_inf
apply inf_implies_le
apply inf_le_right
apply inf_le_inf
apply le_implies_of_inf_le
apply inf_le_left
apply inf_le_right
```

**lean_error:** tail step 3/8 ('apply inf_implies_le'): unknown identifier 'inf_implies_le'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=671, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm],
rw [inf_himp],
rw [inf_comm]
```

**lean_error:** tail step 1/3 ('rw [inf_comm],'): <stdin>:1:13: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=640, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=660, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1110, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=1076, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 6.3s, verify 0.1s, in=1099, out=356)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1134, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=1155, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1123, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```
