# Polynomial.roots_expand_image_frobenius   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
rw [Finset.image_toFinset, roots_expand_map_frobenius,
    (roots f).toFinset_nsmul _ (expChar_pos R p).ne']
```

**True premises at k:** `Finset.image_toFinset`, `Polynomial.roots_expand_map_frobenius`, `Polynomial.roots`, `Multiset.toFinset_nsmul`, `expChar_pos`, `LT.lt.ne'`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 24.5s, verify 0.1s, in=364, out=5299)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (roots_expand_eq_image_frobenius (R:=R) (p:=p) (f:=f))
```

**lean_error:** tail step 1/1 ('simpa using (roots_expand_eq_image_frobenius (R:=R) (p:=p) (f:=f))'): unknown identifier 'roots_expand_eq_image_frobenius'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 128.4s, verify 0.1s, in=323, out=16877)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h_expand_apply : ∀ (y : R), (⇑(expand R p) f) y = f (y ^ p) := by
  intro y
  rw [Polynomial.expand_apply]
  <;> simp [pow_mul]
  <;> ring_nf

have h_frobenius_apply : ∀ (y : R), ⇑(frobenius R p) y = y ^ p := by
  intro y
  rw [frobenius_apply]

have h_main : ∀ (y : R), (⇑(expand R p) f) y = f (⇑(frobenius R p) y) := by
  intro y
  rw [h_expand_apply y]
  rw [h_frobenius_apply y]
  <;> simp [pow_mul]
  <;> ring_nf

have h_roots_expand : ∀ (y : R), y ∈ roots ((expand R p) f) ↔ ⇑(frobenius R p) y ∈ roots f := by
  intro y
  constructor
  · intro h
    have h₁ : (⇑(expand R p) f) y = 0 := by
      have h₂ : y ∈ roots ((expand R p) f) := h
      rw [Polynomial.roots_mem_iff] at h₂
      exact h₂
    have h₂ : f (⇑(frobenius R p) y) = 0 := by
      have h₃ : (⇑(expand R p) f) y = f (⇑(frobenius R p) y) := h_main y
      linarith
    have h₃ : ⇑(frobenius R p) y ∈ roots f := by
      rw [Polynomial.roots_mem_iff]
      exact h₂
    exact h₃
  · intro h
    have h₁ : f (⇑(frobenius R p) y) = 0 := by
      have h₂ : ⇑(frobenius R p) y ∈ roots f := h
      rw [Polynomial.roots_mem_iff] at h₂
      exact h₂
    have h₂ : (⇑(expand R p) f) y = 0 := by
      have h₃ : (⇑(expand R p) f) y = f (⇑(frobenius R p) y) := h_main y
      linarith
    have h₃ : y ∈ roots ((expand R p) f) := by
      rw [Polynomial.roots_mem_iff]
      exact h₂
    exact h₃

have h_image : Finset.image (⇑(frobenius R p)) (toFinset (roots ((expand R p) f))) = toFinset (roots f) := by
  apply Finset.ext
  intro x
  have h₁ : x ∈ Finset.image (⇑(frobenius R p)) (toFinset (roots ((expand R p) f))) ↔ ∃ y ∈ toFinset (roots ((expand R p) f)), ⇑(frobenius R p) y = x := by
    simp [Finset.mem_image]
  rw [h₁]
  constructor
  · intro h
    obtain ⟨y, hy, hxy⟩ := h
    have h₂ : y ∈ toFinset (roots ((expand R p) f)) := hy
    have h₃ : ⇑(frobenius R p) y = x := hxy
    have h₄ : y ∈ roots ((expand R p) f) := by
      simp only [Finset.mem_toFinset] at h₂
      exact h₂
    have h₅ : ⇑(frobenius R p) y ∈ roots f := by
      have h₆ : y ∈ roots ((expand R p) f) := h₄
      exact h_roots_expand y h₆
    have h₆ : f (⇑(frobenius R p) y) = 0 := by
      rw [Polynomial.roots_mem_iff] at h₅
      exact h₅
    have h₇ : f x = 0 := by
      rw [h₃] at h₆
      exact h₆
    have h₈ : x ∈ roots f := by
      rw [Polynomial.roots_mem_iff]
      exact h₇
    have h₉ : x ∈ toFinset (roots f) := by
      simp only [Finset.mem_toFinset]
      exact h₈
    exact h₉
  · intro h
    have h₂ : x ∈ toFinset (roots f) := h
    have h₃ : x ∈ roots f := by
      simp only [Finset.mem_toFinset] at h₂
      exact h₂
    have h₄ : f x = 0 := by
      rw [Polynomial.roots_mem_iff] at h₃
      exact h₃
    have h₅ : Function.Surjective (⇑(frobenius R p)) := PerfectRing.frobenius_surjective inst✝¹
    obtain ⟨y, hy⟩ := h₅ x
    have h₆ : ⇑(frobenius R p) y = x := hy
    have h₇ : f (⇑(frobenius R p) y) = 0 := by
      rw [h₆]
      exact h₄
    have h₈ : ⇑(frobenius R p) y ∈ roots f := by
      rw [Polynomial.roots_mem_iff]
      exact h₇
    have h₉ : y ∈ roots ((expand R p) f) := by
      have h₁₀ : y ∈ roots ((expand R p) f) ↔ ⇑(frobenius R p) y ∈ roots f := h_roots_expand y
      exact (h₁₀).mp h₈
    have h₁₀ : y ∈ toFinset (roots ((expand R p) f)) := by
      simp only [Finset.mem_toFinset]
      exact h₉
    refine' ⟨y, h₁₀, _⟩
    <;> simp_all

exact h_image

</think>
```

**lean_error:** tail step 1/98 ('have h_expand_apply : ∀ (y : R), (⇑(expand R p) f) y = f (y ^ p) := by'): <stdin>:1:70: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 10.1s, verify 0.2s, in=311, out=794)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp [Finset.mem_image, toFinset_coe, mem_roots]
constructor
· rintro ⟨y, hy, rfl⟩
  exact (mem_roots_expand_iff R p f).mp hy
