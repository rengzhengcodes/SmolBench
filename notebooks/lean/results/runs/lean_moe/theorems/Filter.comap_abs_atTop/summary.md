# Filter.comap_abs_atTop   (k=4, 5 tactics total)

file: `Mathlib/Order/Filter/AtTopBot.lean`  

**Ground-truth tail (from k):**
```lean
exact hx.imp And.left And.right
```

**True premises at k:** `And.left`, `And.right`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.5s, verify 0.2s, in=351, out=832)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases hx with h | h
· rcases h with ⟨hxa, _⟩
  left
  simpa using hxa
· rcases h with ⟨_, hxb⟩
  right
  simpa using hxb
```

**lean_error:** tail step 2/7 ('· rcases h with ⟨hxa, _⟩'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 30.1s, verify 0.1s, in=295, out=4052)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases hx with
| inl hx1 =>
  have h₁ : x ∈ Iic (a, b).1 := by
    refine' ⟨b, _⟩
    have h₂ : (x, b) ≤ (a, b) := by
      constructor <;> simp_all [Prod.le_def]
      <;> (try assumption) <;> (try exact hx1.1) <;> (try exact le_refl)
    simpa [Iic] using h₂
  exact Or.inl h₁
| inr hx2 =>
  have h₂ : x ∈ Ici (a, b).2 := by
    refine' ⟨a, _⟩
    have h₃ : (a, b) ≤ (a, x) := by
      constructor <;> simp_all [Prod.le_def]
      <;> (try assumption) <;> (try exact le_refl) <;> (try exact hx2.2)
    simpa [Ici] using h₃
  exact Or.inr h₂
```

**lean_error:** tail step 1/17 ('cases hx with'): <stdin>:1:13: unexpected end of input; expected '|'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=292, out=549)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases hx with
| inl h =>
  simp only [Set.mem_union, Set.mem_Iic, Set.mem_Ici, Prod.fst, Prod.snd]
  left
  exact h.1
| inr h =>
  simp only [Set.mem_union, Set.mem_Iic, Set.mem_Ici, Prod.fst, Prod.snd]
  right
  exact h.2
```

**lean_error:** tail step 1/9 ('cases hx with'): <stdin>:1:13: unexpected end of input; expected '|'
