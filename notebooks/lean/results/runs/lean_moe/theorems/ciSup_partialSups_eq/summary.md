# ciSup_partialSups_eq   (k=3, 4 tactics total)

file: `Mathlib/Order/PartialSups.lean`  

**Ground-truth tail (from k):**
```lean
rwa [bddAbove_range_partialSups]
```

**True premises at k:** `bddAbove_range_partialSups`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.0s, verify 0.5s, in=304, out=1278)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases h with ⟨a, ha⟩
refine ⟨a, ?_⟩
rintro _ ⟨n, rfl⟩
simp [partialSups] at *
apply sSup_le
intro y
rintro ⟨i, hi, rfl⟩
exact ha _ ⟨i, rfl⟩
```

**lean_error:** tail step 5/8 ('apply sSup_le'): tactic 'apply' failed, failed to unify

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 116.5s, verify 0.5s, in=249, out=14051)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨M, hM⟩ := h
refine' ⟨M, _⟩
intro y hy
rcases hy with ⟨n, rfl⟩
have h₂ : (partialSups f) n = Finset.sup (Finset.range n) f := rfl
rw [h₂]
apply Finset.sup_le
intro i hi
have h₃ : f i ∈ Set.range f := Set.mem_range_self f i
exact hM h₃

<details>
<summary>Explanation</summary>
We first obtain an upper bound `M` for the range of `f` from the hypothesis `h`. To show that the set of partial suprema is bounded above by `M`, we take an arbitrary element `y` in the range of the partial suprema function, which means `y = (partialSups f) n` for some `n`. By definition, `(partialSups f) n` is the supremum of `{f i | i < n}`. Since each `f i` is in the range of `f`, we have `f i ≤ M`. Therefore, `M` is an upper bound for the set `{f i | i < n}`, and hence its supremum `(partialSups f) n` is also ≤ `M`. This shows that `M` is an upper bound for the entire set of partial suprema.
</details>
```

**lean_error:** tail step 5/14 ('have h₂ : (partialSups f) n = Finset.sup (Finset.range n) f := rfl'): failed to synthesize instance

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.1s, verify 0.3s, in=251, out=564)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨M, hM⟩ := h
use M
intro n
apply csupr_le
intro i hi
apply hM
exact ⟨i, rfl⟩
```

**lean_error:** tail step 4/7 ('apply csupr_le'): unknown identifier 'csupr_le'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.7s, verify 0.1s, in=586, out=931)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (bddAbove_range_partialSups (f:=f)).2 h
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 31.0s, verify 0.1s, in=543, out=3579)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.mpr h
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 56.5s, verify 0.2s, in=536, out=6187)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [bddAbove_range_partialSups]
exact h
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.6s, verify 0.1s, in=1281, out=1046)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (bddAbove_range_partialSups (f:=f)).2 h
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 71.2s, verify 0.2s, in=1238, out=8354)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : (fun n => (partialSups f) n) = partialSups f := by funext n; rfl
have h₃ : BddAbove (Set.range (partialSups f)) := (bddAbove_range_partialSups f).mp h
rw [h₁] at *
exact h₃
```

**lean_error:** tail step 2/4 ('have h₃ : BddAbove (Set.range (partialSups f)) := (bddAbove_range_partialSups f).mp h'): function expected at

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=1222, out=524)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (bddAbove_range_partialSups f).mpr h
```

**lean_error:** tail step 1/1 ('exact (bddAbove_range_partialSups f).mpr h'): function expected at

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.4s, verify 0.1s, in=1210, out=576)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (bddAbove_range_partialSups (f:=f)).mpr h
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 21.1s, verify 0.2s, in=1355, out=2447)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply (bddAbove_range_partialSups).mpr
exact h
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.0s, verify 0.5s, in=1228, out=451)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [bddAbove_range_partialSups]
exact h
```