· intro hx
  have : ∃ y, frobenius R p y = x := (frobenius_surjective R p) x
  obtain ⟨y, hy⟩ := this
  refine' ⟨y, _, hy⟩
  rw [← hy]
  exact (mem_roots_expand_iff R p f).mpr hx
```

**lean_error:** tail step 2/11 ('simp [Finset.mem_image, toFinset_coe, mem_roots]'): unknown identifier 'toFinset_coe'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.2s, verify 0.1s, in=1394, out=1598)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hp : p ≠ 0 := by
    exact ne_of_gt (expChar_pos R p)
  simpa [Finset.image_toFinset, roots_expand_map_frobenius,
    Multiset.toFinset_nsmul (s:=f.roots) (n:=p) hp]
```

**lean_error:** tail step 1/4 ('have hp : p ≠ 0 := by'): <stdin>:1:21: unexpected end of input; expected '{'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 37.8s, verify 0.3s, in=1419, out=4293)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_map_frobenius]
have h : 0 < p := expChar_pos
have h' : p ≠ 0 := by
  intro h
  have h'' : 0 < p := h
  linarith
rw [Multiset.toFinset_nsmul f.roots p h']
<;> rfl
```

**lean_error:** tail step 3/9 ('have h : 0 < p := expChar_pos'): type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.6s, verify 0.4s, in=1353, out=738)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_map_frobenius]
rw [Multiset.toFinset_nsmul]
· exact LT.lt.ne' (expChar_pos p)
```

**lean_error:** tail step 4/4 ("· exact LT.lt.ne' (expChar_pos p)"): application type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.1s, in=4582, out=1850)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hp : (p : ℕ) ≠ 0 := by
    have hpos : 0 < p := expChar_pos (R:=R) p
    exact Nat.ne_of_gt hpos
  simpa [Finset.image_toFinset, roots_expand_map_frobenius,
        Multiset.toFinset_nsmul (f.roots) p hp]
```

**lean_error:** tail step 1/5 ('have hp : (p : ℕ) ≠ 0 := by'): <stdin>:1:27: unexpected end of input; expected '{'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 29.8s, verify 0.3s, in=4713, out=3357)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [Polynomial.roots_expand_map_frobenius]
have h_ne_zero : p ≠ 0 := by
  have h₁ : 0 < p := expChar_pos R p
  intro h
  linarith
rw [Multiset.toFinset_nsmul f.roots p h_ne_zero]
<;> rfl
```

**lean_error:** tail step 3/8 ('have h_ne_zero : p ≠ 0 := by'): <stdin>:1:28: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.4s, in=4499, out=530)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset]
rw [roots_expand_map_frobenius]
rw [Multiset.toFinset_nsmul]
· exact (expChar_pos p).ne'
· exact LT.lt.ne' (expChar_pos p)
```

**lean_error:** tail step 4/5 ("· exact (expChar_pos p).ne'"): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.0s, verify 0.1s, in=4174, out=1961)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hpos : p ≠ 0 := by
    have hpos' := expChar_pos (R:=R) p
    exact Nat.ne_of_gt hpos'
  simpa [Finset.image_toFinset, roots_expand_map_frobenius,
    Multiset.toFinset_nsmul (s:=f.roots) (n:=p) hpos]
```

**lean_error:** tail step 1/5 ('have hpos : p ≠ 0 := by'): <stdin>:1:23: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 21.5s, verify 0.1s, in=5056, out=2397)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  Finset.image (⇑(frobenius R p)) (toFinset (roots ((expand R p) f))) = ( (roots ((expand R p) f)).map (⇑(frobenius R p)) ).toFinset := by
    apply Finset.image_toFinset
  _ = (p • f.roots).toFinset := by
    rw [Polynomial.roots_expand_map_frobenius]
  _ = f.roots.toFinset := by
    have h : p ≠ 0 := by
      have h₁ : 0 < p := expChar_pos p
      exact lt_ne_iff.mp h₁
    rw [Multiset.toFinset_nsmul h]
```

**lean_error:** tail step 1/10 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 13.4s, verify 0.3s, in=4448, out=1177)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Finset.image_toFinset, Polynomial.roots_expand_map_frobenius]
rw [Multiset.toFinset_nsmul]
· exact LT.lt.ne' (expChar_pos p)
```

**lean_error:** tail step 3/3 ("· exact LT.lt.ne' (expChar_pos p)"): application type mismatch
