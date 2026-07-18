# Coheyting.hnot_boundary   (k=0, 1 tactics total)

file: `Mathlib/Order/Heyting/Boundary.lean`  

**Ground-truth tail (from k):**
```lean
rw [boundary, hnot_inf_distrib, sup_hnot_self]
```

**True premises at k:** `Coheyting.boundary`, `hnot_inf_distrib`, `sup_hnot_self`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✓ ✓ |
| `hint:3` | ✘ ✘ ✓ ✓ |
| `noise:3` | ✓ ✘ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=208, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=208, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [not_boundary]
```

**lean_error:** tail step 1/1 ('simp [not_boundary]'): unknown identifier 'not_boundary'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.8s, verify 0.1s, in=208, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [not_boundary, top_iff]
```

**lean_error:** tail step 1/1 ('rw [not_boundary, top_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.5s, verify 0.1s, in=208, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [nbot_eq_top, top_boundedIff]
```

**lean_error:** tail step 1/1 ('rw [nbot_eq_top, top_boundedIff]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=650, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=650, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [hnot_inf_distrib]
```

**lean_error:** tail step 1/1 ('simp [hnot_inf_distrib]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.9s, verify 0.1s, in=650, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 5.7s, verify 0.1s, in=650, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Coheyting.boundary, hnot_inf_distrib]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=1117, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [hnot_inf_distrib]
```

**lean_error:** tail step 1/1 ('simp [hnot_inf_distrib]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=1117, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [hnot_inf_distrib]
```

**lean_error:** tail step 1/1 ('simp [hnot_inf_distrib]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.8s, verify 0.1s, in=1117, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 5.1s, verify 0.1s, in=1117, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.4s, verify 0.1s, in=1147, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=1147, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [hnot_inf_distrib]
```

**lean_error:** tail step 1/1 ('simp [hnot_inf_distrib]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.9s, verify 0.1s, in=1147, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 3.6s, verify 0.1s, in=1147, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Coheyting.boundary, hnot_inf_distrib]
```
