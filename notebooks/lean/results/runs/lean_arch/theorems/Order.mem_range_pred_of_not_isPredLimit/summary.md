# Order.mem_range_pred_of_not_isPredLimit   (k=1, 2 tactics total)

file: `Mathlib/Order/SuccPred/Limit.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨b, hb.2⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **success**  (gen 0.4s, verify 0.2s, in=269, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use b
simp [hb.2]
```

### `stepk:1` · llama4-maverick-base · rollout 0 → **success**  (gen 0.2s, verify 0.1s, in=243, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨b, hb.2⟩
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=258, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply mem_range_self
```

**lean_error:** tail step 1/1 ('apply mem_range_self'): tactic 'apply' failed, failed to unify
