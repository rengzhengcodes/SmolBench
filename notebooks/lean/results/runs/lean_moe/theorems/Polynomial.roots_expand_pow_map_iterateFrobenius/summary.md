# Polynomial.roots_expand_pow_map_iterateFrobenius   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [← coe_iterateFrobeniusEquiv, roots_expand_pow, Multiset.map_nsmul,
  Multiset.map_map, comp_apply, RingEquiv.apply_symm_apply, map_id']
```

**True premises at k:** `coe_iterateFrobeniusEquiv`, `Polynomial.roots_expand_pow`, `Multiset.map_nsmul`, `Multiset.map_map`, `Function.comp_apply`, `RingEquiv.apply_symm_apply`, `Multiset.map_id'`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | · | ✘ | · |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.4s, verify 0.1s, in=357, out=1109)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (roots_expand_eq_map_iterateFrobenius (R:=R) (p:=p) (n:=n) f)
```

**lean_error:** tail step 1/1 ('simpa using (roots_expand_eq_map_iterateFrobenius (R:=R) (p:=p) (n:=n) f)'): unknown identifier 'roots_expand_eq_map_iterateFrobenius'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 269.8s, verify 0.1s, in=307, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
We need to prove that mapping the iterateFrobenius over the roots of (expand R (p^n)) f yields p^n • roots f.

We have a comm ring R, domain, perfect ring of characteristic p, ExpChar R p (meaning that the Frobenius map is surjective? Actually ExpChar means that the exponential characteristic is p: i.e., p is the smallest positive integer such that p·1 = 0 in R? Wait: ExpChar R p is a class that says the characteristic of R is p? Actually Mathlib: ExpChar R p means that the exponential characteristic of R is p, i.e., p is the smallest positive integer such that p·1 = 0, and moreover R is a ℤ/pℤ-algebra? Not sure. But we also have PerfectRing R p, which means that the Frobenius map is bijective (i.e., R is perfect of characteristic p). So we have both ExpChar and PerfectRing.

We have f : R[X]. The polynomial (expand R (p^n)) f is the polynomial obtained by applying the ring homomorphism expand R (p^n) : R[X] → R[X] which sends X to X^{p^n}? Actually expand R n : R[X] → R[X] is the map sending a polynomial ∑ a_i X^i to ∑ a_i X^{i * n}. Wait: In Mathlib, expand R n f is defined as the polynomial obtained by replacing X by X^n in f. So expand R (p^n) f is f(X^{p^n}). So roots of f(X^{p^n}) are those elements a such that f(a^{p^n}) = 0. So if b is a root of f, then any a such that a^{p^n} = b is a root of f(X^{p^n}). In a perfect ring of characteristic p, the Frobenius map x ↦ x^p is bijective, so x ↦ x^{p^n} is also bijective (since it's the n-th iterate of Frobenius). Therefore, for each root b of f, there is exactly one a such that a^{p^n} = b (since Frobenius^n is bijective). Actually, the map is bijective, so for each b there exists a unique a with a^{p^n} = b. Therefore, the roots of f(X^{p^n}) are in bijection with the roots of f, via the Frobenius^n map. Moreover, the multiplicity should be preserved? Since the map is bijective on the ring, and we're dealing with polynomials over a domain, I think the multiplicity of each root a of f(X^{p^n}) is the same as the multiplicity of b = a^{p^n} as a root of f. Because if we factor f(Y) = ∏ (Y - b_i)^{m_i}, then f(X^{p^n}) = ∏ (X^{p^n} - b_i)^{m_i} = ∏ ( (X - a_i)^{p^n} )^{m_i}? Wait, no: In characteristic p, (X^{p^n} - b_i) = (X - a_i)^{p^n} if a_i^{p^n} = b_i, because (X - a)^{p^n} = X^{p^n} - a^{p^n} in characteristic p (since the binomial coefficients C(p^n, k) are divisible by p for 0 < k < p^n). So indeed, X^{p^n} - b_i = (X - a_i)^{p^n}. Therefore, f(X^{p^n}) = ∏ (X - a_i)^{p^n * m_i}. So each root a_i of f(X^{p^n}) has multiplicity p^n * m_i, where m_i is the multiplicity of b_i = a_i^{p^n} as a root of f. Therefore, the multiset of roots of f(X^{p^n}) is obtained by taking each root b of f with multiplicity m, and replacing it by p^n copies of each a such that a^{p^n} = b. But since the Frobenius^n map is bijective, there is exactly one a for each b. So we get that the multiset of roots of f(X^{p^n}) is the multiset where each root b of f is replaced by p^n copies of the unique a with a^{p^n} = b. Then mapping the Frobenius^n map over these roots sends each a to a^{p^n} = b, and since there are p^n copies of a, we get p^n copies of b. Hence, the multiset map yields p^n • roots f.

Thus the statement is correct.

Now we need to prove this in Lean. We have:

- iterateFrobenius R p n : R →+* R is the ring homomorphism that is the n-th iterate of Frobenius: x ↦ x^{p^n}. Actually, iterateFrobenius R p n is defined as the ring homomorphism obtained by applying Frobenius n times. Since Frobenius is x ↦ x^p, iterate n times gives x ↦ x^{p^n}. The coercion ⇑(iterateFrobenius R p n) is the function x ↦ x^{p^n}.

- roots ((expand R (p ^ n)) f) is the multiset of roots of f(X^{p^n}) in R.

- p ^ n • roots f is the multiset obtained by taking each root of f and repeating it p^n times.

We need to show that mapping x ↦ x^{p^n} over the roots of f(X^{p^n}) gives p^n • roots f.

We can use the fact that in a perfect ring, the Frobenius map is bijective, so we can relate the roots.

Alternatively, we can use the factorization approach: since R is a domain, we can factor f as ∏ (X - c_i)^{m_i} (up to a unit). Then f(X^{p^n}) = ∏ (X^{p^n} - c_i)^{m_i} = ∏ (X - a_i)^{p^n * m_i} where a_i^{p^n} = c_i. Then the roots of f(X^{p^n}) are the a_i each with multiplicity p^n * m_i. Then mapping x ↦ x^{p^n} sends each a_i to c_i, and the multiplicity becomes p^n * m_i, so the multiset map gives ∑ (p^n * m_i) • [c_i] = p^n • (∑ m_i • [c_i]) = p^n • roots f.

But we need to formalize this in Lean. We have the polynomial f : R[X]. We can get its factorization as a product of linear factors (since R is a domain? Not necessarily algebraically closed). Wait, roots are in R, but f may not split over R. However, the statement is about the multiset of roots in R. So we cannot assume f splits into linear factors over R. However, the identity we want is about the multisets of roots in R. So we need to work directly with the roots.

We can use the fact that the map x ↦ x^{p^n} is bijective on R (since R is perfect of characteristic p). Therefore, it induces a bijection between the set of roots of f(X^{p^n}) and the set of roots of f. Moreover, it preserves multiplicities multiplied by p^n? Actually, we need to check multiplicities.

Let’s denote F = iterateFrobenius R p n : R →+* R, which is bijective. Then we have that for any a : R, F(a) = a^{p^n}. The polynomial (expand R (p^n)) f is f ∘ (X ↦ X^{p^n}) as a polynomial map? Actually, expand R n f is the polynomial obtained by substituting X^n for X in f. So (expand R (p^n)) f (a) = f(a^{p^n}). So a is a root of (expand R (p^n)) f iff F(a) is a root of f.

Thus, the preimage of the set of roots of f under F is exactly the set of roots of (expand R (p^n)) f. Since F is bijective, this preimage is in bijection with the set of roots of f, and the multiplicity of each a in the preimage should be p^n times the multiplicity of F(a) in f? Wait, we need to check multiplicities.

Consider the polynomial g = f ∘ (X ↦ X^{p^n}) in R[X]. If f(Y) = ∏ (Y - b_i)^{m_i} * u (where u is a unit), then g(X) = ∏ (X^{p^n} - b_i)^{m_i} * u. In characteristic p, X^{p^n} - b_i = (X - a_i)^{p^n} where a_i^{p^n} = b_i (since Frobenius is bijective, such a_i exists and is unique). Therefore, g(X) = ∏ (X - a_i)^{p^n * m_i} * u. So the multiplicity of a_i as a root of g is p^n * m_i. Since F is bijective, the a_i are in bijection with the b_i. Therefore, the multiset of roots of g is obtained by taking each root b of f with multiplicity m, and replacing it by p^n copies of the unique a such that F(a) = b.

Thus, mapping F over the roots of g gives, for each a, F(a) = b, and the multiplicity of a in the roots of g is p^n * m, so the image multiset has multiplicity p^n * m for each b. Hence, the image is p^n • (multiset of roots of f).

To formalize this, we need to work with the factorization of f. However, f may not factor into linear factors over R. But we can still work with the formal factorization in the polynomial ring, using the fact that R is a domain and we can consider the splitting field? Not needed.

Alternatively, we can use the fact that the map F is bijective and that the multiplicity of a root a of g is equal to p^n times the multiplicity of F(a) as a root of f. This can be shown by considering the derivative or using the Taylor expansion? Hmm.

Another approach: Since F is bijective, we can transfer the polynomial f along F to get a polynomial whose roots are the preimages. Specifically, consider the ring homomorphism F : R → R. It induces a map on polynomials F_* : R[X] → R[X] sending ∑ a_i X^i to ∑ F(a_i) X^i. But we have the opposite: we have g = f ∘ (X ↦ X^{p^n}) = f ∘ (X ↦ F(X))? Actually, F(X) = X^{p^n}, so g = f ∘ F as a polynomial map? Wait, if we consider the polynomial variable X, then substituting F(X) into f gives f(F(X)) = f(X^{p^n}) = g(X). So g = f ∘ F, where F is considered as an endomorphism of the polynomial ring R[X] sending X to X^{p^n} and acting as the identity on coefficients? Actually, F is a ring endomorphism of R, but we need an endomorphism of R[X]. The map that sends X to X^{p^n} and acts as the identity on R is not a ring homomorphism unless p^n = 1? No, it is a ring homomorphism because it's just substituting X^{p^n} for X, which is always a ring homomorphism (evaluation map). So we have a ring homomorphism φ : R[X] → R[X] sending X to X^{p^n} and fixing R. Then g = φ(f). On the other hand, F : R → R is the Frobenius iterate. There is a relation: for any polynomial h, φ(h) = h ∘ (X ↦ X^{p^n}) = (F_* h) ??? Not exactly.

Actually, if we consider the map F : R → R, then we can extend it to a map F[X] : R[X] → R[X] by applying F to coefficients. That is, F[X](∑ a_i X^i) = ∑ F(a_i) X^i. This is a ring homomorphism. On the other hand, φ is the map sending X to X^{p^n} and fixing coefficients. These two maps commute? Let's see: φ(F[X](h)) = φ(∑ F(a_i) X^i) = ∑ F(a_i) X^{i p^n} = F[X](∑ a_i X^{i p^n}) = F[X](φ(h)). So they commute.

Now, note that g = φ(f). We want to relate the roots of g to the roots of f via F. For any a : R, g(a) = f(a^{p^n}) = f(F(a)). So a is a root of g iff F(a) is a root of f. So the roots of g are the preimages of the roots of f under F.

Now, to get the multiplicities, we can use the fact that F is bijective and that the derivative of g at a is related to the derivative of f at F(a) times something? Actually, in characteristic p, the derivative of X^{p^n} is zero, so the usual multiplicity formula doesn't work directly. But we can use the factorization as before.

Since R is a perfect ring, we can use the fact that the Frobenius map is an automorphism. Then, we can consider the polynomial f and its image under the inverse of F on coefficients? Hmm.

Alternatively, we can use the fact that the map F induces an isomorphism of the residue fields? Not sure.

Given that we have PerfectRing R p, we know that the Frobenius map is bijective. We can use this to show that the map a ↦ a^{p^n} is bijective. Then, we can use the fact that the multiplicity of a root a of g is equal to p^n times the multiplicity of F(a) as a root of f. This can be shown by considering the polynomial g(Y) = f(Y^{p^n}) and making a change of variable Y = F^{-1}(X), but since F is bijective, we can substitute.

Let’s try to make this precise: Since F is bijective, let F^{-1} be its inverse (as a function). Then, for any polynomial h, we have h(X) = h(F(F^{-1}(X))) = (h ∘ F)(F^{-1}(X)). So, if we set h = f, then f(X) = (f ∘ F)(F^{-1}(X)) = g(F^{-1}(X)). Therefore, f(X) = g(F^{-1}(X)). This means that f and g are related by the change of variable X = F^{-1}(Y) or Y = F(X). So, the roots of f are the images under F of the roots of g. Moreover, since F^{-1} is a polynomial function? Not necessarily, but as a function on R it is bijective.

Now, to relate multiplicities, we can use the fact that if we have a bijective function φ : R → R, then the multiplicity of a root r of a polynomial h is equal to the multiplicity of φ(r) as a root of h ∘ φ^{-1}? Let's see: Suppose h is a polynomial, and φ is a bijective function on R. Then, h(φ^{-1}(X)) is a polynomial? Not necessarily, unless φ^{-1} is a polynomial function. In our case, φ = F is a polynomial function (since F(x) = x^{p^n}), and its inverse is also a polynomial function because R is perfect? Actually, in a perfect ring of characteristic p, the Frobenius map is an automorphism, but its inverse is not necessarily given by a polynomial. However, since we are working with the polynomial ring, we can still consider the composition.

But we have f(X) = g(F^{-1}(X)) as an equality of functions from R to R. However, g(F^{-1}(X)) is not necessarily a polynomial in X, because F^{-1} is not a polynomial function. So we cannot directly say that f is equal to some polynomial composition.

Thus, the previous approach may not work directly.

Alternative approach: Use the fact that in a perfect ring, the polynomial X^{p^n} - c splits as ∏_{i=0}^{p^n - 1} (X - ζ^i a) where ζ is a primitive p^n-th root of unity? No, that's in characteristic 0. In characteristic p, X^{p^n} - c = (X - a)^{p^n} if a^{p^n} = c, as we used before. This is because in characteristic p, (X - a)^{p^n} = X^{p^n} - a^{p^n} (since the binomial coefficients C(p^n, k) are divisible by p for 0 < k < p^n). So we don't need any roots of unity.

Thus, if we can factor f as ∏ (X - b_i)^{m_i} * u in the polynomial ring over the algebraic closure, then we can deduce the factorization of g. But we don't have the algebraic closure in Lean.

However, we can work formally: Since R is a domain, we can consider the polynomial f in R[X]. The statement about roots and multiplicities can be derived from the fact that the map F is bijective and that the polynomial g(X) = f(X^{p^n}) satisfies that for any a, the multiplicity of a as a root of g is p^n times the multiplicity of F(a) as a root of f. This can be shown by considering the Taylor expansion of f around F(a) and using that the derivative of X^{p^n} vanishes except for the p^n-th term? Actually, in characteristic p, the usual Taylor expansion involves derivatives, but since the derivative of X^{p^n} is zero, we need to use higher derivations.

Alternatively, we can use the fact that in a perfect ring, the map F is an automorphism, and we can consider the polynomial f' = F^{-1}[f] obtained by applying F^{-1} to the coefficients of f. Then, we have that g = φ(f) = φ(F[F^{-1}[f]]) = F[φ(F^{-1}[f])] because φ and F commute? Wait, let's see:

Let F[X] be the map on polynomials induced by F on coefficients. Then, F[X] is an automorphism of R[X] because F is an automorphism of R. We have that φ commutes with F[X], as shown earlier. Now, note that g = φ(f). Then, F[X]^{-1}(g) = F[X]^{-1}(φ(f)) = φ(F[X]^{-1}(f)) because F[X] and φ commute. Let h = F[X]^{-1}(f). Then, g = F[X](φ(h)). But F[X](φ(h)) is the polynomial obtained by applying F to the coefficients of φ(h). However, φ(h) is h(X^{p^n}). So, F[X](φ(h)) is the polynomial where we take h(X^{p^n}) and apply F to each coefficient. But since F is a ring automorphism, this is the same as (F[X] h)(X^{p^n})? Actually, F[X] (φ(h)) = F[X] (h ∘ φ_X) where φ_X is the map sending X to X^{p^n}. Since F[X] commutes with φ_X, we have F[X] (h ∘ φ_X) = (F[X] h) ∘ φ_X. Therefore, g = (F[X] h) ∘ φ_X. But F[X] h = f, because h = F[X]^{-1}(f). So g = f ∘ φ_X, which is just the definition of g. So this is circular.

Hmm.

Perhaps we can use the fact that the map F is bijective to transfer the multiset statement directly. Since F is bijective, the multiset of roots of g is the preimage of the multiset of roots of f under F. Then, mapping F over this preimage gives back the multiset of roots of f, but with each element counted as many times as its preimage size. Since F is bijective, each element has exactly one preimage, so we would get the same multiset. But this would give that the map F over roots of g gives roots f, not p^n • roots f. So we are missing the multiplicity factor.

Thus, the key is that the multiplicity is multiplied by p^n. So we need to show that if b is a root of f with multiplicity m, then each a in F^{-1}({b}) is a root of g with multiplicity p^n * m. Since F is bijective, F^{-1}({b}) is a singleton, so we get that the multiplicity of a in g is p^n * m, and thus the image multiset has multiplicity p^n * m for b.

Therefore, we need to prove that mult_a(g) = p^n * mult_{F(a)}(f) for any a : R.

How to prove this? Let's try to use the factorization in the polynomial ring. Since R is a domain, we can consider the polynomial f in R[X]. Let b = F(a). We want to show that the multiplicity of a as a root of g = f ∘ (X ↦ X^{p^n}) is p^n times the multiplicity of b as a root of f.

We can write f(X) = (X - b)^m * h(X) where h(b) ≠ 0. Then, g(X) = f(X^{p^n}) = (X^{p^n} - b)^m * h(X^{p^n}). Now, in characteristic p, X^{p^n} - b = (X - a)^{p^n} because a^{p^n} = b and the Frobenius map is bijective (so a is unique). Therefore, g(X) = ((X - a)^{p^n})^m * h(X^{p^n}) = (X - a)^{p^n * m} * h(X^{p^n}). Now, we need to check that h(X^{p^n}) does not vanish at X = a, i.e., h(a^{p^n}) = h(b) ≠ 0. Since h(b) ≠ 0, we have that a is not a root of h(X^{p^n}). Therefore, the multiplicity of a as a root of g is exactly p^n * m.

This proof works if we can factor f as (X - b)^m * h(X) with h(b) ≠ 0. This is possible in any commutative ring: we can perform polynomial division by (X - b) repeatedly until the remainder is non-zero when evaluated at b. Since R is a domain, we can do this and get that f(X) = (X - b)^m * h(X) + r where r is a constant (since dividing by a linear polynomial gives a remainder of degree < 1, i.e., constant). Then, evaluating at b gives f(b) = r, so if b is a root, r = 0. We can repeat to get the maximal m such that (X - b)^m divides f. Then, the quotient h(X) satisfies h(b) ≠ 0. This is the standard way to define multiplicity in any commutative ring.

Thus, we can formalize this proof in Lean.

Steps:

1. For any a : R, let b = F(a) = a^{p^n}.
2. Write f(X) = (X - b)^m * h(X) + r where r is a constant (in R) and deg(h) < something? Actually, we can use the fact that we can compute the multiplicity m as the largest natural number such that (X - b)^m divides f in R[X]. Then, we get f = (X - b)^m * h where h(b) ≠ 0.
3. Then, g(X) = f(X^{p^n}) = (X^{p^n} - b)^m * h(X^{p^n}).
4. Show that X^{p^n} - b = (X - a)^{p^n} in R[X] because a^{p^n} = b and the binomial theorem in characteristic p.
5. Thus, g(X) = ((X - a)^{p^n})^m * h(X^{p^n}) = (X - a)^{p^n * m} * h(X^{p^n}).
6. Evaluate h(X^{p^n}) at X = a: h(a^{p^n}) = h(b) ≠ 0, so (X - a) does not divide h(X^{p^n}).
7. Therefore, the multiplicity of a as a root of g is exactly p^n * m.

We need to formalize the multiplicity in Lean. Mathlib has the notion of multiplicity of a root of a polynomial: Polynomial.orderOfRoot p a is the largest n such that (X - a)^n divides p. So we can use that.

Thus, we need to show that Polynomial.orderOfRoot (map (iterateFrobenius R p n) (roots ((expand R (p ^ n)) f))) ??? Wait, no. We need to show that the multiset map gives p^n • roots f. To do this, we can show that for each b : R, the multiplicity of b in the LHS multiset is equal to the multiplicity of b in p^n • roots f.

The multiplicity of b in p^n • roots f is p^n * (multiplicity of b in roots f).

The multiplicity of b in the LHS multiset is the sum over a : R such that F(a) = b of (multiplicity of a in roots of g) * (number of times a appears in the multiset map? Actually, the multiset map takes each element a in the multiset S and maps it to F(a), and the resulting multiset has, for each b, the sum of the multiplicities of all a such that F(a) = b in S.

Thus, multiplicity of b in map F S = ∑_{a : F(a) = b} multiplicity of a in S.

Here, S = roots of g. So we need to show that for each b, ∑_{a : F(a) = b} Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f b.

Since F is bijective, there is exactly one a such that F(a) = b (because F is injective and surjective). Let's denote a = F^{-1}(b). Then, the sum reduces to Polynomial.orderOfRoot g (F^{-1}(b)). So we need to show that Polynomial.orderOfRoot g (F^{-1}(b)) = p^n * Polynomial.orderOfRoot f b.

But we can also directly use a as the variable: for any a, Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f (F(a)). Then, summing over a with F(a) = b gives the same.

Thus, we need to prove the key lemma: ∀ (a : R), Polynomial.orderOfRoot (map (expand R (p ^ n)) f) a = p^n * Polynomial.orderOfRoot f (a ^ (p ^ n)).

Wait, careful: g = expand R (p^n) f, which is f(X^{p^n}). So g(a) = f(a^{p^n}). The orderOfRoot g a is the largest k such that (X - a)^k divides g in R[X].

We claim that this equals p^n * orderOfRoot f (a^{p^n}).

Let m = orderOfRoot f (a^{p^n}). Then, f(X) = (X - a^{p^n})^m * h(X) where h(a^{p^n}) ≠ 0. Then, g(X) = f(X^{p^n}) = (X^{p^n} - a^{p^n})^m * h(X^{p^n}) = (X - a)^{p^n * m} * h(X^{p^n}) because X^{p^n} - a^{p^n} = (X - a)^{p^n} in characteristic p (since (X - a)^{p^n} = X^{p^n} - a^{p^n} as the middle terms vanish). Then, since h(a^{p^n}) ≠ 0, we have h(X^{p^n}) evaluated at X = a is h(a^{p^n}) ≠ 0, so (X - a) does not divide h(X^{p^n}). Therefore, the orderOfRoot g a is exactly p^n * m.

Thus, the lemma holds.

Now, we can use this lemma to compute the multiplicity of each b in the LHS and RHS multisets.

In Lean, we have:

- roots : Polynomial R → Multiset R
- map : (R → R) → Multiset R → Multiset R
- • : ℕ → Multiset R → Multiset R (scalar multiplication, i.e., repeat each element n times)

We need to show that map (⇑(iterateFrobenius R p n)) (roots (expand R (p ^ n) f)) = p^n • roots f.

We can use the fact that two multisets are equal if they have the same multiplicity for each element. So we can use the lemma that for any b : R, the multiplicity of b in the LHS equals the multiplicity of b in the RHS.

Multiplicity of b in LHS: (map F (roots g)) b = ∑_{a in roots g} [F a = b] * (multiplicity of a in roots g). Actually, the multiplicity of b in map F s is the sum over a : R of (if F a = b then multiplicity of a in s else 0). Since F is a function, we can write it as ∑_{a : F a = b} multiplicity of a in s.

Multiplicity of b in RHS: (p^n • roots f) b = p^n * (multiplicity of b in roots f).

Thus, we need to show that ∑_{a : F a = b} Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f b.

Since F is bijective, there is exactly one a such that F a = b, namely a = F^{-1}(b). So the sum reduces to Polynomial.orderOfRoot g (F^{-1}(b)). Therefore, we need to show that Polynomial.orderOfRoot g (F^{-1}(b)) = p^n * Polynomial.orderOfRoot f b.

But we can also use the lemma with a = F^{-1}(b): Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f (F a) = p^n * Polynomial.orderOfRoot f b.

Thus, the lemma directly gives us the required equality.

Therefore, the proof can proceed by:

1. Proving the key lemma: ∀ a : R, Polynomial.orderOfRoot (expand R (p ^ n) f) a = p^n * Polynomial.orderOfRoot f (a ^ (p ^ n)).
   - Note: iterateFrobenius R p n a = a ^ (p ^ n) because iterateFrobenius is defined as the n-th iterate of Frobenius, which is x ↦ x^{p^n}.
   - We need to confirm that in Lean, iterateFrobenius R p n a = a ^ (p ^ n). Let's check: iterateFrobenius R p n is defined as the n-th power of the Frobenius endomorphism. The Frobenius endomorphism is x ↦ x^p. So iterating it n times gives x ↦ x^{p^n}. Yes, so ⇑(iterateFrobenius R p n) a = a ^ (p ^ n).

2. Then, for any b : R, compute the multiplicity of b in the LHS:
   - multiplicity of b in map F (roots g) = ∑_{a : F a = b} Polynomial.orderOfRoot g a.
   - Since F is bijective, there is exactly one a with F a = b, namely a such that a ^ (p ^ n) = b (because F a = a ^ (p ^ n)).
   - So the sum is Polynomial.orderOfRoot g a where a ^ (p ^ n) = b.
   - By the key lemma, this equals p^n * Polynomial.orderOfRoot f (a ^ (p ^ n)) = p^n * Polynomial.orderOfRoot f b.

3. The multiplicity of b in the RHS is p^n * Polynomial.orderOfRoot f b.

4. Therefore, the multiplicities are equal for all b, so the multisets are equal.

Now, we need to formalize this in Lean. We'll need to use the fact that F is bijective to say that the fiber F^{-1}({b}) is a singleton. However, we can avoid using bijectivity directly by using the lemma that for any a, the orderOfRoot g a = p^n * orderOfRoot f (F a). Then, we can compute the sum over a : F a = b of orderOfRoot g a as follows:

∑_{a : F a = b} orderOfRoot g a = ∑_{a : F a = b} (p^n * orderOfRoot f (F a)) = p^n * ∑_{a : F a = b} orderOfRoot f (F a).

But since F a = b for all a in the sum, orderOfRoot f (F a) = orderOfRoot f b. So the sum becomes p^n * (∑_{a : F a = b} 1) * orderOfRoot f b? Wait, no: ∑_{a : F a = b} orderOfRoot f (F a) = ∑_{a : F a = b} orderOfRoot f b = (∑_{a : F a = b} 1) * orderOfRoot f b.

But ∑_{a : F a = b} 1 is the cardinality of the fiber F^{-1}({b}). Since F is bijective, this cardinality is 1. So we get p^n * 1 * orderOfRoot f b = p^n * orderOfRoot f b.

However, to avoid using the bijectivity of F in the sum, we can instead note that the map a ↦ F a is a bijection, so we can change the sum over a : F a = b to a sum over a' : R where we set a' = F a, but this seems complicated.

Alternatively, we can directly use the fact that F is bijective to get that the fiber is a singleton, and then use the lemma.

In Lean, we have the fact that iterateFrobenius R p n is bijective because R is perfect. Specifically, PerfectRing R p implies that the Frobenius map is bijective, and hence its iterates are bijective.

We can get that iterateFrobenius R p n is bijective from PerfectRing R p. Let's check: PerfectRing R p states that the Frobenius endomorphism is bijective. Then, the n-th iterate of a bijective function is bijective. So we can obtain a Bijective instance for iterateFrobenius R p n.

Thus, we can use the fact that F is bijective to say that the fiber F^{-1}({b}) is a singleton.

Now, let's outline the proof steps in Lean:

1. Let F : R →+* R be iterateFrobenius R p n. Let g : Polynomial R be expand R (p ^ n) f.
2. Prove that for any a : R, Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f (F a).
   - To do this, we need to show that (X - a)^(p^n) = X^(p^n) - a^(p^n) in R[X].
   - Then, use the factorization of f around F a.
3. Use the bijectivity of F to show that for any b : R, the sum over a : F a = b of Polynomial.orderOfRoot g a equals p^n * Polynomial.orderOfRoot f b.
4. Conclude that the multisets are equal by showing that their multiplicities are equal for all b.

In Lean, we can use the lemma `Multiset.eq_of_forall_count_eq` to show that two multisets are equal if their counts are equal for all elements.

Thus, we need to show that for any b : R, (map F (roots g)).count b = (p^n • roots f).count b.

We have:
- (map F (roots g)).count b = ∑ a in roots g, if F a = b then 1 else 0, multiplied by the multiplicity? Actually, the count of b in map F s is the sum over a in s of if F a = b then 1 else 0, but weighted by the multiplicity of a in s. More precisely, if s is a multiset, then (map F s).count b = ∑ a in s, (if F a = b then 1 else 0) * s.count a. But since s.count a is the multiplicity of a in s, we can write it as ∑ a, s.count a * (if F a = b then 1 else 0). This is equal to ∑ a : F a = b, s.count a.

Thus, (map F (roots g)).count b = ∑ a : F a = b, (roots g).count a = ∑ a : F a = b, Polynomial.orderOfRoot g a.

Similarly, (p^n • roots f).count b = p^n * (roots f).count b = p^n * Polynomial.orderOfRoot f b.

Therefore, we need to show that ∑ a : F a = b, Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f b.

Now, using the lemma Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f (F a), we can rewrite the LHS as ∑ a : F a = b, p^n * Polynomial.orderOfRoot f (F a) = p^n * ∑ a : F a = b, Polynomial.orderOfRoot f (F a).

Since F a = b for all a in the sum, this is p^n * ∑ a : F a = b, Polynomial.orderOfRoot f b = p^n * (∑ a : F a = b, 1) * Polynomial.orderOfRoot f b.

Now, we need to show that ∑ a : F a = b, 1 = 1, i.e., the fiber has exactly one element. This follows from the bijectivity of F.

Thus, we need to use that F is bijective to get that the fiber F^{-1}({b}) is a singleton.

In Lean, we can get the bijectivity of F from PerfectRing R p. Let's see: PerfectRing R p gives that the Frobenius map is bijective. The n-th iterate of a bijective function is bijective. We can get a Bijective instance for iterateFrobenius R p n by using the fact that the composition of bijective functions is bijective, and iterating n times.

Alternatively, we can use that PerfectRing R p implies that the Frobenius map is an equivalence, and hence its powers are equivalences.

In Mathlib, there is a lemma: `IsUnit.frobenius_map` or something? Actually, for a perfect ring, the Frobenius map is surjective and injective. We can find that `PerfectRing.frobenius_injective` and `PerfectRing.frobenius_surjective` exist. Then, we can get that the n-th iterate is bijective by composing these properties n times.

But perhaps there is a direct lemma: `iterateFrobenius_bijective`? Let's check.

Alternatively, we can avoid using bijectivity by noting that the map a ↦ F a is injective and surjective because R is perfect. We can get injectivity from the fact that if F a = F b, then a^{p^n} = b^{p^n}, and since the Frobenius map is injective (as R is reduced? Actually, in a domain of characteristic p, the Frobenius map is injective because it's a ring homomorphism and the kernel is an ideal; if x^{p^n} = 0 then x = 0 because R is a domain? Wait, in a domain of characteristic p, if x^{p^n} = 0 then x = 0 because the domain has no zero divisors. So the Frobenius map is injective. For surjectivity, we need that every element has a p^n-th root, which is true in a perfect ring. So we can get that F is bijective by combining injectivity (from being a domain) and surjectivity (from PerfectRing R p). However, we already have Inst✝ : PerfectRing R p, which gives surjectivity of Frobenius, and Inst✝² : IsDomain R gives injectivity of Frobenius (since if x^p = 0 then x = 0 in a domain). Then, the n-th iterate will also be injective and surjective.

But perhaps it's easier to use that PerfectRing R p implies that the Frobenius map is bijective, and then use that the n-th iterate of a bijective function is bijective.

In Lean, we can get a Bijective instance for iterateFrobenius R p n by using `Bijective.iterate` or something similar. Let's see: there is a lemma `Function.Bijective.iterate` that says if f is bijective, then f^[n] is bijective. Here, iterateFrobenius R p n is the n-th iterate of the Frobenius map. So we can get that the Frobenius map is bijective from PerfectRing R p, and then apply `Function.Bijective.iterate`.

Thus, we can obtain that F is bijective.

Now, let's try to sketch the proof in Lean:

1. Define F : R →+* R := iterateFrobenius R p n.
2. Define g : Polynomial R := expand R (p ^ n) f.
3. Prove key lemma: ∀ a : R, Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f (F a).
   - Steps:
     a. Show that (X - a : Polynomial R) ^ (p ^ n) = (X : Polynomial R) ^ (p ^ n) - (a : Polynomial R) ^ (p ^ n).
        - This follows from the binomial theorem and the fact that the binomial coefficients C(p^n, k) are divisible by p for 0 < k < p^n, hence zero in R because R has characteristic p.
        - In Lean, we can use `polynomial.C a ^ (p^n) = polynomial.C (a ^ (p^n))` and the binomial expansion.
        - Alternatively, we can use the fact that in a commutative ring of characteristic p, (X + Y)^(p^n) = X^(p^n) + Y^(p^n). Here, we have (X - a)^(p^n) = (X + (-a))^(p^n) = X^(p^n) + (-a)^(p^n) = X^(p^n) - a^(p^n) because p^n is odd? Wait, no: (-a)^(p^n) = - (a^(p^n)) if p^n is odd, but if p=2, then (-a)^(p^n) = a^(p^n) because -1 = 1 in characteristic 2? Actually, in characteristic 2, -a = a, so (-a)^(p^n) = a^(p^n). But we need (X - a)^(p^n) = X^(p^n) - a^(p^n). Let's check:
          - In characteristic p, (X - a)^p = X^p - a^p because the cross terms have coefficients divisible by p.
          - By induction, (X - a)^(p^n) = X^(p^n) - a^(p^n).
          - This holds regardless of whether p is 2 or not, because the binomial coefficients C(p^n, k) for 0 < k < p^n are divisible by p.
          - The sign: (X - a)^(p^n) = ∑_{k=0}^{p^n} C(p^n, k) X^k (-a)^(p^n - k).
          - For 0 < k < p^n, C(p^n, k) is divisible by p, so the term is zero in R.
          - The remaining terms are k=0: C(p^n, 0) X^0 (-a)^(p^n) = (-a)^(p^n) and k=p^n: C(p^n, p^n) X^p^n (-a)^0 = X^p^n.
          - Now, (-a)^(p^n) = (-1)^(p^n) a^(p^n). Since p is prime, if p is odd, then p^n is odd, so (-1)^(p^n) = -1. If p=2, then (-1)^(p^n) = 1 because -1 = 1 in characteristic 2? Wait, no: in any ring of characteristic 2, -1 = 1 because 1 + 1 = 0 implies -1 = 1. So (-1)^(p^n) = 1^(p^n) = 1. But we need (-a)^(p^n) = -a^(p^n) only when p is odd. However, in characteristic 2, we have -a = a, so (-a)^(p^n) = a^(p^n), and we also have -a^(p^n) = a^(p^n) because -1 = 1. So in characteristic 2, (-a)^(p^n) = a^(p^n) = -a^(p^n). Therefore, in both cases, (-a)^(p^n) = -a^(p^n) holds because in characteristic 2, -a^(p^n) = a^(p^n). So we can write (-a)^(p^n) = -a^(p^n) in any commutative ring of characteristic p.
          - Proof: In characteristic p, p·1 = 0. If p is odd, then (-1)^(p^n) = -1 because p^n is odd. If p=2, then -1 = 1, so (-1)^(p^n) = 1 = -1 because -1 = 1. Thus, in both cases, (-1)^(p^n) = -1. Therefore, (-a)^(p^n) = (-1)^(p^n) a^(p^n) = -a^(p^n).
        - Therefore, (X - a)^(p^n) = X^(p^n) - a^(p^n).
     b. Now, let b = F a = a^(p^n). We have g(X) = f(X^(p^n)).
     - Write f(Y) = (Y - b)^m * h(Y) where m = Polynomial.orderOfRoot f b and h(b) ≠ 0.
     - Then, g(X) = f(X^(p^n)) = (X^(p^n) - b)^m * h(X^(p^n)) = (X - a)^(p^n * m) * h(X^(p^n)).
     - Since h(b) ≠ 0, we have h(X^(p^n)) evaluated at X = a is h(a^(p^n)) = h(b) ≠ 0, so (X - a) does not divide h(X^(p^n)).
     - Therefore, Polynomial.orderOfRoot g a = p^n * m = p^n * Polynomial.orderOfRoot f b.
   - To formalize this in Lean, we can use the fact that if we have a polynomial f and we know that f = (X - b)^m * h with h(b) ≠ 0, then we can substitute X^(p^n) and use the above identity.
   - However, we don't have the factorization of f directly. Instead, we can use the property of orderOfRoot: Polynomial.orderOfRoot f b is the largest m such that (X - b)^m divides f.
   - We can use the lemma that if (X - b)^m divides f, then (X - a)^(p^n * m) divides g, and if (X - b)^(m+1) does not divide f, then (X - a)^(p^n * (m+1)) does not divide g.
   - Alternatively, we can use the fact that the orderOfRoot of a composition can be computed using the orderOfRoot of the inner function and the outer function, but this requires that the inner function is a polynomial and we know its derivative or something. However, in our case, the inner function is X^(p^n), which is not invertible as a polynomial, but we have the special property that its derivative is zero except in characteristic p.
   - Perhaps a better way is to use the fact that in Lean, we can compute the orderOfRoot of g at a by evaluating the polynomial and its derivatives, but since derivatives vanish, we need to use the Hasse derivative or something. However, we can avoid this by using the factorization approach with the fact that we can take the polynomial f and write it as (X - b)^m * h where h(b) ≠ 0, and then substitute.

   - To get h, we can use polynomial division: since (X - b)^m divides f, we can write f = (X - b)^m * h. Then, we need to show that h(b) ≠ 0. This is true by maximality of m: if h(b) = 0, then (X - b) divides h, so (X - b)^(m+1) divides f, contradicting the maximality of m.

   - In Lean, we can obtain h and the fact that h(b) ≠ 0 from the orderOfRoot. Specifically, there is a lemma: `Polynomial.eq_C_mul_pow_X_sub_C_of_orderOfRoot_eq` or something similar? Let's check.

   - Actually, we can use `Polynomial.orderOfRoot_dvd_iff` to say that (X - b)^m divides f iff m ≤ orderOfRoot f b. Then, we can take m = orderOfRoot f b, so (X - b)^m divides f, and (X - b)^(m+1) does not divide f.

   - We can then get h such that f = (X - b)^m * h by using the fact that if a polynomial divides another, we can get the quotient. Specifically, since (X - b)^m divides f, there exists h such that f = (X - b)^m * h.

   - Then, we need to show that h(b) ≠ 0. Suppose h(b) = 0. Then, (X - b) divides h, so h = (X - b) * h', and thus f = (X - b)^(m+1) * h', so (X - b)^(m+1) divides f, contradicting that m = orderOfRoot f b is the largest such that (X - b)^m divides f.

   - Therefore, h(b) ≠ 0.

   - Now, substitute X^(p^n) into f: g = f ∘ (X ↦ X^(p^n)) = ((X^(p^n) - b)^m) * (h ∘ (X ↦ X^(p^n))).

   - We have (X^(p^n) - b) = (X - a)^(p^n) as shown.

   - Thus, g = ((X - a)^(p^n))^m * (h ∘ (X ↦ X^(p^n))) = (X - a)^(p^n * m) * (h ∘ (X ↦ X^(p^n))).

   - Now, we need to show that (X - a) does not divide (h ∘ (X ↦ X^(p^n))). This is equivalent to showing that (h ∘ (X ↦ X^(p^n)))(a) ≠ 0, i.e., h(a^(p^n)) ≠ 0, i.e., h(b) ≠ 0, which we have.

   - Therefore, the orderOfRoot of g at a is exactly p^n * m.

   - To formalize the divisibility, we can use that if p(x) = q(x) * r(x) and r(a) ≠ 0, then the orderOfRoot of p at a is equal to the orderOfRoot of q at a.

   - More precisely, if p = q * r and r(a) ≠ 0, then orderOfRoot p a = orderOfRoot q a.

   - In our case, p = g, q = (X - a)^(p^n * m), r = h ∘ (X ↦ X^(p^n)). We have r(a) = h(b) ≠ 0, so orderOfRoot g a = orderOfRoot ((X - a)^(p^n * m)) a = p^n * m.

   - Therefore, we need to prove that if r(a) ≠ 0, then orderOfRoot (q * r) a = orderOfRoot q a.

   - This is true because if q = (X - a)^k * q' with q'(a) ≠ 0, then p = (X - a)^k * q' * r, and (q' * r)(a) = q'(a) * r(a) ≠ 0, so orderOfRoot p a = k = orderOfRoot q a.

   - Thus, we can use this lemma.

   - So the steps are:
     i. Get m = Polynomial.orderOfRoot f b.
     ii. Get h such that f = (X - b)^m * h and h(b) ≠ 0.
     iii. Show that (X^(p^n) - b) = (X - a)^(p^n).
     iv. Then, g = f ∘ (X ↦ X^(p^n)) = ((X - a)^(p^n))^m * (h ∘ (X ↦ X^(p^n))).
     v. Let q = (X - a)^(p^n * m) and r = h ∘ (X ↦ X^(p^n)).
     vi. Show that r(a) ≠ 0.
     vii. Conclude that orderOfRoot g a = orderOfRoot q a = p^n * m.

   - We will need to work with polynomial composition and substitution.

   - In Lean, polynomial composition is `Polynomial.comp`. Specifically, `f.comp p` is the polynomial f(p(X)).

   - Here, g = f.comp (polynomial.X ^ (p ^ n)).

   - Also, (X - a) is `polynomial.X - polynomial.C a`.

   - We will need to use lemmas about `Polynomial.comp` and `Polynomial.orderOfRoot`.

   - This seems doable but a bit involved.

   - Alternatively, we can use the fact that the map a ↦ a^(p^n) is bijective and use the multiset argument directly without proving the orderOfRoot lemma for each a, but I think we still need the orderOfRoot lemma to relate the multiplicities.

   - Another approach: Since we are working over a perfect ring, we can use the fact that the Frobenius map is an automorphism to transfer the polynomial f to another polynomial whose roots are the preimages. Specifically, consider the ring automorphism φ : R → R given by φ(x) = x^(p^n). Then, we can define a polynomial f' ∈ R[X] by applying φ^{-1} to the coefficients of f. Then, we have that the roots of f' are the φ^{-1} of the roots of f. Then, we can relate g to f' via the Frobenius map on the polynomial variable.

   - However, this might be more complicated.

   - Given that we have the PerfectRing R p assumption, we can get that the Frobenius map is bijective, and hence we can define its inverse as a function. However, the inverse is not necessarily a polynomial map, so we cannot directly use it to manipulate polynomials.

   - Thus, the factorization approach seems more straightforward.

   - Let's try to implement the factorization approach in Lean.

   - First, we need to show that (X - a)^(p^n) = X^(p^n) - a^(p^n) in R[X].

   - We can prove this by showing that the difference is zero. The difference is (X - a)^(p^n) - (X^(p^n) - a^(p^n)) = ∑_{k=0}^{p^n} C(p^n, k) X^k (-a)^(p^n - k) - X^(p^n) + a^(p^n).

   - The terms for k=0 and k=p^n cancel: for k=0, we get (-a)^(p^n) and we have +a^(p^n) from the subtraction, so (-a)^(p^n) + a^(p^n) = 0 as shown earlier. For k=p^n, we get X^(p^n) and we subtract X^(p^n), so they cancel.

   - For 0 < k < p^n, the coefficient is C(p^n, k) * (-a)^(p^n - k). Since p divides C(p^n, k), and R has characteristic p, this coefficient is zero.

   - Therefore, the entire sum is zero.

   - In Lean, we can use the binomial theorem and the fact that the binomial coefficients are divisible by p.

   - There is a lemma in Mathlib: `binomial_eq_zero_of_dvd` or something? Actually, we can use that if p ∣ binomial n k, then (binomial n k : R) = 0 when R has characteristic p.

   - We can use `ZMod.char_p_dvd_choose` to get that p divides binomial p^n k for 0 < k < p^n, and then use that in R of characteristic p, the integer p is zero, so any multiple of p is zero.

   - Specifically, we have `ExpChar R p` which says that the exponential characteristic of R is p, meaning that p · 1 = 0 in R and p is the smallest such. Then, for any integer n, if p ∣ n, then (n : R) = 0.

   - Therefore, we can show that (binomial (p^n) k : R) = 0 for 0 < k < p^n.

   - Then, the binomial expansion gives (X - a)^(p^n) = ∑_{k=0}^{p^n} (binomial (p^n) k : R) • X^k • (-a)^(p^n - k).

   - The terms for 0 < k < p^n vanish, leaving k=0 and k=p^n terms.

   - Then, we simplify (-a)^(p^n) to -a^(p^n) as discussed.

   - We can formalize this as a lemma: `(polynomial.X - C a) ^ (p ^ n) = (polynomial.X) ^ (p ^ n) - C (a ^ (p ^ n))`.

   - Let's call this lemma `pow_sub_eq_pow_sub`.

   - Now, given this, we can proceed with the factorization.

   - To get h such that f = (X - b)^m * h and h(b) ≠ 0, we can use the following:

     - Let m = Polynomial.orderOfRoot f b.
     - Then, (X - b)^m divides f, so we can write f = (X - b)^m * h for some h.
     - To show that h(b) ≠ 0, we suppose h(b) = 0 and derive a contradiction by showing that (X - b)^(m+1) divides f.

   - In Lean, we can get h by using `Polynomial.ediv` or the fact that if p divides f, then f / p is the quotient. Specifically, since (X - b)^m divides f, we can define h = f / (X - b)^m.

   - Then, we need to show that h(b) ≠ 0. We can do this by showing that if h(b) = 0, then (X - b) divides h, so (X - b)^(m+1) divides f.

   - There is a lemma: `Polynomial.orderOfRoot_eq_iff` or `Polynomial.orderOfRoot_dvd_iff` that can help.

   - Alternatively, we can use that `Polynomial.orderOfRoot f b = m` implies that (X - b)^m ∣ f and ¬((X - b)^(m+1) ∣ f).

   - So, if we have f = (X - b)^m * h, then (X - b)^(m+1) ∣ f iff (X - b) ∣ h.

   - Therefore, ¬((X - b) ∣ h) because m is the maximal order.

   - And (X - b) ∣ h iff h(b) = 0.

   - Therefore, h(b) ≠ 0.

   - Thus, we can get h(b) ≠ 0 from the maximality of m.

   - Now, we need to show that if r(a) ≠ 0, then orderOfRoot (q * r) a = orderOfRoot q a.

   - We can prove this lemma: if q and r are polynomials, and r(a) ≠ 0, then orderOfRoot (q * r) a = orderOfRoot q a.

   - Proof: Let k = orderOfRoot q a, so q = (X - a)^k * q' with q'(a) ≠ 0. Then, q * r = (X - a)^k * (q' * r). Since q'(a) ≠ 0 and r(a) ≠ 0, we have (q' * r)(a) ≠ 0. Therefore, orderOfRoot (q * r) a = k = orderOfRoot q a.

   - In Lean, we can use `Polynomial.orderOfRoot_mul` and the fact that if r(a) ≠ 0 then orderOfRoot r a = 0.

   - Specifically, `Polynomial.orderOfRoot_mul q r a = orderOfRoot q a + orderOfRoot r a`. If r(a) ≠ 0, then orderOfRoot r a = 0, so orderOfRoot (q * r) a = orderOfRoot q a.

   - Therefore, we need to show that orderOfRoot r a = 0, which is equivalent to r(a) ≠ 0.

   - So, we can use `Polynomial.orderOfRoot_eq_iff` to say that orderOfRoot r a = 0 iff ¬((X - a) ∣ r) iff r(a) ≠ 0.

   - Thus, if we show that r(a) ≠ 0, then orderOfRoot r a = 0, and hence orderOfRoot (q * r) a = orderOfRoot q a + 0 = orderOfRoot q a.

   - Therefore, the key step is to show that r(a) ≠ 0, where r = h ∘ (X ↦ X^(p^n)).

   - We have r(a) = h(a^(p^n)) = h(b) ≠ 0.

   - So, we need to compute the composition and evaluation.

   - In Lean, `(h.comp (polynomial.X ^ (p ^ n))).eval a = h.eval ( (polynomial.X ^ (p ^ n)).eval a ) = h.eval (a ^ (p ^ n)) = h.eval b`.

   - Therefore, we can use `Polynomial.eval_comp` to get this.

   - Now, putting it all together:

     - Let m = Polynomial.orderOfRoot f b.
     - Obtain h such that f = (polynomial.X - C b) ^ m * h.
     - Show that h.eval b ≠ 0.
     - Show that (polynomial.X - C a) ^ (p ^ n) = (polynomial.X) ^ (p ^ n) - C (a ^ (p ^ n)).
     - Then, g = f.comp (polynomial.X ^ (p ^ n)) = [((polynomial.X - C b) ^ m).comp (polynomial.X ^ (p ^ n))] * [h.comp (polynomial.X ^ (p ^ n))].
     - But ((polynomial.X - C b) ^ m).comp (polynomial.X ^ (p ^ n)) = [(polynomial.X - C b).comp (polynomial.X ^ (p ^ n))] ^ m because comp respects powers.
     - And (polynomial.X - C b).comp (polynomial.X ^ (p ^ n)) = (polynomial.X ^ (p ^ n) - C b) = (polynomial.X - C a) ^ (p ^ n) by our lemma.
     - Therefore, ((polynomial.X - C b) ^ m).comp (polynomial.X ^ (p ^ n)) = [(polynomial.X - C a) ^ (p ^ n)] ^ m = (polynomial.X - C a) ^ (p ^ n * m).
     - Thus, g = (polynomial.X - C a) ^ (p ^ n * m) * (h.comp (polynomial.X ^ (p ^ n))).
     - Let q = (polynomial.X - C a) ^ (p ^ n * m) and r = h.comp (polynomial.X ^ (p ^ n)).
     - We have r.eval a = h.eval b ≠ 0, so orderOfRoot r a = 0.
     - Therefore, orderOfRoot g a = orderOfRoot q a + orderOfRoot r a = p ^ n * m + 0 = p ^ n * m.

   - This seems feasible.

   - Now, we need to formalize each step in Lean.

   - Let's start by proving the lemma `(polynomial.X - C a) ^ (p ^ n) = (polynomial.X) ^ (p ^ n) - C (a ^ (p ^ n))`.

   - We'll need to use the binomial theorem and properties of binomial coefficients in characteristic p.

   - In Lean, we can use `polynomial.binomial_sum` to expand (X + Y)^n, but we have (X - a)^n = (X + (-a))^n.

   - So, (X - a)^(p^n) = ∑_{k=0}^{p^n} (binomial (p^n) k : R) • X^k • (-a)^(p^n - k).

   - We need to show that this sum equals X^(p^n) - a^(p^n).

   - We can split the sum into k=0, k=p^n, and 0<k<p^n.

   - For k=0: term is (binomial (p^n) 0 : R) • X^0 • (-a)^(p^n) = 1 • 1 • (-a)^(p^n) = (-a)^(p^n).
   - For k=p^n: term is (binomial (p^n) p^n : R) • X^(p^n) • (-a)^0 = 1 • X^(p^n) • 1 = X^(p^n).
   - For 0<k<p^n: term is (binomial (p^n) k : R) • X^k • (-a)^(p^n - k). Since p ∣ binomial (p^n) k, we have (binomial (p^n) k : R) = 0, so the term is zero.

   - Therefore, the sum is (-a)^(p^n) + X^(p^n).

   - Now, we need to show that (-a)^(p^n) = - (a^(p^n)) in R.

   - As discussed earlier, this holds because in characteristic p, (-1)^(p^n) = -1.

   - Proof: If p is odd, then p^n is odd, so (-1)^(p^n) = -1. If p=2, then in characteristic 2, -1 = 1, so (-1)^(p^n) = 1 = -1.

   - Therefore, (-a)^(p^n) = (-1)^(p^n) * a^(p^n) = -1 * a^(p^n) = - (a^(p^n)).

   - Thus, the sum is X^(p^n) - (a^(p^n)).

   - We can formalize this in Lean by proving that (-a : R) ^ (p ^ n) = - (a ^ (p ^ n)).

   - To prove this, we can note that in a ring of characteristic p, we have (-1) ^ (p ^ n) = -1.

   - We can prove that (-1 : R) ^ (p ^ n) = -1 by induction on n, using that p · 1 = 0 implies that (-1) ^ p = -1 (since (-1)^p = -1 if p is odd, and if p=2, (-1)^2 = 1 = -1 in characteristic 2).

   - Alternatively, we can use that in any commutative ring, (-1) ^ (p ^ n) = (-1) ^ (p ^ n) and then use the fact that p ^ n is odd if p is odd, and if p=2, then (-1) ^ (2 ^ n) = 1, but in characteristic 2, 1 = -1.

   - However, perhaps it's easier to prove directly that (-a) ^ (p ^ n) = - (a ^ (p ^ n)) by using the binomial theorem on (-a) ^ (p ^ n) = (-1 * a) ^ (p ^ n) = (-1) ^ (p ^ n) * a ^ (p ^ n), and then showing that (-1) ^ (p ^ n) = -1.

   - To show (-1) ^ (p ^ n) = -1 in R, we can use that the characteristic of R is p, so p · 1 = 0.

   - We can prove by induction on n that (-1) ^ (p ^ n) = -1.

   - Base case n=0: (-1) ^ 1 = -1.

   - Inductive step: assume (-1) ^ (p ^ n) = -1. Then, (-1) ^ (p ^ (n+1)) = [(-1) ^ (p ^ n)] ^ p = (-1) ^ p.

   - Now, we need to show that (-1) ^ p = -1 in R.

   - If p is odd, then (-1) ^ p = -1.

   - If p=2, then (-1) ^ 2 = 1, and in characteristic 2, 1 = -1.

   - Therefore, in both cases, (-1) ^ p = -1.

   - Thus, (-1) ^ (p ^ (n+1)) = (-1) ^ p = -1.

   - This completes the induction.

   - Therefore, we can prove that (-1 : R) ^ (p ^ n) = -1.

   - Then, (-a) ^ (p ^ n) = [(-1) * a] ^ (p ^ n) = (-1) ^ (p ^ n) * a ^ (p ^ n) = (-1) * a ^ (p ^ n) = - (a ^ (p ^ n)).

   - This works.

   - Now, we can prove the lemma about (X - a)^(p^n) = X^(p^n) - a^(p^n).

   - Next, we need to obtain h such that f = (X - b)^m * h and h(b) ≠ 0.

   - In Lean, we can use `Polynomial.orderoot_eq_iff` to get that m = orderOfRoot f b iff (X - b)^m ∣ f and ¬((X - b)^(m+1) ∣ f).

   - Then, we can get h as f / (X - b)^m using division.

   - Specifically, since (X - b)^m ∣ f, we can write f = (X - b)^m * h where h = f / (X - b)^m.

   - Then, to show that h(b) ≠ 0, we use that if h(b) = 0, then (X - b) ∣ h, so (X - b)^(m+1) ∣ f, contradicting the maximality of m.

   - We can use the lemma that if (X - b) ∣ h, then (X - b)^(m+1) ∣ f.

   - In Lean, we can use `Polynomial.dvd_pow` and `Polynomial.pow_dvd_pow_iff` to manipulate divisibility.

   - Alternatively, we can use that `Polynomial.orderOfRoot f b = m` implies that `Polynomial.orderOfRoot h b = 0`.

   - There is a lemma: `Polynomial.orderOfRoot_eq_iff` that says orderOfRoot h b = 0 iff ¬((X - b) ∣ h).

   - And we know that orderOfRoot f b = m = orderOfRoot ((X - b)^m * h) b = m + orderOfRoot h b.

   - Therefore, orderOfRoot h b = 0.

   - This is a better approach: use the additivity of orderOfRoot for products.

   - Specifically, if f = (X - b)^m * h, then orderOfRoot f b = m + orderOfRoot h b.

   - Since orderOfRoot f b = m, we get orderOfRoot h b = 0, which implies h(b) ≠ 0.

   - Therefore, we can avoid the contradiction argument by using the additivity.

   - So, steps:

     - Let m = Polynomial.orderOfRoot f b.
     - Since (X - b)^m ∣ f, we can write f = (X - b)^m * h for some h (by taking h = f / (X - b)^m).
     - Then, orderOfRoot f b = m + orderOfRoot h b.
     - But orderOfRoot f b = m, so orderOfRoot h b = 0.
     - Therefore, h(b) ≠ 0.

   - This is cleaner.

   - Now, we need to formalize the composition and the power.

   - We have g = f.comp (X^(p^n)).

   - We can write f = (X - b)^m * h, so g = [(X - b)^m * h].comp (X^(p^n)) = [(X - b)^m].comp (X^(p^n)) * [h.comp (X^(p^n))] because comp distributes over multiplication.

   - Then, [(X - b)^m].comp (X^(p^n)) = [(X - b).comp (X^(p^n))]^m because comp respects powers.

   - And (X - b).comp (X^(p^n)) = X^(p^n) - b.

   - By our lemma, X^(p^n) - b = (X - a)^(p^n).

   - Therefore, [(X - b).comp (X^(p^n))]^m = [(X - a)^(p^n)]^m = (X - a)^(p^n * m).

   - Thus, g = (X - a)^(p^n * m) * (h.comp (X^(p^n))).

   - Now, we need to show that orderOfRoot (h.comp (X^(p^n))) a = 0.

   - We have (h.comp (X^(p^n))).eval a = h.eval ( (X^(p^n)).eval a ) = h.eval (a^(p^n)) = h.eval b.

   - Since orderOfRoot h b = 0, we have h.eval b ≠ 0.

   - Therefore, (h.comp (X^(p^n))).eval a ≠ 0, so orderOfRoot (h.comp (X^(p^n))) a = 0.

   - Then, orderOfRoot g a = orderOfRoot ((X - a)^(p^n * m)) a + orderOfRoot (h.comp (X^(p^n))) a = p^n * m + 0 = p^n * m.

   - This completes the proof of the key lemma.

   - Now, we can proceed to the multiset argument.

   - We need to show that for any b : R, (map F (roots g)).count b = p^n * (roots f).count b.

   - As discussed, (map F (roots g)).count b = ∑ a : F a = b, (roots g).count a = ∑ a : F a = b, Polynomial.orderOfRoot g a.

   - Using the key lemma, this equals ∑ a : F a = b, p^n * Polynomial.orderOfRoot f (F a) = p^n * ∑ a : F a = b, Polynomial.orderOfRoot f (F a).

   - Since F a = b for all a in the sum, this equals p^n * ∑ a : F a = b, Polynomial.orderOfRoot f b = p^n * (∑ a : F a = b, 1) * Polynomial.orderOfRoot f b.

   - Now, we need to show that ∑ a : F a = b, 1 = 1.

   - This is equivalent to saying that the fiber F^{-1}({b}) has exactly one element.

   - Since F is bijective, this is true.

   - Therefore, the sum is p^n * 1 * Polynomial.orderOfRoot f b = p^n * Polynomial.orderOfRoot f b.

   - And (p^n • roots f).count b = p^n * (roots f).count b = p^n * Polynomial.orderOfRoot f b.

   - Hence, the counts are equal.

   - Therefore, the multisets are equal.

   - Now, we need to formalize the bijectivity of F.

   - We have F = iterateFrobenius R p n.

   - We know that R is a perfect ring of characteristic p, so the Frobenius map is bijective.

   - The n-th iterate of a bijective function is bijective.

   - In Lean, we can get that the Frobenius map is bijective from PerfectRing R p.

   - Let's check: PerfectRing R p extends FrobeniusSurjective R p and FrobeniusInjective R p? Actually, looking at Mathlib, PerfectRing R p is a class that extends FrobeniusSurjective R p and assumes that R is reduced? No, let's check the actual definition.

   - In Mathlib4, `PerfectRing R p` is defined as `FrobeniusSurjective R p` plus the assumption that `R` is reduced? No, actually, it's just `FrobeniusSurjective R p` and `IsDomain R`? No, let's see:

   - Actually, `PerfectRing R p` is a class that extends `FrobeniusSurjective R p` and adds that `R` is reduced? I'm not sure.

   - However, we have both `Inst✝² : IsDomain R` and `Inst✝ : PerfectRing R p`.

   - Looking at Mathlib's `PerfectRing` (in `Algebra.Ring.Defs.Perfect`), we see that `PerfectRing R p` is a class that extends `FrobeniusSurjective R p` and adds that `R` is reduced? No, actually, it's just `FrobeniusSurjective R p` and the assumption that `R` is a `Semiring`? No, let's check the actual source.

   - Since I don't have access to the source, I'll assume that `PerfectRing R p` gives that the Frobenius map is surjective. For injectivity, we can use that `R` is a domain: if x^p = 0 then x = 0, so the Frobenius map is injective.

   - Therefore, the Frobenius map is bijective.

   - Then, the n-th iterate of a bijective function is bijective.

   - In Lean, we can get a `Bijective` instance for `iterateFrobenius R p n` by using the fact that the Frobenius map is bijective and then using `Bijective.iterate`.

   - Specifically, if `f : R → R` is bijective, then `f^[n]` is bijective.

   - Here, `iterateFrobenius R p n` is the n-th iterate of the Frobenius map.

   - So, we need to get that the Frobenius map is bijective.

   - Let's denote `Frob : R →+* R` as the Frobenius map (x ↦ x^p).

   - We can get that `Frob` is injective because `R` is a domain: if x^p = 0 then x = 0.

   - We can get that `Frob` is surjective because `PerfectRing R p` gives `FrobeniusSurjective R p`.

   - Therefore, `Frob` is bijective.

   - Then, `iterateFrobenius R p n` is `Frob^[n]`, which is bijective because the iterate of a bijective function is bijective.

   - In Lean, there is a lemma: `Function.Bijective.iterate` that says if `f` is bijective, then `f^[n]` is bijective.

   - Therefore, we can obtain a `Bijective` instance for `iterateFrobenius R p n`.

   - Now, to use the fact that the fiber is a singleton, we can use that if `f` is bijective, then for any `b`, there exists a unique `a` such that `f a = b`.

   - In Lean, we can use `Function.Bijective` to get that the function is injective and surjective, and then use `Function.Surjective` and `Function.Injective` to get the uniqueness.

   - Specifically, if `f` is bijective, then the fiber `f⁻¹({b})` is a singleton.

   - We can get the cardinality of the fiber as 1 by using that `f` is injective and surjective.

   - However, in the multiset count, we need the sum over the fiber of 1, which is the cardinality of the fiber.

   - Since the fiber is a singleton, the sum is 1.

   - We can avoid talking about cardinality by directly using the bijectivity to change the sum.

   - Specifically, since `F` is bijective, we can reindex the sum over `a : F a = b` to a sum over a single element.

   - But perhaps it's easier to use the fact that the sum over `a : F a = b` of `1` is equal to 1 because there is exactly one such `a`.

   - To get this, we can use that `F` is injective and surjective.

   - Surjectivity gives that there exists at least one `a` such that `F a = b`.

   - Injectivity gives that there is at most one such `a`.

   - Therefore, there is exactly one such `a`.

   - Thus, the sum over `a : F a = b` of 1 is 1.

   - In Lean, we can use `Set.exists_unique_iff` or something similar to get the unique element, and then compute the sum.

   - However, since we are working with a sum over a type, we can use the fact that if we have a decidable predicate and we know that there is exactly one element satisfying it, then the sum is 1.

   - Alternatively, we can use that the sum over `a : R` of `if F a = b then 1 else 0` is equal to 1 because `F` is bijective.

   - This sum is exactly the cardinality of the fiber.

   - In Lean, we can use `Finset.sum_ite_eq'` or something similar to compute this sum if we have a Finset, but we are summing over the entire type `R`.

   - Since `R` is not necessarily finite, we cannot directly use Finset sums. However, the sum we are considering is actually a sum over the multiset `roots g`, which is finite.

   - Wait, no: in the expression `(map F (roots g)).count b`, we have a sum over the multiset `roots g`, which is finite. So we are summing over the elements of the multiset `roots g`, not over the entire type `R`.

   - Therefore, we don't need to worry about the sum over the entire type `R` being infinite; we are only summing over the finite multiset `roots g`.

   - Similarly, in the key lemma approach, we used the sum over `a : F a = b` of `Polynomial.orderOfRoot g a`, but since `roots g` is finite, only finitely many `a` have `Polynomial.orderOfRoot g a > 0`, so the sum is finite.

   - However, when we rewrote the sum as `∑ a : F a = b, p^n * Polynomial.orderOfRoot f (F a)`, we are still summing over `a : R` such that `F a = b`, but we can restrict to those `a` where `Polynomial.orderOfRoot f (F a) > 0` because otherwise the term is zero. But since `F a = b`, this is equivalent to `Polynomial.orderOfRoot f b > 0`, which is either true or false for all such `a`.

   - Actually, if there are no `a` such that `F a = b`, then the sum is zero. But since `F` is surjective, there is at least one such `a`. And since `F` is injective, there is exactly one such `a`.

   - Therefore, the sum over `a : F a = b` of `Polynomial.orderOfRoot f (F a)` is equal to `Polynomial.orderOfRoot f b` if there exists an `a` such that `F a = b`, and zero otherwise. But since `F` is surjective, it's always equal to `Polynomial.orderOfRoot f b`.

   - Wait, no: if there is exactly one `a` such that `F a = b`, then the sum is `Polynomial.orderOfRoot f (F a)` for that `a`, which is `Polynomial.orderOfRoot f b`.

   - Therefore, we don't need to multiply by the number of elements in the fiber; we can directly say that the sum over `a : F a = b` of `Polynomial.orderOfRoot f (F a)` is equal to `Polynomial.orderOfRoot f b` because there is exactly one `a` in the fiber and for that `a`, `F a = b`.

   - Thus, we can avoid talking about the cardinality of the fiber by using the following:

     ∑ a : F a = b, Polynomial.orderOfRoot f (F a) = Polynomial.orderOfRoot f b

     because the sum has exactly one term (since F is bijective), and that term is Polynomial.orderOfRoot f b.

   - To formalize this, we can use the fact that F is bijective to get that the fiber F⁻¹({b}) is a singleton, and then rewrite the sum over the singleton.

   - In Lean, we can use `Finset.sum_singleton` if we can get the fiber as a Finset, but since R is not finite, we cannot directly get the fiber as a Finset.

   - However, we are summing over the multiset `roots g`, which is finite, so we can instead use the following approach:

     (map F (roots g)).count b = ∑ a in roots g, if F a = b then 1 else 0

     = ∑ a in roots g, if F a = b then (p^n * Polynomial.orderOfRoot f (F a)) / p^n else 0

     But this seems messy.

   - Alternatively, we can use the key lemma to write:

     ∑ a in roots g, if F a = b then 1 else 0 = (1/p^n) * ∑ a in roots g, if F a = b then Polynomial.orderOfRoot g a else 0

     But we don't want to divide by p^n.

   - Perhaps a better way is to note that:

     (map F (roots g)).count b = ∑ a in roots g, if F a = b then 1 else 0

     = ∑ a in roots g, if F a = b then (Polynomial.orderOfRoot g a) / (p^n * Polynomial.orderOfRoot f (F a)) * Polynomial.orderOfRoot f (F a) else 0

     This is not helpful.

   - Let's go back to the original plan:

     We have:

     (map F (roots g)).count b = ∑ a : F a = b, (roots g).count a

     = ∑ a : F a = b, Polynomial.orderOfRoot g a

     = ∑ a : F a = b, p^n * Polynomial.orderOfRoot f (F a)   [by key lemma]

     = p^n * ∑ a : F a = b, Polynomial.orderOfRoot f (F a)

     Now, since F a = b for all a in the sum, we have:

     = p^n * ∑ a : F a = b, Polynomial.orderOfRoot f b

     = p^n * (∑ a : F a = b, 1) * Polynomial.orderOfRoot f b

     Now, we need to show that ∑ a : F a = b, 1 = 1.

     Since the sum is over a : R such that F a = b, and we know that there is exactly one such a (because F is bijective), the sum is 1.

     To formalize this in Lean, we can use the fact that F is bijective to get that the fiber is a singleton, and then use the following lemma:

     If s : Finset R and t : Finset R are such that s = t, then ∑ x in s, f x = ∑ x in t, f x.

     But we don't have a Finset for the fiber.

     However, we can note that the sum ∑ a : F a = b, 1 is equal to the cardinality of the fiber F⁻¹({b}).

     Since F is bijective, this cardinality is 1.

     In Lean, we can use `Fintype.card_fiberwise` or something similar if we have a Fintype instance for R, but R is not necessarily finite.

     Alternatively, we can use that the sum over a : R of `if F a = b then 1 else 0` is equal to 1 because F is bijective.

     This sum is exactly the cardinality of the fiber.

     In Lean, we can use the fact that if f : R → R is bijective, then ∑ a : R, if f a = b then 1 else 0 = 1.

     This is true because the sum counts the number of a such that f a = b, which is exactly 1.

     However, this sum is over the entire type R, which may be infinite, but in Lean, the sum of an infinite number of 1s is not defined unless we have a topological structure or we use the concept of summable families.

     But in our case, we are not summing over the entire type R; we are summing over the multiset `roots g`, which is finite.

     Therefore, we need to relate the sum over the multiset to the sum over the type.

     We can do the following:

     ∑ a in roots g, if F a = b then 1 else 0 = ∑ a : R, (if a ∈ roots g then 1 else 0) * (if F a = b then 1 else 0)

     But this is getting complicated.

     Perhaps a better approach is to use the fact that the map F is bijective to transfer the multiset `roots g` to a multiset whose elements are in bijection with `roots f`.

     Specifically, since F is bijective, we can define a multiset `S` such that `map F S = roots g` and `S` is in bijection with `roots f`.

     But we already have that `roots g` is the multiset of roots of `g`, and we know that `F` induces a bijection between the roots of `g` and the roots of `f` when we take into account multiplicities scaled by p^n.

     Alternatively, we can use the following trick:

     Since F is bijective, we can define a multiset `T` by `T = image (F⁻¹) (roots f)`, where `F⁻¹` is the inverse function.

     Then, `map F T = roots f`.

     But we want to relate `roots g` to `T`.

     We know that for each root `a` of `g` with multiplicity `m_a`, `F a` is a root of `f` with multiplicity `m_a / p^n`.

     Therefore, if we take each root `b` of `f` with multiplicity `m_b`, and replace it by `p^n` copies of `F⁻¹(b)`, we get the multiset of roots of `g`.

     Therefore, `roots g = map (F⁻¹) (p^n • roots f)`.

     Then, `map F (roots g) = map F (map (F⁻¹) (p^n • roots f)) = map (F ∘ F⁻¹) (p^n • roots f) = map id (p^n • roots f) = p^n • roots f`.

     This would be perfect, but it requires that we have an inverse function `F⁻¹ : R → R` such that `F ∘ F⁻¹ = id` and `F⁻¹ ∘ F = id`.

     Since F is bijective, we can obtain such an inverse function using classical logic.

     In Lean, we can use `Classical.choose` to get an inverse function.

     Specifically, since F is surjective, for each b : R, there exists an a : R such that F a = b. We can choose one such a for each b, and this gives a function `G : R → R` such that F (G b) = b for all b.

     Moreover, since F is injective, this G is also a left inverse: G (F a) = a for all a.

     Therefore, G is the inverse of F.

     Then, we can define `T = map G (p^n • roots f)`.

     Then, `map F T = map F (map G (p^n • roots f)) = map (F ∘ G) (p^n • roots f) = map id (p^n • roots f) = p^n • roots f`.

     On the other hand, we want to show that `T = roots g`.

     To show that, we need to show that for any a : R, the multiplicity of a in T is equal to the multiplicity of a in roots g.

     The multiplicity of a in T is the multiplicity of F a in (p^n • roots f) because T = map G (p^n • roots f) and G is the inverse of F.

     More precisely, since G is the inverse of F, we have that a ∈ T with multiplicity m iff F a ∈ (p^n • roots f) with multiplicity m.

     Because map G s has the property that (map G s).count a = s.count (F a) when G is the inverse of F? Let's check:

     If s is a multiset and G : R → R is a function, then (map G s).count b = ∑ a : G a = b, s.count a.

     If G is the inverse of F, then G a = b iff a = F b.

     Therefore, (map G s).count b = s.count (F b).

     Yes, because the sum over a : G a = b of s.count a has exactly one term a = F b (since G is injective and F is its inverse), and s.count (F b).

     Therefore, (map G s).count b = s.count (F b).

     Now, take s = p^n • roots f.

     Then, T = map G s, so T.count a = s.count (F a) = (p^n • roots f).count (F a) = p^n * (roots f).count (F a).

     On the other hand, the multiplicity of a in roots g is Polynomial.orderOfRoot g a.

     By the key lemma, Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f (F a) = p^n * (roots f).count (F a).

     Therefore, T.count a = roots g.count a for all a.

     Hence, T = roots g.

     Therefore, roots g = map G (p^n • roots f).

     Then, applying F to both sides: map F (roots g) = map F (map G (p^n • roots f)) = map (F ∘ G) (p^n • roots f) = map id (p^n • roots f) = p^n • roots f.

     This is exactly what we want.

     This approach avoids dealing with sums over fibers and directly uses the inverse function.

     The steps are:

     1. Obtain a bijective function F : R → R (the iterateFrobenius).
     2. Obtain its inverse G : R → R (using classical choice).
     3. Prove the key lemma: ∀ a : R, Polynomial.orderOfRoot (expand R (p ^ n) f) a = p^n * Polynomial.orderOfRoot f (F a).
     4. Show that for any a : R, (map G (p^n • roots f)).count a = p^n * Polynomial.orderOfRoot f (F a).
        - Because (map G s).count a = s.count (F a) when G is the inverse of F.
        - And s = p^n • roots f, so s.count (F a) = p^n * (roots f).count (F a).
     5. Show that (roots g).count a = Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f (F a) by the key lemma.
     6. Therefore, (map G (p^n • roots f)).count a = (roots g).count a for all a, so map G (p^n • roots f) = roots g.
     7. Then, apply F to both sides and use that F ∘ G = id to get map F (roots g) = p^n • roots f.

     This seems like a solid plan.

     Now, we need to formalize each step in Lean.

     Let's start by obtaining the bijectivity of F.

     We have:
     - `Frob : R →+* R` is the Frobenius map (x ↦ x^p).
     - `Frob.injective` because R is a domain: if x^p = 0 then x = 0.
     - `Frob.surjective` because PerfectRing R p gives FrobeniusSurjective R p.
     - Therefore, Frob is bijective.
     - Then, `iterateFrobenius R p n` is Frob^[n], which is bijective because the iterate of a bijective function is bijective.

     In Lean, we can get `Bijective (iterateFrobenius R p n)` by using `Bijective.iterate` applied to the bijectivity of Frob.

     However, we need to get the bijectivity of Frob first.

     Let's see if we can get `Frob.injective` and `Frob.surjective` from our assumptions.

     - For injectivity: if x^p = 0 in a domain, then x = 0. This is true because in a domain, if x^p = 0 then x = 0 (by induction: if x ≠ 0, then x^p ≠ 0 because the product of non-zero elements is non-zero in a domain).

     - For surjectivity: PerfectRing R p gives that the Frobenius map is surjective. In Mathlib, `PerfectRing R p` extends `FrobeniusSurjective R p`.

     Let's check: in Mathlib4, `PerfectRing R p` is defined as `FrobeniusSurjective R p` (see https://leanprover-community.github.io/mathlib_docs/algebra/ring_defs/perfect.html#PerfectRing). Actually, it seems that `PerfectRing R p` is just `FrobeniusSurjective R p` plus the assumption that `R` is reduced? No, looking at the source, it seems that `PerfectRing R p` is a class that extends `FrobeniusSurjective R p` and adds that `R` is a `Semiring`? I'm not sure.

     However, we have both `IsDomain R` and `PerfectRing R p`, so we can get surjectivity from `PerfectRing R p` and injectivity from `IsDomain R`.

     Let's assume we can get `Bijective Frob`.

     Then, we can get `Bijective (iterateFrobenius R p n)` by using that the iterate of a bijective function is bijective.

     In Lean, there is a lemma: `Function.Bijective.iterate` in the file `Function.Basic`.

     Specifically, if `f : α → α` is bijective, then `f^[n]` is bijective.

     Here, `iterateFrobenius R p n` is `Frob^[n]`.

     Therefore, we can get `Bijective (iterateFrobenius R p n)`.

     Now, we need to get the inverse function G.

     Since we have `Bijective F`, we can get `Function.Bijective F`, which gives us `Function.Injective F` and `Function.Surjective F`.

     Then, we can use `Classical.choose` to get a right inverse: since F is surjective, for each b, there exists an a such that F a = b. We can choose one such a for each b to get a function G : R → R such that F (G b) = b for all b.

     Moreover, since F is injective, this G is also a left inverse: G (F a) = a for all a.

     In Lean, we can use `Function.surjective_iff_has_right_inverse` to get a right inverse, and then use injectivity to show that it is also a left inverse.

     Alternatively, we can use `Function.bijective_iff_has_inverse` to get an inverse function directly.

     Since we have `Bijective F`, we can get that there exists a function `G : R → R` such that `F ∘ G = id` and `G ∘ F = id`.

     In Lean, we can use `Function.bijective_iff_has_inverse.mp` to get this.

     Specifically, if `hf : Bijective F`, then we can get `∃ (G : R → R), F ∘ G = id ∧ G ∘ F = id`.

     Then, we can obtain such a G.

     Now, we need to prove the key lemma: ∀ a : R, Polynomial.orderOfRoot (expand R (p ^ n) f) a = p^n * Polynomial.orderOfRoot f (F a).

     We'll need to do the factorization as discussed.

     Let's sketch the proof of the key lemma in Lean:

     1. Let b = F a.
     2. Let m = Polynomial.orderOfRoot f b.
     3. Since (polynomial.X - C b)^m ∣ f, we can write f = (polynomial.X - C b)^m * h for some h.
        - We can obtain h as f / (polynomial.X - C b)^m using division.
     4. Then, orderOfRoot f b = m + orderOfRoot h b, so orderOfRoot h b = 0.
        - Therefore, h.eval b ≠ 0.
     5. Show that (polynomial.X - C a)^(p ^ n) = (polynomial.X)^(p ^ n) - C (a ^ (p ^ n)).
        - This is our earlier lemma.
     6. Note that b = a ^ (p ^ n), so (polynomial.X)^(p ^ n) - C b = (polynomial.X - C a)^(p ^ n).
     7. Then, g = f.comp (polynomial.X ^ (p ^ n)) = [(polynomial.X - C b)^m * h].comp (polynomial.X ^ (p ^ n))
        = [(polynomial.X - C b)^m].comp (polynomial.X ^ (p ^ n)) * [h.comp (polynomial.X ^ (p ^ n))]
        = [(polynomial.X - C b).comp (polynomial.X ^ (p ^ n))]^m * [h.comp (polynomial.X ^ (p ^ n))]
        = [(polynomial.X ^ (p ^ n) - C b)]^m * [h.comp (polynomial.X ^ (p ^ n))]
        = [(polynomial.X - C a)^(p ^ n)]^m * [h.comp (polynomial.X ^ (p ^ n))]
        = (polynomial.X - C a)^(p ^ n * m) * [h.comp (polynomial.X ^ (p ^ n))].
     8. Let q = (polynomial.X - C a)^(p ^ n * m) and r = h.comp (polynomial.X ^ (p ^ n)).
     9. We have r.eval a = h.eval (a ^ (p ^ n)) = h.eval b ≠ 0, so orderOfRoot r a = 0.
     10. Therefore, orderOfRoot g a = orderOfRoot q a + orderOfRoot r a = p ^ n * m + 0 = p ^ n * m.

     Now, we need to formalize each of these steps in Lean.

     Let's start with step 5: proving `(polynomial.X - C a)^(p ^ n) = (polynomial.X)^(p ^ n) - C (a ^ (p ^ n))`.

     We'll need to use the binomial theorem and properties of binomial coefficients in characteristic p.

     In Lean, we can use `polynomial.binomial_sum` to expand `(X + Y)^n`.

     We have `(X - a)^n = (X + (-a))^n = ∑_{k=0}^n (binomial n k : R) • X^k • (-a)^(n - k)`.

     We need to show that this sum equals `X^n - a^n`.

     We can split the sum into k=0, k=n, and 0<k<n.

     For k=0: term is (binomial n 0 : R) • X^0 • (-a)^n = (-a)^n.
     For k=n: term is (binomial n n : R) • X^n • (-a)^0 = X^n.
     For 0<k<n: term is (binomial n k : R) • X^k • (-a)^(n - k). Since p ∣ binomial n k, we have (binomial n k : R) = 0, so the term is zero.

     Therefore, the sum is (-a)^n + X^n.

     Now, we need to show that (-a)^n = - (a^n) when n = p ^ n.

     As discussed, this holds because (-1)^(p ^ n) = -1 in R.

     We can prove a lemma: `(-1 : R) ^ (p ^ n) = -1`.

     Proof: by induction on n, using that p · 1 = 0 implies that (-1)^p = -1.

     Base case: n=0, (-1)^1 = -1.

     Inductive step: assume (-1)^(p ^ n) = -1. Then, (-1)^(p ^ (n+1)) = [(-1)^(p ^ n)]^p = (-1)^p = -1.

     To show (-1)^p = -1:
       - If p is odd, then (-1)^p = -1.
       - If p=2, then (-1)^2 = 1, and in characteristic 2, 1 = -1.

     Therefore, (-1)^(p ^ n) = -1.

     Then, (-a)^(p ^ n) = [(-1) * a]^(p ^ n) = (-1)^(p ^ n) * a^(p ^ n) = (-1) * a^(p ^ n) = - (a^(p ^ n)).

     Therefore, (X - a)^(p ^ n) = X^(p ^ n) - a^(p ^ n).

     We can formalize this in Lean as follows:

     - Prove that `(-1 : R) ^ (p ^ n) = -1`.
     - Then, prove that `(-a : R) ^ (p ^ n) = - (a ^ (p ^ n))`.
     - Then, use the binomial theorem to expand `(X - a)^(p ^ n)` and show that the middle terms vanish.

     However, in Lean, it might be easier to directly prove that `(X - a)^(p ^ n) = X^(p ^ n) - a^(p ^ n)` by showing that their difference is zero, using the binomial theorem and the fact that the binomial coefficients are divisible by p.

     Let's try to find existing lemmas in Mathlib.

     There is a lemma: `polynomial.C_a_sub_X_pow_card` in `Mathlib.Data.Polynomial.Binomial` that might be relevant, but I'm not sure.

     Alternatively, we can use the fact that in a commutative ring of characteristic p, the Frobenius map is a ring homomorphism, so (x + y)^(p ^ n) = x^(p ^ n) + y^(p ^ n).

     Wait, this is true! In a commutative ring of characteristic p, we have (x + y)^p = x^p + y^p, and by induction, (x + y)^(p ^ n) = x^(p ^ n) + y^(p ^ n).

     Therefore, (x - y)^(p ^ n) = (x + (-y))^(p ^ n) = x^(p ^ n) + (-y)^(p ^ n) = x^(p ^ n) + (-1)^(p ^ n) y^(p ^ n).

     And as we discussed, (-1)^(p ^ n) = -1, so (x - y)^(p ^ n) = x^(p ^ n) - y^(p ^ n).

     This is a much simpler way to prove it!

     Therefore, we can use the fact that the Frobenius map is a ring homomorphism in characteristic p to get that (x + y)^(p ^ n) = x^(p ^ n) + y^(p ^ n).

     In Lean, we have the lemma `FrobeniusHom.map_add` or something similar? Actually, the Frobenius map is a ring homomorphism, so it respects addition and multiplication.

     Specifically, the map `x ↦ x^(p ^ n)` is a ring homomorphism because it is the n-th iterate of the Frobenius map, which is a ring homomorphism.

     Therefore, we have `(x + y)^(p ^ n) = x^(p ^ n) + y^(p ^ n)` and `(x * y)^(p ^ n) = x^(p ^ n) * y^(p ^ n)`.

     In particular, taking y = -x, we get `0 = x^(p ^ n) + (-x)^(p ^ n)`, so `(-x)^(p ^ n) = - (x^(p ^ n))`.

     Wait, no: `(x + (-x))^(p ^ n) = 0^(p ^ n) = 0`, and also `x^(p ^ n) + (-x)^(p ^ n)`, so `x^(p ^ n) + (-x)^(p ^ n) = 0`, hence `(-x)^(p ^ n) = - (x^(p ^ n))`.

     This is true in any commutative ring where the Frobenius map is a ring homomorphism, which it is in characteristic p.

     Therefore, we have `(-a)^(p ^ n) = - (a^(p ^ n))` directly from the fact that the Frobenius map is a ring homomorphism.

     Then, `(a - b)^(p ^ n) = (a + (-b))^(p ^ n) = a^(p ^ n) + (-b)^(p ^ n) = a^(p ^ n) - b^(p ^ n)`.

     Therefore, we can prove `(polynomial.X - C a)^(p ^ n) = (polynomial.X)^(p ^ n) - C (a ^ (p ^ n))` by using that the Frobenius map on the polynomial ring is a ring homomorphism.

     Specifically, the map `p ↦ p^(p ^ n)` is a ring homomorphism from `R[X]` to `R[X]` because it is the n-th iterate of the Frobenius map on `R[X]`.

     Wait, no: the Frobenius map on `R[X]` is not just raising each coefficient to the p-th power; it also sends X to X^p. However, the map that sends a polynomial to its p^n-th power is not a ring homomorphism unless p^n = 1.

     Actually, we are not raising the polynomial to the p^n-th power; we are using the fact that in the polynomial ring, the Frobenius map (raising coefficients to the p-th power) is a ring homomorphism, and we are using the property that `(x + y)^p = x^p + y^p` in the polynomial ring because the polynomial ring has characteristic p.

     Yes! The polynomial ring `R[X]` has characteristic p because R has characteristic p. Therefore, in `R[X]`, we have `(A + B)^p = A^p + B^p` for any polynomials A, B.

     By induction, `(A + B)^(p ^ n) = A^(p ^ n) + B^(p ^ n)`.

     Therefore, taking A = X and B = -a (as a constant polynomial), we get `(X - a)^(p ^ n) = X^(p ^ n) + (-a)^(p ^ n)`.

     And since the Frobenius map on R is a ring homomorphism, we have `(-a)^(p ^ n) = - (a^(p ^ n))`.

     Therefore, `(X - a)^(p ^ n) = X^(p ^ n) - a^(p ^ n)`.

     This is much simpler and avoids the binomial theorem.

     In Lean, we can use the fact that in a semiring of characteristic p, the Frobenius map is a ring homomorphism, so `(x + y) ^ p = x ^ p + y ^ p`.

     Specifically, we have the lemma `pow_add_pow_char` in `Mathlib.Algebra.CharP.Char` which states that if R has characteristic p, then for any x y : R, (x + y) ^ p ^ n = x ^ p ^ n + y ^ p ^ n.

     Let's check: in Mathlib, there is `add_pow_char` and `pow_add_pow_char`.

     Actually, in `Mathlib.Algebra.CharP.Char`, we have:

     ```
     theorem add_pow_char {R : Type*} [Semiring R] [Fact (CharP.R p R)] (x y : R) :
         (x + y) ^ p = x ^ p + y ^ p := ...
     ```

     And then by induction, we can get `(x + y) ^ (p ^ n) = x ^ (p ^ n) + y ^ (p ^ n)`.

     There is a lemma `zpow_add_zpow_char` for integers, but for naturals, we can use `pow_add_pow_char` iteratively.

     However, we can also use that the Frobenius map is a ring homomorphism, so it respects addition, and thus the n-th iterate also respects addition.

     Specifically, the Frobenius map `F : R → R` is a ring homomorphism, so `F (x + y) = F x + F y`.

     Then, `F^n (x + y) = F^n x + F^n y`.

     Here, `F^n x = x ^ (p ^ n)`.

     Therefore, `(x + y) ^ (p ^ n) = x ^ (p ^ n) + y ^ (p ^ n)`.

     This is exactly what we need.

     In Lean, we can get that the Frobenius map is a ring homomorphism from `FrobeniusHom` or something similar.

     Actually, the Frobenius map is defined as a ring homomorphism in `Mathlib.RingTheory.Frobenius`.

     We have `FrobeniusHom R p` which is a ring homomorphism from R to R.

     Then, its n-th iterate is also a ring homomorphism.

     Therefore, we can use that `(x + y) ^ (p ^ n) = x ^ (p ^ n) + y ^ (p ^ n)` because the Frobenius map is a ring homomorphism.

     More precisely, if `F : R →+* R` is the Frobenius homomorphism, then `F^n : R →+* R` is also a ring homomorphism, and `F^n x = x ^ (p ^ n)`.

     Therefore, `F^n (x + y) = F^n x + F^n y` translates to `(x + y) ^ (p ^ n) = x ^ (p ^ n) + y ^ (p ^ n)`.

     Similarly, `F^n (x * y) = F^n x * F^n y` gives `(x * y) ^ (p ^ n) = x ^ (p ^ n) * y ^ (p ^ n)`.

     Therefore, we can use these properties.

     Now, to prove `(X - a)^(p ^ n) = X^(p ^ n) - a^(p ^ n)` in `R[X]`, we note that `R[X]` has characteristic p because R does.

     Therefore, the Frobenius map on `R[X]` is a ring homomorphism, and we have:

     `(X - a)^(p ^ n) = (X + (-a))^(p ^ n) = X^(p ^ n) + (-a)^(p ^ n)`.

     Now, `(-a)^(p ^ n)` in `R[X]` is the constant polynomial `(-a : R) ^ (p ^ n)`.

     Since the Frobenius map on R is a ring homomorphism, we have `(-a) ^ (p ^ n) = - (a ^ (p ^ n))`.

     Therefore, `(X - a)^(p ^ n) = X^(p ^ n) - (a ^ (p ^ n))`.

     In Lean, we can use the fact that the Frobenius map on `R[X]` is a ring homomorphism to get the first equality, and then use the Frobenius map on R to get the second.

     Specifically, we can use:

     - `FrobeniusHom.map_add` or the fact that the Frobenius map is a ring homomorphism to get `(X + Y) ^ p = X ^ p + Y ^ p` in `R[X]`.
     - Then, by induction, `(X + Y) ^ (p ^ n) = X ^ (p ^ n) + Y ^ (p ^ n)`.
     - Take Y = -a (as a constant polynomial).
     - Then, `(X - a) ^ (p ^ n) = X ^ (p ^ n) + (-a) ^ (p ^ n)`.
     - Now, `(-a) ^ (p ^ n)` in `R[X]` is the constant polynomial `((-a : R) ^ (p ^ n))`.
     - Since the Frobenius map on R is a ring homomorphism, we have `(-a : R) ^ (p ^ n) = - (a : R) ^ (p ^ n)`.
     - Therefore, `(X - a) ^ (p ^ n) = X ^ (p ^ n) - C (a ^ (p ^ n))`.

     We can formalize this by using the `FrobeniusHom` structure.

     However, perhaps it's easier to use the characteristic p property directly.

     In Lean, there is a lemma: `pow_add_pow_char` in `Mathlib.Algebra.CharP.Char` that says:

     ```
     theorem pow_add_pow_char {R : Type*} [Semiring R] [Fact (CharP.R p R)] (n : ℕ) (x y : R) :
         (x + y) ^ (p ^ n) = x ^ (p ^ n) + y ^ (p ^ n) := ...
     ```

     Let's check if this exists.

     Actually, in `Mathlib.Algebra.CharP.Char`, we have:

     ```
     theorem add_pow_char {R : Type*} [Semiring R] [Fact (CharP.R p R)] (x y : R) :
         (x + y) ^ p = x ^ p + y ^ p := ...
     ```

     And then we can prove by induction on n that `(x + y) ^ (p ^ n) = x ^ (p ^ n) + y ^ (p ^ n)`.

     There might be a lemma for this.

     Alternatively, we can use that the Frobenius map is a ring homomorphism, so we can get the property for the polynomial ring by noting that it has characteristic p.

     Since we have `ExpChar R p`, which gives that the characteristic of R is p, we can get that the characteristic of `R[X]` is also p.

     Then, we can use the same lemma for `R[X]`.

     Specifically, we have `[Fact (CharP.R p (Polynomial R))]` because if R has characteristic p, then so does `R[X]`.

     Then, we can apply `pow_add_pow_char` to the polynomials X and `-C a` in `R[X]`.

     Let's try this approach.

     Steps:

     1. Show that `R[X]` has characteristic p.
        - Since R has characteristic p, the characteristic of `R[X]` is also p.
        - In Lean, we can use `charPolynomial` or something similar.
        - Actually, there is a lemma: `char_of_char` that says if R has characteristic n, then `R[X]` has characteristic n.
        - We have `Fact (CharP.R p R)`, so we can get `Fact (CharP.R p (Polynomial R))`.

     2. Then, apply `pow_add_pow_char` to `x = X` and `y = -C a` in `R[X]` to get:
        `(X + (-C a)) ^ (p ^ n) = X ^ (p ^ n) + (-C a) ^ (p ^ n)`.

     3. Simplify the left side: `X + (-C a) = X - C a`.

     4. Simplify the right side: `(-C a) ^ (p ^ n) = C ((-a) ^ (p ^ n))` because the Frobenius map on the polynomial ring acts on coefficients.

        - Actually, in `R[X]`, `(C c) ^ n = C (c ^ n)` for any natural number n and c : R.
        - Therefore, `(-C a) ^ (p ^ n) = C ((-a) ^ (p ^ n))`.

     5. Now, we need to show that `((-a) ^ (p ^ n) : R) = - (a ^ (p ^ n))`.

        - This follows from the fact that the Frobenius map on R is a ring homomorphism, so `(-a) ^ p = - (a ^ p)`, and by induction, `(-a) ^ (p ^ n) = - (a ^ (p ^ n))`.

        - Alternatively, we can use that in R of characteristic p, `( -1 ) ^ (p ^ n) = -1`, as discussed.

     6. Therefore, `(-C a) ^ (p ^ n) = C (- (a ^ (p ^ n))) = - C (a ^ (p ^ n))`.

     7. Hence, `(X - C a) ^ (p ^ n) = X ^ (p ^ n) - C (a ^ (p ^ n))`.

     This seems feasible.

     Now, let's see if we can get `Fact (CharP.R p (Polynomial R))` from `Fact (CharP.R p R)`.

     In Lean, there is a lemma: `CharP.char_of_char` or something similar.

     Actually, in `Mathlib.Algebra.CharP.Basic`, we have:

     ```
     instance char_of_char {R : Type*} [Semiring R] {n : ℕ} [Fact (CharP.R n R)] :
         Fact (CharP.R n (Polynomial R)) := ...
     ```

     This should exist.

     Therefore, we can get that `R[X]` has characteristic p.

     Then, we can use `pow_add_pow_char` for `R[X]`.

     Now, we need to get the fact that `(C c) ^ n = C (c ^ n)`.

     This is true because the polynomial ring is a semiring, and the constant polynomial embedding is a semiring homomorphism.

     Specifically, the map `C : R → R[X]` is a semiring homomorphism, so `C (c ^ n) = (C c) ^ n`.

     Therefore, we can use this.

     Now, we need to show that `((-a) ^ (p ^ n) : R) = - (a ^ (p ^ n))`.

     We can prove this by showing that `(-1 : R) ^ (p ^ n) = -1`, and then multiplying by `a ^ (p ^ n)`.

     To show `(-1 : R) ^ (p ^ n) = -1`, we can use that the Frobenius map on R is a ring homomorphism, so `(-1) ^ p = -1`, and then by induction.

     Alternatively, we can use that in R of characteristic p, the Frobenius map is injective (since R is a domain), but we don't need that.

     Let's prove `(-1 : R) ^ (p ^ n) = -1`:

     - We know that the Frobenius map `F : R → R` is a ring homomorphism, so `F (-1) = (-1) ^ p`.
     - But also, `F (-1) = -1` because F is a ring homomorphism and `F (-1) = - F 1 = -1`.
     - Therefore, `(-1) ^ p = -1`.
     - Then, by induction, `(-1) ^ (p ^ n) = -1`.

     However, we need to know that `F (-1) = -1`. This is true because F is a ring homomorphism, so it sends additive inverses to additive inverses: `F (-x) = - F x`. In particular, `F (-1) = - F 1 = -1`.

     Therefore, we can get `(-1) ^ p = -1` from the fact that the Frobenius map is a ring homomorphism.

     Then, by induction, `(-1) ^ (p ^ n) = -1`.

     In Lean, we can get that the Frobenius map is a ring homomorphism from `FrobeniusHom`.

     Specifically, we have `FrobeniusHom R p : R →+* R`.

     Then, `(FrobeniusHom R p) (-1) = -1` because it's a ring homomorphism.

     But `(FrobeniusHom R p) (-1) = (-1) ^ p`.

     Therefore, `(-1) ^ p = -1`.

     Then, we can prove by induction on n that `(-1) ^ (p ^ n) = -1`.

     Alternatively, we can note that the n-th iterate of the Frobenius map is also a ring homomorphism, so `(FrobeniusHom R p)^n (-1) = -1`, and `(FrobeniusHom R p)^n (-1) = (-1) ^ (p ^ n)`.

     Therefore, we can use the fact that the iterateFrobenius is a ring homomorphism to get that `(-1) ^ (p ^ n) = -1`.

     Since we have that `iterateFrobenius R p n` is a ring homomorphism (as the iterate of a ring homomorphism), we can use that to get `(-1) ^ (p ^ n) = -1`.

     Specifically, `iterateFrobenius R p n` is a ring homomorphism, so it sends `-1` to `-1`.

     But `iterateFrobenius R p n (-1) = (-1) ^ (p ^ n)`.

     Therefore, `(-1) ^ (p ^ n) = -1`.

     This is the simplest way.

     Therefore, we can use the fact that `iterateFrobenius R p n` is a ring homomorphism to get that `(-1) ^ (p ^ n) = -1`.

     Now, we have all the pieces to prove `(X - a)^(p ^ n) = X^(p ^ n) - a^(p ^ n)` in `R[X]`.

     Let's summarize the proof of this lemma:

     1. Show that `R[X]` has characteristic p.
        - Because R has characteristic p, and the characteristic of a polynomial ring over R is the same as that of R.
     2. Therefore, in `R[X]`, we have `(x + y) ^ (p ^ n) = x ^ (p ^ n) + y ^ (p ^ n)` for any x, y : R[X].
        - This follows from the fact that the Frobenius map on `R[X]` is a ring homomorphism.
     3. Take x = X and y = -C a.
        - Then, `(X - C a) ^ (p ^ n) = (X + (-C a)) ^ (p ^ n) = X ^ (p ^ n) + (-C a) ^ (p ^ n)`.
     4. Now, `(-C a) ^ (p ^ n) = C ((-a) ^ (p ^ n))` because the constant polynomial embedding is a semiring homomorphism.
     5. We have `(-a) ^ (p ^ n) = - (a ^ (p ^ n))` because:
        - The map `iterateFrobenius R p n : R →+* R` is a ring homomorphism.
        - Therefore, it sends `-1` to `-1`: `(-1) ^ (p ^ n) = -1`.
        - Hence, `(-a) ^ (p ^ n) = [(-1) * a] ^ (p ^ n) = (-1) ^ (p ^ n) * a ^ (p ^ n) = (-1) * a ^ (p ^ n) = - (a ^ (p ^ n))`.
     6. Therefore, `(-C a) ^ (p ^ n) = C (- (a ^ (p ^ n))) = - C (a ^ (p ^ n))`.
     7. Hence, `(X - a) ^ (p ^ n) = X ^ (p ^ n) - C (a ^ (p ^ n))`.

     Now, we can use this lemma in the proof of the key lemma.

     Let's now try to write out the proof in Lean using `have` statements.

     We'll use the following structure:

     ```
     theorem map_iterateFrobenius_roots_expand_eq {R : Type u_1} [CommRing R] [IsDomain R] {p n : ℕ} [ExpChar R p] [PerfectRing R p] (f : R[X]) :
         Multiset.map (⇑(iterateFrobenius R p n)) (roots ((expand R (p ^ n)) f)) = p ^ n • roots f := by
       have h_main : ... := by sorry
       sorry
     ```

     We need to fill in `h_main` and then the final step.

     However, since we are only asked to provide the remaining tactics, we need to start from the current state and provide tactics to close the goal.

     The current state is:

     ```
     R : Type u_1
     inst✝³ : CommRing R
     inst✝² : IsDomain R
     p n : ℕ
     inst✝¹ : ExpChar R p
     f : R[X]
     inst✝ : PerfectRing R p
     ⊢ Multiset.map (⇑(iterateFrobenius R p n)) (roots ((expand R (p ^ n)) f)) = p ^ n • roots f
     ```

     We need to prove this.

     Let's start by introducing some notation.

     Let `F : R →+* R := iterateFrobenius R p n`.

     Let `g : Polynomial R := expand R (p ^ n) f`.

     We know that `⇑F a = a ^ (p ^ n)`.

     We will prove the key lemma: `∀ a : R, Polynomial.orderOfRoot g a = p^n * Polynomial.orderOfRoot f (⇑F a)`.

     Then, we will obtain the inverse function `G : R → R` such that `F ∘ G = id` and `G ∘ F = id`.

     Then, we will show that `map G (p^n • roots f) = roots g`.

     Then, applying `F` to both sides gives `map F (roots g) = p^n • roots f`.

     Let's start by proving the key lemma.

     We'll need to use the factorization of f around `b = ⇑F a`.

     Step 1: Get `m = Polynomial.orderOfRoot f b`.

     Step 2: Since `(X - b)^m ∣ f`, we can write `f = (X - b)^m * h`.

     Step 3: Show that `h.eval b ≠ 0` using that `m` is the maximal order.

     Step 4: Prove that `(X - a)^(p ^ n) = X^(p ^ n) - b` where `b = ⇑F a`.

     Step 5: Then, `g = f.comp (X ^ (p ^ n)) = ((X - a)^(p ^ n))^m * (h.comp (X ^ (p ^ n))) = (X - a)^(p ^ n * m) * (h.comp (X ^ (p ^ n)))`.

     Step 6: Show that `(h.comp (X ^ (p ^ n))).eval a = h.eval b ≠ 0`, so its orderOfRoot at a is 0.

     Step 7: Conclude that `orderOfRoot g a = p ^ n * m`.

     Let's try to formalize this in Lean with `have` statements.

     We'll use `have` for each step and then combine them.

     However, since we are in a Lean proof, we need to actually provide the tactics.

     Given the complexity, it's better to use `have` statements with `sorry` and then use them to close the goal.

     Let's start:

     ```
     theorem map_iterateFrobenius_roots_expand_eq {R : Type u_1} [CommRing R] [IsDomain R] {p n : ℕ} [ExpChar R p] [PerfectRing R p] (f : R[X]) :
         Multiset.map (⇑(iterateFrobenius R p n)) (roots ((expand R (p ^ n)) f)) = p ^ n • roots f := by
       have h_F_bijective : Bijective (⇑(iterateFrobenius R p n)) := by sorry
       have h_key_lemma : ∀ (a : R), Polynomial.orderOfRoot (expand R (p ^ n) f) a = p ^ n * Polynomial.orderOfRoot f (⇑(iterateFrobenius R p n) a) := by sorry
       have h_G_exists : ∃ (G : R → R), (∀ b : R, ⇑(iterateFrobenius R p n) (G b) = b) ∧ (∀ a : R, G (⇑(iterateFrobenius R p n) a) = a) := by sorry
       have h_roots_g_eq : roots (expand R (p ^ n) f) = Multiset.map (fun a : R => Classical.choose (h_G_exists.1 a) (by sorry)) (p ^ n • roots f) := by sorry
       have h_final : Multiset.map (⇑(iterateFrobenius R p n)) (roots (expand R (p ^ n) f)) = p ^ n • roots f := by sorry
       exact h_final
     ```

     This is very sketchy. We need to fill in the details.

     However, since we are only allowed to provide the tactic block that completes the proof, and we cannot use `sorry`, we need to actually provide the proof.

     Given the complexity, it's likely that the intended solution uses a different approach, perhaps using the fact that the map `x ↦ x^(p^n)` is bijective and that the multiplicity is multiplied by p^n, and then using the multiset map property.

     Alternatively, perhaps there is a lemma in Mathlib that directly relates the roots of `f(X^{p^n})` to the roots of `f` when the Frobenius map is bijective.

     Let's search for relevant lemmas in Mathlib.

     There is a lemma: `Polynomial.map_roots` or something similar?

     Actually, there is `Polynomial.roots_map` which says that if `f : R →+* S` is a ring homomorphism, then the roots of `f.map p` are the preimages of the roots of `p` under `f`.

     But we have the opposite: we are mapping the polynomial variable, not the coefficients.

     There is also `Polynomial.roots_comp` which might be relevant.

     Let's look at `Polynomial.roots_comp`.

     In Mathlib, there is a lemma: `Polynomial.roots_comp` that says if `f` and `g` are polynomials, then the roots of `f.comp g` are the preimages under `g` of the roots of `f`, but with some conditions on `g`.

     Specifically, if `g` is not constant, then `a` is a root of `f.comp g` iff `g a` is a root of `f`.

     This is exactly what we need for the roots, but not for the multiplicities.

     The lemma is: `Polynomial.mem_roots_comp` which says `a ∈ (f.comp g).roots ↔ g a ∈ f.roots`.

     This is true when `g` is not constant, but in our case, `g = X^(p^n)` is not constant as long as p^n > 0, which it is since p is a prime and n is a natural number (but n could be 0? In the problem, n is a natural number, but if n=0, then p^n = 1, and the statement becomes trivial. However, we can assume n ≥ 0, and the statement still holds.)

     Actually, in the problem, n is a natural number, so n could be 0. If n=0, then iterateFrobenius R p 0 is the identity, and expand R 1 f = f, so the statement becomes `map id (roots f) = 1 • roots f`, which is true.

     For n ≥ 1, p^n ≥ p ≥ 2, so X^(p^n) is not constant.

     Therefore, we can use `Polynomial.mem_roots_comp` to get that `a` is a root of `g = f.comp (X^(p^n))` iff `F a = a^(p^n)` is a root of `f`.

     This gives us the set of roots, but not the multiplicities.

     To get the multiplicities, we need to use the fact that in characteristic p, the multiplicity is multiplied by p^n.

     There might be a lemma for the orderOfRoot of a composition.

     Let's search for `Polynomial.orderOfRoot_comp`.

     In Mathlib, there is a lemma: `Polynomial.orderOfRoot_comp` which says:

     ```
     theorem orderOfRoot_comp {R : Type*} [Semiring R] {f g : Polynomial R} {a : R} :
         g a = 0 → orderOfRoot (f.comp g) a = orderOfRoot f (g a) * orderOfRoot g a := ...
     ```

     Let's check if this exists.

     Actually, in `Mathlib.Polynomial.OrderOfRoot`, we have:

     ```
     theorem orderOfRoot_comp {R : Type*} [Semiring R] {f g : Polynomial R} {a : R} (hg : g a = 0) :
         orderOfRoot (f.comp g) a = orderOfRoot f (g a) * orderOfRoot g a := ...
     ```

     This is exactly what we need!

     Let's verify the conditions:

     - We have `f : R[X]` (our original f).
     - We have `g : Polynomial R` where `g = X^(p^n)`.
     - We have `a : R`.
     - The condition `g a = 0` is `(a : R) ^ (p ^ n) = 0`.
     - But in our case, we don't necessarily have `a^(p^n) = 0`. In fact, if `a^(p^n) = 0`, then since R is a domain, `a = 0`.

     However, the lemma requires `g a = 0` to conclude that `orderOfRoot (f.comp g) a = orderOfRoot f (g a) * orderOfRoot g a`.

     But in our case, we want to compute `orderOfRoot (f.comp g) a` for any a, not just those where `g a = 0`.

     If `g a ≠ 0`, then `a` is not a root of `g.comp f`? Wait, no: `f.comp g` is `f(g(X))`, and we are evaluating at `a`: `(f.comp g) a = f(g a)`.

     The lemma says that if `g a = 0`, then the orderOfRoot of `f.comp g` at `a` is the product of the orderOfRoot of `f` at `g a` and the orderOfRoot of `g` at `a`.

     But if `g a ≠ 0`, then we cannot directly use this lemma.

     However, note that if `g a ≠ 0`, then `f(g a)` is just some value, and the orderOfRoot of `f.comp g` at `a` is zero if `f(g a) ≠ 0`, and we need to compute it if `f(g a) = 0`.

     Actually, the lemma is only useful when `g a = 0`, i.e., when `a` is a root of `g`.

     But in our case, we want to relate the orderOfRoot of `f.comp g` at `a` to the orderOfRoot of `f` at `g a`.

     There is a more general lemma: `Polynomial.orderOfRoot_comp` without the condition `g a = 0`?

     Let's check the Mathlib documentation.

     Actually, I recall that there is a more general formula:

     `orderOfRoot (f.comp g) a = orderOfRoot f (g a) * orderOfRoot g a` if `g a` is a root of `f` or something? No.

     Wait, let's think: if we write `f(Y) = (Y - b)^m * h(Y)` with `h(b) ≠ 0`, then `f(g(X)) = (g(X) - b)^m * h(g(X))`.

     Then, the orderOfRoot of `f(g(X))` at `a` is `m * orderOfRoot (g(X) - b) a + orderOfRoot (h(g(X))) a`.

     Now, `orderOfRoot (h(g(X))) a` is zero if `h(g(a)) ≠ 0`, which is true if `h(b) ≠ 0` and `g(a) = b`.

     But if `g(a) ≠ b`, then `h(g(a))` could be zero or not, but we are interested in the case where `b` is a root of `f`, so we want to relate to the orderOfRoot of `f` at `b`.

     Actually, if we want to compute the orderOfRoot of `f.comp g` at `a`, we need to know the orderOfRoot of `g(X) - b` at `a` where `b` is such that `f(b) = 0` and the multiplicity of `b` in `f` is m.

     This is getting complicated.

     However, there is a lemma in Mathlib: `Polynomial.orderOfRoot_comp_of_mem_roots` which might be what we need.

     Let's assume that we can use the following approach:

     - For any a : R, let b = F a = a^(p^n).
     - Then, the orderOfRoot of g = f.comp (X^(p^n)) at a is equal to p^n times the orderOfRoot of f at b.

     This is exactly our key lemma.

     And we can prove it using the factorization method or using the `orderOfRoot_comp` lemma with some adjustments.

     Let's try to use the `orderOfRoot_comp` lemma by considering the polynomial `h(Y) = f(Y + b)`.

     Then, `f(Y) = h(Y - b)`.

     Therefore, `f(X^(p^n)) = h(X^(p^n) - b)`.

     Now, `X^(p^n) - b = (X - a)^(p^n)` by our lemma.

     Therefore, `f(X^(p^n)) = h((X - a)^(p^n))`.

     Now, we can use the `orderOfRoot_comp` lemma on `h` and `(X - a)^(p^n)`.

     Specifically, let `k(X) = (X - a)^(p^n)`.

     Then, `f(X^(p^n)) = h(k(X))`.

     Now, we want the orderOfRoot of `h(k(X))` at `a`.

     Note that `k(a) = 0`.

     Therefore, we can apply the `orderOfRoot_comp` lemma to `h` and `k` at `a`, since `k(a) = 0`.

     The lemma says: `orderOfRoot (h.comp k) a = orderOfRoot h (k a) * orderOfRoot k a = orderOfRoot h 0 * orderOfRoot k a`.

     Now, `orderOfRoot h 0` is the orderOfRoot of `h` at 0, which is the multiplicity of 0 as a root of `h`.

     But `h(Y) = f(Y + b)`, so `h(0) = f(b)`.

     The orderOfRoot of `h` at 0 is the largest m such that `Y^m` divides `h(Y)`, which is the same
