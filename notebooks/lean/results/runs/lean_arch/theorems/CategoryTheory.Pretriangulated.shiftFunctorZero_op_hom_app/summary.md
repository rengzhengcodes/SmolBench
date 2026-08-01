# CategoryTheory.Pretriangulated.shiftFunctorZero_op_hom_app   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Triangulated/Opposite.lean`  

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

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.4s, verify 0.2s, in=478, out=151)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [pullbackShiftIso_hom_app]
simp only [CategoryTheory.Functor.map_id, CategoryTheory.Functor.map_comp]
simp only [CategoryTheory.NatIso.app_hom]
simp only [CategoryTheory.NatIso.app_inv]
simp only [CategoryTheory.Functor.op_map_app]
simp only [CategoryTheory.Functor.op_map_app, CategoryTheory.Functor.map_id]
rw [shiftFunctorOpIso_hom_app]
simp only [CategoryTheory.NatIso.app_hom]
simp only [CategoryTheory.Functor.op_map_app]
simp only [CategoryTheory.Functor.map_id]
rw [CategoryTheory.Functor.map_id]
simp only [CategoryTheory.Functor.op_map_app]
refl
```

**lean_error:** tail step 1/13 ('rw [pullbackShiftIso_hom_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 1.4s, in=438, out=76)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply_fun (fun e => e.unop) at ⊢
simp only [← op_comp, Iso.hom_inv_id_app, op_id, comp_id, Iso.hom_inv_id_app_assoc]
rw [pullbackShiftIso_hom_app, shiftFunctorOpIso_hom_app, ← Functor.map_comp]
simp only [Functor.map_id, comp_id]
```

**lean_error:** tail step 1/4 ('apply_fun (fun e => e.unop) at ⊢'): <stdin>:1:31: expected '*' or term

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.0s, in=467, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail
