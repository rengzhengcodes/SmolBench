# String.data_dropWhile   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
rw [dropWhile_eq]
```

**True premises at k:** `String.dropWhile_eq`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✓ | ✓ |
| `hint:3` | ✘ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=232, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold dropWhile
rw [String.data_mk]
```

**lean_error:** tail step 2/2 ('rw [String.data_mk]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.8s, in=206, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dropWhile, String.dropWhile]
simp [List.dropWhile_eq_dropWhileP, List.dropWhileP]
```

**lean_error:** tail step 2/2 ('simp [List.dropWhile_eq_dropWhileP, List.dropWhileP]'): unknown constant 'List.dropWhile_eq_dropWhileP'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 15.5s, verify 0.1s, in=221, out=962)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dropWhile]
```

**final state (truncated):**
```
p : Char → Bool
s : String
⊢ (Substring.toString (Substring.dropWhile (toSubstring s) p)).data = List.dropWhile p s.data
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=429, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [String.dropWhile_eq],
cases s,
refl
```

**lean_error:** tail step 1/3 ('rw [String.dropWhile_eq],'): <stdin>:1:24: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=403, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [String.dropWhile_eq]
simp only [String.mk_val]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=418, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [dropWhile_eq]
rfl
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1022, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [String.dropWhile_eq],
exact rfl
```

**lean_error:** tail step 1/2 ('rw [String.dropWhile_eq],'): <stdin>:1:24: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=1006, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [String.dropWhile_eq]
simp only [Subtype.mk.injEq, List.dropWhile]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=1011, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [dropWhile_eq]
rfl
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1046, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [String.dropWhile_eq],
cases s,
refl
```

**lean_error:** tail step 1/3 ('rw [String.dropWhile_eq],'): <stdin>:1:24: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=1087, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [String.dropWhile_eq]
simp only [Subtype.mk.injEq, List.dropWhile]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1035, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [dropWhile_eq, String.eta]
```

**lean_error:** tail step 1/1 ('rw [dropWhile_eq, String.eta]'): tactic 'rewrite' failed, equality or iff proof expected
