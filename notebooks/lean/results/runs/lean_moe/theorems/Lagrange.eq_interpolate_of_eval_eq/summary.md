# Lagrange.eq_interpolate_of_eval_eq   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Lagrange.lean`  

**Ground-truth tail (from k):**
```lean
exact interpolate_eq_of_values_eq_on _ _ eval_f
```

**True premises at k:** `Lagrange.interpolate_eq_of_values_eq_on`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.5s, verify 0.1s, in=383, out=2130)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h1 : (interpolate s v) (fun i => eval (v i) f) = f := by
  apply interpolate_eq_of_eq_on (s:=s) (v:=v) (r:=fun i => eval (v i) f) (f:=f) hvs degree_f_lt
  intro i hi
  rfl
have h2 : (interpolate s v) r = f := by
  apply interpolate_eq_of_eq_on (s:=s) (v:=v) (r:=r) (f:=f) hvs degree_f_lt
  intro i hi
  exact eval_f i hi
calc
  (interpolate s v) (fun i => eval (v i) f) = f := h1
  _ = (interpolate s v) r := by
    symm
    exact h2
```

**lean_error:** tail step 1/13 ('have h1 : (interpolate s v) (fun i => eval (v i) f) = f := by'): <stdin>:1:61: unexpected end of input; expected '{'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 48.8s, verify 0.1s, in=330, out=5148)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem interpolate_s_v_fun_eq_interpolate_s_v_r :
    ((interpolate s v) fun i => eval (v i) f) = (interpolate s v) r := by
  have h_f_eq_interpolate_fun : f = (interpolate s v) (fun i => eval (v i) f) := by
    have h₁ : degree f < s.card := degree_f_lt
    have h₂ : ∀ i ∈ s, f.eval (v i) = (fun i => eval (v i) f) i := by
      intro i hi
      have h₃ : f.eval (v i) = eval (v i) f := by
        simp [eval₂_eq_eval]
      rw [h₃]
      <;> simp [hi]
      <;>
      (try aesop) <;>
      (try simp_all) <;>
      (try ring_nf) <;>
      (try norm_num) <;>
      (try linarith)
    have h₃ : f = (interpolate s v) (fun i => eval (v i) f) := by
      apply Polynomial.eq_interpolate
      <;> simp_all [h₁, h₂]
      <;>
      (try aesop) <;>
      (try simp_all) <;>
      (try ring_nf) <;>
      (try norm_num) <;>
      (try linarith)
    exact h₃
  
  have h_f_eq_interpolate_r : f = (interpolate s v) r := by
    have h₁ : degree f < s.card := degree_f_lt
    have h₂ : ∀ i ∈ s, f.eval (v i) = r i := by
      intro i hi
      have h₃ : f.eval (v i) = eval (v i) f := by
        simp [eval₂_eq_eval]
      rw [h₃]
      have h₄ : eval (v i) f = r i := eval_f i hi
      rw [h₄]
    have h₃ : f = (interpolate s v) r := by
      apply Polynomial.eq_interpolate
      <;> simp_all [h₁, h₂]
      <;>
      (try aesop) <;>
      (try simp_all) <;>
      (try ring_nf) <;>
      (try norm_num) <;>
      (try linarith)
    exact h₃
  
  have h_main : ((interpolate s v) fun i => eval (v i) f) = (interpolate s v) r := by
    rw [h_f_eq_interpolate_fun.symm]
    rw [h_f_eq_interpolate_r]
    <;>
    (try aesop) <;>
    (try simp_all) <;>
    (try ring_nf) <;>
    (try norm_num) <;>
    (try linarith)
  
  exact h_main
```

**lean_error:** tail step 1/55 ('theorem interpolate_s_v_fun_eq_interpolate_s_v_r :'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.2s, verify 0.1s, in=323, out=448)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply interpolate_congr hvs
intro i hi
exact eval_f i hi
```

**lean_error:** tail step 1/3 ('apply interpolate_congr hvs'): unknown identifier 'interpolate_congr'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 24.5s, verify 0.1s, in=627, out=2507)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← interpolate_eq_of_values_eq_on (by
  intro i hi
  simpa using (eval_f i hi).symm)]
rw [eq_interpolate hvs degree_f_lt]
rfl
```

**lean_error:** tail step 1/5 ('rw [← interpolate_eq_of_values_eq_on (by'): <stdin>:1:40: unexpected end of input; expected '{'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 64.4s, verify 0.2s, in=585, out=6809)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Lagrange.interpolate_eq_of_values_eq_on
<;> assumption
```

**lean_error:** tail step 2/2 ('<;> assumption'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 9.3s, verify 0.2s, in=570, out=459)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
exact eval_f
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.1s, verify 0.6s, in=1686, out=1601)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
symm
rw [← eq_interpolate hvs degree_f_lt]
apply interpolate_eq_of_values_eq_on (s:=s) (v:=v) (r:=r) (r':=fun i => eval (v i) f)
intro i hi
symm
exact eval_f i hi
```

