# OrderHom.coe_iSup   (k=1, 2 tactics total)

file: `Mathlib/Order/Hom/Order.lean`  

**Ground-truth tail (from k):**
```lean
simp [iSup_apply]
```

**True premises at k:** `OrderHom.iSup_apply`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | · ✘ ✓ ✓ |
| `hint:2` | · ✘ ✘ ✓ |
| `hint:3` | · ✘ ✓ ✘ |
| `noise:3` | · ✘ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=270, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=270, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=270, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=270, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=509, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
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

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=509, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=509, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=509, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.7s, verify 0.3s, in=1072, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
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

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=1072, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.1s, verify 0.1s, in=1072, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=1072, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.8s, verify 0.1s, in=1099, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
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

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=1099, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.4s, verify 0.1s, in=1099, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=1099, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [iSup_apply]
```
