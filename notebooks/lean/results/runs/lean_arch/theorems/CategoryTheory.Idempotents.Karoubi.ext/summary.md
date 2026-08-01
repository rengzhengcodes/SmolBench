# CategoryTheory.Idempotents.Karoubi.ext   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Idempotents/Karoubi.lean`  

**Ground-truth tail (from k):**
```lean
simpa only [mk.injEq, heq_eq_eq, true_and, eqToHom_refl, comp_id, id_comp] using h_p
```

**True premises at k:** `heq_eq_eq`, `true_and`, `CategoryTheory.eqToHom_refl`, `CategoryTheory.Category.comp_id`, `CategoryTheory.Category.id_comp`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✓ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.2s, in=410, out=53)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
· rfl
· ext
  · exact h_p
  · apply (cancel_mono p✝).1
    rw [assoc, idem✝]
    exact idem✝¹
· exact proof_irrel _ _
```

**lean_error:** tail step 2/8 ('· rfl'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=380, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
ext
rw [← Category.comp_id p✝¹, ← h_p, Category.assoc, idem✝¹, Category.comp_id, idem✝, eqToHom_refl, Category.comp_id]
```

**lean_error:** tail step 2/3 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=399, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Subtype.ext
exact rfl
exact (idem✝¹.trans (h_p.symm ▸ idem✝)).symm
```

**lean_error:** tail step 1/3 ('apply Subtype.ext'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=955, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [heq_eq_eq, true_and, CategoryTheory.eqToHom_refl]
simp_rw [CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp]
rfl
```

**lean_error:** tail step 1/3 ('simp_rw [heq_eq_eq, true_and, CategoryTheory.eqToHom_refl]'): simp made no progress

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=923, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr
ext
simp only [CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p
simp only [h_p]
```

**lean_error:** tail step 2/4 ('ext'): no applicable extensionality theorem found for

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.3s, verify 0.2s, in=944, out=45)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [heq_eq_eq, true_and, CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p
cases h_p
```

**final state (truncated):**
```
case mk.mk.refl
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝ : X✝ ⟶ X✝
idem✝¹ idem✝ : p✝ ≫ p✝ = p✝
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 1.0s, in=2096, out=41)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [heq_eq_eq],
simp [true_and],
simp [CategoryTheory.eqToHom_refl],
simp [CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp],
congr,
rfl
```

**lean_error:** tail step 1/6 ('simp [heq_eq_eq],'): <stdin>:1:16: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.5s, in=2071, out=44)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
congr
  simp only [true_and, heq_eq_eq]
  simp only [← h_p, CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp]
```

**lean_error:** tail step 2/3 ('simp only [true_and, heq_eq_eq]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=2085, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply heq_eq_eq
simp [h_p]
```

**lean_error:** tail step 1/2 ('apply heq_eq_eq'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=2122, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [CategoryTheory.eqToHom_refl]
simp only [id_comp, comp_id, true_and]
congr with ⟨⟩
```

**lean_error:** tail step 1/3 ('simp_rw [CategoryTheory.eqToHom_refl]'): simp made no progress

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.3s, in=2222, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
congr
simp only [CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p
simp only [h_p]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 5.4s, verify 0.1s, in=2111, out=302)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
congr
```

**final state (truncated):**
```
case mk.mk.e_p
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```
