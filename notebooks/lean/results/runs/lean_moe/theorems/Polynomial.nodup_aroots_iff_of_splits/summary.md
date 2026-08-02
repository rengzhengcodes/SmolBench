# Polynomial.nodup_aroots_iff_of_splits   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Separable.lean`  

**Ground-truth tail (from k):**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

**True premises at k:** `Polynomial.nodup_roots_iff_of_splits`, `Polynomial.map_ne_zero`, `Polynomial.separable_map`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.1s, in=334, out=1282)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (Polynomial.nodup_aroots_iff (f:=f) (K:=K) hf h)
```

**lean_error:** tail step 1/1 ('simpa using (Polynomial.nodup_aroots_iff (f:=f) (K:=K) hf h)'): unknown constant 'Polynomial.nodup_aroots_iff'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 207.6s, verify 0.1s, in=278, out=26734)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h_inj : Function.Injective (algebraMap F K) := by
  apply Algebra.injective_iff_nontrivial.mpr
  <;> simp [algebraMap_one]
have h_sep_iff : Separable f ↔ Separable (map (algebraMap F K) f) := by
  apply Polynomial.Separable.map_iff
  <;> exact h_inj
have h_p_splits : Splits (RingHom.id K) (map (algebraMap F K) f) := h
have h_sep_p_iff_nodup : Separable (map (algebraMap F K) f) ↔ Multiset.Nodup (aroots (map (algebraMap F K) f) K) := by
  have p : Polynomial K := map (algebraMap F K) f
  constructor
  · -- Separable p → Multiset.Nodup (aroots p K)
    intro hsep
    exact Polynomial.Separable.nodup_aroots hsep
  · -- Multiset.Nodup (aroots p K) → Separable p
    intro hnodup
    exact Polynomial.nodup_aroots_separable h_p_splits hnodup
have h_main : Separable f ↔ Multiset.Nodup (aroots f K) := by
  have p : Polynomial K := map (algebraMap F K) f
  have h₁ : Separable f ↔ Separable p := by
    rw [h_sep_iff]
  have h₂ : Separable p ↔ Multiset.Nodup (aroots p K) := by
    exact h_sep_p_iff_nodup
  have h₃ : aroots f K = aroots p K := by
    rfl
  rw [h₁, h₂, h₃]
exact h_main
```

**lean_error:** tail step 1/26 ('have h_inj : Function.Injective (algebraMap F K) := by'): <stdin>:1:54: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.8s, verify 0.1s, in=278, out=638)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [nodup_aroots_iff_separable h]
```

**lean_error:** tail step 1/1 ('rw [nodup_aroots_iff_separable h]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.1s, in=1204, out=1712)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hmap : (map (algebraMap F K) f) ≠ 0 := by
    exact map_ne_zero (f := algebraMap F K) hf
  simpa [aroots] using
    ((nodup_roots_iff_of_splits (f := map (algebraMap F K) f) hmap h).trans
      (separable_map (algebraMap F K)).symm)
```

**lean_error:** tail step 1/5 ('have hmap : (map (algebraMap F K) f) ≠ 0 := by'): <stdin>:1:46: unexpected end of input; expected '{'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 48.1s, verify 0.1s, in=1193, out=5400)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [aroots_map]
have hg_ne_zero : (map (algebraMap F K) f) ≠ 0 := Polynomial.map_ne_zero (algebraMap F K) hf
have hg_splits : (map (algebraMap F K) f).Splits (RingHom.id K) := h
have hg_nodup_roots_iff_separable : (map (algebraMap F K) f).roots.Nodup ↔ (map (algebraMap F K) f).Separable := by
  apply Polynomial.nodup_roots_iff_of_splits hg_ne_zero hg_splits
rw [hg_nodup_roots_iff_separable]
have hg_separable_map : (map (algebraMap F K) f).Separable ↔ f.Separable := by
  apply Polynomial.separable_map
rw [hg_separable_map]
```

**lean_error:** tail step 1/9 ('rw [aroots_map]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.2s, verify 0.1s, in=1123, out=1188)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [aroots_eq_roots_map]
refine' iff_trans (nodup_roots_iff_of_splits (map_ne_zero hf) h) _
exact (separable_map (algebraMap F K)).symm
```

