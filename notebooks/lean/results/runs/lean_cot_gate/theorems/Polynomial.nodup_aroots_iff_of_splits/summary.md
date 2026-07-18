# Polynomial.nodup_aroots_iff_of_splits   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Separable.lean`  

**Ground-truth tail (from k):**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

**True premises at k:** `Polynomial.nodup_roots_iff_of_splits`, `Polynomial.map_ne_zero`, `Polynomial.separable_map`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✘ ✓ |
| `hint:3` | ✓ ✓ ✘ ✘ |
| `noise:3` | ✓ ✓ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=266, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Multiset.nodup_iff_pairwise, pairwise_map, aroots, pairwise_finset_toMultiset,
  Finset.pairwise_iff_pairwise_coe, pairwise_roots_iff_separable h hf]
```

**lean_error:** tail step 1/2 ('rw [Multiset.nodup_iff_pairwise, pairwise_map, aroots, pairwise_finset_toMultiset,'): <stdin>:1:82: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=266, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← nodup_roots_iff_separable hf h, ← map_id f, roots_map (algebraMap F K) (leadingCoeff_ne_zero hf),
  aroots, Multiset.Nodup]
```

**lean_error:** tail step 1/2 ('rw [← nodup_roots_iff_separable hf h, ← map_id f, roots_map (algebraMap F K) (leadingCoeff_ne_zero hf),'): <stdin>:1:103: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=266, out=52)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Multiset.nodup_iff_count_le_one, count_eq_natDegree_of_splits_id_of_nodup h, sepCount_eq_one_iff,
  forall_iff_forall_root (map_monic_ne_zero hf) h]
```

**lean_error:** tail step 1/2 ('rw [Multiset.nodup_iff_count_le_one, count_eq_natDegree_of_splits_id_of_nodup h, sepCount_eq_one_iff,'): <stdin>:1:101: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=266, out=79)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Separable, separable_def, hf, ← map_map, ← Nodup.coe_toMultiset, ←
  Polynomial.map_monic_map_iff (algebraMap F K) f.ne_zero, ←
  (map_ne_zero (algebraMap F K)).2 hf, h.Nodup_iff_deriv_ne_zero, aroots]
```

**lean_error:** tail step 1/3 ('simp [Separable, separable_def, hf, ← map_map, ← Nodup.coe_toMultiset, ←'): <stdin>:1:72: unexpected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.1s, in=1086, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=1086, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=1086, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Polynomial.nodup_roots_iff_of_splits (map_ne_zero hf) h,
    Polynomial.separable_map]
```

**lean_error:** tail step 1/2 ('rw [Polynomial.nodup_roots_iff_of_splits (map_ne_zero hf) h,'): <stdin>:1:60: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 7.8s, verify 0.1s, in=1086, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.2s, verify 0.1s, in=3423, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 4.9s, verify 0.1s, in=3423, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (nodup_roots_iff_of_splits (map_ne_zero hf) h).trans (separable_map (algebraMap F K))
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 71.6s, verify 0.3s, in=3423, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact nodup_roots_iff_of_splits (map_ne_zero hf) h
```

**lean_error:** tail step 1/1 ('exact nodup_roots_iff_of_splits (map_ne_zero hf) h'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 71.9s, verify 0.2s, in=3423, out=36)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (nodup_roots_iff_of_splits (map_ne_zero hf) h).trans (separable_map (algebraMap F K)).symm
```

**lean_error:** tail step 1/1 ('exact (nodup_roots_iff_of_splits (map_ne_zero hf) h).trans (separable_map (algebraMap F K)).symm'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=3449, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=3449, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=3449, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [algebraMap, separable_map] using (nodup_roots_iff_of_splits (map_ne_zero hf) h).symm
```

**lean_error:** tail step 1/1 ('simpa [algebraMap, separable_map] using (nodup_roots_iff_of_splits (map_ne_zero hf) h).symm'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 7.9s, verify 0.1s, in=3449, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```
