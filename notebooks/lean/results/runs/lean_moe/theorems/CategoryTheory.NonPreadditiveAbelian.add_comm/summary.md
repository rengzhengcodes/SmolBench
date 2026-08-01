# CategoryTheory.NonPreadditiveAbelian.add_comm   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`  

**Ground-truth tail (from k):**
```lean
rw [sub_sub_sub, add_def, ← neg_def, neg_neg b, neg_def]
```

**True premises at k:** `CategoryTheory.NonPreadditiveAbelian.sub_sub_sub`, `CategoryTheory.NonPreadditiveAbelian.add_def`, `CategoryTheory.NonPreadditiveAbelian.neg_def`, `CategoryTheory.NonPreadditiveAbelian.neg_neg`, `CategoryTheory.NonPreadditiveAbelian.neg_def`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | · |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.4s, verify 0.2s, in=306, out=502)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 24.6s, verify 0.3s, in=1212, out=5895)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

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

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.1s, verify 0.2s, in=2888, out=2415)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [neg_def]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch
