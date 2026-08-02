# String.offsetOfPos_of_valid   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa using offsetOfPosAux_of_valid [] l r 0
```

**True premises at k:** `String.offsetOfPosAux_of_valid`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=284, out=1303)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l with
| nil =>
    simp [utf8Len, offsetOfPos]
| cons a t ih =>
    simp [utf8Len, offsetOfPos, List.length, ih, Nat.add_comm, Nat.add_left_comm, Nat.add_assoc]
```

**lean_error:** tail step 1/5 ('induction l with'): <stdin>:1:16: unexpected end of input; expected '|'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 227.3s, verify 0.1s, in=228, out=28124)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : offsetOfPos (l ++ r) (utf8Len l + 0) = l.length + offsetOfPos r 0 := by
  apply offsetOfPos_concat_add
have h₂ : offsetOfPos r 0 = 0 := by
  apply offsetOfPos_zero
have h₃ : offsetOfPos (l ++ r) (utf8Len l) = l.length := by
  rw [h₁]
  rw [h₂]
  <;> simp [add_zero]
exact h₃
```

**lean_error:** tail step 1/9 ('have h₁ : offsetOfPos (l ++ r) (utf8Len l + 0) = l.length + offsetOfPos r 0 := by'): <stdin>:1:81: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=229, out=450)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [offsetOfPos, utf8Len]
```

**lean_error:** tail step 1/1 ('simp [offsetOfPos, utf8Len]'): tactic 'simp' failed, nested error:

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 12.3s, verify 0.2s, in=718, out=1996)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold offsetOfPos
  simpa using (offsetOfPosAux_of_valid [] l r 0)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 181.7s, verify 0.1s, in=659, out=22407)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold offsetOfPos
<;> apply String.offsetOfPosAux_of_valid ([] : List Char) l r 0
<;> simp [List.append_assoc]
<;> rfl
```

**lean_error:** tail step 2/4 ('<;> apply String.offsetOfPosAux_of_valid ([] : List Char) l r 0'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 43.9s, verify 0.2s, in=647, out=4690)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold offsetOfPos
rw [String.offsetOfPosAux_of_valid l [] r 0]
simp
```

**lean_error:** tail step 2/3 ('rw [String.offsetOfPosAux_of_valid l [] r 0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.9s, verify 0.2s, in=2216, out=908)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold offsetOfPos
simpa using offsetOfPosAux_of_valid [] l r 0
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 107.7s, verify 0.1s, in=2173, out=12455)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem String.offsetOfPos_of_valid {l r : List Char} :
    offsetOfPos { data := l ++ r } { byteIdx := utf8Len l } = List.length l := by
  have h_main : offsetOfPosAux (l ++ r) (utf8Len l) 0 0 = List.length l := by
    have h₁ : offsetOfPosAux ([] ++ l ++ r) (utf8Len [] + utf8Len l) (utf8Len []) 0 = 0 + l.length := by
      apply offsetOfPosAux_of_valid
    have h₂ : [] ++ l ++ r = l ++ r := by simp
    have h₃ : utf8Len [] + utf8Len l = utf8Len l := by
      simp [utf8Len]
      <;> rfl
    have h₄ : utf8Len [] = 0 := by simp [utf8Len]
    have h₅ : 0 + l.length = l.length := by simp
    have h₆ : offsetOfPosAux (l ++ r) (utf8Len l) 0 0 = List.length l := by
      calc
        offsetOfPosAux (l ++ r) (utf8Len l) 0 0 = offsetOfPosAux ([] ++ l ++ r) (utf8Len [] + utf8Len l) (utf8Len []) 0 := by
          simp [h₂, h₃, h₄]
        _ = 0 + l.length := by rw [h₁]
        _ = l.length := by rw [h₅]
    exact h₆
  
  have h_final : offsetOfPos { data := l ++ r } { byteIdx := utf8Len l } = List.length l := by
    dsimp only [offsetOfPos]
    <;> rw [h_main]
    <;> simp [List.length]
  
  apply h_final
```

**lean_error:** tail step 1/23 ('theorem String.offsetOfPos_of_valid {l r : List Char} :'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 16.2s, verify 0.2s, in=2142, out=1591)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [String.offsetOfPos]
rw [String.offsetOfPosAux_of_valid [] l r 0]
simp
```

**lean_error:** tail step 2/3 ('rw [String.offsetOfPosAux_of_valid [] l r 0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.0s, verify 0.1s, in=2052, out=2115)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [offsetOfPos] using
  offsetOfPosAux_of_valid [] l r 0
```

**lean_error:** tail step 1/2 ('simpa [offsetOfPos] using'): <stdin>:1:25: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 118.7s, verify 0.1s, in=2401, out=13713)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : offsetOfPos { data := l ++ r } { byteIdx := utf8Len l } = offsetOfPosAux ⟨l ++ r⟩ (utf8Len l) 0 := by sorry
have h₂ : offsetOfPosAux ⟨l ++ r⟩ (utf8Len l) 0 = List.length l := by sorry
have h₃ : offsetOfPos { data := l ++ r } { byteIdx := utf8Len l } = List.length l := by
  rw [h₁]
  rw [h₂]
```

**lean_error:** tail step 1/5 ('have h₁ : offsetOfPos { data := l ++ r } { byteIdx := utf8Len l } = offsetOfPosAux ⟨l ++ r⟩ (utf8Len l) 0 := by sorry'): application type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.2s, in=2133, out=646)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold String.offsetOfPos
rw [String.offsetOfPosAux_of_valid l [] r 0]
simp
```

**lean_error:** tail step 2/3 ('rw [String.offsetOfPosAux_of_valid l [] r 0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
