# CategoryTheory.Abelian.exact_iff'   (k=7, 8 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Exact.lean`  

**Ground-truth tail (from k):**
```lean
simp [h.2]
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✘ ✘ | ✘ · · · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 106.6s, verify 0.2s, in=423, out=4696)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Category.assoc, h.2, Category.comp_zero, Category.zero_comp]  
trivial
```

**lean_error:** tail step 1/2 ('rw [Category.assoc, h.2, Category.comp_zero, Category.zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 120.4s, verify 0.1s, in=423, out=5386)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw h.2
simp only [zero_comp, comp_zero]
```

**lean_error:** tail step 1/2 ('rw h.2'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 135.6s, verify 0.1s, in=423, out=6098)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw h.2,
simp,
```

**lean_error:** tail step 1/2 ('rw h.2,'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 148.1s, verify 0.2s, in=423, out=6848)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [category.assoc, h.2, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [category.assoc, h.2, comp_zero, zero_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.4s, verify 0.1s, in=423, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.2]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.5s, verify 0.1s, in=423, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.2]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.6s, verify 0.1s, in=423, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [h.2, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [h.2, comp_zero]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=423, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← cancel_epi (kernel.ι g), ← cancel_mono (cokernel.π f), h]
```

**lean_error:** tail step 1/1 ('simp [← cancel_epi (kernel.ι g), ← cancel_mono (cokernel.π f), h]'): failed to synthesize instance

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.3s, verify 0.1s, in=423, out=305)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [h.1, kernel_ι_cokernel_π]
```

**lean_error:** tail step 1/1 ('simp only [h.1, kernel_ι_cokernel_π]'): unknown identifier 'kernel_ι_cokernel_π'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 8.3s, verify 0.1s, in=423, out=306)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case mpr
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
inst✝ : Abelian C
X Y Z : C
f : X ⟶ Y
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 9.3s, verify 0.1s, in=423, out=355)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case mpr
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
inst✝ : Abelian C
X Y Z : C
f : X ⟶ Y
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 13.5s, verify 0.1s, in=423, out=538)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.1, kernel.condition g]
```

**final state (truncated):**
```
case mpr
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
inst✝ : Abelian C
X Y Z : C
f : X ⟶ Y
...
```
