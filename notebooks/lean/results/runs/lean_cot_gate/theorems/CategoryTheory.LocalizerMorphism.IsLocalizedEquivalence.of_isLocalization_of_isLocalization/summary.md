# CategoryTheory.LocalizerMorphism.IsLocalizedEquivalence.of_isLocalization_of_isLocalization   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Localization/LocalizerMorphism.lean`  

**Ground-truth tail (from k):**
```lean
exact IsLocalizedEquivalence.mk' Φ (Φ.functor ⋙ L₂) L₂ (𝟭 D₂)
```

**True premises at k:** `CategoryTheory.LocalizerMorphism.IsLocalizedEquivalence.mk'`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 113.1s, verify 0.1s, in=477, out=4691)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.of_localization_equivalence
  (Functor.IsLocalization.localization_equivalence inst✝ inst✝²)
```

**lean_error:** tail step 1/2 ('apply IsLocalizedEquivalence.of_localization_equivalence'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 171.1s, verify 0.1s, in=477, out=6908)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.of_equivalence,
apply IsLocalization.equivalence,
exact inst✝,
exact inst✝²
```

**lean_error:** tail step 1/4 ('apply IsLocalizedEquivalence.of_equivalence,'): <stdin>:1:43: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 179.2s, verify 0.1s, in=477, out=7211)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply LocalizerMorphism.isLocalizedEquivalence_of_comp_is_localization
```

**lean_error:** tail step 1/1 ('apply LocalizerMorphism.isLocalizedEquivalence_of_comp_is_localization'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 754.6s, verify 0.1s, in=477, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨G, _⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.functor ⋙ L₂) inst✝ inst✝²⟩
apply IsLocalizedEquivalence.ofEquivalence⟩
apply Equivalence.ofIsLocalization L₁ (Φ.fun
```

**lean_error:** tail step 1/1598 ('refine ⟨G, _⟩'): invalid constructor ⟨...⟩, insufficient number of arguments, constructs 'CategoryTheory.IsEquivalence.mk'' has #4 explicit fields, but only #2 provided

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=477, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' _ this
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' _ this"): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=477, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.of_eq _ _ this
```

**lean_error:** tail step 1/1 ('exact IsLocalizedEquivalence.of_eq _ _ this'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.0s, verify 0.2s, in=477, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' Φ.functor L₁ L₂
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' Φ.functor L₁ L₂"): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.2s, verify 0.1s, in=477, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.of_iso (NatIso.ofComponents (fun _ => Iso.refl _) (by tidy))
```

**lean_error:** tail step 1/1 ('exact IsLocalizedEquivalence.of_iso (NatIso.ofComponents (fun _ => Iso.refl _) (by tidy))'): <stdin>:1:84: unknown tactic

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.3s, verify 0.1s, in=477, out=242)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact LocalizerMorphism.isLocalizedEquivalence_of_isLocalization_of_commSq Φ inst✝ this
```

**lean_error:** tail step 1/1 ('exact LocalizerMorphism.isLocalizedEquivalence_of_isLocalization_of_commSq Φ inst✝ this'): <stdin>:1:81: expected end of input

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 8.5s, verify 0.1s, in=477, out=243)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact isLocalization_isLocalizedEquivalence (Φ.functor ⋙ L₂) this
```

**lean_error:** tail step 1/1 ('exact isLocalization_isLocalizedEquivalence (Φ.functor ⋙ L₂) this'): unknown identifier 'isLocalization_isLocalizedEquivalence'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.5s, verify 0.2s, in=477, out=306)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

**lean_error:** tail step 1/1 ('aesop_cat'): tactic 'aesop' failed, failed to prove the goal after exhaustive search.

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.7s, verify 0.1s, in=477, out=312)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨fun X => ⟨inst✝.map X, inst✝.w _⟩, fun X => ⟨inst✝¹.1 X, inst✝¹.2.1.1 X, this.comm,
  this.right_1, this.left_1⟩⟩
```

**lean_error:** tail step 1/2 ('exact ⟨fun X => ⟨inst✝.map X, inst✝.w _⟩, fun X => ⟨inst✝¹.1 X, inst✝¹.2.1.1 X, this.comm,'): <stdin>:1:21: expected token

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 195.8s, verify 0.1s, in=834, out=7817)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk';
[ exact this, infer_instance ]
```

