# Array.contains_def   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [and_comm]
```

**True premises at k:** `and_comm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=263, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · rintro ⟨x, hx, rfl⟩
    exact hx
  · intro h
    use a
    exact ⟨h, rfl⟩
```

**lean_error:** tail step 2/6 ('· rintro ⟨x, hx, rfl⟩'): tactic 'subst' failed, invalid equality proof, it is not of the form (x = t) or (t = x)

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=239, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Array.mem_def]
simp only [beq_iff_eq]
rw [← exists_and_left]
simp only [exists_eq_left']
rw [eq_comm]
```

**lean_error:** tail step 1/5 ('rw [Array.mem_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=252, out=44)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.intro
{ intro h, cases h with x h, exact h.right }
{ intro h, use a, split, exact h, rw DecidableEq.decide_eq_true }
```

**lean_error:** tail step 2/3 ('{ intro h, cases h with x h, exact h.right }'): <stdin>:1:9: expected '}'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=415, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [and_comm]
exact Iff.rfl
```

**lean_error:** tail step 1/2 ('rw [and_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=388, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [beq_iff_eq]
simp [exists_prop, eq_comm]
rw [and_comm]
```

**lean_error:** tail step 2/3 ('simp [exists_prop, eq_comm]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 80.5s, verify 0.1s, in=404, out=4948)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exists_congr
apply and_comm
```

**lean_error:** tail step 1/2 ('exists_congr'): <stdin>:1:1: unknown tactic

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=486, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [and_comm]
exact Iff.rfl
```

**lean_error:** tail step 1/2 ('rw [and_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=460, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [beq_iff_eq]
simp [exists_prop, and_comm]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 95.5s, verify 0.1s, in=475, out=5894)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [and_comm]
```

**lean_error:** tail step 1/1 ('rw [and_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=510, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [and_comm]
apply Iff.intro
constructor
rw [Exists.prop]
intro h
cases h
simp_all
constructor
intro h
use a
simp_all
```

**lean_error:** tail step 1/11 ('rw [and_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.6s, in=493, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [beq_iff_eq]
simp [exists_prop, and_comm]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 60.9s, verify 0.3s, in=499, out=3699)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Iff.intro
intro h
apply h
intro h
apply h
```

**lean_error:** tail step 3/5 ('apply h'): tactic 'apply' failed, failed to unify
