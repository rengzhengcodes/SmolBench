# ByteArray.get_append_right   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/ByteArray.lean`  

**Ground-truth tail (from k):**
```lean
exact Array.get_append_right hle
```

**True premises at k:** `Array.get_append_right`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✘ | ✓ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=270, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [append_eq_data, get_eq_get_of_lt_size h]
rw [get_append_right_eq _ hle]
```

**lean_error:** tail step 1/2 ('rw [append_eq_data, get_eq_get_of_lt_size h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=244, out=41)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Array.append_data]
simp [Array.get]
rw [getElem_eq_data_get]
simp [Nat.sub_lt_left_of_lt_add hle h']
rw [getElem_eq_data_get]
```

**lean_error:** tail step 1/5 ('rw [Array.append_data]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=259, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [get_append, hle]
```

**lean_error:** tail step 1/1 ('rw [get_append, hle]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=631, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [append_data]
rw [get_append_right hle]
```

**lean_error:** tail step 1/2 ('rw [append_data]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=601, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
conv =>
  lhs
  rw [← List.get_append_right h hle]
apply List.get_of_eq
rw [append_data]
```

**lean_error:** tail step 1/5 ('conv =>'): <stdin>:1:7: unexpected end of input; expected '{'

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=620, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Array.get_append_right
exact hle
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1577, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Array.get_append_right hle h'
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1554, out=50)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
conv =>
  lhs; rw [← List.get_append_right (h:=Nat.not_lt_of_ge hle)]
  rhs; congr; rw [size_to_data]
apply List.get_of_eq; rw [data_toArray, append_data]
```

**lean_error:** tail step 1/4 ('conv =>'): <stdin>:1:7: unexpected end of input; expected '{'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=1566, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Array.get_append_right
exact hle
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1601, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [append_data]
apply Array.get_append_right hle h'
```

**lean_error:** tail step 1/2 ('rw [append_data]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=1681, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Array.get_append_right hle h'
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.1s, in=1590, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Array.get_append_right
```

**final state (truncated):**
```
case hle
i : Nat
a b : ByteArray
hle : size a ≤ i
h : i < size (a ++ b)
h' : optParam (i - size a < size b) ⋯
...
```
