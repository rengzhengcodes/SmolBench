# Array.get_extract_loop_lt   (k=4, 5 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
rw [extract_loop_eq_aux]
```

**True premises at k:** `Array.extract_loop_eq_aux`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.5s, in=317, out=898)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [extract.loop]
```

**lean_error:** tail step 1/1 ('simpa [extract.loop]'): tactic 'simp' failed, nested error:

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 73.6s, verify 0.2s, in=262, out=9243)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold extract.loop
<;> rfl
```

**lean_error:** tail step 2/2 ('<;> rfl'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.4s, in=265, out=535)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [extract.loop, Array.append]
```

**lean_error:** tail step 1/1 ('simp [extract.loop, Array.append]'): tactic 'simp' failed, nested error:

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 13.0s, verify 0.1s, in=709, out=3016)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (extract_loop_eq_aux (as:=as) (bs:=bs) (size:=size) (start:=start))
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 27.4s, verify 0.1s, in=678, out=3477)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Array.extract_loop_eq_aux
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.6s, verify 0.1s, in=669, out=539)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact extract_loop_eq_aux as bs size start
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 15.8s, verify 0.1s, in=2184, out=3732)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (extract_loop_eq_aux (as:=as) (bs:=bs) (size:=size) (start:=start))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 21.1s, verify 0.1s, in=2181, out=2666)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Array.extract_loop_eq_aux
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.5s, verify 0.1s, in=2154, out=535)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact extract_loop_eq_aux as bs size start
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.1s, verify 0.1s, in=2034, out=2275)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (extract_loop_eq_aux (as:=as) (bs:=bs) (size:=size) (start:=start))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 107.1s, verify 0.1s, in=2410, out=13938)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
all_goals {
  have h : extract.loop as size start bs = bs ++ extract.loop as size start #[] := Array.extract_loop_eq_aux
  try { 
    rw [h]
    <;> rfl
  }
  <;>
  (try {
    intro j
    have h₁ : j.val < Array.size (bs ++ extract.loop as size start #[]) := by
      have h₂ : j.val < Array.size (extract.loop as size start bs) := j.is_lt
      have h₃ : Array.size (extract.loop as size start bs) = Array.size (bs ++ extract.loop as size start #[]) := by rw [h]
      linarith
    rw [h]
    <;> simp_all [Array.get_idx_eq_get_idx]
    <;> rfl
  })
}
```

**lean_error:** tail step 1/18 ('all_goals {'): <stdin>:1:11: unexpected end of input; expected '}'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.6s, verify 0.1s, in=2144, out=534)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Array.extract_loop_eq_aux
```
