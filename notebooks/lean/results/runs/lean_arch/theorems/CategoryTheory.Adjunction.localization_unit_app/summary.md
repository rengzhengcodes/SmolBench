# CategoryTheory.Adjunction.localization_unit_app   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Localization/Adjunction.lean`  

**Ground-truth tail (from k):**
```lean
apply Localization.ε_app
```

**True premises at k:** `CategoryTheory.Adjunction.Localization.ε_app`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.3s, in=610, out=60)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [localization.unit_app, Functor.map_comp, CatCommSq.iso_hom_app, Functor.map_comp]
simp only [adjunction.unit_naturality, Category.assoc]
erw [CatCommSq.iso_hom_app]
simp only [Functor.map_id, Category.comp_id]
```

**lean_error:** tail step 1/4 ('erw [localization.unit_app, Functor.map_comp, CatCommSq.iso_hom_app, Functor.map_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 1.1s, in=589, out=76)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [localization.unit_app]
simp only [Functor.comp_map, Iso.hom_inv_app, Functor.map_comp, assoc, ← L₁.map_comp, ← F'.map_comp]
congr 1
simp only [CatCommSq.iso_hom_app, ← assoc]
congr 1
simp only [adj.unit_naturality_assoc]
rfl
```

**lean_error:** tail step 1/7 ('rw [localization.unit_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=599, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply iso.hom_inv_id_app
apply category.comp_id
```

**lean_error:** tail step 1/2 ('apply iso.hom_inv_id_app'): unknown identifier 'iso.hom_inv_id_app'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=1067, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [unit_app, ε_app]
```

**lean_error:** tail step 1/1 ('rw [unit_app, ε_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1050, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← CategoryTheory.Adjunction.Localization.ε_app]
simp only [localization, Adjunction.unit, NatTrans.comp_app]
```

**lean_error:** tail step 1/2 ('rw [← CategoryTheory.Adjunction.Localization.ε_app]'): failed to synthesize

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1056, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ε_app]
```

**lean_error:** tail step 1/1 ('simp only [ε_app]'): unknown identifier 'ε_app'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=1739, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Localization.unit_app, ε_app]
```

**lean_error:** tail step 1/1 ('rw [Localization.unit_app, ε_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.2s, in=1730, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← ε_app]
rfl
```

**lean_error:** tail step 1/2 ('rw [← ε_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1728, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ε_app X₁
```

**lean_error:** tail step 1/1 ('exact ε_app X₁'): unknown identifier 'ε_app'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.7s, in=1771, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Localization.unit, ε_app]
```

**lean_error:** tail step 1/1 ('rw [Localization.unit, ε_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=1831, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [localization_unit]
exact ε_app X₁
```

**lean_error:** tail step 1/2 ('rw [localization_unit]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=1760, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ε_app X₁
```

**lean_error:** tail step 1/1 ('exact ε_app X₁'): unknown identifier 'ε_app'
