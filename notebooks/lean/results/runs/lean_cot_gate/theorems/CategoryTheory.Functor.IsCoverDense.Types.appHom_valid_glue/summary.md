# CategoryTheory.Functor.IsCoverDense.Types.appHom_valid_glue   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Sites/DenseSubsite.lean`  

**Ground-truth tail (from k):**
```lean
apply appHom_restrict
```

**True premises at k:** `CategoryTheory.Functor.IsCoverDense.Types.appHom_restrict`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✓ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✓ ✘ |
| `hint:3` | ✘ ✓ ✘ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=465, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=465, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (α.naturality f).symm
```

**lean_error:** tail step 1/1 ('exact (α.naturality f).symm'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=465, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Functor.op_map, Category.assoc, ← α.naturality]
```

**lean_error:** tail step 1/1 ('simp only [Functor.op_map, Category.assoc, ← α.naturality]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=465, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact whiskerLeft_eq_appHom G.op ℱ ℱ'.val α f a✝
```

**lean_error:** tail step 1/1 ("exact whiskerLeft_eq_appHom G.op ℱ ℱ'.val α f a✝"): <stdin>:1:47: expected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=804, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=804, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact appHom_restrict f a✝
```

**lean_error:** tail step 1/1 ('exact appHom_restrict f a✝'): <stdin>:1:25: expected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=804, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [appHom_restrict]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=804, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact appHom_restrict f a✝
```

**lean_error:** tail step 1/1 ('exact appHom_restrict f a✝'): <stdin>:1:25: expected end of input

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.2s, in=2044, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact appHom_restrict f _
```

**lean_error:** tail step 1/1 ('exact appHom_restrict f _'): stuck at solving universe constraint

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=2044, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.2s, in=2044, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact appHom_restrict f _
```

**lean_error:** tail step 1/1 ('exact appHom_restrict f _'): stuck at solving universe constraint

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 70.9s, verify 0.1s, in=2044, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [appHom_restrict]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.6s, verify 0.1s, in=2074, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=2074, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=2074, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [appHom_restrict]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.1s, verify 0.1s, in=2074, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [appHom_restrict]
```
