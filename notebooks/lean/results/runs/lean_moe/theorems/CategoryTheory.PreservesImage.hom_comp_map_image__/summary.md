# CategoryTheory.PreservesImage.hom_comp_map_image_ι   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Preserves/Shapes/Images.lean`  

**Ground-truth tail (from k):**
```lean
rw [iso_hom, image.lift_fac]
```

**True premises at k:** `CategoryTheory.PreservesImage.iso_hom`, `CategoryTheory.Limits.image.lift_fac`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=477, out=1090)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (PreservesImage.iso_hom_ι (L:=L) (f:=f))
```

**lean_error:** tail step 1/1 ('simpa using (PreservesImage.iso_hom_ι (L:=L) (f:=f))'): unknown identifier 'PreservesImage.iso_hom_ι'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 276.5s, verify 0.1s, in=424, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
L.(image.π f) → L.(image f)
↓             ↓
image.π (L.f) → image (L.f)
```

**lean_error:** tail step 1/3 ('L.(image.π f) → L.(image f)'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.9s, verify 0.2s, in=415, out=601)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [iso]
```

**final state (truncated):**
```
A : Type u₁
B : Type u₂
inst✝⁷ : Category.{v₁, u₁} A
inst✝⁶ : Category.{v₂, u₂} B
inst✝⁵ : HasEqualizers A
inst✝⁴ : HasImages A
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.9s, verify 0.1s, in=770, out=1317)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [PreservesImage.iso_hom] using (image.lift_fac _)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 106.7s, verify 0.3s, in=742, out=12304)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply CategoryTheory.PreservesImage.iso_hom
<;> simp_all [CategoryTheory.Limits.image.lift_fac]
<;> try aesop
```

**lean_error:** tail step 1/3 ('apply CategoryTheory.PreservesImage.iso_hom'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.4s, in=703, out=624)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iso_hom]
rw [lift_fac]
```

**lean_error:** tail step 2/2 ('rw [lift_fac]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=1032, out=865)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [PreservesImage.iso_hom] using
  (image.lift_fac (PreservesImage.imageMonoFactorisation (L:=L) (f:=f)))
```

**lean_error:** tail step 1/2 ('simpa [PreservesImage.iso_hom] using'): <stdin>:1:36: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 177.8s, verify 0.1s, in=1012, out=20532)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₂ : True := by
  have h₃ : image.lift (image.factor f) ≫ image.ι f = f := by
    apply image.lift_fac
  exact trivial
have h₁ : (iso L f).hom ≫ L.map (image.ι f) = image.ι (L.map f) := by
  apply CategoryTheory.PreservesImage.iso_hom
exact h₁
```

**lean_error:** tail step 1/7 ('have h₂ : True := by'): <stdin>:1:20: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.6s, verify 0.2s, in=968, out=568)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [PreservesImage.iso, image.lift_fac]
```

**final state (truncated):**
```
A : Type u₁
B : Type u₂
inst✝⁷ : Category.{v₁, u₁} A
inst✝⁶ : Category.{v₂, u₂} B
inst✝⁵ : HasEqualizers A
inst✝⁴ : HasImages A
...
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.1s, in=1025, out=697)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (PreservesImage.iso_hom (L:=L) (f:=f))
```

**lean_error:** tail step 1/1 ('simpa using (PreservesImage.iso_hom (L:=L) (f:=f))'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 253.9s, verify 0.2s, in=1071, out=29664)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : Mono (L.map (image.ι f)) := by sorry
have h₂ : ∃ (e' : L.X ⟶ L.(image f)), L.map f = L.map (image.ι f) ∘ e' := by sorry
obtain ⟨e', h₂'⟩ := h₂
have h₃ : ∃ (F' : MonoFactorisation (L.map f)), F'.m = L.map (image.ι f) := by sorry
obtain ⟨F', hF'⟩ := h₃
have h₄ : image.lift F' ≫ F'.m = image.ι (L.map f) := by sorry
have h₅ : (iso L f).hom = image.lift F' := by sorry
have h₆ : (iso L f).hom ≫ L.map (image.ι f) = image.ι (L.map f) := by sorry
exact h₆
```

**lean_error:** tail step 2/9 ("have h₂ : ∃ (e' : L.X ⟶ L.(image f)), L.map f = L.map (image.ι f) ∘ e' := by sorry"): <stdin>:1:25: expected ')'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.2s, in=983, out=614)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [image.lift_fac]
simp [iso_hom]
category.assoc
```

**lean_error:** tail step 1/3 ('rw [image.lift_fac]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
