# Array.swapAt!_def   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [swapAt!, h]
```

**True premises at k:** `Array.swapAt!`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 0.6s, in=307, out=1250)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 14.9s, verify 0.1s, in=253, out=1630)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.4s, verify 0.1s, in=254, out=404)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.7s, verify 0.1s, in=557, out=708)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Array.swapAt!, h, Array.swapAt]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 109.7s, verify 0.2s, in=503, out=12924)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [swapAt!]
<;> split_ifs <;> simp_all [decide]
<;> rw [swapAt]
<;> simp
```

**lean_error:** tail step 2/4 ('<;> split_ifs <;> simp_all [decide]'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 0.2s, in=502, out=449)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Array.swapAt!]
split_ifs <;> simp_all
```

**lean_error:** tail step 2/2 ('split_ifs <;> simp_all'): <stdin>:1:1: unknown tactic

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.4s, verify 0.1s, in=2101, out=428)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Array.swapAt!, h, swapAt]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 110.7s, verify 0.1s, in=2067, out=13063)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [show swapAt! a i v = swapAt a ⟨i, h⟩ v by
  dsimp [swapAt!]
  split_ifs <;> simp_all]
rw [show swapAt a ⟨i, h⟩ v = (a.get ⟨i, h⟩, a.set ⟨i, h⟩ v) by
  dsimp [swapAt]
  <;> rfl]
<;> rfl
```

**lean_error:** tail step 1/7 ('rw [show swapAt! a i v = swapAt a ⟨i, h⟩ v by'): <stdin>:1:45: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.3s, verify 0.1s, in=2091, out=522)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [swapAt!, h]
<;> simp [swapAt]
<;> rfl
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.6s, verify 0.1s, in=1967, out=672)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Array.swapAt!, Array.swapAt, h]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 75.6s, verify 0.1s, in=2347, out=8539)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [swapAt!, h, swapAt]
<;> rfl
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.6s, verify 0.1s, in=2072, out=541)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [swapAt!, h]
```
