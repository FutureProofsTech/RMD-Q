# Results: Decrypt-failure analysis

Correctness needs per-coefficient noise `< q/4 = 832`. Three evidence
lines; reproduce: `python3 ref/failure_exact.py`, `make -C c trials`.

## Exact distributions (convolution à la FIPS 203)

| Design | Per-KEM failure |
|--------|-----------------|
| Uncompressed, wt=64…256 | 2⁻⁹¹⁰ … 2⁻⁵¹² |
| Compressed (11,5) | 2⁻³⁸² |
| Compressed (10,5) | 2⁻²⁶⁹ |
| Compressed (10,4, Kyber-style) | **2⁻²³⁵** |

All far under the 2⁻¹³⁸ bar. Method notes: exact roundoff pmfs by
enumerating all `q` inputs (no modeling of compression noise); union bound
over n (valid upper bound despite cross-coeff correlation); sparse secrets
taken at worst-case full weight (conservative). An earlier loose bound
(Hoeffding 2⁻⁵³) and a pruning-massed variant were superseded — the exact
numbers above are current.

## Empirical trials (C harness, `c/trial_kem.c`)

| Batch | Trials | Failures | 95% CP upper |
|-------|--------|----------|--------------|
| Sparse, n=256 | 100,000 | 0 | ≈2⁻¹⁵ |
| CBD, n=256 | 100,000 | 0 | ≈2⁻¹⁵ |

Trials catch systematic bugs (which would show up fast); the analytic
distributions carry the rate argument. Both recorded honestly.

## Status

Uncompressed + compressed failure analysis DONE. Remaining: C-speed trials
at compressed settings (analytic says unnecessary; cheap to add), failure
analysis for any future parameter change (re-run the scripts).
