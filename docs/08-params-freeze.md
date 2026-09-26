# Params freeze v0: estimates, not claims

## Lattice core (ref/estimate_security.py, dual BKZ model)

Validation (same code, same model): ML-KEM-512 -> 2^115 cl / 2^104 qu
(published 2^118 / 2^107: within 3 bits); ML-KEM-768 -> 2^203 / 2^184
(published 2^183 / 2^166: +20 bits optimistic -- model scaling degrades
with N; stated tolerance).

Ours (lattice part only): k=2 -> 2^110 / 2^99; k=3 -> 2^196 / 2^178,
i.e. ~5-7 bits under the same-N Kyber reference IN THIS MODEL.

## Why this does NOT freeze params

1. **Hybrid/combinatorial attacks unmodeled.** Sparse secrets (wt=128/512)
   enable support-guessing hybrids (May/Kirshanova family). The BKZ model
   sees only per-coeff RMS (0.71 vs 1.0) and misses the combinatorial
   surface entirely. Real margin must come from hybrid analysis -- BLOCKING.
2. **Module structure ignored** (plain-LWE view; mildly attacker-favorable,
   standard first cut).
3. **Planted-MQ coupling unmodeled**: lattice estimates assume pure MLWE;
   the joint assumption could be weaker (MQ assists lattice) or stronger.
4. **768-point is 20 bits optimistic**: model needs full-estimator
   cross-check (fpylll-based) before any Cat mapping.
5. **Failure rate**: empirical 0/12 (CP upper only 2^-2.2 -- need C-speed
   trials for 2^-30+ evidence); analytic Hoeffding 2^-52.9/KEM, far from
   the 2^-138 bar (FIPS 203 Table 1 style). Exact failure distribution
   scripts (convolution à la FIPS 203 Thm 1) required.

## Freeze criteria (all must hold)

- [ ] Hybrid attack analysis with concrete exponents for (256,2,wt128).
- [ ] fpylll cross-check of dual/primal beta within 5 bits.
- [ ] Exact failure distribution <= 2^-128 (k=2) / <= 2^-160 (k=3).
- [ ] Planted-distribution kill-phase clean (docs/07 + ref/break_planted.py).
- [ ] MQ parameter rationale (t=8/m=12 vs Gröbner+hybrid at N=512).

Conclusion: NO category claims in v0. Numbers above are directional.
