# Mon_.Mon_tensor_mul_one   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Monoidal/Mon_.lean`  

**Ground-truth tail (from k):**
```lean
exact tensor_right_unitality C M.X N.X
```

**True premises at k:** `CategoryTheory.tensor_right_unitality`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.0s, verify 0.1s, in=448, out=1944)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (right_unitor_tensor (M.X) (N.X))
```

**lean_error:** tail step 1/1 ('simpa using (right_unitor_tensor (M.X) (N.X))'): unknown identifier 'right_unitor_tensor'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 256.4s, verify 0.1s, in=401, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(X ⊗ Y) ⊗ I  --α_{X,Y,I}-->  X ⊗ (Y ⊗ I)
   |                                 |
   ρ_{X⊗Y}                           id_X ⊗ ρ_Y
   V                                 V
   X ⊗ Y    ---------------------->  X ⊗ Y
```

**lean_error:** tail step 1/5 ('(X ⊗ Y) ⊗ I  --α_{X,Y,I}-->  X ⊗ (Y ⊗ I)'): <stdin>:1:2: unknown tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=388, out=511)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Mon_.tensor_mul, tensor_μ]
<|>
  rw [← category.assoc]
  <;> simp [tensor_μ, category.assoc]
  <|>
  rw [← category.assoc]
  <;> simp [tensor_μ, category.assoc]
```

**lean_error:** tail step 1/7 ('simp [Mon_.tensor_mul, tensor_μ]'): unknown constant 'Mon_.tensor_mul'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.4s, in=1072, out=758)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (tensor_right_unitality (M.X) (N.X)).symm
```

**lean_error:** tail step 1/1 ('simpa using (tensor_right_unitality (M.X) (N.X)).symm'): application type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 17.6s, verify 0.1s, in=1064, out=2028)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact tensor_right_unitality M.X N.X
```

**lean_error:** tail step 1/1 ('exact tensor_right_unitality M.X N.X'): application type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 3.4s, in=1006, out=582)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact tensor_right_unitality M.X N.X
```

**lean_error:** tail step 1/1 ('exact tensor_right_unitality M.X N.X'): application type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.0s, verify 0.2s, in=1531, out=865)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [tensor_right_unitality (M.X) (N.X)]
simp
```

**lean_error:** tail step 1/2 ('rw [tensor_right_unitality (M.X) (N.X)]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 24.0s, verify 0.1s, in=1547, out=2865)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact CategoryTheory.tensor_right_unitality M.X N.X
```

**lean_error:** tail step 1/1 ('exact CategoryTheory.tensor_right_unitality M.X N.X'): application type mismatch

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 16.5s, verify 0.2s, in=1455, out=1845)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [tensor_right_unitality M.X N.X]
```

**lean_error:** tail step 1/1 ('rw [tensor_right_unitality M.X N.X]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.7s, verify 0.3s, in=1495, out=793)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (tensor_right_unitality (C:=C) M.X N.X).symm
```

**lean_error:** tail step 1/1 ('simpa using (tensor_right_unitality (C:=C) M.X N.X).symm'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 17.4s, verify 0.1s, in=1610, out=1992)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (tensor_right_unitality M.X N.X).symm
```

**lean_error:** tail step 1/1 ('exact (tensor_right_unitality M.X N.X).symm'): application type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.5s, verify 0.2s, in=1472, out=624)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [tensor_right_unitality M.X N.X]
```

**lean_error:** tail step 1/1 ('rw [tensor_right_unitality M.X N.X]'): tactic 'rewrite' failed, equality or iff proof expected
