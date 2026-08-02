# CategoryTheory.IsPushout.of_isBilimit   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/CommSq.lean`  

**Ground-truth tail (from k):**
```lean
convert IsPushout.of_is_coproduct' h.isColimit HasZeroObject.zeroIsInitial
```

**True premises at k:** `CategoryTheory.IsPushout.of_is_coproduct'`, `CategoryTheory.Limits.HasZeroObject.zeroIsInitial`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.7s, verify 0.9s, in=361, out=2920)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨by simp, ?_⟩
  simpa using h.isColimit
```

**lean_error:** tail step 2/2 ('simpa using h.isColimit'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 144.0s, verify 0.1s, in=308, out=18606)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' IsPushout.mk (fun D' f' g' hfg => _) (fun D' f' g' hfg u₁ u₂ hu₁ hu₂ => _)
  · intro D' f' g' hfg
    have h₁ : ∃! (u : P → D'), b.inl ∘ u = f' ∧ b.inr ∘ u = g' := h f' g'
    obtain ⟨u, hu, hu'⟩ := h₁
    exact ⟨u, hu.1, hu.2⟩
  · intro D' f' g' hfg u₁ u₂ hu₁ hu₂
    have h₁ : ∃! (u : P → D'), b.inl ∘ u = f' ∧ b.inr ∘ u = g' := h f' g'
    obtain ⟨u, hu, hu'⟩ := h₁
    have h₂ : u₁ = u := by
      apply hu'
      exact ⟨hu₁.1, hu₁.2⟩
    have h₃ : u₂ = u := by
      apply hu'
      exact ⟨hu₂.1, hu₂.2⟩
    rw [h₂, h₃]
```

**lean_error:** tail step 1/15 ("refine' IsPushout.mk (fun D' f' g' hfg => _) (fun D' f' g' hfg u₁ u₂ hu₁ hu₂ => _)"): application type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.7s, verify 0.2s, in=301, out=1153)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsPushout.of_isColimit
· simp
· exact h.2
```

**lean_error:** tail step 1/3 ('apply IsPushout.of_isColimit'): tactic 'apply' failed, failed to unify

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=769, out=851)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine IsPushout.of_is_coproduct' ?_ ?_
· exact h.isColimit
· exact (CategoryTheory.Limits.HasZeroObject.zeroIsInitial (C:=C))
```

**lean_error:** tail step 1/3 ("refine IsPushout.of_is_coproduct' ?_ ?_"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 47.4s, verify 0.1s, in=731, out=6400)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_zero_initial : IsInitial (0 : C) := zeroIsInitial
have h_pushout : IsPushout (zeroIsInitial.to X) (zeroIsInitial.to Y) b.inl b.inr :=
  CategoryTheory.IsPushout.of_is_coproduct' h.2 h_zero_initial
have h_x : zeroIsInitial.to X = (0 : 0 → X) := by
  have h₁ : IsInitial (0 : C) := zeroIsInitial
  have h₂ : ∀ (X : C), (zeroIsInitial : IsInitial (0 : C)).to X = (0 : 0 → X) :=
    fun X => h₁.unique (zero : 0 → X)
  exact h₂ X
have h_y : zeroIsInitial.to Y = (0 : 0 → Y) := by
  have h₁ : IsInitial (0 : C) := zeroIsInitial
  have h₂ : ∀ (Y : C), (zeroIsInitial : IsInitial (0 : C)).to Y = (0 : 0 → Y) :=
    fun Y => h₁.unique (zero : 0 → Y)
  exact h₂ Y
rw [h_x] at h_pushout
rw [h_y] at h_pushout
exact h_pushout
```

**lean_error:** tail step 1/16 ('have h_zero_initial : IsInitial (0 : C) := zeroIsInitial'): unknown identifier 'zeroIsInitial'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.2s, in=719, out=515)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct'
· exact h.2
· exact zeroIsInitial
```

**lean_error:** tail step 1/3 ("apply CategoryTheory.IsPushout.of_is_coproduct'"): tactic 'apply' failed, failed to unify

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=1100, out=637)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine IsPushout.of_is_coproduct' ?_ ?_
· exact h.isColimit
· exact CategoryTheory.Limits.HasZeroObject.zeroIsInitial (C:=C)
```

**lean_error:** tail step 1/3 ("refine IsPushout.of_is_coproduct' ?_ ?_"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 27.8s, verify 0.1s, in=1079, out=3839)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : IsInitial (0 : C) := zeroIsInitial
have h₂ : IsColimit b := h.colimit
exact IsPushout.of_is_coproduct' h₂ h₁
```

**lean_error:** tail step 1/3 ('have h₁ : IsInitial (0 : C) := zeroIsInitial'): unknown identifier 'zeroIsInitial'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.5s, verify 0.2s, in=1054, out=1034)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct'
· exact h.2
· exact CategoryTheory.Limits.HasZeroObject.zeroIsInitial
```

**lean_error:** tail step 1/3 ("apply CategoryTheory.IsPushout.of_is_coproduct'"): tactic 'apply' failed, failed to unify

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=1085, out=848)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine IsPushout.of_is_coproduct' ?_ ?_
  · exact h.isColimit
  · exact CategoryTheory.Limits.HasZeroObject.zeroIsInitial (C:=C)
```

**lean_error:** tail step 1/3 ("refine IsPushout.of_is_coproduct' ?_ ?_"): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 23.3s, verify 0.1s, in=1135, out=3209)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hcol : Limits.IsColimit (BinaryCofan.mk b.inl b.inr) := h.colimit
have t : IsInitial (0 : C) := CategoryTheory.Limits.HasZeroObject.zeroIsInitial inst✝¹
apply CategoryTheory.IsPushout.of_is_coproduct' hcol t
```

**lean_error:** tail step 1/3 ('have hcol : Limits.IsColimit (BinaryCofan.mk b.inl b.inr) := h.colimit'): invalid field 'colimit', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.colimit'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.2s, in=1066, out=569)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsPushout.of_is_coproduct'
· exact h.isColimit
· exact zeroIsInitial
```

**lean_error:** tail step 1/3 ("apply IsPushout.of_is_coproduct'"): tactic 'apply' failed, failed to unify
