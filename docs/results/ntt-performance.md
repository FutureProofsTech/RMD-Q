# Results: NTT and performance

Ring `(n,q) = (256,3329)` only (roots provably exist; schedule verified:
forward pairs equal direct CRT reduction, full multiply equals schoolbook).
Other params fall back to schoolbook automatically. Reproduce: `./c/bench`.

## Host x86-64, portable C, -O2 (fresh run)

| Op (n=256) | Schoolbook | NTT | Speedup |
|------------|-----------|-----|---------|
| Poly multiply | 51.0 µs | 4.2 µs | **12.1×** |
| Matrix-vector k=2 | 202.5 µs | 15.0 µs | **13.5×** |
| Matrix-vector, Ahat-hot | — | 17.6 µs/step context | ~20% steady-state |
| Full KEM (est.) | — | ≈ 0.25 ms | — |

CT twins: 1.04× (NTT) and 1.15–1.17× (schoolbook). CT-NTT being near-parity
is explained: the table killed the fast path's per-block `pow()`.

## Projected Cortex-M4 (static model, `ref/m4_cycles.py`)

PROD-256 k=2 KEM ≈ 1.6M cycles (~10 ms @168 MHz); k=3 ≈ 3.4M (~20 ms).
Schoolbook-only would be ~16M/98 ms. Model assumptions documented in-file;
M4 execution evidence is static only (no hardware on site).

## Stack (M4 target, `-fstack-usage`)

Primitive frames ≤ 56 B; matrix-vector ~1100 B (locals); NTT scratch 24 KB
shared static (was 60 KB per-function statics). Streaming schoolbook path
kept for tiny RAM. See [embedded](embedded.md).

## Correctness proof status (arithmetic only)

Barrett (MU=20158) exhaustively proven over all 11M products
(`./barrett_test`); NTT equivalence + roundtrip on LCG vectors
(selftest); ZINVW table verified (`pow(z,-1)` agreement, all 127).
