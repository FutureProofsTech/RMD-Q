"""fpylll cross-check of the estimator's BKZ model (docs/08 validation).

Test: random q-ary lattice, BKZ-beta, achieved root-Hermite factor vs
Chen-Nguyen delta_beta() used by estimate_security.py. Agreement within a
few % validates the model's core constant; the remaining gap items
(sieve costs, m-optimization) stay documented.
"""
import sys
sys.path.insert(0, "ref" if __name__ == "__main__" else ".")
from estimate_security import delta_beta


def trial(m, n, q, beta, seed):
    import random
    from fpylll import IntegerMatrix, LLL, BKZ
    rnd = random.Random(seed)
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(m)]
    # q-ary lattice basis (rows): [qI_m 0; A I_n] -> dim m+n, det q^m
    d = m + n
    B = IntegerMatrix(d, d)
    for i in range(m):
        B[i, i] = q
    for i in range(m):
        for j in range(n):
            B[m + j, i] = A[i][j] % q
    for j in range(n):
        B[m + j, m + j] = 1
    LLL.reduction(B)
    par = BKZ.Param(beta, max_loops=8)
    BKZ.reduction(B, par)
    v0 = [int(B[0, j]) for j in range(d)]
    import math
    norm = math.sqrt(sum(x * x for x in v0))
    det = q ** m
    achieved = (norm / (det ** (1.0 / d))) ** (1.0 / d)
    return achieved


def main():
    for m, n, q, beta in [(40, 40, 3329, 20), (60, 60, 3329, 25)]:
        got = trial(m, n, q, beta, 1234)
        want = delta_beta(beta)
        print(f"m={m} n={n} beta={beta}: achieved delta={got:.5f} "
              f"model={want:.5f} (ratio {got / want:.3f})")


if __name__ == "__main__":
    main()
