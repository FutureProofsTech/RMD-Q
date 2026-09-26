"""Hybrid breaker v1 for noisy TOY-32: hill-climb + restarts + MQ filter.

Strategy (honest heuristic, not guaranteed):
  cost = alpha*||A*cand - b||_inf + beta*mq_violations + gamma*weight_penalty
Greedy single-coordinate moves over sparse-short space, random restarts.
Toy N=32,q=97 should recover true key within seconds/minutes because noise small.
If it stalls, that itself calibrates hardness (documents need for BKZ).
"""
import os
import random
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, keygen, mat_vec_mul, poly_sub, norm_inf_poly, flatten, unflatten, eval_mq

def cost_of(cand_flat, A, b, P, q, target_w=6, alpha=10, beta=50, gamma=1):
    cand_vec = unflatten(cand_flat, 1, len(b[0]) if isinstance(b[0], list) else 32)
    # b is list of polys; handle k=1
    Ac = mat_vec_mul(A, cand_vec, q)[0]
    res = poly_sub(Ac, b[0], q)
    r = norm_inf_poly(res, q)
    mq = sum(1 for v in eval_mq(P, cand_flat, q) if v != 0)
    w = sum(1 for x in cand_flat if x != 0)
    return alpha * r + beta * mq + gamma * max(0, w - target_w), (r, mq, w)

def hill_break(seed_A=b"noisy-A-00000000", seed_P=b"noisy-P-00000000", seed_S=b"noisy-S-00000000",
               max_restarts=30, max_steps=3000, seed=0):
    from rmdq_toy import Params
    p = Params(n=32, q=97, k=1, eta=1, w=6, eta_e=1, t=3, m=6)
    kg = keygen(p, seed_A, seed_P, seed_S)
    A, b, P = kg["A"], kg["b"], kg["P"]
    true = flatten(kg["s"])
    print(f"true key weight={sum(1 for x in true if x)}")
    rnd = random.Random(seed)
    N = 32
    for rs in range(max_restarts):
        # random sparse start weight 6
        cand = [0] * N
        for i in rnd.sample(range(N), 6):
            cand[i] = rnd.choice([1, 96])
        best, info = cost_of(cand, A, b, P, 97)
        if best == 0:
            print(f"RESTART {rs}: instant hit")
            return True
        for step in range(max_steps):
            # propose: move one nonzero to new position, or flip sign, or swap
            prop = cand[:]
            mv = rnd.random()
            if mv < 0.5:
                # move a random nonzero to random zero slot
                nz = [i for i, x in enumerate(prop) if x != 0]
                z = [i for i, x in enumerate(prop) if x == 0]
                if nz and z:
                    a = rnd.choice(nz); c = rnd.choice(z)
                    prop[c] = prop[a]; prop[a] = 0
            elif mv < 0.8:
                i = rnd.randrange(N)
                prop[i] = rnd.choice([0, 1, 96])
            else:
                i = rnd.randrange(N)
                if prop[i] == 1:
                    prop[i] = 96
                elif prop[i] == 96:
                    prop[i] = 1
            c2, info2 = cost_of(prop, A, b, P, 97)
            if c2 <= best:
                cand, best, info = prop, c2, info2
                if best == 0:
                    print(f"BROKE noisy TOY-32 restart={rs} step={step} match={cand==true}")
                    return True
        print(f"restart {rs}: best={best} info(res,mq,w)={info}")
    print("hill-break stalled within budget (documents hardness — next: BKZ/fpylll or larger budget)")
    return False

if __name__ == "__main__":
    ok = hill_break()
    sys.exit(0 if ok else 2)
