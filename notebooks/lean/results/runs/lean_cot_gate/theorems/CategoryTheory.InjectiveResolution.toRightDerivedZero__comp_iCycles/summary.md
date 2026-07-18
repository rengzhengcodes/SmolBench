# CategoryTheory.InjectiveResolution.toRightDerivedZero'_comp_iCycles   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Abelian/RightDerived.lean`  

**Ground-truth tail (from k):**
```lean
simp [toRightDerivedZero']
```

**True premises at k:** `CategoryTheory.InjectiveResolution.toRightDerivedZero'`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | · ✓ ✓ ✘ |
| `hint:2` | · ✓ ✓ ✓ |
| `hint:3` | ✓ · ✓ · |
| `noise:3` | · ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.7s, verify 0.1s, in=366, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasInjectiveResolutions C
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.0s, verify 0.1s, in=366, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.1s, verify 0.1s, in=366, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=366, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [P.toRightDerivedZero'_def]
```

**lean_error:** tail step 1/1 ("simp [P.toRightDerivedZero'_def]"): invalid field 'toRightDerivedZero'_def', the environment does not contain 'CategoryTheory.InjectiveResolution.toRightDerivedZero'_def'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=761, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasInjectiveResolutions C
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=761, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.5s, verify 0.1s, in=761, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=761, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.8s, verify 0.1s, in=1474, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.9s, verify 0.1s, in=1474, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [HomologicalComplex.liftCycles]
```

**final state (truncated):**
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasInjectiveResolutions C
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.0s, verify 0.1s, in=1474, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.1s, verify 0.1s, in=1474, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [HomologicalComplex.liftCycles]
```

**final state (truncated):**
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasInjectiveResolutions C
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=1499, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasInjectiveResolutions C
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=1499, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=1499, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 7.5s, verify 0.1s, in=1499, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [toRightDerivedZero']
```
