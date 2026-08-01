# ltTrichotomy_eq_iff   (k=3, 4 tactics total)

file: `Mathlib/Order/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne']
```

**True premises at k:** `ltTrichotomy_gt`, `false_and`, `true_and`, `false_or`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | · | · |
| `hint:3` | ✘ | · | · |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=343, out=124)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
next => exact Or.inr (Or.inr ⟨h, rfl⟩)
intro h
cases h
case inl.inl h =>
  have h' := h.1
  have := lt_asymm h' h
  contradiction
case inl.inr h =>
  have h' := h.1
  have := lt_asymm h h'
  contradiction
case inr.inl h =>
  have h' := h.1
  have := lt_asymm h h'
  contradiction
case inr.inr h =>
  exact h.2.symm
```

**lean_error:** tail step 1/18 ('split'): tactic 'split' failed

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=317, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ltTrichotomy, if_neg (x < y).not, if_neg (x = y).not, if_pos h]
simp only [eq_comm]
simp only [or_false, false_or, h, and_comm]
```

**lean_error:** tail step 1/3 ('rw [ltTrichotomy, if_neg (x < y).not, if_neg (x = y).not, if_pos h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 73.0s, verify 0.2s, in=332, out=4576)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ltTrichotomy]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=919, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.ne', h.not_lt]
exact Iff.rfl
```

### `hint:2` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=886, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, or_true, h, h.not_lt, h.ne]
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

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.0s, verify 0.1s, in=908, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

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

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1645, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_eq.symm, h.ne.symm]
exact Iff.rfl
```

**lean_error:** tail step 1/2 ('simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_eq.symm, h.ne.symm]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.1s, in=1619, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, or_assoc, h]
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

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.4s, verify 0.1s, in=1634, out=57)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, h, false_or, or_true]
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

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1673, out=33)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_gt, h.ne']
exact Iff.rfl
```

**lean_error:** tail step 1/2 ("simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_gt, h.ne']"): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=1725, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, h, true_and, false_or, or_assoc]
aesop
```

**lean_error:** tail step 2/2 ('aesop'): <stdin>:1:1: unknown tactic

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.5s, verify 0.1s, in=1662, out=60)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, h, false_or, lt_irrefl]
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
