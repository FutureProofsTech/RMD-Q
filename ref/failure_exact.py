"""Exact decrypt-failure distribution (FIPS-203-Thm-1 style, simplified).

Noise per message coeff: N = <e,r> - <s,e1> + e2 (sums of products).
Exact pmf of each product family by enumeration, convolved via binary
exponentiation (dict-based, float; mass conservation asserted).
Failure per coeff: |N| >= q/4. Union bound over n (valid upper bound
despite cross-coeff correlation).
Families:
  CBD  eta=2: {(v,p)} binomial {(−2:1,−1:4,0:6,1:4,2:1)}/16
  sparse value (conditioned nonzero): uniform over {+-1,+-2}
Paths: 'sparse' (legacy: r wt=64 sparse, e1/e2 dense-ish legacy) vs
       'cbd' (r,e1,e2 dense CBD2; s always sparse wt).
"""
import sys
sys.path.insert(0, "ref" if __name__ == "__main__" else ".")


def cbd2_pmf():
    from collections import Counter
    c = Counter()
    for a in (0, 1):
        for b in (0, 1):
            for d in (0, 1):
                for e in (0, 1):
                    c[(a + b) - (d + e)] += 1
    return {v: c[v] / 16.0 for v in c}


def sparse_nz_pmf(eta=2):
    vals = [v for v in range(-eta, eta + 1) if v]
    return {v: 1.0 / len(vals) for v in vals}


def prod_pmf(pa, pb):
    from collections import defaultdict
    out = defaultdict(float)
    for a, pa_ in pa.items():
        for b, pb_ in pb.items():
            out[a * b] += pa_ * pb_
    return dict(out)


def conv_pmf(pa, pb):
    from collections import defaultdict
    out = defaultdict(float)
    for a, pa_ in pa.items():
        for b, pb_ in pb.items():
            out[a + b] += pa_ * pb_
    return dict(out)


def conv_pow(pmf, n):
    out = {0: 1.0}
    base = pmf
    while n:
        if n & 1:
            out = conv_pmf(out, base)
        base = conv_pmf(base, base)
        n >>= 1
    return out


def tail_prob(pmf, thresh):
    return sum(p for v, p in pmf.items() if abs(v) >= thresh)


def conv_cap(pa, pb, drop=1e-320):
    """Convolution dropping negligible mass; returns (pmf, dropped)."""
    from collections import defaultdict
    out = defaultdict(float)
    for a, pa_ in pa.items():
        for b, pb_ in pb.items():
            out[a + b] += pa_ * pb_
    dropped = sum(p for p in out.values() if p < drop)
    out = {v: p for v, p in out.items() if p >= drop}
    tot = sum(out.values())
    return {v: p / tot for v, p in out.items()}, dropped + (1 - tot)


def roundoff_pmf(q, d):
    """EXACT compression roundoff distribution: enumerate all x in [0,q).
    Uses the SAME integer formulas as rmdq_toy.compress/decompress_poly
    (round-half-up via +q//2 / +2^{d-1}); NOT Python banker's round().
    No modeling: decompress(compress(x)) - x (centered), uniform x."""
    from collections import Counter
    c = Counter()
    for x in range(q):
        comp = (((x % q) << d) + q // 2) // q % (1 << d)
        y = (comp * q + (1 << (d - 1))) // (1 << d) % q
        e = (y - x) % q
        if e > q // 2:
            e -= q
        c[e] += 1
    return {v: c[v] / q for v in c}


def compressed_noise_pmf(n, k, q, wt, eta, du, dv):
    """Per-coeff marginal of compression noise: <s,cu> + cv. EXACT: true
    roundoff pmfs (enumerated) convolved exactly; s sparse wt worst case."""
    pu, pv = roundoff_pmf(q, du), roundoff_pmf(q, dv)
    sp = sparse_nz_pmf(eta)
    term = prod_pmf(sp, pu)
    return conv_pmf(conv_pow(term, k * wt), pv)


def base_noise_cbd(n, wt):
    """Uncompressed CBD-path noise pmf (exact): <e,r> + <s,e1> + e2."""
    cbd = cbd2_pmf()
    sp = sparse_nz_pmf(2)
    p_er = conv_pow(prod_pmf(cbd, cbd), n)
    p_se = conv_pow(prod_pmf(sp, cbd), wt)
    return conv_pmf(conv_pmf(p_er, {-v: p for v, p in p_se.items()}), cbd)


def analyze_compressed(n=256, q=3329, k=2, wt=192, eta=2, du=10, dv=4):
    import math
    base = base_noise_cbd(n, wt)
    comp = compressed_noise_pmf(n, k, q, wt, eta, du, dv)
    tot = conv_pmf(base, comp)
    assert abs(sum(tot.values()) - 1.0) < 1e-9
    per = max(tail_prob(tot, q // 4), 1e-300)
    print(f"du={du} dv={dv} wt={wt}: per-KEM(union)=2^{math.log2(min(1.0, n*per)):.1f}")
    return per


def analyze(n=256, q=3329, wt=64, eta=2, path="cbd"):
    cbd = cbd2_pmf()
    sp = sparse_nz_pmf(eta)
    if path == "cbd":
        # <e,r>: n CBD*CBD products; <s,e1>: wt sparse*CBD; e2: CBD
        p_er = conv_pow(prod_pmf(cbd, cbd), n)
        p_se = conv_pow(prod_pmf(sp, cbd), wt)
        noise = conv_pmf(conv_pmf(p_er, { -v: p for v, p in p_se.items() }), cbd)
    else:
        # legacy sparse: r sparse wt, e1 dense legacy (treat as uniform eta),
        # e2 uniform eta
        uni = {v: 1.0 / (2 * eta + 1) for v in range(-eta, eta + 1)}
        p_er = conv_pow(prod_pmf(uni, sp), wt)  # e dense-ish x r sparse: wt terms
        p_se = conv_pow(prod_pmf(sp, uni), wt)
        noise = conv_pmf(conv_pmf(p_er, { -v: p for v, p in p_se.items() }), uni)
    mass = sum(noise.values())
    assert abs(mass - 1.0) < 1e-9, mass
    per = tail_prob(noise, q // 4)
    import math
    per = max(per, 1e-300)
    print(f"path={path} wt={wt}: per-coeff fail=2^{math.log2(per):.1f} "
          f"per-KEM(union x{n})=2^{math.log2(min(1.0, n*per)):.1f} "
          f"(support {len(noise)} pts)")
    return per


if __name__ == "__main__":
    for wt in [64, 128, 192, 256]:
        analyze(wt=wt, path="cbd")
    analyze(wt=64, path="sparse")
    print("--- compressed variants (wt=192) ---")
    for du, dv in [(12, 12), (11, 5), (10, 5), (10, 4)]:
        analyze_compressed(wt=192, du=du, dv=dv)
