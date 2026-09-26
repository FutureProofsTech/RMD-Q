"""LWE security estimator v2 (dual attack, BKZ Core-SVP model).

Dual attack (Bai-Galbraith scaled dual, normal form):
  Given m samples (A, b = A s + e) mod q, find short (v, w) with
  A^T w = v (mod q). Distinguishing advantage:
      eps = exp(-pi * (||v||^2 * s_s^2 + ||w||^2 * s_e^2) * 2pi / q^2)
  (discrete-Gaussian heuristic, standard form). BKZ-beta on the
  (m+N)-dim sermac-q-ary dual yields
      ||(v,w)|| ~= delta(beta)^d * q^(N/d),  d = m + N
  (GSA Hermite bound). Attack cost dominated by BKZ: classical 2^(.292b),
  quantum 2^(.265b), paranoid 2^(.2075b). m optimized per instance.
  Needs eps^2 * m >= ~1 (enough samples to amplify); we require eps >= 2^-32
  with the given m and report the minimal beta.

Stated limits (docs/08): plain-LWE view of Module-LWE (ignores ring/module
structure -- standard first cut, favors attacker slightly); sparse-support
combinatorial attacks unmodeled (extra margin required); sieve cost models
are Healitz-style asymptotics. VALIDATION: same code must reproduce Kyber
reference points within tolerance (see __main__).
"""
import math


def delta_beta(beta):
    b = beta
    return ((b / (2 * math.pi * math.e)) * ((math.pi * b) ** (1.0 / b))) ** (1.0 / (2 * (b - 1)))


def dual_beta(N, q, sig_s, sig_e, m, need_logeps=-32.0):
    d = m + N
    for beta in range(40, 2000):
        L = (delta_beta(beta) ** d) * (q ** (N / d))
        # split L^2 evenly (BKZ balances); eps from both terms
        # ||v||^2 s_s^2 + ||w||^2 s_e^2 with ||v||~||w||~L/sqrt(2), scaled:
        var = (L ** 2 / 2) * (sig_s ** 2 + sig_e ** 2) * 2 * math.pi / q ** 2
        eps = math.exp(-math.pi * var)
        if eps <= 0:
            continue
        if math.log2(eps) >= need_logeps:
            return beta, math.log2(eps)
    return None, None


def costs(beta):
    return {k: v * beta for k, v in
            [("classical", 0.292), ("quantum", 0.265), ("paranoid", 0.2075)]}


def report(name, N, q, sig_s, sig_e, ms=None):
    ms = ms or [N, 2 * N, 4 * N]
    best = None
    for m in ms:
        r = dual_beta(N, q, sig_s, sig_e, m)
        if r[0] and (best is None or r[0] < best[0]):
            best = (r[0], m, r[1])
    beta, m, le = best
    c = costs(beta)
    print(f"{name}: N={N} q={q} sig_s={sig_s:.3f} sig_e={sig_e:.3f} (m={m})")
    print(f"  dual beta~{beta} (logeps~{le:.1f}) -> "
          f"2^{c['classical']:.0f} cl / 2^{c['quantum']:.0f} qu / 2^{c['paranoid']:.0f} par")
    return beta


if __name__ == "__main__":
    print("== references (expect ~404 / ~627 primal-beta equivalents) ==")
    report("ML-KEM-512", 512, 3329, 1.0, 1.0)
    report("ML-KEM-768", 768, 3329, 1.0, 1.0)
    print("== ours (sparse s per-coeff RMS, CBD e) ==")
    for k, wt in [(2, 128), (3, 240)]:
        N = 256 * k
        m2 = sum(v * v for v in range(-2, 3)) / 5.0
        report(f"UQ k={k} wt={wt}", N, 3329, math.sqrt(wt / N * m2), 1.0)
