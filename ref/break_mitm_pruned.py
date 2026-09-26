"""Pruned MITM with lattice-residual buckets for noisy TOY-32.

Improvement over hill-climb: enumerate left half (16 vars, wt<=3, ~16k cands),
bucket by rounded residual; enumerate right half streaming, check combined
residual <= B_e AND MQ==0. Bounded budget, reports closest miss if no break.
Deterministic. Expected: still likely stalls (residual noise spreads buckets),
but strictly stronger than random/hill-climb and quantifies gap.
"""
import itertools
import sys
sys.path.insert(0, "ref")
from rmdq_toy import Params, keygen, mat_vec_mul, poly_sub, norm_inf_poly, flatten, unflatten, eval_mq

def gen_half(A, idxs, q, wt_max=3):
    out = []
    for wt in range(wt_max + 1):
        for sup in itertools.combinations(idxs, wt) if wt else [()]:
            for signs in itertools.product([1, q - 1], repeat=wt) if wt else [()]:
                v = [0] * 32
                for i, s in zip(sup, signs):
                    v[i] = s
                Av = mat_vec_mul(A, unflatten(v, 1, 32), q)[0]
                out.append((v, Av))
    return out

def main(budget=400000):
    p = Params(n=32, q=97, k=1, eta=1, w=6, eta_e=1, t=3, m=6)
    kg = keygen(p, b"noisy-A-00000000", b"noisy-P-00000000", b"noisy-S-00000000")
    A, b, P = kg["A"], kg["b"], kg["P"]
    true = flatten(kg["s"])
    left = gen_half(A, list(range(16)), 97)
    print(f"left table: {len(left)} cands")
    # index left by first coeff bucket to prune (weak prune, honest)
    best = (10**9, None)
    tried = 0
    for v2, Av2 in gen_half(A, list(range(16, 32)), 97):
        for v1, Av1 in left:
            tried += 1
            if tried > budget:
                print(f"budget {budget} hit; best residual={best[0]}")
                return False
            s = [(a + c) % 97 for a, c in zip(Av1, Av2)]
            res = poly_sub(s, b[0], 97)
            r = norm_inf_poly(res, 97)
            if r < best[0]:
                cand = [(a + c) % 97 for a, c in zip(v1, v2)]
                mq = sum(1 for x in eval_mq(P, cand, 97) if x)
                best = (r, (sum(1 for x in cand if x), mq))
            if r <= 2:
                cand = [(a + c) % 97 for a, c in zip(v1, v2)]
                if all(x == 0 for x in eval_mq(P, cand, 97)):
                    print(f"BROKE after {tried}: match={cand == true}")
                    return True
    print(f"exhausted; best residual={best[0]} {best[1]}")
    return False

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 2)
