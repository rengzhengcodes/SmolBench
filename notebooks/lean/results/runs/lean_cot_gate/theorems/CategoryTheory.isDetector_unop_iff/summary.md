# CategoryTheory.isDetector_unop_iff   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Generator.lean`  

**Ground-truth tail (from k):**
```lean
rw [IsDetector, IsCodetector, ← isDetecting_unop_iff, Set.singleton_unop]
```

**True premises at k:** `CategoryTheory.IsDetector`, `CategoryTheory.IsCodetector`, `CategoryTheory.isDetecting_unop_iff`, `Set.singleton_unop`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ · · · | ✘ · ✘ · |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ · |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | · ✘ · ✘ |
| `noise:3` | ✘ ✘ ✘ ✓ | ✘ ✘ ✘ ✘ | ✘ ✓ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 72.5s, verify 0.1s, in=237, out=2871)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (IsDetector.unop_iff_isCodetector G).symm
```

**lean_error:** tail step 1/1 ('exact (IsDetector.unop_iff_isCodetector G).symm'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 106.1s, verify 0.1s, in=237, out=4128)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
trivial
```

**lean_error:** tail step 1/1 ('trivial'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 267.9s, verify 0.2s, in=237, out=10960)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.intro
· rintro ⟨h⟩ X Y f g ne
  have := h Y X f g ne
  rcases this with ⟨h', hh⟩
  exact ⟨h', hh⟩
· rintro ⟨h⟩ A B f g ne
  have := h B A f g ne
  rcases this with ⟨k, hk⟩
  exact ⟨k, hk⟩
```

**lean_error:** tail step 2/9 ('· rintro ⟨h⟩ X Y f g ne'): rcases tactic failed: a✝ : ∀ ⦃X Y : C⦄ (f : X ⟶ Y),

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 284.1s, verify 0.1s, in=237, out=11697)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro h
  constructor
  intros X Y f g ne
  have : f.unop ≠ g.unop := fun h' ↦ ne (by rw [←op_inj, h', op_op])
  obtain ⟨k, hk⟩ := h (f.unop) (g.unop) this
  use k.op
  exact hk
· intro h
  constructor
  intros X Y f g ne
  have : f.op ≠ g.op := fun h' ↦ ne (by rw [←unop_inj, h', unop_op])
  obtain ⟨k, hk⟩ := h Y X f.op g.op this
  use k.unop
  exact hk
```

**lean_error:** tail step 1/15 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.6s, verify 0.1s, in=237, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.4s, verify 0.1s, in=237, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetecting {G.unop} ↔ IsCodetecting {G}
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.5s, verify 0.1s, in=237, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetecting {G.unop} ↔ IsCodetecting {G}
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.6s, verify 0.1s, in=237, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsCodetector, IsDetector]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetecting {G.unop} ↔ IsCodetecting {G}
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=237, out=173)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 7.8s, verify 0.1s, in=237, out=230)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetecting {G.unop} ↔ IsCodetecting {G}
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.8s, verify 0.1s, in=237, out=229)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact isDetector_iff_isCodetector_op G.unop
```

**lean_error:** tail step 1/1 ('exact isDetector_iff_isCodetector_op G.unop'): unknown identifier 'isDetector_iff_isCodetector_op'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 7.9s, verify 0.1s, in=237, out=231)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetecting {G.unop} ↔ IsCodetecting {G}
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 54.9s, verify 0.1s, in=826, out=2179)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← isDetecting_unop_iff {G}, singleton_unop]
```

**lean_error:** tail step 1/1 ('rw [← isDetecting_unop_iff {G}, singleton_unop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 68.0s, verify 0.1s, in=826, out=2697)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isDetecting_unop_iff {G}
```

**lean_error:** tail step 1/1 ('exact isDetecting_unop_iff {G}'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 69.1s, verify 0.1s, in=826, out=2698)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isDetecting_unop_iff {G}
```

**lean_error:** tail step 1/1 ('exact isDetecting_unop_iff {G}'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 249.0s, verify 0.1s, in=826, out=10121)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply isDetecting_unop_iff ({G} : Set Cᵒᵖ)
```

**lean_error:** tail step 1/1 ('apply isDetecting_unop_iff ({G} : Set Cᵒᵖ)'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=826, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('simp [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]'): unknown identifier 'singleton_unop'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=826, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('simp [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]'): unknown identifier 'singleton_unop'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.9s, verify 0.1s, in=826, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]
```

**lean_error:** tail step 1/1 ('simp [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]'): unknown identifier 'singleton_unop'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=826, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]
```

**lean_error:** tail step 1/1 ('simp only [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]'): unknown identifier 'singleton_unop'

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.0s, verify 0.1s, in=826, out=273)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('simp [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]'): unknown identifier 'singleton_unop'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.3s, verify 0.1s, in=826, out=309)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('rw [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.9s, verify 0.1s, in=826, out=396)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [isDetecting_unop_iff, singleton_unop, IsDetector, IsCodetector]
```

