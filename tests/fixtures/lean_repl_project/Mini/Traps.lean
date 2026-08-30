/-- A docstring that names theorem fakeName and lemma otherFake, neither real. -/
@[simp]
theorem trapDoc (h : Nat := by simp) :
    1 + 1 = 2 := by
  rfl

-- A trailing comment that contains := and the word theorem.
theorem trapComment : True :=
  trivial

theorem trapNoAssign : ∀ n : Nat, n = n
  | 0 => rfl
  | _ + 1 => rfl
