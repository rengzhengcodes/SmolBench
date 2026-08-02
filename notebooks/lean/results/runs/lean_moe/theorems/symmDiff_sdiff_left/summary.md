# symmDiff_sdiff_left   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_idem, sdiff_sdiff_self, bot_sup_eq]
```

**True premises at k:** `symmDiff_def`, `sup_sdiff`, `sdiff_idem`, `sdiff_sdiff_self`, `bot_sup_eq`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.6s, verify 0.1s, in=301, out=3002)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [symmDiff_def, sdiff_sup, sdiff_eq_bot_iff, sdiff_le,
      sdiff_eq_self_iff, disjoint_sdiff_self_left]
```

**lean_error:** tail step 1/2 ('simp [symmDiff_def, sdiff_sup, sdiff_eq_bot_iff, sdiff_le,'): <stdin>:1:58: unexpected end of input; expected ']'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 32.6s, verify 0.1s, in=245, out=4006)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [SymmDiff, diff]
<;> boolean
```

**lean_error:** tail step 1/2 ('rw [SymmDiff, diff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.1s, in=245, out=644)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq]
rw [sdiff_sup]
simp [sdiff_sdiff_self]
```

**lean_error:** tail step 1/3 ('rw [symmDiff_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.1s, verify 0.1s, in=945, out=520)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 10.4s, verify 0.4s, in=893, out=1134)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff]
rw [sdiff_sdiff_self]
rw [sdiff_idem]
rw [bot_sup_eq]
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.1s, verify 0.4s, in=883, out=630)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff]
rw [sdiff_sdiff_self]
rw [sdiff_idem]
rw [bot_sup_eq]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.1s, verify 0.1s, in=1928, out=746)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 35.5s, verify 0.4s, in=1895, out=4371)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff]
rw [sdiff_sdiff_self]
rw [sdiff_idem]
rw [bot_sup_eq]
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.0s, verify 0.1s, in=1863, out=474)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.3s, verify 0.1s, in=1805, out=774)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 25.2s, verify 0.4s, in=2014, out=3011)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff]
rw [sdiff_sdiff_self]
rw [sdiff_idem]
rw [bot_sup_eq]
<;> rfl
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 3.9s, verify 0.2s, in=1838, out=372)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff]
simp [sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```
