# PiTensorProduct.liftAux.smul   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, (liftAux φ).map_add, smul_add]
```

**True premises at k:** `smul_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `smul_add`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ | ✘ ✘ · ✘ |
| `hint:2` | ✘ ✘ · ✘ | ✘ ✘ · · | ✘ ✘ · ✓ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✓ ✘ ✘ · | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✓ ✘ | ✘ ✓ · ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 72.3s, verify 0.7s, in=476, out=2640)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [smul_add]
rw [(liftAux φ).map_add]
rw [ihz, ihy]
rw [add_smul]
rw [← (liftAux φ).map_add]
```

**lean_error:** tail step 4/5 ('rw [add_smul]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 87.2s, verify 0.1s, in=476, out=3228)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw smul_add,
rw (liftAux φ).map_add,
rw [ihz, ihy],
rw add_smul,
rw (liftAux φ).map_add,
```

**lean_error:** tail step 1/5 ('rw smul_add,'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 142.0s, verify 0.4s, in=476, out=5413)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [smul_add]
rw [LinearMap.map_add]
rw [ihz, ihy]
rw [← smul_add]
rw [LinearMap.map_add]
```

**lean_error:** tail step 2/5 ('rw [LinearMap.map_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 144.7s, verify 0.3s, in=476, out=5530)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [smul_add]
rw [liftAux_add]
rw [ihz, ihy]
rw [← smul_add]
rw [← liftAux_add φ z y]
```

**lean_error:** tail step 2/5 ('rw [liftAux_add]'): tactic 'rewrite' failed, equality or iff proof expected

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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.6s, verify 0.2s, in=476, out=261)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [smul_add, map_add, ihz, ihy, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, map_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.0s, verify 0.2s, in=476, out=266)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [smul_add, liftAux_add, ihz, ihy, ← smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, liftAux_add, ihz, ihy, ← smul_add]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 11.9s, verify 0.2s, in=476, out=316)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [smul_add, ihz, ihy]
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 15.4s, verify 0.1s, in=476, out=435)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [smul_add, liftAux φ (r • z), liftAux φ (r • y), ihz, ihy]
```

**lean_error:** tail step 1/1 ('simp only [smul_add, liftAux φ (r • z), liftAux φ (r • y), ihz, ihy]'): invalid 'simp', proposition expected

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 10.0s, verify 0.2s, in=1583, out=347)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, ihz, ihy, ← AddMonoidHom.map_add, ← smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, AddMonoidHom.map_add, ihz, ihy, ← AddMonoidHom.map_add, ← smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 15.2s, verify 0.2s, in=1583, out=533)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AddMonoidHom.map_add, smul_add, ihz, ihy, AddMonoidHom.map_add]
```

**lean_error:** tail step 1/1 ('rw [AddMonoidHom.map_add, smul_add, ihz, ihy, AddMonoidHom.map_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 137.4s, verify 0.2s, in=1583, out=5220)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, ihz, ihy, ← smul_add]
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

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 216.7s, verify 0.2s, in=1583, out=8796)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, liftAux.map_add, ihz, ihy, liftAux.map_add, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, liftAux.map_add, ihz, ihy, liftAux.map_add, smul_add]'): tactic 'rewrite' failed, equality or iff proof expected

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

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.9s, verify 0.1s, in=1583, out=352)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux,
  AddMonoidHom.map_add, smul_add]
```

**lean_error:** tail step 1/2 ('rw [smul_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux,'): <stdin>:1:85: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.8s, verify 0.1s, in=1583, out=383)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, smul_add]'): failed to rewrite using equation theorems for 'PiTensorProduct.liftAux'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 14.2s, verify 0.2s, in=1583, out=394)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [smul_add, liftAux, AddMonoidHom.map_add, ihz, ihy]
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

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 14.5s, verify 0.1s, in=1583, out=401)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, ihz, ihy, AddMonoidHom.map_add, smul_add]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 73.0s, verify 0.2s, in=2615, out=2091)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 77.8s, verify 0.2s, in=2615, out=1211)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add, AddMonoidHom.map_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add, AddMonoidHom.map_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 88.3s, verify 0.7s, in=2615, out=2920)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add]
rw [AddMonoidHom.map_add]
rw [ihz, ihy]
rw [smul_add]
rw [← AddMonoidHom.map_add]
```

**lean_error:** tail step 4/5 ('rw [smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 167.8s, verify 0.7s, in=2615, out=4802)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add, ← AddMonoidHom.map_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add, ← AddMonoidHom.map_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

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

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 22.5s, verify 0.3s, in=2615, out=409)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, PiTensorProduct.liftAux, ihz, ihy, smul_add, AddMonoidHom.map_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, AddMonoidHom.map_add, PiTensorProduct.liftAux, ihz, ihy, smul_add, AddMonoidHom.map_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 23.1s, verify 0.1s, in=2615, out=427)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux,
  AddMonoidHom.map_add, ihz, ihy, smul_add]
```

**lean_error:** tail step 1/2 ('rw [smul_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux,'): <stdin>:1:85: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 23.2s, verify 0.2s, in=2615, out=384)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [liftAux.map_add, smul_add, ihz, ihy, liftAux.map_add, smul_add]
```

**lean_error:** tail step 1/1 ('rw [liftAux.map_add, smul_add, ihz, ihy, liftAux.map_add, smul_add]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 23.7s, verify 0.1s, in=2615, out=395)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, smul_add]
```

**lean_error:** tail step 1/1 ('rw [PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, smul_add]'): failed to rewrite using equation theorems for 'PiTensorProduct.liftAux'

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 45.0s, verify 0.7s, in=2643, out=1622)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add]
rw [AddMonoidHom.map_add]
rw [ihz, ihy]
rw [smul_add]
rw [AddMonoidHom.map_add]
```

**lean_error:** tail step 4/5 ('rw [smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 51.1s, verify 0.2s, in=2643, out=1852)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, PiTensorProduct.liftAux.map_add, ihz, ihy, smul_add, ← PiTensorProduct.liftAux.map_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, PiTensorProduct.liftAux.map_add, ihz, ihy, smul_add, ← PiTensorProduct.liftAux.map_add]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 119.5s, verify 0.2s, in=2643, out=4482)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add, ← AddMonoidHom.map_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add, ← AddMonoidHom.map_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 138.4s, verify 0.1s, in=2643, out=5264)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw smul_add
rw [AddMonoidHom.map_add (liftAux φ)]
rw [ihz, ihy]
rw ← smul_add
```

**lean_error:** tail step 1/4 ('rw smul_add'): <stdin>:1:3: expected '['

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

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 11.5s, verify 0.2s, in=2643, out=313)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, AddMonoidHom.map_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 11.7s, verify 0.1s, in=2643, out=315)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, AddMonoidHom.map_add, ihz, ihy, ← smul_add]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 13.0s, verify 0.2s, in=2643, out=354)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [PiTensorProduct.liftAux, AddMonoidHom.map_add, smul_add]
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

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 18.5s, verify 0.1s, in=2643, out=534)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux,
  AddMonoidHom.map_add, smul_add]
```

**lean_error:** tail step 1/2 ('rw [smul_add, PiTensorProduct.liftAux, AddMonoidHom.map_add, PiTensorProduct.liftAux,'): <stdin>:1:85: unexpected end of input; expected ']'
