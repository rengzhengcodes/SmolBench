# Std.RBNode.mem_insert_self   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact match e : zoom (cmp v) t with
| (nil, p) => let ⟨_, _, _, h⟩ := exists_insert_toList_zoom_nil ht e; ⟨_, _, h⟩
| (node .., p) => let ⟨_, _, _, h⟩ := exists_insert_toList_zoom_node ht e; ⟨_, _, h⟩
```

**True premises at k:** `Std.RBNode.zoom`, `Std.RBNode.nil`, `Std.RBNode.exists_insert_toList_zoom_nil`, `Std.RBNode.node`, `Std.RBNode.exists_insert_toList_zoom_node`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 10.0s, verify 0.2s, in=319, out=1980)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨[], [], ?_⟩
simp
```

**final state (truncated):**
```
α : Type u_1
c : RBColor
n : Nat
v : α
cmp : α → α → Ordering
t : RBNode α
...
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 166.0s, verify 0.1s, in=265, out=21112)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases t with
| empty => {
  simp [insert, toList]
  <;>
  (try
    {
      use [] []
      <;> simp_all [List.cons_append, List.append_cons, List.append_nil]
    })
  <;>
  (try
    {
      use (toList (insert cmp t v)) []
      <;> simp_all
    })
}
| node c l x r => {
  simp [insert, toList, Balanced] at *
  <;>
  (try
    {
      have h : cmp v x = LT ∨ cmp v x = GT ∨ cmp v x = EQ := by
        revert cmp v x
        decide
      rcases h with (h | h | h)
      · -- LT case
        {
          sorry
        }
      · -- GT case
        {
          sorry
        }
      · -- EQ case
        {
          sorry
        }
    })
}
```

**lean_error:** tail step 1/39 ('cases t with'): <stdin>:1:12: unexpected end of input; expected '|'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=264, out=480)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply List.mem_iff_exists_append.mpr
have : v ∈ toList (insert cmp t v) := by
  apply toList_mem.mpr
  exact mem_insert_self v t
exact this
```

**lean_error:** tail step 1/5 ('apply List.mem_iff_exists_append.mpr'): unknown constant 'List.mem_iff_exists_append.mpr'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.8s, verify 0.1s, in=1340, out=4416)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_toList]
apply (List.mem_iff_append).mpr
cases h : zoom (cmp v) t with
| mk n' p =>
  cases n' with
  | nil =>
      rcases exists_insert_toList_zoom_nil (t:=t) (c:=c) (n:=n) ht h with ⟨L, R, _, hR⟩
      exact ⟨L, R, hR⟩
  | node c' l v' r =>
      rcases exists_insert_toList_zoom_node (t:=t) (c:=c) (n:=n) ht h with ⟨L, R, _, hR⟩
      exact ⟨L, R, hR⟩
```

**lean_error:** tail step 1/11 ('rw [mem_toList]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 44.5s, verify 0.1s, in=1316, out=4995)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases zoom (cmp v) t with
| nil, p =>
  have h₂ : zoom (cmp v) t = (nil, p) := rfl
  have h₃ : ∃ L R, t.toList = L ++ R ∧ (t.insert cmp v).toList = L ++ v :: R :=
    exists_insert_toList_zoom_nil ht h₂
  obtain ⟨L, R, hL, hR⟩ := h₃
  refine' ⟨L, R, _⟩
  exact hR
| node c' l v' r, p =>
  have h₂ : zoom (cmp v) t = (node c' l v' r, p) := rfl
  have h₃ : ∃ L R, t.toList = L ++ v' :: R ∧ (t.insert cmp v).toList = L ++ v :: R :=
    exists_insert_toList_zoom_node ht h₂
  obtain ⟨L, R, hL, hR⟩ := h₃
  refine' ⟨L, R, _⟩
  exact hR
```

**lean_error:** tail step 1/15 ('cases zoom (cmp v) t with'): <stdin>:1:25: unexpected end of input; expected '|'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 24.6s, verify 0.1s, in=1295, out=2507)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases' zoom (cmp v) t with node' path'
cases' node'
· obtain ⟨L, R, _, h⟩ := exists_insert_toList_zoom_nil ht rfl
    obtain ⟨s, t₁, heq⟩ := h
    exact ⟨s, t₁, heq⟩
· obtain ⟨L, R, _, h⟩ := exists_insert_toList_zoom_node ht rfl
    obtain ⟨s, t₁, heq⟩ := h
    exact ⟨s, t₁, heq⟩
```

**lean_error:** tail step 1/8 ("cases' zoom (cmp v) t with node' path'"): <stdin>:1:1: unknown tactic

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.5s, verify 0.2s, in=2235, out=1341)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rcases h : zoom (cmp v) t with ⟨t', p⟩
  cases t' with
  | nil =>
      exact Std.RBNode.exists_insert_toList_zoom_nil (ht:=ht) (e:=by
        simpa [h])
  | node c' l v' r =>
      exact Std.RBNode.exists_insert_toList_zoom_node (ht:=ht) (e:=by
        simpa [h])
