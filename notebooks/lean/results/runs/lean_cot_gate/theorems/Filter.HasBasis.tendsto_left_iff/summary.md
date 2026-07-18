# Filter.HasBasis.tendsto_left_iff   (k=1, 2 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=354, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.6s, verify 0.1s, in=354, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.6s, verify 0.1s, in=354, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [MapsTo, Set.subset_def]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=354, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [MapsTo, Set.subset_def]
```
