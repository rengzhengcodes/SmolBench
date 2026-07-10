# IsPerfectClosure.equiv_symm_apply   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/IsPerfectClosure.lean`  

**Ground-truth tail (from k):**
```lean
rw [equiv_symm, equiv_apply j i p _ _ _ h]
```

**True premises at k:** `IsPerfectClosure.equiv_symm`, `IsPerfectClosure.equiv_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | · | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | · | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ | ✓ | · | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.2s, in=485, out=101)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, RingEquiv.symm_apply, iterateFrobeniusEquiv_symm_apply]
rw [equiv_apply, iterateFrobeniusEquiv_apply]
rw [RingEquiv.toRingHom_eq_coe, RingHom.comp_apply]
rw [RingEquiv.coe_toRingHom, RingEquiv.coe_toRingHom]
rw [frobenius_iterate, iterateFrobeniusEquiv_coe]
simp only [RingHom.id_apply]
```

**lean_error:** tail step 1/6 ('rw [h, RingEquiv.symm_apply, iterateFrobeniusEquiv_symm_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=485, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa only [equiv_symm_apply] using h
```

**lean_error:** tail step 1/1 ('simpa only [equiv_symm_apply] using h'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=474, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply ring_equiv.symm_apply_apply
apply iterate_frobenius_equiv_symm_apply
simp [h]
```

**lean_error:** tail step 1/3 ('apply ring_equiv.symm_apply_apply'): unknown identifier 'ring_equiv.symm_apply_apply'

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=465, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RingEquiv.symm_apply, iterateFrobeniusEquiv_symm_apply, h]
rw [←i.map_pow, ←i.map_pow]
simp [h]
```

**lean_error:** tail step 1/3 ('rw [RingEquiv.symm_apply, iterateFrobeniusEquiv_symm_apply, h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 139.1s, verify 0.1s, in=449, out=8238)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply (iterateFrobeniusEquiv M p n).injective,
rw [map_pow, ← iterateFrobeniusEquiv_apply, RingEquiv.apply_symm_apply, equiv_comp i j p, h]
```

**lean_error:** tail step 1/2 ('apply (iterateFrobeniusEquiv M p n).injective,'): <stdin>:1:45: expected end of input

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 0.6s, verify 0.2s, in=449, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← h]
```

**final state (truncated):**
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
...
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=850, out=42)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply _ n y]
rw [h] 
rw [(iterateFrobeniusEquiv L p n).symm_apply] 
rw [equiv_symm]
```

**lean_error:** tail step 1/4 ('rw [equiv_symm, equiv_apply _ n y]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=850, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply _ _ _ _ h]
```

**lean_error:** tail step 1/1 ('rw [equiv_symm, equiv_apply _ _ _ _ h]'): application type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 102.0s, verify 0.1s, in=839, out=7974)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply]
```

**final state (truncated):**
```
case h
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
...
```

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=830, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply]
apply iterateFrobeniusEquiv_symm_apply
```

**lean_error:** tail step 2/2 ('apply iterateFrobeniusEquiv_symm_apply'): unknown identifier 'iterateFrobeniusEquiv_symm_apply'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 83.5s, verify 0.3s, in=814, out=4132)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [equiv_symm]
apply equiv_apply x n y h
```

**lean_error:** tail step 2/2 ('apply equiv_apply x n y h'): application type mismatch

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=814, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [equiv_symm, equiv_apply i j _ _ _ h]
```

**lean_error:** tail step 1/1 ('simp only [equiv_symm, equiv_apply i j _ _ _ h]'): application type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.5s, in=1565, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply _ _ y h]
```

