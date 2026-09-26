# Results: Constant-time posture and hygiene

> No formal timing proof exists (out of scope v0). What follows is measured.

## Timing inventory (`docs/04-ct-audit.md`)

| Component | Shape | Status |
|-----------|-------|--------|
| NTT butterflies (CT twins) | Masked adds/subs, Barrett-only | Branch-free; 0 sign-jumps |
| Basemul / accumulation | Barrett + masked | Branch-free |
| CBD sampling | Fixed loops, bit ops | Fixed-shape |
| Pack/unpack, Keccak | Fixed loops | Fixed-shape |
| Schoolbook mul/matvec (default) | Zero-skips | Variable-time (speed path) |
| Legacy sparse sampler | Sort-based | Retired (`-DRMDQ_NO_LEGACY`) |
| Python reference | Everything | Variable-time by design |
| Toy fallbacks (`%`, `if`) | Data-dependent | Toy-only, documented |

## Automated checks

- `make timing-smoke`: objdump scan — 0 sign-jumps in all 4 CT functions;
  reference twin still shows its jump (proves sensitivity).
- `make ct-test`: all KATs rebuilt branch-free, byte-identical outputs.
- `make strict`: strict-C90 + `-Wconversion -Wpedantic` clean (rmdq.c;
  fips202 needs C99 `uint64_t` — standard Keccak practice, documented).
- `make analyze`: GCC analyzer silent.
- ASan + UBSan: clean on all KAT binaries. valgrind: 0 errors
  (selftest, kem_fo, kem256).

## Costs

CT penalty 1.04–1.17× (measured). The CT-NTT is counterintuitively as fast
as the branching twin because the inverse table killed its `pow()` calls.

## Accepted residuals

Formal object-level proof (HOL-Light style), power/EM/fault analysis,
`>>31` shift semantics portability note, single-thread-only statics.
