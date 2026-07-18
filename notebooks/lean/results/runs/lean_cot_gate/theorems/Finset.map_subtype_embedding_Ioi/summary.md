# Finset.map_subtype_embedding_Ioi   (k=1, 2 tactics total)

file: `Mathlib/Order/LocallyFinite.lean`  

**Ground-truth tail (from k):**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp (mem_Ioi.1 hx).le a.prop
```

**True premises at k:** `Finset.subtype_map_of_mem`, `Finset.mem_Ioi`, `LT.lt.le`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ |
| `hint:3` | ✓ ✓ ✓ ✘ | ✘ ✘ ✓ ✘ |
| `noise:3` | ✓ ✓ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 55.1s, verify 0.1s, in=296, out=2474)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw Finset.map_subtype_val
apply Finset.filter_eq_self
intros x hx
apply hp (le_of_lt hx) a.property
```

**lean_error:** tail step 1/4 ('rw Finset.map_subtype_val'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 120.3s, verify 0.1s, in=296, out=5279)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Finset.map_subtype_val], apply Finset.filter_eq_self, intros x hx, exact hp (le_of_lt (mem_Ioi.mp hx)) (a.prop)
```

**lean_error:** tail step 1/1 ('rw [Finset.map_subtype_val], apply Finset.filter_eq_self, intros x hx, exact hp (le_of_lt (mem_Ioi.mp hx)) (a.prop)'): <stdin>:1:27: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 122.1s, verify 0.2s, in=296, out=5364)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp [Finset.mem_map, Finset.mem_subtype, Finset.Ioi, SetLike.mem_coe, Set.mem_Ioi]
constructor
· rintro ⟨y, ⟨hy, py⟩, rfl⟩
  exact hy
· intro hx
  have hpx : p x := hp (lt_le hx) (a.property)
  exact ⟨⟨x, hpx⟩, hx, rfl⟩
```

**lean_error:** tail step 2/8 ('simp [Finset.mem_map, Finset.mem_subtype, Finset.Ioi, SetLike.mem_coe, Set.mem_Ioi]'): unknown identifier 'SetLike.mem_coe'

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 145.7s, verify 0.3s, in=296, out=6432)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Finset.ext
intros x
split
rintro ⟨⟨y, hpy⟩, hy, rfl⟩
exact hy
intro hx
have hpx := hp (le_of_lt hx) a.property
exact ⟨⟨x, hpx⟩, hx, rfl⟩
```

**lean_error:** tail step 3/8 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.9s, verify 0.1s, in=296, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [hp]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝² : Preorder α
p : α → Prop
inst✝¹ : DecidablePred p
inst✝ : LocallyFiniteOrderTop α
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.1s, verify 0.1s, in=296, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Finset.subtype, hp]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝² : Preorder α
p : α → Prop
inst✝¹ : DecidablePred p
inst✝ : LocallyFiniteOrderTop α
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=296, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Ioi, Finset.subtype_Ioi]
```

**lean_error:** tail step 1/1 ('simp [Ioi, Finset.subtype_Ioi]'): unknown constant 'Finset.subtype_Ioi'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=296, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Finset.subtype_eq, Finset.map_finset_subtype]
```

**lean_error:** tail step 1/1 ('simp [Finset.subtype_eq, Finset.map_finset_subtype]'): unknown constant 'Finset.subtype_eq'

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 20.0s, verify 0.2s, in=802, out=930)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
rintro x (hax : ↑a < x)
have ha' : ↑a ≤ x := hax.le
have hp_a : p ↑a := a.2
exact hp ha' hp_a
```

**lean_error:** tail step 2/5 ('rintro x (hax : ↑a < x)'): rcases: scrutinee has type

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 33.7s, verify 0.3s, in=802, out=1526)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intros x hx
apply hp (le_of_lt hx) a.property
```

**lean_error:** tail step 3/3 ('apply hp (le_of_lt hx) a.property'): application type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 41.5s, verify 0.2s, in=802, out=1852)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
rintro x ⟨⟩
exact hp (LT.lt.le ‹_›) (Subtype.property a)
```

**lean_error:** tail step 2/3 ('rintro x ⟨⟩'): rcases tactic failed: a✝ : Quot.lift (fun l => x ∈ l) ⋯ (Finset.Ioi ↑a).val is not an inductive datatype

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 73.2s, verify 0.2s, in=802, out=3284)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply subtype_map_of_mem
intros x hx
exact hp (lt_le (mem_Ioi.mp hx)) (a.prop)
```

**lean_error:** tail step 3/3 ('exact hp (lt_le (mem_Ioi.mp hx)) (a.prop)'): unknown identifier 'lt_le'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.5s, verify 0.1s, in=802, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem <;> simp [hp]
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝² : Preorder α
p : α → Prop
inst✝¹ : DecidablePred p
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=802, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact subtype_map_of_mem fun x hx => lt_le.trans hx.le a.prop
```

