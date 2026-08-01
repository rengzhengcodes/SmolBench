# Std.RBNode.isOrdered_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [isOrdered_iff']
```

**True premises at k:** `Std.RBNode.isOrdered_iff'`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.5s, in=246, out=69)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases t
· simp [Ordered, isOrdered]
· apply Iff.intro
· · intro h
  · cases h
  · simp [Ordered, isOrdered] at *
  · assumption
· · intro h
  · cases h
  · simp [Ordered, isOrdered]
  · constructor
  · assumption
```

**lean_error:** tail step 3/12 ('· apply Iff.intro'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.3s, in=219, out=126)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction t <;> simp [isOrdered, Ordered, *]
rfl
simp [Bool.and_eq_true] 
constructor <;> intro h
· intro l r hl hr x hx
  simp [RBNode.mem] at hx 
  rcases hx with ⟨⟨hxl, hxr⟩ | rfl⟩ 
  · exact hl x hxl
  · exact hr x hxr
· constructor
  · intro x hx
    exact h x (Or.inl ⟨hx, by simp⟩)
  · intro x hx
    exact h x (Or.inr hx)
```

**lean_error:** tail step 2/14 ('rfl'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=235, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
[exact iff_true_intro]
[rw [isOrdered, Ordered]]
```

**lean_error:** tail step 1/2 ('[exact iff_true_intro]'): <stdin>:1:0: expected tactic

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=839, out=65)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isOrdered]
constructor
next h =>
  cases h with
  | intro h =>
    exact h.2.2.2
next h =>
  exact ⟨none, none, ⟨fun _ h => False.elim h, h, fun _ h => False.elim h, h⟩⟩
```

**lean_error:** tail step 1/8 ('rw [isOrdered]'): failed to rewrite using equation theorems for 'Std.RBNode.isOrdered'

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.2s, in=804, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isOrdered_iff']
simp [none_eq_empty, empty_all, true_and]
simp [Ordered]
```

**lean_error:** tail step 2/3 ('simp [none_eq_empty, empty_all, true_and]'): unknown identifier 'none_eq_empty'

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=828, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isOrdered_iff' cmp L R none none]
simp
```

**lean_error:** tail step 1/2 ("rw [isOrdered_iff' cmp L R none none]"): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1774, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isOrdered_iff' L none R none (by simp [cmpLT_iff])
```

**lean_error:** tail step 1/1 ("exact isOrdered_iff' L none R none (by simp [cmpLT_iff])"): function expected at

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 1.8s, in=1730, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isOrdered_iff']
simp [cmpLT_iff, none]
aesop
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1763, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isOrdered_iff']
simp [*, forall_and_distrib]
```

**lean_error:** tail step 2/2 ('simp [*, forall_and_distrib]'): unknown identifier 'forall_and_distrib'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1798, out=43)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [isOrdered]
exact Std.RBNode.isOrdered_iff' _ _ _ _ _ none none
simp
exact ⟨fun _ => And.right, fun h => ⟨trivial, h⟩⟩
```

**lean_error:** tail step 1/4 ('simp [isOrdered]'): simp made no progress

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.2s, in=1872, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isOrdered_iff']
simp [none_eq_empty, empty_All, true_and]
simp [Ordered]
```

**lean_error:** tail step 2/3 ('simp [none_eq_empty, empty_All, true_and]'): unknown identifier 'none_eq_empty'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1787, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isOrdered_iff' L none R none]
simp
```

**lean_error:** tail step 1/2 ("rw [isOrdered_iff' L none R none]"): tactic 'rewrite' failed, equality or iff proof expected
