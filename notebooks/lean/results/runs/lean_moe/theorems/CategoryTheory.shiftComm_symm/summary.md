# CategoryTheory.shiftComm_symm   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact NatTrans.congr_app (congr_arg Iso.hom (shiftFunctorComm_symm C i j)) X
```

**True premises at k:** `CategoryTheory.NatTrans.congr_app`, `congr_arg`, `CategoryTheory.Iso.hom`, `CategoryTheory.shiftFunctorComm_symm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.4s, verify 0.1s, in=338, out=1506)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using congrArg Iso.hom (shiftComm_symm (X:=X) (i:=i) (j:=j))
```

**lean_error:** tail step 1/1 ('simpa using congrArg Iso.hom (shiftComm_symm (X:=X) (i:=i) (j:=j))'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 22.3s, verify 0.1s, in=285, out=1828)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 25.2s, verify 0.1s, in=280, out=493)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.1s, verify 0.7s, in=861, out=1648)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [shiftComm] using
  congrArg Iso.hom
    (congrArg (fun η => η.app X) (shiftFunctorComm_symm (C:=C) i j))
```

**lean_error:** tail step 1/3 ('simpa [shiftComm] using'): <stdin>:1:23: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 249.1s, verify 0.1s, in=831, out=27531)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_symm : (shiftFunctorComm C i j).symm = shiftFunctorComm C j i := shiftFunctorComm_symm i j
have h_mul_app : ∀ {F G : C ⥤ D} (X : C), (F * G).app X = F.app X * G.app X := by
  intro F G X
  rfl
have h_one_app : ∀ {F G : C ⥤ D} (X : C), (1 : F ⥤ G).app X = 1 := by
  intro F G X
  rfl
have h_prod_inv : (shiftFunctorComm C i j) * (shiftFunctorComm C i j).symm = 1 := by
  rfl
have h_prod_inv' : (shiftFunctorComm C i j).symm * (shiftFunctorComm C i j) = 1 := by
  rfl
have h₁ : ((shiftFunctorComm C i j).app X) * ((shiftFunctorComm C i j).symm).app X = 1 := by
  calc
    ((shiftFunctorComm C i j).app X) * ((shiftFunctorComm C i j).symm).app X = ((shiftFunctorComm C i j) * (shiftFunctorComm C i j).symm).app X := by rw [h_mul_app]
    _ = 1.app X := by rw [h_prod_inv]
    _ = 1 := by rw [h_one_app]
have h₂ : ((shiftFunctorComm C i j).symm).app X * ((shiftFunctorComm C i j).app X) = 1 := by
  calc
    ((shiftFunctorComm C i j).symm).app X * ((shiftFunctorComm C i j).app X) = ((shiftFunctorComm C i j).symm * (shiftFunctorComm C i j)).app X := by
      rw [h_mul_app]
    _ = 1.app X := by rw [h_prod_inv']
    _ = 1 := by rw [h_one_app]
have h₃ : ((shiftFunctorComm C i j).app X) * (((shiftFunctorComm C i j).app X).symm) = 1 := by
  rfl
have h₄ : ((shiftFunctorComm C i j).symm).app X = ((shiftFunctorComm C i j).app X).symm := by
  calc
    ((shiftFunctorComm C i j).symm).app X = ((shiftFunctorComm C i j).symm).app X * 1 := by simp
    _ = ((shiftFunctorComm C i j).symm).app X * (((shiftFunctorComm C i j).app X) * (((shiftFunctorComm C i j).app X).symm)) := by rw [h₃]
    _ = (((shiftFunctorComm C i j).symm).app X * ((shiftFunctorComm C i j).app X)) * (((shiftFunctorComm C i j).app X).symm) := by
      simp [mul_assoc]
    _ = 1 * (((shiftFunctorComm C i j).app X).symm) := by rw [h₂]
    _ = (((shiftFunctorComm C i j).app X).symm) := by simp
have h₅ : (shiftComm X i j).symm = ((shiftFunctorComm C i j).app X).symm := by
  simp [shiftComm]
have h₆ : (shiftComm X i j).symm = ((shiftFunctorComm C i j).symm).app X := by
  rw [h₅, h₄]
have h₇ : (shiftComm X i j).symm = (shiftFunctorComm C j i).app X := by
  rw [h₆, h_symm]
have h₈ : (shiftComm X i j).symm = (shiftComm X j i) := by
  simp [shiftComm] at h₇ ⊢
  <;> exact h₇
have h₉ : (shiftComm X i j).symm.hom = (shiftComm X j i).hom := by
  rw [h₈]
exact h₉
```

**lean_error:** tail step 1/44 ('have h_symm : (shiftFunctorComm C i j).symm = shiftFunctorComm C j i := shiftFunctorComm_symm i j'): application type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 25.3s, verify 0.1s, in=822, out=502)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 18.7s, verify 0.3s, in=2718, out=2243)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [shiftComm] using
  congrArg (fun η => (η.app X).hom) (shiftFunctorComm_symm (C:=C) i j)
```

**lean_error:** tail step 1/2 ('simpa [shiftComm] using'): <stdin>:1:23: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 53.5s, verify 0.1s, in=2751, out=4890)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h_symm : (shiftComm X i j).symm = shiftComm X j i := by
  calc
    (shiftComm X i j).symm = ((shiftFunctorComm C i j).symm).app X := by simp [shiftComm]
    _ = (shiftFunctorComm C j i).app X := by rw [shiftFunctorComm_symm]
    _ = shiftComm X j i := by simp [shiftComm]
rw [h_symm]
<;> rfl
```

**lean_error:** tail step 1/7 ('have h_symm : (shiftComm X i j).symm = shiftComm X j i := by'): <stdin>:1:60: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 25.4s, verify 0.2s, in=2718, out=505)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.9s, verify 0.2s, in=2563, out=1718)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
dsimp [shiftComm]
simpa using
  (NatTrans.congr_app
    (congrArg (fun η => η.hom) (shiftFunctorComm_symm (C:=C) i j)) X)
```

**lean_error:** tail step 2/4 ('simpa using'): <stdin>:1:11: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 97.5s, verify 0.5s, in=3052, out=9596)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold shiftComm
have h : ((shiftFunctorComm C i j).app X).symm = ((shiftFunctorComm C i j).symm).app X := by rfl
rw [h]
have h2 : (shiftFunctorComm C i j).symm = shiftFunctorComm C j i := shiftFunctorComm_symm
rw [h2]
rfl
```

**lean_error:** tail step 4/6 ('have h2 : (shiftFunctorComm C i j).symm = shiftFunctorComm C j i := shiftFunctorComm_symm'): type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 83.5s, verify 0.1s, in=2716, out=2106)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [shiftFunctorComm_symm]
congr
```

**lean_error:** tail step 1/2 ('rw [shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
