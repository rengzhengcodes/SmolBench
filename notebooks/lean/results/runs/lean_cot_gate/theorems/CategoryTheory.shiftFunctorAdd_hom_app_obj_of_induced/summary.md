# CategoryTheory.shiftFunctorAdd_hom_app_obj_of_induced   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Induced.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ShiftMkCore.shiftFunctorAdd_eq, HasShift.Induced.add_hom_app_obj]
```

**True premises at k:** `CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq`, `CategoryTheory.HasShift.Induced.add_hom_app_obj`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ | ✘ ✘ · · |
| `hint:2` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ | ✘ ✓ ✘ · |
| `hint:3` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✓ | ✘ ✘ ✘ ✓ |
| `noise:3` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ | ✓ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 191.9s, verify 0.1s, in=534, out=7462)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 258.8s, verify 0.5s, in=534, out=10323)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply F.faithful
dsimp only [functor.comp_map]
simp only [i_hom_naturality, F.map_comp_assoc, ← i_inv_hom_app_assoc, shiftFunctorAdd_hom_naturality, i_inv_comp_right, i_inv_comp_left]
simp only [i_inv_hom_app]
```

**lean_error:** tail step 1/4 ('apply F.faithful'): invalid field 'faithful', the environment does not contain 'CategoryTheory.Functor.faithful'

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 259.4s, verify 0.1s, in=534, out=10343)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply F.faithful
simp only [Functor.map_comp, ← i.hom.naturality_assoc, i.inv_hom_id_app_assoc, Functor.map_comp, i.inv.naturality_assoc, i.inv_hom_id_app_assoc]
simp only [Functor.map_comp, ← i.hom.naturality, i.inv_hom_id_app, Functor.map_id, comp_id]
simp only [Functor.map_comp, i.inv.naturality, i.hom.inv_app_self, comp_id]
simp only [Functor.map_comp, ← i.hom.naturality, i.inv_hom_id_app, comp_id]
simp only [Functor.map_comp, i.inv.naturality, i.hom.inv_app_self, comp_id]
```

**lean_error:** tail step 1/6 ('apply F.faithful'): invalid field 'faithful', the environment does not contain 'CategoryTheory.Functor.faithful'

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 357.7s, verify 0.1s, in=534, out=14433)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply hF.right.faithful,
dsimp,
simp only [functor.comp_map, iso.inv_hom_id_app, i, shiftFunctorAdd, HasShift.induced],
congr! 2,
rw [category.id_comp, category.comp_id]
```

**lean_error:** tail step 1/5 ('apply hF.right.faithful,'): <stdin>:1:23: expected end of input

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.8s, verify 0.2s, in=534, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u_4
D : Type u_2
inst✝³ : Category.{u_5, u_4} C
inst✝² : Category.{u_1, u_2} D
F : C ⥤ D
A : Type u_3
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=534, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [shiftFunctorAdd_induced_hom_app, Iso.inv_hom_id_app_assoc]
```

**lean_error:** tail step 1/1 ('simp only [shiftFunctorAdd_induced_hom_app, Iso.inv_hom_id_app_assoc]'): unknown identifier 'shiftFunctorAdd_induced_hom_app'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.3s, verify 0.1s, in=534, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shiftFunctorAdd, shiftFunctorAddD, shiftFunctorAddC, this hF]
```

**lean_error:** tail step 1/1 ('simp [shiftFunctorAdd, shiftFunctorAddD, shiftFunctorAddC, this hF]'): unknown identifier 'shiftFunctorAddD'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=534, out=39)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shiftFunctorAdd, shiftFunctorAdd' F A s i hF a b, ← F.map_comp, ← Functor.map_comp, ← i]
```

**lean_error:** tail step 1/1 ("simp [shiftFunctorAdd, shiftFunctorAdd' F A s i hF a b, ← F.map_comp, ← Functor.map_comp, ← i]"): application type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 9.1s, verify 0.1s, in=534, out=257)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this hF a b X
```