**lean_error:** tail step 1/1 ('rw [equiv_symm, equiv_apply _ _ y h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1565, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply _ _ _ _ h]
```

**lean_error:** tail step 1/1 ('rw [equiv_symm, equiv_apply _ _ _ _ h]'): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 105.4s, verify 0.1s, in=1554, out=8234)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply]
```

**final state (truncated):**
```
case h
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
...
```

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1545, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply]
apply iterateFrobeniusEquiv_symm_apply
simp [h]
```

**lean_error:** tail step 2/3 ('apply iterateFrobeniusEquiv_symm_apply'): unknown identifier 'iterateFrobeniusEquiv_symm_apply'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 105.7s, verify 0.1s, in=1532, out=5570)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [equiv_symm], exact equiv_apply j i x n y h
```

**lean_error:** tail step 1/1 ('rw [equiv_symm], exact equiv_apply j i x n y h'): <stdin>:1:15: expected end of input

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1532, out=30)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [equiv_symm, equiv_apply i j p x n y h, RingEquiv.symm_symm]
```

**lean_error:** tail step 1/1 ('simp only [equiv_symm, equiv_apply i j p x n y h, RingEquiv.symm_symm]'): application type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1589, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply _ _ y h],
simp only [RingEquiv.symm_symm]
```

**lean_error:** tail step 1/2 ('rw [equiv_symm, equiv_apply _ _ y h],'): <stdin>:1:36: expected end of input

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1589, out=32)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [equiv_symm, iterateFrobeniusEquiv_symm] using
  equiv_apply _ _ _ _ _ h.symm
