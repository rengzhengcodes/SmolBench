# Set.PairwiseDisjoint.exists_mem_filter   (k=4, 5 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨fun i => s i, fun i => (s i).2, hsd.set_of_subtype _ _⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.2s, verify 1.4s, in=425, out=1257)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨fun i => (s i).1, ?_, ?_⟩
· intro i
  exact (s i).property
· intro i hi j hj hij
  have h := hsd hij
  simma using h
```

**lean_error:** tail step 2/6 ('· intro i'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 88.9s, verify 0.3s, in=366, out=10081)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨fun i => (s i : Set α), _, _⟩
· exact s i.prop
· refine' fun i hi j hj hne => _
    have h₁ : i ≠ j := hne
    have h₂ : Pairwise (Disjoint (fun i : ι => (s i : Set α))) := by
      have h₃ : Pairwise (Disjoint (fun i : ι => ↑((fun i => s ↑i) i))) := hsd
      have h₄ : (fun i : ι => ↑((fun i => s ↑i) i)) = (fun i : ι => (s i : Set α)) := by
        funext i
        simp [Subtype.ext_iff]
        <;> aesop
      rw [h₄] at h₃
      exact h₃
    have h₃ : Disjoint ((s i : Set α)) ((s j : Set α)) := h₂ i j h₁
    exact h₃
```

**lean_error:** tail step 2/14 ('· exact s i.prop'): unknown identifier 'i.prop'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.4s, in=358, out=665)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use fun i => (s i).val
constructor
· intro i
  exact (s i).property
· exact hsd
```

**lean_error:** tail step 3/5 ('· intro i'): unsolved goals
