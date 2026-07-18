# Polynomial.roots_X_pow_char_sub_C_pow   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
rwa [pow_one, iterateFrobeniusEquiv_one] at H
```

**True premises at k:** `pow_one`, `iterateFrobeniusEquiv_one`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | · ✓ · · |
| `hint:3` | · · ✓ · |
| `noise:3` | ✓ ✘ · ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=348, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [pow_one] at H
```

**lean_error:** tail step 1/1 ('rwa [pow_one] at H'): tactic 'assumption' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=348, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [pow_one, pow_one] at H
```

**lean_error:** tail step 1/1 ('rwa [pow_one, pow_one] at H'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=348, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [pow_one, pow_one] at H
```

**lean_error:** tail step 1/1 ('rwa [pow_one, pow_one] at H'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.0s, verify 0.1s, in=348, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [pow_one, pow_one, ← iterateFrobeniusEquiv] at H
```

**lean_error:** tail step 1/1 ('rwa [pow_one, pow_one, ← iterateFrobeniusEquiv] at H'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.7s, verify 0.2s, in=713, out=8)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp at H
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.2s, in=713, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using H
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.0s, verify 0.2s, in=713, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pow_one, iterateFrobeniusEquiv_one] at H
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.2s, verify 0.2s, in=713, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pow_one, iterateFrobeniusEquiv_one] at H
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.4s, verify 0.2s, in=1468, out=8)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp at H
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.6s, verify 0.2s, in=1468, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [H]
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.8s, verify 0.2s, in=1468, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using H
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 3.1s, verify 0.2s, in=1468, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [H]
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.2s, in=1492, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using H
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=1492, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [pow_one, mul_one] using H
```

**lean_error:** tail step 1/1 ('simpa only [pow_one, mul_one] using H'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.8s, verify 0.2s, in=1492, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [pow_one, iterateFrobeniusEquiv_one] at H
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.4s, verify 0.1s, in=1492, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rwa [pow_one p, mul_one, iterateFrobeniusEquiv_one] at H
```

**lean_error:** tail step 1/1 ('rwa [pow_one p, mul_one, iterateFrobeniusEquiv_one] at H'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
