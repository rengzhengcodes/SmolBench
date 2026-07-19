# LinearMap.span_inl_union_inr   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [span_union, prod_eq_sup_map, ← span_image, ← span_image]
```

**True premises at k:** `Submodule.span_union`, `LinearMap.prod_eq_sup_map`, `Submodule.span_image`, `Submodule.span_image`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ · ✘ | · · ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ · ✓ ✘ | ✓ ✓ ✓ ✘ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ · ✓ ✓ | ✓ ✓ ✓ ✘ |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ · ✓ ✘ | ✓ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 94.4s, verify 0.2s, in=435, out=3699)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [span_union, map_span, map_span, Submodule.prod_eq_map_inl_sup_map_inr]
```

**lean_error:** tail step 1/1 ('rw [span_union, map_span, map_span, Submodule.prod_eq_map_inl_sup_map_inr]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 114.4s, verify 0.3s, in=435, out=4447)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [span_union]
rw [LinearMap.span_image_eq_map_span (LinearMap.inl R M M₂) s]
rw [LinearMap.span_image_eq_map_span (LinearMap.inr R M M₂) t]
rw [Submodule.prod_eq_sup_inl_inr (span R s) (span R t)]
```

**lean_error:** tail step 2/4 ('rw [LinearMap.span_image_eq_map_span (LinearMap.inl R M M₂) s]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 184.2s, verify 0.3s, in=435, out=7249)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
span_le.2 (by rintro z (⟨x, xs, rfl⟩ | ⟨y, yt, rfl⟩); exact ⟨subset_span xs, zero_mem _⟩ ∨ ⟨zero_mem _, subset_span yt⟩)
rintro ⟨x, y⟩ ⟨hx, hy⟩
have hx' : (x, 0) ∈ span R (inl R M M₂ '' s ∪ inr R M M₂ '' t) := Submodule.span_induction hx (λ a as, subset_span (Or.inl ⟨a, as, rfl⟩)) (zero_mem _) (λ a b ha hb, ha + hb) (λ r a ha, smul_mem _ _ ha)
have hy' : (0, y) ∈ _ := Submodule.span_induction hy (λ b bt, subset_span (Or.inr ⟨b, bt, rfl⟩)) (zero_mem _) (λ a b ha hb, ha + hb) (λ r a ha, smul_mem _ _ ha)
exact hx' + hy'
```

**lean_error:** tail step 2/6 ('span_le.2 (by rintro z (⟨x, xs, rfl⟩ | ⟨y, yt, rfl⟩); exact ⟨subset_span xs, zero_mem _⟩ ∨ ⟨zero_mem _, subset_span yt⟩)'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 199.5s, verify 0.3s, in=435, out=7909)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext p
split
· intro hp
  apply Submodule.mem_prod.2
  apply Submodule.span_induction hp
  · intro z hz
    cases hz with
    | inl hz1 => rcases hz1 with ⟨x, xs, rfl⟩
      exact ⟨Submodule.mem_span_self R xs, Submodule.zero_mem _⟩
    | inr hz2 => rcases hz2 with ⟨y, yt, rfl⟩
      exact ⟨Submodule.zero_mem _, Submodule.mem_span_self R yt⟩
  · rintro ⟨a, b⟩; rfl
  · intros a b ha hb; rcases ha with ⟨ha1, ha2⟩; rcases hb with ⟨hb1, hb2⟩
    exact ⟨Submodule.add_mem _ ha1 hb1, Submodule.add_mem _ ha2 hb2⟩
  · intros c a ha; rcases ha with ⟨ha1, ha2⟩
    exact ⟨Submodule.smul_mem _ c ha1, Submodule.smul_mem _ c ha2⟩
· intro hp
  have h1 : (p.1, 0) ∈ span R (inl R M M₂ '' s) := by
    rw Submodule.span_inl_image R M M₂ s
    exact hp.1
  have h2 : (0, p.2) ∈ span R (inr R M M₂ '' t) := by
    rw Submodule.span_inr_image R M M₂ t
    exact hp.2
  exact Submodule.add_mem _ h1 h2
```

**lean_error:** tail step 2/24 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.2s, in=435, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [span_union, inl_span_image_eq, inr_span_image_eq]
```

**lean_error:** tail step 1/1 ('rw [span_union, inl_span_image_eq, inr_span_image_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=435, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Submodule.span_union, Submodule.span_image, Submodule.span_inl_union_inr]
```

**lean_error:** tail step 1/1 ('simp only [Submodule.span_union, Submodule.span_image, Submodule.span_inl_union_inr]'): unknown constant 'Submodule.span_inl_union_inr'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.4s, verify 0.5s, in=435, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.span_union, Submodule.span_image, Submodule.span_eq_closure, Set.image_union]
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.6s, verify 0.1s, in=435, out=60)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [union_eq_range_sum, ← inl_union_inr_eq_range_sum, span_range_eq_map, sum_eq_prod,
  LinearEquiv.prod_map_apply, ← inl_union_inr_eq_range_sum, union_eq_range_sum, LinearEquiv.map_prod]
```

**lean_error:** tail step 1/2 ('rw [union_eq_range_sum, ← inl_union_inr_eq_range_sum, span_range_eq_map, sum_eq_prod,'): <stdin>:1:85: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 4.7s, verify 0.1s, in=435, out=138)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [span_inl_union_inr]
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 6.5s, verify 0.1s, in=435, out=171)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [span_inl_union_inr]
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.7s, verify 0.2s, in=435, out=230)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Submodule.span_eq_prod]
```

**lean_error:** tail step 1/1 ('rw [Submodule.span_eq_prod]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.3s, verify 0.1s, in=435, out=448)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [span_union, Submodule.map_span, Submodule.map_span, Submodule.map_inl_eq_prod_span,
  Submodule.map_inr_eq_prod_bot, Submodule.prod_sup_prod, sup_bot_eq, bot_sup_eq]
```

