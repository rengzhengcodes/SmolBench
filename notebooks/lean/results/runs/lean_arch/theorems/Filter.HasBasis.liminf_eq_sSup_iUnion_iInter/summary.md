# Filter.HasBasis.liminf_eq_sSup_iUnion_iInter   (k=3, 4 tactics total)

file: `Mathlib/Order/LiminfLimsup.lean`  

**Ground-truth tail (from k):**
```lean
simp only [mem_setOf_eq, iInter_coe_set, mem_iUnion, mem_iInter, mem_Iic, Subtype.exists,
  exists_prop]
```

**True premises at k:** `Set.mem_setOf_eq`, `Set.iInter_coe_set`, `Set.mem_iUnion`, `Set.mem_iInter`, `Set.mem_Iic`, `Subtype.exists`, `exists_prop`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.0s, verify 0.3s, in=408, out=121)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · rintro ⟨i, hi, h⟩
    refine' mem_iUnion.2 ⟨i, mem_iInter.2 _⟩
    intro j
    exact h _ (hv.mem_basis_iff.1 hi).1 j
  · rintro ⟨i, hi⟩
    refine' ⟨i, (hv.mem_basis_iff.2 _).1, _⟩
    · intro j
      exact mem_iInter.1 hi j
    · intro x hx
      exact mem_Iic.1 (mem_iInter.1 hi x)
```

**lean_error:** tail step 2/11 ('· rintro ⟨i, hi, h⟩'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=374, out=46)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [mem_setOf, mem_iUnion, mem_iInter, mem_Iic, hv.mem_iff]
simp only [subset_def, mem_setOf, forall_apply_eq_imp_iff₂, exists_prop]
rfl
```

**lean_error:** tail step 1/3 ('simp_rw [mem_setOf, mem_iUnion, mem_iInter, mem_Iic, hv.mem_iff]'): simp made no progress

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 54.7s, verify 0.1s, in=397, out=3378)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp [Set.Iic]
```

**lean_error:** tail step 1/2 ('ext'): applyExtTheorem only applies to equations, not

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.1s, in=1602, out=128)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.mem_setOf_eq, Subtype.exists, exists_prop]
simp_rw [Set.iInter_coe_set, Set.mem_iUnion, Set.mem_iInter, Set.mem_Iic]
constructor
· rintro ⟨j, hj, h⟩
  refine' ⟨j, _⟩
  rintro i x hx
  exact h i hx
· rintro ⟨j, h⟩
  refine' ⟨j, _, h⟩
  exact h j (Set.mem_iInter.1 (Set.mem_iUnion.2 ⟨j, Set.mem_iInter.2 h j⟩) j)
```

**lean_error:** tail step 1/10 ('rw [Set.mem_setOf_eq, Subtype.exists, exists_prop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 1.5s, verify 0.3s, in=1551, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [mem_setOf_eq, mem_iUnion, mem_iInter, mem_Iic, Subtype.exists, exists_prop]
simp [hv.eventually_iff]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=1591, out=54)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [Set.mem_setOf_eq, Set.iInter_coe_set, Set.mem_iUnion, Set.mem_iInter, Set.mem_Iic]
simp only [exists_prop, Subtype.exists, and_imp, exists_imp_distrib]
```

**lean_error:** tail step 2/2 ('simp only [exists_prop, Subtype.exists, and_imp, exists_imp_distrib]'): unknown identifier 'exists_imp_distrib'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1787, out=43)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_setOf_eq, Subtype.exists, exists_prop]
simp_rw [Set.iInter_coe_set, Set.mem_iInter, Set.mem_Iic]
rw [Set.mem_iUnion]
```

**lean_error:** tail step 1/3 ('rw [Set.mem_setOf_eq, Subtype.exists, exists_prop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.2s, verify 0.3s, in=1738, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [mem_setOf_eq, mem_iUnion, mem_iInter, mem_Iic, exists_prop, Subtype.exists]
simp [hv.eventually_iff]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=1776, out=46)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [Set.mem_setOf_eq, Set.iInter_coe_set, Set.mem_iUnion, Set.mem_iInter, Set.mem_Iic]
simp only [exists_prop, Subtype.exists]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.1s, in=1811, out=97)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Set.mem_setOf_eq, exists_prop]
rw [Set.mem_iUnion, Subtype.exists]
constructor
rintro ⟨i, pi, h⟩
exact ⟨i, fun j => Set.mem_Iic.mpr (h j pi)⟩
rintro ⟨i, h⟩
refine ⟨i, pi := ?_, fun j pj => Set.mem_Iic.mp (h j)⟩
exact Set.mem_iInter.mp (h i)
```

**lean_error:** tail step 1/8 ('rw [Set.mem_setOf_eq, exists_prop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.4s, in=1782, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [mem_setOf_eq, mem_iUnion, mem_iInter, mem_Iic, exists_prop, Subtype.exists]
simp [Subtype.coe_mk]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.4s, verify 0.2s, in=1800, out=46)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [Set.mem_setOf_eq, Set.iInter_coe_set, Set.mem_iUnion, Set.mem_iInter, Set.mem_Iic]
simp only [exists_prop, Subtype.exists]
```
