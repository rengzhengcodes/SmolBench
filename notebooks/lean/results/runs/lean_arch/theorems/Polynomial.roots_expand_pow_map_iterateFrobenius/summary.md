# Polynomial.roots_expand_pow_map_iterateFrobenius   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [← coe_iterateFrobeniusEquiv, roots_expand_pow, Multiset.map_nsmul,
  Multiset.map_map, comp_apply, RingEquiv.apply_symm_apply, map_id']
```

**True premises at k:** `coe_iterateFrobeniusEquiv`, `Polynomial.roots_expand_pow`, `Multiset.map_nsmul`, `Multiset.map_map`, `Function.comp_apply`, `RingEquiv.apply_symm_apply`, `Multiset.map_id'`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.1s, in=318, out=70)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Multiset.map_map],
simp_rw [iterateFrobenius_comp_Frobenius, expand_map],
rw [Multiset.map_map],
simp_rw [Frobenius_def],
rw [roots_map],
simp_rw [Multiset.map_const, Multiset.map_replicate],
rw [Multiset.nsmul_replicate]
```

**lean_error:** tail step 1/7 ('rw [Multiset.map_map],'): <stdin>:1:21: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=290, out=48)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Multiset.map_iterateFrobenius, Multiset.map_map]
simp only [Function.comp_apply]
rw [map_roots_expand]
simp only [iterateFrobenius_expand, smul_roots]
rfl
```

**lean_error:** tail step 1/5 ('rw [← Multiset.map_iterateFrobenius, Multiset.map_map]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=307, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Multiset.map_ext
simp only [iterateFrobenius_def, roots_expand, Multiset.nsmul_replicate]
```

**lean_error:** tail step 1/2 ('apply Multiset.map_ext'): unknown constant 'Multiset.map_ext'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.3s, in=1432, out=53)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Polynomial.roots_expand_pow, Multiset.map_nsmul, Multiset.map_map]
rw [coe_iterateFrobeniusEquiv, Function.comp_apply, RingEquiv.apply_symm_apply]
rw [Multiset.map_id']
```

**lean_error:** tail step 2/3 ('rw [coe_iterateFrobeniusEquiv, Function.comp_apply, RingEquiv.apply_symm_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1383, out=45)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [roots_expand_pow, Multiset.map_map, Function.comp_apply, coe_iterateFrobeniusEquiv, RingEquiv.apply_symm_apply, Multiset.map_id', Multiset.map_nsmul]
```

**lean_error:** tail step 1/1 ("rw [roots_expand_pow, Multiset.map_map, Function.comp_apply, coe_iterateFrobeniusEquiv, RingEquiv.apply_symm_apply, Multiset.map_id', Multiset.map_nsmul]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1421, out=55)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [roots_expand_pow, map_nsmul, map_map (· ∘ ·) (symm (iterateFrobeniusEquiv R p n)) (roots f),
  comp_apply, apply_symm_apply, map_id']
```

**lean_error:** tail step 1/2 ('rw [roots_expand_pow, map_nsmul, map_map (· ∘ ·) (symm (iterateFrobeniusEquiv R p n)) (roots f),'): <stdin>:1:96: unexpected end of input; expected ']'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.3s, in=3032, out=70)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Polynomial.roots_expand_pow, Multiset.map_nsmul, Multiset.map_map]
rw [coe_iterateFrobeniusEquiv, Function.comp_apply, RingEquiv.apply_symm_apply]
rw [Multiset.map_id']
exact Polynomial.roots_expand_pow_map_iterateFrobenius R p n f
```

**lean_error:** tail step 2/4 ('rw [coe_iterateFrobeniusEquiv, Function.comp_apply, RingEquiv.apply_symm_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=2982, out=45)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [roots_expand_pow, Multiset.map_map, Function.comp_apply, coe_iterateFrobeniusEquiv, RingEquiv.apply_symm_apply, Multiset.map_id', Multiset.map_nsmul]
```

**lean_error:** tail step 1/1 ("rw [roots_expand_pow, Multiset.map_map, Function.comp_apply, coe_iterateFrobeniusEquiv, RingEquiv.apply_symm_apply, Multiset.map_id', Multiset.map_nsmul]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=3021, out=47)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [roots_expand_pow, map_nsmul, map_map (f := iterateFrobeniusEquiv R p n).symm, comp_apply,
  apply_symm_apply, map_id']
```

**lean_error:** tail step 1/2 ('rw [roots_expand_pow, map_nsmul, map_map (f := iterateFrobeniusEquiv R p n).symm, comp_apply,'): <stdin>:1:93: unexpected end of input; expected ']'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.3s, in=3059, out=55)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Polynomial.roots_expand_pow, Multiset.map_nsmul, Multiset.map_map]
rw [coe_iterateFrobeniusEquiv, Function.comp_apply, RingEquiv.apply_symm_apply]
rw [Multiset.map_id']
exact rfl
```

**lean_error:** tail step 2/4 ('rw [coe_iterateFrobeniusEquiv, Function.comp_apply, RingEquiv.apply_symm_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=3195, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [roots_expand_pow]
simp_rw [coe_iterateFrobeniusEquiv, ← map_map, RingEquiv.apply_symm_apply, map_id']
```

**lean_error:** tail step 2/2 ("simp_rw [coe_iterateFrobeniusEquiv, ← map_map, RingEquiv.apply_symm_apply, map_id']"): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=3048, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [roots_expand_pow, map_nsmul, map_map]
erw [← coe_iterateFrobeniusEquiv, ← Function.comp_apply, apply_symm_apply, map_id']
```

**lean_error:** tail step 1/2 ('rw [roots_expand_pow, map_nsmul, map_map]'): tactic 'rewrite' failed, equality or iff proof expected
