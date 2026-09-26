# Planted-P keygen (v2): design + leakage analysis

## Motivation

Toy keygen rejection-samples s until P(s)=0 for a random P. Success prob per
try ~ q^-t (exact: fraction of s with P(s)=0). At n=256/t=8/q=3329 this is
~2^-94 per try -- keygen never terminates. Planting (sample s, construct P
around it) always succeeds in O(t*m) time. Measured: n=256/t=8 keygen ~0.0s.

## Construction (ref/rmdq_planted.py)

Per equation: supports sampled independently of s (uniform vars, 25% linear,
as in expand_mq); free coeffs uniform over [0,q). Fix monomial on support(s)
(linear w.p. 1/2 else quadratic pair), coefficient solved as
c_fix = -rest * inv(eval) mod q, inserted at uniform slot. Two cases:

- **All free monomials vanish at s** (common: ~1/3 of equations at sparse
  params): the equation is pure uniform-random (supports+coeffs independent
  of s, no conditioning whatsoever). Padded to m terms with a vanishing
  linear term on a zero coordinate so no length signal exists.
- **Else**: resample free coeffs (bounded, 16 tries) until c_fix != 0, so
  every equation has exactly m nonzero terms.

## Uniformity argument

Given supports + s with at least one non-vanishing free monomial, the map
free-coeffs -> (rest, c_fix) makes coefficients uniform over the hyperplane
{c : <c,evals> = 0} minus the c_fix=0 slice (conditioning mass ~1/q,
negligible). Measured: fix-coeff chi2 = 17.4 on 209 samples over Z_17^*
(H0 mean 15) -- consistent with uniform. Fix positions spread over
support(s) (7 distinct coords over support-8 in toy probe).

## The spike finding (v1 -> v2)

v1 measured fix-coeff chi2 = 1302 (H0 mean 16): ~33-39% of equations had
c_fix = 0, because most random monomials vanish at sparse s (rest = 0).
Consequences analyzed:
- c_fix = 0 equations are pure-random (no planting signal) -- harmless alone.
- BUT term count m-1 vs m is publicly visible, and "all free monomials
  vanish at s" is a set of weak support clauses (linear terms pin zeros).
- v2 kills the length signal (resample-to-nonzero + pad pure-random to m).
- Residual accepted leakage: pad linear terms sit on zero coords (one-sided
  hint, same shape as ordinary 25%-linear free terms); coefficient
  conditioning on rest != 0 (mass ~1/q). Both logged as analysis items, not
  claimed away.

## Assumption statement (conjectured)

**Planted sparse-MQ**: given (A, b=A*s+e, P) with P from the planted
distribution above (t=8, m=12, sparse-short s), recover s. Differs from
random-MQ in that P is guaranteed a sparse-short root. Same family as
planted instances underlying MPCitH/code-based designs, but OUR sparse
support distribution is new and needs dedicated analysis: Gr\"obner with
planted structure, support-recovery attacks via vanishing patterns, and
lattice+MQ hybrid trade-offs (see docs/01-attack-catalog.md).

## Status

Proven: construction correct (P(s)=0 always), uniform fix coeffs (chi2),
end-to-end FO KEM roundtrip on planted n=256 key. NOT proven: hardness.
Kill-phase for planted distribution is the next cryptanalysis milestone.
