# PiTensorProduct.liftAux.smul   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, (liftAux φ).map_add, smul_add]
```

**True premises at k:** `smul_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `smul_add`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✓ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.5s, verify 0.1s, in=547, out=1756)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [smul_add, map_add, ihz, ihy]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.3s, verify 0.1s, in=1707, out=1735)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, (liftAux φ).map_add, smul_add]
  rfl
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.1s, verify 0.2s, in=2798, out=1697)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [smul_add, AddMonoidHom.map_add, ihz, ihy]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 15.4s, verify 0.1s, in=2669, out=2943)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, map_add, ihz, ihy, map_add, smul_add]
  rfl
```
