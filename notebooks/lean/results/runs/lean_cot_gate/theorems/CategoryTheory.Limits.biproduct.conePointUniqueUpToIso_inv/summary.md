# CategoryTheory.Limits.biproduct.conePointUniqueUpToIso_inv   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
rw [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app,
  biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π, b.toCone_π_app, b.ι_π]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp`, `CategoryTheory.Limits.Bicone.toCone_π_app`, `CategoryTheory.Limits.biproduct.bicone_π`, `CategoryTheory.Limits.biproduct.ι_desc`, `CategoryTheory.Limits.biproduct.ι_π`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ · ✘ ✘ |
| `hint:2` | · ✘ ✘ ✘ | · ✘ ✘ · |
| `hint:3` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ · · | · ✘ · ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 219.0s, verify 0.2s, in=408, out=8740)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← category.assoc, iso.hom_inv_id, category.id_comp]
rw [← category.assoc, hb.desc_ι, category.assoc, (Bicone.toCone b).π.naturality, category.assoc, hb.ι_π]
simp [discrete.eq_iff]
```

**lean_error:** tail step 1/3 ('rw [← category.assoc, iso.hom_inv_id, category.id_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 226.1s, verify 0.2s, in=408, out=9046)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [hb.ι_π, hb.ι_π]
```

**lean_error:** tail step 1/1 ('rw [hb.ι_π, hb.ι_π]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 233.0s, verify 0.1s, in=408, out=9344)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h_desc := hb.isColimit.desc_self,
rw h_desc at ⊢,
simp only [comp_id],
rw IsLimit.conePointUniqueUpToIso_inv_π hb.isLimit (isLimit f) j' at ⊢,
simp only [category.assoc],
apply biproduct.ι_π,
apply biproduct.ι_π,
congr
```

**lean_error:** tail step 1/8 ('have h_desc := hb.isColimit.desc_self,'): <stdin>:1:37: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 249.5s, verify 0.1s, in=408, out=10032)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw hb.ι_π
rw hb.ι_π
```

**lean_error:** tail step 1/2 ('rw hb.ι_π'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=408, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [hb]
```

**lean_error:** tail step 1/1 ('simp [hb]'): invalid argument, variable is not a proposition or let-declaration

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=408, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 5.6s, verify 0.1s, in=408, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [hb.to_isLimit_eq]
```

**lean_error:** tail step 1/1 ('simp [hb.to_isLimit_eq]'): invalid field 'to_isLimit_eq', the environment does not contain 'CategoryTheory.Limits.Bicone.IsBilimit.to_isLimit_eq'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 70.4s, verify 0.1s, in=408, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [hb.desc_ι]
```

**lean_error:** tail step 1/1 ('simp [hb.desc_ι]'): invalid field 'desc_ι', the environment does not contain 'CategoryTheory.Limits.Bicone.IsBilimit.desc_ι'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 169.5s, verify 0.1s, in=1668, out=6582)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.ι_desc, biproduct.ι_π]
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

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 173.4s, verify 0.2s, in=1668, out=6729)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Category.assoc, hb.conePointUniqueUpToIso_inv_comp (isLimit f) j', Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_π]
rw [biproduct.ι_desc, Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_π]
```

**lean_error:** tail step 1/2 ("rw [Category.assoc, hb.conePointUniqueUpToIso_inv_comp (isLimit f) j', Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_π]"): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 210.5s, verify 0.2s, in=1668, out=8369)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f), Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_π]
rw [biproduct.ι_desc, Bicone.toCone_π_app, biproduct.ι_π]
```

**lean_error:** tail step 1/2 ('rw [IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f), Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_π]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 307.8s, verify 0.2s, in=1668, out=10613)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Category.assoc, conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f) j', Bicone.toCone_π_app, biproduct.ι_desc, Bicone.toCone_π_app]
apply biproduct.ι_π
```

**lean_error:** tail step 1/2 ("rw [Category.assoc, conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f) j', Bicone.toCone_π_app, biproduct.ι_desc, Bicone.toCone_π_app]"): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.8s, verify 0.1s, in=1668, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
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

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=1668, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [b.toCone_π_app, hb.bicone_π, biproduct.ι_desc]
```

