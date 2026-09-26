"""Gröbner with lattice + MQ + bound equations on TOY-16 slice (GF(17)).

System: A*s - b = 0 is linear over GF(17) BUT true relation is A*s+e=b with
small unknown e. For algebraic demo we eliminate e by testing exact slice:
use noiseless b0=A*s (recomputed) so linear system is exact, plus MQ + x^3-x bounds.
Shows joint system solving shape; noisy case needs error variables (much harder).
"""
import sys
import time
sys.path.insert(0, "ref")
from rmdq_toy import Params, keygen, mat_vec_mul, flatten, unflatten

def main():
    from sympy import symbols, groebner, GF
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    kg = keygen(p, b"seedA-test-0000", b"seedP-test-0000", b"seeds-test-0000")
    A, P = kg["A"], kg["P"]
    s_true = flatten(kg["s"])
    # noiseless b0 = A*s_true (exact linear system)
    b0 = mat_vec_mul(A, unflatten(s_true, 1, 16), 17)[0]
    a = A[0][0]
    n = 16
    xs = symbols("x0:16")
    eqs = []
    # correct rotation: (a*s)[i] = sum_j a[(i-j) mod n]*s[j] with -sign on wrap
    R = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            d = i - j
            if d >= 0:
                R[i][j] = a[d] % 17
            else:
                R[i][j] = (-a[d + n]) % 17
    assert [sum(R[i][j]*s_true[j] for j in range(n)) % 17 for i in range(n)] == b0, "rotation check"
    for i in range(n):
        e = -b0[i]
        for j in range(n):
            e += R[i][j] * xs[j]
        eqs.append(e)
    for terms in P:
        e = 0
        for c, vi, vj in terms:
            if vj == -1:
                e += c * xs[vi]
            else:
                e += c * xs[vi] * xs[vj]
        eqs.append(e)
    for i in range(n):
        eqs.append(xs[i]**3 - xs[i])
    print(f"system: {len(eqs)} eqs (16 lin + 2 MQ + 16 bounds), 16 vars over GF(17)")
    t0 = time.time()
    G = groebner(eqs, *xs, order="grlex", domain=GF(17))
    dt = time.time() - t0
    print(f"done {dt:.2f}s basis len={len(G.polys)}")
    for g in list(G.polys)[:8]:
        print(" ", str(g.as_expr())[:160])
    print("note: noiseless+exact slice only; noisy e adds 16+ error vars (see kill-phase docs)")

if __name__ == "__main__":
    main()
