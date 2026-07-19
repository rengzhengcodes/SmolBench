# CategoryTheory.Adjunction.localization_counit_app   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Localization/Adjunction.lean`  

**Ground-truth tail (from k):**
```lean
apply Localization.η_app
```

**True premises at k:** `CategoryTheory.Adjunction.Localization.η_app`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ | ✘ · ✘ · |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ · ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | · · ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | · ✘ ✘ · | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 56.0s, verify 0.2s, in=592, out=2483)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [localization.adj_counit_app]
```

**lean_error:** tail step 1/1 ('rw [localization.adj_counit_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 65.5s, verify 0.1s, in=592, out=2879)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 88.0s, verify 0.1s, in=592, out=3917)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply adjunction.localization_counit
```

**lean_error:** tail step 1/1 ('apply adjunction.localization_counit'): unknown identifier 'adjunction.localization_counit'

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 156.6s, verify 0.2s, in=592, out=6960)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [localization.adjunction_counit, Category.assoc, ← Functor.map_comp, ← Category.assoc, CatCommSq.iso_inv_app_naturality]
```

**lean_error:** tail step 1/1 ('simp only [localization.adjunction_counit, Category.assoc, ← Functor.map_comp, ← Category.assoc, CatCommSq.iso_inv_app_naturality]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.9s, verify 0.2s, in=592, out=6)

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
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.2s, in=592, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [localization.counit_app]
```

**lean_error:** tail step 1/1 ('simp [localization.counit_app]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.2s, in=592, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [localization.counit_app]
```

**lean_error:** tail step 1/1 ('simp [localization.counit_app]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.4s, verify 0.1s, in=592, out=38)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [localization_counit_app, localization_adj_unit_app, Iso.app_inv, Iso.app_hom,
  Category.assoc, ← Functor.map_comp]
```

**lean_error:** tail step 1/2 ('simp only [localization_counit_app, localization_adj_unit_app, Iso.app_inv, Iso.app_hom,'): <stdin>:1:88: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.4s, verify 0.2s, in=592, out=257)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [adj.localization, adj.localization_counit_app]
```

**lean_error:** tail step 1/1 ('simp [adj.localization, adj.localization_counit_app]'): invalid 'simp', proposition expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 9.6s, verify 0.2s, in=592, out=263)

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
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.6s, verify 0.1s, in=592, out=296)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply localization_counit_naturality
```

**lean_error:** tail step 1/1 ('apply localization_counit_naturality'): unknown identifier 'localization_counit_naturality'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 21.6s, verify 0.2s, in=592, out=637)

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
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 92.5s, verify 0.2s, in=1035, out=4150)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [localization.η_app]
```

**lean_error:** tail step 1/1 ('rw [localization.η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 100.5s, verify 0.1s, in=1035, out=4542)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply η_app
```

**lean_error:** tail step 1/1 ('apply η_app'): unknown identifier 'η_app'

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 102.1s, verify 0.2s, in=1035, out=4626)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [η_app]
```

**lean_error:** tail step 1/1 ('rw [η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 140.2s, verify 0.2s, in=1035, out=6308)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [η_app]
```

**lean_error:** tail step 1/1 ('rw [η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=1035, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact η_app X₂
```

**lean_error:** tail step 1/1 ('exact η_app X₂'): unknown identifier 'η_app'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=1035, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact η_app X₂
```

**lean_error:** tail step 1/1 ('exact η_app X₂'): unknown identifier 'η_app'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.4s, verify 0.2s, in=1035, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Localization.η_app]
```

**final state (truncated):**
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=1035, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [η_app, localization_counit_app]
```

**lean_error:** tail step 1/1 ('simp only [η_app, localization_counit_app]'): unknown identifier 'η_app'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.9s, verify 0.1s, in=1035, out=218)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply η_app
```

**lean_error:** tail step 1/1 ('apply η_app'): unknown identifier 'η_app'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 11.7s, verify 0.1s, in=1035, out=330)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [CategoryTheory.Adjunction.Localization.η_app]
```

**lean_error:** tail step 1/1 ('simp only [CategoryTheory.Adjunction.Localization.η_app]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 14.0s, verify 0.1s, in=1035, out=404)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (η_app _).dual
```

**lean_error:** tail step 1/1 ('exact (η_app _).dual'): unknown identifier 'η_app'

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 33.7s, verify 0.1s, in=1035, out=1043)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [η]
```

**lean_error:** tail step 1/1 ('simp [η]'): unknown identifier 'η'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 173.7s, verify 0.1s, in=1718, out=5188)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply η_app
```

**lean_error:** tail step 1/1 ('apply η_app'): unknown identifier 'η_app'

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 176.8s, verify 0.2s, in=1718, out=3999)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [η_app]
```

**lean_error:** tail step 1/1 ('rw [η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 226.7s, verify 0.1s, in=1718, out=6580)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply η_app
```

**lean_error:** tail step 1/1 ('apply η_app'): unknown identifier 'η_app'

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 785.2s, verify 0.1s, in=1718, out=32768)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [← η_app]
ext
apply (L₂.map_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.counit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.unit.naturality
apply (L₂.map_strictly_full (adj.counit.app X₂)).left (W₂.of_is_iso (L₂.map (adj.unit.app X₂)))
intro h
simp only [← h]
clear h
apply adj.counit.naturality
apply (L₂.map_strictly_full (adj.unit.app X₂)).left (W₂.of
```

**lean_error:** tail step 1/2028 ('simp only [← η_app]'): unknown identifier 'η_app'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.5s, verify 0.2s, in=1718, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Localization.η_app]
```

**final state (truncated):**
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.8s, verify 0.2s, in=1718, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Adjunction.localization, Adjunction.Localization.η_app]
```

**final state (truncated):**
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.5s, verify 0.1s, in=1718, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Localization.counit_app, Localization.η_app, Iso.inv_inv]
```

**lean_error:** tail step 1/1 ('simp only [Localization.counit_app, Localization.η_app, Iso.inv_inv]'): unknown identifier 'Localization.counit_app'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.5s, verify 0.1s, in=1718, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [adj.localization_counit_app, localizationAdj.η_app]
```

**lean_error:** tail step 1/1 ('simp only [adj.localization_counit_app, localizationAdj.η_app]'): invalid field notation, function 'CategoryTheory.Adjunction.localization_counit_app' does not have argument with type (CategoryTheory.Adjunction ...) that can be used, it must be explicit or implicit with a unique name

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 18.3s, verify 0.1s, in=1718, out=317)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (adjLocalization.η_app X₂).symm
```

**lean_error:** tail step 1/1 ('exact (adjLocalization.η_app X₂).symm'): unknown identifier 'adjLocalization.η_app'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 24.5s, verify 0.1s, in=1718, out=427)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [CategoryTheory.Adjunction.Localization.η_app]
```

**lean_error:** tail step 1/1 ('simp only [CategoryTheory.Adjunction.Localization.η_app]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 26.7s, verify 0.1s, in=1718, out=533)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [CategoryTheory.Adjunction.Localization.η_app]
```

**lean_error:** tail step 1/1 ('simp only [CategoryTheory.Adjunction.Localization.η_app]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 725.5s, verify 0.0s, in=1718, out=32768)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 82.3s, verify 0.2s, in=1742, out=3631)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [η_app]
```

**lean_error:** tail step 1/1 ('rw [η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 92.9s, verify 0.2s, in=1742, out=4171)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [η_app]
```

**lean_error:** tail step 1/1 ('rw [η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 102.4s, verify 0.2s, in=1742, out=4637)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [η_app]
```

**lean_error:** tail step 1/1 ('rw [η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 109.9s, verify 0.2s, in=1742, out=5011)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [η_app]
```

**lean_error:** tail step 1/1 ('rw [η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.2s, verify 0.2s, in=1742, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Localization.η_app]
```

**final state (truncated):**
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=1742, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact η_app X₂
```

**lean_error:** tail step 1/1 ('exact η_app X₂'): unknown identifier 'η_app'

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.2s, in=1742, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [localization.counit]
```

**lean_error:** tail step 1/1 ('simp [localization.counit]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.3s, verify 0.2s, in=1742, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Localization.η_app, localization]
```

**final state (truncated):**
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
...
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 14.8s, verify 0.3s, in=1742, out=429)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Adjunction.localization_counit_app, CategoryTheory.Adjunction.Localization.η_app]
```

**lean_error:** tail step 1/1 ('rw [Adjunction.localization_counit_app, CategoryTheory.Adjunction.Localization.η_app]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 15.3s, verify 0.1s, in=1742, out=448)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CategoryTheory.Adjunction.localization_counit_app]
```

**lean_error:** tail step 1/1 ('simp [CategoryTheory.Adjunction.localization_counit_app]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 15.9s, verify 0.2s, in=1742, out=469)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [localization_counit_app, η_app]
```

**lean_error:** tail step 1/1 ('rw [localization_counit_app, η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 55.7s, verify 0.1s, in=1742, out=1948)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [← adj.triangle_left_assoc, ← CategoryTheory.comp.assoc, η_app]
```

**lean_error:** tail step 1/1 ('simp only [← adj.triangle_left_assoc, ← CategoryTheory.comp.assoc, η_app]'): invalid field 'triangle_left_assoc', the environment does not contain 'CategoryTheory.Adjunction.triangle_left_assoc'
