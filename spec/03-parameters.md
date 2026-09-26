# 03 — Parameter sets (frozen v0.1)

`w` = per-polynomial weight bound (`W_total = k*w`). `B_e` = residual slack.

| set | n | q | k | eta | w/poly | eta_e | t | m | wire | purpose |
|-----|---|---|---|-----|--------|-------|---|---|------|---------|
| TOY-16 | 16 | 17 | 1 | 1 | 4 | 1 | 2 | 4 | raw | brute-force seconds; sig toy |
| TOY-32 | 32 | 97 | 1 | 1 | 6 | 1 | 3 | 6 | raw | MITM/Gröbner calibration |
| PROD-256 | 256 | 3329 | 2 | 2 | 128 | 2 | 8 | 12 | 12-bit | primary target; KATs green |
| PROD-384 | 256 | 3329 | 3 | 2 | 160 | 2 | 10 | 12 | 12-bit | estimates only; NO KATs yet |

## Per-column rationale

- `n=256, q=3329`: THE standard lattice ring (same as ML-KEM/FIPS 203) --
  chosen deliberately for NTT reuse, mature cryptanalysis of the ring
  itself, and implementation comparability. Novelty is claimed ONLY for the
  joint assumption and constructions, never the arithmetic.
- `k=2/3`: module rank; scales dimension N=512/768 matching ML-KEM-512/768
  for apples-to-apples comparison.
- `eta=2`, `eta_e=2`: CBD-standard noise levels (Kyber-compatible margins).
- `w=128 (k=2)`: total weight 256 = the hybrid-analysis recommendation
  (docs/09): closes the 5-bit model gap to the Kyber reference at ~zero
  size cost. Aligned in KATs/tests 2026-09-25 (was 64; KAT churn logged).
  `w=160 (k=3)`: same density class; analysis pending (flagged).
- `t=8/m=12 (k=2)`: MQ load; Gröbner scaling (0.3s@16, 180s@24) and XL
  infeasibility at prod support this shape; degree-of-regularity study open.
- Wire `12-bit`: lossless packing (sizes: pk ~0.8KB, ct ~0.8/1.1KB,
  sig ~2.0/2.7KB unpacked-conjectured). Compressed `(10,5)` analyzed
  (2^-268.6 exact) but not wired.

## What is NOT specified here

Sig prod parameters (challenge tau/gamma1/beta with size analysis),
compressed wire formats, KATs for PROD-384 (partial), any security category
mapping. See 07 for the blocking list.
