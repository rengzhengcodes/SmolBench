# OrderHom.coe_iSup   (k=1, 2 tactics total)

file: `Mathlib/Order/Hom/Order.lean`  

**Ground-truth tail (from k):**
```lean
simp [iSup_apply]
```

**True premises at k:** `OrderHom.iSup_apply`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.1s, in=336, out=635)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 109.9s, verify 0.1s, in=283, out=15192)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  (⨆ i, f i) x = ⇑(⨆ i, f i) x := by rfl
  _ = (⨆ i, ⇑(f i)) x := by apply OrderEmbedding.map_iSup
  _ = iSup (fun i => ⇑(f i)) x := by simp [iSup]
```

**lean_error:** tail step 1/4 ('calc'): <stdin>:1:4: unexpected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 10.1s, verify 0.1s, in=280, out=1017)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.0s, verify 0.1s, in=580, out=738)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [OrderHom.iSup_apply]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 99.7s, verify 0.1s, in=524, out=13598)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  (⨆ i, f i) x = ⨆ i, f i x := by rw [OrderHom.iSup_apply]
  _ = ⨆ i, ⇑(f i) x := by apply iSup_congr; intro i; rfl
  _ = (⨆ i, ⇑(f i)) x := by rw [← iSup_apply]
  _ = iSup (fun i => ⇑(f i)) x := by rfl
```

**lean_error:** tail step 1/5 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 20.4s, verify 0.1s, in=528, out=2174)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply, iSup_apply]
```

**lean_error:** tail step 1/1 ('rw [OrderHom.iSup_apply, iSup_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.6s, verify 0.1s, in=1166, out=1144)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [OrderHom.iSup_apply]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 85.4s, verify 0.2s, in=1109, out=11639)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply]
have h : iSup (fun i => ⇑(f i)) x = iSup (fun i => f i x) := by
  congr
  <;> ext i
  <;> rfl
rw [h]
rw [iSup]
<;> rfl
```

**lean_error:** tail step 2/8 ('have h : iSup (fun i => ⇑(f i)) x = iSup (fun i => f i x) := by'): <stdin>:1:63: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 72.5s, verify 0.1s, in=1109, out=7777)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply, iSup_apply]
rfl
```

**lean_error:** tail step 1/2 ('rw [OrderHom.iSup_apply, iSup_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.3s, verify 0.1s, in=1117, out=827)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [OrderHom.iSup_apply]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 22.3s, verify 0.2s, in=1222, out=3019)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply]
<;> rfl
```

**lean_error:** tail step 2/2 ('<;> rfl'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 0.1s, in=1123, out=451)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact OrderHom.iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact OrderHom.iSup_apply f x'): type mismatch
