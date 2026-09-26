"""NTT multiply for (n=256, q=3329), R=X^256+1. Logic verified in ref/ntt_gen.py
(CRT match + 5/5 schoolbook trials); this module is the reusable runtime copy.
Dispatch poly_mul_ntt(a,b,q,n): NTT fast path only when (256,3329), else schoolbook.
"""
import json
import os

_Q = 3329
_N = 256
_T = json.load(open(os.path.join(os.path.dirname(__file__), "ntt_tables.json")))
FWT = _T["FWT"]
ZP = _T["ZP"]
NINV128 = _T["NINV128"]


def fwd(a):
    a = list(a)
    k = 1
    length = 128
    while length >= 2:
        for start in range(0, 256, 2 * length):
            zeta = FWT[k]
            k += 1
            for j in range(start, start + length):
                t = zeta * a[j + length] % _Q
                a[j + length] = (a[j] - t) % _Q
                a[j] = (a[j] + t) % _Q
        length //= 2
    return a


def inv(fc):
    fc = list(fc)
    kk, lens = 1, []
    L = 128
    while L >= 2:
        B = 128 // L
        for bb in range(B):
            lens.append((L, bb, kk))
            kk += 1
        L //= 2
    for L, bb, kk in sorted(lens, key=lambda x: x[0]):
        zi = pow(FWT[kk], -1, _Q)
        for j in range(bb * 2 * L, bb * 2 * L + L):
            u, v = fc[j], fc[j + L]
            fc[j] = (u + v) % _Q
            fc[j + L] = ((u - v) * zi) % _Q
    return [x * NINV128 % _Q for x in fc]


def mul_ntt(a, b):
    fa, fb = fwd(a), fwd(b)
    fc = [0] * 256
    for i in range(128):
        a0, a1 = fa[2 * i], fa[2 * i + 1]
        b0, b1 = fb[2 * i], fb[2 * i + 1]
        z = ZP[i]
        fc[2 * i] = (a0 * b0 + a1 * b1 % _Q * z) % _Q
        fc[2 * i + 1] = (a0 * b1 + a1 * b0) % _Q
    return inv(fc)


def poly_mul(a, b, q, n):
    """Dispatch: NTT fast path for prod params, schoolbook otherwise."""
    assert len(a) == len(b) == n
    if n == _N and q == _Q:
        return mul_ntt(a, b)
    tmp = [0] * (2 * n)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    tmp[i + j] = (tmp[i + j] + ai * bj) % q
    return [(tmp[i] - tmp[i + n]) % q for i in range(n)]


def mat_vec_mul_ntt(A, vec, q, n, k):
    """k x k mat-vec via NTT (prod params only). A[i][j], vec[j] polys."""
    assert n == _N and q == _Q
    Ahat = [[fwd(p) for p in row] for row in A]
    vhat = [fwd(p) for p in vec]
    out = []
    for i in range(k):
        acc0 = [0] * 128
        acc1 = [0] * 128
        for j in range(k):
            for t in range(128):
                a0, a1 = Ahat[i][j][2 * t], Ahat[i][j][2 * t + 1]
                b0, b1 = vhat[j][2 * t], vhat[j][2 * t + 1]
                z = ZP[t]
                acc0[t] = (acc0[t] + a0 * b0 + a1 * b1 % q * z) % q
                acc1[t] = (acc1[t] + a0 * b1 + a1 * b0) % q
        fc = [0] * 256
        for t in range(128):
            fc[2 * t], fc[2 * t + 1] = acc0[t], acc1[t]
        out.append(inv(fc))
    return out