```

**lean_error:** tail step 1/846 ('We need to prove that mapping the iterateFrobenius over the roots of (expand R (p^n)) f yields p^n • roots f.'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=302, out=514)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [roots_expand]
<;> simp [iterateFrobenius]
```

**lean_error:** tail step 1/2 ('rw [roots_expand]'): failed to synthesize instance

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.2s, verify 0.7s, in=1500, out=2546)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Polynomial.roots_expand_pow, coe_iterateFrobeniusEquiv,
    Multiset.map_nsmul, Multiset.map_map, Function.comp, RingEquiv.apply_symm_apply,
    Multiset.map_id']
```

**lean_error:** tail step 1/3 ('simpa [Polynomial.roots_expand_pow, coe_iterateFrobeniusEquiv,'): <stdin>:1:62: unexpected end of input; expected '*' or '-'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 26.3s, verify 0.1s, in=1502, out=2898)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
Multiset.map (⇑(iterateFrobenius R p n)) (roots ((expand R (p ^ n)) f)) = p ^ n • roots f := by
  have h1 : roots ((expand R (p ^ n)) f) = p ^ n • f.roots.map (iterateFrobeniusEquiv R p n).symm := by
    apply Polynomial.roots_expand_pow
  rw [h1]
  have h2 : Multiset.map (⇑(iterateFrobenius R p n)) (p ^ n • f.roots.map (iterateFrobeniusEquiv R p n).symm) = p ^ n • Multiset.map (⇑(iterateFrobenius R p n)) (f.roots.map (iterateFrobeniusEquiv R p n).symm) := by
    rw [Multiset.map_nsmul]
  rw [h2]
  have h3 : Multiset.map (⇑(iterateFrobenius R p n)) (f.roots.map (iterateFrobeniusEquiv R p n).symm) = Multiset.map ((⇑(iterateFrobenius R p n)) ∘ (iterateFrobeniusEquiv R p n).symm) (f.roots) := by
    rw [Multiset.map_map]
    <;>
    simp [Function.comp_apply]
  rw [h3]
  have h4 : (⇑(iterateFrobenius R p n)) ∘ (iterateFrobeniusEquiv R p n).symm = (fun x : R => x) := by
    funext x
    have h5 : ⇑(iterateFrobenius R p n) = ⇑(iterateFrobeniusEquiv R p n) := by
      rw [coe_iterateFrobeniusEquiv]
    rw [h5]
    -- Now we need to show that (⇑(iterateFrobeniusEquiv R p n)) ∘ (iterateFrobeniusEquiv R p n).symm = id
    have h6 : (⇑(iterateFrobeniusEquiv R p n)) ((iterateFrobeniusEquiv R p n).symm x) = x := by
      apply RingEquiv.apply_symm_apply
    exact h6
  rw [h4]
  have h5 : Multiset.map (fun x : R => x) (f.roots) = f.roots := by
    rw [Multiset.map_id']
  rw [h5]
  <;>
  simp [smul_eq_mul]
  <;>
  ring_nf
  <;>
  simp_all [Multiset.nsmul_eq_mul]
  <;>
  aesop

</think>
```

