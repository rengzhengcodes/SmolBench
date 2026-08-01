# Array.swapAt!_def   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [swapAt!, h]
```

**True premises at k:** `Array.swapAt!`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=269, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [swapAt_eq]
rw [getElem_eq]
rw [set_eq]
rw [getElem_eq]
```

**lean_error:** tail step 1/4 ('rw [swapAt_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=243, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [swapAt!, Array.getElem!, Array.set]
```

**lean_error:** tail step 1/1 ('simp [swapAt!, Array.getElem!, Array.set]'): unknown constant 'Array.getElem!'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.5s, verify 0.3s, in=258, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [swapAt!]
simp [swapAt!]
```

**final state (truncated):**
```
α : Type u_1
a : Array α
i : Nat
v : α
h : i < size a
⊢ (if h : i < size a then (a[i], set a { val := i, isLt := ⋯ } v)
...
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=508, out=21)

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

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.4s, in=480, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Array.swapAt!]
simp only [dif_pos h]
rw [Array.swapAt]
simp only [Prod.mk.eta]
rfl
```

**lean_error:** tail step 4/5 ('simp only [Prod.mk.eta]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=497, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [swapAt!, dif_pos h]
rfl
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=2035, out=36)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold swapAt!
split_ifs with h
· unfold swapAt
  congr
  unfold Array.set
  unfold Array.get
  unfold Array.size
· contradiction
```

**lean_error:** tail step 2/8 ('split_ifs with h'): <stdin>:1:1: unknown tactic

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=2015, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [swapAt!, Fin.val_mk, Array.get_set_eq, Array.set_set_eq]
```

**lean_error:** tail step 1/1 ('simp [swapAt!, Fin.val_mk, Array.get_set_eq, Array.set_set_eq]'): unknown constant 'Array.set_set_eq'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=2024, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [swapAt!]
split_ifs
simp [swapAt]
```

**lean_error:** tail step 2/3 ('split_ifs'): <stdin>:1:1: unknown tactic

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.4s, in=2060, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold swapAt!
rw [dif_pos h]
unfold swapAt
rw [set_eq_of_val_eq h]
```

**lean_error:** tail step 4/4 ('rw [set_eq_of_val_eq h]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=2208, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [swapAt!, swapAt]
simp [set_eq_set]
```

**lean_error:** tail step 2/2 ('simp [set_eq_set]'): unknown identifier 'set_eq_set'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.3s, verify 0.3s, in=2049, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [swapAt!]
simp [swapAt]
```

**final state (truncated):**
```
α : Type u_1
a : Array α
i : Nat
v : α
h : i < size a
⊢ (if h : i < size a then (a[i], set a { val := i, isLt := ⋯ } v)
...
```
