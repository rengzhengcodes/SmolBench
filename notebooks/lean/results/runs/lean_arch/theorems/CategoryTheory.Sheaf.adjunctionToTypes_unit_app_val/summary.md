# CategoryTheory.Sheaf.adjunctionToTypes_unit_app_val   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Sites/Adjunction.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 6.3s, in=612, out=82)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [NatTrans.naturality, NatTrans.naturality]
erw [NatIso.unit_inv_app, NatIso.unit_inv_app]
erw [Adjunction.homEquiv_unit, Adjunction.homEquiv_unit]
erw [whiskerRight_comp, whiskerRight_comp]
erw [comp_id, comp_id]
erw [id_comp, id_comp]
rfl
```

**lean_error:** tail step 1/7 ('erw [NatTrans.naturality, NatTrans.naturality]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.0s, verify 4.3s, in=567, out=203)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext X
  dsimp [sheafEquivSheafOfTypes, sheafToPresheaf, sheafOfTypesToPresheaf, Equiv.sheafEquivSheafOfTypes, Equiv.symm, Equiv.unit, sheafEquivPresheaf, toSheafify, presheafToSheaf, sheafify, isSheafify.lift, isSheafify.isSeparated]
  erw [Category.id_comp, Category.comp_id]
  simp only [← Functor.map_comp, ← assoc, ← Adjunction.homEquiv_counit, Adjunction.unit_counit_adjunct]
  simp only [assoc]
  congr 1
  simp only [← Category.assoc, ← Functor.map_comp]
  congr 1
  dsimp [isSheafify.isSeparated]
  simp only [Category.comp_id]
  erw [isSheafify.lift_map]
  simp only [Category.comp_id]
```

**lean_error:** tail step 2/12 ('dsimp [sheafEquivSheafOfTypes, sheafToPresheaf, sheafOfTypesToPresheaf, Equiv.sheafEquivSheafOfTypes, Equiv.symm, Equiv.unit, sheafEquivPresheaf, toSheafify, presheafToSheaf, sheafify, isSheafify.lift, isSheafify.isSeparated]'): unknown constant 'Equiv.sheafEquivSheafOfTypes'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=601, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply eq_to_hom_app,
exact adjunction_unit_naturality _,
```

**lean_error:** tail step 1/2 ('apply eq_to_hom_app,'): <stdin>:1:19: expected end of input