**lean_error:** tail step 1/34 ('Multiset.map (⇑(iterateFrobenius R p n)) (roots ((expand R (p ^ n)) f)) = p ^ n • roots f := by'): <stdin>:1:1: unknown tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 11.6s, verify 0.5s, in=1458, out=986)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Polynomial.roots_expand_pow]
rw [Multiset.map_nsmul]
rw [Multiset.map_map]
simp [coe_iterateFrobeniusEquiv, Function.comp_apply, RingEquiv.apply_symm_apply, Multiset.map_id']
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 17.6s, verify 1.3s, in=3151, out=2954)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Polynomial.roots_expand_pow (R:=R) (p:=p) (n:=n) (f:=f)]
  rw [Multiset.map_nsmul]
  rw [← coe_iterateFrobeniusEquiv]
  rw [Multiset.map_map]
  simp [Function.comp, RingEquiv.apply_symm_apply, Multiset.map_id']
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 42.4s, verify 0.3s, in=3230, out=4762)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Polynomial.roots_expand_pow]
rw [Multiset.map_nsmul]
rw [coe_iterateFrobeniusEquiv]
rw [Multiset.map_map]
have h : ⇑(iterateFrobeniusEquiv R p n) ∘ (iterateFrobeniusEquiv R p n).symm = id := by
  funext x
  rw [RingEquiv.apply_symm_apply]
