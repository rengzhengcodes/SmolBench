/-
Copyright placeholder. This fixture mimics a mathlib file under the module
system: scope commands that a later declaration silently depends on.
-/
module

public import Mini.A

/-! Docs that mention `open Fake in` and `variable` so comments must be ignored. -/

@[expose] public section

noncomputable section

open Set Function
open scoped Topology

universe u

variable {α : Type u} [Inhabited α]

section Closed
open Hidden hiding foo
variable (dropped : Nat)
end Closed

namespace Mini.Outer

set_option autoImplicit true in
def helper (n : Nat) : Nat := n

open Classical in
theorem usesClassical : True := trivial

variable (p : α) in
theorem usesP : True := trivial

variable [DecidableEq α] (x : α)
  {y : α}

attribute [local simp] Nat.add_comm
local notation "‖" a "‖" => a

/-- Target with attributes and a dotted name. -/
@[simp, to_additive (attr := simp)]
protected theorem Inner.target (h : x = y) : x = y := by
  exact h

theorem whereStyle : True ∧ True where
  left := trivial
  right := trivial

end Mini.Outer