```

**lean_error:** tail step 2/8 ("cases t' with"): <stdin>:1:13: unexpected end of input; expected '|'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 70.8s, verify 0.2s, in=2238, out=8039)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
let z : RBNode α × Path α := zoom (cmp v) t
cases z with
| nil p =>
  have h : zoom (cmp v) t = (nil, p) := by simp [z]
  obtain ⟨L, R, _, h₃⟩ := Std.RBNode.exists_insert_toList_zoom_nil ht h
  refine' ⟨L, R, _⟩
  exact h₃
| node c' l v' r p =>
  have h : zoom (cmp v) t = (node c' l v' r, p) := by simp [z]
  obtain ⟨L, R, _, h₃⟩ := Std.RBNode.exists_insert_toList_zoom_node ht h
  refine' ⟨L, R, _⟩
  exact h₃
```

**lean_error:** tail step 2/12 ('cases z with'): <stdin>:1:12: unexpected end of input; expected '|'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 10.2s, verify 0.1s, in=2203, out=652)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases h : zoom (cmp v) t with
| mk t' p =>
  cases t' with
  | nil =>
    obtain ⟨L, R, hL, hR⟩ := exists_insert_toList_zoom_nil ht h
    exact ⟨L, R, hR⟩
  | node c' l v' r =>
    obtain ⟨L, R, hL, hR⟩ := exists_insert_toList_zoom_node ht h
    exact ⟨L, R, hR⟩
```

**lean_error:** tail step 1/9 ('cases h : zoom (cmp v) t with'): <stdin>:1:29: unexpected end of input; expected '|'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.4s, in=2154, out=1606)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact mem_insert_self
```

**lean_error:** tail step 1/1 ('exact mem_insert_self'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 45.1s, verify 0.2s, in=2376, out=5065)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rcases zoom (cmp v) t with ⟨t', p⟩
rcases t' with
| nil =>
  have h₂ : zoom (cmp v) t = (nil, p) := rfl
  obtain ⟨L, R, hL, hR⟩ := exists_insert_toList_zoom_nil ht h₂
  exact ⟨L, R, hR⟩
| node c' l v' r =>
  have h₂ : zoom (cmp v) t = (node c' l v' r, p) := rfl
  obtain ⟨L, R, hL, hR⟩ := exists_insert_toList_zoom_node ht h₂
  exact ⟨L, R, hR⟩
```

**lean_error:** tail step 2/10 ("rcases t' with"): <stdin>:1:14: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 12.7s, verify 0.1s, in=2201, out=1152)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
cases h : zoom (cmp v) t with
| nil p =>
  obtain ⟨L, R, h₁, h₂⟩ := exists_insert_toList_zoom_nil ht h
  exact ⟨L, R, h₂⟩
| node c' l v' r p =>
  obtain ⟨L, R, h₁, h₂⟩ := exists_insert_toList_zoom_node ht h
  exact ⟨L, R, h₂⟩
```

**lean_error:** tail step 1/7 ('cases h : zoom (cmp v) t with'): <stdin>:1:29: unexpected end of input; expected '|'
