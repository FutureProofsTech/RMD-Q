"""GF(17) Gröbner with bound field equations on tiny MQ slice.

Full 16-var + field eqs is heavy; use smallest slice that still shows shape:
take first t=2 equations restricted to involved vars only + x^3-x=0 per involved var
(eta=1 -> coeffs in {-1,0,1} mod 17). Report timing/basis, honest about scaling.
"""
import sys
import time
sys.path.insert(0, "ref")
from rmdq_toy import Params, keygen

def main():
    from sympy import symbols, groebner, GF
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    kg = keygen(p, b"seedA-test-0000", b"seedP-test-0000", b"seeds-test-0000")
    P = kg["P"]
    involved = sorted({v for terms in P for _, vi, vj in terms for v in (vi, vj) if v != -1})
    print(f"involved vars: {len(involved)} of 16")
    xs = symbols("x0:%d" % len(involved))
    imap = {v: i for i, v in enumerate(involved)}
    eqs = []
    for terms in P:
        e = 0
        for c, vi, vj in terms:
            if vj == -1:
                e += c * xs[imap[vi]]
            else:
                e += c * xs[imap[vi]] * xs[imap[vj]]
        eqs.append(e)
    # bound equations x^3 - x = 0 (roots -1,0,1 mod 17)
    for i in range(len(involved)):
        eqs.append(xs[i]**3 - xs[i])
    t0 = time.time()
    G = groebner(eqs, *xs, order="grlex", domain=GF(17))
    dt = time.time() - t0
    print(f"GF(17) groebner: {len(involved)} vars, {len(eqs)} eqs, {dt:.2f}s, basis len={len(G.polys)}")
    for g in list(G.polys)[:6]:
        print(" ", str(g.as_expr())[:200])
    print("interpretation: toy slice solvable check — full 16-var + lattice coupling is the hard part (see break_lll_xl)")

if __name__ == "__main__":
    main()
