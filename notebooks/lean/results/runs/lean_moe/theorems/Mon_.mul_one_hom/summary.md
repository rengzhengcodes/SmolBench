# Mon_.mul_one_hom   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Monoidal/Mon_.lean`  

**Ground-truth tail (from k):**
```lean
rw [tensorHom_def_assoc, M.mul_one, rightUnitor_naturality]
```

**True premises at k:** `CategoryTheory.MonoidalCategory.tensorHom_def_assoc`, `CategoryTheory.MonoidalCategory.rightUnitor_naturality`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.1s, verify 0.1s, in=328, out=2077)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using M.mul_one_hom f
```

**lean_error:** tail step 1/1 ('simpa using M.mul_one_hom f'): invalid field notation, function 'Mon_.mul_one_hom' does not have argument with type (Mon_ ...) that can be used, it must be explicit or implicit with a unique name

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 116.6s, verify 0.1s, in=275, out=17222)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : f ⊗ M.one = (f ⊗ id) ≫ (id ⊗ M.one) := by
  have h₂ : (f ⊗ id) ≫ (id ⊗ M.one) = f ⊗ M.one := by
    calc
      (f ⊗ id) ≫ (id ⊗ M.one) = (id ⊗ M.one) ∘ (f ⊗ id) := rfl
      _ = (id ∘ f) ⊗ (M.one ∘ id) := by
        rw [TensorProduct.map_map]
      _ = f ⊗ M.one := by simp [id]
  rw [← h₂]
calc
  (f ⊗ M.one) ≫ M.mul = ((f ⊗ id) ≫ (id ⊗ M.one)) ≫ M.mul := by rw [h₁]
  _ = (f ⊗ id) ≫ ((id ⊗ M.one) ≫ M.mul) := by rw [← CategoryExt.assoc]
  _ = (f ⊗ id) ≫ (ρ_ M.X) := by rw [M.mul_one]
  _ = f ≫ (ρ_ Z) := by apply ρ_nat
```

**lean_error:** tail step 1/13 ('have h₁ : f ⊗ M.one = (f ⊗ id) ≫ (id ⊗ M.one) := by'): <stdin>:1:51: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.1s, in=267, out=511)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact M.mul_one f
```

**lean_error:** tail step 1/1 ('exact M.mul_one f'): function expected at
