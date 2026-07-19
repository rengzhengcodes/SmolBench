# ltTrichotomy_eq_iff   (k=3, 4 tactics total)

file: `Mathlib/Order/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne']
```

**True premises at k:** `ltTrichotomy_gt`, `false_and`, `true_and`, `false_or`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · · · |
| `hint:2` | · ✓ ✓ ✓ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.7s, verify 0.3s, in=343, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ltTrichotomy]
simp [h]
rfl
```

**lean_error:** tail step 3/3 ('rfl'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=343, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ltTrichotomy, h]
simp
rw [h, or_false, or_true]
simp [h]
```

**lean_error:** tail step 1/4 ('rw [ltTrichotomy, h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=343, out=80)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
  · intro h
    rw [ltTrichotomy, h]
    exact Or.inr (Or.inr ⟨h, rfl⟩)
  · rintro (⟨-, hp⟩ | ⟨-, hq⟩ | ⟨hyx, hr⟩)
    · contradiction
    · contradiction
    · rw [ltTrichotomy, hyx]
      exact hr
```

**lean_error:** tail step 1/9 ('split'): tactic 'split' failed

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 3.3s, verify 0.4s, in=343, out=125)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ltTrichotomy]
constructor
· rintro (⟨_, rfl⟩ | ⟨_, rfl⟩ | ⟨_, rfl⟩)
  · exact Or.inl ⟨h, rfl⟩
  · exact False.elim (h.asymm h)
  · exact Or.inr (Or.inr ⟨h, rfl⟩)
· rintro (⟨h', rfl⟩ | _ | ⟨_, rfl⟩)
  · exact False.elim (h'.asymm h)
  · exact False.elim (h.irrefl)
  · exact Or.inr (Or.inr rfl)
```

**lean_error:** tail step 3/10 ('· rintro (⟨_, rfl⟩ | ⟨_, rfl⟩ | ⟨_, rfl⟩)'): unsolved goals

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **incomplete**  (gen 1.0s, verify 0.1s, in=343, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.not_lt, h.ne, h]
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

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **incomplete**  (gen 1.1s, verify 0.1s, in=343, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.not_lt, h.ne, h]
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

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **incomplete**  (gen 1.2s, verify 0.1s, in=343, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h, h.not_lt, h.ne]
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

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **incomplete**  (gen 1.3s, verify 0.1s, in=343, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ltTrichotomy, h, h.not_lt, h.ne]
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

### `hint:2` · llama-31-405b-base · rollout 3 → **incomplete**  (gen 1.2s, verify 0.1s, in=919, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt]
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

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=919, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, or_false, false_or, h, h.not_lt, h.ne.symm]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=919, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.ne', h.not_lt]
exact Iff.rfl
```

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 1.5s, verify 0.1s, in=919, out=38)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, or_false, false_or, h, h.not_lt, h.ne.symm]
exact Iff.rfl
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=919, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_eq, h.ne']
```

**lean_error:** tail step 1/1 ("simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_eq, h.ne']"): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=919, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_eq.symm, h.ne']
```

**lean_error:** tail step 1/1 ("simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_eq.symm, h.ne']"): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=919, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_gt, h.ne.symm]
```

**lean_error:** tail step 1/1 ('simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_gt, h.ne.symm]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=919, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_eq.symm, h.not_gt]
```

**lean_error:** tail step 1/1 ('simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_eq.symm, h.not_gt]'): invalid field notation, type is not of the form (C ...) where C is a constant
