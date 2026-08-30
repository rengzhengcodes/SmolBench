theorem theoremA {n : ℕ} (hn : n > 0) : P n → Q n := by
  intro h
  simp
  exact Mini.premiseA h (Mini.premiseB n)
