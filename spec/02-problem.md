# 02 — The RMD-Q problem (conjectured)

## Informal statement

Find a sparse-short `s` satisfying BOTH a noisy linear relation AND a
quadratic constraint over the same variables. Neither a pure lattice
decoder nor a pure MQ solver suffices alone -- that jointness IS the
assumption. Security analysis status: models only, see 06/07.

## Formal: Search-RMD-Q

Parameters `(n, q, k, eta, w, eta_e, t, m)` per 03. Let `N = k*n`.

- `Gen`: sample `A <- U(R_q^{k x k})` (via SHAKE128),
  `s <- S(eta, w)^k`, `e <- noise(eta_e)`,
  `P <- MQ(t, m)` (distribution below), conditioned on `P(s) = 0`;
  `b = A*s + e`. Output instance `x = (A, b, P)`, witness `s`.
- `Search`: given `x`, find `s'` with `wt(s') <= k*w`, `||s'||_inf <= eta`,
  `||A*s' - b||_inf <= B_e`, and `P(s') = 0` exactly.
- `Decision`: distinguish `(A, A*s+e, P)` from `(A, u uniform, P)`.

## The MQ distribution (planted, v2)

`P` is NOT uniform-random (rejection keygen cannot terminate at scale:
success prob ~q^-t). Instead `plant_mq` (`ref/rmdq_planted.py`): sample `s`
first, then per equation sample `m-1` free terms (uniform supports and
coefficients over `[0,q)`) plus one fix monomial on `support(s)` with solved
coefficient, inserted at a uniform slot; resample-until-nonzero with a
pure-random escape hatch (all-free-monomials-vanish case, which is then
exactly uniform-random). Homogeneous-quadratic ONLY (no linear terms --
load-bearing for the signature opening identity, see 05).

Uniformity evidence: fix coefficients chi2 = 17.4 on 209 samples over
Z_17^* (H0 mean 15); positions spread over support(s). Full analysis and
accepted residual leakages: `../docs/07-planted-keygen.md`.

## Hardness posture (conjectured, see 06)

- No Shor structure (random module matrix, random sparse MQ).
- Grover at most quadratic on the `C(N,w)*(2*eta+1)^w` sparse space.
- Lattice leg: dual-BKZ model validates within 3 bits on ML-KEM-512;
  ours ~5-7 bits under same-N reference in-model (docs/08).
- Hybrid guessing: optimum g=0 at all tested densities (docs/09).
- Joint XL model: MQ subsystem contributes negligibly at prod scale
  (docs/09). Planted-structure-specific attacks: UNANALYZED (blocking).
