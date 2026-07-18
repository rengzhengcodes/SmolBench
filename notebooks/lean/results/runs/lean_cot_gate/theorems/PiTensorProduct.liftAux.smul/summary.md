# PiTensorProduct.liftAux.smul   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, (liftAux φ).map_add, smul_add]
```

**True premises at k:** `smul_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `smul_add`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✓ ✓ ✓ ✓ |
| `hint:2` | ✘ ✘ · · |
| `hint:3` | ✓ ✘ ✘ · |
| `noise:3` | ✘ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.8s, verify 0.3s, in=476, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [smul_add, ihz, ihy]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=476, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [smul_add, ihz, ihy]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.1s, in=476, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ihz, ihy, add_smul]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=476, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [smul_add, ihz, ihy]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=1583, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [smul_add, liftAux.map_add, smul_add]
```

**lean_error:** tail step 1/1 ('simp_rw [smul_add, liftAux.map_add, smul_add]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.1s, in=1583, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [smul_add, ihz, ihy, ← liftAux φ].map_add]
```

**lean_error:** tail step 1/1 ('simp [smul_add, ihz, ihy, ← liftAux φ].map_add]'): <stdin>:1:38: expected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.0s, verify 0.3s, in=1583, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [smul_add, ihz, ihy, AddMonoidHom.map_add, PiTensorProduct.liftAux]
```

**final state (truncated):**
```
case refine'_2
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝⁷ : CommSemiring R
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.4s, verify 0.3s, in=1583, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [smul_add, PiTensorProduct.liftAux, ihz, ihy, AddMonoidHom.map_add, AddMonoidHom.map_add]
```

**final state (truncated):**
```
case refine'_2
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝⁷ : CommSemiring R
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.7s, verify 0.1s, in=2615, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ihz, ihy, smul_add]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=2615, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [smul_add, ihz, ihy, liftAux.map_add]
```

**lean_error:** tail step 1/1 ('simp [smul_add, ihz, ihy, liftAux.map_add]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.9s, verify 0.1s, in=2615, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ihz, ihy, smul_add, ← liftAux.map_add φ]
```

**lean_error:** tail step 1/1 ('simp [ihz, ihy, smul_add, ← liftAux.map_add φ]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 3.0s, verify 0.2s, in=2615, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [smul_add, PiTensorProduct.liftAux, ihz, ihy, AddMonoidHom.map_add, AddMonoidHom.map_add]
```

**final state (truncated):**
```
case refine'_2
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝⁷ : CommSemiring R
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=2643, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [smul_add, ihz, ihy, ← liftAux φ].map_add
```

**lean_error:** tail step 1/1 ('simp [smul_add, ihz, ihy, ← liftAux φ].map_add'): <stdin>:1:38: expected end of input

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=2643, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [smul_add, PiTensorProduct.liftAux.map_add, ihz, ihy]
```

**lean_error:** tail step 1/1 ('simp [smul_add, PiTensorProduct.liftAux.map_add, ihz, ihy]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.8s, verify 0.1s, in=2643, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [smul_add, ihz, ihy, (liftAux φ).map_add]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.3s, verify 0.1s, in=2643, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [smul_add, liftAux.map_add, ← ihz, ← ihy, ← AddMonoidHom.map_add, smul_add]
```

**lean_error:** tail step 1/1 ('simp_rw [smul_add, liftAux.map_add, ← ihz, ← ihy, ← AddMonoidHom.map_add, smul_add]'): invalid field notation, type is not of the form (C ...) where C is a constant
