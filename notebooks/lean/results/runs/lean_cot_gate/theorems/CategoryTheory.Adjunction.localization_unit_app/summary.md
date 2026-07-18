# CategoryTheory.Adjunction.localization_unit_app   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Localization/Adjunction.lean`  

**Ground-truth tail (from k):**
```lean
apply Localization.ε_app
```

**True premises at k:** `CategoryTheory.Adjunction.Localization.ε_app`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 135.2s, verify 0.1s, in=584, out=6117)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply localization_adj_unit_app
```

**lean_error:** tail step 1/1 ('apply localization_adj_unit_app'): unknown identifier 'localization_adj_unit_app'

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 196.7s, verify 0.1s, in=584, out=9064)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CatCommSq.iso.hom_app, localization.adj_unit]
refl
```

**lean_error:** tail step 1/2 ('simp [CatCommSq.iso.hom_app, localization.adj_unit]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 200.2s, verify 0.2s, in=584, out=9219)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [localization.adjunction_unit_app]
```

**lean_error:** tail step 1/1 ('rw [localization.adjunction_unit_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 217.4s, verify 0.1s, in=584, out=9995)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
rw [Category.assoc, Category.assoc]
apply (L₂.reflects_isomorphisms W₂).1
apply W₁.eq_of_comp_eq
apply iso.inv_comp_eq
rw [Category.assoc, Category.assoc]
dsimp only [Functor.comp_obj, Functor.comp_map]
rw [← F'.map_comp, ← G'.map_comp]
rw [CatCommSq.iso_hom_app, CatCommSq.iso_hom_app, CatCommSq.iso_inv_app, CatCommSq.iso_inv_app]
rw [adjunction.unit_naturality]
rw [Category.id_comp, Category.comp_id]
```

**lean_error:** tail step 1/11 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.5s, verify 0.2s, in=584, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_6, u_1} C₁
inst✝⁶ : Category.{u_8, u_2} C₂
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 4.6s, verify 0.2s, in=584, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [localization.unit_app]
```

**lean_error:** tail step 1/1 ('simp [localization.unit_app]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 6.2s, verify 0.1s, in=584, out=51)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [adjunction.localization.unit_app, Iso.app_inv, Iso.app_hom, Functor.associator_naturality,
  Functor.associator_inv_naturality, Functor.id_map, Iso.inv_hom_id_app_assoc]
```

**lean_error:** tail step 1/2 ('simp only [adjunction.localization.unit_app, Iso.app_inv, Iso.app_hom, Functor.associator_naturality,'): <stdin>:1:101: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 70.3s, verify 0.2s, in=584, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [localization.unit_app]
```

**lean_error:** tail step 1/1 ('simp [localization.unit_app]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 77.7s, verify 0.1s, in=1041, out=3480)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply ε_app
```

**lean_error:** tail step 1/1 ('apply ε_app'): unknown identifier 'ε_app'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 110.1s, verify 0.2s, in=1041, out=4994)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Adjunction.Localization.ε_app]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.Adjunction.Localization.ε_app]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 132.3s, verify 0.1s, in=1041, out=5994)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply ε_app
```

**lean_error:** tail step 1/1 ('apply ε_app'): unknown identifier 'ε_app'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 140.1s, verify 0.1s, in=1041, out=6323)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ε_app]
```

**lean_error:** tail step 1/1 ('simp [ε_app]'): unknown identifier 'ε_app'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=1041, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Localization.unit, Iso.app_hom]
```

**lean_error:** tail step 1/1 ('simp only [Localization.unit, Iso.app_hom]'): unknown identifier 'Localization.unit'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=1041, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [localization, LocalizationAdjunction.unit, ε_app]
```

**lean_error:** tail step 1/1 ('simp only [localization, LocalizationAdjunction.unit, ε_app]'): unknown identifier 'LocalizationAdjunction.unit'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=1041, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [unit, ε_app]
```

**lean_error:** tail step 1/1 ('simp [unit, ε_app]'): unknown identifier 'ε_app'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=1041, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Localization.unit, ε_app]
```

**lean_error:** tail step 1/1 ('simp only [Localization.unit, ε_app]'): unknown identifier 'Localization.unit'

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 148.0s, verify 0.1s, in=1724, out=2822)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ε_app X₁
```

**lean_error:** tail step 1/1 ('exact ε_app X₁'): unknown identifier 'ε_app'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 151.7s, verify 0.1s, in=1724, out=3938)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply ε_app
```

**lean_error:** tail step 1/1 ('apply ε_app'): unknown identifier 'ε_app'

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 230.5s, verify 0.1s, in=1724, out=6597)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply ε_app
```

**lean_error:** tail step 1/1 ('apply ε_app'): unknown identifier 'ε_app'

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 230.8s, verify 0.2s, in=1724, out=7099)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [ε_app]
```

**lean_error:** tail step 1/1 ('rw [ε_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1724, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Localization.unit, localizationAdjunction_unit_app, ε_app]
```

**lean_error:** tail step 1/1 ('simp only [Localization.unit, localizationAdjunction_unit_app, ε_app]'): unknown identifier 'Localization.unit'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=1724, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [unit, ε_app]
```

**lean_error:** tail step 1/1 ('simp [unit, ε_app]'): unknown identifier 'ε_app'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1724, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Localization.unit, Iso.app_hom, localization_unit_app, ε_app]
```

**lean_error:** tail step 1/1 ('simp only [Localization.unit, Iso.app_hom, localization_unit_app, ε_app]'): unknown identifier 'Localization.unit'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=1724, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [localization, LocalizationAdjunction.unit, liftNatTrans_app, iso'_hom_app, assoc]
```

**lean_error:** tail step 1/1 ("simp only [localization, LocalizationAdjunction.unit, liftNatTrans_app, iso'_hom_app, assoc]"): unknown identifier 'LocalizationAdjunction.unit'

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 66.5s, verify 0.2s, in=1748, out=2969)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ε_app]
```

**lean_error:** tail step 1/1 ('rw [ε_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 87.2s, verify 0.1s, in=1748, out=3902)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ε_app]
```

**lean_error:** tail step 1/1 ('simp only [ε_app]'): unknown identifier 'ε_app'

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 88.6s, verify 0.2s, in=1748, out=3970)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.Adjunction.Localization.ε_app]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.Adjunction.Localization.ε_app]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 121.4s, verify 0.2s, in=1748, out=5508)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← ε_app]
```

**lean_error:** tail step 1/1 ('rw [← ε_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=1748, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [unit_app, ε_app]
```

**lean_error:** tail step 1/1 ('simp [unit_app, ε_app]'): unknown identifier 'unit_app'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=1748, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [unit, ε_app]
```

**lean_error:** tail step 1/1 ('simp [unit, ε_app]'): unknown identifier 'ε_app'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=1748, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [unit, ε_app]
```

**lean_error:** tail step 1/1 ('simp only [unit, ε_app]'): unknown identifier 'ε_app'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 5.5s, verify 0.1s, in=1748, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [unit, ε_app]
```

**lean_error:** tail step 1/1 ('simp only [unit, ε_app]'): unknown identifier 'ε_app'
