# String.offsetOfPos_of_valid   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa using offsetOfPosAux_of_valid [] l r 0
```

**True premises at k:** `String.offsetOfPosAux_of_valid`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.8s, verify 1.0s, in=246, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [offsetOfPos]
simp [utf8Len]
```

**lean_error:** tail step 2/2 ('simp [utf8Len]'): tactic 'simp' failed, nested error:

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=246, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold offsetOfPos
rw [utf8Len_eq_stringLen l]
rw [length_append]
simp
```

**lean_error:** tail step 2/4 ('rw [utf8Len_eq_stringLen l]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.2s, verify 0.2s, in=246, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold offsetOfPos
rw [utf8Len_go_eq_utf8Len]
rw [List.length_append]
simp
```

**lean_error:** tail step 2/4 ('rw [utf8Len_go_eq_utf8Len]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.6s, verify 0.9s, in=246, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [offsetOfPos]
rw [utf8Len_go_eq_utf8Len]
rw [List.length_append]
simp
```

**lean_error:** tail step 2/4 ('rw [utf8Len_go_eq_utf8Len]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.9s, verify 0.1s, in=653, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [offsetOfPos, offsetOfPosAux_of_valid l [] r 0]
simp
```

**lean_error:** tail step 1/2 ('rw [offsetOfPos, offsetOfPosAux_of_valid l [] r 0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=653, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [offsetOfPos, offsetOfPosAux_of_valid [] l r 0]
simp [utf8Len]
```

**lean_error:** tail step 1/2 ('rw [offsetOfPos, offsetOfPosAux_of_valid [] l r 0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.2s, in=653, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold offsetOfPos
rw [offsetOfPosAux_of_valid [] l r 0]
simp [List.length]
```

**lean_error:** tail step 2/3 ('rw [offsetOfPosAux_of_valid [] l r 0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 3.5s, verify 0.2s, in=653, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold offsetOfPos
rw [offsetOfPosAux_of_valid l [] r 0] 
simp [utf8Len, List.length_append]
```

**lean_error:** tail step 2/3 ('rw [offsetOfPosAux_of_valid l [] r 0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
