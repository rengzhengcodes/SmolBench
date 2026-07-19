# CategoryTheory.Functor.preservesZeroMorphisms_of_map_exact   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Exact.lean`  

**Ground-truth tail (from k):**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero _ h)
```

**True premises at k:** `CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object`, `CategoryTheory.Limits.idZeroEquivIsoZero`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✘ | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✘ |
| `hint:3` | ✓ ✘ ✓ ✓ | ✘ ✘ ✘ ✘ | ✓ ✓ ✘ ✓ |
| `noise:3` | ✓ ✘ ✓ ✓ | ✘ ✘ ✘ ✘ | ✘ ✓ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 206.9s, verify 0.3s, in=293, out=8402)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply PreservesZeroMorphisms.mk
intros X Y
rw zero_eq_comp_zero
rw L.map_comp
haveI : is_zero (L.obj 0) := is_zero_of_id_zero h
have L.map (0 : X ⟶ 0) = 0 := is_zero.eq_zero_morphism _
have L.map (0 : 0 ⟶ Y) = 0 := is_zero.eq_zero_morphism _
rw [this, this]
rw comp_zero
rfl
```

**lean_error:** tail step 3/10 ('rw zero_eq_comp_zero'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 214.9s, verify 0.3s, in=293, out=8703)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply PreservesZeroMorphisms.mk
intros X Y
have key : (0 : X ⟶ Y) = (0 : X ⟶ 0) ≫ (0 : 0 ⟶ Y) := by rw zero_comp
rw key
rw functor.map_comp
have hL0 : is_zero (L.obj 0) := is_zero_of_id_zero h
have h1 : L.map (0 : X ⟶ 0) = 0 := zero_of_target_is_zero hL0
have h2 : L.map (0 : 0 ⟶ Y) = 0 := zero_of_source_is_zero hL0
rw [h1, h2]
apply comp_zero
```

**lean_error:** tail step 3/10 ('have key : (0 : X ⟶ Y) = (0 : X ⟶ 0) ≫ (0 : 0 ⟶ Y) := by rw zero_comp'): <stdin>:1:60: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 215.2s, verify 0.1s, in=293, out=8711)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intros X Y
rw functor.map_comp
have hX : is_zero (L.obj 0) := is_zero_of_id_eq_zero h
have h1 : L.map (0 : X ⟶ 0) = 0 := hX.eq_zero'
have h2 : L.map (0 : 0 ⟶ Y) = 0 := hX.eq_zero
rw [h1, h2]
rw comp_zero
```

**lean_error:** tail step 1/7 ('intros X Y'): tactic 'introN' failed, insufficient number of binders

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 250.8s, verify 0.1s, in=293, out=10239)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intros X Y
rw [zero_morphism_eq_zero_comp]
rw [L.map_comp]
have hL0 : is_zero (L.obj 0) := is_zero_of_1_eq_zero h
rw [hL0.eq_zero_morphism_target, hL0.eq_zero_morphism_source]
apply zero_comp
```

**lean_error:** tail step 1/6 ('intros X Y'): tactic 'introN' failed, insufficient number of binders

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=293, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): failed to synthesize instance

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=293, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨h⟩
```

**lean_error:** tail step 1/1 ('exact ⟨h⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=293, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun X Y => L.map_zero⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun X Y => L.map_zero⟩'): failed to synthesize instance

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=293, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply preservesZeroMorphismsOfMapZeroIsZero
```

**lean_error:** tail step 1/1 ('apply preservesZeroMorphismsOfMapZeroIsZero'): unknown identifier 'preservesZeroMorphismsOfMapZeroIsZero'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 4.6s, verify 0.1s, in=293, out=134)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_obj_zero_iso_zero _ _ h
```

**lean_error:** tail step 1/1 ('apply preservesZeroMorphisms_of_obj_zero_iso_zero _ _ h'): unknown identifier 'preservesZeroMorphisms_of_obj_zero_iso_zero'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 8.4s, verify 0.1s, in=293, out=259)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_zero_obj (isZero_of_0_eq_1 h)
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_zero_obj (isZero_of_0_eq_1 h)'): unknown identifier 'preservesZeroMorphisms_of_zero_obj'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.0s, verify 0.1s, in=293, out=271)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h, zeroMorphism, comp_id]
```

**lean_error:** tail step 1/1 ('simp [h, zeroMorphism, comp_id]'): unknown identifier 'zeroMorphism'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 12.8s, verify 0.1s, in=293, out=429)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [CategoryTheory.Functor.preservesZeroMorphisms_iff, CategoryTheory.eq_zero_of_abelian,
  Functor.map_zero]
```

