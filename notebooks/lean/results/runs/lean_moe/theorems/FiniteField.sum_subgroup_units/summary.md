# FiniteField.sum_subgroup_units   (k=4, 5 tactics total)

file: `Mathlib/FieldTheory/Finite/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

**True premises at k:** `FiniteField.sum_subgroup_units_eq_zero`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 20.1s, verify 0.4s, in=341, out=3977)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using G.sum_eq_zero_of_ne_bot G_bot
```

**lean_error:** tail step 1/1 ('simpa using G.sum_eq_zero_of_ne_bot G_bot'): invalid field 'sum_eq_zero_of_ne_bot', the environment does not contain 'Subgroup.sum_eq_zero_of_ne_bot'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 239.7s, verify 0.1s, in=294, out=27905)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h_exists : ∃ (x : Kˣ), x ∈ G ∧ x ≠ 1 := by
  by_contra! h
  have h₂ : G = ⊥ := by
    apply Subgroup.ext
    intro x
    constructor <;> intro h₃
    · -- If x ∈ G, then x = 1
      have h₄ := h x
      have h₅ : x ∈ G := h₄
      have h₆ : x = 1 := by
        simp_all [h]
      exact h₆
    · -- If x = 1, then x ∈ G
      simp_all [h]
      <;> aesop
  exact h₂ G_bot

obtain ⟨x, hx, hx_ne_one⟩ := h_exists

set g : ↥G := ⟨x, hx⟩ with hg_def

have g_ne_one : (g : Kˣ) ≠ 1 := by
  intro h
  apply hx_ne_one
  simp_all [Subgroup.mem_carrier]
  <;> aesop

have f_def : ∀ (y : ↥G), (g : Kˣ) * (y : Kˣ) ∈ G := by
  intro y
  have h₁ : (g : Kˣ) ∈ G := g.property
  have h₂ : (y : Kˣ) ∈ G := y.property
  exact G.mul_mem h₁ h₂

let f : ↥G → ↥G := fun y => ⟨(g : Kˣ) * (y : Kˣ), f_def y⟩

have f_injective : Function.Injective f := by
  intro y₁ y₂ h
  have h₁ : (g : Kˣ) * (y₁ : Kˣ) = (g : Kˣ) * (y₂ : Kˣ) := by
    simp_all [f]
    <;> aesop
  have h₂ : (y₁ : Kˣ) = (y₂ : Kˣ) := by
    apply mul_left_cancel₀ (show (g : Kˣ) ≠ 0 by
      intro h₃
      have h₄ : (g : Kˣ) = 0 := h₃
      have h₅ : IsUnit (g : Kˣ) := by
        exact ⟨(g : Kˣ)⁻¹, by simp [Units.ext_iff], ⟨(g : Kˣ)⁻¹ * (g : Kˣ), by simp [mul_inv_self]⟩, ⟨(g : Kˣ) * (g : Kˣ)⁻¹, by simp [inv_mul_self]⟩⟩
      have h₆ : ¬IsUnit (0 : Kˣ) := by
        intro h₇
        rw [IsUnit] at h₇
        obtain ⟨z, hz₁, hz₂⟩ := h₇
        have h₈ : (0 : Kˣ) * z = 1 := by simpa using hz₁
        have h₉ : (0 : Kˣ) * z = 0 := by simp
        rw [h₉] at h₈
        norm_num at h₈
        <;> simp_all
      exact h₆ h₅
    )
    rw [← mul_one (g : Kˣ)]
    simp_all [mul_assoc]
    <;> aesop
  have h₃ : y₁ = y₂ := by
    apply Subtype.ext
    exact h₂
  exact h₃

have f_equiv : ↥G ≃ ↥G := Fintype.equivOfInjective f f_injective

have h_sum_f : ∑ y : ↥G, ↑(f y) = ∑ y : ↥G, ↑y := by
  calc
    ∑ y : ↥G, ↑(f y) = ∑ y : ↥G, ↑(f_equiv y) := by
      apply Finset.sum_congr rfl
      intro y _
      rfl
    _ = ∑ y : ↥G, ↑y := by
      apply Equiv.sum_bij

have h_f_coe : ∀ (y : ↥G), ↑(f y) = (↑g : K) * (↑y : K) := by
  intro y
  simp only [f, Subtype.coe_mk, coe_mk]
  norm_cast
  <;> simp [mul_assoc]
  <;> ring_nf
  <;> norm_num
  <;> linarith

have h_sum_f' : ∑ y : ↥G, ↑(f y) = ∑ y : ↥G, (↑g : K) * (↑y : K) := by
  apply Finset.sum_congr rfl
  intro y _
  rw [h_f_coe y]

have h_sum_f'' : ∑ y : ↥G, (↑g : K) * (↑y : K) = (↑g : K) * ∑ y : ↥G, (↑y : K) := by
  rw [Finset.mul_sum]
  <;> simp [mul_assoc]
  <;> ring_nf
  <;> norm_num
  <;> linarith

