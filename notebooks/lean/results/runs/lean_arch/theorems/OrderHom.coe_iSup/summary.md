# OrderHom.coe_iSup   (k=1, 2 tactics total)

file: `Mathlib/Order/Hom/Order.lean`  

**Ground-truth tail (from k):**
```lean
simp [iSup_apply]
```

**True premises at k:** `OrderHom.iSup_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | · | ✘ | · |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | · | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.3s, in=297, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup_apply]
congr 
ext i
rw [OrderHom.coe_coe]
```

**lean_error:** tail step 3/4 ('ext i'): no applicable extensionality theorem found for

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.2s, in=270, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup_apply]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.4s, verify 0.1s, in=286, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup_apply]
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `hint:2` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 1.2s, verify 0.2s, in=536, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply f x]
rw [iSup]
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=503, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup_apply]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.5s, verify 0.1s, in=525, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup_apply]
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=1097, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply] 
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1055, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=1086, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup_apply]
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 0.9s, verify 0.2s, in=1123, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply]
rw [iSup]
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=1156, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup_apply]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1112, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch
