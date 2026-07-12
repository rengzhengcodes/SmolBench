# RatFunc.ofFractionRing_algebraMap   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
rw [← mk_one, mk_one']
```

**True premises at k:** `RatFunc.mk_one`, `RatFunc.mk_one'`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 13.9s, verify 0.1s, in=265, out=598)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refl
```

**lean_error:** tail step 1/1 ('refl'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 14.9s, verify 0.1s, in=265, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 7.5s, verify 0.1s, in=265, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 8.5s, verify 0.1s, in=265, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 129.8s, verify 0.1s, in=634, out=3520)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-goedel · rollout 0 → **success**  (gen 15.3s, verify 0.1s, in=634, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← mk_one', mk_one]
```

### `hint:2` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 7.9s, verify 0.1s, in=634, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one, mk_one', ← mk_coe_def, Submonoid.coe_one]
```

**lean_error:** tail step 1/1 ("rw [← mk_one, mk_one', ← mk_coe_def, Submonoid.coe_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-real · rollout 0 → **success**  (gen 8.6s, verify 0.1s, in=634, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one, mk_one']
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 33.8s, verify 0.1s, in=1825, out=1625)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← RatFunc.mk_one', RatFunc.mk_one]
```

### `hint:3` · qwen3-lean-goedel · rollout 0 → **success**  (gen 15.2s, verify 0.1s, in=1825, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← mk_one', mk_one]
```

### `hint:3` · qwen3-lean-leannav · rollout 0 → **success**  (gen 8.0s, verify 0.6s, in=1825, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← mk_one, ← mk_one', mk_coe_def, Submonoid.coe_one]
```

### `hint:3` · qwen3-lean-real · rollout 0 → **success**  (gen 8.7s, verify 0.1s, in=1825, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← mk_one', mk_one]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 73.1s, verify 0.1s, in=1850, out=3666)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← mk_one', mk_one]
```

### `noise:3` · qwen3-lean-goedel · rollout 0 → **success**  (gen 15.1s, verify 0.1s, in=1850, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← mk_one', mk_one]
```

### `noise:3` · qwen3-lean-leannav · rollout 0 → **success**  (gen 7.6s, verify 0.1s, in=1850, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← mk_one', mk_one]
```

### `noise:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 8.9s, verify 0.1s, in=1850, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [mk_one, mk_one', RatFunc.ofFractionRing, Submonoid.coe_one, one_mul]
```

**lean_error:** tail step 1/1 ("simp only [mk_one, mk_one', RatFunc.ofFractionRing, Submonoid.coe_one, one_mul]"): simp made no progress
