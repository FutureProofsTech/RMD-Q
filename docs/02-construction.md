# 02 — Construction: UQ-KEM-v0 + UQ-SIG-v0 (NIST-shaped, conjectured)

Uses only FIPS 202 SHAKE/SHA3, integer arithmetic, no float. Pseudocode mirrors FIPS 203 Ch.5-7 and FIPS 204 Ch.5-7 shapes but with new `P` check.

## Notation

* `R_q`, `A`, `b`, `s`, `e`, `P` as in `00`.
* `encode(m)`: map 32B to `R_q` poly viaaj compress (`d_v` bits/coeff). `decode/compress/decompress` integer-only.
* `H = SHAKE256`, `XOF = SHAKE128`. Domain separation bytes: `0x01` KEM, `0x02` SIG, `0x00` matrix expand.
* `wt(), norm_inf()` checks enforce sparse-short.

## UQ-KEM-v0 (CPA-PKE + FO → CCA2 shape)

`KeyGen(seed)`:

1. Expand `A <- XOF(seed_A)`, `P <- XOF(seed_P)`.
2. Rejection-sample `s <- S` until `P(s)=0` (max `L=256` tries; else fail/restart seed).
3. Sample `e <- E`, `b = A*s + e`.
4. `pk = (seed_A, seed_P, b)`, `sk = (s, pk_hash)` where `pk_hash = H(pk)`.

`Encrypt(pk, m32, coins)`:

1. Expand `A,P` from seeds (recompute, do not trust input matrix).
2. Sample sparse `r <- S`, `e1,e2 <- E`.
3. `u = A^T*r + e1`, `v = b^T*r + e2 + encode(m32)`. Compress `u,v` with `du,dv`.
4. Return `ct = (u_c, v_c)`.

`Decrypt(sk, ct)`:

1. Decompress, `m' = decode(v - s^T*u)`, check `wt/norm` of intermediate within slack else fail.
2. FO re-encrypt check (CCA2 shape): recompute `Encrypt(pk, m', coins=H(m'||pk_hash))`, compare byte-wise in constant-time; if mismatch return `K = H(implicit_reject || ct)` (implicit rejection), else `K = H(m' || ct)`. Destroy `r,e1,e2` via zeroize (C backend; Python notes).

Correctness needs `||e^T*r - s^T*e1 + e2||_inf < q/4` with prob `1-delta`; measure `delta` in tests.

## UQ-SIG-v0 (Fiat-Shamir with aborts + MQ opening)

Key same as KEM (shared `s,P` allowed; separate seeds recommended for domain separation in prod).

`Sign(sk, msg)`:

1. `mu = H(H(pk) || msg)`.
2. Loop `attempt=0..R-1`:
   * Sample masking `y <- S_y` (larger bound `gamma`, sparse for light).
   * `w = A*y`, `py = P(y)` (sparse eval, skip zeros).
   * `c = H(mu || w_compressed || py || attempt)` interpreted as sparse challenge weight `tau` (like FIPS 204 `tau=39/49/60`).
   * `z = y + c*s` (polynomial mul by sparse `c`).
   * Rejection: if `||z||_inf >= gamma-beta` restart; if `wt(z)` too large restart.
   * Compute `P(z)` and check consistency: since `P(s)=0`, `P(z) = P(y) + c*DP_y(s) + c^2*P(s) = P(y) + c*DP_y(s)`. Prover also sends `h = DP_y(s)` linear opening (or its hash) so verifier can check without `y`. In v0 toy we send `py` + `h` explicitly (size unoptimized; compression deferred).
   * HARD REQUIREMENT (found by testing, 2026-09): `P` must be homogeneous-quadratic. With linear parts, `P(z) = P(y) + c*h + c^2*P_quad(s)` and the check fails unless `P_quad(s)=0` separately (toy sparsity masked this: both parts vanished by luck). `expand_mq`/planting emit quad-only systems; the opening asserts `vj != -1`.
   * If pass, output `sig = (c, z, h, py_hint)`.
3. Hedged variant: `y` derived from `H(sk_seed || mu || fresh_random)`; deterministic variant from `H(sk_seed || mu)` only. Document both.

`Verify(pk, msg, sig)`:

1. Expand `A,P`, check `||z||, wt(z)` bounds, `c` weight `tau`.
2. Recompute `w' = A*z - c*b` (should equal `A*y - c*e` ≈ `w` within slack).
3. Check `P(z) == py + c*h` (quadratic consistency, since `P(s)=0` term drops). Check `c == H(mu || w'_compressed || py || ...)`.
4. Accept iff all hold.

Security sketch (not proof): EUF-CMA needs forging `(z,c)` satisfying both lattice approx + quadratic consistency without `s`; zero-knowledge from rejection sampling + masking `y` hiding `s` (MLWE-style). Concrete analysis deferred to kill-phase.

## Sizes (unoptimized v0, to be measured)

* Toy: `pk ~ k*n*logq bits + seeds`, `ct ~ 2 polys`, `sig ~ z + c + h`. Prod sketch Cat1: target `pk ~1.2KB, ct ~0.8KB, sig ~2.5-3KB` — conjectured, must measure after C packing.

## Implementation notes

* No float, integer divide only.
* `P` eval must skip zero coeffs of `y/s` for speed on M4 later.
* Side-channel: v0 Python is variable-time; production C must add constant-time CBD, masked SHAKE, hedged signing (deferred, tracked as TODO).
