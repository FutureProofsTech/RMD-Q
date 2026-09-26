# Results: Signatures (v1, toy status)

> This primitive is a research mechanism, not a specified scheme.
> No security level is claimed. See `spec/05-signature.md`.

## What exists and passes

| Check | Result |
|-------|--------|
| Toy sign/verify + tamper reject (n=16, scalar challenge) | Pass (`tests/test_kem_sig.py`) |
| v1 dual opening + challenge binding + MQ check (n=16) | Pass, Python + C byte-exact (`kat_sigv1_16.json`) |
| Masking-`y` recompute in C | Byte-exact (`c/sig_v1`) |
| n=256 planted-key roundtrip (nightly, ~10 min) | Pass (`tests/test_sig256.py`) |

## Key finding (found by testing)

The MQ opening identity `P(z) = P(y) + c·h` is **false** for systems with
linear parts (leftover `c²·P_quad(s)` defect). Toy sparsity masked it (both
parts vanished independently by luck). Consequence: all MQ is
homogeneous-quadratic by design; the opening asserts `vj != -1`.
Documented in `spec/02-problem.md`, `spec/05-signature.md`.

## Sizes (unpacked, conjectured)

k=2: sig ≈ 1.7–2.0 KB (dual openings unoptimized). Packing the signature
wire format is open work.

## Explicitly unspecified

Prod challenge `(tau, gamma1, beta)` with size analysis, hedged policy,
rejection-rate analysis, n=256 C code, zero-knowledge property, and any
security claim. See `spec/07-evidence.md` row N5.
