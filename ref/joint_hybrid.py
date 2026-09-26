"""Joint lattice+MQ hybrid cost model (round 1).

Combines three attacker resources against RMD-Q (N vars, t quadrics,
sparse-short secret weight wt, LWE lattice part):
  1. Guess g support (position,value) pairs           : T_guess(g) trials
  2. XL linearization on the MQ subsystem restricted to the remaining
     N-g variables: multiply t equations by all monomials up to degree D-2;
     solve when #independent rows >= #monomials(D) - 1.
     XL cost ~ C(N',D)^omega (omega=2.8, Strassen-ish; also report 2.37).
     NOTE: XL solves for ALL variables (not just support) classically; the
     joint trick is that after guessing g support coords, remaining system
     has N-g vars AND the attacker only needs the sparse remainder --
     modeled as XL on N-g vars + lattice finish. We take min over paths:
  Path A (MQ-first): XL(D) on N vars, then read off sparse root from the
     (assumed unique-in-practice... bounded by bound equations) solution set.
  Path B (guess-then-XL): guess g, XL(D) on N-g vars.
  Path C (guess-then-lattice): guess g, dual-BKZ remainder (hybrid_attack).
  Total = min over (path, g, D). All costs classical-first (+quantum sieve
  variant reported for the winning corner).

Bound/field equations: sparse values in [-2,2] satisfy degree-5 equations;
for XL counting we credit the attacker with x_i^3=x_i-style cubics ONLY at
toy eta=1 (degree 3); at eta=2 the degree-5 system is counted when flagged.
Honest simplification: XL row counts assume generic independence (overstates
attacker slightly when systems are dependent -- conservative FOR the
defender? NO: overcounting rows needed UNDERSTATES attacker. We use the
standard "enough rows" lower bound, i.e., OPTIMISTIC for attacker --
attacker-favoring, stated).

Stated limits: no module structure, no Gröbner-vs-XL gap modeling (XL is
the analyzable proxy; F4/F5 only faster), sieve asymptotics, plain-LWE
lattice leg (same dual model as docs/08).
"""
import math
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from estimate_security import dual_beta
from hybrid_attack import guess_trials


def xl_cost(Nv, t, D, f, omega=2.8):
    """Min cost to linearize t quadrics + Nv degree-f field equations in Nv
    vars at degree D, else inf. Rows: t*C(Nv+D-2,D-2) + Nv*C(Nv+D-f,D-f)
    (zero terms when D<f); cols C(Nv+D,D); need rows >= cols - 1."""
    from math import comb
    rows = t * comb(Nv + D - 2, D - 2)
    if D >= f:
        rows += Nv * comb(Nv + D - f, D - f)
    cols = comb(Nv + D, D)
    if rows < cols - 1:
        return float("inf")
    return cols ** (omega / 2) * 2  # ~ matrix mult constant fudge x2 (stated)


def xl_min_cost(Nv, t, eta, Dmax=14):
    from math import comb
    f = 2 * eta + 1  # sparse values in [-eta,eta] satisfy degree-f equation
    best = (float("inf"), None)
    for D in range(2, Dmax + 1):
        c = xl_cost(Nv, t, D, f)
        if c < best[0]:
            best = (c, (D, f))
    return best


def joint(N, q, wt, eta, t, sig_e=1.0, gmax=32):
    m2 = sum(v * v for v in range(-eta, eta + 1)) / (2 * eta + 1)
    results = {}
    # Path A: pure XL on full system
    cA, cfgA = xl_min_cost(N, t, eta)
    results["A:XL-only"] = (math.log2(cA) if cA < float("inf") else float("inf"), cfgA)
    best = ("A:XL-only", results["A:XL-only"][0])
    # Path B/C over guesses
    for g in range(0, min(wt, gmax) + 1):
        T = guess_trials(N, wt, eta, g)
        lt = math.log2(T)
        cB, cfgB = xl_min_cost(N - g, t, eta)
        if cB < float("inf"):
            tot = lt + math.log2(cB)
            if tot < best[1]:
                best = (f"B:guess-then-XL g={g} D={cfgB[0]}", tot)
        sig_s = math.sqrt(max(wt - g, 0) / max(N - g, 1) * m2)
        r = dual_beta(max(N - g, 8), q, sig_s, sig_e, max(N - g, 8))
        if r[0] is not None:
            tot = lt + 0.292 * r[0]
            if tot < best[1]:
                best = (f"C:guess-then-lattice g={g} beta={r[0]}", tot)
    results["best"] = best
    return results


def report(name, N, q, wt, eta, t):
    print(f"{name}: N={N} wt={wt} t={t}")
    for k, v in joint(N, q, wt, eta, t).items():
        if k == "best":
            print(f"  BEST: {v[0]} = 2^{v[1]:.0f}")
        else:
            print(f"  {k}: 2^{v[0]:.0f} {v[1]}")


if __name__ == "__main__":
    report("TOY-16", 16, 17, 4, 1, 2)
    print("---")
    report("TOY-32", 32, 97, 6, 1, 3)
    print("---")
    report("UQ k=2 prod", 512, 3329, 128, 2, 8)
    print("---")
    report("UQ k=3 prod", 768, 3329, 240, 2, 10)
