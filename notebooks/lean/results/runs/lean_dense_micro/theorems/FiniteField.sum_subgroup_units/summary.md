# FiniteField.sum_subgroup_units   (k=4, 5 tactics total)

file: `Mathlib/FieldTheory/Finite/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

**True premises at k:** `FiniteField.sum_subgroup_units_eq_zero`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✓ ✘ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 4.1s, verify 0.1s, in=299, out=160)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : ∑ x : ↥G, ↑↑x = ∑ x : ↥G, if x = 1 then ↑↑x else ↑↑x + ↑↑(x⁻¹),
  from Finset.sum_congr rfl (λ x hx, if_pos (Subgroup.inv_mem G x)),
conv in (Finset.sum _ _) { rw [Finset.sum_add_distrib, Finset.sum_involution] },
have : ∀ x : ↥G, x ≠ 1 → (x⁻¹).val ≠ x.val,
  from λ x hx h, hx (Subgroup.inv_eq_one G h),
simp only [Subgroup.coe_inv, Finset.sum_const_zero, this, if_neg, add_right_neg]
```

**lean_error:** tail step 1/6 ('have h : ∑ x : ↥G, ↑↑x = ∑ x : ↥G, if x = 1 then ↑↑x else ↑↑x + ↑↑(x⁻¹),'): <stdin>:1:71: expected '|'

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 6.2s, verify 0.1s, in=299, out=252)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : ∀ x : ↥G, ↑↑x ≠ 0 := by exact fun x => Units.ne_zero ↑x,
let x₀ : ↥G := Classical.arbitrary ↥G,
have hx₀ : ↑↑x₀ ≠ 0 := h x₀,
let xs := (Finset.univ : Finset ↥G).erase x₀,
rw show ∑ x : ↥G, ↑↑x = ↑↑x₀ + ∑ x in xs, ↑↑x,
  by rw [Finset.sum_eq_sum_diff_singleton_add x₀, Finset.sum_singleton],
have h' : ∑ x in xs, ↑↑x = -↑↑x₀,
  from eq_neg_of_add_eq_zero (by exact Finset.sum_involution (fun x => x * x₀⁻¹) _ _ _),
  exact fun x hx => x₀⁻¹ ≠ x * x₀⁻¹,
  exact fun x hx => (x * x₀⁻¹) * x₀ = x,
  exact fun x hx => x * x₀⁻¹ ≠ x₀⁻¹),
rw h',
exact neg_add_self ↑↑x₀
```

**lean_error:** tail step 1/13 ('have h : ∀ x : ↥G, ↑↑x ≠ 0 := by exact fun x => Units.ne_zero ↑x,'): <stdin>:1:64: expected end of input

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 6.8s, verify 0.1s, in=299, out=280)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : ∀ x : ↥G, ∃ y : ↥G, ↑↑x + ↑↑y = 0 := by
  intro x
  obtain ⟨y, hy⟩ := subgroup.add_inv_mem G (↑x)
  exact ⟨⟨y, hy⟩, Subtype.coe_injective hy⟩
let f : ↥G → ↥G := fun x => (h x).some
have hf : ∀ x : ↥G, ↑↑x + ↑↑(f x) = 0 := fun x => (h x).some_spec
clear h
calc ∑ x : ↥G, ↑↑x
    = ∑ x : ↥G, -↑↑(f x) := by
  conv => enter [1, expr.sum]; intro x; rw [←add_eq_zero_iff_eq_neg, hf x]
    ... = -∑ x : ↥G, ↑↑(f x) := by rw [Finset.sum_hom fun x => -x]
    ... = -∑ x : ↥G, ↑↑x := by
  conv => enter [1, expr.sum]; intro x; rw [←hf x, add_comm, add_eq_zero_iff_eq_neg]
    ... = 0 := by rw [neg_add_self]
```

