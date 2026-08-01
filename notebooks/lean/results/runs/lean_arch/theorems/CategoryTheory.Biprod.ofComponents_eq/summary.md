# CategoryTheory.Biprod.ofComponents_eq   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
ext <;>
  simp only [Category.comp_id, biprod.inr_fst, biprod.inr_snd, biprod.inl_snd, add_zero, zero_add,
    Biprod.inl_ofComponents, Biprod.inr_ofComponents, eq_self_iff_true, Category.assoc,
    comp_zero, biprod.inl_fst, Preadditive.add_comp]
```

**True premises at k:** `CategoryTheory.Category.comp_id`, `CategoryTheory.Limits.biprod.inr_fst`, `CategoryTheory.Limits.biprod.inr_snd`, `CategoryTheory.Limits.biprod.inl_snd`, `add_zero`, `zero_add`, `CategoryTheory.Biprod.inl_ofComponents`, `CategoryTheory.Biprod.inr_ofComponents`, `eq_self_iff_true`, `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.comp_zero`, `CategoryTheory.Limits.biprod.inl_fst`, `CategoryTheory.Preadditive.add_comp`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | · | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.5s, in=446, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
· simp only [ofComponents_comp_inl, biprod.inl_fst, biprod.inl_snd]
· simp only [ofComponents_comp_inr, biprod.inr_fst, biprod.inr_snd]
```

**lean_error:** tail step 2/3 ('· simp only [ofComponents_comp_inl, biprod.inl_fst, biprod.inl_snd]'): unknown identifier 'ofComponents_comp_inl'

### `stepk:1` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 2.6s, verify 0.9s, in=420, out=59)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp only [ofComponents, biprod.lift_desc, Category.assoc, biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, comp_zero, zero_comp, add_zero, zero_add]
```

**final state (truncated):**
```
case h₀.h₀
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : Preadditive C
inst✝ : HasBinaryBiproducts C
X₁ X₂ Y₁ Y₂ : C
...
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.5s, in=435, out=99)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biprod.hom_ext
rotate_left
apply biprod.inl_injective
simp only [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd]
apply biprod.hom_ext
rotate_left
apply biprod.inr_injective
simp only [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd]
```

**lean_error:** tail step 3/8 ('apply biprod.inl_injective'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.5s, in=2310, out=79)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
· simp only [CategoryTheory.Biprod.inl_ofComponents, CategoryTheory.Limits.biprod.inl_fst,
  CategoryTheory.Limits.biprod.inl_snd]
· simp only [CategoryTheory.Biprod.inr_ofComponents, CategoryTheory.Limits.biprod.inr_fst,
  CategoryTheory.Limits.biprod.inr_snd]
```

**lean_error:** tail step 2/5 ('· simp only [CategoryTheory.Biprod.inl_ofComponents, CategoryTheory.Limits.biprod.inl_fst,'): <stdin>:1:90: unexpected end of input; expected ']'

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.5s, verify 0.3s, in=2296, out=73)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← CategoryTheory.Category.assoc, biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, CategoryTheory.Limits.comp_zero, CategoryTheory.Preadditive.add_comp, CategoryTheory.Biprod.inl_ofComponents, CategoryTheory.Biprod.inr_ofComponents]
```

**lean_error:** tail step 1/1 ('simp [← CategoryTheory.Category.assoc, biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, CategoryTheory.Limits.comp_zero, CategoryTheory.Preadditive.add_comp, CategoryTheory.Biprod.inl_ofComponents, CategoryTheory.Biprod.inr_ofComponents]'): tactic 'simp' failed, nested

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=2299, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Biprod.ofComponents_eq
```

**lean_error:** tail step 1/1 ('apply Biprod.ofComponents_eq'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 1.0s, in=2925, out=109)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
simp
rw [CategoryTheory.Biprod.inl_ofComponents, CategoryTheory.Biprod.inr_ofComponents]
simp only [CategoryTheory.Category.assoc]
rw [biprod.inl_fst, biprod.inr_fst, biprod.inl_snd, biprod.inr_snd]
simp only [CategoryTheory.Category.comp_id, comp_zero, zero_comp]
simp only [add_zero, zero_add]
simp only [eq_self_iff_true]
simp only [CategoryTheory.Preadditive.add_comp]
done
```

**lean_error:** tail step 3/10 ('rw [CategoryTheory.Biprod.inl_ofComponents, CategoryTheory.Biprod.inr_ofComponents]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.6s, in=2911, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← CategoryTheory.Category.assoc]
aesop_cat
```

**lean_error:** tail step 1/2 ('simp [← CategoryTheory.Category.assoc]'): tactic 'simp' failed, nested error:

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=2914, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Biprod.ofComponents_eq
```

**lean_error:** tail step 1/1 ('apply Biprod.ofComponents_eq'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.6s, in=2949, out=121)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext
· simp only [Biprod.inl_ofComponents, Biprod.inr_ofComponents]
· simp only [Biprod.inl_ofComponents, Biprod.inr_ofComponents]
· simp only [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, comp_zero, add_zero, zero_add]
· simp only [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, comp_zero, add_zero, zero_add]
```

**lean_error:** tail step 2/5 ('· simp only [Biprod.inl_ofComponents, Biprod.inr_ofComponents]'): unsolved goals

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 1.5s, in=3005, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext
  simp
  simp
  simp
  simp
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=2938, out=83)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Biprod.hom_ext
apply Biprod.inl_ext
simp [← Biprod.inl_ofComponents, biprod.inl_fst, biprod.inl_snd, add_zero, zero_add]
apply Biprod.inr_ext
simp [← Biprod.inr_ofComponents, biprod.inr_fst, biprod.inr_snd, add_zero, zero_add]
```

**lean_error:** tail step 1/5 ('apply Biprod.hom_ext'): unknown identifier 'Biprod.hom_ext'