**lean_error:** tail step 1/3 ('rw [aroots_eq_roots_map]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.6s, verify 0.1s, in=3668, out=2473)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hfK : (map (algebraMap F K) f) ≠ 0 :=
    Polynomial.map_ne_zero (algebraMap F K) hf
  simpa [Polynomial.aroots] using
    ((Polynomial.nodup_roots_iff_of_splits (f:=map (algebraMap F K) f) hfK h).trans
      (by
        simpa using (Polynomial.separable_map (algebraMap F K) (p:=f))))
```

**lean_error:** tail step 1/6 ('have hfK : (map (algebraMap F K) f) ≠ 0 :='): <stdin>:1:42: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 52.5s, verify 0.1s, in=3771, out=5912)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hg_ne_zero : (map (algebraMap F K) f) ≠ 0 := by
  apply Polynomial.map_ne_zero
  <;> simp_all [algebraMap_ne_zero]
  <;> aesop

have hg_splits : (map (algebraMap F K) f).Splits (RingHom.id K) := h

have hg_nodup_roots_iff_separable : (map (algebraMap F K) f).roots.Nodup ↔ (map (algebraMap F K) f).Separable := by
  apply Polynomial.nodup_roots_iff_of_splits hg_ne_zero hg_splits

have h_separable_map : (map (algebraMap F K) f).Separable ↔ f.Separable := by
  apply Polynomial.separable_map

have h_main : Multiset.Nodup (aroots f K) ↔ f.Separable := by
  constructor
  · intro hn
    have hn' : Multiset.Nodup ((map (algebraMap F K) f).roots) := by
      simpa [aroots] using hn
    have hsep : (map (algebraMap F K) f).Separable := by
      exact hg_nodup_roots_iff_separable.mp hn'
    exact h_separable_map.mpr hsep
  · intro hsep
    have hsep' : (map (algebraMap F K) f).Separable := by
      exact h_separable_map.mpr hsep
    have hn' : Multiset.Nodup ((map (algebraMap F K) f).roots) := by
      exact hg_nodup_roots_iff_separable.mpr hsep'
    simpa [aroots] using hn'

exact h_main
```

**lean_error:** tail step 1/24 ('have hg_ne_zero : (map (algebraMap F K) f) ≠ 0 := by'): <stdin>:1:52: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.5s, verify 1.8s, in=3540, out=994)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← separable_map (algebraMap F K)]
rw [← nodup_roots_iff_of_splits (map_ne_zero (algebraMap F K) hf) h]
rw [← aroots_def]
```

**lean_error:** tail step 2/3 ('rw [← nodup_roots_iff_of_splits (map_ne_zero (algebraMap F K) hf) h]'): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.5s, verify 2.0s, in=3349, out=4625)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h0 : (map (algebraMap F K) f) ≠ 0 := map_ne_zero hf
  have h' : (map (algebraMap F K) f).Splits (RingHom.id K) := by
    simpa using ((splits_map_iff (algebraMap F K) f).2 h)
  have hiff :=
    (nodup_roots_iff_of_splits (f := map (algebraMap F K) f) h0 h')
  simpa [aroots] using hiff.trans ((separable_map (algebraMap F K) (p := f)).symm)
```

**lean_error:** tail step 2/6 ("have h' : (map (algebraMap F K) f).Splits (RingHom.id K) := by"): <stdin>:1:62: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 91.4s, verify 0.1s, in=3994, out=11001)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hmap_ne_zero : (map (algebraMap F K) f) ≠ 0 := by
  apply Polynomial.map_ne_zero
  <;> infer_instance
  <;> simp_all [hf]
  
have hnodup_roots_iff_separable : ((map (algebraMap F K) f)).roots.Nodup ↔ (map (algebraMap F K) f).Separable := by
  apply Polynomial.nodup_roots_iff_of_splits hmap_ne_zero
  <;> assumption
  
have haroots_eq_roots : (map (algebraMap F K) f).aroots K = (map (algebraMap F K) f).roots := by
  apply Polynomial.aroots_eq_roots_of_splits
  <;> assumption
  
have hmap_aroots : (map (algebraMap F K) f).aroots K = f.aroots K := by
  rw [Polynomial.aroots_map]
  <;> simp [algebraMap_map]
  
have hmain : Multiset.Nodup (aroots f K) ↔ Separable f := by
  constructor
  · -- Prove the forward direction: if aroots f.K is nodup, then f is separable.
    intro hnodup
    have h1 : Multiset.Nodup ((map (algebraMap F K) f).aroots K) := by
      rw [hmap_aroots] at hnodup
      exact hnodup
    have h2 : Multiset.Nodup ((map (algebraMap F K) f).roots) := by
      rw [haroots_eq_roots] at h1
      exact h1
    have h3 : (map (algebraMap F K) f).Separable := by
      have h4 : ((map (algebraMap F K) f)).roots.Nodup ↔ (map (algebraMap F K) f).Separable := hnodup_roots_iff_separable
      exact (h4.mp h2)
    have h5 : f.Separable := by
      have h6 : (map (algebraMap F K) f).Separable ↔ f.Separable := by
        apply Polynomial.separable_map
      exact (h6.mp h3)
    exact h5
  · -- Prove the reverse direction: if f is separable, then aroots f.K is nodup.
    intro hsep
    have h1 : (map (algebraMap F K) f).Separable := by
      have h2 : (map (algebraMap F K) f).Separable ↔ f.Separable := by
        apply Polynomial.separable_map
      exact (h2.mpr hsep)
    have h3 : ((map (algebraMap F K) f)).roots.Nodup := by
      have h4 : ((map (algebraMap F K) f)).roots.Nodup ↔ (map (algebraMap F K) f).Separable := hnodup_roots_iff_separable
      exact (h4.mpr h1)
    have h5 : Multiset.Nodup ((map (algebraMap F K) f).aroots K) := by
      rw [haroots_eq_roots] at h3
      exact h3
    have h6 : Multiset.Nodup (aroots f K) := by
      rw [hmap_aroots] at h5
      exact h5
    exact h6
  
exact hmain
```

**lean_error:** tail step 1/48 ('have hmap_ne_zero : (map (algebraMap F K) f) ≠ 0 := by'): <stdin>:1:54: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 1.4s, in=3510, out=664)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hmap : (map (algebraMap F K) f).roots.Nodup ↔ (map (algebraMap F K) f).Separable :=
  nodup_roots_iff_of_splits (map_ne_zero hf) h
rw [← separable_map (algebraMap F K)] at hmap
rw [← aroots_eq_roots_map] at hmap
exact hmap
```

**lean_error:** tail step 1/5 ('have hmap : (map (algebraMap F K) f).roots.Nodup ↔ (map (algebraMap F K) f).Separable :='): <stdin>:1:88: unexpected end of input
