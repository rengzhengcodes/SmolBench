# Polynomial.roots_expand_image_frobenius   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
rw [Finset.image_toFinset, roots_expand_map_frobenius,
    (roots f).toFinset_nsmul _ (expChar_pos R p).ne']
```

**True premises at k:** `Finset.image_toFinset`, `Polynomial.roots_expand_map_frobenius`, `Polynomial.roots`, `Multiset.toFinset_nsmul`, `expChar_pos`, `LT.lt.ne'`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=327, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toFinset_image, roots_map]
congr
ext
simp only [mem_roots, eval_map, coe_expand]
```

**lean_error:** tail step 1/4 ('rw [toFinset_image, roots_map]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=296, out=114)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Multiset.toFinset_map, Multiset.toFinset_eq_iff, Multiset.map_toFinset, Multiset.toFinset_eq_iff]
simp only [Multiset.map_id', roots_expand, frobenius_def]
exact map_roots_frobenius f
rw [← Multiset.toFinset_map, Multiset.toFinset_eq_iff, Multiset.map_toFinset, Multiset.toFinset_eq_iff]
simp only [Multiset.map_id', roots_expand, frobenius_def]
exact map_roots_frobenius f
```

**lean_error:** tail step 1/6 ('rw [← Multiset.toFinset_map, Multiset.toFinset_eq_iff, Multiset.map_toFinset, Multiset.toFinset_eq_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=316, out=118)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply finset.ext
intro x
constructor
· intro h
  apply toFinset.mem_iff
  rw [←roots_expand f p, toFinset.mem_iff] at h
  erw [frobenius_apply] at h
  rwa [←roots_expand f p]
· intro h
  apply toFinset.mem_iff
  rw [←roots_expand f p, toFinset.mem_iff] at h
  erw [frobenius_apply] at h
  rwa [←roots_expand f p]
```

**lean_error:** tail step 1/13 ('apply finset.ext'): unknown identifier 'finset.ext'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 3.5s, verify 0.3s, in=1330, out=65)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_map_frobenius]
rw [Multiset.toFinset_nsmul _ _ (expChar_pos R p).ne']
exact Multiset.toFinset_map _ _ (LT.lt.ne' (expChar_pos R p))
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1281, out=68)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Finset.image_toFinset, Polynomial.roots_expand_map_frobenius]
simp only [Multiset.toFinset_nsmul]
· rw [Ne, ← pos_iff_ne_zero, expChar_pos]
  exact LT.lt.ne' (expChar_pos p)
rw [Finset.image_toFinset]
```

**lean_error:** tail step 1/5 ('rw [← Finset.image_toFinset, Polynomial.roots_expand_map_frobenius]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=1319, out=76)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply image_toFinset
simp [roots_expand_map_frobenius, toFinset_nsmul _ p (expChar_pos R p)]
```

**lean_error:** tail step 1/2 ('apply image_toFinset'): unknown identifier 'image_toFinset'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.4s, in=4364, out=56)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_map_frobenius]
rw [Multiset.toFinset_nsmul _ (expChar_pos R p).ne']
rw [LT.lt.ne' (expChar_pos R p)]
```

**lean_error:** tail step 3/4 ("rw [Multiset.toFinset_nsmul _ (expChar_pos R p).ne']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=4313, out=48)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Finset.image_toFinset, Polynomial.roots_expand_map_frobenius]
simp only [Multiset.toFinset_nsmul, expChar_pos R p |>.ne', Finset.image_toFinset]
```

**lean_error:** tail step 1/2 ('rw [← Finset.image_toFinset, Polynomial.roots_expand_map_frobenius]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=4353, out=142)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [image_toFinset, roots_expand_map_frobenius, toFinset_nsmul (roots f) p (expChar_pos R p).ne', toFinset_nsmul (roots f) 1 (Nat.one_ne')]
congr
exact (roots f).toFinset
```

**lean_error:** tail step 1/3 ("rw [image_toFinset, roots_expand_map_frobenius, toFinset_nsmul (roots f) p (expChar_pos R p).ne', toFinset_nsmul (roots f) 1 (Nat.one_ne')]"): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 3.0s, verify 0.2s, in=4391, out=54)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset, Polynomial.roots_expand_map_frobenius]
rw [Multiset.toFinset_nsmul _ _ (expChar_pos R p).ne']
rw [LT.lt.ne' (expChar_pos R p)]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.5s, in=4692, out=51)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_map_frobenius]
rw [Multiset.toFinset_nsmul]
simp only [expChar_pos, ne_eq, Ne, not_false_eq_true]
rfl
```

**lean_error:** tail step 5/5 ('rfl'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=4380, out=45)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [image_toFinset, roots_expand_map_frobenius]
simp [toFinset_nsmul, expChar_pos]
exact ne' (expChar_pos R p)
```

**lean_error:** tail step 1/3 ('rw [image_toFinset, roots_expand_map_frobenius]'): tactic 'rewrite' failed, equality or iff proof expected
