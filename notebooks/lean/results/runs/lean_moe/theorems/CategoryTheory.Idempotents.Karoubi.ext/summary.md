# CategoryTheory.Idempotents.Karoubi.ext   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Idempotents/Karoubi.lean`  

**Ground-truth tail (from k):**
```lean
simpa only [mk.injEq, heq_eq_eq, true_and, eqToHom_refl, comp_id, id_comp] using h_p
```

**True premises at k:** `heq_eq_eq`, `true_and`, `CategoryTheory.eqToHom_refl`, `CategoryTheory.Category.comp_id`, `CategoryTheory.Category.id_comp`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=438, out=943)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
· rfl
· simpa using h_p
· apply Subsingleton.elim
```

**lean_error:** tail step 1/4 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 89.9s, verify 0.1s, in=421, out=10246)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h_p_eq : p✝¹ = p✝ := by sorry
have h_idem_eq : idem✝¹ = idem✝ := by sorry
```

**lean_error:** tail step 1/2 ('have h_p_eq : p✝¹ = p✝ := by sorry'): <stdin>:1:15: expected token

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=393, out=537)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
<;> simp_all
<;> aesop_cat
```

**lean_error:** tail step 1/3 ('ext'): no applicable extensionality theorem found for

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.4s, verify 0.1s, in=1008, out=2159)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases h_p
cases idem✝¹
cases idem✝
rfl
```

**lean_error:** tail step 1/4 ('cases h_p'): dependent elimination failed, failed to solve equation

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 265.1s, verify 0.1s, in=1015, out=32500)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext <;> (try rfl) <;> simp_all [heq_eq_eq, true_and, CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp]
```

**lean_error:** tail step 1/1 ('ext <;> (try rfl) <;> simp_all [heq_eq_eq, true_and, CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp]'): no applicable extensionality theorem found for

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.1s, in=960, out=527)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
<;> simp_all [CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp]
<;> try aesop
```

**lean_error:** tail step 1/3 ('ext'): no applicable extensionality theorem found for

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=2186, out=1653)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h_pp : p✝¹ = p✝ := by
  simpa using h_p
cases h_pp
apply Subsingleton.elim
```

**lean_error:** tail step 1/4 ('have h_pp : p✝¹ = p✝ := by'): <stdin>:1:13: expected token

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 267.6s, verify 0.1s, in=2191, out=32768)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
· rfl
· -- Prove p✝¹ = p✝
  have h₁ : eqToHom ⋯ = 𝟙 X✝ := by
    sorry
  have h₂ : p✝¹ ≫ eqToHom ⋯ = p✝¹ := by
    rw [h₁]
    <;> simp [CategoryTheory.comp_id]
  have h₃ : eqToHom ⋯ ≫ p✝ = p✝ := by
    rw [h₁]
    <;> simp [CategoryTheory.id_comp]
  have h₄ : p✝¹ = p✝ := by
    calc
      p✝¹ = p✝¹ ≫ eqToHom ⋯ := by rw [h₂.symm]
      _ = eqToHom ⋯ ≫ p✝ := by rw [h_p]
      _ = p✝ := by rw [h₃]
  exact h₄
· -- Prove idem✝¹ = idem✝
  have h₂ : p✝ = p✝¹ := by
    sorry
  rw [h₂] at *
  <;> simp_all [idem✝, idem✝¹]
  <;> try aesop
```

**lean_error:** tail step 1/23 ('ext'): no applicable extensionality theorem found for

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.1s, in=2139, out=501)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
<;> simp_all [CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.1s, in=2070, out=1562)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hp_eq : p✝¹ = p✝ := by
  simpa using h_p
cases hp_eq
have h_idem : idem✝¹ = idem✝ := Subsingleton.elim _ _
cases h_idem
rfl
```

**lean_error:** tail step 1/6 ('have hp_eq : p✝¹ = p✝ := by'): <stdin>:1:14: expected token

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 140.6s, verify 0.1s, in=2402, out=16121)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Structure.ext
<;> simp_all [CategoryTheory.eqToHom_refl, Category.comp_id, Category.id_comp]
<;> aesop
```

**lean_error:** tail step 1/3 ('apply Structure.ext'): unknown identifier 'Structure.ext'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.8s, in=2141, out=499)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext
simp_all [heq_eq_eq, true_and, CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for
