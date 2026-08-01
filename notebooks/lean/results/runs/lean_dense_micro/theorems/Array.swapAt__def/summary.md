# Array.swapAt!_def   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [swapAt!, h]
```

**True premises at k:** `Array.swapAt!`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ · ✘ ✘ |
| `hint:2` | ✓ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.5s, verify 0.1s, in=269, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [swapAt_eq]
rw [set_eq]
```

**lean_error:** tail step 1/2 ('rw [swapAt_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **incomplete**  (gen 0.6s, verify 0.4s, in=269, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [swapAt!, set]
simp
rw [getElem]
```

**final state (truncated):**
```
α : Type u_1
a : Array α
i : Nat
v : α
h : i < size a
⊢ (if h : i < size a then (instGetElemArrayNatLtInstLTNatSize.1 a i ⋯, set a { val := i, isLt := ⋯ } v)
...
```

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=269, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [swapAt_eq]
rw [getElem_eq]
rw [set_eq]
rw [getElem_eq]
```

**lean_error:** tail step 1/4 ('rw [swapAt_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 3.1s, verify 0.1s, in=269, out=38)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [swapAt_eq_swap]
rw [swap_eq]
congr
rw [getElem_eq_get]
rw [getElem_eq_get]
congr
rw [set_eq]
```

**lean_error:** tail step 1/7 ('rw [swapAt_eq_swap]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 1.0s, verify 0.4s, in=508, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold swapAt!
rw [dif_pos h]
unfold swapAt
simp
```

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.4s, verify 1.2s, in=508, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [swapAt!]
split_ifs with h'
· rfl
· contradiction
```

**lean_error:** tail step 2/4 ("split_ifs with h'"): <stdin>:1:1: unknown tactic

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.2s, in=508, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold swapAt!
split_ifs with h
· unfold swapAt
  rfl
· contradiction
```

**lean_error:** tail step 2/5 ('split_ifs with h'): <stdin>:1:1: unknown tactic

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.9s, verify 0.2s, in=508, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Array.swapAt!]
split_ifs with h
· exact swapAt_def _ _ _
· contradiction
```

**lean_error:** tail step 2/4 ('split_ifs with h'): <stdin>:1:1: unknown tactic
