# 00 — RMD-Q Problem Definition (v0, conjectured)

## Ring and distributions

* `R_q = Z_q[X]/(X^n+1)`, prod `n=256`, toy `n=16,32`. `q` prime NTT-friendly: prod candidates `3329, 7681`; toy `17, 97, 3329`.
* Module rank `k`: prod `2/3/4`, toy `1/2`.
* Secret distribution `S(eta,w)`: each coefficient of `s in R_q^k` sampled from centered binomial / uniform `[-eta,eta]`, then sparsified to Hamming weight `<= w` per polynomial (rejection). Sparse => light encode + fast mult (skip zeros) + integer-only.
* Error distribution `E(eta_e)`: coefficients in `[-eta_e, eta_e]`.
* Matrix `A in R_q^{k x k}` derived deterministically via `SHAKE128(seed_A || i || j)` interpreted as uniform polys (FIPS 202 only).
* MQ system `P: R_q^k -> R_q^t`: `t` sparse quadratic equations over `Z_q` in the `N = k*n` variables of `s`. Each equation uses `<= m` monomials (`m ~ 8-16` for light), coefficients uniform via `SHAKE128(seed_P)`. `P` is public, system is random-looking but sparse for speed. Toy: `t=2-4, m=4-6`.

Deterministic expansion via SHAKE only. RNG for secrets: SP 800-90-style DRBG abstracted as `randombytes()` in ref; Python uses `os.urandom` for prototype (documented, not validated).

## Generation

`RMDQ.Gen(n,q,k,eta,w,eta_e,t,m,seed)`:

1. Expand `A <- SHAKE128(seed_A)`, `P <- SHAKE128(seed_P)`.
2. Sample `s <- S(eta,w)`, `e <- E(eta_e)` with `s` conditioned on `P(s)=0` (rejection sampling at keygen; abort after `L` tries, else restart seed — failure rate analyzed separately).
3. Compute `b = A*s + e in R_q^k`.
4. Output instance `x = (A,b,P)`, witness `s`.

Note: conditioning `P(s)=0` is part of Gen; density of solutions tuned so KeyGen succeeds with prob `p_gen >= 2^-8` for prod (retry), `p_gen` higher for toy by choosing `t` small.

## Search problem

**Search-RMD-Q**: given `x=(A,b,P)`, find `s'` such that:

* `||s'||_inf <= eta` and `wt(s') <= w` (sparse-short),
* `||A*s' - b||_inf <= B_e` (bounded residual, `B_e = eta_e + slack`),
* `P(s') = 0` exactly over `Z_q`.

## Decision problem

**Decision-RMD-Q**: distinguish `(A, b=A*s+e, P)` with `P(s)=0` from `(A, u uniform, P)` where `P` independent of `u`, for `A,P` uniform as above. Advantage must be negligible for secure params. Decision underlies KEM IND-CPA sketch.

## Why conjectured hard (informal, to be tested)

* Lattice-only solver finds many short `s'` with `A*s'≈b` but violates `P(s')=0` with prob `~1 - q^-t` per random candidate; MQ filter kills pure lattice forgeries.
* MQ-only solver finds many `P(s')=0` roots but violates noisy linear bound; linear part hides which root is keyed (adds `q^{k*n}` search with noise).
* Joint solver must satisfy both simultaneously: best known generic is hybrid — lattice sieving to enumerate short candidates + Gröbner/linearization check per candidate, or algebraic-lattice tradeoff. No Shor structure: `A` random module (no ideal trapdoor), `P` random sparse (no oil/vinegar structure on purpose to avoid wedge attacks). Grover gives at most quadratic speedup on brute-force weight search (`sqrt(C(N,w)*(2*eta+1)^w)`).
* Reductions (sketch, not proof): Search-RMD-Q => MLWE search if MQ oracle ignored with `q^-t` loss; Search-RMD-Q => random MQ if lattice bound ignored. No tight reduction claimed in v0 — open.

## Quantum resistance argument (heuristic)

* No hidden subgroup / period structure for Shor: module matrix random, MQ random sparse.
* Grover: brute-force over sparse-short space `S = C(k*n, w)*(2*eta+1)^w`; quantum cost `~sqrt(S)` + polynomial check. Params chosen so `sqrt(S) >= 2^cat` with margin.
* BKZ quantum speedup (if any) assumed at most low polynomial per NIST PQC practice; we add 15-bit margin in prod estimates (to be calibrated by kill-phase).

## Toy vs prod

* Toy (`n=16,k=1,eta=1,w=4,t=2,q=17`): `|S| ~ 2^20`, brute-forceable in seconds for calibration.
* Prod sketch (`n=256,k=2,eta=2,w=64,t=8,q=3329`): `|S| ~ 2^400+`, conjectured Cat1 — must survive kill-phase before any claim.
