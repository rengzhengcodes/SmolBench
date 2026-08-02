# Std.RBNode.exists_insert_toList_zoom_node   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [← zoom_toList e, insert_toList_zoom_node ht e]
```

**True premises at k:** `Std.RBNode.zoom_toList`, `Std.RBNode.insert_toList_zoom_node`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 2.1s, in=439, out=1602)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases e with ⟨rfl, rfl⟩
simp [toList, List.append_assoc]
```

**lean_error:** tail step 1/2 ('rcases e with ⟨rfl, rfl⟩'): tactic 'cases' failed, nested error:

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 219.7s, verify 0.1s, in=385, out=26667)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : toList t = Path.listL p ++ toList l ++ v' :: (toList r ++ Path.listR p) := by
  have h₂ : zoom cmp v t = (node c' l v' r, p) := e
  have h₃ : toList t = Path.listL p ++ toList (node c' l v' r) ++ Path.listR p := by
    apply RBNode.toList_zoom
    <;> assumption
  have h₄ : toList (node c' l v' r) = toList l ++ [v'] ++ toList r := by
    apply RBNode.toList_node
  rw [h₃, h₄]
  <;> simp [List.cons_append, List.append_assoc]
  <;> ring_nf
  <;> simp_all [Path.listL, Path.listR]
  <;> try contradiction
  <;> try aesop
  
have h₂ : v = v' := by
  have h₃ : v ∈ t := by
    have h₄ : zoom cmp v t = (node c' l v' r, p) := e
    have h₅ : zoom cmp v t ≠ (Empty, _) := by
      intro h
      simp_all [Prod.ext_iff]
      <;> contradiction
    have h₆ : v ∈ t := by
      apply RBNode.zoom_ne_empty_iff_mem.mp
      exact h₅
    exact h₆
  have h₄ : let (t', p) := zoom cmp v t in t' ≠ Empty ∧ getValue t' = v := by
    apply RBNode.zoom_eq_getValue
    <;> exact h₃
  obtain ⟨hne, hval⟩ := h₄
  have h₅ : (node c' l v' r, p) = zoom cmp v t := by
    rw [e]
    <;> rfl
  have h₆ : t' = node c' l v' r := by
    have h₇ : (t', p) = zoom cmp v t := by
      simp [Prod.mk.injEq]
      <;> aesop
    have h₈ : t' = node c' l v' r := by
      have h₉ := h₇
      simp_all [Prod.ext_iff]
      <;> aesop
    exact h₈
  have h₇ : getValue t' = v := hval
  have h₈ : getValue (node c' l v' r) = v' := by
    simp [getValue, RBNode]
  have h₉ : getValue (node c' l v' r) = v := by
    rw [h₆] at h₇
    exact h₇
  linarith
  
have h₃ : insert cmp t v = t := by
  have h₄ : v ∈ t := by
    have h₅ : zoom cmp v t = (node c' l v' r, p) := e
    have h₆ : zoom cmp v t ≠ (Empty, _) := by
      intro h
      simp_all [Prod.ext_iff]
      <;> contradiction
    have h₇ : v ∈ t := by
      apply RBNode.zoom_ne_empty_iff_mem.mp
      exact h₆
    exact h₇
  have h₅ : insert cmp t v = t := by
    apply RBNode.insert_eq_of_mem
    <;> assumption
  exact h₅
  
have h₄ : toList (insert cmp t v) = Path.listL p ++ toList l ++ v :: (toList r ++ Path.listR p) := by
  rw [h₃]
  have h₅ : toList t = Path.listL p ++ toList l ++ v' :: (toList r ++ Path.listR p) := h₁
  have h₆ : v = v' := h₂
  rw [h₅]
  simp [h₆]
  <;> ring_nf
  <;> simp_all [Path.listL, Path.listR]
  <;> try contradiction
  <;> try aesop
  
exact ⟨h₁, h₄⟩
```

**lean_error:** tail step 1/73 ("have h₁ : toList t = Path.listL p ++ toList l ++ v' :: (toList r ++ Path.listR p) := by"): <stdin>:1:87: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.3s, in=381, out=506)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· rw [← e]
  exact zoom_toList t (cmp v)
· rw [← e]
  simp [insert_zoom, toList_insert]
```

**lean_error:** tail step 2/5 ('· rw [← e]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.0s, verify 0.3s, in=926, out=2827)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
·
  simpa [Path.withList, List.append_assoc, List.cons_append] using
    (Std.RBNode.zoom_toList (t:=t) (eq:=e)).symm
·
  simpa [Path.withList, List.append_assoc, List.cons_append] using
    (Std.RBNode.insert_toList_zoom_node (t:=t) (ht:=ht) (e:=e))
```

**lean_error:** tail step 2/7 ('·'): <stdin>:1:1: unexpected end of input; expected '{'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 263.2s, verify 0.1s, in=881, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h1 : t.toList = p.withList (node c' l v' r).toList := by
  apply Std.RBNode.zoom_toList
  <;> assumption
have h2 : (t.insert cmp v).toList = p.withList (node c l v r).toList := by
  apply Std.RBNode.insert_toList_zoom_node
  <;> assumption
```

**lean_error:** tail step 1/6 ("have h1 : t.toList = p.withList (node c' l v' r).toList := by"): <stdin>:1:61: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.3s, in=860, out=655)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
· rw [← zoom_toList e]
  simp [Path.withList, RBNode.toList]
  <;> simp_all [List.append_assoc]
· rw [insert_toList_zoom_node ht e]
  simp [Path.withList, RBNode.toList]
  <;> simp_all [List.append_assoc]
```

**lean_error:** tail step 2/7 ('· rw [← zoom_toList e]'): unsolved goals

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.9s, verify 6.8s, in=1440, out=2219)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
  ·
    simpa [Path.withList, List.append_assoc] using
      (Std.RBNode.zoom_toList (t:=t) (eq:=e)).symm
  ·
    simpa [Path.withList, List.append_assoc] using
      (Std.RBNode.insert_toList_zoom_node (t:=t) (ht:=ht) (e:=e))
```

**lean_error:** tail step 2/7 ('·'): <stdin>:1:1: unexpected end of input; expected '{'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 79.9s, verify 0.1s, in=1409, out=9102)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine ⟨_, _⟩
· -- Prove the first conjunct: toList t = Path.listL p ++ toList l ++ v' :: (toList r ++ Path.listR p)
  have h₁ : t.toList = p.withList (node c' l v' r).toList := zoom_toList e
  rw [h₁]
  simp [Path.withList, RBNode.toList, List.append_assoc]
  <;> rfl
· -- Prove the second conjunct: toList (insert cmp t v) = Path.listL p ++ toList l ++ v :: (toList r ++ Path.listR p)
  have h₂ : (t.insert cmp v).toList = p.withList (node c l v r).toList := insert_toList_zoom_node ht e
  rw [h₂]
  simp [Path.withList, RBNode.toList, List.append_assoc]
  <;> rfl
```

**lean_error:** tail step 1/11 ('refine ⟨_, _⟩'): internal exception #7

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.8s, verify 0.3s, in=1380, out=956)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· rw [← zoom_toList e]
  simp [Path.withList, RBNode.toList]
· rw [insert_toList_zoom_node ht e]
  simp [Path.withList, RBNode.toList]
```

**lean_error:** tail step 2/5 ('· rw [← zoom_toList e]'): unsolved goals

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.7s, verify 0.3s, in=1406, out=2373)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
·
  have h := (Std.RBNode.zoom_toList (t:=t) (eq:=e))
  simpa [Path.withList, List.append_assoc, List.cons_append] using h.symm
·
  have h := (Std.RBNode.insert_toList_zoom_node (t:=t) (ht:=ht) (e:=e))
  simpa [Path.withList, List.append_assoc, List.cons_append] using h
```

**lean_error:** tail step 2/7 ('·'): <stdin>:1:1: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 153.5s, verify 0.1s, in=1502, out=17763)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem Std.RBNode.exists_insert_toList_zoom_node {α : Type u_1} {c : RBColor} {n : Nat} {cmp : α → α → Ordering} {c' : RBColor} {l : RBNode α} {v' : α} {r : RBNode α} {p : Path α} {v : α} {t : RBNode α} (ht : Balanced t c n) (e : zoom (cmp v) t = (node c' l v' r, p)) :
    toList t = Path.listL p ++ toList l ++ v' :: (toList r ++ Path.listR p) ∧
    toList (insert cmp t v) = Path.listL p ++ toList l ++ v :: (toList r ++ Path.listR p) := by
  have h1 : p.withList (node c' l v' r).toList = t.toList := by
    apply zoom_toList
    <;> assumption
  
  have h2 : (t.insert cmp v).toList = p.withList (node c l v r).toList := by
    apply insert_toList_zoom_node
    <;> assumption
  
  have h3 : toList t = Path.listL p ++ toList l ++ v' :: (toList r ++ Path.listR p) := by
    have h3₁ : p.withList (node c' l v' r).toList = Path.listL p ++ toList l ++ v' :: (toList r ++ Path.listR p) := by
      rfl
    rw [h1]
    rw [h3₁]
    <;>
    simp_all [Path.withList, Path.listL, Path.listR, RBNode.toList]
    <;>
    rfl
  
  have h4 : toList (insert cmp t v) = Path.listL p ++ toList l ++ v :: (toList r ++ Path.listR p) := by
    have h4₁ : p.withList (node c l v r).toList = Path.listL p ++ toList l ++ v :: (toList r ++ Path.listR p) := by
      rfl
    rw [h2]
    rw [h4₁]
    <;>
    simp_all [Path.withList, Path.listL, Path.listR, RBNode.toList]
    <;>
    rfl
  
  exact ⟨h3, h4⟩
```

**lean_error:** tail step 1/28 ("theorem Std.RBNode.exists_insert_toList_zoom_node {α : Type u_1} {c : RBColor} {n : Nat} {cmp : α → α → Ordering} {c' : RBColor} {l : RBNode α} {v' : α} {r : RBNode α} {p : Path α} {v : α} {t : RBNode α} (ht : Balanced t c n) (e : zoom (cmp v) t = (node c' l v' r, p)) :"): <stdin>:1

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.3s, in=1393, out=672)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
· rw [← zoom_toList e]
  simp [Path.withList, List.append_assoc]
· rw [insert_toList_zoom_node ht e]
  simp [Path.withList, List.append_assoc]
```

**lean_error:** tail step 2/5 ('· rw [← zoom_toList e]'): unsolved goals
