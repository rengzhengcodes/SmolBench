# FiniteField.sum_subgroup_units   (k=4, 5 tactics total)

file: `Mathlib/FieldTheory/Finite/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

**True premises at k:** `FiniteField.sum_subgroup_units_eq_zero`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ X ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | · ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 182.5s, verify 0.1s, in=270, out=8034)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨a, a_mem, a_ne_one⟩ := G.exists_mem_ne 1,
let S := ∑ x : G, ↑x,
have S_eq : S = ∑ x : G, ↑a * ↑x := by {
  apply sum_congr rfl (λ x _, rfl) },
have S_eq' : S = ↑a * S := by { rw [S_eq, ← sum_mul_right] },
have : (1 - ↑a) * S = 0 := by { rw [S_eq', mul_sub_right_distrib, sub_self] },
apply eq_zero_of_ne_zero_of_mul_eq_zero,
{ rw [← Units.coe_one, Units.coe_ne_coe, ne.def], exact a_ne_one.symm },
exact this,
```

**lean_error:** tail step 1/9 ('obtain ⟨a, a_mem, a_ne_one⟩ := G.exists_mem_ne 1,'): <stdin>:1:49: unexpected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 202.7s, verify 0.1s, in=270, out=8979)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨g, hg⟩ : ∃ g : G, g ≠ 1 := by
  apply exists_ne (1 : G)
have hne : ↑g ≠ 1 := by
  rintro rfl
  exact hg (ext (one_eq_coe Kˣ).symm)
have hsum : ↑g * ∑ x : G, ↑x = ∑ x : G, ↑x := by
  rw [mul_sum]
  apply sum_congr (Equiv.mulLeft (group_of_subgroup G) g)
  intro x
  exact (Units.coe_mul _ _).symm
have hdiff : (↑g - 1) * ∑ x : G, ↑x = 0 := by
  rw [mul_sub, hsum, mul_one, sub_self]
exact eq_zero_of_mul_eq_zero hne hdiff
```

**lean_error:** tail step 1/13 ('obtain ⟨g, hg⟩ : ∃ g : G, g ≠ 1 := by'): <stdin>:1:37: unexpected end of input; expected '{'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 213.9s, verify 0.1s, in=270, out=9479)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases exists_ne 1 with ⟨g, hg⟩,
let S := ∑ x : ↥G, ↑↑x,
have h_mul : Function.Bijective (fun x : G => g * x) :=
  ⟨mulLeftInjective g, mulLeftSurjective g⟩,
have h_sum : ∑ x : G, ↑↑(g * x) = ∑ x : G, ↑↑x :=
  Fintype.sum_bijective (fun x => g * x) h_mul,
have h_gS : ∑ x : G, ↑↑(g * x) = ↑g * S := sum_mul_right g (fun x => ↑↑x) G,
have S_eq : S = ↑g * S := by
  rw [← h_gS, h_sum],
have h_zero : (1 - ↑g) * S = 0 :=
  by rw [mul_sub, mul_one, S_eq, sub_self],
have h1g : (1 - ↑g) ≠ 0 := by
  simp [sub_eq_zero, eq_comm, hg],
cases (no_zero_divisors_iff.1 inst✝²) (1 - ↑g) S h_zero with
| inl h => exact absurd h h1g
| inr h => exact h
```

**lean_error:** tail step 1/16 ('rcases exists_ne 1 with ⟨g, hg⟩,'): <stdin>:1:31: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 228.9s, verify 0.1s, in=270, out=10164)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨g, hg⟩ : ∃ g : G, ↑g ≠ 1 := by {
  have h := Subgroup.ne_bot_iff.1 G_bot,
  obtain ⟨g, hg⟩ := h,
  exact ⟨⟨g, hg⟩, hg⟩,
},
let S := ∑ x : G, ↑↑x,
have bij : Function.Bijective (λ x : G, g * x) :=
  (mul_left_bijective ↑g (Subgroup.inv_mem g g.property)).of_mul,
have h_sum : ∑ x : G, ↑↑(g * x) = ∑ x : G, ↑↑x :=
  Finset.sum_bij (λ x _ => g * x) (λ _ => trivial)
    (λ x y _ _ h => (mul_left_injective ↑g (Subgroup.inv_mem g g.property)).1 h)
    (λ y => ⟨g⁻¹ * y, trivial⟩)
    (λ x _ => by simp),
have h_gS : ↑g * S = S := by {
  rw [← Finset.sum_mul],
  exact h_sum.symm,
},
have h_eq : (1 - ↑g) * S = 0 := by {
  rw [mul_sub, mul_one, h_gS, sub_self],
},
have h_ne : 1 - ↑g ≠ 0 := by {
  intro h,
  apply hg,
  ext,
  exact Subgroup.coe_injective (congr_arg _ h),
},
exact (mul_eq_zero.1 h_eq).resolve_left h_ne,
```

**lean_error:** tail step 1/27 ('obtain ⟨g, hg⟩ : ∃ g : G, ↑g ≠ 1 := by {'): <stdin>:1:40: unexpected end of input; expected '}'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=270, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sum_units_eq_zero_of_ne_bot G_bot
```

