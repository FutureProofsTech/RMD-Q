# 05 — Signature (Fiat-Shamir v1, TOY STATUS)

STATUS: toy-only (n=16 KATs; n=256 Python roundtrip exists). NOT specified
for use. This section documents the mechanism as built, with its
limitations, so review can proceed.

## Mechanism (v1 dual opening)

Same keypair shape as KEM (shared `s`, `P`). To sign `msg`:
1. `mu = SHAKE256(0x02||"sig-mu"||pk_hash||msg)`.
2. Loop: sample masking `y` (dense uniform `[-gamma,gamma]`, fixed-shape);
   `w = A*y`, `py = P(y)`;
   `c_poly` = sparse weight-tau challenge from `SHAKE256(mu||w||py)`,
   `c_scalar` bound to the same hash (toy: `{1,2}` scalar);
   `z_lat = y + c_poly*s`, `z_mq = y + c_scalar*s`;
   `h` = bilinear opening with `P(z_mq) = py + c_scalar*h`;
   rejection on bounds; output `(c_*, z_*, h, w, py)`.
3. Verify: recompute `mu`, challenge binding, `w' = A*z_lat - c_poly*b`
   within slack of `w`, and `P(z_mq) == py + c_scalar*h`.

## Load-bearing restriction (found by testing)

`P` MUST be homogeneous-quadratic. With linear parts the opening identity
gains a `c^2*P_quad(s)` defect term and verification fails in general; toy
sparsity masked this (both parts vanished independently by luck). Enforced:
`expand_mq`/planting emit quad-only; opening asserts `vj != -1`.
Homogenization for affine use-cases (dummy `x_0=1`) is future work.

## Explicitly unspecified in v0.1

Prod challenge `(tau, gamma1, beta)` with size analysis; signature wire
sizes; Hedged-vs-deterministic policy beyond the existing variants;
rejection-rate analysis; C implementation at n=256 (Python only);
zero-knowledge property (no proof sketch yet).

## KAT references

- `tests/kat_sigv1_16.json` — full v1 vector incl. masking-`y` recompute
  (`c/sig_v1` byte-exact). `tests/test_sig256.py` — n=256 planted roundtrip
  (nightly, ~10 min).
