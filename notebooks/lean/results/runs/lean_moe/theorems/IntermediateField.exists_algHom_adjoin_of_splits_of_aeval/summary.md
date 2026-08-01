# IntermediateField.exists_algHom_adjoin_of_splits_of_aeval   (k=3, 4 tactics total)

file: `Mathlib/FieldTheory/Extension.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨φ, (DFunLike.congr_fun hφ <| AdjoinSimple.gen F x).trans <|
  algHomAdjoinIntegralEquiv_symm_apply_gen F ix _⟩
```

**True premises at k:** `DFunLike.congr_fun`, `IntermediateField.AdjoinSimple.gen`, `Eq.trans`, `IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.6s, verify 0.6s, in=543, out=2336)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨φ, ?_⟩
have h := congrArg (fun g : (adjoin F S) →ₐ[F] K => g { val := x, property := hx }) hφ
simpa using h
```

**lean_error:** tail step 2/3 ('have h := congrArg (fun g : (adjoin F S) →ₐ[F] K => g { val := x, property := hx }) hφ'): application type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 14.5s, verify 3.1s, in=1689, out=2307)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine ⟨φ, ?_⟩
have h' := DFunLike.congr_fun hφ (AdjoinSimple.gen F x)
simp [AlgHom.comp_apply, IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen] at h'
exact h'
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.0s, verify 0.5s, in=4494, out=2269)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine ⟨φ, ?_⟩
have hval := DFunLike.congr_fun hφ (AdjoinSimple.gen F x)
simp [AlgHom.comp_apply,
      IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen] at hval
simpa using hval
```

**lean_error:** tail step 3/5 ('simp [AlgHom.comp_apply,'): <stdin>:1:24: unexpected end of input; expected ']'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 18.3s, verify 0.3s, in=4188, out=3384)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine ⟨φ, ?_⟩
have h_eq :=
  congrArg (fun f : (F⟮x⟯) →ₐ[F] K => f (AdjoinSimple.gen F x)) hφ
simp [AlgHom.comp_apply,
      IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix] at h_eq
exact h_eq
```

**lean_error:** tail step 2/6 ('have h_eq :='): <stdin>:1:12: unexpected end of input