**lean_error:** tail step 1/1 ('exact this hF a b X'): function expected at

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.7s, verify 0.1s, in=534, out=299)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [HasShift.induced_add F A s i (this hF) a b X]
```

**lean_error:** tail step 1/1 ('simp [HasShift.induced_add F A s i (this hF) a b X]'): unknown constant 'CategoryTheory.HasShift.induced_add'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 12.7s, verify 0.2s, in=534, out=363)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u_4
D : Type u_2
inst✝³ : Category.{u_5, u_4} C
inst✝² : Category.{u_1, u_2} D
F : C ⥤ D
A : Type u_3
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 13.1s, verify 0.2s, in=534, out=371)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Iso.hom_inv_id, Iso.inv_hom_id, Category.assoc]
```

**final state (truncated):**
```
C : Type u_4
D : Type u_2
inst✝³ : Category.{u_5, u_4} C
inst✝² : Category.{u_1, u_2} D
F : C ⥤ D
A : Type u_3
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 78.8s, verify 0.3s, in=1171, out=2815)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b]
apply add_hom_app_obj
```

**lean_error:** tail step 1/2 ('rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 96.3s, verify 0.2s, in=1171, out=3445)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i).toShiftMkCore a b]
apply add_hom_app_obj
```

**lean_error:** tail step 1/2 ('rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i).toShiftMkCore a b]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 144.2s, verify 0.2s, in=1171, out=5300)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (hasShiftMk D A) a b]
exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/2 ('rw [ShiftMkCore.shiftFunctorAdd_eq (hasShiftMk D A) a b]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 153.3s, verify 0.2s, in=1171, out=5716)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.mkCore D A) a b]
exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/2 ('rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.mkCore D A) a b]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.2s, verify 0.2s, in=1171, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u_4
D : Type u_2
inst✝³ : Category.{u_5, u_4} C
inst✝² : Category.{u_1, u_2} D
F : C ⥤ D
A : Type u_3
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=1171, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [add_hom_app_obj]
```

**lean_error:** tail step 1/1 ('simp [add_hom_app_obj]'): unknown identifier 'add_hom_app_obj'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=1171, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/1 ('exact add_hom_app_obj a b X'): unknown identifier 'add_hom_app_obj'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=1171, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact add_hom_app_obj F s i hF a b X
```

**lean_error:** tail step 1/1 ('exact add_hom_app_obj F s i hF a b X'): unknown identifier 'add_hom_app_obj'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 9.8s, verify 0.1s, in=1171, out=271)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]
```

**lean_error:** tail step 1/1 ('simp [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]'): unknown identifier 'add_hom_app_obj'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 10.6s, verify 0.1s, in=1171, out=297)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq _ _ _, HasShift.Induced.add_hom_app_obj]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.6s, verify 0.3s, in=1171, out=328)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]
```

**lean_error:** tail step 1/1 ('rw [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 14.8s, verify 0.2s, in=1171, out=401)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq]
```

**final state (truncated):**
```
C : Type u_4
D : Type u_2
inst✝³ : Category.{u_5, u_4} C
inst✝² : Category.{u_1, u_2} D
F : C ⥤ D
A : Type u_3
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 221.5s, verify 0.1s, in=2577, out=5351)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b], apply add_hom_app_obj
```

