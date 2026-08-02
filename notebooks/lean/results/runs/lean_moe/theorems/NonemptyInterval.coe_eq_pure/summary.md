# NonemptyInterval.coe_eq_pure   (k=0, 1 tactics total)

file: `Mathlib/Order/Interval.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Interval.coe_inj, coe_pure_interval]
```

**True premises at k:** `Interval.coe_inj`, `NonemptyInterval.coe_pure_interval`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.6s, verify 0.2s, in=322, out=3262)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  cases s
  ext
  simpa using h
· intro h
  simpa [h]
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 186.5s, verify 0.2s, in=264, out=24154)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  have h_inj : Function.Injective (fun s : NonemptyInterval α => ↑s) := by
    intro s₁ s₂ h
    cases s₁ <;> cases s₂ <;>
      simp_all [Interval.mk.injEq]
    <;>
      (try aesop) <;>
      (try
        {
          subst_vars
          <;>
          apply ProofIrrelevance.unique
        }) <;>
      (try aesop)
  have h₂ : ↑(pure a) = Interval.pure a := by simp [pure, Interval.pure]
  have h₃ : s = pure a := by
    apply h_inj
    calc
      ↑s = Interval.pure a := h
      _ = ↑(pure a) := by rw [h₂]
  exact h₃
· intro h
  have h₁ : ↑s = Interval.pure a := by
    rw [h]
    <;> simp [pure, Interval.pure]
    <;> aesop
  exact h₁
```

**lean_error:** tail step 2/28 ('· intro h'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.2s, in=264, out=600)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  exact congr_arg _ h
· intro h
  rw [h]
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.8s, verify 0.1s, in=661, out=1073)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [NonemptyInterval.coe_pure_interval] using (Interval.coe_inj (s:=s) (t:=pure a))
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 9.2s, verify 0.1s, in=608, out=999)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  ↑s = Interval.pure a ↔ ↑s = (pure a : Interval α) := by rw [← coe_pure_interval]
  _ ↔ s = pure a := by apply Interval.coe_inj
```

**lean_error:** tail step 1/3 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.1s, verify 0.1s, in=613, out=542)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← NonemptyInterval.coe_pure_interval a, Interval.coe_inj]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.2s, verify 0.1s, in=2332, out=1184)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [NonemptyInterval.coe_pure_interval] using (Interval.coe_inj (s:=s) (t:=pure a))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 10.1s, verify 0.1s, in=2348, out=1102)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  ↑s = Interval.pure a ↔ (s : Interval α) = (pure a : Interval α) := by rw [NonemptyInterval.coe_pure_interval]
  _ ↔ s = pure a := by apply Interval.coe_inj
```

**lean_error:** tail step 1/3 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.6s, verify 0.2s, in=2348, out=602)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← NonemptyInterval.coe_pure_interval]
exact Interval.coe_inj
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.9s, verify 0.1s, in=2180, out=1118)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [NonemptyInterval.coe_pure_interval] using (Interval.coe_inj (s:=s) (t:=pure a))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 51.0s, verify 0.2s, in=2590, out=5799)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
  · intro h
    have h₁ : (s : Interval α) = Interval.pure a := h
    have h₂ : (s : Interval α) = (pure a : Interval α) := by
      rw [h₁]
      rw [← NonemptyInterval.coe_pure_interval]
    exact Interval.coe_inj.mp h₂
  · intro h
    have h₁ : (s : Interval α) = (pure a : Interval α) := Interval.coe_inj.mpr h
    have h₂ : (s : Interval α) = Interval.pure a := by
      rw [h₁]
      rw [NonemptyInterval.coe_pure_interval]
    exact h₂
```

**lean_error:** tail step 2/13 ('· intro h'): unsolved goals

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.7s, verify 0.1s, in=2304, out=437)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← NonemptyInterval.coe_pure_interval a, Interval.coe_inj]
```
