# CategoryTheory.Limits.biproduct.conePointUniqueUpToIso_inv   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
rw [Category.assoc, IsLimit.conePointUniqueUpToIso_inv_comp, Bicone.toCone_π_app,
  biproduct.bicone_π, biproduct.ι_desc, biproduct.ι_π, b.toCone_π_app, b.ι_π]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp`, `CategoryTheory.Limits.Bicone.toCone_π_app`, `CategoryTheory.Limits.biproduct.bicone_π`, `CategoryTheory.Limits.biproduct.ι_desc`, `CategoryTheory.Limits.biproduct.ι_π`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | · |
| `hint:3` | · |
| `noise:3` | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 20.7s, verify 0.1s, in=469, out=3829)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Bicone.desc, Category.assoc]
```

**lean_error:** tail step 1/1 ('simp [Bicone.desc, Category.assoc]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 24.9s, verify 0.2s, in=1756, out=4848)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Category.assoc]
```

**final state (truncated):**
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 28.4s, verify 1.3s, in=3563, out=5790)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Category.assoc]
```

**final state (truncated):**
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
...
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 25.1s, verify 0.2s, in=3392, out=4866)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Category.assoc]
```

**final state (truncated):**
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
...
```
