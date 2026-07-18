# inf_eq_and_sup_eq_iff   (k=4, 5 tactics total)

file: `Mathlib/Order/Lattice.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

**True premises at k:** `inf_idem`, `sup_idem`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✓ ✓ ✓ ✓ |
| `hint:2` | ✓ ✓ ✓ ✓ |

## Per-cell detail

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
