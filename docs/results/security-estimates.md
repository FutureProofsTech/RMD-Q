# Results: Security estimates (models, NOT claims)

> No NIST category is claimed. All numbers directional with stated
> tolerances. Reproduce: `python3 ref/estimate_security.py`,
> `python3 ref/hybrid_attack.py`, `python3 ref/joint_hybrid.py`.

## Dual-BKZ lattice leg (Core-SVP proxy)

| Instance | Classical | Quantum | Reference |
|----------|-----------|---------|-----------|
| ML-KEM-512 (same model) | 2^115 | 2^104 | published 2^118/2^107 (**within 3 bits**) |
| UQ k=2 (N=512, wt=128) | 2^110 | 2^99 | ~5 bits under reference in-model |
| UQ k=3 (N=768, wt=240) | 2^196 | 2^178 | ~7 bits under reference in-model |

Caveat: 20-bit optimism at N=768 vs published — model tolerance stated,
fpylll full-attack cross-check queued. fpylll BKZ-constant check agrees
within 0.3% at β=20/25/35 (conservative direction).

## Hybrid guessing + hints

- Position+value guessing optimum: **g=0 at all densities** (guessing
  uneconomical at 25% density); enumeration validated empirically
  (`tests/test_hybrid.py`).
- Weight lever: wt=256 closes the 5-bit gap at ~zero size cost
  (production KATs aligned to w=128/poly).
- Perfect-hints curve: ≈10 bits lost per 32 leaked coordinates
  (h=128 → 2^71 classical). Sizes the side-channel requirements.

## Joint lattice+MQ (round 2)

XL with field equations (attacker-favorable counting) infeasible at prod
scale at every degree ≤ 14 — MQ leg contributes negligibly in-model;
lattice path binds. Planted-structure-specific attacks unmodeled: THE open
cryptanalytic question. See [cryptanalysis](cryptanalysis.md) for the
empirical side.
