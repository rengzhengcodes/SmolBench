# Set.isPWO_insert   (k=0, 1 tactics total)

file: `Mathlib/Order/WellFoundedSet.lean`  

**Ground-truth tail (from k):**
```lean
simp only [← singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**True premises at k:** `Set.singleton_union`, `Set.isPWO_union`, `Set.isPWO_singleton`, `true_and_iff`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | · · ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.1s, verify 0.1s, in=259, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [insert_eq, isPWO_union, isPWO_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.1s, verify 0.1s, in=259, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [insert_eq, isPWO_union, isPWO_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=259, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [insert_eq, isPWO_union, isPWO_singleton, iff_true_iff]
```

**lean_error:** tail step 1/1 ('simp_rw [insert_eq, isPWO_union, isPWO_singleton, iff_true_iff]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 70.5s, verify 0.4s, in=259, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [insert_eq, isPWO_union]
```

**lean_error:** tail step 1/1 ('simp [insert_eq, isPWO_union]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=722, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=722, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 70.9s, verify 0.1s, in=722, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 70.9s, verify 1.2s, in=722, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1126, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=1126, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1126, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=1126, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=1151, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=1151, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1151, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 5.8s, verify 0.1s, in=1151, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress
