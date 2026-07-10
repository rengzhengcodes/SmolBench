# CategoryTheory.frobeniusMorphism_mate   (k=13, 14 tactics total)

file: `Mathlib/CategoryTheory/Closed/Functor.lean`  

**Ground-truth tail (from k):**
```lean
simp
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✓ | ✘ | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=471, out=59)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [prodComparison_component, assoc, prod.map_snd, comp_id],
rw [prod.map_snd, L.map_comp, assoc, h.counit.naturality, comp_id],
rw [h.counit.naturality_assoc, prod.map_snd, comp_id],
exact rfl
```

**lean_error:** tail step 1/4 ('rw [prodComparison_component, assoc, prod.map_snd, comp_id],'): <stdin>:1:59: expected end of input

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **success**  (gen 0.3s, verify 0.5s, in=471, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.3s, in=460, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply prod.hom_ext
ext
apply h.counit_naturality
```

**lean_error:** tail step 1/3 ('apply prod.hom_ext'): tactic 'apply' failed, failed to unify

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 3.4s, verify 0.1s, in=451, out=157)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply L.map_ext
rotate_left
apply prod.hom_ext
simp only [prodComparison, Functor.map_comp, Functor.map_id, h.counit_naturality, h.unit_naturality, h.hom_ext, h.counit_inv, h.unit_inv, Category.comp_id, Category.id_comp, Functor.map_id, Functor.map_comp, prod.map_fst, prod.map_snd, prod.snd_fst, prod.snd_snd, prodComparison_fst, prodComparison_snd]
```

**lean_error:** tail step 1/4 ('apply L.map_ext'): invalid field 'map_ext', the environment does not contain 'CategoryTheory.Functor.map_ext'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 157.6s, verify 0.1s, in=442, out=12224)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply h.hom_equiv_injective
dsimp
simp only [transpose_comp, transpose_map, h.counit_naturality, prod.map_comp, category.assoc]
simp only [h.hom_equiv_unit, unit_prod_map_snd, category.id_comp]
```

**lean_error:** tail step 1/4 ('apply h.hom_equiv_injective'): invalid field 'hom_equiv_injective', the environment does not contain 'CategoryTheory.Adjunction.hom_equiv_injective'

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **success**  (gen 0.2s, verify 0.6s, in=442, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```
