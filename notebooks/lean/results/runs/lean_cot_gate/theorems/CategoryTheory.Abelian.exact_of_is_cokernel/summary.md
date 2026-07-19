# CategoryTheory.Abelian.exact_of_is_cokernel   (k=3, 4 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Exact.lean`  

**Ground-truth tail (from k):**
```lean
rw [← this, ← Category.assoc, kernel.condition, zero_comp]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Limits.kernel.condition`, `CategoryTheory.Limits.zero_comp`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✓ ✘ ✓ | · ✘ ✘ ✘ |
| `hint:2` | ✘ ✓ ✘ ✓ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✓ ✓ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 55.0s, verify 0.2s, in=310, out=2237)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [this, assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [this, assoc, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 70.9s, verify 0.2s, in=310, out=2859)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [this]
rw [←comp_assoc]
rw [kernel.condition]
rw [zero_comp]
```

**lean_error:** tail step 1/4 ('rw [this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 85.3s, verify 0.2s, in=310, out=3514)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [this, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [this, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 158.2s, verify 0.1s, in=310, out=6510)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← this, category.assoc, kernel.condition], rw zero_comp, trivial
```

**lean_error:** tail step 1/1 ('rw [← this, category.assoc, kernel.condition], rw zero_comp, trivial'): <stdin>:1:45: expected end of input

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=310, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.7s, verify 0.1s, in=310, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← this]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=310, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.7s, verify 0.1s, in=310, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← this]
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 9.3s, verify 0.1s, in=310, out=296)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← this]
```

**final state (truncated):**
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
inst✝ : Abelian C
X Y Z : C
f : X ⟶ Y
g : Y ⟶ Z
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.4s, verify 0.1s, in=310, out=329)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← comp_assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← comp_assoc, kernel.condition, zero_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.1s, verify 0.2s, in=310, out=353)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← this, Category.assoc, Category.comp_zero]
```

**lean_error:** tail step 1/1 ('rw [← this, Category.assoc, Category.comp_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 14.5s, verify 0.1s, in=310, out=474)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [kernel.lift]
```

**lean_error:** tail step 1/1 ('simp [kernel.lift]'): simp made no progress

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 54.8s, verify 0.2s, in=775, out=2231)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [this]
simp only [Category.assoc]
rw [kernel.condition]
simp only [zero_comp]
```

**lean_error:** tail step 1/4 ('rw [this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 79.5s, verify 0.1s, in=775, out=3253)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← this, ← CategoryTheory.Category.assoc, kernel.condition, zero_comp]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 95.2s, verify 0.2s, in=775, out=3948)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [this, ←assoc, kernel.condition, zero_comp]
trivial
```

**lean_error:** tail step 1/2 ('rw [this, ←assoc, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 130.0s, verify 0.2s, in=775, out=5416)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← this]
simp [Category.assoc, kernel.condition, zero_comp]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=775, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [← Category.assoc, this, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [← Category.assoc, this, kernel.condition, zero_comp]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=775, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [this]
```

**lean_error:** tail step 1/1 ('simp [this]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=775, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [Category.assoc, kernel.condition, zero_comp]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=775, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [← Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [← Category.assoc, kernel.condition, zero_comp]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.7s, verify 0.1s, in=775, out=239)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, CategoryTheory.Limits.kernel.condition,
  CategoryTheory.Limits.zero_comp] at this
```

**lean_error:** tail step 1/2 ('simp only [CategoryTheory.Category.assoc, CategoryTheory.Limits.kernel.condition,'): <stdin>:1:81: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 7.8s, verify 0.1s, in=775, out=238)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [CategoryTheory.Category.assoc, kernel.condition, zero_comp]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 8.3s, verify 0.1s, in=775, out=260)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [← Category.assoc, this, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp_rw [← Category.assoc, this, kernel.condition, zero_comp]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 12.6s, verify 0.1s, in=775, out=405)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa only [CategoryTheory.Category.assoc, kernel.condition, zero_comp] using
  ← this
```

**lean_error:** tail step 1/2 ('simpa only [CategoryTheory.Category.assoc, kernel.condition, zero_comp] using'): <stdin>:1:77: unexpected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 117.5s, verify 0.2s, in=1144, out=2664)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [this]
rw [Category.assoc]
rw [kernel.condition]
rw [zero_comp]
```

**lean_error:** tail step 1/4 ('rw [this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 120.3s, verify 0.2s, in=1144, out=2779)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [this, CategoryTheory.Category.assoc, CategoryTheory.Limits.kernel.condition, CategoryTheory.Limits.zero_comp]
```

**lean_error:** tail step 1/1 ('rw [this, CategoryTheory.Category.assoc, CategoryTheory.Limits.kernel.condition, CategoryTheory.Limits.zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 137.6s, verify 0.1s, in=1144, out=3039)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← this, ← Category.assoc, kernel.condition, zero_comp]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 160.1s, verify 0.1s, in=1144, out=4537)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← this, ← Category.assoc, kernel.condition, zero_comp]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=1144, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [this]
```

**lean_error:** tail step 1/1 ('simp [this]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1144, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [this, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [this, kernel.condition, zero_comp]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=1144, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [Category.assoc, kernel.condition, zero_comp]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.7s, in=1144, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [← Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [← Category.assoc, kernel.condition, zero_comp]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 15.9s, verify 0.1s, in=1144, out=282)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [CategoryTheory.Category.assoc, kernel.condition, zero_comp]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 17.3s, verify 0.1s, in=1144, out=358)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [assoc, kernel.condition, zero_comp]'): unknown identifier 'assoc'

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 19.6s, verify 0.1s, in=1144, out=432)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, CategoryTheory.Limits.kernel.condition, CategoryTheory.Limits.zero_comp] at this
```

**lean_error:** tail step 1/1 ('simp only [CategoryTheory.Category.assoc, CategoryTheory.Limits.kernel.condition, CategoryTheory.Limits.zero_comp] at this'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 23.9s, verify 0.2s, in=1144, out=628)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Category.assoc, ← this, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← Category.assoc, ← this, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 50.5s, verify 0.2s, in=1168, out=2062)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [←Category.assoc]
rw [kernel.condition]
rw [zero_comp]
```

**lean_error:** tail step 1/3 ('rw [←Category.assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 66.0s, verify 0.1s, in=1168, out=2672)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw this
rw [CategoryTheory.Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/2 ('rw this'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 68.2s, verify 0.2s, in=1168, out=2756)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [this, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [this, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 71.3s, verify 0.2s, in=1168, out=2878)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [this, Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [this, Category.assoc, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=1168, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [this]
```

**lean_error:** tail step 1/1 ('simp [this]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=1168, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [← Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [← Category.assoc, kernel.condition, zero_comp]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1168, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [← Category.assoc, this, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [← Category.assoc, this, kernel.condition, zero_comp]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.1s, in=1168, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [Category.assoc, kernel.condition, zero_comp]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.1s, verify 0.1s, in=1168, out=217)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [← Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [← Category.assoc, kernel.condition, zero_comp]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.8s, verify 0.1s, in=1168, out=242)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← Category.assoc, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.9s, verify 0.2s, in=1168, out=348)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [kernel.condition, CategoryTheory.Category.assoc, zero_comp]
```

**lean_error:** tail step 1/1 ('simpa [kernel.condition, CategoryTheory.Category.assoc, zero_comp]'): tactic 'assumption' failed

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 12.7s, verify 0.2s, in=1168, out=408)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Category.assoc, kernel.condition, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← Category.assoc, kernel.condition, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
