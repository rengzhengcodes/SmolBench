# Polynomial.nodup_aroots_iff_of_splits   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Separable.lean`  

**Ground-truth tail (from k):**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

**True premises at k:** `Polynomial.nodup_roots_iff_of_splits`, `Polynomial.map_ne_zero`, `Polynomial.separable_map`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=293, out=77)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [separable_def', Multiset.nodup_iff_ne]
exact ⟨λ H, fun _ h1 _ h2 => H (algebraMap F K) h h1 h2,
  λ H, fun _ _ h1 h2 => irreducible_of_separable _ hf (h _ h1) (H _ h1 _ h2)⟩
```

**lean_error:** tail step 1/3 ("rw [separable_def', Multiset.nodup_iff_ne]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=264, out=153)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Multiset.Nodup, Separable, ← derivative_map, ← eval_derivative_map]
rw [← Multiset.pairwise_zero, aroots, Multiset.map_map]
rw [← Multiset.pairwise_zero, Multiset.map_pairwise_of_injective (algebraMap F K).injective]
rw [h, Multiset.pairwise_zero_iff_count]
simp only [count_map, RingHom.coe_id, count_roots]
exact ⟨fun h x hx0 hx => h x (by rwa [Ne.def, ← map_eq_zero] at hx0) hx,
  fun h x hx0 hx => h (algebraMap F K x) (by rwa [map_eq_zero]) hx⟩
```

**lean_error:** tail step 1/7 ('rw [Multiset.Nodup, Separable, ← derivative_map, ← eval_derivative_map]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 63.7s, verify 0.1s, in=282, out=3743)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split_iff
intro h_nodup
rw [separable, polynomial.separable_map]
rw [polynomial.separable_iff_nodup_roots h]
exact h_nodup
intro h_sep
rw [separable, polynomial.separable_map] at h_sep
rw [polynomial.separable_iff_nodup_roots h] at h_sep
exact h_sep
```

**lean_error:** tail step 1/9 ('split_iff'): <stdin>:1:1: unknown tactic

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 4.0s, in=1113, out=55)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [aroots_def' hf, roots_map (algebraMap F K) hf]
erw [map_ne_zero (algebraMap F K) hf] at h
rw [nodup_roots_iff_of_splits hf h, separable_map]
```

**lean_error:** tail step 1/3 ("rw [aroots_def' hf, roots_map (algebraMap F K) hf]"): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1068, out=68)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Multiset.nodup_iff_count_le_one, aroots_def f K, ← Multiset.map_count, ← Multiset.Nodup, ← roots_map (map_ne_zero hf)]
rw [separable_map (algebraMap F K)]
exact nodup_roots_iff_of_splits (map_ne_zero hf) h
```

**lean_error:** tail step 1/3 ('rw [Multiset.nodup_iff_count_le_one, aroots_def f K, ← Multiset.map_count, ← Multiset.Nodup, ← roots_map (map_ne_zero hf)]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 542.0s, verify 0.1s, in=1102, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, ← splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
 rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
rw [← (algebraMap F K).id_comp, splits
```

**lean_error:** tail step 1/1695 ('rw [← map_ne_zero (algebraMap F K) hf] at h'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=3446, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [aroots_def, nodup_roots_iff_of_splits hf h]
rw [separable_map, map_ne_zero hf]
```

**lean_error:** tail step 1/2 ('rw [aroots_def, nodup_roots_iff_of_splits hf h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=3373, out=61)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [aroots, Multiset.map_id', ← Polynomial.roots_map (algebraMap F K) f]
rw [Polynomial.map_ne_zero hf, nodup_roots_iff_of_splits (Polynomial.map_ne_zero hf) h]
rw [Polynomial.separable_map (algebraMap F K)]
```

**lean_error:** tail step 1/3 ("rw [aroots, Multiset.map_id', ← Polynomial.roots_map (algebraMap F K) f]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=3435, out=72)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← map_ne_zero (algebraMap F K) hf] at h
rw [← (algebraMap F K).id_comp, splits_map_iff] at h
exact_mod_cast (nodup_roots_iff_of_splits (map_ne_zero (algebraMap F K) hf) h).symm
```

**lean_error:** tail step 1/3 ('rw [← map_ne_zero (algebraMap F K) hf] at h'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=3473, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [aroots_def, nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=3696, out=46)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [aroots_def, Multiset.nodup_iff_count_le_one, ← roots_map (map_ne_zero hf), ← separable_map]
exact nodup_roots_iff_of_splits (map_ne_zero hf) h
```

**lean_error:** tail step 1/2 ('rw [aroots_def, Multiset.nodup_iff_count_le_one, ← roots_map (map_ne_zero hf), ← separable_map]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=3462, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [aroots, map_ne_zero hf, nodup_roots_iff_of_splits, separable_map, separable_map]
exact h
```

**lean_error:** tail step 1/2 ('rw [aroots, map_ne_zero hf, nodup_roots_iff_of_splits, separable_map, separable_map]'): tactic 'rewrite' failed, equality or iff proof expected
