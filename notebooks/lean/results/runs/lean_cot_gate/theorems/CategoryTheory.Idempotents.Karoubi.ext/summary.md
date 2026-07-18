# CategoryTheory.Idempotents.Karoubi.ext   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Idempotents/Karoubi.lean`  

**Ground-truth tail (from k):**
```lean
simpa only [mk.injEq, heq_eq_eq, true_and, eqToHom_refl, comp_id, id_comp] using h_p
```

**True premises at k:** `heq_eq_eq`, `true_and`, `CategoryTheory.eqToHom_refl`, `CategoryTheory.Category.comp_id`, `CategoryTheory.Category.id_comp`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | · · · · |
| `hint:2` | · · ✓ · |
| `hint:3` | ✓ ✘ · · |
| `noise:3` | · ✓ · ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 0.8s, verify 0.1s, in=356, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
```

**final state (truncated):**
```
case mk.mk.e_p
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.0s, verify 0.1s, in=356, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h_p]
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.2s, verify 0.1s, in=356, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h_p]
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 7.5s, verify 0.1s, in=356, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
```

**final state (truncated):**
```
case mk.mk.e_p
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.1s, verify 0.1s, in=900, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp at h_p
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.3s, verify 0.1s, in=900, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp at h_p
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=900, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using h_p
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.6s, verify 0.1s, in=900, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [eqToHom_refl] at h_p
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.7s, verify 0.1s, in=2045, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using h_p
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=2045, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [h_p] at idem✝¹
```

**lean_error:** tail step 1/1 ('simp [h_p] at idem✝¹'): <stdin>:1:18: expected end of input

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.8s, verify 0.1s, in=2045, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp at h_p
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.9s, verify 0.1s, in=2045, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp at h_p
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.7s, verify 0.1s, in=2070, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp at h_p
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=2070, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using h_p
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.4s, verify 0.1s, in=2070, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp at h_p
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 7.6s, verify 0.1s, in=2070, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h_p] at idem✝¹
```

**lean_error:** tail step 1/1 ('simp [h_p] at idem✝¹'): <stdin>:1:18: expected end of input
