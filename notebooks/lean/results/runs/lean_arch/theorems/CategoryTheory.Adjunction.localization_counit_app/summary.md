# CategoryTheory.Adjunction.localization_counit_app   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Localization/Adjunction.lean`  

**Ground-truth tail (from k):**
```lean
apply Localization.η_app
```

**True premises at k:** `CategoryTheory.Adjunction.Localization.η_app`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.2s, in=618, out=79)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [localization.counit_app, Functor.map_comp]
congr 1
erw [CatCommSq.iso_inv_app, CatCommSq.iso_inv_app]
dsimp
rw [Functor.map_comp, Functor.map_comp]
erw [adjunction_counit_app_functor_comp]
congr 2
erw [CatCommSq.iso_inv_app]
```

**lean_error:** tail step 1/8 ('erw [localization.counit_app, Functor.map_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=597, out=88)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [localization.counit_app]
simp only [Functor.comp_map, assoc, ← G'.map_comp, ← CatCommSq.iso_inv_app_hom_app_assoc]
rw [← CatCommSq.iso_inv_app_hom_app, ← assoc, adj.counit_naturality]
simp only [L₂.map_comp, assoc]
rw [CatCommSq.iso_hom_app_inv_app, id_comp]
rfl
```

**lean_error:** tail step 1/6 ('rw [localization.counit_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 16.0s, verify 0.1s, in=607, out=955)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply iso.inv_comp_eq
apply Functor.map_comp
apply iso.inv_comp_eq
```

**lean_error:** tail step 1/3 ('apply iso.inv_comp_eq'): unknown identifier 'iso.inv_comp_eq'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=1059, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [counit_app, η_app]
```

**lean_error:** tail step 1/1 ('rw [counit_app, η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1037, out=120)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← CategoryTheory.Adjunction.Localization.η_app]
simp only [localization_counit, NatTrans.comp_app]
rw [← G'.map_comp, ← G'.map_comp, CatCommSq.iso_inv_app_hom_app_assoc]
simp only [Functor.map_id, comp_id, assoc]
rw [CatCommSq.iso_inv_app_hom_app, ← L₂.map_comp_assoc]
simp only [adj.counit_naturality, ← assoc, ← Functor.map_comp]
rw [adj.left_triangle, Functor.map_id, id_comp]
rfl
```

**lean_error:** tail step 1/8 ('rw [← CategoryTheory.Adjunction.Localization.η_app]'): failed to synthesize

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=1048, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact η_app X₂
```

**lean_error:** tail step 1/1 ('exact η_app X₂'): unknown identifier 'η_app'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=1731, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [counit_app, η_app]
congr
```

**lean_error:** tail step 1/2 ('rw [counit_app, η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.3s, in=1717, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← η_app]
rfl
```

**lean_error:** tail step 1/2 ('rw [← η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=1720, out=118)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
letI : Lifting L₂ W₂ ((F ⋙ G) ⋙ L₂) (F' ⋙ G') :=
  Lifting.mk (CatCommSq.hComp F G L₂ L₁ L₂ F' G').iso'.symm
simp only [localization_counit, liftNatTrans_app, Lifting.iso, Iso.symm, CatCommSq.hComp_iso'_inv_app,
  whiskerRight_app, Lifting.id_iso', Functor.rightUnitor_inv_app, comp_id, assoc]
```

**lean_error:** tail step 1/4 ("letI : Lifting L₂ W₂ ((F ⋙ G) ⋙ L₂) (F' ⋙ G') :="): <stdin>:1:48: unexpected end of input

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1763, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Localization.counit_app, η_app]
```

**lean_error:** tail step 1/1 ('rw [Localization.counit_app, η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.4s, in=1818, out=46)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← η_app]
symm
exact NatTrans.naturality (localization adj L₁ W₁ L₂ W₂ G' F').counit (L₂.map (adj.unit.app X₂))
```

**lean_error:** tail step 1/3 ('rw [← η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1752, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact η_app X₂
```

**lean_error:** tail step 1/1 ('exact η_app X₂'): unknown identifier 'η_app'
