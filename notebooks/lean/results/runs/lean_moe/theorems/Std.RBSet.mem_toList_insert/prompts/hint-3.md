## Current goal
```
⊢ v' ∈ toList (insert t v) ↔ v' ∈ toList t ∧ find? t v ≠ some v' ∨ v' = v
```

## Full tactic state
```
α : Type u_1
cmp : α → α → Ordering
v' v : α
inst✝ : TransCmp cmp
t : RBSet α cmp
ht₁ : RBNode.Ordered cmp t.val
w✝¹ : RBColor
w✝ : Nat
ht₂ : RBNode.Balanced t.val w✝¹ w✝
⊢ v' ∈ toList (insert t v) ↔ v' ∈ toList t ∧ find? t v ≠ some v' ∨ v' = v
```

## Proof so far (1 tactic)
```lean
let ⟨ht₁, _, _, ht₂⟩ := t.2.out
```

## Theorem
`Std.RBSet.mem_toList_insert` in `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`

## Premises used in the next tactic
- `Std.RBSet.mem_toList`
- `Std.RBNode.mem_insert`

## Premise signatures
### `Std.RBSet.mem_toList` (commanddeclaration)
```lean
theorem mem_toList {t : RBSet α cmp} : x ∈ toList t ↔ x ∈ t.1
```

### `Std.RBNode.mem_insert` (commanddeclaration)
```lean
theorem mem_insert [@TransCmp α cmp] {t : RBNode α} (ht : Balanced t c n) (ht₂ : Ordered cmp t) :
    v' ∈ t.insert cmp v ↔ (v' ∈ t ∧ t.find? (cmp v) ≠ some v') ∨ v' = v
```

## Premise full source (with proof)
### `Std.RBSet.mem_toList` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem mem_toList {t : RBSet α cmp} : x ∈ toList t ↔ x ∈ t.1 := RBNode.mem_toList
```

### `Std.RBNode.mem_insert` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem mem_insert [@TransCmp α cmp] {t : RBNode α} (ht : Balanced t c n) (ht₂ : Ordered cmp t) :
    v' ∈ t.insert cmp v ↔ (v' ∈ t ∧ t.find? (cmp v) ≠ some v') ∨ v' = v := by
  refine ⟨fun h => ?_, fun | .inl ⟨h₁, h₂⟩ => ?_ | .inr h => ?_⟩
  · match e : zoom (cmp v) t with
    | (nil, p) =>
      let ⟨_, _, h₁, h₂⟩ := exists_insert_toList_zoom_nil ht e
      simp [← mem_toList, h₂] at h; rw [← or_assoc, or_right_comm] at h
      refine h.imp_left fun h => ?_
      simp [← mem_toList, h₁, h]
      rw [find?_eq_zoom, e]; nofun
    | (node .., p) =>
      let ⟨_, _, h₁, h₂⟩ := exists_insert_toList_zoom_node ht e
      simp [← mem_toList, h₂] at h; simp [← mem_toList, h₁]; rw [or_left_comm] at h ⊢
      rcases h with _|h <;> simp [*]
      refine .inl fun h => ?_
      rw [find?_eq_zoom, e] at h; cases h
      suffices cmpLT cmp v' v' by cases OrientedCmp.cmp_refl.symm.trans this.1
      have := ht₂.toList_sorted; simp [h₁, List.pairwise_append] at this
      exact h.elim (this.2.2 _ · |>.1) (this.2.1.1 _)
  · exact (mem_insert_of_mem ht h₁).resolve_right fun h' => h₂ <| ht₂.find?_some.2 ⟨h₁, h'⟩
  · exact h ▸ mem_insert_self ht
```

## Transitive premise context (1-hop, 14/14 premises, ≈1465 tokens)
### `Std.RBSet` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Basic.lean`
```lean
/--
An `RBSet` is a self-balancing binary search tree.
The `cmp` function is the comparator that will be used for performing searches;
it should satisfy the requirements of `TransCmp` for it to have sensible behavior.
-/
def RBSet (α : Type u) (cmp : α → α → Ordering) : Type u := {t : RBNode α // t.WF cmp}

/-- `O(1)`. Construct a new empty tree. -/
```

