# FiniteField.sum_subgroup_units   (k=4, 5 tactics total)

file: `Mathlib/FieldTheory/Finite/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

**True premises at k:** `FiniteField.sum_subgroup_units_eq_zero`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 10.3s, verify 0.1s, in=299, out=346)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : ∀ x : ↥G, ∃ y : ↥G, ↑↑x + ↑↑y = 0 := by
  intro x
  obtain ⟨y, hy⟩ := subgroup.add_mem_cancel_right G (↑↑x) (-↑↑x)
  exact ⟨⟨y, hy⟩, Subtype.ext hy⟩
let f : ↥G → ↥G := fun x => (h x).some
have hf : ∀ x : ↥G, ↑↑x + ↑↑(f x) = 0 := fun x => (h x).some_spec
calc ∑ x : ↥G, ↑↑x
    = ∑ x : ↥G, -↑↑(f x) := by
  conv => enter [1, x]; rw [← add_eq_zero_iff_eq_neg, hf]
    ... = -∑ x : ↥G, ↑↑(f x) := by rw [sum_neg_distrib]
    ... = -∑ y : ↥G, ↑↑y := by
  apply sum_bij (fun x y => f x = y)
  · intro x; dsimp; rw [hf, add_eq_zero_iff_eq_neg, neg_add_self]; exact f x
  · intro x y hxy; exact (Subtype.ext_iff.mp hxy).symm
  · intro y; use (f y)
    dsimp; exact (hf y).symm
    ... = -∑ x : ↥G, ↑↑x := by refl
    ... = 0 := by rw [neg_eq_zero]
```

**lean_error:** tail step 1/18 ('have h : ∀ x : ↥G, ∃ y : ↥G, ↑↑x + ↑↑y = 0 := by'): <stdin>:1:48: unexpected end of input; expected '{'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 2.0s, in=269, out=45)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Subtype.coe_sum]
simp only [coeSubtype]
rw [← Units.val_sum]
convert Units.ext (sum_units_ne_zero G_bot)
simp only [Units.val_zero, Units.val_one]
```

**lean_error:** tail step 1/5 ('rw [← Subtype.coe_sum]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 114.1s, verify 0.1s, in=288, out=7130)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
let S := finset.sum finset.univ (λ x, x)
have h_mul : ∀ g : ↥G, g * S = S, from λ g, finset.sum_bij (λ x, g * x) (λ x, x * g⁻¹) (by simp) (by simp) (by simp)
have card : fintype.card ↥G > 1, by { rw [fintype.card_eq_one_iff], exact G_bot },
have exists_g : ∃ g : ↥G, g ≠ 1, from fintype.exists_ne (1 : ↥G),
cases exists_g with g hg,
have hS : S * (g - 1) = 0, by rw [← h_mul g, mul_sub, sub_self],
rw [sub_eq_zero, mul_comm] at hS,
exact hS.resolve_left (mt (λ H, hg (subgroup.coe_one g)) (subgroup.coe_one g))
```

**lean_error:** tail step 1/8 ('let S := finset.sum finset.univ (λ x, x)'): <stdin>:1:36: expected '↦', '=>'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=1027, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=985, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=1016, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply sum_subgroup_units_eq_zero
assumption
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=2882, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=2831, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.2s, verify 0.2s, in=2871, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply sum_subgroup_units_eq_zero
assumption
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=2912, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=3083, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=2901, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply sum_subgroup_units_eq_zero
assumption
```
