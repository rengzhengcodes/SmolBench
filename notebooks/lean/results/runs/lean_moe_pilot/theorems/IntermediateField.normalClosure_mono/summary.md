# IntermediateField.normalClosure_mono   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/NormalClosure.lean`  

**Ground-truth tail (from k):**
```lean
exact iSup_mono (fun f ↦ map_mono f h)
```

**True premises at k:** `iSup_mono`, `IntermediateField.map_mono`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.4s, verify 0.3s, in=360, out=975)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine iSup_le ?_
  intro f
  exact le_iSup_of_le f (by
    simpa using (map_mono (f:=f) h))
```

**lean_error:** tail step 3/4 ('exact le_iSup_of_le f (by'): <stdin>:1:25: unexpected end of input; expected '{'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 187.6s, verify 1.1s, in=313, out=20405)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : ⨆ f, map f K ≤ ⨆ f, map f K' := by
  have h₂ : ∀ f, map f K ≤ ⨆ f, map f K' := by
    intro f
    have h₃ : map f K ≤ map f K' := by
      have h_injective : Function.Injective f := by
        apply RingHom.injective_of_field
        <;> simp [RingHom.map_one]
      have h_kk' : (K : Subfield L) ≤ (K' : Subfield L) := by
        exact h
      have h_map : map f K ≤ map f K' := by
        apply IntermediateField.map_mono
        · exact h_injective
        · exact h_kk'
      exact h_map
    have h₄ : map f K' ≤ ⨆ f, map f K' := by
      apply le_csSup
    exact le_trans h₃ h₄
  exact csSup_le h₂
  <;> assumption
exact h₁

</think>
have h₁ : ⨆ f, map f K ≤ ⨆ f, map f K' := by
  have h₂ : ∀ f, map f K ≤ ⨆ f, map f K' := by
    intro f
    have h₃ : map f K ≤ map f K' := by
      have h_injective : Function.Injective f := by
        apply RingHom.injective_of_field
        <;> simp [RingHom.map_one]
      have h_kk' : (K : Subfield L) ≤ (K' : Subfield L) := by
        exact h
      have h_map : map f K ≤ map f K' := by
        apply IntermediateField.map_mono
        · exact h_injective
        · exact h_kk'
      exact h_map
    have h₄ : map f K' ≤ ⨆ f, map f K' := by
      apply le_csSup
    exact le_trans h₃ h₄
  exact csSup_le h₂
exact h₁
```

**lean_error:** tail step 1/40 ("have h₁ : ⨆ f, map f K ≤ ⨆ f, map f K' := by"): <stdin>:1:44: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 27.0s, verify 0.1s, in=308, out=561)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
iSup_le_iSup (fun f => map_mono h)
```

**lean_error:** tail step 1/1 ('iSup_le_iSup (fun f => map_mono h)'): <stdin>:1:1: unknown tactic

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.9s, verify 0.3s, in=723, out=690)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine iSup_mono ?_
intro f
exact IntermediateField.map_mono f h
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 110.4s, verify 0.1s, in=687, out=10928)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : ∀ (f : L →ₐ[F] L), K.map f ≤ K'.map f := by
  intro f
  apply IntermediateField.map_mono
  <;> assumption
exact iSup_mono h₁
```

**lean_error:** tail step 1/5 ("have h₁ : ∀ (f : L →ₐ[F] L), K.map f ≤ K'.map f := by"): <stdin>:1:53: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 25.8s, verify 0.4s, in=666, out=465)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono
exact h
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.2s, verify 0.3s, in=3545, out=700)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine iSup_mono ?_
intro f
exact IntermediateField.map_mono f h
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 18.4s, verify 0.1s, in=3559, out=1293)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : ∀ (f : L →ₐ[F] L), map f K ≤ map f K' := by
  intro f
  apply IntermediateField.map_mono
  exact h
apply iSup_mono
exact h₁
```

**lean_error:** tail step 1/6 ("have h₁ : ∀ (f : L →ₐ[F] L), map f K ≤ map f K' := by"): <stdin>:1:53: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 26.2s, verify 0.3s, in=3516, out=485)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
gcongr
exact map_mono h
```

**lean_error:** tail step 2/2 ('exact map_mono h'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.9s, verify 0.3s, in=3248, out=885)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine iSup_mono ?_
intro f
exact IntermediateField.map_mono (f := f) h
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 25.0s, verify 0.4s, in=3990, out=1943)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply IntermediateField.map_mono
exact h
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 24.7s, verify 0.3s, in=3478, out=380)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono h
```

**lean_error:** tail step 3/3 ('apply map_mono h'): application type mismatch
