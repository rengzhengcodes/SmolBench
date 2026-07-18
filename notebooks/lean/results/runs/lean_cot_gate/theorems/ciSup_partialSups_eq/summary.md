# ciSup_partialSups_eq   (k=3, 4 tactics total)

file: `Mathlib/Order/PartialSups.lean`  

**Ground-truth tail (from k):**
```lean
rwa [bddAbove_range_partialSups]
```

**True premises at k:** `bddAbove_range_partialSups`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✓ ✘ |
| `hint:2` | ✓ ✓ ✓ · |
| `hint:3` | · · ✓ ✓ |
| `noise:3` | · ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=240, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.partialSups
```

**lean_error:** tail step 1/1 ('exact h.partialSups'): invalid field 'partialSups', the environment does not contain 'BddAbove.partialSups'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=240, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Bounded.partialSups_bddAbove h
```

**lean_error:** tail step 1/1 ('exact Bounded.partialSups_bddAbove h'): unknown identifier 'Bounded.partialSups_bddAbove'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=240, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=240, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact BddAbove.mono (partialSups_le_range h) (Set.subset_range_partialSups f)
```

**lean_error:** tail step 1/1 ('exact BddAbove.mono (partialSups_le_range h) (Set.subset_range_partialSups f)'): internal exception #7

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=510, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=510, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=510, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.6s, verify 0.1s, in=510, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range f)
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.2s, verify 0.1s, in=1171, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range f)
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.7s, verify 0.1s, in=1171, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [bddAbove_range_partialSups]
```

**final state (truncated):**
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range f)
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.7s, verify 0.1s, in=1171, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.1s, verify 0.1s, in=1171, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=1196, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range f)
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=1196, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=1196, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.3s, verify 0.1s, in=1196, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```
