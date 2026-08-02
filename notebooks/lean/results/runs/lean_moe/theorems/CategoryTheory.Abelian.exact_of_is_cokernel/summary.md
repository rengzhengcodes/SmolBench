# CategoryTheory.Abelian.exact_of_is_cokernel   (k=3, 4 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Exact.lean`  

**Ground-truth tail (from k):**
```lean
rw [← this, ← Category.assoc, kernel.condition, zero_comp]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.kernel.condition`, `CategoryTheory.Limits.zero_comp`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.2s, verify 0.2s, in=375, out=3182)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [this, Category.assoc, kernel.condition]
```

**lean_error:** tail step 1/1 ('simpa [this, Category.assoc, kernel.condition]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 42.1s, verify 0.1s, in=323, out=4771)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h2 : cokernel.π f = g ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.w f)) := by
  rw [← this]
calc
  kernel.ι g ≫ cokernel.π f = kernel.ι g ≫ (g ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.w f))) := by rw [h2]
  _ = (kernel.ι g ≫ g) ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.w f)) := by
    rw [← Category.comp_assoc]
  _ = 0 ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.w f)) := by
    rw [kernel.ι_comp]
  _ = 0 := by simp [zero_comp]
```

**lean_error:** tail step 1/9 ('have h2 : cokernel.π f = g ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.w f)) := by'): <stdin>:1:92: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.2s, verify 0.1s, in=317, out=1043)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
abelian.kernel_ι_cokernel_π_of_comp_zero w
```

**lean_error:** tail step 1/1 ('abelian.kernel_ι_cokernel_π_of_comp_zero w'): <stdin>:1:1: unknown tactic

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.5s, verify 0.1s, in=854, out=1233)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [←this, Category.assoc, kernel.condition]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 78.0s, verify 0.1s, in=837, out=8877)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  kernel.ι g ≫ cokernel.π f = kernel.ι g ≫ (g ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) ⋯)) := by rw [this.symm]
  _ = (kernel.ι g ≫ g) ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) ⋯) := by rw [← assoc]
  _ = 0 ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) ⋯) := by rw [kernel.condition]
  _ = 0 := by simp [zero_comp]
```

**lean_error:** tail step 1/5 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.1s, verify 0.4s, in=804, out=611)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← this]
rw [← CategoryTheory.Category.assoc]
rw [kernel.condition]
simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.8s, verify 0.1s, in=1237, out=3558)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Category.assoc, this, kernel.condition]
```

**lean_error:** tail step 1/1 ('simpa [Category.assoc, this, kernel.condition]'): tactic 'assumption' failed

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 61.8s, verify 0.1s, in=1225, out=7013)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  kernel.ι g ≫ cokernel.π f = kernel.ι g ≫ (g ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.condition f))) := by rw [this]
  _ = (kernel.ι g ≫ g) ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.condition f)) := by
    rw [← CategoryTheory.Category.assoc]
  _ = 0 ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.condition f)) := by
    rw [CategoryTheory.Limits.kernel.condition]
  _ = 0 := by
    rw [CategoryTheory.Limits.zero_comp]
```

**lean_error:** tail step 1/8 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 9.1s, verify 0.1s, in=1191, out=811)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [← this, CategoryTheory.Category.assoc, CategoryTheory.Limits.kernel.condition, CategoryTheory.Limits.zero_comp]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
inst✝ : Abelian C
X Y Z : C
f : X ⟶ Y
g : Y ⟶ Z
...
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 9.1s, verify 0.1s, in=1212, out=2057)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← this, Category.assoc, kernel.condition, zero_comp]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 86.2s, verify 0.1s, in=1302, out=9816)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  kernel.ι g ≫ cokernel.π f = kernel.ι g ≫ (g ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) _)) := by rw [this.symm]
  _ = (kernel.ι g ≫ g) ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) _) := by rw [CategoryTheory.Category.assoc]
  _ = 0 ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) _) := by rw [CategoryTheory.Limits.kernel.condition]
  _ = 0 := by apply CategoryTheory.Limits.zero_comp
```

**lean_error:** tail step 1/5 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.1s, in=1200, out=957)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  kernel.ι g ≫ cokernel.π f = kernel.ι g ≫ (g ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.condition f))) := by rw [this]
  _ = (kernel.ι g ≫ g) ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.condition f)) := by rw [Category.assoc]
  _ = 0 ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) (cokernel.condition f)) := by rw [kernel.condition]
  _ = 0 := by simp
```

**lean_error:** tail step 1/5 ('calc'): <stdin>:1:4: unexpected end of input
