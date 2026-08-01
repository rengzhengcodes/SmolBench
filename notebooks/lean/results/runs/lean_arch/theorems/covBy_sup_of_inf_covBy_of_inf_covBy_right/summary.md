# covBy_sup_of_inf_covBy_of_inf_covBy_right   (k=1, 2 tactics total)

file: `Mathlib/Order/ModularLattice.lean`  

**Ground-truth tail (from k):**
```lean
exact fun ha hb => covBy_sup_of_inf_covBy_of_inf_covBy_left hb ha
```

**True premises at k:** `covBy_sup_of_inf_covBy_of_inf_covBy_left`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=280, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intros h₁ h₂,
apply weak_covby_sup_intro,
exact h₁,
exact h₂,
covby_sup_of_covby_left h₂,
```

**lean_error:** tail step 1/5 ('intros h₁ h₂,'): <stdin>:1:12: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=246, out=40)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← snot_le, snot_le]
rintro ⟨h₁, h₂⟩
exact IsWeakUpperModularLattice.covWUM ⟨h₁, h₂⟩
```

**lean_error:** tail step 1/3 ('rw [← snot_le, snot_le]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=269, out=45)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro h1,
intro h2,
rw [←h2.cover_le] at h1,
exact h1.trans (h2.trans_eq (sup_le_le_sup h2.le h1.le)),
```

**lean_error:** tail step 1/4 ('intro h1,'): <stdin>:1:8: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=534, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact covBy_sup_of_inf_covBy_of_inf_covBy_left
```

**lean_error:** tail step 1/1 ('exact covBy_sup_of_inf_covBy_of_inf_covBy_left'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.5s, in=489, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact covBy_sup_of_inf_covBy_of_inf_covBy_left
```

**lean_error:** tail step 1/1 ('exact covBy_sup_of_inf_covBy_of_inf_covBy_left'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=523, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply covBy_sup_of_inf_covBy_of_inf_covBy_left
```

**lean_error:** tail step 1/1 ('apply covBy_sup_of_inf_covBy_of_inf_covBy_left'): tactic 'apply' failed, failed to unify
