# 01 — Notation and primitives

## Ring

`R_q = Z_q[X] / (X^n + 1)` with `n` a power of two, `q` prime. Elements are
polynomials of degree < n with coefficients in `{0, ..., q-1}`. `R_q^k`
denotes k-vectors of such polynomials. Matrix-vector multiplication and the
NTT backend (`c/ntt.c`, valid only for `(n,q) = (256,3329)`) follow
`../docs/05-ntt-speedup.md`.

## Distributions

- `S(eta, w)`: sparse-short. Each polynomial has at most `w` nonzero
  coefficients, each uniform over `[-eta, eta] \ {0}`-ish (reference:
  uniform over `[-eta, eta]` then sparsified to weight `w`;
  `ref/rmdq_toy.py::sample_sparse_poly`). Secret distribution (load-bearing
  for the assumption).
- `CBD(eta)`: centered binomial, Kyber-style fixed-shape sampling
  (`ref/rmdq_toy.py::cbd_poly`, `c/rmdq.c::rmdq_cbd`). Error/encryption
  randomness (standard MLWE noise).
- `U(Z_q)`: uniform. Matrix `A` expansion.

## Symmetric primitives (only these)

- `SHAKE128`, `SHAKE256` (FIPS 202; `c/fips202.c`, vendored Keccak).
- Domain separation bytes: `0x00||"kem-a"` matrix expand,
  `0x01||"kem-coins"` / `0x01||"kem-shared"` FO, `0x02||"sig-*"` signatures,
  `"reject"` implicit-rejection. Exact byte layouts are defined by the
  reference code and pinned by KATs (any deviation fails cross-checks).

## Encoding

- `encode(m)`: 32-byte message to one `R_q` polynomial, bit `i` (little-endian
  bit order over the 32 bytes, `n` bits used) maps to coefficient `q//2`
  (bit 1) or `0` (bit 0).
- `decode`: per-coefficient nearest of `{0, q//2}` (distancedecide); first
  `n` bits packed little-endian. Correct iff per-coeff noise `< q/4`.
- `pack/unpack(bits)`: little-endian bit packing of coefficient vectors
  (`rmdq_pack/unpack`, cross-checked at 4/7/10/12-bit widths).
- Wire format v0.1: UNCOMPRESSED (12-bit packing, lossless since q < 4096).
  Compressed `(du,dv)` options are analyzed (`ref/failure_exact.py`) but NOT
  wired into KATs.

## Norms and checks

- `||·||_inf`: centered representatives in `[-(q-1)/2, (q-1)/2]`.
- `wt(·)`: Hamming weight (number of nonzero coefficients).
- Rejection sampling follows Dilithium shape (abort on bound violation;
  attempt counts vary by design and leak nothing under standard analysis --
  analysis itself open, see 07).
