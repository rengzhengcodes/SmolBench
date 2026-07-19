# inf_eq_and_sup_eq_iff   (k=4, 5 tactics total)

file: `Mathlib/Order/Lattice.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

**True premises at k:** `inf_idem`, `sup_idem`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ | ✘ ✓ ✓ ✓ |
| `hint:2` | ✓ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 53.8s, verify 0.1s, in=224, out=2403)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
exact inf_idem b
exact sup_idem b
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 58.9s, verify 0.1s, in=224, out=2620)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· apply inf_idem
· apply sup_idem
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 66.3s, verify 0.1s, in=224, out=2925)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_self b, sup_self b⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_self b, sup_self b⟩'): unknown identifier 'inf_self'

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 90.0s, verify 0.1s, in=224, out=3867)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_self b, sup_self b⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_self b, sup_self b⟩'): unknown identifier 'inf_self'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=224, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.5s, verify 0.1s, in=224, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.6s, verify 0.1s, in=224, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.6s, verify 0.1s, in=224, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [inf_eq_left, sup_eq_left]
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 3.6s, verify 0.1s, in=224, out=119)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp *
```

**lean_error:** tail step 1/1 ('simp *'): <stdin>:1:5: expected end of input

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 4.5s, verify 0.1s, in=224, out=155)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 4.6s, verify 0.1s, in=224, out=159)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 4.9s, verify 0.1s, in=224, out=168)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 12.5s, verify 0.1s, in=498, out=496)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 20.6s, verify 0.1s, in=498, out=886)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem b, sup_idem b⟩
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 32.7s, verify 0.1s, in=498, out=1454)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
split
exact inf_idem b
exact sup_idem b
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 62.6s, verify 0.1s, in=498, out=2774)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem b, sup_idem b⟩
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=498, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.4s, verify 0.1s, in=498, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.7s, verify 0.1s, in=498, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.8s, verify 0.1s, in=498, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem b, sup_idem b⟩
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 3.5s, verify 0.1s, in=498, out=120)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 4.1s, verify 0.1s, in=498, out=138)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 4.1s, verify 0.1s, in=498, out=136)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 4.5s, verify 0.1s, in=498, out=158)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem b, sup_idem b⟩
```
