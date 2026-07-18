## Current goal
```
⊢ ltTrichotomy x y p q r = s ↔ x < y ∧ p = s ∨ x = y ∧ q = s ∨ y < x ∧ r = s
```

## Full tactic state
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
r✝ : α → α → Prop
inst✝ : LinearOrder α
P : Sort u_3
x y : α
p q r s : P
h : y < x
⊢ ltTrichotomy x y p q r = s ↔ x < y ∧ p = s ∨ x = y ∧ q = s ∨ y < x ∧ r = s
```

## Proof so far (3 tactics)
```lean
refine ltByCases x y (fun h => ?_) (fun h => ?_) (fun h => ?_)
simp only [ltTrichotomy_lt, false_and, true_and, or_false, h, h.not_lt, h.ne]
simp only [ltTrichotomy_eq, false_and, true_and, or_false, false_or, h, lt_irrefl]
```

## Theorem
`ltTrichotomy_eq_iff` in `Mathlib/Order/Basic.lean`

## Premises used in the next tactic
- `ltTrichotomy_gt`
- `false_and`
- `true_and`
- `false_or`

## Premise signatures
### `ltTrichotomy_gt` (lemma)
```lean
@[simp]
lemma ltTrichotomy_gt (h : y < x) : ltTrichotomy x y p q r = r
```

### `false_and` (commanddeclaration)
```lean
@[simp] theorem false_and (p : Prop) : (False ∧ p) = False
```

### `true_and` (commanddeclaration)
```lean
@[simp] theorem true_and (p : Prop) : (True ∧ p) = p
```

### `false_or` (commanddeclaration)
```lean
@[simp] theorem false_or (p : Prop) : (False ∨ p) = p
```

## Premise full source (with proof)
### `ltTrichotomy_gt` (lemma) at `Mathlib/Order/Basic.lean`
```lean
@[simp]
lemma ltTrichotomy_gt (h : y < x) : ltTrichotomy x y p q r = r := ltByCases_gt h
```

### `false_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem false_and (p : Prop) : (False ∧ p) = False := eq_false (·.1)
```

### `true_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem true_and (p : Prop) : (True ∧ p) = p := propext ⟨(·.2), (⟨trivial, ·⟩)⟩
```

### `false_or` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem false_or (p : Prop) : (False ∨ p) = p := propext ⟨fun (.inr h) => h, .inr⟩
```
