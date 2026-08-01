# CategoryTheory.Biprod.ofComponents_eq   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
ext <;>
  simp only [Category.comp_id, biprod.inr_fst, biprod.inr_snd, biprod.inl_snd, add_zero, zero_add,
    Biprod.inl_ofComponents, Biprod.inr_ofComponents, eq_self_iff_true, Category.assoc,
    comp_zero, biprod.inl_fst, Preadditive.add_comp]
```

**True premises at k:** `CategoryTheory.Category.comp_id`, `CategoryTheory.Limits.biprod.inr_fst`, `CategoryTheory.Limits.biprod.inr_snd`, `CategoryTheory.Limits.biprod.inl_snd`, `add_zero`, `zero_add`, `CategoryTheory.Biprod.inl_ofComponents`, `CategoryTheory.Biprod.inr_ofComponents`, `eq_self_iff_true`, `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.comp_zero`, `CategoryTheory.Limits.biprod.inl_fst`, `CategoryTheory.Preadditive.add_comp`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✓ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 17.5s, verify 0.4s, in=503, out=3557)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext <;> simp [ofComponents, Category.assoc]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 17.3s, verify 0.2s, in=2473, out=3500)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext <;> simp [Category.assoc]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 14.2s, verify 0.2s, in=3111, out=2743)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext <;> simp [Category.assoc]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 19.0s, verify 0.8s, in=3058, out=3920)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext <;> simp [Category.assoc]
```
