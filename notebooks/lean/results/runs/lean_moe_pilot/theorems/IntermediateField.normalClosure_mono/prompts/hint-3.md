## Current goal
```
⊢ ⨆ f, map f K ≤ ⨆ f, map f K'
```

## Full tactic state
```
F : Type u_1
K✝ : Type u_2
L : Type u_3
inst✝⁵ : Field F
inst✝⁴ : Field K✝
inst✝³ : Field L
inst✝² : Algebra F K✝
inst✝¹ : Algebra F L
K K' : IntermediateField F L
inst✝ : Normal F L
h : K ≤ K'
⊢ ⨆ f, map f K ≤ ⨆ f, map f K'
```

## Proof so far (1 tactic)
```lean
rw [normalClosure_def', normalClosure_def']
```

## Theorem
`IntermediateField.normalClosure_mono` in `Mathlib/FieldTheory/NormalClosure.lean`

## Premises used in the next tactic
- `iSup_mono`
- `IntermediateField.map_mono`

## Premise signatures
### `iSup_mono` (commanddeclaration)
```lean
@[gcongr]
theorem iSup_mono (h : ∀ i, f i ≤ g i) : iSup f ≤ iSup g
```

### `IntermediateField.map_mono` (commanddeclaration)
```lean
theorem map_mono (f : L →ₐ[K] L') {S T : IntermediateField K L} (h : S ≤ T) :
    S.map f ≤ T.map f
```

## Premise full source (with proof)
### `iSup_mono` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
@[gcongr]
theorem iSup_mono (h : ∀ i, f i ≤ g i) : iSup f ≤ iSup g :=
  iSup_le fun i => le_iSup_of_le i <| h i
