# IntermediateField.exists_algHom_adjoin_of_splits_of_aeval   (k=3, 4 tactics total)

file: `Mathlib/FieldTheory/Extension.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨φ, (DFunLike.congr_fun hφ <| AdjoinSimple.gen F x).trans <|
  algHomAdjoinIntegralEquiv_symm_apply_gen F ix _⟩
```

**True premises at k:** `DFunLike.congr_fun`, `IntermediateField.AdjoinSimple.gen`, `Eq.trans`, `IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=500, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use φ,
rw [hφ, algHomAdjoinIntegralEquiv_symm_apply, Subtype.val_eq]
```

**lean_error:** tail step 1/2 ('use φ,'): <stdin>:1:6: unexpected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=467, out=57)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use hφ
simp only [AlgHom.comp_apply, inclusion_val, AlgEquiv.symm_apply_eq]
rw [← Subtype.coe_inj]
simp only [Subtype.coe_mk, AlgEquiv.apply_symm_apply]
exact ⟨φ, rfl⟩
```

**lean_error:** tail step 1/5 ('use hφ'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=489, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply exists.intro φ
exact hφ
```

**lean_error:** tail step 1/2 ('apply exists.intro φ'): unknown identifier 'exists.intro'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.2s, in=1593, out=42)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
use DFunLike.congr_fun hφ (IntermediateField.AdjoinSimple.gen F x)
rw [IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix]
exact Exists.intro φ
```

**lean_error:** tail step 1/3 ('use DFunLike.congr_fun hφ (IntermediateField.AdjoinSimple.gen F x)'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1554, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨φ, by rw [← hφ, AlgHom.comp_apply, IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen, Subtype.coe_mk]⟩
```

**lean_error:** tail step 1/1 ('exact ⟨φ, by rw [← hφ, AlgHom.comp_apply, IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen, Subtype.coe_mk]⟩'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.4s, in=1582, out=55)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Exists.intro φ
exact (DFunLike.congr_fun (Eq.trans hφ (IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, _⟩)) (IntermediateField.AdjoinSimple.gen F x))
```

**lean_error:** tail step 2/2 ('exact (DFunLike.congr_fun (Eq.trans hφ (IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, _⟩)) (IntermediateField.AdjoinSimple.gen F x))'): type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=4314, out=57)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
use DFunLike.congr_fun hφ (IntermediateField.AdjoinSimple.gen F x)
rw [Eq.trans (IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix _) (IntermediateField.AdjoinSimple.gen F x).property]
exact Exists.intro φ
```

**lean_error:** tail step 1/3 ('use DFunLike.congr_fun hφ (IntermediateField.AdjoinSimple.gen F x)'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.2s, in=4263, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ⟨φ, by rw [← hφ, AlgHom.comp_apply, IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix, Subtype.coe_mk]⟩
```

**lean_error:** tail step 1/1 ('exact ⟨φ, by rw [← hφ, AlgHom.comp_apply, IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix, Subtype.coe_mk]⟩'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.4s, in=4303, out=55)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Exists.intro φ
exact (DFunLike.congr_fun (Eq.trans hφ (IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, _⟩)) (IntermediateField.AdjoinSimple.gen F x))
```

**lean_error:** tail step 2/2 ('exact (DFunLike.congr_fun (Eq.trans hφ (IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, _⟩)) (IntermediateField.AdjoinSimple.gen F x))'): type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.2s, in=4344, out=54)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [hφ, algHomAdjoinIntegralEquiv_symm_apply_gen]
exact Exists.intro φ (DFunLike.congr_fun (Eq.trans hφ (Eq.symm (algHomAdjoinIntegralEquiv_symm_apply_gen ix _))) _)
```

**lean_error:** tail step 1/2 ('rw [hφ, algHomAdjoinIntegralEquiv_symm_apply_gen]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 1.7s, in=4617, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ⟨φ, by rw [← hφ, AlgHom.comp_apply, IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen, Subtype.coe_mk]⟩
```

**lean_error:** tail step 1/1 ('exact ⟨φ, by rw [← hφ, AlgHom.comp_apply, IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen, Subtype.coe_mk]⟩'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.4s, in=4333, out=69)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Exists.intro φ
exact (DFunLike.congr_fun (Eq.trans hφ (IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩)) (IntermediateField.AdjoinSimple.gen F x))
```

**lean_error:** tail step 2/2 ('exact (DFunLike.congr_fun (Eq.trans hφ (IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩)) (IntermediateField.AdjoinSimple.gen F x))'): type mismatch
