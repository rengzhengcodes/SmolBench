# CategoryTheory.Limits.IsColimit.OfNatIso.cocone_fac   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Limits/IsLimit.lean`  

**Ground-truth tail (from k):**
```lean
apply (coconeOfHom_fac _ _).symm
```

**True premises at k:** `CategoryTheory.Limits.IsColimit.OfNatIso.coconeOfHom_fac`, `Eq.symm`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | · | · | · |
| `hint:2` | ✓ | · | ✓ | · |
| `hint:3` | ✓ | · | ✓ | · |
| `noise:3` | ✓ | · | ✓ | · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 97.3s, verify 0.2s, in=351, out=4887)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Cocone.extend_homOfCocone h s, coconeOfHom_homOfCocone h s]
```

**lean_error:** tail step 1/1 ('rw [← Cocone.extend_homOfCocone h s, coconeOfHom_homOfCocone h s]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 11.7s, verify 0.1s, in=351, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 6.2s, verify 0.1s, in=351, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```

### `stepk:1` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 7.4s, verify 0.3s, in=351, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 73.7s, verify 0.1s, in=1068, out=3750)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Eq.symm (coconeOfHom_fac h (homOfCocone h s))
```

### `hint:2` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 12.0s, verify 0.1s, in=1068, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```

### `hint:2` · qwen3-lean-leannav · rollout 0 → **success**  (gen 6.3s, verify 0.1s, in=1068, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [coconeOfHom_fac]
```

### `hint:2` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 7.0s, verify 0.1s, in=1068, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 60.6s, verify 0.1s, in=4573, out=3096)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← coconeOfHom_fac h (homOfCocone h s)]
```

### `hint:3` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 11.8s, verify 0.1s, in=4573, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```

### `hint:3` · qwen3-lean-leannav · rollout 0 → **success**  (gen 6.4s, verify 0.1s, in=4573, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [coconeOfHom_fac]
```

### `hint:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 7.2s, verify 0.1s, in=4573, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 122.8s, verify 0.1s, in=4601, out=6665)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← coconeOfHom_fac]
```

### `noise:3` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 12.1s, verify 0.1s, in=4601, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```

### `noise:3` · qwen3-lean-leannav · rollout 0 → **success**  (gen 9.2s, verify 0.1s, in=4601, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [coconeOfHom_fac]
```

### `noise:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 7.1s, verify 0.1s, in=4601, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```
