# 04 — Key encapsulation mechanism (FO-KEM over RMD-Q CPA-PKE)

Shape mirrors FIPS 203 (CPA-PKE + Fujisaki-Okamoto => IND-CCA2) with the
RMD-Q relation `(A, b=A*s+e, P(s)=0)` as the trapdoor. The MQ part `P`
participates in keygen (joint key) and domain separation; ciphertexts carry
no MQ opening in v0.1 (documented limitation, not a security argument).

## Algorithms

`KeyGen(seeds)`:
1. Expand `A <- SHAKE128(0x00||"kem-a"||seed_A||i||j)`.
2. Sample `s <- S(eta,w)^k`; plant `P` around `s` (`plant_mq`, 02);
   sample `e <- CBD(eta_e)` (hardened path; legacy sparse in toy KATs).
3. `b = A*s + e`. `pk = (seed_A, seed_P, b)`,
   `sk = (s, pk_hash, sigma)` with `pk_hash = SHAKE256(pk_bytes||seeds)`,
   `sigma` = implicit-reject seed. Expanded form stores `b` (768B at k=2).

`Encaps(pk)`:
1. `m <- {0,1\}^256` (32 bytes; toy n<256 uses `(n+7)//8` bytes, tail zero).
2. `coins = SHAKE256(0x01||"kem-coins"||m||pk_hash)`;
   `r <- CBD(eta)`, `e1,e2 <- CBD(eta_e)` from `coins` (deterministic).
3. `u = A^T*r + e1`, `v = b^T*r + e2 + encode(m)` (NTT path at n=256).
4. `ct = (u, v)` (12-bit packed wire), `K = SHAKE256(0x01||"kem-shared"||m||ct)`.

`Decaps(sk, ct)`:
1. `m' = decode(v - s^T*u)`; re-encrypt with derived coins; byte-compare.
2. Match: `K = SHAKE256(...m'...||ct)`; mismatch: `K = SHAKE256("reject"||sigma||ct)`
   (implicit rejection; all intermediate buffers zeroized in C backend --
   audited by inspection only, see 07).

## Correctness condition

`||e^T*r - s^T*e1 + e2||_inf < q/4` per coeff. Exact failure distribution:
2^-910..2^-512 per-KEM uncompressed across wt (ref/failure_exact.py);
2^-268.6 at (du,dv)=(10,5); 2^-235.4 at (10,4). Empirical: 0 failures in
all trial runs (weak evidence; C-speed trials queued, 07).

## KAT references (all green, cross-checked C/Python byte-exact)

- `tests/kat_toy16.json` — CPA toy (schoolbook).
- `tests/kat_fo16.json` / `kat_fo_cbd16.json` — full FO incl. reject K.
- `tests/kat_kem256.json` / `kat_kem256_cbd.json` — n=256 sparse+CBD:
  expansion, NTT `b`, NTT decrypt, 12-bit pack, encaps recompute, K,
  decaps, reject. C programs: `c/kem_toy`, `c/kem_fo`, `c/kem256`.
