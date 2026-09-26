# CT Audit (v0 — variable-time inventory + hardening plan)

Status: **NOT constant-time.** Research code with secret-dependent branches. Do not deploy.

## Inventory (c/rmdq.c, c/kem_fo.c sample_poly)

| Site | Leak | Severity |
|------|------|----------|
| `poly_mul[_stream]`: `if (a[i]==0) continue`, `if (b[j]==0) continue` | zero-skip branches + early cache timing on sparse secrets | HIGH — sparsity pattern leaks support |
| `mat_vec_mul_stream`: same skips propagated | same | HIGH |
| `kem_fo sample_poly`: `rb[i]%(2*eta+1)` is fine, but sparsify `sorted by rb` + `if (cnt>w)` + `keep` set | leaks weight + positions via timing | HIGH |
| `norm_inf/weight`: loops fixed n, no secret branch (comparisons only) | timing-safe shape, value leaks via return (by design — public checks) | LOW |
| `mq_eval`: `if (vj==-1)` on PUBLIC P structure | public, safe | OK |
| `pack/unpack`: fixed loops, shifts/masks only | safe shape | OK |
| Keccak: fixed 24 rounds, fixed loops | safe | OK |
| Python ref: everything variable-time (dict/set/sorted/random) | — | HIGH (prototype only) |

## Hardening plan (deferred to C v1, tracked)

1. Drop zero-skips: always execute `sum += a*b` with `a*b==0` naturally (cost: ~4x toy slowdown, required for prod). Gate with `RMDQ_CT=1` build flag.
2. Replace rejection/sort sparsify with verifiedCivil CBD + constant-time weight check (like mlkem-native `cbd.c` + `VALGRIND_MAKE_MEM_DEFINED` barriers against KyberSlash-style compiler folds). Toy sparse sampler stays test-only.
3. `sample_poly` selection: constant-time conditional moves (`cmov`) instead of `keep` branches.
4. Add `ct_test`: build with `-fsanitize` + valgrind `VALGRIND_MAKE_MEM_DEFINED` declassification harness (as mlkem-native does) — deferred until v1 sampler lands.
5. Python stays non-CT forever; C is the hardened path.

## What changed this phase (CBD sampling)

* FO encrypt randomness (`r`, `e1`, `e2`) + keygen error `e` now have a CBD
  path (`cbd=True`): dense CBD(eta) via `cbd_poly`/`rmdq_cbd`, fixed-shape
  loops, bit-identical C/Python (`kat_fo_cbd16.json` green in `kem_fo`).
  C n=256 encaps (`kem256.c`) samples via CBD (128B rb) or legacy sparse
  (512B rb) per KAT flag; both cross-checked byte-exact with full decaps.
* `sample_poly` legacy branch (kept for old KATs only): now a thin wrapper
  over shared stable-sort `rmdq_sample_sparse_rb` (proven == Python via
  ctypes at n=16 AND n=256).
  Sparse secrets `s` stay sparse (load-bearing for the RMD-Q assumption);
  dense errors only widen the MLWE margin (failure rate re-measured: 0/6
  FO failures at n=256 for w=32/64).
* Legacy sparse sampler kept for old KATs, demoted to test-only.
* **Retired (this round):** `-DRMDQ_NO_LEGACY` compiles out
  `rmdq_sample_sparse_rb` and both sparse FO branches; `make no-legacy-test`
  proves the hardened-only build passes everything (selftest, CBD FO, Sig
  verify incl. masking-y recompute, CBD KEM256, pack, CBD, Barrett).
  Sparse KATs exit 2 with `SKIP legacy sparse sampling (retired)`.
* Remaining variable-time sampling: Sig masking `y` (v0/v1 Python) and C
  `sample_poly` legacy branch (kept for old KATs); n=256 C encaps
  (512B-rb sampling generalization) is next.

* `rmdq_poly_mul_ct` + `rmdq_mat_vec_mul_ct` landed (56B frames), `RMDQ_MUL`/`RMDQ_MATVEC` dispatch macros, `make ct-test` builds all KATs branch-free — outputs byte-identical (`ct-test` passes same vectors). Cost 1.15-1.17x (`c/bench`).
* `rmdq_cbd` (Kyber-style, fixed loops, 48B frame) landed with selftest vectors (0x03→2, 0x0C→15 mod 17, all-ones→0). Sparse sort-sparsify stays test-only; prod path = dense CBD.
* Callers switched to `_stream` (same outputs, 37-38x less stack).
* Packing wired into FO KAT + packed-decaps path (7-bit roundtrip + unpack→decrypt match) — pack/unpack loops are fixed-count, CT-safe shape.
* Core size (Os): rmdq 2.6KB + fips202 1.3KB = ~3.9KB crypto. No malloc/float. rmdq.c strict-C90+Wconversion+fanalyzer clean; fips202.c needs C99 uint64 lanes (standard Keccak practice, M4-OK). No arm-gcc/ASan-runtime/valgrind on host — M4+dynamic validation static-only until toolchains available.
