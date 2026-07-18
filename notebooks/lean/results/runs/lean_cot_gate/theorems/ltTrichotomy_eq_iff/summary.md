# ltTrichotomy_eq_iff   (k=3, 4 tactics total)

file: `Mathlib/Order/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne']
```

**True premises at k:** `ltTrichotomy_gt`, `false_and`, `true_and`, `false_or`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | · · ✘ ✘ |
| `hint:2` | · ✘ ✓ ✘ |
| `hint:3` | ✓ · · ✘ |
| `noise:3` | ✘ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.8s, verify 0.1s, in=322, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ltTrichotomy, h]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.2s, verify 0.1s, in=322, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ltTrichotomy, lt_irrefl, h]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=322, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ltTrichotomy, h, Ne.symm (lt_asymm h)]
```

**lean_error:** tail step 1/1 ('simp [ltTrichotomy, h, Ne.symm (lt_asymm h)]'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.8s, verify 0.1s, in=322, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ltTrichotomy, h, Ne.symm (lt_asymm h), false_and_iff, or_false_iff]
```

**lean_error:** tail step 1/1 ('simp [ltTrichotomy, h, Ne.symm (lt_asymm h), false_and_iff, or_false_iff]'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.6s, verify 0.1s, in=899, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, eq_self_iff_true]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=899, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, h.not_eq, h.not_lt]
```

**lean_error:** tail step 1/1 ('simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, h.not_eq, h.not_lt]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.9s, verify 0.1s, in=899, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, h.not_lt, h.ne.symm]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=899, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, h.not_eq, h.not_lt]
```

**lean_error:** tail step 1/1 ('simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, h.not_eq, h.not_lt]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.1s, verify 0.1s, in=1632, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, h.not_lt, h.ne.symm]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.2s, verify 0.1s, in=1632, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.3s, verify 0.1s, in=1632, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 9.4s, verify 0.1s, in=1632, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, not_lt_of_gt h, h.ne,
  h.ne.symm]
```

**lean_error:** tail step 1/2 ('simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, not_lt_of_gt h, h.ne,'): <stdin>:1:83: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=1656, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, false_or, true_and, h, h.not_eq, h.not_lt]
```

**lean_error:** tail step 1/1 ('simp only [ltTrichotomy_gt h, false_and, false_or, true_and, h, h.not_eq, h.not_lt]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.8s, verify 0.1s, in=1656, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, h.not_lt, h.ne.symm]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.0s, verify 0.1s, in=1656, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, h.not_lt, h.ne.symm]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 70.9s, verify 0.1s, in=1656, out=43)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, not_lt_of_ge (le_of_lt h),
  false_or, h.ne]
```

**lean_error:** tail step 1/2 ('simp only [ltTrichotomy_gt h, false_and, true_and, false_or, h, not_lt_of_ge (le_of_lt h),'): <stdin>:1:90: unexpected end of input; expected ']'
