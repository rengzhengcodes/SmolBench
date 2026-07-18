# CategoryTheory.Limits.pullback_map_eq_pullbackFstFstIso_inv   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Diagonal.lean`  

**Ground-truth tail (from k):**
```lean
simp only [pullbackFstFstIso_inv, lift_snd_assoc, lift_fst]
```

**True premises at k:** `CategoryTheory.Limits.pullbackFstFstIso_inv`, `CategoryTheory.Limits.pullback.lift_snd_assoc`, `CategoryTheory.Limits.pullback.lift_fst`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✓ ✓ ✓ ✓ |
| `hint:2` | ✓ ✓ ✓ ✘ |
| `hint:3` | ✓ ✓ ✓ ✘ |
| `noise:3` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.7s, verify 0.1s, in=423, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [map]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.8s, verify 0.1s, in=423, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [map]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=423, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackFstFstIso]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=423, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.2s, in=870, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso_inv]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=870, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← Iso.eq_inv_comp, pullback.lift_fst]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.2s, verify 0.1s, in=870, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pullback.map, pullbackFstFstIso_inv]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.3s, verify 0.1s, in=870, out=57)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [← cancel_mono i₃, assoc, pullbackFstFstIso_inv, pullback.lift_fst,
  pullback.map_fst, pullback.lift_snd_assoc, Category.assoc, Iso.inv_hom_id, comp_id]
```

**lean_error:** tail step 1/2 ('simp only [← cancel_mono i₃, assoc, pullbackFstFstIso_inv, pullback.lift_fst,'): <stdin>:1:77: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=1006, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso_inv]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=1006, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← Iso.eq_inv_comp, pullback.lift_fst]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.1s, verify 0.1s, in=1006, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [pullback.map, pullbackFstFstIso_inv]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=1006, out=45)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [← cancel_mono f', Category.assoc, pullbackFstFstIso_inv, pullback.lift_fst,
pullback.lift_snd, ← e₁, ← e₂]
```

**lean_error:** tail step 1/2 ("simp only [← cancel_mono f', Category.assoc, pullbackFstFstIso_inv, pullback.lift_fst,"): <stdin>:1:86: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=1030, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [map]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=1030, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso_inv]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=1030, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← Iso.eq_inv_comp, pullback.lift_fst]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=1030, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [pullback.map, pullbackFstFstIso_inv]
```
