# Results: Key Encapsulation Mechanism

Scope: FO-KEM over RMD-Q CPA-PKE at `(n,q,k) = (256,3329,2)` (+ toy scales).
Reproduce: `bash run_all.sh` (regenerates KATs, runs all cross-checks).

## Functional results

| Check | Result |
|-------|--------|
| Toy CPA roundtrip (n=16) | Pass (`tests/test_toy.py`) |
| Toy FO encaps/decaps/reject, sparse + CBD | Pass (`tests/test_kem_sig.py`, `tests/test_kem_cbd.py`) |
| n=256 FO, full 32B message, sparse + CBD | Pass (`tests/test_kem256.py`, `tests/test_kem_cbd.py`) |
| Tampered ct → implicit reject, K mismatch | Pass, all paths |
| C/Python byte-equivalence (expand, sample, ct, K, reject-K) | Pass on `kat_toy16`, `kat_fo16`, `kat_fo_cbd16`, `kat_kem256`, `kat_kem256_cbd` |
| Compressed (10,5) FO, 800B ct, both paths | Pass (`tests/test_kem_compressed.py`); C codec byte-exact (`kat_compress.json`) |
| Decrypt failures, all trial runs | 0 (see [failures](failures.md)) |

## Sizes (k=2, bytes)

| Object | Uncompressed (12-bit pack) | Compressed (10,5) |
|--------|---------------------------|-------------------|
| pk (`seed_A`, `seed_P`, `b`) | ~800 | ~700 |
| ct (`u`, `v`) | ~1150 (768+384) | **800** |
| sk sparse (`s` + seeds) | ~250 | ~250 |

Estimates from `ref/sizes_stack.py`; KAT-measured pack sizes match.
k=3 scales ~1.5× (see `docs/05-ntt-speedup.md`).

## Performance

Full KEM ≈ 0.25 ms host x86-64 portable C (NTT path); ≈1.6M M4 cycles
projected. See [performance](ntt-performance.md). Sampling dominates at
toy scale; NTT-domain matrix caching saves ~20% steady-state (`c/bench`).

## Limitations (honest)

- Ciphertexts carry no MQ opening in v0.1 (jointness lives in keygen).
- Compressed wire proven in Python + C codec only; no compressed C-FO yet.
- `pk_hash` uses truncated-byte serialization in toy paths (consistent, not canonical).
