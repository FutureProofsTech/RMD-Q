"""Sympy Gröbner trial on TOY-16 MQ (t=2, N=16, q=17): shape + timing only."""
import sys
import time
sys.path.insert(0, "ref")
from rmdq_toy import Params, keygen, flatten

def main():
    from sympy import symbols, groebner
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    kg = keygen(p, b"seedA-test-0000", b"seedP-test-0000", b"seeds-test-0000")
    P = kg["P"]
    xs = symbols("x0:16")
    eqs = []
    for terms in P:
        e = 0
        for c, vi, vj in terms:
            if vj == -1:
                e += c * xs[vi]
            else:
                e += c * xs[vi] * xs[vj]
        eqs.append(e)
    t0 = time.time()
    G = groebner(eqs, *xs, order="grlex", domain=f"ZZ_{p.q}" if False else "ZZ")
    dt = time.time() - t0
    print(f"groebner done in {dt:.2f}s, basis len={len(G.polys)}")
    for g in list(G.polys)[:4]:
        print(" ", str(g.as_expr())[:160])
    print("note: domain ZZ (not GF(17)) + no field eqs — shape demo only; full attack needs GF + bounds")

if __name__ == "__main__":
    main()