```

### `IntermediateField.map_mono` (commanddeclaration) at `Mathlib/FieldTheory/IntermediateField.lean`
```lean
theorem map_mono (f : L →ₐ[K] L') {S T : IntermediateField K L} (h : S ≤ T) :
    S.map f ≤ T.map f :=
  SetLike.coe_mono (Set.image_subset f h)
```

## Transitive premise context (1-hop, 7/7 premises, ≈2729 tokens)
### `Lean.MVarId.gcongr` (commanddeclaration) at `Mathlib/Tactic/GCongr/Core.lean`
```lean
/-- The core of the `gcongr` tactic.  Parse a goal into the form `(f _ ... _) ∼ (f _ ... _)`,
look up any relevant @[gcongr] lemmas, try to apply them, recursively run the tactic itself on
"main" goals which are generated, and run the discharger on side goals which are generated. If there
is a user-provided template, first check that the template asks us to descend this far into the
match. -/
partial def _root_.Lean.MVarId.gcongr
    (g : MVarId) (template : Option Expr) (names : List (TSyntax ``binderIdent))
    (mainGoalDischarger : MVarId → MetaM Unit := gcongrForwardDischarger)
    (sideGoalDischarger : MVarId → MetaM Unit := gcongrDischarger) :
    MetaM (Bool × List (TSyntax ``binderIdent) × Array MVarId) := g.withContext do
  withTraceNode `Meta.gcongr (fun _ => return m!"gcongr: ⊢ {← g.getType}") do
  match template with
  | none =>
    -- A. If there is no template, try to resolve the goal by the provided tactic
    -- `mainGoalDischarger`, and continue on if this fails.
    try mainGoalDischarger g; return (true, names, #[])
    catch _ => pure ()
  | some tpl =>
    -- B. If there is a template:
    -- (i) if the template is `?_` (or `?_ x1 x2`, created by entering binders)
    -- then try to resolve the goal by the provided tactic `mainGoalDischarger`;
    -- if this fails, stop and report the existing goal.
    if let .mvar mvarId := tpl.getAppFn then
      if let .syntheticOpaque ← mvarId.getKind then
        try mainGoalDischarger g; return (true, names, #[])
        catch _ => return (false, names, #[g])
    -- (ii) if the template is *not* `?_` then continue on.
  -- Check that the goal is of the form `rel (lhsHead _ ... _) (rhsHead _ ... _)`
  let .app (.app rel lhs) rhs ← withReducible g.getType'
    | throwError "gcongr failed, not a relation"
  let some relName := rel.getAppFn.constName?
    | throwError "gcongr failed, relation head {rel} is not a constant"
  let (some lhsHead, lhsArgs) := lhs.withApp fun e a => (e.constName?, a)
    | if template.isNone then return (false, names, #[g])
      throwError "gcongr failed, {lhs} is not a constant"
  let (some rhsHead, rhsArgs) := rhs.withApp fun e a => (e.constName?, a)
    | if template.isNone then return (false, names, #[g])
      throwError "gcongr failed, {rhs} is not a constant"
  -- B. If there is a template, check that it is of the form `tplHead _ ... _` and that
  -- `tplHead = lhsHead = rhsHead`
  let tplArgs ← if let some tpl := template then
    let (some tplHead, tplArgs) := tpl.withApp fun e a => (e.constName?, a)
      | throwError "gcongr failed, {tpl} is not a constant"
    unless tplHead == lhsHead && tplArgs.size == rhsArgs.size do
      throwError "expected {tplHead}, got {lhsHead}\n{lhs}"
    unless tplHead == rhsHead && tplArgs.size == rhsArgs.size do
      throwError "expected {tplHead}, got {rhsHead}\n{rhs}"
    -- and also build an array of `Expr` corresponding to the arguments `_ ... _` to `tplHead` in
    -- the template (these will be used in recursive calls later), and an array of booleans
    -- according to which of these contain `?_`
    tplArgs.mapM fun tpl => do
      let mctx ← getMCtx
      let hasMVar := tpl.findMVar? fun mvarId =>
        if let some mdecl := mctx.findDecl? mvarId then
          mdecl.kind matches .syntheticOpaque
        else
          false
      pure (some tpl, hasMVar.isSome)
  -- A. If there is no template, check that `lhs = rhs`
  else
    unless lhsHead == rhsHead && lhsArgs.size == rhsArgs.size do
      -- (if not, stop and report the existing goal)
      return (false, names, #[g])
    -- and also build an array of booleans according to which arguments `_ ... _` to the head
    -- function differ between the LHS and RHS
    (lhsArgs.zip rhsArgs).mapM fun (lhsArg, rhsArg) =>
      return (none, !(← withReducibleAndInstances <| isDefEq lhsArg rhsArg))
  -- Name the array of booleans `varyingArgs`: this records which arguments to the head function are
  -- supposed to vary, according to the template (if there is one), and in the absence of a template
  -- to record which arguments to the head function differ between the two sides of the goal.
  let varyingArgs := tplArgs.map (·.2)
  if varyingArgs.all not then
    throwError "try rfl"
  let s ← saveState
  let mut ex? := none
  -- Look up the `@[gcongr]` lemmas whose conclusion has the same relation and head function as
  -- the goal and whether the boolean-array of varying/nonvarying arguments of such
  -- a lemma matches `varyingArgs`.
  for lem in (gcongrExt.getState (← getEnv)).findD (relName, lhsHead, varyingArgs) #[] do
    let gs ← try
      -- Try `apply`-ing such a lemma to the goal.
      Except.ok <$> g.apply (← mkConstWithFreshMVarLevels lem.declName)
    catch e => pure (Except.error e)
    match gs with
    | .error e =>
      -- If the `apply` fails, go on to try to apply the next matching lemma.
      -- If all the matching lemmas fail to `apply`, we will report (somewhat arbitrarily) the
      -- error message on the first failure, so stash that.
      ex? := ex? <|> (some (← saveState, e))
      s.restore
    | .ok gs =>
      let some e ← getExprMVarAssignment? g | panic! "unassigned?"
      let args := e.getAppArgs
      let mut subgoals := #[]
      let mut names := names
      -- If the `apply` succeeds, iterate over `(i, j)` belonging to the lemma's `mainSubgoal`
      -- list: here `i` is an index in the lemma's array of antecedents, and `j` is an index in
      -- the array of arguments to the head function in the conclusion of the lemma (this should
      -- be the same as the head function of the LHS and RHS of our goal), such that the `i`-th
      -- antecedent to the lemma is a relation between the LHS and RHS `j`-th inputs to the head
      -- function in the goal.
      for (i, j) in lem.mainSubgoals do
        -- We anticipate that such a "main" subgoal should not have been solved by the `apply` by
        -- unification ...
        let some (.mvar mvarId) := args[i]? | panic! "what kind of lemma is this?"
        -- Introduce all variables and hypotheses in this subgoal.
        let (names2, _vs, mvarId) ← mvarId.introsWithBinderIdents names
        -- B. If there is a template, look up the part of the template corresponding to the `j`-th
        -- input to the head function
        let tpl ← tplArgs[j]!.1.mapM fun e => do
          let (_vs, _, e) ← lambdaMetaTelescope e
          pure e
        -- Recurse: call ourself (`Lean.MVarId.gcongr`) on the subgoal with (if available) the
        -- appropriate template
        let (_, names2, subgoals2) ← mvarId.gcongr tpl names2 mainGoalDischarger sideGoalDischarger
        (names, subgoals) := (names2, subgoals ++ subgoals2)
      let mut out := #[]
      -- Also try the discharger on any "side" (i.e., non-"main") goals which were not resolved
      -- by the `apply`.
      for g in gs do
        if !(← g.isAssigned) && !subgoals.contains g then
          try sideGoalDischarger g
          catch _ => out := out.push g
      -- Return all unresolved subgoals, "main" or "side"
      return (true, names, out ++ subgoals)
  -- A. If there is no template, and there was no `@[gcongr]` lemma which matched the goal,
  -- report this goal back.
  if template.isNone then
    return (false, names, #[g])
  let some (sErr, e) := ex?
    -- B. If there is a template, and there was no `@[gcongr]` lemma which matched the template,
    -- fail.
    | throwError "gcongr failed, no @[gcongr] lemma applies for the template portion \
        {template} and the relation {rel}"
  -- B. If there is a template, and there was a `@[gcongr]` lemma which matched the template, but
  -- it was not possible to `apply` that lemma, then report the error message from `apply`-ing that
  -- lemma.
  sErr.restore
  throw e

/-- The `gcongr` tactic applies "generalized congruence" rules, reducing a relational goal
between a LHS and RHS matching the same pattern to relational subgoals between the differing
inputs to the pattern.  For example,
```
```

### `iSup` (commanddeclaration) at `Mathlib/Order/SetNotation.lean`
```lean
/-- Indexed supremum -/
def iSup [SupSet α] (s : ι → α) : α :=
  sSup (range s)
```

### `iSup_le` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
theorem iSup_le (h : ∀ i, f i ≤ a) : iSup f ≤ a :=
  sSup_le fun _ ⟨i, Eq⟩ => Eq ▸ h i
```

### `le_iSup_of_le` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
theorem le_iSup_of_le (i : ι) (h : a ≤ f i) : a ≤ iSup f :=
  h.trans <| le_iSup _ i
```

### `IntermediateField` (commanddeclaration) at `Mathlib/FieldTheory/IntermediateField.lean`
```lean
/-- `S : IntermediateField K L` is a subset of `L` such that there is a field
tower `L / S / K`. -/
structure IntermediateField extends Subalgebra K L where
  inv_mem' : ∀ x ∈ carrier, x⁻¹ ∈ carrier
```

### `SetLike.coe_mono` (commanddeclaration) at `Mathlib/Data/SetLike/Basic.lean`
```lean
@[mono]
theorem coe_mono : Monotone (SetLike.coe : A → Set B) := fun _ _ => coe_subset_coe.mpr
```

### `Set.image_subset` (commanddeclaration) at `Mathlib/Data/Set/Image.lean`
```lean
/-- Image is monotone with respect to `⊆`. See `Set.monotone_image` for the statement in
terms of `≤`. -/
@[gcongr]
theorem image_subset {a b : Set α} (f : α → β) (h : a ⊆ b) : f '' a ⊆ f '' b := by
  simp only [subset_def, mem_image]
  exact fun x => fun ⟨w, h1, h2⟩ => ⟨w, h h1, h2⟩
```