**lean_error:** tail step 1/1 ('simp [b.toCone_π_app, hb.bicone_π, biproduct.ι_desc]'): invalid field 'bicone_π', the environment does not contain 'CategoryTheory.Limits.Bicone.IsBilimit.bicone_π'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=1668, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsLimit.conePointUniqueUpToIso_inv_comp, toCone_π_app, hb.ι_π]
```

**lean_error:** tail step 1/1 ('simp [IsLimit.conePointUniqueUpToIso_inv_comp, toCone_π_app, hb.ι_π]'): unknown identifier 'toCone_π_app'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 5.5s, verify 0.1s, in=1668, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
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

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 344.2s, verify 0.2s, in=3436, out=9365)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f) j', Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_desc]
simp [biproduct.ι_π]
```

**lean_error:** tail step 1/2 ("rw [IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f) j', Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_desc]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 348.6s, verify 0.9s, in=3436, out=9856)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Category.assoc]
rw [IsLimit.conePointUniqueUpToIso_inv_comp]
rw [Bicone.toCone_π_app]
rw [biproduct.bicone_π]
rw [biproduct.ι_desc]
rw [Bicone.toCone_π_app]
apply biproduct.ι_π
```

**lean_error:** tail step 7/7 ('apply biproduct.ι_π'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 355.6s, verify 0.2s, in=3436, out=8696)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f) j', Bicone.toCone_π_app, biproduct.ι_desc]
simp [biproduct.ι_π, Category.assoc]
```

**lean_error:** tail step 1/2 ("rw [IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f) j', Bicone.toCone_π_app, biproduct.ι_desc]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 358.2s, verify 0.3s, in=3436, out=8571)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π]
```

**lean_error:** tail step 1/1 ('simp only [assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π]'): unknown identifier 'assoc'

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.1s, verify 0.1s, in=3436, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
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

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.9s, verify 0.1s, in=3436, out=44)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.bicone_π,
  biproduct.ι_desc]
```

**lean_error:** tail step 1/2 ('simp [IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.bicone_π,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.1s, verify 0.1s, in=3436, out=54)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Category.assoc, toCone_π_app, biproduct.bicone_π, IsLimit.conePointUniqueUpToIso_inv_comp, biproduct.ι_desc, biproduct.ι_π]
```

**lean_error:** tail step 1/1 ('simp only [Category.assoc, toCone_π_app, biproduct.bicone_π, IsLimit.conePointUniqueUpToIso_inv_comp, biproduct.ι_desc, biproduct.ι_π]'): unknown identifier 'toCone_π_app'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.5s, verify 0.1s, in=3436, out=68)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app,
  biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π, if_pos, eqToHom_refl, comp_id]
```

**lean_error:** tail step 1/2 ('simp only [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app,'): <stdin>:1:88: unexpected end of input; expected ']'

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 252.9s, verify 0.2s, in=3469, out=10275)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [assoc, IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f), Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π]
```

**lean_error:** tail step 1/1 ('rw [assoc, IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f), Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 258.8s, verify 0.3s, in=3469, out=10561)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f), Bicone.toCone_π_app, biproduct.bicone_π]
rw [biproduct.ι_desc, Bicone.toCone_π_app, biproduct.bicone_π]
rw [biproduct.ι_π, biproduct.ι_π]
simp only [if_congr, eqToHom_trans, eqToHom_refl, comp_zero, zero_comp, if_true, if_false]
```

**lean_error:** tail step 2/4 ('rw [biproduct.ι_desc, Bicone.toCone_π_app, biproduct.bicone_π]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 273.4s, verify 0.1s, in=3469, out=11264)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app, biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π]
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

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 278.2s, verify 0.1s, in=3469, out=11495)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp hb.isLimit (isLimit f) j', Bicone.toCone_π_app, biproduct.ι_desc, biproduct.bicone_π, biproduct.ι_π]
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

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 0.6s, verify 0.1s, in=3469, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
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

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=3469, out=32)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [IsLimit.conePointUniqueUpToIso_inv_comp, toCone_π_app, hb.ι_π]
```

**lean_error:** tail step 1/1 ('simp [IsLimit.conePointUniqueUpToIso_inv_comp, toCone_π_app, hb.ι_π]'): unknown identifier 'toCone_π_app'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 70.3s, verify 0.1s, in=3469, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
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

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 70.5s, verify 0.1s, in=3469, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [hb.toCone_π_app]
```

**lean_error:** tail step 1/1 ('simp [hb.toCone_π_app]'): invalid field 'toCone_π_app', the environment does not contain 'CategoryTheory.Limits.Bicone.IsBilimit.toCone_π_app'