**lean_error:** tail step 1/2 ('rw [span_union, Submodule.map_span, Submodule.map_span, Submodule.map_inl_eq_prod_span,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 41.0s, verify 0.1s, in=1083, out=1689)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Submodule.span_union, Submodule.span_image, Submodule.span_image, LinearMap.prod_eq_sup_map]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 64.3s, verify 0.1s, in=1083, out=2598)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union, Submodule.span_image, Submodule.span_image, LinearMap.prod_eq_sup_map]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 67.0s, verify 0.1s, in=1083, out=2702)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Submodule.span_union, Submodule.span_image, Submodule.span_image, LinearMap.prod_eq_sup_map]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 86.0s, verify 0.1s, in=1083, out=3400)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union, Submodule.span_image, Submodule.span_image, prod_eq_sup_map]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.0s, verify 0.1s, in=1083, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, LinearMap.prod_eq_sup_map]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.1s, verify 0.2s, in=1083, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Submodule.span_union, LinearMap.prod_eq_sup_map, Submodule.span_image]
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.3s, verify 0.1s, in=1083, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union, LinearMap.prod_eq_sup_map, Submodule.span_image, Submodule.span_image]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=1083, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← LinearMap.prod_eq_sup_map, Submodule.span_image, Submodule.span_image,
  Submodule.span_union, Submodule.span_image]
```

**lean_error:** tail step 1/2 ('rw [← LinearMap.prod_eq_sup_map, Submodule.span_image, Submodule.span_image,'): <stdin>:1:76: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.1s, verify 0.1s, in=1083, out=247)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.3s, verify 0.1s, in=1083, out=251)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, LinearMap.prod_eq_sup_map]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.5s, verify 0.1s, in=1083, out=245)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Submodule.span_union, Submodule.span_image, Submodule.span_image, LinearMap.prod_eq_sup_map]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.6s, verify 0.1s, in=1083, out=263)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union, ← span_image (inl R M M₂) s, ← span_image (inr R M M₂) t,
  LinearMap.prod_eq_sup_map]
```

