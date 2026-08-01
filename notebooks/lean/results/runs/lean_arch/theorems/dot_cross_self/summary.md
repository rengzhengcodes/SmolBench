# dot_cross_self   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/CrossProduct.lean`  

**Ground-truth tail (from k):**
```lean
rw [← cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**True premises at k:** `cross_anticomm`, `Matrix.dotProduct_neg`, `dot_self_cross`, `neg_zero`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | · | ✘ |
| `hint:2` | ✘ | · | ✘ |
| `hint:3` | ✘ | · | ✘ |
| `noise:3` | ✘ | · | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=250, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [crossProduct]
ext
simp only [Fin.forall_fin_three, Matrix.vecMul_vec, Matrix.cons_val_one, Matrix.head_cons, Matrix.cons_val_zero]
ring1
dec_trivial
```

**lean_error:** tail step 2/5 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 1.1s, verify 1.1s, in=222, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [crossProduct, dotProduct, Fin.sum_univ_succ, Fin.sum_univ_zero, mul_comm]
ring
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 *
        ((LinearMap.mk₂ R (fun a b => ![a 1 * b 2 - b 1 * a 2, b 0 * a 2 - a 0 * b 2, a 0 * b 1 - b 0 * a 1]) ⋯ ⋯ ⋯ ⋯)
            v)
...
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=239, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [crossProduct, dotProduct]
dsimp [Fin.sumUniv, Fin.sumUniv_three]
ring
```

**lean_error:** tail step 2/3 ('dsimp [Fin.sumUniv, Fin.sumUniv_three]'): unknown constant 'Fin.sumUniv'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=768, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← cross_anticomm v w]
rw [Matrix.dotProduct_neg]
rw [dot_self_cross]
rw [neg_zero]
```

**lean_error:** tail step 1/4 ('rw [← cross_anticomm v w]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.2s, in=727, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← cross_anticomm]
simp [Matrix.dotProduct_neg, dot_self_cross]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=757, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← cross_anticomm v w]
simp [dot_self_cross]
```

**lean_error:** tail step 1/2 ('rw [← cross_anticomm v w]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1632, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← cross_anticomm v w]
rw [Matrix.dotProduct_neg]
rw [dot_self_cross]
rw [neg_zero]
```

**lean_error:** tail step 1/4 ('rw [← cross_anticomm v w]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.9s, verify 0.2s, in=1587, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← cross_anticomm]
simp [Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1621, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← dotProduct_neg w (crossProduct v w)]
rw [← cross_anticomm v w]
exact dot_self_cross v w
```

**lean_error:** tail step 1/3 ('rw [← dotProduct_neg w (crossProduct v w)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1657, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [cross_anticomm v w]
rw [Matrix.dotProduct_neg]
rw [dot_self_cross w v]
rw [neg_zero]
```

**lean_error:** tail step 1/4 ('rw [cross_anticomm v w]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.4s, verify 0.2s, in=1715, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← cross_anticomm]
simp [dot_self_cross]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1646, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← dotProduct_neg, cross_anticomm]
exact dot_self_cross v w
```

**lean_error:** tail step 1/2 ('rw [← dotProduct_neg, cross_anticomm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
