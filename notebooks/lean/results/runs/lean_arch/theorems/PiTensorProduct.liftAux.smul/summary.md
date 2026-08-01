# PiTensorProduct.liftAux.smul   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, (liftAux φ).map_add, smul_add]
```

**True premises at k:** `smul_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `smul_add`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.2s, in=502, out=43)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [TensorProduct.smul_add, map_add, ihz, ihy, smul_add]
rw [smul_add] at ihz 
rw [smul_add] at ihy 
done
```

**lean_error:** tail step 1/4 ('rw [TensorProduct.smul_add, map_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=473, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, (liftAux φ).map_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=491, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Finsupp.smul_add, liftAux_add, ihz, ihy, φ.map_smul, add_smul]
```

**lean_error:** tail step 1/1 ('rw [Finsupp.smul_add, liftAux_add, ihz, ihy, φ.map_smul, add_smul]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.5s, verify 0.5s, in=1615, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, map_add, map_add, smul_add]
rw [ihz, ihy]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1591, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, ihz, ihy, smul_add]
```
```

**lean_error:** tail step 1/2 ('rw [smul_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=1604, out=49)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, liftAux_tprodCoeff, liftAux_tprodCoeff, smul_add, AddMonoidHom.map_add, AddMonoidHom.map_add]
rw [ihz, ihy]
```

**lean_error:** tail step 1/2 ('rw [smul_add, liftAux_tprodCoeff, liftAux_tprodCoeff, smul_add, AddMonoidHom.map_add, AddMonoidHom.map_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=2640, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add, PiTensorProduct.liftAux.map_add, ihz, ihy, PiTensorProduct.liftAux.map_add, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, PiTensorProduct.liftAux.map_add, ihz, ihy, PiTensorProduct.liftAux.map_add, smul_add]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=2609, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add, ihz, ihy, smul_add]
simp only [map_add]
```

**lean_error:** tail step 1/2 ('rw [smul_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=2629, out=47)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add, liftAux_tprodCoeff, liftAux_tprodCoeff, ihz, ihy, AddMonoidHom.map_add, AddMonoidHom.map_add, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, liftAux_tprodCoeff, liftAux_tprodCoeff, ihz, ihy, AddMonoidHom.map_add, AddMonoidHom.map_add, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.9s, verify 0.2s, in=2672, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, map_add, map_add, ihz, ihy, smul_add]
done
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.3s, in=2768, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, ihz, ihy, smul_add]
```
```

**lean_error:** tail step 1/2 ('rw [smul_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=2661, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, liftAux_map_add, ihz, ihy, AddMonoidHom.map_add, AddMonoidHom.map_add, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, liftAux_map_add, ihz, ihy, AddMonoidHom.map_add, AddMonoidHom.map_add, smul_add]'): tactic 'rewrite' failed, equality or iff proof expected
