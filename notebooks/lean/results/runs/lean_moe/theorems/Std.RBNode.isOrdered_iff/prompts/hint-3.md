## Current goal
```
⊢ isOrdered cmp t none = true ↔ Ordered cmp t
```

## Full tactic state
```
α : Type u_1
cmp : α → α → Ordering
inst✝ : TransCmp cmp
t : RBNode α
⊢ isOrdered cmp t none = true ↔ Ordered cmp t
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Std.RBNode.isOrdered_iff` in `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`

## Premises used in the next tactic
- `Std.RBNode.isOrdered_iff'`

## Premise signatures
### `Std.RBNode.isOrdered_iff'` (commanddeclaration)
```lean
theorem isOrdered_iff' [@TransCmp α cmp] {t : RBNode α} :
    isOrdered cmp t L R ↔
    (∀ a ∈ L, t.All (cmpLT cmp a ·)) ∧
    (∀ a ∈ R, t.All (cmpLT cmp · a)) ∧
    (∀ a ∈ L, ∀ b ∈ R, cmpLT cmp a b) ∧
    Ordered cmp t
```

## Premise full source (with proof)
### `Std.RBNode.isOrdered_iff'` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem isOrdered_iff' [@TransCmp α cmp] {t : RBNode α} :
    isOrdered cmp t L R ↔
    (∀ a ∈ L, t.All (cmpLT cmp a ·)) ∧
    (∀ a ∈ R, t.All (cmpLT cmp · a)) ∧
    (∀ a ∈ L, ∀ b ∈ R, cmpLT cmp a b) ∧
    Ordered cmp t := by
  induction t generalizing L R with
  | nil =>
    simp [isOrdered]; split <;> simp [cmpLT_iff]
    next h => intro _ ha _ hb; cases h _ _ ha hb
  | node _ l v r =>
    simp [isOrdered, *]
    exact ⟨
      fun ⟨⟨Ll, lv, Lv, ol⟩, ⟨vr, rR, vR, or⟩⟩ => ⟨
        fun _ h => ⟨Lv _ h, Ll _ h, (Lv _ h).trans_l vr⟩,
        fun _ h => ⟨vR _ h, (vR _ h).trans_r lv, rR _ h⟩,
        fun _ hL _ hR => (Lv _ hL).trans (vR _ hR),
        lv, vr, ol, or⟩,
      fun ⟨hL, hR, _, lv, vr, ol, or⟩ => ⟨
        ⟨fun _ h => (hL _ h).2.1, lv, fun _ h => (hL _ h).1, ol⟩,
        ⟨vr, fun _ h => (hR _ h).2.2, fun _ h => (hR _ h).1, or⟩⟩⟩
```

## Transitive premise context (1-hop, 8/8 premises, ≈908 tokens)
### `Std.TransCmp` (commanddeclaration) at `.lake/packages/std/Std/Classes/Order.lean`
```lean
/-- `TransCmp cmp` asserts that `cmp` induces a transitive relation. -/
class TransCmp (cmp : α → α → Ordering) extends OrientedCmp cmp : Prop where
  /-- The comparator operation is transitive. -/
  le_trans : cmp x y ≠ .gt → cmp y z ≠ .gt → cmp x z ≠ .gt
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

### `Std.RBNode.isOrdered` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Basic.lean`
```lean
/-- `O(n)`. Verifies an ordering relation on the nodes of the tree. -/
def isOrdered (cmp : α → α → Ordering)
    (t : RBNode α) (l : Option α := none) (r : Option α := none) : Bool :=
  match t with
  | nil =>
    match l, r with
    | some l, some r => cmp l r = .lt
    | _, _ => true
  | node _ a v b => isOrdered cmp a l v && isOrdered cmp b v r

/-- The first half of Okasaki's `balance`, concerning red-red sequences in the left child. -/
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

### `Std.RBNode.cmpLT_iff` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Basic.lean`
```lean
theorem cmpLT_iff [TransCmp cmp] : cmpLT cmp x y ↔ cmp x y = .lt := ⟨fun ⟨h⟩ => h, (⟨·⟩)⟩
```

### `Std.RBNode.cmpLT.trans_l` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/WF.lean`
```lean
theorem cmpLT.trans_l {cmp x y} (H : cmpLT cmp x y) {t : RBNode α}
    (h : t.All (cmpLT cmp y ·)) : t.All (cmpLT cmp x ·) := h.imp fun h => H.trans h
```

### `Std.RBNode.cmpLT.trans_r` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/WF.lean`
```lean
theorem cmpLT.trans_r {cmp x y} (H : cmpLT cmp x y) {a : RBNode α}
    (h : a.All (cmpLT cmp · x)) : a.All (cmpLT cmp · y) := h.imp fun h => h.trans H
```

### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
```
