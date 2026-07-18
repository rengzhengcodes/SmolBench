# NonemptyInterval.coe_eq_pure   (k=0, 1 tactics total)

file: `Mathlib/Order/Interval.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Interval.coe_inj, coe_pure_interval]
```

**True premises at k:** `Interval.coe_inj`, `NonemptyInterval.coe_pure_interval`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✓ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=257, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=257, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [coe_eq_coe]
```

**lean_error:** tail step 1/1 ('simp [coe_eq_coe]'): unknown identifier 'coe_eq_coe'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=257, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← coe_eq_coe, coe_pure]
```

**lean_error:** tail step 1/1 ('rw [← coe_eq_coe, coe_pure]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.1s, in=257, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← coe_eq_coe, coe_pure]
```

**lean_error:** tail step 1/1 ('rw [← coe_eq_coe, coe_pure]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=594, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← coe_pure_interval, coe_inj]
```

**lean_error:** tail step 1/1 ('rw [← coe_pure_interval, coe_inj]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=594, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [coe_inj, coe_pure_interval]
```

**lean_error:** tail step 1/1 ('simp [coe_inj, coe_pure_interval]'): unknown identifier 'coe_inj'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=594, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [coe_pure_interval, coe_inj]
```

**lean_error:** tail step 1/1 ('simp only [coe_pure_interval, coe_inj]'): unknown identifier 'coe_inj'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.9s, verify 0.1s, in=594, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Interval.coe_inj, coe_pure_interval]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=2251, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [coe_pure_interval, coe_inj]
```

**lean_error:** tail step 1/1 ('simp only [coe_pure_interval, coe_inj]'): unknown identifier 'coe_inj'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=2251, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← coe_pure_interval, coe_inj]
```

**lean_error:** tail step 1/1 ('rw [← coe_pure_interval, coe_inj]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.2s, verify 0.1s, in=2251, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← coe_pure_interval, coe_inj]
```

**lean_error:** tail step 1/1 ('simp [← coe_pure_interval, coe_inj]'): unknown identifier 'coe_inj'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.6s, verify 0.1s, in=2251, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [coe_pure_interval, ← coe_inj]
```

**lean_error:** tail step 1/1 ('simp only [coe_pure_interval, ← coe_inj]'): unknown identifier 'coe_inj'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=2268, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [coe_pure_interval, coe_inj]
```

**lean_error:** tail step 1/1 ('simp only [coe_pure_interval, coe_inj]'): unknown identifier 'coe_inj'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=2268, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← coe_pure_interval, coe_inj]
```

**lean_error:** tail step 1/1 ('rw [← coe_pure_interval, coe_inj]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=2268, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← coe_pure_interval, coe_inj]
```

**lean_error:** tail step 1/1 ('rw [← coe_pure_interval, coe_inj]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=2268, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← coe_pure_interval, ← coe_inj]
```

**lean_error:** tail step 1/1 ('simp [← coe_pure_interval, ← coe_inj]'): unknown identifier 'coe_inj'
