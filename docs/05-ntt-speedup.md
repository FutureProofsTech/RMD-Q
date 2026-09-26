# NTT speedup (v1 backend, q=3329 n=256 only)

## What was slow

Schoolbook negacyclic mul: O(n^2) = 65k mult-adds per multiply at n=256, each
with data-dependent zero-skips (fast but leaky) or branch-free (1.15x cost).
Full KEM projected ~16M M4 cycles (~98ms) — feasible but ~15x off ML-KEM pace.

## What changed

Standard 7-layer DIT NTT for this exact ring (X^256+1, q=3329), the same
transform shape standardized implementations use for ML-KEM. **Our novelty
remains the RMD-Q cryptosystem, not the arithmetic**: ring arithmetic for a
given ring is standard practice (like using SHAKE). Everything re-derived and
independently verified:

1. `ref/ntt_gen.py` proves: forward pairs == direct CRT reduction mod
   (X^2-Z[i]) with odd-power moduli Z[i]=w^e (negacyclic proof), inv(fwd)==id,
   ntt-mul==schoolbook (5 trials). Tables emitted by script, never hand-copied.
2. `c/ntt.c` + `c/ntt_tables.h`: independent C implementation; selftest proves
   equivalence vs schoolbook on LCG vectors + fwd/inv roundtrip.
3. Barrett q=3329 (MU=20158): **exhaustively** proven over all 11M products
   (`./barrett_test`), max 1 correction.
4. `c/bench`: n=256 mul 48.6→7.5us (**6.0x**), mat-vec k=2 182.9→20.9us (**8.8x**).

## New numbers

- M4 projection (static count): PROD-256 k=2 KEM ~1.6M cycles (~10ms), k=3 ~3.4M (~20ms).
- Cost: NTT path needs ~2KB scratch (static buffers; single-threaded) vs O(1) streaming schoolbook. Speed-optimized vs RAM-optimized backends coexist; q!=3329 or n!=256 falls back to schoolbook automatically. M4 bss reality: ntt.o carries 60KB static scratch (Ahat/shat/ohat twins) -- fine on host, too fat for small MCUs; streaming path is the embedded story until buffers are shared/caller-provided.
- Ahat update: precompute measured, not just planned -- hot 25.6us vs cold 32us (~20%; pointwise+inverse dominate).
- Remaining CT gap (CLOSED this round, see below): butterfly `if (x<0)`
  adjusts + `%` in basemul were data-dependent.

## Still to do (speed)

- Precompute Ahat (NTT-domain matrix) to skip k^2 forward transforms per op.
- M4 DSP assembly only after portable C is frozen.

## CT-NTT (landed)

Branch-free twins `rmdq_ntt_fwd_ct/inv_ct`, `rmdq_poly_mul_ntt_ct`,
`rmdq_mat_vec_mul_ntt_ct`: masked adds/subs, Barrett-only reduction,
precomputed `RMDQ_ZINVW` table (also removed the `pow()`-per-block crutch,
which is why CT is FASTER: 3.8us vs 7.3us fast-path).
- Equivalence: selftest proves CT == branching on LCG vectors (fwd, inv,
  roundtrip, mul, matvec) + `make ct-test` runs the full n=256 KEM
  cross-check under `-DRMDQ_NTT=_ct -DRMDQ_MATVEC_NTT=_ct` byte-identical.
- Objdump smoke (x86_64 -O2): CT fwd contains no sign-test jumps (`js/jns`
  absent); remaining conditionals are fixed-trip loop back-edges
  (secret-independent by construction). The branching twin retains one `js`
  on a reduce adjust. Smoke only, not a proof; formal object-level check
  (HOL-Light style) is out of scope for v0.
- Caveats: `>>31` arithmetic shift is implementation-defined (universal on
  gcc/x86_64+ARM, equivalence-tested); toy fallback path in `_ct` matvec
  still uses `%`+`if` (toy-only, documented); static scratch buffers are
  single-thread-only.
