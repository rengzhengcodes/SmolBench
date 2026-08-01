# CategoryTheory.Groupoid.Free.lift_unique   (k=9, 10 tactics total)

file: `Mathlib/CategoryTheory/Groupoid/FreeGroupoid.lean`  

**Ground-truth tail (from k):**
```lean
convert this <;> simp only [inv_eq_inv]
```

**True premises at k:** `CategoryTheory.Groupoid.inv_eq_inv`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=428, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.2s, in=402, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [CategoryTheory.inv_eq_inv]
exact this
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.inv_eq_inv]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 57.3s, verify 5.2s, in=417, out=3472)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.3s, in=776, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inv_eq_inv] at this
exact this
```

**lean_error:** tail step 1/2 ('rw [inv_eq_inv] at this'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.3s, in=753, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [this]
simp only [inv_eq_inv]
```

**lean_error:** tail step 1/2 ('rw [this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.3s, in=765, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [this]
exact inv_eq_inv _
```

**lean_error:** tail step 1/2 ('rw [this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.3s, in=876, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [this]
exact this
```

**lean_error:** tail step 1/2 ('rw [this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.3s, in=853, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← this]
simp only [CategoryTheory.Groupoid.inv_eq_inv]
```

**lean_error:** tail step 1/2 ('rw [← this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.2s, in=865, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [this]
exact inv_eq_inv _
```

**lean_error:** tail step 1/2 ('rw [this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.2s, in=900, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inv_eq_inv] at this
exact this
```

**lean_error:** tail step 1/2 ('rw [inv_eq_inv] at this'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.3s, in=888, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [this]
simp only [inv_eq_inv]
```

**lean_error:** tail step 1/2 ('rw [this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.0s, in=889, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail
