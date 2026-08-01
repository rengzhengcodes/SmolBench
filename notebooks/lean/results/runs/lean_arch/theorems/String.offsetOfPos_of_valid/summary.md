# String.offsetOfPos_of_valid   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa using offsetOfPosAux_of_valid [] l r 0
```

**True premises at k:** `String.offsetOfPosAux_of_valid`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=246, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold offsetOfPos
rw [utf8Len_eq_stringLen l]
rw [List.length_append l r]
simp
```

**lean_error:** tail step 2/4 ('rw [utf8Len_eq_stringLen l]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=220, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [String.offsetOfPos, utf8Len, String.utf8ByteSize]
rfl
```

**lean_error:** tail step 1/2 ('simp [String.offsetOfPos, utf8Len, String.utf8ByteSize]'): tactic 'simp' failed, nested error:

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=235, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [offsetOfPos, utf8Len]
```

**lean_error:** tail step 1/1 ('simp [offsetOfPos, utf8Len]'): tactic 'simp' failed, nested error:

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=653, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold offsetOfPos
rw [offsetOfPosAux_of_valid [] l r 0]
simp [List.length]
```

**lean_error:** tail step 2/3 ('rw [offsetOfPosAux_of_valid [] l r 0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=624, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [String.offsetOfPos, String.offsetOfPosAux_of_valid [] l r 0]
simp [Nat.zero_add]
```

**lean_error:** tail step 2/2 ('simp [Nat.zero_add]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 74.1s, verify 0.1s, in=642, out=4587)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply offsetOfPosAux_of_valid [] l r 0
```

**lean_error:** tail step 1/1 ('apply offsetOfPosAux_of_valid [] l r 0'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=2096, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold offsetOfPos
rw [utf8Len_append]
exact offsetOfPosAux_of_valid [] l r 0
```

**lean_error:** tail step 2/3 ('rw [utf8Len_append]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.7s, in=2076, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [String.offsetOfPos, offsetOfPosAux_of_valid [] l r 0]
simp [utf8Len, String.utf8ByteSize]
```

**lean_error:** tail step 2/2 ('simp [utf8Len, String.utf8ByteSize]'): tactic 'simp' failed, nested error:

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=2085, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [offsetOfPos, offsetOfPosAux_of_valid l [] r 0]
simp [Nat.add_zero, List.length_append]
```

**lean_error:** tail step 1/2 ('rw [offsetOfPos, offsetOfPosAux_of_valid l [] r 0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.2s, in=2121, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold offsetOfPos
rw [utf8Len_eq_list_length]
exact offsetOfPosAux_of_valid [] l r 0
```

**lean_error:** tail step 2/3 ('rw [utf8Len_eq_list_length]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 1.3s, in=2257, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [String.offsetOfPos, String.offsetOfPosAux_of_valid l r [] 0]
simp [utf8Len, List.length]
```

**lean_error:** tail step 2/2 ('simp [utf8Len, List.length]'): tactic 'simp' failed, nested error:

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 68.3s, verify 0.1s, in=2110, out=4226)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply offsetOfPosAux_of_valid [] l r 0
```

**lean_error:** tail step 1/1 ('apply offsetOfPosAux_of_valid [] l r 0'): tactic 'apply' failed, failed to unify
