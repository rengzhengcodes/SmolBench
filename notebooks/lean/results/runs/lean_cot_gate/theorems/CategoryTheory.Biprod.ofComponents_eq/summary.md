# CategoryTheory.Biprod.ofComponents_eq   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
ext <;>
  simp only [Category.comp_id, biprod.inr_fst, biprod.inr_snd, biprod.inl_snd, add_zero, zero_add,
    Biprod.inl_ofComponents, Biprod.inr_ofComponents, eq_self_iff_true, Category.assoc,
    comp_zero, biprod.inl_fst, Preadditive.add_comp]
```

**True premises at k:** `CategoryTheory.Category.comp_id`, `CategoryTheory.Limits.biprod.inr_fst`, `CategoryTheory.Limits.biprod.inr_snd`, `CategoryTheory.Limits.biprod.inl_snd`, `add_zero`, `zero_add`, `CategoryTheory.Biprod.inl_ofComponents`, `CategoryTheory.Biprod.inr_ofComponents`, `eq_self_iff_true`, `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.comp_zero`, `CategoryTheory.Limits.biprod.inl_fst`, `CategoryTheory.Preadditive.add_comp`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ · · · |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ · ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=419, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.8s, verify 0.2s, in=419, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ofComponents]
```

**final state (truncated):**
```
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : Preadditive C
inst✝ : HasBinaryBiproducts C
X₁ X₂ Y₁ Y₂ : C
f₁₁ : X₁ ⟶ Y₁
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.0s, verify 0.2s, in=419, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ofComponents]
```

**final state (truncated):**
```
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : Preadditive C
inst✝ : HasBinaryBiproducts C
X₁ X₂ Y₁ Y₂ : C
f₁₁ : X₁ ⟶ Y₁
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.1s, verify 0.2s, in=419, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ofComponents]
```

**final state (truncated):**
```
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : Preadditive C
inst✝ : HasBinaryBiproducts C
X₁ X₂ Y₁ Y₂ : C
f₁₁ : X₁ ⟶ Y₁
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=2283, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=2283, out=52)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ofComponents_ext' _ _ (biprod.hom_ext (Biprod.inl_ofComponents _ _ _ _).symm
  (Biprod.inr_ofComponents _ _ _ _).symm)]
```

**lean_error:** tail step 1/2 ("rw [ofComponents_ext' _ _ (biprod.hom_ext (Biprod.inl_ofComponents _ _ _ _).symm"): <stdin>:1:80: unexpected end of input; expected ')', ',' or ':'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.7s, verify 0.1s, in=2283, out=89)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_inl_eq_inr, Biprod.inl_ofComponents, Biprod.inl_ofComponents, Biprod.inr_ofComponents,
  Biprod.inr_ofComponents, biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd,
  comp_id, comp_zero, zero_comp, add_zero, zero_add, comp_id]
```

**lean_error:** tail step 1/3 ('rw [eq_iff_inl_eq_inr, Biprod.inl_ofComponents, Biprod.inl_ofComponents, Biprod.inr_ofComponents,'): <stdin>:1:97: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.8s, verify 0.1s, in=2283, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Biprod.ofComponents_inl, Biprod.ofComponents_inr, Biprod.ext]
```

**lean_error:** tail step 1/1 ('simp [Biprod.ofComponents_inl, Biprod.ofComponents_inr, Biprod.ext]'): unknown identifier 'Biprod.ofComponents_inl'

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=2901, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.2s, verify 0.1s, in=2901, out=103)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_iff_inl_eq_inl_and_inr_eq_inr, Biprod.inl_ofComponents, Biprod.inl_ofComponents,
  Biprod.inr_ofComponents, Biprod.inr_ofComponents, ← Category.assoc, ← Category.assoc,
  biprod.inl_fst, biprod.inl_snd, biprod.inr_fst, biprod.inr_snd, comp_id, comp_zero,
  zero_add, add_zero, comp_id]
```

**lean_error:** tail step 1/4 ('rw [eq_iff_inl_eq_inl_and_inr_eq_inr, Biprod.inl_ofComponents, Biprod.inl_ofComponents,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 8.6s, verify 0.4s, in=2901, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Biprod.ofComponents, Biprod.ofComponents_fst, Biprod.ofComponents_snd, ← Category.assoc]
```

**lean_error:** tail step 1/1 ('simp [Biprod.ofComponents, Biprod.ofComponents_fst, Biprod.ofComponents_snd, ← Category.assoc]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 72.1s, verify 0.1s, in=2901, out=68)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [ofComponents_eq] <;>
  simp only [add_zero, zero_add, biprod.inl_fst, biprod.inr_snd, biprod.inl_snd,
    biprod.inr_fst, comp_zero, zero_comp, add_zero, zero_add, eq_self_iff_true]
```

**lean_error:** tail step 1/3 ('rw [ofComponents_eq] <;>'): <stdin>:1:24: unexpected end of input; expected '['

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=2925, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=2925, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ofComponents_eq]
```

**lean_error:** tail step 1/1 ('rw [ofComponents_eq]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.4s, verify 0.2s, in=2925, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Biprod.ofComponents, Biprod.ofComponents_fst, Biprod.ofComponents_snd]
```

**final state (truncated):**
```
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : Preadditive C
inst✝ : HasBinaryBiproducts C
X₁ X₂ Y₁ Y₂ : C
f₁₁ : X₁ ⟶ Y₁
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.1s, verify 0.1s, in=2925, out=110)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_iff_inl_eq_inr, Biprod.inl_ofComponents, Biprod.inr_ofComponents, Biprod.inl_ofComponents,
  Biprod.inr_ofComponents, ← Category.assoc, biprod.inl_fst, comp_id, ← Category.assoc,
  biprod.inl_snd, comp_zero, zero_add, ← Category.assoc, biprod.inr_fst, comp_zero, zero_add,
  ← Category.assoc, biprod.inr_snd, comp_id]
```

**lean_error:** tail step 1/4 ('rw [eq_iff_inl_eq_inr, Biprod.inl_ofComponents, Biprod.inr_ofComponents, Biprod.inl_ofComponents,'): <stdin>:1:97: unexpected end of input; expected ']'
