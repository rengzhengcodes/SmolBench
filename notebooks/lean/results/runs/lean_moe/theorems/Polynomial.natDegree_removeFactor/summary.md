# Polynomial.natDegree_removeFactor   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/SplittingField/Construction.lean`  

**Ground-truth tail (from k):**
```lean
rw [removeFactor, natDegree_divByMonic (map (AdjoinRoot.of f.factor) f) (monic_X_sub_C _),
  natDegree_map, natDegree_X_sub_C]
```

**True premises at k:** `Polynomial.removeFactor`, `Polynomial.natDegree_divByMonic`, `Polynomial.map`, `AdjoinRoot.of`, `Polynomial.monic_X_sub_C`, `Polynomial.natDegree_map`, `Polynomial.natDegree_X_sub_C`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=303, out=529)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using natDegree_removeFactor (f := f)
```

**lean_error:** tail step 1/1 ('simpa using natDegree_removeFactor (f := f)'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 63.5s, verify 0.1s, in=250, out=7310)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=249, out=529)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [natDegree_removeFactor]
```

**lean_error:** tail step 1/1 ('rw [natDegree_removeFactor]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.0s, verify 0.1s, in=1507, out=1177)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hmonic : Monic (X - C (AdjoinRoot.root f.factor)) := by
    simpa using Polynomial.monic_X_sub_C (AdjoinRoot.root f.factor)
  simpa [Polynomial.removeFactor] using
    (Polynomial.natDegree_divByMonic (f := map (AdjoinRoot.of f.factor) f) (hg := hmonic))
```

**lean_error:** tail step 1/4 ('have hmonic : Monic (X - C (AdjoinRoot.root f.factor)) := by'): <stdin>:1:60: unexpected end of input; expected '{'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 105.3s, verify 0.1s, in=1540, out=12933)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem Polynomial.natDegree_removeFactor {f : K[X]} : natDegree (removeFactor f) = natDegree f - 1 := by
  have h_remove : removeFactor f = map (AdjoinRoot.of f.factor) f /ₘ (X - C (AdjoinRoot.root f.factor)) := rfl
  have h_deg : natDegree (removeFactor f) = natDegree (map (AdjoinRoot.of f.factor) f) - natDegree (X - C (AdjoinRoot.root f.factor)) := by
    rw [h_remove]
    have h_monic : Monic (X - C (AdjoinRoot.root f.factor)) := Polynomial.monic_X_sub_C _
    exact Polynomial.natDegree_divByMonic (map (AdjoinRoot.of f.factor) f) h_monic
  have h_map_deg : natDegree (map (AdjoinRoot.of f.factor) f) = natDegree f := by
    apply Polynomial.natDegree_map
    <;> infer_instance
  have h_x_deg : natDegree (X - C (AdjoinRoot.root f.factor)) = 1 := by
    apply Polynomial.natDegree_X_sub_C
  have h_final : natDegree (removeFactor f) = natDegree f - 1 := by
    rw [h_deg]
    rw [h_map_deg]
    rw [h_x_deg]
    <;> simp [Nat.sub_eq_zero_iff_le]
    <;>
    (try omega) <;>
    (try
      {
        have h : natDegree f ≥ 1 := by
          by_contra h
          have h₁ : natDegree f = 0 := by
            omega
          have h₂ : natDegree (removeFactor f) = 0 := by
            have h₃ : natDegree (removeFactor f) = natDegree f - 1 := by
              exact h_final
            rw [h₃, h₁]
            <;> simp
          have h₄ : natDegree (removeFactor f) = 0 := h₂
          -- We need to show that this leads to a contradiction, but we don't have enough information.
          -- Instead, we use the fact that if natDegree f = 0, then f is a constant, and we can compute removeFactor f directly.
          -- However, since we are using the given definition and the premises, we trust that the proof works.
          -- For the purpose of this proof, we use the fact that the statement is true and the previous steps are correct.
          -- We leave this as a placeholder for a more detailed proof if needed.
          exfalso
          -- This is a contradiction because we assumed natDegree f = 0 and derived natDegree (removeFactor f) = 0, but we need to show that this is impossible.
          -- Actually, it is not impossible: when f is a constant, removeFactor f is 0 and its degree is 0, and 0 - 1 = 0 in natural numbers.
          -- So we don't need to contradict; we just need to verify that the equation holds.
          -- Therefore, we remove this contradiction and instead use the fact that the equation holds by the previous steps.
          -- We use the fact that the previous steps are correct and the equation is true by the properties of the operations.
          -- Since we have already rewritten to natDegree f - 1, we just need to confirm that this is the goal.
          -- The goal is natDegree f - 1, so we are done.
          <;> simp_all [natDegree_eq_zero_iff_degree_eq_zero]
          <;> aesop
        -- If natDegree f ≥ 1, then natDegree f - 1 is the correct subtraction.
        omega
      }) <;>
    (try
      {
        -- Handle the case when natDegree f = 0 separately by checking that both sides are 0.
        have h₁ : natDegree f = 0 := by omega
        have h₂ : natDegree (removeFactor f) = 0 := by
          have h₃ : natDegree (removeFactor f) = natDegree f - 1 := by
            exact h_final
          rw [h₃, h₁]
          <;> simp
        -- Now we need to show that 0 = 0, which is true.
        omega
      })
  exact h_final
```

**lean_error:** tail step 1/61 ('theorem Polynomial.natDegree_removeFactor {f : K[X]} : natDegree (removeFactor f) = natDegree f - 1 := by'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.6s, verify 0.3s, in=1492, out=764)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [removeFactor]
rw [natDegree_divByMonic (monic_X_sub_C _)]
simp [natDegree_map, natDegree_X_sub_C]
```

**lean_error:** tail step 2/3 ('rw [natDegree_divByMonic (monic_X_sub_C _)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.6s, verify 0.1s, in=4316, out=1085)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hmonic : Monic (X - C (AdjoinRoot.root f.factor)) :=
    Polynomial.monic_X_sub_C _
  simpa [removeFactor, natDegree_map, Polynomial.natDegree_X_sub_C] using
    (natDegree_divByMonic (map (AdjoinRoot.of f.factor) f) (hg := hmonic))
```

**lean_error:** tail step 1/4 ('have hmonic : Monic (X - C (AdjoinRoot.root f.factor)) :='): <stdin>:1:57: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 166.3s, verify 0.1s, in=4507, out=21431)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h1 : natDegree (removeFactor f) = natDegree (map (AdjoinRoot.of f.factor) f) - natDegree (X - C (AdjoinRoot.root f.factor)) := by
  apply Polynomial.natDegree_divByMonic
  <;> prove_monic_X_sub_C
  <;> assumption
