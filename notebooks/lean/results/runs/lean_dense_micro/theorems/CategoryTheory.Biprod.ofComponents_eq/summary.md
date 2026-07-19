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

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ · | ✓ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✓ | ✘ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=446, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ofComponents_eq]
ext
all_goals { simp only [category.assoc] }
```

**lean_error:** tail step 1/3 ('rw [ofComponents_eq]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.6s, verify 0.6s, in=446, out=41)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
· rw [biprod.inl_fst_assoc, biprod.inl_snd_assoc]
· rw [biprod.inr_fst_assoc, biprod.inr_snd_assoc]
```

**lean_error:** tail step 2/3 ('· rw [biprod.inl_fst_assoc, biprod.inl_snd_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.4s, in=446, out=58)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr 1
· apply biprod.hom_ext
· apply biprod.hom_ext
all_goals { simp only [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, category.assoc] }
```

**lean_error:** tail step 2/4 ('· apply biprod.hom_ext'): unsolved goals

### `stepk:1` · llama-31-405b-base · rollout 3 → **incomplete**  (gen 2.5s, verify 1.0s, in=446, out=73)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
· simp only [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, ofComponents_eq]
· simp only [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, ofComponents_eq]
```

**final state (truncated):**
```
case h₁.h₀
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : Preadditive C
inst✝ : HasBinaryBiproducts C
X₁ X₂ Y₁ Y₂ : C
...
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 0.8s, verify 0.3s, in=446, out=4)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=446, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [biprod.ext]
```

**lean_error:** tail step 1/1 ('simp [biprod.ext]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.1s, in=446, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [biprod.ext]
```

**lean_error:** tail step 1/1 ('simp [biprod.ext]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=446, out=67)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [← cancel_mono biprod.inl, ← cancel_mono biprod.inr, ← cancel_epi biprod.fst, ← cancel_epi biprod.snd,
  biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, ofComponents_eq]
```

**lean_error:** tail step 1/2 ('simp only [← cancel_mono biprod.inl, ← cancel_mono biprod.inr, ← cancel_epi biprod.fst, ← cancel_epi biprod.snd,'): <stdin>:1:112: unexpected end of input; expected ']'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.5s, verify 0.5s, in=2310, out=79)

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

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 3.9s, verify 0.5s, in=2310, out=81)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
· simp only [Biprod.inl_ofComponents, comp_id, assoc, biprod.inl_fst, biprod.inl_snd, add_zero, zero_add, comp_zero]
· simp only [Biprod.inr_ofComponents, comp_id, assoc, biprod.inr_fst, biprod.inr_snd, add_zero, zero_add, comp_zero]
```

**lean_error:** tail step 2/3 ('· simp only [Biprod.inl_ofComponents, comp_id, assoc, biprod.inl_fst, biprod.inl_snd, add_zero, zero_add, comp_zero]'): unknown identifier 'comp_id'

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 4.4s, verify 0.1s, in=2310, out=89)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext; simp; erw [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd];
  simp; erw [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd];
  exact add_zero _;
  exact zero_add _;
  exact add_zero _;
  exact zero_add _
```

**lean_error:** tail step 1/6 ('ext; simp; erw [biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd];'): <stdin>:1:3: expected end of input

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 4.5s, verify 1.4s, in=2310, out=93)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
simp [Biprod.ofComponents]
simp [Biprod.inl_ofComponents]
simp [Biprod.inr_ofComponents]
simp [biprod.inl_fst]
simp [biprod.inr_fst]
simp [biprod.inl_snd]
simp [biprod.inr_snd]
simp [comp_zero]
simp [add_zero]
simp [zero_add]
simp [assoc]
simp [comp_id]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.7s, verify 0.1s, in=2310, out=4)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext; simp
```

**lean_error:** tail step 1/1 ('ext; simp'): <stdin>:1:3: expected end of input

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.1s, verify 0.3s, in=2310, out=4)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
aesop_cat
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.2s, in=2310, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext <;> simp
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 2.9s, verify 0.1s, in=2310, out=60)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext <;>
  simp only [inl_ofComponents, inr_ofComponents, assoc, comp_zero, comp_add,
    zero_add, add_zero, biprod.inr_fst, biprod.inr_snd, biprod.inl_snd, biprod.inl_fst]
```

**lean_error:** tail step 1/3 ('ext <;>'): <stdin>:1:7: unexpected end of input; expected '['
