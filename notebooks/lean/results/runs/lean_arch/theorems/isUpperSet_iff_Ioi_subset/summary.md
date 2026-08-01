# isUpperSet_iff_Ioi_subset   (k=0, 1 tactics total)

file: `Mathlib/Order/UpperLower/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp [isUpperSet_iff_forall_lt, subset_def, @forall_swap (_ ∈ s)]
```

**True premises at k:** `isUpperSet_iff_forall_lt`, `Set.subset_def`, `forall_swap`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=296, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h a ha b hb
    exact h hb ha
  · intro h a b hab
    exact h hab a hab.left
```

**lean_error:** tail step 2/5 ('· intro h a ha b hb'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=268, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsUpperSet, ← subset_Ioi_iff]
simp_rw [subset_def, mem_Ioi]
```

**lean_error:** tail step 1/2 ('rw [IsUpperSet, ← subset_Ioi_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 34.9s, verify 0.1s, in=285, out=2103)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split,
{ intros h a ha, intros b hba, exact h ha hba },
{ intros h a b ha hba, exact h ha hba }
```

**lean_error:** tail step 1/3 ('split,'): <stdin>:1:5: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.3s, in=736, out=47)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
constructor
· intro h a ha b hlt
  exact h ha hlt
· intro h a b hlt ha
  apply h ha
  exact hlt
```

**lean_error:** tail step 3/7 ('· intro h a ha b hlt'): unsolved goals

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=706, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
simp_rw [Set.subset_def, forall_swap, ← mem_Ioi]
rfl
```

**lean_error:** tail step 2/3 ('simp_rw [Set.subset_def, forall_swap, ← mem_Ioi]'): tactic 'simp' failed, nested error:

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 160.9s, verify 0.2s, in=725, out=10031)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
rw [Set.subset_def]
rw [forall_swap]
```

**lean_error:** tail step 2/3 ('rw [Set.subset_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.5s, in=1240, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
constructor
intro h a ha b hba
exact h ha hba
intro h a b hab ha
exact h b ha hab
```

**lean_error:** tail step 4/6 ('exact h ha hba'): application type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=1206, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
simp_rw [← subset_def, Ioi]
exact forall_swap
```

**lean_error:** tail step 2/3 ('simp_rw [← subset_def, Ioi]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 17.3s, verify 0.1s, in=1229, out=1019)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply isUpperSet_iff_forall_lt
apply forall_congr'
intro a
rw [Set.subset_def]
apply forall_swap
simp only [forall_swap]
```

**lean_error:** tail step 1/6 ('apply isUpperSet_iff_forall_lt'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.4s, in=1266, out=92)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
constructor
intro h a ha b hba
exact h _ _ ha hba
intro h a b ha hba
exact h a ha b hba
rw [Set.subset_def] at *
constructor
intro h a ha b hba
exact h b (hba.trans ha)
intro h a ha b hba
exact h a ha b hba
apply forall_swap
```

**lean_error:** tail step 4/13 ('exact h _ _ ha hba'): function expected at

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=1294, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
simp_rw [← subset_def]
exact forall_swap _ _ _
```

**lean_error:** tail step 2/3 ('simp_rw [← subset_def]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 61.4s, verify 1.3s, in=1255, out=3715)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Iff.intro
intro h
rw [isUpperSet_iff_forall_lt] at h
intros a ha
rw [Set.subset_def]
intros b hlt
exact h hlt ha
intro h
rw [isUpperSet_iff_forall_lt]
intros a b hlt has
apply h has
rw [Set.subset_def]
exact this b hlt
```

**lean_error:** tail step 12/13 ('rw [Set.subset_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
