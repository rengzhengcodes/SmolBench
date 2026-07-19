# CategoryTheory.Limits.IsZero.iff_isSplitMono_eq_zero   (k=6, 7 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`  

**Ground-truth tail (from k):**
```lean
simp only [h, zero_comp]
```

**True premises at k:** `CategoryTheory.Limits.zero_comp`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✓ | · ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 43.5s, verify 0.1s, in=264, out=1740)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw h
exact zero_comp (retraction f)
```

**lean_error:** tail step 1/2 ('rw h'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 51.7s, verify 0.1s, in=264, out=2081)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h]
rw [zero_comp]
rfl
```

**lean_error:** tail step 1/3 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 67.6s, verify 0.1s, in=264, out=2808)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw h
apply zero_comp
```

**lean_error:** tail step 1/2 ('rw h'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 72.2s, verify 0.2s, in=264, out=3008)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
subst h
apply zero_comp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.6s, verify 0.1s, in=264, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
```

**final state (truncated):**
```
case mpr
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasZeroMorphisms C
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=264, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.1s, in=264, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.9s, verify 0.1s, in=264, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 3.3s, verify 0.1s, in=264, out=102)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 3.5s, verify 0.1s, in=264, out=109)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 3.9s, verify 0.1s, in=264, out=117)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=264, out=129)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 28.4s, verify 0.1s, in=561, out=1133)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h]
apply zero_comp
```

**lean_error:** tail step 1/2 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 42.4s, verify 0.1s, in=561, out=1696)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h]
exact zero_comp
```

**lean_error:** tail step 1/2 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 80.7s, verify 0.1s, in=561, out=3387)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 211.1s, verify 0.1s, in=561, out=9499)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsSplitMono.id f, h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [IsSplitMono.id f, h, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.7s, verify 0.1s, in=561, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h]
```

**final state (truncated):**
```
case mpr
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasZeroMorphisms C
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=561, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=561, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=561, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← h, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 4.3s, verify 0.1s, in=561, out=123)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 4.4s, verify 0.1s, in=561, out=126)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 4.8s, verify 0.1s, in=561, out=128)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=561, out=128)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 70.3s, verify 0.1s, in=830, out=1758)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply zero_comp
```

**lean_error:** tail step 1/1 ('apply zero_comp'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 74.3s, verify 0.1s, in=830, out=1407)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 107.2s, verify 0.1s, in=830, out=2998)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw h
apply zero_comp
```

**lean_error:** tail step 1/2 ('rw h'): <stdin>:1:3: expected '['

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 108.7s, verify 0.1s, in=830, out=3618)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.3s, verify 0.1s, in=830, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=830, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=830, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← h, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.7s, verify 0.1s, in=830, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.3s, verify 0.1s, in=830, out=125)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 7.8s, verify 0.1s, in=830, out=96)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Category.id_comp f, h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← Category.id_comp f, h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.9s, verify 0.1s, in=830, out=160)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.7s, verify 0.1s, in=830, out=202)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 29.4s, verify 0.1s, in=854, out=1173)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 42.1s, verify 0.1s, in=854, out=1676)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw h
apply zero_comp
```

**lean_error:** tail step 1/2 ('rw h'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 83.4s, verify 0.1s, in=854, out=3527)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h]
apply zero_comp
```

**lean_error:** tail step 1/2 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 107.8s, verify 0.1s, in=854, out=4714)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw h
apply zero_comp
```

**lean_error:** tail step 1/2 ('rw h'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.8s, verify 0.1s, in=854, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h]
```

**final state (truncated):**
```
case mpr
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasZeroMorphisms C
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=854, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.5s, in=854, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=854, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← h, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 3.2s, verify 0.1s, in=854, out=95)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Category.id_comp f, h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [← Category.id_comp f, h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 4.1s, verify 0.1s, in=854, out=121)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 4.9s, verify 0.1s, in=854, out=128)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.1s, verify 0.1s, in=854, out=143)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct
