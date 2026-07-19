# Coheyting.hnot_boundary   (k=0, 1 tactics total)

file: `Mathlib/Order/Heyting/Boundary.lean`  

**Ground-truth tail (from k):**
```lean
rw [boundary, hnot_inf_distrib, sup_hnot_self]
```

**True premises at k:** `Coheyting.boundary`, `hnot_inf_distrib`, `sup_hnot_self`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✘ ✓ | ✓ ✘ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✘ ✘ ✓ ✓ | ✓ ✓ ✓ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✓ ✘ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 87.5s, verify 0.1s, in=208, out=3922)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [boundary_eq, inf_neg_self, neg_bot]
```

**lean_error:** tail step 1/1 ('rw [boundary_eq, inf_neg_self, neg_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 134.7s, verify 0.1s, in=208, out=6052)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [neg_inf, sup_neg_self]
```

**lean_error:** tail step 1/1 ('rw [neg_inf, sup_neg_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 144.3s, verify 0.1s, in=208, out=6475)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [neg_inf_eq_sup_neg, sup_neg_self]
```

**lean_error:** tail step 1/1 ('rw [neg_inf_eq_sup_neg, sup_neg_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 234.8s, verify 0.1s, in=208, out=10393)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [boundary, join_neg_self, neg_top]
```

**lean_error:** tail step 1/1 ('rw [boundary, join_neg_self, neg_top]'): tactic 'rewrite' failed, equality or iff proof expected

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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.1s, verify 0.1s, in=208, out=224)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [boundary_eq, neg_inf_eq, neg_neg, sup_neg_eq]
```

**lean_error:** tail step 1/1 ('rw [boundary_eq, neg_inf_eq, neg_neg, sup_neg_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 8.2s, verify 0.1s, in=208, out=228)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [not_inf, not_not, not_sup_self]
```

**lean_error:** tail step 1/1 ('rw [not_inf, not_not, not_sup_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.3s, verify 0.1s, in=208, out=230)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [boundary, neg_inf, neg_neg, sup_neg_eq_top]
```

**lean_error:** tail step 1/1 ('rw [boundary, neg_inf, neg_neg, sup_neg_eq_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.5s, verify 0.1s, in=208, out=234)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [not_inf, not_not, not_boundary]
```

**lean_error:** tail step 1/1 ('rw [not_inf, not_not, not_boundary]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 19.8s, verify 0.2s, in=650, out=900)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Coheyting.boundary]
rw [hnot_inf_distrib]
rw [sup_hnot_self]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 40.2s, verify 0.1s, in=650, out=1862)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [hnot_inf_distrib, sup_hnot_self]
```

**lean_error:** tail step 1/1 ('rw [hnot_inf_distrib, sup_hnot_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 52.6s, verify 0.2s, in=650, out=2419)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Coheyting.boundary]
rw [hnot_inf_distrib]
rw [sup_hnot_self (¬a)]
```

**lean_error:** tail step 3/3 ('rw [sup_hnot_self (¬a)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 83.2s, verify 0.1s, in=650, out=3745)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

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

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.5s, verify 0.1s, in=650, out=206)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 7.6s, verify 0.1s, in=650, out=208)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.1s, verify 0.1s, in=650, out=253)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 11.1s, verify 0.1s, in=650, out=331)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 71.8s, verify 0.1s, in=1117, out=1696)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 96.8s, verify 0.2s, in=1117, out=3402)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Coheyting.boundary]
rw [hnot_inf_distrib]
rw [sup_hnot_self]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 100.6s, verify 0.1s, in=1117, out=2641)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 119.7s, verify 0.1s, in=1117, out=3211)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Coheyting.boundary, hnot_inf_distrib]
apply sup_hnot_self
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

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 12.5s, verify 0.1s, in=1117, out=178)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 12.9s, verify 0.1s, in=1117, out=189)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 13.0s, verify 0.1s, in=1117, out=208)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.4s, verify 0.1s, in=1117, out=210)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Coheyting.hnot_boundary a
```

**lean_error:** tail step 1/1 ('exact Coheyting.hnot_boundary a'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 33.8s, verify 0.1s, in=1147, out=1571)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [hnot_inf_distrib, sup_hnot_self]
```

**lean_error:** tail step 1/1 ('rw [hnot_inf_distrib, sup_hnot_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 47.3s, verify 0.1s, in=1147, out=2179)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [hnot_inf_distrib]
rw [sup_hnot_self]
```

**lean_error:** tail step 1/2 ('rw [hnot_inf_distrib]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 66.3s, verify 0.1s, in=1147, out=3020)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [hnot_inf_distrib, sup_hnot_self]
```

**lean_error:** tail step 1/1 ('rw [hnot_inf_distrib, sup_hnot_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 74.0s, verify 0.1s, in=1147, out=3361)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Coheyting.boundary], rw [hnot_inf_distrib], rw [sup_hnot_self]
```

**lean_error:** tail step 1/1 ('rw [Coheyting.boundary], rw [hnot_inf_distrib], rw [sup_hnot_self]'): <stdin>:1:23: expected end of input

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

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 6.8s, verify 0.1s, in=1147, out=170)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.4s, verify 0.1s, in=1147, out=203)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.0s, verify 0.1s, in=1147, out=215)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.4s, verify 0.1s, in=1147, out=233)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Coheyting.boundary, hnot_inf_distrib, sup_hnot_self]
```
