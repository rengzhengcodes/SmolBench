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

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 1.0s, in=281, out=210)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction ht
case nil => 
  exists [] 
  exists []
  rfl
case red_node x y h_l h_r h_b => 
  cases cmp v x <;> cases cmp v y <;> 
  try { exists [x] } 
  try { exists [x, y] } 
  try { exists [] } 
  exists []
  try { exact h_l _ } 
  try { exact h_r _ } 
  try { apply Exists.intro none; apply Exists.intro (some _) } 
  rfl
case black_node x y h_l h_r h_b => 
  cases cmp v x <;> cases cmp v y <;> 
  try { exists [x] } 
  try { exists [x, y] } 
  try { exists [] } 
  exists []
  try { exact h_l _ } 
  try { exact h_r _ } 
  try { apply Exists.intro none; apply Exists.intro (some _) } 
  rfl
```

**lean_error:** tail step 2/25 ('case nil =>'): <stdin>:1:11: unexpected end of input; expected '{'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.9s, in=253, out=328)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction t generalizing c n
all_goals simp [insert, toList, All]
all_goals (try simp [RBNode.mem, flip])
all_goals (try split <;> simp [*])
case red.left =>
  rcases (IHl generalizing c n).mp ht.2.1 with ⟨s₁, t₁, rfl⟩
  simp [*]
  exact ⟨s₁, v :: toList t₂, by simp [*]⟩
case red.right =>
  rcases (IHr generalizing c n).mp ht.2.2 with ⟨s₂, t₂, rfl⟩
  simp [*]
  exact ⟨v :: toList t₁ ++ s₂, t₂, by simp [*]⟩
all_goals try constructor <;> simp [*]
case black.left =>
  rcases (IHl generalizing c n).mp ht.2.1 with ⟨s₁, t₁, rfl⟩
  simp [*]
  · exact ⟨s₁, v :: toList t₂, by simp [*]⟩
  · exact ⟨[], v :: s₁ ++ toList t₂, by simp [*]⟩
case black.right =>
  rcases (IHr generalizing c n).mp ht.2.2 with ⟨s₂, t₂, rfl⟩
  simp [*]
  · exact ⟨v :: toList t₁ ++ s₂, t₂, by simp [*]⟩
  · exact ⟨toList t₁ ++ s₂, t₂, by simp [*]⟩
```

**lean_error:** tail step 5/23 ('case red.left =>'): <stdin>:1:16: unexpected end of input; expected '{'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 75.7s, verify 0.1s, in=270, out=4714)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply list.exists_split
```

**lean_error:** tail step 1/1 ('apply list.exists_split'): unknown identifier 'list.exists_split'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.8s, in=1270, out=52)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases zoom (cmp v) t with
| (nil, p) => exact exists_insert_toList_zoom_nil ht ‹_›
| (node _ _ _ _, p) => exact exists_insert_toList_zoom_node ht ‹_›
```

**lean_error:** tail step 1/3 ('cases zoom (cmp v) t with'): <stdin>:1:25: unexpected end of input; expected '|'

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1245, out=47)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases e : zoom (cmp v) t
case nil =>
  simp [exists_insert_toList_zoom_nil ht e]
case node c' l v' r =>
  simp [exists_insert_toList_zoom_node ht e]
```

**lean_error:** tail step 2/5 ('case nil =>'): <stdin>:1:11: unexpected end of input; expected '{'

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 58.4s, verify 0.1s, in=1259, out=3616)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases (zoom (cmp v) t) with s p
case nil => apply exists_insert_toList_zoom_nil
case node => apply exists_insert_toList_zoom_node
```

**lean_error:** tail step 1/3 ('cases (zoom (cmp v) t) with s p'): <stdin>:1:29: unknown tactic

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=2139, out=54)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases zoom (cmp v) t with
| (nil, p) => exact Std.RBNode.exists_insert_toList_zoom_nil ht this
| (node _ _ _ _, p) => exact Std.RBNode.exists_insert_toList_zoom_node ht this
```

**lean_error:** tail step 1/3 ('cases zoom (cmp v) t with'): <stdin>:1:25: unexpected end of input; expected '|'

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.2s, in=2116, out=99)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases e : zoom (cmp v) t
case inl h =>
  rcases exists_insert_toList_zoom_nil ht h with ⟨L, R, h1, h2⟩
  exact ⟨L, R, h2⟩
case inr h =>
  rcases exists_insert_toList_zoom_node ht h with ⟨L, R, h1, h2⟩
  simp [h1] at h2
  exact ⟨L, R, h2⟩
```

**lean_error:** tail step 2/8 ('case inl h =>'): <stdin>:1:13: unexpected end of input; expected '{'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=2128, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply exists_insert_toList_zoom_nil
apply exists_insert_toList_zoom_node
exact ht
```

**lean_error:** tail step 1/3 ('apply exists_insert_toList_zoom_nil'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=2164, out=52)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
cases zoom (cmp v) t with
| (nil, p) => exact exists_insert_toList_zoom_nil ht ‹_›
| (node _ _ _ _, p) => exact exists_insert_toList_zoom_node ht ‹_›
```

**lean_error:** tail step 1/3 ('cases zoom (cmp v) t with'): <stdin>:1:25: unexpected end of input; expected '|'

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 1.3s, in=2238, out=66)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
cases e : zoom (cmp v) t
case nil =>
  simp [insert_toList_zoom_nil ht e]
  exact exists_insert_toList_zoom_nil ht e
case node c' l v' r =>
  simp [insert_toList_zoom_node ht e]
  exact exists_insert_toList_zoom_node ht e
```

**lean_error:** tail step 2/7 ('case nil =>'): <stdin>:1:11: unexpected end of input; expected '{'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=2153, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply exists_insert_toList_zoom_nil
apply exists_insert_toList_zoom_node
```

**lean_error:** tail step 1/2 ('apply exists_insert_toList_zoom_nil'): tactic 'apply' failed, failed to unify
