# String.foldr_eq   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa using foldrAux_of_valid f [] s.1 [] a
```

**True premises at k:** `String.foldrAux_of_valid`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.1s, in=281, out=123)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 15.6s, verify 0.1s, in=227, out=1952)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.7s, verify 0.1s, in=226, out=516)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [String.foldr]
```

**final state (truncated):**
```
α : Type u_1
f : Char → α → α
s : String
a : α
⊢ foldrAux f a s (endPos s) 0 = List.foldr f a s.data
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.3s, verify 0.2s, in=698, out=2276)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [String.foldr] using
  (foldrAux_of_valid (f := f) (l := []) (m := s.data) (r := []) (a := a))
```

**lean_error:** tail step 1/2 ('simpa [String.foldr] using'): <stdin>:1:26: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 133.2s, verify 0.1s, in=649, out=17988)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h1 : foldr f a s = foldrAux f a s s.utf8Len 0 := by rfl
have h2 : foldrAux f a s s.utf8Len 0 = List.foldr f a s.data := by
  have h3 : s = ⟨([] : List Char) ++ (s.data : List Char) ++ ([] : List Char)⟩ := by rfl
  have h4 : utf8Len (([] : List Char)) + utf8Len (s.data : List Char) = s.utf8Len := by
    have h4₁ : utf8Len (([] : List Char)) = 0 := by simp [utf8Len]
    have h4₂ : utf8Len (s.data : List Char) = s.utf8Len := by rfl
    rw [h4₁, h4₂]
    <;> simp
  have h5 : utf8Len (([] : List Char)) = 0 := by simp [utf8Len]
  have h6 : foldrAux f a s s.utf8Len 0 = (s.data : List Char).foldr f a := by
    have h7 : foldrAux f a ⟨([] : List Char) ++ (s.data : List Char) ++ ([] : List Char)⟩ (utf8Len (([] : List Char)) + utf8Len (s.data : List Char)) (utf8Len (([] : List Char))) = (s.data : List Char).foldr f a := by
      apply String.foldrAux_of_valid
    have h8 : s = ⟨([] : List Char) ++ (s.data : List Char) ++ ([] : List Char)⟩ := by rw [h3]
    have h9 : s.utf8Len = utf8Len (([] : List Char)) + utf8Len (s.data : List Char) := by
      linarith
    have h10 : (0 : ℕ) = utf8Len (([] : List Char)) := by
      linarith
    calc
      foldrAux f a s s.utf8Len 0 = foldrAux f a s s.utf8Len 0 := rfl
      _ = foldrAux f a ⟨([] : List Char) ++ (s.data : List Char) ++ ([] : List Char)⟩ (utf8Len (([] : List Char)) + utf8Len (s.data : List Char)) (utf8Len (([] : List Char))) := by
        rw [h8]
        <;> simp [h9, h10]
        <;> try norm_num
        <;> try ring_nf
      _ = (s.data : List Char).foldr f a := by rw [h7]
  exact h6
rw [h1, h2]
```

**lean_error:** tail step 1/27 ('have h1 : foldr f a s = foldrAux f a s s.utf8Len 0 := by rfl'): invalid field notation, function 'String.utf8Len' does not have argument with type (String ...) that can be used, it must be explicit or implicit with a unique name

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.1s, verify 0.2s, in=631, out=526)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [String.foldr]
have := foldrAux_of_valid f "" s "" a
simpa using this
```

**lean_error:** tail step 2/3 ('have := foldrAux_of_valid f "" s "" a'): application type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.9s, verify 0.1s, in=2082, out=1649)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases s with
| mk data =>
  simpa [String.foldr, List.append_nil, List.nil_append] using
    (foldrAux_of_valid (f:=f) (l:=[]) (m:=data) (r:=[]) (a:=a))
