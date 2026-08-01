# PerfectRing.lift_comp_lift_apply_eq_self   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/IsPerfectClosure.lean`  

**Ground-truth tail (from k):**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

**True premises at k:** `PerfectRing.lift_comp_lift_apply`, `PerfectRing.lift_self_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=441, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [lift_symm] 
simp only [RingHom.comp_apply, lift_id]
```

**lean_error:** tail step 1/2 ('rw [lift_symm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=411, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← lift_iLift j i p x]
rw [iLift_lift i j p x]
rw [RingHom.id_apply]
```

**lean_error:** tail step 1/3 ('rw [← lift_iLift j i p x]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=430, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply lift_comp
```

**lean_error:** tail step 1/1 ('apply lift_comp'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=760, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [lift_comp_lift_apply],
rw [lift_self_apply]
```

**lean_error:** tail step 1/2 ('rw [lift_comp_lift_apply],'): <stdin>:1:25: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=743, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← lift_comp_lift_apply, lift_self_apply]
```

**lean_error:** tail step 1/1 ('rw [← lift_comp_lift_apply, lift_self_apply]'): failed to synthesize

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=749, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=1249, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=1234, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← lift_comp_lift_apply i j i, lift_self_apply]
```

**lean_error:** tail step 1/1 ('rw [← lift_comp_lift_apply i j i, lift_self_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1238, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1272, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [lift_comp_lift_apply],
rw [lift_self_apply]
```

**lean_error:** tail step 1/2 ('rw [lift_comp_lift_apply],'): <stdin>:1:25: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=1310, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← lift_comp_lift_apply i j i]
rw [lift_self_apply]
```

**lean_error:** tail step 1/2 ('rw [← lift_comp_lift_apply i j i]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1261, out=36)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```
