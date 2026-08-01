# symmDiff_symmDiff_symmDiff_comm   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [symmDiff_assoc, symmDiff_left_comm]
```

**True premises at k:** `symmDiff_assoc`, `symmDiff_left_comm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | · | ✘ | · |
| `hint:3` | · | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=290, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
symm
rw [symm b, symm c]
rw [assoc]
rw [comm b]
rw [assoc]
```

**lean_error:** tail step 2/5 ('rw [symm b, symm c]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=250, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [symm_diff_assoc, symm_diff_left_comm a, symm_diff_comm b, symm_diff_assoc]
simp_rw [symm_diff_comm]
```

**lean_error:** tail step 1/2 ('simp_rw [symm_diff_assoc, symm_diff_left_comm a, symm_diff_comm b, symm_diff_assoc]'): unknown identifier 'symm_diff_assoc'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 47.9s, verify 0.1s, in=279, out=2824)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
repeat' $ apply symm_diff_assoc
apply symm_diff_comm
repeat' $ apply symm_diff_assoc
```

**lean_error:** tail step 1/3 ("repeat' $ apply symm_diff_assoc"): <stdin>:1:8: expected '.', 'decide', 'intro', 'match', 'native_decide', 'open', 'set_option', '{', '·', identifier or no space before spliced term

### `hint:2` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 1.0s, verify 0.1s, in=604, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_assoc, symmDiff_left_comm, symmDiff_assoc]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
...
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=547, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_assoc, symmDiff_assoc, symmDiff_left_comm b c a, symmDiff_assoc]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_assoc, symmDiff_assoc, symmDiff_left_comm b c a, symmDiff_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 19.7s, verify 0.7s, in=593, out=1126)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_assoc]
rw [symmDiff_left_comm]
rw [symmDiff_assoc]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=1159, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_assoc, symmDiff_left_comm]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
...
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=1088, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_assoc, symmDiff_assoc, symmDiff_left_comm] 
rw [symmDiff_assoc]
```

**lean_error:** tail step 2/2 ('rw [symmDiff_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 29.2s, verify 0.2s, in=1148, out=1706)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_assoc],
rw [symmDiff_left_comm],
rw [←symmDiff_assoc]
```

**lean_error:** tail step 1/3 ('rw [symmDiff_assoc],'): <stdin>:1:19: expected end of input

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1183, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_assoc, symmDiff_left_comm b a (c ∆ d)]
rw [symmDiff_assoc]
```

**lean_error:** tail step 1/2 ('rw [symmDiff_assoc, symmDiff_left_comm b a (c ∆ d)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1192, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_assoc, symmDiff_assoc, symmDiff_left_comm b c (a ∆ d)] 
rw [symmDiff_assoc, symmDiff_comm b a]
```

**lean_error:** tail step 1/2 ('rw [symmDiff_assoc, symmDiff_assoc, symmDiff_left_comm b c (a ∆ d)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.8s, verify 0.1s, in=1172, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_assoc, symmDiff_left_comm, symmDiff_assoc]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
...
```
