# Order.mem_range_pred_of_not_isPredLimit   (k=1, 2 tactics total)

file: `Mathlib/Order/SuccPred/Limit.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨b, hb.2⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 8.3s, verify 0.1s, in=242, out=371)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use b
exact hb.2
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 12.2s, verify 0.1s, in=242, out=542)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi b
exact hb.2
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 15.0s, verify 0.1s, in=242, out=666)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi b
exact hb.right
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 41.4s, verify 0.1s, in=242, out=2049)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use b
exact hb.right
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=242, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨b, hb.2⟩
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.5s, verify 0.1s, in=242, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨b, hb.2⟩
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.5s, verify 0.1s, in=242, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨b, hb.2⟩
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.6s, verify 0.1s, in=242, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨b, hb.2⟩
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 4.7s, verify 0.1s, in=242, out=138)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact mem_range.mpr ⟨b, hb.2⟩
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 5.3s, verify 0.1s, in=242, out=162)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨b, hb.2⟩
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=242, out=174)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [hb.right]
```

**lean_error:** tail step 1/1 ('rwa [hb.right]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 7.1s, verify 0.1s, in=242, out=216)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← hb.2, mem_range_self]
```

**lean_error:** tail step 1/1 ('rw [← hb.2, mem_range_self]'): tactic 'rewrite' failed, equality or iff proof expected
