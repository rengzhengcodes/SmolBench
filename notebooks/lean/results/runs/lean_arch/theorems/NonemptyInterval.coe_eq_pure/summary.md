# NonemptyInterval.coe_eq_pure   (k=0, 1 tactics total)

file: `Mathlib/Order/Interval.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Interval.coe_inj, coe_pure_interval]
```

**True premises at k:** `Interval.coe_inj`, `NonemptyInterval.coe_pure_interval`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.2s, in=281, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  ext1
  exact h
· intro h
  exact congr_arg coe h
```

**lean_error:** tail step 2/6 ('· intro h'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=255, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← coe_pure, coe_inj]
simp [pure, NonemptyInterval.pure]
```

**lean_error:** tail step 1/2 ('rw [← coe_pure, coe_inj]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=270, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [NonemptyInterval.coe_eq_pure]
```

**lean_error:** tail step 1/1 ('rw [NonemptyInterval.coe_eq_pure]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 1.3s, in=618, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_pure_interval],
exact coe_inj
```

**lean_error:** tail step 1/2 ('rw [coe_pure_interval],'): <stdin>:1:22: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=589, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← coe_pure_interval, ← Interval.coe_inj]
simp only [coe_inj]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=607, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← coe_pure_interval]
exact coe_inj
```

**lean_error:** tail step 2/2 ('exact coe_inj'): unknown identifier 'coe_inj'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=2263, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [NonemptyInterval.coe_pure_interval]
exact Interval.coe_inj
```

**lean_error:** tail step 1/2 ('rw [NonemptyInterval.coe_pure_interval]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=2241, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← coe_pure_interval, Interval.coe_inj]
simp only [pure.injEq, imp_self, forall_const]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.2s, verify 0.2s, in=2252, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← NonemptyInterval.coe_pure_interval]
exact Interval.coe_inj
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=2289, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Interval.coe_inj, NonemptyInterval.coe_pure_interval]
exact Iff.rfl
```

**lean_error:** tail step 1/2 ('rw [Interval.coe_inj, NonemptyInterval.coe_pure_interval]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=2448, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← coe_pure_interval a, Interval.coe_inj]
simp only [pure_inj]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=2278, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← coe_pure_interval, coe_inj]
```

**lean_error:** tail step 1/1 ('rw [← coe_pure_interval, coe_inj]'): tactic 'rewrite' failed, equality or iff proof expected
