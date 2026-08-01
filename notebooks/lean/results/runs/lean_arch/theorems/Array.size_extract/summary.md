# Array.size_extract   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
rw [size_extract_loop, size_empty, Nat.zero_add, Nat.sub_min_sub_right,
Nat.min_assoc, Nat.min_self]
```

**True premises at k:** `Array.size_extract_loop`, `Array.size_empty`, `Nat.zero_add`, `Nat.sub_min_sub_right`, `Nat.min_assoc`, `Nat.min_self`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.7s, in=265, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [extract.loop]
simp [Array.size, extract.loop._match_1]
rw [Nat.sub_min]
```

**lean_error:** tail step 1/3 ('simp [extract.loop]'): tactic 'simp' failed, nested error:

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=239, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [size, extract.loop]
split <;> simp [*] <;> omega
```

**lean_error:** tail step 1/2 ('simp [size, extract.loop]'): tactic 'simp' failed, nested error:

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.4s, in=254, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [extract.loop, min]
```

**lean_error:** tail step 1/1 ('simp [extract.loop, min]'): tactic 'simp' failed, nested error:

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 3.1s, verify 0.2s, in=1303, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [size_extract_loop, size_empty, Nat.zero_add]
rw [Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=1280, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [size_extract_loop, size_empty, Nat.zero_add, Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1292, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [extract.loop, size_empty, Nat.zero_add, Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]
```

**lean_error:** tail step 1/1 ('rw [extract.loop, size_empty, Nat.zero_add, Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=4637, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [size_extract_loop, size_empty, zero_add]
rw [sub_min_sub_right, min_assoc, min_self]
```

**lean_error:** tail step 1/2 ('rw [size_extract_loop, size_empty, zero_add]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=4636, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [size_extract_loop, size_empty, Nat.zero_add, Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.2s, in=4626, out=72)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [extract.loop, Array.size_empty]
simp [Nat.zero_add, Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]
```

**lean_error:** tail step 1/2 ('rw [extract.loop, Array.size_empty]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=4662, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [size_extract_loop, size_empty, zero_add]
rw [sub_min_sub_right, min_assoc, min_self]
```

**lean_error:** tail step 1/2 ('rw [size_extract_loop, size_empty, zero_add]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=5023, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [size_extract_loop, size_empty, Nat.zero_add]
rw [Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self, Nat.min_self]
```

**lean_error:** tail step 2/2 ('rw [Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self, Nat.min_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 1.3s, in=4651, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [extract.loop, size_empty, Nat.zero_add, Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]
```

**lean_error:** tail step 1/1 ('rw [extract.loop, size_empty, Nat.zero_add, Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
