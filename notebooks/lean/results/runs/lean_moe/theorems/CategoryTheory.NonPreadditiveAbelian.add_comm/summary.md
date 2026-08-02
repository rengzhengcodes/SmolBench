# CategoryTheory.NonPreadditiveAbelian.add_comm   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`  

**Ground-truth tail (from k):**
```lean
rw [sub_sub_sub, add_def, ← neg_def, neg_neg b, neg_def]
```

**True premises at k:** `CategoryTheory.NonPreadditiveAbelian.sub_sub_sub`, `CategoryTheory.NonPreadditiveAbelian.add_def`, `CategoryTheory.NonPreadditiveAbelian.neg_def`, `CategoryTheory.NonPreadditiveAbelian.neg_neg`, `CategoryTheory.NonPreadditiveAbelian.neg_def`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | · | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.4s, verify 0.2s, in=306, out=502)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 24.4s, verify 0.1s, in=251, out=2784)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
abel
```
```

**lean_error:** tail step 1/2 ('abel'): abel_nf made no progress

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=250, out=317)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
abel
```

**lean_error:** tail step 1/1 ('abel'): abel_nf made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 24.6s, verify 0.3s, in=1212, out=5895)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 98.4s, verify 0.1s, in=1180, out=11300)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  0 - 0 - (-b - a) = 0 - (-b) - (0 - a) := by rw [sub_sub_sub]
  _ = -(-b) - (-a) := by rw [neg_def, neg_def]
  _ = b - (-a) := by rw [neg_neg]
  _ = b + a := by rw [add_def.symm]
```

**lean_error:** tail step 1/5 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 13.2s, verify 0.2s, in=1145, out=1269)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [sub_zero]
abel
```

**lean_error:** tail step 2/2 ('abel'): abel_nf made no progress

### `hint:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 11.4s, verify 0.4s, in=3350, out=2426)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [sub_self, sub_zero, add_def, neg_def, sub_sub_sub, neg_sub, neg_neg]
```

**final state (truncated):**
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
a b : X ⟶ Y
⊢ 0 - (0 - b - a) = b - (0 - a)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 268.8s, verify 0.1s, in=3256, out=32768)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₃ : 0 - (-b) = b := by
  have h₃₁ : 0 - (-b) = - (-b) := by rw [neg_def]
  rw [h₃₁]
  have h₃₂ : - (-b) = b := by apply neg_neg
  rw [h₃₂]
```

**lean_error:** tail step 1/5 ('have h₃ : 0 - (-b) = b := by'): <stdin>:1:28: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.9s, verify 0.1s, in=2994, out=780)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
<;> simp_all [sub_zero, zero_sub, neg_neg]
<;> rfl
```

**lean_error:** tail step 1/3 ('simp'): simp made no progress

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.1s, verify 0.2s, in=2888, out=2415)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [neg_def]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 188.2s, verify 0.1s, in=3371, out=21771)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
abel
```

**lean_error:** tail step 1/1 ('abel'): abel_nf made no progress

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 12.0s, verify 0.1s, in=3011, out=1140)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [sub_self, sub_zero]
```

**final state (truncated):**
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
a b : X ⟶ Y
⊢ 0 - (-b - a) = b + a
```
