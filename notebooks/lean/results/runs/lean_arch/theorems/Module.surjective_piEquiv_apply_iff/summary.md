# Module.surjective_piEquiv_apply_iff   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/StdBasis.lean`  

**Ground-truth tail (from k):**
```lean
rw [← LinearMap.range_eq_top, range_piEquiv]
```

**True premises at k:** `LinearMap.range_eq_top`, `Module.range_piEquiv`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 1.7s, in=335, out=222)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h
    rw [Submodule.eq_top_iff']
    intro x
    obtain ⟨y, rfl⟩ := h x
    exact Submodule.sum_mem _ (fun b _ => Submodule.smul_mem _ _ (Submodule.subset_span (mem_range_self b)))
  · intro h
    intro x
    rw [Submodule.eq_top_iff'] at h
    obtain ⟨s, f, hs, rfl⟩ := h x
    refine' ⟨∑ i in s, f i • v i, _⟩
    ext i
    simp only [LinearEquiv.coe_coe, LinearEquiv.piEquiv_apply, LinearEquiv.symm_symm, LinearEquiv.symm_apply_apply]
    have : v i ∈ span R (range v) := Submodule.subset_span (mem_range_self i)
    apply (Submodule.sums_mem _ _ _ _).symm
    intro i
    split_ifs with hi
    · exact this
    · exact Submodule.zero_mem _
```

**lean_error:** tail step 2/19 ('· intro h'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=307, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← LinearMap.coe_range, (piEquiv ι R M v).range_eq_map, LinearMap.map_top, ← Submodule.eq_top_iff', LinearEquiv.range]
simp [range_comp, (· ∘ ·)]
```

**lean_error:** tail step 1/2 ("rw [← LinearMap.coe_range, (piEquiv ι R M v).range_eq_map, LinearMap.map_top, ← Submodule.eq_top_iff', LinearEquiv.range]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=324, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply piEquiv_surjective_iff
```

**lean_error:** tail step 1/1 ('apply piEquiv_surjective_iff'): unknown identifier 'piEquiv_surjective_iff'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=681, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=642, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Module.range_piEquiv v, LinearMap.range_eq_top]
rfl
```

**lean_error:** tail step 1/2 ('rw [← Module.range_piEquiv v, LinearMap.range_eq_top]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=670, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_piEquiv, range_eq_top]
```

**lean_error:** tail step 1/1 ('rw [range_piEquiv, range_eq_top]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1242, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1196, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← LinearMap.range_eq_top, Module.range_piEquiv]
rfl
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 2.3s, in=1231, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Iff.rfl
```

**lean_error:** tail step 1/1 ('exact Iff.rfl'): type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1267, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.3s, in=1294, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Module.range_piEquiv v, LinearMap.range_eq_top]
rfl
```

**lean_error:** tail step 1/2 ('rw [← Module.range_piEquiv v, LinearMap.range_eq_top]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.1s, in=1256, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Iff.rfl
```

**lean_error:** tail step 1/1 ('exact Iff.rfl'): type mismatch
