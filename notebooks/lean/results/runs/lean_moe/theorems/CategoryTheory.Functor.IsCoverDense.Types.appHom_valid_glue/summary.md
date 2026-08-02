# CategoryTheory.Functor.IsCoverDense.Types.appHom_valid_glue   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Sites/DenseSubsite.lean`  

**Ground-truth tail (from k):**
```lean
apply appHom_restrict
```

**True premises at k:** `CategoryTheory.Functor.IsCoverDense.Types.appHom_restrict`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 12.1s, verify 0.2s, in=536, out=1811)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [appHom]
```

**final state (truncated):**
```
case h
C : Type u_1
inst✝⁵ : Category.{u_6, u_1} C
D : Type u_2
inst✝⁴ : Category.{u_5, u_2} D
E : Type u_3
...
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 168.7s, verify 0.1s, in=501, out=19681)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.3s, verify 0.2s, in=493, out=1138)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← CategoryStruct.comp_assoc]
rw [α.naturality f]
simp
```

**lean_error:** tail step 1/3 ('rw [← CategoryStruct.comp_assoc]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.1s, in=884, out=1347)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (f:=f) (x:=a✝))
```

**lean_error:** tail step 1/1 ("simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (f:=f) (x:=a✝))"): <stdin>:1:57: expected token

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.2s, in=864, out=526)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [appHom_restrict]
```

**lean_error:** tail step 1/1 ('rw [appHom_restrict]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.6s, verify 0.1s, in=847, out=644)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [appHom_restrict]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=2142, out=1013)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (ℱ:=ℱ) (G:=G) (X:=X) (Y:=Y) f a✝)
```

**lean_error:** tail step 1/1 ("simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (ℱ:=ℱ) (G:=G) (X:=X) (Y:=Y) f a✝)"): <stdin>:1:76: expected token

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 20.4s, verify 0.1s, in=2168, out=2288)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem CategoryTheory.Functor.IsCoverDense.Types.appHom_valid_glue {C : Type u_1} {inst✝⁵ : Category.{u_6, u_1} C} {D : Type u_2} {inst✝⁴ : Category.{u_5, u_2} D} {E : Type u_3} {inst✝³ : Category.{?u.46606, u_3} E} {J : GrothendieckTopology C} {K : GrothendieckTopology D} {L : GrothendieckTopology E} {A : Type u_4} {inst✝² : Category.{?u.46658, u_4} A} {G : C ⥤ D} {inst✝¹ : IsCoverDense G K} {inst✝ : Full G} {ℱ : Dᵒᵖ ⥤ Type v} {ℱ' : SheafOfTypes K} {α : G.op ⋙ ℱ ⟶ G.op ⋙ ℱ'.val} {X : D} {Y : C} {f : op X ⟶ op (G.obj Y)} {a✝ : ℱ.obj (op X)} :
    (appHom α X ≫ ℱ'.val.map f) a✝ = (ℱ.map f ≫ α.app (op Y)) a✝ := by
  ext
  have h₁ : (appHom α X ≫ ℱ'.val.map f) a✝ = ℱ'.val.map f (appHom α X a✝) := by
    simp [Function.comp_apply]
    <;>
    rfl
  
  have h₂ : (ℱ.map f ≫ α.app (op Y)) a✝ = α.app (op Y) (ℱ.map f a✝) := by
    simp [Function.comp_apply]
    <;>
    rfl
  
  have h₃ : ℱ'.val.map f (appHom α X a✝) = α.app (op Y) (ℱ.map f a✝) := by
    apply appHom_restrict
  
  have h₄ : (appHom α X ≫ ℱ'.val.map f) a✝ = (ℱ.map f ≫ α.app (op Y)) a✝ := by
    rw [h₁]
    rw [h₂]
    rw [h₃]
  
  apply h₄
```

**lean_error:** tail step 1/18 ("theorem CategoryTheory.Functor.IsCoverDense.Types.appHom_valid_glue {C : Type u_1} {inst✝⁵ : Category.{u_6, u_1} C} {D : Type u_2} {inst✝⁴ : Category.{u_5, u_2} D} {E : Type u_3} {inst✝³ : Category.{?u.46606, u_3} E} {J : GrothendieckTopology C} {K : GrothendieckTopology D} {L : Gro

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.1s, in=2132, out=569)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [appHom_restrict]
```

**lean_error:** tail step 1/1 ('simp only [appHom_restrict]'): simp made no progress

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.1s, in=2036, out=1333)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (f:=f) (x:=a✝))
```

**lean_error:** tail step 1/1 ("simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (f:=f) (x:=a✝))"): <stdin>:1:57: expected token

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 11.4s, verify 0.2s, in=2369, out=1241)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [appHom_restrict]
```

**lean_error:** tail step 1/1 ('rw [appHom_restrict]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=2129, out=501)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Function.comp_apply, appHom_restrict]
```

**lean_error:** tail step 1/1 ('simp only [Function.comp_apply, appHom_restrict]'): simp made no progress
