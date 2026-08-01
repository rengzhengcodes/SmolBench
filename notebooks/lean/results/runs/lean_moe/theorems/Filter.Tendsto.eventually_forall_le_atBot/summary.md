# Filter.Tendsto.eventually_forall_le_atBot   (k=1, 2 tactics total)

file: `Mathlib/Order/Filter/AtTopBot.lean`  

**Ground-truth tail (from k):**
```lean
exact (h_evtl.comap f).filter_mono hf.le_comap
```

**True premises at k:** `Filter.Eventually.filter_mono`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✓ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=391, out=414)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact hf.eventually h_evtl
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.6s, verify 0.1s, in=670, out=1382)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact hf.eventually h_evtl
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.7s, verify 0.1s, in=934, out=907)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact hf.eventually h_evtl
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 30.1s, verify 0.1s, in=923, out=6341)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact hf.eventually h_evtl
```
