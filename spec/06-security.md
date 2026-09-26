# 06 — Security: claims made here, and claims NOT made

## Claimed (with evidence pointers to 07)

- C1. KEM CPA-decrypt correctness at PROD-256 with stated failure rates
  (exact distributions computed; empirical zero-failure runs).
- C2. FO-KEM mechanics: determinism, re-encrypt check, implicit rejection
  (byte-exact KATs both paths).
- C3. Toy instances are breakable as predicted (brute force, MITM, LLL,
  Gröbner, msolve all demonstrated at calibrated scales).
- C4. Implementation hygiene properties actually tested: memory safety
  (ASan/UBSan/valgrind clean), KAT determinism, cross-implementation
  byte-equivalence (C vs Python on all vectors), strict warnings + analyzer
  silence, timing-smoke (no sign-jumps in CT paths).
- C5. Relative lattice estimates (dual-BKZ model validated within 3 bits
  on ML-KEM-512; ours ~5-7 bits under same-N reference in-model).

## Explicitly NOT claimed

- N1. NO NIST security category. No Cat 1/3/5 mapping is made or implied.
- N2. NO reductionist proof (no ROM/QROM proof for FO-KEM or Fiat-Shamir
  over RMD-Q; proof sketches do not exist yet).
- N3. NO certification of the RMD-Q or planted-MQ assumptions. They are
  conjectures with model-level support and calibrated toy evidence only.
- N4. NO side-channel resistance beyond what's measured (timing-smoke on
  CT paths; no power/EM/fault analysis; no formal object-level proof).
- N5. NO signature security claim at any level (toy mechanism only).
- N6. NO deployment readiness (no audit, single-threaded statics, Python
  reference is variable-time by design).
- N7. Numbers from simplified models (BKZ asymptotics, XL counting,
  Hoeffding bounds) are DIRECTIONAL, not guarantees; tolerances stated
  where validated (3-bit at 512, 20-bit optimism at 768).
