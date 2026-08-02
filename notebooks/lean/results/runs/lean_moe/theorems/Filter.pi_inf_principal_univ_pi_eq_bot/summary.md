# Filter.pi_inf_principal_univ_pi_eq_bot   (k=9, 10 tactics total)

file: `Mathlib/Order/Filter/Pi.lean`  

**Ground-truth tail (from k):**
```lean
filter_upwards [mem_pi_of_mem i hi] with x using mt fun h => h i trivial
```

**True premises at k:** `Filter.mem_pi_of_mem`, `mt`, `trivial`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 30.1s, verify 0.1s, in=349, out=7904)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Filter.mem_pi.2 ⟨i, hi⟩
```

**lean_error:** tail step 1/1 ('exact Filter.mem_pi.2 ⟨i, hi⟩'): application type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 223.1s, verify 0.1s, in=285, out=25527)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have hA : {x : ι → α i | x i ∈ (s i)ᶜ} ∈ comap (fun x : ι → α i => x i) (f i) := by
  have h₁ : (s i)ᶜ ∈ f i := hi
  have h₂ : {x : ι → α i | x i ∈ (s i)ᶜ} = (fun x : ι → α i => x i) ⁻¹' (s i)ᶜ := by
    ext x
    simp [Set.mem_preimage]
    <;>
    aesop
  rw [h₂]
  have h₃ : (fun x : ι → α i => x i) ⁻¹' (s i)ᶜ ∈ comap (fun x : ι → α i => x i) (f i) := by
    refine' ⟨(s i)ᶜ, h₁, _⟩
    <;>
    simp [Set.mem_preimage]
    <;>
    aesop
  exact h₃
have h_le : pi f ≤ comap (fun x : ι → α i => x i) (f i) := by
  have h₁ : pi f = Inf j : ι, comap (fun x : ι → α i => x i) (f j) := rfl
  rw [h₁]
  have h₂ : BoundedBelow (Set.range (fun j : ι => comap (fun x : ι → α i => x i) (f j))) := by
    use ⊥
    intro j _
    exact bot_le
  have h₃ : (Set.range (fun j : ι => comap (fun x : ι => α i => x i) (f j))).Nonempty := by
    exact ⟨i, by simp⟩
  have h₄ : comap (fun x : ι → α i => x i) (f i) ∈ Set.range (fun j : ι => comap (fun x : ι => α i => x i) (f j)) := by
    refine' ⟨i, _⟩
    <;> simp
  have h₅ : csInf (Set.range (fun j : ι => comap (fun x : ι => α i => x i) (f j))) ≤ comap (fun x : ι => α i => x i) (f i) := by
    apply csInf_le h₂ h₃
    exact h₄
  exact h₅
have hA_in_pi : {x : ι → α i | x i ∈ (s i)ᶜ} ∈ pi f := by
  have h₁ : {x : ι → α i | x i ∈ (s i)ᶜ} ∈ comap (fun x : ι → α i => x i) (f i) := hA
  have h₂ : pi f ≤ comap (fun x : ι → α i => x i) (f i) := h_le
  have h₃ : {x : ι → α i | x i ∈ (s i)ᶜ} ∈ pi f := by
    exact h₂ h₁
  exact h₃
have h_subset : {x : ι → α i | x i ∈ (s i)ᶜ} ⊆ (Set.pi univ s)ᶜ := by
  intro x hx
  have h₁ : x i ∈ (s i)ᶜ := hx
  have h₂ : x i ∉ s i := by simpa using h₁
  have h₃ : ¬ (∀ j : ι, x j ∈ s j) := by
    intro h
    have h₄ : x i ∈ s i := h i
    exact h₂ h₄
  simpa [Set.mem_compl_iff, Set.mem_pi] using h₃
have h_main : (Set.pi univ s)ᶜ ∈ pi f := by
  have h₁ : {x : ι → α i | x i ∈ (s i)ᶜ} ⊆ (Set.pi univ s)ᶜ := h_subset
  have h₂ : {x : ι → α i | x i ∈ (s i)ᶜ} ∈ pi f := hA_in_pi
  exact Filter.mem_of_superset h₂ h₁
exact h_main
```

