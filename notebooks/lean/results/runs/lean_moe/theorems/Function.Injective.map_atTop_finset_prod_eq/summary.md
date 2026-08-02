# Function.Injective.map_atTop_finset_prod_eq   (k=12, 13 tactics total)

file: `Mathlib/Order/Filter/AtTopBot.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨_, (image_subset_iff_subset_preimage _).1 ht, rfl⟩
```

**True premises at k:** `Finset.image_subset_iff_subset_preimage`, `rfl`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.8s, verify 0.1s, in=428, out=2188)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨Finset.preimage t g hg, ?_, ?_⟩
· intro x hx
  have hx' : g x ∈ Finset.image g s := by
    exact Finset.mem_image.mpr ⟨x, hx, rfl⟩
  have hx'' : g x ∈ t := ht hx'
  simpa [Finset.mem_preimage] using hx''
· rfl
```

**lean_error:** tail step 1/7 ('refine ⟨Finset.preimage t g hg, ?_, ?_⟩'): application type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 24.8s, verify 0.1s, in=383, out=2778)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨Finset.preimage t g, _, _⟩
· apply Finset.subset_preimage
  exact ht
· rfl
```

**lean_error:** tail step 1/4 ("refine' ⟨Finset.preimage t g, _, _⟩"): application type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.1s, in=371, out=520)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use Finset.preimage t g
constructor
· intro x hx
  simp only [Finset.mem_preimage]
  apply ht
  exact Finset.mem_image_of_mem g hx
· rfl
```

**lean_error:** tail step 1/7 ('use Finset.preimage t g'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 34.3s, verify 1.8s, in=1205, out=8228)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' ⟨t.preimage g (hg.injOn _), ?_, ?_⟩
  · exact (image_subset_iff_subset_preimage (hg.injOn _)).1 ht
  · rfl
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 119.0s, verify 0.1s, in=1186, out=13463)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' ⟨Finset.preimage t g, fun x hx => ht (Finset.mem_image ⟨x, hx, rfl⟩), rfl⟩
```

**lean_error:** tail step 1/1 ("refine' ⟨Finset.preimage t g, fun x hx => ht (Finset.mem_image ⟨x, hx, rfl⟩), rfl⟩"): type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.3s, verify 0.2s, in=1124, out=739)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' ⟨t.preimage g (hg.injOn _), _, rfl⟩
exact (Finset.image_subset_iff_subset_preimage _).2 ht
```

**lean_error:** tail step 2/2 ('exact (Finset.image_subset_iff_subset_preimage _).2 ht'): type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.2s, verify 0.1s, in=2248, out=4434)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hsub : s ⊆ t.preimage g (hg.injOn _) :=
  (Finset.image_subset_iff_subset_preimage (hg.injOn _)).1 ht
rfl
```

**lean_error:** tail step 1/3 ('have hsub : s ⊆ t.preimage g (hg.injOn _) :='): <stdin>:1:44: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 97.7s, verify 0.1s, in=2234, out=10973)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : Set.InjOn g (t.preimage g _) := by
  apply Set.InjOn_mono hg
  exact Set.preimage_subset_univ
have h₂ : s.image g ⊆ t ↔ s ⊆ t.preimage g _ := by
  apply Finset.image_subset_iff_subset_preimage
  <;> assumption
have h₃ : s.image g ⊆ t := ht
have h₄ : s ⊆ t.preimage g _ := by
  rw [h₂] at h₃
  exact h₃
exact rfl
```

**lean_error:** tail step 1/11 ('have h₁ : Set.InjOn g (t.preimage g _) := by'): <stdin>:1:44: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.6s, verify 0.1s, in=2172, out=564)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (Finset.image_subset_iff_subset_preimage (hg.injOn _)).mpr ht
```

**lean_error:** tail step 1/1 ('exact (Finset.image_subset_iff_subset_preimage (hg.injOn _)).mpr ht'): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 26.2s, verify 0.2s, in=2142, out=6208)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using rfl
```

**lean_error:** tail step 1/1 ('simpa using rfl'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 50.0s, verify 0.1s, in=2405, out=5480)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine' ⟨Finset.preimage t g, _⟩
  <;> simp_all [Finset.subset_preimage]
  <;> aesop
```

**lean_error:** tail step 1/3 ("refine' ⟨Finset.preimage t g, _⟩"): application type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.7s, verify 0.2s, in=2164, out=573)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine' ⟨t.preimage g (hg.injOn _), _, rfl⟩
rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]
exact ht
```

**lean_error:** tail step 2/3 ('rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
