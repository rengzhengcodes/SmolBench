# String.foldr_eq   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa using foldrAux_of_valid f [] s.1 [] a
```

**True premises at k:** `String.foldrAux_of_valid`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 7.6s, verify 0.1s, in=243, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold foldr String.foldr
rw [String.casesOn s]
```

**lean_error:** tail step 1/2 ('unfold foldr String.foldr'): tactic 'unfold' failed to unfold 'String.foldr' at

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 1.7s, in=217, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [foldr]
simp [String.foldr_eq]
```

**lean_error:** tail step 2/2 ('simp [String.foldr_eq]'): simp made no progress

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 16.4s, verify 0.1s, in=232, out=971)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [String.foldr]
```

**final state (truncated):**
```
α : Type u_1
f : Char → α → α
s : String
a : α
⊢ foldrAux f a s (endPos s) 0 = List.foldr f a s.data
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 7.7s, verify 0.1s, in=634, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [foldr, String.casesOn s]
  exact foldrAux_of_valid f [] s.data [] a
  exact foldrAux_of_valid f [] [] s.data a
```

**lean_error:** tail step 1/3 ('rw [foldr, String.casesOn s]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=606, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [String.foldr]
simp [String.foldrAux_of_valid]
simp [List.foldr_eq]
```

**lean_error:** tail step 2/3 ('simp [String.foldrAux_of_valid]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 9.3s, verify 0.1s, in=623, out=542)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [foldr, foldrAux_of_valid]
```

**lean_error:** tail step 1/1 ('rw [foldr, foldrAux_of_valid]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 3.1s, in=1966, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold foldr String.foldr
simp only [foldrAux_of_valid]
```

**lean_error:** tail step 1/2 ('unfold foldr String.foldr'): tactic 'unfold' failed to unfold 'String.foldr' at

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.2s, in=1952, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [String.foldr, foldrAux_of_valid]
simp [List.foldr_eq]
```

**lean_error:** tail step 2/2 ('simp [List.foldr_eq]'): unknown constant 'List.foldr_eq'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 21.0s, verify 0.2s, in=1955, out=1253)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [foldr]
apply foldrAux_of_valid f [] s.data [] a
```

**lean_error:** tail step 2/2 ('apply foldrAux_of_valid f [] s.data [] a'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 3.0s, in=1991, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold foldr
exact foldrAux_of_valid f [] s.data [] a
```

**lean_error:** tail step 2/2 ('exact foldrAux_of_valid f [] s.data [] a'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=2117, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [String.foldr]
simp [String.valid, String.foldrAux_of_valid]
rw [List.foldr_eq]
rfl
```

**lean_error:** tail step 2/4 ('simp [String.valid, String.foldrAux_of_valid]'): unknown constant 'String.valid'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 0.3s, in=1980, out=243)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [foldr, foldrAux_of_valid]
```

**lean_error:** tail step 1/1 ('rw [foldr, foldrAux_of_valid]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
