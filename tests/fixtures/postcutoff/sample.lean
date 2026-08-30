/-
Block comment that must not declare anything:
theorem commentedOutBlock : True := trivial
/- nested block comment
theorem nestedCommented : True := trivial
-/
still inside the outer block comment
-/

/-- A doc comment mentioning `theorem docCommented`. -/
theorem topLevelThm : True := trivial

-- theorem lineCommented : True := trivial

namespace Alpha

theorem inNamespace : True := trivial

protected theorem protectedThm : True := trivial

private theorem privateThm : True := trivial

theorem _root_.RootLevel.escaped : True := trivial

namespace Beta

lemma nested : True := trivial

section Helper

def sectionScoped : Nat := 0

end Helper

def afterSectionEnd : Nat := 1

end Beta

noncomputable section

def inNoncomputableSection : Nat := 2

end

instance : Inhabited Nat := ⟨0⟩

instance [Inhabited Bool] : Inhabited (Bool × Bool) := ⟨(true, true)⟩

instance namedInst : Inhabited Bool := ⟨true⟩

open Nat in
theorem afterOpenIn : True := trivial

open Nat in theorem sameLineOpenIn : True := trivial

@[simp]
theorem simpTagged : True := trivial

@[deprecated (since := "2026-01-01")]
theorem deprecatedThm : True := trivial

@[deprecated (since := "2026-01-01")]
alias oldName := newName

alias plainAlias := inNamespace

@[deprecated (since := "2026-02-02")]
alias ⟨_, iffBackward⟩ := someIff

example : True := trivial

structure Struct where
  theorem : Nat

class MyClass (α : Type) where
  op : α → α

abbrev Abbrev := Nat

inductive Ind where
  | a
  | b

def universeDef.{u} (α : Type u) : Type u := α

end Alpha

def rootAfterEnd : Nat := 3
