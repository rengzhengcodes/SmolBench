# FixedPoints.finrank_le_card   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Fixed.lean`  

**Ground-truth tail (from k):**
```lean
apply rank_le_card
```

**True premises at k:** `FixedPoints.rank_le_card`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=313, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' le_trans (Module.rank_le_card _ _) _,
exact_mod_cast Fintype.card_le_of_embedding (subfield.embedding G F)
```

**lean_error:** tail step 1/2 ("refine' le_trans (Module.rank_le_card _ _) _,"): <stdin>:1:44: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.3s, in=285, out=195)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Cardinal.lift_le]
exact Cardinal.lift_mk_le'.mpr ⟨Fintype.equivSubfield G F⟩
exact LinearIndependent.restrict_smul (IsSMulRegular.of_isUnit (Units.mkOfKey G)) (LinearIndependent.restrict_smul (IsSMulRegular.of_isUnit (Units.mkOfKey M)) LinearIndependent.unit_smul)
rw [← Cardinal.lift_le]
exact Cardinal.lift_mk_le'.mpr ⟨Fintype.equivSubfield G F⟩
rw [← Cardinal.lift_le]
exact Cardinal.lift_mk_le'.mpr ⟨Fintype.equivSubfield G F⟩
rw [← Cardinal.lift_le]
exact Cardinal.lift_mk_le'.mpr ⟨Fintype.equivSubfield G F⟩
rw [Module.rank, Cardinal.lift_le]
exact Cardinal.mk_le_of_injective (MulAction.toLinearMap_injective G F)
```

**lean_error:** tail step 2/11 ("exact Cardinal.lift_mk_le'.mpr ⟨Fintype.equivSubfield G F⟩"): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=302, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply_mod_cast rank_le_card
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=552, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FixedPoints.rank_le_card
```

**lean_error:** tail step 1/1 ('exact FixedPoints.rank_le_card'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=524, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact FixedPoints.rank_le_card G F
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.3s, in=541, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Cardinal.natCast_le.mpr
exact rank_le_card
```

**lean_error:** tail step 1/2 ('apply Cardinal.natCast_le.mpr'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=2368, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact FixedPoints.rank_le_card
```

**lean_error:** tail step 1/1 ('exact FixedPoints.rank_le_card'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=2330, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact rank_le_card G F
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=2357, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply FixedPoints.rank_le_card
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=2396, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact FixedPoints.rank_le_card
```

**lean_error:** tail step 1/1 ('exact FixedPoints.rank_le_card'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=2577, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact FixedPoints.rank_le_card G F
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=2385, out=5)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact rank_le_card
```

**lean_error:** tail step 1/1 ('exact rank_le_card'): type mismatch
