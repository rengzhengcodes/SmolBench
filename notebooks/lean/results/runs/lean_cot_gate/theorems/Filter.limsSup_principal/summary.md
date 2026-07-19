# Filter.limsSup_principal   (k=1, 2 tactics total)

file: `Mathlib/Order/LiminfLimsup.lean`  

**Ground-truth tail (from k):**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

**True premises at k:** `csInf_upper_bounds_eq_csSup`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✘ ✓ ✓ ✓ |
| `hint:3` | ✓ ✘ ✘ ✓ | ✓ ✓ ✘ ✘ | ✓ ✘ ✓ ✘ |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 117.5s, verify 0.3s, in=271, out=4552)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
apply sInf_le
use sSup s
exact fun x hx => le_sSup hx
apply le_sInf
intro a ha
exact sSup_le ha
```

**lean_error:** tail step 2/7 ('apply sInf_le'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 152.1s, verify 0.1s, in=271, out=6129)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h1 := csInf_le _ (sSup_upper_bound hs h)
have h2 := le_csInf (by rcases h with ⟨a, ha⟩; use a; exact ha) (fun a ha => sSup_le ha)
exact le_antisymm h1 h2
```

**lean_error:** tail step 1/3 ('have h1 := csInf_le _ (sSup_upper_bound hs h)'): internal exception #7

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 177.0s, verify 1.0s, in=271, out=7198)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
apply sInf_le
exact is_ub_sSup h hs
apply IsLowerBound.le_sInf
intros a ha
exact sSup_le ha
```

**lean_error:** tail step 2/6 ('apply sInf_le'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 210.9s, verify 0.2s, in=271, out=8578)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
· apply sInf_le
  · exact fun x xs => le_sSup h hs xs
· apply le_sInf
  · intro a ha
    exact sSup_le ha
```

**lean_error:** tail step 2/6 ('· apply sInf_le'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=271, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [csSup_of_le, csInf_of_le, h]
```

**lean_error:** tail step 1/1 ('simp [csSup_of_le, csInf_of_le, h]'): unknown identifier 'csSup_of_le'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=271, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf_eq_csInf, csInf_cSup h hs]
```

**lean_error:** tail step 1/1 ('rw [sInf_eq_csInf, csInf_cSup h hs]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=271, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [sSup_eq_csSup_of_bddAbove_of_nonempty h hs]
```

**lean_error:** tail step 1/1 ('simp [sSup_eq_csSup_of_bddAbove_of_nonempty h hs]'): unknown identifier 'sSup_eq_csSup_of_bddAbove_of_nonempty'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=271, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sInf_Ici_eq_cSup s
```

**lean_error:** tail step 1/1 ('exact sInf_Ici_eq_cSup s'): unknown identifier 'sInf_Ici_eq_cSup'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.3s, verify 0.1s, in=271, out=137)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sInf_upperBounds_eq_sSup h hs
```

**lean_error:** tail step 1/1 ('exact sInf_upperBounds_eq_sSup h hs'): unknown identifier 'sInf_upperBounds_eq_sSup'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.8s, verify 0.1s, in=271, out=162)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [csSup_def]
```

**lean_error:** tail step 1/1 ('simp [csSup_def]'): unknown identifier 'csSup_def'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.2s, verify 0.1s, in=271, out=206)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using sInf_eq_sSup' h hs
```

**lean_error:** tail step 1/1 ("simpa using sInf_eq_sSup' h hs"): unknown identifier 'sInf_eq_sSup''

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.3s, verify 0.1s, in=271, out=265)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf_eq_iInf, iInf_of_nonempty_of_bddAbove hs h]
```

**lean_error:** tail step 1/1 ('rw [sInf_eq_iInf, iInf_of_nonempty_of_bddAbove hs h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 6.5s, verify 0.1s, in=529, out=235)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 7.0s, verify 0.1s, in=529, out=242)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 7.8s, verify 0.1s, in=529, out=281)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 10.8s, verify 0.1s, in=529, out=386)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=529, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.8s, verify 0.1s, in=529, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=529, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=529, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.4s, verify 0.1s, in=529, out=139)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('rw [csInf_upper_bounds_eq_csSup h hs]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 5.7s, verify 0.1s, in=529, out=155)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 5.9s, verify 0.1s, in=529, out=162)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 6.3s, verify 0.1s, in=529, out=178)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 10.8s, verify 0.1s, in=854, out=162)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 13.0s, verify 0.1s, in=854, out=212)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('rw [csInf_upper_bounds_eq_csSup h hs]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 13.6s, verify 0.1s, in=854, out=253)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('rw [csInf_upper_bounds_eq_csSup h hs]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 13.7s, verify 0.1s, in=854, out=261)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=854, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=854, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=854, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [upperBounds, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('simp only [upperBounds, csInf_upper_bounds_eq_csSup h hs]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=854, out=30)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [sInf_eq_csInf, sSup_eq_csSup, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('simp only [sInf_eq_csInf, sSup_eq_csSup, csInf_upper_bounds_eq_csSup h hs]'): unknown identifier 'sInf_eq_csInf'

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.5s, verify 0.1s, in=854, out=134)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.5s, verify 0.1s, in=854, out=179)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [upperBounds, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('rw [upperBounds, csInf_upper_bounds_eq_csSup h hs]'): failed to rewrite using equation theorems for 'upperBounds'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 10.6s, verify 0.1s, in=854, out=151)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.6s, verify 0.1s, in=854, out=234)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [upperBounds, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('rw [upperBounds, csInf_upper_bounds_eq_csSup h hs]'): failed to rewrite using equation theorems for 'upperBounds'

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 6.1s, verify 0.1s, in=879, out=215)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 6.4s, verify 0.1s, in=879, out=226)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 7.8s, verify 0.1s, in=879, out=284)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 8.4s, verify 0.1s, in=879, out=305)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.0s, verify 0.1s, in=879, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=879, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=879, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=879, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [upperBounds, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('simp only [upperBounds, csInf_upper_bounds_eq_csSup h hs]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 4.6s, verify 0.1s, in=879, out=126)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 4.9s, verify 0.1s, in=879, out=133)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 5.7s, verify 0.1s, in=879, out=158)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 6.1s, verify 0.1s, in=879, out=170)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```
