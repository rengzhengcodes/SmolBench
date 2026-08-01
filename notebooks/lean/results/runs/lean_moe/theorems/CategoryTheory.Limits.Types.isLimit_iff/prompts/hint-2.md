## Current goal
```
⊢ IsLimit c
```

## Full tactic state
```
case refine_2
J : Type v
inst✝ : Category.{w, v} J
F : J ⥤ Type u
c : Cone F
h : ∀ s ∈ Functor.sections F, ∃! x, ∀ (j : J), c.π.app j x = s j
x : (c_1 : Cone F) → c_1.pt → c.pt
hx :
  ∀ (c_1 : Cone F) (y : c_1.pt),
    (fun x => ∀ (j : J), c.π.app j x = ↑(sectionOfCone c_1 y) j) (x c_1 y) ∧
      ∀ (y_1 : c.pt), (fun x => ∀ (j : J), c.π.app j x = ↑(sectionOfCone c_1 y) j) y_1 → y_1 = x c_1 y
⊢ IsLimit c
```

## Proof so far (4 tactics)
```lean
refine ⟨fun ⟨t⟩ s hs ↦ ?_, fun h ↦ ⟨?_⟩⟩
let cs := coneOfSection hs
exact ⟨t.lift cs ⟨⟩, fun j ↦ congr_fun (t.fac cs j) ⟨⟩,
  fun x hx ↦ congr_fun (t.uniq cs (fun _ ↦ x) fun j ↦ funext fun _ ↦ hx j) ⟨⟩⟩
choose x hx using fun c y ↦ h _ (sectionOfCone c y).2
```

## Theorem
`CategoryTheory.Limits.Types.isLimit_iff` in `Mathlib/CategoryTheory/Limits/Types.lean`

## Premises used in the next tactic
- `funext`
- `funext`
- `congr_fun`

## Premise signatures
### `funext` (commanddeclaration)
```lean
theorem funext {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x}
    (h : ∀ x, f x = g x) : f = g
```

### `funext` (commanddeclaration)
```lean
theorem funext {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x}
    (h : ∀ x, f x = g x) : f = g
```

### `congr_fun` (stdtacticaliasalias)
```lean
alias congr_fun
```

## Premise full source (with proof)
### `funext` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
**Function extensionality** is the statement that if two functions take equal values
every point, then the functions themselves are equal: `(∀ x, f x = g x) → f = g`.
It is called "extensionality" because it talks about how to prove two objects are equal
based on the properties of the object (compare with set extensionality,
which is `(∀ x, x ∈ s ↔ x ∈ t) → s = t`).

This is often an axiom in dependent type theory systems, because it cannot be proved
from the core logic alone. However in lean's type theory this follows from the existence
of quotient types (note the `Quot.sound` in the proof, as well as the `show` line
which makes use of the definitional equality `Quot.lift f h (Quot.mk x) = f x`).
-/
theorem funext {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x}
    (h : ∀ x, f x = g x) : f = g := by
  let eqv (f g : (x : α) → β x) := ∀ x, f x = g x
  let extfunApp (f : Quot eqv) (x : α) : β x :=
    Quot.liftOn f
      (fun (f : ∀ (x : α), β x) => f x)
      (fun _ _ h => h x)
  show extfunApp (Quot.mk eqv f) = extfunApp (Quot.mk eqv g)
  exact congrArg extfunApp (Quot.sound h)
```

### `funext` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
**Function extensionality** is the statement that if two functions take equal values
every point, then the functions themselves are equal: `(∀ x, f x = g x) → f = g`.
It is called "extensionality" because it talks about how to prove two objects are equal
based on the properties of the object (compare with set extensionality,
which is `(∀ x, x ∈ s ↔ x ∈ t) → s = t`).

This is often an axiom in dependent type theory systems, because it cannot be proved
from the core logic alone. However in lean's type theory this follows from the existence
of quotient types (note the `Quot.sound` in the proof, as well as the `show` line
which makes use of the definitional equality `Quot.lift f h (Quot.mk x) = f x`).
-/
theorem funext {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x}
    (h : ∀ x, f x = g x) : f = g := by
  let eqv (f g : (x : α) → β x) := ∀ x, f x = g x
  let extfunApp (f : Quot eqv) (x : α) : β x :=
    Quot.liftOn f
      (fun (f : ∀ (x : α), β x) => f x)
      (fun _ _ h => h x)
  show extfunApp (Quot.mk eqv f) = extfunApp (Quot.mk eqv g)
  exact congrArg extfunApp (Quot.sound h)
```

### `congr_fun` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```
