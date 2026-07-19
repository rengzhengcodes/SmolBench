# CategoryTheory.Limits.biprod.braiding'_eq_braiding   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
aesop_cat
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | · · ✘ ✘ | · · ✘ ✘ | · · ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 122.2s, verify 1.0s, in=277, out=5303)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
```

**final state (truncated):**
```
case w.h₀.h₀
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
...
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 124.8s, verify 0.5s, in=277, out=5417)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp [braiding, braiding']
```

**final state (truncated):**
```
case w.h₀.h₁
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
...
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 137.0s, verify 0.2s, in=277, out=6048)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biproduct.hom_ext
simp
```

**lean_error:** tail step 1/2 ('apply biproduct.hom_ext'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 202.3s, verify 0.1s, in=277, out=9032)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply coproduct.hom_ext; simp
```

**lean_error:** tail step 1/1 ('apply coproduct.hom_ext; simp'): <stdin>:1:23: expected end of input

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 0.5s, verify 0.1s, in=277, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [braiding', braiding]
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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.6s, verify 0.1s, in=277, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [braiding', braiding]
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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.7s, verify 0.1s, in=277, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [braiding', braiding, Biproduct.isoSwap_hom]
```

**lean_error:** tail step 1/1 ("simp [braiding', braiding, Biproduct.isoSwap_hom]"): unknown identifier 'Biproduct.isoSwap_hom'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=277, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [braiding', braiding, swap]
```

**lean_error:** tail step 1/1 ("simp [braiding', braiding, swap]"): unknown identifier 'swap'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 4.0s, verify 0.1s, in=277, out=139)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [braiding', braiding]
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 5.8s, verify 0.1s, in=277, out=202)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [braiding', braiding]
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.4s, verify 0.1s, in=277, out=163)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact braiding'_eq_braiding
```

**lean_error:** tail step 1/1 ("exact braiding'_eq_braiding"): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.0s, verify 0.1s, in=277, out=346)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biprod.hom_ext <;>
apply biprod.hom_ext <;>
apply biprod.hom_ext <;>
apply biprod.hom_ext <;>
simp only [braiding'_fst_fst, braiding'_fst_snd, braiding_fst, braiding_snd]
```

**lean_error:** tail step 1/5 ('apply biprod.hom_ext <;>'): <stdin>:1:24: unexpected end of input; expected '['