**lean_error:** tail step 1/14 ('have h : ∀ x : ↥G, ∃ y : ↥G, ↑↑x + ↑↑y = 0 := by'): <stdin>:1:48: unexpected end of input; expected '{'

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 10.3s, verify 0.1s, in=299, out=419)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : ∀ x : G, ∃ y : G, x * y = 1 := λ x, Subgroup.mul_inv x,
let units : G → Kˣ := Subgroup.subtype,
have h2 : ∀ x : G, ↑(units x) = x := λ x, rfl,
have h3 : ∀ x : G, ∃ y : G, ↑(units x) * ↑(units y) = 1 := λ x, h x,
let f : G → K := λ x, ↑(units x),
have h4 : ∀ x : G, f x ≠ 0 := λ x, Units.ne_zero _,
let g : G → K := λ x, 1 / f x,
have h5 : ∀ x : G, f x * g x = 1 := λ x, div_mul_cancel (h4 x),
let h6 := ∑ x : G, g x,
have h7 : h6 ≠ 0 := λ h6_eq_0, G_bot $ Subgroup.ext $ λ x, by
  { have : f x * h6 = 0, from h6_eq_0 ▸ finset.sum_mul,
    rw [finset.sum_mul, h5 x] at this,
    exact this },
have h8 : h6 * ∑ x : G, f x = ∑ x : G, 1 := finset.sum_mul,
have h9 : h6 * ∑ x : G, f x = Fintype.card G := finset.sum_const 1,
rw h9 at h8,
have h10 : ∑ x : G, f x = Fintype.card G / h6 := eq_div_of_mul_eq h7 h8,
have h11 : ∑ x : G, f x = 0 := by
  { have : Fintype.card G / h6 = 0, from nat.cast_eq_zero _,
    exact this },
exact h11
```

**lean_error:** tail step 1/21 ('have h : ∀ x : G, ∃ y : G, x * y = 1 := λ x, Subgroup.mul_inv x,'): <stdin>:1:43: expected '↦', '=>'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=299, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact G.sum_eq_zero_of_ne_bot G_bot
```

**lean_error:** tail step 1/1 ('exact G.sum_eq_zero_of_ne_bot G_bot'): invalid field 'sum_eq_zero_of_ne_bot', the environment does not contain 'Subgroup.sum_eq_zero_of_ne_bot'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=299, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sum_ne_zero_comm_pairwise_of_card_gt_one G_bot
```

**lean_error:** tail step 1/1 ('exact sum_ne_zero_comm_pairwise_of_card_gt_one G_bot'): unknown identifier 'sum_ne_zero_comm_pairwise_of_card_gt_one'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=299, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact G.sum_eq_zero_iff_ne_bot.mpr G_bot
```

**lean_error:** tail step 1/1 ('exact G.sum_eq_zero_iff_ne_bot.mpr G_bot'): invalid field 'sum_eq_zero_iff_ne_bot', the environment does not contain 'Subgroup.sum_eq_zero_iff_ne_bot'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=299, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sum_const_eq_zero (G_bot ∘ subgroup.eq_bot_iff_forall.mpr) 1
```

**lean_error:** tail step 1/1 ('exact sum_const_eq_zero (G_bot ∘ subgroup.eq_bot_iff_forall.mpr) 1'): unknown identifier 'sum_const_eq_zero'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1027, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=1027, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact @FiniteField.sum_subgroup_units_eq_zero _ _ G _ G_bot
```

**lean_error:** tail step 1/1 ('exact @FiniteField.sum_subgroup_units_eq_zero _ _ G _ G_bot'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=1027, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact @FiniteField.sum_subgroup_units_eq_zero _ _ _ _ _ G_bot
```

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.1s, verify 0.2s, in=1027, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero (ne_of_lt (Fintype.card_pos_iff.mpr ⟨1, G_bot⟩))
```

**lean_error:** tail step 1/1 ('exact FiniteField.sum_subgroup_units_eq_zero (ne_of_lt (Fintype.card_pos_iff.mpr ⟨1, G_bot⟩))'): application type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 0.9s, verify 0.1s, in=1027, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=1027, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.1s, verify 0.1s, in=1027, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.3s, verify 0.1s, in=1027, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```