**lean_error:** tail step 1/1 ('exact sum_units_eq_zero_of_ne_bot G_bot'): unknown identifier 'sum_units_eq_zero_of_ne_bot'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 70.3s, verify 0.1s, in=270, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sum_units_eq_zero G_bot
```

**lean_error:** tail step 1/1 ('exact sum_units_eq_zero G_bot'): unknown identifier 'sum_units_eq_zero'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 72.1s, verify 0.1s, in=270, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sum_Units_coe_eq_zero_of_ne_bot G_bot
```

**lean_error:** tail step 1/1 ('exact sum_Units_coe_eq_zero_of_ne_bot G_bot'): unknown identifier 'sum_Units_coe_eq_zero_of_ne_bot'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 81.7s, verify 0.0s, in=0, out=0)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** RuntimeError: Inference endpoint unreachable after 10 consecutive connection failures (instance-state check failed: ClientError: An error occurred (RequestExpired) when calling the DescribeInstances operation: Request has expired.). If the instance is running, your public IP probably changed and the

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.2s, in=270, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using sum_mul_coe_eq_zero_of_card_ne_one_of_sum_eq_zero G (card_ne_one_of_ne_bot G G_bot)
```

**lean_error:** tail step 1/1 ('simpa using sum_mul_coe_eq_zero_of_card_ne_one_of_sum_eq_zero G (card_ne_one_of_ne_bot G G_bot)'): unknown identifier 'sum_mul_coe_eq_zero_of_card_ne_one_of_sum_eq_zero'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.0s, verify 0.1s, in=270, out=179)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply sum_self_eq_zero
```

**lean_error:** tail step 1/1 ('apply sum_self_eq_zero'): unknown identifier 'sum_self_eq_zero'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.0s, verify 0.1s, in=270, out=210)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Units.sum_eq_zero_of_mul_left (nontrivial_iff_exists_ne_one.mp G_bot)
```

**lean_error:** tail step 1/1 ('exact Units.sum_eq_zero_of_mul_left (nontrivial_iff_exists_ne_one.mp G_bot)'): unknown constant 'Units.sum_eq_zero_of_mul_left'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.8s, verify 0.1s, in=270, out=277)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Subgroup.sum_coe_eq_zero_of_mul_left_inj G_bot fun a _ ↦ left_mul_injective a
```

**lean_error:** tail step 1/1 ('exact Subgroup.sum_coe_eq_zero_of_mul_left_inj G_bot fun a _ ↦ left_mul_injective a'): unknown constant 'Subgroup.sum_coe_eq_zero_of_mul_left_inj'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 18.1s, verify 0.1s, in=270, out=596)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sum_inv_eq_zero G G_bot
```

**lean_error:** tail step 1/1 ('exact sum_inv_eq_zero G G_bot'): unknown identifier 'sum_inv_eq_zero'

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 10.9s, verify 0.1s, in=995, out=405)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 11.1s, verify 0.1s, in=995, out=418)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 13.2s, verify 0.2s, in=995, out=511)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply sum_subgroup_units_eq_zero
exact G_bot
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 75.4s, verify 0.1s, in=995, out=3431)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=995, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=995, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.5s, verify 0.1s, in=995, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 5.5s, verify 0.1s, in=995, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.4s, verify 0.1s, in=995, out=169)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.8s, verify 0.1s, in=995, out=203)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.9s, verify 0.1s, in=995, out=208)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 10.1s, verify 0.1s, in=995, out=252)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 22.4s, verify 0.1s, in=2859, out=500)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero
```

**final state (truncated):**
```
case neg.hg
K : Type u_1
R : Type u_2
inst✝³ : Ring K
inst✝² : NoZeroDivisors K
G : Subgroup Kˣ
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 26.0s, verify 0.1s, in=2859, out=799)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 29.6s, verify 0.1s, in=2859, out=856)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 30.9s, verify 0.6s, in=2859, out=816)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.7s, verify 0.1s, in=2859, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.8s, verify 0.1s, in=2859, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=2859, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.0s, verify 0.1s, in=2859, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 11.9s, verify 0.1s, in=2859, out=121)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 13.0s, verify 0.1s, in=2859, out=193)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 13.5s, verify 0.1s, in=2859, out=203)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 13.6s, verify 0.1s, in=2859, out=182)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 7.3s, verify 0.1s, in=2883, out=275)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 16.1s, verify 0.1s, in=2883, out=643)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 25.1s, verify 0.1s, in=2883, out=1038)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 35.3s, verify 0.1s, in=2883, out=1543)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=2883, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=2883, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=2883, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 4.5s, verify 0.1s, in=2883, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.5s, verify 0.1s, in=2883, out=192)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.8s, verify 0.1s, in=2883, out=207)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 9.0s, verify 0.1s, in=2883, out=213)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 9.4s, verify 0.1s, in=2883, out=224)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```
