# CategoryTheory.adhesive_of_preserves_and_reflects_isomorphism   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Adhesive.lean`  

**Ground-truth tail (from k):**
```lean
exact adhesive_of_preserves_and_reflects F
```

**True premises at k:** `CategoryTheory.adhesive_of_preserves_and_reflects`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=444, out=674)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact inferInstance
```

**lean_error:** tail step 1/1 ('exact inferInstance'): failed to synthesize instance

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 267.5s, verify 0.1s, in=400, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h_proj1 : (F.map f).kernelPair.π₁ = F.map (f.kernelPair.π₁) := by sorry
have h_proj2 : (F.map f).kernelPair.π₂ = F.map (f.kernelPair.π₂) := by sorry
```

**lean_error:** tail step 1/2 ('have h_proj1 : (F.map f).kernelPair.π₁ = F.map (f.kernelPair.π₁) := by sorry'): internal exception #7

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=385, out=459)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Adhesive.of_reflects F
```

**lean_error:** tail step 1/1 ('exact Adhesive.of_reflects F'): unknown constant 'CategoryTheory.Adhesive.of_reflects'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.2s, verify 0.1s, in=1138, out=440)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects (F:=F)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 19.3s, verify 0.1s, in=1125, out=2623)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
haveI : ∀ {X Y S : C} (f : X ⟶ S) (g : Y ⟶ S) [Mono f], HasPullback f g := by
  intro X Y S f g hf
  exact HasPullbacks.hasPullback f g

haveI : ∀ {X Y S : C} (f : S ⟶ X) (g : S ⟶ Y) [Mono f], HasPushout f g := by
  intro X Y S f g hf
  exact HasPushouts.hasPushout f g

apply CategoryTheory.adhesive_of_preserves_and_reflects
```

**lean_error:** tail step 1/7 ('haveI : ∀ {X Y S : C} (f : X ⟶ S) (g : Y ⟶ S) [Mono f], HasPullback f g := by'): <stdin>:1:77: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 77.2s, verify 0.1s, in=1065, out=8021)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.4s, verify 0.1s, in=3140, out=530)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects (F:=F)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 37.1s, verify 0.1s, in=3155, out=5000)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : ∀ {X Y S : C} (f : X ⟶ S) (g : Y ⟶ S) [Mono f], HasPullback f g := by
  intro X Y S f g hf
  exact inst✝⁴.hasPullback f g
have h₂ : ∀ {X Y S : C} (f : S ⟶ X) (g : S ⟶ Y) [Mono f], HasPushout f g := by
  intro X Y S f g hf
  exact inst✝³.hasPushout f g
exact CategoryTheory.adhesive_of_preserves_and_reflects F h₁ h₂
```

**lean_error:** tail step 1/7 ('have h₁ : ∀ {X Y S : C} (f : X ⟶ S) (g : Y ⟶ S) [Mono f], HasPullback f g := by'): <stdin>:1:79: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.7s, verify 0.1s, in=3017, out=681)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects F
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.1s, verify 0.1s, in=2880, out=422)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects (F := F)
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 36.9s, verify 0.1s, in=3402, out=4942)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have H₁ : ∀ {X Y S : C} (f : X ⟶ S) (g : Y ⟶ S) [Mono f], HasPullback f g := by
  intro X Y S f g hf
  exact HasPullbacks.hasPullback f g
have H₂ : ∀ {X Y S : C} (f : S ⟶ X) (g : S ⟶ Y) [Mono f], HasPushout f g := by
  intro X Y S f g hf
  exact HasPushouts.hasPushout f g
apply adhesive_of_preserves_and_reflects
<;> assumption
```

**lean_error:** tail step 1/8 ('have H₁ : ∀ {X Y S : C} (f : X ⟶ S) (g : Y ⟶ S) [Mono f], HasPullback f g := by'): <stdin>:1:79: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.2s, verify 0.1s, in=3004, out=681)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects F
```
