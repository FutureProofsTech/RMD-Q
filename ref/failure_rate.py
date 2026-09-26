"""Decrypt-failure measurement: empirical trials + analytic bound.

Failure event (CPA): ||e^T r - s^T e1 + e2||_inf >= q/4 (decode threshold).
- Empirical: run trials at given params, count coeff errors. Reports rate
  with Clopper-Pearson upper bound (95%) when zero failures observed.
- Analytic: per-coeff noise sum of bounded terms; Hoeffding bound per coeff,
  union bound over n. Conservative (ignores NTT/ring structure).
"""
import math
import sys
sys.path.insert(0, "ref")
from rmdq_toy import Params, keygen, encrypt, decrypt


def trial(params, seedtag, cbd):
    from rmdq_kem import kem_keygen, kem_encaps, kem_decaps
    pk, sk = kem_keygen(params, f"{seedtag}A".encode().ljust(16, b"0")[:16],
                        b"P".ljust(16, b"0"),
                        f"{seedtag}S".encode().ljust(16, b"0")[:16],
                        cbd_err=cbd)
    m = bytes((hash(seedtag) + j) % 256 for j in range(32))
    K, ct, _ = kem_encaps(pk, params, m32=m, cbd=cbd)
    K2, ok = kem_decaps(sk, ct, params, cbd=cbd)
    return ok and K == K2


def cp_upper(n, k, conf=0.95):
    # Clopper-Pearson upper bound, k=0 observed: 1 - (1-conf)^(1/n)
    if k:
        return None
    return 1 - (1 - conf) ** (1.0 / n)


def hoeffding_bound(n, q, eta_s, w_s, eta_e, dense_e):
    # per-coeff noise: <e,r> (n terms) - <s,e1> + e2; each product bounded.
    # sparse s (wt total W, |.|<=eta_s) x dense e1 (|.|<=eta_e): worst |sum|.
    # Hoeffding needs independent bounded summands: use crude worst-case
    # ranges per term family and sum variances.
    # e^T r: r sparse wt W_r, e dense |.|<=eta_e: terms |.| <= eta_e*eta_r...
    # (kept simple + conservative; see docs for derivation)
    B = q // 4
    # variance proxy: sum over all n of (range^2/4) per family (Popoviciu)
    var_er = n * ((2 * eta_e * 2) ** 2) / 4.0
    var_se = n * ((2 * 2 * 2) ** 2) / 4.0
    var_e2 = (2 * 2) ** 2 / 4.0
    var = var_er + var_se + var_e2
    per_coeff = math.exp(-2 * B * B / (4 * var)) if var else 0.0
    return min(1.0, n * per_coeff)


def main():
    import sys
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    for name, kw in [("sparse", dict(cbd=False)), ("cbd", dict(cbd=True))]:
        p = Params(n=256, q=3329, k=2, eta=2, w=64, eta_e=2, t=0, m=0)
        fails = sum(1 for i in range(trials)
                    if not trial(p, f"F{i:03d}{name[0]}", kw["cbd"]))
        print(f"n=256 k=2 {name}: {fails}/{trials} FO failures", end="")
        if not fails:
            print(f" (95% CP upper ~2^{math.log2(cp_upper(trials, 0)):.1f})")
        else:
            print()
    print(f"analytic Hoeffding per-KEM upper: 2^{math.log2(max(hoeffding_bound(256, 3329, 2, 128, 2, True), 1e-300)):.1f}")


if __name__ == "__main__":
    main()
