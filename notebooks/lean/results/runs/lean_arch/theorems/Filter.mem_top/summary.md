# Filter.mem_top   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [mem_top_iff_forall, eq_univ_iff_forall]
```

**True premises at k:** `Filter.mem_top_iff_forall`, `Set.eq_univ_iff_forall`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=254, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mem_top_iff, subset_univ_iff]
```

**lean_error:** tail step 1/1 ('rw [mem_top_iff, subset_univ_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=226, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mem_top, ← univ_subset_iff]
aesop
```

**lean_error:** tail step 1/2 ('rw [mem_top, ← univ_subset_iff]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=243, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [mem_top_sets, univ]
```

**lean_error:** tail step 1/1 ('simp [mem_top_sets, univ]'): unknown identifier 'mem_top_sets'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=575, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_top_iff_forall, eq_univ_iff_forall] 
exact Iff.rfl
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=544, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_top_iff_forall]
rw [eq_univ_iff_forall]
exact Iff.rfl
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=564, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_top_iff_forall, eq_univ_iff_forall]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=1091, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mem_top_iff_forall, eq_univ_iff_forall]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=1061, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mem_top_iff_forall, eq_univ_iff_forall]
simp only [iff_self_iff]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1080, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mem_top_iff_forall, eq_univ_iff_forall]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1115, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mem_top_iff_forall, eq_univ_iff_forall]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.3s, in=1143, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mem_top_iff_forall]
rw [eq_univ_iff_forall]
exact Iff.rfl
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1104, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mem_top_iff_forall, eq_univ_iff_forall]
```