**lean_error:** tail step 1/1 ('exact subtype_map_of_mem fun x hx => lt_le.trans hx.le a.prop'): unknown identifier 'lt_le.trans'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=802, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact subtype_map_of_mem fun x hx => (mem_Ioi.1 hx).le
```

**lean_error:** tail step 1/1 ('exact subtype_map_of_mem fun x hx => (mem_Ioi.1 hx).le'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=802, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Finset.subtype_map_of_mem fun _ h => hp (Finset.mem_Ioi.1 h).le h.2
```

**lean_error:** tail step 1/1 ('exact Finset.subtype_map_of_mem fun _ h => hp (Finset.mem_Ioi.1 h).le h.2'): invalid projection, structure expected

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 48.1s, verify 0.3s, in=1901, out=1618)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intros x hx
have hle : ↑a ≤ x := le_of_lt (Finset.mem_Ioi.mp hx)
exact hp hle a.prop
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 63.4s, verify 0.3s, in=1901, out=1913)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intros x hx
have hlt : ↑a < x := Finset.mem_Ioi.mp hx
exact hp (le_of_lt hlt) a.property
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 71.8s, verify 0.2s, in=1901, out=1354)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intros x hx
apply hp (le_of_lt (Finset.mem_Ioi.mp hx)) a.2
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 103.4s, verify 0.3s, in=1901, out=3030)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intros x hx
apply hp (le_of_lt (Finset.mem_Ioi.mp hx).1) a.prop
```

**lean_error:** tail step 3/3 ('apply hp (le_of_lt (Finset.mem_Ioi.mp hx).1) a.prop'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.4s, verify 0.2s, in=1901, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp hx.le a.prop
```

**lean_error:** tail step 1/1 ('exact Finset.subtype_map_of_mem fun x hx => hp hx.le a.prop'): invalid field 'le', the environment does not contain 'Membership.mem.le'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.6s, verify 0.1s, in=1901, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp (mem_Ioi.mp hx).le (x.2)
```

**lean_error:** tail step 1/1 ('exact Finset.subtype_map_of_mem fun x hx => hp (mem_Ioi.mp hx).le (x.2)'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.7s, verify 0.1s, in=1901, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp (mem_Ioi.1 hx).le a.prop
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.8s, verify 0.1s, in=1901, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Finset.subtype_map_of_mem fun _ h => hp (Finset.mem_Ioi.1 h).le (val a).2
```

**lean_error:** tail step 1/1 ('exact Finset.subtype_map_of_mem fun _ h => hp (Finset.mem_Ioi.1 h).le (val a).2'): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 11.1s, verify 0.3s, in=1924, out=524)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intros x hmem
have hax : ↑a < x := mem_Ioi.mp hmem
exact hp hax.le a.property
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 44.9s, verify 0.2s, in=1924, out=1990)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intros x hx
exact hp (mem_Ioi.mp hx).le a.prop
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 46.3s, verify 0.3s, in=1924, out=2055)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intros x hx
exact hp (le_of_lt hx) a.2
```

**lean_error:** tail step 3/3 ('exact hp (le_of_lt hx) a.2'): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 58.2s, verify 0.3s, in=1924, out=2616)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intros x hx
exact hp (LT.lt.le hx) (a.prop)
```

**lean_error:** tail step 3/3 ('exact hp (LT.lt.le hx) (a.prop)'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=1924, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp hx.le a.prop
```

**lean_error:** tail step 1/1 ('exact Finset.subtype_map_of_mem fun x hx => hp hx.le a.prop'): invalid field 'le', the environment does not contain 'Membership.mem.le'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.1s, verify 0.1s, in=1924, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp hx.le (mem_Ioi.mp hx).le
```

**lean_error:** tail step 1/1 ('exact Finset.subtype_map_of_mem fun x hx => hp hx.le (mem_Ioi.mp hx).le'): internal exception #7

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=1924, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp (mem_Ioi.mp hx).le (x.2)
```

**lean_error:** tail step 1/1 ('exact Finset.subtype_map_of_mem fun x hx => hp (mem_Ioi.mp hx).le (x.2)'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.5s, verify 0.1s, in=1924, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Finset.subtype_map_of_mem fun _ h => hp (Finset.mem_Ioi.1 h).le (mem_coe.2 h)
```

**lean_error:** tail step 1/1 ('exact Finset.subtype_map_of_mem fun _ h => hp (Finset.mem_Ioi.1 h).le (mem_coe.2 h)'): application type mismatch
