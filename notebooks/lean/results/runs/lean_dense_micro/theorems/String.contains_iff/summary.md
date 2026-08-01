# String.contains_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [contains, any_iff]
```

**True premises at k:** `String.contains`, `String.any_iff`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.6s, verify 0.1s, in=222, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Iff.intro
exact contains_correct
exact mem_correct_of_contains
```

**lean_error:** tail step 1/3 ('exact Iff.intro'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=222, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold contains
exact Iff.rfl
```

**lean_error:** tail step 2/2 ('exact Iff.rfl'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=222, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Iff.intro
exact fun h => String.contains_mem h
exact fun h => String.mem_contains h
```

**lean_error:** tail step 1/3 ('exact Iff.intro'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=222, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Iff.intro
exact fun h => String.contains_iff_mem_data.mp h
exact fun h => String.contains_iff_mem_data.mpr h
```

**lean_error:** tail step 1/3 ('exact Iff.intro'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=500, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold contains
rw any_iff
simp [Bool.beq_eq]
```

**lean_error:** tail step 2/3 ('rw any_iff'): <stdin>:1:3: expected '['

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=500, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
change contains s c with any s (fun a => a == c),
rw any_iff,
simp [Membership.mem]
```

**lean_error:** tail step 1/3 ('change contains s c with any s (fun a => a == c),'): <stdin>:1:48: expected end of input

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=500, out=45)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
change contains s c with s.any fun a => a == c
rw [any_iff]
apply Iff.trans
apply ExistsUnique.exists_iff_exists
simp
exact eq_comm
simp
exact Iff.rfl
```

**lean_error:** tail step 1/8 ('change contains s c with s.any fun a => a == c'): tactic 'Lean.Parser.Tactic.changeWith' has not been implemented

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=500, out=61)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
change contains s c with s.any (fun a => a == c)
rw [any_iff]
constructor
intro h
obtain ⟨c', h_mem, h_eq⟩ := h
rw [←h_eq]
exact h_mem
intro h
exact ⟨c, h, rfl⟩
```

**lean_error:** tail step 1/9 ('change contains s c with s.any (fun a => a == c)'): tactic 'Lean.Parser.Tactic.changeWith' has not been implemented
