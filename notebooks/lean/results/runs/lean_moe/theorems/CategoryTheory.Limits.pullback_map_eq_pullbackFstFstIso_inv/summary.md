# CategoryTheory.Limits.pullback_map_eq_pullbackFstFstIso_inv   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Diagonal.lean`  

**Ground-truth tail (from k):**
```lean
simp only [pullbackFstFstIso_inv, lift_snd_assoc, lift_fst]
```

**True premises at k:** `CategoryTheory.Limits.pullbackFstFstIso_inv`, `CategoryTheory.Limits.pullback.lift_snd_assoc`, `CategoryTheory.Limits.pullback.lift_fst`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✓ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.3s, verify 0.5s, in=508, out=1225)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [map]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 13.3s, verify 0.6s, in=980, out=2764)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
· simp [map, pullbackFstFstIso, Category.assoc]
· simp [map, pullbackFstFstIso, Category.assoc]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 15.6s, verify 0.5s, in=1122, out=3265)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
· simp [Category.assoc]
· simp [Category.assoc]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.4s, verify 0.2s, in=1128, out=1750)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext <;> simp [Category.assoc]
```
