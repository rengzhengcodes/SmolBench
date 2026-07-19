# PiTensorProduct.liftAux.smul   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, (liftAux φ).map_add, smul_add]
```

**True premises at k:** `smul_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `smul_add`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ |
| `hint:2` | ✓ ✓ ✘ ✓ | ✘ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.4s, verify 0.2s, in=502, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [TensorProduct.smul_add, map_add, ihz, ihy, smul_add]
```

**lean_error:** tail step 1/1 ('rw [TensorProduct.smul_add, map_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.5s, in=502, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [TensorProduct.smul_add, map_add, ihz, ihy, map_smul] 
rw [map_smul]
```

**lean_error:** tail step 1/2 ('rw [TensorProduct.smul_add, map_add, ihz, ihy, map_smul]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 3.2s, verify 0.2s, in=502, out=46)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [TensorProduct.smul_add, map_add, ihz, ihy, smul_add]
rw [TensorProduct.smul_add, map_add, ihz, ihy] at ihz 
exact ihz
```

**lean_error:** tail step 1/3 ('rw [TensorProduct.smul_add, map_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 3.4s, verify 0.1s, in=502, out=51)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [TensorProduct.smul_add, map_add, ihz, ihy, smul_add],
rw [TensorProduct.smul_add, map_add, ihz, ihy, smul_add] at ihz,
exact ihz,
```

**lean_error:** tail step 1/3 ('rw [TensorProduct.smul_add, map_add, ihz, ihy, smul_add],'): <stdin>:1:56: expected end of input

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.5s, verify 0.3s, in=502, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [smul_add, (liftAux φ).map_add, ihz, ihy, smul_add]
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 2.0s, verify 0.2s, in=502, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [smul_add, (liftAux φ).map_add, ihz, ihy, smul_add]
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 2.4s, verify 0.2s, in=502, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [smul_add, (liftAux φ).map_add, ihz, ihy, ←smul_add]
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 2.5s, verify 0.2s, in=502, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [smul_add, (liftAux φ).map_add, ihz, ihy, ←smul_add]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.4s, in=1615, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, map_add, map_add, smul_add]
rw [ihz, ihy]
```

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 1.7s, verify 0.3s, in=1615, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, map_add, map_add, smul_add]
rw [ihz, ihy]
```

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.5s, verify 0.3s, in=1615, out=38)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add (liftAux φ), AddMonoidHom.map_add (liftAux φ), smul_add]
exact add_comm _ _
```

**lean_error:** tail step 2/2 ('exact add_comm _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 2.8s, verify 0.4s, in=1615, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add r z y, map_add (liftAux φ), map_add (liftAux φ)]
rw [ihz, ihy, smul_add]
done
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=1615, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, liftAux_add, ihz, ihy, smul_add]
```

**lean_error:** tail step 1/1 ('rw [smul_add, liftAux_add, ihz, ihy, smul_add]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 2.2s, verify 0.2s, in=1615, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [smul_add, (liftAux φ).map_add, smul_add, ihz, ihy]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 2.7s, verify 0.1s, in=1615, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, AddMonoidHom.map_add, AddMonoidHom.map_add, smul_add, ihz, ihy]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 2.8s, verify 0.1s, in=1615, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, (liftAux φ).map_add, (liftAux φ).map_add, ihz, ihy, smul_add]
```