### `cmp` (commanddeclaration) at `Mathlib/Init/Data/Ordering/Basic.lean`
```lean
/--
Construct an `Ordering` from a type with a decidable `LT` instance,
assuming that incomparable terms are `Ordering.eq`.
-/
def cmp {α : Type u} [LT α] [DecidableRel ((· < ·) : α → α → Prop)] (a b : α) : Ordering :=
  cmpUsing (· < ·) a b
```

### `Std.TransCmp` (commanddeclaration) at `.lake/packages/std/Std/Classes/Order.lean`
```lean
/-- `TransCmp cmp` asserts that `cmp` induces a transitive relation. -/
class TransCmp (cmp : α → α → Ordering) extends OrientedCmp cmp : Prop where
  /-- The comparator operation is transitive. -/
  le_trans : cmp x y ≠ .gt → cmp y z ≠ .gt → cmp x z ≠ .gt
```

### `Balanced` (commanddeclaration) at `Mathlib/Analysis/LocallyConvex/Basic.lean`
```lean
/-- A set `A` is balanced if `a • A` is contained in `A` whenever `a` has norm at most `1`. -/
def Balanced (A : Set E) :=
  ∀ a : 𝕜, ‖a‖ ≤ 1 → a • A ⊆ A
```

### `Std.RBNode.exists_insert_toList_zoom_nil` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem exists_insert_toList_zoom_nil {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (nil, p)) :
    ∃ L R, t.toList = L ++ R ∧ (t.insert cmp v).toList = L ++ v :: R :=
  ⟨p.listL, p.listR, by simp [← zoom_toList e, insert_toList_zoom_nil ht e]⟩
```

### `or_assoc` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
theorem or_assoc : (a ∨ b) ∨ c ↔ a ∨ (b ∨ c) :=
  Iff.intro (.rec (.imp_right .inl) (.inr ∘ .inr))
            (.rec (.inl ∘ .inl) (.imp_left .inr))
```

### `or_right_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem or_right_comm : (a ∨ b) ∨ c ↔ (a ∨ c) ∨ b := by rw [or_assoc, or_assoc, @or_comm b]
```

### `Lean.Parser.Term.nofun` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
@[builtin_term_parser] def «nofun» := leading_parser "nofun"
```

### `Std.RBNode.exists_insert_toList_zoom_node` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem exists_insert_toList_zoom_node {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (node c' l v' r, p)) :
    ∃ L R, t.toList = L ++ v' :: R ∧ (t.insert cmp v).toList = L ++ v :: R := by
  refine ⟨p.listL ++ l.toList, r.toList ++ p.listR, ?_⟩
  simp [← zoom_toList e, insert_toList_zoom_node ht e]
```

### `or_left_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem or_left_comm  : a ∨ (b ∨ c) ↔ b ∨ (a ∨ c) := by rw [← or_assoc, ← or_assoc, @or_comm a b]
```

### `Lean.Parser.Term.suffices` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
@[builtin_term_parser] def «suffices» := leading_parser:leadPrec
  withPosition ("suffices " >> sufficesDecl) >> optSemicolon termParser
```

### `Std.RBNode.cmpLT` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Basic.lean`
```lean
/--
We say that `x < y` under the comparator `cmp` if `cmp x y = .lt`.

* In order to avoid assuming the comparator is always lawful, we use a
  local `∀ [TransCmp cmp]` binder in the relation so that the ordering
  properties of the tree only need to hold if the comparator is lawful.
* The `Nonempty` wrapper is a no-op because this is already a proposition,
  but it prevents the `[TransCmp cmp]` binder from being introduced when we don't want it.
-/
def cmpLT (cmp : α → α → Ordering) (x y : α) : Prop := Nonempty (∀ [TransCmp cmp], cmp x y = .lt)
```

### `List.pairwise_append` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem pairwise_append {l₁ l₂ : List α} :
    (l₁ ++ l₂).Pairwise R ↔ l₁.Pairwise R ∧ l₂.Pairwise R ∧ ∀ a ∈ l₁, ∀ b ∈ l₂, R a b := by
  induction l₁ <;> simp [*, or_imp, forall_and, and_assoc, and_left_comm]
```

### `Or.resolve_right` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
theorem Or.resolve_right (h: Or a b) (nb : Not b) : a := h.elim id (absurd · nb)
```
