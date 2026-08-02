# List.modifyNth_eq_modifyNthTR   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp [modifyNthTR, modifyNthTR_go_eq]
```

**True premises at k:** `List.modifyNthTR`, `List.modifyNthTR_go_eq`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.5s, in=284, out=908)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction n generalizing l with
| zero =>
    cases l <;> rfl
| succ n ih =>
    cases l with
    | nil => rfl
    | cons a t =>
        simp [modifyNth, modifyNthTR, ih]
```

**lean_error:** tail step 1/8 ('induction n generalizing l with'): <stdin>:1:31: unexpected end of input; expected '|'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 29.8s, verify 0.1s, in=232, out=3567)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l with
| nil =>
  intro n f
  simp [modifyNth, modifyNthTR]
| cons x xs ih =>
  intro n f
  cases n with
  | zero =>
    simp [modifyNth, modifyNthTR]
  | succ n =>
    simp [modifyNth, modifyNthTR, Nat.succ_eq_add_one, List.cons]
    <;>
    (try {
      apply congr_arg (fun l => x :: l)
      <;> exact ih
    }) <;>
    (try { rfl })
```

**lean_error:** tail step 1/17 ('induction l with'): <stdin>:1:16: unexpected end of input; expected '|'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 11.1s, verify 0.1s, in=233, out=506)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [modifyNth, modifyNthTR]
```

**final state (truncated):**
```
case h.h.h.h
α : Type u_1
f : α → α
n : Nat
l : List α
⊢ modifyNthTail (modifyHead f) n l = modifyNthTR.go f l n #[]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.8s, verify 0.1s, in=770, out=1251)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [modifyNthTR, modifyNthTR_go_eq]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 41.6s, verify 0.1s, in=758, out=4951)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem List.modifyNth_eq_modifyNthTR {α : Type u_1} (f : α → α) (n : Nat) (l : List α) :
    modifyNth f n l = modifyNthTR f n l := by
  funext α f n l
  have h_main : modifyNthTR f n l = modifyNth f n l := by
    dsimp only [modifyNthTR]
    calc
      modifyNth f n l = go l n #[] := by rfl
      _ = modifyNthTR.go f l n #[] := by rfl
      _ = (#[]).data ++ modifyNth f n l := by apply modifyNthTR_go_eq
      _ = [] ++ modifyNth f n l := by simp
      _ = modifyNth f n l := by simp
  exact h_main
```

**lean_error:** tail step 1/12 ('theorem List.modifyNth_eq_modifyNthTR {α : Type u_1} (f : α → α) (n : Nat) (l : List α) :'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 12.3s, verify 0.2s, in=750, out=634)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [modifyNthTR]
rw [modifyNthTR_go_eq]
simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=2031, out=727)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [modifyNthTR] using (modifyNthTR_go_eq (f:=f) (acc:=#[]) l n)
```

**lean_error:** tail step 1/1 ('simpa [modifyNthTR] using (modifyNthTR_go_eq (f:=f) (acc:=#[]) l n)'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 64.7s, verify 0.2s, in=2036, out=7646)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [modifyNthTR]
rw [List.modifyNthTR_go_eq]
simp [Array.data_mk]
<;> simp [List.nil_append]
```

**lean_error:** tail step 3/4 ('simp [Array.data_mk]'): unknown constant 'Array.data_mk'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 12.0s, verify 0.1s, in=2037, out=594)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [modifyNthTR, modifyNthTR_go_eq]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.1s, in=1914, out=1045)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [modifyNthTR] using (modifyNthTR_go_eq (f:=f) (acc:=#[]) (l:=l) (n:=n))
```

**lean_error:** tail step 1/1 ('simpa [modifyNthTR] using (modifyNthTR_go_eq (f:=f) (acc:=#[]) (l:=l) (n:=n))'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 82.5s, verify 0.1s, in=2252, out=10079)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h : modifyNthTR f n l = modifyNth f n l := by
  dsimp [modifyNthTR]
  rw [modifyNthTR_go_eq]
  <;> simp [List.nil_append]
  <;> rfl
rw [h]
<;> rfl
```

**lean_error:** tail step 1/7 ('have h : modifyNthTR f n l = modifyNth f n l := by'): <stdin>:1:50: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 11.3s, verify 0.1s, in=2022, out=531)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [modifyNthTR, modifyNthTR_go_eq]
```
