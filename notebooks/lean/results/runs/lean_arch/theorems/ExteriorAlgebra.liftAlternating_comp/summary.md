# ExteriorAlgebra.liftAlternating_comp   (k=6, 7 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**True premises at k:** `AlternatingMap.curryLeft_compAlternatingMap`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | X |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=544, out=82)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [liftAlternating_comm],
rw [LinearMap.compAlternatingMap_curryLeft],
rw [liftAlternating_comm],
rw [AlternatingMap.curryLeft_compAlternatingMap],
rw [liftAlternating_comm],
rw [LinearMap.compAlternatingMap_curryLeft],
rw [hx ((fun i => AlternatingMap.curryLeft (f i)) ∘ Nat.succ)]
```

**lean_error:** tail step 1/7 ('rw [liftAlternating_comm],'): <stdin>:1:25: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=512, out=78)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [liftAlternating_apply, liftAlternating_apply]
simp only [LinearMap.compAlternatingMap_apply, AlternatingMap.curryLeft_apply]
congr with i
cases i
simp only [Nat.succ_ne_zero, not_false_eq_true, IsEmpty.forall_iff]
simp only [Nat.succ.injEq, Function.funext_iff, forall_const]
```

**lean_error:** tail step 1/6 ('rw [liftAlternating_apply, liftAlternating_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 5.2s, verify 300.1s, in=533, out=314)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply hx
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=960, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=915, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
congr 1
exact hx _
```

**lean_error:** tail step 1/3 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=949, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=1147, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=1105, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
simp only [Function.comp_apply]
rw [hx]
```

**lean_error:** tail step 1/3 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=1136, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=1171, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [liftAlternating_compLinearMap g]
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/2 ('rw [liftAlternating_compLinearMap g]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.8s, in=1148, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [AlternatingMap.curryLeft_compAlternatingMap]
rw [hx]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 305.3s, verify 36.7s, in=1160, out=403)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
rw [hx]
```

**lean_error:** tail step 1/2 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'apply' failed, failed to unify
