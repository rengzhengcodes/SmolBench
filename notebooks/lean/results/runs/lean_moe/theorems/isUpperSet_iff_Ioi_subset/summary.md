# isUpperSet_iff_Ioi_subset   (k=0, 1 tactics total)

file: `Mathlib/Order/UpperLower/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp [isUpperSet_iff_forall_lt, subset_def, @forall_swap (_ ∈ s)]
```

**True premises at k:** `isUpperSet_iff_forall_lt`, `Set.subset_def`, `forall_swap`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.3s, verify 0.2s, in=343, out=1417)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro hs a ha b hb
  exact hs ha (le_of_lt hb)
· intro h a b ha hle
  rcases lt_or_eq_of_le hle with hlt | rfl
  · exact h ha hlt
  · exact ha
```

**lean_error:** tail step 2/7 ('· intro hs a ha b hb'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.9s, verify 0.2s, in=828, out=3345)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
  · intro hs a ha b hb
    exact (isUpperSet_iff_forall_lt.mp hs) hb ha
  · intro h
    refine (isUpperSet_iff_forall_lt.mpr ?_)
    intro a b hab ha
    have hsub : Ioi a ⊆ s := h ha
    exact hsub hab
```

**lean_error:** tail step 2/8 ('· intro hs a ha b hb'): unsolved goals

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.1s, in=1393, out=1376)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Set.subset_def, Ioi, Set.mem_setOf_eq, forall_swap, imp_left_comm] using (isUpperSet_iff_forall_lt (s:=s))
```

**lean_error:** tail step 1/1 ('simpa [Set.subset_def, Ioi, Set.mem_setOf_eq, forall_swap, imp_left_comm] using (isUpperSet_iff_forall_lt (s:=s))'): unknown identifier 'imp_left_comm'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.2s, in=1314, out=2242)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
  · intro hs a ha b hb
    have hlt := (isUpperSet_iff_forall_lt (s:=s)).1 hs
    exact hlt hb ha
  · intro h
    apply (isUpperSet_iff_forall_lt (s:=s)).2
    intro a b hab ha
    have hsub := h ha
    exact hsub hab
```

**lean_error:** tail step 2/9 ('· intro hs a ha b hb'): unsolved goals
