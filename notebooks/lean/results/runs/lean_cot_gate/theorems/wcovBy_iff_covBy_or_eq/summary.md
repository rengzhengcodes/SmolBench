# wcovBy_iff_covBy_or_eq   (k=0, 1 tactics total)

file: `Mathlib/Order/Cover.lean`  

**Ground-truth tail (from k):**
```lean
rw [le_antisymm_iff, wcovBy_iff_covBy_or_le_and_le]
```

**True premises at k:** `le_antisymm_iff`, `wcovBy_iff_covBy_or_le_and_le`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ · ✘ · |
| `hint:2` | ✓ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✘ ✓ ✘ ✘ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✘ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 56.4s, verify 0.1s, in=229, out=2296)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro h
  by_cases h_eq : a = b
  · exact Or.inr h_eq
  · exact Or.inl (lt_of_le_ne h h_eq)
· intro h
  cases h
  · exact h.le
  · exact le_rfl
```

**lean_error:** tail step 1/9 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 119.4s, verify 0.1s, in=229, out=4601)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro hab
  by_cases h : a = b
  · right; exact h
  · left; split; [ exact hab | intro hba; apply absurd (antisymm hab hba) h ]
· intro h
  cases h
  · exact h.1
  · subst h; exact le_refl _
```

**lean_error:** tail step 1/9 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 149.7s, verify 0.1s, in=229, out=5751)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
intro h
by_cases ha : a = b
  right
  exact ha
  left
  exact ⟨h, ha⟩
intro h
cases h
  exact h_left
  exact h.le
```

**lean_error:** tail step 1/11 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 182.6s, verify 0.1s, in=229, out=7021)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro h
  by_cases a = b
  · right; exact this
  · left; apply lt_of_le_ne; exact ⟨h, this⟩
· rintro (hlt | rfl); exact hlt.le; exact le_rfl
```

**lean_error:** tail step 1/6 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=229, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [covBy, or_comm]
```

**lean_error:** tail step 1/1 ('simp [covBy, or_comm]'): unknown identifier 'covBy'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.8s, verify 0.1s, in=229, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CovBy, or_comm]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝ : PartialOrder α
a b c : α
⊢ a ⩿ b ↔ a = b ∨ a < b ∧ ∀ ⦃c : α⦄, a < c → ¬c < b
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=229, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Covby, not_lt]
```

**lean_error:** tail step 1/1 ('simp [Covby, not_lt]'): unknown identifier 'Covby'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.9s, verify 0.1s, in=229, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CovBy, or_comm]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝ : PartialOrder α
a b c : α
⊢ a ⩿ b ↔ a = b ∨ a < b ∧ ∀ ⦃c : α⦄, a < c → ¬c < b
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 95.3s, verify 0.1s, in=644, out=3752)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, ← le_antisymm_iff]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 116.4s, verify 0.3s, in=644, out=4499)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
apply or_congr_right
apply le_antisymm_iff
```

**lean_error:** tail step 3/3 ('apply le_antisymm_iff'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 227.0s, verify 0.1s, in=644, out=8782)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw wcovBy_iff_covBy_or_le_and_le
rw le_antisymm_iff
refl
```

**lean_error:** tail step 1/3 ('rw wcovBy_iff_covBy_or_le_and_le'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 239.8s, verify 0.1s, in=644, out=9371)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
apply or_congr (iff.refl _) (le_antisymm_iff.symm)
```

**lean_error:** tail step 2/2 ('apply or_congr (iff.refl _) (le_antisymm_iff.symm)'): unknown identifier 'iff.refl'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=644, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.1s, in=644, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=644, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=644, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 166.8s, verify 0.1s, in=786, out=2613)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (wcovBy_iff_covBy_or_le_and_le.trans (or_congr Iff.rfl le_antisymm_iff))
```

**lean_error:** tail step 1/1 ('exact (wcovBy_iff_covBy_or_le_and_le.trans (or_congr Iff.rfl le_antisymm_iff))'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 196.1s, verify 0.1s, in=786, out=3806)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
rw [le_antisymm_iff]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 221.9s, verify 0.1s, in=786, out=6251)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (wcovBy_iff_covBy_or_le_and_le.trans (or_congr_right le_antisymm_iff))
```

**lean_error:** tail step 1/1 ('apply (wcovBy_iff_covBy_or_le_and_le.trans (or_congr_right le_antisymm_iff))'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 246.0s, verify 0.2s, in=786, out=5175)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
exact (or_congr rfl le_antisymm_iff.symm)
```

**lean_error:** tail step 2/2 ('exact (or_congr rfl le_antisymm_iff.symm)'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=786, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=786, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=786, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=786, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 94.6s, verify 0.2s, in=810, out=3729)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
apply or_congr rfl le_antisymm_iff.symm
```

**lean_error:** tail step 2/2 ('apply or_congr rfl le_antisymm_iff.symm'): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 132.8s, verify 0.1s, in=810, out=5109)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
rw [← le_antisymm_iff]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 140.5s, verify 0.1s, in=810, out=5401)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw wcovBy_iff_covBy_or_le_and_le
rw or_congr_right (le_antisymm_iff a b)
```

**lean_error:** tail step 1/2 ('rw wcovBy_iff_covBy_or_le_and_le'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 220.8s, verify 0.1s, in=810, out=8506)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, ← le_antisymm_iff]
refl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=810, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=810, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.8s, verify 0.1s, in=810, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.7s, verify 0.1s, in=810, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```
