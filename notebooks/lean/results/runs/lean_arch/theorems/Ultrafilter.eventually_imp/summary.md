# Ultrafilter.eventually_imp   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Ultrafilter.lean`  

**Ground-truth tail (from k):**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

**True premises at k:** `imp_iff_not_or`, `Ultrafilter.eventually_or`, `Ultrafilter.eventually_not`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.3s, in=339, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨_, _⟩
· intro h r
  exact h.mp r
· intro h
  exact h.mono fun x => id
```

**lean_error:** tail step 2/5 ('· intro h r'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=314, out=53)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eventually_imp_distrib_right]
simp only [imp_iff_not_or, eventually_or_distrib_left, eventually_not]
rw [← not_imp_not]
simp only [not_eventually, not_or]
rw [eventually_imp_distrib_left]
```

**lean_error:** tail step 1/5 ('rw [eventually_imp_distrib_right]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 78.5s, verify 0.1s, in=328, out=4828)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split,
exact filter.mp,
exact filter.mpr
```

**lean_error:** tail step 1/3 ('split,'): <stdin>:1:5: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=768, out=38)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [imp_iff_not_or],
rw [Ultrafilter.eventually_or],
rw [Ultrafilter.eventually_not],
simp only [not_or, not_not],
exact Iff.rfl
```

**lean_error:** tail step 1/5 ('rw [imp_iff_not_or],'): <stdin>:1:19: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 2.0s, in=751, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [imp_iff_not_or, eventually_or, eventually_not]
simp only [or_iff_not_imp_left, imp_iff_not_or.symm]
```

**lean_error:** tail step 1/2 ('rw [imp_iff_not_or, eventually_or, eventually_not]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 112.9s, verify 0.3s, in=757, out=7034)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Iff.intro
intro h
apply Imp.intro
intro h_p
exact h.mp h_p
intro h
apply Iff.mpr imp_iff_not_or
apply Iff.mpr eventually_or
apply Iff.mpr eventually_not
exact h
```

**lean_error:** tail step 3/10 ('apply Imp.intro'): unknown identifier 'Imp.intro'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.8s, in=1008, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [imp_iff_not_or],
rw [Ultrafilter.eventually_not],
rw [Ultrafilter.eventually_or]
```

**lean_error:** tail step 1/3 ('rw [imp_iff_not_or],'): <stdin>:1:19: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=996, out=48)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
simp only [imp_iff_right_iff, not_imp_not]
rw [← not_imp_not]
simp [imp_iff_not_or]
```

**lean_error:** tail step 1/4 ('rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.3s, in=997, out=106)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Iff.intro
intro h
apply Imp.intro
intro h_p
exact h.mono (fun x => Imp.intro (fun h_px => h_p h_px))
intro h
apply h
apply Iff.mpr (eventually_or)
apply Or.inr
apply eventually_not.mpr
intro h_p
apply h_p
apply Iff.mpr (imp_iff_not_or)
apply Or.inl
apply eventually_not.mpr
intro h_p
apply h_p
```

**lean_error:** tail step 3/17 ('apply Imp.intro'): unknown identifier 'Imp.intro'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=1034, out=38)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [imp_iff_not_or],
rw [Ultrafilter.eventually_or],
rw [Ultrafilter.eventually_not],
simp only [not_or, not_not],
exact Iff.rfl
```

**lean_error:** tail step 1/5 ('rw [imp_iff_not_or],'): <stdin>:1:19: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=1045, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
simp only [imp_iff_not_or.symm]
rw [← imp_iff_not_or]
simp [Ultrafilter.eventually_not]
```

**lean_error:** tail step 1/4 ('rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.3s, in=1023, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Iff.intro
intro h
apply Imp.intro
intro h'
apply h
intro h
apply h
```

**lean_error:** tail step 3/7 ('apply Imp.intro'): unknown identifier 'Imp.intro'