**lean_error:** tail step 1/1 ('rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b], apply add_hom_app_obj'): <stdin>:1:66: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 224.8s, verify 0.1s, in=2577, out=5960)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/1 ('exact add_hom_app_obj a b X'): unknown identifier 'add_hom_app_obj'

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 244.6s, verify 0.3s, in=2577, out=6940)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b]
exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/2 ('rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 248.1s, verify 0.1s, in=2577, out=7599)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (by apply_instance) a b], apply add_hom_app_obj
```

**lean_error:** tail step 1/1 ('rw [ShiftMkCore.shiftFunctorAdd_eq (by apply_instance) a b], apply add_hom_app_obj'): <stdin>:1:40: unknown tactic

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.9s, verify 0.2s, in=2577, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u_4
D : Type u_2
inst✝³ : Category.{u_5, u_4} C
inst✝² : Category.{u_1, u_2} D
F : C ⥤ D
A : Type u_3
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=2577, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [add_hom_app_obj]
```

**lean_error:** tail step 1/1 ('simp only [add_hom_app_obj]'): unknown identifier 'add_hom_app_obj'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.3s, verify 0.1s, in=2577, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [add_hom_app_obj]
```

**lean_error:** tail step 1/1 ('simp [add_hom_app_obj]'): unknown identifier 'add_hom_app_obj'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.4s, verify 0.1s, in=2577, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ShiftMkCore.shiftFunctorAdd_eq]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 17.9s, verify 0.3s, in=2577, out=275)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]
```

**lean_error:** tail step 1/1 ('rw [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 22.1s, verify 0.1s, in=2577, out=414)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
trans (ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b).symm.hom.app _ <|
  HasShift.Induced.add_hom_app_obj F s i hF a b X
```

**lean_error:** tail step 1/2 ('trans (ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b).symm.hom.app _ <|'): <stdin>:1:87: unexpected end of input

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 22.7s, verify 0.1s, in=2577, out=387)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
trans (CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b)
```

**lean_error:** tail step 1/1 ('trans (CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b)'): internal exception #7

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 22.8s, verify 0.1s, in=2577, out=451)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq, CategoryTheory.HasShift.Induced.add_hom_app_obj]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 63.5s, verify 0.2s, in=2606, out=2293)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b]
exact add_hom_app_obj F s i hF a b X
```

**lean_error:** tail step 1/2 ('rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 83.7s, verify 0.3s, in=2606, out=2982)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b]
exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/2 ('rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.induced F A s i) a b]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 125.9s, verify 0.2s, in=2606, out=4559)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.core D) a b]
simp
```

**lean_error:** tail step 1/2 ('rw [ShiftMkCore.shiftFunctorAdd_eq (HasShift.core D) a b]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 197.9s, verify 0.1s, in=2606, out=7746)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ShiftMkCore.shiftFunctorAdd_eq (by infer_instance) a b], exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/1 ('rw [ShiftMkCore.shiftFunctorAdd_eq (by infer_instance) a b], exact add_hom_app_obj a b X'): <stdin>:1:59: expected end of input

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.0s, verify 0.2s, in=2606, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u_4
D : Type u_2
inst✝³ : Category.{u_5, u_4} C
inst✝² : Category.{u_1, u_2} D
F : C ⥤ D
A : Type u_3
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=2606, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [add_hom_app_obj]
```

**lean_error:** tail step 1/1 ('simp [add_hom_app_obj]'): unknown identifier 'add_hom_app_obj'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=2606, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/1 ('exact add_hom_app_obj a b X'): unknown identifier 'add_hom_app_obj'

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=2606, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact add_hom_app_obj F s i hF a b X
```

**lean_error:** tail step 1/1 ('exact add_hom_app_obj F s i hF a b X'): unknown identifier 'add_hom_app_obj'

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 10.2s, verify 0.1s, in=2606, out=276)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ShiftMkCore.shiftFunctorAdd_eq, HasShift.Induced.add_hom_app_obj]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.9s, verify 0.1s, in=2606, out=332)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]
```

**lean_error:** tail step 1/1 ('simp only [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]'): unknown identifier 'add_hom_app_obj'

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 12.5s, verify 0.1s, in=2606, out=356)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq, CategoryTheory.HasShift.Induced.add_hom_app_obj]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 16.5s, verify 0.1s, in=2606, out=491)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]
```

**lean_error:** tail step 1/1 ('simp only [ShiftMkCore.shiftFunctorAdd_eq, add_hom_app_obj]'): unknown identifier 'add_hom_app_obj'
