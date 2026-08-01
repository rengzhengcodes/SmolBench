# Filter.Tendsto.eventually_forall_le_atBot   (k=1, 2 tactics total)

file: `Mathlib/Order/Filter/AtTopBot.lean`  

**Ground-truth tail (from k):**
```lean
exact (h_evtl.comap f).filter_mono hf.le_comap
```

**True premises at k:** `Filter.Eventually.filter_mono`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=348, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
filter_eventually.preimage hf h_evtl
filter_eventually.mono
intros x h y hy
exact h y hy
```

**lean_error:** tail step 1/4 ('filter_eventually.preimage hf h_evtl'): <stdin>:1:1: unknown tactic

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=321, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
filter_upwards [hf.eventually h_evtl] simp only [mem_preimage, mem_atBot]
```

**lean_error:** tail step 1/1 ('filter_upwards [hf.eventually h_evtl] simp only [mem_preimage, mem_atBot]'): <stdin>:1:38: expected end of input

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=337, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply h_evtl.comp hf
```

**lean_error:** tail step 1/1 ('apply h_evtl.comp hf'): invalid field 'comp', the environment does not contain 'Filter.GenerateSets.comp'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=608, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Filter.Eventually.filter_mono hf h_evtl
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=579, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact hf h_evtl
```

**lean_error:** tail step 1/1 ('exact hf h_evtl'): kernel type check failed: application type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=597, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h_evtl.filter_mono hf
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=857, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Filter.Eventually.filter_mono hf h_evtl
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.4s, in=831, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (hf h_evtl).filter_mono tendsto_principal_principal.mpr le_rfl
```

**lean_error:** tail step 1/1 ('exact (hf h_evtl).filter_mono tendsto_principal_principal.mpr le_rfl'): invalid field 'filter_mono', the environment does not contain 'Membership.mem.filter_mono'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=846, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h_evtl.filter_mono hf
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=881, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Filter.Eventually.filter_mono hf h_evtl
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=882, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact hf h_evtl
```

**lean_error:** tail step 1/1 ('exact hf h_evtl'): kernel type check failed: application type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=870, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply h_evtl.filter_mono
exact hf
```

**lean_error:** tail step 1/2 ('apply h_evtl.filter_mono'): tactic 'apply' failed, failed to unify
