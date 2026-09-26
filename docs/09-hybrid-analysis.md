# Hybrid attack analysis (round 1): verdict + recommendation

## Result

Position+value guessing + BKZ remainder (ref/hybrid_attack.py, same dual
model as docs/08): the optimum is g=0 at ALL tested densities -- guessing
never pays. At wt/N = 25%, hitting support costs ~2^4 per guess while BKZ
beta drops only ~1 per removed dimension. This matches published experience
for dense-ish secrets (Kyber row: optimum g=0 too).

Enumeration half validated empirically (tests/test_hybrid.py: predicted vs
measured guessing trials agree); lattice half inherits docs/08 validation.

## Numbers (classical / quantum, Core-SVP proxy)

- UQ k=2 wt=128: pure 2^110 / 2^99; hybrid optimum g=0 (same).
- UQ k=3 wt=240: pure 2^196 / 2^178; hybrid optimum g=0 (same).
- Reference, same model: Kyber512 2^115 / 2^104.

## Weight lever (free-ish lunch)

Raising wt costs ~nothing in sizes (sparse-encoded sk grows slightly) and a
little sampling time. Model response at k=2: wt=64 -> 2^106; 128 -> 2^110;
192 -> 2^112; 256 -> 2^115/2^104 = EXACTLY the Kyber512 reference point
(same per-coeff RMS). **Recommendation: wt=192 minimum, wt=224-256 to close
the gap**, pending failure-rate re-check (denser s = more decrypt noise)
and planted-MQ density review (denser support = fewer vanishing clauses).

## What this does NOT cover (still blocking Cats)

- Support-only hybrids with hints ( Ruhama/directional variants that beat
  position+value guessing in some regimes).
- BKW / coded-BKW style attacks exploiting the ring structure.
- Quantum speedups beyond Grover-over-guesses + sieve (e.g., quantum walks
  on combinatorial search).
- The planted-MQ coupling: a joint lattice+MQ hybrid could outperform both
  pure analyses. This is THE open cryptanalytic question for RMD-Q.
- Model tolerance: 20-bit optimism seen at N=768 (docs/08); fpylll
  cross-check still required.

Conclusion: hybrid guessing does not undercut the pure-lattice numbers at
these densities, and wt is a free lever to match the Kyber reference. But
category claims remain blocked on the items in docs/08.

## Degree-of-regularity study (ref/dreg_study.py, round 3)

- Bardet semi-regular d_reg WITH field equations: 15 (n=16), 27 (n=32),
  None-past-80 (n=512) vs observed F4 max degree 2-4. Verdict: Bardet
  bounds are UNINFORMATIVE for this shape (few quadrics + many field eqs);
  empirical msolve scaling is the evidence to use, not the formula.
- Planted vs uniform-random MQ at n=16: no measurable non-genericity
  (identical trivial GB with bounds; 0.0s class without).
- Structural finding: with field equations the GB is trivial but the
  variety is enormous -- MQ attack cost sits in solution-filtering for the
  sparse root, not basis computation. At toy scale the demonstrated winner
  is the HYBRID (lattice enumeration + MQ filter, ref/break_joint.py:
  exact recovery in 299 nodes), not pure algebra. This reframes the MQ
  threat model toward joint attacks -- which is precisely what the joint
  XL model (above) bounds.

## Joint lattice+MQ model (ref/joint_hybrid.py, round 2) — verdict: lattice binds — verdict: lattice binds

## Noisy hints (proxy analysis, not a separate attack implementation)

Perfect-hints runs give anchor points (k=2 classical): h=0 -> 2^110,
h=32 -> 2^100, h=64 -> 2^90, h=128 -> 2^71. A noisy hint correct w.p. p
is strictly weaker than a perfect hint; interpolating, p=0.5 leakage sits
roughly at the perfect-h≈N(1-p)/4 corner (documented proxy, not derived).
Takeaway for implementers: budget side-channel defenses for <32 coords of
equivalent leakage; at h>=64 the classical margin drops under 2^90 and the
design would need re-parameterization. A proper DakNet-style noisy-hint
analysis (May et al. framework) is queued as future work.

Paths: (A) pure XL with field equations, (B) guess-then-XL, (C)
guess-then-lattice. XL counting is standard Macaulay (rows = t·C(N+D-2,D-2)
+ N·C(N+D-f,D-f), need rows >= cols-1) INCLUDING degree-f field equations
(f=2·eta+1, public parameter info -- attacker-favorable to include).

- TOY-16: XL feasible 2^32 (D=10); lattice path 2^12 dominates (matches
  reality: toy falls fast).
- TOY-32: XL 2^54; lattice 2^12 dominates.
- Prod k=2/k=3: XL infeasible at all D<=14 even with field equations
  (t=8-10 equations cannot linearize 512-768 vars); lattice path
  (2^110/2^196) binds IN THIS MODEL FAMILY.
- msolve scaling (GB only): n=16 planted 0.3-0.5s, n=24 planted 180s,
  n=28 planted >1200s (bounded, unfinished), n=32 OOMs at 114GB on
  16 cores. Full solve (not just basis) exceeded 300s even at n=16.

Reading: the MQ subsystem (t=8 sparse quadrics in 512 vars) contributes
negligibly to joint XL attacks; nothing in this model family undercuts the
pure-lattice numbers. Caveats: XL row-independence is attacker-favorable
counting while real F4 beats XL constants; degree-of-regularity subtleties
unmodeled; planted-structure-specific attacks (the real unknown) unmodeled.
The joint question stays open but the first quantitative model favors
lattice-dominance.
