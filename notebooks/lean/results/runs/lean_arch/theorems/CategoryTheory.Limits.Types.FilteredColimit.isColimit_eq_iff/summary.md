# CategoryTheory.Limits.Types.FilteredColimit.isColimit_eq_iff   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Limits/Types.lean`  

**Ground-truth tail (from k):**
```lean
exact (congrFun
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xj).symm
```

**True premises at k:** `congrFun`, `CategoryTheory.Limits.IsColimit.comp_coconePointUniqueUpToIso_hom`, `CategoryTheory.Limits.Types.colimitCoconeIsColimit`, `Eq.symm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.2s, in=410, out=52)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [IsColimit.coconePointUniqueUpToIso_inv]
simp only [Equiv.toEquiv_eq_coe, IsColimit.coconePointUniqueUpToIso_inv]
simp only [colimitCoconeIsColimit_desc]
```

**lean_error:** tail step 1/3 ('erw [IsColimit.coconePointUniqueUpToIso_inv]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=387, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← colimitCoconeIsColimit F].fac
rw [IsColimit.coconePointUniqueUpToIso_hom]
rw [colimitCoconeIsColimit F].fac] 
aesop_cat
```

**lean_error:** tail step 1/4 ('rw [← colimitCoconeIsColimit F].fac'): <stdin>:1:31: expected end of input

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=399, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iso.toEquiv_symm_apply
apply (colimitCoconeIsColimit F).uniqueUpToIso_comp_t_ι_app j xj
```

**lean_error:** tail step 1/2 ('apply Iso.toEquiv_symm_apply'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 3.9s, verify 0.1s, in=2570, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 1.1s, verify 0.3s, in=2563, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj]
rfl
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=2559, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xj).symm
```

**lean_error:** tail step 1/2 ('exact (congrFun'): <stdin>:1:15: unexpected end of input; expected ')', ',' or ':'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.1s, in=8786, out=46)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj
rw [Eq.symm (colimit_eq_iff_aux F)]
```

**lean_error:** tail step 1/2 ('congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj'): <stdin>:1:1: unknown tactic

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=8802, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=8775, out=44)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (congrFun 
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

**lean_error:** tail step 1/2 ('exact (congrFun'): <stdin>:1:15: unexpected end of input; expected ')', ',' or ':'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.0s, verify 0.1s, in=8817, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j).symm xj
exact Eq.refl _
```

**lean_error:** tail step 1/2 ('congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j).symm xj'): <stdin>:1:1: unknown tactic

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=9525, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj
```

**lean_error:** tail step 1/1 ('exact congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=8806, out=44)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (congrFun 
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

**lean_error:** tail step 1/2 ('exact (congrFun'): <stdin>:1:15: unexpected end of input; expected ')', ',' or ':'
