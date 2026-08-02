# List.insertNth_eq_insertNthTR   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp [insertNthTR, insertNthTR_go_eq]
```

**True premises at k:** `List.insertNthTR`, `List.insertNthTR_go_eq`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.1s, in=282, out=908)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction f generalizing l with
| zero =>
    cases l <;> rfl
| succ f ih =>
    cases l with
    | nil => rfl
    | cons hd tl =>
        simp [insertNth, insertNthTR, ih]
```

**lean_error:** tail step 1/8 ('induction f generalizing l with'): <stdin>:1:31: unexpected end of input; expected '|'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 37.7s, verify 0.1s, in=230, out=4293)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.5s, verify 0.1s, in=231, out=550)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_all [insertNth, insertNthTR]
```

**final state (truncated):**
```
case h.h.h.h
α : Type u_1
f : Nat
n : α
l : List α
⊢ modifyNthTail (cons n) f l = insertNthTR.go n f l #[]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.4s, verify 0.1s, in=751, out=3438)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [List.insertNthTR] using
  (List.insertNthTR_go_eq (a:=n) (acc:=#[]) f l)
```

**lean_error:** tail step 1/2 ('simpa [List.insertNthTR] using'): <stdin>:1:30: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 153.0s, verify 0.1s, in=730, out=19954)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h : insertNthTR f n l = insertNth f n l := by
  dsimp [insertNthTR]
  have h₂ : insertNthTR.go f l (#[] : Array α) = (#[] : Array α).data ++ insertNth f n l := by
    apply insertNthTR_go_eq with f l
    <;> simp [insertNthTR]
    <;> try norm_num
    <;> try aesop
  rw [h₂]
  simp [List.append_Nil]
exact h.symm
```

**lean_error:** tail step 1/10 ('have h : insertNthTR f n l = insertNth f n l := by'): <stdin>:1:50: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.2s, verify 0.2s, in=728, out=635)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [insertNthTR]
rw [insertNthTR_go_eq]
simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.3s, verify 0.1s, in=2113, out=1383)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [List.insertNthTR] using (List.insertNthTR_go_eq (a:=n) (acc:=#[]) (n:=f) (l:=l)).symm
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 111.1s, verify 0.2s, in=2109, out=13954)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [insertNthTR]
rw [insertNthTR_go_eq]
<;> simp [Array.data_def]
```

**lean_error:** tail step 3/3 ('<;> simp [Array.data_def]'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.9s, verify 0.1s, in=2119, out=812)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [insertNthTR, insertNthTR_go_eq]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.8s, verify 0.1s, in=1986, out=1246)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [insertNthTR, insertNthTR_go_eq]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 243.6s, verify 0.1s, in=2342, out=32357)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
dsimp [insertNthTR] at *
have h : go f l #[] = insertNth f n l := by
  have h₁ : go f l #[] = insertNthTR.go f l #[] := by rfl
  rw [h₁]
  have h₂ : insertNthTR.go f l #[] = (#[]).data ++ insertNth f n l := by
    apply insertNthTR_go_eq
    <;> try simp_all [insertNthTR.go]
    <;> try omega
    <;> try aesop
  rw [h₂]
  simp
  <;>
  (try decide) <;>
  (try ring_nf) <;>
  (try simp_all [insertNth]) <;>
  (try omega)
```

**lean_error:** tail step 2/16 ('have h : go f l #[] = insertNth f n l := by'): <stdin>:1:43: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.8s, verify 0.1s, in=2101, out=805)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [insertNthTR, insertNthTR_go_eq]
```