**lean_error:** tail step 1/2 ('rw [span_union, ← span_image (inl R M M₂) s, ← span_image (inr R M M₂) t,'): <stdin>:1:73: unexpected end of input; expected ']'

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 103.2s, verify 0.5s, in=1865, out=1176)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union]
rw [Submodule.span_image (LinearMap.inl R M M₂)]
rw [Submodule.span_image (LinearMap.inr R M M₂)]
rw [LinearMap.prod_eq_sup_map]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 123.1s, verify 0.1s, in=1865, out=2667)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 147.5s, verify 0.1s, in=1865, out=4099)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, ← prod_eq_sup_map]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 182.8s, verify 0.1s, in=1865, out=4580)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 3.2s, verify 0.1s, in=1865, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union, prod_eq_sup_map, span_image, span_image]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 3.3s, verify 0.2s, in=1865, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Submodule.span_union, LinearMap.prod_eq_sup_map, Submodule.span_image]
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.5s, verify 0.1s, in=1865, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union, LinearMap.prod_eq_sup_map, Submodule.span_image, Submodule.span_image]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.6s, verify 0.1s, in=1865, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union, LinearMap.prod_eq_sup_map, Submodule.span_image, Submodule.span_image]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 11.7s, verify 0.1s, in=1865, out=179)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union, LinearMap.prod_eq_sup_map, Submodule.span_image, Submodule.span_image]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 11.9s, verify 0.3s, in=1865, out=245)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Submodule.span_union, Submodule.span_image, Submodule.span_image, LinearMap.prod_eq_sup_map]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 12.3s, verify 0.1s, in=1865, out=199)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 16.2s, verify 0.1s, in=1865, out=325)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Submodule.span_union, Submodule.span_image, Submodule.span_image,
  LinearMap.prod_eq_sup_map (span R s) (span R t)]
```

**lean_error:** tail step 1/2 ('rw [Submodule.span_union, Submodule.span_image, Submodule.span_image,'): <stdin>:1:69: unexpected end of input; expected ']'

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 52.6s, verify 0.1s, in=1889, out=2146)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, Submodule.span_image, Submodule.span_image, LinearMap.prod_eq_sup_map]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 74.2s, verify 0.1s, in=1889, out=2970)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, Submodule.span_image (LinearMap.inl R M M₂), Submodule.span_image (LinearMap.inr R M M₂), prod_eq_sup_map]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 82.7s, verify 0.1s, in=1889, out=3282)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, Submodule.span_image (LinearMap.inl R M M₂), Submodule.span_image (LinearMap.inr R M M₂), LinearMap.prod_eq_sup_map]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 172.9s, verify 0.1s, in=1889, out=6780)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, ← LinearMap.prod_eq_sup_map]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=1889, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.8s, verify 0.2s, in=1889, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Submodule.span_union, LinearMap.prod_eq_sup_map, Submodule.span_image]
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.9s, verify 0.1s, in=1889, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, LinearMap.prod_eq_sup_map, span_image, span_image]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.9s, verify 0.2s, in=1889, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, ← LinearMap.prod_eq_sup_map, Submodule.span_image, Submodule.span_image]
```

**lean_error:** tail step 1/1 ('rw [span_union, ← LinearMap.prod_eq_sup_map, Submodule.span_image, Submodule.span_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 6.8s, verify 0.1s, in=1889, out=205)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, prod_eq_sup_map]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.4s, verify 0.1s, in=1889, out=223)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Submodule.span_union, Submodule.span_image, Submodule.span_image, LinearMap.prod_eq_sup_map]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.8s, verify 0.1s, in=1889, out=271)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Submodule.span_union, Submodule.span_image, Submodule.span_image, LinearMap.prod_eq_sup_map]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 11.1s, verify 0.1s, in=1889, out=358)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [span_union, span_image, span_image] using LinearMap.prod_eq_sup_map _ _
```

**lean_error:** tail step 1/1 ('simpa only [span_union, span_image, span_image] using LinearMap.prod_eq_sup_map _ _'): typeclass instance problem is stuck, it is often due to metavariables
