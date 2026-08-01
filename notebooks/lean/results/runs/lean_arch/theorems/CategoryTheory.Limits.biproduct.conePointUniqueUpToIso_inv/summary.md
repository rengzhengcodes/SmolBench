# CategoryTheory.Limits.biproduct.conePointUniqueUpToIso_inv   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
rw [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app,
  biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π, b.toCone_π_app, b.ι_π]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp`, `CategoryTheory.Limits.Bicone.toCone_π_app`, `CategoryTheory.Limits.biproduct.bicone_π`, `CategoryTheory.Limits.biproduct.ι_desc`, `CategoryTheory.Limits.biproduct.ι_π`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 3.6s, in=437, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsLimit.conePointUniqueUpToIso_inv_comp]
rw [Category.assoc]
rw [Bicone.toCone_π_app]
rw [Bicone.toCone_π_app]
rw [Category.assoc]
rw [desc_fac]
```

**lean_error:** tail step 1/6 ('rw [IsLimit.conePointUniqueUpToIso_inv_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=403, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsLimit.conePointUniqueUpToIso_inv, IsLimit.fac]
simp [← Category.assoc, IsLimit.fac]
congr 1
simp [← Category.assoc]
congr 1
simp [← IsLimit.fac_assoc]
```

**lean_error:** tail step 1/6 ('simp [IsLimit.conePointUniqueUpToIso_inv, IsLimit.fac]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=426, out=83)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Category.assoc],
simp [IsLimit.conePointUniqueUpToIso_inv_comp],
simp [desc],
rw [Bicone.toCone_π_app],
dsimp,
simp [Bicone.IsBilimit.inv_π_app],
rw [←Category.assoc],
simp [Bicone.IsBilimit.ι_desc],
rw [Category.assoc],
simp,
```

**lean_error:** tail step 1/10 ('rw [Category.assoc],'): <stdin>:1:19: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 6.2s, verify 0.1s, in=1697, out=68)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f) j'],
rw [Bicone.toCone_π_app, biproduct.bicone_π],
rw [biproduct.ι_desc],
rw [biproduct.ι_π]
```

**lean_error:** tail step 1/4 ("rw [CategoryTheory.Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f) j'],"): <stdin>:1:101: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.5s, in=1658, out=90)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp, CategoryTheory.Limits.Bicone.toCone_π_app]
simp only [biproduct.ι_desc, CategoryTheory.Limits.Bicone.toCone_π_app]
congr
simp only [biproduct.ι_π]
split_ifs <;> simp_all only [eqToHom_refl, CategoryTheory.CategoryStruct.id_comp]
```

**lean_error:** tail step 4/5 ('simp only [biproduct.ι_π]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.7s, verify 0.1s, in=1686, out=56)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π, Category.assoc]
```

**final state (truncated):**
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 6.2s, verify 0.1s, in=3466, out=70)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.Category.assoc],
rw [IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f)],
rw [Bicone.toCone_π_app],
rw [biproduct.bicone_π],
rw [biproduct.ι_desc],
rw [biproduct.ι_π]
```

**lean_error:** tail step 1/6 ('rw [CategoryTheory.Category.assoc],'): <stdin>:1:34: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.4s, in=3436, out=74)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app]
split_ifs with h
· simp [← h]
· simp only [CategoryTheory.Limits.biproduct.ι_desc, CategoryTheory.Limits.biproduct.ι_π, h, zero_comp]
```

**lean_error:** tail step 2/4 ('split_ifs with h'): tactic 'split_ifs' failed, no if-then-else conditions to split

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.4s, in=3455, out=76)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.bicone_π]
rw [CategoryTheory.Category.assoc, biproduct.ι_desc, Bicone.toCone_π_app, biproduct.bicone_π]
```

**lean_error:** tail step 2/2 ('rw [CategoryTheory.Category.assoc, biproduct.ι_desc, Bicone.toCone_π_app, biproduct.bicone_π]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=3495, out=109)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.Category.assoc],
rw [IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f)],
rw [Bicone.toCone_π_app],
rw [biproduct.bicone_π],
rw [biproduct.ι_desc],
rw [biproduct.ι_π],
split_ifs,
simp only [dite_eq_ite, ite_eq_left_iff],
tauto,
simp only [dite_eq_ite, ite_eq_right_iff],
tauto
```

**lean_error:** tail step 1/11 ('rw [CategoryTheory.Category.assoc],'): <stdin>:1:34: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=3659, out=78)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp,
  Bicone.toCone_π_app]
dsimp only [biproduct.bicone_π, biproduct.ι_desc]
rw [biproduct.ι_π]
split_ifs with h
· simp [h]
· simp only [zero_comp]
```

**lean_error:** tail step 1/7 ('simp only [CategoryTheory.Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp,'): <stdin>:1:82: unexpected end of input; expected ']'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 524.7s, verify 0.1s, in=3484, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_π, dite_eq_ite, if_true, eqToHom_map, eqToIso_refl, comp_id, biproduct.ι_desc]
```

**lean_error:** tail step 1/1 ('simp only [CategoryTheory.Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_π, dite_eq_ite, if_true, eqToHom_map, eqToIso_refl, comp_id, biproduct.ι_desc]'): unknown identifier 'comp_id'
