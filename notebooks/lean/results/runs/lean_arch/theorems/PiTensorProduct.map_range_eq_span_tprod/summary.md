# PiTensorProduct.map_range_eq_span_tprod   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Set.mem_range, comp_apply, map_tprod, Set.mem_setOf_eq]
```

**True premises at k:** `Set.mem_range`, `Function.comp_apply`, `PiTensorProduct.map_tprod`, `Set.mem_setOf_eq`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.8s, in=639, out=36)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  rintro ⟨_, m, rfl⟩
  exact ⟨m, rfl⟩
rintro ⟨m, rfl⟩
exact ⟨_, m, rfl⟩
```

**lean_error:** tail step 3/5 ('exact ⟨m, rfl⟩'): unknown identifier 'm'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 2.4s, in=605, out=80)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Set.mem_range, Set.mem_setOf_eq]
constructor
intro h
rcases h with ⟨y, rfl⟩
use fun i => (f i) (tprod R y i)
rw [← tprod_tprod R f y, map_tprod]
use fun i => tprod R y i
rw [tprod_tprod, map_tprod]
```

**lean_error:** tail step 5/8 ('use fun i => (f i) (tprod R y i)'): function expected at

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=628, out=336)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply set.ext_iff
simp only [set.mem_range, set.mem_set_of_eq]
```

**lean_error:** tail step 1/2 ('apply set.ext_iff'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=1268, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod]
rw [Set.mem_setOf_eq]
```

**lean_error:** tail step 1/2 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1228, out=44)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
simp only [mem_tprod, exists_congr, heq_eq_eq, eq_comm]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 10.2s, verify 0.2s, in=1257, out=597)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.4s, in=1479, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod]
rw [Set.mem_setOf_eq]
```

**lean_error:** tail step 1/2 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1437, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
simp only [mem_tprod, exists_exists_and_eq_and]
rfl
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 8.3s, verify 0.2s, in=1468, out=482)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=1504, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod]
rw [Set.mem_setOf_eq]
```

**lean_error:** tail step 1/2 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=1488, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
simp only [mem_tprod, exists_eq']
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1493, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Iff.rfl
```

**lean_error:** tail step 1/1 ('exact Iff.rfl'): type mismatch
