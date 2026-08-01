# CategoryTheory.Abelian.exact_of_is_cokernel   (k=3, 4 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Exact.lean`  

**Ground-truth tail (from k):**
```lean
rw [← this, ← Category.assoc, kernel.condition, zero_comp]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.kernel.condition`, `CategoryTheory.Limits.zero_comp`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=336, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← this],
simp only [CokernelCofork.π_desc],
exact kernel.condition _
```

**lean_error:** tail step 1/3 ('rw [← this],'): <stdin>:1:11: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.2s, in=304, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Category.assoc, ← this, Category.assoc, cokernel.condition, comp_zero]
```

**lean_error:** tail step 1/1 ('rw [← Category.assoc, ← this, Category.assoc, cokernel.condition, comp_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=325, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply CokernelCofork-condition
apply h.fac
exact this
```

**lean_error:** tail step 1/3 ('apply CokernelCofork-condition'): unknown identifier 'condition'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=801, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [this, CategoryTheory.Category.assoc],
simp only [kernel.condition, zero_comp]
```

**lean_error:** tail step 1/2 ('rw [this, CategoryTheory.Category.assoc],'): <stdin>:1:40: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 2.8s, in=760, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← this, Category.assoc, kernel.condition g, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← this, Category.assoc, kernel.condition g, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=790, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [←this, Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [←this, Category.assoc, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1167, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [this, Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [this, Category.assoc, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.2s, in=1123, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← this, Category.assoc, kernel.condition g, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← this, Category.assoc, kernel.condition g, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=1156, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← cancel_epi (kernel.ι g), this, zero_comp]
exact kernel.condition
```

**lean_error:** tail step 1/2 ('rw [← cancel_epi (kernel.ι g), this, zero_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1191, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [this, CategoryTheory.Category.assoc],
simp only [kernel.condition, zero_comp]
```

**lean_error:** tail step 1/2 ('rw [this, CategoryTheory.Category.assoc],'): <stdin>:1:40: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.4s, verify 0.2s, in=1194, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← this, Category.assoc, kernel.condition g, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← this, Category.assoc, kernel.condition g, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1180, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← cancel_epi (kernel.ι g), this, zero_comp]
exact kernel.condition
```

**lean_error:** tail step 1/2 ('rw [← cancel_epi (kernel.ι g), this, zero_comp]'): tactic 'rewrite' failed, equality or iff proof expected
