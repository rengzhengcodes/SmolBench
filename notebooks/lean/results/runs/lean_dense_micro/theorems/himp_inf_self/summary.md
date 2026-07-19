# himp_inf_self   (k=0, 1 tactics total)

file: `Mathlib/Order/Heyting/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

**True premises at k:** `inf_comm`, `inf_himp`, `inf_comm`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=268, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm]
rw [imp_inf_self]
```

**lean_error:** tail step 2/2 ('rw [imp_inf_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.8s, verify 0.2s, in=268, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm]
rw [imp_inf_self]
```

**lean_error:** tail step 2/2 ('rw [imp_inf_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.4s, verify 0.2s, in=268, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm]
rw [imp_eq_sup]
rw [sup_inf_self_left]
rw [inf_comm]
```

**lean_error:** tail step 2/4 ('rw [imp_eq_sup]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.6s, verify 0.2s, in=268, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm]
rw [imp_eq_sup_inv]
rw [inf_comm]
rw [inf_sup_assoc]
rw [inf_idem]
rw [inf_comm]
```

**lean_error:** tail step 2/6 ('rw [imp_eq_sup_inv]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=268, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm, imp_inf_self]
```

**lean_error:** tail step 1/1 ('rw [inf_comm, imp_inf_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=268, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm, ← himp_left_comm, inf_comm]
```

**lean_error:** tail step 1/1 ('rw [inf_comm, ← himp_left_comm, inf_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=268, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm, ← himp_bot, himp_inf_distrib, bot_sup_eq, sup_idem]
```

**lean_error:** tail step 1/1 ('rw [inf_comm, ← himp_bot, himp_inf_distrib, bot_sup_eq, sup_idem]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=268, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm, imp_inf_distrib, inf_comm, inf_assoc, inf_absorb_right, inf_comm]
```

**lean_error:** tail step 1/1 ('rw [inf_comm, imp_inf_distrib, inf_comm, inf_assoc, inf_absorb_right, inf_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 0.9s, verify 0.1s, in=671, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=671, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=671, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm],
rw [inf_himp],
rw [inf_comm]
```

**lean_error:** tail step 1/3 ('rw [inf_comm],'): <stdin>:1:13: expected end of input

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 1.1s, verify 0.2s, in=671, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm]
rw [inf_himp]
rw [inf_comm]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.0s, verify 0.1s, in=671, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=671, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=671, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=671, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```
