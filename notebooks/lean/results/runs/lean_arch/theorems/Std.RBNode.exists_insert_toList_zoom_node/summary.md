# Std.RBNode.exists_insert_toList_zoom_node   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [← zoom_toList e, insert_toList_zoom_node ht e]
```

**True premises at k:** `Std.RBNode.zoom_toList`, `Std.RBNode.insert_toList_zoom_node`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=395, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toList_zoom _ _ e, toList_insert_of_zoom _ _ _ _ e]
exact ⟨rfl, listL_insert _ _ _ _ _ e⟩
```

**lean_error:** tail step 1/2 ('rw [toList_zoom _ _ e, toList_insert_of_zoom _ _ _ _ e]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=373, out=70)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← e]
simp [toList, Path.list_append, List.append_assoc, List.append_left_inj]
constructor <;> simp [toList, insert, Path.list_append, List.append_assoc]
rw [List.append_assoc (toList l), ← List.append_assoc (_ :: toList r)]
simp [List.append_left_comm]
```

**lean_error:** tail step 1/5 ('rw [← e]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 7.1s, verify 0.2s, in=384, out=440)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply And.intro
exact e_left
apply insert_eq_toList
```

**lean_error:** tail step 2/3 ('exact e_left'): unknown identifier 'e_left'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=859, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [insert_toList_zoom_node ht e, zoom_toList e],
exact ⟨rfl, rfl⟩
```

**lean_error:** tail step 1/2 ('rw [insert_toList_zoom_node ht e, zoom_toList e],'): <stdin>:1:48: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=846, out=68)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [e, node_toList, Path.withList, List.append_assoc, List.append_assoc, ← List.append_assoc _ _ (v'::_), List.append_assoc]
simp [List.append_assoc]
rw [insert_toList_zoom_node ht e, e, node_toList, Path.withList]
simp [List.append_assoc]
```

**lean_error:** tail step 1/4 ("rw [e, node_toList, Path.withList, List.append_assoc, List.append_assoc, ← List.append_assoc _ _ (v'::_), List.append_assoc]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=848, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply zoom_toList e
apply insert_toList_zoom_node
```

**lean_error:** tail step 1/2 ('apply zoom_toList e'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=1360, out=45)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [toList, Path.withList, Path.listL, Path.listR]
rw [zoom_toList e, toList, insert_toList_zoom_node ht e]
exact Or.inr ⟨_, rfl, rfl⟩
```

**lean_error:** tail step 1/3 ('rw [toList, Path.withList, Path.listL, Path.listR]'): failed to rewrite using equation theorems for 'Std.RBNode.Path.withList'

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=1344, out=51)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [e, Path.withList_cons, List.append_assoc, List.append_assoc, ← List.singleton_append, ← List.append_assoc]
simp
rw [insert_toList_zoom_node ht e, e, Path.withList_cons, node_toList]
```

**lean_error:** tail step 1/3 ('rw [e, Path.withList_cons, List.append_assoc, List.append_assoc, ← List.singleton_append, ← List.append_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=1349, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply zoom_toList e
apply insert_toList_zoom_node
```

**lean_error:** tail step 1/2 ('apply zoom_toList e'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1383, out=52)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [toList, zoom_toList e],
rw [insert_toList_zoom_node ht e, toList, Path.withList],
exact Eq.trans (Path.withList _ _).symm (congrArg Path.withList (by simp [toList]))
```

**lean_error:** tail step 1/3 ('rw [toList, zoom_toList e],'): <stdin>:1:26: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=1427, out=75)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [e, Path.withList, List.append_assoc, List.append_assoc, ← List.append_assoc _ _ (v' :: _), List.append_assoc]
simp
rw [insert_toList_zoom_node ht e, e, Path.withList, List.append_assoc, List.append_assoc, ← List.append_assoc _ _ (v :: _), List.append_assoc]
simp
```

**lean_error:** tail step 1/4 ("rw [e, Path.withList, List.append_assoc, List.append_assoc, ← List.append_assoc _ _ (v' :: _), List.append_assoc]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=1372, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply zoom_toList e
apply insert_toList_zoom_node
```

**lean_error:** tail step 1/2 ('apply zoom_toList e'): tactic 'apply' failed, failed to unify
