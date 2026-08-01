# LinearMap.span_inl_union_inr   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [span_union, prod_eq_sup_map, ← span_image, ← span_image]
```

**True premises at k:** `Submodule.span_union`, `LinearMap.prod_eq_sup_map`, `Submodule.span_image`, `Submodule.span_image`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.1s, in=466, out=145)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm,
  apply Submodule.span_le.mpr,
  rintro _ ⟨x | x, hx, rfl⟩,
  exacts [(Submodule.prod_le_iff.mp (by apply Submodule.span_mono) _ hx).1, (Submodule.prod_le_iff.mp (by apply Submodule.span_mono) _ hx).2],
apply Submodule.span_le.mpr,
rintro ⟨x, y⟩ hxy,
exact Submodule.add_mem _ (Submodule.span_mono _ _ (by apply Submodule.prod_le_iff.mpr; exact hxy).1) (Submodule.span_mono _ _ (by apply Submodule.prod_le_iff.mpr; exact hxy).2)
```

**lean_error:** tail step 1/7 ('apply le_antisymm,'): <stdin>:1:17: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.2s, in=432, out=70)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, ← Submodule.map_inl_eq_map, ← Submodule.map_inr_eq_map, Submodule.map_sup, Submodule.prod_eq_map, inl_map_subtype.span_eq_sup_map]
simp [← Submodule.map_inl_eq_map, ← Submodule.map_inr_eq_map]
```

**lean_error:** tail step 1/2 ('rw [span_union, span_image, span_image, ← Submodule.map_inl_eq_map, ← Submodule.map_inr_eq_map, Submodule.map_sup, Submodule.prod_eq_map, inl_map_subtype.span_eq_sup_map]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.4s, in=455, out=172)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
. constructor
  . intro x hx
    rw [mem_span_finite] at hx
    rcases hx with ⟨-, h⟩
    refine Submodule.prod.mem _ _ _ h
  . intro x hx
    rw [mem_span_finite] at hx
    rcases hx with ⟨-, h⟩
    refine Submodule.prod.mem _ _ _ h
. apply subset_span
  . rintro _ (h | h) <;> [exact inl_mem h, exact inr_mem h]
. apply span_le
  . rintro _ (h | h) <;> [exact prod.fst (span R s) (span R t) h, exact prod.snd (span R s) (span R t) h]
```

**lean_error:** tail step 2/14 ('. constructor'): tactic 'constructor' failed, target is not an inductive datatype

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.4s, in=1114, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union]
rw [span_image (LinearMap.inl R M M₂), span_image (LinearMap.inr R M M₂)]
exact prod_eq_sup_map _ _
```

**lean_error:** tail step 3/3 ('exact prod_eq_sup_map _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.8s, in=1067, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 14.7s, verify 0.1s, in=1103, out=873)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union],
rw [span_image, span_image],
rw [prod_eq_sup_map]
```

**lean_error:** tail step 1/3 ('rw [span_union],'): <stdin>:1:15: expected end of input

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.5s, in=1891, out=49)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union]
rw [span_image (LinearMap.inl R M M₂), span_image (LinearMap.inr R M M₂)]
exact LinearMap.prod_eq_sup_map (span R s) (span R t)
```

**lean_error:** tail step 3/3 ('exact LinearMap.prod_eq_sup_map (span R s) (span R t)'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.4s, verify 0.9s, in=1842, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 11.1s, verify 0.4s, in=1880, out=654)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union]
rw [span_image, span_image]
rw [← prod_eq_sup_map]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.5s, in=1917, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union]
rw [span_image (LinearMap.inl R M M₂), span_image (LinearMap.inr R M M₂)]
exact LinearMap.prod_eq_sup_map (span R s) (span R t)
```

**lean_error:** tail step 3/3 ('exact LinearMap.prod_eq_sup_map (span R s) (span R t)'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 2.4s, verify 0.1s, in=1958, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 8.5s, verify 0.2s, in=1906, out=492)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map, Submodule.prod_span]
```

**lean_error:** tail step 1/1 ('rw [span_union, span_image, span_image, prod_eq_sup_map, Submodule.prod_span]'): tactic 'rewrite' failed, equality or iff proof expected
