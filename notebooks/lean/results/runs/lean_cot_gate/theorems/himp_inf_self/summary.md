# himp_inf_self   (k=0, 1 tactics total)

file: `Mathlib/Order/Heyting/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

**True premises at k:** `inf_comm`, `inf_himp`, `inf_comm`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ · ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✘ |
| `noise:3` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=241, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm, inf_rel, sup_comm]
```

**lean_error:** tail step 1/1 ('rw [inf_comm, inf_rel, sup_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.9s, verify 0.1s, in=241, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm, inf_himp]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
inst✝ : GeneralizedHeytingAlgebra α
a✝ b✝ c d a b : α
⊢ a ⊓ b = b ⊓ a
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=241, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm, inf_himp_self]
```

**lean_error:** tail step 1/1 ('rw [inf_comm, inf_himp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=241, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_comm, sdiff_inf_self]
```

**lean_error:** tail step 1/1 ('rw [inf_comm, sdiff_inf_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=636, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=636, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=636, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.5s, verify 0.1s, in=636, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=1078, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=1078, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.7s, verify 0.1s, in=1078, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.4s, verify 0.1s, in=1078, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [inf_comm, inf_himp, inf_comm]
```

**lean_error:** tail step 1/1 ('simp_rw [inf_comm, inf_himp, inf_comm]'): no goals to be solved

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1102, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=1102, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.5s, verify 0.1s, in=1102, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.5s, verify 0.1s, in=1102, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inf_comm, inf_himp, inf_comm]
```
