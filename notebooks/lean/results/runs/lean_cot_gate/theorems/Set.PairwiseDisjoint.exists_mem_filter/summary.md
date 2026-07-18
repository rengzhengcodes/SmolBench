# Set.PairwiseDisjoint.exists_mem_filter   (k=4, 5 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨fun i => s i, fun i => (s i).2, hsd.set_of_subtype _ _⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 42.3s, verify 0.3s, in=351, out=1742)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use fun i => (s i).1
split
exact fun i => (s i).2
exact hsd
```

**lean_error:** tail step 2/4 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 56.7s, verify 0.1s, in=351, out=2458)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi s✝
split
  · intro i
    exact (s✝ i).2
  · exact hsd
```

**lean_error:** tail step 1/5 ('existsi s✝'): <stdin>:1:9: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 73.8s, verify 0.1s, in=351, out=3274)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi s
split
. intro i
  exact (s i).property
. exact hsd
```

**lean_error:** tail step 1/5 ('existsi s'): application type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 93.2s, verify 0.3s, in=351, out=4162)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use fun i ↦ ↑(s i)
split
· intro i
  exact (s i).2
· exact hsd
```

**lean_error:** tail step 2/5 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.7s, verify 0.1s, in=351, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun i => (s i).val, fun i => (s i).2, hsd⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun i => (s i).val, fun i => (s i).2, hsd⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=351, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun i => (s i).val, fun i => (s i).property, hsd⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun i => (s i).val, fun i => (s i).property, hsd⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=351, out=36)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun i => (s i).val, fun i => (s i).2, fun i j h => hsd i j h⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun i => (s i).val, fun i => (s i).2, fun i j h => hsd i j h⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=351, out=55)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun i => ↑(s ⟨i, mem_coe.mpr (hsd.mono fun _ _ _ _ => ‹_›)⟩), fun i => (s ⟨i, _⟩).2, hsd⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun i => ↑(s ⟨i, mem_coe.mpr (hsd.mono fun _ _ _ _ => ‹_›)⟩), fun i => (s ⟨i, _⟩).2, hsd⟩'): invalid constructor ⟨...⟩, expected type must be an inductive type 
