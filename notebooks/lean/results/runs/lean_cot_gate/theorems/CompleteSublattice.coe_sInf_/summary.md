# CompleteSublattice.coe_sInf'   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteSublattice.lean`  

**Ground-truth tail (from k):**
```lean
rw [coe_sInf, ← Set.image, sInf_image]
```

**True premises at k:** `CompleteSublattice.coe_sInf`, `Set.image`, `sInf_image`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | · · ✘ ✘ |
| `hint:2` | ✘ · ✓ ✘ |
| `hint:3` | · ✘ ✓ · |
| `noise:3` | ✘ · ✘ · |

## Per-cell detail

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
