# Results: Kill-phase cryptanalysis log

Methodology: every attack is tried at calibrated toy scale first — it must
either break the toy (proving the methodology bites) or stall with measured
scaling. Reproduce: scripts in `ref/break_*.py`, `ref/grobner_*.py`,
`ref/msolve_*.py`, `c/mitm_toy32` (`make mitm-test`).

## Outcomes table

| Attack | Scale | Result |
|--------|-------|--------|
| Brute force, sparse space | TOY-16 | **Break, 172 tries**, exact key |
| MITM, noiseless | TOY-32 | **Break, 117 probes** (proves noise essential) |
| MITM full, noisy | TOY-32 | **Break, 23.35M checks** exact key in C |
| MITM pruned | TOY-32 noisy | Stalls (best residual 33/400k — need ≤2) |
| Hill-climb | TOY-32 noisy | Stalls at residual ~38–42 |
| LLL+Babai | TOY-16 | Misses exact key; MQ filter correctly rejects |
| Pure-Python LLL hybrid | TOY-32 | Stalls (documents need for real BKZ) |
| Gröbner (sympy) | TOY-16 planted | Basis 2.1s/53 polys; **full solve >300s** |
| msolve basis | planted n=16 / n=24 | 0.3–0.5s / 180s |
| msolve basis | planted n=28 | **>1200s unfinished** (bounded) |
| msolve basis | planted n=32 | **OOM at 114GB on 16 cores** (kernel-logged) |
| Pure-MQ, no bounds | any scale | Trivial GB (0.1s), recovers nothing (positive-dim) |
| Joint lattice-enum + MQ filter | TOY-16 | **Exact recovery, 299 nodes** (vs 147k brute space) |
| Gröbner+field-eq slice | TOY-16 | Exact key in ~2s (unique solution) |

## Structural findings

1. **Bases cheap, solutions hard**: with field equations the GB is trivial
   but the variety is enormous — MQ cost sits in solution-filtering for the
   sparse root, where the hybrid demonstrably wins at toy scale.
2. **Hardness sits where theory says**: bounds force zero-dimensionality
   and drive the blowup (0.5s → 180s → >1200s → OOM across n=16/24/28/32).
3. **No planted non-genericity** measurable at n=16 (planted ≡ random).
4. **Bardet bounds uninformative** for this shape (15/27/past-80 predicted
   vs 2–4 observed) — empirical scaling is the evidence.
5. Lattice-only candidates correctly rejected by MQ filter in every run
   (jointness works as designed at toy scale).