**lean_error:** tail step 1/1 ('simp [isDetecting_unop_iff, singleton_unop, IsDetector, IsCodetector]'): unknown identifier 'singleton_unop'

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 13.7s, verify 0.1s, in=826, out=422)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetecting {G.unop} ↔ IsCodetecting {G}
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 120.6s, verify 0.1s, in=1538, out=1773)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, isDetecting_unop_iff]
```

**lean_error:** tail step 1/1 ('rw [IsDetector, IsCodetector, isDetecting_unop_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 221.7s, verify 0.2s, in=1538, out=6157)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector]
exact isDetecting_unop_iff {G}
```

**lean_error:** tail step 2/2 ('exact isDetecting_unop_iff {G}'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 231.8s, verify 0.1s, in=1538, out=7126)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isDetector, isCodetector]
apply isDetecting_unop_iff
```

**lean_error:** tail step 1/2 ('rw [isDetector, isCodetector]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 336.7s, verify 0.2s, in=1538, out=11248)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector]
rw [← singleton_unop G]
rw [isDetecting_unop_iff]
```

**lean_error:** tail step 2/3 ('rw [← singleton_unop G]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=1538, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('simp only [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]'): unknown identifier 'singleton_unop'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=1538, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]
```

**lean_error:** tail step 1/1 ('rw [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.5s, verify 0.1s, in=1538, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]
```

**lean_error:** tail step 1/1 ('rw [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.6s, verify 0.1s, in=1538, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]
```

**lean_error:** tail step 1/1 ('simp_rw [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]'): unknown identifier 'singleton_unop'

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 16.7s, verify 0.1s, in=1538, out=286)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetecting {G.unop} ↔ IsCodetecting {G}
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 16.8s, verify 0.1s, in=1538, out=345)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('simp [isDetecting_unop_iff, singleton_unop]'): unknown identifier 'singleton_unop'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 19.4s, verify 0.1s, in=1538, out=378)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetecting {G.unop} ↔ IsCodetecting {G}
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 21.4s, verify 0.1s, in=1538, out=451)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← IsDetector, ← IsCodetector, isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('rw [← IsDetector, ← IsCodetector, isDetecting_unop_iff, singleton_unop]'): failed to rewrite using equation theorems for 'CategoryTheory.IsDetector'

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 84.6s, verify 0.1s, in=1578, out=3336)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isDetecting_unop_iff]
```

**lean_error:** tail step 1/1 ('rw [isDetecting_unop_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 162.9s, verify 0.1s, in=1578, out=6314)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isDetecting_unop_iff {G}]
```

**lean_error:** tail step 1/1 ('rw [isDetecting_unop_iff {G}]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 195.2s, verify 0.2s, in=1578, out=7664)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector]
apply isDetecting_unop_iff
```

**lean_error:** tail step 2/2 ('apply isDetecting_unop_iff'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 246.7s, verify 0.2s, in=1578, out=10007)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector]
rw [← isDetecting_unop_iff (𝒢 := {G})]
simp [Set.singleton_unop]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1578, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('simp only [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]'): unknown identifier 'singleton_unop'

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=1578, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]
```

**lean_error:** tail step 1/1 ('rw [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.1s, verify 0.1s, in=1578, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('simp [IsDetector, IsCodetector, isDetecting_unop_iff, singleton_unop]'): unknown identifier 'singleton_unop'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=1578, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]
```

**lean_error:** tail step 1/1 ('simp only [IsDetector, IsCodetector, ← singleton_unop, isDetecting_unop_iff]'): unknown identifier 'singleton_unop'

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.8s, verify 0.1s, in=1578, out=289)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]
```

**lean_error:** tail step 1/1 ('rw [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 10.4s, verify 0.1s, in=1578, out=312)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [IsDetector, IsCodetector] using isDetecting_unop_iff {G}
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.7s, verify 0.1s, in=1578, out=385)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isDetector, isCodetector, isDetecting_unop_iff, singleton_unop]
```

**lean_error:** tail step 1/1 ('rw [isDetector, isCodetector, isDetecting_unop_iff, singleton_unop]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.2s, verify 0.1s, in=1578, out=402)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]
```

**lean_error:** tail step 1/1 ('rw [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
