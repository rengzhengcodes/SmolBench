# CategoryTheory.InjectiveResolution.isoRightDerivedObj_hom_naturality   (k=3, 4 tactics total)

file: `Mathlib/CategoryTheory/Abelian/RightDerived.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=814, out=74)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [HomologicalComplex.homologyFunctor_map],
  erw [HomotopyCategory.homologyFunctorFactors_hom_app],
  erw [HomotopyCategory.homologyFunctorFactors_hom_app],
  dsimp,
  erw [Category.comp_id],
  erw [Category.comp_id],
  erw [Category.id_comp],
  erw [Category.id_comp]
```

**lean_error:** tail step 1/8 ('rw [HomologicalComplex.homologyFunctor_map],'): <stdin>:1:43: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.8s, in=782, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
simp only [Functor.map_comp, assoc]
congr
ext
simp only [homologyMap_eq_homologyFunctor_map, assoc]
rfl
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=803, out=250)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply homology_functor_map_eq_homology_map
```

**lean_error:** tail step 1/1 ('apply homology_functor_map_eq_homology_map'): unknown identifier 'homology_functor_map_eq_homology_map'
