# CategoryTheory.NonPreadditiveAbelian.add_comm   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`  

**Ground-truth tail (from k):**
```lean
rw [sub_sub_sub, add_def, ← neg_def, neg_neg b, neg_def]
```

**True premises at k:** `CategoryTheory.NonPreadditiveAbelian.sub_sub_sub`, `CategoryTheory.NonPreadditiveAbelian.add_def`, `CategoryTheory.NonPreadditiveAbelian.neg_def`, `CategoryTheory.NonPreadditiveAbelian.neg_neg`, `CategoryTheory.NonPreadditiveAbelian.neg_def`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | · | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.5s, in=267, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sub_zero, sub_neg_eq_add]
rw [add_comm]
```

**lean_error:** tail step 1/2 ('rw [sub_zero, sub_neg_eq_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=241, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [sub_zero, sub_neg_eq_add, neg_sub, add_comm]
```

**final state (truncated):**
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
a b : X ⟶ Y
⊢ 0 - (-a - b) = a + b
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.2s, verify 0.1s, in=256, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [sub_eq_add_neg, add_assoc, add_comm, add_left_neg]
```

**final state (truncated):**
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
a b : X ⟶ Y
⊢ 0 - 0 - (-b - a) = a + b
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.4s, in=1134, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_zero, neg_def, neg_def, sub_sub_sub]
rw [sub_zero, neg_def, sub_self, sub_zero]
```

**lean_error:** tail step 1/2 ('rw [sub_zero, neg_def, neg_def, sub_sub_sub]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1115, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_zero, sub_neg_eq_add]
rw [add_comm]
```

**lean_error:** tail step 1/2 ('rw [sub_zero, sub_neg_eq_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1123, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [neg_def, neg_def, add_def]
rw [neg_neg, add_def]
rw [add_def, neg_neg]
rw [add_def]
```

**lean_error:** tail step 1/4 ('rw [neg_def, neg_def, add_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=2954, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [sub_zero, neg_def, neg_def, neg_neg]
rw [sub_zero, add_def]
rw [neg_neg]
```

**lean_error:** tail step 1/3 ('rw [sub_zero, neg_def, neg_def, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=3056, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [sub_zero, sub_neg_eq_add]
rw [add_comm]
```

**lean_error:** tail step 1/2 ('rw [sub_zero, sub_neg_eq_add]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=2943, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [neg_def, neg_def, add_def, add_def]
rw [sub_zero, neg_neg]
rw [← add_def]
```

**lean_error:** tail step 1/3 ('rw [neg_def, neg_def, add_def, add_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=2979, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [sub_zero, neg_def, neg_neg, add_def]
rw [sub_zero, neg_def, neg_neg]
```

**lean_error:** tail step 1/2 ('rw [sub_zero, neg_def, neg_neg, add_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=3169, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [sub_zero, sub_zero, neg_neg, neg_neg]
rw [add_comm]
rfl
```

**lean_error:** tail step 1/3 ('rw [sub_zero, sub_zero, neg_neg, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=2968, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [neg_neg, add_def, sub_zero, add_def, neg_neg]
rw [sub_zero, add_def, neg_neg]
```

**lean_error:** tail step 1/2 ('rw [neg_neg, add_def, sub_zero, add_def, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
