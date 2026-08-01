# Array.get_extract_loop_lt   (k=4, 5 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
rw [extract_loop_eq_aux]
```

**True premises at k:** `Array.extract_loop_eq_aux`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.4s, in=280, out=79)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [extract.loop]
split
next => rfl
generalize hlt
revert i
induction bs
rfl
intro i hlt
cases i
rfl
rename_i i
rw [Array.size_push, Nat.succ_lt_succ_iff] at hlt
rw [Array.push_append]
specialize (ibs i hlt)
rw [ibs]
done
```

**lean_error:** tail step 3/16 ('next => rfl'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.8s, in=252, out=36)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [extract.loop]
congr
simp [Array.ext_iff]
intro i h1 h2
simp [*] at h2 
contradiction
simp [*]
```

**lean_error:** tail step 1/7 ('simp [extract.loop]'): tactic 'simp' failed, nested error:

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=269, out=124)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [extract.loop_def]
rw [extract.loop_def]
rw [Array.append_assoc]
```

**lean_error:** tail step 1/3 ('rw [extract.loop_def]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=664, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Array.extract_loop_eq_aux as bs size start
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=636, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Array.extract_loop_eq_aux]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=653, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply extract_loop_eq_aux
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=2097, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact extract_loop_eq_aux as bs size start
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=2079, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Array.extract_loop_eq_aux]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=2086, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply extract_loop_eq_aux
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=2122, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact extract_loop_eq_aux as bs size start
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=2259, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Array.extract_loop_eq_aux]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=2111, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact extract_loop_eq_aux as bs size start
```
