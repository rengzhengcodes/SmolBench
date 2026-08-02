# not_irreducible_expand   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
exact not_irreducible_pow (Fact.out : p.Prime).ne_one
```

**True premises at k:** `not_irreducible_pow`, `Fact.out`, `Nat.Prime.ne_one`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 18.6s, verify 0.3s, in=407, out=5012)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro h
let g := map (↑(RingEquiv.symm (frobeniusEquiv R p))) f
have hp : 0 < p := (Fact.out : Nat.Prime p).pos
have hfac := h.2 g (g ^ p.pred) (by
  simpa [pow_succ, Nat.succ_pred_eq_of_pos hp] using (pow_succ g p.pred))
have hunitg : IsUnit g :=
  by
    rcases hfac with hunit | hunit
    · exact hunit
    · exact (isUnit_of_pow (n:=p.pred) hunit)
have hunitpow : IsUnit (g ^ p) := (IsUnit.pow hunitg p)
exact h.1 hunitpow
```

**lean_error:** tail step 2/12 ('let g := map (↑(RingEquiv.symm (frobeniusEquiv R p))) f'): typeclass instance problem is stuck, it is often due to metavariables

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 151.9s, verify 0.1s, in=371, out=18964)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem your_theorem_name : ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p) := by
  have h₁ : map (↑(RingEquiv.symm (frobeniusEquiv R p))) (f ^ p) = (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ p := by
    apply map_pow
    <;>
    (try simp_all [RingEquiv.apply_symm_apply]) <;>
    (try ring_nf) <;>
    (try norm_num) <;>
    (try aesop)
    <;>
    (try
      {
        simp_all [RingEquiv.apply_symm_apply]
        <;>
        ring_nf
        <;>
        norm_num
        <;>
        aesop
      })
  
  have h₂ : ¬Irreducible ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ p) := by
    have h₃ : ¬Irreducible ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) : R[X]) ^ p := by
      intro h
      have h₄ : Irreducible ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) : R[X]) ^ p := h
      have h₅ : (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ p = (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) * (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (p - 1) := by
        have h₅₁ : p ≥ 2 := by
          have h₅₂ : Nat.Prime p := ⟨p, by exact Fact.out (inst✝² : Fact (Nat.Prime p))⟩
          exact Nat.Prime.two_le h₅₂
        have h₅₂ : (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ p = (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (2 + (p - 2)) := by
          have h₅₃ : p = 2 + (p - 2) := by
            have h₅₄ : p ≥ 2 := h₅₁
            omega
          rw [h₅₃]
          <;> simp [pow_add, pow_two, mul_comm]
          <;> ring_nf
          <;> simp_all [mul_assoc]
          <;> linarith
        rw [h₅₂]
        have h₅₃ : (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (2 + (p - 2)) = ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ 2) * (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (p - 2) := by
          rw [pow_add]
          <;> ring_nf
        rw [h₅₃]
        have h₅₄ : ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ 2) * (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (p - 2) = (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) * ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) * (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (p - 2)) := by
          ring_nf
        rw [h₅₄]
        have h₅₅ : (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) * ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) * (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (p - 2)) = (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) * (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (1 + (p - 2)) := by
          ring_nf
        rw [h₅₅]
        have h₅₆ : (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) * (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (1 + (p - 2)) = (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) * (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) ^ (p - 1) := by
          have h₅₇ : 1 + (p - 2) = p - 1 := by
            have h₅₈ : p ≥ 2 := h₅₁
            omega
          rw [h₅₇]
          <;> ring_nf
        rw [h₅₆]
        <;> simp [mul_assoc]
      rw [h₅] at h₄
      have h₆ : ¬IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ∨ (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) = 0 := by
        by_contra! h₆
        have h₇ : IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) := by tauto
        have h₈ : (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ≠ 0 := by tauto
        have h₉ : IsUnit ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ p) := by
          exact IsUnit.pow h₇ p
        have h₁₀ : ¬IsUnit ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ p) := by
          intro h₁₀
          have h₁₁ : Irreducible ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ p) := h₄
          exact h₁₁.not_isUnit h₁₀
        exact h₁₀ h₉
      cases h₆ with
      | inl h₆ =>
        -- Case: (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) is not a unit
        have h₇ : ¬IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) := h₆
        have h₈ : ¬IsUnit ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ (p - 1)) := by
          intro h₈
          have h₉ : IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) := by
            have h₁₀ : IsUnit ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ (p - 1)) := h₈
            have h₁₁ : p - 1 ≥ 1 := by
              have h₁₂ : Nat.Prime p := ⟨p, by exact Fact.out (inst✝² : Fact (Nat.Prime p))⟩
              have h₁₃ : p ≥ 2 := Nat.Prime.two_le h₁₂
              omega
            have h₁₂ : IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) := by
              -- If (p-1)-th power is a unit, then the base is a unit
              have h₁₃ : IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) := by
                apply IsUnit.of_pow_dvd_one (p - 1)
                <;>
                (try simp_all [Nat.pow_succ, Nat.mul_sub_left_distrib]) <;>
                (try ring_nf at * <;> simp_all) <;>
                (try omega) <;>
                (try
                  {
                    have h₁₄ : p ≥ 2 := by
                      have h₁₅ : Nat.Prime p := ⟨p, by exact Fact.out (inst✝² : Fact (Nat.Prime p))⟩
                      exact Nat.Prime.two_le h₁₅
                    omega
                  })
                <;>
                (try
                  {
                    use (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ (p - 2) * h₁₀
                    <;>
                    (try simp_all [Nat.pow_succ, Nat.mul_sub_left_distrib, mul_assoc]) <;>
                    (try ring_nf at * <;> simp_all) <;>
                    (try omega)
                  })
              exact h₁₃
            exact h₁₂
          exact h₇ h₉
        have h₉ : ¬IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) := h₇
        have h₁₀ : ¬IsUnit ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ (p - 1)) := h₈
        have h₁₁ : ¬IsUnit ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) * ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ (p - 1))) := by
          intro h₁₁
          have h₁₂ : IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ∨ IsUnit ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ (p - 1)) := by
            apply Or.isUnit_mul
            exact h₁₁
          cases h₁₂ with
          | inl h₁₂ =>
            exact h₉ h₁₂
          | inr h₁₂ =>
            exact h₁₀ h₁₂
        have h₁₂ : (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) * ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ (p - 1)) = (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) ^ p := by
          ring_nf
          <;>
          (try simp_all [Nat.pow_succ, Nat.mul_sub_left_distrib]) <;>
          (try ring_nf at * <;> simp_all) <;>
          (try omega)
        rw [h₁₂] at h₁₁
        exact h₁₁
      | inr h₆ =>
        -- Case: (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) = 0
        have h₇ : (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) = 0 := h₆
        have h₈ : ((map (↑(RingEquiv.symm (frobeniusEquiv R p))) f : R[X]) : R[X]) ^ p = 0 := by
          rw [h₇]
          simp
        rw [h₈] at h₄
        exact Irreducible.not_zero _ h₄
    exact h₃
  
  have h₃ : ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p) := by
    rw [h₁]
    exact h₂
  
  exact h₃
