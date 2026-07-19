# Complementeds.isCompl_coe   (k=0, 1 tactics total)

file: `Mathlib/Order/Disjoint.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [isCompl_iff, disjoint_coe, codisjoint_coe]
```

**True premises at k:** `isCompl_iff`, `Complementeds.disjoint_coe`, `Complementeds.codisjoint_coe`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✓ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | · · ✓ · |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ · |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | · ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 151.7s, verify 0.1s, in=228, out=5923)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split.
rintro ⟨h1, h2⟩
split
· apply subtype.coe_injective
  rw [coe_inf, h1, coe_bot]
· apply subtype.coe_injective
  rw [coe_sup, h2, coe_top]
rintro ⟨h1, h2⟩
split
· rw [← coe_inf, h1, coe_bot]
· rw [← coe_sup, h2, coe_top]
```

**lean_error:** tail step 1/11 ('split.'): 'split' tactic, term to split is not supported yet

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 190.5s, verify 0.1s, in=228, out=7515)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· rintro ⟨h₁, h₂⟩
  constructor
  · ext
    simp [coe_inf, h₁]
  · ext
    simp [coe_sup, h₂]
· rintro ⟨h₁, h₂⟩
  constructor
  · simp [coe_inf, ←coe_bot, ←h₁]
  · simp [coe_sup, ←coe_top, ←h₂]
```

**lean_error:** tail step 1/11 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 213.9s, verify 0.1s, in=228, out=8472)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· rintro ⟨h1, h2⟩
  constructor
  · rw [← coe_sup, h1]
    rfl
  · rw [← coe_inf, h2]
    rfl
· rintro ⟨h1, h2⟩
  constructor
  · apply Complementeds.ext
    rw coe_sup
    exact h1
  · apply Complementeds.ext
    rw coe_inf
    exact h2
```

**lean_error:** tail step 1/15 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 288.8s, verify 0.1s, in=228, out=11629)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split,
{ rintro ⟨h1, h2⟩,
  split,
  { ext, exact h1 },
  { ext, exact h2 } },
{ rintro ⟨h1, h2⟩,
  split,
  { ext, exact h1 },
  { ext, exact h2 } }
```

**lean_error:** tail step 1/9 ('split,'): <stdin>:1:5: expected end of input

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=228, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsCompl]
```

**lean_error:** tail step 1/1 ('simp [IsCompl]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=228, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsCompl, isCompl_iff]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=228, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsCompl, IsCompl_iff]
```

**lean_error:** tail step 1/1 ('simp [IsCompl, IsCompl_iff]'): unknown identifier 'IsCompl_iff'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.1s, in=228, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [IsCompl, coe_inf, coe_top, coe_sup, coe_bot]
```

**lean_error:** tail step 1/1 ('simp only [IsCompl, coe_inf, coe_top, coe_sup, coe_bot]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.1s, verify 0.1s, in=228, out=246)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsCompl]
```

**lean_error:** tail step 1/1 ('simp [IsCompl]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.2s, verify 0.1s, in=228, out=249)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsCompl]
```

**lean_error:** tail step 1/1 ('simp [IsCompl]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.1s, verify 0.1s, in=228, out=307)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 14.9s, verify 0.1s, in=228, out=461)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [isCompl_iff_disjoint_and_sup_eq_top, complemented_disjoint, complemented_sup, coe_top]
```

**lean_error:** tail step 1/1 ('simp only [isCompl_iff_disjoint_and_sup_eq_top, complemented_disjoint, complemented_sup, coe_top]'): unknown identifier 'isCompl_iff_disjoint_and_sup_eq_top'

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 87.8s, verify 0.2s, in=749, out=3403)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
simp [Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 95.6s, verify 0.2s, in=749, out=3693)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
simp
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 96.1s, verify 0.2s, in=749, out=3713)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
simp [Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 103.3s, verify 0.2s, in=749, out=3976)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
rw [Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
rfl
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=749, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [isCompl_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.9s, verify 0.1s, in=749, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [isCompl_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=749, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=749, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 6.2s, verify 0.1s, in=749, out=203)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, disjoint_coe, codisjoint_coe]
```

**final state (truncated):**
```
α : Type u_1
inst✝¹ : DistribLattice α
inst✝ : BoundedOrder α
a b : Complementeds α
⊢ Disjoint a b ∧ Codisjoint a b ↔ IsCompl a b
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 7.1s, verify 0.1s, in=749, out=215)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, disjoint_coe, codisjoint_coe]
```

**final state (truncated):**
```
α : Type u_1
inst✝¹ : DistribLattice α
inst✝ : BoundedOrder α
a b : Complementeds α
⊢ Disjoint a b ∧ Codisjoint a b ↔ IsCompl a b
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.5s, verify 0.1s, in=749, out=226)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 9.3s, verify 0.1s, in=749, out=287)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, disjoint_coe, codisjoint_coe]
```

**final state (truncated):**
```
α : Type u_1
inst✝¹ : DistribLattice α
inst✝ : BoundedOrder α
a b : Complementeds α
⊢ Disjoint a b ∧ Codisjoint a b ↔ IsCompl a b
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 157.1s, verify 0.1s, in=1474, out=2513)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff, Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
trivial
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 177.5s, verify 0.2s, in=1474, out=3552)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
rw [Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 193.1s, verify 0.2s, in=1474, out=3909)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
rw [disjoint_coe, codisjoint_coe]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 210.0s, verify 0.2s, in=1474, out=4595)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
rw [Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.9s, verify 0.1s, in=1474, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isCompl_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.1s, verify 0.1s, in=1474, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.2s, verify 0.1s, in=1474, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isCompl_iff, codisjoint_coe, disjoint_coe]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.2s, verify 0.1s, in=1474, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 15.4s, verify 0.1s, in=1474, out=258)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [isCompl_iff, Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 15.5s, verify 0.1s, in=1474, out=266)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 16.9s, verify 0.1s, in=1474, out=310)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isCompl_iff, Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 17.3s, verify 0.1s, in=1474, out=318)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isCompl_iff, disjoint_iff, codisjoint_iff, disjoint_coe, codisjoint_coe]
```

**final state (truncated):**
```
α : Type u_1
inst✝¹ : DistribLattice α
inst✝ : BoundedOrder α
a b : Complementeds α
⊢ ↑a ⊓ ↑b = ⊥ ∧ ↑a ⊔ ↑b = ⊤ ↔ a ⊓ b = ⊥ ∧ a ⊔ b = ⊤
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 93.4s, verify 0.2s, in=1512, out=3614)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
rw [Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
refl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 96.5s, verify 0.2s, in=1512, out=3727)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
rw [Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
exact Iff.rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 104.3s, verify 0.1s, in=1512, out=4014)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 153.7s, verify 0.2s, in=1512, out=6002)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
rw [disjoint_coe, codisjoint_coe]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=1512, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [isCompl_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.5s, verify 0.1s, in=1512, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=1512, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.7s, verify 0.1s, in=1512, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 7.2s, verify 0.1s, in=1512, out=216)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isCompl_iff, Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
```

**final state (truncated):**
```
α : Type u_1
inst✝¹ : DistribLattice α
inst✝ : BoundedOrder α
a b : Complementeds α
⊢ Disjoint a b ∧ Codisjoint a b ↔ IsCompl a b
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 7.3s, verify 0.1s, in=1512, out=220)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.9s, verify 0.1s, in=1512, out=236)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [isCompl_iff, Complementeds.disjoint_coe, Complementeds.codisjoint_coe]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 9.2s, verify 0.1s, in=1512, out=280)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [isCompl_iff, disjoint_coe, codisjoint_coe]
```
