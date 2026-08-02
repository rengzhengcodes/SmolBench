# CategoryTheory.Limits.image.ι_zero'   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`  

**Ground-truth tail (from k):**
```lean
simp
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.4s, verify 0.2s, in=361, out=1005)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases h
simp
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 267.8s, verify 0.1s, in=311, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
eqToIso_equalizer {f g : X ⟶ Y} (h : f = g) : Equalizer f g ≅ X
```

**lean_error:** tail step 1/1 ('eqToIso_equalizer {f g : X ⟶ Y} (h : f = g) : Equalizer f g ≅ X'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=305, out=488)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_all [eqToIso_hom]
```

**lean_error:** tail step 1/1 ('simp_all [eqToIso_hom]'): unknown identifier 'eqToIso_hom'
