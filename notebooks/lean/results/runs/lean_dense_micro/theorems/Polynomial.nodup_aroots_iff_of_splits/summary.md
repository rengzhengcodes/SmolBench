# Polynomial.nodup_aroots_iff_of_splits   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Separable.lean`  

**Ground-truth tail (from k):**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

**True premises at k:** `Polynomial.nodup_roots_iff_of_splits`, `Polynomial.map_ne_zero`, `Polynomial.separable_map`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=293, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [separable_iff_roots_nodup hf, roots_nodup_iff_aroots_nodup hf] 
exact h 
done
```

**lean_error:** tail step 1/3 ('rw [separable_iff_roots_nodup hf, roots_nodup_iff_aroots_nodup hf]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=293, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [separable_iff_roots_nodup hf, aroots_def, Multiset.nodup_map_iff]
exact (algebraMap F K).injective
```

**lean_error:** tail step 1/2 ('rw [separable_iff_roots_nodup hf, aroots_def, Multiset.nodup_map_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=293, out=43)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [separable_iff_roots_nodup hf, aroots_def, Multiset.nodup_iff_nodup]
exact h.split_roots_nodup_iff_roots_nodup.symm
```

**lean_error:** tail step 1/2 ('rw [separable_iff_roots_nodup hf, aroots_def, Multiset.nodup_iff_nodup]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=293, out=77)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [separable_def', Multiset.Nodup, ← Multiset.count_le_one_iff]
constructor
· intro h
  rw [separable_def'] at *
  intro x
  have := h x
  rw [Multiset.count_le_one_iff] at this
  exact this
· intro h x
  have := h x
  exact this
```

**lean_error:** tail step 1/11 ("rw [separable_def', Multiset.Nodup, ← Multiset.count_le_one_iff]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=293, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [separable_iff_roots_nodup hf, ← aroots_def h]
```

**lean_error:** tail step 1/1 ('rw [separable_iff_roots_nodup hf, ← aroots_def h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=293, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [separable_iff_roots_nodup hf, ← aroots_def' h]
```

**lean_error:** tail step 1/1 ("rw [separable_iff_roots_nodup hf, ← aroots_def' h]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=293, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [separable_iff_roots_nodup hf, ← aroots_def f hf h]
```

**lean_error:** tail step 1/1 ('rw [separable_iff_roots_nodup hf, ← aroots_def f hf h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=293, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [separable_iff, ← aroots_map, Multiset.Nodup.nodup_iff_nodup_map]
```

**lean_error:** tail step 1/1 ('rw [separable_iff, ← aroots_map, Multiset.Nodup.nodup_iff_nodup_map]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=1113, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [aroots, map_ne_zero hf]
rw [separable_map (algebraMap F K)]
exact nodup_roots_iff_of_splits hf h
```

**lean_error:** tail step 1/3 ('rw [aroots, map_ne_zero hf]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1113, out=46)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [aroots_def' hf, roots_map (algebraMap F K) hf]
erw [Polynomial.nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

**lean_error:** tail step 1/2 ("rw [aroots_def' hf, roots_map (algebraMap F K) hf]"): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=1113, out=50)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [separable_map (algebraMap F K)]
rw [Multiset.nodup_iff_count_le_one]
rw [aroots]
rw [map_ne_zero hf]
rw [nodup_roots_iff_of_splits hf h]
```

**lean_error:** tail step 1/5 ('rw [separable_map (algebraMap F K)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.9s, verify 0.1s, in=1113, out=55)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_ne_zero (algebraMap F K) hf] at h
convert nodup_roots_iff_of_splits (map (algebraMap F K) f) _ h using 1
· exact separable_map (algebraMap F K)
```

**lean_error:** tail step 1/3 ('rw [map_ne_zero (algebraMap F K) hf] at h'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1113, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [aroots_def' hf, nodup_roots_iff_of_splits (map_ne_zero _ hf) h, separable_map]
```

**lean_error:** tail step 1/1 ("rw [aroots_def' hf, nodup_roots_iff_of_splits (map_ne_zero _ hf) h, separable_map]"): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.2s, in=1113, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (nodup_roots_iff_of_splits (map_ne_zero hf) h).symm.trans (separable_map (algebraMap F K))
```

**lean_error:** tail step 1/1 ('exact (nodup_roots_iff_of_splits (map_ne_zero hf) h).symm.trans (separable_map (algebraMap F K))'): type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.2s, in=1113, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (nodup_roots_iff_of_splits (map_ne_zero _ hf) h).symm.trans (separable_map (algebraMap F K)).symm
```

**lean_error:** tail step 1/1 ('exact (nodup_roots_iff_of_splits (map_ne_zero _ hf) h).symm.trans (separable_map (algebraMap F K)).symm'): type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.2s, in=1113, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (nodup_roots_iff_of_splits (map_ne_zero (algebraMap F K) hf) h).symm.trans
  (separable_map (algebraMap F K)).symm
```

**lean_error:** tail step 1/2 ('exact (nodup_roots_iff_of_splits (map_ne_zero (algebraMap F K) hf) h).symm.trans'): type mismatch
