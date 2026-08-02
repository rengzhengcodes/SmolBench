# Polynomial.roots_expand_image_iterateFrobenius   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
rw [Finset.image_toFinset, roots_expand_pow_map_iterateFrobenius,
  (roots f).toFinset_nsmul _ (expChar_pow_pos R p n).ne']
```

**True premises at k:** `Finset.image_toFinset`, `Polynomial.roots_expand_pow_map_iterateFrobenius`, `Polynomial.roots`, `Multiset.toFinset_nsmul`, `expChar_pow_pos`, `LT.lt.ne'`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.1s, in=376, out=1060)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (roots_expand_eq_image_iterateFrobenius (R:=R) (p:=p) (n:=n) (f:=f))
```

**lean_error:** tail step 1/1 ('simpa using (roots_expand_eq_image_iterateFrobenius (R:=R) (p:=p) (n:=n) (f:=f))'): unknown identifier 'roots_expand_eq_image_iterateFrobenius'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 154.5s, verify 0.1s, in=333, out=19416)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem problem {R : Type u_1} [CommRing R] [IsDomain R] {p n : ℕ} [ExpChar R p] [PerfectRing R p] (f : R[X]) :
    Finset.image (⇑(iterateFrobenius R p n)) (toFinset (roots ((expand R (p ^ n)) f))) = toFinset (roots f) := by
  have h_eval_expand : ∀ (n : ℕ) (f : R[X]) (x : R), eval (expand n f) x = eval f (x ^ n) := by
    intro n f x
    rw [polynomial.expand_eq_comp_X_pow]
    simp [polynomial.eval_comp, polynomial.eval_X_pow]
    <;> ring_nf
  
  have h_surjective : Function.Surjective (⇑(iterateFrobenius R p n)) := by
    have h₁ : ⇑(iterateFrobenius R p n) = (fun x : R => x ^ (p ^ n)) := by
      funext x
      rw [iterateFrobenius_apply]
    rw [h₁]
    have h₂ : Function.Surjective (fun x : R => x ^ (p ^ n)) := by
      have h₃ : Function.Surjective (fun x : R => x ^ p) := by
        have h₄ : Function.Surjective (⇑(FrobeniusEndomorphism R p)) := PerfectRing R p.surjective
        have h₅ : ⇑(FrobeniusEndomorphism R p) = (fun x : R => x ^ p) := by
          funext x
          simp [FrobeniusEndomorphism.map_pow]
          <;> rfl
        rw [h₅] at h₄
        exact h₄
      -- Now, the n-th iterate of a surjective function is surjective
      have h₆ : Function.Surjective (Function.iterate (fun x : R => x ^ p) n) :=
        Function.iterate_surjective h₃ n
      -- Show that Function.iterate (fun x => x ^ p) n = (fun x => x ^ (p ^ n))
      have h₇ : Function.iterate (fun x : R => x ^ p) n = (fun x : R => x ^ (p ^ n)) := by
        have h₈ : ∀ n : ℕ, Function.iterate (fun x : R => x ^ p) n = (fun x : R => x ^ (p ^ n)) := by
          intro n
          induction n with
          | zero =>
            funext x
            simp [Function.iterate_zero]
            <;> simp [Nat.pow_zero]
          | succ n ih =>
            funext x
            simp_all [Function.iterate_succ_apply', pow_succ, mul_pow]
            <;> ring_nf at *
            <;> simp_all
        exact h₈ n
      rw [h₇] at h₆
      exact h₆
    exact h₂
  
  have h_subset₁ : Finset.image (⇑(iterateFrobenius R p n)) (toFinset (roots ((expand R (p ^ n)) f))) ⊆ toFinset (roots f) := by
    intro y hy
    rcases hy with ⟨x, hx, rfl⟩
    have hx' : x ∈ toFinset (roots ((expand R (p ^ n)) f)) := hx
    have hxy : y = ⇑(iterateFrobenius R p n) x := rfl
    have hx_root : x ∈ roots ((expand R (p ^ n)) f) := by
      simpa [toFinset] using hx'
    have h_eval_expand_zero : eval ((expand R (p ^ n)) f) x = 0 := by
      simpa [roots_iff] using hx_root
    have h_eval_expand : eval ((expand R (p ^ n)) f) x = eval f (x ^ (p ^ n)) := by
      have h₁ := h_eval_expand (p ^ n) f x
      exact h₁
    have h_eval_f_zero : eval f (x ^ (p ^ n)) = 0 := by
      linarith
    have h_pow : x ^ (p ^ n) = y := by
      have h₂ : y = ⇑(iterateFrobenius R p n) x := hxy
      rw [h₂]
      have h₃ := iterateFrobenius_apply
      rw [h₃]
    have h_eval_f_y_zero : eval f y = 0 := by
      rw [h_pow] at h_eval_f_zero
      exact h_eval_f_zero
    have hy_root : y ∈ roots f := by
      simpa [roots_iff] using h_eval_f_y_zero
    exact toFinset_mem_roots.mpr hy_root
  
  have h_subset₂ : toFinset (roots f) ⊆ Finset.image (⇑(iterateFrobenius R p n)) (toFinset (roots ((expand R (p ^ n)) f))) := by
    intro y hy
    have hy_root : y ∈ roots f := by
      simpa [toFinset] using hy
    have h_eval_f_y_zero : eval f y = 0 := by
      simpa [roots_iff] using hy_root
    have h_surj : Function.Surjective (⇑(iterateFrobenius R p n)) := h_surjective
    obtain ⟨x, hx⟩ := h_surj y
    have hxy : ⇑(iterateFrobenius R p n) x = y := hx
    have hx_root : x ∈ roots ((expand R (p ^ n)) f) := by
      have h_eval_expand : eval ((expand R (p ^ n)) f) x = eval f (x ^ (p ^ n)) := by
        have h₁ := h_eval_expand (p ^ n) f x
        exact h₁
      have h_eval_expand_zero : eval ((expand R (p ^ n)) f) x = 0 := by
        have h₂ : eval f (x ^ (p ^ n)) = eval f y := by
          rw [hxy]
        rw [h_eval_expand]
        rw [h₂]
        exact h_eval_f_y_zero
      have hx_root' : x ∈ roots ((expand R (p ^ n)) f) := by
        rw [roots_iff]
        exact h_eval_expand_zero
      exact hx_root'
    have hx_in : x ∈ toFinset (roots ((expand R (p ^ n)) f)) := by
      simpa [toFinset] using hx_root
    refine' ⟨x, hx_in, _⟩
    <;> simp_all [hxy]
    <;> aesop
  
  have h_main : Finset.image (⇑(iterateFrobenius R p n)) (toFinset (roots ((expand R (p ^ n)) f))) = toFinset (roots f) := by
    apply Finset.subset_antisymm
    · -- Prove the first subset
      exact h_subset₁
    · -- Prove the second subset
      exact h_subset₂
  
  exact h_main
```

**lean_error:** tail step 1/102 ('theorem problem {R : Type u_1} [CommRing R] [IsDomain R] {p n : ℕ} [ExpChar R p] [PerfectRing R p] (f : R[X]) :'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.3s, verify 0.2s, in=323, out=690)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp only [Finset.mem_image, toFinset_coe, Set.mem_toFinset]
constructor
· rintro ⟨y, hy, rfl⟩
  exact (mem_roots_expand_iff R p n f).mp hy
· intro hx
  refine' ⟨iterateFrobenius R p n x, _, _⟩
  · exact (mem_roots_expand_iff R p n f).mpr hx
  · simp [iterateFrobenius_apply, PerfectRing.frobenius_inv]
```

**lean_error:** tail step 2/9 ('simp only [Finset.mem_image, toFinset_coe, Set.mem_toFinset]'): unknown identifier 'toFinset_coe'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.1s, verify 1.2s, in=1469, out=2427)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
by
  have hne : (p ^ n) ≠ 0 := by
    apply ne_of_gt
    exact expChar_pow_pos (R:=R) (q:=p) n
  simpa [image_toFinset,
        roots_expand_pow_map_iterateFrobenius,
        Multiset.toFinset_nsmul (s:=f.roots) (n:=p ^ n) hne]
```

**lean_error:** tail step 1/7 ('by'): <stdin>:1:0: expected tactic

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 36.7s, verify 0.3s, in=1504, out=4471)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_pow_map_iterateFrobenius]
have h : p ^ n ≠ 0 := by
  have h₁ : 0 < p ^ n := expChar_pow_pos p n inst✝²
  exact Nat.pos_iff_ne_zero.mpr h₁
