# Order.mem_range_pred_of_not_isPredLimit   (k=1, 2 tactics total)

file: `Mathlib/Order/SuccPred/Limit.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨b, hb.2⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=312, out=364)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨b, hb.2⟩
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 8.9s, verify 0.2s, in=258, out=1216)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨b, hb.2⟩
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.2s, in=252, out=377)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use b
exact hb.2.symm
```

**lean_error:** tail step 2/2 ('exact hb.2.symm'): type mismatch
