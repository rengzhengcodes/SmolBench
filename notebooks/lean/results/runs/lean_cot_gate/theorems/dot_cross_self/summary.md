# dot_cross_self   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/CrossProduct.lean`  

**Ground-truth tail (from k):**
```lean
rw [← cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**True premises at k:** `cross_anticomm`, `Matrix.dotProduct_neg`, `dot_self_cross`, `neg_zero`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · · ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✓ ✘ ✘ | · ✘ ✘ ✓ | ✘ ✓ · ✘ |
| `hint:3` | ✘ ✘ ✘ ✓ | · ✘ ✘ ✘ | ✘ · ✘ · |
| `noise:3` | ✘ ✘ ✓ ✘ | · ✘ ✘ ✘ | · ✓ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 47.7s, verify 0.1s, in=221, out=2038)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact cross_dot_right_self v w
```

**lean_error:** tail step 1/1 ('exact cross_dot_right_self v w'): unknown identifier 'cross_dot_right_self'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 61.5s, verify 0.1s, in=221, out=2660)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dotProduct_comm]
apply cross_dot_self_right
```

**lean_error:** tail step 2/2 ('apply cross_dot_self_right'): unknown identifier 'cross_dot_self_right'

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 109.4s, verify 0.1s, in=221, out=4828)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [crossProduct, cross, dotProduct]
simp [sum_univ_fin_3]
ring
```

**lean_error:** tail step 1/3 ('rw [crossProduct, cross, dotProduct]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 150.6s, verify 0.1s, in=221, out=6902)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw crossProduct
ring
```

**lean_error:** tail step 1/2 ('rw crossProduct'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.2s, verify 0.2s, in=221, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [crossProduct]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ vecHead w * (v 1 * w 2 - v 2 * w 1) +
      (vecHead (vecTail w) * (v 2 * w 0 - v 0 * w 2) + vecHead (vecTail (vecTail w)) * (v 0 * w 1 - v 1 * w 0)) =
    0
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.5s, verify 0.2s, in=221, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dotProduct, crossProduct]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ (Finset.sum Finset.univ fun x => w x * ![v 1 * w 2 - v 2 * w 1, v 2 * w 0 - v 0 * w 2, v 0 * w 1 - v 1 * w 0] x) = 0
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.7s, verify 0.2s, in=221, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dotProduct, crossProduct]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ (Finset.sum Finset.univ fun x => w x * ![v 1 * w 2 - v 2 * w 1, v 2 * w 0 - v 0 * w 2, v 0 * w 1 - v 1 * w 0] x) = 0
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.2s, verify 0.1s, in=221, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dotProduct, crossProduct, Fin.sum_univ_fin_three]
```

**lean_error:** tail step 1/1 ('simp [dotProduct, crossProduct, Fin.sum_univ_fin_three]'): unknown constant 'Fin.sum_univ_fin_three'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 4.2s, verify 0.1s, in=221, out=120)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact dot_crossProduct_right _ _
```

**lean_error:** tail step 1/1 ('exact dot_crossProduct_right _ _'): unknown identifier 'dot_crossProduct_right'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.8s, verify 0.1s, in=221, out=290)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [crossProduct_comm, dot_neg, cross_dot_self]
```

