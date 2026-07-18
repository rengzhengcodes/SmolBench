# Polynomial.roots_expand_pow_map_iterateFrobenius   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [← coe_iterateFrobeniusEquiv, roots_expand_pow, Multiset.map_nsmul,
  Multiset.map_map, comp_apply, RingEquiv.apply_symm_apply, map_id']
```

**True premises at k:** `coe_iterateFrobeniusEquiv`, `Polynomial.roots_expand_pow`, `Multiset.map_nsmul`, `Multiset.map_map`, `Function.comp_apply`, `RingEquiv.apply_symm_apply`, `Multiset.map_id'`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=288, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [roots_expand, ← map_pow_frobenius]
```

**lean_error:** tail step 1/1 ('simp [roots_expand, ← map_pow_frobenius]'): unknown identifier 'map_pow_frobenius'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=288, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← expand_roots, map_comp, Function.comp, iterateFrobenius_apply]
```

**lean_error:** tail step 1/1 ('rw [← expand_roots, map_comp, Function.comp, iterateFrobenius_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=288, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [roots_expand, ← map_pow, map_frobenius, Multiset.map_map]
```

**lean_error:** tail step 1/1 ('rw [roots_expand, ← map_pow, map_frobenius, Multiset.map_map]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=288, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [roots_expand, map_multiset_map, ← iterateFrobenius_map, map_multiset_map, ← pow_smul]
```

**lean_error:** tail step 1/1 ('rw [roots_expand, map_multiset_map, ← iterateFrobenius_map, map_multiset_map, ← pow_smul]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.0s, verify 0.1s, in=1402, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv, Function.comp_apply,
  apply_symm_apply, map_id']
```

**lean_error:** tail step 1/2 ('simp [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv, Function.comp_apply,'): <stdin>:1:91: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=1402, out=57)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv,
  Function.comp_apply, apply_symm_apply, map_id', nsmul_eq_mul, mul_comm (p ^ n)]
```

**lean_error:** tail step 1/2 ('simp only [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv,'): <stdin>:1:75: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.6s, verify 0.1s, in=1402, out=72)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [roots_expand_pow, coe_iterateFrobeniusEquiv, Multiset.map_nsmul, Multiset.map_map,
  Function.comp_apply, apply_symm_apply, Multiset.map_id', coe_nsmul, ← map_nsmul,
  ← Multiset.nsmul_eq_smul]
```

**lean_error:** tail step 1/3 ('rw [roots_expand_pow, coe_iterateFrobeniusEquiv, Multiset.map_nsmul, Multiset.map_map,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 5.0s, verify 0.1s, in=1402, out=198)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  Multiset.map (iterateFrobenius R p n) (roots (expand R (p ^ n) f)) = _ := by
    rw [roots_expand_pow]
  _ = p ^ n • Multiset.map (iterateFrobenius R p n) (roots f.map (iterateFrobeniusEquiv R p n).symm) :=
    rfl
  _ = p ^ n • Multiset.map (iterateFrobenius R p n ∘ (iterateFrobeniusEquiv R p n).symm) (roots f) :=
    map_map _ _ _
  _ = p ^ n • Multiset.map id (roots f) := by
    rw [Function.comp_apply, coe_iterateFrobeniusEquiv, RingEquiv.apply_symm_apply, id.def]
  _ = p ^ n • roots f := by rw [map_id']
```

**lean_error:** tail step 1/10 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=3009, out=49)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv,
  Function.comp, iterateFrobeniusEquiv.apply_symm_apply, map_id']
```

**lean_error:** tail step 1/2 ('simp [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv,'): <stdin>:1:70: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.7s, verify 0.1s, in=3009, out=53)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [roots_expand_pow, ← map_nsmul, ← map_map, ← coe_iterateFrobeniusEquiv, Function.comp_apply,
  iterateFrobeniusEquiv.apply_symm_apply, map_id']
```

**lean_error:** tail step 1/2 ('rw [roots_expand_pow, ← map_nsmul, ← map_map, ← coe_iterateFrobeniusEquiv, Function.comp_apply,'): <stdin>:1:95: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.8s, verify 0.1s, in=3009, out=51)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [roots_expand_pow, map_nsmul, ← map_map, coe_iterateFrobeniusEquiv, Function.comp_apply,
  iterateFrobeniusEquiv.apply_symm_apply, map_id']
```

**lean_error:** tail step 1/2 ('simp [roots_expand_pow, map_nsmul, ← map_map, coe_iterateFrobeniusEquiv, Function.comp_apply,'): <stdin>:1:93: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 72.6s, verify 0.1s, in=3009, out=60)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [roots_expand_pow, coe_iterateFrobeniusEquiv, map_nsmul, map_map, Function.comp,
  iterateFrobeniusEquiv_symm_apply_iterateFrobenius, apply_symm_apply, map_id']
```

**lean_error:** tail step 1/2 ('simp only [roots_expand_pow, coe_iterateFrobeniusEquiv, map_nsmul, map_map, Function.comp,'): <stdin>:1:90: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=3032, out=43)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv, Function.comp_apply,
  apply_symm_apply, map_id']
```

**lean_error:** tail step 1/2 ('simp [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv, Function.comp_apply,'): <stdin>:1:91: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=3032, out=46)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [roots_expand_pow, ← map_nsmul, ← map_map, Function.comp_apply,
  iterateFrobeniusEquiv_apply_symm_apply, map_id', map_nsmul]
```

**lean_error:** tail step 1/2 ('rw [roots_expand_pow, ← map_nsmul, ← map_map, Function.comp_apply,'): <stdin>:1:66: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=3032, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv,
  Function.comp_apply, RingEquiv.apply_symm_apply, Multiset.map_id']
```

**lean_error:** tail step 1/2 ('simp only [roots_expand_pow, map_nsmul, map_map, coe_iterateFrobeniusEquiv,'): <stdin>:1:75: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=3032, out=50)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [roots_expand_pow, ← map_nsmul, ← map_map, Function.comp_apply,
  iterateFrobeniusEquiv_apply_symm_apply, map_id', nsmul_eq_mul, mul_comm]
```

**lean_error:** tail step 1/2 ('rw [roots_expand_pow, ← map_nsmul, ← map_map, Function.comp_apply,'): <stdin>:1:66: unexpected end of input; expected ']'