rw [h]
rw [Multiset.map_id']
```

**lean_error:** tail step 3/9 ('rw [coe_iterateFrobeniusEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 8.5s, verify 0.5s, in=3125, out=710)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Polynomial.roots_expand_pow]
rw [Multiset.map_nsmul]
rw [Multiset.map_map]
simp [coe_iterateFrobeniusEquiv, Function.comp_apply, RingEquiv.apply_symm_apply, Multiset.map_id']
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.0s, verify 0.2s, in=2979, out=3174)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [roots_expand_pow, Multiset.map_nsmul, Multiset.map_map]
  simpa [Function.comp, coe_iterateFrobeniusEquiv, RingEquiv.apply_symm_apply,
    Multiset.map_id']
```

**lean_error:** tail step 2/3 ('simpa [Function.comp, coe_iterateFrobeniusEquiv, RingEquiv.apply_symm_apply,'): <stdin>:1:76: unexpected end of input; expected '*' or '-'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 63.9s, verify 0.4s, in=3435, out=7204)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Polynomial.roots_expand_pow]
rw [Multiset.map_nsmul]
rw [Multiset.map_map]
have h : (⇑(iterateFrobenius R p n)) ∘ (iterateFrobeniusEquiv R p n).symm = id := by
  funext x
  simp [Function.comp_apply]
  <;> rw [← coe_iterateFrobeniusEquiv]
  <;> simp [RingEquiv.apply_symm_apply]
rw [h]
rw [Multiset.map_id']
<;> simp [multiset_nsmul]
```

**lean_error:** tail step 4/11 ('have h : (⇑(iterateFrobenius R p n)) ∘ (iterateFrobeniusEquiv R p n).symm = id := by'): <stdin>:1:84: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 25.1s, verify 0.5s, in=3104, out=1364)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Polynomial.roots_expand_pow]
rw [Multiset.map_nsmul]
rw [Multiset.map_map]
simp [coe_iterateFrobeniusEquiv, Function.comp_apply, RingEquiv.apply_symm_apply, Multiset.map_id']
```

**final state (truncated):**
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
...
```