**lean_error:** tail step 1/1 ('rw [crossProduct_comm, dot_neg, cross_dot_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 15.6s, verify 0.1s, in=221, out=483)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dotProduct_cross_right, cross_comm, dotProduct_neg, dotProduct_cross_left]
```

**lean_error:** tail step 1/1 ('rw [dotProduct_cross_right, cross_comm, dotProduct_neg, dotProduct_cross_left]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 24.5s, verify 0.1s, in=221, out=842)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dotProduct_cross_dot_right]
```

**lean_error:** tail step 1/1 ('rw [dotProduct_cross_dot_right]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 62.6s, verify 0.1s, in=737, out=2710)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [cross_anticomm w v]
rw [dotProduct_neg]
rw [dot_self_cross]
rw [neg_zero]
```

**lean_error:** tail step 1/4 ('rw [cross_anticomm w v]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 70.7s, verify 0.3s, in=737, out=2969)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← cross_anticomm w v]
rw [dotProduct_neg]
rw [dot_self_cross]
rw [neg_zero]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 71.7s, verify 0.1s, in=737, out=2958)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 115.4s, verify 0.1s, in=737, out=5124)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [cross_anticomm w v, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm w v, Matrix.dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.1s, verify 0.1s, in=737, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [dot_self_cross, cross_anticomm, dotProduct_neg]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.3s, in=737, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [cross_anticomm, ← dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, ← dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=737, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.0s, verify 0.1s, in=737, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← cross_anticomm w v, dotProduct_neg, dot_self_cross, neg_zero]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.9s, verify 0.1s, in=737, out=294)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa only [cross_anticomm, dot_self_cross, Matrix.dotProduct_neg, neg_zero]
```

**lean_error:** tail step 1/1 ('simpa only [cross_anticomm, dot_self_cross, Matrix.dotProduct_neg, neg_zero]'): tactic 'assumption' failed

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 10.5s, verify 0.1s, in=737, out=315)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 13.6s, verify 0.1s, in=737, out=419)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 15.1s, verify 0.1s, in=737, out=461)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [cross_anticomm, ← Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, ← Matrix.dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 90.1s, verify 0.1s, in=1603, out=2074)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 166.4s, verify 0.1s, in=1603, out=5332)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [cross_anticomm w v, dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm w v, dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 190.0s, verify 0.1s, in=1603, out=6370)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← neg_eq_iff_eq_neg.mp (cross_anticomm v w)]
rw [dotProduct_neg]
rw [dot_self_cross]
rw [neg_zero]
```

**lean_error:** tail step 1/4 ('rw [← neg_eq_iff_eq_neg.mp (cross_anticomm v w)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 191.3s, verify 0.1s, in=1603, out=7105)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← cross_anticomm w v, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 3.1s, verify 0.1s, in=1603, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.2s, verify 0.1s, in=1603, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.3s, verify 0.1s, in=1603, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [cross_anticomm, ← dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, ← dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.4s, verify 0.1s, in=1603, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [dot_cross_self, cross_anticomm, dotProduct_neg]
```

**lean_error:** tail step 1/1 ('simp [dot_cross_self, cross_anticomm, dotProduct_neg]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 16.3s, verify 0.1s, in=1603, out=383)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [dot_self_cross w v, cross_anticomm, Matrix.dotProduct_neg, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [dot_self_cross w v, cross_anticomm, Matrix.dotProduct_neg, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 16.9s, verify 0.1s, in=1603, out=234)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [dot_self_cross, Matrix.dotProduct_neg, cross_anticomm, neg_zero]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 17.2s, verify 0.1s, in=1603, out=261)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [cross_anticomm, Matrix.dotProduct_neg] using dot_self_cross w v
```

**lean_error:** tail step 1/1 ('simpa [cross_anticomm, Matrix.dotProduct_neg] using dot_self_cross w v'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 22.4s, verify 0.1s, in=1603, out=491)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 43.9s, verify 0.1s, in=1629, out=1890)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 97.6s, verify 0.1s, in=1629, out=4293)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [cross_anticomm w v]
rw [dotProduct_neg]
rw [dot_self_cross]
rw [neg_zero]
```

**lean_error:** tail step 1/4 ('rw [cross_anticomm w v]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 106.1s, verify 0.1s, in=1629, out=4659)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← cross_anticomm w v, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 124.0s, verify 0.1s, in=1629, out=5546)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [cross_anticomm w v, dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm w v, dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.3s, verify 0.1s, in=1629, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [dot_self_cross, cross_anticomm, dotProduct_neg]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.6s, verify 0.1s, in=1629, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.7s, verify 0.1s, in=1629, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.9s, verify 0.1s, in=1629, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 8.6s, verify 0.1s, in=1629, out=249)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [dot_self_cross, cross_anticomm, Matrix.dotProduct_neg, neg_zero]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.3s, verify 0.1s, in=1629, out=274)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.7s, verify 0.1s, in=1629, out=389)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]
```

**lean_error:** tail step 1/1 ('rw [cross_anticomm, dotProduct_neg, dot_self_cross, neg_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 15.0s, verify 0.1s, in=1629, out=468)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← cross_anticomm w v, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```
