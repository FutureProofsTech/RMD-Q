# 07 — Evidence gap table

Each spec claim mapped to its evidence and review status. "Blocking" =
must resolve before the corresponding claim upgrades.

| # | Claim (where) | Evidence | Status |
|---|---------------|----------|--------|
| C1 | KEM correctness + failure rates (04) | `ref/failure_exact.py` (exact convolution; compressed variants); empirical 0-fail runs | PARTIAL: analytic done; C-speed trials + compressed KATs queued |
| C2 | FO mechanics (04) | `kat_fo16/cbd16`, `kat_kem256(+cbd)` green in C+Python incl. reject | DONE at KAT level |
| C3 | Toy breakability (02) | brute/MITM/LLL/Gröbner/msolve at calibrated scales | DONE (ongoing: harder engines welcome) |
| C4 | Hygiene (00) | ASan/UBSan/valgrind/M4/strict/analyzer/smoke; cross-impl KATs | DONE (re-run per change via `run_all.sh`) |
| C5 | Relative lattice estimates (02) | `ref/estimate_security.py` + fpylll 0.3% check | PARTIAL: N=768 optimism 20 bits; full-estimator cross-check queued |
| N2 | Reductions | — | BLOCKING: no proof sketches exist |
| N3a | Planted-MQ hardness | uniformity stats; n=16 fall / n=32+ stall; msolve curve | BLOCKING: needs degree-of-regularity study + stronger engines |
| N3b | Joint lattice+MQ | XL model (lattice binds in-model); joint demo at toy | BLOCKING: planted-structure-specific attacks unmodeled |
| N3c | Hybrid/hints/BKW | guessing optimum g=0; enumeration validated; perfect-hints curve | BLOCKING: hints-variants, BKW, quantum-walk unmodeled |
| N4 | Side channels | timing-smoke automated; CT twins equivalence-tested | BLOCKING: formal object proof; power/EM/fault out of scope v0 |
| N5 | Sig security | mechanism + toy KATs only | BLOCKING: everything (params, proofs, analysis) |
| Sizes | pk/ct/sig bytes (03) | measured pack + estimates; sig unpacked-conjectured | PARTIAL: packed Sig wire + M4 RAM diet (24KB bss noted) |

## Review guide (where to attack this spec)

1. `02-problem.md`: is planted-MQ well-posed? Attack the uniformity argument.
2. `04-kem.md`: FO transform soundness over the joint relation; implicit-reject edge cases.
3. `05-signature.md`: the dual opening; the homogeneity restriction — necessary and sufficient?
4. `ref/joint_hybrid.py`: XL counting assumptions; find a cheaper joint path.
5. `ref/estimate_security.py`: the 20-bit N=768 optimism — model bug or reality?
