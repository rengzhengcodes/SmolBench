## Current goal
```
⊢ proj i ∘ₗ stdBasis R φ j = diag j i
```

## Full tactic state
```
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
inst✝¹ : (i : ι) → Module R (φ i)
inst✝ : DecidableEq ι
i j : ι
⊢ proj i ∘ₗ stdBasis R φ j = diag j i
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`LinearMap.proj_comp_stdBasis` in `Mathlib/LinearAlgebra/StdBasis.lean`

## Premises used in the next tactic
- `LinearMap.stdBasis_eq_pi_diag`
- `LinearMap.proj_pi`

## Premise signatures
### `LinearMap.stdBasis_eq_pi_diag` (commanddeclaration)
```lean
theorem stdBasis_eq_pi_diag (i : ι) : stdBasis R φ i = pi (diag i)
```

### `LinearMap.proj_pi` (commanddeclaration)
```lean
theorem proj_pi (f : (i : ι) → M₂ →ₗ[R] φ i) (i : ι) : (proj i).comp (pi f) = f i
```

## Premise full source (with proof)
### `LinearMap.stdBasis_eq_pi_diag` (commanddeclaration) at `Mathlib/LinearAlgebra/StdBasis.lean`
```lean
theorem stdBasis_eq_pi_diag (i : ι) : stdBasis R φ i = pi (diag i) := by
  ext x j
  -- Porting note: made types explicit
  convert (update_apply (R := R) (φ := φ) (ι := ι) 0 x i j _).symm
  rfl
```

### `LinearMap.proj_pi` (commanddeclaration) at `Mathlib/LinearAlgebra/Pi.lean`
```lean
theorem proj_pi (f : (i : ι) → M₂ →ₗ[R] φ i) (i : ι) : (proj i).comp (pi f) = f i :=
  ext fun _ => rfl
```

## Transitive premise context (1-hop, 3/3 premises, ≈393 tokens)
### `Lean.MVarId.note` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Tactic/Assert.lean`
```lean
/-- Add the hypothesis `h : t`, given `v : t`, and return the new `FVarId`. -/
def _root_.Lean.MVarId.note (g : MVarId) (h : Name) (v : Expr) (t? : Option Expr := .none) :
    MetaM (FVarId × MVarId) := do
  (← g.assert h (← match t? with | some t => pure t | none => inferType v) v).intro1P

/--
  Convert the given goal `Ctx |- target` into `Ctx |- let name : type := val; target`.
  It assumes `val` has type `type` -/
```

### `Lean.Parser.Term.explicit` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
/--
`@x` disables automatic insertion of implicit parameters of the constant `x`.
`@e` for any term `e` also disables the insertion of implicit lambdas at this position.
-/
@[builtin_term_parser] def explicit := leading_parser
  "@" >> termParser maxPrec
/--
`.(e)` marks an "inaccessible pattern", which does not influence evaluation of the pattern match, but may be necessary for type-checking.
In contrast to regular patterns, `e` may be an arbitrary term of the appropriate type.
-/
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```
