# Coheyting.hnot_boundary   (k=0, 1 tactics total)

file: `Mathlib/Order/Heyting/Boundary.lean`  

**Ground-truth tail (from k):**
```lean
rw [boundary, hnot_inf_distrib, sup_hnot_self]
```

**True premises at k:** `Coheyting.boundary`, `hnot_inf_distrib`, `sup_hnot_self`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=238, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [coheyting_bnot_cobnot]
rw [cobnot_top]
```

**lean_error:** tail step 1/2 ('rw [coheyting_bnot_cobnot]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 2.9s, in=207, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [himp_eq]
simp only [codisjoint_top_iff, himp_bot]
exact codisjoint_himp_self_left a
```

**lean_error:** tail step 1/3 ('rw [himp_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=227, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [coheyting_algebra.heyting_negation, coheyting_algebra.neg_top]
```

**lean_error:** tail step 1/1 ('rw [coheyting_algebra.heyting_negation, coheyting_algebra.neg_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=690, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [hnot_inf_distrib, Coheyting.boundary]
exact sup_hnot_self a
```

**lean_error:** tail step 1/2 ('rw [hnot_inf_distrib, Coheyting.boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=649, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← hnot_inf_distrib, boundary]
simp [sup_hnot_self]
```

**lean_error:** tail step 1/2 ('rw [← hnot_inf_distrib, boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=679, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [hnot_inf_distrib, sup_hnot_self, boundary]
simp [sup_comm]
```

**lean_error:** tail step 1/2 ('rw [hnot_inf_distrib, sup_hnot_self, boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1160, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [hnot_inf_distrib, Coheyting.boundary]
exact sup_hnot_self a
```

**lean_error:** tail step 1/2 ('rw [hnot_inf_distrib, Coheyting.boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1117, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← top_sdiff']
simp_rw [sdiff_self]
exact top_le_iff.mpr rfl
```

**lean_error:** tail step 2/3 ('simp_rw [sdiff_self]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1149, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [hnot_inf_distrib, sup_hnot_self, boundary]
simp [sup_comm]
```

**lean_error:** tail step 1/2 ('rw [hnot_inf_distrib, sup_hnot_self, boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1184, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [hnot_inf_distrib, Coheyting.boundary]
exact sup_hnot_self a
```

**lean_error:** tail step 1/2 ('rw [hnot_inf_distrib, Coheyting.boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1198, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← hnot_inf_distrib, boundary]
simp only [sup_hnot_self, top_inf]
```

**lean_error:** tail step 1/2 ('rw [← hnot_inf_distrib, boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1173, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [hnot_inf_distrib, sup_hnot_self, boundary]
simp [sup_comm]
```

**lean_error:** tail step 1/2 ('rw [hnot_inf_distrib, sup_hnot_self, boundary]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