**lean_error:** tail step 3/6 ("apply interpolate_eq_of_values_eq_on (s:=s) (v:=v) (r:=r) (r':=fun i => eval (v i) f)"): tactic 'apply' failed, failed to unify

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 75.7s, verify 0.1s, in=1657, out=7980)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
Lagrange.eq_interpolate_of_eval_eq
  (hvs : Set.InjOn v ↑s)
  (degree_f_lt : degree f < ↑s.card)
  (eval_f : ∀ i ∈ s, eval (v i) f = r i)
  : ((interpolate s v) fun i => eval (v i) f) = (interpolate s v) r := by
  have h_main : (interpolate s v) r = (interpolate s v) (fun i => eval (v i) f) := by
    apply Lagrange.interpolate_eq_of_values_eq_on
    intro i hi
    exact eval_f i hi
  
  have h_final : ((interpolate s v) fun i => eval (v i) f) = (interpolate s v) r := by
    rw [h_main.symm]
  
  exact h_final
```

**lean_error:** tail step 1/12 ('Lagrange.eq_interpolate_of_eval_eq'): <stdin>:1:1: unknown tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 11.6s, verify 1.6s, in=1584, out=655)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
intro i hi
exact eval_f i hi
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.7s, verify 0.3s, in=1556, out=1703)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← eq_interpolate hvs degree_f_lt]
apply interpolate_eq_of_values_eq_on
intro i hi
exact (eval_f i hi).symm
```

**lean_error:** tail step 2/4 ('apply interpolate_eq_of_values_eq_on'): tactic 'apply' failed, failed to unify

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 173.9s, verify 0.1s, in=1794, out=19036)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h_poly_eq_zero : f - (interpolate s v) r = 0 := by
  by_contra h
  have h₁ : (f - (interpolate s v) r) ≠ 0 := h
  have h₂ : (f - (interpolate s v) r).num_roots ≤ (f - (interpolate s v) r).natDegree := by
    apply polynomial.num_roots_le_degree
    exact h₁
  have h₃ : (f - (interpolate s v) r).natDegree = (f - (interpolate s v) r).degree := by
    rw [polynomial.natDegree_eq_iff_degree_eq] <;>
      (try simp_all) <;>
      (try aesop) <;>
      (try
        {
          intro h₃
          apply h₁
          simp_all [h₃]
        })
    <;>
    aesop
  have h₄ : (f - (interpolate s v) r).degree < s.card := by
    have h₄₁ : degree f < s.card := degree_f_lt
    have h₄₂ : degree (interpolate s v r) < s.card := degree_interpolate hvs
    have h₄₃ : degree (f - (interpolate s v) r) ≤ max (degree f) (degree (interpolate s v r)) := by
      apply degree_sub_le
    have h₄₄ : max (degree f) (degree (interpolate s v r)) < s.card := by
      have h₄₄₁ : degree f < s.card := h₄₁
      have h₄₄₂ : degree (interpolate s v r) < s.card := h₄₂
      exact lt_max h₄₄₁ h₄₄₂
    linarith
  have h₅ : (f - (interpolate s v) r).natDegree < s.card := by
    rw [h₃] at *
    exact h₄
  have h₆ : ({v i | i ∈ s} : Finset F).card = s.card := by
    have h₆₁ : Set.InjOn v ↑s := hvs
    have h₆₂ : ({v i | i ∈ s} : Finset F) = (Finset.image v s) := by
      ext x
      simp [Finset.mem_image]
      <;>
      aesop
    rw [h₆₂]
    rw [Finset.card_image_of_injOn hvs]
  have h₇ : ∀ i ∈ s, IsRoot (f - (interpolate s v) r) (v i) := by
    intro i hi
    have h₇₁ : eval (v i) (f - (interpolate s v) r) = eval (v i) f - eval (v i) (interpolate s v r) := by
      rw [eval_sub]
    rw [h₇₁]
    have h₇₂ : eval (v i) f = r i := eval_f i hi
    have h₇₃ : eval (v i) (interpolate s v r) = r i := by
      apply eval_interpolate
      <;> assumption
    rw [h₇₂, h₇₃]
    <;> simp [sub_self]
  have h₈ : ({v i | i ∈ s} : Finset F) ⊆ ((f - (interpolate s v) r).roots : Finset F) := by
    intro x hx
    simp only [Finset.mem_image, Finset.mem_coe, Finset.mem_roots] at hx ⊢
    obtain ⟨i, hi, rfl⟩ := hx
    exact h₇ i hi
  have h₉ : s.card ≤ ((f - (interpolate s v) r).roots : Finset F).card := by
    have h₉₁ : ({v i | i ∈ s} : Finset F).card = s.card := h₆
    have h₉₂ : ({v i | i ∈ s} : Finset F) ⊆ ((f - (interpolate s v) r).roots : Finset F) := h₈
    have h₉₃ : ({v i | i ∈ s} : Finset F).card ≤ ((f - (interpolate s v) r).roots : Finset F).card := Finset.card_le_of_subset h₉₂
    linarith
  have h₁₀ : ((f - (interpolate s v) r).roots : Finset F).card = (f - (interpolate s v) r).num_roots := by
    rw [Finset.card_coe]
  have h₁₁ : s.card ≤ (f - (interpolate s v) r).num_roots := by
    linarith
  have h₁₂ : (f - (interpolate s v) r).num_roots < s.card := by
    linarith
  linarith
rw [sub_eq_zero] at h_poly_eq_zero
exact h_poly_eq_zero
```

**lean_error:** tail step 1/70 ('have h_poly_eq_zero : f - (interpolate s v) r = 0 := by'): <stdin>:1:55: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 8.6s, verify 0.3s, in=1602, out=379)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
exact eval_f
```
