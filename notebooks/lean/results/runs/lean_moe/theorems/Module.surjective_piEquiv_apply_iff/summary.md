# Module.surjective_piEquiv_apply_iff   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/StdBasis.lean`  

**Ground-truth tail (from k):**
```lean
rw [← LinearMap.range_eq_top, range_piEquiv]
```

**True premises at k:** `LinearMap.range_eq_top`, `Module.range_piEquiv`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.7s, verify 0.1s, in=382, out=1838)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
classical
  simpa using (LinearMap.surjective_iff_span_eq_top (v := v))
```

**lean_error:** tail step 1/2 ('classical'): <stdin>:1:9: unexpected end of input; expected '{'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 252.7s, verify 0.1s, in=330, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h_key : ∀ (x : ι → R), ⇑((piEquiv ι R M) v) x = ∑ i : ι, x i • v i := by
  intro x
  have h₁ : ⇑((piEquiv ι R M) v) x = ∑ i : ι, x i • ⇑((piEquiv ι R M) v) (fun j : ι => if j = i then (1 : R) else 0)) := by
    -- Use linearity and the fact that x = ∑ i, x i • e_i
    have h₂ : ⇑((piEquiv ι R M) v) x = ∑ i : ι, x i • ⇑((piEquiv ι R M) v) (fun j : ι => if j = i then (1 : R) else 0)) := by
      -- Prove that the map is linear and then use the sum over the basis
      have h₃ : LinearMap (⇑((piEquiv ι R M) v)) := by
        -- The underlying function of a linear equivalence is linear
        exact piEquiv ι R M.map
      -- Use the linear map to distribute over the sum
      have h₄ : ⇑((piEquiv ι R M) v) x = ∑ i : ι, x i • ⇑((piEquiv ι R M) v) (fun j : ι => if j = i then (1 : R) else 0)) := by
        -- Express x as a sum over the basis
        have h₅ : x = ∑ i : ι, x i • (fun j : ι => if j = i then (1 : R) else 0)) := by
          -- Prove that x is the sum of its components times the basis vectors
          ext j
          simp [Finset.sum_ite_eq', Finset.mem_singleton]
          <;>
          aesop
        -- Use linearity of the map
        rw [h₅]
        rw [h₃.map_sum]
        <;>
        simp [smul_smul]
        <;>
        apply Finset.sum_congr rfl
        <;>
        intros i _
        <;>
        simp [smul_smul]
        <;>
        ring
      exact h₄
    exact h₂
  -- Now, use the basis property to replace ⇑((piEquiv ι R M) v) e_i with v i
  have h₂ : ∑ i : ι, x i • ⇑((piEquiv ι R M) v) (fun j : ι => if j = i then (1 : R) else 0)) = ∑ i : ι, x i • v i := by
    apply Finset.sum_congr rfl
    intro i _
    rw [h_basis i]
  rw [h₁]
  rw [h₂]
```

**lean_error:** tail step 1/40 ('have h_key : ∀ (x : ι → R), ⇑((piEquiv ι R M) v) x = ∑ i : ι, x i • v i := by'): <stdin>:1:77: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=318, out=711)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [piEquiv_apply]
  constructor
  · intro h
    apply eq_top_iff'.mpr
    intro m
    have := h m
    simp at this
    exact this
  · intro h
    intro m
    have := h.symm m
    simp at this
    obtain ⟨f, hf⟩ := this
    use f
    simp [hf]
```

**lean_error:** tail step 1/15 ('rw [piEquiv_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.1s, in=742, out=2580)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Module.range_piEquiv] using
    (LinearMap.range_eq_top (f := (piEquiv ι R M v))).symm
```

**lean_error:** tail step 1/2 ('simpa [Module.range_piEquiv] using'): <stdin>:1:34: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 35.7s, verify 0.1s, in=695, out=4308)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_range_eq : range (piEquiv ι R M v) = span R (range v) := by rw [Module.range_piEquiv]
have h_surj_iff : Surjective ⇑((piEquiv ι R M) v) ↔ range (piEquiv ι R M v) = ⊤ := by apply LinearMap.range_eq_top
rw [h_surj_iff]
rw [h_range_eq]
<;> rfl
<;> rfl
```

**lean_error:** tail step 1/6 ('have h_range_eq : range (piEquiv ι R M v) = span R (range v) := by rw [Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.9s, verify 0.1s, in=678, out=471)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← LinearMap.range_eq_top, Module.range_piEquiv]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 1.2s, in=1333, out=1157)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Module.range_piEquiv] using
    (LinearMap.range_eq_top (f := (piEquiv ι R M v))).symm
```

**lean_error:** tail step 1/2 ('simpa [Module.range_piEquiv] using'): <stdin>:1:34: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 52.4s, verify 0.2s, in=1290, out=6479)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
haveI : RingHomSurjective (RingHom.id R) := ⟨fun y => ⟨y, rfl⟩⟩
have h₁ : Surjective ⇑((piEquiv ι R M) v) ↔ LinearMap.range (piEquiv ι R M v) = ⊤ := by
  apply LinearMap.range_eq_top
have h₂ : LinearMap.range (piEquiv ι R M v) = span R (range v) := by
  rw [Module.range_piEquiv]
rw [h₁]
rw [h₂]
```

**lean_error:** tail step 2/7 ('have h₁ : Surjective ⇑((piEquiv ι R M) v) ↔ LinearMap.range (piEquiv ι R M v) = ⊤ := by'): <stdin>:1:87: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.0s, verify 0.1s, in=1264, out=382)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← LinearMap.range_eq_top, Module.range_piEquiv]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.1s, in=1278, out=1553)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [range_piEquiv (v := v)] using
  ((LinearMap.range_eq_top (f := piEquiv ι R M v)).symm)
```

**lean_error:** tail step 1/2 ('simpa [range_piEquiv (v := v)] using'): <stdin>:1:36: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 40.6s, verify 0.1s, in=1392, out=4985)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top]
rw [Module.range_piEquiv]
<;> rfl
```

**lean_error:** tail step 1/3 ('rw [LinearMap.range_eq_top]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.5s, verify 0.1s, in=1272, out=561)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← LinearMap.range_eq_top, Module.range_piEquiv]
```
