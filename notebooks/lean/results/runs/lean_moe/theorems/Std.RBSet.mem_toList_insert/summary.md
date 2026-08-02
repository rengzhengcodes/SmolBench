# Std.RBSet.mem_toList_insert   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa [mem_toList] using RBNode.mem_insert ht₂ ht₁
```

**True premises at k:** `Std.RBSet.mem_toList`, `Std.RBNode.mem_insert`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.1s, verify 0.7s, in=386, out=3391)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [RBSet.mem_toList] using (RBSet.mem_insert (t:=t) (a:=v) (b:=v'))
```

**lean_error:** tail step 1/1 ("simpa [RBSet.mem_toList] using (RBSet.mem_insert (t:=t) (a:=v) (b:=v'))"): unknown constant 'Std.RBSet.mem_insert'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 239.9s, verify 0.1s, in=331, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
def Ordered {α : Type} {cmp : α → α → Ordering} (t : RBNode α cmp) : Prop where
  | ordered : ∀ {a b : α}, a ∈ toList t → b ∈ toList t → cmp a b = LT → a < b
```

**lean_error:** tail step 1/2 ('def Ordered {α : Type} {cmp : α → α → Ordering} (t : RBNode α cmp) : Prop where'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=321, out=458)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [RBSet.mem_toList, RBSet.mem_insert, RBSet.find?_eq_some_iff]
```

**lean_error:** tail step 1/1 ('simp [RBSet.mem_toList, RBSet.mem_insert, RBSet.find?_eq_some_iff]'): unknown constant 'Std.RBSet.mem_insert'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.1s, verify 0.9s, in=1214, out=2134)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [RBSet.mem_toList, RBSet.find?, RBSet.insert] using
    (RBNode.mem_insert (t:=t.1) (v:=v) (v':=v') ht₂ ht₁)
```

**lean_error:** tail step 1/2 ('simpa [RBSet.mem_toList, RBSet.find?, RBSet.insert] using'): <stdin>:1:57: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 56.1s, verify 0.2s, in=1161, out=6382)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_toList] at *
rw [show (insert t v).1 = t.val.insert cmp v by dsimp [RBSet.insert]; rfl]
rw [show t.1 = t.val by rfl]
rw [show find? t v = t.val.find? cmp v by dsimp [RBSet.find?]; rfl]
apply RBNode.mem_insert ht₂ ht₁
```

**lean_error:** tail step 2/5 ('rw [show (insert t v).1 = t.val.insert cmp v by dsimp [RBSet.insert]; rfl]'): no goals to be solved

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.4s, verify 0.2s, in=1106, out=468)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_toList, mem_toList]
simp [RBSet.insert, RBNode.mem_insert ht₂ ht₁]
```

**final state (truncated):**
```
α : Type u_1
cmp : α → α → Ordering
v' v : α
inst✝ : TransCmp cmp
t : RBSet α cmp
ht₁ : RBNode.Ordered cmp t.val
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.4s, verify 0.7s, in=2763, out=2067)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [RBSet.mem_toList, RBSet.find?, RBSet.insert] using
  (Std.RBNode.mem_insert (t:=t.1) (v:=v) (v':=v') ht₂ ht₁)
```

**lean_error:** tail step 1/2 ('simpa [RBSet.mem_toList, RBSet.find?, RBSet.insert] using'): <stdin>:1:57: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 108.5s, verify 3.3s, in=2745, out=13218)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h_eq : t.1 = t.val := by rfl
have h_insert_val : (insert t v).1 = t.val.insert cmp v := by rfl
have h_find : find? t v = t.val.find? (cmp v) := by rfl
have h_ordered : RBNode.Ordered cmp t.val := ht₁
have h_balanced : RBNode.Balanced t.val w✝¹ w✝ := ht₂
calc
  v' ∈ toList (insert t v) ↔ v' ∈ (insert t v).1 := by rw [mem_toList]
  _ = v' ∈ t.val.insert cmp v := by rw [h_insert_val]
  _ ↔ (v' ∈ t.val ∧ t.val.find? (cmp v) ≠ some v') ∨ v' = v := by
    apply mem_insert
    <;> assumption
  _ = (v' ∈ toList t ∧ find? t v ≠ some v') ∨ v' = v := by
    have h₁ : v' ∈ t.val ↔ v' ∈ toList t := by
      rw [mem_toList]
    have h₂ : t.val.find? (cmp v) = find? t v := by rfl
    rw [h₁]
    rw [h₂]
    <;> rfl
```

**lean_error:** tail step 5/18 ('have h_balanced : RBNode.Balanced t.val w✝¹ w✝ := ht₂'): <stdin>:1:41: expected token

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 25.9s, verify 0.2s, in=2659, out=2724)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mem_toList, mem_toList]
apply mem_insert ht₂ ht₁
```

**lean_error:** tail step 2/2 ('apply mem_insert ht₂ ht₁'): unknown identifier 'mem_insert'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.4s, in=2601, out=1362)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Std.RBSet.mem_toList] using
  (Std.RBNode.mem_insert (t:=t.val) (v:=v) (v':=v') ht₂ ht₁)
```

**lean_error:** tail step 1/2 ('simpa [Std.RBSet.mem_toList] using'): <stdin>:1:34: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 143.5s, verify 0.6s, in=2973, out=18148)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h1 : v' ∈ toList (insert t v) ↔ v' ∈ (insert t v).1 := by rw [mem_toList]
have h2 : v' ∈ toList t ↔ v' ∈ t.1 := by rw [mem_toList]
have h3 : find? t v = (t.1).find? (cmp v) := by rfl
have h4 : (insert t v).1 = (t.1).insert cmp v := by rfl
have h5 : v' ∈ toList (insert t v) ↔ (v' ∈ toList t ∧ find? t v ≠ some v') ∨ v' = v := by
  rw [h1]
  rw [h4]
  have h6 : v' ∈ (t.1).insert cmp v ↔ (v' ∈ t.1 ∧ t.1.find? (cmp v) ≠ some v') ∨ v' = v := by
    apply mem_insert
    <;> exact ⟨ht₁, ht₂⟩
  rw [h6]
  have h7 : v' ∈ t.1 ↔ v' ∈ toList t := by
    rw [h2]
    <;> tauto
  have h8 : t.1.find? (cmp v) = find? t v := by
    rw [h3]
    <;> rfl
  rw [h7]
  rw [h8]
  <;>
  (try tauto) <;>
  (try
    {
      constructor <;>
      intro h <;>
      (try { cases h <;> simp_all [and, or, not_false_iff_not_true] <;> tauto }) <;>
      (try { tauto })
    })
  <;>
  (try
    {
      simp_all [and, or, not_false_iff_not_true]
      <;> tauto
    })
exact h5
```

**lean_error:** tail step 5/35 ("have h5 : v' ∈ toList (insert t v) ↔ (v' ∈ toList t ∧ find? t v ≠ some v') ∨ v' = v := by"): <stdin>:1:89: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 42.5s, verify 0.5s, in=2648, out=4577)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mem_toList, mem_toList]
simp [insert]
rw [RBNode.mem_insert ht₂ ht₁]
simp [find?]
```
