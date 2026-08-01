# CategoryTheory.Limits.biproduct.lift_desc   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc, comp_dite,
  dite_comp]
```

**True premises at k:** `CategoryTheory.Limits.biproduct.lift_eq`, `CategoryTheory.Limits.biproduct.desc_eq`, `CategoryTheory.Preadditive.comp_sum`, `CategoryTheory.Preadditive.sum_comp`, `CategoryTheory.Limits.biproduct.ι_π_assoc`, `CategoryTheory.comp_dite`, `CategoryTheory.dite_comp`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | · | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 11.8s, verify 0.1s, in=323, out=394)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [lift_desc]
ext
simp only [biproduct.ι_desc_assoc]
rw [Finset.sum_eq_sum_of_bijection]
  · simp only [Finset.sum_univ_eq_sum_of_bijection]
  · exact fun j => j
  · simp only [Function.LeftInverse.injective]
    exact fun j => Finset.mem_univ _
  · simp only [Function.RightInverse.surjective]
    exact fun j => Finset.mem_univ _
  · simp only [Finset.sum_univ_eq_sum_of_bijection]
  · exact fun j => j
  · simp only [Function.LeftInverse.injective]
    exact fun j => Finset.mem_univ _
  · simp only [Function.RightInverse.surjective]
    exact fun j => Finset.mem_univ _
  · simp only [Finset.sum_univ_eq_sum_of_bijection]
  · exact fun j => j
  · simp only [Function.LeftInverse.injective]
    exact fun j => Finset.mem_univ _
  · simp only [Function.RightInverse.surjective]
    exact fun j => Finset.mem_univ _ 
rw [Finset.sum_eq_sum_of_bijection]
  · simp only [Finset.sum_univ_eq_sum_of_bijection]
  · exact fun j => j
  · simp only [Function.LeftInverse.injective]
    exact fun j => Finset.mem_univ _
  · simp only [Function.RightInverse.surjective]
    exact fun j => Finset.mem_univ _
  · simp only [Finset.sum_univ_eq_sum_of_bijection]
  · exact fun j => j
  · simp only [Function.LeftInverse.injective]
    exact fun j => Finset.mem_univ _
  · simp only [Function.RightInverse.surjective]
    exact fun j => Finset.mem_univ _
```

**lean_error:** tail step 1/35 ('rw [lift_desc]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=295, out=77)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp only [biproduct.lift_desc, Category.assoc, biproduct.matrix, Matrix.cons_val_zero,
  Matrix.head_cons, dite_comp, comp_zero, Matrix.empty_val', zero_comp, Finset.sum_dite,
  Finset.sum_const_zero, Finset.sum_congr, dite_eq_left_iff, dite_eq_right_iff]
aesop_cat
```

**lean_error:** tail step 1/5 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 37.8s, verify 0.2s, in=312, out=2257)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biproduct.hom_ext
intro j
simp [lift_π, desc_ι, comp_sum, sum_comp]
```

**lean_error:** tail step 1/3 ('apply biproduct.hom_ext'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.2s, in=1810, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [lift_eq, desc_eq, comp_sum, sum_comp]
ext
simp [ι_π_assoc, comp_dite, dite_comp]
```

**lean_error:** tail step 1/3 ('rw [lift_eq, desc_eq, comp_sum, sum_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.3s, in=1774, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
simp [sum_comp, comp_sum, biproduct.ι_π_assoc]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 80.2s, verify 2.7s, in=1799, out=4892)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Eq.trans
exact biproduct.lift_eq
apply Eq.trans
exact sum_comp (Finset.univ) _ (desc h)
apply Eq.trans
exact sum_congr (Finset.univ) (λ j, _)
focus 1
apply Eq.trans
exact comp_sum (Finset.univ) (g j ≫ biproduct.ι f j) (λ k, biproduct.π f k ≫ h k)
apply Eq.trans
exact sum_congr (Finset.univ) (λ k, _)
focus 1
apply Eq.trans
exact Category.assoc _ _ _
apply Eq.trans
exact biproduct.ι_π_assoc
apply Eq.trans
exact comp_dite
apply Eq.trans
exact dite_comp
apply Eq.trans
exact if_pos
apply Eq.refl
done
done
done
```

**lean_error:** tail step 2/26 ('exact biproduct.lift_eq'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 2.9s, in=2549, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [lift_eq, desc_eq, comp_sum, sum_comp]
ext
simp [ι_π_assoc, comp_dite, dite_comp]
```

**lean_error:** tail step 1/3 ('rw [lift_eq, desc_eq, comp_sum, sum_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.4s, in=2515, out=93)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.biproduct.lift_eq, CategoryTheory.Limits.biproduct.desc_eq]
simp only [CategoryTheory.Preadditive.sum_comp, CategoryTheory.Preadditive.comp_sum, Category.assoc]
simp only [← Category.assoc, biproduct.ι_π, comp_dite, zero_comp, Finset.sum_dite_eq', Finset.mem_univ, dite_eq_if, if_true]
aesop_cat
```

**lean_error:** tail step 3/4 ("simp only [← Category.assoc, biproduct.ι_π, comp_dite, zero_comp, Finset.sum_dite_eq', Finset.mem_univ, dite_eq_if, if_true]"): unknown identifier 'dite_eq_if'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=2538, out=65)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext j
simp only [sum_comp, biproduct.ι_π, comp_dite, biproduct.lift_π, Category.assoc, comp_zero, Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl, Category.comp_id, if_true]
```

**lean_error:** tail step 1/2 ('ext j'): no applicable extensionality theorem found for

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 0.2s, in=2572, out=32)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [lift_eq, desc_eq, comp_sum, sum_comp]
ext
simp [ι_π_assoc, comp_dite, dite_comp]
```

**lean_error:** tail step 1/3 ('rw [lift_eq, desc_eq, comp_sum, sum_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.4s, in=2622, out=59)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
simp only [Category.assoc, sum_comp, comp_sum]
rw [← sum_comp, ← comp_sum]
simp only [Category.assoc]
congr
ext j
simp only [Category.assoc]
```

**lean_error:** tail step 3/7 ('rw [← sum_comp, ← comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 70.5s, verify 4.4s, in=2561, out=4284)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq, sum_comp, comp_sum]
simp
```

**lean_error:** tail step 1/2 ('rw [biproduct.lift_eq, biproduct.desc_eq, sum_comp, comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
