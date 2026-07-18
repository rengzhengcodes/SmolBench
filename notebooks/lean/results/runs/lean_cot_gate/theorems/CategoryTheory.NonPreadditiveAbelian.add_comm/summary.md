# CategoryTheory.NonPreadditiveAbelian.add_comm   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`  

**Ground-truth tail (from k):**
```lean
rw [sub_sub_sub, add_def, ← neg_def, neg_neg b, neg_def]
```

**True premises at k:** `CategoryTheory.NonPreadditiveAbelian.sub_sub_sub`, `CategoryTheory.NonPreadditiveAbelian.add_def`, `CategoryTheory.NonPreadditiveAbelian.neg_def`, `CategoryTheory.NonPreadditiveAbelian.neg_neg`, `CategoryTheory.NonPreadditiveAbelian.neg_def`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ · ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 25.4s, verify 0.1s, in=241, out=1034)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
abel
```

**lean_error:** tail step 1/1 ('abel'): abel_nf made no progress

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 94.5s, verify 0.1s, in=241, out=3816)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
abel
```

**lean_error:** tail step 1/1 ('abel'): abel_nf made no progress

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 112.3s, verify 0.1s, in=241, out=4575)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
abel
```

**lean_error:** tail step 1/1 ('abel'): abel_nf made no progress

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 136.1s, verify 0.1s, in=241, out=5553)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
abel
```

**lean_error:** tail step 1/1 ('abel'): abel_nf made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.5s, verify 0.1s, in=241, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.6s, verify 0.1s, in=241, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=241, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 71.2s, verify 0.1s, in=241, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 122.0s, verify 0.1s, in=1108, out=4998)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 176.9s, verify 0.1s, in=1108, out=7156)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_sub_sub, neg_def, neg_neg, ← add_def]
```

**lean_error:** tail step 1/1 ('rw [sub_sub_sub, neg_def, neg_neg, ← add_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 190.3s, verify 0.1s, in=1108, out=7707)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [neg_def, neg_def]
rw [neg_neg]
```

**lean_error:** tail step 1/2 ('rw [neg_def, neg_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 228.3s, verify 0.2s, in=1108, out=9257)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_sub_sub]
conv_lhs =>
  congr
  · rw [neg_def, neg_neg]
  · rw [neg_def]
rfl
```

**lean_error:** tail step 2/6 ('conv_lhs =>'): <stdin>:1:11: unexpected end of input; expected '{'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.2s, verify 0.1s, in=1108, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [add_def, neg_def]
```

**final state (truncated):**
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
a b : X ⟶ Y
⊢ 0 - 0 - (0 - b - a) = b - (0 - a)
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=1108, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [sub_self, sub_zero, neg_def, neg_def, neg_neg]
```

**lean_error:** tail step 1/1 ('rw [sub_self, sub_zero, neg_def, neg_def, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=1108, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [neg_def, ← neg_def, sub_sub_sub, sub_zero, sub_sub_self]
```

**lean_error:** tail step 1/1 ('rw [neg_def, ← neg_def, sub_sub_sub, sub_zero, sub_sub_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 70.2s, verify 0.3s, in=1108, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 177.8s, verify 0.1s, in=2931, out=6159)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 308.7s, verify 0.2s, in=2931, out=8853)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [sub_sub_sub 0 (-b) 0 a]
rw [neg_def, neg_def, neg_neg]
rw [← add_def]
```

**lean_error:** tail step 2/3 ('rw [neg_def, neg_def, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 343.6s, verify 0.1s, in=2931, out=9777)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 352.9s, verify 0.1s, in=2931, out=9810)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← add_def]
```

**lean_error:** tail step 1/1 ('rw [← add_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=2931, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [sub_zero, neg_def, neg_def, neg_def]
```

**lean_error:** tail step 1/1 ('rw [sub_zero, neg_def, neg_def, neg_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=2931, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [sub_self, neg_def, sub_zero, neg_def, neg_neg]
```

**lean_error:** tail step 1/1 ('rw [sub_self, neg_def, sub_zero, neg_def, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.9s, verify 0.1s, in=2931, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [neg_def, sub_self, sub_zero]
```

**final state (truncated):**
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
a b : X ⟶ Y
⊢ 0 - (0 - b - a) = b + a
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.9s, verify 0.1s, in=2931, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [neg_def, ← neg_def, neg_neg, neg_def, ← neg_def, neg_neg, ← neg_def, neg_neg]
```

**lean_error:** tail step 1/1 ('rw [neg_def, ← neg_def, neg_neg, neg_def, ← neg_def, neg_neg, ← neg_def, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 149.8s, verify 0.3s, in=2956, out=6113)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [sub_sub_sub]
rw [neg_def]
rw [neg_neg]
rw [neg_def]
rw [← add_def]
```

**lean_error:** tail step 3/5 ('rw [neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 169.6s, verify 0.1s, in=2956, out=6871)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [neg_def, neg_neg, add_def]
```

**lean_error:** tail step 1/1 ('rw [neg_def, neg_neg, add_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 175.5s, verify 0.1s, in=2956, out=7076)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [sub_sub_sub, neg_def, neg_neg, add_def]
```

**lean_error:** tail step 1/1 ('rw [sub_sub_sub, neg_def, neg_neg, add_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 262.9s, verify 0.1s, in=2956, out=10602)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [sub_sub_sub 0 0 (-b) a]
rw [neg_def, neg_neg, add_def]
```

**lean_error:** tail step 1/2 ('rw [sub_sub_sub 0 0 (-b) a]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.1s, verify 0.1s, in=2956, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [add_def, neg_def]
```

**final state (truncated):**
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
a b : X ⟶ Y
⊢ 0 - 0 - (0 - b - a) = b - (0 - a)
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=2956, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [sub_self, zero_sub, ← neg_def, neg_neg]
```

**lean_error:** tail step 1/1 ('rw [sub_self, zero_sub, ← neg_def, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 70.9s, verify 0.2s, in=2956, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [neg_def, ← neg_def, neg_neg, neg_def, ← neg_def, neg_neg, ← neg_def, neg_neg]
```

**lean_error:** tail step 1/1 ('rw [neg_def, ← neg_def, neg_neg, neg_def, ← neg_def, neg_neg, ← neg_def, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 71.5s, verify 0.1s, in=2956, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [sub_zero, neg_def, neg_def, neg_neg]
```

**lean_error:** tail step 1/1 ('rw [sub_zero, neg_def, neg_def, neg_neg]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
