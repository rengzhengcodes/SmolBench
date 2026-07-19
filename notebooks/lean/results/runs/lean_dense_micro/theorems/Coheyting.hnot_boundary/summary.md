# Coheyting.hnot_boundary   (k=0, 1 tactics total)

file: `Mathlib/Order/Heyting/Boundary.lean`  

**Ground-truth tail (from k):**
```lean
rw [boundary, hnot_inf_distrib, sup_hnot_self]
```

**True premises at k:** `Coheyting.boundary`, `hnot_inf_distrib`, `sup_hnot_self`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✓ ✓ | ✘ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.5s, verify 0.1s, in=238, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact codiscrete_dual_bot a
```

**lean_error:** tail step 1/1 ('exact codiscrete_dual_bot a'): unknown identifier 'codiscrete_dual_bot'

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=238, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact codisjoint_top_right_iff.mpr (bot_disjoint a)
```

**lean_error:** tail step 1/1 ('exact codisjoint_top_right_iff.mpr (bot_disjoint a)'): unknown identifier 'codisjoint_top_right_iff.mpr'

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=238, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [coheytingAlgebra.complement_bot]
rw [bot_sup_eq]
rw [complement_top]
```

**lean_error:** tail step 1/3 ('rw [coheytingAlgebra.complement_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=238, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact codisjoint_top_right_iff.mpr (codisjoint_top_left.mpr (heyting.implies_complement (complement_complement a)))
```

**lean_error:** tail step 1/1 ('exact codisjoint_top_right_iff.mpr (codisjoint_top_left.mpr (heyting.implies_complement (complement_complement a)))'): unknown identifier 'codisjoint_top_right_iff.mpr'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=238, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.7s, verify 0.1s, in=238, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=238, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [codisjoint_iff_le_sup_right, hnot_le]
```

**lean_error:** tail step 1/1 ('simp [codisjoint_iff_le_sup_right, hnot_le]'): unknown identifier 'codisjoint_iff_le_sup_right'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=238, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [compl_bot, coheytingBoundary, inf_top_eq]
```

**lean_error:** tail step 1/1 ('simp_rw [compl_bot, coheytingBoundary, inf_top_eq]'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=690, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [hnot_inf_distrib, boundary]
rw [sup_hnot_self]
```

**lean_error:** tail step 1/2 ('rw [hnot_inf_distrib, boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=690, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [hnot_inf_distrib, Coheyting.boundary]
exact sup_hnot_self a
```

**lean_error:** tail step 1/2 ('rw [hnot_inf_distrib, Coheyting.boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 1.1s, verify 0.2s, in=690, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Coheyting.boundary]
rw [hnot_inf_distrib]
rw [sup_hnot_self]
```

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 1.4s, verify 0.2s, in=690, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Coheyting.boundary]
rw [hnot_inf_distrib]
rw [sup_hnot_self]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=690, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [hnot_inf_distrib, sup_hnot_self]
```

**lean_error:** tail step 1/1 ('rw [hnot_inf_distrib, sup_hnot_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=690, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [hnot_inf_distrib, sup_hnot_self]
```

**lean_error:** tail step 1/1 ('rw [hnot_inf_distrib, sup_hnot_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.5s, verify 0.1s, in=690, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=690, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [hnot_inf_distrib, sup_hnot_self, inf_top_eq]
```

**lean_error:** tail step 1/1 ('rw [hnot_inf_distrib, sup_hnot_self, inf_top_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
