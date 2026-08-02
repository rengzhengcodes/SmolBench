# CategoryTheory.Limits.Types.FilteredColimit.isColimit_eq_iff   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Limits/Types.lean`  

**Ground-truth tail (from k):**
```lean
exact (congrFun
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xj).symm
```

**True premises at k:** `congrFun`, `CategoryTheory.Limits.IsColimit.comp_coconePointUniqueUpToIso_hom`, `CategoryTheory.Limits.Types.colimitCoconeIsColimit`, `Eq.symm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✘ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.6s, verify 0.1s, in=456, out=1484)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using
  congrArg (fun f => f xj)
    (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) (j:=j))
```

**lean_error:** tail step 1/3 ('simpa using'): <stdin>:1:11: unexpected end of input

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 72.8s, verify 0.1s, in=408, out=8514)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).toEquiv (t.ι j xj) = ((IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).hom : t pt → (colimitCocone F).pt) (t.ι j xj) := by
  rw [Category.Iso.toEquiv_apply]
have h₂ : ((IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).hom : t pt → (colimitCocone F).pt) (t.ι j xj) = (colimitCocone F).ι j xj := by
  apply (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).hom.comm'
rw [h₁]
rw [h₂]
```

**lean_error:** tail step 1/6 ('have h₁ : (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).toEquiv (t.ι j xj) = ((IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).hom : t pt → (colimitCocone F).pt) (t.ι j xj) := by'): <stdin>:1:217: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.1s, in=398, out=459)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsColimit.coconePointUniqueUpToIso_ι_app]
```

**lean_error:** tail step 1/1 ('simp [IsColimit.coconePointUniqueUpToIso_ι_app]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.9s, verify 0.1s, in=2675, out=1788)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xj).symm
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 125.1s, verify 0.1s, in=2696, out=15568)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 14.2s, verify 0.3s, in=2627, out=1351)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xi).symm
```

**lean_error:** tail step 1/1 ('exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xi).symm'): type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 18.5s, verify 0.8s, in=9111, out=3333)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xj).symm
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 68.7s, verify 0.1s, in=9222, out=7953)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
<;> trivial
```

**lean_error:** tail step 1/1 ('<;> trivial'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 51.7s, verify 0.1s, in=9093, out=5378)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 16.9s, verify 0.1s, in=8341, out=2951)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 136.5s, verify 0.1s, in=10116, out=17105)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  (colimitCocone F).ι.app j xj = (t.ι.app j ≫ (coconePointUpToIso ht (colimitCoconeIsColimit F)).hom) xj := by
    rw [IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j]
  _ = (coconePointUpToIso ht (colimitCoconeIsColimit F)).hom (t.ι.app j xj) := by
    simp [Function.comp_apply]
  _ = (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).toEquiv (t.ι.app j xj) := by rfl
```

**lean_error:** tail step 1/6 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.3s, in=8941, out=464)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xi).symm
```

**lean_error:** tail step 1/1 ('exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xi).symm'): type mismatch
