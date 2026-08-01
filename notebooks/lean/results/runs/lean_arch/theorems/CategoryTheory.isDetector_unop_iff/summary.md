# CategoryTheory.isDetector_unop_iff   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Generator.lean`  

**Ground-truth tail (from k):**
```lean
rw [IsDetector, IsCodetector, ← isDetecting_unop_iff, Set.singleton_unop]
```

**True premises at k:** `CategoryTheory.IsDetector`, `CategoryTheory.IsCodetector`, `CategoryTheory.isDetecting_unop_iff`, `Set.singleton_unop`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.2s, in=267, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h X Y f g
  apply Quiver.Hom.op_inj
  exact h _ _ f.op g.op
· intro h X Y f g
  exact h _ _ f.unop g.unop
```

**lean_error:** tail step 2/6 ('· intro h X Y f g'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 2.3s, in=239, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsCodetector, IsDetector]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=256, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
[unfold IsDetector, IsCodetector, Functor.op, Functor.unop_op, iff_iff_and_or, iff_true_intro]
```

**lean_error:** tail step 1/1 ('[unfold IsDetector, IsCodetector, Functor.op, Functor.unop_op, iff_iff_and_or, iff_true_intro]'): <stdin>:1:0: expected tactic

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.3s, in=882, out=65)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector]
constructor
· intro h
  apply isDetecting_unop_iff.mp
  rw [Set.singleton_unop]
  exact h
· intro h
  apply isDetecting_unop_iff.mpr
  rw [Set.singleton_unop]
  exact h
```

**lean_error:** tail step 3/10 ('· intro h'): unsolved goals

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=835, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, CategoryTheory.isDetecting_unop_iff, Set.singleton_unop]
```

**lean_error:** tail step 1/1 ('rw [IsDetector, IsCodetector, CategoryTheory.isDetecting_unop_iff, Set.singleton_unop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=871, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, isDetecting_unop_iff]
simp [Set.singleton_unop]
```

**lean_error:** tail step 1/2 ('rw [IsDetector, IsCodetector, isDetecting_unop_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.3s, in=1607, out=67)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector]
constructor
· intro h
  apply isDetecting_unop_iff.2
  rw [← Set.singleton_unop]
  exact h
· intro h
  apply isDetecting_unop_iff.1
  rw [Set.singleton_unop]
  exact h
```

**lean_error:** tail step 3/10 ('· intro h'): unsolved goals

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=1537, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, CategoryTheory.isDetecting_unop_iff, Set.singleton_unop]
```

**lean_error:** tail step 1/1 ('rw [IsDetector, IsCodetector, CategoryTheory.isDetecting_unop_iff, Set.singleton_unop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1596, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, isDetecting_unop_iff]
simp [Set.singleton_unop]
```

**lean_error:** tail step 1/2 ('rw [IsDetector, IsCodetector, isDetecting_unop_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.8s, verify 1.0s, in=1631, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector]
rw [← Set.singleton_unop G, isDetecting_unop_iff]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=1669, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]
rfl
```

**lean_error:** tail step 1/2 ('rw [IsDetector, IsCodetector, isDetecting_unop_iff, Set.singleton_unop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1620, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, isDetecting_unop_iff]
simp [Set.singleton_unop]
```

**lean_error:** tail step 1/2 ('rw [IsDetector, IsCodetector, isDetecting_unop_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