rw [Multiset.toFinset_nsmul f.roots h]
<;> rfl
```

**lean_error:** tail step 3/7 ('have h : p ^ n ≠ 0 := by'): <stdin>:1:24: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.4s, in=1431, out=681)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_pow_map_iterateFrobenius]
rw [Multiset.toFinset_nsmul]
· exact LT.lt.ne' (expChar_pow_pos p n)
```

**lean_error:** tail step 4/4 ("· exact LT.lt.ne' (expChar_pow_pos p n)"): application type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.1s, verify 0.1s, in=4997, out=1649)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
classical
  have hne : (p ^ n) ≠ 0 := by
    have hpos : (0 : ℕ) < p ^ n := expChar_pow_pos (R:=R) p n
    exact Nat.ne_of_gt hpos
  simpa [Finset.image_toFinset,
        roots_expand_pow_map_iterateFrobenius,
        Multiset.toFinset_nsmul (s:=f.roots) (n:=p ^ n) hne]
```

**lean_error:** tail step 1/7 ('classical'): <stdin>:1:9: unexpected end of input; expected '{'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 34.9s, verify 0.3s, in=5155, out=4282)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_pow_map_iterateFrobenius]
have h : p ^ n ≠ 0 := by
  have h₁ : 0 < p ^ n := expChar_pow_pos p n
  exact LT.lt.ne' h₁
rw [Multiset.toFinset_nsmul f.roots (p ^ n) h]
<;> rfl
```

**lean_error:** tail step 3/7 ('have h : p ^ n ≠ 0 := by'): <stdin>:1:24: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.1s, verify 0.4s, in=4926, out=836)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_pow_map_iterateFrobenius]
rw [Multiset.toFinset_nsmul]
· exact (expChar_pow_pos p n).ne'
```

**lean_error:** tail step 4/4 ("· exact (expChar_pow_pos p n).ne'"): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.8s, verify 0.1s, in=4547, out=2071)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hne : (p ^ n) ≠ 0 := by
    have hpos := expChar_pow_pos (R:=R) (q:=p) n
    exact (Nat.ne_of_gt hpos)
  simpa [Finset.image_toFinset,
    roots_expand_pow_map_iterateFrobenius,
    Multiset.toFinset_nsmul (f.roots) (p ^ n) hne]
```

**lean_error:** tail step 1/6 ('have hne : (p ^ n) ≠ 0 := by'): <stdin>:1:28: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 18.3s, verify 0.3s, in=5530, out=1986)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_pow_map_iterateFrobenius]
have h : p ^ n ≠ 0 := LT.lt.ne' (expChar_pow_pos p n)
rw [Multiset.toFinset_nsmul f.roots h]
```

**lean_error:** tail step 3/4 ("have h : p ^ n ≠ 0 := LT.lt.ne' (expChar_pow_pos p n)"): application type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.4s, in=4861, out=693)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_pow_map_iterateFrobenius]
rw [Multiset.toFinset_nsmul]
· exact (LT.lt.ne' (expChar_pow_pos p n)).symm
```

**lean_error:** tail step 4/4 ("· exact (LT.lt.ne' (expChar_pow_pos p n)).symm"): application type mismatch