**lean_error:** tail step 1/51 ('have hA : {x : ι → α i | x i ∈ (s i)ᶜ} ∈ comap (fun x : ι → α i => x i) (f i) := by'): <stdin>:1:83: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.3s, in=286, out=586)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Filter.mem_pi.mpr
use {i}
use Finset.singleton_mem
intro j hj
rw [Finset.mem_singleton] at hj
subst hj
exact hi
```

**lean_error:** tail step 3/7 ('use Finset.singleton_mem'): unknown constant 'Finset.singleton_mem'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 9.8s, verify 0.7s, in=914, out=2135)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hmem : eval i ⁻¹' ((s i)ᶜ) ∈ pi f := mem_pi_of_mem i hi
  refine mem_of_superset hmem ?_
  intro x hx
  intro hxmem
  have : x i ∈ s i := hxmem i (by trivial)
  exact hx this
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 95.9s, verify 0.1s, in=853, out=10846)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : (eval i)⁻¹' (s i)ᶜ ∈ pi f := Filter.mem_pi_of_mem hi
have h₂ : (eval i)⁻¹' (s i)ᶜ ⊆ (Set.pi univ s)ᶜ := by
  intro x hx
  have h₃ : x i ∉ s i := by simpa [Set.mem_compl_iff] using hx
  have h₄ : ∃ (j : ι), x j ∉ s j := ⟨i, h₃⟩
  simpa [Set.mem_compl_iff, Set.mem_pi] using h₄
exact mem_of_superset h₂ h₁
```

**lean_error:** tail step 1/7 ("have h₁ : (eval i)⁻¹' (s i)ᶜ ∈ pi f := Filter.mem_pi_of_mem hi"): application type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 16.1s, verify 0.5s, in=830, out=1580)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Filter.mem_of_superset (Filter.mem_pi_of_mem i hi)
intro x hx
simp only [Set.mem_preimage, Set.mem_compl_iff, Set.mem_pi, Set.mem_univ, true_and] at hx ⊢
push_neg at hx ⊢
exact ⟨i, hx⟩
```

**lean_error:** tail step 5/5 ('exact ⟨i, hx⟩'): application type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.8s, verify 3.0s, in=1097, out=1642)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine mem_of_superset (mem_pi_of_mem i hi) ?_
intro x hx
intro hxmem
exact hx (hxmem i (by trivial))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 123.9s, verify 0.1s, in=1028, out=13741)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : eval i ⁻¹' (s i)ᶜ ∈ pi f := Filter.mem_pi_of_mem hi
have h₂ : eval i ⁻¹' (s i)ᶜ ⊆ (Set.pi univ s)ᶜ := by
  intro x hx
  have h₃ : ¬(x i ∈ s i) := by
    simp only [Set.mem_compl_iff, mem_preimage] at hx
    exact hx
  intro h
  have h₄ : x i ∈ s i := h i
  exact h₃ h₄
have h₃ : (Set.pi univ s)ᶜ ∈ pi f := Filter.mono_set_of h₂ h₁
exact h₃
```

**lean_error:** tail step 1/11 ("have h₁ : eval i ⁻¹' (s i)ᶜ ∈ pi f := Filter.mem_pi_of_mem hi"): application type mismatch

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 12.2s, verify 0.5s, in=1004, out=1179)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Filter.mem_of_superset (mem_pi_of_mem i hi)
intro x hx
simp only [Set.mem_preimage, Set.mem_compl_iff, Set.mem_pi, Set.mem_univ, true_and] at hx ⊢
push_neg at hx ⊢
exact ⟨i, hx⟩
```

**lean_error:** tail step 5/5 ('exact ⟨i, hx⟩'): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.5s, in=1093, out=2468)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hmem : eval i ⁻¹' (s i)ᶜ ∈ pi f := mem_pi_of_mem i hi
  refine mem_of_superset hmem ?_
  intro x hx
  have hx' : x i ∈ (s i)ᶜ := by
    simpa [Set.preimage, Set.mem_setOf_eq] using hx
  intro hxmem
  exact hx' (hxmem i (mem_univ i))
```

**lean_error:** tail step 4/7 ("have hx' : x i ∈ (s i)ᶜ := by"): <stdin>:1:29: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 76.4s, verify 0.1s, in=1084, out=8632)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h : eval i ⁻¹' (s i)ᶜ ∈ pi f := Filter.mem_pi_of_mem hi
have h_subset : eval i ⁻¹' (s i)ᶜ ⊆ (Set.pi univ s)ᶜ :=
  intro g hg
  have h₁ : g i ∈ (s i)ᶜ := hg
  intro h
  have h₂ : g i ∈ s i := (Set.mem_pi.univ h).i
  exact h₁ h₂
exact Filter.mem_of_superset h h_subset
```

**lean_error:** tail step 1/8 ("have h : eval i ⁻¹' (s i)ᶜ ∈ pi f := Filter.mem_pi_of_mem hi"): application type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 106.2s, verify 0.5s, in=1027, out=11507)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Filter.mem_of_superset (Filter.mem_pi_of_mem i hi)
intro x hx
simp only [Set.mem_compl_iff, Set.mem_preimage, Set.mem_pi, Set.mem_univ] at hx ⊢
intro h
exact hx (h i trivial)
```