```

**lean_error:** tail step 1/139 ('theorem your_theorem_name : ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p) := by'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 13.2s, verify 0.3s, in=350, out=1319)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro h
have hp : p ≥ 2 := Nat.Prime.two_le (Fact.out (p := Nat.Prime p))
let g := map (↑(RingEquiv.symm (frobeniusEquiv R p))) f
have : g ^ p = g * g ^ (p - 1) := by
  rw [← pow_succ, Nat.succ_pred_eq_of_pos (Nat.pos_of_ne_zero (Nat.Prime.ne_zero (Fact.out (p := Nat.Prime p))))]
exact h.not_irreducible_pow (by
  refine' ⟨g, p - 1, _⟩
  simp [hp])
```

**lean_error:** tail step 3/8 ('let g := map (↑(RingEquiv.symm (frobeniusEquiv R p))) f'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=856, out=418)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out _))
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out _))'): function expected at

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 26.4s, verify 0.1s, in=831, out=2889)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_p_ne_one : p ≠ 1 := by
  have h_p_prime : Nat.Prime p := Fact.out inst✝²
  exact Nat.Prime.ne_one h_p_prime

have h_not_irr : ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p) := by
  apply not_irreducible_pow
  <;> assumption
  <;> exact h_p_ne_one

exact h_not_irr
```

**lean_error:** tail step 1/8 ('have h_p_ne_one : p ≠ 1 := by'): <stdin>:1:29: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=783, out=585)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out inst✝²))
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out inst✝²))'): <stdin>:1:58: expected token

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.2s, in=1606, out=669)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply not_irreducible_pow
exact (Nat.Prime.ne_one (Fact.out _))
```

**lean_error:** tail step 2/2 ('exact (Nat.Prime.ne_one (Fact.out _))'): function expected at

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 25.4s, verify 0.1s, in=1597, out=2765)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hp : Nat.Prime p := inst✝².out
have hne : p ≠ 1 := Nat.Prime.ne_one hp
exact not_irreducible_pow (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) p hne
```

**lean_error:** tail step 1/3 ('have hp : Nat.Prime p := inst✝².out'): <stdin>:1:29: expected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.2s, in=1511, out=463)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply not_irreducible_pow
exact Nat.Prime.ne_one (Fact.out inst✝²)
```

**lean_error:** tail step 2/2 ('exact Nat.Prime.ne_one (Fact.out inst✝²)'): <stdin>:1:37: expected token

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.2s, in=1518, out=635)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply not_irreducible_pow
exact (Nat.Prime.ne_one (Fact.out _))
```

**lean_error:** tail step 2/2 ('exact (Nat.Prime.ne_one (Fact.out _))'): function expected at

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 32.7s, verify 0.1s, in=1689, out=3661)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h_p_ne_one : p ≠ 1 := by
  have h : Nat.Prime p := Fact.out inst✝²
  exact Nat.Prime.ne_one h
exact not_irreducible_pow (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f) h_p_ne_one
```

**lean_error:** tail step 1/4 ('have h_p_ne_one : p ≠ 1 := by'): <stdin>:1:29: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.2s, in=1517, out=487)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply not_irreducible_pow
exact Nat.Prime.ne_one (Fact.out inst✝²)
```

**lean_error:** tail step 2/2 ('exact Nat.Prime.ne_one (Fact.out inst✝²)'): <stdin>:1:37: expected token
