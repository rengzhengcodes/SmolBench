# CategoryTheory.Presieve.factorsThruAlong_id   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Sites/Coverage.lean`  

**Ground-truth tail (from k):**
```lean
simp [FactorsThruAlong, FactorsThru]
```

**True premises at k:** `CategoryTheory.Presieve.FactorsThruAlong`, `CategoryTheory.Presieve.FactorsThru`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ · · ✓ |
| `hint:2` | ✘ ✓ ✓ ✓ |
| `hint:3` | ✓ ✘ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=239, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.6s, verify 0.2s, in=239, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [FactorsThruAlong]
```

**final state (truncated):**
```
C : Type u_2
inst✝ : Category.{u_1, u_2} C
X : C
S T : Presieve X
⊢ (∀ ⦃Z : C⦄ ⦃g : Z ⟶ X⦄, S g → ∃ W i e, T e ∧ i ≫ e = g) ↔ FactorsThru S T
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.8s, verify 0.2s, in=239, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [FactorsThruAlong]
```

**final state (truncated):**
```
C : Type u_2
inst✝ : Category.{u_1, u_2} C
X : C
S T : Presieve X
⊢ (∀ ⦃Z : C⦄ ⦃g : Z ⟶ X⦄, S g → ∃ W i e, T e ∧ i ≫ e = g) ↔ FactorsThru S T
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.1s, verify 0.2s, in=239, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.3s, in=1046, out=8)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
aesop_cat
```

**lean_error:** tail step 1/1 ('aesop_cat'): tactic 'aesop' failed, failed to prove the goal after exhaustive search.

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.1s, verify 0.2s, in=1046, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.4s, verify 0.2s, in=1046, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.7s, verify 0.2s, in=1046, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 3.2s, verify 0.2s, in=2034, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.4s, verify 0.3s, in=2034, out=8)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
aesop_cat
```

**lean_error:** tail step 1/1 ('aesop_cat'): tactic 'aesop' failed, failed to prove the goal after exhaustive search.

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 3.6s, verify 0.2s, in=2034, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [FactorsThru, FactorsThruAlong]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.8s, verify 0.2s, in=2034, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.9s, verify 0.2s, in=2059, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.3s, verify 0.2s, in=2059, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.6s, verify 0.2s, in=2059, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.9s, verify 0.2s, in=2059, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [FactorsThruAlong, FactorsThru]
```