have h_sum_f''' : ∑ y : ↥G, ↑(f y) = (↑g : K) * ∑ y : ↥G, ↑y := by
  calc
    ∑ y : ↥G, ↑(f y) = ∑ y : ↥G, (↑g : K) * (↑y : K) := h_sum_f'
    _ = (↑g : K) * ∑ y : ↥G, (↑y : K) := h_sum_f''
    _ = (↑g : K) * ∑ y : ↥G, ↑y := by
      simp [Subtype.coe_mk, coe_mk]
      <;> rfl

have h_main : (↑g : K) * ∑ y : ↥G, ↑y = ∑ y : ↥G, ↑y := by
  linarith

have h_S_sub : (↑g - 1 : K) * (∑ y : ↥G, ↑y) = 0 := by
  calc
    (↑g - 1 : K) * (∑ y : ↥G, ↑y) = (↑g : K) * (∑ y : ↥G, ↑y) - 1 * (∑ y : ↥G, ↑y) := by
      rw [mul_sub]
    _ = (↑g : K) * (∑ y : ↥G, ↑y) - (∑ y : ↥G, ↑y) := by simp
    _ = (∑ y : ↥G, ↑y) - (∑ y : ↥G, ↑y) := by rw [h_main]
    _ = 0 := by simp

have h_g_coe_ne_one : (↑g : K) ≠ 1 := by
  intro h
  have h₂ : (g : Kˣ) = 1 := by
    norm_cast at h ⊢
    <;> simp_all [Subtype.coe_mk, coe_mk]
    <;> aesop
  exact g_ne_one h₂

have h_g_sub_one_ne_zero : (↑g - 1 : K) ≠ 0 := by
  intro h
  have h₂ : (↑g : K) = 1 := by
    have h₃ : (↑g - 1 : K) = 0 := h
    have h₄ : (↑g : K) = 1 := by
      rw [sub_eq_zero] at h₃
      exact h₃
    exact h₄
  exact h_g_coe_ne_one h₂

have h_S_zero : (∑ y : ↥G, ↑y) = 0 := by
  have h₁ : (↑g - 1 : K) * (∑ y : ↥G, ↑y) = 0 := h_S_sub
  have h₂ : (↑g - 1 : K) ≠ 0 := h_g_sub_one_ne_zero
  exact noZeroDivisors h₂ h₁

exact h_S_zero
```

**lean_error:** tail step 1/122 ('have h_exists : ∃ (x : Kˣ), x ∈ G ∧ x ≠ 1 := by'): <stdin>:1:47: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.7s, verify 0.1s, in=283, out=1044)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨g, hg⟩ : ∃ g : ↥G, g ≠ 1 := by
  by_contra h
  push_neg at h
  have : G = ⊥ := by
    apply Subgroup.eq_bot_iff.mpr
    intro x hx
    have := h ⟨x, hx⟩
    simp_all
  contradiction
have hsum : (↑g - 1 : K) * ∑ x : ↥G, (↑↑x : K) = 0 := by
  calc
    (↑g - 1 : K) * ∑ x : ↥G, (↑↑x : K) = ↑g * ∑ x : ↥G, (↑↑x : K) - ∑ x : ↥G, (↑↑x : K) := by
      rw [sub_mul]
    _ = ∑ x : ↥G, (↑↑(g * x) : K) - ∑ x : ↥G, (↑↑x : K) := by
      rw [mul_sum]
      congr 1
      ext x
      simp [coe_mul]
    _ = 0 := by
      have : ∑ x : ↥G, (↑↑(g * x) : K) = ∑ x : ↥G, (↑↑x : K) := by
        apply Finset.sum_bij' (fun x : ↥G => g * x) (fun x : ↥G => g⁻¹ * x)
        · intro x _; simp [mul_assoc]
        · intro x _; simp [mul_assoc]
        · intro x _; simp [mul_assoc]
        · intro x _; simp [mul_assoc]
        · intro x _; simp
      rw [this]
      simp
have : (↑g - 1 : K) ≠ 0 := by
  intro h
  apply hg
  simp_all [sub_eq_zero]
have : ∑ x : ↥G, (↑↑x : K) = 0 := by
  apply eq_of_sub_eq_zero
  apply mul_left_cancel₀ this
  rw [hsum]
  simp
exact this
```

**lean_error:** tail step 1/38 ('obtain ⟨g, hg⟩ : ∃ g : ↥G, g ≠ 1 := by'): <stdin>:1:38: unexpected end of input; expected '{'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.5s, verify 1.0s, in=1085, out=551)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using FiniteField.sum_subgroup_units_eq_zero (K:=K) (G:=G) G_bot
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 155.1s, verify 0.2s, in=1087, out=18054)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_sum_G : ∑ x : G, (x.val : K) = 0 := FiniteField.sum_subgroup_units_eq_zero G_bot
have h_sum_eq : ∑ x : ↥G, ↑↑x = ∑ x : G, (x.val : K) := by
  let e : G ≃ ↥G := ⟨fun x => ⟨x.val, x.property⟩, fun y => ⟨y.val, by exact y.property⟩, _, _⟩
  constructor <;> intro (x : G) <;> simp [Subgroup.mem_carrier] <;> aesop
  <;> constructor <;> intro (y : ↥G) <;> simp_all [Subgroup.mem_carrier] <;> aesop
  <;>
  (try simp_all) <;>
  (try aesop)
  <;>
  (try
    {
      intros
      <;> simp_all [Subgroup.mem_carrier]
      <;> aesop
    })
  <;>
  (try
    {
      aesop
    })
  have h4 : ∑ x : ↥G, ↑↑x = ∑ x : G, ↑↑(e x) := by
    rw [Equiv.sum_bij e.symm]
  rw [h4]
  apply Finset.sum_congr rfl
  intro x _
  simp [e, Submodule.coe_coe, Submodule.coe_val]
  <;>
  simp_all [Submodule.coe_coe, Submodule.coe_val]
  <;>
  aesop
linarith
```

**lean_error:** tail step 2/31 ('have h_sum_eq : ∑ x : ↥G, ↑↑x = ∑ x : G, (x.val : K) := by'): <stdin>:1:58: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 20.5s, verify 0.1s, in=1035, out=2175)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.5s, verify 0.1s, in=3031, out=1061)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (FiniteField.sum_subgroup_units_eq_zero (K:=K) (G:=G) G_bot)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 202.1s, verify 0.1s, in=3093, out=23427)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hG_ne_bot : G ≠ ⊥ := by
  intro h
  apply G_bot
  exact h
-- Construct an equivalence between G and ↥G
have h_equiv : G ≃ ↥G := by
  refine' ⟨fun x => ⟨(x : Kˣ), x.property⟩, fun x => ⟨x.val, x.2⟩, _, _⟩
  · -- Prove that the first function is well-defined
    intro x
    exact x.property
  · -- Prove that the second function is well-defined
    intro x
    exact x.2
  · -- Prove that they are inverses
    intro x
    simp [Subgroup.mem_carrier]
    <;> aesop
  · -- Prove that they are inverses the other way
    intro x
    simp [Subgroup.mem_carrier]
    <;> aesop
-- Transfer the Fintype instance from ↥G to G
haveI : Fintype G := Fintype.ofEquiv (↥G) h_equiv
-- Apply the lemma to get the sum over G
have h_sum_G : ∑ x : G, (x.val : K) = 0 := by
  apply FiniteField.sum_subgroup_units_eq_zero
  <;> assumption
-- Show that the sum over G is equal to the sum over ↥G
have h_sum_eq : ∑ x : ↥G, ↑↑x = ∑ x : G, (x.val : K) := by
  -- Use the equivalence to change the sum
  have h₁ : ∑ x : G, (x.val : K) = ∑ y : ↥G, ((h_equiv.symm y).val : K) := by
    rw [Equiv.sum_bij' h_equiv]
    <;> simp [Function.comp_apply]
  -- Show that ((h_equiv.symm y).val : K) = ↑↑y for y : ↥G
  have h₂ : ∑ y : ↥G, ((h_equiv.symm y).val : K) = ∑ y : ↥G, ↑↑y := by
    apply Finset.sum_congr rfl
    intro y hy
    -- Simplify the expression for h_equiv.symm y
    have h₃ : (h_equiv.symm y : Kˣ) = y.val := by
      dsimp [h_equiv] at *
      <;>
      (try cases y <;> simp_all [Subgroup.mem_carrier, Subgroup.val_mem_carrier]) <;>
      (try aesop) <;>
      (try
        {
          y
        }) <;>
      (try
        {
          simp_all [Subgroup.mem_carrier, Subgroup.val_mem_carrier]
          <;> aesop
        })
    -- Now, we have (h_equiv.symm y : Kˣ) = y.val
    -- Therefore, ((h_equiv.symm y).val : K) = (y.val : K)
    -- And ↑↑y = (y : Kˣ).val = (y.val : K)
    -- So they are equal.
    calc
      ((h_equiv.symm y).val : K) = ((h_equiv.symm y : Kˣ) : K) := by simp
      _ = (y.val : K) := by rw [h₃]
      _ = ↑↑y := by
        simp [Submodule.coe_coe]
        <;>
        simp_all [Submodule.coe_coe]
        <;>
        aesop
  -- Therefore, the two sums are equal.
  linarith
-- Therefore, the sum over ↥G is 0.
linarith
```

**lean_error:** tail step 1/69 ('have hG_ne_bot : G ≠ ⊥ := by'): <stdin>:1:28: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.2s, verify 0.1s, in=2972, out=509)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero G_bot
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.6s, verify 0.1s, in=2799, out=858)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using FiniteField.sum_subgroup_units_eq_zero (K:=K) (G:=G) G_bot
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 83.6s, verify 0.2s, in=3325, out=9700)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply FiniteField.sum_subgroup_units_eq_zero
<;> assumption
<;> try simp_all
<;> try aesop
```

**lean_error:** tail step 2/4 ('<;> assumption'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.1s, verify 0.1s, in=2942, out=497)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sum_subgroup_units_eq_zero G_bot
```
