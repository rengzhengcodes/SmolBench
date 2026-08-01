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
