# Prod.swap_iInf   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteLattice.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [iInf, swap_sInf, ← range_comp, Function.comp]
```

**True premises at k:** `iInf`, `Prod.swap_sInf`, `Set.range_comp`, `Function.comp`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.1s, verify 0.1s, in=356, out=758)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 148.4s, verify 0.1s, in=299, out=18335)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : OrderIso.prodComm (iInf f) = iInf (fun i => OrderIso.prodComm (f i)) := by
  have h₁₁ : OrderIso.prodComm (iInf f) = OrderIso.prodComm (iInf (Set.range f)) := by
    simp [iInf_eq_iInf_range]
  rw [h₁₁]
  have h₁₂ : OrderIso.prodComm (iInf (Set.range f)) = iInf (OrderIso.prodComm '' Set.range f) := by
    apply OrderIso.prodComm.map_iInf
  rw [h₁₂]
  have h₁₃ : OrderIso.prodComm '' Set.range f = Set.range (fun i => OrderIso.prodComm (f i)) := by
    ext x
    simp [Set.mem_range, Set.mem_image]
    <;> aesop
  rw [h₁₃]
  <;> simp [iInf_eq_iInf_range]
  <;> congr 1 <;> ext i <;> simp
have h₂ : OrderIso.prodComm (iInf f) = swap (iInf f) := by
  have h₂₁ : OrderIso.prodComm = fun p : α × β => p.swap := by
    ext p
    <;> simp [OrderIso.prodComm_apply]
    <;> rfl
  rw [h₂₁]
  <;> rfl
have h₃ : iInf (fun i => OrderIso.prodComm (f i)) = iInf (fun i => swap (f i)) := by
  have h₃₁ : OrderIso.prodComm = fun p : α × β => p.swap := by
    ext p
    <;> simp [OrderIso.prodComm_apply]
    <;> rfl
  rw [h₃₁]
  <;> rfl
have h₄ : swap (iInf f) = iInf (fun i => swap (f i)) := by
  calc
    swap (iInf f) = OrderIso.prodComm (iInf f) := by
      rw [h₂]
      <;> rfl
    _ = iInf (fun i => OrderIso.prodComm (f i)) := by rw [h₁]
    _ = iInf (fun i => swap (f i)) := by rw [h₃]
exact h₄
```

**lean_error:** tail step 1/36 ('have h₁ : OrderIso.prodComm (iInf f) = iInf (fun i => OrderIso.prodComm (f i)) := by'): <stdin>:1:84: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.8s, verify 0.1s, in=300, out=761)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext <;> simp [Prod.iInf]
```

**lean_error:** tail step 1/1 ('ext <;> simp [Prod.iInf]'): unknown constant 'Prod.iInf'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.3s, verify 0.2s, in=1186, out=1238)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
dsimp [iInf]
simpa [Set.range_comp, Function.comp] using (Prod.swap_sInf (s := Set.range f))
```

**lean_error:** tail step 2/2 ('simpa [Set.range_comp, Function.comp] using (Prod.swap_sInf (s := Set.range f))'): type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 18.3s, verify 0.1s, in=1127, out=2021)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  swap (iInf f) = swap (sInf (range f)) := by rw [iInf]
  _ = sInf (Prod.swap '' (range f)) := by rw [Prod.swap_sInf]
  _ = sInf (range (fun i => swap (f i))) := by
    have h : Prod.swap '' (range f) = range (fun i => swap (f i)) := by
      have h1 : range (Prod.swap ∘ f) = Prod.swap '' (range f) := by rw [Set.range_comp]
      have h2 : (Prod.swap ∘ f) = (fun i => swap (f i)) := by
        funext i
        simp [Prod.swap, Function.comp]
        <;> aesop
      rw [h2] at h1
      exact h1
    rw [h]
  _ = ⨅ i, swap (f i) := rfl
```

**lean_error:** tail step 1/14 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.3s, verify 0.3s, in=1144, out=514)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iInf, iInf]
rw [Prod.swap_sInf]
rw [← Set.range_comp]
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

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.9s, verify 0.2s, in=2605, out=901)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold iInf
  simpa [range_comp] using (swap_sInf (s := Set.range f))
```

**lean_error:** tail step 2/2 ('simpa [range_comp] using (swap_sInf (s := Set.range f))'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 29.5s, verify 0.1s, in=2573, out=3323)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  swap (iInf f) = swap (sInf (range f)) := by rw [iInf]
  _ = sInf (Prod.swap '' (range f)) := by rw [Prod.swap_sInf]
  _ = sInf (range (Prod.swap ∘ f)) := by
    rw [← Set.range_comp]
    <;> simp [Function.comp]
  _ = sInf (range (fun i => swap (f i))) := by
    congr_arg sInf
    funext i
    simp [Prod.swap]
    <;> rfl
  _ = ⨅ i, swap (f i) := by rw [iInf]
```

**lean_error:** tail step 1/12 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.0s, verify 0.3s, in=2599, out=521)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [iInf]
rw [Prod.swap_sInf]
rw [← Set.range_comp]
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

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.1s, verify 0.2s, in=2481, out=1181)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold iInf
  simpa [Set.range_comp] using (swap_sInf (s := Set.range f))
```

**lean_error:** tail step 2/2 ('simpa [Set.range_comp] using (swap_sInf (s := Set.range f))'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 43.0s, verify 0.1s, in=2817, out=4876)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  swap (iInf f) = swap (sInf (range f)) := by rw [iInf]
  _ = sInf (Prod.swap '' (range f)) := by rw [Prod.swap_sInf]
  _ = sInf (range (fun i => swap (f i))) := by
    have h : Prod.swap '' (range f) = range (fun i => swap (f i)) := by
      have h1 : range (Prod.swap ∘ f) = Prod.swap '' (range f) := by rw [Set.range_comp]
      have h2 : Prod.swap ∘ f = fun i => swap (f i) := by
        funext i
        simp [Prod.swap_def, Function.comp_apply]
      rw [h2] at h1
      exact h1.symm
    rw [h]
  _ = ⨅ i, swap (f i) := by
    rw [iInf]
    <;> rfl
```

**lean_error:** tail step 1/15 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.7s, verify 0.3s, in=2583, out=524)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [iInf]
rw [Prod.swap_sInf]
rw [← Set.range_comp]
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
