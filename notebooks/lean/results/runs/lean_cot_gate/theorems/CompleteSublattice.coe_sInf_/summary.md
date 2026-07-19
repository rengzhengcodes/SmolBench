# CompleteSublattice.coe_sInf'   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteSublattice.lean`  

**Ground-truth tail (from k):**
```lean
rw [coe_sInf, ← Set.image, sInf_image]
```

**True premises at k:** `CompleteSublattice.coe_sInf`, `Set.image`, `sInf_image`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ · ✘ ✘ | · · ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✓ ✘ ✘ | ✘ · ✓ ✘ | ✓ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | · ✘ ✓ · | ✘ · ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✓ | ✘ · ✘ · | ✓ ✘ ✓ · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 25.4s, verify 0.1s, in=257, out=911)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact f.map_sInf S
```

**lean_error:** tail step 1/1 ('exact f.map_sInf S'): invalid field 'map_sInf', the environment does not contain 'CompleteLatticeHom.map_sInf'

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 92.5s, verify 0.1s, in=257, out=3648)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [CompleteSublattice.coe_sInf]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 113.8s, verify 0.1s, in=257, out=4523)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
f.map_sInf S
```

**lean_error:** tail step 1/1 ('f.map_sInf S'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 150.1s, verify 0.1s, in=257, out=6098)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact f.preserves_sInf S
```

**lean_error:** tail step 1/1 ('exact f.preserves_sInf S'): invalid field 'preserves_sInf', the environment does not contain 'CompleteLatticeHom.preserves_sInf'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.2s, in=257, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 0.8s, verify 0.1s, in=257, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [coe_sInf, iInf_subtype]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=257, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Subtype.coe_sInf]
```

**lean_error:** tail step 1/1 ('simp [Subtype.coe_sInf]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=257, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.1s, verify 0.1s, in=257, out=202)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact coe_iInf (fun N => N) S
```

**lean_error:** tail step 1/1 ('exact coe_iInf (fun N => N) S'): unknown identifier 'coe_iInf'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.4s, verify 0.1s, in=257, out=211)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact coe_iInf S
```

**lean_error:** tail step 1/1 ('exact coe_iInf S'): unknown identifier 'coe_iInf'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.9s, verify 0.1s, in=257, out=297)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [sInf_def]
```

**lean_error:** tail step 1/1 ('simp [sInf_def]'): unknown identifier 'sInf_def'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.7s, verify 0.1s, in=257, out=328)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [sInf_def, mem_image, ← exists_prop, and_comm, iInf_exists]
```

**lean_error:** tail step 1/1 ('simp only [sInf_def, mem_image, ← exists_prop, and_comm, iInf_exists]'): unknown identifier 'sInf_def'

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 50.3s, verify 0.1s, in=745, out=1850)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 67.0s, verify 0.2s, in=745, out=2518)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf]
apply sInf_image
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 101.3s, verify 0.1s, in=745, out=4036)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 138.1s, verify 0.1s, in=745, out=5591)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf], rw [sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf], rw [sInf_image]'): <stdin>:1:13: expected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=745, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.8s, verify 0.1s, in=745, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [coe_sInf, sInf_image]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.9s, verify 0.1s, in=745, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, ← sInf_image, Set.image]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=745, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [coe_sInf S, Set.image, sInf_image]
```

**lean_error:** tail step 1/1 ('simp_rw [coe_sInf S, Set.image, sInf_image]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 4.9s, verify 0.1s, in=745, out=162)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, ← Set.image, sInf_image]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.2s, verify 0.1s, in=745, out=233)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, Set.image, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, Set.image, sInf_image]'): failed to rewrite using equation theorems for 'Set.image'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.7s, verify 0.1s, in=745, out=253)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [coe_sInf, Set.image, sInf_image, Subtype.val_eq_coe]
```

**lean_error:** tail step 1/1 ('simp [coe_sInf, Set.image, sInf_image, Subtype.val_eq_coe]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.8s, verify 0.1s, in=745, out=292)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, Set.image, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, Set.image, sInf_image]'): failed to rewrite using equation theorems for 'Set.image'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 50.5s, verify 0.1s, in=844, out=943)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 103.5s, verify 0.1s, in=844, out=2300)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 118.5s, verify 0.1s, in=844, out=2877)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 146.0s, verify 0.1s, in=844, out=4408)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.0s, verify 0.1s, in=844, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [coe_sInf, sInf_image]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=844, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.2s, verify 0.1s, in=844, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, ← sInf_image, Set.image]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.3s, verify 0.1s, in=844, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [← sInf_image, coe_sInf]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 12.3s, verify 0.1s, in=844, out=223)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, Set.image, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, Set.image, sInf_image]'): failed to rewrite using equation theorems for 'Set.image'

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 12.9s, verify 0.1s, in=844, out=287)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [coe_sInf, Set.image, sInf_image]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.4s, verify 0.1s, in=844, out=234)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, Set.image, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, Set.image, sInf_image]'): failed to rewrite using equation theorems for 'Set.image'

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 15.1s, verify 0.1s, in=844, out=331)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [coe_sInf, Set.image, sInf_image]
```

**lean_error:** tail step 1/1 ('simp_rw [coe_sInf, Set.image, sInf_image]'): simp made no progress

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 41.5s, verify 0.1s, in=868, out=1510)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 49.5s, verify 0.1s, in=868, out=1817)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 75.9s, verify 0.1s, in=868, out=2913)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 88.6s, verify 0.2s, in=868, out=3463)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf]
apply sInf_image
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=868, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.2s, verify 0.2s, in=868, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [coe_sInf, sInf_image]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=868, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.5s, verify 0.2s, in=868, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [coe_sInf, sInf_image]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.2s, verify 0.1s, in=868, out=237)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf, ← Set.image, sInf_image]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.1s, verify 0.1s, in=868, out=267)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [coe_sInf, Set.image, sInf_image]
```

**lean_error:** tail step 1/1 ('simpa only [coe_sInf, Set.image, sInf_image]'): tactic 'assumption' failed

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.2s, verify 0.1s, in=868, out=271)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf, ← Set.image, sInf_image]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 8.4s, verify 0.2s, in=868, out=278)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [coe_sInf, sInf_image, Set.image]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```
