"""Joint lattice-enumeration + MQ-filter attack (toy scale demo).

Methodology: Babai point from LLL-reduced Kannan lattice, then bounded
enumeration of neighbors by increasing residual norm; FIRST candidate with
P(s)==0 wins. Compares nodes-visited vs pure brute force over the sparse
space. Proves the joint methodology concretely; prod extrapolation via the
enumeration-count model (not by running it).
"""
import itertools
import sys
import time
sys.path.insert(0, "ref")
from rmdq_toy import Params, keygen, mat_vec_mul, poly_sub, norm_inf_poly, flatten, unflatten, eval_mq


def neighbors_by_weight(center, n, q, max_extra):
    """Yield candidates in rough order of distance from center (for demo)."""
    yield list(center)
    # single-coordinate deviations +-1, +-2 (eta=1 toy: values are 0/1/q-1;
    # enumerate alternative values per coord)
    for i in range(n):
        for v in (0, 1, q - 1):
            if v != center[i]:
                c = list(center)
                c[i] = v
                yield c


def joint_attack(n=16, q=17, t=2, m=4, budget=60000):
    from break_lll_xl import lll, babai, rot_negacyclic
    p = Params(n=n, q=q, k=1, eta=1, w=4, eta_e=1, t=t, m=m)
    kg = keygen(p, b"seedA-test-0000", b"seedP-test-0000", b"seeds-test-0000")
    A, b, P = kg["A"], kg["b"], kg["P"]
    true = flatten(kg["s"])
    # LLL + Babai (lattice half)
    a = A[0][0]
    R = rot_negacyclic(a)
    M = 5
    B = []
    for i in range(n):
        row = [0] * (2 * n + 1)
        row[i] = q
        B.append(row)
    for i in range(n):
        row = [-R[i][j] for j in range(n)] + [1 if j == i else 0 for j in range(n)] + [0]
        B.append(row)
    row = [-x for x in b[0]] + [0] * n + [M]
    B.append(row)
    Bred = lll(B)
    _, pt = babai(Bred, list(b[0]) + [0] * n + [M])
    center = [int(round(x)) % q for x in pt[n:2 * n]]
    visited = 0
    # phase 1: neighborhood of Babai point
    for cand in neighbors_by_weight(center, n, q, 2):
        visited += 1
        if visited > budget:
            break
        Ac = mat_vec_mul(A, unflatten(cand, 1, n), q)[0]
        if norm_inf_poly(poly_sub(Ac, b[0], q), q) > 2:
            continue
        if all(x == 0 for x in eval_mq(P, cand, q)):
            print(f"JOINT n={n}: hit after {visited} nodes (true match: {cand == true})")
            return visited
    # phase 2: fall back to full brute force (bounded)
    N = n
    for wt in range(5):
        for sup in itertools.combinations(range(N), wt) if wt else [()]:
            for signs in itertools.product([-1, 1], repeat=wt) if wt else [()]:
                cand = [0] * N
                for idx, sgn in zip(sup, signs):
                    cand[idx] = sgn % q
                visited += 1
                if visited > budget:
                    print(f"JOINT n={n}: budget {budget} hit, best-effort end")
                    return None
                Ac = mat_vec_mul(A, unflatten(cand, 1, n), q)[0]
                if norm_inf_poly(poly_sub(Ac, b[0], q), q) > 2:
                    continue
                if all(x == 0 for x in eval_mq(P, cand, q)):
                    print(f"JOINT n={n}: brute-phase hit after {visited} nodes "
                          f"(match={cand == true})")
                    return visited
    return None


if __name__ == "__main__":
    t0 = time.time()
    joint_attack()
    print(f"done {time.time()-t0:.1f}s (pure brute-force space ~147k for reference)")
