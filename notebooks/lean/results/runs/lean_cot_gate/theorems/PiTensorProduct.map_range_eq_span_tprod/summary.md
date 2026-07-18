# PiTensorProduct.map_range_eq_span_tprod   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Set.mem_range, comp_apply, map_tprod, Set.mem_setOf_eq]
```

**True premises at k:** `Set.mem_range`, `Function.comp_apply`, `PiTensorProduct.map_tprod`, `Set.mem_setOf_eq`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✓ ✓ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✘ |
| `hint:3` | ✓ ✘ ✓ ✓ |
| `noise:3` | ✓ ✓ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=617, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.9s, verify 0.1s, in=617, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Function.comp, Set.mem_range]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=617, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Set.mem_range, Set.mem_setOf_eq, Function.comp_apply, mem_range_tprod]
```

**lean_error:** tail step 1/1 ('simp only [Set.mem_range, Set.mem_setOf_eq, Function.comp_apply, mem_range_tprod]'): unknown identifier 'mem_range_tprod'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.9s, verify 0.1s, in=617, out=38)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Set.mem_range, exists_prop, Function.comp_apply, tprod_mem_tprod_range, exists_and_left,
  Classical.and_iff_right_iff_imp]
```

**lean_error:** tail step 1/2 ('simp only [Set.mem_range, exists_prop, Function.comp_apply, tprod_mem_tprod_range, exists_and_left,'): <stdin>:1:99: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=1248, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=1248, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Set.mem_range, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=1248, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Function.comp, Set.mem_setOf_eq, Set.mem_range, PiTensorProduct.map_tprod]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.6s, verify 0.1s, in=1248, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, mem_setOf_eq, map_tprod]
```

**lean_error:** tail step 1/1 ('simp only [Set.mem_range, Function.comp_apply, mem_setOf_eq, map_tprod]'): unknown identifier 'mem_setOf_eq'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.7s, verify 0.1s, in=1462, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Function.comp_apply, PiTensorProduct.map_tprod]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=1462, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Function.comp_apply, exists_prop, Set.mem_range, Set.mem_setOf_eq,
  PiTensorProduct.map_tprod]
```

**lean_error:** tail step 1/2 ('simp only [Function.comp_apply, exists_prop, Set.mem_range, Set.mem_setOf_eq,'): <stdin>:1:77: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 5.4s, verify 0.1s, in=1462, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Set.mem_range, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 5.5s, verify 0.1s, in=1462, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, Set.mem_setOf_eq, PiTensorProduct.map_tprod]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=1487, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Set.mem_range, Set.mem_setOf_eq]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.4s, verify 0.1s, in=1487, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Function.comp, Set.mem_setOf_eq, Set.mem_range, PiTensorProduct.map_tprod]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=1487, out=33)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, exists_prop, PiTensorProduct.map_tprod,
  Set.mem_setOf_eq]
```

**lean_error:** tail step 1/2 ('simp only [Set.mem_range, Function.comp_apply, exists_prop, PiTensorProduct.map_tprod,'): <stdin>:1:86: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=1487, out=33)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Function.comp_apply, exists_prop, Set.mem_range, Set.mem_setOf_eq,
  PiTensorProduct.map_tprod]
```

**lean_error:** tail step 1/2 ('simp only [Function.comp_apply, exists_prop, Set.mem_range, Set.mem_setOf_eq,'): <stdin>:1:77: unexpected end of input; expected ']'
