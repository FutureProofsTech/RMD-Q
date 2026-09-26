"""TOY-32 kill-phase: MITM demo on noiseless variant + bounded search on noisy variant.

Proves: (1) without noise, joint problem falls to split-weight MITM fast;
(2) with noise, naive brute stalls — motivating lattice-hybrid need.
Honest calibration, not a full break of noisy TOY-32.
"""
import itertools
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, expand_matrix, expand_mq, mat_vec_mul, poly_sub, poly_add, norm_inf_poly, flatten, unflatten, eval_mq, sample_vec

def mitm_noiseless():
    print("=== MITM on noiseless TOY-32 (e=0) ===")
    p = Params(n=32, q=97, k=1, eta=1, w=6, eta_e=0, t=3, m=6)
    seed_A, seed_P = b"MITM-A-000000000", b"MITM-P-000000000"
    A = expand_matrix(seed_A, 1, 32, 97, b"\x00kem-a")
    P = expand_mq(seed_P, 3, 32, 6, 97)
    # find a key s with P(s)=0 by rejection (same as keygen)
    s_true = None
    for attempt in range(256):
        s = sample_vec(1, 32, 97, 1, 6, b"MITM-S-000000000", attempt)
        if all(v == 0 for v in eval_mq(P, flatten(s), 97)):
            s_true = flatten(s)
            print(f"key found attempt={attempt} weight={sum(1 for x in s_true if x)}")
            break
    assert s_true is not None
    # b = A*s (no noise)
    b = mat_vec_mul(A, unflatten(s_true, 1, 32), 97)[0]
    # MITM split vars 0..15 | 16..31, weights w1+w2=wt (try all splits)
    import random
    # build table for left half weight<=3
    table = {}
    N1 = list(range(16))
    for wt in range(4):
        for sup in itertools.combinations(N1, wt) if wt else [()]:
            for signs in itertools.product([-1, 1], repeat=wt) if wt else [()]:
                v = [0] * 32
                for i, sg in zip(sup, signs):
                    v[i] = sg % 97
                Av = mat_vec_mul(A, unflatten(v, 1, 32), 97)[0]
                table.setdefault(tuple(Av), []).append(v)
    print(f"table size {len(table)}")
    # search right half
    N2 = list(range(16, 32))
    tried = 0
    for wt in range(7):
        for sup in itertools.combinations(N2, wt) if wt else [()]:
            for signs in itertools.product([-1, 1], repeat=wt) if wt else [()]:
                v2 = [0] * 32
                for i, sg in zip(sup, signs):
                    v2[i] = sg % 97
                Av2 = mat_vec_mul(A, unflatten(v2, 1, 32), 97)[0]
                need = tuple(( (bi - ai) % 97 for bi, ai in zip(b, Av2)))
                if need in table:
                    for v1 in table[need]:
                        cand = [(a + c) % 97 for a, c in zip(v1, v2)]
                        if all(x == 0 for x in eval_mq(P, cand, 97)):
                            print(f"MITM BROKE noiseless key after {tried} right probes: match={cand==s_true}")
                            return True
                tried += 1
                if tried % 20000 == 0:
                    print(f"  ...{tried} probes")
                if tried > 120000:
                    print("MITM probe budget exceeded (unexpected for noiseless toy)")
                    return False
    print("MITM failed (unexpected)")
    return False

def bounded_noisy():
    print("=== Bounded random search on noisy TOY-32 (expected to stall) ===")
    import random
    p = Params(n=32, q=97, k=1, eta=1, w=6, eta_e=1, t=3, m=6)
    from rmdq_toy import keygen
    kg = keygen(p, b"noisy-A-00000000", b"noisy-P-00000000", b"noisy-S-00000000")
    A, b, P = kg["A"], kg["b"], kg["P"]
    true = flatten(kg["s"])
    rnd = random.Random(0)
    for i in range(20000):
        # random sparse candidate
        sup = rnd.sample(range(32), 6)
        cand = [0]*32
        for j in sup:
            cand[j] = rnd.choice([1, 96])
        Ac = mat_vec_mul(A, unflatten(cand,1,32), 97)[0]
        if norm_inf_poly(poly_sub(Ac, b[0], 97), 97) > 2:
            continue
        if all(x==0 for x in eval_mq(P, cand, 97)):
            print(f"random hit after {i}: match={cand==true}")
            return True
    print("no random hit in 20k probes (expected — naive stalls, need lattice-hybrid)")
    return False

if __name__ == "__main__":
    mitm_noiseless()
    bounded_noisy()