```

**lean_error:** tail step 1/2 ('simpa only [equiv_symm, iterateFrobeniusEquiv_symm] using'): <stdin>:1:57: unexpected end of input

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 68.5s, verify 0.1s, in=1578, out=5222)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
But wait, the goal is:

(RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)

After applying `rw [equiv_symm]`, the left-hand side becomes (equiv j i p) x.

Then, we need to relate this to the right-hand side. The `equiv_apply` lemma says that equiv i j p x = (iterateFrobeniusEquiv M p n).symm (j y). But here we have equiv j i p x. Maybe we need to use equiv_apply with swapped i and j?

Wait, the user provided `h : j y = x ^ p ^ n`, which is similar to the hypothesis in `equiv_apply`, which requires `i y = x ^ p ^ n`.

So perhaps we need to adjust the application of `equiv_apply`. Let me check the statement of `equiv_apply`:

theorem equiv_apply (x : L) (n : ℕ) (y : K) (h : i y = x ^ p ^ n) :
    equiv i j p x = (iterateFrobeniusEquiv M p n).symm (j y)

But in our case, we have `equiv j i p x` on the left after applying `equiv_symm`. So maybe we can apply `equiv_apply` with i and j swapped. Let's see:

If we set i' = j, j' = i, then the lemma would become:

equiv j i p x = (iterateFrobeniusEquiv ... ).symm (i y)

But the right-hand side of our goal is (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)

Wait, the iterateFrobeniusEquiv is over L here, but in the lemma it's over M. Hmm, maybe there's a mix-up in the variables.

Alternatively, maybe after applying `rw [equiv_symm]`, we can apply `equiv_apply` with the appropriate arguments. Let's try to see:

After `rw [equiv_symm]`, the left-hand side is (equiv j i p) x.

We need to show that this equals (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y).

If we can apply `equiv_apply` to (equiv j i p) x, then according to the lemma, if we have j y = x ^ p ^ n, then equiv j i p x = (iterateFrobeniusEquiv ... ).symm (i y). Wait, but in our case, the hypothesis is h : j y = x ^ p ^ n. So that's exactly the hypothesis needed for `equiv_apply` with i and j swapped.

So applying `equiv_apply` with x, n, y, h should give us:

equiv j i p x = (iterateFrobeniusEquiv M p n).symm (i y)

But the right-hand side of our goal is (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y). So unless iterateFrobeniusEquiv M p n is the same as iterateFrobeniusEquiv L p n, which they aren't. Wait, maybe there's a typo in the problem statement?

Wait, looking back at the current goal:

(RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)

After applying `rw [equiv_symm]`, the left-hand side is (equiv j i p) x.

We need to show that this equals (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y).

But according to `equiv_apply`, if we have j y = x ^ p ^ n, then equiv j i p x = (iterateFrobeniusEquiv M p n).symm (i y). But the right-hand side here is (iterateFrobeniusEquiv L p n).symm (i y). So unless L and M are the same, which they aren't, this doesn't match.

Wait, but maybe there's a mistake in the problem setup. Alternatively, perhaps the iterateFrobeniusEquiv is being applied to the wrong field. Let me check the parameters of `iterateFrobeniusEquiv` in the lemma.

In the `equiv_apply` lemma, the iterateFrobeniusEquiv is over M, which is the codomain of j. In our case, we have j : K →+* M, so in the lemma, the iterateFrobeniusEquiv is over M. But in our goal, the iterateFrobeniusEquiv is over L. That seems inconsistent.

Wait, but in the current goal, the right-hand side is (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y). The iterateFrobeniusEquiv is over L, which is the codomain of i. But in the lemma, when we have equiv_apply, the iterateFrobeniusEquiv is over M, which is the codomain of j.

So perhaps there's a mismatch here. How can we reconcile this?

Alternatively, maybe the problem requires using some other lemma or unfolding some definitions. Let me think.

Wait, the user mentioned that the premises used in the next tactic are `IsPerfectClosure.equiv_symm` and `IsPerfectClosure.equiv_apply`. So perhaps the solution is to first apply `rw [equiv_symm]`, and then apply `equiv_apply` with the appropriate arguments, but we need to adjust for the different iterateFrobeniusEquiv.

Alternatively, maybe the iterateFrobeniusEquiv L p n is the same as the iterateFrobeniusEquiv M p n in this context. But that doesn't seem right.

Wait, let's look at the statement of `iterateFrobeniusEquiv`. It's defined as:

iterateFrobeniusEquiv L p n = (FrobeniusEquiv L p)^n

But FrobeniusEquiv is defined for a ring equipped with an exponent characteristic p, and it's a ring equivalence from L to L, given by the Frobenius endomorphism. So iterating it n times would give a ring equivalence from L to L.

But in the lemma `equiv_apply`, the right-hand side is (iterateFrobeniusEquiv M p n).symm (j y), which is an element of M. But in our goal, the right-hand side is (iterateFrobeniusEquiv L p n).symm (i y), which is an element of L.

So unless there's some compatibility between these iterateFrobeniusEquivs, this seems like a problem.

But wait, in the goal, we have x : M, and the left-hand side after applying `equiv_symm` is (equiv j i p) x, which is an element of K (since equiv j i p is a ring equivalence from M to K? Wait, no. The `equiv` is a ring equivalence between the closures. Wait, maybe I need to recall the definition of `equiv` in this context.

The `equiv` is defined in the `IsPerfectClosure` context. Let me check the definition. The `equiv` is a ring equivalence between the perfect closures of K with respect to i and j. But perhaps in this case, since i and j are embeddings of K into L and M, which are perfect closures, the `equiv` provides an isomorphism between L and M over K.

But I might be getting confused here. Let's try to proceed step by step.

The goal is to show that (RingEquiv.symm (equiv i j p)) x equals (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y).

After applying `rw [equiv_symm]`, the left-hand side becomes (equiv j i p) x.

So now the goal is:

(equiv j i p) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)

Now, according to the `equiv_apply` lemma, if we have j y = x ^ p ^ n, then (equiv j i p) x = (iterateFrobeniusEquiv M p n).symm (i y). But in our goal, the right-hand side is (iterateFrobeniusEquiv L p n).symm (i y). So unless L and M are the same, which they aren't, this doesn't match.

But wait, the hypothesis h is j y = x ^ p ^ n. So maybe we can apply the `equiv_apply` lemma here, but then we need to relate the iterateFrobeniusEquiv over M to the one over L.

Alternatively, perhaps there's a typo in the problem statement, and the iterateFrobeniusEquiv should be over M instead of L. But assuming the problem is correct, we need to find a way to make this work.

Alternatively, maybe the ring equivalence (equiv j i p) x is equal to (iterateFrobeniusEquiv L p n).symm (i y) through some other means. Let's think about the definitions.

The `equiv` between j and i would be a ring isomorphism between the perfect closures, which are L and M. But if L and M are both perfect closures of K, then they should be isomorphic, but the specific isomorphism might depend on the embeddings i and j.

Alternatively, maybe the iterateFrobeniusEquiv L p n is related to the iterateFrobeniusEquiv M p n via the equivalence.

But I'm not sure. Let's try to see what happens if we apply `equiv_apply` here. The lemma says:

equiv_apply (x : L) (n : ℕ) (y : K) (h : i y = x ^ p ^ n) :
    equiv i j p x = (iterateFrobeniusEquiv M p n).symm (j y)

But in our case, after applying `equiv_symm`, we have equiv j i p x. If we apply `equiv_apply` with i and j swapped, then we would have:

equiv j i p x = (iterateFrobeniusEquiv M p n).symm (i y)

But the right-hand side of our goal is (iterateFrobeniusEquiv L p n).symm (i y). So unless there's a way to relate these two, this doesn't help.

Wait, but maybe the iterateFrobeniusEquiv L p n is the same as the iterateFrobeniusEquiv M p n when transported via the equivalence. But I don't see how that would be the case.

Alternatively, perhaps the problem requires using the fact that the Frobenius map is natural, or that the equivalence commutes with the Frobenius.

Alternatively, maybe the key is to use the `h` hypothesis, which is j y = x ^ p ^ n. Let's see:

We have j y = x ^ p ^ n. If we apply the Frobenius map to both sides, we get (j y)^p = x ^ p ^ (n+1). But I'm not sure if that helps.

Alternatively, maybe we can express x in terms of j y. Since j y = x ^ p ^ n, then x = (j y) ^ p ^ (-n)? But exponents are natural numbers, so that might not make sense.

Alternatively, perhaps we can use the fact that the Frobenius map is an isomorphism in characteristic p, since the rings are perfect.

Wait, the `PerfectRing` instances are given for L and M, so the Frobenius endomorphism is surjective. Hence, the Frobenius map is an isomorphism.

Therefore, the iterateFrobeniusEquiv is a ring equivalence. So, (iterateFrobeniusEquiv L p n) is a ring equivalence from L to L, given by raising to the p^n-th power. Similarly for M.

But in the lemma `equiv_apply`, the right-hand side is (iterateFrobeniusEquiv M p n).symm (j y), which is j y raised to the p^n-th power, since the inverse of the Frobenius equivalence is the inverse Frobenius, which is raising to the p^n-th root. But since the Frobenius is an isomorphism, this is well-defined.

But in our goal, the right-hand side is (iterateFrobeniusEquiv L p n).symm (i y), which is i y raised to the p^n-th root in L.

But according to the lemma, after applying `equiv_symm` and `equiv_apply`, we get that (equiv j i p) x = (iterateFrobeniusEquiv M p n).symm (i y). But we need to show that this equals (iterateFrobeniusEquiv L p n).symm (i y). So unless these two expressions are equal, which would require that the p^n-th root of i y in M is the same as the p^n-th root of i y in L, which doesn't make sense unless L and M are the same, which they aren't.

This suggests that there's a mistake in the problem statement or in the application of the lemmas. However, since the user says that the premises used in the next tactic are `equiv_symm` and `equiv_apply`, and the lemma `equiv_apply` is the one that should be used here, perhaps the solution is to apply these two lemmas and then somehow reconcile the iterateFrobeniusEquiv over M and L.

Alternatively, maybe the key is that the equivalence between L and M over K commutes with the Frobenius maps. So, the equivalence equiv j i p would carry the Frobenius on L to the Frobenius on M. Therefore, the iterateFrobeniusEquiv on L would correspond to the iterateFrobeniusEquiv on M via the equivalence.

If that's the case, then perhaps (iterateFrobeniusEquiv M p n).symm (i y) is equal to (equiv j i p) (iterateFrobeniusEquiv L p n).symm (i y). But I'm not sure.

Alternatively, maybe we need to apply the `equiv_apply` lemma and then use the fact that the equivalence commutes with the Frobenius.

But this is getting too vague. Let's try to proceed with the initial idea of applying `rw [equiv_symm, equiv_apply]` and see if that works.

If we first apply `rw [equiv_symm]`, the left-hand side becomes (equiv j i p) x.

Then, applying `rw [equiv_apply]` would require that we have the hypothesis j y = x ^ p ^ n, which we do have (h : j y = x ^ p ^ n). So applying `equiv_apply` with x, n, y, h would replace (equiv j i p) x with (iterateFrobeniusEquiv M p n).symm (i y).

So after these two rewrites, the goal becomes:

(iterateFrobeniusEquiv M p n).symm (i y) = (iterateFrobeniusEquiv L p n).symm (i y)

But this is not true unless L and M are the same, which they aren't. So this suggests that the initial approach is incorrect.

Hmm, this is a problem. So perhaps there's a missing step or a different lemma that needs to be applied.

Wait, but the user mentioned that the theorem is `IsPerfectClosure.equiv_symm_apply`, which is the one we're trying to prove. The premises used are `equiv_symm` and `equiv_apply`, so maybe the proof is just applying these two lemmas.

But according to the current goal, after applying these two lemmas, we end up with a goal that equates two different expressions involving iterateFrobeniusEquiv over L and M, which doesn't seem to hold.

This suggests that there's an error in the reasoning. Maybe the correct approach is to use `equiv_apply` in a different way.

Wait, let's look at the statement of `equiv_apply` again:

theorem equiv_apply (x : L) (n : ℕ) (y : K) (h : i y = x ^ p ^ n) :
    equiv i j p x = (iterateFrobeniusEquiv M p n).symm (j y)

In our case, after applying `equiv_symm`, we have (equiv j i p) x on the left. If we can apply `equiv_apply` to this, but with i and j swapped, then we would need a hypothesis of the form j y = x ^ p ^ n, which we have (h : j y = x ^ p ^ n).

So applying `equiv_apply` with swapped i and j would give:

equiv j i p x = (iterateFrobeniusEquiv M p n).symm (i y)

But the right-hand side of our goal is (iterateFrobeniusEquiv L p n).symm (i y). So unless there's a way to relate these two iterateFrobeniusEquivs, this doesn't help.

Wait, but maybe the iterateFrobeniusEquiv L p n is the same as the iterateFrobeniusEquiv M p n when restricted to K. But K is embedded into both L and M via i and j. However, since L and M are perfect closures of K, they are isomorphic over K, but the isomorphism is given by the equiv j i p.

Therefore, perhaps the iterateFrobeniusEquiv on L and M are compatible via this isomorphism. Specifically, the following diagram might commute:

L --(iterateFrobeniusEquiv L p n)--> L
| (equiv j i p)               | (equiv j i p)
V                              V
M --(iterateFrobeniusEquiv M p n)--> M

If this diagram commutes, then (equiv j i p) (iterateFrobeniusEquiv L p n).symm (i y) = (iterateFrobeniusEquiv M p n).symm (j y). But I'm not sure if this is true.

Alternatively, since the Frobenius map is natural, the equivalence should commute with the Frobenius. Therefore, (equiv j i p) composed with the Frobenius on L should equal the Frobenius on M composed with (equiv j i p). If that's the case, then the iterateFrobeniusEquiv would also commute with the equivalence.

Assuming this is true, then (equiv j i p) (iterateFrobeniusEquiv L p n).symm (i y) = (iterateFrobeniusEquiv M p n).symm (j y). But in our case, we have (equiv j i p) x = (iterateFrobeniusEquiv M p n).symm (i y) from `equiv_apply`, and we need to show that this equals (iterateFrobeniusEquiv L p n).symm (i y).

But unless (iterateFrobeniusEquiv M p n).symm (i y) equals (iterateFrobeniusEquiv L p n).symm (i y), which would require that i y is in K and the p^n-th root of i y is the same in both L and M. But since L and M are both perfect closures of K, the p^n-th root of i y in L and M should be compatible via the isomorphism.

But how do we formalize this? Maybe we need to use the fact that the equivalence equiv j i p sends i y to j y, and since j y = x ^ p ^ n, which is related to the iterateFrobeniusEquiv.

This is getting too abstract. Let's try to see what happens if we proceed with the initial approach of applying `rw [equiv_symm, equiv_apply]`. This would transform the left-hand side into (iterateFrobeniusEquiv M p n).symm (i y), and the right-hand side is (iterateFrobeniusEquiv L p n).symm (i y). So the goal would be to show that these two are equal.

But how can we show that? Unless there's a lemma that states that the iterateFrobeniusEquiv over different perfect closures are compatible via the equivalence.

Alternatively, maybe the key is that i y is in K, and the p^n-th root of i y is the same in both L and M, but since L and M are different perfect closures, this isn't necessarily true unless the equivalence is used to transport the root.

But this seems like a dead end. Maybe the problem requires a different approach.

Wait, let's look back at the theorem statement. The theorem is `IsPerfectClosure.equiv_symm_apply`, which is supposed to be the one we're proving. The current goal is the statement of this theorem.

The proof so far is empty, so we need to start from scratch. The user says that the premises used in the next tactic are `equiv_symm` and `equiv_apply`, so the solution must involve these two lemmas.

Given that, the correct approach must be to apply `rw [equiv_symm, equiv_apply]`, even if it seems like it leaves a remaining goal. But perhaps in the context of the theorem, these rewrites are sufficient.

Wait, let's try to see what the goal would look like after applying these two rewrites.

Original goal:

(RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)

After `rw [equiv_symm]`:

(equiv j i p) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)

After `rw [equiv_apply]` (using h : j y = x ^ p ^ n):

(iterateFrobeniusEquiv M p n).symm (i y) = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)

So the goal is now:

(iterateFrobeniusEquiv M p n).symm (i y) = (iterateFrobeniusEquiv L p n).symm (i y)

But this seems like it's not provable unless L and M are the same, which they aren't. Therefore, there must be a mistake in this approach.

But the user says that the premises used are `equiv_symm` and `equiv_apply`, so perhaps the correct answer is to apply these two lemmas, and the remaining goal is handled by some other means, possibly automatically.

Alternatively, maybe the iterateFrobeniusEquiv L p n is actually the same as iterateFrobeniusEquiv M p n when applied to i y. But i y is in L, and iterateFrobeniusEquiv L p n is an equivalence on L, while iterateFrobeniusEquiv M p n is an equivalence on M. So unless i y is in K and the p^n-th root is the same in both L and M, which would require that the embeddings i and j agree on the p^n-th roots, which they might not.

But given that L and M are both perfect closures of K, and i and j are embeddings of K into L and M, then for any y in K, the p^n-th root of i y in L and the p^n-th root of j y in M should be compatible via the isomorphism between L and M. But since j y = x ^ p ^ n, and x is in M, this might not directly help.

This is getting too complicated. Given the time constraints, I'll proceed with the initial answer of `rw [equiv_symm, equiv_apply]`, as that's what the premises suggest, and perhaps the remaining goal is handled by some automation or is a definitional equality.

Therefore, the final answer is:
```

**lean_error:** tail step 1/121 ('But wait, the goal is:'): <stdin>:1:1: unknown tactic

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=1569, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply]

simp [h]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 157.3s, verify 0.3s, in=1556, out=9330)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [equiv_symm]
apply equiv_apply
```

**final state (truncated):**
```
case h
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
...
```

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 0.8s, verify 0.2s, in=1556, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [equiv_symm, equiv_apply i j, h]
```

**final state (truncated):**
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
...
```
