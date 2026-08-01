# monotone_dual_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Monotone/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

**True premises at k:** `monotone_toDual_comp_iff`, `antitone_comp_ofDual_iff`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | · | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.3s, in=314, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h a b hab
    apply h
    exact hab
  · intro h a b hab
    apply h
    exact hab
```

**lean_error:** tail step 2/7 ('· intro h a b hab'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.4s, in=280, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Monotone, Monotone, Function.comp]
simp only [toDual_le_toDual, ofDual_le_ofDual]
rfl
```

**lean_error:** tail step 3/3 ('rfl'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 8.5s, verify 0.4s, in=303, out=508)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply iff.intro
intro h
convert h
simp [Function.comp]
intro h
convert h
simp [Function.comp]
```

**lean_error:** tail step 1/7 ('apply iff.intro'): unknown identifier 'iff.intro'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=640, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=585, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← monotone_toDual_comp_iff, ← antitone_comp_ofDual_iff]
rfl
```

**lean_error:** tail step 1/2 ('rw [← monotone_toDual_comp_iff, ← antitone_comp_ofDual_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=629, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=972, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
exact Iff.rfl
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.8s, in=917, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← monotone_toDual_comp_iff, ← antitone_comp_ofDual_iff]
simp only [Function.comp]
rw [antitone_comp_ofDual_iff]
```

**lean_error:** tail step 1/3 ('rw [← monotone_toDual_comp_iff, ← antitone_comp_ofDual_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=961, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=995, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 1.1s, verify 0.2s, in=978, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← antitone_comp_ofDual_iff, ← monotone_toDual_comp_iff]
simp only [Function.comp]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u
β : Type v
γ : Type w
δ : Type u_2
π : ι → Type u_3
...
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=984, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```
