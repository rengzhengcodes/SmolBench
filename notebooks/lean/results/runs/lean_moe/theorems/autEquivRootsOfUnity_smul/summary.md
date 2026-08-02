# autEquivRootsOfUnity_smul   (k=6, 7 tactics total)

file: `Mathlib/FieldTheory/KummerExtension.lean`  

**Ground-truth tail (from k):**
```lean
exact smul_comm _ _ _
```

**True premises at k:** `SMulCommClass.smul_comm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.3s, in=510, out=1275)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [mul_comm, mul_left_comm, mul_assoc]
```

**lean_error:** tail step 1/1 ('simp [mul_comm, mul_left_comm, mul_assoc]'): simp made no progress

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 86.5s, verify 0.1s, in=481, out=11833)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  (autEquivRootsOfUnity ⋯ hn H L) σ • (ζ ^ i • rootOfSplitsXPowSubC hn a L) = (autEquivRootsOfUnity hζ hn H L) σ • (ζ ^ i • rootOfSplitsXPowSubC hn a L) := by rfl
  _ = ((autEquivRootsOfUnity hζ hn H L) σ * ζ ^ i) • rootOfSplitsXPowSubC hn a L := by rw [smul_smul]
  _ = (ζ ^ i * (autEquivRootsOfUnity hζ hn H L) σ) • rootOfSplitsXPowSubC hn a L := by
    rw [mul_comm]
    <;> simp [mul_assoc]
  _ = ζ ^ i • (autEquivRootsOfUnity hζ hn H L) σ • rootOfSplitsXPowSubC hn a L := by
    rw [smul_smul]
    <;> simp [mul_assoc]
```

**lean_error:** tail step 1/9 ('calc'): <stdin>:1:4: unexpected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=462, out=674)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
smul_smul
<;> simp_all [mul_smul, smul_mul, mul_assoc]
<;> congr 1
<;> simp_all [autEquivRootsOfUnity]
```

**lean_error:** tail step 1/4 ('smul_smul'): <stdin>:1:1: unknown tactic