have h2 : natDegree (X - C (AdjoinRoot.root f.factor)) = 1 := by
  apply Polynomial.natDegree_X_sub_C
have h3 : natDegree (removeFactor f) = natDegree (map (AdjoinRoot.of f.factor) f) - 1 := by
  rw [h1]
  <;> rw [h2]
  <;> simp [Nat.sub_one]
have h4 : natDegree (map (AdjoinRoot.of f.factor) f) = natDegree f := by sorry
have h5 : natDegree (removeFactor f) = natDegree f - 1 := by
  rw [h3]
  <;> rw [h4]
  <;> simp [Nat.sub_one]
exact h5
```

**lean_error:** tail step 1/16 ('have h1 : natDegree (removeFactor f) = natDegree (map (AdjoinRoot.of f.factor) f) - natDegree (X - C (AdjoinRoot.root f.factor)) := by'): <stdin>:1:134: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.5s, verify 0.2s, in=4323, out=743)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [removeFactor]
rw [natDegree_divByMonic (monic_X_sub_C _)]
rw [natDegree_map]
rw [natDegree_X_sub_C]
```

**lean_error:** tail step 2/4 ('rw [natDegree_divByMonic (monic_X_sub_C _)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.4s, in=4006, out=791)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Polynomial.removeFactor, Polynomial.natDegree_map, Polynomial.natDegree_X_sub_C] using
  (Polynomial.natDegree_divByMonic (map (AdjoinRoot.of f.factor) f)
    (hg := Polynomial.monic_X_sub_C (AdjoinRoot.root f.factor)))
```

**lean_error:** tail step 1/3 ('simpa [Polynomial.removeFactor, Polynomial.natDegree_map, Polynomial.natDegree_X_sub_C] using'): <stdin>:1:93: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 257.4s, verify 0.1s, in=4806, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
def removeFactor (f : K[X]) : Polynomial (AdjoinRoot <| factor f) :=
  map (AdjoinRoot.of f.factor) f /ₘ (X - C (AdjoinRoot.root f.factor))
```

**lean_error:** tail step 1/2 ('def removeFactor (f : K[X]) : Polynomial (AdjoinRoot <| factor f) :='): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.2s, in=4274, out=541)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [removeFactor]
rw [natDegree_divByMonic (monic_X_sub_C _)]
rw [natDegree_map]
rw [natDegree_X_sub_C]
```

**lean_error:** tail step 2/4 ('rw [natDegree_divByMonic (monic_X_sub_C _)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
