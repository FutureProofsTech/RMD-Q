"""Break TOY-16 by brute force over sparse-short space — kill-phase proof.

Enumerates all weight<=w eta=1 candidates for N=16, checks A*s≈b within B_e and P(s)=0.
Expected <1s for TOY-16 (~147k candidates). Proves toy is breakable as required.
"""
import itertools
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, keygen, expand_matrix, expand_mq, mat_vec_mul, poly_sub, norm_inf_poly, flatten, unflatten, eval_mq

def brute_break():
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    seed_A, seed_P, seed_s = b"seedA-test-0000", b"seedP-test-0000", b"seeds-test-0000"
    kg = keygen(p, seed_A, seed_P, seed_s)
    A, b, P = kg["A"], kg["b"], kg["P"]
    true_s = flatten(kg["s"])
    print(f"true s = {true_s}")
    N = 16
    # enumerate support + signs: C(16,4)=1820 * 2^4 signs (eta=1, nonzero = ±1) = ~29k (plus fewer-weight) — trivial
    count = 0
    # enumerate weights 0..4 (keygen sparsifies to <=w, not exactly w)
    for wt in range(0, 5):
        supports = itertools.combinations(range(N), wt) if wt else [()]
        for support in supports:
            signs_iter = itertools.product([-1, 1], repeat=wt) if wt else [()]
            for signs in signs_iter:
                cand = [0] * N
                for idx, sgn in zip(support, signs):
                    cand[idx] = sgn % p.q
                count += 1
                # lattice check: A*cand ≈ b within B_e=2 (toy slack)
                cand_vec = unflatten(cand, 1, 16)
                Ac = mat_vec_mul(A, cand_vec, p.q)[0]
                res = poly_sub(Ac, b[0], p.q)
                if norm_inf_poly(res, p.q) > 2:
                    continue
                if any(v != 0 for v in eval_mq(P, cand, p.q)):
                    continue
                print(f"BROKEN after {count} candidates: recovered {cand}")
                print(f"match true key: {cand == true_s}")
                return True
    print(f"not broken after {count} (unexpected for toy)")
    return False

if __name__ == "__main__":
    ok = brute_break()
    sys.exit(0 if ok else 1)
