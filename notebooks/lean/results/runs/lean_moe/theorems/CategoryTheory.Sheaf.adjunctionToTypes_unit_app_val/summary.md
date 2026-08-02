# CategoryTheory.Sheaf.adjunctionToTypes_unit_app_val   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Sites/Adjunction.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=647, out=549)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 58.9s, verify 0.1s, in=619, out=7941)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [sheafEquivSheafOfTypes, Adjunction.whiskerRight, homEquiv, toSheafify, sheafEquivSheafOfTypes_symm_apply, Adjunction.unit_whiskerRight, Equiv.unit_id]
```

**lean_error:** tail step 1/1 ('simp [sheafEquivSheafOfTypes, Adjunction.whiskerRight, homEquiv, toSheafify, sheafEquivSheafOfTypes_symm_apply, Adjunction.unit_whiskerRight, Equiv.unit_id]'): unknown identifier 'homEquiv'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=608, out=626)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Adjunction.homEquiv_eq, Adjunction.unit_eq_homEquiv_id]
<;>
  ext
<;>
  simp [Category.assoc]
```

**lean_error:** tail step 1/5 ('simp [Adjunction.homEquiv_eq, Adjunction.unit_eq_homEquiv_id]'): invalid field notation, type is not of the form (C ...) where C is a constant
