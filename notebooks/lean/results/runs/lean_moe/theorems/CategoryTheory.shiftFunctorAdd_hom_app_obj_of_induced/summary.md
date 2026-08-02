# CategoryTheory.shiftFunctorAdd_hom_app_obj_of_induced   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Induced.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ShiftMkCore.shiftFunctorAdd_eq, HasShift.Induced.add_hom_app_obj]
```

**True premises at k:** `CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq`, `CategoryTheory.HasShift.Induced.add_hom_app_obj`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.3s, in=593, out=454)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa
```

**lean_error:** tail step 1/1 ('simpa'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 216.5s, verify 0.2s, in=552, out=26826)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : HasShift D A := this hF
have hC : HasShift C A := inst✝
simp [shiftFunctorAdd, h, hC, F, s, i] at *
<;>
try aesop
<;>
try
{
  ext X
  simp_all [Category.ext_iff, Function.comp_apply]
  <;>
  try aesop
}
```

**lean_error:** tail step 2/13 ('have hC : HasShift C A := inst✝'): <stdin>:1:30: expected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.2s, verify 0.3s, in=551, out=481)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shiftFunctorAdd, Functor.comp_obj, Functor.comp_map]
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

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.3s, verify 0.1s, in=1216, out=1431)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using
  (CategoryTheory.HasShift.Induced.add_hom_app_obj (F:=F) (s:=s) (i:=i) (hF:=hF) a b X)
```

**lean_error:** tail step 1/2 ('simpa using'): <stdin>:1:11: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 255.4s, verify 0.1s, in=1199, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
shiftFunctorAdd D a b = (hasShift D A).add a b
```

**lean_error:** tail step 1/1 ('shiftFunctorAdd D a b = (hasShift D A).add a b'): <stdin>:1:1: unknown tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.2s, in=1210, out=929)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← ShiftMkCore.shiftFunctorAdd_eq (inferInstance : ShiftMkCore D A) a b]
simp [add_hom_app_obj]
```

**lean_error:** tail step 1/2 ('rw [← ShiftMkCore.shiftFunctorAdd_eq (inferInstance : ShiftMkCore D A) a b]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.2s, verify 0.4s, in=2737, out=3372)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using
  (HasShift.Induced.add_hom_app_obj (F:=F) (s:=s) (i:=i) (hF:=hF) a b X)
```

**lean_error:** tail step 1/2 ('simpa using'): <stdin>:1:11: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 105.7s, verify 0.1s, in=2744, out=12091)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h : shiftFunctorAdd D a b = add F s i hF.2 a b := by
  dsimp [shiftFunctorAdd, HasShift.add]
  <;> rfl
rw [h]
exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/5 ('have h : shiftFunctorAdd D a b = add F s i hF.2 a b := by'): <stdin>:1:57: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 14.1s, verify 0.2s, in=2669, out=1302)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [HasShift.Induced.add_hom_app_obj]
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

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.2s, verify 0.2s, in=2519, out=770)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (HasShift.Induced.add_hom_app_obj (F:=F) (s:=s) (i:=i) (hF:=hF) a b X)
```

**lean_error:** tail step 1/1 ('simpa using (HasShift.Induced.add_hom_app_obj (F:=F) (s:=s) (i:=i) (hF:=hF) a b X)'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 111.4s, verify 0.1s, in=2901, out=12738)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
let hasShift : HasShift D A := letI hF
have h1 : shiftFunctorAdd D a b = hasShift.add a b := by
  have h2 : shiftFunctorAdd D a b = (hasShift : ShiftMkCore D A).add a b := by
    apply ShiftMkCore.shiftFunctorAdd_eq
  rw [h2]
  <;> simp [HasShift.add]
have h2 : hasShift.add = add F s i hF := by
  rfl
have h3 : shiftFunctorAdd D a b = add F s i hF a b := by
  rw [h1]
  <;> rw [h2]
rw [h3]
exact add_hom_app_obj a b X
```

**lean_error:** tail step 1/13 ('let hasShift : HasShift D A := letI hF'): <stdin>:1:38: unexpected end of input; expected '|'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 23.6s, verify 0.9s, in=2659, out=2353)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [add_hom_app_obj]
<;> apply ShiftMkCore.shiftFunctorAdd_eq
<;> rfl
```

**lean_error:** tail step 1/3 ('simp [add_hom_app_obj]'): unknown identifier 'add_hom_app_obj'
