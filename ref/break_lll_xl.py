"""Pure-Python LLL + Babai + linearization trials on TOY-16 (no external deps).

1. LLL on Kannan-embedded MLWE lattice (dim 2n) -> Babai recovers short (e,s) ignoring MQ, then MQ filter.
2. XL sketch: linearize MQ monomials, report system rank (shows underdetermined -> need more).
Honest calibration: expect LLL to recover small error for n=16,q=17 (easy lattice), proving
lattice part alone is weak and MQ filter is doing real work (matches design intent).
"""
import math
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, keygen, flatten, eval_mq

# ---------- tiny LLL (float Gram-Schmidt, integer rows) ----------

def dot_f(a, b):
    return sum(x * y for x, y in zip(a, b))

def lll(B, delta=0.75):
    """B: list of rows (lists of ints/floats). Returns reduced basis (floats)."""
    n = len(B)
    B = [list(map(float, row)) for row in B]
    def gs():
        O = []
        mu = [[0.0] * n for _ in range(n)]
        Bstar = []
        for i in range(n):
            v = B[i][:]
            for j in range(i):
                mu[i][j] = dot_f(B[i], O[j]) / dot_f(O[j], O[j]) if dot_f(O[j], O[j]) else 0.0
                v = [x - mu[i][j] * y for x, y in zip(v, O[j])]
            O.append(v)
            Bstar.append(v)
        return O, mu
    k = 1
    while k < n:
        O, mu = gs()
        # size reduce B[k]
        for j in range(k - 1, -1, -1):
            q = round(mu[k][j])
            if q:
                B[k] = [x - q * y for x, y in zip(B[k], B[j])]
        O, mu = gs()
        lhs = dot_f(O[k], O[k])
        rhs = (delta - mu[k][k - 1] ** 2) * dot_f(O[k - 1], O[k - 1])
        if lhs >= rhs:
            k += 1
        else:
            B[k], B[k - 1] = B[k - 1], B[k]
            k = max(k - 1, 1)
    return B

def babai(Bred, target):
    """Nearest-plane Babai with reduced basis rows. Returns integer coeff vector + approx point."""
    n = len(Bred)
    # Gram-Schmidt of reduced basis
    O = []
    for i in range(n):
        v = Bred[i][:]
        for j in range(i):
            denom = dot_f(O[j], O[j])
            mu = dot_f(Bred[i], O[j]) / denom if denom else 0.0
            v = [x - mu * y for x, y in zip(v, O[j])]
        O.append(v)
    # work backwards
    coeffs = [0] * n
    t = list(target)
    # project onto reversed GS: standard Babai uses basis as rows; do greedy
    for i in range(n - 1, -1, -1):
        denom = dot_f(O[i], O[i])
        mu = dot_f(t, O[i]) / denom if denom else 0.0
        c = int(round(mu))
        coeffs[i] = c
        t = [x - c * y for x, y in zip(t, Bred[i])]
    pt = [0.0] * len(target)
    for c, b in zip(coeffs, Bred):
        pt = [x + c * y for x, y in zip(pt, b)]
    return coeffs, pt

def rot_negacyclic(poly):
    """n x n rotation matrix rows for multiplication by poly in R=Z[X]/(X^n+1)."""
    n = len(poly)
    M = []
    for i in range(n):
        row = [0] * n
        for j in range(n):
            # (x^i * poly) mod X^n+1
            for k2, c in enumerate(poly):
                idx = i + k2
                sgn = 1
                if idx >= n:
                    idx -= n
                    sgn = -1
                if idx == j:
                    row[j] += sgn * c
        M.append(row)
    return M

def trial_lll_toy16():
    print("=== LLL+Babai on TOY-16 lattice part (ignore MQ, filter after) ===")
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    kg = keygen(p, b"seedA-test-0000", b"seedP-test-0000", b"seeds-test-0000")
    A, bvec, P = kg["A"], kg["b"], kg["P"]
    true = flatten(kg["s"])
    n, q = 16, 17
    a = A[0][0]
    bb = bvec[0]
    R = rot_negacyclic(a)
    # Kannan embedding 2n+1 x 2n+1 for BDD: rows [qI 0 0; -R I 0; -b 0 M] with M ~ q//2? use M=5 toy
    M = 5
    dim = 2 * n + 1
    B = []
    for i in range(n):
        row = [0] * dim
        row[i] = q
        B.append(row)
    for i in range(n):
        row = [-R[i][j] for j in range(n)] + [1 if j == i else 0 for j in range(n)] + [0]
        B.append(row)
    row = [-x for x in bb] + [0] * n + [M]
    B.append(row)
    Bred = lll(B)
    # shortest vector should reveal (e, s, M) shape; find row with last coord +-M
    cands = [row for row in Bred if abs(abs(row[-1]) - M) < 0.5]
    print(f"reduced rows with |last|~M: {len(cands)}")
    # Babai target (b,0, M) to recover
    target = list(bb) + [0] * n + [M]
    coeffs, pt = babai(Bred, target)
    # derive s guess: pt[n:2n] rounded mod q
    s_guess = [int(round(x)) % q for x in pt[n:2 * n]]
    # map q-1 -> -1 style compare: convert to centered then to 0..q-1
    print(f"s_true = {true}")
    print(f"s_guess= {s_guess}")
    match = s_guess == true
    print(f"exact match: {match}")
    # MQ filter on guess
    mq = eval_mq(P, s_guess, q)
    print(f"MQ(guess)={mq} (zeros needed)")
    return match

def trial_xl_rank():
    print("=== XL linearization rank on TOY-16 MQ ===")
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    kg = keygen(p, b"seedA-test-0000", b"seedP-test-0000", b"seeds-test-0000")
    P = kg["P"]
    # monomials: all x_i*x_j (i<=j) + x_i + 1 => count
    N = 16
    mons = N * (N + 1) // 2 + N + 1
    print(f"vars={N} eqs={len(P)} monomials(<=2)={mons} -> heavily underdetermined (need XL multiply to degree 3-4)")
    print("conclusion: plain linearization cannot solve; XL/Gröbner must extend (future sage run)")

if __name__ == "__main__":
    trial_lll_toy16()
    trial_xl_rank()
