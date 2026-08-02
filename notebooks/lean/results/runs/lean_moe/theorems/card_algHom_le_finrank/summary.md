# card_algHom_le_finrank   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/FreeModule/Finite/Matrix.lean`  

**Ground-truth tail (from k):**
```lean
apply rank_lt_aleph0
```

**True premises at k:** `rank_lt_aleph0`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.1s, in=375, out=862)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (rank_lt_aleph_0 (K:=K) (M:=M))
```

**lean_error:** tail step 1/1 ('simpa using (rank_lt_aleph_0 (K:=K) (M:=M))'): unknown identifier 'rank_lt_aleph_0'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 15.6s, verify 0.1s, in=331, out=1743)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem your_theorem_name : Module.rank K M < ℵ₀ := by
  have h_main : Module.rank K M < ℵ₀ := by
    apply Module.rank_lt_aleph0_of_fg
    <;> assumption
    <;> try infer_instance
    <;> try exact this
  
  exact h_main
```

**lean_error:** tail step 1/7 ('theorem your_theorem_name : Module.rank K M < ℵ₀ := by'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.1s, in=319, out=463)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Module.Finite.rank_lt_aleph₀
```

**lean_error:** tail step 1/1 ('exact Module.Finite.rank_lt_aleph₀'): unknown constant 'Module.Finite.rank_lt_aleph₀'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=720, out=429)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact rank_lt_aleph0
```

**lean_error:** tail step 1/1 ('exact rank_lt_aleph0'): type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 36.5s, verify 0.1s, in=694, out=4314)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply rank_lt_aleph0
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.1s, in=665, out=398)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact rank_lt_aleph0
```

**lean_error:** tail step 1/1 ('exact rank_lt_aleph0'): type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1565, out=294)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact rank_lt_aleph0
```

**lean_error:** tail step 1/1 ('exact rank_lt_aleph0'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 12.4s, verify 0.1s, in=1556, out=1334)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact rank_lt_aleph0
```

**lean_error:** tail step 1/1 ('exact rank_lt_aleph0'): type mismatch

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 41.7s, verify 0.3s, in=1506, out=4784)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact rank_lt_aleph0
```

**lean_error:** tail step 1/1 ('exact rank_lt_aleph0'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.7s, verify 0.1s, in=1485, out=784)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (rank_lt_aleph0 (R:=K) (M:=M))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=1688, out=428)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact rank_lt_aleph0
```

**lean_error:** tail step 1/1 ('exact rank_lt_aleph0'): type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=1513, out=422)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact rank_lt_aleph0
```

**lean_error:** tail step 1/1 ('exact rank_lt_aleph0'): type mismatch
