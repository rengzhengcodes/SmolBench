# String.data_dropWhile   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
rw [dropWhile_eq]
```

**True premises at k:** `String.dropWhile_eq`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.3s, in=270, out=281)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 9.2s, verify 0.1s, in=214, out=1104)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=215, out=413)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.0s, verify 0.1s, in=480, out=1169)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [String.dropWhile_eq]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 28.1s, verify 0.1s, in=419, out=3353)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [String.dropWhile_eq]
<;> simp [String.data_mk]
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.4s, verify 0.1s, in=418, out=514)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [String.dropWhile_eq]
simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.0s, verify 0.1s, in=1089, out=600)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [String.dropWhile_eq]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 38.7s, verify 0.1s, in=1036, out=4597)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem String.data_dropWhile {p : Char → Bool} {s : String} :
    (dropWhile s p).data = List.dropWhile p s.data := by
  have h_main : s.dropWhile p = ⟨s.1.dropWhile p⟩ := by
    apply String.dropWhile_eq
  
  have h_final : (dropWhile s p).data = List.dropWhile p s.data := by
    rw [h_main]
    cases s with
    | mk l =>
      -- After case analysis, s = ⟨l⟩, so s.1 = l and s.data = l.
      -- The goal becomes (⟨l.dropWhile p⟩).data = List.dropWhile p l.
      -- By definition of the String constructor, (⟨l.dropWhile p⟩).data = l.dropWhile p.
      -- And List.dropWhile p l is definitionally equal to l.dropWhile p.
      <;> rfl
  
  exact h_final
```

**lean_error:** tail step 1/14 ('theorem String.data_dropWhile {p : Char → Bool} {s : String} :'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.4s, verify 0.1s, in=1043, out=749)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [String.dropWhile_eq]
<;> rfl
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.2s, verify 0.1s, in=1044, out=910)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [String.dropWhile_eq]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 148.5s, verify 1.0s, in=1150, out=18893)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
cases s with
| data valid =>
  simp [dropWhile_eq, String.data, Prod.mk.injEq]
  <;> rfl
```

**lean_error:** tail step 1/4 ('cases s with'): <stdin>:1:12: unexpected end of input; expected '|'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.1s, verify 0.1s, in=1044, out=586)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [String.dropWhile_eq]
simp
```
