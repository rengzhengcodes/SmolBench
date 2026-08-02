# isLeast_csInf   (k=1, 2 tactics total)

file: `Mathlib/Order/ConditionallyCompleteLattice/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨argminOn_mem _ _ _ _, fun a ha => argminOn_le id _ _ ha⟩
```

**True premises at k:** `Function.argminOn_mem`, `Function.argminOn_le`, `id`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.1s, in=334, out=888)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨argminOn_mem (f:=id) (s:=s) hs, ?_⟩
intro y hy
have h := argminOn_le (f:=id) (s:=s) hs hy
simpa using h
```

**lean_error:** tail step 1/4 ('refine ⟨argminOn_mem (f:=id) (s:=s) hs, ?_⟩'): application type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 28.1s, verify 0.1s, in=284, out=3168)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : IsMinOn id (argminOn id s hs) s := IsMinOn.argminOn hs
exact ⟨h.1, fun x hx => by
  have h₂ : id (argminOn id s hs) ≤ id x := h.2 x hx
  simpa using h₂⟩
```

**lean_error:** tail step 1/4 ('have h : IsMinOn id (argminOn id s hs) s := IsMinOn.argminOn hs'): unknown identifier 'IsMinOn'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.2s, verify 0.1s, in=283, out=500)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsLeast.intro
· exact mem_argminOn_id s hs
· intro y hy
  exact argminOn_le_id s hs y hy
```

**lean_error:** tail step 1/4 ('apply IsLeast.intro'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.2s, in=1012, out=946)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine ⟨?_, ?_⟩
· exact Function.argminOn_mem (s:=s) (hs:=hs)
· intro b hb
  simpa using (Function.argminOn_le (f:=id) (s:=s) (a:=b) hb)
```

**lean_error:** tail step 2/4 ('· exact Function.argminOn_mem (s:=s) (hs:=hs)'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 26.5s, verify 0.1s, in=961, out=2986)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' ⟨Function.argminOn_mem s hs, _⟩
intro a ha
have h : id (argminOn id s hs) ≤ id a := argminOn_le id s a ha
simpa [id] using h
```

**lean_error:** tail step 1/4 ("refine' ⟨Function.argminOn_mem s hs, _⟩"): application type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.2s, in=973, out=528)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
· exact Function.argminOn_mem _ hs
· intro y hy
  exact Function.argminOn_le _ hy
```

**lean_error:** tail step 2/4 ('· exact Function.argminOn_mem _ hs'): application type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.3s, in=2092, out=966)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine ⟨?_, ?_⟩
· simpa using (Function.argminOn_mem (s:=s) (hs:=hs) (f:=id) (h:= (· < ·)))
· intro b hb
  have hle := (Function.argminOn_le (f:=id) (h:= (· < ·)) (s:=s) (a:=b) hb)
  simpa using hle
```

**lean_error:** tail step 3/5 ('· intro b hb'): unsolved goals

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 85.9s, verify 0.1s, in=2066, out=10529)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
obtain ⟨m, hm, hm'⟩ := IsWellOrder.exists_min' inst✝ s hs
have h_bdd_below : BddBelow s := by
  use m
  intro a ha
  exact hm' a ha
have h_le : m ≤ sInf s := by
  apply le_csInf h_bdd_below
  intro a ha
  exact hm' a ha
have h_ge : sInf s ≤ m := by
  have h₁ : m ∈ s := hm
  exact csInf_le hs h_bdd_below m h₁
have h_eq : sInf s = m := le_antisymm h_ge h_le
have h_in_s : sInf s ∈ s := by
  rw [h_eq]
  exact hm
have h_le_all : ∀ a ∈ s, sInf s ≤ a := by
  intro a ha
  exact csInf_le hs h_bdd_below a ha
exact ⟨h_in_s, h_le_all⟩
```

**lean_error:** tail step 1/20 ("obtain ⟨m, hm, hm'⟩ := IsWellOrder.exists_min' inst✝ s hs"): <stdin>:1:51: expected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.9s, verify 0.2s, in=2060, out=646)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· exact Function.argminOn_mem _ _ hs
· intro a ha
  exact Function.argminOn_le _ ha hs
```

**lean_error:** tail step 2/4 ('· exact Function.argminOn_mem _ _ hs'): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.4s, in=1985, out=1086)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine ⟨?_, ?_⟩
· simpa using (Function.argminOn_mem (f:=id) (s:=s) (hs:=hs))
· intro b hb
  simpa using (Function.argminOn_le (f:=id) (s:=s) (a:=b) (ha:=hb))
```

**lean_error:** tail step 3/4 ('· intro b hb'): unsolved goals

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 65.8s, verify 0.1s, in=2230, out=7788)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ⟨Function.argminOn_mem hs, fun b hb => simpa [id] using Function.argminOn_le hb hs⟩
```

**lean_error:** tail step 1/1 ('exact ⟨Function.argminOn_mem hs, fun b hb => simpa [id] using Function.argminOn_le hb hs⟩'): <stdin>:1:56: expected '⟩'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.5s, verify 0.4s, in=2054, out=728)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
· simp [Function.argminOn_mem]
· intro b hb
  exact Function.argminOn_le s hb hs
```

**lean_error:** tail step 3/4 ('· intro b hb'): unsolved goals
