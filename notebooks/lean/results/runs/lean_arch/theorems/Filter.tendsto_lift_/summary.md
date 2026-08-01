# Filter.tendsto_lift'   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Lift.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal, comp]
```

**True premises at k:** `Filter.lift'`, `Filter.tendsto_lift`, `Filter.tendsto_principal`, `Function.comp`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | · | ✓ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.2s, in=324, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h' s hs
    apply Filter.lift'_mem.1 h'
    exact hs
  · intro h'
    apply Filter.lift'_mem.2
    intro s hs
    exact h' s hs
```

**lean_error:** tail step 2/8 ("· intro h' s hs"): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=298, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Filter.lift']
simp only [Tendsto, Filter.mem_lift'_iff]
rfl
```

**lean_error:** tail step 2/3 ("simp only [Tendsto, Filter.mem_lift'_iff]"): unknown constant 'Filter.mem_lift'_iff'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 9.7s, verify 0.1s, in=313, out=505)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Tendsto, Filter.lift']
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
f f₁ f₂ : Filter α
h h₁ h₂ : Set α → Set β
...
```

### `hint:2` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 2.7s, verify 0.4s, in=1246, out=38)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.lift']
rw [Filter.tendsto_lift]
simp only [Tendsto, le_principal_iff, mem_map', Filter.Eventually]
simp only [Function.comp]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
f f₁ f₂ : Filter α
h h₁ h₂ : Set α → Set β
...
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=1215, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.lift', Filter.tendsto_lift]
simp only [Filter.tendsto_principal, Function.comp]
rfl
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 18.9s, verify 0.1s, in=1235, out=1075)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Filter.tendsto_lift
simp only [Filter.tendsto_principal]
```

**lean_error:** tail step 1/2 ('apply Filter.tendsto_lift'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=3900, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.tendsto_lift, Filter.lift']
simp only [Filter.tendsto_principal]
```

**lean_error:** tail step 1/2 ("rw [Filter.tendsto_lift, Filter.lift']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=3878, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.lift', tendsto_lift]
simp_rw [tendsto_principal, Function.comp]
```

**lean_error:** tail step 2/2 ('simp_rw [tendsto_principal, Function.comp]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.4s, in=3889, out=64)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Iff.intro
intro h
apply Filter.tendsto_lift.mpr
intro s
apply Filter.tendsto_principal.mpr
exact h s
intro h
apply Filter.tendsto_lift.mp
intro s
apply Filter.tendsto_principal.mp
exact h s
```

**lean_error:** tail step 3/11 ('apply Filter.tendsto_lift.mpr'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.4s, in=3927, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.lift']
rw [Filter.tendsto_lift]
simp only [Tendsto, le_principal_iff, mem_map', Filter.Eventually]
exact Iff.rfl
```

**lean_error:** tail step 4/4 ('exact Iff.rfl'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=4202, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.lift', tendsto_lift]
simp_rw [tendsto_principal, Function.comp]
rfl
```

**lean_error:** tail step 2/3 ('simp_rw [tendsto_principal, Function.comp]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=3916, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.tendsto_lift, Filter.lift']
simp only [Filter.tendsto_principal]
```

**lean_error:** tail step 2/2 ('simp only [Filter.tendsto_principal]'): simp made no progress