**lean_error:** tail step 1/2 ("apply IsLocalizedEquivalence.mk';"): <stdin>:1:32: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 228.9s, verify 0.1s, in=834, out=9028)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk' inferInstance inferInstance
```

**lean_error:** tail step 1/1 ("apply IsLocalizedEquivalence.mk' inferInstance inferInstance"): type class instance expected

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 230.4s, verify 0.1s, in=834, out=9087)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("apply IsLocalizedEquivalence.mk'"): failed to synthesize

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 235.4s, verify 0.1s, in=834, out=9284)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk' this inferInstance
```

**lean_error:** tail step 1/1 ("apply IsLocalizedEquivalence.mk' this inferInstance"): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=834, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=834, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=834, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.3s, verify 0.1s, in=834, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' this (inferInstance : IsEquivalence G)
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' this (inferInstance : IsEquivalence G)"): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.0s, verify 0.1s, in=834, out=268)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' this inferInstance
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' this inferInstance"): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 9.9s, verify 0.1s, in=834, out=285)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.4s, verify 0.1s, in=834, out=305)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Φ.IsLocalizedEquivalence.mk' (Functor.isEquivalence_id _)
```

**lean_error:** tail step 1/1 ("exact Φ.IsLocalizedEquivalence.mk' (Functor.isEquivalence_id _)"): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.2s, verify 0.1s, in=834, out=331)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact mk' this (IsEquivalence.refl _)
```

**lean_error:** tail step 1/1 ("exact mk' this (IsEquivalence.refl _)"): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 321.1s, verify 0.1s, in=2125, out=8160)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("apply IsLocalizedEquivalence.mk'"): failed to synthesize

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 368.4s, verify 0.1s, in=2125, out=8378)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk'
inferInstance
inferInstance
```

**lean_error:** tail step 1/3 ("apply IsLocalizedEquivalence.mk'"): failed to synthesize

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 399.2s, verify 0.1s, in=2125, out=9613)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("apply IsLocalizedEquivalence.mk'"): failed to synthesize

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 402.2s, verify 0.1s, in=2125, out=9686)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk' (Φ.localizedFunctor L₁ L₂)
· apply CatCommSq.mk (liftCompIso L₁ (Φ.localizedFunctor L₁ L₂)).symm
· inferInstance
```

**lean_error:** tail step 1/3 ("apply IsLocalizedEquivalence.mk' (Φ.localizedFunctor L₁ L₂)"): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.6s, in=2125, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' this inferInstance
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' this inferInstance"): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=2125, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' this inferInstance
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' this inferInstance"): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.4s, verify 0.1s, in=2125, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=2125, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' this inferInstance
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' this inferInstance"): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 11.7s, verify 0.1s, in=2125, out=145)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' (inst := inferInstance)
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' (inst := inferInstance)"): invalid argument name 'inst' for function 'CategoryTheory.LocalizerMorphism.IsLocalizedEquivalence.mk''

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 13.1s, verify 0.1s, in=2125, out=225)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' this inferInstance
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' this inferInstance"): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 14.2s, verify 0.1s, in=2125, out=189)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 16.0s, verify 0.1s, in=2125, out=286)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' (this := this) inferInstance
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' (this := this) inferInstance"): type class instance expected

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 166.3s, verify 0.1s, in=2157, out=6728)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("apply IsLocalizedEquivalence.mk'"): failed to synthesize

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 172.9s, verify 0.1s, in=2157, out=6974)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk' this inferInstance
```

**lean_error:** tail step 1/1 ("apply IsLocalizedEquivalence.mk' this inferInstance"): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 178.2s, verify 0.1s, in=2157, out=7178)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("apply IsLocalizedEquivalence.mk'"): failed to synthesize

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 216.1s, verify 0.1s, in=2157, out=8565)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsLocalizedEquivalence.mk' with G := 𝟭 D₂
exact this
infer_instance
```

**lean_error:** tail step 1/3 ("apply IsLocalizedEquivalence.mk' with G := 𝟭 D₂"): <stdin>:1:33: expected end of input

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=2157, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=2157, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.5s, verify 0.1s, in=2157, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' this (inferInstance : IsEquivalence G)
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' this (inferInstance : IsEquivalence G)"): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.7s, verify 0.2s, in=2157, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' this
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' this"): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.0s, verify 0.1s, in=2157, out=173)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=2157, out=200)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk'
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.7s, verify 0.1s, in=2157, out=221)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact mk'
```

**lean_error:** tail step 1/1 ("exact mk'"): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.2s, verify 0.1s, in=2157, out=367)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsLocalizedEquivalence.mk' this (inferInstance : IsEquivalence (𝟭 D₂))
```

**lean_error:** tail step 1/1 ("exact IsLocalizedEquivalence.mk' this (inferInstance : IsEquivalence (𝟭 D₂))"): application type mismatch