**lean_error:** tail step 1/2 ('simpa [CategoryTheory.Functor.preservesZeroMorphisms_iff, CategoryTheory.eq_zero_of_abelian,'): <stdin>:1:92: unexpected end of input; expected '*' or '-'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 14.5s, verify 0.1s, in=924, out=638)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) h)
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 14.9s, verify 0.2s, in=924, out=654)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
exact idZeroEquivIsoZero (L.obj 0) h
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 19.0s, verify 0.2s, in=924, out=828)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have i := idZeroEquivIsoZero (L.obj 0) h
exact preservesZeroMorphisms_of_map_zero_object i
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 87.5s, verify 0.1s, in=924, out=3775)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).toFun h
```

**lean_error:** tail step 1/1 ('apply preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).toFun h'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=924, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (Limits.idZeroEquivIsoZero _).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (Limits.idZeroEquivIsoZero _).symm h'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.1s, in=924, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.2s, verify 0.1s, in=924, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).invFun h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).invFun h'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=924, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) ⟨h.symm⟩)
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) ⟨h.symm⟩)'): invalid constructor ⟨...⟩, insufficient number of arguments, constructs 'Eq.refl' does not have explicit fields, but #1 provided

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 6.3s, verify 0.1s, in=924, out=185)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero _ h)
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 6.3s, verify 0.1s, in=924, out=187)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero _ h)
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 7.2s, verify 0.1s, in=924, out=218)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object ((idZeroEquivIsoZero (L.obj 0)).toFun h)
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 7.5s, verify 0.1s, in=924, out=231)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
replace h := idZeroEquivIsoZero (L.obj 0).toFun h
exact preservesZeroMorphisms_of_map_zero_object h
```

**lean_error:** tail step 1/2 ('replace h := idZeroEquivIsoZero (L.obj 0).toFun h'): internal exception #7

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 28.7s, verify 0.1s, in=1285, out=619)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) h)
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 34.5s, verify 0.1s, in=1285, out=902)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero.mp h)
```

**lean_error:** tail step 1/1 ('apply preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero.mp h)'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 41.8s, verify 0.2s, in=1285, out=1114)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
exact (idZeroEquivIsoZero (L.obj 0)).toFun h
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 49.4s, verify 0.1s, in=1285, out=1618)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) h)
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=1285, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (Limits.idZeroEquivIsoZero _).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (Limits.idZeroEquivIsoZero _).symm h'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.6s, verify 0.1s, in=1285, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.7s, verify 0.1s, in=1285, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.8s, verify 0.1s, in=1285, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 11.3s, verify 0.1s, in=1285, out=194)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [idZeroEquivIsoZero] using preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero _ h)
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 11.6s, verify 0.1s, in=1285, out=189)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) h)
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 11.7s, verify 0.1s, in=1285, out=251)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
aesop_cat (rule_sets [simp]) using preservesZeroMorphisms_of_map_zero_object
  (idZeroEquivIsoZero (L.obj 0) (by exact h))
```

**lean_error:** tail step 1/2 ('aesop_cat (rule_sets [simp]) using preservesZeroMorphisms_of_map_zero_object'): <stdin>:1:21: expected ':='

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 13.4s, verify 0.1s, in=1285, out=270)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero _ h)
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 15.1s, verify 0.1s, in=1309, out=655)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) h)
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 18.0s, verify 0.1s, in=1309, out=783)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object L (idZeroEquivIsoZero (L.obj 0) h)
```

**lean_error:** tail step 1/1 ('apply preservesZeroMorphisms_of_map_zero_object L (idZeroEquivIsoZero (L.obj 0) h)'): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 20.3s, verify 0.1s, in=1309, out=882)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) h)
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 22.1s, verify 0.1s, in=1309, out=957)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) h)
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.4s, in=1309, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (Limits.idZeroEquivIsoZero _).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (Limits.idZeroEquivIsoZero _).symm h'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=1309, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=1309, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (IdZeroEquivIsoZero (L.obj 0)).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (IdZeroEquivIsoZero (L.obj 0)).symm h'): function expected at

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=1309, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).symm h'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=1309, out=178)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero.toFun h)
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero.toFun h)'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 6.4s, verify 0.1s, in=1309, out=182)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0) h)
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.5s, verify 0.1s, in=1309, out=269)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).toFun h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero (L.obj 0)).toFun h'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 9.4s, verify 0.1s, in=1309, out=298)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object ((idZeroEquivIsoZero _).toFun h)
```