```

**lean_error:** tail step 1/4 ('cases s with'): <stdin>:1:12: unexpected end of input; expected '|'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 37.8s, verify 0.1s, in=2061, out=4970)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem String.foldr_eq {α : Type u} (f : Char → α → α) (a : α) (s : String) :
    foldr f a s = List.foldr f a s.data := by
  have h1 : foldr f a s = foldrAux f a s s.size 0 := by
    rw [String.foldr]
    <;> simp [String.foldrAux]
    <;> rfl
  rw [h1]
  have h2 : s.size = utf8Len s.data := by
    rw [String.size]
    <;> rfl
  rw [h2]
  have h3 : s = ⟨s.data⟩ := by rfl
  rw [h3]
  have h4 : foldrAux f a ⟨s.data⟩ (utf8Len s.data) 0 = (s.data).foldr f a := by
    have h5 : foldrAux f a ⟨([] : List Char) ++ s.data ++ ([] : List Char)⟩ (utf8Len ([] : List Char) + utf8Len s.data) (utf8Len ([] : List Char)) = (s.data).foldr f a := by
      apply String.foldrAux_of_valid
    have h6 : ⟨s.data⟩ = ⟨([] : List Char) ++ s.data ++ ([] : List Char)⟩ := by
      simp [List.append_assoc]
    have h7 : utf8Len s.data = utf8Len ([] : List Char) + utf8Len s.data := by
      simp [utf8Len_nil]
      <;> ring
    have h8 : 0 = utf8Len ([] : List Char) := by simp [utf8Len_nil]
    calc
      foldrAux f a ⟨s.data⟩ (utf8Len s.data) 0 = foldrAux f a ⟨([] : List Char) ++ s.data ++ ([] : List Char)⟩ (utf8Len s.data) 0 := by rw [h6]
      _ = foldrAux f a ⟨([] : List Char) ++ s.data ++ ([] : List Char)⟩ (utf8Len ([] : List Char) + utf8Len s.data) (utf8Len ([] : List Char)) := by rw [h7, h8]
      _ = (s.data).foldr f a := by rw [h5]
  rw [h4]
```

**lean_error:** tail step 1/27 ('theorem String.foldr_eq {α : Type u} (f : Char → α → α) (a : α) (s : String) :'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 22.3s, verify 0.5s, in=2014, out=2179)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [String.foldrAux_of_valid f [] s.data [] a]
simp
```

**lean_error:** tail step 1/2 ('rw [String.foldrAux_of_valid f [] s.data [] a]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.5s, verify 0.1s, in=1933, out=1279)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 106.7s, verify 0.1s, in=2261, out=14373)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
dsimp [String.foldr]
<;>
(try
  {
    have h₁ : foldrAux f a ⟨[] ++ s.data ++ []⟩ (utf8Len [] + utf8Len s.data) (utf8Len []) = s.data.foldr f a := by
      apply String.foldrAux_of_valid
    have h₂ : ⟨[] ++ s.data ++ []⟩ = s := by
      ext <;> simp [List.append_assoc]
      <;> aesop
    have h₃ : utf8Len [] = 0 := by simp
    have h₄ : utf8Len s = utf8Len s.data := by
      simp [String.utf8Len]
      <;> rfl
    calc
      foldrAux f a s (utf8Len s) 0 = foldrAux f a s (utf8Len s.data) 0 := by rw [h₄]
      _ = foldrAux f a s (utf8Len [] + utf8Len s.data) (utf8Len []) := by
        simp [h₃]
        <;> ring
      _ = foldrAux f a ⟨[] ++ s.data ++ []⟩ (utf8Len [] + utf8Len s.data) (utf8Len []) := by
        congr 1 <;> ext <;> simp [List.append_assoc]
        <;> aesop
      _ = s.data.foldr f a := by rw [h₁]
  })
```

**lean_error:** tail step 2/23 ('<;>'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.2s, in=2004, out=495)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [String.foldr]
have := foldrAux_of_valid f "" s.data "" a
simpa using this
```

**lean_error:** tail step 2/3 ('have := foldrAux_of_valid f "" s.data "" a'): application type mismatch
