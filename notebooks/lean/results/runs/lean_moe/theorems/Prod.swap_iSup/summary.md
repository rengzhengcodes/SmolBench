# Prod.swap_iSup   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteLattice.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [iSup, swap_sSup, ← range_comp, Function.comp]
```

**True premises at k:** `iSup`, `Prod.swap_sSup`, `Set.range_comp`, `Function.comp`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | · |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=356, out=507)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 117.6s, verify 0.1s, in=299, out=15156)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h1 : (iSup f).2 = ⨆ i, (f i).2 := by
  calc
    (iSup f).2 = (sup (Set.range f)).2 := by rw [iSup_eq_sup]
    _ = sup (Set.range f.image Prod.snd) := by
      simp [SupSet.prod_def, Prod.snd]
      <;> aesop
    _ = sup (Set.range (fun i => (f i).2)) := by
      rw [Set.image_range]
      <;> simp [Prod.snd]
      <;> aesop
    _ = ⨆ i, (f i).2 := by rw [iSup_eq_sup]
have h2 : (iSup f).1 = ⨆ i, (f i).1 := by
  calc
    (iSup f).1 = (sup (Set.range f)).1 := by rw [iSup_eq_sup]
    _ = sup (Set.range f.image Prod.fst) := by
      simp [SupSet.prod_def, Prod.fst]
      <;> aesop
    _ = sup (Set.range (fun i => (f i).1)) := by
      rw [Set.image_range]
      <;> simp [Prod.fst]
      <;> aesop
    _ = ⨆ i, (f i).1 := by rw [iSup_eq_sup]
have h3 : swap (iSup f) = (⨆ i, (f i).2, ⨆ i, (f i).1) := by
  calc
    swap (iSup f) = ((iSup f).2, (iSup f).1) := rfl
    _ = (⨆ i, (f i).2, ⨆ i, (f i).1) := by
      ext <;> simp_all [Prod.ext_iff]
      <;> try aesop
      <;> try { exact h1 }
      <;> try { exact h2 }
have h4 : ⨆ i, swap (f i) = (⨆ i, (f i).2, ⨆ i, (f i).1) := by
  apply Prod.ext
  · -- First component
    have h4₁ : (⨆ i, swap (f i)).1 = ⨆ i, (f i).2 := by
      calc
        (⨆ i, swap (f i)).1 = ⨆ i, (swap (f i)).1 := rfl
        _ = ⨆ i, (f i).2 := by
          apply iSup_congr
          intro i
          simp [swap]
    exact h4₁
  · -- Second component
    have h4₂ : (⨆ i, swap (f i)).2 = ⨆ i, (f i).1 := by
      calc
        (⨆ i, swap (f i)).2 = ⨆ i, (swap (f i)).2 := rfl
        _ = ⨆ i, (f i).1 := by
          apply iSup_congr
          intro i
          simp [swap]
    exact h4₂
have h5 : swap (iSup f) = ⨆ i, swap (f i) := by
  rw [h3]
  rw [h4]
exact h5
```

**lean_error:** tail step 1/54 ('have h1 : (iSup f).2 = ⨆ i, (f i).2 := by'): <stdin>:1:41: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=300, out=540)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup_swap]
```

**lean_error:** tail step 1/1 ('rw [iSup_swap]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.2s, in=1186, out=738)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold iSup
  simpa [Set.range_comp, Function.comp] using (Prod.swap_sSup (s := Set.range f))
```

**lean_error:** tail step 2/2 ('simpa [Set.range_comp, Function.comp] using (Prod.swap_sSup (s := Set.range f))'): type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 36.1s, verify 0.7s, in=1127, out=4073)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup]
rw [Prod.swap_sSup]
have h₁ : Prod.swap '' (range f) = range (Prod.swap ∘ f) := by rw [← Set.range_comp]
rw [h₁]
have h₂ : (Prod.swap ∘ f) = (fun i => swap (f i)) := by funext i; simp [Prod.swap]
rw [h₂]
rw [iSup]
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.9s, verify 0.4s, in=1144, out=479)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup]
rw [Prod.swap_sSup]
rw [← Set.range_comp]
rw [iSup]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.2s, in=2605, out=880)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold iSup
  simpa [Set.range_comp, Function.comp] using (swap_sSup (s := Set.range f))
```

**lean_error:** tail step 2/2 ('simpa [Set.range_comp, Function.comp] using (swap_sSup (s := Set.range f))'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 76.5s, verify 0.1s, in=2573, out=9549)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  swap (iSup f) = swap (sSup (range f)) := by rw [iSup]
  _ = sSup (Prod.swap '' (range f)) := by rw [Prod.swap_sSup]
  _ = sSup (range (Prod.swap ∘ f)) := by rw [← Set.range_comp]
  _ = sSup (range (fun i => swap (f i))) := by
    apply congr 1
    <;> ext i
    <;> simp [Prod.swap, Function.comp_apply]
    <;> rfl
  _ = iSup (fun i => swap (f i)) := by rw [iSup]
  _ = ⨆ i, swap (f i) := by rfl
```

**lean_error:** tail step 1/11 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 10.8s, verify 0.1s, in=2599, out=1044)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup, iSup, Function.comp]
rw [Prod.swap_sSup]
rw [← Set.range_comp]
```

**lean_error:** tail step 1/3 ('rw [iSup, iSup, Function.comp]'): failed to rewrite using equation theorems for 'Function.comp'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 4.7s, in=2481, out=1140)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold iSup
  simpa [range_comp] using (swap_sSup (s := range f))
```

**lean_error:** tail step 2/2 ('simpa [range_comp] using (swap_sSup (s := range f))'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 51.1s, verify 0.1s, in=2817, out=6157)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  swap (iSup f) = swap (sSup (range f)) := by rw [iSup]
  _ = sSup (Prod.swap '' (range f)) := by rw [Prod.swap_sSup]
  _ = sSup (range (fun i => swap (f i))) := by
    rw [← Set.range_comp]
    <;> rfl
  _ = iSup (fun i => swap (f i)) := by rw [iSup]
  _ = ⨆ i, swap (f i) := by rfl
```

**lean_error:** tail step 1/8 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.3s, verify 0.1s, in=2583, out=764)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, Set.range_comp.symm, iSup]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, Set.range_comp.symm, iSup]'): tactic 'rewrite' failed, equality or iff proof expected
