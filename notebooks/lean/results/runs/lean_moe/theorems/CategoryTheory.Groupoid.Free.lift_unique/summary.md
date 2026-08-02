# CategoryTheory.Groupoid.Free.lift_unique   (k=9, 10 tactics total)

file: `Mathlib/CategoryTheory/Groupoid/FreeGroupoid.lean`  

**Ground-truth tail (from k):**
```lean
convert this <;> simp only [inv_eq_inv]
```

**True premises at k:** `CategoryTheory.Groupoid.inv_eq_inv`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.1s, verify 0.1s, in=467, out=357)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using this
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 23.7s, verify 0.2s, in=425, out=2672)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.4s, verify 0.1s, in=424, out=368)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using this
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.4s, verify 0.1s, in=828, out=1117)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using this
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 70.7s, verify 0.3s, in=814, out=8159)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Groupoid.inv_eq_inv] at *
exact this
```

**lean_error:** tail step 2/2 ('exact this'): type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.8s, verify 0.1s, in=787, out=497)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [inv_eq_inv] using this
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.2s, verify 0.1s, in=933, out=535)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using this
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 79.5s, verify 0.4s, in=924, out=9394)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
dsimp [Quiver.Hom.toPath, Prefunctor.map] at this ⊢
exact this
```

**lean_error:** tail step 2/2 ('exact this'): type mismatch

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.8s, verify 0.3s, in=892, out=423)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inv_eq_inv, inv_eq_inv]
exact this
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=944, out=460)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using this
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 85.9s, verify 0.2s, in=960, out=10207)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
assumption
```

**lean_error:** tail step 1/1 ('assumption'): tactic 'assumption' failed

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=915, out=661)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Functor.map_inv Φ _
```

**lean_error:** tail step 1/1 ('exact Functor.map_inv Φ _'): typeclass instance problem is stuck, it is often due to metavariables
