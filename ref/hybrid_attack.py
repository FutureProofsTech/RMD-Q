"""Hybrid lattice-combinatorial attack estimates for sparse secrets.

Attack (Howgrave-Graham--Smart / Wunderer-style guessing + BKZ remainder):
  guess g (position, value) pairs; a guess is RIGHT with probability
      p = C(wt, g)/C(N, g) * (1/(2*eta))^g
  (g-subset inside support, values right among 2*eta nonzero options).
  Expected trials T = 1/p. After a right guess, subtract known part:
  remaining LWE has dimension N-g, weight wt-g -> per-coeff RMS' and fresh
  dual-BKZ cost via estimate_security.dual_beta (SAME model as docs/08).
  Total classical: T * 2^(.292b); quantum: sqrt(T) * 2^(.265b) (Grover over
  the guessing + quantum sieve; standard hybrid accounting).
  Minimize over g (g=0 recovers the pure-lattice number).

Stated limits: plain-LWE view; position+value guessing (support-only hybrids
with hints can only do BETTER -- flagged); sieve asymptotics; no module
speedups for the attacker. Enumeration part validated empirically at toy
scale (test_hybrid.py); lattice part inherits docs/08 validation.
"""
import math
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from estimate_security import dual_beta, costs


def guess_trials(N, wt, eta, g, dense=False):
    if g > wt or g > N or g < 0:
        return float("inf")
    if g == 0:
        return 1.0
    from math import comb
    vopts = (2 * eta + 1) if dense else (2 * eta)
    if dense:
        return float(vopts ** g)
    return comb(N, g) * (vopts ** g) / comb(wt, g)


def hybrid(N, q, wt, eta, sig_e, m=None, gmax=48, dense=False, sig_s_fixed=None):
    m2 = sum(v * v for v in range(-eta, eta + 1)) / (2 * eta + 1)
    m = m or N
    best = None
    rows = []
    for g in range(0, min(wt, gmax) + 1):
        T = guess_trials(N, wt, eta, g, dense)
        if sig_s_fixed is not None:
            sig_s = sig_s_fixed
        else:
            sig_s = math.sqrt(max(wt - g, 0) / max(N - g, 1) * m2) if N - g else 0.0
        r = dual_beta(max(N - g, 8), q, sig_s, sig_e, m)
        if r[0] is None:
            continue
        beta = r[0]
        cl = math.log2(T) + 0.292 * beta if T < float("inf") else float("inf")
        qu = 0.5 * math.log2(T) + 0.265 * beta if T < float("inf") else float("inf")
        rows.append((g, math.log2(T) if T < float("inf") else float("inf"), beta, cl, qu))
        if best is None or cl < best[4]:
            best = (g, rows[-1][1], beta, cl, qu)
    return best, rows


def report(name, N, q, wt, eta, sig_e=1.0, dense=False, sig_s_fixed=None):
    best, rows = hybrid(N, q, wt, eta, sig_e, dense=dense, sig_s_fixed=sig_s_fixed)
    g, lt, beta, cl, qu = best
    print(f"{name}: N={N} wt={wt} eta={eta}")
    print(f"  pure lattice (g=0): 2^{rows[0][3]:.0f} cl / 2^{rows[0][4]:.0f} qu")
    print(f"  hybrid optimum g={g}: 2^{cl:.0f} cl / 2^{qu:.0f} qu "
          f"(logT={lt:.1f}, beta={beta})")
    # show neighborhood
    for r in rows[max(0, g - 2):g + 3]:
        print(f"    g={r[0]:3d} logT={r[1]:6.1f} beta={r[2]:4d} cl=2^{r[3]:.0f} qu=2^{r[4]:.0f}")
    return best


if __name__ == "__main__":
    report("TOY-16", 16, 17, 4, 1)
    print("---")
    report("TOY-32", 32, 97, 6, 1)
    print("---")
    report("UQ k=2 (prod sketch)", 512, 3329, 128, 2)
    print("---")
    report("UQ k=3 (prod sketch)", 768, 3329, 240, 2)
    print("---")
    report("ML-KEM-512 (dense CBD, value-guess only)", 512, 3329, 512, 2,
           dense=True, sig_s_fixed=1.0)
    print("---")
    print("perfect-hints variant (h coords leaked exactly; remaining dims attacked):")
    for h in [0, 32, 64, 128]:
        # expected remaining weight after removing h random coords
        N2, wt2 = 512 - h, round(128 * (512 - h) / 512)
        best, _ = hybrid(N2, 3329, wt2, 2, 1.0)
        print(f"  h={h:3d}: remaining N={N2} wt~{wt2}: hybrid 2^{best[3]:.0f} cl / 2^{best[4]:.0f} qu")
