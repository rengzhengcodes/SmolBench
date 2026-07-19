# CategoryTheory.NonPreadditiveAbelian.add_comm   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`  

**Ground-truth tail (from k):**
```lean
rw [sub_sub_sub, add_def, ← neg_def, neg_neg b, neg_def]
```

**True premises at k:** `CategoryTheory.NonPreadditiveAbelian.sub_sub_sub`, `CategoryTheory.NonPreadditiveAbelian.add_def`, `CategoryTheory.NonPreadditiveAbelian.neg_def`, `CategoryTheory.NonPreadditiveAbelian.neg_neg`, `CategoryTheory.NonPreadditiveAbelian.neg_def`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=267, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sub_zero, sub_neg_eq_add]
rw [add_comm]
```

**lean_error:** tail step 1/2 ('rw [sub_zero, sub_neg_eq_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=267, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sub_zero, sub_neg_eq_add]
rw [add_comm]
```

**lean_error:** tail step 1/2 ('rw [sub_zero, sub_neg_eq_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=267, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [zero_sub, sub_zero]
rw [neg_sub, sub_neg]
rw [add_comm]
```

**lean_error:** tail step 1/3 ('rw [zero_sub, sub_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.0s, verify 0.1s, in=267, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sub_zero, sub_neg_eq_add]
rw [add_comm]
```

**lean_error:** tail step 1/2 ('rw [sub_zero, sub_neg_eq_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.6s, verify 0.1s, in=267, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 0.7s, verify 0.1s, in=267, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=267, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=267, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1134, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_zero, sub_zero]
rw [neg_def, neg_neg]
rw [add_def]
```

**lean_error:** tail step 1/3 ('rw [sub_zero, sub_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=1134, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_zero, sub_zero]
conv_lhs => congr; rw [neg_def]
rw [neg_neg, neg_neg]
```

**lean_error:** tail step 1/3 ('rw [sub_zero, sub_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=1134, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_zero, neg_def, neg_neg, add_def]
rw [sub_zero, neg_def, neg_neg]
```

**lean_error:** tail step 1/2 ('rw [sub_zero, neg_def, neg_neg, add_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=1134, out=45)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_zero, sub_zero]
rw [neg_def, neg_def]
rw [sub_sub_sub]
conv_lhs =>
  congr
  next => skip
  rw [sub_self]
rw [sub_zero]
```

**lean_error:** tail step 1/8 ('rw [sub_zero, sub_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=1134, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [zero_sub, sub_zero]
```

**lean_error:** tail step 1/1 ('rw [zero_sub, sub_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=1134, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_zero, sub_neg, sub_zero]
```

**lean_error:** tail step 1/1 ('rw [sub_zero, sub_neg, sub_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=1134, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_zero, sub_neg, neg_def, neg_def]
```

**lean_error:** tail step 1/1 ('rw [sub_zero, sub_neg, neg_def, neg_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1134, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [zero_sub, neg_def, neg_neg, sub_zero]
```

**lean_error:** tail step 1/1 ('rw [zero_sub, neg_def, neg_neg, sub_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
