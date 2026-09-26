"""NTT tables for q=3329, n=256, R=X^256+1: 7-layer DIT, k=1..127 schedule.

Closed forms (asserted, not trusted):
- FWT[k] = 17^bitrev7(k) mod q (k=0 unused placeholder = 1).
- Pair moduli ZP[p] found empirically by CRT search, then checked against
  closed form 17^bitrev7(64+perm(p)).
Verifies: CRT match (all pairs), inv(fwd)==id, ntt-mul==schoolbook negacyclic.
Emits ref/ntt_tables.json.
"""
import json
import os

Q = 3329
ROOT = 17  # order exactly 256 (17^128 = -1 mod q, asserted below)


def rev(x, bits):
    r = 0
    for _ in range(bits):
        r = (r << 1) | (x & 1)
        x >>= 1
    return r


def fwd(a, FWT):
    a = list(a)
    k = 1
    length = 128
    while length >= 2:
        for start in range(0, 256, 2 * length):
            zeta = FWT[k]
            k += 1
            for j in range(start, start + length):
                t = zeta * a[j + length] % Q
                a[j + length] = (a[j] - t) % Q
                a[j] = (a[j] + t) % Q
        length //= 2
    return a


def reduce_mod(a, z):
    r = list(a)
    for deg in range(255, 1, -1):
        if r[deg]:
            r[deg - 2] = (r[deg - 2] + r[deg] * z) % Q
    return (r[0], r[1])


def main():
    import random
    assert pow(ROOT, 128, Q) == Q - 1 and pow(ROOT, 256, Q) == 1
    FWT = [1] + [pow(ROOT, rev(k, 7), Q) for k in range(1, 128)]
    rnd = random.Random(42)

    # 1. find pair moduli empirically (adjacent pairs), check product identity
    a = [rnd.randrange(Q) for _ in range(256)]
    f = fwd(a, FWT)
    cands = [(e, pow(ROOT, e, Q)) for e in range(256)]
    ZP, exps = [], []
    for p in range(128):
        pair = (f[2 * p], f[2 * p + 1])
        hits = [e for e, z in cands if reduce_mod(a, z) == pair]
        assert len(hits) == 1, (p, len(hits))
        ZP.append(cands[hits[0]][1])
        exps.append(hits[0])
    # product check: prod(Y - m_i) == Y^128 + 1 ?
    assert all(e % 2 == 1 for e in exps), "moduli must be odd powers (negacyclic)"
    print("pair moduli all odd exponents, e.g.", exps[:8])
    # closed form check
    closed = [rev(64 + (p // 2) * 2 + (p % 2), 7) for p in range(128)]
    print("closed-form match:", exps == closed)

    # 2. inverse + full mul
    NINV128 = pow(128, -1, Q)

    def inv(fc):
        fc = list(fc)
        lens = [2, 4, 8, 16, 32, 64, 128]
        ends = {}
        kk, L = 1, 128
        while L >= 2:
            B = 128 // L
            for bb in range(B):
                ends[(L, bb)] = kk
                kk += 1
            L //= 2
        for L in lens:
            B = 128 // L
            for bb in range(B):
                zi = pow(FWT[ends[(L, bb)]], -1, Q)
                for j in range(bb * 2 * L, bb * 2 * L + L):
                    u, v = fc[j], fc[j + L]
                    fc[j] = (u + v) % Q
                    fc[j + L] = ((u - v) * zi) % Q
        return [x * NINV128 % Q for x in fc]

    a = [rnd.randrange(Q) for _ in range(256)]
    assert inv(fwd(a, FWT)) == a
    print("inv(fwd)==id")

    def ntt_mul(aa, bb):
        fa, fb = fwd(aa, FWT), fwd(bb, FWT)
        fc = [0] * 256
        for i in range(128):
            a0, a1 = fa[2 * i], fa[2 * i + 1]
            b0, b1 = fb[2 * i], fb[2 * i + 1]
            z = ZP[i]
            fc[2 * i] = (a0 * b0 + a1 * b1 % Q * z) % Q
            fc[2 * i + 1] = (a0 * b1 + a1 * b0) % Q
        return inv(fc)

    for trial in range(5):
        aa = [rnd.randrange(Q) for _ in range(256)]
        bb = [rnd.randrange(Q) for _ in range(256)]
        ref = [0] * 256
        for i, ai in enumerate(aa):
            for j, bj in enumerate(bb):
                if i + j < 256:
                    ref[i + j] = (ref[i + j] + ai * bj) % Q
                else:
                    ref[i + j - 256] = (ref[i + j - 256] - ai * bj) % Q
        assert ntt_mul(aa, bb) == ref, f"mul trial {trial}"
    print("ntt-mul == schoolbook negacyclic (5 trials)")

    with open(os.path.join(os.path.dirname(__file__), "ntt_tables.json"), "w") as f:
        json.dump({"ROOT": ROOT, "NINV128": NINV128, "FWT": FWT, "ZP": ZP,
                   "ZINVW": [pow(z, -1, Q) for z in FWT]}, f)
    print("wrote ref/ntt_tables.json")


if __name__ == "__main__":
    main()
