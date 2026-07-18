# CategoryTheory.Idempotents.Karoubi.ext   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Idempotents/Karoubi.lean`  

**Ground-truth tail (from k):**
```lean
simpa only [mk.injEq, heq_eq_eq, true_and, eqToHom_refl, comp_id, id_comp] using h_p
```

**True premises at k:** `heq_eq_eq`, `true_and`, `CategoryTheory.eqToHom_refl`, `CategoryTheory.Category.comp_id`, `CategoryTheory.Category.id_comp`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · · · |
| `hint:2` | · ✘ ✓ ✓ | · · ✓ · |
| `hint:3` | ✘ ✘ ✘ ✘ | ✓ ✘ · · |
| `noise:3` | ✘ ✘ ✘ ✘ | · ✓ · ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 155.2s, verify 0.1s, in=356, out=6199)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have hp : p✝¹ = p✝ := by { have := congr_arg (λ f, f ≫ 𝟙 X✝) h_p, simp [category.comp_id] at this, exact this }
cases hp
congr
exact proof_irrel idem✝¹ idem✝
```

**lean_error:** tail step 1/4 ('have hp : p✝¹ = p✝ := by { have := congr_arg (λ f, f ≫ 𝟙 X✝) h_p, simp [category.comp_id] at this, exact this }'): <stdin>:1:11: expected token

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 155.6s, verify 0.2s, in=356, out=6217)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
trivial
rw [←Category.comp_id, ←Category.id_comp] at h_p
exact h_p
apply proof_irrel
```

**lean_error:** tail step 2/5 ('trivial'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 171.3s, verify 0.1s, in=356, out=6863)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
rfl
simp only [eqToHom_refl] at h_p
rw [Category.id_comp, Category.comp_id] at h_p
exact h_p
apply subsingleton.elim
```

**lean_error:** tail step 1/6 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 182.8s, verify 0.1s, in=356, out=7319)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Category.id_comp, Category.comp_id] at h_p
apply ext
exact rfl
exact h_p
apply subsingleton.elim
```

**lean_error:** tail step 1/5 ('rw [Category.id_comp, Category.comp_id] at h_p'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

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

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **incomplete**  (gen 145.4s, verify 0.2s, in=900, out=5808)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p
subst h_p
```

**final state (truncated):**
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝ : X✝ ⟶ X✝
idem✝¹ idem✝ : p✝ ≫ p✝ = p✝
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 153.5s, verify 0.2s, in=900, out=6135)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [eqToHom_refl] at h_p
simp [comp_id, id_comp] at h_p
cases h_p
rfl
```

**lean_error:** tail step 2/4 ('simp [comp_id, id_comp] at h_p'): simp made no progress

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 159.9s, verify 0.2s, in=900, out=6390)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [eqToHom_refl] at h_p
congr
ext
trivial
simp [true_and]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 211.6s, verify 0.3s, in=900, out=8436)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [eqToHom_refl] at h_p
simp only [CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p
congr
exact h_p
trivial
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

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 317.4s, verify 0.2s, in=2045, out=7588)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [eqToHom_refl] at h_p
rw [Category.comp_id, Category.id_comp] at h_p
subst h_p
apply Subsingleton.elim
```

**lean_error:** tail step 2/4 ('rw [Category.comp_id, Category.id_comp] at h_p'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 321.9s, verify 0.2s, in=2045, out=9067)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [eqToHom_refl] at h_p
simp [CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p
subst h_p
congr
```

**lean_error:** tail step 2/4 ('simp [CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 328.7s, verify 0.2s, in=2045, out=7815)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [eqToHom_refl] at h_p
rw [CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p
exact h_p
```

**lean_error:** tail step 2/3 ('rw [CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 360.3s, verify 0.3s, in=2045, out=9558)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [eqToHom_refl, Category.id_comp, Category.comp_id] at h_p
subst h_p
apply proof_irrel
```

**lean_error:** tail step 3/3 ('apply proof_irrel'): tactic 'apply' failed, failed to unify

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

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 114.5s, verify 0.2s, in=2070, out=4547)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [eqToHom_refl] at h_p
simp [Category.id_comp, Category.comp_id] at h_p
congr
```

**lean_error:** tail step 2/3 ('simp [Category.id_comp, Category.comp_id] at h_p'): simp made no progress

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 168.1s, verify 0.5s, in=2070, out=6728)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eqToHom_refl] at h_p
simp [Category.comp_id, Category.id_comp] at h_p
apply Karoubi.ext
· rfl
· exact h_p
· apply proof_irrel
```

**lean_error:** tail step 4/6 ('· rfl'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 177.5s, verify 0.2s, in=2070, out=7110)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CategoryTheory.eqToHom_refl, CategoryTheory.Category.comp_id, CategoryTheory.Category.id_comp] at h_p
rw h_p
congr
apply Subsingleton.elim
```

**lean_error:** tail step 2/4 ('rw h_p'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 193.5s, verify 0.1s, in=2070, out=7699)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [eqToHom_refl] at h_p,
simp only [comp_id, id_comp] at h_p,
subst h_p,
congr,
apply proof_irrel
```

**lean_error:** tail step 1/5 ('simp only [eqToHom_refl] at h_p,'): <stdin>:1:31: expected end of input

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
